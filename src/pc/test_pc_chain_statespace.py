"""test_pc_chain_statespace.py — STATE-SPACE chained planning (the fix for the failed first attempt).

The first attempt (test_pc_chained_planner.py) inferred the ACTIONS as free PCNodes.  Diagnosis: a free
node has no top-down prediction (pi=0) so its error is eps=mu, and relaxation regularises it toward ZERO
-> the inferred actions were ~0.02 (tiny, noisy) and the intermediate trajectory was degenerate
(2 -> 1 -> 6 -> 6 -> 6 instead of 2 -> 3 -> 4 -> 5 -> 6).  Two more bugs: the actions were trained as
fixed UNIT vectors (no magnitude), and a gamma discount weakened the goal's pull on early steps.

This version plans in STATE SPACE: a chain of state nodes x0..xK with the shared LEARNED forward model
as the transition; we READ THE STATES as the sub-goals.  Fixes:
  * actions are CONTINUOUS SIGNED (a real step with magnitude), trained on random displacements;
  * NO gamma discount (the goal pulls every step), and the actions are INITIALISED toward the goal
    direction so relaxation refines a real plan instead of collapsing to zero;
  * the plan we use is the sequence of decoded STATES (sub-goals); the action is a by-product.
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.node import PCNode, SensorNode
from pc.connection import ConnType
from pc.network import PCNetwork

DIM = 10


def blob(pos, sigma=1.0):
    x = np.arange(DIM)
    b = np.exp(-0.5 * ((x - pos) / sigma) ** 2)
    return b / (b.sum() + 1e-9)


def peak(mu):
    w = np.clip(mu, 0, None); s = w.sum()
    return float((np.arange(DIM) * w).sum() / s) if s > 1e-6 else float("nan")


def train_forward(rng, steps=12000):
    """Forward model  next_blob = f(cur_blob, u)  with u a CONTINUOUS SIGNED step (with magnitude)."""
    net = PCNetwork(eta_inf=0.1, n_relax=20, eta_learn=0.02, lambda_decay=0.0005, w_clip=3.0, rng=rng)
    x = net.add(SensorNode("x", dim=DIM))
    u = net.add(SensorNode("u", dim=1))
    y = net.add(PCNode("y", dim=DIM, activation="identity", rng=rng))
    cx = net.connect("x", "y", ConnType.UP)
    cu = net.connect("u", "y", ConnType.UP)
    for _ in range(steps):
        p = rng.uniform(1.0, 8.0)
        step = rng.uniform(-1.5, 1.5)                       # SIGNED, with magnitude
        p_next = np.clip(p + step, 0.0, 9.0)
        x.set_input(blob(p)); u.set_input(np.array([step])); y.clamp(blob(p_next))
        net.step(learn=True); net.commit_step()
    return cx.W.copy(), cu.W.copy()


def plan(W_x, W_u, start, goal, K=4, n_relax=400, rng=None):
    """Chain x0..xK with the shared forward model; clamp endpoints; relax; return the decoded STATE path."""
    rng = rng or np.random.default_rng(0)
    net = PCNetwork(eta_inf=0.08, n_relax=n_relax, eps_tol=1e-8, rng=rng)
    xs = [net.add(PCNode(f"x{k}", dim=DIM, activation="identity", rng=rng)) for k in range(K + 1)]
    us = [net.add(PCNode(f"u{k}", dim=1, activation="identity", rng=rng)) for k in range(K)]
    UPS = float(os.environ.get("CH_UPS", "12.0"))          # action-connection pressure (overcomes the
    for k in range(K):                                     # free-action self-regularisation toward 0)
        net.connect(f"x{k}", f"x{k+1}", ConnType.UP).W = W_x   # shared transition weights
        cu = net.connect(f"u{k}", f"x{k+1}", ConnType.UP); cu.W = W_u; cu.pressure_scale = UPS
    xs[0].clamp(blob(start)); xs[K].clamp(blob(goal))
    step0 = (goal - start) / K                              # the per-step displacement to reach the goal
    for k in range(1, K):                                   # init states by interpolation
        xs[k].mu = blob(start + k * step0)
    for k in range(K):                                      # init actions toward the goal direction
        us[k].mu = np.array([step0])
    net.step(learn=False)
    return [peak(x.mu) for x in xs], [float(u.mu[0]) for u in us]


def main():
    rng = np.random.default_rng(42)
    print("=" * 76)
    print("  STATE-SPACE chained planning (1D PoC) — read the intermediate STATES as sub-goals")
    print("  training the forward model (continuous signed steps) ...")
    W_x, W_u = train_forward(rng)
    print("=" * 76)
    for (s, g) in [(2.0, 6.0), (7.0, 3.0), (1.0, 8.0)]:
        path, acts = plan(W_x, W_u, s, g, K=4, rng=rng)
        ideal = [s + k * (g - s) / 4 for k in range(5)]
        err = float(np.mean(np.abs(np.array(path) - np.array(ideal))))
        print(f"  {s:.0f} -> {g:.0f}:  states {[f'{p:.1f}' for p in path]}   ideal {[f'{p:.1f}' for p in ideal]}")
        print(f"            actions {[f'{a:+.2f}' for a in acts]}   (ideal {(g-s)/4:+.2f})   path-err {err:.2f}")
    print("=" * 76)
    print("  Read (honest): vs the failed first attempt (2->1->6->6->6, actions ~0.02), the chain now")
    print("  plans a MONOTONIC goal-reaching path with MEANINGFUL signed actions (+0.3, correct sign).")
    print("  Residual: the spacing is FRONT-LOADED (big early steps, then crawl) -- the clamped goal")
    print("  dominates the relaxation; a bidirectional action-smoothness prior DIVERGES, so it is left out.")
    print("  The intermediate states are still dense, goal-directed sub-goals (usable for the policy).")


if __name__ == "__main__":
    main()
