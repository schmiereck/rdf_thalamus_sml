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

import os

import numpy as np


class LearnedInverseKinematics:
    def __init__(self, hid: int = 128, lr: float = 0.03, rng=None, feat=None, nq: int | None = None) -> None:
        rng = rng or np.random.default_rng(0)
        # GELENKZAHL.  Bis 2026-08-06 war ueberall die 3 fest verdrahtet -- bei ACT14_DOF=4 warf train()
        # sofort einen ValueError, weshalb pc_act23 learn_inverse NIE aufrief und der ganze act23-Lauf
        # auf dem analytischen Jacobi fuhr.  Gemessen kostet der dort einen SYSTEMATISCHEN Hoehenfehler
        # (24 Ziele: +6.5mm Median, +14.8mm Mittel, 100% nach OBEN, p=7.8e-4; groesser nahe der Basis,
        # rho=-0.73 mit dem Radius) -- die Klaue fasst ueber der Objektmitte zu und haelt nicht.
        # M(q) bildet die 3-D Handgeschwindigkeit auf nq Gelenkschritte ab, ist also nq x 3.
        self.nq = int(nq) if nq is not None else (4 if int(os.environ.get("ACT14_DOF", "3")) >= 4 else 3)
        # Joint-angle featurisation for the M(q3) net.  "raw" (default) = normalised angles (byte-identical
        # to before).  "phase" = a CIRCULAR encoding [cos q, sin q] per joint (din 6): the joints span a full
        # [0, pi] and the inverse Jacobian M(q3) is itself trig in the angles, so the cos/sin basis is the
        # natural one -- the analogue of RoPE phase for the kinematics.  Env ACT_IK_FEAT=phase.
        self.feat = (feat if feat is not None else os.environ.get("ACT_IK_FEAT", "raw")).lower()
        self.din = 2 * self.nq if self.feat == "phase" else self.nq
        self.hid = int(hid)
        self.W1 = rng.normal(0, 1 / np.sqrt(self.din), (hid, self.din)); self.b1 = np.zeros(hid)
        self.ndim = 3                                       # Beobachtungsbreite; 6 mit Richtungsterm
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (3 * self.nq, hid))                # -> M(q) nq x ndim
        self.b2 = np.zeros(3 * self.nq)
        self.lr = lr
        self.qmu = np.zeros(self.nq); self.qsd = np.ones(self.nq)
        self.sv = np.ones(3); self.sd = 1.0                # v / dq magnitude scales (M learned on v/sv, dq/sd)
        self.v_max = 0.015
        self.trained = False

    def _resize(self, nq: int, rng=None, ndim: int | None = None) -> None:
        """Gewichte auf andere Gelenk-/Beobachtungsbreite neu aufsetzen (nur beim Aufbau)."""
        rng = rng or np.random.default_rng(0)
        self.nq = int(nq)
        if ndim is not None:
            self.ndim = int(ndim)
        self.din = 2 * self.nq if self.feat == "phase" else self.nq
        self.W1 = rng.normal(0, 1 / np.sqrt(self.din), (self.hid, self.din)); self.b1 = np.zeros(self.hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(self.hid), (self.ndim * self.nq, self.hid))
        self.b2 = np.zeros(self.ndim * self.nq)
        self.qmu = np.zeros(self.nq); self.qsd = np.ones(self.nq)
        self.trained = False

    # ------------------------------------------------------------------
    def _phi(self, Q):                                     # RAW q3 (B,3) -> network input (B,din)
        Q = np.atleast_2d(np.asarray(Q, float))
        if self.feat == "phase":
            return np.concatenate([np.cos(Q), np.sin(Q)], axis=1)   # circular: [cos q0..2, sin q0..2]
        return (Q - self.qmu) / self.qsd                            # raw: normalised angles

    def _M(self, q3):                                      # q3: (B,3) RAW -> (B,3,3), h, phi(B,din)
        phi = self._phi(q3)
        h = np.tanh(phi @ self.W1.T + self.b1)             # (B,hid)
        Mf = h @ self.W2.T + self.b2                       # (B,9)
        return Mf.reshape(-1, self.nq, self.ndim), h, phi

    def train(self, fk, q_lo, q_hi, steps: int = 80000, dq_amp: float = 0.03,
              epochs: int = 10, bs: int = 256, wd: float = 3e-2, rng=None, dir_fk=None) -> float:
        """Babble (q, dq) -> v = fk(q+dq) - fk(q); fit M(q) so M(q)*v ~ dq.  Returns the babble
        reconstruction error (mm of hand displacement through fk).

        dir_fk (optional): liefert die KLAUENRICHTUNG zu q.  Ist sie gegeben, lernt M(q) aus dem
        6-D Fehler [Positions-, Richtungsaenderung] statt nur aus der Position -- noetig, sobald der
        Arm REDUNDANT ist (ACT14_DOF=4).  Gemessen ohne diesen Term: die gelernte IK erreicht zwar
        die Position im Babble (2.1mm), driftet im Einsatz aber in der Orientierung, und weil der
        Reichpunkt am Klauen-Kontakt haengt, wandert er mit -- Reichfehler 78mm gegen 15mm analytisch.
        Genau davor warnt der Kommentar in pc_act14 zu ARM3."""
        rng = rng or np.random.default_rng(1)
        q_lo = np.asarray(q_lo, float); q_hi = np.asarray(q_hi, float)
        if len(q_lo) != self.nq:                            # Gelenkzahl aus dem Bereich NACHZIEHEN, falls
            self._resize(len(q_lo), rng)                    #   der Aufrufer eine andere meint als ACT14_DOF
        Q = rng.uniform(q_lo, q_hi, (steps, self.nq))
        DQ = rng.uniform(-dq_amp, dq_amp, (steps, self.nq))
        self.ndim = 6 if dir_fk is not None else 3          # Beobachtungsbreite (Position [+ Richtung])
        if dir_fk is not None:
            V = np.array([np.concatenate([fk(q + dq) - fk(q), dir_fk(q + dq) - dir_fk(q)])
                          for q, dq in zip(Q, DQ)])
        else:
            V = np.array([fk(q + dq) - fk(q) for q, dq in zip(Q, DQ)])
        if self.W2.shape[0] != self.ndim * self.nq:         # Ausgabebreite an die Beobachtung anpassen
            self._resize(self.nq, rng, ndim=self.ndim)
        self.v_max = float(np.percentile(np.linalg.norm(V[:, :3], axis=1), 95))   # nur Positionsteil
        self.qmu, self.qsd = Q.mean(0), Q.std(0) + 1e-9
        self.sv = np.asarray(V.std(0), float) + 1e-9        # SPALTENWEISE: Positions- und Richtungsanteil
        self.sd = float(DQ.std() + 1e-9)                    #   haben verschiedene Groessenordnungen
        Vn = V / self.sv; DQn = DQ / self.sd               # learn M' so M'·(v/sv) ≈ dq/sd
        n = steps
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; q, v, dq = Q[b], Vn[b], DQn[b]
                M, h, phi = self._M(q)                      # (B,3,3),(B,hid),(B,din)
                pred = np.einsum("bij,bj->bi", M, v)        # (B,3)
                e = (pred - dq) / len(b)                    # (B,3)
                dMf = (e[:, :, None] * v[:, None, :]).reshape(len(b), self.ndim * self.nq)
                # weight decay on the M-producing weights = a LEARNED analogue of DLS damping:
                # it penalises large inverse-Jacobian entries, taming near-singular configurations.
                self.W2 -= self.lr * (dMf.T @ h + wd * self.W2); self.b2 -= self.lr * dMf.sum(0)
                dh = (dMf @ self.W2) * (1 - h ** 2)         # (B,hid)
                self.W1 -= self.lr * (dh.T @ phi + wd * self.W1); self.b1 -= self.lr * dh.sum(0)
        self.trained = True
        chk = rng.integers(0, n, 512)
        rec = [np.linalg.norm(fk(Q[i] + self.predict_dq(Q[i], V[i])) - fk(Q[i]) - V[i][:3])
               for i in chk]        # nur der POSITIONSteil zaehlt als Rekonstruktionsfehler (mm)
        return float(np.mean(rec)) * 1000.0

    def observe(self, q3, v, dq, lr: float = 5e-3, wd: float = 3e-2) -> None:
        """LIFELONG: one online SGD step fitting M(q3)*v ≈ dq from a REAL observed motion
        (v = actual hand displacement, dq = actual joint change).  Adapts the learned inverse
        kinematics to the real arm as it moves — no analytic Jacobian, no babbling."""
        if not self.trained:
            return
        vn = (np.asarray(v, float) / self.sv)[None, :]
        dqn = (np.asarray(dq, float) / self.sd)[None, :]
        M, h, phi = self._M(np.asarray(q3, float)[None, :])  # (1,3,3),(1,hid),(1,din)
        pred = np.einsum("bij,bj->bi", M, vn)               # (1,3)
        e = pred - dqn                                      # (1,3)
        dMf = (e[:, :, None] * vn[:, None, :]).reshape(1, self.ndim * self.nq)
        self.W2 -= lr * (dMf.T @ h + wd * self.W2); self.b2 -= lr * dMf.sum(0)
        dh = (dMf @ self.W2) * (1 - h ** 2)
        self.W1 -= lr * (dh.T @ phi + wd * self.W1); self.b1 -= lr * dh.sum(0)

    # ------------------------------------------------------------------
    def predict_dq(self, q3, v):
        M, _, _ = self._M(np.asarray(q3, float)[None, :])
        return self.sd * (M[0] @ (np.asarray(v, float) / self.sv))   # de-normalise the scales

    def reach_velocity(self, fk, q3, target, gain: float = 2.0, max_dq: float = 0.03,
                       dir_fk=None, dir_ref=None, wdir: float = 0.05):
        """Drop-in for ArmBodyModel3D.reach_velocity, but the inverse is LEARNED (no Jacobian).

        Wurde MIT Richtungsterm trainiert (ndim=6), gehoert die Klauenrichtung in den Fehler: sonst
        laesst der redundante 4-DOF-Arm die Orientierung driften und der Reichpunkt wandert mit."""
        q3 = np.asarray(q3, float)
        v = gain * (np.asarray(target, float) - fk(q3))
        nv = float(np.linalg.norm(v))
        if nv > self.v_max:                                 # stay in the learned local regime
            v = v * (self.v_max / nv)
        if self.ndim == 6:
            if dir_fk is None or dir_ref is None:
                w = np.zeros(3)                             # keine Richtungsvorgabe -> nur Position halten
            else:
                w = wdir * (np.asarray(dir_ref, float) - np.asarray(dir_fk(q3), float))
            v = np.concatenate([v, w])
        dq = self.predict_dq(q3, v)
        m = float(np.max(np.abs(dq)))
        if m > max_dq:
            dq *= max_dq / m
        return dq
