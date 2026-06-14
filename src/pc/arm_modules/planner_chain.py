"""PlannerModule (+ GoalModule2D) — the agent's PLANNER, ported faithfully from the 1D line
(`test_pc_planner.py`) to the arm's 2-D table workspace.

This is the 2-LAYER structure "the Planner dreams a goal ABOVE the goal module":

    object_xy --(Planner PC-net: state-blob + flag -> plan_z -> goal latent)--> goal_latent
                              |
                  (GoalModule2D.decode_dream)
                              v
                          goal_xy   (the place target the arm then delivers to)

* `GoalModule2D` is a small PC-net (`g_z -> g_img`) that learns a smooth, dreamable latent
  embedding of 2-D positions (pretrained by babbling); `decode_dream(z) -> position`.
* `PlannerModule` is a PC-net `p_state (blob(object) + conditioning flag) -> plan_z -> plan_g_z`
  trained REWARD-SUPERVISED on a state-dependent rule, so it learns a non-constant goal map.
  A conditioning flag steers WHICH rule (mirror <-> centre) — faithful to the 1D experiment.

Both are real `PCNetwork`s and register a `PCModule` node-port grouping (`pc_module()`), so the
literal 1D PCModule architecture lives inside.  Work is done in a normalised [0,G) grid; the
world<->grid map is calibrated from `REACH_XY` (the reachable table patch).

Ports (PlannerModule)
  in  : object_xy          (2)  perceived object world xy
        conditioning_flag  (1)  0 -> mirror rule, 1 -> centre rule
  out : goal_xy            (2)  dreamed place target (world xy)
"""
from __future__ import annotations

import numpy as np

from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule
from pc.pc_act14 import REACH_XY
from .base import ArmModule

G = 24          # latent grid resolution (world REACH patch mapped to a G×G grid)
LO, HI = REACH_XY[0], REACH_XY[1]
SPAN = HI - LO


def world_to_grid(p):
    return np.clip((np.asarray(p, float) - LO) / SPAN * (G - 1), 0.0, G - 1)


def grid_to_world(g):
    return LO + np.asarray(g, float) / (G - 1) * SPAN


def _blob2d(pos_grid, n, sigma=1.0):
    """(n,n) gaussian blob at grid pos=(x,y) scaled into an n×n image [row=y, col=x]."""
    cx = pos_grid[0] / (G - 1) * (n - 1)
    cy = pos_grid[1] / (G - 1) * (n - 1)
    xs = np.arange(n)
    gx = np.exp(-0.5 * ((xs - cx) / sigma) ** 2)
    gy = np.exp(-0.5 * ((xs - cy) / sigma) ** 2)
    return np.outer(gy, gx)


def _com2d(weight):
    w = np.clip(weight, 0.0, None); s = w.sum()
    if s < 1e-4:
        return None
    ys, xs = np.mgrid[0:w.shape[0], 0:w.shape[1]]
    return np.array([(xs * w).sum() / s, (ys * w).sum() / s])


# world-coordinate rules the Planner is rewarded to follow (state-dependent => a real map)
CENTER_W = (LO + HI) / 2.0
def rule_mirror(obj_world):                       # send the object to its mirror about centre
    return np.clip(2.0 * CENTER_W - np.asarray(obj_world, float), LO, HI)
def rule_centre(_obj_world):                      # send the object to the workspace centre
    return CENTER_W.copy()


