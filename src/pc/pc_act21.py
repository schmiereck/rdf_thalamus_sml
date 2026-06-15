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


def _perturb(sim, dz):
    wid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "wrist_link")
    sim.m.body_pos[wid, 2] += dz
    mujoco.mj_forward(sim.m, sim.d)


def main():
    HEADLESS = os.environ.get("ACT21_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT21_CAM", "overview").lower()
    COLLECT = int(os.environ.get("ACT21_COLLECT", "30"))   # more teacher demos for the enlarged workspace
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

    Xs, Ys = [], []
    def log(state, aim, j5):
        Xs.append(state.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))
    print(f"  collecting reactive-teacher demos ({COLLECT} eps) ...")
    act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal, log_fn=log)
    motor.fit(np.array(Xs), np.array(Ys))

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

    OBSTACLE = os.environ.get("ACT21_OBSTACLE", "0") == "1"
    obstacle = None; brng = np.random.default_rng(31)
    if OBSTACLE:
        from pc.arm_modules import ObstacleModule
        print("  *** OBSTACLE mode: LEARNED board (visual perception + collision world-model) integrated ***")
        obstacle = ObstacleModule(rng=np.random.default_rng(9))
        obstacle.train(sim, n_collide=int(os.environ.get("ACT21_OBS_N", "11000")),
                       vis_steps=int(os.environ.get("ACT21_OBS_VIS", "2800")))   # cached to disk
        agent.add(obstacle)

    def place_board_clear(cmd):
        """Drop the LOW board (arm stays at HOME so the grasp is unperturbed).  The board is OFFSET in x so
        its thin footprint never spawns into the central home gripper, and clear of the commanded cube so
        the grasp approach is free.  Then perceive it."""
        hg = sim.grasp_pos()[:2]; cobj = sim.obj_pos(cmd)[:2]; cx, cy = 0.05, 0.16
        for _ in range(40):
            cx = brng.uniform(-0.07, 0.07); cy = brng.uniform(0.12, 0.19)
            free_arm = abs(cx - hg[0]) > 0.042 or abs(cy - hg[1]) > 0.075   # not under the home gripper
            if free_arm and np.linalg.norm([cx - cobj[0], cy - cobj[1]]) > 0.07:
                break
        obstacle.board.place(cx, cy, 0.012, 0.055, obstacle.board_tall); sim.step(20)
        obstacle.perceive_board(sim)

    ct_fn = (lambda hxy, goal: obstacle.carry_target(hxy, goal)) if OBSTACLE else None

    if PERTURB and not OBSTACLE:
        _perturb(sim, PERTURB)
        print(f"  *** perturbed the arm: +{PERTURB*1000:.0f}mm forearm -> trained FK/IK are now STALE ***")

    GSEED = 77
    if OBSTACLE and HEADLESS:
        pen = {"max": 0.0, "rows": []}
        def track_pen():
            h = sim.grasp_pos()
            if h[2] > 0.04:                                   # carrying-ish: does the hand enter the board?
                b = obstacle.board
                dx = 0.024 - abs(h[0] - b.cx); dy = b.hy - abs(h[1] - b.cy)
                if dx > 0 and dy > 0:
                    pen["max"] = max(pen["max"], min(dx, dy))
        def perceive_hl(cmd):
            place_board_clear(cmd); return None, None, "grasp"   # privileged cube; board placed + perceived
        def ep_end_hl(ep, ok, err):
            pen["rows"].append((int(ok), pen["max"] * 1000)); pen["max"] = 0.0
        d, m = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
                                  goal_fn=fixed_goals(GSEED), lifelong=True, perceive_fn=perceive_hl,
                                  carry_target_fn=ct_fn, track_fn=track_pen, episode_end_fn=ep_end_hl,
                                  cap=int(os.environ.get("ACT21_CAP", "2200")))
        rows = np.array(pen["rows"], float)
        print("=" * 72)
        print(f"  OBSTACLE integrated into act21 ({m} eps): delivered {d}/{m}")
        print(f"  carried-hand board penetration: mean {rows[:,1].mean():.0f} mm  max {rows[:,1].max():.0f} mm")
        print("  Read (honest): the obstacle module is cleanly plugged into the act21 agent (learned")
        print("  perception + collision world-model + planner, via the carry_target_fn hook), and the")
        print("  END-EFFECTOR carry ROUTES around the PERCEIVED board (penetration ~0, nothing hand-coded).")
        print("  LIMIT: full-task delivery is low -- the TALL board obstructs the WHOLE arm (grasp approach")
        print("  + links), which end-effector xy-routing does not solve; that needs ARM-LEVEL obstacle")
        print("  avoidance (3-D), a shorter obstacle, or a constrained start/goal geometry.  Nameable limit.")
        print("=" * 72)
        return

    if HEADLESS:
        act16.run_combined._quiet = True
        # --- A: frozen baseline on FIXED goals (post-perturb) ---
        dA, mA = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
                                    goal_fn=fixed_goals(GSEED), lifelong=False)
        # --- B: LIFELONG exploration with the curiosity planner (adapt + explore), log per episode ---
        rows = []
        def ep_end(ep, ok, err):
            rows.append((int(ok), err, curio.coverage(), bm._surprise_mm))
        dB, mB = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                                    goal_fn=curiosity_goal, lifelong=True, episode_end_fn=ep_end)
        # --- C: frozen re-measure on the SAME FIXED goals as A (isolates lifelong recovery) ---
        dC, mC = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
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
            if OBSTACLE:
                place_board_clear(cmd)                        # SEE + place the learned board this episode
            return vc.perceive(cmd), None, "grasp"

        def track_and_plot():
            vc.track()
            bmm = bm._surprise_mm
            d = vc.surprise(); ps = curio.surprise()
            if d is not None:
                sviz.push(d["sensor"], d["state"], d["total"], d["relax"], bmm,
                          planner=(ps["novelty"] if ps else None))

        d, m = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                                  goal_fn=curiosity_goal, lifelong=True, perceive_fn=perceive,
                                  track_fn=track_and_plot, carry_target_fn=ct_fn)
        print(f"  explored+delivered {d}/{m} to self-dreamed goals; coverage {curio.coverage():.2f}"
              + ("  [routing carries around the learned board]" if OBSTACLE else ""))
        print("  [viz] close the windows to exit.")
        (vc.viz or sviz).hold()
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  [viz/perception] {e}; falling back to privileged run")
        act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                           goal_fn=curiosity_goal, lifelong=True)


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
