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
    baseX, baseY = np.array(Xs), np.array(Ys)             # anchor demos (kept for online DAgger shaping)
    motor.fit(baseX, baseY)

    print("  training the LEARNED inverse kinematics ...")
    print(f"    IK babble reconstruction: {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    # RECOVERY-DAgger polish (default ON): the BC policy occasionally grasps beside the cube, RE-grasps, then
    # HANGS with it instead of carrying -- those recovery states are rare in the teacher demos, so plain BC
    # hangs there.  Run the policy PRIVILEGED, let the teacher label the policy-VISITED states (incl the
    # carry/hang phase = "carry to goal"), refit every RBATCH eps.  In-distribution polish so the explore/viz
    # policy no longer hangs (headless: privileged delivery ~7/12 -> ~11/12).  Disable with ACT21_RECOVER=0.
    if os.environ.get("ACT21_RECOVER", "1") == "1" and os.environ.get("ACT21_SHAPE", "0") != "1":  # (SHAPE
        from pc.arm_modules.planner import LO as _LO, HI as _HI, SPAN as _SPAN          # does its own DAgger)
        RN = int(os.environ.get("ACT21_RECOVER_EPS", "30")); RBATCH = 6; rbuf = {"X": [], "Y": []}
        def _fg(seed):                                        # FIXED goal sequence (matches the explore A/C eval)
            r = np.random.default_rng(seed)
            return lambda cmd, obj: r.uniform(_LO + 0.15 * _SPAN, _HI - 0.15 * _SPAN)
        def _rlog(state, aim, j5, phase):
            s = np.asarray(state, float); rbuf["X"].append(s.copy()); rbuf["Y"].append(act16.reactive_subgoal(s))
        def _rfit(ep, ok, err):
            if (ep + 1) % RBATCH == 0 and rbuf["X"]:          # sliding-window DAgger refit (+ anchor BC demos)
                bx = np.array(rbuf["X"][-4000:]); by = np.array(rbuf["Y"][-4000:])
                motor.fit(np.vstack([bx, baseX]), np.vstack([by, baseY]), epochs=120, set_norm=False, quiet=True)
        act16.run_combined._quiet = True
        d0, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=12, policy_fn=motor.predict,
                                   goal_fn=_fg(77), lifelong=False)               # eval on FIXED goals
        act16.run_combined(sim, bm.body, None, CAM, episodes=RN, policy_fn=motor.predict,
                           macro_log_fn=_rlog, episode_end_fn=_rfit, lifelong=False)   # train on DIVERSE goals
        d1, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=12, policy_fn=motor.predict,
                                   goal_fn=_fg(77), lifelong=False)
        act16.run_combined._quiet = False
        print(f"  recovery-DAgger polish ({RN} eps, teacher labels visited states incl carry): "
              f"frozen FIXED-goal delivery {d0}/12 -> {d1}/12")

    agent = ArmAgent("researching-arm")
    for m in (curio, motor, bm):
        agent.add(m)
    print(agent.summary())

    if os.environ.get("ACT21_STEER", "0") == "1":
        run_command_steering(sim, bm, motor, CAM, RES, HEADLESS)
        return

    from pc.arm_modules.planner import LO, HI, SPAN

    def curiosity_goal(cmd, obj_xy):
        return curio.dream()                                # the planner dreams its OWN goal (novelty)

    def fixed_goals(seed):
        """A FIXED random-goal sequence (identical for a given seed) so the A vs C delivery
        comparison isolates the lifelong recovery — NOT the curiosity goal-difficulty drift."""
        r = np.random.default_rng(seed)
        return lambda cmd, obj: r.uniform(LO + 0.15 * SPAN, HI - 0.15 * SPAN)

    SHAPE = os.environ.get("ACT21_SHAPE", "0") == "1"        # 3b: ONLINE dense-shaping policy learning
    OBSTACLE = os.environ.get("ACT21_OBSTACLE", "1" if SHAPE else "0") == "1"   # SHAPE defaults to walls ON
    #   (the 3b line); set ACT21_OBSTACLE=0 for the RECOVERY-DAgger run -- walls OFF + carry states INCLUDED
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
            if phase == "carry" and ct_fn is not None:        # skip ONLY the obstacle-ROUTED carry (route-
                return                                        # servoed, conflicts with BC).  Walls OFF -> INCLUDE
            s = np.asarray(state, float)                      # carry: trains the "grasped-but-HANGS" recovery
            buf["X"].append(s.copy()); buf["Y"].append(act16.reactive_subgoal(s))   # (teacher label = carry to goal)
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
                from pc.arm_modules import VisualCortexModule
                vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=False); agent.add(vc)
                sviz = SurpriseViz(title="act21 3b — dense-shaping + walls + lifelong"); viz_obj = vc.viz or sviz
                def perceive(cmd):
                    return vc.perceive(cmd), None, "grasp"
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
        print(f"  DENSE-SHAPING ({EP} eps, walls {'on' if OBSTACLE else 'off'}, lifelong): "
              f"delivered {int(rows[:,0].sum())}/{len(rows)}")
        print(f"    FIXED-goal frozen eval: baseline {d0}/{m0}  ->  after shaping {dF}/{mF}")
        print(f"    in-run delivery (first third -> last third): {di[:h].mean():.2f} -> {di[-h:].mean():.2f}")
        if OBSTACLE:
            print(f"    board penetration mean {np.nanmean(rows[:,2]):.0f} mm   FK surprise {np.nanmean(rows[:,3]):.2f} mm")
            print("  Read (HONEST, walls/3b): curated dense DAgger HOLDS the baseline (does NOT exceed it).")
            print("  (1) NAIVE dense shaping POISONED the policy (8/12 -> 1/12) -- accumulating every visited")
            print("      state incl. long FAILURE rollouts + routed-carry targets that conflict with the BC")
            print("      demos; fixed by excluding the (route-servoed) carry phase + a sliding window -> 8/12.")
            print("  (2) it does not RAISE delivery: the BC policy already sits at the TEACHER ceiling, so dense")
            print("      shaping (like AWR) cannot exceed the teacher.  Beating it needs BEYOND-teacher learning.")
        else:
            print("  Read (HONEST, RECOVERY-DAgger, walls off): INCLUDING the carry/recovery states (the policy")
            print("  sometimes grasps then HANGS instead of carrying) lets the teacher label those policy-VISITED")
            print("  states (label = carry to goal).  Those states are rare in the BC demos -> the BC policy hangs")
            print("  there; DAgger on them RAISES the frozen delivery (this is in-distribution recovery, not")
            print("  beyond-teacher).  This is the 'last polish' for the wrist-on misses (re-grasp + carry).")
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
            return vc.perceive(cmd), None, "grasp"            # board is placed POST-GOAL (on the carry path)

        def track_and_plot():
            obs = vc.track()                                  # (xy, conf) -> feeds the closed-loop servo
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


