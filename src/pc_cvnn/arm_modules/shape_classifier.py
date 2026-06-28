r"""ShapeClassifierModule — LEARNED perception of an object's FORM (cube / L / U), colour-agnostic AND
ROTATION-handled-by-the-complex-representation (the CVNN earns its keep here).

Pluggable ArmModule.  Two design choices:

1. Colour-DECOUPLED: the object is reduced to an OCCUPANCY mask from the per-pixel SATURATION
   (max(RGB)-min(RGB)) -- high on any coloured object, ~0 on the grey floor -- so hue is thrown away and
   only the FOOTPRINT (form) remains.

2. ROTATION = PHASE (the rotational analogue of RoPE, which made translation = phase).  The occupancy is
   sampled in POLAR rings around its centroid and angular-Fourier transformed -> COMPLEX angular harmonics
   F[ring, k].  Rotating the object by alpha shifts each harmonic's PHASE by k*alpha (verified), so the
   MAGNITUDE |F| is ROTATION-INVARIANT by construction.  The classifier reads |F| -> it never has to learn
   or memorise rotations (a flat real MLP on the raw mask had to, and confused cube<->L).  The harmonic
   PHASE simultaneously carries the orientation (free, like ObjectOrientation) -- exposed as shape_yaw.

   NOTE: this needs a clean rotation->image-rotation, i.e. a TOP-DOWN view; the default cam is "top".
   On the angled "overview" cam a world yaw is a perspective-warped image transform (would need the learned
   perspective correction, cf. ObjectOrientationModule).

Ports
  out : shape_logits (3)   cube / L / U class scores
        shape_id     (1)   argmax class index (0=cube, 1=L, 2=U)
        shape_yaw    (1)   object orientation (rad) read from the harmonic PHASE (k=2, mod pi)
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule

SHAPES = ["cube", "L", "U"]
SHAPE_BODY = {"cube": ("obj_red", np.array([0.012, 0.012, 0.012])), "L": ("obj_L", None), "U": ("obj_U", None)}
SAT_TH = 0.15
_MARKERS = ("target_marker", "target_sel_1", "target_sel_2", "target_sel_3")


def _softmax(z):
    z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)


class ShapeClassifierModule(ArmModule):
    def __init__(self, n_ang: int = 64, n_harm: int = 8, hid: int = 32, cam: str = "top", name="ShapeClassifier", rng=None):
        super().__init__(name)
        self.NA = int(n_ang); self.NH = int(n_harm); self.cam = cam
        self.RINGS = np.arange(2, 26, 2)                      # polar ring radii (px) around the centroid
        self.rng = rng or np.random.default_rng(0)
        din = len(self.RINGS) * self.NH                      # |F[ring, k]| features (rotation-invariant)
        self.W1 = self.rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = self.rng.normal(0, 1 / np.sqrt(hid), (len(SHAPES), hid)); self.b2 = np.zeros(len(SHAPES))
        self.fmu = np.zeros(din); self.fsd = np.ones(din)    # feature standardisation (set in train)
        self._last = None
        self.add_out("shape_logits", len(SHAPES), "cube / L / U class scores")
        self.add_out("shape_id", 1, "argmax shape class index (0=cube,1=L,2=U)")
        self.add_out("shape_yaw", 1, "object orientation (rad, mod pi) from the harmonic phase")

    # ------------------------------------------------------------------
    # colour-agnostic occupancy + COMPLEX angular-harmonic descriptor
    # ------------------------------------------------------------------
    def _harmonics(self, img):
        """img HxWx3 in [0,1] -> complex angular harmonics F[ring, k] of the saturation occupancy, or None."""
        mask = ((img.max(2) - img.min(2)) > SAT_TH).astype(np.float32)   # hue-agnostic occupancy
        if mask.sum() < 6:
            return None
        ys, xs = np.nonzero(mask); cy, cx = ys.mean(), xs.mean(); H, W = mask.shape
        th = np.arange(self.NA) / self.NA * 2 * np.pi
        F = np.empty((len(self.RINGS), self.NH), complex)
        for i, r in enumerate(self.RINGS):
            py = np.clip((cy + r * np.sin(th)).astype(int), 0, H - 1)
            px = np.clip((cx + r * np.cos(th)).astype(int), 0, W - 1)
            F[i] = np.fft.fft(mask[py, px])[:self.NH]
        return F

    def descriptor(self, img):
        """Rotation-INVARIANT feature vector |F[ring,k]| (the magnitude discards the rotation phase)."""
        F = self._harmonics(img)
        return None if F is None else np.abs(F).ravel()

    @staticmethod
    def _yaw_from(F):
        """Orientation from the harmonic phase: a long axis is k=2 (undirected), yaw = angle/2 (mod pi)."""
        ang = np.angle(F[:, 2]).mean()                       # average the k=2 phase over rings
        return 0.5 * float(ang)

    # ------------------------------------------------------------------
    def _forward(self, X):
        Xn = (X - self.fmu) / self.fsd
        h = np.maximum(0.0, Xn @ self.W1.T + self.b1)
        return h @ self.W2.T + self.b2, h

    def classify(self, feat):
        return self._forward(np.atleast_2d(feat))[0][0]

    @staticmethod
    def _park_markers(sim):
        import mujoco
        for nm in _MARKERS:                                  # the magenta markers corrupt the occupancy mask
            try:
                bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
                sim.d.mocap_pos[sim.m.body_mocapid[bid]] = [0.4, -0.6, -0.05]
            except Exception:
                pass

    def _perc_render(self, sim):
        import mujoco
        opt = mujoco.MjvOption(); opt.geomgroup[1] = 0       # hide the arm -> clean object footprint
        sim._renderer.update_scene(sim.d, camera=self.cam, scene_option=opt)
        return sim._renderer.render().astype(np.float32) / 255.0

    def train(self, sim, steps=4500, lr=0.05, bs=64, epochs=10, rng=None):
        """Self-supervised: render each shape at random pos + yaw (others parked), take the rotation-
        INVARIANT complex descriptor, label by truth, fit the classifier.  Returns train accuracy."""
        import mujoco
        rng = rng or self.rng
        sim.reset_home(); self._park_markers(sim)
        allb = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
        X, Y = [], []
        for _ in range(steps):
            k = int(rng.integers(len(SHAPES))); body, half = SHAPE_BODY[SHAPES[k]]
            for o in allb:
                sim.set_object(o, [0.4, 0.4 + 0.02 * allb.index(o)], z=0.008)
            if half is not None:
                sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)]] = half
            sim.set_object(body, [rng.uniform(-0.08, 0.08), rng.uniform(0.07, 0.20)], z=0.008,
                           yaw=rng.uniform(0, 2 * np.pi)); mujoco.mj_forward(sim.m, sim.d)
            d = self.descriptor(self._perc_render(sim))
            if d is not None:
                X.append(d); Y.append(k)
        X = np.array(X); Y = np.array(Y); n = len(X)
        self.fmu = X.mean(0); self.fsd = X.std(0) + 1e-9     # standardise the invariant features
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
        F = self._harmonics(self._perc_render(sim))
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
