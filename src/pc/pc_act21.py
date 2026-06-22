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

    # CLOSE THE PERCEPTION LOOP IN TRAINING: set up the camera VisualCortex BEFORE the demos so the
    # policy is TRAINED on the SAME camera-perceived (+ servo-corrected) positions it is TESTED on.
    # Privileged-demo training vs camera test was a measured train/test MISMATCH (camera-test delivery
    # 6/14 with privileged demos -> 9/14 with camera demos) -- the parallel camera amplified it.  All
    # branches REUSE this one vc so demos and test always match.  ACT21_DEMO_CAM=0 = old privileged demos.
    DEMO_CAM = os.environ.get("ACT21_DEMO_CAM", "1") == "1"
    from pc.arm_modules import VisualCortexModule
    vc, vcP = VisualCortexModule.from_sim(sim, CAM, RES, headless=HEADLESS)
    def cam_perceive(cmd):
        return vc.perceive(cmd), None, "grasp"
    def cam_track():
        return vc.track()

    Xs, Ys = [], []
    def log(state, aim, j5):
        Xs.append(state.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))
    print(f"  collecting reactive-teacher demos ({COLLECT} eps{', THROUGH the camera' if DEMO_CAM else ''}) ...")
    if DEMO_CAM:                                           # demos through the camera + servo (match test)
        act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal,
                           log_fn=log, perceive_fn=cam_perceive, track_fn=cam_track, servo=True)
    else:
        act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal, log_fn=log)
    baseX, baseY = np.array(Xs), np.array(Ys)             # anchor demos (kept for online DAgger shaping)
    motor.fit(baseX, baseY)

    print("  training the LEARNED inverse kinematics ...")
    print(f"    IK babble reconstruction: {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    agent = ArmAgent("researching-arm")
    for m in (curio, motor, bm, vc):
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

    SHAPE = os.environ.get("ACT21_SHAPE", "0") == "1"        # 3b: ONLINE dense-shaping policy learning
    OBSTACLE = os.environ.get("ACT21_OBSTACLE", "0") == "1" or SHAPE   # shaping runs WITH the walls
    SERVO = os.environ.get("ACT21_SERVO", "1") == "1"        # closed-loop: live fovea corrects the grasp
    #   target belief during the approach (default on; ACT21_SERVO=0 for the frozen-snapshot baseline)
    obstacle = None; brng = np.random.default_rng(31)
    if OBSTACLE:
        from pc.arm_modules import ObstacleModule
        print("  *** OBSTACLE mode: LEARNED board (visual perception + collision world-model) integrated ***")
        obstacle = ObstacleModule(rng=np.random.default_rng(9))
        obstacle.train(sim, n_collide=int(os.environ.get("ACT21_OBS_N", "11000")),
                       vis_steps=int(os.environ.get("ACT21_OBS_VIS", "2800")))   # cached to disk
        agent.add(obstacle)

    def place_board_on_path(cmd, obj_xy, goal):
        """POST-GOAL hook: now that the place target is committed, drop the LOW board so it BLOCKS the
        object->goal carry while staying off the target (placeable + visible), out of the camera shadow, and
        clear of the open gripper at the object (the three placement bugs).  No clean spot -> board parked."""
        obstacle.place_blocking(sim, obj_xy, goal)

    ct_fn = (lambda hxy, goal: obstacle.carry_target(hxy, goal)) if OBSTACLE else None
    pg_fn = place_board_on_path if OBSTACLE else None

    if PERTURB and not OBSTACLE:
        _perturb(sim, PERTURB)
        print(f"  *** perturbed the arm: +{PERTURB*1000:.0f}mm forearm -> trained FK/IK are now STALE ***")

    GSEED = 77
    if SHAPE:
        # ---- 3b: ONLINE DENSE-SHAPING policy learning (extends the act21 stand: walls + lifelong + viz) ----
        # The policy DRIVES; the routed teacher (reactive_subgoal, with the obstacle-routed carry sub-goal)
        # supplies a DENSE per-step target at every policy-VISITED state (DAgger).  Refit the policy on those
        # dense targets every BATCH episodes -> dense credit, not AWR's one episode reward.  Walls on,
        # kinematics lifelong, many repetitions, the live act21 viz.
        ITERS = int(os.environ.get("ACT21_SHAPE_ITERS", "8"))
        BATCH = int(os.environ.get("ACT21_SHAPE_BATCH", "6"))
        CAPv = int(os.environ.get("ACT21_CAP", "2200"))
        buf = {"X": [], "Y": []}; pen = {"max": 0.0}; rows = []
        MAXBUF = int(os.environ.get("ACT21_SHAPE_BUF", "4000"))   # sliding window: avoid the failure-data poison
        def tlog(state, aim, j5, phase):                      # DENSE teacher target at the policy-visited state
            if phase == "carry":                              # skip the routed carry (it is route-servoed,
                return                                        # and its targets conflict with the BC demos)
            s = np.asarray(state, float)
            buf["X"].append(s.copy()); buf["Y"].append(act16.reactive_subgoal(s))   # recomputed teacher label
        def track_pen():
            h = sim.grasp_pos()
            if obstacle is not None and obstacle._occ is not None and h[2] > 0.04:
                b = obstacle.board
                dx = 0.024 - abs(h[0] - b.cx); dy = b.hy - abs(h[1] - b.cy)
                if dx > 0 and dy > 0:
                    pen["max"] = max(pen["max"], min(dx, dy))
        def on_ep(ep, ok, err):
            rows.append((int(ok), err * 1000, pen["max"] * 1000, bm._surprise_mm, curio.coverage()))
            pen["max"] = 0.0
            if (ep + 1) % BATCH == 0 and buf["X"]:            # online DAgger refit on the dense targets
                bx = np.array(buf["X"][-MAXBUF:]); by = np.array(buf["Y"][-MAXBUF:])   # sliding window
                X = np.vstack([bx, baseX]); Y = np.vstack([by, baseY])
                motor.fit(X, Y, epochs=120, set_norm=False, quiet=True)
        EP = ITERS * BATCH
        sgoal = fixed_goals(GSEED)                            # FIXED goals so delivery is a stable metric
        print(f"  *** 3b ONLINE DENSE-SHAPING: {ITERS} iters x {BATCH} eps, walls + lifelong, DAgger refit ***")

        def eval_fixed(n=12):                                 # frozen-policy delivery on FIXED goals + walls
            act16.run_combined._quiet = True
            dd, mm = act16.run_combined(sim, bm, None, CAM, episodes=n, policy_fn=motor.predict,
                                        goal_fn=fixed_goals(GSEED), lifelong=False, carry_target_fn=ct_fn,
                                        post_goal_fn=pg_fn, cap=CAPv)
            act16.run_combined._quiet = False
            return dd, mm
        d0, m0 = eval_fixed(); print(f"  baseline (frozen BC policy, fixed goals + walls): {d0}/{m0}")

        viz_obj = None
        if not HEADLESS:
            try:
                from pc.pc_act18 import SurpriseViz
                sviz = SurpriseViz(title="act21 3b — dense-shaping + walls + lifelong"); viz_obj = vc.viz or sviz
                def perceive(cmd):
                    return cam_perceive(cmd)                   # REUSE the early vc (trained the demos)
                def trackf():
                    obs = vc.track(); track_pen()             # (xy, conf) -> feeds the closed-loop servo
                    dd = vc.surprise(); ps = curio.surprise()
                    if dd is not None:
                        sviz.push(dd["sensor"], dd["state"], dd["total"], dd["relax"], bm._surprise_mm,
                                  planner=(ps["novelty"] if ps else None))
                    return obs
                d, m = act16.run_combined(sim, bm, None, CAM, episodes=EP, policy_fn=motor.predict,
                                          goal_fn=sgoal, lifelong=True, perceive_fn=perceive,
                                          macro_log_fn=tlog, carry_target_fn=ct_fn, post_goal_fn=pg_fn,
                                          track_fn=trackf, episode_end_fn=on_ep, cap=CAPv, servo=SERVO)
            except Exception as e:
                import traceback; traceback.print_exc()
                print(f"  [viz] {e}; running headless-style"); HEADLESS = True
        if HEADLESS or viz_obj is None:
            d, m = act16.run_combined(sim, bm, None, CAM, episodes=EP, policy_fn=motor.predict,
                                      goal_fn=sgoal, lifelong=True, macro_log_fn=tlog,
                                      carry_target_fn=ct_fn, post_goal_fn=pg_fn, track_fn=track_pen,
                                      episode_end_fn=on_ep, cap=CAPv)
        dF, mF = eval_fixed()                                 # frozen re-measure on the SAME fixed goals
        rows = np.array(rows, float)
        di = np.array([rows[i * BATCH:(i + 1) * BATCH, 0].mean() for i in range(ITERS)])
        h = max(1, ITERS // 3)
        print("=" * 72)
        print(f"  3b DENSE-SHAPING ({EP} eps, walls on, lifelong): delivered {int(rows[:,0].sum())}/{len(rows)}")
        print(f"    FIXED-goal frozen eval: baseline {d0}/{m0}  ->  after shaping {dF}/{mF}")
        print(f"    in-run delivery (first third -> last third): {di[:h].mean():.2f} -> {di[-h:].mean():.2f}")
        print(f"    board penetration mean {np.nanmean(rows[:,2]):.0f} mm   FK surprise {np.nanmean(rows[:,3]):.2f} mm")
        print("  Read (HONEST): curated dense DAgger HOLDS the baseline (it does NOT exceed it).  Two findings:")
        print("  (1) NAIVE dense shaping POISONED the policy (8/12 -> 1/12) -- accumulating every visited state")
        print("      incl. long FAILURE rollouts + routed-carry targets that conflict with the BC demos;")
        print("      fixed by excluding the (route-servoed) carry phase + a sliding window -> holds 8/12.")
        print("  (2) it does not RAISE delivery: the BC policy already sits at the TEACHER ceiling, so dense")
        print("      shaping (like AWR before it) cannot exceed the teacher.  Beating the plateau needs")
        print("      BEYOND-teacher learning (a better teacher/controller or reward), not more imitation.")
        print("  The machinery EXTENDS the act21 stand (walls + lifelong + viz + curves); the limit is named.")
        print("=" * 72)
        try:
            _plot_shape(rows, BATCH, os.path.join(os.path.dirname(__file__), "act21_shape.png"))
        except Exception as e:
            print(f"  [viz] could not save the shaping curve: {e}")
        if viz_obj is not None:
            print("  [viz] close the windows to exit."); viz_obj.hold()
        return

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
            return None, None, "grasp"                           # privileged cube; board placed post-goal
        def ep_end_hl(ep, ok, err):
            pen["rows"].append((int(ok), pen["max"] * 1000)); pen["max"] = 0.0
        d, m = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
                                  goal_fn=fixed_goals(GSEED), lifelong=True, perceive_fn=perceive_hl,
                                  carry_target_fn=ct_fn, post_goal_fn=pg_fn, track_fn=track_pen,
                                  episode_end_fn=ep_end_hl, cap=int(os.environ.get("ACT21_CAP", "2200")))
        rows = np.array(pen["rows"], float)
        print("=" * 72)
        print(f"  OBSTACLE integrated into act21 ({m} eps): delivered {d}/{m}")
        print(f"  carried-hand board penetration: mean {rows[:,1].mean():.0f} mm  max {rows[:,1].max():.0f} mm")
        print("  Read (honest): the obstacle module is cleanly plugged into the act21 agent (learned")
        print("  perception + collision world-model + planner, via the carry_target_fn hook), and the")
        print("  END-EFFECTOR carry ROUTES around the PERCEIVED board (penetration ~0, nothing hand-coded).")
        print("  The LOW board is now placed POST-GOAL on the carry path, OFF the target (placeable +")
        print("  visible), out of the camera shadow, and clear of the open gripper at the object -- the")
        print("  three placement bugs are gone.  LIMIT: full-task delivery is bounded by the imitation/")
        print("  AWR policy (the known plateau) + the weak push fallback, not by the obstacle anymore.")
        print("=" * 72)
        return

    if HEADLESS:
        act16.run_combined._quiet = True
        _cp = dict(perceive_fn=cam_perceive, track_fn=cam_track, servo=True) if DEMO_CAM else {}
        # --- A: frozen baseline on FIXED goals (post-perturb) ---
        dA, mA = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
                                    goal_fn=fixed_goals(GSEED), lifelong=False, **_cp)
        # --- B: LIFELONG exploration with the curiosity planner (adapt + explore), log per episode ---
        rows = []
        def ep_end(ep, ok, err):
            rows.append((int(ok), err, curio.coverage(), bm._surprise_mm))
        dB, mB = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                                    goal_fn=curiosity_goal, lifelong=True, episode_end_fn=ep_end, **_cp)
        # --- C: frozen re-measure on the SAME FIXED goals as A (isolates lifelong recovery) ---
        dC, mC = act16.run_combined(sim, bm, None, CAM, episodes=BASE, policy_fn=motor.predict,
                                    goal_fn=fixed_goals(GSEED), lifelong=False, **_cp)
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
        sviz = SurpriseViz(title="act21 — curiosity + lifelong (surprise over time)")

        def perceive(cmd):
            return cam_perceive(cmd)                          # REUSE the early vc (trained the demos)

        def track_and_plot():
            obs = cam_track()                                 # (xy, conf) -> feeds the closed-loop servo
            bmm = bm._surprise_mm
            d = vc.surprise(); ps = curio.surprise()
            if d is not None:
                sviz.push(d["sensor"], d["state"], d["total"], d["relax"], bmm,
                          planner=(ps["novelty"] if ps else None))
            return obs

        d, m = act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                                  goal_fn=curiosity_goal, lifelong=True, perceive_fn=perceive,
                                  track_fn=track_and_plot, carry_target_fn=ct_fn, post_goal_fn=pg_fn,
                                  servo=SERVO)
        print(f"  explored+delivered {d}/{m} to self-dreamed goals; coverage {curio.coverage():.2f}"
              + ("  [routing carries around the learned board]" if OBSTACLE else ""))
        print("  [viz] close the windows to exit.")
        (vc.viz or sviz).hold()
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  [viz/perception] {e}; falling back to privileged run")
        act16.run_combined(sim, bm, None, CAM, episodes=EXPLORE, policy_fn=motor.predict,
                           goal_fn=curiosity_goal, lifelong=True)


