r"""
pc_act16.py — manipulation with CLAWS: GRASP first, PUSH as fallback (user's idea).

Per the user's live observation: with the curved CLAWS the arm sometimes GRASPS the cube and
carries it well; when it misses, it should fall back to PUSHing the cube from behind with the
(slightly-closed) claws.  So this combines both and we can later see which the net learns better:
  1. GRASP:  open claws above the cube -> lower -> close -> lift.  If the cube came up -> CARRY
     it to the target and place it.
  2. PUSH (fallback, if the grasp missed): pre-closed claws approach from behind and push the
     cube to the target by genuine contact (the inward claw tips cup it).
The reach uses the LEARNED 3-D kinematics to the `contact` site (claw notch).  A visible target
marker (mocap disk) is placed on the table.  Perception is privileged sim state (camera = act15).

  ACT16_HEADLESS=1   metrics over episodes     ACT16_TARGET=obj_red|...   commanded cube
  ACT16_MODE=both|grasp|push                    (default both = grasp-then-push)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, HOME, _rand_xy, CamViz, REACH_XY

J5_OPEN, J5_GRIP, J5_PUSH = 1.8, 0.0, 0.12     # open / fully-closed (grip) / nearly-closed (push)
OBJS = ["obj_red", "obj_green", "obj_blue"]
OVER_Z, GRASP_Z, CARRY_Z, PUSH_Z = 0.06, 0.014, 0.055, 0.016
STANDOFF, NEAR, TOL, CAP = 0.045, 0.02, 0.025, 2200
PERSIST = os.environ.get("ACT16_PERSIST", "0") == "1"        # keep the scene between episodes


def run_combined(sim, body, viz, CAM, episodes=12, cmd_fixed=None, force=None):
    rng = np.random.default_rng(1)
    STRAY_LO, STRAY_HI = REACH_XY[0] - 0.03, REACH_XY[1] + 0.03   # valid table area (patch + margin)

    def others(nm):
        return [o for o in OBJS if o != nm]

    def clear(p, names, gap):
        return all(np.linalg.norm(p - sim.obj_pos(o)[:2]) > gap for o in names)

    def scatter():
        pts = []
        for nm in OBJS:
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.06 for q in pts):
                p = _rand_xy(rng)
            pts.append(p); sim.set_object(nm, p)
        mujoco.mj_forward(sim.m, sim.d); sim.step(150)

    def reposition_strays():
        """Any cube that wandered out of the valid area is dropped back inside (clear of others)."""
        moved = False
        for nm in OBJS:
            p = sim.obj_pos(nm)[:2]
            if np.any(p < STRAY_LO) or np.any(p > STRAY_HI):
                q = _rand_xy(rng)
                while not clear(q, others(nm), 0.06):
                    q = _rand_xy(rng)
                sim.set_object(nm, q); moved = True
        if moved:
            mujoco.mj_forward(sim.m, sim.d); sim.step(80)

    if PERSIST:
        sim.reset_home(); scatter()
    n_grasp = n_push = deliveries = 0
    for ep in range(episodes):
        if PERSIST:
            sim.arm_home(); reposition_strays()
        else:
            sim.reset_home(); scatter()
        sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        cmd = cmd_fixed or OBJS[ep % len(OBJS)]               # cycle which cube to fetch
        c0 = sim.obj_pos(cmd)[:2]
        tgt = _rand_xy(rng)                                  # target: away from the cube AND not on any cube
        while np.linalg.norm(tgt - c0) < 0.06 or not clear(tgt, OBJS, 0.05):
            tgt = _rand_xy(rng)
        sim.set_target_marker(tgt); sim.step(40)
        mode = force or "grasp"; phase = "over" if mode == "grasp" else "approach"
        dwell = 0; via = "grasp"; done = False
        for k in range(CAP):
            c = sim.obj_pos(cmd)[:2]; cz = sim.obj_pos(cmd)[2]; h = sim.grasp_pos(); hxy = h[:2]; hz = h[2]
            if via == "push" and np.linalg.norm(c - tgt) < TOL:  # pushed home -> done
                break
            d = tgt - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])

            if mode == "grasp":
                via = "grasp"
                if phase == "over":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], OVER_Z])
                    if np.linalg.norm(hxy - c) < NEAR:
                        phase = "lower"
                elif phase == "lower":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], GRASP_Z])
                    if hz < GRASP_Z + 0.010:
                        phase, dwell = "close", 0
                elif phase == "close":
                    dwell += 1                                    # close SLOWLY (ramp) so the
                    frac = min(1.0, dwell / 60.0)                 # claws don't shove the cube
                    j5 = J5_OPEN + (J5_GRIP - J5_OPEN) * frac
                    aim = np.array([c[0], c[1], GRASP_Z])
                    if dwell > 90:
                        phase = "lift"
                elif phase == "lift":
                    j5, aim = J5_GRIP, np.array([hxy[0], hxy[1], CARRY_Z])
                    if hz > CARRY_Z - 0.015:
                        if cz > 0.030:                            # cube clearly lifted off the table
                            phase = "carry"                      # grasped!
                        else:
                            mode, phase = "push", "approach"      # missed -> push fallback
                elif phase == "carry":
                    j5, aim = J5_GRIP, np.array([tgt[0], tgt[1], CARRY_Z])
                    if np.linalg.norm(hxy - tgt) < NEAR:
                        phase = "place"
                elif phase == "place":
                    j5, aim = J5_GRIP, np.array([tgt[0], tgt[1], GRASP_Z])
                    if hz < GRASP_Z + 0.012:
                        phase, dwell = "release", 0
                else:  # release
                    j5, aim, dwell = J5_OPEN, np.array([tgt[0], tgt[1], GRASP_Z]), dwell + 1
                    if dwell > 50:
                        break
            else:  # push fallback (pre-closed claws, approach from behind, push)
                via = "push"
                behind = c - d * STANDOFF
                if phase == "approach":
                    j5, aim = J5_PUSH, np.array([behind[0], behind[1], PUSH_Z])
                    if np.linalg.norm(hxy - behind) < NEAR and np.dot(hxy - c, d) < 0:
                        phase = "push"
                else:  # push
                    ahead = c + d * 0.02
                    j5, aim = J5_PUSH, np.array([ahead[0], ahead[1], PUSH_Z])
                    if np.dot(hxy - c, d) > 0.02 or np.linalg.norm(hxy - c) > 0.06:
                        phase = "approach"

            sim.target("joint_5", j5)
            g, mdq = (0.9, 0.010) if via == "push" else (2.0, 0.026)   # push gently (don't knock)
            q3 = sim.arm3_angles(); sim.set_arm3_targets(q3 + body.reach_velocity(q3, aim, gain=g, max_dq=mdq))
            sim.step(2)
            if viz is not None and k % 5 == 0:
                viz.update(sim.render(CAM), f"ep {ep} {via} {cmd} [{phase}]"
                                            f"  obj->tgt {np.linalg.norm(c-tgt)*1000:.0f}mm")
        err = np.linalg.norm(sim.obj_pos(cmd)[:2] - tgt)
        ok = err < TOL
        deliveries += ok; n_grasp += (via == "grasp" and ok); n_push += (via == "push" and ok)
        print(f"  ep {ep:2d}: {'OK ' if ok else 'no '} via {via:5s}  obj->tgt {err*1000:.0f} mm")
    print(f"  == combined grasp-then-push: DELIVERED {deliveries}/{episodes}  "
          f"(by grasp {n_grasp}, by push {n_push}) ==")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


def main():
    HEADLESS = os.environ.get("ACT16_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT16_CAM", "overview").lower()
    TARGET = os.environ.get("ACT16_TARGET", "") or None       # fix one cube, or None = cycle all
    EPISODES = int(os.environ.get("ACT16_EPISODES", "12"))
    MODE = os.environ.get("ACT16_MODE", "both").lower()
    force = None if MODE == "both" else MODE                  # grasp | push to force one branch

    print(f"act16 — manipulation with CLAWS: grasp-then-push  (mode={MODE})")
    sim = BracketArmSim()
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (to the contact point) ...")
    body.babble(sim, 4000)
    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless")
    run_combined(sim, body, viz, CAM, episodes=EPISODES, cmd_fixed=TARGET, force=force)


if __name__ == "__main__":
    main()
