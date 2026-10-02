"""Independent numerical specification audit, without changing the production engine.

Reference energy: .5 sum_node |mu - mean(incoming W.T f(mu_source))|**2.
Top nodes have zero prediction. Unit alpha/beta/gamma, no decay/clipping for gradients.
Known failures are reported as failures, not converted into passing regression tests.
"""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.node import PCNode, SensorNode, _mod_tanh, _mod_relu
from pc_cvnn.network import PCNetwork
from pc_cvnn.relax_vec import RelaxPlan


def negative_gradient(fun, value, h=1e-6):
    result = np.zeros_like(value, dtype=complex)
    for index in np.ndindex(value.shape):
        e = np.zeros_like(value, dtype=complex)
        e[index] = h
        result[index] = -(fun(value+e)-fun(value-e))/(2*h)
        result[index] -= 1j*(fun(value+1j*e)-fun(value-1j*e))/(2*h)
    return result


def relative(a, b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b), 1e-12))


def radial_tanh_pullback(z, g):
    """Real 2D Jacobian transpose, including the continuous value at zero."""
    r=np.abs(z)
    tangent=np.divide(np.tanh(r),r,out=np.ones_like(r),where=r>0)
    projection=np.divide(np.real(z.conj()*g),r*r,out=np.zeros_like(r),where=r>0)
    return tangent*g + (1-np.tanh(r)**2-tangent)*z*projection


def refresh(net):
    # Hierarchical predictions only: deliberately no temporal warm start.
    for c in net._connections:
        c.predict()
    for n in net._nodes.values():
        n.finalize_prediction()
        n.compute_error()


def energy(net):
    refresh(net)
    return .5*sum(float(np.sum(np.abs(n.epsilon)**2)) for n in net._nodes.values())


def graph(activation, parents, seed, real=False):
    rng = np.random.default_rng(seed)
    net = PCNetwork(alpha=1, beta=1, gamma=1, eta_temporal=0,
                    eta_learn=1e-5, w_clip=0, rng=rng)
    net._plan = None
    sensor = net.add(SensorNode('y', 2))
    for i in range(parents):
        src = net.add(PCNode(str(i), 3, activation=activation, rng=rng))
        src.mu = rng.normal(size=3) + (0 if real else 1j*rng.normal(size=3))
        c = net.connect(str(i), 'y')
        c.W = .3*(rng.normal(size=(3, 2)) + (0 if real else 1j*rng.normal(size=(3, 2))))
        c.W = c.W.astype(complex)
    sensor.set_input(rng.normal(size=2) + (0 if real else 1j*rng.normal(size=2)))
    net._plan = None
    return net


def gradient_cases():
    cases = []
    for activation, parents, real in [('identity',1,False), ('tanh',1,False),
                                      ('identity',2,True), ('tanh',1,True)]:
        for seed in (11,17,23):
            net = graph(activation, parents, seed, real)
            node, conn = net.node('0'), net._connections[0]
            original = node.mu.copy()
            def state_energy(z):
                node.mu = z.copy()
                return energy(net)
            expected = negative_gradient(state_energy, original)
            node.mu = original.copy()
            refresh(net)
            # Independent analytic oracle; never installed into production engine.
            pressure=sum(c.W.conj()@c.target.epsilon/parents for c in net._connections
                         if c.source is node)
            if activation=='tanh':
                pressure=radial_tanh_pullback(original,pressure)
            reference_state=-node.epsilon+pressure
            reference_error=relative(reference_state,expected)
            for c in net._connections:
                c.propagate_error()
            node.update_state(1e-5, 1)
            actual = (node.mu-original)/1e-5
            state_error = relative(actual, expected)
            node.mu = original.copy()
            w = conn.W.copy()
            def weight_energy(v):
                conn.W = v.copy()
                return energy(net)
            expected_w = negative_gradient(weight_energy, w)
            conn.W = w.copy()
            refresh(net)
            reference_w=np.outer(node.activation.conj(),conn.target.epsilon)/parents
            reference_weight_error=relative(reference_w,expected_w)
            conn.learn()
            actual_w = (conn.W-w)/conn.eta_learn
            weight_error = relative(actual_w, expected_w)
            cases.append(dict(activation=activation, parents=parents, real_weights=real,
                              seed=seed, state_relative_error=state_error,
                              weight_relative_error=weight_error,
                              reference_state_relative_error=reference_error,
                              reference_weight_relative_error=reference_weight_error,
                              state_pass=state_error<1e-6, weight_pass=weight_error<1e-6))
    return cases


