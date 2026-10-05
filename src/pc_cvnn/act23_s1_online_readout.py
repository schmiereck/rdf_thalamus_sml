"""Conditional complex readout: local sequential updates on a frozen S1 encoder."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from act23_s1_objective_audit import solve
from act23_s1_pc_forward_audit import PCForward, _arrays, _rows, _mse
from energy_pc import activation
from pc_engine_math_audit import negative_gradient, relative


class OnlineReadout:
    def __init__(self, weights):
        self.weights=np.array(weights,dtype=complex,copy=True)

    def predict(self, feature):
        return self.weights.T@feature

    def update(self, feature, target, rate=.004):
        if not np.isfinite(rate) or rate<0:
            raise ValueError('Invalid rate')
        if rate==0:
            return
        error=target-self.predict(feature)
        candidate=self.weights+rate*np.outer(np.conj(feature),error)
        if not np.isfinite(candidate).all():
            raise FloatingPointError('Nonfinite readout update; weights unchanged')
        self.weights=candidate


def controls():
    rng=np.random.default_rng(713)
    w=.2*(rng.normal(size=(4,2))+1j*rng.normal(size=(4,2)))
    f=rng.normal(size=4)+1j*rng.normal(size=4)
    y=rng.normal(size=2)+1j*rng.normal(size=2)
    original=w.copy()
    net=OnlineReadout(w)
    numeric=negative_gradient(lambda v:.5*np.sum(np.abs(y-v.T@f)**2),w)
    net.update(f,y,1e-5)
    gradient_error=relative((net.weights-w)/1e-5,numeric)
    assert gradient_error<1e-6
    before=net.weights.tobytes(); net.predict(f); net.update(f,y,0)
    assert net.weights.tobytes()==before
    assert np.array_equal(w,original)
    known=OnlineReadout(np.zeros_like(w))
    for _ in range(3000):
        feature=rng.normal(size=4)+1j*rng.normal(size=4)
        known.update(feature,w.T@feature,.02)
    mse=float(np.mean(np.abs(known.weights-w)**2))
    assert mse<1e-12
    return dict(actual_update_gradient_error=gradient_error,known_mapping_weight_mse=mse,
                predict_and_zero_rate_preserve_weights=True)


def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--encoder-run',type=Path,default=Path('log/s1-objective-20261003'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    write(args.output_dir/'controls.json',controls())
    old=json.loads((args.encoder_run/'manifest.json').read_text(encoding='utf-8'))
    source=Path(old['source']); rows=_rows(source)
    assert hashlib.sha256((source/'transitions.jsonl').read_bytes()).hexdigest()==old['data_sha256']
    x,y,groups,split=_arrays(rows); train,test=split=='train',split=='test'
    assert train.sum()==2400 and test.sum()==600
    assert len(set(groups[train]))==40 and len(set(groups[test]))==10
    assert not set(groups[train]) & set(groups[test])
    xm,xs=np.array(old['input_mean']),np.array(old['input_std'])
    ym,ys=np.array(old['output_mean']),np.array(old['output_std'])
    for actual,expected in [(xm,x[train].mean(0)),(xs,x[train].std(0)),
                            (ym,y[train].mean(0)),(ys,y[train].std(0))]:
        assert np.array_equal(actual,expected)
    xn,yn=(x-xm)/xs,(y-ym)/ys
    checkpoint=args.encoder_run/'tanh_prior1.npz'
    encoder_hash=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    with np.load(checkpoint,allow_pickle=False) as stored:
        w=stored['W']
    w_before=w.tobytes()
    original=PCForward(15,5,24,17)
    model=OnlineReadout(original.net._connections[1].W)
    initial=model.weights.copy(); del original
    write(args.output_dir/'manifest.json',dict(
        schema='s1-online-readout-v1',encoder_run=str(args.encoder_run),encoder_file_sha256=encoder_hash,
        data_sha256=old['data_sha256'],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        initial_head_sha256=hashlib.sha256(initial.tobytes()).hexdigest(),seed=17,epochs=12,learning_rate=.004,
        sequential_replay=True,temporal='off',encoder_frozen=True,batch_initialization=False,
        train_rollouts=sorted(map(int,set(groups[train]))),test_rollouts=sorted(map(int,set(groups[test]))),
        test_split_reused_diagnostic=True))
    features=[]; max_gradient=0.
    for index,xx in enumerate(xn):
        z,g,_=solve(w[:,:15],xx,'tanh',1.)
        features.append(activation(z,'tanh')); max_gradient=max(max_gradient,g)
        if (index+1)%600==0:
            print(json.dumps(dict(features=index+1,elapsed_seconds=time.perf_counter()-start)),flush=True)
    features=np.array(features)
    # Recompute batch reference only from training, never install it in the online head.
    batch=np.linalg.lstsq(features[train],yn[train],rcond=1e-10)[0]
    with np.load(args.encoder_run/'heads.npz',allow_pickle=False) as saved:
        assert np.array_equal(batch,saved['tanh_prior1'])
    history=[]
    initial_train_mse=_mse(y[train],(features[train]@initial).real*ys+ym)[0]
    for epoch in range(12):
        for i in np.flatnonzero(train):
            model.update(features[i],yn[i])
        info=dict(epoch=epoch+1,train_mse_rad2=_mse(y[train],(features[train]@model.weights).real*ys+ym)[0],
                  complex_training_loss=float(.5*np.mean(np.sum(np.abs(yn[train]-features[train]@model.weights)**2,axis=1))),
                  elapsed_seconds=time.perf_counter()-start)
        history.append(info)
        with (args.output_dir/'progress.jsonl').open('a',encoding='utf-8') as file:
            file.write(json.dumps(info)+'\n')
        print(json.dumps(info),flush=True)
    frozen=model.weights.tobytes()
    predictions={label:(features[test]@head).real*ys+ym for label,head in
                 [('online',model.weights),('initial',initial),('batch',batch),('generative',w[:,15:])]}
    predictions['persistence']=x[test,:5]
    baseline,bper=_mse(y[test],predictions['persistence'])
    metrics={}
    for label,pred in predictions.items():
        mse,per=_mse(y[test],pred)
        metrics[label]=dict(mse_rad2=mse,per_joint_mse_rad2=per,ratio_to_persistence=mse/baseline,
                           better_joints=sum(a<b for a,b in zip(per,bper)),
                           gate=mse<=.9*baseline and sum(a<b for a,b in zip(per,bper))>=4,
                           per_rollout_mse={str(g):_mse(y[test][groups[test]==g],pred[groups[test]==g])[0]
                                            for g in sorted(set(groups[test]))})
    assert model.weights.tobytes()==frozen and w.tobytes()==w_before
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==encoder_hash
    with np.load(args.encoder_run/'predictions.npz',allow_pickle=False) as saved:
        assert np.array_equal(predictions['batch'],saved['tanh_prior1_conditional_head'])
    np.savez(args.output_dir/'model.npz',encoder=w[:,:15],online_head=model.weights,
             initial_head=initial,batch_reference=batch,input_mean=xm,input_std=xs,output_mean=ym,output_std=ys)
    np.savez(args.output_dir/'predictions.npz',**predictions)
    result=dict(metrics=metrics,training=history,initial_train_mse_rad2=initial_train_mse,
                max_encoder_gradient=max_gradient,encoder_unchanged=True,evaluation_preserves_head=True,
                batch_reference_bitwise_reproduced=True,
                online_vs_batch_mse_ratio=metrics['online']['mse_rad2']/metrics['batch']['mse_rad2'],
                elapsed_seconds=time.perf_counter()-start)
    write(args.output_dir/'result.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
