r"""ObstacleVisionModule — LEARNED camera -> obstacle-occupancy perception (the visual board recognition).

Increment 2 of "learn the board, then see it": the world model already learned the board's impassability
from physical collisions, CONDITIONED on an occupancy map (test_pc_chain_arm_obstacle).  Here that occupancy
stops being ground truth and is PERCEIVED: a small net maps the top-down camera image to the occupancy grid.
It is trained self-supervised -- the agent places random boards it can render and knows the footprint of, so
(image -> occupancy) is learnable without hand-coded colour thresholds (a bigger/conv net would sharpen it;
that is the extensible knob).

Occupancy is the clean interface: VisionModule.occupancy -> WorldModel's occupancy port, unchanged.

The net regresses the board's POSE (cx, cy, half-y) from the image and reconstructs the occupancy via
occ_map.  This is the LEARNED visual recognition (image -> board location), reduced to 3 smooth targets:
a plain MLP that tries to regress the full 144-cell occupancy collapses to the MEAN board (FC layers
cannot localize from raw pixels with little data -- a conv net is the extensible fix).  Parametric here =
a single axis-aligned board; the occupancy interface keeps the world model / planner unchanged.

Ports
  out : occupancy (OCC_N*OCC_N)  perceived board occupancy over the working bbox
"""
from __future__ import annotations

import numpy as np
import mujoco

from pc.chain_obstacle_data import BoardCtl, occ_map, OCC_N, WX, WY
from .base import ArmModule

DS = 40                                 # the camera is downsampled to DS x DS (RGB) before the net
CX_R = (-0.10, 0.10); CY_R = (0.10, 0.21); HY_R = (0.04, 0.07)
_LO = np.array([CX_R[0], CY_R[0], HY_R[0]]); _SP = np.array([CX_R[1] - CX_R[0], CY_R[1] - CY_R[0], HY_R[1] - HY_R[0]])
_GX = np.linspace(0.0, 1.0, DS)         # normalised image coords for the soft-argmax


def _downsample(img, ds=DS):
    h, w = img.shape[:2]
    ys = (np.linspace(0, h - 1, ds)).astype(int); xs = (np.linspace(0, w - 1, ds)).astype(int)
    return (img[np.ix_(ys, xs)].astype(np.float32) / 255.0).reshape(ds, ds, 3)


