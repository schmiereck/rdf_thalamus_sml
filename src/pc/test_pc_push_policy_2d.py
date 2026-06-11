r"""
test_pc_push_policy_2d.py — DE-RISK: a LEARNED 2-D push-side policy (no hand-coded side).

The 1-D learned push-side policy is validated (test_pc_push_policy.py: MPC through a
learned push model discovers reposition-then-push, the side emerges).  This de-risks
the 2-D version before putting it on act10:

  1. learn a 2-D push-DYNAMICS model  M(d_vec, a_vec, finger) -> Δobj_vec  by babble
     (genuine 2-D push: the object is shoved AWAY in the hand's motion direction; the
     hand can't pull) — captures the side/direction-dependent contact dynamics.
  2. short-horizon MPC through M with CUMULATIVE discounted cost over a compact 2-D
     action set (8 push directions + 4 reposition directions); the push side (which way
     to go around the object) FALLS OUT of the learned dynamics + planning.

Test: from a hand START on the WRONG side (between object and target, so a detour is
required), does MPC deliver the object to the target?  Controls: a SCRAMBLED model and
a GREEDY (horizon 1) planner should fail.

Run:  python test_pc_push_policy_2d.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

G = 24
CONTACT_R = 1.6
MAG = float(os.environ.get("MAG2D", "1.6"))          # detour fits a short horizon (sweet spot)
GAMMA = 0.85
LO, HI = G / 8.0, G * 7.0 / 8.0

_ANG8 = np.array([k * np.pi / 4 for k in range(8)])
DIRS8 = np.stack([np.cos(_ANG8), np.sin(_ANG8)], 1)
DIRS4 = DIRS8[::2]                                    # cardinal directions
# 8 push dirs (coarse + fine, fine avoids near-target overshoot) + 4 reposition dirs
ACTIONS = ([(d * MAG, 1.0) for d in DIRS8] + [(d * MAG * 0.4, 1.0) for d in DIRS8]
           + [(d * MAG, 0.0) for d in DIRS4])


def shove(obj, p_new, a, finger):
    """Genuine 2-D push: if the finger is out, the hand is in contact, and it moved
    INTO the object, the object is shoved to stay just ahead in the motion direction.
    Returns the new object position (the hand can only push, never pull)."""
    amag = np.linalg.norm(a)
    if finger > 0.5 and amag > 1e-6 and np.linalg.norm(p_new - obj) < CONTACT_R:
        if np.dot(a, obj - (p_new - a)) > 0:         # moved toward the object
            return np.clip(p_new + (a / amag) * CONTACT_R * 0.9, 0, G - 1)
    return obj


class PushModel2D:
    """Learned 2-D push dynamics: [dx/R, dy/R, ax, ay, finger] -> Δobj (2)."""
    def __init__(self, hid=48, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 0.5, (hid, 5)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 0.3, (2, hid)); self.b2 = np.zeros(2)
        self.lr = lr; self.rng = rng; self.last_surprise = None   # EMA |predicted Δobj - actual Δobj|

    def _x(self, d, a, f):
        return np.array([d[0] / CONTACT_R, d[1] / CONTACT_R, a[0], a[1], f])

    def predict(self, d, a, f):
        h = np.tanh(self.W1 @ self._x(d, a, f) + self.b1)
        return self.W2 @ h + self.b2, h

    def babble(self, steps):
        for _ in range(steps):
            obj = self.rng.uniform(LO, HI, 2)
            ang = self.rng.uniform(0, 2 * np.pi); dist = self.rng.uniform(0, CONTACT_R + 2)
            d = dist * np.array([np.cos(ang), np.sin(ang)])
            a = self.rng.uniform(-MAG, MAG, 2); f = float(self.rng.integers(0, 2))
            p_new = obj + d + a
            o2 = shove(obj, p_new, a, f)
            dobj = o2 - obj
            y, h = self.predict(d, a, f)
            err = y - dobj
            self.W2 -= self.lr * np.outer(err, h); self.b2 -= self.lr * err
            dh = (self.W2.T @ err) * (1 - h ** 2)
            self.W1 -= self.lr * np.outer(dh, self._x(d, a, f)); self.b1 -= self.lr * dh

    def observe(self, d, a, f, dobj, lr=0.003):
        """One online gradient step from a REAL experienced push — lifelong learning."""
        y, h = self.predict(d, a, f)
        err = y - dobj
        s = float(np.sqrt(np.mean(err ** 2)))                     # SURPRISE: predicted vs actual Δobj
        self.last_surprise = s if self.last_surprise is None else 0.9 * self.last_surprise + 0.1 * s
        self.W2 -= lr * np.outer(err, h); self.b2 -= lr * err
        dh = (self.W2.T @ err) * (1 - h ** 2)
        self.W1 -= lr * np.outer(dh, self._x(d, a, f)); self.b1 -= lr * dh

    def scramble(self):
        self.W1 = self.rng.normal(0, 0.5, self.W1.shape); self.W2 = self.rng.normal(0, 0.5, self.W2.shape)


def plan(model, obj, p, target, horizon):
    best_a, best_c = ACTIONS[0], 1e9
    for (a, f) in ACTIONS:
        c = _cost(model, obj, p, target, a, f, horizon)
        if c < best_c:
            best_c, best_a = c, (a, f)
    return best_a


def _cost(model, obj, p, target, a, f, horizon):
    dobj, _ = model.predict(p - obj, a, f)
    o2 = np.clip(obj + dobj, 0, G - 1); p2 = np.clip(p + a, 0, G - 1)
    cost = float(np.linalg.norm(o2 - target))
    if horizon > 1:
        cost += GAMMA * min(_cost(model, o2, p2, target, aa, ff, horizon - 1)
                            for (aa, ff) in ACTIONS)
    return cost


def run(model, horizon, episodes=30, max_steps=80, rng=None):
    rng = rng or np.random.default_rng()
    delivered = 0
    for _ in range(episodes):
        obj = rng.uniform(LO, HI, 2)
        tgt = rng.uniform(LO, HI, 2)
        while np.linalg.norm(obj - tgt) < 8:
            tgt = rng.uniform(LO, HI, 2)
        u = (tgt - obj) / np.linalg.norm(tgt - obj)
        p = np.clip(obj + u * (CONTACT_R + 0.5), 0, G - 1)   # hand on the WRONG (target) side
        for _ in range(max_steps):
            a, f = plan(model, obj, p, tgt, horizon)
            p = np.clip(p + a, 0, G - 1)
            obj = shove(obj, p, a, f)
            if np.linalg.norm(obj - tgt) < 1.6:
                delivered += 1; break
    return 100.0 * delivered / episodes


def main():
    print("=" * 74)
    print("  Learned 2-D push-side policy (de-risk): MPC through a learned 2-D push model")
    print(f"  world={G}  contact_R={CONTACT_R}  {len(ACTIONS)} actions  hand STARTS wrong side")
    print("=" * 74)
    m = PushModel2D(rng=np.random.default_rng(2)); m.babble(40000)
    for H in (1, 3):
        acc = run(m, horizon=H, rng=np.random.default_rng(3))
        print(f"  learned model, horizon={H}: delivered {acc:5.1f}%"
              f"  {'(greedy, too short)' if H == 1 else ''}")
    sm = PushModel2D(rng=np.random.default_rng(4)); sm.babble(40000); sm.scramble()
    print(f"  SCRAMBLED model, horizon=3: delivered {run(sm, 3, rng=np.random.default_rng(3)):5.1f}%"
          f"   [control]")
    print("-" * 74)
    print("  Read: horizon-3 with the learned model delivers from the wrong side in 2-D")
    print("        (reposition-then-push emerges); greedy & scrambled fail.")
    print("=" * 74)


if __name__ == "__main__":
    main()
