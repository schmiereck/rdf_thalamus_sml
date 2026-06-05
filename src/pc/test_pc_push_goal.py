r"""
test_pc_push_goal.py — De-risking step: GoalModule + finger/drag → transport an
OBJECT to a target in a small 1-D world.

Combines the three validated building blocks:
  * goal-as-prior drives goal-directed action       (test_pc_goal_reach)
  * GoalModule with a learned latent "language"      (test_pc_goal_module)
  * finger/drag actuator (carry, no impulse)         (test_pc_act5)

The crucial new question: in the reaching tests the agent moved ITSELF; here the
goal prior is on the OBJECT, and the agent must move the object INDIRECTLY by
grabbing it with the finger and dragging it.  Does a goal-prior on the object
(via the goal module) produce the right "desired object position" that a simple
grab-and-carry controller can transport to — for a shown goal image AND for a
goal dreamed purely in latent space?

Net:
  obj_img (Sensor, dim=W)  — current object position (blob)        [observation]
  goal_img(Sensor, dim=W)  — object-AT-target image (goal module input)
  goal_z  (PCNode, dim=Z)  — latent goal "language"
  belief  (PCNode, dim=B)  — belief about where the object is/should be
  goal_z→goal_img (decoder) ; goal_z→belief (language) ; belief→obj_img (fwd model)

Action: after relax, the network's predicted object position is decoded from
belief→obj_img (center of mass).  A grab-and-carry controller drives the pointer
to the object, the finger grabs (rigid drag = object carried by pointer
displacement), and carries it to the believed desired position.  With the goal
prior, that desired ≈ target, so the object is transported to the target.

Run:  python test_pc_push_goal.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule

W = 11     # image width
Z = 3      # latent language dim
B = 3      # belief dim
GRAB = 0.06        # finger grabs when |pointer - obj| < GRAB
P_GAIN = 0.25      # pointer approach/carry gain
VP_MAX = 0.05      # max pointer speed (slow enough that the drag keeps the grasp)


def blob(p: float, w: int = W, sigma: float = 1.0) -> np.ndarray:
    c = p * (w - 1)
    x = np.arange(w)
    return np.exp(-0.5 * ((x - c) / sigma) ** 2)


def com(img: np.ndarray) -> float:
    img = np.clip(img, 0.0, None)
    s = img.sum()
    return float((np.arange(len(img)) * img).sum() / s / (len(img) - 1)) if s > 1e-6 else 0.5


def build(rng, eta_temporal=0.0):
    net = PCNetwork(eta_inf=0.1, n_relax=80, eps_tol=1e-6, alpha=1.0, beta=1.0,
                    gamma=0.3, eta_learn=0.01, lambda_decay=0.0, w_clip=3.0, rng=rng)
    obj_img  = net.add(SensorNode("obj_img", dim=W))
    goal_img = net.add(SensorNode("goal_img", dim=W))
    goal_z   = net.add(PCNode("goal_z", dim=Z, activation="tanh",
                              eta_temporal=eta_temporal, rng=rng))
    belief   = net.add(PCNode("belief", dim=B, activation="identity",
                              eta_temporal=eta_temporal, rng=rng))
    net.connect("goal_z", "goal_img", ConnType.UP, pressure_scale=1.0)  # decoder
    net.connect("goal_z", "belief",   ConnType.UP, pressure_scale=2.0)  # language (prior strong)
    net.connect("belief", "obj_img",  ConnType.UP, pressure_scale=1.0)  # forward model
    gm = PCModule("GoalModule")
    gm.add_in_port("image", ["goal_img"]).add_out_port("code", ["goal_z"])
    net.add_module(gm)
    return net, obj_img, goal_img, goal_z, belief


def babble(net, obj_img, goal_img, rng, steps):
    """Learn decoder + language + forward model with goal == current object."""
    o = float(rng.uniform(0.2, 0.8))
    for _ in range(steps):
        o = float(np.clip(o + rng.normal(0.0, 0.05), 0.0, 1.0))
        obj_img.set_input(blob(o))
        goal_img.set_input(blob(o))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        net.phase_learn(); net.commit_step()


def encode(net, goal_img, goal_z, tgt):
    goal_img.set_input(blob(tgt))
    net.phase_predict(); net.phase_error(); net.phase_relax()
    return goal_z.mu.copy()


def push_episode(net, obj_img, goal_img, goal_z, tgt, obj0, p0, *,
                 mode, z_star=None, max_steps=200, tol=0.05):
    if mode == "dream":
        goal_img.unclamp(); goal_z.clamp(z_star)
    obj, p = float(obj0), float(p0)
    for t in range(max_steps):
        if mode == "shown":
            goal_img.set_input(blob(tgt))
        elif mode == "control":
            goal_img.set_input(blob(obj))          # goal == current object → no drive
        obj_img.set_input(blob(obj))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        desired = com(net.node("obj_img").pi)      # where the net believes the object should be
        # grab-and-carry controller
        grabbed = abs(p - obj) < GRAB
        p_target = desired if grabbed else obj     # carry to desired, else go grab the object
        vp = float(np.clip(P_GAIN * (p_target - p), -VP_MAX, VP_MAX))
        p_new = float(np.clip(p + vp, 0.0, 1.0))
        if grabbed:
            obj = float(np.clip(obj + (p_new - p), 0.0, 1.0))   # rigid drag: object carried
        p = p_new
        net.commit_step()
        if abs(obj - tgt) < tol:
            break
    if mode == "dream":
        goal_z.unclamp(); goal_img.clamp(blob(0.5))
    return abs(obj - tgt), t + 1, abs(obj - tgt) < tol


def run(net, obj_img, goal_img, goal_z, rng, *, mode, episodes):
    dists, steps, ok = [], [], 0
    for _ in range(episodes):
        tgt  = float(rng.uniform(0.15, 0.85))
        obj0 = float(rng.uniform(0.15, 0.85))
        p0   = obj0                                   # start the pointer on the object
        z = encode(net, goal_img, goal_z, tgt) if mode == "dream" else None
        d, s, r = push_episode(net, obj_img, goal_img, goal_z, tgt, obj0, p0,
                               mode=mode, z_star=z)
        dists.append(d); steps.append(s); ok += int(r)
    return 100.0 * ok / episodes, float(np.mean(dists)), float(np.mean(steps))


def main():
    rng = np.random.default_rng(0)
    net, obj_img, goal_img, goal_z, belief = build(rng)
    print("=" * 76)
    print("  Push-to-goal via GoalModule + finger/drag  (1-D; object transported)")
    print(f"  image W={W}  latent Z={Z}   start |obj-tgt| baseline ≈ 0.34")
    print("=" * 76)
    babble(net, obj_img, goal_img, rng, steps=8000)
    a = run(net, obj_img, goal_img, goal_z, rng, mode="shown",   episodes=300)
    b = run(net, obj_img, goal_img, goal_z, rng, mode="control", episodes=300)
    d = run(net, obj_img, goal_img, goal_z, rng, mode="dream",   episodes=300)
    print(f"  A) shown goal image    : reached={a[0]:5.1f}%  final|obj-tgt|={a[1]:.3f}  steps={a[2]:.1f}")
    print(f"  B) control (no goal)   : reached={b[0]:5.1f}%  final|obj-tgt|={b[1]:.3f}  steps={b[2]:.1f}")
    print(f"  D) DREAM (latent only) : reached={d[0]:5.1f}%  final|obj-tgt|={d[1]:.3f}  steps={d[2]:.1f}")
    print("-" * 76)
    print("  Read: A/D transport the object to target & B does not")
    print("        → a goal prior on the OBJECT drives the finger to push it there.")
    print("=" * 76)


if __name__ == "__main__":
    main()
