r"""
test_pc_planner_experience.py — can the planner LEARN its state->goal map from its
OWN experience, online, instead of a pre-defined rule?

So far the learned planner (test_pc_planner.py / act6 LearnedStateGoalNet) is trained
offline on (state, goal) pairs from a GIVEN rule.  The user's deeper vision: the
mapping should GROW OUT OF DOING — the agent pursues goals, and the net learns to
predict them from the perceived state, streamed and online (replay), eventually
DRIVING behaviour itself.  This closes the last conceptual loop.

There is a real failure mode: regressing a STOCHASTIC target distribution (e.g. raw
curiosity goals) collapses to its mean.  So this de-risk characterises WHEN online
experience-learning works:

  E1  structured teacher (a hidden deterministic state->goal rule): the net should
      learn it from streamed pairs (tracking error drops) and then DRIVE the loop
      stably (closed-loop distribution shift).
  E2  stochastic teacher (curiosity / novelty): the net likely COLLAPSES to the mean
      when it drives (low world coverage) — telling us experience-learning amortises
      a structured/conditioned policy, not raw exploration.

Reuses the act6 GoalModule + LearnedStateGoalNet (with the new online learn_pair).

Run:  python test_pc_planner_experience.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc.test_pc_act6 import GoalModule, LearnedStateGoalNet

WORLD = 48.0
LO, HI = 6.0, 42.0          # the act6 centered-3/4 band
Z = 6
NBINS = 12


def bin_of(p):
    return int(np.clip((p - LO) / (HI - LO) * NBINS, 0, NBINS - 1))


def make_net(gm, grid, zgrid, seed):
    return LearnedStateGoalNet(gm, LO, HI, grid, zgrid, n_flags=0,
                               rng=np.random.default_rng(seed))


def train_online(net, teacher, *, episodes, replay=120, batch=16,
                 explore_states=False, rng):
    """Stream (state -> teacher goal) pairs; learn online with a replay buffer.
    explore_states=False : the object pursues each goal, so the next state is where
                           it landed (genuinely self-generated trajectory).
    explore_states=True  : the object is re-placed randomly each episode, so the net
                           sees DIVERSE states (isolates state-diversity from policy).
    Returns the tracking-error curve on a held-out state grid vs the teacher."""
    buf = []
    obj = float(rng.uniform(LO, HI))
    probe = np.linspace(LO, HI, 15)
    curve = []
    for ep in range(episodes):
        g = teacher(obj)
        buf.append((obj, g))
        if len(buf) > replay:
            buf.pop(0)
        net.learn_pair(obj, (), g)
        for _ in range(batch):
            s, t = buf[rng.integers(0, len(buf))]
            net.learn_pair(s, (), t)
        obj = float(rng.uniform(LO, HI)) if explore_states else g
        if (ep + 1) % max(1, episodes // 6) == 0:
            err = np.mean([abs(net.dream(s, ()) - teacher(s)) for s in probe])
            curve.append((ep + 1, float(err)))
    return curve


def main():
    rng = np.random.default_rng(0)
    gm = GoalModule(WORLD, img=16, latent=Z, activation="identity",
                    rng=np.random.default_rng(7))
    gm.pretrain(15000)
    grid  = np.linspace(0.03 * WORLD, 0.97 * WORLD, 60)
    zgrid = np.array([gm.encode(p) for p in grid])
    print("=" * 78)
    print("  Experience-based learning of the state->goal map (online, self-generated)")
    print(f"  world={WORLD:.0f}px band=[{LO:.0f},{HI:.0f}] latent={Z}"
          f"  gm decode_err={gm.decode_error():.2f}px")
    print("=" * 78)

    # ---- E1: structured teacher (hidden mirror rule) ----
    mirror = lambda p: float(np.clip(LO + HI - p, LO, HI))
    print("  E1) structured teacher (hidden rule: goal = mirror of state)")
    for tag, expl in [("follow-policy (ping-pong, few states)", False),
                      ("explore-states (diverse states)",      True)]:
        net1 = make_net(gm, grid, zgrid, seed=1)
        curve = train_online(net1, mirror, episodes=600, explore_states=expl,
                             rng=np.random.default_rng(2))
        obj, drive_err = float(rng.uniform(LO, HI)), []
        for _ in range(60):
            g = net1.dream(obj, ()); drive_err.append(abs(g - mirror(obj))); obj = g
        print(f"      [{tag}]")
        print(f"        tracking err vs teacher: "
              + " ".join(f"ep{e}:{v:.1f}" for e, v in curve)
              + f"   closed-loop drive err={np.mean(drive_err):.2f}px")

    # ---- E2: stochastic teacher (curiosity) → collapse check ----
    visited = []
    def curiosity(_obj):
        cands = rng.uniform(LO, HI, 24)
        zc = [np.array([np.interp(p, grid, zgrid[:, k]) for k in range(Z)]) for p in cands]
        nov = [1.0 if not visited else min(np.linalg.norm(z - s) for s in visited) for z in zc]
        z = zc[int(np.argmax(nov))]
        visited.append(z)
        if len(visited) > 20:
            visited.pop(0)
        return float(np.clip(gm.decode_dream(z), LO, HI))

    net2 = make_net(gm, grid, zgrid, seed=3)
    train_online(net2, curiosity, episodes=600, rng=np.random.default_rng(4))
    # teacher-driven coverage (reset visited) vs net-driven coverage
    visited.clear()
    tcov = np.zeros(NBINS, bool)
    obj = float(rng.uniform(LO, HI))
    for _ in range(80):
        obj = curiosity(obj); tcov[bin_of(obj)] = True
    ncov = np.zeros(NBINS, bool)
    objs = []
    obj = float(rng.uniform(LO, HI))
    for _ in range(80):
        obj = net2.dream(obj, ()); ncov[bin_of(obj)] = True; objs.append(obj)
    print("  E2) stochastic teacher (curiosity / novelty)")
    print(f"      teacher-driven coverage = {tcov.mean():.2f}  of the world")
    print(f"      net-driven   coverage = {ncov.mean():.2f}"
          f"   net-driven obj range=[{min(objs):.0f},{max(objs):.0f}]"
          f"  std={np.std(objs):.1f}")
    print("-" * 78)
    print("  Read: E1 tracking error drops + low closed-loop error → online experience-")
    print("        learning works for a STRUCTURED policy. E2 net-driven coverage <<")
    print("        teacher → regressing stochastic curiosity COLLAPSES to the mean;")
    print("        experience-learning amortises a structured/conditioned policy.")
    print("=" * 78)


if __name__ == "__main__":
    main()