class CommandState:
    """GUI-free state of a COMMAND to the net: which OBJECT (an abstract code -- the net localizes it
    itself via the fovea/selection head), which ACTION (grasp/push), which named TARGET marker.  Exposes
    the cmd_fn/force_fn/goal_fn hooks run_combined consumes, so the same state drives both the graphical
    panel and the headless self-test.  Targets are the fixed mocap markers target_sel_1/_2/_3; goal_fn
    returns the SELECTED marker's table xy.  The target is NEVER re-placed automatically -- only by the
    user (selecting another marker, or 'Ziel neu' = place_selected_random)."""

    OBJECTS = [("rot", "obj_red"), ("grün", "obj_green"), ("blau", "obj_blue")]
    MARKERS = ["target_sel_1", "target_sel_2", "target_sel_3"]   # fixed, selectable named goals

    def __init__(self, sim):
        self.sim = sim
        self.obj = "obj_red"          # commanded object (abstract code)
        self.action = "grasp"         # "grasp" or "push"
        self.target_idx = 0           # which named marker is the goal
        self.go = False               # the user pressed "Ausführen"
        self.exit = False             # the user pressed "Beenden"

    def _mocap(self, name):
        return self.sim.m.body_mocapid[mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, name)]

    def marker_xy(self, idx):
        return self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2].copy()

    def set_marker_xy(self, idx, xy):
        self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2] = xy

    def sync_active(self):
        """Keep the BRIGHT active-goal disk (target_marker, which run_combined snaps to the committed
        goal each episode) sitting on the SELECTED marker, so the goal never appears to jump/reset --
        it only moves on a user action (selecting another marker or pressing Ziel neu)."""
        self.sim.d.mocap_pos[self._mocap("target_marker")][:2] = self.marker_xy(self.target_idx)
        mujoco.mj_forward(self.sim.m, self.sim.d)

    def place_selected_random(self, rng):
        """Ziel neu: re-place the SELECTED marker at a fresh random VALID table position (clear of the
        objects, off the base), between episodes, on demand.  Nothing re-places the target otherwise."""
        from pc.pc_act14 import _rand_xy
        from pc.pc_act16 import BASE_CLEAR
        objs = [nm for _l, nm in self.OBJECTS]
        p = _rand_xy(rng)
        for _ in range(200):
            if float(np.linalg.norm(p)) >= BASE_CLEAR and all(
                    float(np.linalg.norm(p - self.sim.obj_pos(o)[:2])) > 0.05 for o in objs):
                break
            p = _rand_xy(rng)
        self.set_marker_xy(self.target_idx, p); self.sync_active()

    # ---- run_combined hooks (the command, fed to the net) ----
    def cmd_fn(self, ep):
        return self.obj                                   # abstract object code; net FINDS it via perception

    def force_fn(self, cmd):
        return self.action

    def goal_fn(self, cmd, obj_xy):
        return self.marker_xy(self.target_idx)            # the selected named target marker

    def label(self):
        col = next(c for c, nm in self.OBJECTS if nm == self.obj)
        act = "Greifen" if self.action == "grasp" else "Schieben"
        return f"{col} | {act} | Ziel {self.target_idx + 1}"