class ObstacleVisionModule(ArmModule):
    def __init__(self, lr=0.02, rng=None, name="ObstacleVision"):
        super().__init__(name)
        rng = rng or np.random.default_rng(0)
        # LEARNED soft-argmax detector: a per-pixel colour filter -> spatial softmax -> board centroid/spread,
        # then an affine read-out to the board pose.  Few params, but localises BY CONSTRUCTION (an FC net
        # on raw pixels could not -- it collapsed to the mean board).  Colour filter init biased to "blue".
        self.a = np.array([-1.0, -1.0, 2.0]); self.b = 0.0    # colour filter (learned)
        self.T = 4.0                                          # saliency sharpening temperature (learned)
        self.A = np.zeros((3, 6)); self.A[0, 0] = self.A[1, 1] = self.A[2, 2] = 1.0
        self.c = np.zeros(3)                                  # affine over QUADRATIC features (parallax)
        self.lr = lr; self._img = None; self._pose = None
        self.add_out("occupancy", OCC_N * OCC_N, "perceived board occupancy over the working bbox")

    # ---- params <-> flat vector (for numerical-gradient training) ----
    def _get(self):
        return np.concatenate([self.a, [self.b, self.T], self.A.ravel(), self.c])

    def _set(self, v):
        self.a = v[:3]; self.b = v[3]; self.T = v[4]; self.A = v[5:23].reshape(3, 6); self.c = v[23:26]

    def _features(self, Xrgb):
        """Xrgb (N,DS,DS,3) -> soft-argmax centroid/spread, then QUADRATIC features (parallax of the tall
        board is nonlinear in its position, so a richer-than-affine read-out helps)."""
        s = 1.0 / (1.0 + np.exp(-self.T * (Xrgb @ self.a + self.b)))   # sharpened saliency (N,DS,DS)
        p = s / (s.sum((1, 2), keepdims=True) + 1e-6)
        mx = (p.sum(1) * _GX).sum(1); my = (p.sum(2) * _GX).sum(1)
        sy = np.sqrt((p.sum(2) * (_GX[None, :] - my[:, None]) ** 2).sum(1) + 1e-6)
        return np.stack([mx, my, sy, mx * my, mx * mx, my * my], 1)    # (N,6)

    def _pose_pred(self, Xrgb):
        return self._features(Xrgb) @ self.A.T + self.c       # (N,3) normalised pose

    # ---- scene posing for a clean look (cubes parked, arm retracted) ----
    @staticmethod
    def stage(sim):
        for nm in ("obj_red", "obj_green", "obj_blue"):
            sim.set_object(nm, [0.0, -0.55])
        rng3 = sim.arm3_range()
        sim.set_arm3_targets(np.array([0.0, rng3[1, 1] * 0.7, rng3[2, 0] * 0.5]))
        for _ in range(120):
            sim.step(2)

    def scatter_cubes(self, sim, rng):
        """Place the three cubes at random positions in the working region (the act21 perceive scene)."""
        for nm in ("obj_red", "obj_green", "obj_blue"):
            sim.set_object(nm, [rng.uniform(-0.11, 0.11), rng.uniform(0.08, 0.20)])

    def stage_scene(self, sim):
        """act21 perceive pose: arm at HOME, cubes present (scattered) -> matches run_combined's perceive."""
        sim.reset_home()

    def train(self, sim, steps=2500, iters=400, cam="top", staging="park", rng=None):
        """Self-supervised: render random boards, fit image -> normalised board POSE (cx, cy, half-y).
        Numerical-gradient descent over the detector params (small + robust; no backprop through the
        soft-argmax).  staging='park' = bare board (cubes parked, arm retracted); staging='scene' = the
        act21 scene (arm home + scattered cubes present each sample) so the detector ignores the cubes."""
        rng = rng or np.random.default_rng(1)
        board = BoardCtl(sim)
        if staging == "scene":
            self.stage_scene(sim)
        else:
            self.stage(sim)
        X = np.empty((steps, DS, DS, 3), np.float32); Y = np.empty((steps, 3), np.float32)
        for i in range(steps):
            if staging == "scene":
                self.scatter_cubes(sim, rng)
            cx = rng.uniform(*CX_R); cy = rng.uniform(*CY_R); hy = rng.uniform(*HY_R)
            board.place(cx, cy, 0.012, hy); mujoco.mj_forward(sim.m, sim.d)
            X[i] = _downsample(sim.render(cam))
            Y[i] = (np.array([cx, cy, hy]) - _LO) / _SP * 2.0 - 1.0

        def loss(v, idx):
            self._set(v)
            return float(np.mean((self._pose_pred(X[idx]) - Y[idx]) ** 2))

        v = self._get(); eps = 1e-3; m = np.zeros_like(v); vv = np.zeros_like(v); t = 0
        for it in range(iters):
            idx = rng.integers(0, steps, 384)
            g = np.zeros_like(v)
            for j in range(len(v)):
                vp = v.copy(); vp[j] += eps; vm = v.copy(); vm[j] -= eps
                g[j] = (loss(vp, idx) - loss(vm, idx)) / (2 * eps)
            t += 1; m = 0.9 * m + 0.1 * g; vv = 0.999 * vv + 0.001 * g * g
            v -= self.lr * (m / (1 - 0.9 ** t)) / (np.sqrt(vv / (1 - 0.999 ** t)) + 1e-8)
        self._set(v)

    def perceive(self, img):
        """Predict the board pose from the image, publish the reconstructed occupancy + the pose."""
        self._img = img
        p = self._pose_pred(_downsample(img)[None, ...])[0]
        cx, cy, hy = (np.clip(p, -1, 1) + 1.0) / 2.0 * _SP + _LO
        self._pose = (float(cx), float(cy), float(hy))
        occ = occ_map(cx, 0.012, hy, cy)
        self.set_out("occupancy", occ)
        return occ

    def perceive_sim(self, sim, cam="top"):
        return self.perceive(sim.render(cam))

    def step(self):
        pass