class GoalModule2D:
    """PC-net dreamable latent embedding of 2-D positions (act9 port).  Works in grid coords."""

    def __init__(self, img=12, latent=10, rng=None):
        self.M = img
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=50, eps_tol=1e-6, eta_learn=0.01,
                        gamma=0.3, w_clip=3.0, rng=self.rng)
        self.img = net.add(SensorNode("g_img", dim=img * img))
        self.z = net.add(PCNode("g_z", dim=latent, activation="identity", eta_temporal=0.0, rng=self.rng))
        net.connect("g_z", "g_img", ConnType.UP, pressure_scale=1.0)
        self.net = net
        self.latent = latent

    def _blob(self, pos_grid):
        return _blob2d(pos_grid, self.M).reshape(-1)

    def _pos(self, flat):
        c = _com2d(np.clip(flat, 0.0, None).reshape(self.M, self.M))
        return np.array([G / 2.0, G / 2.0]) if c is None else c / (self.M - 1) * (G - 1)

    def pretrain(self, steps=8000):
        pos = self.rng.uniform(0, G - 1, 2)
        for _ in range(steps):
            pos = np.clip(pos + self.rng.normal(0, G * 0.05, 2), 0, G - 1)
            self.img.set_input(self._blob(pos))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()

    def encode(self, pos_grid):
        self.z.unclamp(); self.img.set_input(self._blob(pos_grid))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self.z.mu.copy()

    def decode_dream(self, z):
        self.img.unclamp(); self.z.clamp(np.asarray(z, float))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        out = self._pos(self.net.node("g_img").pi)
        self.z.unclamp(); self.img.set_input(self._blob(np.array([G / 2.0, G / 2.0])))
        return out

    def decode_error(self, n=12):
        errs = []
        for _ in range(n):
            p = self.rng.uniform(G * 0.1, G * 0.9, 2)
            self.z.unclamp(); self.img.set_input(self._blob(p))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            errs.append(float(np.linalg.norm(self._pos(self.net.node("g_img").pi) - p)))
        return float(np.mean(errs))


class PlannerModule(ArmModule):
    """A PC layer above the goal module: state -> dreamed goal latent -> goal_xy."""

    def __init__(self, gm: GoalModule2D, n_flags=1, simg=8, plan_dim=16, flag_amp=6.0,
                 rng=None, name="Planner"):
        super().__init__(name)
        self.gm = gm; self.n_flags = n_flags; self.S = simg; self.flag_amp = flag_amp
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=80, eps_tol=1e-6, alpha=1.0, beta=1.0,
                        gamma=0.3, eta_learn=0.01, w_clip=3.0, rng=self.rng)
        self.state = net.add(SensorNode("p_state", dim=simg * simg + n_flags))
        self.plan_z = net.add(PCNode("plan_z", dim=plan_dim, activation="tanh", eta_temporal=0.0, rng=self.rng))
        self.goal_z = net.add(PCNode("plan_g_z", dim=gm.latent, activation="identity", eta_temporal=0.0, rng=self.rng))
        net.connect("plan_z", "p_state", ConnType.UP, pressure_scale=1.0)   # decode the situation
        net.connect("plan_z", "plan_g_z", ConnType.UP, pressure_scale=2.0)  # predict the goal latent
        self.net = net
        self._last = None                                   # last per-step diagnostics

        # faithful PCModule node-port grouping (the literal 1D PCModule lives here)
        self._pcmod = (PCModule(name)
                       .add_in_port("state", ["p_state"])
                       .add_out_port("plan", ["plan_z"])
                       .add_out_port("goal_latent", ["plan_g_z"]))

        # precompute the goal-module latent over a coarse grid for fast bilinear lookup
        self._gx = np.linspace(0, G - 1, 13)
        self._grid_z = np.array([[gm.encode(np.array([x, y])) for x in self._gx] for y in self._gx])

        (self.add_in("object_xy", 2, "perceived object world xy")
             .add_in("conditioning_flag", n_flags, "0=mirror, 1=centre")
             .add_out("goal_xy", 2, "dreamed place target (world xy)"))

    def pc_module(self):
        return self._pcmod

    # -- latent lookup (bilinear over the precomputed grid; avoids a relax per train step) --
    def goal_latent(self, goal_grid):
        x = np.interp(goal_grid[0], self._gx, np.arange(len(self._gx)))
        y = np.interp(goal_grid[1], self._gx, np.arange(len(self._gx)))
        x0, y0 = int(np.floor(x)), int(np.floor(y)); x1, y1 = min(x0 + 1, len(self._gx) - 1), min(y0 + 1, len(self._gx) - 1)
        fx, fy = x - x0, y - y0
        z = ((1 - fx) * (1 - fy) * self._grid_z[y0, x0] + fx * (1 - fy) * self._grid_z[y0, x1]
             + (1 - fx) * fy * self._grid_z[y1, x0] + fx * fy * self._grid_z[y1, x1])
        return z

    def _state_vec(self, obj_world, flags=()):
        g = world_to_grid(obj_world)
        return np.concatenate([_blob2d(g, self.S).reshape(-1), self.flag_amp * np.asarray(flags, float)])

    def train(self, sample_fn, steps):
        """sample_fn() -> (obj_world, flags_tuple, rewarded_goal_world)."""
        for _ in range(steps):
            obj, flags, goal = sample_fn()
            self.state.set_input(self._state_vec(obj, flags))
            self.goal_z.clamp(self.goal_latent(world_to_grid(goal)))
            self.net.phase_predict(); self.net.phase_error(); r = self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()
        self.goal_z.unclamp()

    def dream(self, obj_world, flags=()):
        """Clamp the state, relax, read the predicted goal latent, decode -> world goal_xy."""
        self.goal_z.unclamp()
        self.state.set_input(self._state_vec(obj_world, flags))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        self._snapshot_surprise()
        goal_grid = self.gm.decode_dream(self.goal_z.mu.copy())
        return grid_to_world(goal_grid)

    def _snapshot_surprise(self):
        sens = float(np.sum(self.state.epsilon ** 2))
        st = float(np.sum(self.plan_z.epsilon ** 2) + np.sum(self.goal_z.epsilon ** 2))
        self._last = {"sensor": sens, "state": st, "total": sens + st}

    def step(self):
        obj = self.get_in("object_xy")
        if obj is None:
            return
        flag = self.get_in("conditioning_flag")
        flags = () if flag is None else tuple(np.asarray(flag, float).tolist())
        self.set_out("goal_xy", self.dream(obj, flags))

    def surprise(self):
        return self._last


