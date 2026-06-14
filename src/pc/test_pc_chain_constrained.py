"""test_pc_chain_constrained.py — chained planning under CONSTRAINED (nonlinear) dynamics.

The earlier PoCs used a planar move where the straight/even interpolation is already the answer, so the
chained forward model added nothing (and front-loaded).  The chained model EARNS ITS KEEP only when the
dynamics are CONSTRAINED so the naive path is INFEASIBLE.  This 1D PoC adds a "MUD" zone with a
position-dependent SPEED LIMIT: inside the mud only tiny steps are possible, elsewhere large ones.

  dynamics:  next = pos + clip(u, -lim(pos), +lim(pos)),  lim(pos)=MUD_CAP in the mud else OPEN_CAP

A nonlinear forward model is required (the effect of the action depends on position), so the world model
is a small PC net WITH A HIDDEN LAYER (x_blob, u) -> h(tanh) -> next_blob.  We plan by rolling out this
learned model (prediction -> input of the next step) and correcting the single action from the goal error.

Honest expectation: the world model is tiny.  The point is to see whether the chained model's plan
RESPECTS the learned speed limit (feasible) where even interpolation VIOLATES it.
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.node import PCNode, SensorNode
from pc.connection import ConnType
from pc.network import PCNetwork

DIM = 12                                                    # positions 0..11
MUD_LO, MUD_HI = 5.0, 7.0
MUD_CAP, OPEN_CAP = 0.3, 1.5


def blob(pos, sigma=1.0):
    x = np.arange(DIM)
    b = np.exp(-0.5 * ((x - pos) / sigma) ** 2)
    return b / (b.sum() + 1e-9)


def peak(mu):
    w = np.clip(mu, 0, None); s = w.sum()
    return float((np.arange(DIM) * w).sum() / s) if s > 1e-6 else float("nan")


def lim(pos):
    return MUD_CAP if MUD_LO <= pos <= MUD_HI else OPEN_CAP


def true_step(pos, u):
    return float(np.clip(pos + np.clip(u, -lim(pos), lim(pos)), 0.0, DIM - 1))


class ForwardModel:
    """Tiny NONLINEAR PC world model: (x_blob, u) -> h(tanh) -> next_blob.  A hidden layer is needed so
    the effect of the action can depend on position (the mud speed limit)."""

    UMAX = 1.8                                              # action range (steps beyond this are capped anyway)

    def __init__(self, hid=48, rng=None):
        rng = rng or np.random.default_rng(0)
        self.net = PCNetwork(eta_inf=0.1, n_relax=30, eta_learn=0.02, lambda_decay=0.0005, w_clip=4.0, rng=rng)
        self.x = self.net.add(SensorNode("x", dim=DIM))
        self.u = self.net.add(SensorNode("u", dim=1))
        self.h = self.net.add(PCNode("h", dim=hid, activation="tanh", rng=rng))
        self.y = self.net.add(PCNode("y", dim=DIM, activation="identity", rng=rng))
        self.net.connect("x", "h", ConnType.UP); self.net.connect("u", "h", ConnType.UP)
        self.net.connect("h", "y", ConnType.UP)

    def train(self, steps=20000, rng=None):
        rng = rng or np.random.default_rng(1)
        for _ in range(steps):
            p = rng.uniform(0.5, DIM - 1.5); u = rng.uniform(-self.UMAX, self.UMAX)
            self.x.set_input(blob(p)); self.u.set_input(np.array([u])); self.y.clamp(blob(true_step(p, u)))
            self.net.step(learn=True); self.net.commit_step()
        self.y.unclamp()

    def predict(self, x_blob, u):
        """Forward prediction next_blob from (x,u): clamp inputs, relax, read y's prediction.  The action
        is CLIPPED to the trained range so the model is never queried out-of-distribution (where it would
        hallucinate huge jumps that ignore the speed limit)."""
        u = float(np.clip(u, -self.UMAX, self.UMAX))
        self.x.set_input(x_blob); self.u.set_input(np.array([u])); self.y.unclamp()
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self.net.node("y").pi.copy()


class MLPForward:
    """Same world model, but a small backprop-trained MLP -> a MORE ACCURATE tiny model, to test whether
    the CHAINED-PLANNING MECHANISM works once the model fidelity is good enough (separating the mechanism
    from the PC-net's poor hidden-layer training)."""
    UMAX = 1.8

    def __init__(self, hid=64, lr=0.03, rng=None):
        rng = rng or np.random.default_rng(0)
        din = DIM + 1
        self.W1 = rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (DIM, hid)); self.b2 = np.zeros(DIM)
        self.lr = lr

    def _x(self, x_blob, u):
        return np.concatenate([np.asarray(x_blob, float), [float(u)]])

    def train(self, steps=40000, rng=None):
        rng = rng or np.random.default_rng(1)
        for _ in range(steps):
            p = rng.uniform(0.5, DIM - 1.5); u = rng.uniform(-self.UMAX, self.UMAX)
            x = self._x(blob(p), u); t = blob(true_step(p, u))
            h = np.tanh(self.W1 @ x + self.b1); y = self.W2 @ h + self.b2
            e = y - t
            self.W2 -= self.lr * np.outer(e, h); self.b2 -= self.lr * e
            dh = (self.W2.T @ e) * (1 - h ** 2)
            self.W1 -= self.lr * np.outer(dh, x); self.b1 -= self.lr * dh

    def predict(self, x_blob, u):
        u = float(np.clip(u, -self.UMAX, self.UMAX))
        h = np.tanh(self.W1 @ self._x(x_blob, u) + self.b1)
        return self.W2 @ h + self.b2


