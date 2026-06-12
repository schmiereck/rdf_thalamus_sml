r"""
pc_act17.py — PERCEPTION + CONTROL coupled: see the commanded cube AND the target in the
camera, grasp the cube and place it on the target.  Full loop on the MuJoCo arm:

    overhead camera --(fovea + zoom)--> PC perception --> cube + target positions
        --> learned 3-D kinematics --> grasp (act16) --> place on the target.

Both the commanded-colour cube and the (magenta) target marker are LOCATED from the camera.
Perception runs UP FRONT each episode with the arm kinematically PARKED out of the workspace
and the fovea search restricted to the table area, so the arm (green turret / blue forearm)
never confuses the colour selection or occludes the scene — any of the three cube colours can
be commanded.  A finer fovea ZOOM sharpens localisation to ~cube scale.

  ACT17_HEADLESS=1   metrics      ACT17_PERSIST=1   continual scene      ACT17_CMD=  fix one cube
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.test_pc_act10 import F
from pc.test_pc_act11 import selected_lum
from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, REACH_XY, _rand_xy
from pc.pc_act15 import detect_px, sel_com
import pc.pc_act16 as act16

# match against the ACTUAL cube rgba (as in the MJCF) so lighting/ambient desaturation
# doesn't push the colour-cosine below threshold (pure primaries were too strict)
CMD_COLOR = {"obj_red": np.array([0.9, 0.1, 0.1]), "obj_green": np.array([0.1, 0.85, 0.1]),
             "obj_blue": np.array([0.15, 0.3, 0.95])}
MAGENTA = np.array([1., 0, 1.])
MATCH_TH = 0.86


def sel_lum(rgb_w, rgb):
    """Per-cell luminance kept where the cell colour matches `rgb` (tolerant cosine)."""
    out = np.zeros((F, F)); n = rgb / np.linalg.norm(rgb)
    lum = rgb_w.sum(2)
    dot = (rgb_w @ n) / (np.linalg.norm(rgb_w, axis=2) + 1e-6)
    out[(lum > 0.18) & (dot > MATCH_TH)] = lum[(lum > 0.18) & (dot > MATCH_TH)]
    return out


def sel_com2(rgb_w, rgb):
    sel = sel_lum(rgb_w, rgb); tot = sel.sum()
    if tot < 1e-6:
        return None
    idx = np.arange(F)
    return np.array([(sel.sum(0) * idx).sum() / tot, (sel.sum(1) * idx).sum() / tot])


def crop_k(img, gaze, k):
    Rh, Rw = img.shape[:2]; s = F * k
    x0 = int(round(gaze[0])) - s // 2; y0 = int(round(gaze[1])) - s // 2
    crop = np.zeros((s, s, 3))
    xs0, xs1 = max(0, x0), min(Rw, x0 + s); ys0, ys1 = max(0, y0), min(Rh, y0 + s)
    if xs1 > xs0 and ys1 > ys0:
        crop[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] = img[ys0:ys1, xs0:xs1] / 255.0
    return crop.reshape(F, k, F, k, 3).mean(axis=(1, 3))


def to_image(com, gaze, k):
    return np.array([gaze[0] + (com[0] - (F - 1) / 2) * k, gaze[1] + (com[1] - (F - 1) / 2) * k])


class Act17Viz:
    """Left: full camera with the fovea window + gaze; right: the F×F crop the net sees."""
    def __init__(self, cam, res):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        self.plt = plt; self._Rect = Rectangle; self.res = res; plt.ion()
        self.fig, (self.axI, self.axC) = plt.subplots(1, 2, figsize=(9.2, 5),
                                                      gridspec_kw={"width_ratios": [3, 1]})
        self.fig.patch.set_facecolor("#0e0e12")
        self.axI.set_title(f"act17 — {cam} camera", color="w"); self.axI.axis("off")
        self.axC.set_title("net sees (fovea)", color="w"); self.axC.axis("off")
        self.imI = self.axI.imshow(np.zeros((res, res, 3), np.uint8))
        self.imC = self.axC.imshow(np.zeros((F, F, 3)), interpolation="nearest")
        self.rect = self._Rect((0, 0), F * 8, F * 8, fill=False, ec="#33ccff", lw=2)
        self.axI.add_patch(self.rect)
        (self.gz,) = self.axI.plot([], [], "+", ms=14, mew=2, color="#33ccff")
        self.txt = self.axI.text(0.02, 0.98, "", transform=self.axI.transAxes, va="top",
                                 color="w", fontsize=9, family="monospace")

    def update(self, frame, txt=""):           # camera-only (CamViz-compatible, for the grasp loop)
        self.imI.set_data(frame); self.txt.set_text(txt)
        self.rect.set_visible(False); self.gz.set_data([], [])
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def fovea(self, frame, gaze, k, rgb_w, txt):
        self.imI.set_data(frame); self.imC.set_data(np.clip(rgb_w, 0, 1))
        self.rect.set_visible(True); self.rect.set_width(F * k); self.rect.set_height(F * k)
        self.rect.set_xy((gaze[0] - F * k / 2, gaze[1] - F * k / 2))
        self.gz.set_data([gaze[0]], [gaze[1]]); self.txt.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def hold(self):
        self.plt.ioff(); self.plt.show()


def main():
    HEADLESS = os.environ.get("ACT17_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT17_CAM", "overview").lower()
    CMD = os.environ.get("ACT17_CMD", "") or None               # fix one cube, or None = cycle
    RES = int(os.environ.get("ACT17_RES", "240"))
    EPISODES = int(os.environ.get("ACT17_EPISODES", "12"))
    DELAY = float(os.environ.get("ACT17_DELAY", "0.04"))

    print(f"act17 — perception+control coupled (camera->fovea->grasp)  cam={CAM}  cmd={CMD or 'cycle'}")
    sim = BracketArmSim(render_wh=(RES, RES))
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm kinematics ..."); body.babble(sim, 4000)

    # perception renders with the ARM HIDDEN (geom group 1 off) — equivalent to the arm being
    # out of the camera's workspace view; removes all arm colour-clash and occlusion robustly.
    perc_opt = mujoco.MjvOption()
    perc_opt.geomgroup[1] = 0

    def render_perc():
        sim._renderer.update_scene(sim.d, camera=CAM, scene_option=perc_opt)
        return sim._renderer.render()

    # calibrate image<->world on the table plane (affine), via the red cube
    crng = np.random.default_rng(3); W, P = [], []
    sim.reset_home()
    for o in CMD_COLOR:
        if o != "obj_red":
            sim.set_object(o, [0.33, 0.33])
    for _ in range(16):
        p = _rand_xy(crng); sim.set_object("obj_red", p); mujoco.mj_forward(sim.m, sim.d)
        px = detect_px(render_perc(), CMD_COLOR["obj_red"])
        if px is not None:
            W.append([p[0], p[1], 1.0]); P.append(px)
    W, P = np.array(W), np.array(P)
    Hx = np.linalg.lstsq(W, P[:, 0], rcond=None)[0]; Hy = np.linalg.lstsq(W, P[:, 1], rcond=None)[0]
    A = np.array([Hx[:2], Hy[:2]]); b = np.array([Hx[2], Hy[2]]); Ainv = np.linalg.inv(A)
    res = np.mean([np.linalg.norm(A @ w[:2] + b - p) for w, p in zip(W, P)])
    print(f"  calib world->px residual {res:.1f}px")
    px_to_world = lambda px: Ainv @ (np.asarray(px, float) - b)
    px_scale = 0.5 * (np.linalg.norm(Ainv[:, 0]) + np.linalg.norm(Ainv[:, 1]))   # world metres per px

    def measure_width(img, rgb, center_px):
        """Apparent world width of the colour blob around center_px (for the grasp/push choice)."""
        R = 36; x0 = int(center_px[0]) - R; y0 = int(center_px[1]) - R
        reg = img[max(0, y0):y0 + 2 * R, max(0, x0):x0 + 2 * R].astype(float) / 255.0
        if reg.size == 0:
            return 0.0
        n = rgb / np.linalg.norm(rgb)
        lum = reg.sum(2); dot = (reg @ n) / (np.linalg.norm(reg, axis=2) + 1e-6)
        mask = (lum > 0.18) & (dot > MATCH_TH)
        if mask.sum() < 6:
            return 0.0
        ys, xs = np.nonzero(mask)
        return max(xs.max() - xs.min(), ys.max() - ys.min()) * px_scale
    # fovea-search grid restricted to the TABLE patch (in px) so the arm/turret are excluded
    corners = np.array([[REACH_XY[i][0], REACH_XY[j][1]] for i in (0, 1) for j in (0, 1)])
    cpx = np.array([A @ c + b for c in corners])
    pmin = np.maximum(cpx.min(0) - 16, 0).astype(int)           # table-patch px box (scan grid range)
    pmax = np.minimum(cpx.max(0) + 16, RES).astype(int)
    gx = np.linspace(pmin[0] + F * 4, pmax[0] - F * 4, 4)
    gy = np.linspace(pmin[1] + F * 4, pmax[1] - F * 4, 4)

    viz = None
    if not HEADLESS:
        try:
            viz = Act17Viz(CAM, RES)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless")

    def locate(img, rgb, label):
        best, gaze = 0.0, np.array([RES / 2.0, RES / 2.0])
        for y in gy:
            for x in gx:
                rgb_w = crop_k(img, [x, y], 8); s = sel_lum(rgb_w, rgb).sum()
                if viz is not None:
                    viz.fovea(img, [x, y], 8, rgb_w, f"scan {label}"); time.sleep(DELAY * 0.4)
                if s > best:
                    best, gaze = s, np.array([x, y])
        for k in (8, 8, 4, 3, 3):
            rgb_w = crop_k(img, gaze, k); com = sel_com2(rgb_w, rgb)
            if viz is not None:
                viz.fovea(img, gaze, k, rgb_w, f"foveate {label} (zoom k={k})"); time.sleep(DELAY)
            if com is None:
                break
            gaze = np.clip(to_image(com, gaze, k), F * k / 2, RES - F * k / 2)
        return px_to_world(gaze)

    def perceive(cmd):
        img = render_perc()                                       # arm hidden -> only table+objects+target
        cube = locate(img, CMD_COLOR[cmd], f"obj '{cmd[4]}'")
        tgt = locate(img, MAGENTA, "target")
        # AFFORDANCE: measure the object's width from the camera and choose the mode
        w = measure_width(img, CMD_COLOR[cmd], A @ cube + b)
        mode = "push" if w > 0.042 else "grasp"                   # wider than the gripper -> push
        if os.environ.get("ACT17_DBG"):
            print(f"  [dbg] {cmd} loc {np.round(cube,3)} true {np.round(sim.obj_pos(cmd)[:2],3)}"
                  f"  width {w*1000:.0f}mm -> {mode}")
        return cube, tgt, mode

    act16.run_combined(sim, body, viz, CAM, episodes=EPISODES, cmd_fixed=CMD, perceive_fn=perceive, mixed=True)


if __name__ == "__main__":
    main()