def low_level():
    rng = np.random.default_rng(51)
    z = np.array([0, 1j, 1+2j, -2-.3j], complex)
    direction = np.array([1+1j, 1, .7-.2j, -.3+2j])
    h = 1e-6
    r = np.abs(z)
    # Adjoint/Jacobian of radial tanh: distinct radial and tangential eigenvalues.
    a = np.divide(np.tanh(r), r, out=np.ones_like(r), where=r>0)
    radial = np.divide(np.real(z.conj()*direction), r*r,
                       out=np.zeros_like(r), where=r>0)
    reference = a*direction + ((1-np.tanh(r)**2)-a)*z*radial
    numerical = (_mod_tanh(z+h*direction)-_mod_tanh(z-h*direction))/(2*h)
    nd = PCNode('n', 4, activation='tanh', rng=rng)
    nd.mu = z.copy()
    derivative_error = relative(nd.activation_deriv*direction, numerical)
    # Temporal V update against implemented linear-output energy.
    nd.eta_temporal = 1e-5; nd.w_clip_V = 0
    nd._prev_f_mu = .4*(rng.normal(size=4)+1j*rng.normal(size=4))
    original = nd.V.copy()
    nd._predicted_next_mu = nd.V@nd._prev_f_mu
    expected = negative_gradient(lambda v: .5*np.sum(np.abs(nd.mu-v@nd._prev_f_mu)**2), original)
    nd.learn_temporal()
    temporal_error = relative((nd.V-original)/nd.eta_temporal, expected)
    # Zero temporal rate is not a freeze if V clips.
    nd.eta_temporal=0; nd.w_clip_V=3
    nd.V[:] = 4
    nd.learn_temporal()
    zero_rate_mutates = bool(np.any(nd.V != 4))
    nd.clamp(z); old = nd.mu.copy()
    nd._pressure[:] = 20
    nd.update_state(.1, 1)
    clamp_ok = bool(np.array_equal(nd.mu, old) and not np.any(nd._pressure))
    v = nd.V.copy(); nd.reset(rng)
    reset_ok = bool(np.array_equal(v, nd.V) and not np.any(nd._predicted_next_mu) and not nd.is_clamped)
    sensor = SensorNode('sensor',4)
    sensor.reset(rng)
    # Nonfinite handling silently replaces entire free state with zeros.
    nd.mu[:] = 1; nd.epsilon[:] = np.nan; nd.update_state(.1,1)
    return dict(modrelu_identity_max_error=float(np.max(np.abs(_mod_relu(z)-z))),
                tanh_reference_jvp_relative_error=relative(reference,numerical),
                stored_derivative_as_jvp_relative_error=derivative_error,
                temporal_linear_output_gradient_relative_error=temporal_error,
                zero_temporal_rate_still_clips=zero_rate_mutates,
                clamp_preserved=clamp_ok, reset_preserves_V_clears_history=reset_ok,
                sensor_reset_unclamps=not sensor.is_clamped,
                nonfinite_state_silently_zeroed=bool(np.all(nd.mu==0)))


def ascent_counterexample():
    net = graph('identity',1,11)
    src, dst, c = net.node('0'), net.node('y'), net._connections[0]
    src.mu[:] = 0; dst.set_input(np.array([1,0],complex))
    c.W[:] = 0; c.W[0,0]=1j
    before = energy(net)
    c.propagate_error(); src.update_state(.1,1)
    after = energy(net)
    return dict(before=before, after=after, increased=after>before)


def parity():
    a = graph('tanh',2,27)
    a.n_relax=8; a.eps_tol=0
    b = copy.deepcopy(a)
    a._plan=None; b._plan=RelaxPlan(b)
    maximum=0.
    for step in range(8):
        value = np.array([np.sin(step), .2j*step])
        for n in (a,b):
            n.node('y').set_input(value)
            if step==4:
                n.node('y').unclamp()
            n.step(learn=step%2==0)
            n.commit_step()
        for key in a._nodes:
            for attr in ('mu','pi','epsilon','V','_predicted_next_mu'):
                maximum=max(maximum,float(np.max(np.abs(getattr(a.node(key),attr)-getattr(b.node(key),attr)))))
        for ca,cb in zip(a._connections,b._connections):
            maximum=max(maximum,float(np.max(np.abs(ca.W-cb.W))))
    return dict(maximum_absolute_difference=maximum, passed=maximum<1e-10)


def supervised_control():
    # Known complex linear mapping; clamped source isolates W learning from inference.
    net=graph('identity',1,91)
    c=net._connections[0]; src=net.node('0'); dst=net.node('y')
    rng=np.random.default_rng(92)
    target=.2*(rng.normal(size=(3,2))+1j*rng.normal(size=(3,2)))
    initial=float(np.mean(np.abs(c.W-target)**2))
    c.eta_learn=.02
    for _ in range(2000):
        x=rng.normal(size=3)+1j*rng.normal(size=3)
        src.clamp(x); dst.set_input(target.T@x)
        refresh(net); c.learn()
    final=float(np.mean(np.abs(c.W-target)**2))
    return dict(initial_weight_mse=initial, final_weight_mse=final, passed=final<1e-12)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root=Path(__file__).parent
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in ('node.py','connection.py','network.py','relax_vec.py')}
    result=dict(schema='pc-engine-math-audit-v1', engine_sha256=hashes,
                gradients=gradient_cases(), node=low_level(),
                ascent=ascent_counterexample(), vector_parity=parity(),
                supervised_linear=supervised_control())
    result['energy_gradient_contract_passed']=all(c['state_pass'] and c['weight_pass'] for c in result['gradients'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
