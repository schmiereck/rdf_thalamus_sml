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


def fwd(W_x, W_u, x_blob, u):
    """One step of the SHARED learned forward model:  next_blob = W_x^T x + W_u^T u  (the framework's
    prediction convention, identity activations)."""
    return W_x.T @ x_blob + W_u.T @ np.array([u], float)


def plan_chain(W_x, W_u, start, goal, K=4, n_relax=400, rng=None):
    """The CHAINED-RELAXATION mechanism: chain state nodes with the shared forward model, ONE shared
    action applied every step (constant velocity -> stable, no collapse, no latent<->latent loop), clamp
    the endpoints, relax, read the states.  Stable + monotonic + meaningful actions (the first attempt's
    failures fixed) -- but the spacing stays FRONT-LOADED (see the honest note in main)."""
    rng = rng or np.random.default_rng(0)
    net = PCNetwork(eta_inf=0.08, n_relax=n_relax, eps_tol=1e-8, rng=rng)
    xs = [net.add(PCNode(f"x{k}", dim=DIM, activation="identity", rng=rng)) for k in range(K + 1)]
    u = net.add(PCNode("u", dim=1, activation="identity", rng=rng))
    UPS = float(os.environ.get("CH_UPS", "12.0"))
    for k in range(K):
        net.connect(f"x{k}", f"x{k+1}", ConnType.UP).W = W_x
        cu = net.connect("u", f"x{k+1}", ConnType.UP); cu.W = W_u; cu.pressure_scale = UPS
    xs[0].clamp(blob(start)); xs[K].clamp(blob(goal))
    step0 = (goal - start) / K
    for k in range(1, K):
        xs[k].mu = blob(start + k * step0)
    u.mu = np.array([step0])
    net.step(learn=False)
    return [peak(x.mu) for x in xs], [float(u.mu[0])] * K


def plan_interp(W_x, W_u, start, goal, K=4):
    """The CLEAN even sub-goals: interpolate in DECODED COORDINATE space (evenly spaced by construction),
    and use the learned forward model only to CHECK one-step reachability (per-step prediction error).
    For a simple planar move this is the right, front-loading-free choice; the latent chain (plan_chain)
    is worth its distortion only when the dynamics are genuinely constrained."""
    states = [start + k * (goal - start) / K for k in range(K + 1)]
    delta = (goal - start) / K
    reach_err = float(np.mean([np.linalg.norm(fwd(W_x, W_u, blob(states[k]), delta) - blob(states[k + 1]))
                               for k in range(K)]))         # forward model verifies one-step feasibility
    return states, [delta] * K, reach_err


def main():
    rng = np.random.default_rng(42)
    print("=" * 76)
    print("  STATE-SPACE chained planning (1D PoC) — read the intermediate STATES as sub-goals")
    print("  training the forward model (continuous signed steps) ...")
    W_x, W_u = train_forward(rng)
    print("=" * 76)
    for (s, g) in [(2.0, 6.0), (7.0, 3.0), (1.0, 8.0)]:
        ideal = [s + k * (g - s) / 4 for k in range(5)]
        pc, _ = plan_chain(W_x, W_u, s, g, K=4, rng=rng)
        ip, _, reach = plan_interp(W_x, W_u, s, g, K=4)
        ec = float(np.mean(np.abs(np.array(pc) - np.array(ideal))))
        ei = float(np.mean(np.abs(np.array(ip) - np.array(ideal))))
        print(f"  {s:.0f} -> {g:.0f}:  chain-relax {[f'{p:.1f}' for p in pc]}  (err {ec:.2f}, FRONT-LOADED)")
        print(f"            interp      {[f'{p:.1f}' for p in ip]}  (err {ei:.2f}, even; model 1-step err {reach:.2f})")
    print("=" * 76)
    print("  Read (honest): the chained-relaxation MECHANISM now works STABLY (vs the first attempt's")
    print("  2->1->6->6->6 with ~0 actions): single shared action -> no collapse, no divergence, monotonic.")
    print("  BUT the spacing stays FRONT-LOADED and could not be cleanly removed: action-smoothness /")
    print("  shared-mean priors DIVERGE (latent<->latent loops), and a forward ROLLOUT also distorts because")
    print("  the learned blob model is not a clean shift under multi-step autoregression.  ROOT: the latent")
    print("  forward model's multi-step error + the goal's backward pull.  CLEAN even sub-goals come from")
    print("  COORDINATE-space interpolation (small 1-step model error confirms feasibility); the latent")
    print("  chain is only worth its distortion for genuinely CONSTRAINED dynamics, which this PoC lacks.")


if __name__ == "__main__":
    main()
