"""LatentGoalServo — execute on the LATENT DIFFERENCE (the act6 goal-as-prior idea), on the arm.

Today a dreamed goal LATENT is decoded once to (x,y) and approached open-loop.  This keeps the goal
as a LATENT and CLOSES THE LOOP on it: the place target is driven by the latent error between the
goal latent and the latent of the CURRENTLY PERCEIVED object —

    z_g = encode(goal)            ("image of the object at the goal -> latent")
    e   = z_g - encode(obj_now)   (the deviation to the current state)
    tgt = obj_now + D @ e          (a LEARNED latent-inverse turns the latent error into a step)

Iterated, the object is driven until its latent matches the goal latent (not until it hits a decoded
coordinate).  Because the loop reads the CURRENT object's latent, it converges to the TRUE goal even
when decode_dream has a reconstruction bias — that is the concrete win over open-loop decoding.

Reuses `GoalModule2D` (the learned position-latent embedding).  The latent-inverse `D` is learned by
babbling in the latent (the analogue of the learned inverse kinematics), so the latent difference is
turned into action by a learned map, not a hand-coded one.
"""
from __future__ import annotations

import numpy as np

from .planner import GoalModule2D, G, LO, HI, SPAN, world_to_grid, grid_to_world


class LatentGoalServo:
    def __init__(self, gm: GoalModule2D, rng=None):
        self.gm = gm
        self.rng = rng or np.random.default_rng(0)
        self.z_g = None
        # grid-cached encode (fast, smooth) so the servo/babble need no per-call relax
        self._gx = np.linspace(0, G - 1, 17)
        self._grid_z = np.array([[gm.encode(np.array([x, y])) for x in self._gx] for y in self._gx])
        self.D = None                                       # latent-inverse: dpos (2) = dz @ D
        self.zmu = 0.0; self.zsd = 1.0

    # bilinear latent lookup over the precomputed grid (in grid coords)
    def _z_grid(self, gxy):
        x = np.interp(gxy[0], self._gx, np.arange(len(self._gx)))
        y = np.interp(gxy[1], self._gx, np.arange(len(self._gx)))
        x0, y0 = int(np.floor(x)), int(np.floor(y))
        x1, y1 = min(x0 + 1, len(self._gx) - 1), min(y0 + 1, len(self._gx) - 1)
        fx, fy = x - x0, y - y0
        return ((1 - fx) * (1 - fy) * self._grid_z[y0, x0] + fx * (1 - fy) * self._grid_z[y0, x1]
                + (1 - fx) * fy * self._grid_z[y1, x0] + fx * fy * self._grid_z[y1, x1])

    def encode_world(self, xy):
        return self._z_grid(world_to_grid(xy))

    def train(self, steps=4000, dpos_frac=0.06, rng=None):
        """Babble in the latent: sample pos & a small dpos, fit dpos ~= (z'-z) @ D (least squares).
        Returns the babble reconstruction error (mm)."""
        rng = rng or self.rng
        lo, hi = LO + 0.05 * SPAN, HI - 0.05 * SPAN
        amp = dpos_frac * SPAN
        P = rng.uniform(lo, hi, (steps, 2))
        DP = rng.uniform(-amp, amp, (steps, 2))
        Z = np.array([self.encode_world(p) for p in P])
        Z2 = np.array([self.encode_world(np.clip(p + dp, lo, hi)) for p, dp in zip(P, DP)])
        DZ = Z2 - Z
        self.zsd = float(DZ.std() + 1e-9)
        DZn = DZ / self.zsd
        # least squares dpos ~= DZn @ D   ->  D = (DZn^+ ) DP
        self.D = np.linalg.lstsq(DZn, DP, rcond=None)[0]    # (latent, 2)
        rec = DZn @ self.D - DP
        return float(np.mean(np.linalg.norm(rec, axis=1))) * 1000.0

    def set_goal(self, goal_xy):
        self.z_g = self.encode_world(goal_xy)

    def latent_error(self, obj_xy):
        return float(np.linalg.norm(self.z_g - self.encode_world(obj_xy)))

    def servo(self, obj_xy, gain=1.0):
        """One latent-servo step: turn the latent error into a place target (clipped to reach)."""
        e = (self.z_g - self.encode_world(obj_xy)) / self.zsd
        dpos = gain * (e @ self.D)
        return np.clip(np.asarray(obj_xy, float) + dpos, LO, HI)


# --------------------------------------------------------------------------- #
def main():
    """Standalone: latent-servo convergence + robustness vs open-loop decode under a decode bias."""
    import os
    rng = np.random.default_rng(0)
    gm = GoalModule2D(rng=np.random.default_rng(7)); gm.pretrain(int(os.environ.get("LG_GM_STEPS", "8000")))
    servo = LatentGoalServo(gm, rng=np.random.default_rng(1))
    rec = servo.train(steps=4000)
    print("=" * 72)
    print("  LatentGoalServo — execute on the latent difference (goal-as-prior)")
    print(f"  GoalModule decode error {gm.decode_error():.2f} grid-units;  latent-inverse babble {rec:.1f} mm")
    print("=" * 72)

    lo, hi = LO + 0.1 * SPAN, HI - 0.1 * SPAN
    ls_err, ol_err = [], []
    for _ in range(40):
        goal = rng.uniform(lo, hi); servo.set_goal(goal)
        # open-loop: decode the goal latent once (carries the decode reconstruction bias)
        ol = grid_to_world(gm.decode_dream(servo.z_g))
        ol_err.append(np.linalg.norm(ol - goal) * 1000)
        # latent servo: drive a point from a random start until the latent error stops shrinking
        obj = rng.uniform(lo, hi)
        for _ in range(60):
            obj = servo.servo(obj, gain=0.6)
            if servo.latent_error(obj) < 1e-3:
                break
        ls_err.append(np.linalg.norm(obj - goal) * 1000)
    print(f"  reach the TRUE goal:  open-loop decode  {np.mean(ol_err):5.1f} mm")
    print(f"                        latent servo      {np.mean(ls_err):5.1f} mm")
    print("-" * 72)
    print("  Read: the closed-loop latent servo converges to where the CURRENT object's latent matches")
    print("  the goal latent -> it reaches the true goal, side-stepping decode_dream's reconstruction bias.")
    print("=" * 72)


if __name__ == "__main__":
    main()