def plan_rollout(fm, start, goal, K=10, iters=60, lr=0.5):
    """Chained forward-model rollout with ONE action corrected from the goal error (prediction -> next)."""
    u = (goal - start) / K
    for _ in range(iters):
        p = blob(start)
        for _ in range(K):
            p = fm.predict(p, u)
        u += lr * (goal - peak(p)) / K
    path = [start]; p = blob(start)
    for _ in range(K):
        p = fm.predict(p, u); path.append(peak(p))
    return path, u


def feasible(path):
    """Max per-step move RELATIVE to the local speed limit (>1 = violates the constraint)."""
    ratios = []
    for a, b in zip(path[:-1], path[1:]):
        ratios.append(abs(b - a) / lim((a + b) / 2.0))
    return max(ratios), ratios


def main():
    rng = np.random.default_rng(42)
    print("=" * 78)
    print(f"  CONSTRAINED chained planning (1D, MUD zone [{MUD_LO:.0f},{MUD_HI:.0f}] cap {MUD_CAP},"
          f" open cap {OPEN_CAP})")
    MLP = os.environ.get("CON_MLP", "1") == "1"            # 1 = accurate backprop MLP world model
    print(f"  training the tiny NONLINEAR forward world model ({'MLP' if MLP else 'PC'}) ...")
    fm = (MLPForward(rng=rng) if MLP else ForwardModel(rng=rng))
    fm.train(int(os.environ.get("CON_STEPS", "40000")))
    # sanity: model 1-step accuracy
    errs = [abs(peak(fm.predict(blob(p), u)) - true_step(p, u))
            for p, u in [(2, 1.5), (5.5, 1.5), (6, 1.5), (3, -1.0)]]
    print(f"  model 1-step error (open & mud): {np.mean(errs):.2f}")
    print("=" * 78)

    start, goal, K = 2.0, 10.0, 14
    rollout, u = plan_rollout(fm, start, goal, K=K)
    interp = [start + k * (goal - start) / K for k in range(K + 1)]

    def zone_steps(path):                                  # average step size OPEN vs inside the MUD
        op, mu = [], []
        for a, b in zip(path[:-1], path[1:]):
            (mu if MUD_LO <= (a + b) / 2 <= MUD_HI else op).append(abs(b - a))
        return (np.mean(op) if op else float("nan")), (np.mean(mu) if mu else float("nan"))

    ro_op, ro_mu = zone_steps(rollout); in_op, in_mu = zone_steps(interp)
    print(f"  start {start:.0f} -> goal {goal:.0f}  (must cross the MUD [{MUD_LO:.0f},{MUD_HI:.0f}], cap {MUD_CAP})")
    print(f"  rollout (chained model): {[f'{p:.1f}' for p in rollout]}  end {rollout[-1]:.1f}")
    print(f"     avg step: open {ro_op:.2f}  MUD {ro_mu:.2f}   -> {'SLOWS in the mud' if ro_mu < 0.7*ro_op else 'does NOT slow'}")
    print(f"  interp  (even, naive)  : {[f'{p:.1f}' for p in interp]}  end {interp[-1]:.1f}")
    print(f"     avg step: open {in_op:.2f}  MUD {in_mu:.2f}   -> uniform (ignores the limit)")
    print("-" * 78)
    print("  Read (HONEST, negative): the chained rollout runs stably and reaches near the goal, but it does")
    print("  NOT respect the mud speed-limit -- its mud steps are about the same as its open steps (the")
    print("  apparent slowing is just GOAL SATURATION near the end, not constraint-awareness).  Two reasons:")
    print("  (1) the tiny world model under-learns the SHARP 5x cap; (2) a SINGLE constant action cannot")
    print("  express the NON-UNIFORM profile a constraint needs -- and per-step actions COLLAPSE/DIVERGE in")
    print("  the PC relaxation (seen earlier).  So constrained planning needs BOTH a richer world model AND")
    print("  a stable per-step action inference.  The architecture is extensible in principle; these are the")
    print("  two levers.  (Matches the 'tiny world model' caveat -- honest negative result, not a fail of nerve.)")


if __name__ == "__main__":
    main()
