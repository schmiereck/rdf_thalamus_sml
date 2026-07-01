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

import os

import numpy as np

from .base import ArmModule
from pc_cvnn.network import PCNetwork
from pc_cvnn.node import PCNode, SensorNode
from pc_cvnn.connection import ConnType

SHAPES = ["cube", "L", "U"]
SHAPE_BODY = {"cube": ("obj_red", np.array([0.012, 0.012, 0.012])), "L": ("obj_L", None), "U": ("obj_U", None)}
SAT_TH = 0.15
GRIP_PX = 18                                             # gripper-sized window (px) for the densest-grip-point search
RED = np.array([0.9, 0.1, 0.1])
_MARKERS = ("target_marker", "target_sel_1", "target_sel_2", "target_sel_3")


def _softmax(z):
    z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)


class PCShapeHead:
    """Supervised shape classifier IN the complex PC engine (pc_cvnn PCNetwork): a SensorNode for the
    feature, a hidden PCNode and a class PCNode, wired generatively (class -> hidden -> feature) with
    COMPLEX weights and PC learning.  Reads the rotation-INVARIANT |F| descriptor: the complex harmonics F
    themselves are rotation-DEPENDENT (phase = rotation), so a flat net can't classify them invariantly
    (measured: ~chance on F vs 100% on |F|) -- the magnitude IS the invariant feature.  Trains supervised
    (clamp feature + one-hot class, relax, learn); infers the class by relaxing it free under the feature."""

    def __init__(self, din, n_cls=3, hid=24, rng=None):
        rng = rng or np.random.default_rng(0)
        net = PCNetwork(eta_inf=0.1, n_relax=40, eps_tol=1e-6, eta_learn=0.03, gamma=0.5, w_clip=3.0, rng=rng)
        self.x = net.add(SensorNode("sh_x", din))
        self.z = net.add(PCNode("sh_z", hid, activation="tanh", eta_temporal=0.0, rng=rng))
        self.y = net.add(PCNode("sh_y", n_cls, activation="identity", eta_temporal=0.0, rng=rng))
        net.connect("sh_z", "sh_x", ConnType.UP); net.connect("sh_y", "sh_z", ConnType.UP)
        self.net = net; self.n_cls = n_cls

    def fit(self, X, Y, epochs=8, rng=None):
        rng = rng or np.random.default_rng(0)
        for _ in range(epochs):
            for i in rng.permutation(len(X)):
                self.x.set_input(X[i])
                oh = np.zeros(self.n_cls); oh[int(Y[i])] = 1.0
                self.y.clamp(oh.astype(np.complex128)); self.net.step(learn=True)
            self.y.unclamp()

    def logits(self, feat):
        self.y.unclamp(); self.x.set_input(feat); self.net.step(learn=False)
        return np.real(self.y.mu).copy()


