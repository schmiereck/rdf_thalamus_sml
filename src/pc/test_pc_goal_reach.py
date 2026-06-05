r"""
test_pc_goal_reach.py — Minimal goal-as-prior reaching test (dark-room antidote).

Question
--------
In test_pc_act5 the agent falls into the "dark room": it minimises prediction
error by removing the object from view (dragging it away) and then sitting in the
quiet, error-free empty state, instead of doing the task.  The standard active-
inference remedy is a PRIOR over the preferred observation: clamp a GOAL state so
that "not at the goal" carries prediction error, and let error-minimising ACTION
drive the agent TO the goal (the empty/quiet state is no longer error-free).

This strips the idea to its core to test whether the principle works:

    A 2-D point agent.  A goal (gx, gy) is clamped as a top-down prior.  The
    proprioceptive prediction error (current − predicted≈goal) drives the action
    (move the point).  Does the agent reach arbitrary goals — and only because of
    the prior?

Architecture (3 nodes — "goal module → state → observation"):
    goal  (Sensor, dim2, clamped)   — the prior / "image in mind"
    belief(PCNode, dim2, identity)  — the agent's state estimate
    pos   (Sensor, dim2, clamped)   — current proprioceptive position
    goal → belief → pos  (UP)       — goal predicts the state, state predicts pos

Action (active inference): after relaxing, move the agent to reduce pos's
prediction error:  agent -= ACTION_GAIN · pos.epsilon  (pos.epsilon = current − π).
With belief pulled toward the goal, π ≈ goal, so the agent moves toward the goal;
at the goal the error is zero and the agent stops — a stable fixed point.

Conditions:
    A) with prior          → should reach the goal (final dist → 0)
    B) control, no prior   → goal = current each step (no error) → stays put
    C) scrambled fwd model, then re-babbled → reaches again (mapping is LEARNED)

Run:  python test_pc_goal_reach.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType


def build_net(rng: np.random.Generator) -> tuple:
    net = PCNetwork(
        eta_inf=0.1,
        n_relax=60,
        eps_tol=1e-6,
        alpha=1.0,
        beta=1.0,
        gamma=0.3,
        eta_learn=0.01,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )
    goal   = net.add(SensorNode("goal",   dim=2))
    belief = net.add(PCNode("belief", dim=2, activation="identity", rng=rng))
    pos    = net.add(SensorNode("pos",    dim=2))
    # goal (top) predicts belief; belief predicts pos (bottom observation).
    net.connect("goal",   "belief", ConnType.UP, pressure_scale=1.0)
    net.connect("belief", "pos",    ConnType.UP, pressure_scale=1.0)
    return net, goal, belief, pos


def babble(net, goal, pos, rng, steps: int) -> None:
    """Learn the forward model: random-walk with goal == current, so the net
    learns goal→belief→pos as an identity (it learns that 'where I am' is what it
    expects to see).  No goal-directed action here — pure forward-model learning."""
    agent = rng.uniform(0.2, 0.8, size=2)
    for _ in range(steps):
        agent = np.clip(agent + rng.normal(0.0, 0.05, size=2), 0.0, 1.0)
        goal.set_input(agent)        # during babble the goal IS the current pos
        pos.set_input(agent)
        net.phase_predict(); net.phase_error(); net.phase_relax()
        net.phase_learn(); net.commit_step()


def reach_episode(net, goal, pos, g, start, *, with_prior: bool,
                  action_gain: float, max_steps: int, tol: float) -> tuple:
    """One reaching episode.  Returns (final_distance, steps_taken, reached)."""
    agent = start.copy()
    for t in range(max_steps):
        # Prior: clamp the goal node to g.  Control: clamp it to the current pos
        # (goal == current → no prediction error → no goal-directed drive).
        goal.set_input(g if with_prior else agent)
        pos.set_input(agent)
        net.phase_predict(); net.phase_error(); net.phase_relax()
        # Active inference: move to reduce the proprioceptive prediction error.
        eps = net.node("pos").epsilon
        agent = np.clip(agent - action_gain * eps, 0.0, 1.0)
        net.commit_step()           # no learning during reaching (keep fwd model fixed)
        if np.linalg.norm(agent - g) < tol:
            return float(np.linalg.norm(agent - g)), t + 1, True
    return float(np.linalg.norm(agent - g)), max_steps, False


def run_reach(net, goal, pos, rng, *, with_prior: bool, episodes: int,
              action_gain=0.3, max_steps=80, tol=0.05) -> dict:
    dists, steps, reached = [], [], 0
    for _ in range(episodes):
        g     = rng.uniform(0.1, 0.9, size=2)
        start = rng.uniform(0.1, 0.9, size=2)
        d, s, ok = reach_episode(net, goal, pos, g, start, with_prior=with_prior,
                                 action_gain=action_gain, max_steps=max_steps, tol=tol)
        dists.append(d); steps.append(s); reached += int(ok)
    return {
        "mean_final_dist": float(np.mean(dists)),
        "reached_pct":     100.0 * reached / episodes,
        "mean_steps":      float(np.mean(steps)),
    }


def main() -> None:
    rng = np.random.default_rng(0)
    print("=" * 74)
    print("  Goal-as-prior reaching test  (2-D point; goal clamped as a prior)")
    print("  start-distance baseline ≈ 0.52 (random start vs random goal in [0.1,0.9])")
    print("=" * 74)

    # ---- A) with prior, after learning the forward model ----
    net, goal, belief, pos = build_net(rng)
    babble(net, goal, pos, rng, steps=4000)
    a = run_reach(net, goal, pos, rng, with_prior=True, episodes=300)
    print(f"  A) with prior (learned fwd model) : reached={a['reached_pct']:5.1f}%"
          f"  final_dist={a['mean_final_dist']:.3f}  steps={a['mean_steps']:.1f}")

    # ---- B) control: no prior (goal == current) ----
    b = run_reach(net, goal, pos, rng, with_prior=False, episodes=300)
    print(f"  B) control: NO prior              : reached={b['reached_pct']:5.1f}%"
          f"  final_dist={b['mean_final_dist']:.3f}  steps={b['mean_steps']:.1f}")

    # ---- C) scramble the forward model, re-babble, reach again ----
    for conn in net._connections:                      # perturb all weights
        conn.W += rng.normal(0.0, 1.0, size=conn.W.shape)
    c0 = run_reach(net, goal, pos, rng, with_prior=True, episodes=100)
    babble(net, goal, pos, rng, steps=4000)            # re-learn the mapping
    c1 = run_reach(net, goal, pos, rng, with_prior=True, episodes=300)
    print(f"  C) scrambled fwd model (broken)   : reached={c0['reached_pct']:5.1f}%"
          f"  final_dist={c0['mean_final_dist']:.3f}")
    print(f"  C) after re-babble (re-learned)   : reached={c1['reached_pct']:5.1f}%"
          f"  final_dist={c1['mean_final_dist']:.3f}  steps={c1['mean_steps']:.1f}")

    print("-" * 74)
    print("  Read: A reaches & B does not  → the PRIOR drives goal-directed action")
    print("        C broken→relearned      → the forward model is LEARNED, not wired")
    print("=" * 74)


if __name__ == "__main__":
    main()
