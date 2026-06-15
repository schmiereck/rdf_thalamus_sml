r"""chain_obstacle_data.py — PHYSICAL collision data collection for the obstacle-aware world model.

The agent does a physics random-walk in the front working area with a STATIC board (a fixed wall) placed
at random.  When a move drives the gripper into the board it is physically BLOCKED -> the achieved
displacement is ~0 (a collision).  Each transition records (hand xy, board-occupancy map, desired step u,
ACHIEVED displacement).  The world model later LEARNS from these that progress is blocked where the board
is -- the agent learns the obstacle by crashing into it, not from a hand-coded forbidden zone.

This module only COLLECTS + encodes; the model and planner live in test_pc_chain_arm_obstacle.py.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import mujoco

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import reach_step

# front working area (avoids the base-singularity / self-collision mess at the centre)
WX = (-0.16, 0.16)
WY = (0.06, 0.24)
Z0 = 0.05
U_DES = 0.05                      # desired in-plane step magnitude (large enough to drive into the board)
OCC_N = 12                        # occupancy map resolution (OCC_N x OCC_N over the working bbox)
SPAN = max(WX[1] - WX[0], WY[1] - WY[0])
ORG = np.array([WX[0], WY[0]])


def occ_map(cx, hx, hy, cy):
    """Board footprint as an OCC_N x OCC_N occupancy map over the working bbox (1 inside the board)."""
    xs = ORG[0] + (np.arange(OCC_N) + 0.5) / OCC_N * SPAN
    ys = ORG[1] + (np.arange(OCC_N) + 0.5) / OCC_N * SPAN
    gx, gy = np.meshgrid(xs, ys)                       # [row=y, col=x]
    return ((np.abs(gx - cx) <= hx) & (np.abs(gy - cy) <= hy)).astype(float).ravel()


class BoardCtl:
    """Move/resize the STATIC board obstacle at runtime (body_pos + geom_size + mj_forward)."""

    def __init__(self, sim):
        self.sim = sim
        self.bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "board")
        self.gid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_GEOM, "board_geom")
        self.cx = self.cy = 0.0; self.hx = 0.012; self.hy = 0.05; self.tall = 0.06

    def place(self, cx, cy, hx, hy, tall=0.06):
        self.cx, self.cy, self.hx, self.hy, self.tall = cx, cy, hx, hy, tall
        self.sim.m.body_pos[self.bid] = [cx, cy, tall]
        self.sim.m.geom_size[self.gid] = [hx, hy, tall]
        mujoco.mj_forward(self.sim.m, self.sim.d)

    def park(self):
        self.place(0.0, 0.55, 0.012, 0.05)            # far out of the working area

    def occ(self):
        return occ_map(self.cx, self.hx, self.hy, self.cy)


def _settle(sim, target, steps):
    for _ in range(steps):
        reach_step(sim, target, gain=3.0); sim.step(2)


def collect(sim, board, n, rng, restart_every=24):
    """Physics random-walk -> (XY, OCC, U, D) arrays in METRES.  Re-places the board and restarts in a new
    spot periodically to cover the area; records the ACHIEVED displacement each step (blocked at the board)."""
    XY, OCC, U, D = [], [], [], []
    for nm in ("obj_red", "obj_green", "obj_blue"):           # park the cubes: collisions must be with
        sim.set_object(nm, [0.0, -0.55 - 0.03 * "rgb".index(nm[4])])   # the BOARD only, not stray cubes
    hand = sim.grasp_pos().copy()
    for i in range(n):
        if i % restart_every == 0:
            board.park()
            start = np.array([rng.uniform(*WX), rng.uniform(*WY), Z0])
            _settle(sim, start, 40)
            # random board crossing the working area (sometimes parked, so free transitions too)
            if rng.random() < 0.78:
                board.place(rng.uniform(-0.10, 0.10), rng.uniform(0.11, 0.20),
                            0.012, rng.uniform(0.04, 0.07))
            else:
                board.park()
            hand = sim.grasp_pos().copy()
        xy0 = sim.grasp_pos()[:2].copy()
        ang = rng.uniform(0, 2 * np.pi); mag = rng.uniform(0.2, 1.0) * U_DES
        u = mag * np.array([np.cos(ang), np.sin(ang)])
        target = np.array([xy0[0] + u[0], xy0[1] + u[1], Z0])
        _settle(sim, target, 10)
        xy1 = sim.grasp_pos()[:2].copy()
        XY.append(xy0); OCC.append(board.occ()); U.append(u); D.append(xy1 - xy0)
    return np.array(XY), np.array(OCC), np.array(U), np.array(D)


def main():
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from pc.pc_act14 import BracketArmSim
    rng = np.random.default_rng(0)
    sim = BracketArmSim(render_wh=(80, 80)); sim.set_reach_site("contact")
    board = BoardCtl(sim)
    n = int(os.environ.get("OBS_N", "1500"))
    XY, OCC, U, D = collect(sim, board, n, rng)
    dn = np.linalg.norm(D, axis=1); un = np.linalg.norm(U, axis=1)
    ratio = dn / (un + 1e-9)
    blocked = ratio < 0.35
    print(f"collected {n} physics transitions")
    print(f"  achieved/desired ratio: mean {ratio.mean():.2f}  blocked(<0.35) fraction {blocked.mean():.2f}")
    print(f"  XY x[{XY[:,0].min():.2f},{XY[:,0].max():.2f}] y[{XY[:,1].min():.2f},{XY[:,1].max():.2f}]")
    print(f"  |D| mm: p50 {np.percentile(dn,50)*1000:.1f}  p95 {np.percentile(dn,95)*1000:.1f}")
    # are blocked transitions concentrated where a board was present + the move pointed into it?
    occ_any = OCC.sum(1) > 0
    print(f"  board present fraction {occ_any.mean():.2f}; blocked|board {blocked[occ_any].mean():.2f}  "
          f"blocked|no-board {blocked[~occ_any].mean():.2f}")


if __name__ == "__main__":
    main()