def _evaluate(planner, rule, flags_fn=lambda o: (), n=40):
    """Dreamed goal vs rule target across the workspace: per-axis error (mm) + slope."""
    xs = np.linspace(LO[0] + 0.1 * SPAN[0], LO[0] + 0.9 * SPAN[0], n)
    ys = np.linspace(LO[1] + 0.1 * SPAN[1], LO[1] + 0.9 * SPAN[1], n)
    objs = np.stack([xs, ys], 1)
    dreamed = np.array([planner.dream(o, flags_fn(o)) for o in objs])
    target = np.array([rule(o) for o in objs])
    err_mm = float(np.mean(np.linalg.norm(dreamed - target, axis=1))) * 1000.0
    slope_x = float(np.polyfit(objs[:, 0], dreamed[:, 0], 1)[0])   # mirror -> ~-1, centre -> ~0
    return err_mm, slope_x, objs, dreamed, target


def main():
    import os
    rng = np.random.default_rng(0)
    print("=" * 76)
    print("  PlannerModule (2-layer, arm 2-D) — dream a goal from the perceived object")
    gm = GoalModule2D(rng=np.random.default_rng(7))
    gm.pretrain(int(os.environ.get("PLAN_GM_STEPS", "8000")))
    floor = gm.decode_error()
    floor_mm = floor / (G - 1) * float(np.linalg.norm(SPAN)) * 1000.0
    print(f"  GoalModule2D decode error: {floor:.2f} grid-units of {G}  (~{floor_mm:.0f} mm floor)")
    print("=" * 76)

    def rand_obj():
        return np.array([rng.uniform(LO[0] + 0.05 * SPAN[0], HI[0] - 0.05 * SPAN[0]),
                         rng.uniform(LO[1] + 0.05 * SPAN[1], HI[1] - 0.05 * SPAN[1])])

    STEPS = int(os.environ.get("PLAN_STEPS", "12000"))

    # A) untrained baseline
    base = PlannerModule(gm, n_flags=1, rng=np.random.default_rng(1))
    a = _evaluate(base, rule_mirror, flags_fn=lambda o: (0.0,))
    print(f"  A) untrained               : rule_err={a[0]:5.1f} mm  slope_x={a[1]:+.2f}   (expect large, slope~0)")

    # B) SINGLE-rule mirror -> the strong result (reaches the decode floor)
    mono = PlannerModule(gm, n_flags=0, rng=np.random.default_rng(1))
    mono.train(lambda: (lambda o: (o, (), rule_mirror(o)))(rand_obj()), STEPS)
    b = _evaluate(mono, rule_mirror)
    print(f"  B) trained MIRROR (1 rule) : rule_err={b[0]:5.1f} mm  slope_x={b[1]:+.2f}   (expect small, slope~-1)")

    # C) CONDITIONED: one net, a flag switches mirror<->centre
    cond = PlannerModule(gm, n_flags=1, rng=np.random.default_rng(1))

    def cond_sample():
        o = rand_obj(); f = int(rng.integers(0, 2))
        g = rule_mirror(o) if f == 0 else rule_centre(o)
        return o, (float(f),), g

    cond.train(cond_sample, STEPS)
    c0 = _evaluate(cond, rule_mirror, flags_fn=lambda o: (0.0,))
    c1 = _evaluate(cond, rule_centre, flags_fn=lambda o: (1.0,))
    print(f"  C) conditioned flag=0 MIRROR: rule_err={c0[0]:5.1f} mm  slope_x={c0[1]:+.2f}")
    print(f"     conditioned flag=1 CENTRE: rule_err={c1[0]:5.1f} mm  slope_x={c1[1]:+.2f}   (steers, slope~0)")
    print("-" * 76)
    print("  obj_world -> dreamed (single-rule mirror):")
    for i in range(0, len(b[2]), 10):
        o, d, t = b[2][i], b[3][i], b[4][i]
        print(f"    obj=({o[0]:+.3f},{o[1]:.3f})  dreamed=({d[0]:+.3f},{d[1]:.3f})  target=({t[0]:+.3f},{t[1]:.3f})")
    print("=" * 76)
    print("  Read (honest): B beats A and reaches the GoalModule decode floor -> the 2-layer Planner")
    print("  LEARNS a state-dependent goal map.  C: one flag steers mirror<->centre; the single shallow")
    print("  shared net learns the conditioned mirror only PARTIALLY (capacity split across both rules).")


