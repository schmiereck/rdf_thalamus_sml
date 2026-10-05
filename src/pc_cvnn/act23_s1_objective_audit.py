"""Controlled S1 objective audit; all predictions are offline, no robot or PKL."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize

from act23_s1_pc_forward_audit import PCForward, _arrays, _rows, _mse
from energy_pc import activation, pullback
from pc_engine_math_audit import negative_gradient, relative


def objective(z, w, target, name, prior):
    error = w.T @ activation(z, name) - target
    value = .5*float(prior*np.vdot(z,z).real + np.vdot(error,error).real)
    gradient = prior*z + pullback(z, w.conj()@error, name)
    return value, gradient


def solve(w, target, name, prior):
    dim = w.shape[0]
    if name == 'identity':
        if prior:
            z = np.linalg.solve(prior*np.eye(dim)+w.conj()@w.T, w.conj()@target)
        else:
            z = np.linalg.lstsq(w.T, target, rcond=1e-10)[0]
        iterations = 1
    else:
        def fun(v):
            value, g = objective(v[:dim]+1j*v[dim:],w,target,name,prior)
            return value, np.concatenate([g.real,g.imag])
        result = minimize(fun, np.zeros(2*dim), jac=True, method='L-BFGS-B',
                          options=dict(maxiter=2048,gtol=1e-9,ftol=1e-15,maxls=40))
        z = result.x[:dim]+1j*result.x[dim:]
        iterations = int(result.nit)
    _, grad = objective(z,w,target,name,prior)
    residual = float(np.max(np.abs(grad)))
    if not np.isfinite(z).all() or residual >= 1e-5:
        raise RuntimeError(f'Unconverged {name}/{prior}: {residual}')
    return z, residual, iterations


def controls():
    rng=np.random.default_rng(17)
    w=.2*(rng.normal(size=(4,3))+1j*rng.normal(size=(4,3)))
    target=rng.normal(size=3)+1j*rng.normal(size=3)
    point=rng.normal(size=4)+1j*rng.normal(size=4)
    errors=[]
    for name,prior in [('tanh',1.),('identity',1.),('identity',0.)]:
        numeric=-negative_gradient(lambda z: objective(z,w,target,name,prior)[0],point)
        error=relative(objective(point,w,target,name,prior)[1],numeric)
        assert error<1e-6
        z,residual,_=solve(w,target,name,prior)
        if not prior:
            assert np.max(np.abs(w.T@z-target))<1e-10
        errors.append(dict(activation=name,prior=prior,gradient_error=error,solution_gradient=residual))
    # Known scalar complex linear posterior: (1+|i|²)z=conj(i)*1.
    z,_,_=solve(np.array([[1j]]),np.array([1]),'identity',1.)
    assert abs(z[0]+.5j)<1e-12
    # Exact known conditional linear law, with held-out random samples.
    x=rng.normal(size=(100,5)); mapping=rng.normal(size=(5,2))
    fit=np.linalg.lstsq(x[:70],(x@mapping)[:70],rcond=1e-10)[0]
    error=float(np.max(np.abs(x[70:]@fit-(x@mapping)[70:])))
    assert error<1e-10
    return dict(gradients=errors,scalar_posterior=True,known_linear_test_max_error=error)


def write(path, obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('log/s1-proprio/seed101-50x60-safe'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    write(args.output_dir/'controls.json', controls())
    rows=_rows(args.source); x,y,groups,split=_arrays(rows)
    train,test=split=='train',split=='test'
    assert train.sum()==2400 and test.sum()==600
    assert len(set(groups[train]))==40 and len(set(groups[test]))==10
    assert not set(groups[train]) & set(groups[test])
    assert np.isfinite(x).all() and np.isfinite(y).all()
    xm,xs=x[train].mean(0),x[train].std(0)
    ym,ys=y[train].mean(0),y[train].std(0)
    assert min(xs.min(),ys.min())>1e-6  # no hidden change of constant-column convention
    xn,yn=(x-xm)/xs,(y-ym)/ys
    target=np.concatenate([xn,yn],axis=1)
    base=PCForward(15,5,24,17)
    initial=np.concatenate([c.W for c in base.net._connections],axis=1)
    del base
    initial_sha=hashlib.sha256(initial.tobytes()).hexdigest()
    variants=[('tanh_prior1','tanh',1.),('linear_prior1','identity',1.),
              ('linear_prior0','identity',0.)]
    write(args.output_dir/'manifest.json',dict(
        schema='s1-objective-audit-v1',seed=17,epochs=12,latent_dim=24,learning_rate=.004,
        variants=variants,initial_weights_sha256=initial_sha,scipy_version=scipy.__version__,
        source=str(args.source),data_sha256=hashlib.sha256((args.source/'transitions.jsonl').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_mean=xm.tolist(),input_std=xs.tolist(),output_mean=ym.tolist(),output_std=ys.tolist(),
        train_rollouts=sorted(map(int,set(groups[train]))),test_rollouts=sorted(map(int,set(groups[test]))),
        test_split_reused_diagnostic=True,gradient_gate=1e-5,head_lstsq_rcond=1e-10))
    trained={}; train_stats={}
    for label,name,prior in variants:
        w=initial.copy(); epochs=[]
        for epoch in range(12):
            max_grad=0.; error_sum=0.; iterations=0
            for i in np.flatnonzero(train):
                z,g,it=solve(w,target[i],name,prior)
                f=activation(z,name); error=target[i]-w.T@f
                w += .004*np.outer(f.conj(),error)
                assert np.isfinite(w).all()
                max_grad=max(max_grad,g); error_sum+=float(np.vdot(error,error).real)
                iterations+=it
            info=dict(variant=label,epoch=epoch+1,max_gradient=max_grad,
                      mean_reconstruction_squared_error=error_sum/int(train.sum()),
                      mean_iterations=iterations/int(train.sum()),elapsed_seconds=time.perf_counter()-start)
            epochs.append(info)
            with (args.output_dir/'progress.jsonl').open('a',encoding='utf-8') as file:
                file.write(json.dumps(info)+'\n')
            print(json.dumps(info),flush=True)
        trained[label]=w.copy()
        train_stats[label]=dict(epochs=epochs,weight_change_norm=float(np.linalg.norm(w-initial)),
                               initial_norm=float(np.linalg.norm(initial)),final_norm=float(np.linalg.norm(w)))
        np.savez(args.output_dir/(label+'.npz'),W=w)
    # All recipes trained before any test metric is evaluated. Freeze W_x/W_y.
    predictions={}; inference_stats={}; heads={}
    for label,name,prior in variants:
        w=trained[label]; before=w.tobytes(); features=[]; maximum=0.
        for i in range(len(x)):
            z,g,_=solve(w[:,:15],xn[i],name,prior)
            maximum=max(maximum,g); features.append(activation(z,name))
        features=np.array(features)
        head,_,rank,singular=np.linalg.lstsq(features[train],yn[train],rcond=1e-10)
        predictions[label]=(features@w[:,15:]).real*ys+ym
        predictions[label+'_conditional_head']=(features@head).real*ys+ym
        assert w.tobytes()==before
        inference_stats[label]=dict(max_gradient=maximum,all_converged=True,
                                   conditional_head_feature_rank=int(rank),
                                   largest_singular=float(singular[0]),smallest_singular=float(singular[-1]),
                                   frozen_parameters_unchanged=True)
        heads[label]=head
        print(json.dumps(dict(evaluated_features=label,max_gradient=maximum)),flush=True)
    linear,_,rank,_=np.linalg.lstsq(xn[train],yn[train],rcond=1e-10)
    predictions['direct_linear']=xn@linear*ys+ym
    predictions['persistence']=x[:,:5]
    baseline,bper=_mse(y[test],predictions['persistence'][test])
    metrics={}
    for label,pred in predictions.items():
        mse,per=_mse(y[test],pred[test])
        metrics[label]=dict(test_mse_rad2=mse,train_mse_rad2=_mse(y[train],pred[train])[0],
                           per_joint_mse_rad2=per,ratio_to_persistence=mse/baseline,
                           better_joints=sum(a<b for a,b in zip(per,bper)),
                           diagnostic_gate=mse<=.9*baseline and sum(a<b for a,b in zip(per,bper))>=4,
                           per_rollout_mse={str(g):_mse(y[groups==g],pred[groups==g])[0]
                                            for g in sorted(set(groups[test]))})
    np.savez(args.output_dir/'heads.npz',direct_linear=linear,**heads)
    np.savez(args.output_dir/'predictions.npz',**{k:v[test] for k,v in predictions.items()})
    result=dict(metrics=metrics,training=train_stats,inference=inference_stats,
                direct_linear_rank=int(rank),elapsed_seconds=time.perf_counter()-start)
    write(args.output_dir/'result.json',result)
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    main()
