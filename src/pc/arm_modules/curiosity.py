"""CuriosityPlanner — a Planner that dreams goals by INTRINSIC NOVELTY, with NO reward and NO
hand-given rule (the act14-20 port of the 1D Option-2 curiosity planner, `test_pc_planner_curiosity`).

`PlannerModule` learns a HUMAN-set rule (mirror/centre).  This swaps the criterion for an epistemic
one: "go where you haven't been".  Each episode it proposes K candidate goal latents on the
`GoalModule2D` manifold, scores them by NOVELTY (latent distance to already-visited goals), dreams the
most novel one (`decode_dream` -> world xy), and after delivery marks it visited so its novelty drops.

The 1D result: distance/density novelty covers the world ~2x faster than random, with low transport
(dreamed goals stay actionable), entirely without reward.  It is a drop-in alternative to
`PlannerModule` (same out-port `goal_xy`) — the pluggable architecture lets the agent swap its planner.
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule
from .planner import GoalModule2D, G, LO, HI, SPAN, world_to_grid


class DistanceNovelty:
    """Model-free epistemic value: novelty = latent distance to the nearest visited goal."""

    def __init__(self) -> None:
        self.seen: list[np.ndarray] = []

    def score(self, z) -> float:
        if not self.seen:
            return 1.0
        return float(min(np.linalg.norm(z - s) for s in self.seen))

    def visit(self, z) -> None:
        self.seen.append(np.asarray(z, float))

    def reset(self) -> None:
        self.seen = []


class CuriosityPlanner(ArmModule):
    def __init__(self, gm: GoalModule2D, K: int = 24, n_bins: int = 6, rng=None,
                 name: str = "CuriosityPlanner") -> None:
        super().__init__(name)
        self.gm = gm; self.K = K; self.rng = rng or np.random.default_rng(0)
        self.nov = DistanceNovelty()
        self.NB = n_bins
        self.covered = np.zeros((n_bins, n_bins), bool)
        self._last = None                                   # last dream diagnostics (novelty)
        # precomputed latent grid for fast encode (bilinear) — same cache as PlannerModule
        self._gx = np.linspace(0, G - 1, 13)
        self._grid_z = np.array([[gm.encode(np.array([x, y])) for x in self._gx] for y in self._gx])
        self.add_out("goal_xy", 2, "self-dreamed (novelty) place target, world xy")

    # bilinear latent lookup over the precomputed grid (avoids a relax per candidate)
    def _latent(self, goal_grid):
        x = np.interp(goal_grid[0], self._gx, np.arange(len(self._gx)))
        y = np.interp(goal_grid[1], self._gx, np.arange(len(self._gx)))
        x0, y0 = int(np.floor(x)), int(np.floor(y))
        x1, y1 = min(x0 + 1, len(self._gx) - 1), min(y0 + 1, len(self._gx) - 1)
        fx, fy = x - x0, y - y0
        return ((1 - fx) * (1 - fy) * self._grid_z[y0, x0] + fx * (1 - fy) * self._grid_z[y0, x1]
                + (1 - fx) * fy * self._grid_z[y1, x0] + fx * fy * self._grid_z[y1, x1])

    def _bin(self, xy):
        b = np.clip(((np.asarray(xy, float) - LO) / SPAN * self.NB).astype(int), 0, self.NB - 1)
        return int(b[0]), int(b[1])

    def coverage(self) -> float:
        return float(self.covered.mean())

    def dream(self, *_):
        """Propose K reachable goals, dream the MOST NOVEL one (no reward, no rule).

        Novelty is scored on each candidate's LATENT (the agent's learned world model of
        similarity); the goal returned is the selected candidate's position.  We do NOT re-decode
        the latent — decode_dream's reconstruction error would pull goals toward the manifold
        interior and shrink coverage; the latent already drove the choice."""
        cand_w = self.rng.uniform(LO + 0.05 * SPAN, HI - 0.05 * SPAN, (self.K, 2))
        zs = [self._latent(world_to_grid(p)) for p in cand_w]
        scores = [self.nov.score(z) for z in zs]
        i = int(np.argmax(scores))
        self.nov.visit(zs[i])
        goal = cand_w[i]
        self.covered[self._bin(goal)] = True
        self._last = {"novelty": float(scores[i]), "visited": len(self.nov.seen),
                      "coverage": self.coverage()}
        return goal

    def step(self) -> None:
        self.set_out("goal_xy", self.dream())

    def surprise(self) -> dict | None:
        return self._last


# --------------------------------------------------------------------------- #
def main():
    """Isolated 2-D coverage experiment: distance-novelty vs random (no sim, no reward)."""
    import os
    print("=" * 76)
    print("  CuriosityPlanner (2-D) — explore the workspace with NO reward, NO rule")
    gm = GoalModule2D(rng=np.random.default_rng(7))
    gm.pretrain(int(os.environ.get("CUR_GM_STEPS", "8000")))
    print(f"  GoalModule2D decode error: {gm.decode_error():.2f} grid-units of {G}")
    NB = int(os.environ.get("CUR_BINS", "5")); ROUNDS = int(os.environ.get("CUR_ROUNDS", "30"))
    K = int(os.environ.get("CUR_K", "24")); REPEATS = int(os.environ.get("CUR_REPEATS", "8"))
    print(f"  bins={NB}x{NB}  rounds={ROUNDS}  candidates/round={K}  repeats={REPEATS}")
    print("=" * 76)

    def run(use_novelty, seed):
        rng = np.random.default_rng(seed)
        pl = CuriosityPlanner(gm, K=K, n_bins=NB, rng=rng)
        curve = []
        for _ in range(ROUNDS):
            if use_novelty:
                pl.dream()                                  # novelty selection
            else:
                g = rng.uniform(LO + 0.05 * SPAN, HI - 0.05 * SPAN)   # random goal
                pl.covered[pl._bin(g)] = True
            curve.append(pl.coverage())
        return np.array(curve)

    for name, novel in (("random   ", False), ("distance ", True)):
        curves = np.array([run(novel, 100 + r) for r in range(REPEATS)])
        c = curves.mean(0)
        full = [int(np.argmax(cv >= 0.999)) + 1 if cv.max() >= 0.999 else ROUNDS + 1 for cv in curves]
        print(f"  {name}: cov@5={c[4]:.2f} cov@10={c[9]:.2f} cov@15={c[14]:.2f}  rounds->full={np.mean(full):4.1f}")
    print("-" * 76)
    print("  Read: distance-novelty covers the workspace faster than random, with NO reward —")
    print("  the planner finds its own goals.  (Port of the 1D Option-2 curiosity result to 2-D.)")
    print("=" * 76)


if __name__ == "__main__":
    main()
