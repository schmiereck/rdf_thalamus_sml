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
GRASP_OFFSET = float(os.environ.get("ACT16_GRASP_OFFSET", "0.006"))   # (#2) grasp height = obj_half + this
#   (cube -> 0.018, was 0.014): the claw tips sit ~14mm below the contact site, so grasp_z=0.014 put them
#   AT the floor and any overshoot was blocked/deflected; +4mm lifts them clear while still gripping the cube
GRASP_MAX_HALF = 0.016                          # footprint half above which an object is too wide to grasp
SERVO_K, SERVO_CONF, SERVO_LOST = 0.5, 0.5, 6   # closed-loop grasp-target belief: correction gain,
#   min track-confidence to update, frames of low confidence before a saccadic re-acquire
MAX_REACQ = 2                                   # cap re-acquires per episode: a persistent track failure
#   must not loop perceive() forever (the fovea visibly re-searching every few seconds) -- then hold
PHASE_STALL = 500                               # steps in ONE phase before the episode gives up (stuck arm)
HOVER_LIMIT = int(os.environ.get("ACT16_HOVER", "40"))   # (#4) steps the policy may hover OPEN+HIGH over
#   the object before the GRASP REFLEX takes over the descend+close (it stalled instead of grasping)
BASE_CLEAR = float(os.environ.get("ACT16_BASE_CLEAR", "0.11"))  # (#1) keep objects + target this far from
#   the base ORIGIN: the base plate is 0.075-half (a 15cm square at 0,0) and REACH starts at y=0.07, so
#   objects/target could spawn ON the base (unreachable / the open gripper collides with the turret)
WRIST_ALIGN = os.environ.get("ACT16_WRIST", "1") == "1"      # (B, default ON) roll joint_4 so the claw aligns to
#   the object's grip axis.  PROPRIOCEPTIVE (claw_yaw from FK, no camera), re-applied EVERY step (set_arm3_targets
#   resets joint_4 to HOME each step, AND claw_yaw is POSE-dependent, so it must keep correcting as the arm moves).
#   Orientation IS sensitive: forced-DIAGONAL cube grip slips (21/40 vs aligned 39/40), elongated LONG-axis 9/40.
#   The user KEEPS it on -- it looks clean in the viz and aligns the grasp robustly.  A few coupled-pipeline
#   grasps still regress (pc_act21 C 9/10 -> 6/10), but per the user's observation that is NOT the wrist: it is
#   the UNDERTRAINED RECOVERY states (miss -> re-grasp -> carry; the policy sometimes re-grasps then "hangs" with
#   the cube instead of carrying) -- rare in the teacher demos -> a TRAINING-coverage gap, addressed separately.
#   Cube -> fixed WRIST_TGT mod 90deg (step B, no perception); elongated -> short axis mod pi.  Disable: ACT16_WRIST=0.
WRIST_TGT = float(os.environ.get("ACT16_WRIST_TGT", "0.0"))  # world-frame grip yaw the claw aligns to (rad)
SIZE_ADAPT = os.environ.get("ACT_SIZE_ADAPT", "1") == "1"    # (c) derive grasp heights from object size
PERSIST = os.environ.get("ACT16_PERSIST", "0") == "1"        # keep the scene between episodes
SCENE_N = int(os.environ.get("ACT16_SCENE_N", "3"))         # objects PLACED per episode (cmd + distractors);
#   the rest of OBJS are parked off-table -- keeps the scene at ~3 like before despite 5 commandable colours
ELONG_RATE = float(os.environ.get("ACT16_ELONG", "0.25"))   # fraction of episodes with ONE elongated (2:1)
ELONG_HALF = np.array([0.024, 0.012, 0.012])                # object mixed into the data (a shape variation)


def _push_subgoal(hxy, hz, c, t):
    """MARKOVIAN push: get behind the object (relative to the target), lower, and follow-push it toward
    the target.  Phase inferred from geometry (no hidden state); the gripper stays spread (J5_PUSH)."""
    d = t - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])
    behind = c - d * STANDOFF                              # contact point on the far side from the target
    proj = float(np.dot(hxy - c, d))                      # along the push dir: <0 behind, >0 past the object
    perp = float(np.linalg.norm((hxy - c) - proj * d))    # lateral offset from the push line
    low = hz < PUSH_Z + 0.012
    on_line_behind = (proj < 0.02) and (perp < NEAR)      # hand behind/at the object, on the push line
    if low and on_line_behind:                            # PUSH: follow-push the object toward the target
        return np.array([c[0] + d[0] * 0.03, c[1] + d[1] * 0.03, PUSH_Z, J5_PUSH])   # (aim just ahead of it)
    if on_line_behind and not low:                        # at the push line but raised -> LOWER
        return np.array([behind[0], behind[1], PUSH_Z, J5_PUSH])
    return np.array([behind[0], behind[1], PUSH_LIFT_Z, J5_PUSH])   # otherwise -> reposition behind, RAISED


