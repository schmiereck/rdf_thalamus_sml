r"""ShapeClassifierModule — LEARNED perception of an object's FORM (cube / L / U) from the camera,
decoupled from COLOUR.

Pluggable ArmModule (the 1D-PCModule port).  The object is reduced to a colour-AGNOSTIC OCCUPANCY MASK
-- per pixel the SATURATION  max(RGB) - min(RGB)  is high on any coloured object and ~0 on the grey
floor, so the mask carries the FOOTPRINT (the shape) with the hue thrown away.  A small MLP then reads
the centred, fixed-window G x G occupancy pattern -> the 3-way shape class.  Because the input never
contains hue, the net MUST use the form, not the colour, to tell cube / L / U apart -- the chosen
"Wahrnehmung anhand der Form" design.

Localisation here is colour-agnostic too: the crop is centred on the occupancy CENTROID (one object in
view), not a privileged simulator position.  (Finding the right object among DISTRACTORS by form is a
later screw.)

Ports
  out : shape_logits (3)   cube / L / U class scores
        shape_id     (1)   argmax class index (0=cube, 1=L, 2=U)
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule

SHAPES = ["cube", "L", "U"]
# which body renders each shape (+ a geom half-size override for the cube; L/U are composite, no override)
SHAPE_BODY = {"cube": ("obj_red", np.array([0.012, 0.012, 0.012])), "L": ("obj_L", None), "U": ("obj_U", None)}
SAT_TH = 0.15                                            # saturation threshold for "object" vs grey floor


def _softmax(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


class ShapeClassifierModule(ArmModule):
    def __init__(self, grid: int = 16, win: int = 64, hid: int = 64, name="ShapeClassifier", rng=None):
        super().__init__(name)
        self.G = int(grid)
        self.win = int(win)                                  # px window cropped around the object (win % G == 0)
        self.rng = rng or np.random.default_rng(0)
        din = self.G * self.G
        self.W1 = self.rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = self.rng.normal(0, 1 / np.sqrt(hid), (len(SHAPES), hid)); self.b2 = np.zeros(len(SHAPES))
        self._last = None
        self.add_out("shape_logits", len(SHAPES), "cube / L / U class scores")
        self.add_out("shape_id", 1, "argmax shape class index (0=cube,1=L,2=U)")

    # ------------------------------------------------------------------
    # colour-agnostic occupancy crop
    # ------------------------------------------------------------------
    def occupancy(self, img):
        """img HxWx3 in [0,1] -> a centred G x G occupancy mask (saturation-based), or None if no object."""
        sat = img.max(2) - img.min(2)                        # hue-agnostic: ~0 on grey floor, high on colour
        mask = (sat > SAT_TH).astype(np.float32)
        if mask.sum() < 6:
            return None
        ys, xs = np.nonzero(mask)
        cy, cx = int(round(ys.mean())), int(round(xs.mean()))
        h, w = mask.shape; r = self.win // 2
        pad = np.zeros((h + self.win, w + self.win), np.float32)
        pad[r:r + h, r:r + w] = mask                         # pad so the window never runs off the image
        win = pad[cy:cy + self.win, cx:cx + self.win]        # (win,win) centred on the occupancy centroid
        b = self.win // self.G
        return win.reshape(self.G, b, self.G, b).mean((1, 3)).reshape(-1)   # G x G mean-pooled -> flat

    # ------------------------------------------------------------------
    # forward / train (numpy MLP, cross-entropy)
    # ------------------------------------------------------------------
    def _forward(self, X):
        h = np.maximum(0.0, X @ self.W1.T + self.b1)
        logits = h @ self.W2.T + self.b2
        return logits, h

    def classify(self, occ):
        logits, _ = self._forward(np.atleast_2d(occ))
        return logits[0]

    def _perc_render(self, sim, cam):
        import mujoco
        opt = mujoco.MjvOption(); opt.geomgroup[1] = 0       # hide the arm -> clean object footprint
        sim._renderer.update_scene(sim.d, camera=cam, scene_option=opt)
        return sim._renderer.render().astype(np.float32) / 255.0

    def train(self, sim, cam="overview", steps=6000, lr=0.05, bs=64, epochs=8, rng=None):
        """Self-supervised: render each shape at random pos + yaw (others parked), take the colour-agnostic
        occupancy crop, label by the TRUE shape, fit the MLP.  Returns train accuracy."""
        import mujoco
        rng = rng or self.rng
        sim.reset_home(); sim.set_target_marker([0.0, -0.6], z=-0.05)
        allb = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
        X, Y = [], []
        for i in range(steps):
            k = int(rng.integers(len(SHAPES))); shp = SHAPES[k]
            body, half = SHAPE_BODY[shp]
            for o in allb:                                   # park everything off-stage
                sim.set_object(o, [0.4, 0.4 + 0.02 * allb.index(o)], z=0.008)
            if half is not None:
                sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)]] = half
            xy = [rng.uniform(-0.09, 0.09), rng.uniform(0.10, 0.20)]
            sim.set_object(body, xy, z=0.008, yaw=rng.uniform(0, 2 * np.pi)); mujoco.mj_forward(sim.m, sim.d)
            occ = self.occupancy(self._perc_render(sim, cam))
            if occ is not None:
                X.append(occ); Y.append(k)
        X = np.array(X); Y = np.array(Y); n = len(X)
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb = X[b]; yb = Y[b]
                logits, h = self._forward(xb)
                p = _softmax(logits); p[np.arange(len(b)), yb] -= 1.0; p /= len(b)   # dL/dlogits
                self.W2 -= lr * (p.T @ h); self.b2 -= lr * p.sum(0)
                dh = (p @ self.W2) * (h > 0)
                self.W1 -= lr * (dh.T @ xb); self.b1 -= lr * dh.sum(0)
        self._X, self._Y = X, Y
        return float((self._forward(X)[0].argmax(1) == Y).mean())

    # ------------------------------------------------------------------
    def perceive(self, sim, cam="overview"):
        """Perceive the (single) object's shape from the camera -> publish the class."""
        occ = self.occupancy(self._perc_render(sim, cam))
        if occ is None:
            self._last = None; self.set_out("shape_logits", None); self.set_out("shape_id", None)
            return None
        logits = self.classify(occ); k = int(logits.argmax())
        self._last = (k, _softmax(logits))
        self.set_out("shape_logits", logits); self.set_out("shape_id", [k])
        return SHAPES[k]

    def step(self):
        pass
