r"""test_pc_chain_arm_obstacle.py — obstacle-aware world model LEARNED FROM PHYSICAL COLLISIONS.

Increment 1 of "the agent learns the board by crashing into it" (visual perception = increment 2):

  * the agent does a physics random-walk in the front working area with a STATIC board placed at random;
    where a move drives the gripper into the board it is physically BLOCKED (achieved displacement ~0)
    -- a collision (chain_obstacle_data.collect);
  * an OBSTACLE-CONDITIONED world model  Δxy = f(RBF(xy), occupancy_map, u)  is fit on these transitions
    (the proven recipe from the 2D PoC: 2 hidden layers + Adam + displacement target).  It LEARNS that
    progress is blocked where the occupancy map says board AND the move points into it -- NOT a hand-coded
    forbidden zone;
  * the min-time planner routes the transport around the LEARNED speed dip -- on a NEW random board the
    model never trained on that exact placement.

Honest framing (the user's intent): this is meant to be an EXTENSIBLE architecture, not a 100% sandbox
solution.  The board is encoded as a TRUE occupancy map here; replacing that with a LEARNED camera->occupancy
perception is increment 2 (visual recognition).  The occupancy is the clean interface between the two.

Env: OBS_N (transitions)  OBS_EPOCHS  OBS_SEED (test board)  OBS_NOVIZ
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import BracketArmSim
import pc.test_pc_chain_constrained_2d as ch
from pc.chain_obstacle_data import (BoardCtl, collect, occ_map, ORG, SPAN, OCC_N, U_DES, WX, WY)

G = ch.G
S2G = (G - 1) / SPAN
to_grid = lambda p: np.clip((np.asarray(p, float) - ORG) * S2G, 0.0, G - 1)
to_m = lambda g: ORG + np.asarray(g, float) / S2G


class ObstacleWorldModel:
    """Δxy = MLP([RBF(xy), occupancy, u]) * UMAX.  Two hidden layers + Adam (the recipe that learned the
    spatial gate in 2D).  The occupancy channel lets the SAME model express 'blocked where the board is'."""

    def __init__(self, occ_dim, hid=256, lr=0.002, rng=None):
        rng = rng or np.random.default_rng(0)
        din = G * G + occ_dim + 2
        self.din = din; self.UMAX = U_DES * S2G
        self.W1 = rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (hid, hid)); self.b2 = np.zeros(hid)
        self.W3 = rng.normal(0, 1 / np.sqrt(hid), (2, hid)); self.b3 = np.zeros(2)
        self.lr = lr

    def _x(self, pos_grid, occ, u_grid):
        return np.concatenate([ch.feat(pos_grid), np.asarray(occ, float), np.asarray(u_grid, float) / self.UMAX])

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
                h1 = np.tanh(xb @ self.W1.T + self.b1)
                h2 = np.tanh(h1 @ self.W2.T + self.b2)
                y = h2 @ self.W3.T + self.b3
                e = (y - tb) / len(b)
                g = {"W3": e.T @ h2, "b3": e.sum(0)}
                dh2 = (e @ self.W3) * (1 - h2 ** 2); g["W2"] = dh2.T @ h1; g["b2"] = dh2.sum(0)
                dh1 = (dh2 @ self.W2) * (1 - h1 ** 2); g["W1"] = dh1.T @ xb; g["b1"] = dh1.sum(0)
                t += 1
                for p in ps:
                    mom[p] = b1a * mom[p] + (1 - b1a) * g[p]; vel[p] = b2a * vel[p] + (1 - b2a) * g[p] ** 2
                    setattr(self, p, getattr(self, p) - self.lr * (mom[p] / (1 - b1a ** t)) /
                            (np.sqrt(vel[p] / (1 - b2a ** t)) + eps))

    def delta(self, pos_grid, occ, u_grid):
        u = np.asarray(u_grid, float); nrm = np.linalg.norm(u)
        if nrm > self.UMAX:
            u = u / nrm * self.UMAX
        h1 = np.tanh(self.W1 @ self._x(pos_grid, occ, u) + self.b1)
        h2 = np.tanh(self.W2 @ h1 + self.b2)
        return (self.W3 @ h2 + self.b3) * self.UMAX

    def speed(self, pos_grid, occ, ndir=8):
        return float(np.mean([np.linalg.norm(self.delta(
            pos_grid, occ, self.UMAX * np.array([np.cos(a), np.sin(a)])))
            for a in np.linspace(0, 2 * np.pi, ndir, endpoint=False)]))


def traversability(wm, occ, a_g, b_g):
    """How far the LEARNED model says you actually get moving from a toward b (per unit desired): ~1 free,
    ~0 blocked (the segment crosses the board the model learned to crash into).  Directional -- this is the
    signal the direction-AVERAGED speed field washes out for a thin wall."""
    u = b_g - a_g; n = float(np.linalg.norm(u))
    if n < 1e-6:
        return 1.0
    g = float(np.linalg.norm(wm.delta(a_g, occ, u / n * wm.UMAX))) / wm.UMAX
    return float(np.clip(g, 0.02, 2.0))


def path_cost(wm, occ, W):
    # 1/traversability^2: the collision the model learned is a thin barrier, so a single short segment
    # crossing it would otherwise incur only moderate cost; squaring makes crossing the LEARNED low-
    # traversability band prohibitive (a risk-averse cost over the model's own prediction, still no
    # hand-coded forbidden zone).
    return float(sum(np.linalg.norm(b - a) / traversability(wm, occ, a, b) ** 2
                     for a, b in zip(W[:-1], W[1:])))


def _descend_model(wm, occ, W, K, iters, lr=0.10, eps=0.15):
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


def plan_around(wm, occ, start_g, goal_g, K=18, iters=170):
    """Min-cost waypoints through the LEARNED directional traversability (multi-start arcs + descent)."""
    straight = np.array([start_g + (goal_g - start_g) * k / K for k in range(K + 1)], float)
    d = goal_g - start_g; perp = np.array([-d[1], d[0]]); perp = perp / (np.linalg.norm(perp) + 1e-9)
    arch = np.sin(np.linspace(0, np.pi, K + 1))
    best, best_c = None, np.inf
    for side in (+1.0, -1.0):
        for amp in (2.0, 4.0, 6.0, 8.0):
            W0 = np.clip(straight + side * amp * arch[:, None] * perp[None, :], 0.0, G - 1.0)
            W = _descend_model(wm, occ, W0, K, iters)
            c = path_cost(wm, occ, W)
            if c < best_c:
                best, best_c = W, c
    return best


def main():
    rng = np.random.default_rng(0)
    N = int(os.environ.get("OBS_N", "9000"))
    EPOCHS = int(os.environ.get("OBS_EPOCHS", "80"))
    SEED = int(os.environ.get("OBS_SEED", "4"))
    print("=" * 86)
    print("  OBSTACLE-AWARE world model LEARNED FROM PHYSICAL COLLISIONS (true occupancy; vision = next)")
    sim = BracketArmSim(render_wh=(120, 120)); sim.set_reach_site("contact")
    board = BoardCtl(sim)
    print(f"  collecting {N} physics transitions (the agent crashes into random boards) ...")
    XY, OCC, U, D = collect(sim, board, N, rng)
    blocked = (np.linalg.norm(D, 1) / (np.linalg.norm(U, axis=1) + 1e-9))
    print(f"  collected; blocked fraction {(np.linalg.norm(D,axis=1)/(np.linalg.norm(U,axis=1)+1e-9) < 0.35).mean():.2f}")

    # --- fit the obstacle-conditioned world model on the collisions ---
    wm = ObstacleWorldModel(occ_dim=OCC.shape[1], rng=np.random.default_rng(0))
    Pg = np.array([to_grid(p) for p in XY]); Ug = U * S2G; Dg = D * S2G
    X = np.array([wm._x(p, o, u) for p, o, u in zip(Pg, OCC, Ug)])
    T = Dg / wm.UMAX
    ntr = int(0.9 * len(X)); wm.fit(X[:ntr], T[:ntr], EPOCHS)
    pred = np.array([wm.delta(p, o, u) for p, o, u in zip(Pg[ntr:], OCC[ntr:], Ug[ntr:])]) / S2G
    print(f"  held-out 1-step error: {np.mean(np.linalg.norm(pred - D[ntr:], axis=1))*1000:.1f} mm")

    # --- the test board.  Its occupancy is either TRUE or PERCEIVED from the camera (the visual
    #     recognition, increment 2): a LEARNED soft-argmax detector reads the board pose from the top view. ---
    brng = np.random.default_rng(SEED)
    bcx, bcy, bhy = brng.uniform(-0.07, 0.07), brng.uniform(0.12, 0.18), brng.uniform(0.045, 0.065)
    perr = None; pcx, pcy, phy = bcx, bcy, bhy
    if os.environ.get("OBS_PERCEIVE", "1") == "1":
        from pc.arm_modules.obstacle_vision import ObstacleVisionModule
        import mujoco
        print("  training the LEARNED camera->board perception (soft-argmax detector) ...")
        vis = ObstacleVisionModule(rng=np.random.default_rng(0))
        vis.train(sim, steps=int(os.environ.get("OBS_VIS_STEPS", "3000")),
                  iters=int(os.environ.get("OBS_VIS_ITERS", "500")))
        vis.stage(sim); board.place(bcx, bcy, 0.012, bhy); mujoco.mj_forward(sim.m, sim.d)
        occ = vis.perceive_sim(sim); pcx, pcy, phy = vis._pose
        perr = float(np.linalg.norm([pcx - bcx, pcy - bcy]) * 1000)
        print(f"  PERCEIVED board pose: ({pcx:+.3f},{pcy:.3f}) vs true ({bcx:+.3f},{bcy:.3f})  -> error {perr:.1f} mm")
    else:
        occ = occ_map(bcx, 0.012, bhy, bcy)
    occ0 = np.zeros_like(occ)
    left = np.array([bcx - 0.05, bcy])                       # just left of the board, push RIGHT into it
    gl = to_grid(left); uin = np.array([U_DES, 0]) * S2G; uaway = np.array([0, U_DES]) * S2G
    din = np.linalg.norm(wm.delta(gl, occ, uin)) / S2G * 1000
    daway = np.linalg.norm(wm.delta(gl, occ, uaway)) / S2G * 1000
    dfree = np.linalg.norm(wm.delta(gl, occ0, uin)) / S2G * 1000
    print("=" * 86)
    print(f"  test board x={bcx:+.3f} y={bcy:.3f} half-y={bhy:.3f}")
    print(f"  at the board face, pushing INTO the board: {din:.1f} mm  vs AWAY: {daway:.1f} mm  "
          f"vs INTO with NO board perceived: {dfree:.1f} mm")
    print("    (learned collision => INTO < AWAY, and INTO < INTO-no-board: the perceived board blocks it)")

    # --- speed field for the perceived board; plan around the LEARNED dip (no hand-coded forbidden zone) ---
    res = 40; gx = np.linspace(0, G - 1, res); cell = SPAN / (res - 1); Pgrid_xy = Pg
    reach = np.zeros((res, res), bool); Sfree = np.full((res, res), np.nan); Sobs = np.full((res, res), np.nan)
    for iy, yy in enumerate(gx):
        for ix, xx in enumerate(gx):
            if ((Pgrid_xy[:, 0] - xx) ** 2 + (Pgrid_xy[:, 1] - yy) ** 2).min() < (1.7 * cell * S2G) ** 2:
                reach[iy, ix] = True
                Sfree[iy, ix] = wm.speed((xx, yy), occ0) / S2G
                Sobs[iy, ix] = wm.speed((xx, yy), occ) / S2G
    Sp = np.where(reach, np.nan_to_num(Sobs, nan=1e-4), 1e-4); Sp = np.where(Sp > 1e-4, Sp, 1e-4)

    start_m = np.array([bcx - 0.13, bcy]); goal_m = np.array([bcx + 0.13, bcy])
    K = 18
    planned_m = np.array([to_m(g) for g in plan_around(wm, occ, to_grid(start_m), to_grid(goal_m), K=K)])
    straight_m = np.array([start_m + (goal_m - start_m) * k / K for k in range(K + 1)])

    def board_pen(pts, ns=40):
        m = 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            for k in range(ns):
                p = a + (b - a) * (k + 0.5) / ns
                dx = 0.012 - abs(p[0] - bcx); dy = bhy - abs(p[1] - bcy)
                if dx > 0 and dy > 0:
                    m = max(m, min(dx, dy))
        return m * 1000

    print("-" * 86)
    print(f"  straight (naive): penetrates the TRUE board by {board_pen(straight_m):.0f} mm  -> INFEASIBLE")
    pp = board_pen(planned_m)
    print(f"  planned  (chain): TRUE-board penetration {pp:.0f} mm  "
          f"({'CLEARS' if pp < 4 else 'still clips'} -- routes via the LEARNED directional traversability)")
    if perr is not None:
        print(f"  full chain: SEE the board ({perr:.0f} mm pose error) -> learned world model -> route around"
              " it; the agent")
        print("  never told where the board is -- it LEARNED impassability from crashing and PERCEIVED the")
        print("  board from the camera.  Nothing hand-coded: collision-learned dynamics + soft-argmax detector.")
    else:
        print("  Read: obstacle LEARNED from physical collisions; planner routes around the model's OWN dip,")
        print("  not a hand-coded forbidden zone.  (Set OBS_PERCEIVE=1 for the learned camera perception.)")
    print("=" * 86)

    if os.environ.get("OBS_NOVIZ", "0") != "1":
        try:
            _plot(Sfree, Sobs, reach, bcx, bcy, bhy, (pcx, pcy, phy) if perr is not None else None,
                  start_m, goal_m, straight_m, planned_m,
                  os.path.join(os.path.dirname(__file__), "chain_arm_obstacle.png"))
        except Exception as e:
            print(f"  [viz] could not save the plot: {e}")


def _plot(Sfree, Sobs, reach, bcx, bcy, bhy, perceived, start_m, goal_m, straight_m, planned_m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    ext = (ORG[0], ORG[0] + SPAN, ORG[1], ORG[1] + SPAN)
    cmap = plt.cm.magma.copy(); cmap.set_bad("#0e0e12")
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    fig.patch.set_facecolor("#0e0e12")
    vmax = np.nanmax(Sfree) * 1000
    for ax, Sm, ttl in ((axes[0], Sfree, "no board perceived (free field)"),
                        (axes[1], Sobs, "board perceived -> LEARNED speed dip + plan")):
        ax.set_facecolor("#0e0e12")
        im = ax.imshow(np.ma.masked_where(~reach, Sm) * 1000, origin="lower", extent=ext, cmap=cmap,
                       aspect="equal", vmin=0, vmax=vmax)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.ax.yaxis.set_tick_params(color="w")
        plt.setp(cb.ax.get_yticklabels(), color="w"); cb.set_label("learned speed (mm/step)", color="w")
        ax.add_patch(Rectangle((bcx - 0.012, bcy - bhy), 0.024, 2 * bhy, facecolor="none",
                               edgecolor="#66ddff", lw=1.6, ls="--"))
        ax.set_title(ttl, color="w", fontsize=10); ax.tick_params(colors="w")
        [sp.set_color("#555") for sp in ax.spines.values()]
        ax.set_xlabel("table x (m)", color="w")
    axes[0].set_ylabel("table y (m)", color="w")
    axes[1].add_patch(Rectangle((bcx - 0.012, bcy - bhy), 0.024, 2 * bhy, facecolor="#ff3344",
                                edgecolor="#ff8899", alpha=0.6, zorder=4, label="true board"))
    if perceived is not None:
        pcx, pcy, phy = perceived
        axes[1].add_patch(Rectangle((pcx - 0.012, pcy - phy), 0.024, 2 * phy, facecolor="none",
                                    edgecolor="#33ccff", lw=1.8, ls="--", zorder=5, label="PERCEIVED board"))
    axes[1].plot(straight_m[:, 0], straight_m[:, 1], "--", color="#ff5566", lw=1.4, label="straight (collides)")
    axes[1].plot(planned_m[:, 0], planned_m[:, 1], "o-", color="#66ff88", lw=1.8, ms=4, label="planned (around)")
    axes[1].scatter([start_m[0]], [start_m[1]], c="#fff", s=70, marker="s", zorder=6)
    axes[1].scatter([goal_m[0]], [goal_m[1]], c="#ffdd33", s=110, marker="*", zorder=6)
    axes[1].legend(facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=8, loc="upper left")
    ttl2 = "perceived board -> LEARNED speed dip + plan" if perceived is not None else \
           "board perceived -> LEARNED speed dip + plan"
    axes[1].set_title(ttl2, color="w", fontsize=10)
    fig.suptitle("SEE the board (learned detector) -> world model learned from collisions -> route around",
                 color="w")
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(path, dpi=120, facecolor=fig.get_facecolor())
    print(f"  [viz] plot saved -> {path}")


if __name__ == "__main__":
    main()