class CommandPanel:
    """Graphical command interface in ONE window: the arm-execution camera (left), the net's FOVEA view
    (real camera + the foveated window + the HEX cells the net sees) and the PC-module SURPRISE curves
    (right) -- so everything is on one screen -- plus the command buttons (object colour, named target,
    grasp/push, 'Ziel neu', Ausführen, Beenden).  Doubles as the run_combined `viz` (update/hold) for the
    arm view, hosts an embedded HexFoveaViz (self.fov_viz) + SurpriseViz (self.surp_viz) on its own axes."""

    OBJ_COL = {"obj_red": "#d23030", "obj_green": "#2fae40", "obj_blue": "#3358d2"}

    def __init__(self, state, cam, res, rng=None):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button
        from pc.pc_act18 import HexFoveaViz, SurpriseViz
        self.plt = plt; self.state = state; self._cam = cam
        self._rng = rng if rng is not None else np.random.default_rng(0); plt.ion()
        # default sized to fit a 1920x1200 @125% screen (logical ~1536x960); env ACT21_FIGSIZE to change
        fw, fh = (float(x) for x in os.environ.get("ACT21_FIGSIZE", "12.0,7.5").split(","))
        self.fig = plt.figure(figsize=(fw, fh)); self.fig.patch.set_facecolor("#0e0e12")
        self.fig.canvas.manager.set_window_title("Befehls-Schnittstelle — Netz steuern")
        # --- plot band (top): arm camera | fovea (real + hex cells) | surprise curves ---
        self.axCam = self.fig.add_axes([0.035, 0.30, 0.38, 0.63]); self.axCam.axis("off")
        self.axCam.set_title(f"Arm — {cam} Kamera", color="w", fontsize=10)
        self.imCam = self.axCam.imshow(np.zeros((res, res, 3), np.uint8))
        axFovI = self.fig.add_axes([0.44, 0.62, 0.24, 0.31])
        axFovC = self.fig.add_axes([0.44, 0.30, 0.21, 0.26])
        self.fov_viz = HexFoveaViz(cam, res, axI=axFovI, axC=axFovC)        # net's fovea, in THIS window
        axE = self.fig.add_axes([0.715, 0.635, 0.27, 0.295])
        axR = self.fig.add_axes([0.715, 0.30, 0.27, 0.235])
        self.surp_viz = SurpriseViz(axE=axE, axR=axR, show_readout=False)   # PC-module surprise, in THIS window
        self.status = self.fig.text(0.5, 0.255, "", ha="center", color="w", fontsize=11, family="monospace")
        self.live = self.fig.text(0.225, 0.285, "", ha="center", color="#9fb4c8", fontsize=8.5,
                                  family="monospace")        # live arm-execution status under the camera
        # --- buttons (bottom): two rows ---
        self._obj_btns = {}; self._tgt_btns = {}
        for i, (lbl, nm) in enumerate(state.OBJECTS):       # object colour buttons
            ax = self.fig.add_axes([0.035 + 0.13 * i, 0.150, 0.12, 0.055])
            b = Button(ax, lbl.capitalize(), color=self.OBJ_COL[nm], hovercolor=self.OBJ_COL[nm])
            b.on_clicked(lambda _e, nm=nm: self._set_obj(nm)); self._obj_btns[nm] = b
        for i in range(len(state.MARKERS)):                 # named target buttons
            ax = self.fig.add_axes([0.55 + 0.13 * i, 0.150, 0.12, 0.055])
            b = Button(ax, f"Ziel {i + 1}", color="#3a3a44", hovercolor="#55556a")
            b.on_clicked(lambda _e, i=i: self._set_tgt(i)); self._tgt_btns[i] = b
        axA = self.fig.add_axes([0.035, 0.04, 0.20, 0.07])    # action toggle + place-target
        self.bA = Button(axA, "Modus: Greifen", color="#555", hovercolor="#777"); self.bA.on_clicked(self._toggle)
        axP = self.fig.add_axes([0.25, 0.04, 0.20, 0.07])
        self.bP = Button(axP, "Ziel neu (Zufall)", color="#7a5cae", hovercolor="#9a78d0"); self.bP.on_clicked(self._place)
        axG = self.fig.add_axes([0.58, 0.04, 0.18, 0.07])     # go + exit
        self.bG = Button(axG, "Ausführen", color="#1f8a5b", hovercolor="#27a96f"); self.bG.on_clicked(self._go)
        axX = self.fig.add_axes([0.77, 0.04, 0.18, 0.07])
        self.bX = Button(axX, "Beenden", color="#8a3030", hovercolor="#a94040"); self.bX.on_clicked(self._exit)
        self.fig.canvas.mpl_connect("close_event", lambda _e: setattr(self.state, "exit", True))
        self._refresh()

    def _set_obj(self, nm): self.state.obj = nm; self._refresh()
    def _go(self, _e): self.state.go = True
    def _exit(self, _e): self.state.exit = True

    def _set_tgt(self, i):
        self.state.target_idx = i; self.state.sync_active()   # bright goal disk follows the selection (no jump)
        self.update(self.state.sim.render(self._cam), f"Ziel {i + 1} gewählt"); self._refresh()

    def _place(self, _e):
        self.state.place_selected_random(self._rng)           # re-randomize the SELECTED target on demand
        self.update(self.state.sim.render(self._cam), f"Ziel {self.state.target_idx + 1} neu platziert")
        self._refresh()

    def _toggle(self, _e):
        self.state.action = "push" if self.state.action == "grasp" else "grasp"
        self.bA.label.set_text("Modus: " + ("Schieben" if self.state.action == "push" else "Greifen"))
        self._refresh()

    def _refresh(self):
        labels = {nm: lbl.capitalize() for lbl, nm in self.state.OBJECTS}
        for nm, b in self._obj_btns.items():                # highlight selected: marker + bright target colour
            b.label.set_text(("● " if nm == self.state.obj else "") + labels[nm])
        for i, b in self._tgt_btns.items():
            b.color = "#c050c0" if i == self.state.target_idx else "#3a3a44"; b.ax.set_facecolor(b.color)
        self.status.set_text("Befehl:  " + self.state.label())
        self.fig.canvas.draw_idle()

    # ---- run_combined viz interface ----
    def update(self, frame, txt=""):
        self.imCam.set_data(frame)
        if txt:
            self.live.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def wait(self):
        """Pump the GUI event loop until the user presses Ausführen or Beenden."""
        while not (self.state.go or self.state.exit):
            self.plt.pause(0.05)
        return "exit" if self.state.exit else "go"

    def hold(self):
        self.plt.ioff(); self.plt.show()


