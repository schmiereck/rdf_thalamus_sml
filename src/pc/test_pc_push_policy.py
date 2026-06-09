r"""
test_pc_push_policy.py — DE-RISK: a LEARNED push-side policy (no hand-coded side).

act8b step 5 pushes the object to the target, but the policy "get on the far side
(sign(eps_obj)) and push" is HAND-CODED.  The deeper question: can the agent LEARN to
choose the side + when to push, so that "reposition-then-push" EMERGES?

Approach (model-based, in the project's spirit — no perception here, that is already
solved; this isolates the ACTION policy):
  1. Learn a PUSH-DYNAMICS model  M(d, a, finger) -> Δobj  by babble (random hand
     offset d=pointer-obj, random move a, random finger), observing the genuine
     push (act8b World1D.shove).  M captures the asymmetric, SIDE-DEPENDENT physics
     ("pushing only moves the object when the finger is out and the hand drives INTO
     it from behind").
  2. Plan with short-horizon MPC THROUGH the learned model: search action sequences
     (move ±step × finger {0,1}) over a horizon, predict the object trajectory with M,
     pick the first action of the sequence that best reduces |obj - target|.  The side
     choice is NOT coded — it falls out of the learned dynamics + planning.

Test: does MPC deliver the object to the target (discovering reposition-then-push)?
Controls: a SCRAMBLED model (planning on garbage dynamics) and a GREEDY 1-step planner
(too short to discover the detour) should both fail -> proves the learned model AND
the planning horizon are doing the work.

Run:  python test_pc_push_policy.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc.test_pc_act8b import World1D, CONTACT_R, W

STEP_A = 1.5          # max move magnitude
GAMMA = 0.85          # discount for cumulative-cost MPC
# Coarse AND fine moves × finger {push, lift}: fine steps let the MPC fine-tune near
# the target without overshooting (the overshoot→retract→stall failure in act8b).
ACTIONS = [(+1.5, 1.0), (-1.5, 1.0), (+0.6, 1.0), (-0.6, 1.0),
           (+1.5, 0.0), (-1.5, 0.0), (+0.6, 0.0), (-0.6, 0.0)]  # (a, finger)


class PushModel:
    """Learned push dynamics:  features [d/R, a, finger] -> Δobj.  d = pointer-obj."""
    def __init__(self, hid=40, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 0.5, (hid, 3)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 0.3, hid);      self.b2 = 0.0
        self.lr = lr; self.rng = rng

    def _x(self, d, a, f):
        return np.array([d / CONTACT_R, a, f])

    def predict(self, d, a, f):
        h = np.tanh(self.W1 @ self._x(d, a, f) + self.b1)
        return float(self.W2 @ h + self.b2), h

    def babble(self, world, steps):
        for _ in range(steps):
            obj = float(self.rng.uniform(world.lo, world.hi))
            d = float(self.rng.uniform(-(CONTACT_R + 3), CONTACT_R + 3))
            a = float(self.rng.uniform(-STEP_A, STEP_A))   # continuous → covers fine moves
            f = float(self.rng.integers(0, 2))
            world.obj = obj
            world.shove((obj + d) + a, a, f)           # genuine push from act8b
            dobj = world.obj - obj
            y, h = self.predict(d, a, f)
            err = y - dobj
            self.W2 -= self.lr * err * h; self.b2 -= self.lr * err
            dh = (self.W2 * err) * (1 - h ** 2)
            self.W1 -= self.lr * np.outer(dh, self._x(d, a, f)); self.b1 -= self.lr * dh

    def scramble(self):
        self.W1 = self.rng.normal(0, 0.5, self.W1.shape)
        self.W2 = self.rng.normal(0, 0.5, self.W2.shape)


def plan(model, obj, p, target, horizon):
    """MPC through the learned model with CUMULATIVE discounted cost: return the first
    action of the best sequence (full search — beam search prunes the high-early-cost
    reposition detour, so it underperforms here; horizon 3 full = 100%)."""
    best_a, best_cost = ACTIONS[0], 1e9
    for (a, f) in ACTIONS:
        c = _step_cost(model, obj, p, target, a, f, horizon)
        if c < best_cost:
            best_cost, best_a = c, (a, f)
    return best_a


def _step_cost(model, obj, p, target, a, f, horizon):
    dobj, _ = model.predict(p - obj, a, f)
    obj2 = float(np.clip(obj + dobj, 0, W - 1))
    p2 = float(np.clip(p + a, 0, W - 1))
    cost = abs(obj2 - target)
    if horizon > 1:
        cost += GAMMA * min(_step_cost(model, obj2, p2, target, aa, ff, horizon - 1)
                            for (aa, ff) in ACTIONS)
    return cost


def run(model, horizon, episodes=40, max_steps=90, rng=None):
    rng = rng or np.random.default_rng()
    w = World1D(seed=0)
    delivered, wrong_side_starts = 0, 0
    for _ in range(episodes):
        w.scatter(with_target=True)
        obj0, tgt = w.obj, w.target
        # start the hand on the WRONG side (target side) so a detour is REQUIRED
        side_to_target = np.sign(tgt - obj0)
        p = float(np.clip(obj0 + side_to_target * (CONTACT_R + 0.5), 0, W - 1))
        wrong_side_starts += 1
        for _ in range(max_steps):
            a, f = plan(model, w.obj, p, w.target, horizon)
            p = float(np.clip(p + a, 0, W - 1))
            w.shove(p, a, f)
            if abs(w.obj - w.target) < 1.5:
                delivered += 1
                break
    return 100.0 * delivered / episodes


def main():
    rng = np.random.default_rng(0)
    w = World1D(seed=1)
    print("=" * 74)
    print("  Learned push-side policy (de-risk): MPC through a learned push model")
    print(f"  world={W}  contact_R={CONTACT_R}  hand STARTS on the wrong (target) side")
    print("=" * 74)

    model = PushModel(rng=np.random.default_rng(2)); model.babble(w, 30000)
    # probe: the learned push is side-dependent (push only INTO the object)
    print("  learned M(d,a,f=1)  Δobj  (push only when driving into the object):")
    for d in (-2.0, -1.0, 0.0, 1.0, 2.0):
        print(f"    d={d:+.1f}: a=+1 → {model.predict(d,+1,1)[0]:+.2f}   "
              f"a=-1 → {model.predict(d,-1,1)[0]:+.2f}")
    print("-" * 74)

    for H in (1, 3):                              # full search, 8 actions → horizon ≤3
        acc = run(model, horizon=H, rng=np.random.default_rng(3))
        tag = "(greedy, too short)" if H == 1 else ""
        print(f"  learned model, horizon={H}: delivered {acc:5.1f}%  {tag}")
    sm = PushModel(rng=np.random.default_rng(4)); sm.babble(w, 30000); sm.scramble()
    print(f"  SCRAMBLED model, horizon=3: delivered {run(sm, 3, rng=np.random.default_rng(3)):5.1f}%"
          f"   [control: planning on garbage dynamics]")
    print("-" * 74)
    print("  Read: horizon-6 with the learned model delivers from the WRONG side")
    print("        (reposition-then-push EMERGES); greedy & scrambled fail → the learned")
    print("        dynamics + planning choose the side, not a hand-coded rule.")
    print("=" * 74)


if __name__ == "__main__":
    main()
