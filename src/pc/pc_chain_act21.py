r"""pc_act21.py — a RESEARCHING agent: curiosity-driven goals + lifelong adaptation, observed.

Moves further off scripts/rules:
  * the PLANNER is now the CuriosityPlanner — it dreams its own goals by NOVELTY (no reward, no
    mirror/centre rule); the agent explores the workspace because it wants to see new places.
  * FK and the LEARNED inverse kinematics adapt ONLINE (lifelong) from the agent's own motion.

This is an OBSERVATORY for point (c): does long exploration improve the measured values?  After an
optional arm PERTURBATION (a changed body the trained models don't know), it runs three phases —
frozen baseline -> lifelong exploration (logging coverage / FK-surprise / delivery per episode) ->
frozen re-measure — so you SEE the agent recover and improve as it explores.

Env: ACT21_HEADLESS  ACT21_EPISODES (explore)  ACT21_BASE (A/B measure)  ACT21_COLLECT  ACT21_RES
     ACT21_PERTURB (m forearm lengthening, default 0.02)  ACT21_GM_STEPS  ACT21_CAM
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.pc_act14 import BracketArmSim
import pc.pc_act16 as act16
from pc.arm_modules import ArmAgent, BodyModelModule, GoalModule2D, MotorModule, CuriosityPlanner
from pc.arm_modules.planner_chain import TransitionModel2D, ChainedPlannerModule



def _perturb(sim, dz):
    wid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "wrist_link")
    sim.m.body_pos[wid, 2] += dz
    mujoco.mj_forward(sim.m, sim.d)


def main():
    HEADLESS = os.environ.get("ACT21_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT21_CAM", "overview").lower()
    COLLECT = int(os.environ.get("ACT21_COLLECT", "18"))
    EXPLORE = int(os.environ.get("ACT21_EPISODES", "24"))
    BASE = int(os.environ.get("ACT21_BASE", "10"))
    RES = int(os.environ.get("ACT21_RES", "240"))
    PERTURB = float(os.environ.get("ACT21_PERTURB", "0.02"))
    GM_STEPS = int(os.environ.get("ACT21_GM_STEPS", "8000"))

    print("act21 — researching agent: CuriosityPlanner (no rule) + lifelong FK/IK, observed")
    sim = BracketArmSim(render_wh=(RES, RES)); sim.set_reach_site("contact")

    # ---- build + train the modules (as act20) ----
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    gm = GoalModule2D(rng=np.random.default_rng(7)); gm.pretrain(GM_STEPS)
    motor = MotorModule(rng=np.random.default_rng(2))
    curio = CuriosityPlanner(gm, rng=np.random.default_rng(1))

    # Transition Model & Chained Planner
    trans_model = TransitionModel2D(gm, rng=np.random.default_rng(99))
    chained_planner = ChainedPlannerModule(gm, trans_model, horizon=4, rng=np.random.default_rng(10))

    Xs, Ys = [], []
    prev_obj_xy = None
    def log(state, aim, j5):
        nonlocal prev_obj_xy
        Xs.append(state.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))
        
        # Train transition model on object movements
        curr_obj_xy = state[3:5]
        if prev_obj_xy is not None:
            diff = curr_obj_xy - prev_obj_xy
            dist = np.linalg.norm(diff)
            if 0.001 < dist < 0.05: # ignore stationary or teleportation
                trans_model.observe(prev_obj_xy, curr_obj_xy, diff / dist)
        prev_obj_xy = curr_obj_xy.copy()

    print(f"  collecting reactive-teacher demos ({COLLECT} eps) ...")
    act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal, log_fn=log)
    motor.fit(np.array(Xs), np.array(Ys))

    # Chained planning trajectory execution policy
    subgoals = []
    subgoal_idx = 0
    final_goal = None

    def chained_policy(state):
        nonlocal subgoals, subgoal_idx, final_goal
        
        hand_xyz = state[0:3]
        obj_xy = state[3:5]
        obj_z = state[5]
        tgt_in_state = state[6:8].copy()
        
        # Detect target change (new episode or goal change)
        if final_goal is None or np.linalg.norm(tgt_in_state - final_goal) > 0.005:
            final_goal = tgt_in_state.copy()
            # Plan a sequence of subgoals from object position to final goal
            subgoals = chained_planner.plan(obj_xy, final_goal)
            subgoal_idx = 1
            
        # Determine if we are in the carrying or pushing phase
        dist_hand_obj = np.linalg.norm(hand_xyz[:2] - obj_xy)
        is_transporting = (obj_z > 0.028) or (dist_hand_obj < 0.06)
        
        if is_transporting:
            # Advance subgoal if we are close to the current one
            if subgoal_idx < len(subgoals):
                curr_subgoal = subgoals[subgoal_idx]
                dist_to_subgoal = np.linalg.norm(obj_xy - curr_subgoal)
                if dist_to_subgoal < 0.035 and subgoal_idx < len(subgoals) - 1:
                    subgoal_idx += 1
                    curr_subgoal = subgoals[subgoal_idx]
            else:
                curr_subgoal = final_goal
        else:
            # During initial approach, keep the final goal to avoid confusing the policy
            curr_subgoal = final_goal
            
        mod_state = state.copy()
        mod_state[6:8] = curr_subgoal
        return motor.predict(mod_state)


    prev_explore_xy = None
    def log_explore(state, aim, j5):
        nonlocal prev_explore_xy
        curr_xy = state[3:5]
        if prev_explore_xy is not None:
            diff = curr_xy - prev_explore_xy
            dist = np.linalg.norm(diff)
            if 0.001 < dist < 0.05:
                trans_model.observe(prev_explore_xy, curr_xy, diff / dist)
        prev_explore_xy = curr_xy.copy()

    print("  training the LEARNED inverse kinematics ...")
    print(f"    IK babble reconstruction: {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    agent = ArmAgent("researching-arm")
    for m in (curio, motor, bm):
        agent.add(m)
    print(agent.summary())

    from pc.arm_modules.planner import LO, HI, SPAN

    def curiosity_goal(cmd, obj_xy):
        return curio.dream()                                # the planner dreams its OWN goal (novelty)

    def fixed_goals(seed):
        """A FIXED random-goal sequence (identical for a given seed) so the A vs C delivery
        comparison isolates the lifelong recovery — NOT the curiosity goal-difficulty drift."""
        r = np.random.default_rng(seed)
        return lambda cmd, obj: r.uniform(LO + 0.15 * SPAN, HI - 0.15 * SPAN)

    if PERTURB:
        _perturb(sim, PERTURB)
        print(f"  *** perturbed the arm: +{PERTURB*1000:.0f}mm forearm -> trained FK/IK are now STALE ***")

    GSEED = 77
    if HEADLESS:
        act16.run_combined._quiet = True
        # --- A: frozen baseline on FIXED goals (post-perturb) ---
        dA, mA = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=chained_policy,
                                    goal_fn=fixed_goals(GSEED), lifelong=False)
        # --- B: LIFELONG exploration with the curiosity planner (adapt + explore), log per episode ---
        rows = []
        def ep_end(ep, ok, err):
            rows.append((int(ok), err, curio.coverage(), bm._surprise_mm))
        dB, mB = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=chained_policy,
                                    goal_fn=curiosity_goal, lifelong=True, episode_end_fn=ep_end, log_fn=log_explore)
        # --- C: frozen re-measure on the SAME FIXED goals as A (isolates lifelong recovery) ---
        dC, mC = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=chained_policy,
                                    goal_fn=fixed_goals(GSEED), lifelong=False)
        act16.run_combined._quiet = False

        rows = np.array(rows, float)
        half = max(1, len(rows) // 2)
        print("=" * 72)
        print(f"  PERTURB +{PERTURB*1000:.0f}mm — does lifelong exploration recover the agent?")
        print(f"  A) frozen, FIXED goals (post-perturb): delivered {dA}/{mA}")
        print(f"  B) lifelong + CURIOSITY ({EXPLORE} eps): delivered {dB}/{mB}  [curiosity seeks the hard edges]")
        print(f"       coverage   {rows[0,2]:.2f} -> {rows[-1,2]:.2f}   (workspace explored, NO reward/rule)")
        print(f"       FK surprise {np.nanmean(rows[:half,3]):.2f} -> {np.nanmean(rows[half:,3]):.2f} mm (early->late half)")
        print(f"  C) frozen, SAME FIXED goals (after)  : delivered {dC}/{mC}")
        print("  Read: C should beat A on the SAME goals -> lifelong recovered the perturbed kinematics;")
        print("        meanwhile B's curiosity raised coverage (it deliberately seeks novel hard regions).")
        print("=" * 72)
        try:
            _plot_metrics(rows, PERTURB, os.path.join(os.path.dirname(__file__), "act21_metrics.png"))
        except Exception as e:
            print(f"  [viz] could not save metrics plot: {e}")
        return

    # -------- coupled: VisualCortex perception + live views --------
    print("  (coupling VisualCortex perception + CuriosityPlanner + lifelong; live fovea + surprise)")
    try:
        from pc.pc_act18 import SurpriseViz
        from pc.arm_modules import VisualCortexModule
        vc, P = VisualCortexModule.from_sim(sim, CAM, RES, headless=False)
        agent.add(vc)
        sviz = SurpriseViz(title="act21 — curiosity + lifelong (surprise over time)")

        def perceive(cmd):
            return vc.perceive(cmd), None, "grasp"

        def track_and_plot():
            vc.track()
            bmm = bm._surprise_mm
            d = vc.surprise(); ps = curio.surprise()
            if d is not None:
                sviz.push(d["sensor"], d["state"], d["total"], d["relax"], bmm,
                          planner=(ps["novelty"] if ps else None))

        d, m = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=chained_policy,
                                  goal_fn=curiosity_goal, lifelong=True, perceive_fn=perceive, track_fn=track_and_plot,
                                  log_fn=log_explore)
        print(f"  explored+delivered {d}/{m} to self-dreamed goals; coverage {curio.coverage():.2f}")
        print("  [viz] close the windows to exit.")
        (vc.viz or sviz).hold()
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  [viz/perception] {e}; falling back to privileged run")
        act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=chained_policy,
                           goal_fn=curiosity_goal, lifelong=True, log_fn=log_explore)



def _plot_metrics(rows, perturb, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ep = np.arange(1, len(rows) + 1)
    fig, ax = plt.subplots(3, 1, figsize=(7, 7), sharex=True)
    fig.patch.set_facecolor("#0e0e12"); fig.suptitle(f"act21 lifelong exploration (+{perturb*1000:.0f}mm perturb)", color="w")
    for a in ax:
        a.set_facecolor("#0e0e12"); a.grid(True, color="#333", lw=0.4); a.tick_params(colors="w")
        [s.set_color("#555") for s in a.spines.values()]
    ax[0].plot(ep, rows[:, 2], color="#cc88ff"); ax[0].set_ylabel("coverage", color="#cc88ff")
    ax[0].set_title("workspace coverage (curiosity, no reward)", color="w", fontsize=9)
    ax[1].plot(ep, rows[:, 3], color="#88ff88"); ax[1].set_ylabel("FK surprise (mm)", color="#88ff88")
    ax[1].set_title("body-model FK surprise — should DROP as lifelong adapts", color="w", fontsize=9)
    ax[2].plot(ep, np.cumsum(rows[:, 0]) / ep, color="#33ccff"); ax[2].set_ylabel("delivery rate", color="#33ccff")
    ax[2].set_title("cumulative delivery to dreamed goals", color="w", fontsize=9); ax[2].set_xlabel("episode", color="w")
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] metrics curves saved -> {path}")


if __name__ == "__main__":
    main()
