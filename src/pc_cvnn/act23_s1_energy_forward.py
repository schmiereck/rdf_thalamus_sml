"""Fixed S1 re-evaluation with isolated energy inference; no simulator or PKL.

The historical test split is reused for diagnosis, not a new generalization claim.
No hyperparameter selection: seed17, 24 latent units, 12 epochs, learning rate .004.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from act23_s1_pc_forward_audit import PCForward, _arrays, _rows, _mse
from energy_pc import EnergyPC
from test_energy_pc import fingerprint


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def normalization(values):
    mean, std = values.mean(0), values.std(0)
    active = std >= 1e-6
    return mean, np.where(active, std, 1.), active, std


def summarize(diags):
    return dict(samples=len(diags), converged=sum(d['converged'] for d in diags),
                max_gradient=max(d['gradient_max'] for d in diags),
                mean_steps=float(np.mean([d['steps'] for d in diags])),
                max_energy_increase=max(max(np.diff(d['energies']), default=0.) for d in diags),
                backtracks=sum(d['backtracks'] for d in diags))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, default=Path('log/s1-proprio/seed101-50x60-safe'))
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    rows = _rows(args.source)
    x, y, groups, split = _arrays(rows)
    train, test = split == 'train', split == 'test'
    assert np.isfinite(x).all() and np.isfinite(y).all()
    assert train.sum() == 2400 and test.sum() == 600
    assert len(set(groups[train])) == 40 and len(set(groups[test])) == 10
    assert not set(groups[train]) & set(groups[test])
    for g in np.unique(groups):
        rr = [r for r in rows if r['rollout_id'] == g]
        assert [r['step_id'] for r in rr] == list(range(60))
        assert all(a['q_next_rad'] == b['q_rad'] and a['qvel_next_rad_s'] == b['qvel_rad_s']
                   for a, b in zip(rr, rr[1:]))
    xm, xs, active, raw_xs = normalization(x[train])
    ym, ys, _, raw_ys = normalization(y[train])
    xn = np.where(active, (x-xm)/xs, 0.)
    yn = (y-ym)/ys
    # Identical W seed and layout to historical S1; no legacy inference is called.
    original = PCForward(15, 5, 24, 17)
    specs = {'s1_context': (15, 'identity'), 's1_next_q': (5, 'identity'),
             's1_latent': (24, 'tanh')}
    net = EnergyPC(specs, [(c.source.id, c.target.id, c.W) for c in original.net._connections])
    del original
    recipe = dict(seed=17, latent_dim=24, epochs=12, learning_rate=.004,
                  inference_steps=128, inference_rate=.08, gradient_tolerance=1e-5,
                  refinement_steps=2048, refinement_tolerance=1e-7,
                  temporal='off', fresh_zero_state_each_sample=True,
                  clipping=False, decay=False, top_prior_precision=1.,
                  gain_factors='unit', training_only_normalization=True,
                  test_split_reused_diagnostic=True,
                  gate_ratio=.90, gate_better_joints=4)
    hashes = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
              for name in ('energy_pc.py', 'act23_s1_energy_forward.py', 'test_energy_pc.py',
                           'node.py', 'connection.py', 'network.py', 'relax_vec.py')}
    write(args.output_dir/'manifest.json', dict(recipe=recipe, source=str(args.source),
          data_sha256=hashlib.sha256((args.source/'transitions.jsonl').read_bytes()).hexdigest(),
          code_sha256=hashes, initial_weights_sha256=fingerprint(net),
          normalization=dict(input_mean=xm.tolist(), input_std=raw_xs.tolist(),
                             input_active=active.tolist(), target_mean=ym.tolist(),
                             target_std=raw_ys.tolist()),
          train_rollouts=sorted(map(int,set(groups[train]))),
          test_rollouts=sorted(map(int,set(groups[test])))))
    epoch_stats = []
    for epoch in range(12):
        diags = []
        for i in np.flatnonzero(train):
            net.reset()
            net.clamp('s1_context', xn[i]); net.clamp('s1_next_q', yn[i])
            d = net.infer()
            net.learn(.004)
            diags.append(d)
        stats = dict(epoch=epoch+1, elapsed_seconds=time.perf_counter()-start, **summarize(diags))
        epoch_stats.append(stats)
        with (args.output_dir/'progress.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(stats)+'\n')
        print(json.dumps(stats), flush=True)
    np.savez(args.output_dir/'weights.npz', **{f'W{i}': e.weight for i,e in enumerate(net.edges)})
    frozen = fingerprint(net)
    predictions, refined_predictions, diags, refined_diags = [], [], [], []
    for i in np.flatnonzero(test):
        net.reset(); net.clamp('s1_context', xn[i])
        diags.append(net.infer())
        predictions.append(net.mu['s1_next_q'].real.copy()*ys+ym)
        # Predeclared convergence diagnostic on the same frozen checkpoint, not tuning.
        refined_diags.append(net.infer(max_steps=2048, tolerance=1e-7))
        refined_predictions.append(net.mu['s1_next_q'].real.copy()*ys+ym)
    assert fingerprint(net) == frozen
    predictions, refined_predictions = np.array(predictions), np.array(refined_predictions)
    baseline = _mse(y[test], x[test,:5])
    metrics = {}
    for label, pred in [('energy_pc_128', predictions), ('energy_pc_refined', refined_predictions),
                        ('persistence', x[test,:5]), ('constant', np.broadcast_to(ym, y[test].shape))]:
        mse, per = _mse(y[test], pred)
        metrics[label] = dict(mse_rad2=mse, per_joint_mse_rad2=per,
                             ratio_to_persistence=mse/baseline[0],
                             better_joints=sum(a<b for a,b in zip(per,baseline[1])))
    by_rollout = []
    for g in sorted(set(groups[test])):
        mask = groups[test] == g
        by_rollout.append(dict(rollout=int(g), pc_mse=_mse(y[test][mask], refined_predictions[mask])[0],
                               persistence_mse=_mse(y[test][mask], x[test][mask,:5])[0]))
    np.savez(args.output_dir/'predictions.npz', test_indices=np.flatnonzero(test),
             prediction=predictions, refined=refined_predictions)
    primary = metrics['energy_pc_128']
    result = dict(recipe=recipe, metrics=metrics, training=epoch_stats,
                  inference=summarize(diags), refined_inference=summarize(refined_diags),
                  evaluation_preserves_weights=True, final_weights_sha256=frozen,
                  inactive_input_columns=np.flatnonzero(~active).tolist(),
                  max_refinement_change_rad=float(np.max(np.abs(predictions-refined_predictions))),
                  per_rollout=by_rollout,
                  primary_performance_gate=primary['ratio_to_persistence'] <= .9 and primary['better_joints'] >= 4,
                  elapsed_seconds=time.perf_counter()-start)
    write(args.output_dir/'result.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
