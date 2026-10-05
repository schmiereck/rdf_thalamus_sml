"""Frozen S1 evaluation on new complete trajectory sets; never fits any parameters."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pc_cvnn.servo_latent import FrozenServoPredictor, position_from_latent, unpack_complex, HORIZON_SECONDS
from act23_s1_pc_forward_audit import _arrays, _mse


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,default=Path('log/s1-online-readout-20261003/model.npz'))
    p.add_argument('--data-root',type=Path,default=Path('log/s1-independent-20261003'))
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    model=FrozenServoPredictor(args.checkpoint); before=model.fingerprint()
    with np.load(args.checkpoint,allow_pickle=False) as saved:
        batch=saved['batch_reference']
    old_rows=[json.loads(line) for line in Path('log/s1-proprio/seed101-50x60-safe/transitions.jsonl').read_text(encoding='utf-8').splitlines()]
    old_x,_,_,old_split=_arrays(old_rows)
    lower,upper=old_x[old_split=='train'].min(0),old_x[old_split=='train'].max(0)
    sources={}; groups={}; all_y=[]; all_p=[]; all_b=[]; all_q=[]
    for seed in (211,307):
        folder=args.data_root/f'seed{seed}'
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        assert manifest['seed']==seed and manifest['evaluation_only']
        assert manifest['rows']==1200 and manifest['rollouts']==20 and manifest['transitions_per_rollout']==60
        assert abs(manifest['transition_seconds']-HORIZON_SECONDS)<1e-12
        assert manifest['transition_steps']==10 and manifest['max_delta_rad']==.025
        for key in ('pressure_sensor_used','teacher_or_ik_used','object_or_contact_observed'):
            assert manifest[key] is False
        data=folder/'transitions.jsonl'
        rows=[json.loads(line) for line in data.read_text(encoding='utf-8').splitlines()]
        x,y,rollout,split=_arrays(rows)
        assert len(rows)==1200 and np.all(split=='test') and len(set(rollout))==20
        for group in sorted(set(rollout)):
            rr=[row for row in rows if row['rollout_id']==group]
            assert [r['step_id'] for r in rr]==list(range(60))
            assert all(a['q_next_rad']==b['q_rad'] and a['qvel_next_rad_s']==b['qvel_rad_s']
                       for a,b in zip(rr,rr[1:]))
        assert np.isfinite(x).all() and np.isfinite(y).all()
        assert np.all(x[:,:5]>=manifest['observation_low_rad']) and np.all(x[:,:5]<=manifest['observation_high_rad'])
        assert np.all(y>=manifest['observation_low_rad']) and np.all(y<=manifest['observation_high_rad'])
        pred=[]; bpred=[]; pos=[]; features=[]; residuals=[]
        for xx in x:
            result=model.infer(xx[:5],xx[5:10],xx[10:])
            pred.append(result['predicted_q_rad']); pos.append(result['position_latent'])
            f=unpack_complex(result['transition_latent']); features.append(result['transition_latent'])
            bpred.append((batch.T@f).real*model.output_std+model.output_mean)
            residuals.append(result['gradient_max'])
        pred,bpred,pos=np.array(pred),np.array(bpred),np.array(pos)
        decoded=np.array([position_from_latent(packed) for packed in pos])
        roundtrip=float(np.max(np.abs(decoded-x[:,:5])))
        assert roundtrip<1e-12
        metrics={}
        base,bper=_mse(y,x[:,:5])
        for label,estimate in [('online',pred),('batch',bpred),('persistence',x[:,:5])]:
            mse,per=_mse(y,estimate)
            metrics[label]=dict(mse_rad2=mse,per_joint_mse_rad2=per,ratio_to_persistence=mse/base,
                               better_joints=sum(a<b for a,b in zip(per,bper)),
                               gate=mse<=.9*base and sum(a<b for a,b in zip(per,bper))>=4)
        metrics['diagnostics']=dict(max_gradient=max(residuals),position_roundtrip_rad=roundtrip,
                  input_outside_old_training_range_per_column=np.sum((x<lower)|(x>upper),axis=0).tolist(),
                  per_rollout_online_mse={str(g):_mse(y[rollout==g],pred[rollout==g])[0] for g in sorted(set(rollout))},
                  per_rollout_persistence_mse={str(g):_mse(y[rollout==g],x[rollout==g,:5])[0] for g in sorted(set(rollout))})
        np.savez(args.output_dir/f'seed{seed}.npz',prediction=pred,batch=bpred,
                 position_latent=pos,transition_latent=np.array(features),rollout=rollout)
        sources[str(seed)]=hashlib.sha256(data.read_bytes()).hexdigest()
        groups[str(seed)]=metrics
        all_y.append(y); all_p.append(pred); all_b.append(bpred); all_q.append(x[:,:5])
        print(json.dumps(dict(seed=seed,online=metrics['online'])),flush=True)
    y,pred,bpred,q=map(np.concatenate,(all_y,all_p,all_b,all_q))
    base,bper=_mse(y,q); pooled={}
    for label,estimate in [('online',pred),('batch',bpred),('persistence',q)]:
        mse,per=_mse(y,estimate)
        pooled[label]=dict(mse_rad2=mse,per_joint_mse_rad2=per,ratio_to_persistence=mse/base,
                           better_joints=sum(a<b for a,b in zip(per,bper)),
                           gate=mse<=.9*base and sum(a<b for a,b in zip(per,bper))>=4)
    assert model.fingerprint()==before
    assert hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()==model.model_id
    result=dict(model_sha256=model.model_id,encoder_id=model.encoder_id,source_sha256=sources,
                seeds=groups,pooled=pooled,rows=2400,horizon_seconds=HORIZON_SECONDS,
                parameter_freeze=True,all_new_rows_test_only=True,
                overall_gate=pooled['online']['gate'] and all(v['online']['gate'] for v in groups.values()))
    (args.output_dir/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(pooled,indent=2))


if __name__=='__main__':
    main()
