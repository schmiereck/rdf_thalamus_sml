"""Smoke test — build a small PC graph and run a few steps."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType


def test_vertical_chain():
    """3-layer vertical chain: sensor → hidden → top."""
    rng = np.random.default_rng(42)
    net = PCNetwork(
        eta_inf=0.05, n_relax=100, eps_tol=1e-6,
        alpha=1.0, beta=1.0,
        eta_learn=0.005, lambda_decay=0.001,
        rng=rng,
    )

    sensor = net.add(SensorNode("i1", dim=8))
    hidden = net.add(PCNode("a1", dim=16, activation="tanh", rng=rng))
    top    = net.add(PCNode("b1", dim=4,  activation="tanh", rng=rng))

    net.connect("b1", "a1", ConnType.UP)
    net.connect("a1", "i1", ConnType.UP)

    print(net.summary())

    x = rng.choice([0.0, 1.0], size=8)
    sensor.set_input(x)

    sensor_errors = []
    for t in range(200):
        info = net.step(learn=True)
        sensor_errors.append(info["sensor_error"])

    print(f"\nInput : {x}")
    print(f"Sensor-error step   1: {sensor_errors[0]:.4f}")
    print(f"Sensor-error step 100: {sensor_errors[99]:.4f}")
    print(f"Sensor-error step 200: {sensor_errors[-1]:.4f}")
    assert sensor_errors[-1] < sensor_errors[0], \
        f"Sensor error should decrease: {sensor_errors[0]:.4f} → {sensor_errors[-1]:.4f}"
    print("PASS: sensor error decreases\n")


def test_lateral_connections():
    """2 sensor nodes, 2 hidden nodes connected laterally."""
    rng = np.random.default_rng(7)
    net = PCNetwork(
        eta_inf=0.05, n_relax=100,
        beta=1.0, gamma=0.5,
        eta_learn=0.005, lambda_decay=0.001,
        rng=rng,
    )

    s0 = net.add(SensorNode("i0", dim=4))
    s1 = net.add(SensorNode("i1", dim=4))
    h0 = net.add(PCNode("a0", dim=8, rng=rng))
    h1 = net.add(PCNode("a1", dim=8, rng=rng))

    net.connect("a0", "i0", ConnType.UP)
    net.connect("a1", "i1", ConnType.UP)
    net.connect("a0", "a1", ConnType.LATERAL)
    net.connect("a1", "a0", ConnType.LATERAL)

    print(net.summary())

    s0.set_input(np.array([1.0, 0.0, 1.0, 0.0]))
    s1.set_input(np.array([0.0, 1.0, 0.0, 1.0]))

    sensor_errors = [net.step(learn=True)["sensor_error"] for _ in range(200)]

    print(f"Sensor-error step   1: {sensor_errors[0]:.4f}")
    print(f"Sensor-error step 200: {sensor_errors[-1]:.4f}")
    assert sensor_errors[-1] < sensor_errors[0], \
        f"Sensor error should decrease: {sensor_errors[0]:.4f} → {sensor_errors[-1]:.4f}"
    print("PASS: lateral network sensor error decreases\n")


def test_arbitrary_fanout():
    """One top node predicts three hidden nodes (1:3 fanout)."""
    rng = np.random.default_rng(0)
    net = PCNetwork(
        eta_inf=0.05, n_relax=100,
        eta_learn=0.005, lambda_decay=0.001,
        rng=rng,
    )

    top = net.add(PCNode("b1", dim=4, rng=rng))
    for i in range(3):
        net.add(PCNode(f"a{i}", dim=8, rng=rng))
        net.add(SensorNode(f"i{i}", dim=8))
        net.connect("b1", f"a{i}", ConnType.UP)
        net.connect(f"a{i}", f"i{i}", ConnType.UP)

    print(net.summary())

    for i in range(3):
        net.node(f"i{i}").set_input(rng.uniform(-1, 1, 8))

    sensor_errors = [net.step()["sensor_error"] for _ in range(200)]
    assert sensor_errors[-1] < sensor_errors[0], \
        f"Sensor error should decrease: {sensor_errors[0]:.4f} → {sensor_errors[-1]:.4f}"
    print(f"PASS: 1:3 fanout sensor error {sensor_errors[0]:.4f} → {sensor_errors[-1]:.4f}\n")


def test_phase_isolation():
    """Verify that individual phases can be called manually."""
    rng = np.random.default_rng(1)
    net = PCNetwork(eta_inf=0.05, n_relax=20, rng=rng)
    sensor = net.add(SensorNode("s", dim=4))
    hidden = net.add(PCNode("h", dim=8, rng=rng))
    net.connect("h", "s", ConnType.UP)

    sensor.set_input(np.array([1.0, 0.0, 1.0, 0.0]))

    net.phase_predict()
    net.phase_error()
    net.phase_relax()
    net.phase_learn()
    print("PASS: individual phases callable\n")


if __name__ == "__main__":
    test_vertical_chain()
    test_lateral_connections()
    test_arbitrary_fanout()
    test_phase_isolation()
    print("All tests passed.")
