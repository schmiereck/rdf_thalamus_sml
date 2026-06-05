r"""
test_pc_goal_module.py — Goal MODULE with its own learned latent "language".

Extends test_pc_goal_reach: the goal is no longer a ready-made (x,y) vector but a
goal IMAGE fed into a dedicated GoalModule that encodes it into a small LATENT
code — the module's own "language".  The downstream AgentModule learns, purely
through its connection to that latent, to interpret the language and act to reach
the goal.  Because the latent is its own node space, a goal can later be specified
(or DREAMED) directly in latent space, with no image at all.

Architecture
------------
  GoalModule:
    goal_img (Sensor, dim=W)  — the shown goal image (a blob at the target pos)
    goal_z   (PCNode, dim=Z)  — the latent code = the module's "language"
    goal_z → goal_img (UP)    — decoder: latent reconstructs the image (learned)
  AgentModule:
    belief   (PCNode, dim=B)  — the agent's state estimate
    pos      (Sensor, dim=1)  — current proprioceptive position
    goal_z → belief (UP)      — the language link the agent LEARNS to interpret
    belief → pos    (UP)      — forward model: state predicts position (learned)

Inference clamps the shown image → goal_z encodes it → drives belief → belief
predicts pos → error vs current → action moves the agent (active inference).

Three goal-delivery modes:
  A) shown  : clamp goal_img = blob(target)         (goal given as an image)
  B) control: clamp goal_img = blob(current)        (no goal → no error → no drive)
  D) DREAM  : clamp goal_z = z* directly, no image   (goal specified in latent space)

All mappings (decoder, language link, forward model) are LEARNED in a babble
phase where the goal image shows the current position.

Run:  python test_pc_goal_module.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule

W = 9      # goal-image width (pixels)
Z = 3      # latent "language" dimension
B = 3      # belief dimension


def blob(p: float, w: int = W, sigma: float = 1.0) -> np.ndarray:
    """Soft gaussian blob centred at p∈[0,1] over a w-pixel image (peak 1)."""
    c = p * (w - 1)
    x = np.arange(w)
    return np.exp(-0.5 * ((x - c) / sigma) ** 2)


def build(rng: np.random.Generator):
    net = PCNetwork(
        eta_inf=0.1, n_relax=80, eps_tol=1e-6, alpha=1.0, beta=1.0,
        gamma=0.3, eta_learn=0.01, lambda_decay=0.0, w_clip=3.0, rng=rng,
    )
    goal_img = net.add(SensorNode("goal_img", dim=W))
    goal_z   = net.add(PCNode("goal_z", dim=Z, activation="tanh", rng=rng))
    belief   = net.add(PCNode("belief", dim=B, activation="identity", rng=rng))
    pos      = net.add(SensorNode("pos", dim=1))

    net.connect("goal_z", "goal_img", ConnType.UP, pressure_scale=1.0)  # decoder
    net.connect("goal_z", "belief",   ConnType.UP, pressure_scale=1.0)  # language link
    net.connect("belief", "pos",      ConnType.UP, pressure_scale=1.0)  # forward model

    goal_mod = PCModule("GoalModule")
    (goal_mod.add_in_port("image", ["goal_img"])
             .add_out_port("code", ["goal_z"]))
    net.add_module(goal_mod)
    agent_mod = PCModule("AgentModule")
    (agent_mod.add_in_port("code", ["goal_z"])
              .add_out_port("position", ["pos"]))
    net.add_module(agent_mod)
    return net, goal_img, goal_z, belief, pos


def babble(net, goal_img, pos, rng, steps: int) -> None:
    """Learn decoder + language link + forward model: random-walk with the goal
    image showing the CURRENT position (goal == current), so the whole chain
    image→z→belief→pos is learned consistently."""
    agent = float(rng.uniform(0.2, 0.8))
    for _ in range(steps):
        agent = float(np.clip(agent + rng.normal(0.0, 0.05), 0.0, 1.0))
        goal_img.set_input(blob(agent))
        pos.set_input(np.array([agent]))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        net.phase_learn(); net.commit_step()


def encode(net, goal_img, goal_z, g: float) -> np.ndarray:
    """Encode a goal image into the latent language (one inference pass)."""
    goal_img.set_input(blob(g))
    net.phase_predict(); net.phase_error(); net.phase_relax()
    return goal_z.mu.copy()


def reach(net, goal_img, goal_z, pos, g, start, *, mode: str,
          z_star=None, gain=0.3, max_steps=120, tol=0.05):
    """One reaching episode.  mode ∈ {shown, control, dream}."""
    if mode == "dream":
        goal_img.unclamp()
        goal_z.clamp(z_star)
    agent = float(start)
    for t in range(max_steps):
        if mode == "shown":
            goal_img.set_input(blob(g))
        elif mode == "control":
            goal_img.set_input(blob(agent))        # goal == current → no error
        pos.set_input(np.array([agent]))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        eps = float(net.node("pos").epsilon[0])
        agent = float(np.clip(agent - gain * eps, 0.0, 1.0))
        net.commit_step()
        if abs(agent - g) < tol:
            break
    if mode == "dream":
        goal_z.unclamp()
        goal_img.clamp(blob(0.5))                  # restore a clamped sensor
    return abs(agent - g), t + 1, abs(agent - g) < tol


def run(net, goal_img, goal_z, pos, rng, *, mode, episodes, **kw):
    dists, steps, reached = [], [], 0
    for _ in range(episodes):
        g = float(rng.uniform(0.1, 0.9))
        start = float(rng.uniform(0.1, 0.9))
        z_star = encode(net, goal_img, goal_z, g) if mode == "dream" else None
        d, s, ok = reach(net, goal_img, goal_z, pos, g, start,
                         mode=mode, z_star=z_star, **kw)
        dists.append(d); steps.append(s); reached += int(ok)
    return (100.0 * reached / episodes, float(np.mean(dists)), float(np.mean(steps)))


def main() -> None:
    rng = np.random.default_rng(0)
    net, goal_img, goal_z, belief, pos = build(rng)
    print("=" * 76)
    print("  Goal MODULE with a learned latent 'language'  (1-D reach via goal image)")
    print(f"  image W={W}  latent Z={Z}  belief B={B}   start-dist baseline ≈ 0.40")
    print("=" * 76)
    print(net.summary().splitlines()[0])

    babble(net, goal_img, pos, rng, steps=8000)

    a = run(net, goal_img, goal_z, pos, rng, mode="shown",   episodes=300)
    b = run(net, goal_img, goal_z, pos, rng, mode="control", episodes=300)
    d = run(net, goal_img, goal_z, pos, rng, mode="dream",   episodes=300)
    print(f"  A) shown goal image      : reached={a[0]:5.1f}%  final_dist={a[1]:.3f}  steps={a[2]:.1f}")
    print(f"  B) control (no goal)     : reached={b[0]:5.1f}%  final_dist={b[1]:.3f}  steps={b[2]:.1f}")
    print(f"  D) DREAM (latent only)   : reached={d[0]:5.1f}%  final_dist={d[1]:.3f}  steps={d[2]:.1f}")

    # Show the latent code is a smooth, meaningful map of position.
    zs = np.array([encode(net, goal_img, goal_z, p) for p in np.linspace(0.1, 0.9, 9)])
    print("-" * 76)
    print("  latent code z per position (0.1 … 0.9):")
    for i, p in enumerate(np.linspace(0.1, 0.9, 9)):
        print(f"    p={p:.2f} → z=[{zs[i,0]:+.2f} {zs[i,1]:+.2f} {zs[i,2]:+.2f}]")
    print("-" * 76)
    print("  Read: A reaches & B does not → the goal-image PRIOR drives action;")
    print("        D reaches with NO image → goals live in the latent 'language' (dreamable);")
    print("        z varies smoothly with position → the language is a usable code.")
    print("=" * 76)


if __name__ == "__main__":
    main()
