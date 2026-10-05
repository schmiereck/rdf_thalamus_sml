"""Post-run leakage/replay and shuffled-label controls for the S1 objective audit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from act23_s1_objective_audit import solve
from act23_s1_pc_forward_audit import _arrays, _rows, _mse
from energy_pc import activation


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest=json.loads((args.run_dir/'manifest.json').read_text(encoding='utf-8'))
    source=Path(manifest['source'])
    assert hashlib.sha256((source/'transitions.jsonl').read_bytes()).hexdigest()==manifest['data_sha256']
    rows=_rows(source); x,y,groups,split=_arrays(rows)
    train,test=split=='train',split=='test'
    for group in np.unique(groups):
        rr=[r for r in rows if r['rollout_id']==group]
        assert [r['step_id'] for r in rr]==list(range(60))
        assert all(a['q_next_rad']==b['q_rad'] and a['qvel_next_rad_s']==b['qvel_rad_s']
                   for a,b in zip(rr,rr[1:]))
    poisoned=copy.deepcopy(rows)
    for row in poisoned:
        row['qvel_next_rad_s']=[999.]*5
        if row['split']=='test':
            row['q_next_rad']=[-999.]*5
    px,py,_,_=_arrays(poisoned)
    assert np.array_equal(px,x) and np.array_equal(py[train],y[train])
    xm,xs=np.array(manifest['input_mean']),np.array(manifest['input_std'])
    ym,ys=np.array(manifest['output_mean']),np.array(manifest['output_std'])
    assert np.array_equal(xm,x[train].mean(0)) and np.array_equal(xs,x[train].std(0))
    assert np.array_equal(ym,y[train].mean(0)) and np.array_equal(ys,y[train].std(0))
    xn,yn=(px-xm)/xs,(y-ym)/ys
    pyn=(py-ym)/ys
    paths=[args.run_dir/name for name in ('tanh_prior1.npz','heads.npz','predictions.npz')]
    before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    with np.load(paths[0],allow_pickle=False) as saved:
        w=saved['W']
    features=[]
    for xx in xn:
        z,_,_=solve(w[:,:15],xx,'tanh',1.)
        features.append(activation(z,'tanh'))
    features=np.array(features)
    original=np.linalg.lstsq(features[train],yn[train],rcond=1e-10)[0]
    poison_head=np.linalg.lstsq(features[train],pyn[train],rcond=1e-10)[0]
    assert np.array_equal(original,poison_head)
    pred=(features[test]@poison_head).real*ys+ym
    with np.load(paths[1],allow_pickle=False) as saved:
        head_difference=float(np.max(np.abs(original-saved['tanh_prior1'])))
    with np.load(paths[2],allow_pickle=False) as saved:
        replay_difference=float(np.max(np.abs(pred-saved['tanh_prior1_conditional_head'])))
    assert head_difference<1e-10 and replay_difference<1e-10
    rng=np.random.default_rng(918)
    shuffled=np.linalg.lstsq(features[train],rng.permutation(yn[train]),rcond=1e-10)[0]
    shuffled_mse=_mse(y[test],(features[test]@shuffled).real*ys+ym)[0]
    correct_mse=_mse(y[test],pred)[0]
    assert shuffled_mse>correct_mse*100
    assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    result=dict(passed=True,test_target_poison_changes_inputs=False,
                test_target_poison_changes_head=False,normalization_training_only=True,
                trajectory_continuity=True,checkpoint_files_unchanged=True,
                replay_max_difference_rad=replay_difference,head_max_difference=head_difference,
                correct_mse_rad2=correct_mse,shuffled_training_targets_mse_rad2=shuffled_mse,
                shuffle_seed=918)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
