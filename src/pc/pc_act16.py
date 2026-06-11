r"""
pc_act16.py — PUSH manipulation with CLAWS (revisits act14's blocked push).

act14's push failed for two reasons: (1) block fingers let the cube squirt sideways, and
(2) the control point was the grasp site (10 cm offset), not where contact happens.  Fixes:
  * CLAWS: the fingers now have inward-curved tips (bracket_arm.xml) that, slightly closed,
    form a concave POCKET — the cube self-centres in it instead of escaping sideways.
  * CONTACT POINT: the learned 3-D kinematics now reach the `contact` site (at the claw
    notch), so "put the contact behind the cube" really puts the CLAWS behind it.
The cube moves by genuine MuJoCo contact (no scripted shove).  Reach uses the LEARNED
kinematics (act14).  Perception is privileged sim state (camera = act15).

  ACT16_HEADLESS=1   metrics over episodes        ACT16_TARGET=obj_red|...   commanded cube
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, HOME, ARM3, _rand_xy, CamViz

J5_OPEN, J5_PUSH = 1.8, 0.1        # OPEN = claws spread+raised (clear cube); PUSH = nearly closed
#                                    (gap < cube width so the claws actually contact, tips cup it)
OBJS = ["obj_red", "obj_green", "obj_blue"]


def run_claw_push(sim, body, viz, CAM, episodes=12, cmd="obj_red"):
    rng = np.random.default_rng(1)
    REPOS_Z, PUSH_Z, STANDOFF, NEAR, TOL, CAP = 0.085, 0.016, 0.035, 0.02, 0.025, 1400
    deliveries = 0
    for ep in range(episodes):
        sim.reset_home(); sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        pts = []
        for nm in OBJS:
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.06 for q in pts):
                p = _rand_xy(rng)
            pts.append(p); sim.set_object(nm, p)
        tgt = _rand_xy(rng)
        while np.linalg.norm(tgt - pts[OBJS.index(cmd)]) < 0.06:
            tgt = _rand_xy(rng)
        mujoco.mj_forward(sim.m, sim.d); sim.step(150)
        pushing = False
        for k in range(CAP):
            c = sim.obj_pos(cmd)[:2]; h = sim.grasp_pos(); hxy = h[:2]
            if np.linalg.norm(c - tgt) < TOL:
                break
            d = tgt - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])
            behind = c - d * STANDOFF
            if not pushing:                                   # OPEN claws: approach from behind
                aim = np.array([behind[0], behind[1], REPOS_Z])
                if np.linalg.norm(hxy - behind) < NEAR and np.dot(hxy - c, d) < 0:
                    pushing = True
            else:                                             # claws cup the cube, push toward target
                ahead = c + d * 0.02
                aim = np.array([ahead[0], ahead[1], PUSH_Z])
                if np.dot(hxy - c, d) > 0.02 or np.linalg.norm(hxy - c) > 0.06:
                    pushing = False                           # cube escaped the pocket -> reposition
            sim.target("joint_5", J5_PUSH if pushing else J5_OPEN)
            g, mdq = (1.2, 0.012) if pushing else (2.0, 0.03)
            q3 = sim.arm3_angles(); sim.set_arm3_targets(q3 + body.reach_velocity(q3, aim, gain=g, max_dq=mdq))
            sim.step(2)
            if viz is not None and k % 5 == 0:
                viz.update(sim.render(CAM), f"ep {ep} claw-push {cmd} {'PUSH' if pushing else 'open'}"
                                            f"  obj->tgt {np.linalg.norm(c-tgt)*1000:.0f}mm")
        err = np.linalg.norm(sim.obj_pos(cmd)[:2] - tgt)
        deliveries += err < TOL
        print(f"  ep {ep:2d}: {'OK ' if err < TOL else 'no '} obj->tgt {err*1000:.0f} mm")
    print(f"  == claw-push (real contacts, concave claws, contact-point reach): "
          f"DELIVERED {deliveries}/{episodes} ==")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


def main():
    HEADLESS = os.environ.get("ACT16_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT16_CAM", "overview").lower()
    TARGET = os.environ.get("ACT16_TARGET", "obj_red")
    EPISODES = int(os.environ.get("ACT16_EPISODES", "12"))

    print("act16 — PUSH with CLAWS (concave pocket + contact-point reach)")
    sim = BracketArmSim()
    sim.set_reach_site("contact")                             # reach the CLAW notch, not the grasp site
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (to the contact point) ...")
    body.babble(sim, 4000)
    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless");
    run_claw_push(sim, body, viz, CAM, episodes=EPISODES, cmd=TARGET)


if __name__ == "__main__":
    main()
