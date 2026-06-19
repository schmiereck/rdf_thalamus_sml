r"""test_pc_wrist_roll.py — STEP 1 of the wrist-roll (joint_4) extension: the LEARNED orientation kinematics.

The position kinematics (ArmBodyModel3D) maps the 3 positioning joints -> hand xyz and ignores the gripper
ORIENTATION.  joint_4 (wrist-roll) rotates the finger-separation axis in the table plane -- the orientation
the claws grip ALONG.  It was frozen at home because a cube is symmetric; to grip an ELONGATED object the
claws must align to its narrow axis, which needs this DOF + a model of what it does.

Here the agent LEARNS that orientation kinematics the SAME way it learned the position kinematics -- by
BABBLING (random joint poses -> read the achieved claw yaw -> fit a net), with NO analytic rotation algebra.
Validated honestly END-TO-END: ask the learned model which joint_4 gives a desired grip yaw, command it on
the REAL arm, measure the achieved yaw error in DEGREES.

  python src/pc/test_pc_wrist_roll.py            headless: babble, fit, validate (deg error) + save a plot
  WRIST_LIVE=1 python src/pc/test_pc_wrist_roll.py   live: roll the claw to a sequence of commanded yaws
"""
from __future__ import annotations

import os
import sys

import numpy as np
import mujoco

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import BracketArmSim, HOME, ARM_JOINTS, reach_step
from pc.arm_modules import WristRollModule


def _set(sim, q5):
    for j, v in zip(ARM_JOINTS, q5):
        sim.d.qpos[sim.jqadr[j]] = float(v)
    mujoco.mj_forward(sim.m, sim.d)


def _angdiff_deg(a, b):
    return np.degrees(np.abs(np.arctan2(np.sin(a - b), np.cos(a - b))))


def validate_forward(sim, wrist, rng, n=1500):
    ranges = np.array([sim.m.jnt_range[sim._jid(j)] for j in ARM_JOINTS])
    Q = rng.uniform(ranges[:, 0], ranges[:, 1], size=(n, 5))
    Y = np.empty(n)
    for i in range(n):
        _set(sim, Q[i]); Y[i] = sim.claw_yaw()
    pr = wrist.predict_yaw(Q)
    return _angdiff_deg(Y, pr)


def validate_inverse(sim, wrist, rng, n=400):
    """Honest end-to-end: pick a random pose + a random REAL joint_4 (=> a real achievable yaw), ask the
    learned model for the joint_4 that hits that yaw, command it, measure the ACHIEVED yaw error."""
    ranges = np.array([sim.m.jnt_range[sim._jid(j)] for j in ARM_JOINTS])
    errs = []
    for _ in range(n):
        j0, j1, j2, j3 = rng.uniform(ranges[:4, 0], ranges[:4, 1])
        j4_true = rng.uniform(*wrist.J4_RANGE)
        _set(sim, [j0, j1, j2, j3, j4_true]); want = sim.claw_yaw()       # a real, achievable yaw
        j4_hat = wrist.wrist_for_yaw([j0, j1, j2], want, j3=j3)           # learned inverse
        _set(sim, [j0, j1, j2, j3, j4_hat]); got = sim.claw_yaw()         # achieved on the real arm
        errs.append((want, got))
    errs = np.array(errs)
    return _angdiff_deg(errs[:, 0], errs[:, 1]), errs


def main():
    rng = np.random.default_rng(0)
    sim = BracketArmSim()
    wrist = WristRollModule(rng=np.random.default_rng(3))

    print("wrist-roll — STEP 1: LEARNED orientation kinematics (joint_4 -> claw yaw), babbled")
    n_bab = int(os.environ.get("WRIST_BABBLE", "6000"))
    print(f"  babbling {n_bab} random poses (read the achieved claw yaw) + fitting ...")
    bab_deg, mse = wrist.babble(sim, n=n_bab, epochs=int(os.environ.get("WRIST_EPOCHS", "300")))
    print(f"    babble fit: mean angular error {bab_deg:.1f} deg   (cos/sin MSE {mse:.4f})")

    fwd = validate_forward(sim, wrist, rng)
    print(f"  FORWARD (held-out poses): claw-yaw error  mean {fwd.mean():.1f} deg  median {np.median(fwd):.1f} deg")

    inv, errs = validate_inverse(sim, wrist, rng)
    print(f"  INVERSE (choose joint_4 for a desired yaw, measured on the REAL arm):")
    print(f"    achieved-yaw error  mean {inv.mean():.1f} deg  median {np.median(inv):.1f} deg  "
          f"<=10deg: {100*np.mean(inv < 10):.0f}%")
    print("  Read: the agent LEARNED what wrist-roll does (by babbling, no rotation algebra) and can pick")
    print("  the joint_4 that orients the claws to a commanded yaw.  This is the prerequisite for STEP 2:")
    print("  perceive an elongated object's axis and align the grip to it.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
        ax[0].scatter(np.degrees(errs[:, 0]), np.degrees(errs[:, 1]), s=6, alpha=0.4)
        lim = [-185, 185]; ax[0].plot(lim, lim, "r--", lw=1)
        ax[0].set_xlim(lim); ax[0].set_ylim(lim)
        ax[0].set_xlabel("commanded yaw (deg)"); ax[0].set_ylabel("achieved yaw (deg)")
        ax[0].set_title(f"inverse: commanded vs achieved (mean err {inv.mean():.1f} deg)")
        ax[1].hist(inv, bins=40, color="tab:green", alpha=0.8)
        ax[1].set_xlabel("achieved-yaw error (deg)"); ax[1].set_ylabel("count")
        ax[1].set_title("learned wrist-roll inverse error")
        fig.suptitle("Wrist-roll STEP 1 — LEARNED orientation kinematics (joint_4 -> claw yaw)")
        fig.tight_layout()
        out = os.path.join(os.path.dirname(__file__), "wrist_roll.png")
        fig.savefig(out, dpi=110); print(f"  [viz] saved {out}")
    except Exception as e:
        print(f"  [viz] plot skipped: {e}")

    if os.environ.get("WRIST_LIVE", "0") == "1":
        live_demo(sim, wrist)


def live_demo(sim, wrist):
    """Reach down to a fixed grasp pose, then roll the claw to a sequence of commanded table-plane yaws so
    the wrist-roll is visible; print commanded vs achieved each time."""
    import time
    try:
        import mujoco.viewer as mjv
    except Exception as e:
        print(f"  [live] viewer unavailable: {e}"); return
    sim.set_reach_site("contact")
    sim.reset_home()
    grasp_xyz = np.array([0.0, 0.16, 0.03])
    for _ in range(400):
        reach_step(sim, grasp_xyz, gain=2.0); sim.step(2)
    q3 = sim.arm3_angles(); j3 = sim.d.qpos[sim.jqadr["joint_3"]]
    targets = np.radians([150, 120, 180, -150, 179])
    with mjv.launch_passive(sim.m, sim.d) as v:
        for want in targets:
            j4 = wrist.wrist_for_yaw(q3, float(want), j3=j3)
            for _ in range(250):
                sim.set_arm_wrist_targets(q3, j4, j3=j3); sim.step(2)
                if not v.is_running():
                    return
                v.sync(); time.sleep(0.002)
            got = sim.claw_yaw()
            print(f"  [live] commanded {np.degrees(want):.0f} deg -> achieved {np.degrees(got):.0f} deg "
                  f"(joint_4={j4:.2f})")
        for _ in range(200):
            if not v.is_running():
                return
            v.sync(); time.sleep(0.01)


if __name__ == "__main__":
    main()
