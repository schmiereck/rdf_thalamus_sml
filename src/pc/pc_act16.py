r"""
pc_act16.py — manipulation with CLAWS: GRASP first, PUSH as fallback (user's idea).

Per the user's live observation: with the curved CLAWS the arm sometimes GRASPS the cube and
carries it well; when it misses, it should fall back to PUSHing the cube from behind with the
(slightly-closed) claws.  So this combines both and we can later see which the net learns better:
  1. GRASP:  open claws above the cube -> lower -> close -> lift.  If the cube came up -> CARRY
     it to the target and place it.
  2. PUSH (fallback, if the grasp missed): pre-closed claws approach from behind and push the
     cube to the target by genuine contact (the inward claw tips cup it).
The reach uses the LEARNED 3-D kinematics to the `contact` site (claw notch).  A visible target
marker (mocap disk) is placed on the table.  Perception is privileged sim state (camera = act15).

  ACT16_HEADLESS=1   metrics over episodes     ACT16_TARGET=obj_red|...   commanded cube
  ACT16_MODE=both|grasp|push                    (default both = grasp-then-push)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, HOME, _rand_xy, CamViz, REACH_XY

J5_OPEN, J5_GRIP, J5_PUSH = 1.8, 0.0, 0.55     # open / fully-closed (grip) / partly-open
#                              (push: claws spread ~40mm to contact a wide block's face at 2 points)
OBJS = ["obj_red", "obj_green", "obj_blue"]
CUBE_HALF = np.array([0.012, 0.012, 0.012])     # graspable cube
WIDE_HALF = np.array([0.024, 0.024, 0.010])     # wide SQUARE block: too wide to grasp -> push
#                                                 (square so the push direction doesn't matter)
OVER_Z, GRASP_Z, CARRY_Z, PUSH_Z = 0.06, 0.014, 0.055, 0.016
PUSH_LIFT_Z = 0.07                              # raise the claws to move behind an object (clear it)
STANDOFF, NEAR, TOL, CAP = 0.045, 0.02, 0.025, 2200
GRASP_OFFSET = 0.002                            # grasp height = object_half_height + this (cube -> 0.014)
GRASP_MAX_HALF = 0.016                          # footprint half above which an object is too wide to grasp
SIZE_ADAPT = os.environ.get("ACT_SIZE_ADAPT", "1") == "1"    # (c) derive grasp heights from object size
PERSIST = os.environ.get("ACT16_PERSIST", "0") == "1"        # keep the scene between episodes


def reactive_subgoal(state):
    """A REACTIVE (stateless) re-derivation of the grasp-and-place teacher: the sub-goal as a PURE
    function of the observed state [hand xyz, obj xy, obj z, target xy, gripper, OBJ_HEIGHT, OBJ_FOOTPRINT].
    Unlike the FSM (hidden `phase`) this is MARKOVIAN, so it is a valid DAgger expert and BC target -- the
    phase is INFERRED from geometry.  (c) SIZE-ADAPTIVE: the grasp/place/carry heights are derived from the
    object's half-height (cube -> the old 0.014, flat/tall -> grasp at their own centre).
    Returns a flat [aim_x, aim_y, aim_z, gripper] (the same shape the policy emits)."""
    hx, hy, hz, cx, cy, cz, tx, ty, j5, obj_h, obj_fp = state
    hxy = np.array([hx, hy]); c = np.array([cx, cy]); t = np.array([tx, ty])
    if SIZE_ADAPT:
        grasp_z = obj_h + GRASP_OFFSET                    # grasp at the object's centre (cube -> 0.014)
        carry_z = max(CARRY_Z, 2.0 * obj_h + 0.02)        # lift high enough to clear a TALL object
        lift_thresh = obj_h + 0.014                       # "lifted off the table" relative to its height
    else:
        grasp_z, carry_z, lift_thresh = GRASP_Z, CARRY_Z, 0.028
    grasped = (cz > lift_thresh) and (j5 < 0.9)           # object lifted off the table AND gripper closed
    if grasped:                                           # CARRY -> place -> release
        if np.linalg.norm(hxy - t) > NEAR:               # carry over the target
            return np.array([tx, ty, carry_z, J5_GRIP])
        if hz > grasp_z + 0.012:                          # lower onto the target
            return np.array([tx, ty, grasp_z, J5_GRIP])
        return np.array([tx, ty, grasp_z, J5_OPEN])       # release
    # The gripper STATE disambiguates the two regimes that look alike in (hz): descending-to-grasp
    # (gripper OPEN) vs ascending-with-cube (gripper CLOSED).  Splitting on j5 stops the open/close
    # oscillation that flung the cube (the old code re-OPENED on the lower branch while lifting).
    if j5 > 1.0:                                          # gripper OPEN -> APPROACH regime
        if np.linalg.norm(hxy - c) > NEAR:               # move over the cube
            return np.array([cx, cy, OVER_Z, J5_OPEN])
        if hz > grasp_z + 0.012:                          # lower onto it, still open
            return np.array([cx, cy, grasp_z, J5_OPEN])
        return np.array([cx, cy, grasp_z, max(J5_GRIP, j5 - 0.2)])    # at pose -> begin closing gently
    # gripper closing/closed (j5 <= 1.0): GRASP/LIFT regime -- commit, never re-open or re-approach
    if j5 > 0.25:                                         # keep closing gently, holding the grasp pose
        return np.array([cx, cy, grasp_z, max(J5_GRIP, j5 - 0.2)])    # (claws STALL ~0.18 on the cube)
    return np.array([cx, cy, carry_z, J5_GRIP])           # firm grip -> LIFT


def run_combined(sim, body, viz, CAM, episodes=12, cmd_fixed=None, force=None, perceive_fn=None,
                 mixed=False, track_fn=None, lifelong=False, log_fn=None, policy_fn=None,
                 episode_end_fn=None, cap=CAP, teacher_log_fn=None, goal_fn=None, place_servo_fn=None,
                 ood_rate=0.0, ood_rng=None, size_fn=None):
    """If perceive_fn is given it is called per episode (arm parked, scene visible) and must
    return (cube_xy, target_xy) as PERCEIVED (e.g. from the camera) — the cube position is used
    for the grasp approach, the target for the place, instead of the privileged sim values.
    Closes the perception->action loop.  (target_xy may be None to keep the given target.)"""
    rng = np.random.default_rng(1)
    STRAY_LO, STRAY_HI = REACH_XY[0] - 0.03, REACH_XY[1] + 0.03   # valid table area (patch + margin)

    def others(nm):
        return [o for o in OBJS if o != nm]

    def clear(p, names, gap):
        return all(np.linalg.norm(p - sim.obj_pos(o)[:2]) > gap for o in names)

    obj_wide = {}                                    # object affordance: wide block (push) vs cube (grasp)

    def scatter():
        pts = []
        for nm in OBJS:
            wide = mixed and (rng.random() < 0.5)            # mixed cube/wide types only when asked
            obj_wide[nm] = wide
            half = WIDE_HALF if wide else CUBE_HALF
            sim.set_object_size(nm, half)
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.08 for q in pts):
                p = _rand_xy(rng)
            pts.append(p); sim.set_object(nm, p, z=float(half[2]))
        mujoco.mj_forward(sim.m, sim.d); sim.step(150)

    def reposition_strays():
        """Any cube that wandered out of the valid area is dropped back inside (clear of others)."""
        moved = False
        for nm in OBJS:
            p = sim.obj_pos(nm)[:2]
            if np.any(p < STRAY_LO) or np.any(p > STRAY_HI):
                q = _rand_xy(rng)
                while not clear(q, others(nm), 0.06):
                    q = _rand_xy(rng)
                sim.set_object(nm, q); moved = True
        if moved:
            mujoco.mj_forward(sim.m, sim.d); sim.step(80)

    if PERSIST:
        sim.reset_home(); scatter()
    n_grasp = n_push = deliveries = 0; perr_sum = perr_n = terr_sum = terr_n = 0.0
    dec_ok = dec_n = 0; grasp_ok = grasp_tot = push_ok = push_tot = 0
    base_ok = base_n = ood_ok = ood_n = 0                    # generalization-probe split
    if ood_rate > 0 and ood_rng is None:
        ood_rng = np.random.default_rng(123)
    for ep in range(episodes):
        if PERSIST:
            sim.arm_home(); reposition_strays()
        else:
            sim.reset_home(); scatter()
        sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        cmd = cmd_fixed or OBJS[ep % len(OBJS)]               # cycle which cube to fetch
        c0 = sim.obj_pos(cmd)[:2]
        cmd_half = CUBE_HALF                                  # base small cube (the standard eval set)
        ood_ep = ood_rate > 0 and float(ood_rng.random()) < ood_rate
        if ood_ep:                                            # GENERALIZATION PROBE: a NOVEL object for the
            fp = float(ood_rng.uniform(0.010, 0.015))         # VISUAL-recognition test — varied FOOTPRINT
            half = np.array([fp, fp, float(ood_rng.uniform(0.011, 0.013))])   # but ~CONSTANT height (≈cube)
            sim.set_object_size(cmd, half); sim.set_object(cmd, c0, z=float(half[2]))   # so the grasp height
            mujoco.mj_forward(sim.m, sim.d); sim.step(60); cmd_half = half             # stays as learned
            c0 = sim.obj_pos(cmd)[:2]
        obj_h = float(cmd_half[2])                            # object size for the SIZE-ADAPTIVE grasp
        obj_fp = float(np.mean(cmd_half[:2]))                 # (privileged; size_fn can override footprint)
        if size_fn is not None:
            fpp = size_fn(cmd)
            if fpp is not None:
                obj_fp = float(fpp)
        tgt = _rand_xy(rng)                                  # target: away from the cube AND not on any cube
        while np.linalg.norm(tgt - c0) < 0.06 or not clear(tgt, OBJS, 0.05):
            tgt = _rand_xy(rng)
        sim.set_target_marker(tgt); sim.step(40)
        tgt_true = tgt.copy(); cube_plan = None; mode_perc = None  # perceive cube + target + mode
        if perceive_fn:
            cube_plan, tgt_perc, mode_perc = perceive_fn(cmd)
            if cube_plan is not None:
                perr_sum += float(np.linalg.norm(cube_plan - sim.obj_pos(cmd)[:2])); perr_n += 1
            if tgt_perc is not None:
                terr_sum += float(np.linalg.norm(tgt_perc - tgt_true)); terr_n += 1; tgt = tgt_perc
            if mode_perc is not None:                             # affordance decision correctness
                ideal = "push" if obj_wide.get(cmd, False) else "grasp"
                dec_ok += int(mode_perc == ideal); dec_n += 1
        if goal_fn is not None:                               # PLANNER dreams the place target from the
            obj_xy = cube_plan if cube_plan is not None else sim.obj_pos(cmd)[:2]   # perceived object
            tgt = np.asarray(goal_fn(cmd, obj_xy), float)     # -> commit to it (and SCORE against it)
            tgt_true = tgt.copy(); sim.set_target_marker(tgt); sim.step(20)   # also moves the visible marker
        mode = force or mode_perc or "grasp"
        phase = "over" if mode == "grasp" else "approach"
        dwell = 0; via = "grasp"; done = False
        for k in range(cap):
            c_true = sim.obj_pos(cmd)[:2]; cz = sim.obj_pos(cmd)[2]; h = sim.grasp_pos(); hxy = h[:2]; hz = h[2]
            # FOLLOW the object live while approaching it; when it is occluded (gripper over it)
            # the tracker returns None and we keep the last estimate (memory) — the act11 pattern.
            if track_fn is not None and k % 4 == 0:           # follow live: drives the gaze + viz +
                track_fn()                                   # lifelong net learning, and SHOWS the
                #   real-view occlusion.  It does NOT overwrite the grasp estimate: the agent acts
                #   on the clean up-front perception as MEMORY (the act11 act-on-memory pattern),
                #   so a partial real-view occlusion never biases the grasp.
            # use the PERCEIVED cube position for the grasp approach (cube is static then); the
            # true position is used once the cube is grabbed / for the fallback and the measure.
            c = cube_plan if (cube_plan is not None and phase in ("over", "lower", "close")) else c_true
            if via == "push" and np.linalg.norm(c - tgt) < TOL:  # pushed home -> done
                break
            if policy_fn is not None and np.linalg.norm(c_true - tgt_true) < TOL and cz < 0.035:
                break                                            # learned policy: object placed -> done
            d = tgt - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])

            if mode == "grasp":
                via = "grasp"
                if phase == "over":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], OVER_Z])
                    if np.linalg.norm(hxy - c) < NEAR:
                        phase = "lower"
                elif phase == "lower":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], GRASP_Z])
                    if hz < GRASP_Z + 0.010:
                        phase, dwell = "close", 0
                elif phase == "close":
                    dwell += 1                                    # close SLOWLY (ramp) so the
                    frac = min(1.0, dwell / 60.0)                 # claws don't shove the cube
                    j5 = J5_OPEN + (J5_GRIP - J5_OPEN) * frac
                    aim = np.array([c[0], c[1], GRASP_Z])
                    if dwell > 90:
                        phase = "lift"
                elif phase == "lift":
                    j5, aim = J5_GRIP, np.array([hxy[0], hxy[1], CARRY_Z])
                    if hz > CARRY_Z - 0.015:
                        if cz > 0.030:                            # cube clearly lifted off the table
                            phase = "carry"                      # grasped!
                        else:
                            mode, phase = "push", "approach"      # missed -> push fallback
                elif phase == "carry":
                    j5, aim = J5_GRIP, np.array([tgt[0], tgt[1], CARRY_Z])
                    if np.linalg.norm(hxy - tgt) < NEAR:
                        phase = "place"
                elif phase == "place":
                    j5, aim = J5_GRIP, np.array([tgt[0], tgt[1], GRASP_Z])
                    if hz < GRASP_Z + 0.012:
                        phase, dwell = "release", 0
                else:  # release
                    j5, aim, dwell = J5_OPEN, np.array([tgt[0], tgt[1], GRASP_Z]), dwell + 1
                    if dwell > 50:
                        break
            else:  # PUSH: get behind the object (OVER it, since the arm can't go through), push
                via = "push"
                behind = c - d * STANDOFF
                if phase == "approach":                          # move behind the object, raised
                    j5, aim = J5_PUSH, np.array([behind[0], behind[1], PUSH_LIFT_Z])
                    if np.linalg.norm(hxy - behind) < NEAR:
                        phase = "pdown"
                elif phase == "pdown":                           # lower the claws behind it
                    j5, aim = J5_PUSH, np.array([behind[0], behind[1], PUSH_Z])
                    if hz < PUSH_Z + 0.012:
                        phase = "push"
                else:                                            # push the object toward the target
                    ahead = c + d * 0.02
                    j5, aim = J5_PUSH, np.array([ahead[0], ahead[1], PUSH_Z])
                    if np.dot(hxy - c, d) > 0.025 or np.linalg.norm(hxy - c) > 0.08:
                        phase = "approach"

            if place_servo_fn is not None:                    # (b) LATENT-DIFFERENCE place: while the
                if cz > 0.028 and sim.d.qpos[sim.jqadr["joint_5"]] < 0.9:   # object is carried, drive
                    tgt = np.asarray(place_servo_fn(hxy), float)  # the place target by the latent servo
            # state for a LEARNED action policy: hand, object, object-z, target, gripper, OBJ SIZE (c)
            state = np.array([h[0], h[1], h[2], c[0], c[1], cz, tgt[0], tgt[1],
                              sim.d.qpos[sim.jqadr["joint_5"]], obj_h, obj_fp], float)
            if teacher_log_fn is not None:                    # DAgger: the FSM's sub-goal at the
                teacher_log_fn(state, np.asarray(aim, float).copy(), float(j5))   # (policy-)VISITED state
            if policy_fn is not None:                         # LEARNED policy drives instead of the FSM
                out = policy_fn(state); aim = np.asarray(out[:3], float); j5 = float(out[3]); via = "policy"
            if log_fn is not None:                            # log the EXECUTED (state -> subgoal)
                log_fn(state, np.asarray(aim, float), float(j5))
            sim.target("joint_5", j5)
            gentle = via == "push" and phase == "push"           # gentle only during the actual push
            g, mdq = (1.3, 0.016) if gentle else (2.0, 0.026)
            q3 = sim.arm3_angles(); sim.set_arm3_targets(q3 + body.reach_velocity(q3, aim, gain=g, max_dq=mdq))
            sim.step(2)
            if lifelong and k % 3 == 0:                       # LIFELONG: refine the learned kinematics
                body.observe(sim.arm3_angles(), sim.grasp_pos(), lr=0.02)   # from the real (joints,hand)
            if viz is not None and k % 5 == 0:
                viz.update(sim.render(CAM), f"ep {ep} {via} {cmd} [{phase}]"
                                            f"  obj->tgt {np.linalg.norm(c-tgt)*1000:.0f}mm")
        sim.target("joint_5", J5_OPEN)                      # complete any placement: RELEASE, then let
        for s in range(40):                                 # the scene SETTLE before scoring (the cube
            sim.step(4)                                     # may still be falling / just-released when
            if track_fn is not None and s % 2 == 0:         # "placed" was declared).  KEEP the live
                track_fn()                                  # fovea window updating through the settle
            if viz is not None and policy_fn is not None:   # so the RELEASE + drop is actually SHOWN
                viz.update(sim.render(CAM), f"ep {ep} {via} {cmd} [settling]")   # (else it freezes mid-air)
        cpos = sim.obj_pos(cmd)
        err = np.linalg.norm(cpos[:2] - tgt_true)           # measure against the TRUE target
        rested = cpos[2] < cmd_half[2] + 0.010              # rests on the table (uses the OBJECT's height)
        ok = err < TOL and rested
        deliveries += ok; n_grasp += (via == "grasp" and ok); n_push += (via == "push" and ok)
        if via == "grasp":
            grasp_tot += 1; grasp_ok += ok
        else:
            push_tot += 1; push_ok += ok
        if ood_ep:
            ood_n += 1; ood_ok += ok
        else:
            base_n += 1; base_ok += ok
        if episode_end_fn is not None:                       # self-improvement: reward = f(ok, err)
            episode_end_fn(ep, bool(ok), float(err))
        typ = "OOD " if ood_ep else (("wide" if obj_wide.get(cmd, False) else "cube") if perceive_fn else "")
        if not getattr(run_combined, "_quiet", False):
            print(f"  ep {ep:2d}: {'OK ' if ok else 'no '} {typ:4s} via {via:5s}  obj->tgt {err*1000:.0f} mm")
    if not getattr(run_combined, "_quiet", False):
        print(f"  == combined grasp-then-push: DELIVERED {deliveries}/{episodes}  "
              f"(by grasp {n_grasp}, by push {n_push}) ==")
        if ood_n:                                            # generalization probe: keep base vs OOD apart
            print(f"  GENERALIZATION: base small-cube {base_ok}/{base_n}  |  OOD novel size/shape {ood_ok}/{ood_n}")
        if dec_n:
            print(f"  AFFORDANCE decision (grasp cube / push wide) correct: {dec_ok}/{int(dec_n)}")
            print(f"  per mode: grasp {grasp_ok}/{grasp_tot}, push {push_ok}/{push_tot}")
        if perr_n:
            print(f"  camera-perceived CUBE vs true: {perr_sum/perr_n*1000:.1f} mm  (over {int(perr_n)} eps)")
        if terr_n:
            print(f"  camera-perceived TARGET vs true: {terr_sum/terr_n*1000:.1f} mm  (over {int(terr_n)} eps)")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()
    return deliveries, episodes


def main():
    HEADLESS = os.environ.get("ACT16_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT16_CAM", "overview").lower()
    TARGET = os.environ.get("ACT16_TARGET", "") or None       # fix one cube, or None = cycle all
    EPISODES = int(os.environ.get("ACT16_EPISODES", "12"))
    MODE = os.environ.get("ACT16_MODE", "both").lower()
    force = None if MODE == "both" else MODE                  # grasp | push to force one branch

    print(f"act16 — manipulation with CLAWS: grasp-then-push  (mode={MODE})")
    sim = BracketArmSim()
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (to the contact point) ...")
    body.babble(sim, 4000)
    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless")
    run_combined(sim, body, viz, CAM, episodes=EPISODES, cmd_fixed=TARGET, force=force)


if __name__ == "__main__":
    main()
