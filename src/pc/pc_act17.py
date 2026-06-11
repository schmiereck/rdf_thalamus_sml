r"""
pc_act17.py — PERCEPTION + CONTROL coupled: see the commanded cube in the CAMERA, grasp & place it.

The full loop on the MuJoCo arm:
    overhead camera --(fovea)--> PC perception --> commanded-cube position
        --> learned 3-D kinematics --> grasp (act16) --> place at the target.

Perception is done UP FRONT each episode (arm parked at home, cube visible), then the cube
position is REMEMBERED and the grasp runs "blind" on it (the arm would otherwise occlude the
cube).  A coarse fovea scan acquires the commanded-colour cube, a refine saccade centres it,
and a FINER fovea ZOOM (smaller crop) sharpens the localisation to ~cube scale — the user's
"finer fovea" idea, now needed because grasping needs ~cube-radius accuracy.

First milestone commands RED (distinct from the arm's colours); GREEN/BLUE clash with the
arm in the image (recolour cubes / mask the arm) — a follow-up.

  ACT17_HEADLESS=1   metrics over episodes        ACT17_PERSIST=1   continual scene
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.test_pc_act10 import F
from pc.test_pc_act11 import selected_lum
from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, REACH_XY, _rand_xy, CamViz
from pc.pc_act15 import detect_px, sel_com
import pc.pc_act16 as act16

CMD_COLOR = {"obj_red": np.array([1., 0, 0]), "obj_green": np.array([0, 1., 0]),
             "obj_blue": np.array([0, 0, 1.])}


def crop_k(img, gaze, k):
    """Fovea crop of F*k px centred on gaze, average-pooled to F×F×3 (k sets the zoom)."""
    Rh, Rw = img.shape[:2]; s = F * k
    x0 = int(round(gaze[0])) - s // 2; y0 = int(round(gaze[1])) - s // 2
    crop = np.zeros((s, s, 3))
    xs0, xs1 = max(0, x0), min(Rw, x0 + s); ys0, ys1 = max(0, y0), min(Rh, y0 + s)
    if xs1 > xs0 and ys1 > ys0:
        crop[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] = img[ys0:ys1, xs0:xs1] / 255.0
    return crop.reshape(F, k, F, k, 3).mean(axis=(1, 3))


def to_image(com, gaze, k):
    return np.array([gaze[0] + (com[0] - (F - 1) / 2) * k, gaze[1] + (com[1] - (F - 1) / 2) * k])


def main():
    HEADLESS = os.environ.get("ACT17_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT17_CAM", "overview").lower()
    CMD = os.environ.get("ACT17_CMD", "obj_red")
    RES = int(os.environ.get("ACT17_RES", "240"))
    EPISODES = int(os.environ.get("ACT17_EPISODES", "12"))

    print(f"act17 — perception + control coupled (camera->fovea->grasp)  cam={CAM} cmd={CMD}")
    sim = BracketArmSim(render_wh=(RES, RES))
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm kinematics ..."); body.babble(sim, 4000)

    # calibrate image<->world on the table plane (affine), via the cube at known spots
    crng = np.random.default_rng(3); W, P = [], []
    sim.reset_home()
    for o in CMD_COLOR:                                          # park distractors out of view
        if o != CMD:
            sim.set_object(o, [0.32, 0.32])
    for _ in range(16):
        p = _rand_xy(crng); sim.set_object(CMD, p); mujoco.mj_forward(sim.m, sim.d)
        px = detect_px(sim.render(CAM), CMD_COLOR[CMD])
        if px is not None:
            W.append([p[0], p[1], 1.0]); P.append(px)
    W, P = np.array(W), np.array(P)
    Hx = np.linalg.lstsq(W, P[:, 0], rcond=None)[0]; Hy = np.linalg.lstsq(W, P[:, 1], rcond=None)[0]
    A = np.array([Hx[:2], Hy[:2]]); b = np.array([Hx[2], Hy[2]]); Ainv = np.linalg.inv(A)
    res = np.mean([np.linalg.norm(A @ w[:2] + b - p) for w, p in zip(W, P)])
    print(f"  calib world->px residual {res:.1f}px")
    px_to_world = lambda px: Ainv @ (np.asarray(px, float) - b)

    grid = np.linspace(F * 8 / 2, RES - F * 8 / 2, 5)

    def perceive(cmd):
        """See the commanded cube in the camera (coarse scan -> refine -> fine zoom) -> world xy."""
        rgb = CMD_COLOR[cmd]; img = sim.render(CAM)
        best, gaze = 0.0, np.array([RES / 2.0, RES / 2.0])
        for gy in grid:
            for gx in grid:
                s = selected_lum(crop_k(img, [gx, gy], 8), rgb).sum()
                if s > best:
                    best, gaze = s, np.array([gx, gy])
        for k in (8, 8, 4, 3, 3):                               # refine, then ZOOM in (smaller k)
            com = sel_com(crop_k(img, gaze, k), rgb)
            if com is None:
                break
            gaze = np.clip(to_image(com, gaze, k), F * k / 2, RES - F * k / 2)
        return px_to_world(gaze)

    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless")
    act16.run_combined(sim, body, viz, CAM, episodes=EPISODES, cmd_fixed=CMD, perceive_fn=perceive)


if __name__ == "__main__":
    main()
