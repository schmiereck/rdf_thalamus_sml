"""LearnedInverseKinematics — replaces the SCRIPTED analytic reach controller with a LEARNED one.

The old reach control (`ArmBodyModel3D.reach_velocity`) computed the joint step from the analytic
damped-least-squares pseudo-inverse of the learned FK's Jacobian:  dq = Jᵀ(JJᵀ+λI)⁻¹·v.  The
inversion law is hand-written.  This learns it instead.

A net predicts the CONFIGURATION-DEPENDENT inverse Jacobian as a matrix  M(q3) ∈ ℝ³ˣ³, and

    dq = M(q3) · v      (v = desired hand velocity)

so the (physically correct) linearity in v is built in, while M's dependence on the arm
configuration is learned.  Trained SELF-SUPERVISED by babbling: sample q3 and a small random dq,
observe the hand displacement v = fk(q3+dq) − fk(q3) through the agent's own learned `fk`, and fit
M(q3) so that M(q3)·v ≈ dq.  No analytic Jacobian anywhere — the differential inverse kinematics is
itself learned.
"""
from __future__ import annotations

import numpy as np


class LearnedInverseKinematics:
    def __init__(self, hid: int = 128, lr: float = 0.03, rng=None) -> None:
        rng = rng or np.random.default_rng(0)
        self.W1 = rng.normal(0, 1 / np.sqrt(3), (hid, 3)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (9, hid)); self.b2 = np.zeros(9)   # -> M(q3) 3x3
        self.lr = lr
        self.qmu = np.zeros(3); self.qsd = np.ones(3)
        self.sv = 1.0; self.sd = 1.0                       # v / dq magnitude scales (M learned on v/sv, dq/sd)
        self.v_max = 0.015
        self.trained = False

    # ------------------------------------------------------------------
    def _M(self, q3n):                                     # q3n: (B,3) normalised -> (B,3,3)
        h = np.tanh(q3n @ self.W1.T + self.b1)             # (B,hid)
        Mf = h @ self.W2.T + self.b2                       # (B,9)
        return Mf.reshape(-1, 3, 3), h

    def train(self, fk, q_lo, q_hi, steps: int = 80000, dq_amp: float = 0.03,
              epochs: int = 10, bs: int = 256, wd: float = 3e-2, rng=None) -> float:
        """Babble (q3, dq) -> v=fk(q3+dq)-fk(q3); fit M(q3) so M(q3)·v ≈ dq.  Returns the babble
        reconstruction error (mm of hand displacement through fk)."""
        rng = rng or np.random.default_rng(1)
        q_lo = np.asarray(q_lo, float); q_hi = np.asarray(q_hi, float)
        Q = rng.uniform(q_lo, q_hi, (steps, 3))
        DQ = rng.uniform(-dq_amp, dq_amp, (steps, 3))
        V = np.array([fk(q + dq) - fk(q) for q, dq in zip(Q, DQ)])
        self.v_max = float(np.percentile(np.linalg.norm(V, axis=1), 95))
        self.qmu, self.qsd = Q.mean(0), Q.std(0) + 1e-9
        self.sv = float(V.std() + 1e-9); self.sd = float(DQ.std() + 1e-9)   # O(1) train scales
        Qn = (Q - self.qmu) / self.qsd
        Vn = V / self.sv; DQn = DQ / self.sd               # learn M' so M'·(v/sv) ≈ dq/sd
        n = steps
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; qn, v, dq = Qn[b], Vn[b], DQn[b]
                M, h = self._M(qn)                          # (B,3,3),(B,hid)
                pred = np.einsum("bij,bj->bi", M, v)        # (B,3)
                e = (pred - dq) / len(b)                    # (B,3)
                dMf = (e[:, :, None] * v[:, None, :]).reshape(len(b), 9)   # (B,9)
                # weight decay on the M-producing weights = a LEARNED analogue of DLS damping:
                # it penalises large inverse-Jacobian entries, taming near-singular configurations.
                self.W2 -= self.lr * (dMf.T @ h + wd * self.W2); self.b2 -= self.lr * dMf.sum(0)
                dh = (dMf @ self.W2) * (1 - h ** 2)         # (B,hid)
                self.W1 -= self.lr * (dh.T @ qn + wd * self.W1); self.b1 -= self.lr * dh.sum(0)
        self.trained = True
        chk = rng.integers(0, n, 512)
        rec = [np.linalg.norm(fk(Q[i] + self.predict_dq(Q[i], V[i])) - fk(Q[i]) - V[i]) for i in chk]
        return float(np.mean(rec)) * 1000.0

    def observe(self, q3, v, dq, lr: float = 5e-3, wd: float = 3e-2) -> None:
        """LIFELONG: one online SGD step fitting M(q3)*v ≈ dq from a REAL observed motion
        (v = actual hand displacement, dq = actual joint change).  Adapts the learned inverse
        kinematics to the real arm as it moves — no analytic Jacobian, no babbling."""
        if not self.trained:
            return
        qn = ((np.asarray(q3, float) - self.qmu) / self.qsd)[None, :]
        vn = (np.asarray(v, float) / self.sv)[None, :]
        dqn = (np.asarray(dq, float) / self.sd)[None, :]
        M, h = self._M(qn)                                  # (1,3,3),(1,hid)
        pred = np.einsum("bij,bj->bi", M, vn)               # (1,3)
        e = pred - dqn                                      # (1,3)
        dMf = (e[:, :, None] * vn[:, None, :]).reshape(1, 9)
        self.W2 -= lr * (dMf.T @ h + wd * self.W2); self.b2 -= lr * dMf.sum(0)
        dh = (dMf @ self.W2) * (1 - h ** 2)
        self.W1 -= lr * (dh.T @ qn + wd * self.W1); self.b1 -= lr * dh.sum(0)

    # ------------------------------------------------------------------
    def predict_dq(self, q3, v):
        qn = (np.asarray(q3, float) - self.qmu) / self.qsd
        M, _ = self._M(qn[None, :])
        return self.sd * (M[0] @ (np.asarray(v, float) / self.sv))   # de-normalise the scales

    def reach_velocity(self, fk, q3, target, gain: float = 2.0, max_dq: float = 0.03):
        """Drop-in for ArmBodyModel3D.reach_velocity, but the inverse is LEARNED (no Jacobian)."""
        q3 = np.asarray(q3, float)
        v = gain * (np.asarray(target, float) - fk(q3))
        nv = float(np.linalg.norm(v))
        if nv > self.v_max:                                 # stay in the learned local regime
            v = v * (self.v_max / nv)
        dq = self.predict_dq(q3, v)
        m = float(np.max(np.abs(dq)))
        if m > max_dq:
            dq *= max_dq / m
        return dq
