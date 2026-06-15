r"""ObstacleModule — the LEARNED obstacle as a first-class ArmModule for the act21 agent.

Bundles the three learned pieces (all built earlier, here promoted out of the test script so the agent can
plug them in cleanly):
  * PERCEPTION  : ObstacleVisionModule (learned soft-argmax camera -> board pose -> occupancy);
  * WORLD MODEL : ObstacleWorldModel, delta = MLP([RBF(xy), occupancy, u]), LEARNED from physical
                  collisions (the agent crashing into the board) -- it predicts WHERE progress is blocked;
  * PLANNER     : min-cost route over the model's own directional traversability (no hand-coded zone).

For the act21 loop it exposes, per episode, a CARRY ROUTE around the perceived board (object -> goal), and a
`carry_target(hxy)` look-ahead the carry servo/policy follows.  Trained once at startup (collision collection
+ perception), CACHED to disk so later runs start fast.

Ports
  out : occupancy (OCC_N*OCC_N)  perceived board occupancy
"""
from __future__ import annotations

import os
import numpy as np

from pc.chain_obstacle_data import (BoardCtl, collect, occ_map, ORG, SPAN, OCC_N, U_DES)
from .base import ArmModule
from .obstacle_vision import ObstacleVisionModule

G = 13                                                # RBF grid for the world-model position code
S2G = (G - 1) / SPAN
to_grid = lambda p: np.clip((np.asarray(p, float) - ORG) * S2G, 0.0, G - 1)
to_m = lambda g: ORG + np.asarray(g, float) / S2G


def _blob1d(pos, sigma=0.8):
    x = np.arange(G); b = np.exp(-0.5 * ((x - pos) / sigma) ** 2)
    return b / (b.sum() + 1e-9)


def _feat(pos):
    """2D position as a unit-L2 RBF code (outer product of per-axis blobs) -- the representation that let
    the world model learn the spatial gate."""
    bx, by = _blob1d(pos[0]), _blob1d(pos[1])
    f = np.outer(bx, by).ravel()
    return f / (np.linalg.norm(f) + 1e-9)


class ObstacleWorldModel:
    """delta_xy = MLP([RBF(xy), occupancy, u]) * UMAX -- 2 hidden layers + Adam + displacement target."""

    def __init__(self, occ_dim, hid=256, lr=0.002, rng=None):
        rng = rng or np.random.default_rng(0)
        din = G * G + occ_dim + 2
        self.din = din; self.UMAX = U_DES * S2G
        self.W1 = rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (hid, hid)); self.b2 = np.zeros(hid)
        self.W3 = rng.normal(0, 1 / np.sqrt(hid), (2, hid)); self.b3 = np.zeros(2)
        self.lr = lr

    def _x(self, pg, occ, ug):
        return np.concatenate([_feat(pg), np.asarray(occ, float), np.asarray(ug, float) / self.UMAX])

    def fit(self, X, T, epochs, bs=256, rng=None):
        rng = rng or np.random.default_rng(1)
        X = np.asarray(X, float); T = np.asarray(T, float); n = len(X)
        ps = ["W1", "b1", "W2", "b2", "W3", "b3"]
        mom = {p: np.zeros_like(getattr(self, p)) for p in ps}
        vel = {p: np.zeros_like(getattr(self, p)) for p in ps}
        b1a, b2a, eps, t = 0.9, 0.999, 1e-8, 0
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb, tb = X[b], T[b]
                h1 = np.tanh(xb @ self.W1.T + self.b1); h2 = np.tanh(h1 @ self.W2.T + self.b2)
                y = h2 @ self.W3.T + self.b3; e = (y - tb) / len(b)
                g = {"W3": e.T @ h2, "b3": e.sum(0)}
                dh2 = (e @ self.W3) * (1 - h2 ** 2); g["W2"] = dh2.T @ h1; g["b2"] = dh2.sum(0)
                dh1 = (dh2 @ self.W2) * (1 - h1 ** 2); g["W1"] = dh1.T @ xb; g["b1"] = dh1.sum(0)
                t += 1
                for p in ps:
                    mom[p] = b1a * mom[p] + (1 - b1a) * g[p]; vel[p] = b2a * vel[p] + (1 - b2a) * g[p] ** 2
                    setattr(self, p, getattr(self, p) - self.lr * (mom[p] / (1 - b1a ** t)) /
                            (np.sqrt(vel[p] / (1 - b2a ** t)) + eps))

    def delta(self, pg, occ, ug):
        u = np.asarray(ug, float); nrm = np.linalg.norm(u)
        if nrm > self.UMAX:
            u = u / nrm * self.UMAX
        h1 = np.tanh(self.W1 @ self._x(pg, occ, u) + self.b1)
        h2 = np.tanh(self.W2 @ h1 + self.b2)
        return (self.W3 @ h2 + self.b3) * self.UMAX

    def state(self):
        return {k: getattr(self, k) for k in ["W1", "b1", "W2", "b2", "W3", "b3"]}

    def load(self, d):
        for k in ["W1", "b1", "W2", "b2", "W3", "b3"]:
            setattr(self, k, d[k])


