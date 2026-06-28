r"""ShapeClassifierModule — LEARNED perception of an object's FORM (cube / L / U), colour-agnostic AND
ROTATION-handled-by-the-complex-representation (the CVNN earns its keep here).

Design:

1. Colour-DECOUPLED: object -> OCCUPANCY mask from the per-pixel SATURATION (max(RGB)-min(RGB)) -- high on
   any coloured object, ~0 on the grey floor -- so hue is thrown away, only the FOOTPRINT (form) remains.

2. ROTATION = PHASE (the rotational analogue of RoPE).  The occupancy is sampled in POLAR rings around its
   centroid and angular-Fourier transformed -> COMPLEX harmonics F[ring,k].  A rotation by alpha shifts each
   harmonic's PHASE by k*alpha, so the MAGNITUDE |F| is ROTATION-INVARIANT by construction; the classifier
   reads |F| and never learns rotations.  The phase carries the orientation (shape_yaw, free).

3. WORKS ON THE ANGLED "overview" CAMERA via a calibrated TABLE-PLANE HOMOGRAPHY: a world rotation is not a
   clean IMAGE rotation under perspective, BUT the table is a plane, so the polar rings are sampled in WORLD
   (table) coordinates -- where rotation IS clean -- and each ring point is projected into the overview image
   by the homography (overview-px <-> world, fit by DLT in calibrate()).  So rotation = phase holds in the
   rectified world frame.  cam="top" instead samples directly in px (a straight-down view needs no rectify).

Ports
  out : shape_logits (3)   cube / L / U class scores
        shape_id     (1)   argmax class index (0=cube, 1=L, 2=U)
        shape_yaw    (1)   object orientation (rad, mod pi) from the harmonic phase (world frame)
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule

SHAPES = ["cube", "L", "U"]
SHAPE_BODY = {"cube": ("obj_red", np.array([0.012, 0.012, 0.012])), "L": ("obj_L", None), "U": ("obj_U", None)}
SAT_TH = 0.15
RED = np.array([0.9, 0.1, 0.1])
_MARKERS = ("target_marker", "target_sel_1", "target_sel_2", "target_sel_3")


def _softmax(z):
    z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)


class ShapeClassifierModule(ArmModule):
    def __init__(self, n_ang=72, n_harm=8, hid=32, cam="overview", name="ShapeClassifier", rng=None):
        super().__init__(name)
        self.NA = int(n_ang); self.NH = int(n_harm); self.cam = cam
        self.RW = np.arange(0.003, 0.033, 0.003)             # WORLD polar ring radii (m), used on overview
        self.RPX = np.arange(2, 26, 2)                       # px ring radii, used on the top cam
        self.rng = rng or np.random.default_rng(0)
        self.H = None; self.Hinv = None                      # table-plane homography world<->overview-px
        nr = len(self.RW)
        din = nr * self.NH
        self.W1 = self.rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = self.rng.normal(0, 1 / np.sqrt(hid), (len(SHAPES), hid)); self.b2 = np.zeros(len(SHAPES))
        self.fmu = np.zeros(din); self.fsd = np.ones(din)
        self._last = None
        self.add_out("shape_logits", len(SHAPES), "cube / L / U class scores")
        self.add_out("shape_id", 1, "argmax shape class index (0=cube,1=L,2=U)")
        self.add_out("shape_yaw", 1, "object orientation (rad, mod pi) from the harmonic phase")

    # ------------------------------------------------------------------
    # rendering / housekeeping
    # ------------------------------------------------------------------
    @staticmethod
    def _park_markers(sim):
        import mujoco
        for nm in _MARKERS:                                  # magenta markers corrupt the saturation mask
            try:
                bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
                sim.d.mocap_pos[sim.m.body_mocapid[bid]] = [0.4, -0.6, -0.05]
            except Exception:
                pass

    def _render_u8(self, sim):
        import mujoco
        opt = mujoco.MjvOption(); opt.geomgroup[1] = 0       # hide the arm -> clean footprint
        sim._renderer.update_scene(sim.d, camera=self.cam, scene_option=opt)
        return sim._renderer.render()                        # uint8

    # ------------------------------------------------------------------
    # table-plane homography (overview px <-> world), fit by DLT
    # ------------------------------------------------------------------
    def _world_to_px(self, W):
        Wh = np.column_stack([np.atleast_2d(W), np.ones(len(np.atleast_2d(W)))])
        q = Wh @ self.H.T
        return q[:, :2] / q[:, 2:3]

    def _px_to_world(self, P):
        Ph = np.column_stack([np.atleast_2d(P).astype(float), np.ones(len(np.atleast_2d(P)))])
        q = Ph @ self.Hinv.T
        return q[:, :2] / q[:, 2:3]

    def calibrate(self, sim, n=40, rng=None):
        """Fit the overview-px <-> world table-plane homography (DLT), like setup_following_fovea: place a
        red marker object at known world spots, detect its px, solve the 8-DOF homography."""
        import mujoco
        from pc_cvnn.pc_act15 import detect_px
        from pc_cvnn.pc_act14 import _rand_xy
        rng = rng or np.random.default_rng(3)
        sim.reset_home(); self._park_markers(sim)
        for o in ("obj_green", "obj_blue", "obj_L", "obj_U"):
            sim.set_object(o, [0.5, -0.6], z=0.008)
        W, P = [], []
        for _ in range(n):
            p = _rand_xy(rng); sim.set_object("obj_red", p, z=0.008); mujoco.mj_forward(sim.m, sim.d)
            px = detect_px(self._render_u8(sim), RED)
            if px is not None:
                W.append([p[0], p[1]]); P.append([px[0], px[1]])
        Mh = []
        for (x, y), (u, v) in zip(W, P):
            Mh.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
            Mh.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
        self.H = np.linalg.svd(np.array(Mh))[2][-1].reshape(3, 3); self.Hinv = np.linalg.inv(self.H)
        return len(W)

    # ------------------------------------------------------------------
    # colour-agnostic occupancy + COMPLEX angular-harmonic descriptor
    # ------------------------------------------------------------------
    def _harmonics(self, img_u8):
        """uint8 HxWx3 -> complex angular harmonics F[ring,k] (world frame if calibrated, else px), or None."""
        f = img_u8.astype(np.float32) / 255.0
        mask = ((f.max(2) - f.min(2)) > SAT_TH).astype(np.float32)   # hue-agnostic occupancy
        if mask.sum() < 6:
            return None
        H, Wd = mask.shape
        ys, xs = np.nonzero(mask)
        th = np.arange(self.NA) / self.NA * 2 * np.pi
        if self.H is not None:                               # WORLD-frame sampling (overview perspective)
            cw = self._px_to_world(np.column_stack([xs, ys])).mean(0)    # world centroid (perspective-correct)
            F = np.empty((len(self.RW), self.NH), complex)
            for i, r in enumerate(self.RW):
                ring_w = cw + r * np.column_stack([np.cos(th), np.sin(th)])
                rp = self._world_to_px(ring_w)
                py = np.clip(rp[:, 1].astype(int), 0, H - 1); px = np.clip(rp[:, 0].astype(int), 0, Wd - 1)
                F[i] = np.fft.fft(mask[py, px])[:self.NH]
            return F
        cy, cx = ys.mean(), xs.mean()                        # px-frame sampling (top-down cam)
        F = np.empty((len(self.RPX), self.NH), complex)
        for i, r in enumerate(self.RPX):
            py = np.clip((cy + r * np.sin(th)).astype(int), 0, H - 1)
            px = np.clip((cx + r * np.cos(th)).astype(int), 0, Wd - 1)
            F[i] = np.fft.fft(mask[py, px])[:self.NH]
        return F

    def descriptor(self, img_u8):
        F = self._harmonics(img_u8)
        return None if F is None else np.abs(F).ravel()

    @staticmethod
    def _yaw_from(F):
        return 0.5 * float(np.angle(F[:, 2]).mean())         # long axis = k=2 (undirected), yaw mod pi

    # ------------------------------------------------------------------
    def _forward(self, X):
        Xn = (X - self.fmu) / self.fsd
        h = np.maximum(0.0, Xn @ self.W1.T + self.b1)
        return h @ self.W2.T + self.b2, h

    def classify(self, feat):
        return self._forward(np.atleast_2d(feat))[0][0]

    def train(self, sim, steps=4500, lr=0.05, bs=64, epochs=10, rng=None):
        """Self-supervised: render each shape at random pos + yaw (others parked), take the rotation-
        INVARIANT complex descriptor, label by truth, fit the classifier.  Returns train accuracy.
        Calibrates the homography first if cam is the angled overview and not yet calibrated."""
        import mujoco
        rng = rng or self.rng
        if self.cam != "top" and self.H is None:
            self.calibrate(sim, rng=np.random.default_rng(3))
        sim.reset_home(); self._park_markers(sim)
        allb = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
        X, Y = [], []
        for _ in range(steps):
            k = int(rng.integers(len(SHAPES))); body, half = SHAPE_BODY[SHAPES[k]]
            for o in allb:
                sim.set_object(o, [0.5, -0.6], z=0.008)
            if half is not None:
                sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)]] = half
            sim.set_object(body, [rng.uniform(-0.08, 0.08), rng.uniform(0.08, 0.20)], z=0.008,
                           yaw=rng.uniform(0, 2 * np.pi)); mujoco.mj_forward(sim.m, sim.d)
            d = self.descriptor(self._render_u8(sim))
            if d is not None:
                X.append(d); Y.append(k)
        X = np.array(X); Y = np.array(Y); n = len(X)
        self.fmu = X.mean(0); self.fsd = X.std(0) + 1e-9
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb = X[b]; yb = Y[b]
                logits, h = self._forward(xb)
                p = _softmax(logits); p[np.arange(len(b)), yb] -= 1.0; p /= len(b)
                self.W2 -= lr * (p.T @ h); self.b2 -= lr * p.sum(0)
                dh = (p @ self.W2) * (h > 0)
                self.W1 -= lr * (dh.T @ ((xb - self.fmu) / self.fsd)); self.b1 -= lr * dh.sum(0)
        self._X, self._Y = X, Y
        return float((self._forward(X)[0].argmax(1) == Y).mean())

    # ------------------------------------------------------------------
    def perceive(self, sim):
        """Perceive the (single, in-view) object's shape + orientation from the camera."""
        self._park_markers(sim)
        F = self._harmonics(self._render_u8(sim))
        if F is None:
            self._last = None
            for pn in ("shape_logits", "shape_id", "shape_yaw"):
                self.set_out(pn, None)
            return None
        logits = self.classify(np.abs(F).ravel()); k = int(logits.argmax()); yaw = self._yaw_from(F)
        self._last = (k, _softmax(logits), yaw)
        self.set_out("shape_logits", logits); self.set_out("shape_id", [k]); self.set_out("shape_yaw", [yaw])
        return SHAPES[k]

    def step(self):
        pass