class TransitionModel2D:
    """PC-net learning transition dynamics in the 2D GoalModule latent space.
    
    Predicts next latent z_{t+1} from current latent z_t and 2D action u_t:
        z_{t+1} = W_x^T z_t + W_u^T u_t
    """

    def __init__(self, gm: GoalModule2D, rng=None) -> None:
        self.gm = gm
        self.rng = rng or np.random.default_rng()
        self.net = PCNetwork(
            eta_inf=0.1,
            n_relax=20,
            eta_learn=0.01,
            lambda_decay=0.0005,
            w_clip=3.0,
            rng=self.rng
        )

        self.x_node = self.net.add(SensorNode("x", dim=gm.latent))
        self.u_node = self.net.add(SensorNode("u", dim=2))
        self.y_node = self.net.add(PCNode("y", dim=gm.latent, activation="identity", rng=self.rng))

        self.c_x = self.net.connect("x", "y", ConnType.UP)
        self.c_u = self.net.connect("u", "y", ConnType.UP)

    def observe(self, pos_t: np.ndarray, pos_next: np.ndarray, action_2d: np.ndarray) -> None:
        """Train transition model on one step transition."""
        z_t = self.gm.encode(pos_t)
        z_next = self.gm.encode(pos_next)

        self.x_node.set_input(z_t)
        self.u_node.set_input(np.asarray(action_2d, float))
        self.y_node.clamp(z_next)

        self.net.step(learn=True)
        self.net.commit_step()