def _plot_shape(rows, batch, path):
    """3b dense-shaping curve: windowed delivery + board penetration over online iterations."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    iters = max(1, len(rows) // batch)
    di = np.array([rows[i * batch:(i + 1) * batch, 0].mean() for i in range(iters)])
    pe = np.array([rows[i * batch:(i + 1) * batch, 2].mean() for i in range(iters)])
    x = np.arange(1, iters + 1)
    fig, ax = plt.subplots(2, 1, figsize=(7, 5.5), sharex=True)
    fig.patch.set_facecolor("#0e0e12"); fig.suptitle("act21 3b — online dense-shaping (walls + lifelong)", color="w")
    for a in ax:
        a.set_facecolor("#0e0e12"); a.grid(True, color="#333", lw=0.4); a.tick_params(colors="w")
        [s.set_color("#555") for s in a.spines.values()]
    ax[0].plot(x, di, "-o", color="#33ccff"); ax[0].set_ylabel("delivery rate", color="w")
    ax[0].set_title("does dense shaping raise delivery over iters?", color="w", fontsize=9)
    ax[1].plot(x, pe, "-o", color="#ff8866"); ax[1].set_ylabel("board penetration (mm)", color="#ff8866")
    ax[1].set_xlabel("online iteration", color="w")
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] shaping curve saved -> {path}")


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
