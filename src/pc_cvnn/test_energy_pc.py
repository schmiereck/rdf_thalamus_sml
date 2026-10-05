"""Independent executable checks for the isolated energy backend; fails nonzero."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from energy_pc import EnergyPC, activation, pullback
from pc_engine_math_audit import negative_gradient, relative


def fingerprint(net):
    return hashlib.sha256(b''.join(e.weight.tobytes() for e in net.edges)).hexdigest()


def reference_energy(net):
    # Independent direct forward specification, not EnergyPC.terms/activation.
    total = 0.
    for key, state in net.mu.items():
        predictions = []
        for edge in net.edges:
            if edge.target == key:
                z = net.mu[edge.source]
                f = np.tanh(np.abs(z))*np.exp(1j*np.angle(z)) if net.spec[edge.source][1] == 'tanh' else z
                predictions.append(edge.weight.T @ f)
        p = np.mean(predictions, axis=0) if predictions else np.zeros_like(state)
        total += .5*float(np.sum(np.abs(state-p)**2))
    return total


def gradients():
    results = []
    for name, count, real in [('identity', 1, False), ('tanh', 1, False),
                               ('identity', 2, True), ('tanh', 1, True),
                               ('tanh', 2, False), ('relu', 2, False)]:
        for seed in (11, 17, 23):
            rng = np.random.default_rng(seed)
            def sample(shape):
                return rng.normal(size=shape) + (0 if real else 1j*rng.normal(size=shape))
            nodes = {str(i): (3, name) for i in range(count)}
            nodes['y'] = (2, 'identity')
            net = EnergyPC(nodes, [(str(i), 'y', .3*sample((3, 2))) for i in range(count)])
            for key in net.mu:
                net.mu[key] = sample(net.mu[key].shape).astype(complex)
            _, dz, dw = net.directions()
            state_errors, weight_errors = [], []
            for key in net.mu:
                old = net.mu[key].copy()
                def f(z):
                    net.mu[key] = z.copy()
                    return reference_energy(net)
                numeric = negative_gradient(f, old)
                net.mu[key] = old
                state_errors.append(relative(dz[key], numeric))
            for i, edge in enumerate(net.edges):
                old = edge.weight.copy()
                def f(w):
                    edge.weight = w.copy()
                    return reference_energy(net)
                numeric = negative_gradient(f, old)
                edge.weight = old
                weight_errors.append(relative(dw[i], numeric))
            error = max(state_errors + weight_errors)
            assert error < 1e-6, (name, seed, error)
            results.append(dict(activation=name, parents=count, real=real, seed=seed,
                                state_max=max(state_errors), weight_max=max(weight_errors)))
    return results


def lifecycle():
    net = EnergyPC({'z': (1, 'identity'), 'y': (1, 'identity')}, [('z', 'y', [[1j]])])
    net.clamp('y', [1])
    before = fingerprint(net)
    d = net.infer(max_steps=1, step_size=.1)
    assert abs(d['energies'][-1]-.41) < 1e-12
    assert np.array_equal(net.mu['y'], [1])
    assert fingerprint(net) == before
    net.edges[0].weight[:] = 100
    before = fingerprint(net)
    net.learn(0)
    assert fingerprint(net) == before
    states = copy.deepcopy(net.mu)
    net.commit_step()
    assert all(np.array_equal(net.mu[k], states[k]) for k in states)
    net.reset()
    assert fingerprint(net) == before and not net.clamped
    assert all(not np.any(z) for z in net.mu.values())
    # Sample reset removes target history; explicit clamps are owned copies.
    value = np.array([2j]); net.clamp('y', value); value[:] = 999
    assert np.array_equal(net.mu['y'], [2j])
    net.unclamp('y'); assert 'y' not in net.clamped
    net.mu['z'][:] = np.nan
    try:
        net.infer()
        raise AssertionError('Nonfinite state accepted')
    except FloatingPointError:
        assert np.isnan(net.mu['z']).any()
    for mode in ('frozen', 'learn'):
        try:
            EnergyPC({'x': (1, 'identity')}, [], temporal_mode=mode)
            raise AssertionError('Unsupported temporal mode accepted')
        except ValueError:
            pass
    return dict(counterexample_energy=d['energies'], clamp_held=True, inference_frozen=True,
                zero_rate_strict_freeze=True, reset_preserves_weights=True,
                reset_clears_clamps=True, temporal_off_noop=True,
                nonfinite_raises=True, unsupported_temporal_modes_rejected=True)


def controls():
    rng = np.random.default_rng(412)
    a = .2*(rng.normal(size=(3, 4))+1j*rng.normal(size=(3, 4)))
    b = .2*(rng.normal(size=(3, 2))+1j*rng.normal(size=(3, 2)))
    x = rng.normal(size=4)+1j*rng.normal(size=4)
    net = EnergyPC({'z': (3, 'identity'), 'x': (4, 'identity'), 'y': (2, 'identity')},
                   [('z', 'x', a), ('z', 'y', b)])
    net.clamp('x', x)
    diag = net.infer(max_steps=2000, tolerance=1e-9)
    z = np.linalg.solve(np.eye(3)+a.conj()@a.T, a.conj()@x)
    error = max(np.max(np.abs(net.mu['z']-z)), np.max(np.abs(net.mu['y']-b.T@z)))
    assert diag['converged'] and error < 1e-8
    assert np.max(np.diff(diag['energies'])) < 1e-12
    # Nonlinear known solution for W; clamped source isolates learning correctness.
    nonlinear = EnergyPC({'z': (3, 'tanh'), 'y': (2, 'identity')}, [('z', 'y', b*0)])
    for _ in range(2000):
        s = rng.normal(size=3)+1j*rng.normal(size=3)
        f = np.tanh(np.abs(s))*np.exp(1j*np.angle(s))
        nonlinear.clamp('z', s); nonlinear.clamp('y', b.T@f)
        nonlinear.learn(.03)
    mse = float(np.mean(np.abs(nonlinear.edges[0].weight-b)**2))
    assert mse < 1e-12
    nonlinear.reset(); nonlinear.clamp('y', [.2+.1j, -.1+.3j])
    nd = nonlinear.infer(max_steps=2000, tolerance=1e-9)
    assert nd['converged'] and np.max(np.diff(nd['energies'])) < 1e-12
    return dict(linear_closed_form_max_error=float(error), linear_steps=diag['steps'],
                nonlinear_weight_mse=mse, nonlinear_converged=True,
                nonlinear_gradient_max=nd['gradient_max'])


def boundary_and_graph_checks():
    # Origin, near-origin, saturation and mixed directions exercise the full real Jacobian.
    z = np.array([0, 1e-12+1e-12j, 1j, 1+2j, 30j])
    g = np.array([1j, 1-2j, 2, -.3+.2j, 1+1j])
    h = 1e-6
    numeric = (activation(z+h*g, 'tanh')-activation(z-h*g, 'tanh'))/(2*h)
    jvp_error = float(np.max(np.abs(pullback(z, g, 'tanh')-numeric)))
    assert jvp_error < 1e-8
    # Cyclic graph and a self-loop: a node receives errors AND sends predictions.
    rng = np.random.default_rng(66)
    w = lambda: .1*(rng.normal(size=(2,2))+1j*rng.normal(size=(2,2)))
    weights = [w(), w(), w()]
    net = EnergyPC({'a': (2,'tanh'), 'b': (2,'identity')},
                   [('a','b',weights[0]), ('b','a',weights[1]), ('a','a',weights[2])])
    for key in net.mu:
        net.mu[key] = rng.normal(size=2)+1j*rng.normal(size=2)
    _, dz, _ = net.directions()
    errors=[]
    for key in net.mu:
        old=net.mu[key].copy()
        def f(v):
            net.mu[key]=v.copy()
            return reference_energy(net)
        numeric=negative_gradient(f,old)
        net.mu[key]=old
        errors.append(relative(dz[key],numeric))
    assert max(errors)<1e-6
    # Reset makes an identical probe independent of prior clamps/targets and state.
    def predict():
        net.reset(); net.clamp('b',[.3,.2j]); net.infer()
        return net.mu['a'].copy()
    first=predict()
    net.clamp('a',[100,100]); net.clamp('b',[-100,-100]); net.infer()
    second=predict()
    assert np.array_equal(first,second)
    assert all(np.array_equal(e.weight, original) for e,original in zip(net.edges,weights))
    # Large starting step must backtrack rather than increase energy.
    net.reset(); net.clamp('b',[2,3])
    trace=net.infer(step_size=100, max_steps=1000)
    assert trace['backtracks']>0 and trace['converged']
    assert max(np.diff(trace['energies']))<1e-10
    return dict(tanh_jvp_max_error=jvp_error, cyclic_gradient_max=max(errors),
                history_independent_prediction=True, caller_weights_unchanged=True,
                large_step_backtracks=trace['backtracks'])


def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = dict(gradients=gradients(), lifecycle=lifecycle(), controls=controls(),
                  boundaries=boundary_and_graph_checks(), passed=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