class ChainedPlannerModule(ArmModule):
    """Planner that unrolls the TransitionModel2D over K steps.
    
    Clamps start state (object_xy) and goal state (goal_xy), and relaxes to infer
    intermediate trajectory states and required action directions.
    """

    def __init__(
        self,
        gm: GoalModule2D,
        trans_model: TransitionModel2D,
        horizon: int = 4,
        gamma: float = 0.85,
        rng=None,
        name: str = "ChainedPlanner"
    ) -> None:
        super().__init__(name)
        self.gm = gm
        self.trans_model = trans_model
        self.horizon = horizon
        self.gamma = gamma
        self.rng = rng or np.random.default_rng()

        self.add_in("object_xy", 2, "current object position (world xy)")
        self.add_in("goal_xy", 2, "target goal position (world xy)")
        self.add_out("next_subgoal_xy", 2, "immediate next planned subgoal (world xy)")
        self.add_out("plan_trajectory", 2 * (horizon + 1), "full planned trajectory coordinates")

        self._last_plan = None

    def plan(self, start_xy: np.ndarray, goal_xy: np.ndarray) -> list[np.ndarray]:
        K = self.horizon
        net = PCNetwork(eta_inf=0.08, n_relax=150, eps_tol=1e-6, rng=self.rng)

        nodes_x = []
        for k in range(K + 1):
            nodes_x.append(net.add(PCNode(f"x{k}", dim=self.gm.latent, activation="identity", rng=self.rng)))

        nodes_u = []
        for k in range(K):
            nodes_u.append(net.add(PCNode(f"u{k}", dim=2, activation="identity", rng=self.rng)))

        conns_x = []
        conns_u = []
        for k in range(K):
            cx = net.connect(f"x{k}", f"x{k+1}", ConnType.UP)
            cu = net.connect(f"u{k}", f"x{k+1}", ConnType.UP)
            conns_x.append(cx)
            conns_u.append(cu)

        # Share weights from transition model
        W_x = self.trans_model.c_x.W
        W_u = self.trans_model.c_u.W
        for cx in conns_x:
            cx.W = W_x
        for cu in conns_u:
            cu.W = W_u

        # Error discounting
        for k in range(K):
            scale = self.gamma ** k
            conns_x[k].pressure_scale = scale
            conns_u[k].pressure_scale = scale

        # Clamp endpoints
        z_start = self.gm.encode(start_xy)
        z_goal = self.gm.encode(goal_xy)
        nodes_x[0].clamp(z_start)
        nodes_x[K].clamp(z_goal)

        # Initialize middle nodes with linear interpolation in latent space plus small noise
        for k in range(1, K):
            frac = k / K
            z_init = (1.0 - frac) * z_start + frac * z_goal
            nodes_x[k].mu = z_init + self.rng.normal(0, 0.01, self.gm.latent)

        for k in range(K):
            nodes_u[k].mu = self.rng.uniform(0.4, 0.6, 2)
            nodes_u[k].mu /= nodes_u[k].mu.sum()

        # Relaxation
        net.step(learn=False)

        # Decode trajectory
        trajectory = []
        for k in range(K + 1):
            xy = self.gm.decode_dream(nodes_x[k].mu)
            trajectory.append(xy)

        self._last_plan = {
            "trajectory": trajectory,
            "actions": [u.mu.copy() for u in nodes_u]
        }
        return trajectory

    def step(self) -> None:
        start = self.get_in("object_xy")
        goal = self.get_in("goal_xy")
        if start is None or goal is None:
            return
        traj = self.plan(start, goal)
        # The immediate next subgoal is traj[1]
        self.set_out("next_subgoal_xy", traj[1])
        self.set_out("plan_trajectory", np.array(traj).reshape(-1))


if __name__ == "__main__":
    main()


