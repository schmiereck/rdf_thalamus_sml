r"""test_pc_chain_arm.py — the constrained chain on the ARM's reachable plane, with a SHARP obstacle and
LIVE execution.

Two layers of constraint, both real:
  * the arm's LEARNED kinematic speed field (slow near the base-yaw singularity, fast in the periphery),
    fit from the agent's own babbling with the 2D-PoC model (2 hidden layers + Adam + RBF features +
    displacement target);
  * a SHARP obstacle -- a physical "board" (a thin tall wall, a repurposed cube) dropped at a RANDOM place
    per episode so its footprint blocks the straight transport.  The board is given to the planner as a
    forbidden zone (speed -> 0); VISUAL recognition of the board is deferred (a separate later step).

The min-time planner (multi-start arcs + normalized-step descent over the speed field, with the board
zeroed out) routes the transport AROUND the board through the fast region.  With ARMCH_EXEC=1 the planned
route is then EXECUTED on the MuJoCo arm via the learned inverse-kinematics servo, in a LIVE two-panel
view: a top-down speed-field map with the moving hand, and the MuJoCo overhead camera (the real arm + the
board).  Honest: it is the HAND/end-effector that traverses the route (kinematic servo, no dynamics);
grasp-and-carry of a separate object is a later coupling.

Env: ARMCH_BABBLE NACT EPOCHS Z0 BAND  |  ARMCH_EXEC (live)  ARMCH_SEED (board)  ARMCH_NOVIZ
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import BracketArmSim
from pc.arm_modules import BodyModelModule
import pc.test_pc_chain_constrained_2d as ch          # reuse Forward2D / planner / speed-field machinery

G = ch.G
U_DES = 0.009                                         # max desired Cartesian step (m); > the local speed cap
MAX_DQ = 0.03                                         # the joint-step cap that creates the speed field


# ----------------------------------------------------------------------------- arm kinematics helpers
def gather_plane(bm, sim, z0, band, n_uniform, rng):
    rng3 = sim.arm3_range()
    Q = rng.uniform(rng3[:, 0], rng3[:, 1], (n_uniform, 3))
    H = np.array([bm.fk(q) for q in Q])
    m = np.abs(H[:, 2] - z0) < band
    return Q[m], H[m]


def achieved(bm, q, xy, u):
    """REAL achieved in-plane displacement for a desired step u: learned IK -> joint step CAPPED to max_dq
    (the cap that makes the base slow) -> learned FK gives the resulting hand displacement."""
    v = np.array([u[0], u[1], 0.0])
    dq = bm.ik.predict_dq(q, v)
    mm = float(np.max(np.abs(dq)))
    if mm > MAX_DQ:
        dq = dq * MAX_DQ / mm
    return (bm.fk(q + dq)[:2] - xy)


def true_speed(bm, q, xy, ndir=8):
    mags = [np.linalg.norm(achieved(bm, q, xy, U_DES * np.array([np.cos(a), np.sin(a)])))
            for a in np.linspace(0, 2 * np.pi, ndir, endpoint=False)]
    return float(np.mean(mags))


# ----------------------------------------------------------------------------- the obstacle (a "board")
class Board:
    """A thin tall wall on the table, axis-aligned (thin in x, long in y).  `blocks` is the planner's
    forbidden zone (footprint + a hand-clearance margin); `pen` is the actual penetration of a point into
    the real footprint (0 = clear), used to check the executed motion stays out."""

    def __init__(self, cx, hy, hx=0.012, tall=0.06, margin=0.045):
        self.cx = float(cx); self.hy = float(hy); self.hx = float(hx); self.tall = float(tall)
        self.margin = float(margin)

    def blocks(self, xy):
        return abs(xy[0] - self.cx) <= self.hx + self.margin and abs(xy[1]) <= self.hy + self.margin

    def pen(self, xy):
        dx = self.hx - abs(xy[0] - self.cx); dy = self.hy - abs(xy[1])
        return float(min(dx, dy)) if (dx > 0 and dy > 0) else 0.0

    def place_in_sim(self, sim):
        sim.set_object("obj_red", [0.0, -0.45]); sim.set_object("obj_green", [0.0, -0.50])   # out of the way
        sim.set_object_size("obj_blue", [self.hx, self.hy, self.tall])
        sim.set_object("obj_blue", [self.cx, 0.0], z=self.tall)


def plan_around(gx, Sp, start_g, goal_g, K=18, iters=240):
    """Min-time waypoints over the (obstacle-zeroed) speed field.  Multi-start sine arcs of GROWING
    amplitude break the symmetry AND give enough clearance to clear the board; keep the best feasible."""
    straight = np.array([start_g + (goal_g - start_g) * k / K for k in range(K + 1)], float)
    d = goal_g - start_g; perp = np.array([-d[1], d[0]]); perp = perp / (np.linalg.norm(perp) + 1e-9)
    arch = np.sin(np.linspace(0, np.pi, K + 1))
    best, best_t = None, np.inf
    for side in (+1.0, -1.0):
        for amp in (2.0, 4.0, 6.0, 8.0):
            W0 = np.clip(straight + side * amp * arch[:, None] * perp[None, :], 0.0, G - 1.0)
            W = ch._descend(gx, Sp, W0, K, iters)
            t = ch.path_time(gx, Sp, W)
            if t < best_t:
                best, best_t = W, t
    return best


# ----------------------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(0)
    BABBLE = int(os.environ.get("ARMCH_BABBLE", "6000"))
    NACT = int(os.environ.get("ARMCH_NACT", "5"))
    EPOCHS = int(os.environ.get("ARMCH_EPOCHS", "60"))
    Z0 = float(os.environ.get("ARMCH_Z0", "0.04"))
    BAND = float(os.environ.get("ARMCH_BAND", "0.05"))
    EXEC = os.environ.get("ARMCH_EXEC", "0") == "1"
    SEED = int(os.environ.get("ARMCH_SEED", "7"))

    print("=" * 84)
    print("  CONSTRAINED chain on the ARM plane: LEARNED speed field + a SHARP random board obstacle")
    sim = BracketArmSim(render_wh=(360, 360)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, BABBLE)
    print(f"  learned inverse kinematics: babble {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    Q, H = gather_plane(bm, sim, Z0, BAND, 30000, rng); XY = H[:, :2]
    org = XY.min(0); span = float((XY.max(0) - org).max()); s = (G - 1) / span
    to_grid = lambda p: (np.asarray(p, float) - org) * s
    to_m = lambda g: org + np.asarray(g, float) / s
    ch.UMAX = U_DES * s

    # train the learned speed-field model on babbled (xy, desired-step -> achieved displacement)
    P, Ug, Tg = [], [], []
    for q, xy in zip(Q, XY):
        for _ in range(NACT):
            a = rng.uniform(0, 2 * np.pi); mag = rng.uniform(0, U_DES)
            u = mag * np.array([np.cos(a), np.sin(a)])
            P.append(to_grid(xy)); Ug.append(u * s); Tg.append(achieved(bm, q, xy, u) * s)
    P, Ug, Tg = np.array(P), np.array(Ug), np.array(Tg)
    fm = ch.Forward2D(rng=np.random.default_rng(0))
    fm.fit_arrays(np.array([fm._x(p, u) for p, u in zip(P, Ug)]), Tg / ch.UMAX, EPOCHS)

    # learned speed field on a fine grid, masked to the reachable plane
    res = 46; gx = np.linspace(0, G - 1, res); cell = span / (res - 1); XYg = to_grid(XY)
    S = np.full((res, res), np.nan); reach = np.zeros((res, res), bool)
    for iy, yy in enumerate(gx):
        for ix, xx in enumerate(gx):
            if ((XYg[:, 0] - xx) ** 2 + (XYg[:, 1] - yy) ** 2).min() < (1.6 * cell * s) ** 2:
                reach[iy, ix] = True; S[iy, ix] = fm.speed((xx, yy)) / s
    Sp = np.where(reach, np.nan_to_num(S, nan=1e-4), 1e-4); Sp = np.where(Sp > 1e-4, Sp, 1e-4)

    # --- drop a RANDOM board so its footprint blocks the straight transport, zero it in the field ---
    brng = np.random.default_rng(SEED)
    board = Board(cx=brng.uniform(-0.04, 0.04), hy=brng.uniform(0.05, 0.08))
    Sp_obs = Sp.copy()
    for iy, yy in enumerate(gx):
        for ix, xx in enumerate(gx):
            if board.blocks(to_m((xx, yy))):
                Sp_obs[iy, ix] = 1e-4
    print(f"  board: x={board.cx:+.3f} half-y={board.hy:.3f}  (footprint blocks the straight line y=0)")

    start_m = np.array([XY[:, 0].min() * 0.85, 0.0]); goal_m = np.array([XY[:, 0].max() * 0.85, 0.0])
    K = 18
    planned_m = np.array([to_m(g) for g in plan_around(gx, Sp_obs, to_grid(start_m), to_grid(goal_m), K=K)])
    straight_m = np.array([start_m + (goal_m - start_m) * k / K for k in range(K + 1)])

    def nearest_q(xy):
        return Q[np.argmin(((XY - xy) ** 2).sum(1))]

    def true_time(pts, ns=12):
        t = 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            for k in range(ns):
                p = a + (b - a) * (k + 0.5) / ns
                t += (np.linalg.norm(b - a) / ns) / max(true_speed(bm, nearest_q(p), p), 1e-4)
        return t

    def hits_board(pts, ns=40):
        return max(board.pen(a + (b - a) * (k + 0.5) / ns)
                   for a, b in zip(pts[:-1], pts[1:]) for k in range(ns))

    print("=" * 84)
    print(f"  learned speed (mm/step): centre {fm.speed(to_grid([0,0]))/s*1000:.2f}  "
          f"periphery {fm.speed(to_grid([0.22,0]))/s*1000:.2f}")
    sp_pen = hits_board(straight_m) * 1000; pl_pen = hits_board(planned_m) * 1000
    print(f"  straight (naive) : crosses the board by {sp_pen:.0f} mm  -> INFEASIBLE   TRUE-time {true_time(straight_m):.1f}")
    print(f"  planned  (chain) : board clearance {'OK' if pl_pen < 1 else f'PEN {pl_pen:.0f}mm'} "
          f"(max pen {pl_pen:.0f} mm)         TRUE-time {true_time(planned_m):.1f}")
    print("-" * 84)
    print("  Read: the planner routes the transport AROUND the random board (a SHARP forbidden zone) AND")
    print("  through the fast region of the LEARNED kinematic speed field; the straight line is infeasible")
    print("  (it ploughs through the board).  The board is given to the planner (visual recognition deferred).")
    print("=" * 84)

    if EXEC:
        execute_live(sim, bm, Q, XY, Z0, board, S, reach, org, span, s, start_m, goal_m, straight_m,
                     planned_m, nearest_q)
    elif os.environ.get("ARMCH_NOVIZ", "0") != "1":
        try:
            _plot_static(S, reach, org, span, board, start_m, goal_m, straight_m, planned_m,
                         os.path.join(os.path.dirname(__file__), "chain_arm_board.png"))
        except Exception as e:
            print(f"  [viz] could not save the plot: {e}")


# ----------------------------------------------------------------------------- live execution
def execute_live(sim, bm, Q, XY, z0, board, S, reach, org, span, s, start_m, goal_m, straight_m,
                 planned_m, nearest_q, tol=0.012, max_steps=700):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.ion()
    ext = (org[0], org[0] + span, org[1], org[1] + span)
    Sm = np.ma.masked_where(~reach, S) * 1000.0
    cmap = plt.cm.magma.copy(); cmap.set_bad("#0e0e12")

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.4, 6.2))
    fig.patch.set_facecolor("#0e0e12")
    axL.set_facecolor("#0e0e12")
    im = axL.imshow(Sm, origin="lower", extent=ext, cmap=cmap, aspect="equal")
    cb = fig.colorbar(im, ax=axL, fraction=0.046, pad=0.04); cb.set_label("learned hand speed (mm/step)", color="w")
    cb.ax.yaxis.set_tick_params(color="w"); plt.setp(cb.ax.get_yticklabels(), color="w")
    axL.add_patch(Rectangle((board.cx - board.hx, -board.hy), 2 * board.hx, 2 * board.hy,
                            facecolor="#ff3344", edgecolor="#ff8899", alpha=0.85, zorder=4, label="board"))
    axL.plot(straight_m[:, 0], straight_m[:, 1], "--", color="#ff5566", lw=1.3, alpha=0.7, label="straight (collides)")
    axL.plot(planned_m[:, 0], planned_m[:, 1], "o-", color="#66ff88", lw=1.6, ms=3, label="planned route")
    axL.scatter([start_m[0]], [start_m[1]], c="#fff", s=70, marker="s", zorder=6)
    axL.scatter([goal_m[0]], [goal_m[1]], c="#ffdd33", s=110, marker="*", zorder=6)
    trail_ln, = axL.plot([], [], "-", color="#33ccff", lw=2.0, zorder=7)
    hand_pt, = axL.plot([], [], "o", color="#ffffff", ms=9, zorder=8)
    axL.set_xlabel("table x (m)", color="w"); axL.set_ylabel("table y (m)", color="w")
    axL.set_title("top-down: learned speed field + executed route", color="w", fontsize=10)
    axL.tick_params(colors="w"); [sp.set_color("#555") for sp in axL.spines.values()]
    axL.legend(facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=8, loc="upper left")

    board.place_in_sim(sim)
    sim.fk_truth(nearest_q(start_m))
    rimg = axR.imshow(sim.render("overview")); axR.axis("off")
    axR.set_title("MuJoCo overhead: the real arm + the board", color="w", fontsize=10)

    q = nearest_q(start_m).astype(float).copy(); rng3 = sim.arm3_range()
    path = planned_m; wp = 1; trail = []; steps = 0; maxpen = 0.0
    while wp < len(path) and steps < max_steps:
        target = np.array([path[wp][0], path[wp][1], z0])
        dq = bm.reach_velocity(q, target)
        q = np.clip(q + dq, rng3[:, 0], rng3[:, 1])
        hand = bm.fk(q); steps += 1
        maxpen = max(maxpen, board.pen(hand[:2])); trail.append(hand[:2].copy())
        if np.linalg.norm(hand[:2] - path[wp][:2]) < tol:
            wp += 1
        if steps % 3 == 0 or wp >= len(path):
            tr = np.array(trail)
            trail_ln.set_data(tr[:, 0], tr[:, 1]); hand_pt.set_data([hand[0]], [hand[1]])
            sim.fk_truth(q); rimg.set_data(sim.render("overview"))
            axR.set_title(f"MuJoCo overhead  (step {steps}, waypoint {wp}/{len(path)-1})", color="w", fontsize=10)
            plt.pause(0.001)
    print(f"  [exec] reached waypoint {wp}/{len(path)-1} in {steps} servo steps; "
          f"max board penetration {maxpen*1000:.1f} mm "
          f"({'STAYED CLEAR' if maxpen*1000 < 2 else 'CLIPPED'})")
    out = os.path.join(os.path.dirname(__file__), "chain_arm_board_exec.png")
    fig.tight_layout(); fig.savefig(out, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] final frame saved -> {out}")
    plt.ioff(); plt.show()


def _plot_static(S, reach, org, span, board, start_m, goal_m, straight_m, planned_m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    ext = (org[0], org[0] + span, org[1], org[1] + span)
    Sm = np.ma.masked_where(~reach, S) * 1000.0
    cmap = plt.cm.magma.copy(); cmap.set_bad("#0e0e12")
    fig, ax = plt.subplots(figsize=(7.2, 6.6))
    fig.patch.set_facecolor("#0e0e12"); ax.set_facecolor("#0e0e12")
    im = ax.imshow(Sm, origin="lower", extent=ext, cmap=cmap, aspect="equal")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.set_label("learned hand speed (mm / step)", color="w")
    cb.ax.yaxis.set_tick_params(color="w"); plt.setp(cb.ax.get_yticklabels(), color="w")
    ax.add_patch(Rectangle((board.cx - board.hx, -board.hy), 2 * board.hx, 2 * board.hy,
                           facecolor="#ff3344", edgecolor="#ff8899", alpha=0.85, zorder=4, label="board (forbidden)"))
    ax.plot(straight_m[:, 0], straight_m[:, 1], "--", color="#ff5566", lw=1.4, label="naive straight (collides)")
    ax.plot(planned_m[:, 0], planned_m[:, 1], "o-", color="#66ff88", lw=1.8, ms=4, label="planned (routes around)")
    ax.scatter([start_m[0]], [start_m[1]], c="#ffffff", s=80, marker="s", zorder=6, label="start")
    ax.scatter([goal_m[0]], [goal_m[1]], c="#ffdd33", s=120, marker="*", zorder=6, label="goal")
    ax.set_title("arm plane: learned speed field + sharp board obstacle", color="w", fontsize=10)
    ax.set_xlabel("table x (m)", color="w"); ax.set_ylabel("table y (m)", color="w")
    ax.tick_params(colors="w"); [sp.set_color("#555") for sp in ax.spines.values()]
    ax.legend(facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(path, dpi=120, facecolor=fig.get_facecolor())
    print(f"  [viz] plot saved -> {path}")


if __name__ == "__main__":
    main()
