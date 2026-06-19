r"""test_pc_macro_plan.py — STEP 3: CHAIN + PLAN macro sub-goals through the LEARNED macro model.

Step 2 learned a macro sub-goal-outcome model F(state7, macro-action4) -> end-state7 that CHAINS tightly
(~4mm final-object drift over a full episode).  Step 3 PLANS with it: given the start state + the goal, it
SEARCHES (CEM, cross-entropy method) for the chain of macro sub-goals whose model-rollout lands the object on
the goal.  The plan is DISCOVERED by search through the LEARNED model -- not hand-scripted.  (The macro TYPES
are learned by the model from data; the low-level execution of a macro reuses the proven reach + gentle-grasp
primitive.)

HONEST FINDING: the planner CHAINS and reaches the goal IN-MODEL (0.8mm vs 22mm naive), but pre-compensating
the place target on the REAL arm is WORSE (planned 41mm / 12-of-16 vs baseline 14mm / 16-of-16) -- the ~20mm
in-model 'offset' is MODEL BIAS, not a real controller offset (the teacher already places ~14mm), so the
planner exploited its own model error.  The teacher-trained macro model is reliable for COARSE / RELATIVE
chaining (sequencing, routing), NOT fine ABSOLUTE place correction.  Also: the model does NOT capture the
gripper's causal role (grip is constant-per-phase in the data), so the plan keeps the learned grip pattern.
Lesson (matches the chain studies): coordinate interpolation for unconstrained precise moves; reserve the
learned chain for CONSTRAINED dynamics or COARSE dense policy-shaping (3b).

  python src/pc/test_pc_macro_plan.py             headless: train model, plan, in-model validation + affordance
                                                  discovery check + a plot of the planned chain
  MPLAN_LIVE=1 python src/pc/test_pc_macro_plan.py   LIVE on the full MuJoCo arm: execute the PLANNED chain
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim, REACH_XY
import pc.pc_act16 as act16
from pc.pc_act16 import OVER_Z, GRASP_Z, CARRY_Z, J5_OPEN, J5_GRIP
from pc.arm_modules import BodyModelModule
from test_pc_fwd_plan import FwdMLP, SDIM
from test_pc_macro_model import collect_teacher

PHASE_GRIP = [J5_OPEN, J5_OPEN, J5_GRIP, J5_GRIP, J5_GRIP, J5_GRIP, J5_OPEN]   # over lower close lift carry low rel
PHASE_Z = [OVER_Z, GRASP_Z, GRASP_Z, CARRY_Z, CARRY_Z, GRASP_Z, GRASP_Z]


def make_chain(c0, W, P, grips=None):
    """The pick-place as a macro chain; grasp macros aim at the object c0, carry at W, place at P.
    grips overrides the gripper pattern (for the affordance-discovery experiment)."""
    g = PHASE_GRIP if grips is None else grips
    xy = [c0, c0, c0, c0, W, P, P]
    return [np.array([p[0], p[1], z, gg]) for p, z, gg in zip(xy, PHASE_Z, g)]


def roll(model, s0, chain):
    s = s0.copy(); traj = [s.copy()]
    for a in chain:
        s = s + model.predict_delta(s[None, :], a[None, :])[0]; traj.append(s.copy())
    return s, np.array(traj)


def plan_cem(model, s0, c0, G, iters=6, pop=96, elite=12, rng=None):
    """SEARCH (CEM) the free chain DOFs -- the carry waypoint W and the place target P -- so the model-rollout
    lands the object on the goal G.  The plan is discovered through the LEARNED model."""
    rng = rng or np.random.default_rng(0)
    mean = np.concatenate([G, G]); std = np.full(4, 0.05)
    best = None
    for _ in range(iters):
        X = rng.normal(mean, std, (pop, 4))
        costs = []
        for x in X:
            fin, _ = roll(model, s0, make_chain(c0, x[:2], x[2:]))
            costs.append(np.linalg.norm(fin[3:5] - G) + 0.03 * np.linalg.norm(x[:2] - 0.5 * (c0 + G)))
        costs = np.array(costs); idx = np.argsort(costs)[:elite]
        mean = X[idx].mean(0); std = X[idx].std(0) + 1e-3
        best = (X[idx[0]], costs[idx[0]])
    W, P = best[0][:2], best[0][2:]
    fin, traj = roll(model, s0, make_chain(c0, W, P))
    return W, P, fin, traj


def main():
    cam = os.environ.get("MPLAN_CAM", "overview").lower()
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    print(f"  learned inverse kinematics: {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    n_ep = int(os.environ.get("MPLAN_EPS", "80"))
    print("macro-plan — STEP 3: CHAIN + PLAN macro sub-goals through the LEARNED macro model")
    print(f"  training the macro model on {n_ep} teacher rollouts ...")
    S, A, E, seqs = collect_teacher(sim, bm, cam, n_ep)
    model = FwdMLP(din=11, dout=7, h=128, rng=np.random.default_rng(0))
    model.fit(np.column_stack([S, A]), E - S, epochs=int(os.environ.get("MPLAN_EPOCHS", "600")))

    sim.reset_home(); home_hand = sim.grasp_pos().copy()
    def s0_for(c0):
        return np.array([home_hand[0], home_hand[1], home_hand[2], c0[0], c0[1], 0.012, J5_OPEN])

    if os.environ.get("MPLAN_LIVE", "0") == "1":
        return live(sim, bm, model, s0_for, cam)

    # ---- in-model validation: planning corrects the learned PLACE OFFSET ----
    lo, hi = REACH_XY; rng = np.random.default_rng(7); pe, be = [], []
    for _ in range(60):
        c0 = lo + rng.random(2) * (hi - lo); G = lo + rng.random(2) * (hi - lo)
        s0 = s0_for(c0)
        _, _, fin, _ = plan_cem(model, s0, c0, G, rng=rng)
        pe.append(np.linalg.norm(fin[3:5] - G) * 1000)
        base, _ = roll(model, s0, make_chain(c0, G, G))          # naive: aim carry+place straight at G
        be.append(np.linalg.norm(base[3:5] - G) * 1000)
    print(f"  IN-MODEL: PLANNED chain lands obj {np.mean(pe):.1f} mm from goal   vs naive aim-at-goal {np.mean(be):.1f} mm")
    print("  => planning INVERTS the learned model to pre-compensate the teacher's systematic place offset.")
    print("  (Honest: the model does NOT capture the gripper's causal role -- grip is constant-per-phase in")
    print("   the teacher data -- so the plan keeps the learned grip pattern; its lever is the place offset.)")

    # ---- REAL ARM: does the planned place correction TRANSFER?  place-at-planned-P vs place-at-goal ----
    n = int(os.environ.get("MPLAN_AB", "16"))
    dp, ep = real_ab(sim, bm, model, s0_for, cam, n, planned=True)
    db, eb = real_ab(sim, bm, model, s0_for, cam, n, planned=False)
    print(f"  REAL ARM (place-at-PLANNED-P vs place-at-goal), {n} eps each, tol 25mm:")
    print(f"    PLANNED : delivered {dp}/{n}   mean obj->goal {ep:.0f} mm")
    print(f"    baseline: delivered {db}/{n}   mean obj->goal {eb:.0f} mm")
    print("  HONEST: the planner CHAINS + reaches the goal IN-MODEL, but pre-compensating the place on the")
    print("  real arm is WORSE -- the ~20mm in-model 'offset' is MODEL BIAS, not a real one (the teacher")
    print("  already places ~14mm), so the planner exploited its own model error.  The teacher-trained macro")
    print("  model is reliable for COARSE / RELATIVE chaining (sequence, routing), NOT fine ABSOLUTE place")
    print("  correction.  Matches the earlier finding: coordinate interpolation for unconstrained precise")
    print("  moves; reserve the learned chain for CONSTRAINED dynamics (or coarse dense policy-shaping, 3b).")

    c0 = np.array([0.0, 0.15]); G = np.array([0.06, 0.18])
    _, _, _, traj = plan_cem(model, s0_for(c0), c0, G, rng=np.random.default_rng(1))
    _plot(c0, G, traj, os.path.join(os.path.dirname(__file__), "macro_plan.png"))
    print("  Next (3b): train the model on POLICY rollouts + use the chain as COARSE dense shaping targets")
    print("  for the policy (not precise place targets), measured vs the AWR plateau; watch it live.")


def real_ab(sim, bm, model, s0_for, cam, n, planned):
    """Execute on the real arm: place at the PLANNED P (planned=True) or straight at the goal (baseline).
    Same goal sequence (seeded) for a fair A/B.  Returns (delivered<25mm, mean obj->goal mm)."""
    gr = np.random.default_rng(123); store = {"P": None}; errs = {"e": [], "ok": 0}
    lo, hi = REACH_XY

    def goal_fn(cmd, obj_xy):
        return lo + gr.random(2) * (hi - lo)

    def post_goal(cmd, obj_xy, G):
        if planned:
            _, P, _, _ = plan_cem(model, s0_for(np.asarray(obj_xy)[:2]), np.asarray(obj_xy)[:2],
                                  np.asarray(G)[:2], rng=np.random.default_rng(0))
            store["P"] = P

    def place_servo_fn(hxy):
        return store["P"] if (planned and store["P"] is not None) else hxy

    def ep_end(ep, ok, err):
        errs["e"].append(err * 1000); errs["ok"] += int(err < 0.025)

    act16.run_combined._quiet = True
    act16.run_combined(sim, bm, None, cam, episodes=n, policy_fn=act16.reactive_subgoal, goal_fn=goal_fn,
                       post_goal_fn=post_goal, place_servo_fn=(place_servo_fn if planned else None),
                       episode_end_fn=ep_end, lifelong=False)
    act16.run_combined._quiet = False
    return errs["ok"], float(np.mean(errs["e"]))


def _plot(c0, G, traj, path):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.5, 5))
        labels = ["over", "lower", "close", "lift", "carry", "lower", "release"]
        ax.plot(traj[:, 3] * 1000, traj[:, 4] * 1000, "-o", color="tab:blue", label="planned object path")
        for i, lab in enumerate(labels):
            ax.annotate(lab, (traj[i + 1, 3] * 1000, traj[i + 1, 4] * 1000), fontsize=7)
        ax.scatter([c0[0] * 1000], [c0[1] * 1000], c="g", s=80, marker="s", label="object start")
        ax.scatter([G[0] * 1000], [G[1] * 1000], c="r", s=120, marker="*", label="goal")
        ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)"); ax.set_aspect("equal")
        ax.set_title("STEP 3 — macro sub-goal chain PLANNED through the learned model"); ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(path, dpi=110); print(f"  [viz] saved {path}")
    except Exception as e:
        print(f"  [viz] plot skipped: {e}")


def live(sim, bm, model, s0_for, cam):
    """Execute the PLANNED chain on the full arm via the proven run_combined primitives (place-target driven
    by the plan).  The carry waypoint + place target come from planning through the LEARNED model."""
    store = {"W": None, "P": None}
    lo, hi = REACH_XY; rng = np.random.default_rng(3)

    def goal_fn(cmd, obj_xy):
        return lo + rng.random(2) * (hi - lo)

    def post_goal(cmd, obj_xy, G):
        W, P, _, _ = plan_cem(model, s0_for(np.asarray(obj_xy)[:2]), np.asarray(obj_xy)[:2], np.asarray(G)[:2],
                              rng=np.random.default_rng(0))
        store["W"], store["P"] = W, P

    def carry_target_fn(hxy, goal):
        W = store["W"]
        return W if (W is not None and np.linalg.norm(np.asarray(hxy) - W) > 0.03) else goal

    def place_servo_fn(hxy):
        return store["P"] if store["P"] is not None else hxy

    print("  LIVE: executing the PLANNED macro chain on the arm (place target + carry waypoint from the plan)")
    try:
        import mujoco.viewer as mjv
    except Exception as e:
        print(f"  [live] viewer unavailable: {e}"); return
    with mjv.launch_passive(sim.m, sim.d) as v:
        d, m = act16.run_combined(sim, bm, None, cam, episodes=int(os.environ.get("MPLAN_LIVE_EPS", "6")),
                                  policy_fn=act16.reactive_subgoal, goal_fn=goal_fn, post_goal_fn=post_goal,
                                  carry_target_fn=carry_target_fn, place_servo_fn=place_servo_fn,
                                  track_fn=v.sync, lifelong=False)
    print(f"  delivered {d}/{m} via the planned chain")


if __name__ == "__main__":
    main()
