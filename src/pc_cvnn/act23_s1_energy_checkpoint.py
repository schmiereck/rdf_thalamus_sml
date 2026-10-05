"""Frozen S1 solver cross-check: exactly eliminate the free output leaf.

For fixed z its unique optimum is y=W_y.T f(z). Substitution leaves
E(z)=.5||z||² + .5||x-W_x.T f(z)||². Same trained weights and objective,
no labels in the solver, no retraining or model selection.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize

from act23_s1_pc_forward_audit import _arrays, _rows, _mse
from energy_pc import activation, pullback
from pc_engine_math_audit import negative_gradient, relative


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((args.checkpoint_dir/'manifest.json').read_text(encoding='utf-8'))
    source=Path(manifest['source'])
    assert hashlib.sha256((source/'transitions.jsonl').read_bytes()).hexdigest()==manifest['data_sha256']
    x,y,groups,split=_arrays(_rows(source)); test=split=='test'
    norm=manifest['normalization']
    active=np.array(norm['input_active'])
    xs=np.where(active,norm['input_std'],1.)
    xn=np.where(active,(x-norm['input_mean'])/xs,0.)
    ym=np.array(norm['target_mean']); ys=np.maximum(norm['target_std'],1e-6)
    checkpoint=args.checkpoint_dir/'weights.npz'
    before=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    with np.load(checkpoint,allow_pickle=False) as data:
        wx,wy=data['W0'],data['W1']
    dim=wx.shape[0]
    predictions=[]; diagnostics=[]; derivative_error=None
    for index in np.flatnonzero(test):
        xx=xn[index]
        def complex_objective(z):
            error=wx.T@activation(z,'tanh')-xx
            energy=.5*float(np.vdot(z,z).real+np.vdot(error,error).real)
            grad=z+pullback(z,wx.conj()@error,'tanh')
            return energy,grad
        if derivative_error is None:
            z=np.full(dim,.1+.2j)
            numeric=-negative_gradient(lambda v:complex_objective(v)[0],z)
            derivative_error=relative(complex_objective(z)[1],numeric)
            assert derivative_error<1e-6
        def objective(v):
            value,grad=complex_objective(v[:dim]+1j*v[dim:])
            return value,np.concatenate([grad.real,grad.imag])
        result=minimize(objective,np.zeros(2*dim),jac=True,method='L-BFGS-B',
                        options=dict(maxiter=2048,gtol=1e-9,ftol=1e-15,maxls=40))
        z=result.x[:dim]+1j*result.x[dim:]
        energy,grad=complex_objective(z)
        residual=float(np.max(np.abs(grad)))
        assert residual<1e-5, ('Unresolved inference',index,residual)
        predictions.append((wy.T@activation(z,'tanh')).real*ys+ym)
        diagnostics.append(dict(index=int(index),gradient_max=residual,energy=energy,
                                iterations=int(result.nit),optimizer_success=bool(result.success)))
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==before
    predictions=np.array(predictions)
    mse,per=_mse(y[test],predictions); base,bper=_mse(y[test],x[test,:5])
    with np.load(args.checkpoint_dir/'predictions.npz',allow_pickle=False) as saved:
        difference=float(np.max(np.abs(predictions-saved['refined'])))
    result=dict(scipy_version=scipy.__version__,checkpoint_file_sha256=before,
                derivative_relative_error=derivative_error,
                mse_rad2=mse,per_joint_mse_rad2=per,ratio_to_persistence=mse/base,
                better_joints=sum(a<b for a,b in zip(per,bper)),
                max_difference_from_refined_rad=difference,
                max_gradient=max(d['gradient_max'] for d in diagnostics),
                converged_1e5=sum(d['gradient_max']<1e-5 for d in diagnostics),
                converged_1e7=sum(d['gradient_max']<1e-7 for d in diagnostics),
                optimizer_successes=sum(d['optimizer_success'] for d in diagnostics),
                checkpoint_unchanged=True,diagnostics=diagnostics)
    (args.output_dir/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    np.savez(args.output_dir/'predictions.npz',prediction=predictions)
    print(json.dumps({k:v for k,v in result.items() if k!='diagnostics'},indent=2))


if __name__=='__main__':
    main()
