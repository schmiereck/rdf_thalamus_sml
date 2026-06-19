r"""ObjectOrientationModule — LEARNED perception of an ELONGATED object's long-axis orientation from the camera.

Step 2 of the wrist-roll extension.  To grip an elongated object the claws must align to its NARROW axis;
that needs the object's orientation, PERCEIVED (the user's choice: no privileged simulator angle).

A colour-filtered saliency map of the object gives a strong principal-axis signal already (the long axis is
visible from above), BUT the overhead camera is angled, so the IMAGE principal angle is a perspective-warped,
position-dependent version of the true table yaw.  The LEARNED part is that correction: a map
  (image principal axis, image position)  ->  (cos 2theta, sin 2theta)   [table long-axis]
fitted self-supervised by rendering the object at known random orientations.  Orientation is regressed as the
DOUBLE angle (cos/sin of 2theta) because a long axis is UNDIRECTED -- theta and theta+180 look identical and
grip identically, so the 180-deg ambiguity is designed in, not a bug.

Closed-form least-squares fit (the target is near-linear in the lifted features), so it is cheap + robust --
the same spirit as the board detector's soft-argmax: a structured read-out that localises by construction,
not an FC net on raw pixels (which collapses).

Ports
  out : grip_yaw (1)   the table yaw (radians) the CLAWS should align along to grip (long-axis + 90 deg)
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule

# colour filter directions (centred RGB) for the three objects.  Off-channels are strongly NEGATIVE so the
# magenta (1,0,1) target marker -- which sits in the object zone -- is rejected (red: 1-0-1.4<0; blue same).
COLOUR_W = {"obj_red": np.array([1.0, -0.8, -1.4]), "obj_green": np.array([-0.8, 1.0, -0.8]),
            "obj_blue": np.array([-1.4, -0.8, 1.0])}


def _saliency_axis(img, w):
    """Colour-filtered saliency -> image-plane principal axis (cos2phi, sin2phi), eigenvalue ratio,
    normalised centroid.  img is HxWx3 in [0,1]."""
    h, wd = img.shape[:2]
    s = np.clip(img.reshape(-1, 3) @ w, 0.0, None).reshape(h, wd)
    tot = s.sum() + 1e-6
    s = s / tot
    ys, xs = np.mgrid[0:h, 0:wd]
    mx = float((s * xs).sum()); my = float((s * ys).sum())
    cxx = float((s * (xs - mx) ** 2).sum()); cyy = float((s * (ys - my) ** 2).sum())
    cxy = float((s * (xs - mx) * (ys - my)).sum())
    # principal axis of the 2x2 covariance via the closed-form double-angle (robust, no eig call)
    phi2 = np.arctan2(2.0 * cxy, cxx - cyy)                       # = 2*phi (double angle directly)
    ev_gap = np.hypot(2.0 * cxy, cxx - cyy) / (cxx + cyy + 1e-6)  # anisotropy (1 = very elongated)
    return (np.cos(phi2), np.sin(phi2), float(ev_gap), mx / wd, my / h)


class ObjectOrientationModule(ArmModule):
    def __init__(self, name="ObjectOrientation"):
        super().__init__(name)
        self.M = None                                            # learned features -> (cos2t, sin2t)
        self._yaw = None
        self.add_out("grip_yaw", 1, "table yaw (radians) the claws align along to grip")

    @staticmethod
    def _feat(F):
        """F = (cos2phi, sin2phi, evgap, px, py) per sample -> lifted features for the perspective map.
        The image->table axis rotation is position-dependent, so cross px/py with the axis terms."""
        F = np.atleast_2d(F).astype(float)
        c2, s2, _, px, py = F.T
        return np.column_stack([c2, s2, c2 * px, s2 * px, c2 * py, s2 * py, px, py, np.ones_like(c2)])

    def train(self, sim, cmd="obj_red", cam="overview", steps=2500, half=(0.030, 0.012, 0.012), rng=None):
        """Self-supervised: render the object at random pos + yaw, fit (image axis -> table double-angle).
        Other objects are parked so only the commanded one responds to its colour filter."""
        import mujoco
        rng = rng or np.random.default_rng(0)
        w = COLOUR_W[cmd]
        bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, cmd)
        sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(half, float)
        others = [o for o in ("obj_red", "obj_green", "obj_blue") if o != cmd]
        sim.reset_home()
        sim.set_target_marker([0.0, -0.6], z=-0.05)              # park the magenta marker (perception nuisance)
        for o in others:
            sim.set_object(o, [0.0, -0.55])
        X = np.empty((steps, 5)); T = np.empty((steps, 2))
        for i in range(steps):
            xy = [rng.uniform(-0.10, 0.10), rng.uniform(0.10, 0.20)]; yaw = rng.uniform(0, np.pi)
            sim.set_object(cmd, xy, z=float(half[2]), yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(2)
            img = sim.render(cam).astype(np.float32) / 255.0
            c2, s2, ev, px, py = _saliency_axis(img, w)
            X[i] = [c2, s2, ev, px, py]; T[i] = [np.cos(2 * yaw), np.sin(2 * yaw)]
        Phi = self._feat(X)
        self.M, *_ = np.linalg.lstsq(Phi, T, rcond=None)         # closed-form least squares
        pr = Phi @ self.M
        pred = 0.5 * np.arctan2(pr[:, 1], pr[:, 0]); true = 0.5 * np.arctan2(T[:, 1], T[:, 0])
        return float(np.mean(self._axis_err(true, pred)))        # train-set axis error (deg)

    @staticmethod
    def _axis_err(a, b):
        """Angular error MODULO 180 deg (undirected axis), in degrees."""
        d = np.arctan2(np.sin(2 * (a - b)), np.cos(2 * (a - b))) / 2.0
        return np.degrees(np.abs(d))

    def perceive(self, sim, cmd, cam="overview"):
        """Perceive the object's long axis -> publish the grip yaw (long-axis + 90 deg, the claws cross it)."""
        w = COLOUR_W[cmd]
        img = sim.render(cam).astype(np.float32) / 255.0
        F = np.array(_saliency_axis(img, w))
        pr = (self._feat(F) @ self.M)[0]
        long_axis = 0.5 * float(np.arctan2(pr[1], pr[0]))
        self._yaw = long_axis + np.pi / 2.0                      # grip ACROSS the long axis
        self.set_out("grip_yaw", [self._yaw])
        return self._yaw, long_axis

    def step(self):
        pass
