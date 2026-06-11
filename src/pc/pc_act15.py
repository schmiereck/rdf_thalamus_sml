r"""
pc_act15.py — Step 2: the OVERHEAD CAMERA as the net's input, via the FOVEA.

act14 gave us the real arm in MuJoCo with rendered cameras.  act15 feeds a CAMERA IMAGE
into the existing PC perception (the act11 hex sensor sheet + colour-cued selection), but
keeps the FOVEA trick to reconcile a high-resolution camera with the small net: the net
does NOT see the whole frame — it sees only the net-CHOSEN crop (gaze window) of the
high-res image, average-pooled to the F×F hex sheet.  (A compromise that needs no
pan/zoom/​swivel camera.)

Validated here (perception only — manipulation is deferred): can the net LOCATE the
COMMANDED-colour cube from the camera, by saccading the fovea onto it?  And how much does
the real camera's OFF-TO-THE-SIDE perspective distortion (vs a straight-down view) hurt?
  ACT15_CAM=top        straight-down camera (little distortion)
  ACT15_CAM=overview   the real measured camera beside the arm (3-D perspective distortion)

Run:  ACT15_HEADLESS=1 python pc_act15.py        (metrics: localisation px + mm)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.test_pc_act10 import F, gather
from pc.test_pc_act11 import (PALETTE, NAMES, MATCH_TH, color_match, selected_lum,
                              build_hexnet, set_sheet)
from pc.pc_act14 import BracketArmSim, HOME

K = 8                      # fovea down-sampling: each F-cell averages a K×K block of the image
CROP = F * K               # the fovea window is CROP×CROP image pixels -> F×F hex sheet
CUBES = ["obj_red", "obj_green", "obj_blue"]
CMD_COLOR = {"obj_red": PALETTE[0], "obj_green": PALETTE[1], "obj_blue": PALETTE[2]}


def fovea_crop(img, gaze):
    """Extract the CROP×CROP window of the high-res camera image centred on `gaze` (x,y px)
    and average-pool it to F×F×3 in [0,1] — the net only ever sees this fovea crop."""
    Rh, Rw = img.shape[:2]
    x0 = int(round(gaze[0])) - CROP // 2
    y0 = int(round(gaze[1])) - CROP // 2
    crop = np.zeros((CROP, CROP, 3))
    xs0, xs1 = max(0, x0), min(Rw, x0 + CROP)
    ys0, ys1 = max(0, y0), min(Rh, y0 + CROP)
    if xs1 > xs0 and ys1 > ys0:
        crop[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] = img[ys0:ys1, xs0:xs1] / 255.0
    return crop.reshape(F, K, F, K, 3).mean(axis=(1, 3))          # F×F×3


def sel_com(rgb_w, cmd):
    """Colour-cued centre of mass in fovea-cell coords (col,row), or None."""
    sel = selected_lum(rgb_w, cmd)
    tot = sel.sum()
    if tot < 1e-6:
        return None
    idx = np.arange(F)
    col = float((sel.sum(axis=0) * idx).sum() / tot)
    row = float((sel.sum(axis=1) * idx).sum() / tot)
    return np.array([col, row])


def crop_to_image(com, gaze):
    """Map a fovea-cell COM (col,row) back to full-image pixels."""
    return np.array([gaze[0] + (com[0] - (F - 1) / 2) * K,
                     gaze[1] + (com[1] - (F - 1) / 2) * K])


def detect_px(img, rgb):
    """True image position (col,row) of a colour = COM of matching bright pixels, or None."""
    f = img.astype(float) / 255.0
    nrm = np.linalg.norm(f, axis=2) + 1e-6
    dotp = (f @ (rgb / np.linalg.norm(rgb))) / nrm
    mask = (dotp > 0.93) & (f.sum(axis=2) > 0.5)
    if mask.sum() < 3:
        return None
    ys, xs = np.nonzero(mask)
    return np.array([xs.mean(), ys.mean()])


def main():
    HEADLESS = os.environ.get("ACT15_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT15_CAM", "top").lower()
    CMD = os.environ.get("ACT15_CMD", "obj_red")
    RES = int(os.environ.get("ACT15_RES", "240"))
    rng = np.random.default_rng(0)

    print(f"act15 — overhead camera + fovea into the net   cam={CAM}  res={RES}  cmd={CMD}")
    sim = BracketArmSim(render_wh=(RES, RES))
    sim.reset_home()                                              # arm parked at home (out of the way)
    net, cells, h1 = build_hexnet(rng)
    lo, hi = np.array([-0.08, 0.09]), np.array([0.08, 0.19])      # reachable/visible table patch

    def scatter():
        pts = []
        for nm in CUBES:
            p = rng.uniform(lo, hi)
            while any(np.linalg.norm(p - q) < 0.05 for q in pts):
                p = rng.uniform(lo, hi)
            pts.append(p); sim.set_object(nm, p)
        mujoco.mj_forward(sim.m, sim.d)

    # calibrate image<->world on the table plane (homography), by detecting the cube at known spots
    def calibrate():
        W, P = [], []
        for _ in range(16):
            p = rng.uniform(lo, hi)
            sim.set_object(CMD, p)
            for nm in CUBES:
                if nm != CMD:
                    sim.set_object(nm, [0.3, 0.3])               # park distractors out of view
            mujoco.mj_forward(sim.m, sim.d)
            px = detect_px(sim.render(CAM), CMD_COLOR[CMD])
            if px is not None:
                W.append([p[0], p[1], 1.0]); P.append(px)
        W, P = np.array(W), np.array(P)
        Hx = np.linalg.lstsq(W, P[:, 0], rcond=None)[0]           # world(x,y,1) -> px_x
        Hy = np.linalg.lstsq(W, P[:, 1], rcond=None)[0]           # world(x,y,1) -> px_y
        A = np.array([Hx[:2], Hy[:2]]); b = np.array([Hx[2], Hy[2]])
        # residual of this affine fit (distortion makes it imperfect, esp. for 'overview')
        res = np.mean([np.linalg.norm(A @ w[:2] + b - p) for w, p in zip(W, P)])
        return A, b, res

    A, b, calib_res = calibrate()
    Ainv = np.linalg.inv(A)
    px_to_world = lambda px: Ainv @ (np.asarray(px, float) - b)
    print(f"  calib: affine world->px residual {calib_res:.1f}px "
          f"({'low — near-orthographic' if calib_res < 4 else 'higher — perspective distortion'})")

    # ---- learn the camera scene through the fovea (sensor_error should drop) ----
    se = []
    for it in range(1500):
        if it % 3 == 0:
            scatter()
        img = sim.render(CAM)
        true = detect_px(img, CMD_COLOR[CMD])
        gaze = (true + rng.normal(0, 18, 2)) if true is not None else np.array([RES / 2, RES / 2])
        rgb_w = fovea_crop(img, gaze)
        set_sheet(cells, rgb_w, np.zeros((F, F)), np.zeros((F, F)))
        r = net.step(learn=True); net.commit_step()
        if np.isfinite(r["sensor_error"]):
            se.append(r["sensor_error"])
    print(f"  net sensor_error (camera scene): {np.mean(se[:150]):.3f} -> {np.mean(se[-150:]):.3f}")

    # ---- acquire (coarse fovea scan) then foveate the COMMANDED cube; measure localisation ----
    grid = np.linspace(CROP / 2, RES - CROP / 2, 5)
    px_err, w_err, found, N = 0.0, 0.0, 0, 40
    for ep in range(N):
        scatter()
        img = sim.render(CAM)
        true = detect_px(img, CMD_COLOR[CMD])
        if true is None:
            continue
        # coarse scan: pick the fovea position with the most commanded-colour evidence
        best_s, gaze = 0.0, None
        for gy in grid:
            for gx in grid:
                s = selected_lum(fovea_crop(img, [gx, gy]), CMD_COLOR[CMD]).sum()
                if s > best_s:
                    best_s, gaze = s, np.array([gx, gy])
        if gaze is None:
            continue
        for _ in range(14):                                      # refine: centre the cube
            com = sel_com(fovea_crop(img, gaze), CMD_COLOR[CMD])
            if com is None:
                break
            gaze = np.clip(crop_to_image(com, gaze), CROP / 2, RES - CROP / 2)
        com = sel_com(fovea_crop(img, gaze), CMD_COLOR[CMD])
        if com is None:
            continue
        found += 1
        px_err += np.linalg.norm(gaze - true)
        w_err += np.linalg.norm(px_to_world(gaze) - px_to_world(true)) * 1000
    print(f"  COMMANDED-cube localisation from camera (fovea): {px_err/max(1,found):.1f}px "
          f"= {w_err/max(1,found):.1f}mm   (found {found}/{N})")
    print(f"  [fovea] net sees only a {CROP}x{CROP}px crop -> {F}x{F} sheet (of the {RES}px image)")


if __name__ == "__main__":
    main()