class ShapeClassifierModule(ArmModule):
    def __init__(self, n_ang=72, n_harm=8, hid=32, cam="overview", name="ShapeClassifier", rng=None, engine=None):
        super().__init__(name)
        self.NA = int(n_ang); self.NH = int(n_harm); self.cam = cam
        self.RW = np.arange(0.004, 0.046, 0.004)             # WORLD polar ring radii (m); reach ~44mm to cover
        self.RPX = np.arange(2, 26, 2)                       # px ring radii, used on the top cam
        self.rng = rng or np.random.default_rng(0)
        self.H = None; self.Hinv = None                      # table-plane homography world<->overview-px
        nr = len(self.RW)
        din = nr * self.NH
        # classifier backend: "mlp" (default, numpy) or "pc" (the complex PC engine, ACT_SHAPE_ENGINE=pc).
        # Both read the rotation-invariant |F|; the PC head reaches the same 100% (parity), in the PC paradigm.
        self.engine = (engine or os.environ.get("ACT_SHAPE_ENGINE", "mlp")).lower()
        self.W1 = self.rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = self.rng.normal(0, 1 / np.sqrt(hid), (len(SHAPES), hid)); self.b2 = np.zeros(len(SHAPES))
        self.head = PCShapeHead(din, len(SHAPES), rng=self.rng) if self.engine == "pc" else None
        self.fmu = np.zeros(din); self.fsd = np.ones(din)
        self._last = None
        self.add_in("shape_cmd", len(SHAPES), "one-hot shape command (cube/L/U) to select by FORM")
        self.add_out("shape_logits", len(SHAPES), "cube / L / U class scores")
        self.add_out("shape_id", 1, "argmax shape class index (0=cube,1=L,2=U)")
        self.add_out("shape_yaw", 1, "object orientation (rad, mod pi) from the harmonic phase")
        self.add_out("selected_xy", 2, "world xy of the object whose FORM matches shape_cmd")

    # ------------------------------------------------------------------
    # rendering / housekeeping
    # ------------------------------------------------------------------
    @staticmethod
    def _park_markers(sim):
        import mujoco
        moved = False
        for nm in _MARKERS:                                  # magenta markers corrupt the saturation mask
            try:
                bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
                sim.d.mocap_pos[sim.m.body_mocapid[bid]] = [0.4, -0.6, -0.05]; moved = True
            except Exception:
                pass
        if moved:
            mujoco.mj_forward(sim.m, sim.d)                  # CRITICAL: refresh xpos, else the markers still
            #   RENDER at their old spots (mocap_pos alone doesn't update the rendered pose) -> their magenta
            #   disks survive in the mask and classify as "cube", hijacking select('cube').

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
            p = _rand_xy(rng); sim.set_object("obj_red", p, z=0.012); mujoco.mj_forward(sim.m, sim.d)
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
    def _mask(self, img_u8):
        """uint8 HxWx3 -> hue-agnostic saturation occupancy mask (1 on any coloured object, 0 on floor)."""
        f = img_u8.astype(np.float32) / 255.0
        return ((f.max(2) - f.min(2)) > SAT_TH).astype(np.float32)

    def _centroid(self, mask):
        """Centre of `mask`: a WORLD centroid (overview, perspective-correct via H) or a PX centroid (top)."""
        ys, xs = np.nonzero(mask)
        if self.H is not None:
            return self._px_to_world(np.column_stack([xs, ys])).mean(0)
        return np.array([xs.mean(), ys.mean()])

    def _harmonics_at(self, mask, ctr):
        """Complex angular harmonics F[ring,k] of `mask`, sampled on polar rings around `ctr`.  Overview:
        rings in WORLD metres around the world centroid, projected to px by H (rotation is clean there).
        Top: rings in px around the px centroid.  Sampling ONLY this `mask` ignores neighbouring objects."""
        H, Wd = mask.shape
        th = np.arange(self.NA) / self.NA * 2 * np.pi
        ring = np.column_stack([np.cos(th), np.sin(th)])
        if self.H is not None:
            F = np.empty((len(self.RW), self.NH), complex)
            for i, r in enumerate(self.RW):
                rp = self._world_to_px(ctr + r * ring)
                py = np.clip(rp[:, 1].astype(int), 0, H - 1); px = np.clip(rp[:, 0].astype(int), 0, Wd - 1)
                F[i] = np.fft.fft(mask[py, px])[:self.NH]
            return F
        F = np.empty((len(self.RPX), self.NH), complex)
        for i, r in enumerate(self.RPX):
            py = np.clip((ctr[1] + r * np.sin(th)).astype(int), 0, H - 1)
            px = np.clip((ctr[0] + r * np.cos(th)).astype(int), 0, Wd - 1)
            F[i] = np.fft.fft(mask[py, px])[:self.NH]
        return F

    def _harmonics(self, img_u8):
        """Single-object: harmonics of the whole occupancy mask (assumes one object in view)."""
        mask = self._mask(img_u8)
        return None if mask.sum() < 6 else self._harmonics_at(mask, self._centroid(mask))

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
        if self.engine == "pc":                              # complex PC-engine head on the standardised |F|
            return self.head.logits((np.asarray(feat, float) - self.fmu) / self.fsd)
        return self._forward(np.atleast_2d(feat))[0][0]

    def train(self, sim, steps=4500, lr=0.05, bs=64, epochs=10, rng=None, viz_fn=None, viz_every=40):
        """Self-supervised: render each shape at random pos + yaw (others parked), take the rotation-
        INVARIANT complex descriptor, label by truth, fit the classifier.  Returns train accuracy.
        Calibrates the homography first if cam is the angled overview and not yet calibrated.
        viz_fn(i, steps): optional callback every viz_every steps (e.g. to show the training live)."""
        import mujoco
        rng = rng or self.rng
        if self.cam != "top" and self.H is None:
            self.calibrate(sim, rng=np.random.default_rng(3))
        sim.reset_home(); self._park_markers(sim)
        allb = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
        X, Y = [], []
        for i in range(steps):
            k = int(rng.integers(len(SHAPES))); body, half = SHAPE_BODY[SHAPES[k]]
            for o in allb:
                sim.set_object(o, [0.5, -0.6], z=0.008)
            bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
            if half is not None:
                sim.m.geom_size[sim.m.body_geomadr[bid]] = half
            zc = float(sim.m.geom_size[sim.m.body_geomadr[bid]][2])   # rest z = the object's half-height
            sim.set_object(body, [rng.uniform(-0.08, 0.08), rng.uniform(0.08, 0.20)], z=zc,
                           yaw=rng.uniform(0, 2 * np.pi)); mujoco.mj_forward(sim.m, sim.d)
            if viz_fn is not None and i % viz_every == 0:        # show the form-training live (every N steps)
                viz_fn(i, steps, SHAPES[k])
            d = self.descriptor(self._render_u8(sim))
            if d is not None:
                X.append(d); Y.append(k)
        X = np.array(X); Y = np.array(Y); n = len(X)
        self.fmu = X.mean(0); self.fsd = X.std(0) + 1e-9
        self._X, self._Y = X, Y
        if self.engine == "pc":                              # fit the complex PC head on standardised |F|
            self.head.fit((X - self.fmu) / self.fsd, Y, epochs=min(epochs, 8), rng=rng)
            chk = rng.choice(n, min(n, 300), replace=False)  # train acc on a subset (PC infer is per-sample)
            return float(np.mean([self.classify(X[i]).argmax() == Y[i] for i in chk]))
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb = X[b]; yb = Y[b]
                logits, h = self._forward(xb)
                p = _softmax(logits); p[np.arange(len(b)), yb] -= 1.0; p /= len(b)
                self.W2 -= lr * (p.T @ h); self.b2 -= lr * p.sum(0)
                dh = (p @ self.W2) * (h > 0)
                self.W1 -= lr * (dh.T @ ((xb - self.fmu) / self.fsd)); self.b1 -= lr * dh.sum(0)
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

    def perceive_all(self, sim, min_area=40):
        """Localise + classify EVERY object under distractors: segment the colour-agnostic occupancy into
        CONNECTED COMPONENTS (one blob = one object), then classify each by its own form descriptor (rings
        sampled ONLY on that component, so neighbours don't leak in).  Returns a list of detections:
        {shape, id, prob, pos (world xy, overview), yaw, px}.  No colour, no privileged positions."""
        from scipy import ndimage
        self._park_markers(sim)
        mask = self._mask(self._render_u8(sim))
        labels, n = ndimage.label(mask)
        out = []
        for lab in range(1, n + 1):
            comp = (labels == lab).astype(np.float32)
            if comp.sum() < min_area:
                continue                                     # drop specks / glints
            ctr = self._centroid(comp)                       # world (overview) or px (top)
            F = self._harmonics_at(comp, ctr)
            logits = self.classify(np.abs(F).ravel()); k = int(logits.argmax())
            ys, xs = np.nonzero(comp)
            # GRASP point: the MATERIAL point nearest the centroid -- central + on a (thin) bar, which the
            # gripper spans cleanly.  Best for the thin-bar shapes (the cube-built / tip / wrist variants were
            # all marginal; this v1 grasped the thin-bar L well).  No wrist (orientation gave no gain).
            grasp = ctr
            if self.H is not None:
                W = self._px_to_world(np.column_stack([xs, ys]))            # world coords of the component px
                grasp = W[int(np.argmin(np.linalg.norm(W - ctr, axis=1)))]  # nearest material to the centroid
            out.append({"shape": SHAPES[k], "id": k, "prob": float(_softmax(logits)[k]),
                        "pos": (ctr if self.H is not None else None), "grasp_xy": grasp, "grasp_yaw": 0.0,
                        "yaw": self._yaw_from(F), "px": np.array([xs.mean(), ys.mean()])})
        return out

    def select(self, sim, shape_cmd, min_area=40):
        """Command CONDITIONED on FORM (the colour-free analogue of the colour SelectionHead): among ALL
        objects detected by perceive_all, return the detection whose SHAPE matches the command -- its world
        xy + the full detection -- or None if no such shape is present.  shape_cmd: 'cube'/'L'/'U' or 0/1/2;
        if several match (e.g. two cubes) the most confident is returned.  Publishes selected_xy."""
        k = shape_cmd if isinstance(shape_cmd, (int, np.integer)) else SHAPES.index(shape_cmd)
        matches = [d for d in self.perceive_all(sim, min_area=min_area) if d["id"] == k]
        if not matches:
            self._sel = None; self.set_out("selected_xy", None); return None
        best = max(matches, key=lambda d: d["prob"])
        self._sel = best; self.set_out("selected_xy", best["pos"])
        return best

    def step(self):
        pass
