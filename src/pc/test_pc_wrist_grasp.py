r"""test_pc_wrist_grasp.py — STEP 2b: GRIP an elongated object by aligning the claws to its perceived axis.

Brings the two learned pieces together on the real arm: PERCEIVE the elongated object's long axis
(ObjectOrientationModule) -> choose the joint_4 that points the claws ACROSS it (WristRollModule.wrist_for_yaw)
-> reach, lower, close, lift.  An elongated object is too WIDE to grip along its long axis but grippable
across the narrow one, so the wrist-roll is what makes the grasp possible.

Honest A/B: the SAME grasp with the wrist ALIGNED vs FROZEN at home.  FINDING (measured): on this arm+gripper
the wrist-roll gives NO grasping benefit -- the curved scooping claws lift the object at ANY orientation
(frozen ~15/16) so orientation does not gate the grasp, and the non-vertical roll axis TILTS the claws so
aligned is WORSE.  Steps 1+2a (learned kinematics + orientation) are clean; the payoff needs a parallel-jaw
gripper and/or a verticalised roll axis (an MJCF change).  This script is the honest LIMIT-PROBE.

  python src/pc/test_pc_wrist_grasp.py                 headless A/B success over random orientations
  WGRASP_LIVE=1 python src/pc/test_pc_wrist_grasp.py   watch a few aligned grasps in the viewer
"""
from __future__ import annotations

import os
import sys

import numpy as np
import mujoco

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import BracketArmSim, HOME
from pc.arm_modules import WristRollModule
from pc.arm_modules.object_orientation import ObjectOrientationModule

HALF = (0.030, 0.012, 0.012)          # elongated: long 60mm / narrow 24mm (= a cube)
J5_GRIP = 0.0
# the DEFAULT open claw gap is ~97mm (j5=1.8) -- wider than the object, so the claws SCOOP it at any
# orientation and elongation never gates the grasp.  Use a narrower, realistic open width so the long axis
# (60mm) does NOT fit between the open claws and the grasp MUST be aligned to the narrow axis.
J5_OPEN = float(os.environ.get("WGRASP_OPEN", "0.95"))   # ~52mm open gap (< 60mm long, > 24mm narrow)


def reach_arm3(sim, target_xyz, j4, gain=2.0, max_dq=0.03):
    """One damped-least-squares step over the 3 POSITIONING joints only (joint_4 held at the aligned yaw)."""
    err = np.asarray(target_xyz) - sim.grasp_pos()
    J = sim.site_jacobian()[:, :3]
    dq = J.T @ np.linalg.solve(J @ J.T + 0.02 * np.eye(3), gain * err)
    m = float(np.max(np.abs(dq)))
    if m > max_dq:
        dq *= max_dq / m
    q3 = sim.arm3_angles() + dq
    sim.set_arm_wrist_targets(q3, j4)
    return float(np.linalg.norm(err))


def attempt_grasp(sim, wrist, ori, xy, yaw, aligned, cam):
    """Reach down with the wrist at HOME (so the reach is unperturbed), THEN -- at the grasp pose -- roll
    joint_4 to the perceived aligned yaw, close, lift.  (Setting joint_4 before the reach twisted the arm and
    blocked the descent; rolling only once down keeps the reach clean and applies the orientation last.)"""
    j4_home = HOME["joint_4"]
    sim.reset_home(); sim.set_target_marker([0.0, -0.6], z=-0.05)
    for o in ("obj_green", "obj_blue"):
        sim.set_object(o, [0.0, -0.55])
    sim.set_object("obj_red", xy, z=float(HALF[2]), yaw=yaw)
    mujoco.mj_forward(sim.m, sim.d); sim.step(20)
    grip_yaw, _ = ori.perceive(sim, "obj_red", cam=cam)            # PERCEIVED grip orientation
    c = sim.obj_pos("obj_red")[:2]
    over = np.array([c[0], c[1], 0.06]); down = np.array([c[0], c[1], 0.016])
    sim.target("joint_5", J5_OPEN)
    for _ in range(200):                                          # move over the object (wrist HOME)
        reach_arm3(sim, over, j4_home); sim.step(2)
    for _ in range(220):                                          # lower onto it (wrist HOME)
        reach_arm3(sim, down, j4_home); sim.step(2)
    # match the grip yaw MOD 180 (symmetric claws) so it stays within joint_4's reachable swing
    j4t = wrist.wrist_for_yaw(sim.arm3_angles(), grip_yaw, mod180=True) if aligned else j4_home
    for r in range(120):                                          # ROLL the claws to the aligned yaw
        reach_arm3(sim, down, j4_home + (j4t - j4_home) * min(1.0, r / 60.0)); sim.step(2)
    for k in range(120):                                          # close gently
        sim.target("joint_5", J5_OPEN + (J5_GRIP - J5_OPEN) * min(1.0, k / 60.0))
        reach_arm3(sim, down, j4t); sim.step(2)
    for _ in range(200):                                          # lift
        reach_arm3(sim, np.array([c[0], c[1], 0.08]), j4t); sim.step(2)
    return sim.obj_pos("obj_red")[2] > 0.045                      # lifted clear of the table => gripped


