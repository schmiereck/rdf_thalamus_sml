"""test_pc_chained_planner.py — Proof of Concept: Chained PCModules with shared weights.

Demonstrates that we can chain multiple instances of a predictive module (sharing the
same weight matrix reference in Python/NumPy) to plan multi-step trajectories in a 1D
space. By clamping the start and end states and letting the intermediate states and
actions relax, the network performs path planning and infers the necessary actions.
"""

from __future__ import annotations

import os
import sys
import numpy as np

# Ensure we can import from the src directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.node import PCNode, SensorNode
from pc.connection import ConnType
from pc.network import PCNetwork


def make_blob(pos: float, dim: int = 10, sigma: float = 1.0) -> np.ndarray:
    """Create a 1D Gaussian blob representing a position."""
    x = np.arange(dim)
    b = np.exp(-0.5 * ((x - pos) / sigma) ** 2)
    return b / (b.sum() + 1e-9)


def main() -> None:
    print("=" * 76)
    print("  Testing Chained PCModules with Shared Weights for Trajectory Planning")
    print("=" * 76)

    # 1. Train the transition model (x_t, u_t) -> x_t+1
    rng = np.random.default_rng(42)
    # n_relax=20 is enough to adjust the representation and learn transition weights
    net_train = PCNetwork(
        eta_inf=0.1,
        n_relax=20,
        eta_learn=0.02,
        lambda_decay=0.0005,
        w_clip=3.0,
        rng=rng
    )

    x_node = net_train.add(SensorNode("x", dim=10))
    u_node = net_train.add(SensorNode("u", dim=2))
    y_node = net_train.add(PCNode("y", dim=10, activation="identity", rng=rng))

    # Connect source nodes (current state x, action u) to target node (next state y)
    c_x = net_train.connect("x", "y", ConnType.UP)
    c_u = net_train.connect("u", "y", ConnType.UP)

    # Train on transition data (random babbling of actions and positions)
    steps = 15000
    print(f"  Training transition dynamics on {steps} random steps...")
    for step in range(steps):
        p_t = rng.uniform(1.0, 8.0)
        # Action: 0 = move right (+1.0), 1 = move left (-1.0)
        act_idx = rng.choice([0, 1])
        act_val = 1.0 if act_idx == 0 else -1.0
        p_next = np.clip(p_t + act_val, 0.0, 9.0)

        u_val = np.zeros(2)
        u_val[act_idx] = 1.0

        x_node.set_input(make_blob(p_t))
        u_node.set_input(u_val)
        y_node.clamp(make_blob(p_next))

        net_train.step(learn=True)
        net_train.commit_step()

    print("  Transition model training completed successfully.")

    # Extract the learned transition weights
    W_x = c_x.W.copy()
    W_u = c_u.W.copy()

    # 2. Build the chained planner network
    # We want a planning horizon of K = 4 steps.
    # We have states x0, x1, x2, x3, x4 and actions u0, u1, u2, u3.
    print("\n  Assembling Chained Planning Network (Horizon K = 4)...")
    # No learning during planning, only relaxation!
    net_plan = PCNetwork(eta_inf=0.08, n_relax=250, eps_tol=1e-7, rng=rng)

    # Create the state nodes (PCNodes so we can clamp endpoints and let middle relax)
    nodes_x = []
    for k in range(5):
        nodes_x.append(net_plan.add(PCNode(f"x{k}", dim=10, activation="identity", rng=rng)))

    # Create the action nodes (PCNodes that will be inferred)
    nodes_u = []
    for k in range(4):
        nodes_u.append(net_plan.add(PCNode(f"u{k}", dim=2, activation="identity", rng=rng)))

    # Connect steps: (x_k, u_k) -> x_k+1
    conns_x = []
    conns_u = []
    for k in range(4):
        cx = net_plan.connect(f"x{k}", f"x{k+1}", ConnType.UP)
        cu = net_plan.connect(f"u{k}", f"x{k+1}", ConnType.UP)
        conns_x.append(cx)
        conns_u.append(cu)

    # Inject shared weight matrices (referencing the SAME numpy array memory)
    for cx in conns_x:
        cx.W = W_x
    for cu in conns_u:
        cu.W = W_u

    # Apply error attenuation (discounting / decay) for future steps
    # Future steps propagate their error signals back, but attenuated by gamma^k
    gamma = 0.85
    for k in range(4):
        scale = gamma ** k
        conns_x[k].pressure_scale = scale
        conns_u[k].pressure_scale = scale

    # Test Scenario A: Plan Path Moving Right (2.0 -> 6.0)
    print("\n" + "-" * 76)
    print("  Scenario A: Plan path from START = 2.0 to GOAL = 6.0 (Expect 4 RIGHT steps)")
    print("-" * 76)

    # Clamp boundary conditions
    nodes_x[0].clamp(make_blob(2.0))
    nodes_x[4].clamp(make_blob(6.0))

    # Initialize intermediate states with a noisy interpolation
    for k in range(1, 4):
        nodes_x[k].unclamp()
        init_pos = 2.0 + k * (6.0 - 2.0) / 4.0
        nodes_x[k].mu = make_blob(init_pos) + rng.normal(0, 0.02, 10)

    # Initialize action probabilities to neutral with some noise
    for k in range(4):
        nodes_u[k].unclamp()
        nodes_u[k].mu = rng.uniform(0.4, 0.6, 2)
        nodes_u[k].mu /= nodes_u[k].mu.sum()

    # Run relaxation to perform path planning
    net_plan.step(learn=False)

    # Read and print the plan
    print("  Relaxation complete. Inferred path and actions:")
    for k in range(5):
        pos_est = np.argmax(nodes_x[k].mu)
        print(f"    x{k}: peak at {pos_est} | weights: "
              f"[{' '.join(f'{v:.2f}' for v in nodes_x[k].mu)}]")
        if k < 4:
            u_probs = nodes_u[k].mu
            direction = "RIGHT" if u_probs[0] > u_probs[1] else "LEFT"
            print(f"       >>> u{k}: [Right={u_probs[0]:.2f}, Left={u_probs[1]:.2f}] -> {direction}")

    # Test Scenario B: Plan Path Moving Left (7.0 -> 3.0)
    print("\n" + "-" * 76)
    print("  Scenario B: Plan path from START = 7.0 to GOAL = 3.0 (Expect 4 LEFT steps)")
    print("-" * 76)

    # Clamp boundary conditions
    nodes_x[0].clamp(make_blob(7.0))
    nodes_x[4].clamp(make_blob(3.0))

    # Initialize intermediate states with a noisy interpolation
    for k in range(1, 4):
        nodes_x[k].unclamp()
        init_pos = 7.0 + k * (3.0 - 7.0) / 4.0
        nodes_x[k].mu = make_blob(init_pos) + rng.normal(0, 0.02, 10)

    # Initialize action probabilities to neutral with some noise
    for k in range(4):
        nodes_u[k].unclamp()
        nodes_u[k].mu = rng.uniform(0.4, 0.6, 2)
        nodes_u[k].mu /= nodes_u[k].mu.sum()

    # Run relaxation
    net_plan.step(learn=False)

    # Read and print the plan
    print("  Relaxation complete. Inferred path and actions:")
    for k in range(5):
        pos_est = np.argmax(nodes_x[k].mu)
        print(f"    x{k}: peak at {pos_est} | weights: "
              f"[{' '.join(f'{v:.2f}' for v in nodes_x[k].mu)}]")
        if k < 4:
            u_probs = nodes_u[k].mu
            direction = "RIGHT" if u_probs[0] > u_probs[1] else "LEFT"
            print(f"       >>> u{k}: [Right={u_probs[0]:.2f}, Left={u_probs[1]:.2f}] -> {direction}")

    print("=" * 76)


if __name__ == "__main__":
    main()