def traversability(wm, occ, a_g, b_g):
    u = b_g - a_g; n = float(np.linalg.norm(u))
    if n < 1e-6:
        return 1.0
    g = float(np.linalg.norm(wm.delta(a_g, occ, u / n * wm.UMAX))) / wm.UMAX
    return float(np.clip(g, 0.02, 2.0))


def path_cost(wm, occ, W):
    # 1/traversability^2 -> crossing the LEARNED low-traversability band (the collision the model learned)
    # is prohibitive, so the route bows around the thin wall.  No hand-coded forbidden zone.
    return float(sum(np.linalg.norm(b - a) / traversability(wm, occ, a, b) ** 2
                     for a, b in zip(W[:-1], W[1:])))


def _descend(wm, occ, W, K, iters, lr=0.10, eps=0.15):
    W = W.copy()
    for _ in range(iters):
        g = np.zeros_like(W)
        for i in range(1, K):
            for d in range(2):
                Wp = W.copy(); Wp[i, d] += eps; Wm = W.copy(); Wm[i, d] -= eps
                g[i, d] = (path_cost(wm, occ, Wp) - path_cost(wm, occ, Wm)) / (2 * eps)
        gn = np.linalg.norm(g)
        if gn > 1e-9:
            g = g / gn * min(gn, 2.0)
        W[1:K] -= lr * g[1:K]; W = np.clip(W, 0.0, G - 1.0)
    return W


def _seg_hits_box(a, b, cx, cy, hx, hy):
    """Does the segment a->b intersect the axis-aligned board box (slab clip)?  Fast pre-check so we only
    run the (costly) planner when the straight carry actually crosses the perceived board."""
    a = np.asarray(a, float); d = np.asarray(b, float) - a
    lo = np.array([cx - hx, cy - hy]); hi = np.array([cx + hx, cy + hy])
    t0, t1 = 0.0, 1.0
    for i in range(2):
        if abs(d[i]) < 1e-9:
            if a[i] < lo[i] or a[i] > hi[i]:
                return False
        else:
            ta = (lo[i] - a[i]) / d[i]; tb = (hi[i] - a[i]) / d[i]
            if ta > tb:
                ta, tb = tb, ta
            t0 = max(t0, ta); t1 = min(t1, tb)
            if t0 > t1:
                return False
    return True


def plan_route(wm, occ, start_g, goal_g, K=12, iters=60):
    """Min-cost waypoints (grid coords) around the LEARNED obstacle: multi-start arcs + descent, best kept."""
    straight = np.array([start_g + (goal_g - start_g) * k / K for k in range(K + 1)], float)
    d = goal_g - start_g; perp = np.array([-d[1], d[0]]); perp = perp / (np.linalg.norm(perp) + 1e-9)
    arch = np.sin(np.linspace(0, np.pi, K + 1))
    best, best_c = straight, path_cost(wm, occ, straight)
    for side in (+1.0, -1.0):
        for amp in (3.0, 6.0):
            W = _descend(wm, occ, np.clip(straight + side * amp * arch[:, None] * perp[None, :], 0, G - 1), K, iters)
            c = path_cost(wm, occ, W)
            if c < best_c:
                best, best_c = W, c
    return best