def reactive_subgoal(state):
    """A REACTIVE (stateless) re-derivation of the grasp-and-place teacher: the sub-goal as a PURE
    function of the observed state [hand xyz, obj xy, obj z, target xy, gripper, OBJ_HEIGHT, OBJ_FOOTPRINT].
    Unlike the FSM (hidden `phase`) this is MARKOVIAN, so it is a valid DAgger expert and BC target -- the
    phase is INFERRED from geometry.  AFFORDANCE: a footprint wider than the gripper can grasp -> PUSH it;
    else GRASP.  (c) SIZE-ADAPTIVE: the grasp/place/carry heights are derived from the object's half-height
    (cube -> the old 0.014, flat/tall -> grasp at their own centre).
    Returns a flat [aim_x, aim_y, aim_z, gripper] (the same shape the policy emits)."""
    hx, hy, hz, cx, cy, cz, tx, ty, j5, obj_h, obj_fp = state
    hxy = np.array([hx, hy]); c = np.array([cx, cy]); t = np.array([tx, ty])
    if obj_fp > GRASP_MAX_HALF:                           # AFFORDANCE: too wide to grasp -> push
        return _push_subgoal(hxy, hz, c, t)
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
    # RETRY a MISSED grasp instead of dragging the cube to the foot (obs 4): if the gripper is closed and
    # raised to carry height but the cube is STILL on the table, the grasp clearly missed -> re-OPEN above
    # the cube and retry the approach.  Triggers only once the empty lift is COMPLETE (a real grasp would
    # have raised the cube in lockstep, so cz>lift_thresh fires `grasped` first), so it never oscillates.
    if (j5 < 0.25) and (hz > carry_z - 0.012):
        return np.array([cx, cy, OVER_Z, J5_OPEN])        # missed -> reopen + re-approach (no push-to-foot)
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
                 ood_rate=0.0, ood_rng=None, size_fn=None, tol=None, carry_target_fn=None,
                 post_goal_fn=None, macro_log_fn=None, servo=False):
    """If perceive_fn is given it is called per episode (arm parked, scene visible) and must
    return (cube_xy, target_xy) as PERCEIVED (e.g. from the camera) — the cube position is used
    for the grasp approach, the target for the place, instead of the privileged sim values.
    Closes the perception->action loop.  (target_xy may be None to keep the given target.)"""
    rng = np.random.default_rng(1)
    tol = TOL if tol is None else float(tol)             # delivery tolerance (enlargeable target)
    _tm = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "target_marker")
    if _tm >= 0:                                          # show the disk at the scoring tolerance radius
        sim.m.geom_size[sim.m.body_geomadr[_tm]][0] = tol
    STRAY_LO, STRAY_HI = REACH_XY[0] - 0.03, REACH_XY[1] + 0.03   # valid table area (patch + margin)

    def others(nm):
        return [o for o in OBJS if o != nm]

    def clear(p, names, gap):
        return all(np.linalg.norm(p - sim.obj_pos(o)[:2]) > gap for o in names)

    def geom_half(nm):                               # the object's ACTUAL half-extents (cube/wide/OOD)
        bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
        return sim.m.geom_size[sim.m.body_geomadr[bid]].copy()

    obj_wide = {}                                    # object affordance: wide block (push) vs cube (grasp)

    def scatter():
        pts = []
        for nm in OBJS:
            wide = mixed and (rng.random() < 0.5)            # mixed cube/wide types only when asked
            obj_wide[nm] = wide
            half = WIDE_HALF if wide else CUBE_HALF
            sim.set_object_size(nm, half)
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.08 for q in pts) or np.linalg.norm(p) < BASE_CLEAR:
                p = _rand_xy(rng)                            # (#1) clear of other objects AND off the base
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
    narrow_ok = narrow_n = wide_ok = wide_n = 0              # affordance split: grasp narrow / push wide
    if ood_rate > 0 and ood_rng is None:
        ood_rng = np.random.default_rng(123)
    for ep in range(episodes):
        if PERSIST:
            sim.arm_home(); reposition_strays()
        else:
            sim.reset_home(); scatter()
        sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        cmd = cmd_fixed(ep) if callable(cmd_fixed) else (cmd_fixed or OBJS[ep % len(OBJS)])               # cycle which cube to fetch
        # SCENE DENSITY: place SCENE_N objects (the commanded one + distractors); park the rest off-table
        keep = [cmd] + list(rng.choice(others(cmd), max(0, min(SCENE_N - 1, len(OBJS) - 1)), replace=False))
        for i, o in enumerate([o for o in OBJS if o not in keep]):
            sim.set_object(o, np.array([0.55 + 0.06 * i, 0.55]))   # parked far off-camera + out of reach
        # occasionally MIX IN an elongated (2:1) object -- a shape variation in the data (mostly cubes).
        # DISTRACTOR ONLY (never the commanded target): the cube-trained policy can't grasp an elongated
        # object across its short axis yet (the deferred orientation-grasp work) -- it would close the
        # claw early / on the wrong axis.  As a distractor it just adds shape variety for perception.
        distract = [o for o in keep if o != cmd]
        if ELONG_RATE > 0 and distract and float(rng.random()) < ELONG_RATE:
            eo = str(rng.choice(distract))
            sim.set_object_size(eo, ELONG_HALF)
            sim.set_object(eo, sim.obj_pos(eo)[:2], z=float(ELONG_HALF[2]), yaw=float(rng.uniform(0, np.pi)))
        mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        c0 = sim.obj_pos(cmd)[:2]
        cmd_half = geom_half(cmd)                             # ACTUAL size (cube, or a mixed elongated block)
        ood_ep = ood_rate > 0 and float(ood_rng.random()) < ood_rate
        if ood_ep:                                            # GENERALIZATION PROBE: a NOVEL object for the
            fp = float(ood_rng.uniform(0.010, 0.015))         # VISUAL-recognition test — varied FOOTPRINT
            half = np.array([fp, fp, float(ood_rng.uniform(0.011, 0.013))])   # but ~CONSTANT height (≈cube)
            sim.set_object_size(cmd, half); sim.set_object(cmd, c0, z=float(half[2]))   # so the grasp height
            mujoco.mj_forward(sim.m, sim.d); sim.step(60); cmd_half = half             # stays as learned
            c0 = sim.obj_pos(cmd)[:2]
        obj_h = float(cmd_half[2])                            # object size for the SIZE-ADAPTIVE grasp
        obj_fp = float(np.min(cmd_half[:2]))                  # SHORT-axis half: graspable across the NARROWEST
        #   dimension (cube: =mean; elongated: the 12mm short axis -> graspable when the claw aligns to it)
        # (B) WRIST target: align the claw to the object's grip axis.  Elongated -> the SHORT axis (mod pi: a
        # rectangle has 180deg symmetry, the long axis is the WRONG grip, the finite-ish pads can't span 48mm);
        # cube -> ACT16_WRIST_TGT mod 90deg.  Uses privileged obj_yaw for now (perception = step C).
        elong = abs(cmd_half[0] - cmd_half[1]) > 1e-4
        if elong:
            wrist_tgt = sim.obj_yaw(cmd) + (np.pi / 2 if cmd_half[0] > cmd_half[1] else 0.0)
            wrist_mod = np.pi
        else:
            wrist_tgt, wrist_mod = WRIST_TGT, np.pi / 2
        if size_fn is not None:
            fpp = size_fn(cmd)
            if fpp is not None:
                obj_fp = float(fpp)
        tgt = _rand_xy(rng)                                  # target: away from the cube, off any cube, off base
        while np.linalg.norm(tgt - c0) < 0.06 or not clear(tgt, OBJS, 0.05) or np.linalg.norm(tgt) < BASE_CLEAR:
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
            for _ in range(8):                                # SANITIZE the dreamed goal: off objects + base
                moved = False
                for o in OBJS:                                # (#3) push it OFF any object it landed on
                    dv = tgt - sim.obj_pos(o)[:2]; dn = float(np.linalg.norm(dv))
                    if dn < 0.05:
                        tgt = sim.obj_pos(o)[:2] + (dv / dn if dn > 1e-6 else np.array([1.0, 0.0])) * 0.05
                        moved = True
                d = float(np.linalg.norm(tgt))                # (#1) keep it off the base
                if d < BASE_CLEAR:
                    tgt = tgt * (BASE_CLEAR / d) if d > 1e-6 else np.array([0.0, BASE_CLEAR]); moved = True
                if not moved:
                    break
            tgt_true = tgt.copy(); sim.set_target_marker(tgt); sim.step(20)   # also moves the visible marker
        if post_goal_fn is not None:                          # now the COMMITTED goal is known: e.g. drop an
            obj_now = cube_plan if cube_plan is not None else sim.obj_pos(cmd)[:2]   # obstacle on the carry path
            post_goal_fn(cmd, obj_now, tgt_true)              # (placed AFTER the goal so it can clear both ends)
        mode = (force(cmd) if callable(force) else force) or mode_perc or "grasp"
        phase = "over" if mode == "grasp" else "approach"
        dwell = 0; via = "grasp"; done = False; grasp_retry = 0
        # closed-loop grasp-target BELIEF: starts at the up-front perception, then the live fovea
        # CORRECTS it each frame (precision-weighted, occlusion-gated) instead of freezing the snapshot
        obj_belief = (cube_plan.copy() if cube_plan is not None else None) if servo else None
        servo_lost = 0; reacquires = 0; hover = 0            # (#4) grasp-reflex hover counter
        last_phase = phase; phase_age = 0                    # STALL-ESCAPE: don't hang in one phase forever
        for k in range(cap):
            phase_age = phase_age + 1 if phase == last_phase else 0
            last_phase = phase
            if phase_age > PHASE_STALL:                       # stuck (e.g. can't reach the believed object)
                break                                         # -> give up this episode instead of looping
            c_true = sim.obj_pos(cmd)[:2]; cz = sim.obj_pos(cmd)[2]; h = sim.grasp_pos(); hxy = h[:2]; hz = h[2]
            tgt_eff = tgt                                     # routed carry target (obstacle): once the
            if carry_target_fn is not None and cz > 0.03:     # object is lifted, follow the planned route
                _wp = carry_target_fn(hxy, tgt_true)          # AROUND the perceived board instead of going
                if _wp is not None:                           # straight to the goal (goal still used for done)
                    tgt_eff = np.array([_wp[0], _wp[1]], float)
            # FOLLOW the object live while approaching it; when it is occluded (gripper over it)
            # the tracker returns None and we keep the last estimate (memory) — the act11 pattern.
            if track_fn is not None and k % 4 == 0:           # follow live: drives the gaze + viz +
                tr = track_fn()                              # lifelong net learning, and SHOWS the
                #   real-view occlusion.  WITHOUT servo it does NOT overwrite the grasp estimate (the
                #   agent acts on the clean up-front perception as MEMORY, the act11 pattern).  WITH
                #   servo the SAME observation CLOSES THE LOOP: it corrects the grasp-target belief.
                if servo and obj_belief is not None and isinstance(tr, tuple) \
                        and phase in ("over", "lower"):
                    obs, conf = tr
                    if obs is not None and conf >= SERVO_CONF:          # confident view -> correct
                        obj_belief = obj_belief + SERVO_K * conf * (np.asarray(obs, float) - obj_belief)
                        servo_lost = 0
                    else:                                              # lost it (occluded/weak)
                        servo_lost += 1
                        if servo_lost >= SERVO_LOST and perceive_fn is not None and reacquires < MAX_REACQ:
                            fresh, _, _ = perceive_fn(cmd)             # saccadic RE-ACQUIRE ("stochern")
                            if fresh is not None:
                                obj_belief = np.asarray(fresh, float)
                            servo_lost = 0; reacquires += 1           # bounded: then hold the belief
            # grasp approach aims at the BELIEF (servo: live-corrected) or the frozen perception;
            # the true position is used once the cube is grabbed / for the fallback and the measure.
            grasp_src = obj_belief if (servo and obj_belief is not None) else cube_plan
            c = grasp_src if (grasp_src is not None and phase in ("over", "lower", "close")) else c_true
            if via == "push" and np.linalg.norm(c - tgt) < tol:  # pushed home -> done
                break
            if policy_fn is not None and np.linalg.norm(c_true - tgt_true) < tol and cz < 0.035:
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
                        elif obj_fp <= GRASP_MAX_HALF and grasp_retry < 2:
                            grasp_retry += 1; phase = "over"      # narrow: RETRY the grasp (no push-to-foot)
                        else:
                            mode, phase = "push", "approach"      # wide / retries spent -> push fallback
                elif phase == "carry":
                    j5, aim = J5_GRIP, np.array([tgt_eff[0], tgt_eff[1], CARRY_Z])   # via the routed waypoint
                    if np.linalg.norm(hxy - tgt_true) < NEAR:
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
            state = np.array([h[0], h[1], h[2], c[0], c[1], cz, tgt_eff[0], tgt_eff[1],
                              sim.d.qpos[sim.jqadr["joint_5"]], obj_h, obj_fp], float)
            if teacher_log_fn is not None:                    # DAgger: the FSM's sub-goal at the
                teacher_log_fn(state, np.asarray(aim, float).copy(), float(j5))   # (policy-)VISITED state
            route_carry = carry_target_fn is not None and phase == "carry"   # the routed carry follows the
            if policy_fn is not None and not route_carry:     # planned waypoints (FSM servo); the LEARNED
                out = policy_fn(state); aim = np.asarray(out[:3], float); j5 = float(out[3]); via = "policy"
            elif route_carry:                                 # policy carries to a STATIC goal only, so it
                via = "route"                                 # cannot follow side-waypoints -> servo the route
            # (#4) GRASP REFLEX -- active-inference framing: once the hand is positioned OVER the object the
            # agent EXPECTS to be grasping; hovering OPEN + HIGH instead is a sustained prediction error that
            # drives a descend+close.  Fires ONLY on a stall (HOVER_LIMIT), so the learned policy still drives
            # normally -- this just guarantees the grasp EXECUTES instead of the policy hovering forever (#4).
            gz = obj_h + GRASP_OFFSET
            if np.linalg.norm(hxy - c) < 0.03 and cz < 0.035 and j5 > 0.6 and hz > gz + 0.012:
                hover += 1
            else:
                hover = 0
            if hover > HOVER_LIMIT:
                aim = np.array([c[0], c[1], gz]); j5 = max(J5_GRIP, j5 - 0.2); via = "reflex"
            if log_fn is not None:                            # log the EXECUTED (state -> subgoal)
                log_fn(state, np.asarray(aim, float), float(j5))
            if macro_log_fn is not None:                      # EXECUTED step + the FSM phase (for macro
                macro_log_fn(state, np.asarray(aim, float), float(j5), phase)   # sub-goal segmentation)
            sim.target("joint_5", j5)
            gentle = abs(j5 - J5_PUSH) < 0.2 and aim[2] < PUSH_Z + 0.02   # spread gripper + low = a PUSH
            g, mdq = (1.3, 0.016) if gentle else (2.0, 0.026)            # (derived from the sub-goal, so it
            q3 = sim.arm3_angles(); sim.set_arm3_targets(q3 + body.reach_velocity(q3, aim, gain=g, max_dq=mdq))
            if WRIST_ALIGN:                                    # (B) align the claw to the object's grip axis,
                cy = sim.claw_yaw()                            # re-applied EVERY step: set_arm3_targets resets
                err = (cy - wrist_tgt + wrist_mod / 2) % wrist_mod - wrist_mod / 2   # joint_4 to HOME each step,
                j4t = float(np.clip(sim.d.qpos[sim.jqadr["joint_4"]] + 0.6 * err, 0.0, np.pi))   # and claw_yaw is
                sim.target("joint_4", j4t)                     # POSE-dependent so it must keep correcting (slope ~ -1)
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
        ok = err < tol and rested
        deliveries += ok; n_grasp += (via == "grasp" and ok); n_push += (via == "push" and ok)
        if via == "grasp":
            grasp_tot += 1; grasp_ok += ok
        else:
            push_tot += 1; push_ok += ok
        if ood_ep:
            ood_n += 1; ood_ok += ok
        else:
            base_n += 1; base_ok += ok
        if obj_fp > GRASP_MAX_HALF:                           # affordance: this object should be PUSHED
            wide_n += 1; wide_ok += ok
        else:
            narrow_n += 1; narrow_ok += ok
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
        if wide_n:                                            # affordance: grasp-narrow vs push-wide split
            print(f"  AFFORDANCE: narrow->grasp {narrow_ok}/{narrow_n}  |  wide->push {wide_ok}/{wide_n}")
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
