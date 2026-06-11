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
# the 3 motors used first: base-yaw + shoulder + elbow (wrist j3=pi points the gripper down so
# the grasp reaches the table; j4/gripper held at home).  "3 motors with height".
ARM3 = ["joint_0", "joint_1", "joint_2"]


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

    # ---- 3-motor subset (base+shoulder+elbow); wrist j3=pi (down), j4/gripper at home ----
    def arm3_angles(self):
        return np.array([self.d.qpos[self.jqadr[j]] for j in ARM3])

    def set_arm3_targets(self, q3):
        self.set_arm_targets([q3[0], q3[1], q3[2], HOME["joint_3"], HOME["joint_4"]])

    def arm3_range(self):
        return np.array([self.m.jnt_range[self._jid(j)] for j in ARM3])   # (3,2)

    def fk_truth(self, q3):
        """Eye-hand 'observation': set the 3 joints (others fixed), forward kinematics ->
        grasp position.  In sim this is instant via mj_forward (no dynamics)."""
        for j, v in zip(ARM3, q3):
            self.d.qpos[self.jqadr[j]] = float(v)
        self.d.qpos[self.jqadr["joint_3"]] = HOME["joint_3"]
        self.d.qpos[self.jqadr["joint_4"]] = HOME["joint_4"]
        mujoco.mj_forward(self.m, self.d)
        return self.grasp_pos()

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


class ArmBodyModel3D:
    """The agent's LEARNED 3-D kinematics for the 3-motor arm.  The forward kinematics is
    exactly LINEAR in the lifted feature set  Φ(θ) = [cosθ0·g, sinθ0·g, g]  with
    g = [1, cosθ1, sinθ1, cos(θ1+θ2), sin(θ1+θ2)]  (base-yaw rotates the shoulder/elbow
    plane), so a learned linear map  hand = W·[Φ;1]  recovers the kinematics by babbling
    (the 3-D analogue of act12's linear-in-features body model).  Its finite-difference
    Jacobian drives damped-least-squares reach control."""

    NF = 22                                              # 3*7 features + bias

    def __init__(self, rng=None):
        self.rng = rng or np.random.default_rng(0)
        self.W = np.zeros((self.NF, 3)); self.last_surprise = None

    @staticmethod
    def _feat(q3):
        t0, t1, t2 = float(q3[0]), float(q3[1]), float(q3[2])
        # base-yaw rotates the shoulder/elbow plane; the elbow axis is reversed + 90deg
        # offsets, so include BOTH (θ1+θ2) and (θ1-θ2) — least-squares picks the right combo.
        g = np.array([1.0, np.cos(t1), np.sin(t1),
                      np.cos(t1 + t2), np.sin(t1 + t2), np.cos(t1 - t2), np.sin(t1 - t2)])
        return np.concatenate([np.cos(t0) * g, np.sin(t0) * g, g])    # 21

    def _aug(self, q3):
        return np.append(self._feat(q3), 1.0)                          # +bias -> 22

    def fk(self, q3):
        return self._aug(q3) @ self.W

    def babble(self, sim, steps):
        rng3 = sim.arm3_range()
        X = np.empty((steps, self.NF)); Y = np.empty((steps, 3))
        for i in range(steps):
            q3 = self.rng.uniform(rng3[:, 0], rng3[:, 1])
            X[i] = self._aug(q3); Y[i] = sim.fk_truth(q3)
        self.W = np.linalg.solve(X.T @ X + 1e-6 * np.eye(self.NF), X.T @ Y)   # ridge least squares

    def observe(self, q3, hand_obs, lr=0.05):           # lifelong / vision refinement
        a = self._aug(q3); err = a @ self.W - np.asarray(hand_obs, float)
        s = float(np.linalg.norm(err))
        self.last_surprise = s if self.last_surprise is None else 0.9 * self.last_surprise + 0.1 * s
        self.W -= lr * np.outer(a, err)

    def jacobian(self, q3, eps=1e-4):
        J = np.zeros((3, 3))
        for i in range(3):
            dq = np.zeros(3); dq[i] = eps
            J[:, i] = (self.fk(q3 + dq) - self.fk(q3 - dq)) / (2 * eps)
        return J

    def reach_velocity(self, q3, target, gain=2.0, max_dq=0.03, damp=0.02):
        err = np.asarray(target, float) - self.fk(q3)
        J = self.jacobian(q3)
        dq = J.T @ np.linalg.solve(J @ J.T + damp * np.eye(3), gain * err)
        m = float(np.max(np.abs(dq)))
        if m > max_dq:
            dq *= max_dq / m
        return dq


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


def run_learned_reach(sim, viz, CAM, HEADLESS):
    """3-motor arm driven by the agent's LEARNED 3-D kinematics (babbled MLP FK + Jacobian).
    Validates that the net can do the coupled base+shoulder+elbow kinematics WITH height by
    reaching the grasp point to each cube on the table."""
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (linear-in-features, 4000 poses) ...")
    body.babble(sim, 4000)
    # FK accuracy on fresh random poses
    rng3 = sim.arm3_range(); errs = []
    for _ in range(400):
        q = np.random.default_rng().uniform(rng3[:, 0], rng3[:, 1])
        errs.append(np.linalg.norm(body.fk(q) - sim.fk_truth(q)))
    print(f"  learned FK error: mean {np.mean(errs)*1000:.1f} mm  max {np.max(errs)*1000:.1f} mm")

    results = []
    for nm in ("obj_red", "obj_green", "obj_blue"):
        sim.reset_home(); sim.target("joint_3", HOME["joint_3"]); sim.step(250)
        tgt = sim.obj_pos(nm) + np.array([0.0, 0.0, 0.03])     # 3 cm above the cube
        for k in range(700):
            q3 = sim.arm3_angles()                              # joint encoders (felt)
            dq = body.reach_velocity(q3, tgt)
            sim.set_arm3_targets(q3 + dq); sim.step(2)
            if viz is not None and k % 4 == 0:
                e = np.linalg.norm(tgt - sim.grasp_pos())
                viz.update(sim.render(CAM), f"reach {nm}  learned-kin  {e*1000:.0f} mm")
        err_mm = np.linalg.norm(tgt - sim.grasp_pos()) * 1000
        results.append((nm, err_mm)); print(f"  reach {nm}: {err_mm:.0f} mm  (grasp {np.round(sim.grasp_pos(),3)})")
    print(f"  == learned-kinematics reach: mean {np.mean([r for _,r in results]):.0f} mm over {len(results)} cubes ==")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


def main():
    HEADLESS = os.environ.get("ACT14_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT14_CAM", "overview").lower()
    STEPS = int(os.environ.get("ACT14_STEPS", "1200"))
    TARGET = os.environ.get("ACT14_TARGET", "obj_red")
    MODE = os.environ.get("ACT14_MODE", "demo").lower()        # demo (analytic) | learn (learned kin)

    print("act14 — real 5-DOF arm in MuJoCo (3-D gravity + contacts + overhead camera)")
    sim = BracketArmSim()
    print(f"  model: nq={sim.m.nq} actuators={sim.m.nu} cameras={sim.m.ncam}  mode={MODE}")

    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless"); HEADLESS = True

    if MODE == "learn":
        run_learned_reach(sim, viz, CAM, HEADLESS)
        return

    print(f"  analytic-Jacobian reach demo toward '{TARGET}'")
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