class ObstacleModule(ArmModule):
    def __init__(self, board_tall=0.025, rng=None, name="Obstacle"):
        super().__init__(name)
        self.rng = rng or np.random.default_rng(0)
        self.vision = ObstacleVisionModule(rng=self.rng)
        self.wm: ObstacleWorldModel | None = None
        self.board = None                                  # BoardCtl, set on train
        self.board_tall = float(board_tall)               # LOW board: blocks the carry, the arm clears it
        self.route = None; self._wp = 1; self._occ = None; self._pose = None
        self._wm_err = float("nan")
        self.add_out("occupancy", OCC_N * OCC_N, "perceived board occupancy")

    def train(self, sim, n_collide=11000, wm_epochs=80, vis_steps=2800, vis_iters=450,
              cache=None, quiet=False):
        """World model: from physical collisions (occupancy is height-independent, so collected with a TALL
        board for a strong block and REUSED).  Perception: trained for THIS board height (a low board looks
        different from above).  Cached; the world model is reused, perception retrains only if the height
        changed."""
        self.board = BoardCtl(sim)
        cache = cache or os.path.join(os.path.dirname(__file__), "..", "obstacle_cache.npz")
        self.wm = ObstacleWorldModel(occ_dim=OCC_N * OCC_N, rng=np.random.default_rng(0))
        have_wm = False
        if os.path.exists(cache):
            d = np.load(cache, allow_pickle=True)
            self.wm.load({k: d[f"wm_{k}"] for k in ["W1", "b1", "W2", "b2", "W3", "b3"]})
            self._wm_err = float(d["wm_err"]); have_wm = True
            if ("vis_tall" in d.files and "vis_scene" in d.files
                    and abs(float(d["vis_tall"]) - self.board_tall) < 1e-6 and str(d["vis_scene"]) == "home"):
                self.vision._set(d["vis"])
                if not quiet:
                    print(f"  [obstacle] loaded cached world-model + perception; wm 1-step {self._wm_err:.1f} mm")
                self.board.park(); return
            if not quiet:
                print(f"  [obstacle] loaded cached world-model; retraining perception for board half-height "
                      f"{self.board_tall:.3f} m ...")
        if not have_wm:
            if not quiet:
                print(f"  [obstacle] collecting {n_collide} physical collisions (the agent crashes into boards) ...")
            XY, OCC, U, D = collect(sim, self.board, n_collide, self.rng)
            Pg = np.array([to_grid(p) for p in XY]); Ug = U * S2G; Dg = D * S2G
            X = np.array([self.wm._x(p, o, u) for p, o, u in zip(Pg, OCC, Ug)])
            ntr = int(0.9 * len(X)); self.wm.fit(X[:ntr], Dg[:ntr] / self.wm.UMAX, wm_epochs)
            pr = np.array([self.wm.delta(p, o, u) for p, o, u in zip(Pg[ntr:], OCC[ntr:], Ug[ntr:])]) / S2G
            self._wm_err = float(np.mean(np.linalg.norm(pr - D[ntr:], axis=1)) * 1000)
            if not quiet:
                print(f"  [obstacle] world-model 1-step error {self._wm_err:.1f} mm")
        if not quiet:
            print(f"  [obstacle] training perception (act21 scene, board half-height {self.board_tall:.3f} m) ...")
        self.vision.train(sim, steps=vis_steps, iters=vis_iters, staging="scene",
                          board_tall=self.board_tall, rng=np.random.default_rng(1))
        np.savez(cache, vis=self.vision._get(), vis_tall=self.board_tall, wm_err=self._wm_err,
                 **{f"wm_{k}": v for k, v in self.wm.state().items()})
        self.board.park()
        if not quiet:
            print(f"  [obstacle] cached -> {cache}")

    # -- per-episode interface --
    def place_random(self, obj_xy, goal_xy, hy=0.06, rng=None):
        """Drop the physical board so it blocks the straight object->goal line (between them, perpendicular)."""
        rng = rng or self.rng
        mid = 0.5 * (np.asarray(obj_xy, float) + np.asarray(goal_xy, float))
        cx = float(np.clip(mid[0] + rng.uniform(-0.015, 0.015), -0.10, 0.10))
        self.board.place(cx, float(np.clip(mid[1], 0.11, 0.20)), 0.012, hy)
        return cx

    def perceive_board(self, sim):
        """SEE the board in the CURRENT scene (arm home + cubes, as in run_combined's perceive phase) ->
        occupancy.  Resets the per-episode route (planned lazily on the first carry step, when the goal is
        known)."""
        self._occ = self.vision.perceive_sim(sim); self._pose = self.vision._pose
        self.set_out("occupancy", self._occ)
        self.route = None; self._wp = 1
        return self._occ, self._pose

    def carry_target(self, hxy, goal_xy):
        """Look-ahead waypoint (metres) the carry follows.  Plans the route around the PERCEIVED board on
        the first call (start = where the carry begins, goal = the delivery target), then advances along it."""
        if self._occ is None:
            return None
        h = np.asarray(hxy, float); goal = np.asarray(goal_xy, float)
        if self.route is None:
            # only PLAN if the straight carry would cross the perceived board (else go straight -- fast)
            cx, cy, hy = self._pose
            if _seg_hits_box(h, goal, cx, cy, 0.012 + 0.03, hy + 0.03):
                route_g = plan_route(self.wm, self._occ, to_grid(h), to_grid(goal))
                self.route = np.array([to_m(g) for g in route_g]); self._wp = 1
            else:
                self.route = np.array([h, goal]); self._wp = 1
        if len(self.route) <= 2:
            return self.route[-1]
        while self._wp < len(self.route) - 1:
            d_wp = np.linalg.norm(self.route[self._wp] - h)
            if d_wp < 0.03 or np.linalg.norm(self.route[self._wp + 1] - h) < d_wp:
                self._wp += 1
            else:
                break
        return self.route[self._wp]

    def surprise(self):
        return {"wm_mm": self._wm_err}

    def step(self):
        pass