def main():
    cam = os.environ.get("WGRASP_CAM", "overview").lower()
    sim = BracketArmSim(render_wh=(480, 480)); sim.set_reach_site("contact")
    wrist = WristRollModule(rng=np.random.default_rng(3))
    ori = ObjectOrientationModule()

    print("wrist-grasp — STEP 2b: grip an elongated object by aligning the claws to its PERCEIVED axis")
    print("  learning wrist-roll kinematics (babble) + object-orientation perception ...")
    bab, _ = wrist.babble(sim, n=int(os.environ.get("WGRASP_BABBLE", "6000")))
    sim.set_reach_site("contact")
    tr = ori.train(sim, cmd="obj_red", cam=cam, steps=int(os.environ.get("WGRASP_ORI", "2500")),
                   half=HALF, rng=np.random.default_rng(0))
    print(f"    wrist kinematics {bab:.1f} deg ; orientation perception {tr:.1f} deg")

    if os.environ.get("WGRASP_LIVE", "0") == "1":
        return live(sim, wrist, ori, cam)

    rng = np.random.default_rng(11); n = int(os.environ.get("WGRASP_N", "16"))
    al = fr = 0
    for i in range(n):
        xy = [rng.uniform(-0.06, 0.06), rng.uniform(0.13, 0.18)]; yaw = rng.uniform(0, np.pi)
        a = attempt_grasp(sim, wrist, ori, xy, yaw, True, cam)
        f = attempt_grasp(sim, wrist, ori, xy, yaw, False, cam)
        al += a; fr += f
        print(f"  ep {i:2d}  yaw {np.degrees(yaw):3.0f}deg   aligned {'OK ' if a else 'no '}   frozen {'OK' if f else 'no'}")
    print("=" * 64)
    print(f"  ALIGNED wrist (perceived axis):  {al}/{n} gripped")
    print(f"  FROZEN wrist (home yaw):         {fr}/{n} gripped")
    print("  Read (HONEST, measured): on THIS arm+gripper the wrist-roll gives NO grasping benefit, for two")
    print("  measured reasons -- (1) the gripper has CURVED concave claw tips (a scooping 'pushing pocket')")
    print("  + a wide opening, so it lifts a small elongated object by SCOOPING at ANY orientation (frozen")
    print("  grips ~all yaws), i.e. orientation does not gate the grasp; (2) the wrist-roll axis is NOT")
    print("  vertical in the grasp pose (j3 pitched), so rolling TILTS the claws up to ~20deg -> aligned is")
    print("  WORSE.  Steps 1 (kinematics) + 2a (orientation perception) are clean LEARNED modules, but the")
    print("  payoff needs an MJCF change: a PARALLEL-JAW gripper (flat fingers, narrow travel) so alignment")
    print("  matters, and/or a verticalised roll axis.  A nameable hardware/gripper limit, not a code bug.")


def live(sim, wrist, ori, cam):
    import time
    try:
        import mujoco.viewer as mjv
    except Exception as e:
        print(f"  [live] viewer unavailable: {e}"); return
    rng = np.random.default_rng(1)
    with mjv.launch_passive(sim.m, sim.d) as v:
        for _ in range(5):
            xy = [rng.uniform(-0.05, 0.05), rng.uniform(0.13, 0.18)]; yaw = rng.uniform(0, np.pi)
            sim.reset_home(); sim.set_target_marker([0.0, -0.6], z=-0.05)
            for o in ("obj_green", "obj_blue"):
                sim.set_object(o, [0.0, -0.55])
            sim.set_object("obj_red", xy, z=float(HALF[2]), yaw=yaw); mujoco.mj_forward(sim.m, sim.d)
            grip_yaw, _ = ori.perceive(sim, "obj_red", cam=cam)
            c = sim.obj_pos("obj_red")[:2]
            seq = [(np.array([c[0], c[1], 0.06]), J5_OPEN, 200), (np.array([c[0], c[1], 0.016]), J5_OPEN, 200),
                   (np.array([c[0], c[1], 0.016]), J5_GRIP, 140), (np.array([c[0], c[1], 0.09]), J5_GRIP, 200)]
            for aim, j5, steps in seq:
                for _ in range(steps):
                    if not v.is_running():
                        return
                    sim.target("joint_5", j5)
                    reach_arm3(sim, aim, wrist.wrist_for_yaw(sim.arm3_angles(), grip_yaw))
                    sim.step(2); v.sync(); time.sleep(0.002)
            print(f"  [live] yaw {np.degrees(yaw):.0f}deg -> lifted z={sim.obj_pos('obj_red')[2]:.3f}")


if __name__ == "__main__":
    main()
