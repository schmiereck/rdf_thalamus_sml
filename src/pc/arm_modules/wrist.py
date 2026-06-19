r"""WristRollModule — the agent's LEARNED ORIENTATION kinematics for the wrist-roll joint (joint_4).

The position kinematics (ArmBodyModel3D) is POSITION-only: it maps the 3 positioning joints -> the hand xyz
and ignores how the gripper is ORIENTED.  joint_4 (wrist-roll) rotates the finger-separation axis in the
table plane -- the orientation the claws grip ALONG.  At home it was frozen (a cube is symmetric, so the
grip yaw did not matter); to grip an ELONGATED object the claws must align to its narrow axis, which needs
this DOF and a model of what it does.

This module LEARNS that orientation kinematics the same way the position model was learned -- by BABBLING:
set random joint configurations, read the achieved claw yaw, fit  (cos yaw, sin yaw) = MLP(features(joints)).
Yaw is periodic, so the net regresses the cos/sin pair (never a wrapped angle).  The INVERSE (the thing the
grasp needs) -- "given the positioning pose, which joint_4 gives the desired grip yaw?" -- is then a tiny 1-D
search over joint_4 through the learned forward model.  No analytic rotation algebra; the map is learned.

Ports
  in  : joint_angles (5)        the full arm configuration
  out : claw_yaw (1)            the predicted finger-separation yaw (radians)
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule


def _feat(Q):
    """Joints (N,5) -> [1, cos, sin per joint] (10+1).  The grasp orientation is a product of hinge
    rotations, so its yaw's cos/sin are smooth in the cos/sin of the joint angles -- a good lifted basis."""
    Q = np.atleast_2d(Q).astype(float)
    return np.concatenate([np.ones((len(Q), 1)), np.cos(Q), np.sin(Q)], axis=1)   # (N, 11)


class _MLP:
    """2-hidden-layer tanh MLP + Adam (the recipe that worked for the displacement world model)."""

    def __init__(self, nin, nout, h=64, rng=None):
        rng = rng or np.random.default_rng(0)
        s = lambda a, b: rng.standard_normal((a, b)) * np.sqrt(2.0 / a)
        self.W1 = s(nin, h); self.b1 = np.zeros(h)
        self.W2 = s(h, h);   self.b2 = np.zeros(h)
        self.W3 = s(h, nout); self.b3 = np.zeros(nout)

    def _fwd(self, X):
        z1 = np.tanh(X @ self.W1 + self.b1)
        z2 = np.tanh(z1 @ self.W2 + self.b2)
        return z1, z2, z2 @ self.W3 + self.b3

    def predict(self, X):
        return self._fwd(X)[2]

    def fit(self, X, T, epochs=300, bs=256, lr=2e-3, rng=None):
        rng = rng or np.random.default_rng(0)
        ps = [self.W1, self.b1, self.W2, self.b2, self.W3, self.b3]
        m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0
        n = len(X)
        for ep in range(epochs):
            idx = rng.permutation(n)
            for s0 in range(0, n, bs):
                b = idx[s0:s0 + bs]; xb = X[b]; tb = T[b]
                z1, z2, out = self._fwd(xb)
                g = (out - tb) * (2.0 / len(b))
                gW3 = z2.T @ g; gb3 = g.sum(0)
                d2 = (g @ self.W3.T) * (1 - z2 ** 2); gW2 = z1.T @ d2; gb2 = d2.sum(0)
                d1 = (d2 @ self.W2.T) * (1 - z1 ** 2); gW1 = xb.T @ d1; gb1 = d1.sum(0)
                grads = [gW1, gb1, gW2, gb2, gW3, gb3]
                t += 1
                for i, (p, gr) in enumerate(zip(ps, grads)):
                    m[i] = 0.9 * m[i] + 0.1 * gr; v[i] = 0.999 * v[i] + 0.001 * gr * gr
                    p -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
        return float(np.mean((self.predict(X) - T) ** 2))


class WristRollModule(ArmModule):
    J4_RANGE = (0.0, 3.1416)

    def __init__(self, rng=None, name="WristRoll"):
        super().__init__(name)
        self.rng = rng or np.random.default_rng(0)
        self.net = _MLP(11, 2, h=64, rng=self.rng)     # features -> (cos yaw, sin yaw)
        self._last = None
        self.add_in("joint_angles", 5, "full arm configuration")
        self.add_out("claw_yaw", 1, "predicted finger-separation yaw (radians)")

    # ---- learn the orientation kinematics by babbling ----
    def babble(self, sim, n=6000, epochs=300):
        import mujoco
        from pc.pc_act14 import ARM_JOINTS
        rng = self.rng
        ranges = np.array([sim.m.jnt_range[sim._jid(j)] for j in ARM_JOINTS])   # (5,2)
        Q = rng.uniform(ranges[:, 0], ranges[:, 1], size=(n, 5))
        Y = np.empty(n)
        for i in range(n):
            for j, v in zip(ARM_JOINTS, Q[i]):
                sim.d.qpos[sim.jqadr[j]] = float(v)
            mujoco.mj_forward(sim.m, sim.d)
            Y[i] = sim.claw_yaw()
        T = np.stack([np.cos(Y), np.sin(Y)], axis=1)
        mse = self.net.fit(_feat(Q), T, epochs=epochs, rng=rng)
        # report the babble fit as an ANGULAR error (degrees), the honest metric
        pr = self.predict_yaw(Q)
        err = np.degrees(np.abs(np.arctan2(np.sin(Y - pr), np.cos(Y - pr))))
        return float(np.mean(err)), mse

    def predict_yaw(self, Q):
        out = self.net.predict(_feat(Q))
        return np.arctan2(out[:, 1], out[:, 0])

    # ---- inverse: which joint_4 gives the desired grip yaw, for a fixed positioning pose? ----
    def wrist_for_yaw(self, q_pose, desired_yaw, j3=None):
        """q_pose = [j0, j1, j2] (positioning joints); j3 = wrist-pitch (default HOME).  Returns the joint_4
        that the LEARNED model says yields claw_yaw closest to desired_yaw (1-D search through the model)."""
        from pc.pc_act14 import HOME
        j3 = HOME["joint_3"] if j3 is None else j3
        j4s = np.linspace(self.J4_RANGE[0], self.J4_RANGE[1], 121)
        Q = np.column_stack([np.full(len(j4s), q_pose[0]), np.full(len(j4s), q_pose[1]),
                             np.full(len(j4s), q_pose[2]), np.full(len(j4s), j3), j4s])
        pr = self.predict_yaw(Q)
        d = np.abs(np.arctan2(np.sin(pr - desired_yaw), np.cos(pr - desired_yaw)))
        return float(j4s[int(np.argmin(d))])

    def step(self):
        pass
