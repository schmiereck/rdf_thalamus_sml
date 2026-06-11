r"""
pc_act14.py — Step 1 of the move to a PHYSICAL robot: the real 5-DOF arm in MuJoCo,
with real 3-D gravity, contact physics, lighting/shadows/textures and an overhead camera.

This stage establishes the simulation FOUNDATION (it does NOT yet wire the PC net):

  * `BracketArmSim` loads assets/bracket_arm.xml — a faithful MJCF replica of the real
    arm (ba_arduino_controller_moveit_config): joints joint_0..joint_4 (+ gripper joint_5),
    exact link lengths/axes, [0,pi] servo limits, the measured overhead camera.
  * Position actuators hold the arm against gravity; objects rest/collide on the table.
  * A demo reaches the gripper to a target object in 3-D using MuJoCo's site Jacobian
    (damped least-squares) — a closed-loop 3-D reach under gravity.  In later steps the
    agent's LEARNED kinematics + the camera image replace the analytic Jacobian and the
    synthetic scene (Step 2 = overhead camera as the net's input).

Run:  python pc_act14.py                 (live overview-camera window + scripted reach)
      ACT14_CAM=top python ...            (top-down camera instead)
      ACT14_HEADLESS=1 python ...         (no window; saves a few frames + prints metrics)
"""

from __future__ import annotations

import os
import sys

import numpy as np
import mujoco

ASSET = os.path.join(os.path.dirname(__file__), "assets", "bracket_arm.xml")
ARM_JOINTS = ["joint_0", "joint_1", "joint_2", "joint_3", "joint_4"]   # 5 DOF (gripper = joint_5)
HOME = {"joint_0": 1.5708, "joint_1": 0.0, "joint_2": 0.0,
        "joint_3": 3.14, "joint_4": 1.5708, "joint_5": 0.76}


class BracketArmSim:
    """Thin wrapper around the MuJoCo model of the real arm."""

    def __init__(self, render_wh=(360, 360)):
        self.m = mujoco.MjModel.from_xml_path(ASSET)
        self.d = mujoco.MjData(self.m)
        self._renderer = mujoco.Renderer(self.m, height=render_wh[0], width=render_wh[1])
        self.grasp_sid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, "grasp")
        # qpos / dof addresses of the controllable arm joints (gripper handled separately)
        self.jqadr = {j: self.m.jnt_qposadr[self._jid(j)] for j in HOME}
        self.jdof = [self.m.jnt_dofadr[self._jid(j)] for j in ARM_JOINTS]
        self.act = {j: mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_ACTUATOR, "m" + j[-1]) for j in HOME}
        self.reset_home()

    def _jid(self, name):
        return mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, name)

    def reset_home(self):
        mujoco.mj_resetData(self.m, self.d)
        for j, v in HOME.items():
            self.d.qpos[self.jqadr[j]] = v
            self.d.ctrl[self.act[j]] = v
        mujoco.mj_forward(self.m, self.d)

    # ---- control ----
    def target(self, joint, value):
        self.d.ctrl[self.act[joint]] = float(value)

    def arm_targets(self):
        return np.array([self.d.ctrl[self.act[j]] for j in ARM_JOINTS])

    def set_arm_targets(self, q):
        for j, v in zip(ARM_JOINTS, q):
            lo, hi = self.m.jnt_range[self._jid(j)]
            self.d.ctrl[self.act[j]] = float(np.clip(v, lo, hi))

    def step(self, n=1):
        for _ in range(n):
            mujoco.mj_step(self.m, self.d)

    # ---- state ----
    def grasp_pos(self):
        return self.d.site_xpos[self.grasp_sid].copy()

    def obj_pos(self, name):
        return self.d.xpos[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)].copy()

    def site_jacobian(self):
        """3x5 position Jacobian of the grasp site w.r.t. the 5 arm joints."""
        jacp = np.zeros((3, self.m.nv))
        mujoco.mj_jacSite(self.m, self.d, jacp, None, self.grasp_sid)
        return jacp[:, self.jdof]

    def render(self, cam="overview"):
        self._renderer.update_scene(self.d, camera=cam)
        return self._renderer.render()


def reach_step(sim, target_xyz, gain=2.0, max_dq=0.03):
    """One damped-least-squares step of the grasp site toward target_xyz (analytic Jacobian)."""
    err = np.asarray(target_xyz) - sim.grasp_pos()
    J = sim.site_jacobian()
    dq = J.T @ np.linalg.solve(J @ J.T + 0.02 * np.eye(3), gain * err)
    m = float(np.max(np.abs(dq)))
    if m > max_dq:
        dq *= max_dq / m
    sim.set_arm_targets(sim.arm_targets() + dq)
    return float(np.linalg.norm(err))


class CamViz:
    def __init__(self, cam):
        import matplotlib.pyplot as plt
        self.plt = plt; plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(5.2, 5.2))
        self.ax.set_title(f"act14 — MuJoCo {cam} camera"); self.ax.axis("off")
        self.im = self.ax.imshow(np.zeros((10, 10, 3), np.uint8))

    def update(self, frame, txt=""):
        self.im.set_data(frame)
        self.ax.set_xlabel(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def hold(self):
        self.plt.ioff(); self.plt.show()


def main():
    HEADLESS = os.environ.get("ACT14_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT14_CAM", "overview").lower()
    STEPS = int(os.environ.get("ACT14_STEPS", "1200"))
    TARGET = os.environ.get("ACT14_TARGET", "obj_red")

    print("act14 — real 5-DOF arm in MuJoCo (3-D gravity + contacts + overhead camera)")
    sim = BracketArmSim()
    print(f"  model: nq={sim.m.nq} actuators={sim.m.nu} cameras={sim.m.ncam}  reaching '{TARGET}'")

    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless"); HEADLESS = True

    sim.step(300)                                  # let the arm settle at home under gravity
    last = 1e9
    for k in range(STEPS):
        tgt = sim.obj_pos(TARGET) + np.array([0.0, 0.0, 0.04])   # pre-grasp: 4 cm above the cube
        last = reach_step(sim, tgt)
        sim.step(2)
        if viz is not None and k % 4 == 0:
            viz.update(sim.render(CAM), f"step {k}/{STEPS}  grasp->target {last*1000:.0f} mm")
        elif HEADLESS and k in (0, STEPS // 2, STEPS - 1):
            import matplotlib.image as mpimg
            mpimg.imsave(f"act14_reach_{k}.png", sim.render(CAM))

    print(f"  final grasp->target distance: {last*1000:.1f} mm  (grasp {np.round(sim.grasp_pos(),3)},"
          f" target {np.round(sim.obj_pos(TARGET),3)})")
    print("  arm joints (rad):", np.round([sim.d.qpos[sim.jqadr[j]] for j in ARM_JOINTS], 3))
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


if __name__ == "__main__":
    main()
