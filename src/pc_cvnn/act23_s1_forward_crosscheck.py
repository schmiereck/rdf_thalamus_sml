"""Forensic checks of the frozen S1 recipe; no controller or engine edits."""
import copy
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from act23_s1_pc_forward_audit import PCForward, _rows, _arrays


def weights(model):
    arrays = [c.W for c in model.net._connections]
    arrays += [n.V for n in model.net._nodes.values()]
    return hashlib.sha256(b''.join(a.tobytes() for a in arrays)).hexdigest()


def evaluate(model, x, y, groups, mean, std, commit=False, read_pi=False):
    model = copy.deepcopy(model)
    before = weights(model)
    predictions = []
    previous = None
    for xx, group in zip(x, groups):
        if group != previous:
            model.reset()
        previous = group
        pred = model.predict(xx)
        if read_pi:
            pred = model.next_q.pi.real.copy()
        predictions.append(pred * std + mean)
        if commit:
            model.net.commit_step()
    assert weights(model) == before, 'evaluation mutated weights'
    return float(np.mean((np.array(predictions) - y) ** 2))


def main():
    start = time.perf_counter()
    source = Path('log/s1-proprio/seed101-50x60-safe')
    rows = _rows(source)
    x, y, groups, split = _arrays(rows)
    train, test = split == 'train', split == 'test'
    assert len(set(groups[train])) == 40 and len(set(groups[test])) == 10
    assert not set(groups[train]) & set(groups[test])
    for g in np.unique(groups):
        rr = [r for r in rows if r['rollout_id'] == g]
        assert [r['step_id'] for r in rr] == list(range(60))
        for a, b in zip(rr, rr[1:]):
            assert a['q_next_rad'] == b['q_rad']
            assert a['qvel_next_rad_s'] == b['qvel_rad_s']
    xm, xs = x[train].mean(0), x[train].std(0)
    ym, ys = y[train].mean(0), y[train].std(0)
    xn, yn = (x-xm)/xs, (y-ym)/ys
    model = PCForward(15, 5, 24, 17)
    initial = weights(model)
    for epoch in range(12):
        for g in sorted(set(groups[train])):
            model.reset()
            for i in np.flatnonzero((groups == g) & train):
                model.train_row(xn[i], yn[i])
    assert weights(model) != initial
    before = weights(model)
    model.reset()
    assert weights(model) == before
    # No test targets enter evaluate's inference calls.
    results = {}
    for commit in (False, True):
        for pi in (False, True):
            key = f'commit_{commit}_read_' + ('pi' if pi else 'mu')
            results[key] = evaluate(model, xn[test], y[test], groups[test], ym, ys, commit, pi)
    probe = copy.deepcopy(model)
    probe.reset()
    a = probe.predict(xn[test][0])
    b = probe.predict(xn[test][0])
    repeat_diff = float(np.max(np.abs(a-b)))
    # Synthetic identity: same PC recipe, 40 training / 10 test groups of 60 samples.
    rng = np.random.default_rng(421)
    sx = rng.normal(size=(3000, 15))
    sy = sx[:, :5].copy()
    sm = PCForward(15, 5, 24, 17)
    for epoch in range(12):
        for g in sorted(set(groups[train])):
            sm.reset()
            for i in np.flatnonzero((groups == g) & train):
                sm.train_row(sx[i], sy[i])
    synthetic = evaluate(sm, sx[test], sy[test], groups[test], 0., 1.)
    # A finite-difference check of complex error pressure at identity activation.
    c = model.net._connections[0]
    w = c.W.copy()
    z = rng.normal(size=24) + 1j*rng.normal(size=24)
    target = rng.normal(size=15) + 1j*rng.normal(size=15)
    error = target - w.T @ z
    def energy(zz):
        return .5 * float(np.sum(np.abs(target - w.T @ zz)**2))
    h = 1e-6
    numeric = np.empty(24, complex)
    for i in range(24):
        e = np.zeros(24, complex); e[i] = h
        real = -(energy(z+e)-energy(z-e))/(2*h)
        imag = -(energy(z+1j*e)-energy(z-1j*e))/(2*h)
        numeric[i] = real + 1j*imag
    result = dict(data_sha256=hashlib.sha256((source/'transitions.jsonl').read_bytes()).hexdigest(),
                  recipe_mse=results, synthetic_identity_mse=synthetic,
                  synthetic_zero_mse=float(np.mean(sy[test]**2)),
                  persistence_mse=float(np.mean((x[test,:5]-y[test])**2)),
                  reset_preserves_weights=True, evaluation_preserves_weights=True,
                  repeated_prediction_max_difference=repeat_diff,
                  pressure_gradient_relative_error=float(np.linalg.norm(w@error-numeric)/np.linalg.norm(numeric)),
                  conjugate_pressure_relative_error=float(np.linalg.norm(w.conj()@error-numeric)/np.linalg.norm(numeric)),
                  elapsed_seconds=time.perf_counter()-start)
    output = Path('log/s1-forward-crosscheck-20261002')
    output.mkdir(exist_ok=False)
    (output/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