def _steer_perceive(vc):
    """perceive_fn for steering: the net LOCALIZES the commanded object itself (fovea + selection head);
    mode is left to the action toggle (force_fn), target stays the chosen marker (given, not perceived)."""
    def perceive(cmd):
        return vc.perceive(cmd), None, None
    return perceive


def run_command_steering(sim, bm, motor, CAM, RES, HEADLESS):
    """A clean interface to COMMAND the net: choose object (colour) + target (named marker) + action,
    and the net localizes the object via its OWN perception (VisualCortexModule fovea/selection head)
    then delivers it.  ONE graphical window (arm camera + the net's fovea view + the PC-module surprise
    curves + the buttons) when a display is available; a scripted self-test when headless."""
    import pc.pc_act16 as act16
    from pc.arm_modules import VisualCortexModule
    state = CommandState(sim)

    if HEADLESS:                                              # headless self-test of the full command->net path
        print("  building the net's perception (fovea + selection head) ...")
        vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=True)
        perceive = _steer_perceive(vc)
        print("\n" + "=" * 72)
        print("  COMMAND STEERING — headless self-test (no GUI): cycle objects to named targets via the NET")
        print("=" * 72)
        act16.PERSIST = False                                 # fair eval: a FRESH scatter per episode
        objs = [nm for _l, nm in state.OBJECTS]
        d, m = act16.run_combined(sim, bm, None, CAM, episodes=12,
                                  cmd_fixed=lambda ep: objs[ep % 3], force=state.force_fn,
                                  goal_fn=lambda c, o: state.marker_xy(0), perceive_fn=perceive,
                                  track_fn=vc.track, policy_fn=motor.predict, lifelong=True,
                                  tol=act16.TOL, servo=True)
        print(f"  command-steering self-test (12 eps, object commanded -> net localizes -> deliver): {d}/{m}")
        return

    os.environ["ACT16_PERSIST"] = "1"; act16.PERSIST = True   # GUI: scene persists between commands
    act16.run_combined._quiet = True                          # the steering loop OWNS the viz lifecycle (so
    #   run_combined does NOT block on viz.hold() / print after each command -> the buttons keep responding)
    print("\n" + "=" * 72)
    print("  COMMAND STEERING — grafische Schnittstelle (Kamera + Fovea + Surprise-Kurven in EINEM Fenster)")
    print("  Objekt (Farbe) + Ziel (Marker) + Modus + 'Ziel neu' (Zufalls-Ziel), dann 'Ausführen'.")
    print("=" * 72)
    panel = CommandPanel(state, CAM, RES, rng=np.random.default_rng(7))
    panel.update(sim.render(CAM), "Wahrnehmung des Netzes wird trainiert ...")
    # build the perception with the fovea drawing INTO the panel (so the fovea view is in the same window)
    vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=True, viz=panel.fov_viz)
    perceive = _steer_perceive(vc)
    act16.run_combined(sim, bm, None, CAM, episodes=0)        # place the scene ONCE (scatter, 0 episodes)
    state.sync_active()                                       # bright goal disk starts on the selected marker
    panel.update(sim.render(CAM), "bereit — Befehl wählen und Ausführen")   # the scene that WILL be used

    def track_and_plot():                                     # one follow frame + push the surprise curves
        obs = vc.track()
        s = vc.surprise()
        if s is not None:
            panel.surp_viz.push(s["sensor"], s["state"], s["total"], s["relax"],
                                getattr(bm, "_surprise_mm", None))
        return obs

    res = {}
    def ep_end(ep, ok, err): res["ok"] = bool(ok); res["err"] = float(err)

    ep = 0
    while panel.wait() != "exit":
        state.go = False
        print(f"  [Befehl {ep}] {state.label()} -> Netz lokalisiert {state.obj} und liefert ...")
        # rescatter=False: reuse the scene already on the table (placed ONCE at startup, kept across
        # commands) so the positions the user SEES are the ones executed.
        act16.run_combined(sim, bm, panel, CAM, episodes=1, cmd_fixed=state.cmd_fn, force=state.force_fn,
                           goal_fn=state.goal_fn, perceive_fn=perceive, track_fn=track_and_plot,
                           policy_fn=motor.predict, lifelong=True, tol=act16.TOL, servo=True,
                           rescatter=False, episode_end_fn=ep_end)
        ok = res.get("ok", False); err_mm = res.get("err", float("nan")) * 1000.0
        line = f"[Befehl {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand zum Ziel {err_mm:.0f} mm"
        print("  " + line)
        panel.update(sim.render(CAM), line)
        ep += 1
    act16.run_combined._quiet = False
    print("  Steering beendet.")
    panel.hold()


if __name__ == "__main__":
    main()
