r"""
test_pc_planner.py — Option 1: a PLANNER that DREAMS a goal from the current state.

The goal-prior machinery is solved (act6 / dream_goal): given a goal LATENT, the
object is transported to it.  The open question was "WHICH latent to dream".  This
test adds the next PC layer on top of the goal module — a Planner — and gives it a
concrete, reward-supervised criterion: it learns the mapping

    current state  ->  the goal latent that was 'rewarded' for that state.

Architecture (Planner net, sitting on top of a pretrained act6 GoalModule):
    p_state   (Sensor, dim=S+flags) — current object position (blob) + conditioning flags
    plan_z    (PCNode, dim=P, tanh) — the planner's own top latent
    plan_g_z  (PCNode, dim=Z)       — the goal-module latent it PREDICTS
    plan_z -> p_state   (decoder : ground the latent in the situation)
    plan_z -> plan_g_z  (predict the goal latent for this situation)

Train: clamp (state, rewarded-goal-latent) pairs, relax, learn — plan_z becomes a
joint code of (situation, its goal).  Dream: clamp state only, relax, read plan_g_z,
hand it to GoalModule.decode_dream -> desired world-position -> carry the object there.

The "rewarded goal" is a state-dependent RULE (mirror: goal = WORLD - obj), so the
planner must learn a non-constant map, not memorise one goal.  A baseline (untrained
weights) and a conditioning experiment (a flag switches mirror<->centre) round it out.

Run:  python test_pc_planner.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule
from pc.test_pc_act6 import GoalModule

WORLD = 48.0
S = 16     # state-image width (object position as a blob)
P = 10     # planner latent dim
Z = 6      # goal-module latent dim (MUST match the GoalModule latent)
FLAG_AMP = 4.0   # conditioning-flag amplitude (vs blob peak 1.0) — see Planner._state_vec


def blob(pos: float, n: int = S, world: float = WORLD, sigma: float = 1.0) -> np.ndarray:
    c = pos / world * (n - 1)
    x = np.arange(n)
    return np.exp(-0.5 * ((x - c) / sigma) ** 2)


def carry_to(desired: float, start: float, *, gain=0.15, vmax=2.0,
             grab=1.5, tol=1.5, max_steps=500) -> float:
    """act6 synced rigid grab-carry: return final |obj - desired|."""
    obj = p = float(start)
    for _ in range(max_steps):
        if abs(p - obj) < grab:
            vp = float(np.clip(gain * (desired - obj), -vmax, vmax))
            obj = float(np.clip(obj + vp, 0.0, WORLD)); p = float(np.clip(p + vp, 0.0, WORLD))
        else:
            vp = float(np.clip(gain * (obj - p), -vmax, vmax))
            p = float(np.clip(p + vp, 0.0, WORLD))
        if abs(obj - desired) < tol:
            break
    return abs(obj - desired)


class Planner:
    """A PC layer above the goal module: state -> dreamed goal latent."""

    def __init__(self, gm: GoalModule, n_flags: int = 0,
                 rng: np.random.Generator | None = None) -> None:
        self.gm = gm
        self.n_flags = n_flags
        self.dim_state = S + n_flags
        rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=80, eps_tol=1e-6, alpha=1.0, beta=1.0,
                        gamma=0.3, eta_learn=0.01, lambda_decay=0.0, w_clip=3.0, rng=rng)
        self.state  = net.add(SensorNode("p_state", dim=self.dim_state))
        self.plan_z = net.add(PCNode("plan_z", dim=P, activation="tanh",
                                     eta_temporal=0.0, rng=rng))
        self.goal_z = net.add(PCNode("plan_g_z", dim=Z, activation="identity",
                                     eta_temporal=0.0, rng=rng))
        net.connect("plan_z", "p_state",  ConnType.UP, pressure_scale=1.0)  # decode state
        net.connect("plan_z", "plan_g_z", ConnType.UP, pressure_scale=1.5)  # predict goal (tighter)
        self.net = net

        # Precompute the goal module's latent over a grid (fast lookup, no per-step relax).
        self._grid = np.linspace(0.03 * WORLD, 0.97 * WORLD, 60)
        self._zgrid = np.array([gm.encode(p) for p in self._grid])

    def goal_latent(self, g: float) -> np.ndarray:
        """Interpolate the goal-module latent for world-position g."""
        return np.array([np.interp(g, self._grid, self._zgrid[:, k]) for k in range(Z)])

    def _state_vec(self, obj: float, flags=()) -> np.ndarray:
        # Flags amplified so a single conditioning channel is not drowned out by the
        # S state pixels during plan_z inference (gives the flag real steering power).
        return np.concatenate([blob(obj), FLAG_AMP * np.asarray(flags, dtype=float)])

    def train(self, sample_fn, steps: int) -> None:
        """sample_fn() -> (obj_world, flags_tuple, rewarded_goal_world)."""
        for _ in range(steps):
            obj, flags, g = sample_fn()
            self.state.set_input(self._state_vec(obj, flags))
            self.goal_z.clamp(self.goal_latent(g))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()
        self.goal_z.unclamp()

    def dream(self, obj: float, flags=()) -> float:
        """Clamp state only, relax, read the predicted goal latent, decode to a pos."""
        self.goal_z.unclamp()
        self.state.set_input(self._state_vec(obj, flags))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self.gm.decode_dream(self.goal_z.mu.copy())


def evaluate(planner: Planner, rule, *, flags_fn=lambda obj: (), n=60):
    """Across the world: dreamed goal vs rule target, slope, transport error."""
    objs = np.linspace(0.1 * WORLD, 0.9 * WORLD, n)
    dreamed = np.array([planner.dream(o, flags_fn(o)) for o in objs])
    target  = np.array([rule(o) for o in objs])
    rule_err = float(np.mean(np.abs(dreamed - target)))
    # slope of dreamed vs obj — tells us the map is state-dependent (mirror -> ~ -1).
    slope = float(np.polyfit(objs, dreamed, 1)[0])
    transport = float(np.mean([carry_to(d, o) for d, o in zip(dreamed, objs)]))
    return rule_err, slope, transport, objs, dreamed, target


def main() -> None:
    rng = np.random.default_rng(0)
    gm = GoalModule(WORLD, img=16, latent=Z, activation="identity",
                    rng=np.random.default_rng(7))
    gm.pretrain(15000)
    print("=" * 78)
    print("  Planner (Option 1): dream a goal from the current state")
    print(f"  world={WORLD:.0f}px  state={S}px  plan_z={P}  goal_z={Z}"
          f"   gm decode_err={gm.decode_error():.2f}px")
    print("=" * 78)

    mirror = lambda o: WORLD - o          # rewarded rule: send object to the mirror pos
    centre = lambda o: WORLD / 2.0

    # ---- A) untrained baseline: weights random -> dreamed goal is not the rule ----
    base = Planner(gm, n_flags=0, rng=np.random.default_rng(1))
    a = evaluate(base, mirror)
    print(f"  A) untrained baseline  : rule_err={a[0]:5.1f}px  slope={a[1]:+.2f}"
          f"  transport={a[2]:.2f}px   (expect large err, slope~0)")

    # ---- B) trained on the mirror rule (state-dependent goal) ----
    pl = Planner(gm, n_flags=0, rng=np.random.default_rng(1))
    pl.train(lambda: (lambda o: (o, (), mirror(o)))(float(rng.uniform(0.1, 0.9) * WORLD)),
             steps=9000)
    b = evaluate(pl, mirror)
    print(f"  B) trained: MIRROR rule: rule_err={b[0]:5.1f}px  slope={b[1]:+.2f}"
          f"  transport={b[2]:.2f}px   (expect small err, slope~-1)")
    print("-" * 78)
    print("     obj -> dreamed goal (should track WORLD-obj):")
    for i in range(0, len(b[3]), 12):
        print(f"       obj={b[3][i]:5.1f}  dreamed={b[4][i]:5.1f}  target={b[5][i]:5.1f}")

    # ---- C) conditioning: 1 flag switches the rule (mirror <-> centre) ----
    print("-" * 78)
    cond = Planner(gm, n_flags=1, rng=np.random.default_rng(2))

    def cond_sample():
        o = float(rng.uniform(0.1, 0.9) * WORLD)
        f = int(rng.integers(0, 2))
        g = mirror(o) if f == 0 else centre(o)
        return o, (float(f),), g

    cond.train(cond_sample, steps=12000)
    c0 = evaluate(cond, mirror, flags_fn=lambda o: (0.0,))
    c1 = evaluate(cond, centre, flags_fn=lambda o: (1.0,))
    print("  C) conditioning flag steers the dreamed goal (same net, same states):")
    print(f"     flag=0 -> MIRROR : rule_err={c0[0]:5.1f}px  slope={c0[1]:+.2f}")
    print(f"     flag=1 -> CENTRE : rule_err={c1[0]:5.1f}px  slope={c1[1]:+.2f}"
          f"  (centre -> slope~0, dreamed~{WORLD/2:.0f})")
    print("-" * 78)
    print("  Read: B beats A -> the planner LEARNS a state-dependent goal map;")
    print("        small transport -> dreamed goals are actionable;")
    print("        C: one flag flips the dreamed goal -> the net is steerable from outside.")
    print("=" * 78)


if __name__ == "__main__":
    main()
