r"""pc_act23.py — a SELF-LEARNING grasper: a self-supervised world/outcome model + uncertainty-aware acting.

The user's overarching goal is an architecture that LEARNS new shapes/positions ITSELF (no scripted
teacher); beating the teacher is NOT the criterion (see the memory note user-goal-self-learning).  This
driver builds that loop on the arm:

  * the agent TRIES grasp actions (grasp-point offset + wrist) in perceived situations and observes whether
    the object is DELIVERED -> the only training signal is its OWN outcome (self-supervised);
  * a WorldModelModule (ensemble) learns P(deliver | perceived situation, action) with UNCERTAINTY;
  * it ACTS on the lower confidence bound (mu - lam*sigma), so it deviates from a safe default only where it
    is CONFIDENT -> it never underperforms the default (the fix for the naive-argmax model exploitation that
    made an earlier attempt WORSE than the teacher).

Four honest checks (success here = self-acquisition + generalisation + improvement + safety, NOT > teacher):
  1. model AUC for P(deliver) on held-out trials;
  2. SAFETY: LCB acting >= the WRIST_ALIGN default, and clearly better than naive argmax (lam=0);
  3. GENERALISATION: trained on cube+L only -> does it help / not hurt on the HELD-OUT U;
  4. LEARNING CURVE: U delivery as the agent collects more of its OWN U experience.

ACT23_MODE = "diag" (default) runs the SIGNAL-RICH validation -- a diagonally-oriented ELONGATED object whose
delivery genuinely depends on the wrist.  The teacher's wrist heuristic is DISABLED (a fixed wrist as the
no-privilege default); the world model learns -- from its OWN outcomes -- which wrist delivers as a function
of the PERCEIVED long-axis orientation (ObjectOrientationModule, camera, not the privileged sim yaw).  It
recovers / beats the privileged-yaw teacher WITHOUT privilege (the clean architecture demonstration).
ACT23_MODE = "shapes" runs the near-ceiling cube/L/U grasp checks (honest: too little signal to self-improve).

Env: ACT23_MODE ACT23_NPOS ACT23_NTRIAL ACT23_HOLD ACT23_TEST ACT23_LAM ACT23_K ACT23_NCAND ACT23_CURVE_STEPS
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

os.environ.setdefault("ACT14_DOF", "4")   # act23 runs the 4-DOF arm: joint_3 freed (user request) --
#   it was LOCKED at HOME=3.14 everywhere and is THE reason for the small workspace; the learned
#   kinematics babbles all 4 positioning joints and the reach keeps the CLAW DIRECTION (redundancy).
#   ACT14_DOF=3 restores the classic arm.  Must be set BEFORE pc_act14 is imported (ARM3 is built then).
# WORKSPACE enlarged toward the 4-DOF reach (user request), bounded by the MEASURED GRASP ENVELOPE:
# the panned physical-rig camera localises 0-5mm over the whole table and straight-ahead grasps work
# to r=0.32, BUT the teacher choreography fails at combined |x|>~0.09 with y>~0.15 (probes: (+-0.115,
# 0.16) 0/4, (+-0.095,0.20) 0/3 -- ALSO at 3 DOF, a PRE-EXISTING envelope hole the old probes never
# sampled; 4 DOF adds claw TILT there, 30-42deg vs 14-19).  So: y extended 0.21->0.24 (centre column +
# narrow top verified), x kept at ~old size.  The envelope hole is an open work item (fits stage 2:
# a learned policy could learn its own envelope).
for _k, _v in (("ACT_REACH_X0", "-0.12"), ("ACT_REACH_X1", "0.12"),
               ("ACT_REACH_Y0", "0.07"), ("ACT_REACH_Y1", "0.24")):
    os.environ.setdefault(_k, _v)
os.environ.setdefault("ACT_GOAL_ROPE", "1")   # STAGE 4a: RoPE goal-latent (near-linear in position ->
#   the learned latent-inverse is near-exact; measured in act21: servo isolated ~0mm vs 4.4mm blob)
from pc_cvnn.pc_act14 import BracketArmSim, HOME, ARM3
from pc_cvnn.pc_act18 import (F as HEX_F, warp_gaze_delta, fovea_gradient,
                              ZOOM as FOVEA_ZOOM, ZOOM_MIN, ZOOM_MAX)
from pc_cvnn.test_pc_act10 import com2d
from pc_cvnn.arm_modules.body_model import BodyModelModule
from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule
from pc_cvnn.arm_modules.object_orientation import ObjectOrientationModule
from pc_cvnn.arm_modules.world_model import (WorldModelModule, feats_from, action_vec, wrist_of,
                                             quality as wm_quality, tilt_of as wm_tilt_of,
                                             TILT_ACTION, TILT_CURIOSITY)
from pc_cvnn.arm_modules.runtime_policy import RuntimePolicyModule
from pc_cvnn.arm_modules import colour_openset
from pc_cvnn.arm_modules.colour_openset import ColourOpenSetModule
from pc_cvnn.arm_modules.planner import GoalModule2D, LO as GOAL_LO, HI as GOAL_HI
from pc_cvnn.arm_modules.latent_goal import LatentGoalServo, LatentGoalLanguage
from pc_cvnn.arm_modules.latent_dynamics import LatentDynamicsModule
from pc_cvnn.arm_modules.latent_attractor import LatentAttractorController
from pc_cvnn.arm_modules.curiosity import DistanceNovelty
from pc_cvnn.arm_modules.self_eval import SelfEvalModule
from pc_cvnn.arm_modules.object_memory import ObjectMemoryModule
import pc_cvnn.pc_act16 as act16

CAM = "overview"
# FOVEA-DRIVEN SERVO (this branch's goal): the approach corrections come from the NET's own gaze
# belief instead of the algorithmic detector (perceive_all stays as fallback + identity re-anchor
# only) -- the first load-bearing de-crutching of the detector.  Modes: "1" = while the fovea's
# IDENTITY lock holds its belief IS the servo obs, "shadow" = compute + log |net - detector| but let
# the detector keep driving (measurement mode), "0" = main behaviour (gaze = attention only).
# Requires the learned gaze, so any mode != "0" forces FOVEA_NET on.
FOVEA_SERVO = os.environ.get("ACT23_FOVEA_SERVO", "1")
# LEARNED FOVEA GAZE (opt-in): the net's own active-inference centering drives the gaze of the form/
# class tracker, the detector only re-anchors identity every FOVEA_ANCHOR frames.  Without FOVEA_SERVO
# the gaze is attention only (grasp target comes from the detector regardless), so this cannot regress
# delivery; it makes "where to look" a net decision (the user's goal).  ACT23_FOVEA_NET=1 enables.
FOVEA_NET = os.environ.get("ACT23_FOVEA_NET", "0") == "1" or FOVEA_SERVO != "0"
FOVEA_ANCHOR = int(os.environ.get("ACT23_FOVEA_ANCHOR", "6"))
# PREDICTIVE OBJECT MEMORY: replaces the detector re-anchor with a proprioceptive belief so the
# net-driven gaze follows the object through grasp OCCLUSION + CARRY with NO detector.  Default ON
# when the learned gaze is active (itself opt-in).  ACT23_FOVEA_MEM=0 falls back to the detector anchor.
FOVEA_MEM = FOVEA_NET and os.environ.get("ACT23_FOVEA_MEM", "1") == "1"
BODY = {"cube": "obj_red", "L": "obj_L", "U": "obj_U"}
ALL = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
TARGET = np.array([0.0, 0.10])
# NACHBAR-INFORMATION als Situations-Feature (s. _neighbour_feats).  ACT23_NEIGHBOURS=0 schaltet sie
# ab -- die Dimensionen BLEIBEN dann im Schema (sonst passte der Puffer nicht mehr), sie tragen nur
# konstant den neutralen Wert.  NB_DMAX = ab welchem Abstand ein Objekt nicht mehr als Nachbar zaehlt;
# 0.12m deckt Schieben beim Schliessen, Rammen beim Tragen und das Blob-Verschmelzen (~40mm) ab.
NEIGHBOURS = os.environ.get("ACT23_NEIGHBOURS", "1") != "0"
NB_DMAX = float(os.environ.get("ACT23_NB_DMAX", "0.12"))
NB_DIM = 5
NB_NEUTRAL = np.array([0.0, NB_DMAX, 1.0, 0.0, 0.0])   # "nie gemessen" -- gueltig-Flag 0


def _auc(y, s):
    y = np.asarray(y).ravel(); s = np.asarray(s).ravel()
    pos = s[y > 0.5]; neg = s[y <= 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


class Env:
    def __init__(self):
        self.sim = BracketArmSim(render_wh=(240, 240)); self.sim.set_reach_site("contact")
        self.bm = BodyModelModule(rng=np.random.default_rng(5)); self.bm.babble(self.sim, 4000)
        self.clf = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
        self.clf.calibrate(self.sim); self.clf.train(self.sim, steps=3000, rng=np.random.default_rng(1))
        act16.run_combined._quiet = True
        self._rid = mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")

    def setup(self, shape, p, yaw):
        self.sim.reset_home()
        for o in ALL:
            self.sim.set_object(o, [0.5, -0.6], z=0.012)
        self.sim.m.geom_size[self.sim.m.body_geomadr[self._rid]] = np.array([0.012] * 3)
        self.sim.set_object(BODY[shape], p, z=0.012, yaw=yaw)
        mujoco.mj_forward(self.sim.m, self.sim.d); self.sim.step(60)

    def select(self, shape):
        return self.clf.select(self.sim, shape)

    def grasp(self, shape, grasp_xy, wrist):
        gc = 0.3 if shape == "U" else None
        wf = None if wrist is None else (lambda s, _w=wrist: _w)
        d, m = act16.run_combined(self.sim, self.bm.body, None, CAM, episodes=1, cmd_fixed=BODY[shape],
                                  force="grasp", perceive_fn=lambda c, g=grasp_xy: (g, None, "grasp"),
                                  policy_fn=None, servo=False, goal_fn=lambda c, o: TARGET, rescatter=False,
                                  grip_close=gc, carry_gentle=(shape == "U"), wrist_fn=wf)
        return int(d)


def rand_pos(rng):
    return np.array([rng.uniform(-0.10, 0.10), rng.uniform(0.09, 0.22)])   # inside the enlarged workspace


def collect(env, world, shapes, npos, ntrial, rng, into_world=True):
    """Self-supervised: try random (offset, wrist) grasps, observe delivery. Returns (X,Y) tuples."""
    Xh, Yh = [], []
    for shape in shapes:
        for _ in range(npos):
            p = rand_pos(rng); yaw = rng.uniform(0, 2 * np.pi)
            env.setup(shape, p, yaw); sel = env.select(shape)
            if sel is None:
                continue
            g0 = np.asarray(sel["grasp_xy"], float); fe = feats_from(sel, shape)
            for _ in range(ntrial):
                dx, dy = rng.uniform(-world.off_max, world.off_max, 2); w = rng.uniform(0, np.pi)
                env.setup(shape, p, yaw)
                d = env.grasp(shape, g0 + np.array([dx, dy]), w)
                a = action_vec(dx, dy, w)
                if into_world:
                    world.observe(fe, a, d)
                Xh.append(np.concatenate([fe, a])); Yh.append(d)
    return np.array(Xh), np.array(Yh)


def deliver_rate(env, world, shape, positions, mode, lam):
    """mode: 'default' (WRIST_ALIGN), 'lcb' (uncertainty-aware), 'argmax' (lam=0 naive)."""
    d = 0; n = 0
    for p, yaw in positions:
        env.setup(shape, p, yaw); sel = env.select(shape)
        if sel is None:
            continue
        g0 = np.asarray(sel["grasp_xy"], float); n += 1
        if mode == "default":
            env.setup(shape, p, yaw); d += env.grasp(shape, g0, None); continue
        fe = feats_from(sel, shape)
        a, _, _ = world.select_action(fe, n=int(os.environ.get("ACT23_NCAND", "40")),
                                      lam=(0.0 if mode == "argmax" else lam))
        env.setup(shape, p, yaw)
        d += env.grasp(shape, g0 + a[:2], wrist_of(a))
    return d, max(1, n)


def main():
    NPOS = int(os.environ.get("ACT23_NPOS", "10"))
    NTRIAL = int(os.environ.get("ACT23_NTRIAL", "6"))
    HOLD = int(os.environ.get("ACT23_HOLD", "5"))
    TEST = int(os.environ.get("ACT23_TEST", "12"))
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    K = int(os.environ.get("ACT23_K", "5"))
    CURVE_STEPS = int(os.environ.get("ACT23_CURVE_STEPS", "3"))

    print("act23 — SELF-LEARNING grasper: self-supervised world model + uncertainty-aware acting")
    env = Env()
    world = WorldModelModule(k=K, rng=np.random.default_rng(2))
    rng = np.random.default_rng(7)

    # (1) self-supervised collection on cube + L (NOT U), train, AUC on held-out trials
    print(f"  collecting OWN trials on cube+L ({NPOS} pos x {NTRIAL} trials/shape) ...")
    collect(env, world, ["cube", "L"], NPOS, NTRIAL, rng, into_world=True)
    Xh, Yh = collect(env, world, ["cube", "L"], HOLD, NTRIAL, rng, into_world=False)
    world.train(epochs=600)
    auc = _auc(Yh, [world.predict(x[:7], x[7:][None])[0][0] for x in Xh]) if len(Xh) else float("nan")
    print(f"  [1] model trained on {world.n()} own trials; held-out P(deliver) AUC = {auc:.2f}  "
          f"(deliver rate {np.mean(Yh) if len(Yh) else float('nan'):.2f})", flush=True)

    # fixed test positions per shape (paired across methods)
    tpos = {s: [(rand_pos(rng), rng.uniform(0, 2 * np.pi)) for _ in range(TEST)] for s in ("cube", "L", "U")}

    # (2) SAFETY + (3) GENERALISATION (U is held-out): default vs LCB vs naive-argmax
    print("  [2/3] default(WRIST_ALIGN) vs LCB(uncertainty-aware) vs argmax(naive) "
          "[U = generalisation, never collected]:")
    for s in ("cube", "L", "U"):
        dd, n = deliver_rate(env, world, s, tpos[s], "default", LAM)
        dl, _ = deliver_rate(env, world, s, tpos[s], "lcb", LAM)
        da, _ = deliver_rate(env, world, s, tpos[s], "argmax", LAM)
        tag = "  <- held-out (generalisation)" if s == "U" else ""
        print(f"    {s}: default {dd}/{n}   LCB {dl}/{n}   naive-argmax {da}/{n}{tag}", flush=True)

    # (4) LEARNING CURVE: acquire the U from its OWN experience
    print(f"  [4] U learning curve (self-acquisition, {CURVE_STEPS} steps of own U trials):")
    d0, n0 = deliver_rate(env, world, "U", tpos["U"], "lcb", LAM)
    curve = [d0 / n0]
    print(f"    U after 0 own U-trials: LCB {d0}/{n0}", flush=True)
    for it in range(CURVE_STEPS):
        collect(env, world, ["U"], NPOS, NTRIAL, rng, into_world=True)
        world.train(epochs=600)
        du, nu = deliver_rate(env, world, "U", tpos["U"], "lcb", LAM)
        curve.append(du / nu)
        print(f"    U after {(it + 1) * NPOS * NTRIAL} own U-trials: LCB {du}/{nu}  (model {world.n()} trials)",
              flush=True)
    try:
        _plot(curve, NPOS * NTRIAL, os.path.join(os.path.dirname(__file__), "act23_learning.png"))
    except Exception as e:
        print(f"  [viz] could not save the learning curve: {e}")


def _plot(curve, per, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.arange(len(curve)) * per
    fig, ax = plt.subplots(figsize=(7, 4)); fig.patch.set_facecolor("#0e0e12")
    ax.set_facecolor("#0e0e12"); ax.grid(True, color="#333", lw=0.4); ax.tick_params(colors="w")
    [s.set_color("#555") for s in ax.spines.values()]
    ax.plot(x, curve, "-o", color="#33ccff")
    ax.set_xlabel("own U trials collected", color="w"); ax.set_ylabel("U delivery (LCB)", color="w")
    ax.set_title("act23: self-acquisition of the held-out U from own experience", color="w", fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] learning curve saved -> {path}")


def main_diag():
    """SIGNAL-RICH validation: a diagonally-oriented elongated object whose delivery depends on the wrist.
    The world model learns -- from its OWN outcomes -- which wrist delivers given the PERCEIVED long-axis
    orientation (no privileged sim yaw), and recovers/beats the privileged-yaw teacher without privilege."""
    NPOS = int(os.environ.get("ACT23_NPOS", "14"))
    NTRIAL = int(os.environ.get("ACT23_NTRIAL", "6"))
    TEST = int(os.environ.get("ACT23_TEST", "16"))
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    K = int(os.environ.get("ACT23_K", "5"))
    CURVE_STEPS = int(os.environ.get("ACT23_CURVE_STEPS", "3"))
    CMD = "obj_red"; HALF = (0.028, 0.010, 0.012)

    print("act23 [diag] — SELF-LEARNING the grip wrist for a diagonal ELONGATED object (no privileged yaw)")
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    oo = ObjectOrientationModule()
    err = oo.train(sim, cmd=CMD, cam=CAM, steps=2500, half=HALF, rng=np.random.default_rng(0))
    print(f"  perceived long-axis train err: {err:.1f} deg  (self-supervised, camera -- NOT privileged)")
    act16.run_combined._quiet = True
    bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, CMD)

    def setup(p, yaw):
        sim.reset_home()
        for o in ("obj_green", "obj_blue", "obj_L", "obj_U"):
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_target_marker([0.0, -0.6], z=-0.05)
        sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(HALF, float)
        sim.set_object(CMD, p, z=float(HALF[2]), yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        sim.set_target_marker(TARGET, z=0.001)

    def feats():
        _, la = oo.perceive(sim, CMD, CAM); p = sim.obj_pos(CMD)[:2]   # PERCEIVED long axis (camera)
        return np.array([p[0], p[1], np.cos(2 * la), np.sin(2 * la), 1.0, 0.0, 0.0])

    def grasp(wrist):
        wf = None if wrist == "priv" else (lambda s, _w=wrist: _w)     # "priv" -> run_combined's privileged yaw
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=CMD, force="grasp",
                                  perceive_fn=lambda c: (sim.obj_pos(CMD)[:2], None, "grasp"),
                                  policy_fn=None, servo=False, goal_fn=lambda c, o: TARGET, rescatter=False,
                                  wrist_fn=wf)
        return int(d)

    world = WorldModelModule(k=K, off_max=0.0, rng=np.random.default_rng(2))   # off_max=0 -> pure wrist search
    rng = np.random.default_rng(7)

    def collect(npos, ntr):
        for _ in range(npos):
            p = rand_pos(rng); yaw = rng.uniform(0, np.pi)
            setup(p, yaw); fe = feats()
            for _ in range(ntr):
                w = rng.uniform(0, np.pi); setup(p, yaw)
                world.observe(fe, action_vec(0, 0, w), grasp(w))

    collect(NPOS, NTRIAL); world.train(epochs=600)
    # held-out AUC
    Xh, Yh = [], []
    for _ in range(8):
        p = rand_pos(rng); yaw = rng.uniform(0, np.pi); setup(p, yaw); fe = feats()
        for _ in range(4):
            w = rng.uniform(0, np.pi); setup(p, yaw); Yh.append(grasp(w)); Xh.append((fe, action_vec(0, 0, w)))
    auc = _auc(Yh, [world.predict(f, a[None])[0][0] for f, a in Xh])
    print(f"  [1] held-out P(deliver) AUC = {auc:.2f}  (deliver rate {np.mean(Yh):.2f})", flush=True)

    tpos = [(rand_pos(rng), rng.uniform(0, np.pi)) for _ in range(TEST)]

    def rate(mode):
        d = 0
        for p, yaw in tpos:
            setup(p, yaw)
            if mode == "fixed":
                w = 0.0
            elif mode == "priv":
                w = "priv"
            else:
                a, _, _ = world.select_action(feats(), n=0, lam=LAM); w = wrist_of(a)
            setup(p, yaw); d += grasp(w)
        return d

    print("  [2/3] self-learned wrist vs baselines (no privileged yaw for the agent):")
    print(f"    fixed wrist=0 (no privilege)    : {rate('fixed')}/{TEST}")
    print(f"    privileged obj_yaw (upper bound): {rate('priv')}/{TEST}")
    print(f"    SELF-LEARNED (LCB)              : {rate('self')}/{TEST}", flush=True)
    print(f"  [4] learning curve (self-learned, +{NPOS * NTRIAL}/step):")
    for it in range(CURVE_STEPS):
        collect(NPOS, NTRIAL); world.train(epochs=600)
        print(f"    after {(it + 1) * NPOS * NTRIAL} more own trials (model {world.n()}): self {rate('self')}/{TEST}",
              flush=True)


class CommandState23:
    """Unified command state for the act23 GUI.  ONE coherent object list (no colour/form mode), plus a
    grasp-policy toggle (teacher WRIST_ALIGN <-> SELF-learned world-model wrist).  Exposes the cmd/force/goal
    hooks run_combined consumes."""

    # one button per CONCRETE object; field 3 = how the net LOCALISES it (colour via vc / form via shape_clf /
    # long = the elongated obj_blue, localised by colour, wrist by the self-learned world model)
    OBJECTS = [("Rotes Wuerfel", "obj_red", "color"), ("Gruenes Wuerfel", "obj_green", "color"),
               ("L-Form", "obj_L", "shape"), ("U-Form", "obj_U", "shape"), ("Langes Objekt", "obj_blue", "long")]
    SHAPE_KEY = {"obj_L": "L", "obj_U": "U"}
    MARKERS = ["target_sel_1", "target_sel_2", "target_sel_3"]
    OBJ_COL = {"obj_red": "#d23030", "obj_green": "#2fae40", "obj_blue": "#3358d2",
               "obj_L": "#d98a2b", "obj_U": "#27b3b3", "obj_T": "#7a3fd0"}

    def __init__(self, sim):
        self.sim = sim; self.sel = 0; self.action = "grasp"; self.target_idx = 0
        self.policy = "self"          # "self" -> world-model wrist (long obj); "teacher" -> WRIST_ALIGN
        self.choreo = "fsm"           # "fsm" -> scripted choreography (collects DAgger data);
        #                               "netz" -> the LEARNED runtime policy drives the sub-goals (Stufe 2)
        self.goalmode = os.environ.get("ACT23_GOAL", "latent")   # STAGE 4a: "latent" -> the place target
        #   is a GOAL LATENT, executed by the latent-difference servo; "koord" -> classic coordinate place
        self.go = False; self.exit = False
        self.auto = False             # AUTO-Lauf: random object + random target per episode (self-training)
        self.busy = False             # an episode is RUNNING: matplotlib fires button callbacks inside the
        #   run's flush_events -- scene-mutating actions must be DEFERRED to after the episode (a mid-run
        #   "Objekt hinzufügen" grew the object list past the pose snapshot + moved objects under the claw)
        # INSTANCE copies: OPEN-SET discovery appends objects at runtime (a self-labelled class becomes a
        # commandable button) -- the class-level lists stay the pristine trained set.
        self.OBJECTS = list(CommandState23.OBJECTS)
        self.SHAPE_KEY = dict(CommandState23.SHAPE_KEY)

    def add_object(self, label, body, shape_key):
        """Register a SELF-DISCOVERED object: commandable like L/U, localised by its self-labelled open
        class (`shape_key`, e.g. 'neu-1').  The body handle is GUI plumbing only -- perception (select /
        track) runs purely on the class name."""
        self.OBJECTS = self.OBJECTS + [(label, body, "shape")]
        self.SHAPE_KEY[body] = shape_key

    def selected(self):
        return self.OBJECTS[self.sel]

    def _mocap(self, name):
        return self.sim.m.body_mocapid[mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, name)]

    def marker_xy(self, idx):
        return self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2].copy()

    def set_marker_xy(self, idx, xy):
        self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2] = xy

    def sync_active(self):
        self.sim.d.mocap_pos[self._mocap("target_marker")][:2] = self.marker_xy(self.target_idx)
        mujoco.mj_forward(self.sim.m, self.sim.d)

    def place_selected_random(self, rng):
        from pc_cvnn.pc_act14 import _rand_xy
        from pc_cvnn.pc_act16 import BASE_CLEAR
        bodies = [nm for _l, nm, _m in self.OBJECTS]
        p = _rand_xy(rng)
        for _ in range(200):
            if float(np.linalg.norm(p)) >= BASE_CLEAR and all(
                    float(np.linalg.norm(p - self.sim.obj_pos(o)[:2])) > 0.05 for o in bodies):
                break
            p = _rand_xy(rng)
        self.set_marker_xy(self.target_idx, p); self.sync_active()

    # run_combined hooks
    def cmd_fn(self, ep):
        return self.selected()[1]

    def force_fn(self, cmd):
        return self.action

    def goal_fn(self, cmd, obj_xy):
        return self.marker_xy(self.target_idx)

    def label(self):
        act = "Greifen" if self.action == "grasp" else "Schieben"
        pol = "Selbst-gelernt" if self.policy == "self" else "Teacher"
        ch = {"netz": "Netz", "attractor": "Attraktor"}.get(self.choreo, "FSM")
        zl = " (latent)" if self.goalmode == "latent" else ""
        return f"{self.selected()[0]} | {act} | Greifer: {pol} | Choreo: {ch} | Ziel {self.target_idx + 1}{zl}"


class CommandPanel23:
    """Same look as pc_act21's CommandPanel (arm camera + fovea + surprise + buttons) but with ONE unified
    object row (no colour/form mode) and a grasp-policy toggle."""

    def __init__(self, state, cam, res, rng=None, randomize_fn=None):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button
        from pc_cvnn.pc_act18 import HexFoveaViz, SurpriseViz
        self.plt = plt; self.state = state; self._cam = cam; self._randomize_fn = randomize_fn
        self._rng = rng if rng is not None else np.random.default_rng(0); plt.ion()
        fw, fh = (float(x) for x in os.environ.get("ACT23_FIGSIZE", "12.0,7.5").split(","))
        self.fig = plt.figure(figsize=(fw, fh)); self.fig.patch.set_facecolor("#0e0e12")
        self.fig.canvas.manager.set_window_title("act23 — Selbst-lernender Greifer (Netz steuern)")
        self.axCam = self.fig.add_axes([0.035, 0.30, 0.38, 0.63]); self.axCam.axis("off")
        self.axCam.set_title(f"Arm — {cam} Kamera", color="w", fontsize=10)
        self.imCam = self.axCam.imshow(np.zeros((res, res, 3), np.uint8))
        axFovI = self.fig.add_axes([0.44, 0.62, 0.24, 0.31]); axFovC = self.fig.add_axes([0.44, 0.30, 0.21, 0.26])
        self.fov_viz = HexFoveaViz(cam, res, axI=axFovI, axC=axFovC)
        axE = self.fig.add_axes([0.715, 0.635, 0.27, 0.295]); axR = self.fig.add_axes([0.715, 0.30, 0.27, 0.235])
        self.surp_viz = SurpriseViz(axE=axE, axR=axR, show_readout=False)
        self.status = self.fig.text(0.5, 0.255, "", ha="center", color="w", fontsize=11, family="monospace")
        self.live = self.fig.text(0.225, 0.285, "", ha="center", color="#9fb4c8", fontsize=8.5, family="monospace")
        # unified OBJECT row (one button per concrete object)
        self._obj_btns = {}
        for i, (lbl, nm, _m) in enumerate(state.OBJECTS):
            ax = self.fig.add_axes([0.035 + 0.115 * i, 0.150, 0.108, 0.055])
            col = state.OBJ_COL[nm]
            b = Button(ax, lbl, color=col, hovercolor=col); b.label.set_fontsize(7.5)
            b.on_clicked(lambda _e, k=i: self._set_obj(k)); self._obj_btns[i] = b
        self.fig.text(0.018, 0.178, "Objekt", color="#9fb4c8", fontsize=8, rotation=90, va="center")
        # grasp-policy toggle (right of the object row -- slot 6 belongs to a discovered form)
        axPol = self.fig.add_axes([0.78, 0.150, 0.155, 0.055])
        self.bPol = Button(axPol, "", color="#3a5a44", hovercolor="#4a7256"); self.bPol.on_clicked(self._toggle_policy)
        # OPEN-SET: drop the unknown probe object into the scene (the net must DISCOVER + self-label it)
        self._introduce_fn = None
        self._pending_introduce = False; self._pending_randomize = False   # deferred mid-episode clicks
        axN = self.fig.add_axes([0.035, 0.220, 0.16, 0.05])
        self.bN = Button(axN, "Objekt hinzufügen", color="#8a7430", hovercolor="#a89040")
        self.bN.on_clicked(self._introduce)
        # AUTO-Lauf: self-play episodes (random object + random target) until toggled off
        axAuto = self.fig.add_axes([0.205, 0.220, 0.115, 0.05])
        self.bAuto = Button(axAuto, "Auto: aus", color="#3a3a5a", hovercolor="#50507a")
        self.bAuto.on_clicked(self._toggle_auto)
        # STAGE 2: scripted FSM choreography <-> the LEARNED runtime policy drives the sub-goals
        axCh = self.fig.add_axes([0.33, 0.220, 0.125, 0.05])
        self.bCh = Button(axCh, "Choreo: FSM", color="#5a3a3a", hovercolor="#7a5050")
        self.bCh.on_clicked(self._toggle_choreo)
        # STAGE 4a: place target as GOAL LATENT (latent-difference servo) <-> classic coordinate
        axLG = self.fig.add_axes([0.462, 0.220, 0.082, 0.05])
        _lat = state.goalmode == "latent"
        self.bLG = Button(axLG, "Ziel: Latent" if _lat else "Ziel: Koord",
                          color=("#2a6a5a" if _lat else "#5a4a3a"), hovercolor="#3a8a75")
        self.bLG.label.set_fontsize(7)
        self.bLG.on_clicked(self._toggle_goalmode)
        # named target buttons (top-right of the control band)
        self._tgt_btns = {}
        for i in range(len(state.MARKERS)):
            ax = self.fig.add_axes([0.55 + 0.135 * i, 0.220, 0.12, 0.05])
            b = Button(ax, f"Ziel {i + 1}", color="#3a3a44", hovercolor="#55556a")
            b.on_clicked(lambda _e, i=i: self._set_tgt(i)); self._tgt_btns[i] = b
        # bottom controls
        axA = self.fig.add_axes([0.035, 0.04, 0.20, 0.07])
        self.bA = Button(axA, "Modus: Greifen", color="#555", hovercolor="#777"); self.bA.on_clicked(self._toggle)
        axP = self.fig.add_axes([0.25, 0.04, 0.16, 0.07])
        self.bP = Button(axP, "Ziel neu", color="#7a5cae", hovercolor="#9a78d0"); self.bP.on_clicked(self._place)
        axO = self.fig.add_axes([0.415, 0.04, 0.155, 0.07])
        self.bO = Button(axO, "Objekte neu", color="#5c7aae", hovercolor="#78a0d0"); self.bO.on_clicked(self._objects)
        axG = self.fig.add_axes([0.58, 0.04, 0.18, 0.07])
        self.bG = Button(axG, "Ausführen", color="#1f8a5b", hovercolor="#27a96f"); self.bG.on_clicked(self._go)
        axX = self.fig.add_axes([0.77, 0.04, 0.18, 0.07])
        self.bX = Button(axX, "Beenden", color="#8a3030", hovercolor="#a94040"); self.bX.on_clicked(self._exit)
        self.fig.canvas.mpl_connect("close_event", lambda _e: setattr(self.state, "exit", True))
        self._refresh()

    def _set_obj(self, k): self.state.sel = k; self._refresh()
    def _toggle_policy(self, _e):
        self.state.policy = "teacher" if self.state.policy == "self" else "self"; self._refresh()
    def _go(self, _e): self.state.go = True
    def _exit(self, _e): self.state.exit = True

    def _set_tgt(self, i):
        self.state.target_idx = i; self.state.sync_active()
        self.update(self.state.sim.render(self._cam), f"Ziel {i + 1} gewählt"); self._refresh()

    def _place(self, _e):
        self.state.place_selected_random(self._rng)
        self.update(self.state.sim.render(self._cam), f"Ziel {self.state.target_idx + 1} neu platziert"); self._refresh()

    def _objects(self, _e):
        if self._randomize_fn is None:
            return
        if self.state.busy:                                    # mid-episode click -> defer (see state.busy)
            self._pending_randomize = True
            self.live.set_text("Objekte neu — nach der laufenden Episode"); self.fig.canvas.draw_idle()
            return
        self._randomize_fn(); self.update(self.state.sim.render(self._cam), "Objekte neu gewürfelt"); self._refresh()

    def _introduce(self, _e):
        if self._introduce_fn is None:
            return
        if self.state.busy:                                    # mid-episode click -> defer (see state.busy)
            self._pending_introduce = True
            self.live.set_text("Neues Objekt — nach der laufenden Episode"); self.fig.canvas.draw_idle()
            return
        self._introduce_fn(); self._refresh()

    def _toggle_auto(self, _e):
        self.state.auto = not self.state.auto
        self.bAuto.label.set_text("Auto: an" if self.state.auto else "Auto: aus")
        self.bAuto.color = "#2a7a4a" if self.state.auto else "#3a3a5a"
        self.bAuto.ax.set_facecolor(self.bAuto.color); self.fig.canvas.draw_idle()

    def _toggle_choreo(self, _e):
        # cycle FSM -> Netz -> Attractor (Etappe 3: latent-attractor place planning replaces the
        # latent servo; still net-family, the runtime policy drives the grasp) -> FSM
        nxt = {"fsm": "netz", "netz": "attractor", "attractor": "fsm"}
        self.state.choreo = nxt.get(self.state.choreo, "fsm")
        lbl = {"fsm": "Choreo: FSM", "netz": "Choreo: Netz", "attractor": "Choreo: Attraktor"}
        col = {"fsm": "#5a3a3a", "netz": "#2a5a7a", "attractor": "#5a2a7a"}
        self.bCh.label.set_text(lbl[self.state.choreo])
        self.bCh.color = col[self.state.choreo]
        self.bCh.ax.set_facecolor(self.bCh.color); self._refresh()

    def _toggle_goalmode(self, _e):
        self.state.goalmode = "koord" if self.state.goalmode == "latent" else "latent"
        lat = self.state.goalmode == "latent"
        self.bLG.label.set_text("Ziel: Latent" if lat else "Ziel: Koord")
        self.bLG.color = "#2a6a5a" if lat else "#5a4a3a"
        self.bLG.ax.set_facecolor(self.bLG.color); self._refresh()

    def add_discovered(self, idx):
        """Button for a SELF-DISCOVERED object (state.OBJECTS[idx]), appended to the object row."""
        from matplotlib.widgets import Button
        lbl, nm, _m = self.state.OBJECTS[idx]
        ax = self.fig.add_axes([0.035 + 0.115 * idx, 0.150, 0.108, 0.055])
        col = self.state.OBJ_COL.get(nm, "#888888")
        b = Button(ax, lbl, color=col, hovercolor=col); b.label.set_fontsize(7.5)
        b.on_clicked(lambda _e, k=idx: self._set_obj(k)); self._obj_btns[idx] = b
        self._refresh()

    def _toggle(self, _e):
        self.state.action = "push" if self.state.action == "grasp" else "grasp"
        self.bA.label.set_text("Modus: " + ("Schieben" if self.state.action == "push" else "Greifen")); self._refresh()

    def _refresh(self):
        for i, b in self._obj_btns.items():
            lbl = self.state.OBJECTS[i][0]
            b.label.set_text(("● " if i == self.state.sel else "") + lbl)
        self.bPol.label.set_text("Greifer: " + ("Selbst-gelernt" if self.state.policy == "self" else "Teacher"))
        for i, b in self._tgt_btns.items():
            b.color = "#c050c0" if i == self.state.target_idx else "#3a3a44"; b.ax.set_facecolor(b.color)
        self.status.set_text("Befehl:  " + self.state.label()); self.fig.canvas.draw_idle()

    def update(self, frame, txt=""):
        self.imCam.set_data(frame)
        if txt:
            self.live.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def wait(self):
        while not (self.state.go or self.state.exit):
            self.plt.pause(0.05)
        return "exit" if self.state.exit else "go"

    def hold(self):
        self.plt.ioff(); self.plt.show()


def run_self_learning_steering(headless=False):
    """The act23 command-steering GUI: pick an object, toggle Teacher<->Self-learned wrist, watch the arm
    grasp + deliver.  The self-learned wrist (world model) drives the LONG object; cube/L/U use the scripted
    controller exactly as pc_act21/shape_grasp_viz."""
    import pc_cvnn.pc_act16 as act16
    from pc_cvnn.arm_modules import VisualCortexModule, ShapeClassifierModule
    act16.ELONG_RATE = 0.0                                 # don't let run_combined elongate a distractor cube
    # run_combined must NEVER rebuild the scene itself: without PERSIST it calls reset_home()+scatter() at
    # EVERY episode, and scatter() set_object_size()s every body in OBJS to CUBE_HALF.  On the composite L/U
    # that clobbers the FIRST geom only (the L's 56mm arm / one U prong becomes a 24mm cube -> "a segment
    # looks rotated 90 deg" at Ausfuehren), permanently -- _set_sizes() only repairs obj_red/obj_blue.  With
    # PERSIST run_combined just does arm_home()+reposition_strays(): act23 owns ALL placement (setup_long,
    # place_all, the run_one snapshot-restore), so the scene truly persists and no geom is ever resized.
    act16.PERSIST = True
    RES = int(os.environ.get("ACT23_RES", "480"))   # 240 -> 480 am 2026-08-02 (Zweig fovea-res):
    #   zusammen mit ACT_FOVEA_F 16->20 und UNVERAENDERTEM K=4 halbiert sich der Zellabstand im
    #   Weltmass (2x Fovea-Aufloesung) bei gleichem Gesichtsfeld.  Gemessen kostet das im
    #   Fovea-Netz fast nichts (Abtastung 2.9 -> 3.2ms); teuer sind allein die 400 statt 256
    #   ZELLEN der PC-Relaxation.  Das Rendern selbst wird 4x teurer, lag aber bei ~10s je
    #   Episode.  ACHTUNG bei Aenderungen: alle PIXEL-Schwellen des Formklassifikators sind auf
    #   240px geeicht und skalieren ueber ShapeClassifierModule.px_scale mit; die gespeicherte
    #   Homographie wird ueber needs_recal() neu gefittet.
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    NPOS = int(os.environ.get("ACT23_NPOS", "10")); NTRIAL = int(os.environ.get("ACT23_NTRIAL", "5"))
    LONG = "obj_blue"; LONG_HALF = (0.034, 0.009, 0.012)   # clearly a LONG thin bar (not a cube)
    CUBE_BODIES = ["obj_red", "obj_green"]

    print("act23 [viz] — self-learning grasper command-steering" + (" (headless self-test)" if headless else ""))
    _print_run_settings()
    sim = BracketArmSim(render_wh=(RES, RES)); sim.set_reach_site("contact")
    # ACT23_POLICY=teacher starts in teacher mode (headless isolation: execution/perception WITHOUT the
    # young world model's action lottery; the GUI toggle changes it live as before)
    shape_half0 = {nm: sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]].copy()
                   for nm in ("obj_L", "obj_U", "obj_T")}  # pristine XML first-geom half-extents (repair below)

    # PERSISTENCE (user request): the four numpy learners -- body model, shape classifier incl. the
    # self-labelled OPEN-SET classes, world model incl. its trial buffer, runtime policy incl. its DAgger
    # aggregate -- survive across sessions, so lifelong progress (the whole point of the stage-2 DAgger
    # volume) is not lost and the ~10min startup training is skipped.  The hex perception net is NOT
    # persisted (complex PCNetwork; its warmup is ~2min and runs every session).  ACT23_FRESH=1 retrains;
    # ACT23_STATE_PATH overrides the file.  Headless self-tests stay FRESH by default (reproducible gate).
    import pickle
    STATE_PATH = os.environ.get("ACT23_STATE_PATH", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "state", "act23_state.pkl"))
    PERSIST_STATE = (not headless) or os.environ.get("ACT23_STATE_HEADLESS", "0") == "1"
    STATE_SCHEMA = 2       # BUMP whenever a learner's STRUCTURE changes (action/feature dims, new fields)

    def _lg_pack(lg):
        """STAGE 4a persistence: after training, the latent-goal servo only ever touches its cached
        latent GRID + the learned latent-inverse D -- the PC goal-net itself is never called again.
        So persist just those arrays (no PCNetwork pickling risk) + the workspace bounds they were
        trained on (a changed REACH invalidates the world->grid map, like the shape world-check)."""
        return {"gx": lg._gx, "grid_z": lg._grid_z, "D": lg.D, "zsd": lg.zsd,
                "lo": np.asarray(GOAL_LO, float), "hi": np.asarray(GOAL_HI, float)}

    def _lg_unpack(bb):
        lg = LatentGoalServo.__new__(LatentGoalServo)
        lg.gm = None; lg.rng = np.random.default_rng(3); lg.z_g = None
        lg._gx = bb["gx"]; lg._grid_z = bb["grid_z"]; lg.D = bb["D"]
        lg.zmu = 0.0; lg.zsd = bb["zsd"]
        return lg

    def _validate_loaded(b):
        """SAFE versioning (user request): a pickle can LOAD fine and still not fit the current code
        (a class evolved since the save) -- then it would crash mid-session instead of at startup.
        Two gates: explicit schema/structure fields, then a FUNCTIONAL smoke test of every learner on
        dummy inputs.  Returns None if usable, else the human-readable reason."""
        from pc_cvnn.arm_modules.world_model import ACT_DIM as _AD
        if b.get("schema") != STATE_SCHEMA:
            return f"Schema {b.get('schema')} != Code {STATE_SCHEMA}"
        if b.get("dof") != len(ARM3):
            return f"DOF {b.get('dof')} != {len(ARM3)}"
        try:
            w, rt, sc, bmod = b["world"], b["runtime"], b["shape_clf"], b["bm"]
            bmod.body.fk(np.zeros(len(ARM3)))                  # kinematics forward
            cand = w.candidates(0)
            if cand.shape[1] != _AD:
                return f"Aktions-Dim {cand.shape[1]} != {_AD}"
            w.predict(np.zeros(w.feat_dim), cand[:2])          # world-model ensemble forward
            sc.classify(np.zeros(sc.fmu.shape[0]))             # shape head forward
            sc.resolve(np.zeros(sc.fmu.shape[0]))              # open-set gate (exemplars + thresholds)
            if rt.trained:
                rt.predict(np.zeros(11))                       # runtime policy forward
            if b.get("colours") is not None:                   # optional stage-3 colour classes
                b["colours"].classify(np.ones(3) / 3)
            lg = b.get("latent_goal")                          # optional stage-4a goal-latent servo
            if lg is not None:                                 #   (lightweight blob, see _lg_pack)
                if not (np.allclose(lg["lo"], GOAL_LO) and np.allclose(lg["hi"], GOAL_HI)):
                    b["latent_goal"] = None                    # workspace changed -> latent grid stale,
                else:                                          #   retrain (analogue of the world check)
                    _t = _lg_unpack(lg); _t.set_goal(np.array([0.0, 0.15]))
                    _p = _t.servo(np.array([0.02, 0.14]))
                    if _p.shape != (2,) or not np.all(np.isfinite(_p)):
                        return "Ziel-Latent-Servo liefert Unsinn"
            if b.get("self_eval") is not None:                 # optional self-judge (step 1)
                _ok, _d, _f = b["self_eval"].judge([], None, colour_key="x")
                if _ok is not False or _f is not False:
                    return "Selbst-Urteil-Smoke fehlgeschlagen"
        except Exception as e:
            return f"Funktionstest: {type(e).__name__}: {e}"
        return None

    _loaded = None
    if PERSIST_STATE and os.environ.get("ACT23_FRESH", "0") != "1" and os.path.exists(STATE_PATH):
        reason = None
        try:
            with open(STATE_PATH, "rb") as f:
                _b = pickle.load(f)
            reason = _validate_loaded(_b)
            if reason is None:
                _loaded = _b
        except Exception as e:
            reason = f"Laden: {type(e).__name__}: {e}"
        if reason is not None:                                 # keep the old state instead of silently
            bak = STATE_PATH + ".bak"                          #   overwriting it on the next save
            try:
                os.replace(STATE_PATH, bak)
                print(f"  [Persistenz] Zustand passt nicht zum Code ({reason}) — alte Datei -> "
                      f"{os.path.basename(bak)}, trainiere frisch", flush=True)
            except Exception:
                print(f"  [Persistenz] Zustand unbrauchbar ({reason}) — trainiere frisch", flush=True)

    if _loaded is not None:
        bm = _loaded["bm"]
    else:
        bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    state = CommandState23(sim)
    state.policy = os.environ.get("ACT23_POLICY", "self")
    state.choreo = os.environ.get("ACT23_CHOREO", "netz")   # DEFAULT netz seit 2026-08-02 (war fsm):
    #   der Nutzer schaltet beim GUI-Start ohnehin jedes Mal von Hand auf Netz um.  ACT23_CHOREO=fsm
    #   holt die gescriptete Choreographie zurueck (Rauchtests/Vergleichslaeufe nutzen sie weiter).
    panel = None
    if not headless:
        panel = CommandPanel23(state, CAM, RES, rng=np.random.default_rng(7))
        panel.update(sim.render(CAM), "Training: Farb-Wahrnehmung (Würfel + Formen als Distraktoren streuen) ...")
    os.environ["ACT18_SCATTER_EXTRA"] = "obj_L,obj_U"   # scatter the shapes too during vc warmup (consistency)
    # PERSIST the fovea net (task 3): reuse a saved, already-warmed+class-trained HexFovea -> skip the
    # ~2-3 min startup warmup + selection training.  Only meaningful with the learned gaze (FOVEA_NET).
    _pf = (_loaded.get("fovea") if (_loaded is not None and FOVEA_NET) else None)
    if _pf is not None:                                # structural check: a grid/K change since the save
        try:                                           #   makes the persisted net incompatible -> fall back
            ok = (hasattr(_pf, "net") and hasattr(_pf, "sel_head") and len(_pf.cells) == HEX_F * HEX_F
                  and int(_pf.K) == int(os.environ.get("ACT_FOVEA_K", "4")))
        except Exception:
            ok = False
        if not ok:
            print("  [Persistenz] gespeicherte Fovea passt nicht (Gitter/K geändert) -- Warmup läuft neu",
                  flush=True)
            _pf = None
    _fovea_loaded = _pf is not None
    vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=True, pretrained_fovea=_pf,
                                         viz=(panel.fov_viz if panel is not None else None))
    def _fresh_shape_clf():
        if panel is not None:
            panel.update(sim.render(CAM), "Form-Wahrnehmung wird trainiert ...")
        sc = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
        saved = sim.d.mocap_pos.copy(); sc.calibrate(sim)

        def _shape_viz(i, steps, shp):                         # show the form-training live (one shape at a time)
            panel.update(sim.render(CAM), f"Form-Wahrnehmung: {i}/{steps}  (lernt gerade: {shp})")

        sc.train(sim, steps=int(os.environ.get("ACT23_SHAPE_STEPS", "2500")), rng=np.random.default_rng(1),
                 viz_fn=(_shape_viz if panel is not None else None),
                 viz_every=int(os.environ.get("ACT23_SHAPE_VIZ_EVERY", "40")))
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        return sc

    def _shapes_match_world(sc):
        """WORLD-CONSISTENCY post-load check (the versioning philosophy, but vs the WORLD instead of
        the schema): the loaded classifier must still FIND each trained shape in the CURRENT sim.  An
        object-geometry edit silently invalidates the trained |F| manifold -- measured with the
        widened U: the old-U classifier saw it as 27/30 NOVEL and select('U') never matched, so the
        command would run on the privileged fallback forever and the open-set would breed a phantom
        class ON the U.  Each trained shape gets 2 poses; 1 hit each is enough (the healthy
        classifier localises 0-2mm, a stale one misses ALL poses of the changed shape)."""
        keep = {o: (sim.obj_pos(o)[:2].copy(), float(sim.obj_pos(o)[2]), float(sim.obj_yaw(o)))
                for o in ALL}
        saved = sim.d.mocap_pos.copy()
        ok = True
        try:
            for body, key in (("obj_red", "cube"), ("obj_L", "L"), ("obj_U", "U")):
                hits = 0
                for xy, yaw in (((0.0, 0.15), 0.0), ((0.05, 0.18), 0.9)):
                    for o in ALL:
                        sim.set_object(o, [0.5, -0.6], z=0.012)
                    sim.set_object(body, list(xy), z=0.012, yaw=yaw)
                    mujoco.mj_forward(sim.m, sim.d)
                    det = sc.select(sim, key)
                    if det is not None and float(np.linalg.norm(np.asarray(det["pos"])
                                                                - np.asarray(xy))) < 0.03:
                        hits += 1
                if hits == 0:
                    print(f"  [Persistenz] Welt-Check: Form '{key}' wird nicht mehr erkannt", flush=True)
                    ok = False
        finally:
            for o, (xy, z, yaw) in keep.items():
                sim.set_object(o, xy.tolist(), z=z, yaw=yaw)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        return ok

    if _loaded is not None:
        shape_clf = _loaded["shape_clf"]
        # HOMOGRAPHIE VOR dem Welt-Check nachfitten, wenn sich die Bildaufloesung geaendert hat.
        # Sonst laege JEDE wahrgenommene Position um den Aufloesungsfaktor daneben, _shapes_match_world
        # schluege fehl und der Klassifikator wuerde komplett neu trainiert -- wobei die SELBST
        # BENANNTEN offenen Klassen (neu-*) verloren gingen.  H ist reine Kamera-Kalibrierung, kein
        # Gelerntes: neu fitten kostet nichts und rettet die Klassen.
        if shape_clf.needs_recal(sim):
            _sv = sim.d.mocap_pos.copy()
            _n = shape_clf.calibrate(sim)
            sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
            print(f"  [Persistenz] Bildaufloesung geaendert -> Homographie neu gefittet ({_n} Punkte); "
                  f"gelernte Formen und offene Klassen bleiben erhalten", flush=True)
        if _shapes_match_world(shape_clf):
            if panel is not None:
                panel.update(sim.render(CAM), "Form-Wahrnehmung aus gespeichertem Zustand geladen")
        else:
            print("  [Persistenz] Form-Klassifikator passt nicht mehr zur Welt (Objekt-Geometrie "
                  "geändert?) -> NUR die Form-Wahrnehmung wird neu trainiert; Welt-Modell, Policy und "
                  "Farbklassen bleiben erhalten.  Offene Form-Klassen (neu-*) leben im alten "
                  "Deskriptor-Raum und werden verworfen -- neue Objekte werden wieder selbst entdeckt.",
                  flush=True)
            shape_clf = _fresh_shape_clf()
            _loaded["objects"] = []                            # discovered commands were keyed on the old
            _loaded["shape_key"] = {}                          #   classes -> dropped with the old manifold
    else:
        shape_clf = _fresh_shape_clf()

    # ACT23_UDIAG=1: U-GRASP-POINT diagnosis (mechanism-ID, no fix).  The 746-log showed U fails
    # mostly as "greift ins Leere" (47% nicht-gegriffen, |dyaw|~7).  Hypothesis (code-grounded,
    # shape_classifier:599-603): select() returns grasp_xy = MATERIAL nearest the CENTROID, and a U's
    # centroid sits in its concavity -> the grasp lands on a THIN inner rim, not the solid base.  This
    # renders the U occupancy + overlays centroid, the select() grasp point (nearest-material, what
    # runs now) and the DENSEST point (distance-transform max = base) with their material thickness,
    # so the claim is SEEN before any change.  Writes log/u_grasp_diag.png and exits.
    if os.environ.get("ACT23_UDIAG") == "1":
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from scipy import ndimage as _ndi
        sc = shape_clf
        saved_mp = sim.d.mocap_pos.copy()
        poses = [((0.0, 0.15), 0.0), ((0.05, 0.18), 0.9), ((-0.03, 0.13), 2.2)]
        fig, axes = _plt.subplots(1, len(poses), figsize=(4.2 * len(poses), 4.4))
        for ax, (xy, yaw) in zip(np.atleast_1d(axes), poses):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            sim.set_object("obj_U", list(xy), z=0.012, yaw=yaw)
            mujoco.mj_forward(sim.m, sim.d)
            img = sc._render_u8(sim); mask = sc._mask(img)
            labels, n = _ndi.label(mask)
            # largest component = the U
            comp = None; best_a = 0
            for lab in range(1, n + 1):
                c = (labels == lab).astype(np.float32)
                if c.sum() > best_a:
                    best_a = c.sum(); comp = c
            ys, xs = np.nonzero(comp)
            dist = _ndi.distance_transform_edt(comp)                    # material thickness (px)
            dv = dist[ys, xs]
            i_dense = int(np.argmax(dv))                                # thickest = solid base
            if sc.H is not None:
                ctr_w = sc._centroid(comp)
                W = sc._px_to_world(np.column_stack([xs, ys]))
                i_sel = int(np.argmin(np.linalg.norm(W - ctr_w, axis=1)))   # what select() uses
                move_mm = 1000.0 * float(np.linalg.norm(W[i_sel] - W[i_dense]))
                unit = "mm"
            else:                                                       # no homography -> px space
                cpx = np.array([xs.mean(), ys.mean()])
                i_sel = int(np.argmin(np.linalg.norm(np.column_stack([xs, ys]) - cpx, axis=1)))
                move_mm = float(np.hypot(xs[i_sel] - xs[i_dense], ys[i_sel] - ys[i_dense]))
                unit = "px"
            # centroid in px (mean of component)
            cx, cy = xs.mean(), ys.mean()
            thick_sel = float(dist[ys[i_sel], xs[i_sel]])
            thick_dense = float(dv[i_dense])
            ax.imshow(mask, cmap="gray", origin="upper")
            ax.plot(cx, cy, "b+", ms=14, mew=2.5, label="Schwerpunkt (Konkavität)")
            ax.plot(xs[i_sel], ys[i_sel], "rx", ms=13, mew=2.8,
                    label=f"select()-Griff  Dicke {thick_sel:.1f}px")
            ax.plot(xs[i_dense], ys[i_dense], "go", ms=11, mfc="none", mew=2.6,
                    label=f"dichtester (Basis)  Dicke {thick_dense:.1f}px")
            ax.set_title(f"U yaw {yaw:.1f} | Griff->Basis {move_mm:.0f}{unit}", fontsize=9)
            ax.legend(fontsize=7, loc="upper right")
            ax.axis("off")
            print(f"  [UDIAG] yaw {yaw:.2f}: select-Dicke {thick_sel:.1f}px  "
                  f"dichtest-Dicke {thick_dense:.1f}px  Griff->Basis {move_mm:.0f}{unit}", flush=True)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        outp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "log", "u_grasp_diag.png")
        fig.tight_layout(); fig.savefig(outp, dpi=110)
        print(f"  [UDIAG] geschrieben -> {outp}", flush=True)
        raise SystemExit(0)

    # STAGE 4a: the place TARGET as a LATENT state (the act6 goal-as-prior, wired into the GUI).
    # The commanded goal is ENCODED once into the goal-module latent; while the object is carried,
    # the place target is DRIVEN by the latent DIFFERENCE between goal latent and the hand's latent
    # (learned latent-inverse) -- execution converges where the LATENTS MATCH, not on a decoded
    # coordinate (act-b: side-steps decode bias; RoPE latent = near-linear -> servo isolated ~0mm).
    # GUI toggle "Ziel: Latent/Koord"; env ACT23_GOAL=koord restores the coordinate place.
    _lgb = _loaded.get("latent_goal") if _loaded is not None else None
    if _lgb is not None:
        lgoal = _lg_unpack(_lgb)
        print("  [Stufe 4] Ziel-Latent-Servo aus gespeichertem Zustand geladen", flush=True)
    else:
        if panel is not None:
            panel.update(sim.render(CAM), "Stufe 4: Ziel-Latent wird trainiert (Goal-Modul + Latent-Inverse) ...")
        _gm = GoalModule2D(rng=np.random.default_rng(7))
        _gm.pretrain(int(os.environ.get("ACT23_GM_STEPS", "8000")))
        lgoal = LatentGoalServo(_gm, rng=np.random.default_rng(3))
        _rec = lgoal.train(steps=4000)
        print(f"  [Stufe 4] Ziel-Latent bereit (RoPE-Latent={_gm.rope}): "
              f"Latent-Inverse-Babble {_rec:.1f} mm", flush=True)
    lgoal_lang = LatentGoalLanguage(lgoal)
    lat_dyn = LatentDynamicsModule(latent_dim=10, action_dim=4, rng=np.random.default_rng(8))
    if _loaded is not None and "latent_dynamics" in _loaded:
        lat_dyn.unpack(_loaded["latent_dynamics"])
        print("  [Etappe 2] Latent-Dynamics Übergangsmodell aus Zustand geladen", flush=True)
    lat_attractor = LatentAttractorController(lgoal, lat_dyn, rng=np.random.default_rng(9))
    print("  [Etappe 3] Latent-Attraktor Steuerung bereit (kontinuierliches Latent-Planning)", flush=True)

    # STAGE 4b: the planner DREAMS its practice targets (act21 CuriosityPlanner.dream, wired into the
    # auto-run): candidate goals are scored by DISTANCE-NOVELTY in the GOAL-LATENT space -- the SAME
    # latent the 4a place servo executes on (lgoal.encode_world; one latent space for dreaming AND
    # acting; the dreamed latent IS the executed z_g, since post_goal_fn encodes the same position).
    # The dream memory (visited latents) PERSISTS across sessions -- the agent remembers what it has
    # already practiced.  ACT23_DREAM=0 restores the coordinate-novelty target pick.
    DREAM = os.environ.get("ACT23_DREAM", "1") == "1"
    dream_nov = DistanceNovelty()
    if _loaded is not None:
        dream_nov.seen = [np.asarray(z) for z in _loaded.get("dream_seen", [])]

    # SELF-JUDGED OUTCOME (step 1 of the self-improvement plan, user request): after every episode
    # the agent judges its own result -- commanded object found via its SELF-LABELLED classes, the
    # distance to the wish measured as GOAL-LATENT difference through the learned latent-inverse.
    # This step only INSTALLS the judge and MEASURES agreement with the privileged verdict; the
    # learners' outcome labels stay privileged until the agreement is proven (steps 2/3).
    seval = (_loaded.get("self_eval") if _loaded is not None else None) or SelfEvalModule(tol=act16.TOL)
    objmem = ObjectMemoryModule()                             # per-episode predictive belief for the gaze

    # self-supervised world model for the GRASP WRIST (collect own trials, then train).
    # OPEN-WORLD situation features -- ONE camera perception path (|F| pipeline) for EVERY object:
    #   [pos(2), cos/sin(2*yaw), cos/sin(4*yaw4), desc_embed(NH)]
    # yaw (k=2 phase, mod pi) carries an ELONGATED object's axis; yaw4 (k=4 phase, mod pi/2) carries a
    # SQUARE's orientation -- k=2 is DEGENERATE on a cube, and the fixed teacher wrist (WRIST_TGT mod
    # 90deg) is exactly what slips off DIAGONAL cubes now that the continuous scene keeps their random
    # yaw (scatter() used to re-place them axis-aligned each episode, masking the gap).  The descriptor
    # embedding (no class one-hot) lets this ONE model absorb trials from any form.  (The former
    # ObjectOrientationModule features are subsumed by the k=2 phase -- one perception path, no oo.)
    world = (_loaded["world"] if _loaded is not None else
             WorldModelModule(k=5, off_max=0.008, rng=np.random.default_rng(2),
                              feat_dim=6 + shape_clf.NH + NB_DIM))
    _n_mig = world.ensure_feat_dim(6 + shape_clf.NH + NB_DIM, NB_NEUTRAL)   # geladene Puffer nachziehen
    if _n_mig:
        print(f"  [Schema] Nachbar-Information ergaenzt: {_n_mig} bestehende Zeilen migriert "
              f"(gueltig-Flag 0 -- sie hatten die Information nie)", flush=True)
    #   off_max>0 (STAGE-1 de-scripting): the grasp-point OFFSET dims are live -- the model can learn to
    #   grasp a form off its perceived grasp point; grip+gentle action dims replace the obj_U runtime rules.

    # STAGE 2 de-scripting (user request): a LEARNED runtime policy replaces the scripted choreography.
    # EVERY episode -- startup trials, manual commands, the curiosity auto-run -- is lifelong DAgger data:
    # each VISITED state is labelled by the MARKOVIAN reactive teacher (act16.reactive_subgoal; the act19
    # lesson: the stateful phase machine's labels degrade DAgger).  "Choreo: Netz" (GUI toggle /
    # ACT23_CHOREO=netz) lets the POLICY drive the sub-goals incl. the gripper; guards stay on by default
    # (train-with-guard) -- verify guard-free with ACT16_CLOSE_GUARD=0 ACT16_REFLEX=0.
    runtime = _loaded["runtime"] if _loaded is not None else RuntimePolicyModule(rng=np.random.default_rng(4))

    # STAGE 3 (user request): OPEN-SET COLOURS -- fully self-labelled, no teacher colour set anywhere.
    # Scene glances feed component CHROMATICITIES; classes are self-named ("farbe-N") and bound to the
    # body they were discovered on (plumbing aid, like the form registration).  Concrete de-crutching:
    # the LONG object is localised by its self-labelled colour class instead of privileged sim access.
    # OPTIONAL blob keys (old saves load fine without them -- no schema bump, the user's running
    # lifelong state survives).
    colours = (_loaded.get("colours") if _loaded is not None else None) or ColourOpenSetModule()
    colour_of_body = dict(_loaded.get("colour_of_body", {})) if _loaded is not None else {}
    # SELF-HEAL pre-0a539ac collision damage in persisted states: birth names were len+1, so a
    # name could be re-issued -> DUPLICATE entries in the list / entries without a class (index/
    # remove then operate on the wrong occurrence).  Sync the list to the dict, once, at load.
    _cn = [n for n in dict.fromkeys(colours.names) if n in colours.classes]
    if _cn != colours.names:
        print(f"  [Persistenz] Farbklassen-Liste repariert ({len(colours.names)} -> {len(_cn)} "
              f"Einträge: Duplikate/Verwaiste aus der Vor-Fix-Ära entfernt)", flush=True)
        colours.names = _cn
    _stale = {b: c for b, c in colour_of_body.items() if c not in colours.classes}
    for b in _stale:                                           # a binding to a merged-away class can
        del colour_of_body[b]                                  #   never match again -> drop, re-binds
    if _stale:                                                 #   itself at the next discovery glance
        print(f"  [Persistenz] verwaiste Farb-Bindungen entfernt: {_stale}", flush=True)

    # ACT23_REDDIAG=1: RED<->L CONFUSION diagnosis (mechanism-ID, no fix).  The user watched the red
    # cube command grasp the nearby L instead; the 24-ep GUI log shows red LOSING the fovea servo in
    # 5 of 6 episodes (the [Fovea-Servo] line only prints on >0 frames -> the colour-keyed tracker
    # found ZERO candidates all episode) and twice reporting "Blob-Verschmelzung erkannt".  The
    # persisted classes are CLEAN (farbe-1 sits 0.023 from true red), so this is NOT class drift.
    # Code-grounded hypothesis (shape_classifier:623): a component's chroma is the MEAN over all its
    # pixels -- red fused with the orange L into ONE component averages to a mixed tone matching
    # NEITHER class -> 0 candidates -> perceive() falls back to the old trained vc hex code (:1437),
    # which is documented to fire on foreign objects.  Fix candidate to validate here: split the
    # component's PIXELS by the self-learned colour classes (the same continuity idea self_eval uses
    # after release, but anchored on COLOUR so it works BEFORE the grasp, with no hand anchor).
    # Writes log/red_l_diag.png and exits.
    if os.environ.get("ACT23_REDDIAG") == "1":
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from scipy import ndimage as _ndi
        sc = shape_clf
        saved_mp = sim.d.mocap_pos.copy()
        ck_red, ck_L = colour_of_body.get("obj_red"), colour_of_body.get("obj_L")
        cnames = [n for n in colours.names if n in colours.classes]
        MU = np.array([colours.classes[n]["mu"] for n in cnames])   # vectorised per-pixel classify
        print(f"  [REDDIAG] Bindungen: obj_red='{ck_red}' obj_L='{ck_L}' | {len(cnames)} Farbklassen "
              f"| TH={colour_openset.TH}", flush=True)
        gaps = [0.070, 0.050, 0.038, 0.028]
        fig, axes = _plt.subplots(1, len(gaps), figsize=(4.3 * len(gaps), 4.8))
        for ax, gap in zip(np.atleast_1d(axes), gaps):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            rp = np.array([-0.015, 0.155])
            sim.set_object("obj_red", rp.tolist(), z=0.012)
            sim.set_object("obj_L", (rp + np.array([gap, 0.0])).tolist(), z=0.012, yaw=0.4)
            mujoco.mj_forward(sim.m, sim.d)
            truth = np.asarray(sim.obj_pos("obj_red")[:2], float)
            # (a) what the agent ACTUALLY sees today: whole-component chroma -> class
            dets = sc.perceive_all(sim)
            hits = [d for d in dets if colours.classify(d["chroma"])[0] == ck_red]
            # (b) the same scene at pixel level, to test the colour split
            sc._park_markers(sim)
            img = sc._render_u8(sim); mask = sc._mask(img)
            labels, n = _ndi.label(mask)
            # the component containing the true red centre
            rpx = sc._world_to_px(truth[None, :])[0] if sc.H is not None else None
            lab_red = 0
            if rpx is not None:
                yy, xx = int(round(rpx[1])), int(round(rpx[0]))
                if 0 <= yy < labels.shape[0] and 0 <= xx < labels.shape[1]:
                    lab_red = int(labels[yy, xx])
            if lab_red == 0:                                    # centre landed off-mask -> largest comp
                sizes = _ndi.sum(mask, labels, range(1, n + 1))
                lab_red = int(np.argmax(sizes)) + 1 if n else 0
            comp = (labels == lab_red)
            ys, xs = np.nonzero(comp)
            prgb = img[ys, xs].astype(float)
            psum = prgb.sum(1, keepdims=True)
            pch = np.divide(prgb, psum, out=np.zeros_like(prgb), where=psum > 1e-6)
            dmat = np.linalg.norm(pch[:, None, :] - MU[None, :, :], axis=2)   # (npx, nclass)
            nearest = dmat.argmin(1); ndist = dmat.min(1)
            assigned = np.where(ndist <= colour_openset.TH, nearest, -1)
            i_red = cnames.index(ck_red) if ck_red in cnames else -2
            sel = assigned == i_red
            # component-level truth: is this ONE blob holding BOTH objects?
            comp_ch = prgb.mean(0) / max(prgb.mean(0).sum(), 1e-6)
            comp_cls, comp_d = colours.classify(comp_ch)
            comp_ctr = sc._centroid(comp.astype(np.float32)) if sc.H is not None else None
            err_whole = (1000.0 * float(np.linalg.norm(np.asarray(comp_ctr, float) - truth))
                         if comp_ctr is not None else float("nan"))
            err_split = float("nan"); split_ctr = None
            if sel.sum() >= 8 and sc.H is not None:
                Wsel = sc._px_to_world(np.column_stack([xs[sel], ys[sel]]))
                split_ctr = Wsel.mean(0)
                err_split = 1000.0 * float(np.linalg.norm(split_ctr - truth))
            # (c) the SHIPPED method on the same scene -- validates the real code path, not this rehearsal
            real = sc.perceive_colour(sim, colours, ck_red)
            err_real, n_real = float("nan"), 0
            if real:
                rbest = min(real, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - truth)))
                err_real = 1000.0 * float(np.linalg.norm(np.asarray(rbest["pos"]) - truth))
                n_real = int(rbest["area"])
            print(f"  [REDDIAG] Lücke {gap*1000:.0f}mm: {n} Komponenten, Rot-Komp {comp.sum():.0f}px "
                  f"-> Klasse '{comp_cls}' (d={comp_d:.3f}); perceive_all-Treffer auf '{ck_red}': "
                  f"{len(hits)} | Pixel-Split: {sel.sum()}/{len(xs)} px als '{ck_red}' | "
                  f"Fehler ganz {err_whole:.0f}mm vs Split {err_split:.0f}mm | "
                  f"perceive_colour(): {len(real)} Det, {n_real}px, Fehler {err_real:.0f}mm", flush=True)
            ov = np.zeros(mask.shape + (3,), float)
            ov[..., 0] = mask * 0.35
            ov[..., 1] = mask * 0.35
            ov[..., 2] = mask * 0.35
            ov[ys[sel], xs[sel]] = [1.0, 0.2, 0.2]              # pixels the split calls RED
            ax.imshow(ov, origin="upper")
            if rpx is not None:
                ax.plot(rpx[0], rpx[1], "w+", ms=15, mew=2.5, label="wahres Rot")
            ax.plot(xs.mean(), ys.mean(), "yo", ms=10, mfc="none", mew=2.4,
                    label=f"Komp-Schwerpunkt ({err_whole:.0f}mm)")
            if split_ctr is not None:
                spx = sc._world_to_px(split_ctr[None, :])[0]
                ax.plot(spx[0], spx[1], "cs", ms=10, mfc="none", mew=2.4,
                        label=f"Farb-Split ({err_split:.0f}mm)")
            ax.set_title(f"Lücke {gap*1000:.0f}mm | {n} Komp | Komp-Klasse '{comp_cls}'", fontsize=9)
            ax.legend(fontsize=7, loc="upper right"); ax.axis("off")
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        outp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "log", "red_l_diag.png")
        fig.tight_layout(); fig.savefig(outp, dpi=110)
        print(f"  [REDDIAG] geschrieben -> {outp}", flush=True)

        # BENCH: the same question END-TO-END over many random neighbour constellations, WITHOUT the
        # learning loop.  A full A/B could not answer it: both arms ran bit-identical until the split
        # first fired, then the trajectories diverged (different curiosity picks, different object
        # counts) and the delivery delta became trajectory noise -- and the red/L fusion never even
        # occurred headless.  This isolates PERCEPTION: place the L at a random offset around the red
        # cube, ask what the colour path returns with and without the split, and score against truth.
        rng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "11")))
        N = int(os.environ.get("ACT23_REDBENCH_N", "120"))
        stat = {"fused": 0, "old_ok": 0, "old_err": [], "new_ok": 0, "new_err": [], "rec": 0}
        for _ in range(N):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            rp = np.array([rng.uniform(-0.08, 0.08), rng.uniform(0.11, 0.20)])
            ang = rng.uniform(0, 2 * np.pi)
            gap = rng.uniform(0.022, 0.075)                # spans fused .. clearly separate
            sim.set_object("obj_red", rp.tolist(), z=0.012)
            sim.set_object("obj_L", (rp + gap * np.array([np.cos(ang), np.sin(ang)])).tolist(),
                           z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
            mujoco.mj_forward(sim.m, sim.d)
            truth = np.asarray(sim.obj_pos("obj_red")[:2], float)
            saved2 = sim.d.mocap_pos.copy()
            dets = sc.perceive_all(sim)
            old = [d for d in dets if d["pos"] is not None
                   and colours.classify(d["chroma"])[0] == ck_red]
            if not old:
                stat["fused"] += 1                         # today: 0 candidates -> vc fallback (grasps L)
                new = sc.perceive_colour(sim, colours, ck_red)
                if new:
                    stat["rec"] += 1
                    b = min(new, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - truth)))
                    e = 1000.0 * float(np.linalg.norm(np.asarray(b["pos"]) - truth))
                    stat["new_err"].append(e); stat["new_ok"] += int(e < 15.0)
            else:
                b = min(old, key=lambda d: colours.classify(d["chroma"])[1])
                e = 1000.0 * float(np.linalg.norm(np.asarray(b["pos"]) - truth))
                stat["old_err"].append(e); stat["old_ok"] += int(e < 15.0)
            sim.d.mocap_pos[:] = saved2; mujoco.mj_forward(sim.m, sim.d)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        ne, oe = stat["new_err"], stat["old_err"]
        print(f"\n  [REDBENCH] {N} zufällige Rot+L-Konstellationen (Lücke 22-75mm, kein Lernen):", flush=True)
        print(f"    nicht verschmolzen: {N - stat['fused']}  -> alter Pfad findet Rot, "
              f"Median {np.median(oe) if oe else float('nan'):.0f}mm, <15mm: {stat['old_ok']}/{len(oe)}",
              flush=True)
        print(f"    VERSCHMOLZEN      : {stat['fused']}  -> alter Pfad findet 0 Kandidaten "
              f"(= vc-Rückfall, greift den Nachbarn)", flush=True)
        print(f"      davon vom Farb-Split gerettet: {stat['rec']}/{stat['fused']}, "
              f"Median {np.median(ne) if ne else float('nan'):.0f}mm, <15mm: {stat['new_ok']}/{len(ne)}",
              flush=True)
        raise SystemExit(0)

    # ACT23_TDIAG=1: FORM-BLINDNESS diagnosis for the open-class object (mechanism-ID, no fix).  In the
    # 120-ep GUI run "Neue Form 7" lost the fovea servo in 7 of 13 episodes (54%) vs 3 of 107 for every
    # other object (p<1e-5) -- the tracker keys on d["shape"]==key and found ZERO candidates all episode.
    # Unlike the red/L case this is the FORM path, so the colour split cannot help.  Class OVERBIRTH is
    # ruled out (0 class pairs closer than novel_th), but neu-72 sits at EXACTLY novel_th (7.72) from the
    # bound class neu-9, with neu-34/78/98/95 at 11-13.  Hypothesis: the descriptor of obj_T WANDERS with
    # pose/neighbour, so resolve() lands on a competitor or on None (novel) instead of neu-9.  This renders
    # obj_T over many poses -- alone and with a close neighbour -- and tallies what it is actually called.
    if os.environ.get("ACT23_TDIAG") == "1":
        sc = shape_clf
        _sk = dict((_loaded or {}).get("shape_key", {}))       # persisted body -> open-class binding
        NOVEL_BODY = next(iter(_sk), "obj_T")                  # (NOVEL_BODY itself is defined further down)
        key = _sk.get(NOVEL_BODY)
        print(f"  [TDIAG] {NOVEL_BODY} gebunden an Formklasse '{key}' | novel_th={sc.novel_th:.2f} "
              f"| offene Klassen {len(sc.open)}", flush=True)
        saved_mp = sim.d.mocap_pos.copy()
        rng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "11")))
        N = int(os.environ.get("ACT23_TDIAG_N", "80"))
        import collections
        for scenario in ("allein", "mit Nachbarn"):
            tally = collections.Counter(); dists = {"eigen": [], "beste_fremd": []}
            tally_fix = collections.Counter()
            found = 0
            for _ in range(N):
                for o in ALL + [NOVEL_BODY]:
                    sim.set_object(o, [0.5, -0.6], z=0.012)
                tp = np.array([rng.uniform(-0.08, 0.08), rng.uniform(0.11, 0.20)])
                sim.set_object(NOVEL_BODY, tp.tolist(), z=0.012, yaw=float(rng.uniform(0, 2*np.pi)))
                if scenario != "allein":                       # a neighbour at fusion distance
                    ang = rng.uniform(0, 2*np.pi)
                    gap = rng.uniform(0.022, 0.055)
                    sim.set_object("obj_L", (tp + gap*np.array([np.cos(ang), np.sin(ang)])).tolist(),
                                   z=0.012, yaw=float(rng.uniform(0, 2*np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                dets = sc.perceive_all(sim)
                if not dets:
                    tally["KEINE Detektion"] += 1; continue
                # the detection nearest the true obj_T position is the one that matters
                d = min(dets, key=lambda q: 1e9 if q["pos"] is None
                        else float(np.linalg.norm(np.asarray(q["pos"]) - tp)))
                if d["pos"] is None or float(np.linalg.norm(np.asarray(d["pos"]) - tp)) > 0.05:
                    tally["nicht lokalisiert"] += 1; continue
                found += 1
                nm = d["shape"]
                tally[nm if nm is not None else "None (novel)"] += 1
                # how far is this descriptor from its OWN class vs the best competitor?
                de = sc.desc_embed(d["desc"]) if d.get("desc") is not None else None
                if d.get("desc") is not None:
                    best = {}
                    for cn, ex in sc.open.items():
                        A = np.asarray(ex, float)
                        best[cn] = float(np.linalg.norm(A - np.asarray(d["desc"], float), axis=1).min())
                    if key in best:
                        dists["eigen"].append(best[key])
                        others = [v for c, v in best.items() if c != key]
                        if others:
                            dists["beste_fremd"].append(min(others))
                # the SHIPPED recovery (ACT23_FORM_SPLIT) on the same scene, for the A/B in one view
                ck = colour_of_body.get(NOVEL_BODY)
                sp = sc.perceive_colour(sim, colours, ck, with_form=True) if ck else []
                if sp:
                    b = min(sp, key=lambda q: float(np.linalg.norm(np.asarray(q["pos"]) - tp)))
                    tally_fix[b["shape"] if b["shape"] is not None else "None (novel)"] += 1
                else:
                    tally_fix["kein Farb-Split"] += 1
            print(f"\n  [TDIAG] {scenario}: {N} Posen, lokalisiert {found}")
            for nm, c in tally.most_common():
                mark = "  <== KORREKT" if nm == key else ("  <== BLIND" if nm != key else "")
                print(f"      als '{nm}' erkannt: {c:3d} = {100.0*c/N:5.1f}%{mark}", flush=True)
            if dists["eigen"]:
                e = np.array(dists["eigen"]); f = np.array(dists["beste_fremd"])
                print(f"      Deskriptor-Abstand zu '{key}': median {np.median(e):.2f} "
                      f"p90 {np.percentile(e,90):.2f} | bester Fremd-Abstand median {np.median(f):.2f}"
                      f" | novel_th {sc.novel_th:.2f}")
                print(f"      Anteil mit Abstand>novel_th zur eigenen Klasse: "
                      f"{100.0*np.mean(e > sc.novel_th):.0f}%  (= wird NOVEL statt '{key}')")
                print(f"      Anteil wo ein FREMD naeher liegt: {100.0*np.mean(f < e):.0f}%")
            print(f"    -- MIT Form-Split (ACT23_FORM_SPLIT: Form auf dem farb-getrennten Teil) --")
            for nm, c in tally_fix.most_common():
                mark = "  <== KORREKT" if nm == key else ""
                print(f"      als '{nm}': {c:3d} = {100.0*c/N:5.1f}%{mark}", flush=True)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        raise SystemExit(0)

    def save_state():
        """Persist the four learners + the self-discovered command objects (every episode; cheap)."""
        if not PERSIST_STATE:
            return
        try:
            os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
            base = {nm for _l, nm, _m in CommandState23.OBJECTS}
            blob = {"schema": STATE_SCHEMA, "dof": len(ARM3),
                    "bm": bm, "shape_clf": shape_clf, "world": world, "runtime": runtime,
                    "colours": colours, "colour_of_body": dict(colour_of_body),
                    "latent_goal": _lg_pack(lgoal),
                    "latent_dynamics": lat_dyn.pack(),
                    "dream_seen": [np.asarray(z) for z in dream_nov.seen],
                    "self_eval": seval,

                    "objects": [o for o in state.OBJECTS if o[1] not in base],
                    "shape_key": {k: v for k, v in state.SHAPE_KEY.items()
                                  if k not in CommandState23.SHAPE_KEY}}
            if FOVEA_NET:                                      # task 3: persist the warmed+class-trained
                blob["fovea"] = vc.fovea                        #   hex fovea (only when the learned gaze is
                #   used) so later sessions skip the ~2-3 min warmup + selection + class training
            with open(STATE_PATH, "wb") as f:
                pickle.dump(blob, f)
        except Exception as e:
            print(f"  [Persistenz] Speichern fehlgeschlagen: {e}", flush=True)

    def choreo_log(s, _aim, _j5):
        runtime.observe(s, act16.reactive_subgoal(s))      # label the VISITED state, ignore the FSM's own
        #   (aim, j5): the reactive teacher is a pure function of state, the phase machine is not

    def situation_feats(cmd):
        """PERCEIVED situation of `cmd` for the world model (None if the camera can't find it).  The
        privileged position is only a MATCHING aid; the features themselves are the detection's.
        The matched detection (incl. its mask-sampled grasp_cands) is kept on
        situation_feats.last_det for the grasp-point candidate selection in run_one."""
        p_ref = sim.obj_pos(cmd)[:2]
        situation_feats.last_det = None
        saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
        dets = shape_clf.perceive_all(sim, cands=True)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        dets = [d for d in dets if d["pos"] is not None]
        if not dets:
            return None
        best = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - p_ref)))
        if float(np.linalg.norm(np.asarray(best["pos"]) - p_ref)) > 0.05:
            return None                                    # nearest blob is a DIFFERENT object -> no honest read
        situation_feats.last_det = best
        y2, y4 = float(best["yaw"]), float(best["yaw4"])
        # ORIENTATION THROUGH THE FOVEA (user's long-term goal, first wired lever): the k=2 RING
        # PHASE the overview path reads is NOISY (measured consistency p50: long 36deg, L 21, T 45,
        # U 26); the FOVEA-style read -- local window at the tracked object + identity chroma gate +
        # PCA long axis in world coords -- reads long 1.0deg, L 1.1, T 4.9, U 11.8.  Replace the k=2
        # slots (same dims, no schema break; the old rows' yaw was ~noise, the model had little to
        # unlearn).  Cubes keep the k=4 ring phase (PCA is degenerate for squares).
        if os.environ.get("ACT23_FOVEA_YAW", "1") == "1":
            _c = colour_of_body.get(cmd)
            _mu = (np.asarray(colours.classes[_c]["mu"], float)
                   if _c is not None and _c in colours.classes else None)
            saved = sim.d.mocap_pos.copy()                 # yaw_at parks the markers -> restore
            _r = shape_clf.yaw_at(sim, np.asarray(best["pos"], float), mu=_mu,
                                  engine=os.environ.get("ACT23_YAW_SRC", "cells"))
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if _r is not None:
                y2 = float(_r[0])
        return np.concatenate([np.asarray(best["pos"], float),
                               [np.cos(2 * y2), np.sin(2 * y2), np.cos(4 * y4), np.sin(4 * y4)],
                               shape_clf.desc_embed(best["desc"]),
                               _neighbour_feats(best, dets)])

    def _neighbour_feats(best, dets):
        """NACHBAR-INFORMATION fuers Welt-Modell (Nutzerwunsch, in ModulViz die gestrichelte Kante
        ShapeClassifier -> SelfEval).  Der User hat wiederholt beobachtet, was hier fehlt: die Klaue
        SCHIEBT beim Schliessen ein Objekt weg, sie RAMMT beim Tragen einen Nachbarn, und zwei nahe
        Objekte VERSCHMELZEN zu einem Blob (Farb-/Form-Split).  All das haengt an der Nachbarschaft,
        und das Welt-Modell sah bisher nur das Zielobjekt.

        Kostet NICHTS: perceive_all liefert ohnehin ALLE Detektionen, situation_feats warf sie bisher
        weg.  Kein zusaetzliches Rendern, keine privilegierte Information -- dieselbe eigene Kamera.
        (Nicht aus der FOVEA: die ist der Aufmerksamkeitspfad auf das EINE Zielobjekt.)

        5 Dimensionen: [gueltig, d_nah, cos phi, sin phi, n_nah]
          gueltig  1.0 = diese Zeile hat echte Nachbar-Information (alte Zeilen: 0.0, s.
                   ensure_feat_dim -- ein erfundener Sachwert waere eine Luege im Trainingssatz)
          d_nah    Abstand zum naechsten Nachbarn, auf NB_DMAX gedeckelt
          phi      RICHTUNG dorthin, im OBJEKTRAHMEN (gegen die eigene yaw-Achse gedreht) und als
                   PHASE kodiert -- dieselbe Konvention wie Wrist und Neigung.  Objekt-relativ, weil
                   "Nachbar auf der Zinkenseite" etwas anderes ist als "Nachbar hinter mir", und das
                   nur im Objektrahmen ausdrueckbar ist.
          n_nah    wieviele Nachbarn innerhalb NB_DMAX liegen (Gedraenge)"""
        v = np.array([0.0, NB_DMAX, 1.0, 0.0, 0.0])
        if not NEIGHBOURS:
            return v
        p = np.asarray(best["pos"], float)
        d = [(float(np.linalg.norm(np.asarray(o["pos"], float) - p)), o)
             for o in dets if o is not best and o.get("pos") is not None]
        v[0] = 1.0                                    # gemessen -- auch "keine Nachbarn" ist Information
        near = [x for x in d if x[0] <= NB_DMAX]
        v[4] = float(len(near))
        if d:
            dist, o = min(d, key=lambda x: x[0])
            v[1] = float(min(dist, NB_DMAX))
            rel = np.asarray(o["pos"], float) - p
            phi = float(np.arctan2(rel[1], rel[0])) - float(best.get("yaw", 0.0))   # Objektrahmen
            v[2], v[3] = np.cos(phi), np.sin(phi)
        return v

    bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, LONG)
    # ACT23_SEED (default 7 = historical behaviour): scene placement + auto target picks.  Parallel
    # label-harvest WORKERS (act23_dose_workers.py) start from the SAME state pickle with the same
    # pickled module rngs -- without distinct seeds here they would replay bit-identical episodes
    # and the parallelism would collect the same data W times (user's 8%-CPU observation).
    crng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "7"))); act16.run_combined._quiet = True

    def park_all():
        sim.reset_home()
        for o in ALL:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")]] = np.array([0.012] * 3)
        sim.set_target_marker([0.0, -0.6], z=-0.05)

    def setup_obj(cmd, p, yaw):
        park_all()
        if cmd == LONG:
            sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(LONG_HALF, float)
            z = float(LONG_HALF[2])
        else:
            z = 0.012
        sim.set_object(cmd, p, z=z, yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        sim.set_target_marker(TARGET, z=0.001)

    def grasp_trial(cmd, wrist, gxy, grip=None, gentle=False):
        wf = None if wrist is None else (lambda s, _w=wrist: _w)
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=cmd, force="grasp",
                                  perceive_fn=lambda c: (gxy, None, "grasp"), policy_fn=None, servo=False,
                                  goal_fn=lambda c, o: TARGET, rescatter=False, wrist_fn=wf,
                                  grip_close=grip, carry_gentle=bool(gentle),
                                  log_fn=choreo_log)         # startup trials feed the runtime policy too
        return int(d)

    def grasp_gxy(cmd):
        """The PERCEIVED grasp point for a trial: shapes via select() (a U's body centre lies in its
        concavity, on no material -- privileged centre grasps would poison the trials); else privileged."""
        key = state.SHAPE_KEY.get(cmd)
        if key is not None:
            saved = sim.d.mocap_pos.copy()                     # select() parks the markers -> restore
            det = shape_clf.select(sim, key)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if det is not None:
                return np.asarray(det["grasp_xy"], float)
        return sim.obj_pos(cmd)[:2]

    def collect_trials(cmd, label, yaw_hi):
        """Self-supervised trials on `cmd`: random pose + yaw, RANDOM action (wrist + grasp-point offset
        + grip close-angle + gentle flag), the OWN delivered/not outcome as the only label.
        act16.OBJS=[cmd]: this object IS the scene -- park_all() parks the others OUTSIDE run_combined's
        stray bounds, and with them in OBJS reposition_strays() would drop them back onto the table as
        surprise distractors.  (Restored to all objects for the steering scene.)"""
        act16.OBJS = [cmd]
        print(f"  collecting OWN trials: {label} ({NPOS}x{NTRIAL}) ...")
        for j in range(NPOS):
            p = rand_pos(crng); yaw = crng.uniform(0, yaw_hi); setup_obj(cmd, p, yaw)
            fe = situation_feats(cmd)
            if fe is None:
                continue                                       # camera can't see it here -> no honest trial
            for t in range(NTRIAL):
                w = crng.uniform(0, np.pi); setup_obj(cmd, p, yaw)
                if t == 0:                                     # anchor trial ON the structured candidate
                    off = np.zeros(2); grip = 0.0; gentle = 0.0   # grid (offset-0, firm grip): the LCB
                    #   prefers those candidates, so the model needs EVIDENCE there -- purely random
                    #   trials left them unsampled and a young model picked edge offsets + wide grips
                    #   ("Greifer schliesst nicht weit genug", carried objects slipped mid-carry)
                else:
                    off = crng.uniform(-0.008, 0.008, 2)
                    grip = float(crng.uniform(0.0, 0.4)); gentle = float(crng.integers(2))
                ok = grasp_trial(cmd, w, grasp_gxy(cmd) + off, grip, gentle)
                world.observe(fe, action_vec(off[0], off[1], w, grip, gentle), ok)
            if panel is not None and j % 2 == 0:
                panel.update(sim.render(CAM), f"Selbst-Lernen ({label}): {(j + 1) * NTRIAL}/{NPOS * NTRIAL} Versuche")

    if _loaded is not None:
        print(f"  [Persistenz] Zustand geladen: Welt-Modell {world.n()} Versuche, Runtime-Policy "
              f"{runtime.n()} Samples, offene Klassen {shape_clf.open_names} — Startup-Training übersprungen",
              flush=True)
        _bad = runtime.sanitize()                              # HEAL a DAgger buffer polluted by off-table
        if _bad:                                               # perception-glitch states (897ca5a servo bug
            runtime.train(epochs=200)                          # logged px-as-metres -> a quarter of the buffer
            save_state()                                       # went absurd + wrecked the fitted policy)
            print(f"  [Reparatur] {_bad} vergiftete Policy-Samples (off-table) entfernt + Policy neu "
                  f"trainiert ({runtime.n()} sauber) — Netz-Choreo war daneben-greifend", flush=True)
    else:
        collect_trials(LONG, "langes Objekt", np.pi)
        collect_trials("obj_red", "Würfel, auch diagonal", np.pi / 2)   # cube yaw mod pi/2 (square symmetry);
        #   the descriptor is COLOUR-agnostic, so red-cube trials transfer to the green cube too
        collect_trials("obj_L", "L-Form", 2 * np.pi)                    # stage 1: the SHAPES get own trials too
        collect_trials("obj_U", "U-Form", 2 * np.pi)                    #   (self wrist/grip/offset instead of
        #   the teacher rules; the grip+gentle dims must SEE both regimes to learn the U's contingency)
        world.train(epochs=600)
        print(f"  world model trained on {world.n()} own trials.")
        runtime.train(epochs=400)
        print(f"  runtime policy (Stufe 2) trained on {runtime.n()} teacher-labelled states "
              f"({'bereit' if runtime.trained else 'zu wenig Daten'}).")
        save_state()                                           # capture the fresh startup training

    scene = {}                                                 # intended (body -> (xy, z, yaw)); the scene is FIXED
    #   after placement and restored per command, so only the commanded object moves.
    # DETERMINISTIC well-spread SLOTS: the workspace (x +-0.11, y 0.07..0.21, minus the base-clear disk) is too
    # small for random rejection-sampling to reliably separate 5 biggish objects -- it fails and falls back to a
    # central clump.  Fixed slots (shuffled onto the objects + small jitter) GUARANTEE a spread, non-dense scene.
    # SPACING matters: the L spans 56mm (reach ~35mm from its centre), so two shapes pointing at each other need
    # ~70mm of centre clearance or their geoms INTERPENETRATE at placement.  mj_forward doesn't resolve contacts,
    # so an overlap is INVISIBLE in the placed render -- then the first sim.step in run_combined ejects the
    # overlapping shape ("a segment snaps/twists shortly after Ausfuehren").  SIX slots, EVERY cell inside the
    # MEASURED 4-DOF grasp envelope (probes, 3-4/4 each: centre column any y, |x|<=0.06 at the top, |x|<=0.09
    # low; the mid band |x|>~0.085 / y 0.16..0.235 FAILS 0-2/4 -- pre-existing envelope hole, see REACH note).
    # Min pair 71mm at jitter +-2mm; (0,0.115) r>BASE_CLEAR=0.11.
    SLOTS = [(-0.06, 0.24), (0.06, 0.24), (0.0, 0.19), (-0.09, 0.115), (0.09, 0.115), (0.0, 0.115)]
    scene_slots = {}                                           # body -> slot index (finds the FREE slot)

    def randomize_objects():
        sim.reset_home()
        bodies = [(nm, m) for _l, nm, m in state.OBJECTS]
        if NOVEL_BODY in scene and all(nm != NOVEL_BODY for nm, _ in bodies):
            bodies.append((NOVEL_BODY, "shape"))               # introduced but not yet discovered: keep it in play
        order = list(range(len(SLOTS))); crng.shuffle(order)   # random object<->slot assignment (variety)
        scene_slots.clear()
        for (nm, m), si in zip(bodies, order):
            p = np.array(SLOTS[si], float) + crng.uniform(-0.002, 0.002, 2)   # small jitter
            z = float(LONG_HALF[2]) if m == "long" else 0.012
            yaw = crng.uniform(0, np.pi) if m == "long" else crng.uniform(0, 2 * np.pi)
            scene[nm] = (p, z, float(yaw)); scene_slots[nm] = si
        place_all()
        open_set_glance()                                      # lifelong open-set look at the fresh scene
        if panel is not None:                                  # show the placed scene immediately (decide from it)
            panel.update(sim.render(CAM), "Szene platziert — Objekt wählen und Ausführen")
            if vc.viz is not None:                             # RE-CENTER the fovea on a fresh scene: the old
                g = np.array([RES / 2.0, RES / 2.0])           #   gaze points at where an object USED to be --
                vc._P["state"]["gaze"] = g                     #   over the new layout that looks like "the fovea
                img = sim.render(CAM)                          #   still focuses an old position" (user-observed;
                arr = vc.fovea.step(img, g, vc._P["state"]["cmd"], False)   # aiming itself always re-perceives).
                vc.viz.fovea(img, g, vc.fovea._ek(), np.clip(arr[:, :, 1:], 0, 1),
                             "Szene neu — Fovea zentriert")    # box + cells + image consistent (learn=False)

    def _set_sizes():
        sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")]] = np.array([0.012] * 3)
        sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(LONG_HALF, float)   # obj_blue stays elongated
        for nm, h0 in shape_half0.items():                 # repair the L/U FIRST geom too: any set_object_size
            sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] = h0
            #   on a composite body hits only its first geom and silently DEFORMS the shape ("a segment turns
            #   90 deg") -- with PERSIST above this is a no-op, but the shape must never stay deformed.

    def place_all():
        _set_sizes()
        for nm, (p, z, yaw) in scene.items():
            sim.set_object(nm, p, z=z, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d)
        sim.step(60)                          # SETTLE: resolve any residual contact NOW (arm at home, no reach),
        #   so the shown "Szene platziert" == the physical state run_combined starts from -- nothing can snap
        #   on the first step of Ausfuehren.  With the well-spaced slots this is a no-op (objects stay put).
        state.sync_active()

    # ------------------------------------------------------------------
    # OPEN-SET form learning: the reserve probe body obj_T was NEVER seen by any training phase (parked
    # off-table in the XML).  "Objekt hinzufügen" drops it into a free slot; the net must DISCOVER it
    # (consistent novel |F| sightings -> a self-labelled class, shape_classifier.observe_scene) and it
    # then becomes commandable through the SAME form pipeline as L/U (select/track/grasp by class name).
    # NOTE an HONEST side discovery: the LONG bar (obj_blue, resized at runtime) is ALSO form-untrained,
    # so the lifelong glances typically self-label IT first ('neu-1') -- correct open-set behaviour, its
    # sightings then claim that class instead of feeding the buffer.  It is not REGISTERED as a command
    # (it has its own button/path already); only obj_T maps to a new button, usually as 'neu-2'.
    # ------------------------------------------------------------------
    NOVEL_BODY = "obj_T"

    def _register_open_class(cname):
        """A class the net just SELF-LABELLED becomes commandable: append the object to the GUI list and
        key its localisation/tracking on the open-class name.  The body handle is command PLUMBING only
        (which MuJoCo body the button stands for) -- select / track / situation_feats run purely on the
        class name the net invented.
        VERIFY the match first (user-hit bug): a class born during the introduction glances is NOT
        necessarily the introduced object's -- the untrained long I is usually STILL undiscovered then and
        gets born FIRST from the same glances; blindly binding the first-born class put the I's class on
        the T's button (fovea+grasp locked the blue I on every T command).  So only register `cname` if a
        detection of that class sits AT the introduced object (privileged pos as plumbing aid only, same
        role as in situation_feats)."""
        if NOVEL_BODY in state.SHAPE_KEY or NOVEL_BODY not in scene:
            return
        saved = sim.d.mocap_pos.copy()                         # perceive_all parks the markers -> restore
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        pT = sim.obj_pos(NOVEL_BODY)[:2]
        if not any(d["shape"] == cname and d["pos"] is not None
                   and float(np.linalg.norm(np.asarray(d["pos"]) - pT)) < 0.04 for d in dets):
            print(f"  [open-set] Klasse '{cname}' entdeckt, sitzt aber NICHT auf dem neuen Objekt "
                  f"(z.B. der lange Balken) -- nicht als Kommando registriert", flush=True)
            return
        label = f"Neue Form {len(shape_clf.open_names)}"
        state.add_object(label, NOVEL_BODY, cname)
        act16.OBJS = [nm for _l, nm, _m in state.OBJECTS]; act16.SCENE_N = len(act16.OBJS)
        print(f"  [open-set] NEUE FORM selbst benannt: '{cname}' -> Kommando '{label}'", flush=True)
        if panel is not None:
            panel.add_discovered(len(state.OBJECTS) - 1)
            panel.update(sim.render(CAM), f"Neue Form entdeckt und selbst benannt: '{cname}' — jetzt kommandierbar")

    def open_set_glance():
        """One open-set LOOK at the current scene: unknown blobs feed the novelty buffer, a young class's
        exemplar set grows over new poses (observe_scene); a class born here becomes a commandable object.
        Runs at scene EVENTS (placement, after a command), not per tracked frame."""
        if shape_clf.novel_th is None:
            return []
        saved = sim.d.mocap_pos.copy()                         # observe_scene parks the markers -> restore
        born = shape_clf.observe_scene(sim, bounds=(-0.115, 0.115, 0.075, 0.235),   # only inside the
                                       protect=set(state.SHAPE_KEY.values()))       # bound commands never starve
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)   # calibrated workspace (5mm inside
        #   REACH_XY; anything beyond lies where a knocked/mis-dropped object renders clipped or
        #   distorted and would read consistently-"novel" for a boring reason)
        if os.environ.get("ACT23_DEBUG", "0") == "1" and shape_clf.last_events:
            print(f"    [dbg open-set] {shape_clf.last_events}  buffer={len(shape_clf._novel_buf)}", flush=True)
        for cname in born:
            _register_open_class(cname)
        # STAGE 3: OPEN-SET COLOURS from the same glance -- every in-workspace component's chromaticity
        # feeds the fully self-labelled colour classes; a newborn class is BOUND to the body it was
        # discovered on (nearest body <4cm, plumbing aid exactly like the form registration).
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        bodies = list(dict.fromkeys([nm for _l, nm, _m in state.OBJECTS]
                                    + ([NOVEL_BODY] if NOVEL_BODY in scene else [])))
        for d in dets:
            if d["pos"] is None:
                continue
            if shape_clf.area_hi is not None and d["area"] > shape_clf.area_hi:
                continue                                       # merged blob = MIXED chromaticity -> would
                #   breed a phantom colour class (one appeared un-bound in the headless run)
            x, y = float(d["pos"][0]), float(d["pos"][1])
            if not (-0.115 <= x <= 0.115 and 0.075 <= y <= 0.235):
                continue                                       # same calibrated-workspace gate as the forms
            for cname in colours.observe(d["chroma"]):
                near = min(bodies, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - d["pos"])))
                if (float(np.linalg.norm(sim.obj_pos(near)[:2] - np.asarray(d["pos"]))) < 0.04
                        and near not in colour_of_body):
                    colour_of_body[near] = cname
                    print(f"  [open-set] NEUE FARBE selbst benannt: '{cname}' (auf {near})", flush=True)
                else:
                    print(f"  [open-set] NEUE FARBE selbst benannt: '{cname}'", flush=True)
        return born

    def introduce_object():
        """'Objekt hinzufügen': drop the NEVER-TRAINED probe object into a free slot.  The net then has to
        DISCOVER it -- consistent open-set sightings commit a self-labelled class and the new command
        button appears.  No truth label anywhere; if the glances don't confirm, the object simply stays on
        the table and every later scene glance keeps observing it."""
        if NOVEL_BODY in scene:
            if panel is not None:
                panel.update(sim.render(CAM), "Das Objekt ist schon in der Szene")
            return
        free = [si for si in range(len(SLOTS)) if si not in scene_slots.values()]
        si = int(free[0]) if free else 0
        p = np.array(SLOTS[si], float) + crng.uniform(-0.003, 0.003, 2)
        yaw = float(crng.uniform(0, 2 * np.pi))
        _set_sizes()
        sim.set_object(NOVEL_BODY, p, z=0.012, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d); sim.step(60)
        scene[NOVEL_BODY] = (p, 0.012, yaw); scene_slots[NOVEL_BODY] = si
        if panel is not None:
            panel.update(sim.render(CAM), "Ein unbekanntes Objekt ist aufgetaucht ...")
        for g in range(4):                                     # NOVEL_CONFIRM sightings + one spare
            open_set_glance()
            if NOVEL_BODY in state.SHAPE_KEY:
                break
            if panel is not None:
                panel.update(sim.render(CAM), f"Netz beobachtet das unbekannte Objekt ({g + 1}) ...")
            sim.step(20)
        if NOVEL_BODY not in state.SHAPE_KEY and panel is not None:
            panel.update(sim.render(CAM), "Noch keine neue Klasse — das Netz beobachtet bei jedem Befehl weiter")

    if _loaded is not None:                                    # restore SELF-DISCOVERED command objects: the
        for lbl, nm, m in _loaded.get("objects", []):          #   open-set classes live in shape_clf; the GUI
            state.OBJECTS = state.OBJECTS + [(lbl, nm, m)]     #   plumbing (button, body<->class key) is re-
            if panel is not None:                              #   registered here so "Neue Form" survives
                panel.add_discovered(len(state.OBJECTS) - 1)   #   the restart as a commandable object
        state.SHAPE_KEY.update(_loaded.get("shape_key", {}))
        _dropped = shape_clf.enforce_cap_on_load(protect=set(state.SHAPE_KEY.values()))
        if _dropped:                                            # the cap never ran on this persisted pile
            print(f"  [Aufräumen] {len(_dropped)} verwaiste Phantom-Klassen verworfen "
                  f"-> {shape_clf.open_names}", flush=True)
    if panel is not None:
        panel._randomize_fn = randomize_objects     # wire "Objekte neu" (panel built before randomize_objects existed)
        panel._introduce_fn = introduce_object      # wire "Objekt hinzufügen" (open-set discovery)
    randomize_objects()
    # CONTINUITY: make run_combined treat ALL 5 objects as its scene -> with SCENE_N = all, keep=all so it never
    # PARKS a distractor off-table, and reposition_strays never fires (nothing is a stray) -> nothing teleports.
    # The scene just evolves: only the commanded object is grasped + delivered (and STAYS), like real life.
    act16.OBJS = [nm for _l, nm, _m in state.OBJECTS]
    act16.SCENE_N = len(act16.OBJS)

    def train_fovea_classes(rounds=None):
        """DETECTOR-FREE GAZE (user's goal): retrain the hex fovea net so its sel-channel dynamics
        handle EVERY self-labelled colour class, not just the 3 fixed command codes the warmup used.
        The measured limit was that step_id's injected class-colour sel is OFF-DISTRIBUTION for the
        net, so fovea_gradient's drive was too weak to carry the gaze without the detector re-anchor.
        Here the net LEARNS (net.step(learn=True)) to reconstruct the class-conditioned sel at
        centred objects (positive) + near-empty sel on background (negative), across all classes and
        random poses -- so the identity drive strengthens and the gaze can follow with a far sparser
        (ideally no) detector anchor.  Runs only when the learned gaze is active."""
        from pc_cvnn.pc_act14 import _rand_xy
        items = [(nm, np.asarray(colours.classes[c]["mu"], float))
                 for nm, c in colour_of_body.items() if c in colours.classes]
        if not items:
            return
        rounds = int(os.environ.get("ACT23_FOVEA_TRAIN_N", "80")) if rounds is None else rounds
        K = vc.fovea.K; lo, hi = HEX_F * K, RES - HEX_F * K
        snap = {nm: (sim.obj_pos(nm)[:2].copy(), float(sim.obj_pos(nm)[2]), float(sim.obj_yaw(nm)))
                for _l, nm, _m in state.OBJECTS}
        saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim); vc.fovea.z = 1.0
        for i in range(rounds):
            for body, mu in items:
                # SCALE INVARIANCE across the zoom span (user request 0.5..2.0): the search zooms
                # OUT to re-find the class saliency and IN for detail -- sel must stay readable there.
                vc.fovea.z = (ZOOM_MIN + (ZOOM_MAX - ZOOM_MIN) * crng.random()) if FOVEA_ZOOM else 1.0
                p = _rand_xy(crng)
                sim.set_object(body, p, z=0.012, yaw=float(crng.uniform(0, 2 * np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                img = sim.render(CAM)
                try:
                    px = np.asarray(shape_clf._world_to_px(np.asarray(p, float))[0], float)
                except Exception:
                    continue
                gz = np.clip(px + crng.uniform(-4, 4, 2), lo, hi)
                vc.fovea.step_id(img, gz, mu, learn=True)          # positive: class-sel blob ON the object
                bg = crng.uniform([lo, lo], [hi, hi])
                vc.fovea.step_id(img, bg, mu, learn=True)          # negative: sel ~empty off the object
            if panel is not None and i % 10 == 0:
                panel.update(sim.render(CAM), f"Blick-Netz auf Farbklassen trainieren {i}/{rounds} ...")
        for nm, (xy, z, yaw) in snap.items():
            sim.set_object(nm, xy.tolist(), z=z, yaw=yaw)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        vc.fovea.z = 1.0
        vc.fovea._zoom_trained = _zoom_span                # persisted marker: a fovea trained on another
        #   zoom span OR another sel primitive retrains once on load (world-consistency pattern)
        print(f"  [Netz-Blick] Fovea auf {len(items)} Farbklassen umtrainiert "
              f"({rounds} Runden, Zoom {ZOOM_MIN if FOVEA_ZOOM else 1.0:.2f}-"
              f"{ZOOM_MAX if FOVEA_ZOOM else 1.0:.2f}) -- Blick-Trieb verstärkt", flush=True)

    _zoom_span = ("chroma",) + ((ZOOM_MIN, ZOOM_MAX) if FOVEA_ZOOM else (None,))
    #   "chroma" tags the sel PRIMITIVE the classes were trained with: step_id switched from the
    #   cosine match (grey table leaked through vs unsaturated class centroids) to _match_chroma,
    #   so a fovea class-trained on the old cosine-sel retrains once.
    if (FOVEA_NET and os.environ.get("ACT23_FOVEA_TRAIN", "1") == "1"
            and (not _fovea_loaded                 # a loaded fovea was already class-trained -> skip,
                 or getattr(vc.fovea, "_zoom_trained", "nie") != _zoom_span)):   # UNLESS zoom span or
        if _fovea_loaded:                          # sel primitive changed since it was trained
            print(f"  [Netz-Blick] geladene Fovea kennt {_zoom_span} nicht -- "
                  f"trainiere Klassen einmalig nach", flush=True)
        train_fovea_classes()

    # ACT23_MODVIZ=1: eigenes Fenster mit dem MODUL-GRAPHEN und den Zusammenspiel-Kurven
    # (src/pc_cvnn/module_viz.py).  Rein passiv -- ein Redraw je Episode, kein Eingriff in den Lauf.
    modviz = None
    if os.environ.get("ACT23_MODVIZ", "0") == "1":
        try:
            from pc_cvnn.module_viz import ModuleViz
            modviz = ModuleViz()
            print("  [ModulViz] eigenes Fenster geoeffnet (ACT23_MODVIZ=1)", flush=True)
        except Exception as _e:
            print(f"  [ModulViz] nicht verfuegbar: {_e}", flush=True)

    sel_off = {"dxy": None}                                    # the self-selected grasp-point OFFSET (dx,dy)
    #   of the CURRENT command: perceive() and the form tracker's servo obs both add it, so the executed
    #   grasp target is (perceived point + learned offset) consistently through approach corrections
    _sel_seed = {}                                             # last select() detection: seeds the form tracker
    #   with the SAME object the grasp targets (the tracker's own first-frame max-prob pick can differ --
    #   the user watched the U command start focused on the L before snapping over)

    def _off(xy):
        """Add the model's self-selected grasp-point offset to a perceived grasp target (stage 1)."""
        return np.asarray(xy, float) + (sel_off["dxy"] if sel_off["dxy"] is not None else 0.0)

    U_DENSEGRASP = os.environ.get("ACT23_U_DENSEGRASP", "0") == "1"   # DEFAULT AUS seit 2026-08-01 (war ON,
    #   U-only A/B 2026-07-24: +11pp, 16->25/80).  Es war eine FORM-SONDERREGEL (`if body == "obj_U"`) --
    #   genau das gezuechtete Verhalten, das der Nutzer nicht will, und es half auch nicht genug (413-Ep-Lauf:
    #   U 22% geliefert, 42% Griffverlust laut Drucksensor).  Der dichteste Punkt ist per Konstruktion
    #   KANDIDAT 0 der Maskenabtastung (shape_classifier:614, argsort(-dv)) und damit fuer JEDE Form
    #   waehlbar -- die U verliert ihn also nicht, sie muss ihn nur verdienen.  ACT23_U_DENSEGRASP=1
    #   stellt die Sonderregel wieder her (A/B).
    FORM_SPLIT = os.environ.get("ACT23_FORM_SPLIT", "1") != "0"      # the same MERGED-BLOB recovery for the
    #   FORM path (L/U/open classes): a fused component's form descriptor is destroyed, so re-read the form
    #   on the colour-separated part (perceive_colour(with_form=True)).  Measured on obj_T over 80 poses:
    #   own class 56%->95% alone, 8.8%->81% with a close neighbour, residual errors are ABSTENTIONS (never
    #   mislabels).  Also cuts how often the shape branch drops to its PRIVILEGED true-position fallback.
    #   ACT23_FORM_SPLIT=0 restores the old behaviour.
    COLOUR_SPLIT = os.environ.get("ACT23_COLOUR_SPLIT", "1") != "0"   # MERGED-BLOB recovery for the colour
    #   path (shape_classifier.perceive_colour): when a cube fuses with a neighbour and no component's mean
    #   chroma matches its class, split the occupancy per PIXEL instead of dropping to the vc hex code that
    #   grasps the neighbour.  ACT23_COLOUR_SPLIT=0 restores the old fallback.  Measured: 25mm -> 6mm.

    def _gp(det, body):
        """Greifpunkt-BEZUG einer Detektion: immer grasp_xy (Material naechst dem Schwerpunkt).

        Das ist zugleich der Bezugspunkt, auf den run_one die Kandidaten-Offsets bezieht (:2087) und
        auf den _off() sie addiert -- fruehere U-Sonderregel gab hier grasp_dense zurueck, waehrend die
        Offsets weiter gegen grasp_xy gerechnet wurden: die Verschiebung waere DOPPELT gezaehlt worden,
        sobald die Kandidaten im Netz-Modus anspringen.  Ein Bezugspunkt fuer alle Formen schliesst das
        aus.  ACT23_U_DENSEGRASP=1 holt die alte Sonderregel fuer ein A/B zurueck."""
        if U_DENSEGRASP and body == "obj_U" and det.get("grasp_dense") is not None:
            return det["grasp_dense"]
        return det["grasp_xy"]

    def perceive(cmd):
        _l, body, method = state.selected()
        if method == "shape":                                  # L/U: FORM perception (shape classifier)
            saved = sim.d.mocap_pos.copy()                     # select() PARKS the mocap markers -> restore the
            det = shape_clf.select(sim, state.SHAPE_KEY[body])  #   target markers, else goal_fn returns a parked goal
            if det is None and FORM_SPLIT:
                # FUSED BLOB on the FORM path: a neighbour closer than ~40mm merges into one component and
                # DESTROYS the form descriptor -- measured on obj_T (ACT23_TDIAG): recognised as its own
                # class 56% alone but only 8.8% when fused, the rest read as novel or as a foreign class.
                # Recover the same way the colour path does, then classify the FORM on the separated part
                # (measured: 56->95% alone, 8.8->81% fused, and the residual errors are abstentions, never
                # mislabels).  Without this the branch below falls back to the PRIVILEGED true position.
                _ck = colour_of_body.get(body)
                _m = [d for d in shape_clf.perceive_colour(sim, colours, _ck, with_form=True)
                      if d["shape"] == state.SHAPE_KEY[body]] if _ck else []
                if _m:
                    det = max(_m, key=lambda d: float(d["prob"]))
                    print(f"    [Form-Split] {body}: Blob verschmolzen -> Form auf dem farb-getrennten "
                          f"Teil erkannt als '{det['shape']}' ({det['area']:.0f}px)", flush=True)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if det is not None:
                _sel_seed.update(key=state.SHAPE_KEY[body], xy=np.asarray(det["pos"], float),
                                 px=np.asarray(det["px"], float),
                                 gxy=np.asarray(_gp(det, body), float))    # raw seed grasp point: the
                #   fovea servo shifts THIS by the gaze's world motion (grasp geometry preserved)
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [dbg] {body} via Formklasse: Greifziel "
                          f"{np.round(_off(_gp(det, body)), 3).tolist()} "
                          f"(wahr {np.round(sim.obj_pos(body)[:2], 3).tolist()})", flush=True)
                return _off(_gp(det, body)), None, "grasp"
            if os.environ.get("ACT23_DEBUG", "0") == "1":
                print(f"    [dbg] {body}: Formklasse NICHT gefunden -> privilegierter Rückfall", flush=True)
            return _off(sim.obj_pos(body)[:2]), None, "grasp"  # perception missed -> privileged fallback
        if method in ("long", "color"):                        # STAGE 3 de-crutching, now for the CUBES too:
            # localise by the SELF-LABELLED colour class (bound at discovery) instead of the trained vc
            # hex codes.  For the long object this replaced the last PRIVILEGED lookup; for the cubes it
            # replaces the vc colour codes AND the red-only marker parking (red aliased with the magenta
            # target disks -- perceive_all parks the markers itself, so the aliasing source is gone).
            cname = colour_of_body.get(body)
            knob = "ACT23_LONG_PRIV" if method == "long" else "ACT23_CUBE_VC"
            if cname is not None and os.environ.get(knob, "0") != "1":
                saved = sim.d.mocap_pos.copy()
                dets = shape_clf.perceive_all(sim)
                cands = [d for d in dets if d["pos"] is not None
                         and colours.classify(d["chroma"])[0] == cname]
                if not cands and COLOUR_SPLIT:
                    # MERGED BLOB: this object fused with a neighbour, so no component's MEAN chroma
                    # matches its class any more (measured: red next to the L reads as the L's class).
                    # Recover it by splitting the occupancy per PIXEL instead of dropping through to the
                    # old vc hex code, which grasps the neighbour (see perceive_colour docstring).
                    cands = shape_clf.perceive_colour(sim, colours, cname)
                    if cands:                                  # ALWAYS logged (not DEBUG-gated): this is the
                        #   only visible marker that the recovery fired, and a GUI run must stay auditable
                        print(f"    [Farb-Split] {body}: Blob verschmolzen -> Pixel-Split rettet das Ziel "
                              f"({len(cands)} Teil(e), {cands[0]['area']:.0f}px)", flush=True)
                sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                if cands:
                    best = min(cands, key=lambda d: colours.classify(d["chroma"])[1])
                    _sel_seed.update(key=None, xy=np.asarray(best["pos"], float),
                                     px=np.asarray(best["px"], float),
                                     gxy=np.asarray(best["grasp_xy"], float))
                    if os.environ.get("ACT23_DEBUG", "0") == "1":
                        print(f"    [dbg] {body} via Farbklasse '{cname}' lokalisiert", flush=True)
                    return _off(best["grasp_xy"]), None, "grasp"
            if method == "long":
                p0 = np.asarray(sim.obj_pos(body)[:2], float)  # fallback: class unborn / not in sight
                try:
                    _sel_seed.update(key=None, xy=p0, gxy=p0,
                                     px=np.asarray(shape_clf._world_to_px(p0)[0], float))
                except Exception:
                    pass
                return _off(p0), None, "grasp"
        if body == "obj_red":                                  # CUBE FALLBACK (class unborn / not in sight /
            saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim)   # ACT23_CUBE_VC=1): the old trained-vc
            try:                                               #   path.  PARK the magenta markers for RED only:
                xy = vc.perceive(body)                         #   red is a SUBSET of magenta (1,0,1) and the sel
            finally:                                           #   head has no 'marker' code to out-claim it
                sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)   # contrastively -> the RED command
            return _off(xy), None, None                        #   LOCKED the target disk (user-observed).
        return _off(vc.perceive(body)), None, None             # cubes: the net localises by colour

    def plot_surprise():
        if panel is not None:
            s = vc.surprise()
            q3 = sim.arm3_angles()                             # body-model FK surprise: predicted vs real hand
            bmm = float(np.linalg.norm(bm.body.fk(q3) - sim.grasp_pos())) * 1000.0   # (was always 0: wrong attr)
            if s is not None:
                m = objmem._last                               # ObjectMemory chart curves (nan while inactive,
                panel.surp_viz.push(s["sensor"], s["state"], s["total"], s["relax"], bmm,   # i.e. FOVEA_MEM off
                                    mem_err=getattr(objmem, "err_px", None),                # or no belief yet)
                                    mem_conf=None if m is None else m["conf"])

    def track_and_plot():
        obs = vc.track()
        plot_surprise()
        return obs

    def make_shape_track(body, key=None, ckey=None):
        """FORM-aware live tracker (the user's fovea goal): per tracked frame, segment+classify the scene
        (perceive_all) and return the commanded SHAPE's grasp point + confidence in run_combined's
        (obs, conf) servo protocol -- approach corrections work for L/U exactly like the colour servo.
        TWO separate uses of the detections (the v1 lesson):
          * SERVO obs: commanded-CLASS match + a 5cm world jump gate.  Only valid while the object rests
            ON the table (the px->world homography is a TABLE-plane map) -- run_combined only servos in
            over/lower anyway.
          * DISPLAY follow: nearest component in IMAGE px, ANY class -- a lifted/carried shape leaves the
            table plane (world pos wrong) and often mis-classifies, but its image blob stays trackable ->
            the fovea window follows the shape through grasp AND transport, like the colour fovea does.
        SEEDING: for shapes the belief starts LAZILY from the select() detection the grasp actually
        targets (_sel_seed; the first-frame max-prob pick can be a DIFFERENT same-class blob -- the user
        watched the U command start focused on the L).  key=None = the LONG object: no class to key on ->
        DISPLAY-ONLY blob follower seeded from the object's start position, obs stays None (the colour
        fovea drive locked the CYAN U here: the obj_blue code fires on cyan, user-observed).
        ckey = a SELF-LABELLED COLOUR class name (stage 3 cube de-crutching): servo cands are matched by
        colours.classify on the detection chromaticity instead of the shape class; conf maps the chroma
        distance into [0,1] against the class threshold (within-spread ~0.075 -> conf ~0.7).
        The hex net can't be command-keyed to a FORM, so the form tracker DRIVES the hex view itself:
        one perception step at the followed px (fovea.step: lifelong hex learning + surprise stay alive)
        and the viz drawn at the SAME gaze -- box and cells consistent, no colour-keyed follow step to
        fight the pin, no zoom-out spiral (v1 called vc.track() from the pin: the colour drive walked the
        box away from the sampled crop and zoomed out every frame -- the user's frozen/mismatched views)."""
        mem = {"xy": None, "px": None}                         # world belief (servo) + image belief (display)
        #   (the long object used to be seeded PRIVILEGED here; stage 3: perceive() now always writes
        #   _sel_seed for it too -- colour-class localization, or its explicit fallback -- so the lazy
        #   seed below covers key=None as well)
        objmem.reset()                                         # fresh predictive belief per episode
        vc.fovea.z = 1.0                                       # defined DETAIL zoom for the form view
        vc._fsv = {"d": [], "nf": 0, "nd": 0}                  # fovea-servo stats (per episode): frames
        #   with a net obs / a detector obs, and |net - detector| mm where both exist (shadow metric)

        def _track():
            if mem["px"] is None and _sel_seed.get("key", "__unset__") == key:
                mem["xy"] = _sel_seed.get("xy"); mem["px"] = _sel_seed.get("px")   # lazy: perceive() runs
                #   INSIDE run_combined, after this tracker was built -> read the seed on the first frame
                #   (key=None = the long object; its seed now comes from perceive() too, stage 3)
            saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
            dets = shape_clf.perceive_all(sim)
            obs, conf = None, 0.0
            if key is not None:                                # SHAPE-keyed servo cands (L/U, open classes)
                cands = [d for d in dets if d["shape"] == key and d["pos"] is not None]
                if not cands and FORM_SPLIT:                   # fused -> form descriptor destroyed; re-read
                    _ck = colour_of_body.get(body)             #   the FORM on the colour-separated part
                    if _ck:                                    #   (measured obj_T: 8.8% -> 81% when fused)
                        cands = [d for d in shape_clf.perceive_colour(sim, colours, _ck, with_form=True)
                                 if d["shape"] == key and d["pos"] is not None]
                        if cands:                              # counted SEPARATELY from the colour split so
                            vc._fsv["fsplit"] = vc._fsv.get("fsplit", 0) + 1   # a run can tell them apart
            elif ckey is not None:                             # COLOUR-CLASS-keyed servo cands (cubes)
                cands = [d for d in dets if d["pos"] is not None
                         and colours.classify(d["chroma"])[0] == ckey]
                if not cands and COLOUR_SPLIT:                 # fused with a neighbour -> recover by the
                    cands = shape_clf.perceive_colour(sim, colours, ckey)   # PIXEL colour split, else the
                    #   servo goes blind for the whole episode (measured: red lost the fovea in 5 of 6
                    #   GUI episodes -- the [Fovea-Servo] line was missing entirely)
                    if cands:                                  # COUNT per frame (printing every frame would
                        vc._fsv["split"] = vc._fsv.get("split", 0) + 1   # flood the log) -> reported once
                        #   in the per-episode [Fovea-Servo] line below
            else:
                cands = []                                     # long: display-only blob follower
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if cands:
                if mem["xy"] is None:                          # first sighting: most confident match
                    best = (max(cands, key=lambda d: d["prob"]) if key is not None
                            else min(cands, key=lambda d: colours.classify(d["chroma"])[1]))
                else:                                          # tracking: nearest to the belief
                    best = min(cands, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - mem["xy"])))
                if mem["xy"] is None or float(np.linalg.norm(np.asarray(best["pos"]) - mem["xy"])) <= 0.05:
                    obs = _off(_gp(best, body))                # correct toward the GRASP point (+ the learned
                    conf = (float(best["prob"]) if key is not None   # offset, else the servo would fight it)
                            else float(np.clip(1.0 - colours.classify(best["chroma"])[1]
                                               / (2.0 * colour_openset.TH), 0.0, 1.0)))
                    mem["xy"] = np.asarray(best["pos"], float); mem["px"] = np.asarray(best["px"], float)
                    vc._fsv["nd"] += 1
            if obs is None and mem["px"] is not None and dets:  # class match failed (lifted/mis-class/long) ->
                near = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["px"]) - mem["px"])))
                if float(np.linalg.norm(np.asarray(near["px"]) - mem["px"])) < 40.0:   # follow the blob in px
                    mem["px"] = np.asarray(near["px"], float)
            if mem["px"] is not None:                          # form tracker drives the hex fovea view
                lo, hi = HEX_F * vc.fovea.K, RES - HEX_F * vc.fovea.K
                # IDENTITY-CONDITIONED net gaze: point the hex fovea at the commanded object's OWN
                # self-labelled COLOUR CLASS (centroid chroma) -- fovea_gradient then drives toward THAT
                # object (no detector needed for the drive's identity, only a light occlusion re-anchor).
                id_mu = colours.classes.get(colour_of_body.get(body), {}).get("mu") if FOVEA_NET else None
                if FOVEA_NET:
                    # LEARNED FOVEA GAZE (user's goal: WHERE to look is a NET decision like the arm servos).
                    # The gaze is its own state, DRIVEN by the net's active-inference gradient on the sel
                    # channel (class-conditioned saliency, id_mu) + centring the perceived blob.  Recovery
                    # from occlusion/carry: the PREDICTIVE MEMORY (belief -> hand while carrying) if enabled,
                    # else the DETECTOR re-anchors every FOVEA_ANCHOR frames.
                    if mem.get("gaze") is None:
                        mem["gaze"] = np.asarray(mem["px"], float)   # seed from the first detection
                    mem["_fc"] = mem.get("_fc", 0) + 1
                    if not FOVEA_MEM and mem["_fc"] % FOVEA_ANCHOR == 0:
                        mem["gaze"] = 0.5 * mem["gaze"] + 0.5 * np.asarray(mem["px"], float)
                    gaze = np.clip(mem["gaze"], lo, hi)
                else:
                    gaze = np.clip(mem["px"], lo, hi)              # detector-set gaze (default, unchanged)
                vc._P["state"]["gaze"] = gaze
                img = sim.render(CAM)
                if id_mu is not None:                              # class-conditioned perception (sel = the
                    arr = vc.fovea.step_id(img, gaze, id_mu, True)  #   commanded colour class' saliency)
                else:
                    arr = vc.fovea.step(img, gaze, vc._P["state"]["cmd"], True)
                if FOVEA_NET:
                    ctr = (HEX_F - 1) / 2.0
                    sel = np.real(arr[:, :, 0]) if id_mu is not None else None
                    if sel is not None and float(sel.sum()) > 0.3:  # IDENTITY drive: class-colour saliency
                        mem["_lost"] = 0                            #   present -> fovea_gradient toward it
                        com = com2d(sel)
                        drive = -fovea_gradient(vc.fovea.cells)     # net active-inference gaze drive
                        if com is not None:
                            mem["gaze"] = np.clip(np.asarray(gaze, float)
                                                  + warp_gaze_delta(com, ctr, vc.fovea._ek())
                                                  + np.clip(drive * 6.0, -2, 2), lo, hi)
                        mass = float(np.clip(sel.max(), 0.0, 1.0))
                        # FOVEA-DRIVEN SERVO (the branch goal): while THIS identity lock holds, the
                        # net's own gaze belief -- not the detector -- supplies the approach obs: the
                        # seeded grasp point shifted by the gaze's world motion since the FIRST lock
                        # (anchor fs0, so a constant gaze<->centroid offset cancels and the grasp
                        # geometry survives -- a U's centre is a hole).  Same 5cm jump gate as the
                        # detector path; the sustained-loss branch below never reaches here, so a
                        # wrong-object fixation (user-observed) cannot steer the arm: the lock IS the
                        # gate.  "shadow" only measures |net - detector|.
                        if (FOVEA_SERVO != "0" and com is not None and shape_clf.H is not None
                                and _sel_seed.get("gxy") is not None
                                and _sel_seed.get("key", "__unset__") == key
                                and sim.d.qpos[sim.jqadr["joint_5"]] >= act16.J5_CLOSED_TH):
                            # gripper-open gate: while CARRYING, the table-plane px->world map is wrong
                            # for the lifted object (run_combined ignores servo obs outside over/lower
                            # anyway, pc_act16 ~379 -- the gate keeps the shadow STATS honest and the
                            # anchor fs0 from being dragged by a carried object)
                            wg = shape_clf._px_to_world(np.asarray(mem["gaze"], float))[0]
                            if mem.get("fs0") is None:
                                mem["fs0"] = wg
                            dxy = wg - mem["fs0"]
                            pos_f = _sel_seed["xy"] + dxy
                            if mem["xy"] is None or float(np.linalg.norm(pos_f - mem["xy"])) <= 0.05:
                                obs_f = _off(_sel_seed["gxy"] + dxy)
                                vc._fsv["nf"] += 1
                                if obs is not None:
                                    vc._fsv["d"].append(float(np.linalg.norm(obs_f - obs)) * 1000.0)
                                if FOVEA_SERVO == "1":
                                    # the identity LOCK is the confidence statement; map mass into
                                    # [0.5, 1] so a held lock always clears SERVO_CONF=0.5 (mass is a
                                    # saliency MAGNITUDE, not a class probability -- raw mass < 0.5
                                    # would count as "lost" and trigger detector re-acquire saccades)
                                    obs, conf = obs_f, 0.5 + 0.5 * mass
                    elif mem.get("_lost", 0) < 4:                  # BRIEF loss (occlusion flicker): keep the
                        mem["_lost"] = mem.get("_lost", 0) + 1     #   gaze on the material via raw occupancy
                        occ = np.ptp(np.real(arr[:, :, 1:]), axis=2)
                        com = com2d(occ)
                        if com is not None and float(occ.sum()) > 0.3:
                            mem["gaze"] = np.clip(np.asarray(gaze, float)
                                                  + warp_gaze_delta(com, ctr, vc.fovea._ek()), lo, hi)
                        mass = float(np.clip(occ.max(), 0.0, 1.0))
                    else:                                          # SUSTAINED identity loss = the material
                        mem["_lost"] = mem.get("_lost", 0) + 1     #   under the fovea is NOT the commanded
                        com = None; mass = 0.0                     #   object (user-observed: occupancy
                        #   centering LOCKED onto a wrong object and held itself there).  Release the
                        #   lock (no centering) and SEARCH: zoom_step(0) below widens the view toward
                        #   ZOOM_MAX until the class saliency re-enters the crop -- the identity branch
                        #   then re-acquires and the zoom narrows back in.  Active inference, no detector.
                    # NET-STEERABLE ZOOM (ACT_FOVEA_ZOOM=1; else a no-op): confident lock -> zoom IN
                    # (down to ZOOM_MIN detail), lost -> zoom OUT for the search overview.
                    centrality = float(np.exp(-np.linalg.norm(com - ctr) / 4.0)) if com is not None else 0.0
                    vc.fovea._zoom_step(mass * centrality)
                    if FOVEA_MEM:                                  # PREDICTIVE MEMORY drives recovery (no
                        visible = com is not None and mass > 0.15  #   detector): seen -> belief snaps to the
                        # NB: a PIXEL observation for the memory ONLY -- must NOT reuse `obs`, which is the
                        # world-xy grasp servo obs returned below (clobbering it fed px-as-metres to the
                        # grasp servo -> the arm flew off, never grasped: the 897ca5a "alles kaputt" bug).
                        obs_mem = mem["gaze"] if visible else None  #   net's centred estimate; hidden while
                        try:                                       #   carrying -> belief follows the hand
                            hand_px = shape_clf._world_to_px(sim.grasp_pos()[:2])[0]
                        except Exception:
                            hand_px = None
                        carrying = bool(sim.d.qpos[sim.jqadr["joint_5"]] < act16.J5_CLOSED_TH)
                        belief, _mode = objmem.update(obs_mem, hand_px, carrying)
                        # CONFIDENCE GATE (user-observed): after the release the belief HELD the last
                        # hand px, so the gaze parked on the ROBOT and never returned to the object.
                        # A decayed belief must release the gaze -> the occupancy/identity centering
                        # above re-acquires the object.
                        if not visible and belief is not None and objmem.conf >= 0.25:
                            mem["gaze"] = np.clip(np.asarray(belief, float), lo, hi)
                        # chart diagnostic: the memory's PREDICTION ERROR vs the detector's last fix --
                        # rises while the belief coasts through carry/occlusion, snaps down on a sighting
                        objmem.err_px = (float(np.linalg.norm(np.asarray(belief, float)
                                                              - np.asarray(mem["px"], float)))
                                         if belief is not None else float("nan"))
                    if _dbg:                                        # net-gaze tracking quality + zoom use
                        vc._fovea_drift = getattr(vc, "_fovea_drift", [])   # gaze<->detector px (small=tracks)
                        vc._fovea_drift.append(float(np.linalg.norm(
                            np.asarray(gaze, float) - np.asarray(mem["px"], float))))
                        vc._fovea_zoom = getattr(vc, "_fovea_zoom", [])
                        vc._fovea_zoom.append(float(vc.fovea.z))
                if vc.viz is not None:
                    vc.viz.fovea(img, gaze, vc.fovea._ek(), np.clip(arr[:, :, 1:], 0, 1),
                                 f"{'Netz-Servo' if FOVEA_SERVO == '1' else ('Netz-Blick' if FOVEA_NET else 'Form-Tracker')} folgt {key or body}")
                plot_surprise()
            else:
                track_and_plot()                               # nothing tracked yet -> the colour follow frame
            return obs, conf

        return _track

    HOME_Q3 = np.array([HOME[j] for j in ARM3])            # all positioning joints (3, or 4 with joint_3)

    def drive_home():
        """CONTINUOUS episode transition: after the release the arm DRIVES back to (near) its home posture
        under its normal actuators (the same reach primitive the episode uses) instead of the qpos teleport
        arm_home() does -- a physical robot can't teleport, and the user wants sim runs to stay connectable
        to the real rig.  Two legs: RAISE the claw first (a low sideways retreat could sweep the just-placed
        object), then bounded joint-space steps toward home.  NEAR home is enough (0.05 rad/joint): the next
        episode starts from a SIMILAR pose, not a bit-identical one (run_combined gets arm_reset=False).
        WRIST: set_arm3_targets CLOBBERS joint_4 to HOME on every call (the aa8446a bug class) -- without a
        per-step re-assert the wrist WHIPPED home at ground level on the first leg-1 step and flung the
        just-placed object (user-observed).  So leg 1 HOLDS the episode's wrist angle while lifting; only
        leg 2, at carry height, ramps it home at a bounded rate."""
        sim.target("joint_5", act16.J5_OPEN)
        HOME_Z_MIN = float(os.environ.get("ACT23_HOME_Z_MIN", "0.055"))   # Hoehen-Wache in Bein 2
        w = float(sim.d.qpos[sim.jqadr["joint_4"]])            # the wrist angle the episode ended with
        HOME_W = HOME["joint_4"]
        for k in range(60):                                    # leg 1: straight up, wrist HELD
            q3 = sim.arm3_angles(); h = sim.grasp_pos()
            if h[2] > act16.CARRY_Z - 0.01:
                break
            sim.set_arm3_targets(q3 + bm.body.reach_velocity(q3, np.array([h[0], h[1], act16.CARRY_Z]),
                                                             gain=2.0, max_dq=0.026))
            sim.target("joint_4", w)                           # re-assert vs the set_arm3_targets clobber
            sim.step(2)
            if panel is not None and k % 8 == 0:
                panel.update(sim.render(CAM), "Arm hebt ab ...")
        for k in range(240):                                   # leg 2: joints home, wrist RAMPED home slowly
            q3 = sim.arm3_angles()
            if float(np.max(np.abs(q3 - HOME_Q3))) < 0.05 and abs(w - HOME_W) < 0.1:
                break
            step = np.clip(HOME_Q3 - q3, -0.03, 0.03)
            # HOEHEN-WACHE (user-beobachtet: "die Finger schleifen beim Zurueckfahren manchmal am
            # Boden, wenn der Arm beim Ablegen weit weg von der Base war").  Die Gelenkraum-
            # Interpolation ist NICHT hoehenerhaltend: gemessen in der echten Sim faellt der tiefste
            # Klauenpunkt waehrend Bein 2 von 69mm (Ablage nah) auf 23mm (Ablage bei r=0.27) -- das
            # ist die Hoehe eines 24mm-Objekts.  Das gelernte FK-Modell zeigt diesen Durchhang NICHT
            # (es sagte konstant 89mm voraus), deshalb wird hier die TATSAECHLICHE Hoehe aus der Sim
            # gelesen und reaktiv gegengesteuert, statt sich auf die Vorhersage zu verlassen.
            hz = float(sim.grasp_pos()[2])
            if hz < HOME_Z_MIN:
                h = sim.grasp_pos()
                lift = bm.body.reach_velocity(q3, np.array([h[0], h[1], act16.CARRY_Z]),
                                              gain=2.0, max_dq=0.03)
                step = 0.5 * step + 0.5 * lift                 # heimwaerts UND wieder hoch
            sim.set_arm3_targets(q3 + step)
            w += float(np.clip(HOME_W - w, -0.02, 0.02))
            sim.target("joint_4", w)
            sim.step(2)
            if panel is not None and k % 8 == 0:
                panel.update(sim.render(CAM), "Arm fährt zur Ausgangsposition ...")

    res = {}
    def ep_end(ep, ok, err): res["ok"] = bool(ok); res["err"] = float(err)

    _dbg = os.environ.get("ACT23_DEBUG", "0") == "1"
    _dbgimg = os.environ.get("ACT23_DEBUG_IMG", "")
    def _pos():
        return {nm: np.round(sim.obj_pos(nm)[:2], 3).tolist() for _l, nm, _m in state.OBJECTS}
    def _save(tag):
        if _dbgimg:
            from PIL import Image
            Image.fromarray(sim.render(CAM)).save(os.path.join(_dbgimg, f"stage_{tag}.png"))

    def run_one():
        import time as _time
        # ZEITKONTO je Episode (Nutzerwunsch 2026-08-02: sehen, wann die CPU nicht mehr reicht).
        # Grob nach BLOECKEN, nicht nach Funktionen -- die Frage ist "welcher Teil wird teuer", und
        # genau auf dieser Ebene kann man handeln (Fovea-Aufloesung, Trainings-Epochen, Episodenlaenge).
        # Die Fovea zaehlt SICH SELBST (HexFovea.step), weil sie sonst in der Ausfuehrung verschwindet.
        _T = {"gesamt": _time.perf_counter()}
        _fov0 = getattr(vc.fovea, "t_step", 0.0), getattr(vc.fovea, "n_step", 0)
        _l, body, method = state.selected()
        # SNAPSHOT every object's pose before acting.  run_combined parks distractor cubes off-table and the
        # arm can knock objects -> afterwards restore all NON-commanded objects to exactly here, so the scene
        # stays put and only the commanded object moves (to the target).  No more surprise re-scatter.
        snap = {nm: (sim.obj_pos(nm)[:2].copy(), float(sim.obj_pos(nm)[2]), float(sim.obj_yaw(nm)))
                for _l2, nm, _m in state.OBJECTS}
        if _dbg: print(f"    [dbg] before  : {_pos()}", flush=True)
        _save(f"{body}_0before")
        _sel_seed.clear()                                      # form tracker seeds from THIS command's select()
        # STAGE 3 cube de-crutching: a cube with a bound SELF-LABELLED colour class localises + servos
        # via that class (like the long object) -- the trained vc hex codes and the red marker parking
        # remain only as FALLBACK while the class isn't born/bound yet (or ACT23_CUBE_VC=1 restores them).
        cube_ckey = (colour_of_body.get(body)
                     if method == "color" and os.environ.get("ACT23_CUBE_VC", "0") != "1" else None)
        if method == "color" and cube_ckey is None:            # FALLBACK display: drive the FOVEA to the cube
            #   via the vc colour code.  With a colour class the form tracker drives the view itself.
            #   LONG never drives by colour: its obj_blue code FIRES ON THE CYAN U (user-observed).
            try:
                if body == "obj_red":                          # red-only marker parking (see perceive())
                    saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim)
                    try:
                        vc.perceive(body)
                    finally:
                        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                else:
                    vc.perceive(body)
                if panel is not None:
                    track_and_plot(); panel.update(sim.render(CAM), f"Fovea -> {_l}")
            except Exception:
                pass
        u_cmd = (body == "obj_U"); wf = None
        fe = situation_feats(body)                               # perceived situation for the LIFELONG loop
        a_exec = None                                            # FULL action this episode runs (self mode):
        sel_off["dxy"] = None                                    #   [offset, wrist, grip, gentle]
        # STAGE-1 de-scripting: in self mode the world model picks the WHOLE action for EVERY object --
        # wrist (the fixed teacher angle slips off diagonal cubes), grasp-point OFFSET (off_max>0),
        # and grip close-angle + gentle-carry, which used to be the hand-coded body=='obj_U' runtime
        # rules (the user's no-runtime-rules principle: the net decides, conditioned on the perceived
        # form descriptor).  L/U/T get own startup trials now; the teacher path below remains as pure
        # TRAINING scripting whose choices are logged as demonstrations.
        use_net = state.choreo in ("netz", "attractor") and runtime.trained   # decided HERE: it also gates
        #   exploration.  "attractor" is a NETZ-family mode: the runtime policy still drives the grasp;
        #   only the latent PLACE servo is replaced by the model-based attractor plan (Etappe 3, below).
        if state.policy == "self" and fe is not None:
            n_cand = 24 if (state.auto and not use_net) else 0  # EXPLORE only in the Auto self-play (random
            #   offset/grip candidates); a MANUAL command EXPLOITS the structured grid (offset-0 wrists x
            #   grip regimes) -- the user watched a young model pick edge offsets + non-closing grips.
            #   NOT on Netz episodes: the world model gets NO outcome labels there (poisoning fix), so
            #   random candidates are pure risk without learning -- exploit the model's best action.
            offs = None
            det = getattr(situation_feats, "last_det", None)
            # FALSIFIABILITY COUPLING (measured in the user's 260-ep netz run: Bilanz collapsed to
            # 3-6/30 with broad "nicht gegriffen" floods while sigma stayed inflated 0.9-2.0): with
            # the netz failure-route abstaining, a mask OFFSET that PREVENTS the lift never gets a
            # label -- the same unfalsifiability trap as the wrist, reopened through the offset door;
            # inflated sigma pushes LCB exactly into those unlabeled extrapolation offsets (model
            # exploitation, the act22 lesson).  Candidates are only OFFERED where the failure route
            # can label them: FSM episodes (or ACT23_ATTEMPT_NETZ=1).
            #
            # SEIT 2026-08-01 auch auf NETZ-Episoden -- weil der FALSIFIZIERER jetzt existiert.  Der
            # Fingerdruck-Streifen labelt genau das, was ein schlechter Greifpunkt anrichtet: kein Druck
            # beim Heben = die Klaue hat nie gehalten, kausal am GRIFF und an nichts sonst.  Gemessen im
            # 413-Ep-Netz-Lauf: feuert in 34% der Episoden, 138 von 139 Treffern waren echte
            # Nicht-Lieferungen, und die Enthaltungsquote fiel 33-43% -> 25%.  Damit ist die Begruendung
            # oben ("die netz-Fehlerroute enthaelt sich") ueberholt.  Der Puffer zeigt, was der Riegel
            # gekostet hat: die letzten ~1500 Zeilen haben Offset EXAKT 0 -- das Modell konnte nicht
            # lernen, WO es greifen soll, weil nie etwas anderes probiert wurde.
            # BLEIBT ENG: auf Netz-Episoden ist n_cand=0, es kommen also KEINE Zufalls-Offsets dazu --
            # nur die <=6 maskenabgetasteten Punkte auf echtem Material (<=50mm).  Ehrliche Grenze: ~38%
            # der Fehlschlaege fallen weiter als Enthaltung durch, die Falsifizierbarkeit ist also nicht
            # vollstaendig, nur nicht mehr null.  ACT23_GRASP_CANDS_NETZ=0 riegelt wieder ab.
            _griplabel = os.environ.get("ACT23_GRIPLABEL", "1") != "0"
            cands_ok = ((not use_net) or os.environ.get("ACT23_ATTEMPT_NETZ", "0") == "1"
                        or (_griplabel and os.environ.get("ACT23_GRASP_CANDS_NETZ", "1") != "0"))
            if (os.environ.get("ACT23_GRASP_CANDS", "1") == "1" and cands_ok
                    and det is not None and det.get("grasp_cands")):
                # GRASP-POINT DISCOVERY (user's standing goal): the candidates are REAL places on the
                # perceived material (mask-sampled), expressed as offsets from the heuristic point the
                # execution/servo uses as reference.  The world model SCORES them (LCB) against the
                # heuristic prior; credit routing (incl. the _attempted failure route) labels whatever
                # gets tried -- where to grip becomes the model's own, perception-grounded decision.
                g0 = np.asarray(det["grasp_xy"], float)
                offs = [np.asarray(p, float) - g0 for p in det["grasp_cands"]]
                # SCHRANKE 12mm (war 50mm -- zu weit gewaehlt, korrigiert nach dem 316-Ep-Lauf
                # 2026-08-01).  Gemessen, dosisabhaengig und in 5 von 6 Objekten getrennt sichtbar:
                #   Verschiebung  0-10mm -> 55% geliefert   (Heuristik-Referenz 52%)
                #                10-20mm -> 31%
                #                20-30mm -> 16%
                #                 30mm+  ->  0%  (0 von 18)
                # Griffverlust laut Drucksensor 17% (Heuristik) gegen 48% (verschoben).  Jenseits von
                # ~12mm EXTRAPOLIERT das Modell nur noch -- genau die act22-Modellausbeutung, und LCB
                # laeuft dort hinein, weil die Offset-Dimension kaum Zeilen hat.  Das ist KEINE neue
                # Regel: die Schranke gab es schon, sie stand nur an der falschen Stelle.
                # EHRLICH: auch 0-10mm zeigt keinen VORTEIL gegenueber dem heuristischen Punkt (55 vs
                # 52%) -- die Schranke rettet die Selbstkorrektur, sie belegt keinen Nutzen.
                _cap = float(os.environ.get("ACT23_GRASP_CAND_CAP", "0.012"))
                offs = [o for o in offs if float(np.linalg.norm(o)) <= _cap]
            a, _mu_a, _sd_a = world.select_action(fe, n=n_cand, lam=LAM, offsets=offs,
                                                  curiosity=TILT_CURIOSITY)
            a_exec = a; wf = (lambda s, _w=wrist_of(a): _w)
            # ANFAHR-NEIGUNG AUS DER AKTION: bisher stand dir_ref FEST auf senkrecht (0,0,-1) und die
            # Klaue kippte bei grossem Radius zwangslaeufig (gemessen: 45 Grad bei r=0.27, Korrelation
            # +1.00) -- "ein Finger von unten, einer von oben" (User).  Jetzt WAEHLT das Modell die
            # gewuenschte Neigung; sie wird in der RADIALEBENE nach aussen gekippt, weil genau dorthin
            # die Kinematik den Arm zieht.  Waehlt es die ohnehin erreichbare Neigung, entfaellt der
            # Konflikt zwischen Position und Haltung und es gibt keinen Positionsverlust.
            _tilt = wm_tilt_of(a)
            if TILT_ACTION:
                _nat = np.degrees(world.natural_tilt(world.radius_of(fe) or 0.0))
                print(f"    [Neigung] {body}: gewaehlt {np.degrees(_tilt):.0f} Grad "
                      f"(natuerlich {_nat:.0f}, r={100*(world.radius_of(fe) or 0):.0f}cm), "
                      f"sigma {_sd_a:.3f}", flush=True)
            if TILT_ACTION and _tilt > 1e-6:
                _p = np.asarray(fe[:2], float)
                _n = float(np.linalg.norm(_p))
                if _n > 1e-6:
                    _ux, _uy = _p / _n                      # Radialrichtung Basis -> Objekt
                    bm.body.dir_ref = np.array([np.sin(_tilt) * _ux, np.sin(_tilt) * _uy,
                                                -np.cos(_tilt)], float)
                    _dir_ref_set = True
            if float(np.linalg.norm(a[:2])) > 1e-9:
                sel_off["dxy"] = np.asarray(a[:2], float)
            if offs:
                # IMMER geloggt (nicht DEBUG-gated), wie [Neigung]: seit die Kandidaten auch im
                # Netz-Modus laufen, ist der Greifpunkt eine ECHTE Wahl des Modells und ein GUI-Lauf
                # muss nachvollziehbar bleiben -- "Bezug" = wieviel der gewaehlte Punkt vom
                # heuristischen abweicht, "dicht" = Abstand zum dichtesten (Kandidat 0).
                # den dichtesten Punkt EXPLIZIT aus der Detektion nehmen, nicht offs[0] annehmen: die
                # 50mm-Schranke oben kann ihn herausfiltern, dann waere offs[0] ein anderer Kandidat
                # und die Zeile loege ueber genau die Groesse, die man mitliest.
                _dn = det.get("grasp_dense")
                _d0 = None if _dn is None else np.asarray(_dn, float) - g0
                _sel = np.asarray(a[:2], float)
                _txt = "Heuristik" if float(np.linalg.norm(_sel)) <= 1e-9 else \
                       f"{1e3*_sel[0]:+.0f},{1e3*_sel[1]:+.0f}mm"
                _nd = "" if _d0 is None else f", zum dichtesten {1e3*float(np.linalg.norm(_sel-_d0)):.0f}mm"
                print(f"    [Greifpunkt] {body}: {_txt} aus {len(offs)} Masken-Kandidaten{_nd}",
                      flush=True)
            # A/B FORCE knobs (probe arms, PRIVILEGED, default off -- never a runtime rule): measure the
            # CAUSAL value of a correct wrist / a material-centred grasp point for the prong shapes
            # before anything is allowed to learn it.  ACT23_FORCE_WRIST=priv aligns the wrist to the
            # true yaw (relwrist=0 -- the direction the 40-ep YawAB probe found suggestive for L);
            # ACT23_FORCE_GRASP=prong replaces the model's grasp offset so the planned point sits ON
            # MATERIAL (L: centre of the free long-prong part, local (-7,+7)mm; U: base-bar centre
            # (0,-14)mm, the proven balanced grip) instead of the form centre (U's form centre = the
            # OPEN SLOT between the prongs, measured a coin flip).  a_exec is updated so credit labels
            # describe what actually RAN; probes run on disposable state copies only.
            _fw = os.environ.get("ACT23_FORCE_WRIST", "")
            if _fw in ("priv", "pair"):
                # "pair" = the shape-dependent pair hypothesis the two single-knob A/Bs uncovered:
                # L wants the wrist PARALLEL to the long prong (W arm 14/20 vs 9/20) while U wants it
                # QUER across the base bar (in the G arm 4 of 5 U deliveries had relwrist 61-72 deg,
                # aligned wrists at the bar failed) -- so pair adds 90 deg for obj_U, else = priv.
                wp = float(sim.obj_yaw(body))
                if _fw == "pair" and body == "obj_U":
                    wp += 0.5 * np.pi
                wp %= np.pi
                a_exec = a_exec.copy(); a_exec[2], a_exec[3] = np.cos(2 * wp), np.sin(2 * wp)
                wf = (lambda s, _w=wp: _w)
            if (os.environ.get("ACT23_FORCE_GRASP", "") == "prong" and body in ("obj_L", "obj_U")
                    and det is not None and det.get("grasp_xy") is not None):
                loc = np.array([-0.007, 0.007]) if body == "obj_L" else np.array([0.0, -0.014])
                yr = float(sim.obj_yaw(body)); cy, sy = np.cos(yr), np.sin(yr)
                tgt = sim.obj_pos(body)[:2] + np.array([cy * loc[0] - sy * loc[1],
                                                        sy * loc[0] + cy * loc[1]])
                sel_off["dxy"] = tgt - np.asarray(det["grasp_xy"], float)
                a_exec = a_exec.copy(); a_exec[0], a_exec[1] = sel_off["dxy"]
            if os.environ.get("ACT23_YAW_AB", "0") == "1":
                # A/B measurement ONLY (never fed to a learner): the PRIVILEGED true long axis next
                # to the EXECUTED wrist/offset (after any force knob), so an offline script can test
                # whether the choice is yaw-CONDITIONED (concentration of wrist-yaw).
                w_used = wrist_of(a_exec)
                off_used = sel_off["dxy"] if sel_off["dxy"] is not None else np.zeros(2)
                yaw_t = np.degrees(sim.obj_yaw(body))
                line = (f"    [YawAB] {body} wrist {np.degrees(w_used) % 180.0:.1f} "
                        f"yaw {yaw_t % 180.0:.1f}")
                if body in ("obj_L", "obj_U"):
                    # PRONG-SHAPE extension (user-observed failure: the claw approaches the L along
                    # the long prong but DIAGONAL -> the form slips and spins away): L/U are not
                    # 180-deg symmetric, so log the full 360-deg yaw, the PLANNED grasp point rotated
                    # into the OBJECT frame (which prong / where on it: L long prong = local +y at
                    # x~-7mm, foot at y=-21mm; U prongs = local +y at x=+-23mm (32mm slot since
                    # 2026-07-18, was +-19), base bar y=-14mm),
                    # and the wrist RELATIVE to the yaw -- offline pairing with GELIEFERT/dyaw tests
                    # whether alignment + grasp placement predict the slip, before anything learns.
                    line += f" yaw360 {yaw_t % 360.0:.1f}"
                    if det is not None and det.get("grasp_xy") is not None:
                        gp = np.asarray(det["grasp_xy"], float) + np.asarray(off_used, float)
                        rel = gp - sim.obj_pos(body)[:2]
                        cy, sy = np.cos(-sim.obj_yaw(body)), np.sin(-sim.obj_yaw(body))
                        lo = np.array([cy * rel[0] - sy * rel[1], sy * rel[0] + cy * rel[1]]) * 1e3
                        line += (f" grasp_obj {lo[0]:.0f},{lo[1]:.0f}"
                                 f" relwrist {(np.degrees(w_used) - yaw_t) % 180.0:.1f}")
                print(line, flush=True)
            if _dbg:
                print(f"    [dbg] Aktion (Welt-Modell): Offset {np.round(a[:2] * 1000, 1).tolist()}mm, "
                      f"Wrist {np.degrees(wrist_of(a)) % 180.0:.0f} Grad, Grip {a[4]:.2f}"
                      f"{', sanft' if a[5] > 0.5 else ''} | {0 if offs is None else len(offs)} "
                      f"Masken-Kandidaten", flush=True)
        # CLOSED-LOOP fovea: servo=True lets the live tracker CORRECT the grasp-target belief during the
        # reach (+ occlusion memory).  L/U track via the FORM-aware tracker (make_shape_track:
        # perceive_all per frame, matched by SHAPE class); CUBES with a bound colour class track via the
        # SAME tracker keyed on the class (vc.track only as fallback) -- the user's fovea goal: the fovea
        # supports approach+grasp instead of sitting on whatever colour was last commanded.  Only the
        # long object stays servo=False (no class to key on when this comment was written; kept as-is).
        if method == "shape":
            track_fn = make_shape_track(body, key=state.SHAPE_KEY[body])
        elif method == "long":
            track_fn = make_shape_track(body)                  # display-only blob follower (no class to key on)
        elif cube_ckey is not None:                            # cube with a bound colour class: colour-keyed
            track_fn = make_shape_track(body, ckey=cube_ckey)  #   servo tracker (stage 3 de-crutching)
        else:
            track_fn = track_and_plot
            vc._fsv = None                                     # no form tracker -> no fovea-servo stats
        if a_exec is not None:                                 # SELF: the model's grip + gentle dims
            grip_exec = float(np.clip(a_exec[4], 0.0, 0.45)); gentle_exec = bool(a_exec[5] > 0.5)
        else:                                                  # TEACHER: the old rules, now demonstrations
            grip_exec = 0.3 if u_cmd else None; gentle_exec = u_cmd
        # STAGE 2: "Choreo: Netz" -> the learned runtime policy drives the sub-goals; the reactive
        # teacher LABELS the visited states either way (log_fn on FSM runs = behaviour data, teacher_
        # log_fn on policy runs = true DAgger), so every episode trains the choreography lifelong.
        if state.choreo in ("netz", "attractor") and not runtime.trained:
            print("    [Stufe 2] Choreo-Netz noch nicht trainiert -- FSM fährt", flush=True)
        # STAGE 4a: "Ziel: Latent" -> the committed goal becomes a LATENT (post_goal_fn encodes it
        # once); while the object is carried, place_servo_fn drives the place target by the latent
        # difference to the hand's latent.  Works under FSM AND Netz (the policy state's target
        # follows the servo'd tgt via tgt_eff).  "Ziel: Koord" = both hooks off, classic place.
        use_latent = state.goalmode == "latent"
        pol_trace = []                                         # STEP 3: (state, action) the POLICY drives
        #   this episode -> becomes self-imitation demonstrations IF the agent self-judges a delivery
        runtime.begin_episode()                                # PEND the teacher rows; committed only if
        #   this episode is NOT a self-validated success (teacher corrects failures, see end_episode)
        # dir_ref wurde ggf. oben aus der gewaehlten AKTION gekippt -- Originalwert sichern und nach
        # der Episode zuruecksetzen, damit die Neigung NUR fuer diesen Griff gilt und nicht dauerhaft
        # in Transport/Ablage und die naechste Episode durchschlaegt.
        _dir_ref_orig = None if not TILT_ACTION else np.array(bm.body.dir_ref, float).copy()
        _T["vor_ausfuehrung"] = _time.perf_counter()           # alles davor = Wahrnehmung + Aktionswahl
        act16.run_combined(sim, bm.body, panel, CAM, episodes=1, cmd_fixed=state.cmd_fn, force=state.force_fn,
                           goal_fn=state.goal_fn, perceive_fn=perceive, track_fn=track_fn,
                           policy_fn=(runtime.predict if use_net else None),
                           log_fn=(None if use_net else choreo_log),
                           teacher_log_fn=(choreo_log if use_net else None),
                           policy_log_fn=((lambda s, out: pol_trace.append((s.copy(), out.copy())))
                                          if use_net else None),
                           post_goal_fn=(lambda c, o, g: lgoal.set_goal_vector(g) if (isinstance(g, np.ndarray) and g.ndim==1 and len(g)>2) else lgoal.set_goal(g)),
                           #   (seval) needs the episode's goal latent even in "Ziel: Koord" mode
                           place_servo_fn=((lambda hxy: lat_attractor.plan_step(lgoal.encode_world(hxy), lgoal.get_goal_vector(), hxy)[2])
                                            if state.choreo == "attractor" else
                                            ((lambda hxy: lgoal.servo(hxy, gain=0.6)) if use_latent else None)),
                           servo=(method in ("color", "shape")), rescatter=False, episode_end_fn=ep_end,
                           lifelong=True, carry_gentle=gentle_exec, grip_close=grip_exec, wrist_fn=wf,
                           arm_reset=False)
        _T["nach_ausfuehrung"] = _time.perf_counter()
        if _dir_ref_orig is not None:
            bm.body.dir_ref = _dir_ref_orig                    # Neigung galt nur fuer diese Episode
        _save(f"{body}_1after_runcombined")
        if os.environ.get("ACT23_YAW_AB", "0") == "1" and body in ("obj_L", "obj_U", "obj_blue"):
            # measurement companion to [YawAB]: how much the commanded shape ROTATED over the episode
            # (privileged, wrapped to +-180).  On FAILED episodes this is the pure slip-spin signature
            # the user watches in the GUI (diagonal contact torques the L away); on deliveries it also
            # contains the carry.  The offline script pairs it with relwrist/grasp_obj + the outcome.
            dy = (np.degrees(sim.obj_yaw(body) - snap[body][2]) + 180.0) % 360.0 - 180.0
            print(f"    [YawAB-End] {body} dyaw {dy:+.1f}", flush=True)
            # PLACE diagnosis (measurement-only, 2026-07-23): the 746-ep + dose logs showed L place
            # error is GRASP-driven (central+aligned grasp -> median 19mm/70% delivered; off-centre or
            # mirrored -> ~48% gross) EXCEPT a ~5% residual that flings the object 100-285mm despite a
            # perfect grasp -- bimodal = a discrete event (release-flick / lift-whip / skitter off the
            # small table), not gradual place scatter.  Flag those: end position outside the reach area
            # = flung off, so the GUI watcher knows which episodes to inspect for the mechanism.
            _e = sim.obj_pos(body)[:2]
            _rb = [float(os.environ["ACT_REACH_X0"]), float(os.environ["ACT_REACH_X1"]),
                   float(os.environ["ACT_REACH_Y0"]), float(os.environ["ACT_REACH_Y1"])]
            _off = not (_rb[0] - 0.01 <= _e[0] <= _rb[1] + 0.01 and _rb[2] - 0.01 <= _e[1] <= _rb[3] + 0.01)
            _trav = 1000.0 * float(np.linalg.norm(_e - snap[body][0][:2]))
            print(f"    [PlaceAB] {body} Weg {_trav:.0f}mm{'  VON-FLAECHE-GEFLOGEN' if _off else ''}", flush=True)
        _g = dict(getattr(act16.run_combined, "_grip", {}) or {})
        def _ph(*names):                                       # Mittelwert ueber die genannten Phasen
            v = [x for n in names for x in _g.get(n, [])]
            return (float(np.mean(v)), float(np.min(v))) if v else (0.0, 0.0)
        _close_m, _ = _ph("close", "lower")                    # zufassen
        _lift_m, _lift_lo = _ph("lift")                        # Last uebernehmen
        _carry_m, _carry_lo = _ph("carry")                     # halten
        _rel_m, _ = _ph("place", "release")                    # loesen
        print(f"    [Griffdruck] zufassen {_close_m:5.2f} | heben {_lift_m:5.2f} (min {_lift_lo:4.2f})"
              f" | tragen {_carry_m:5.2f} (min {_carry_lo:4.2f}) | loesen {_rel_m:5.2f}  [N]", flush=True)
        _rel = getattr(act16.run_combined, "_release", None)
        if _rel is not None:
            # ABLAGE-MESSUNG (nur Diagnose): trennt "zu hoch losgelassen" von "seitlich verfehlt".
            # fall  = wie hoch das OBJEKT beim Oeffnen der Klaue noch ueber seiner Ruhelage stand
            # drift = wie weit es sich danach noch bewegt hat (Fallen + Rollen)
            # ab_ziel_beim_Oeffnen = der seitliche Fehler, den die Policy schon VOR dem Loslassen hatte
            _end = np.asarray(sim.obj_pos(body)[:2], float)
            _fall = 1000.0 * max(0.0, _rel["cz"] - _rel["obj_h"])
            _drift = 1000.0 * float(np.linalg.norm(_end - _rel["cxy"]))
            _lat = 1000.0 * float(np.linalg.norm(_rel["cxy"] - _rel["tgt"]))
            _fin = 1000.0 * float(np.linalg.norm(_end - _rel["tgt"]))
            print(f"    [Ablage] {body}: beim Oeffnen Objekt {_fall:.0f}mm ueber Ruhelage, "
                  f"seitlich {_lat:.0f}mm vom Ziel -> danach {_drift:.0f}mm gedriftet, "
                  f"final {_fin:.0f}mm", flush=True)
        _fsv = getattr(vc, "_fsv", None)
        if FOVEA_SERVO != "0" and _fsv and (_fsv["nf"] or _fsv["nd"]):
            # measurement line (shadow AND live): how often the net belief carried the servo vs the
            # detector, and how far apart the two were when both existed
            print(f"    [Fovea-Servo{' Schatten' if FOVEA_SERVO == 'shadow' else ''}] "
                  f"Netz-Obs {_fsv['nf']} / Detektor-Obs {_fsv['nd']} Frames"
                  + (f", |Netz-Detektor| mittel {np.mean(_fsv['d']):.1f} mm, "
                     f"max {np.max(_fsv['d']):.0f} mm" if _fsv["d"] else "")
                  + (f", Farb-Split trug {_fsv['split']} Frames" if _fsv.get("split") else "")
                  + (f", Form-Split trug {_fsv['fsplit']} Frames" if _fsv.get("fsplit") else ""),
                  flush=True)
        if _dbg and FOVEA_NET and getattr(vc, "_fovea_drift", None):   # net-gaze tracking quality + zoom
            d = vc._fovea_drift; zz = getattr(vc, "_fovea_zoom", []) or [1.0]
            print(f"    [Netz-Blick] Drift Blick<->Objekt: mittel {np.mean(d):.1f}px, "
                  f"max {np.max(d):.0f}px | Zoom z {np.min(zz):.2f}..{np.max(zz):.2f} "
                  f"(mittel {np.mean(zz):.2f}) ({len(d)} Frames)", flush=True)
            vc._fovea_drift = []; vc._fovea_zoom = []
        hxy_end = sim.grasp_pos()[:2].copy()  # where the agent's own hand ENDED (~= release point;
        #   the soft release retreats vertically) -- the self-judge's CONTINUITY anchor, proprioceptive
        drive_home()                          # retreat FIRST: restoring an object under the still-lowered arm
        #   could re-create contact under the claw; and the next episode then starts from ~home WITHOUT a reset
        # CONTINUITY + keep the shapes UPRIGHT: leave the COMMANDED object where the action left it (delivered
        # + staying), but put every NON-commanded object back on its pre-command pose.  set_object writes a pure
        # z-rotation, so this also UN-TIPS any shape the arm nudged onto its side (the thin 24mm-tall L/U bars
        # tip easily).  No teleport (OBJS=all5 above), no full reset -- the scene just evolves as you command.
        _set_sizes()
        for nm in snap:                                        # iterate the SNAPSHOT, not state.OBJECTS: the
            #   object list can GROW mid-episode (a GUI click during the run discovers/introduces a new
            #   object -> KeyError on restore, user-hit); anything not snapped simply stays where it is
            if nm != body:
                p, z, yaw = snap[nm]; sim.set_object(nm, p, z=z, yaw=yaw)   # non-commanded: pre-command pose
            else:
                # COMMANDED object: KEEP the delivered position + heading (no position reset -- you pick it by
                # where you SEE it), but stand it UPRIGHT.  A thin, asymmetric L/U gets TORQUED by the claw during
                # the grasp and can end tilted ("a segment snaps/twists") -- set_object writes a pure z-rotation,
                # so this un-tips the delivered shape in place.  Cubes/long are already upright -> a no-op for them.
                cp = sim.obj_pos(nm)[:2].copy(); cz = snap[nm][1]
                sim.set_object(nm, cp, z=cz, yaw=sim.obj_yaw(nm))
        mujoco.mj_forward(sim.m, sim.d); state.sync_active()
        # SELF-JUDGEMENT (before the housekeeping below MOVES a flung object -- the judge must see
        # the true outcome scene): the agent's own verdict via its self-labelled classes + the goal
        # latent; agreement with the privileged verdict is tallied per episode.
        saved_mc = sim.d.mocap_pos.copy()
        jdets = shape_clf.perceive_all(sim, wpx=True)      # material px: merged-blob recovery needs them
        sim.d.mocap_pos[:] = saved_mc; mujoco.mj_forward(sim.m, sim.d)
        det0 = getattr(situation_feats, "last_det", None)  # the object's OWN start-of-episode detection:
        s_ok, s_d, s_found = seval.judge(jdets, lgoal, colour_key=colour_of_body.get(body),   # its area is
                                         colours=colours, shape_key=state.SHAPE_KEY.get(body),  # the merge
                                         near_xy=hxy_end, key=body,                             # reference
                                         exp_area=(None if det0 is None else det0.get("area")))
        if s_ok is None:
            print(f"    [Selbst-Urteil] enthalten -- noch keine eigene Klasse für {body}", flush=True)
        else:
            tally = seval.record(s_ok, res.get("ok", False))
            ref = (seval._last or {}).get("ref_mm", 0.0)   # self-calibrated perception radius applied
            refs = f", Ref-Korrektur {ref:.0f}mm" if ref >= 1.0 else ""
            if (seval._last or {}).get("merged"):
                refs += ", Blob-Verschmelzung erkannt"     # judged on MY material at the hand, not the fused centroid
            verdict = (f"geliefert ({s_d * 1000:.0f}mm vom Wunsch{refs})" if s_ok
                       else (f"nicht geliefert ({s_d * 1000:.0f}mm vom Wunsch{refs})" if s_found
                             else "nicht geliefert (Objekt nicht am Loslass-Punkt gesehen)"))
            wv = "geliefert" if res.get("ok", False) else "nicht geliefert"
            mark = "=" if bool(s_ok) == bool(res.get("ok", False)) else "!="
            print(f"    [Selbst-Urteil] {verdict}  {mark}  Welt: {wv}  (Übereinstimmung {tally})",
                  flush=True)
            if mark == "!=" and os.environ.get("ACT23_DEBUG", "0") == "1":
                le = seval._last
                print(f"      [su-dbg] hand={np.round(hxy_end,3).tolist()} obj_true="
                      f"{np.round(sim.obj_pos(body)[:2],3).tolist()} strict={le.get('n_strict')} "
                      f"cands={le.get('n_cands')} cand_pos={le.get('cand_pos')}", flush=True)
        # ETAPPE 2 (Latent Dynamics): observe THIS episode's latent transition -- the object moved from
        # its start pose to its end pose under the executed action -- and train the transition model.
        # BUGFIX 2026-07-24: the previous code used an undefined name `action` (the action is `a_exec`)
        # inside a bare `except: pass`, so it raised a NameError EVERY episode and trained NOTHING for
        # the whole 314-ep run (the [Latent-Dynamics] line never printed).  Now: real (z_start, a_exec,
        # z_end) transition, skip teacher episodes (a_exec None), and errors are LOGGED not swallowed.
        # NOTE: this is an EPISODE-LEVEL transition (one per episode), not per-step -- coarse but honest;
        # a_exec is the 6-dim world-model action (the dynamics module truncates to its action_dim).
        if a_exec is not None:
            try:
                _a_dyn = np.asarray(a_exec, float)
                z_start_dyn = lgoal.encode_world(snap[body][0][:2])
                z_end_dyn = lgoal.encode_world(sim.obj_pos(body)[:2])
                lat_dyn.observe(z_start_dyn, _a_dyn, z_end_dyn)
                surp = lat_dyn.predict_surprise(z_start_dyn, _a_dyn, z_end_dyn)
                loss_d = lat_dyn.train(epochs=5)
                if os.environ.get("ACT23_YAW_AB", "0") == "1":
                    print(f"    [Latent-Dynamics] Übergang beobachtet -> Surprise S={surp:.3f} | "
                          f"MSE={loss_d:.5f} | Puffer {len(lat_dyn.buffer_z)}", flush=True)
            except Exception as e:
                print(f"    [Latent-Dynamics] FEHLER: {type(e).__name__}: {e}", flush=True)
        # SCENE housekeeping (user-observed degeneration over long auto runs): an object DRAGGED outside
        # the reachable workspace by a failed grasp stays out FOREVER (the restore puts non-commanded
        # objects back on their pre-command = out pose; a commanded one keeps its end pose) -- every
        # later reach toward it is unreachable and SWEEPS through the scene ("the arm lifts some
        # unmarked object and throws it").  Return such objects to a free slot: ENVIRONMENT tidying
        # between episodes (the bounded act23 heir of act16's reposition_strays), not an agent rule.
        for _l2, nm, _m2 in state.OBJECTS:
            p = sim.obj_pos(nm)[:2]
            if abs(p[0]) <= 0.135 and 0.055 <= p[1] <= 0.265:
                continue                                       # inside (generous bounds: a legit delivery can
                #   rest tolerance-width past a top target -- CONTINUITY, only truly-LOST objects return)
            occ = [sim.obj_pos(o)[:2] for _l3, o, _m3 in state.OBJECTS if o != nm]
            free = [s for s in SLOTS
                    if all(float(np.linalg.norm(np.asarray(s) - q)) > 0.055 for q in occ)]
            if not free:
                continue
            s = max(free, key=lambda sl: min(float(np.linalg.norm(np.asarray(sl) - q)) for q in occ))
            zr = scene.get(nm, (None, 0.012, 0.0))[1]
            sim.set_object(nm, np.asarray(s, float) + crng.uniform(-0.003, 0.003, 2), z=zr,
                           yaw=float(crng.uniform(0, 2 * np.pi)))
            print(f"    [Szene] {nm} lag außerhalb des Arbeitsbereichs — zurück auf einen freien Platz",
                  flush=True)
        mujoco.mj_forward(sim.m, sim.d)
        if panel is not None and vc.viz is not None:           # refresh the hex "overview Kamera (Fovea)" with
            try:                                               #   the RESTORED scene (it last rendered a pre-
                vc.viz.update(sim.render(CAM), "Szene aktualisiert")   # restore frame -> stale layout); a plain
            except Exception:                                  #   image refresh -- no colour-keyed track step
                pass                                           #   that would walk the gaze off the final view
        open_set_glance()                  # lifelong OPEN-SET look at the settled scene: young self-labelled
        #   classes keep growing exemplars over the new poses; an undiscovered novel object keeps feeding
        #   the buffer (discovery can also happen HERE, not only at "Objekt hinzufügen")
        if _dbg:
            print(f"    [dbg] after ep : {_pos()}", flush=True)
            hs = {nm: np.round(sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] * 1000, 1).tolist()
                  for nm in ("obj_L", "obj_U", "obj_T")}   # the exact failure mode: a resized first geom
            print(f"    [dbg] L/U/T half : {hs}  (XML: L [7,28,12] U [7,14,12] T [21,7,12])", flush=True)
        _save(f"{body}_2after_restore")
        # LIFELONG loop (EVERY object): every command IS a trial for the world model (situation -> action
        # -> outcome).  STEP 2 (prediction-checkpoint CREDIT ROUTING, user's self-improvement plan): the
        # crude "learn only in FSM mode" gate is replaced by TWO self-measured checkpoints that decide
        # WHOSE decision failed, so the world model learns in the NORMAL (Netz) mode too -- from the
        # episodes where its OWN decision (the grasp: wrist/offset/grip/gentle) was actually put to the
        # test.  The four cases (poisoning fix, now precise):
        #   - NOT lifted            -> the grasp never happened: the POLICY/choreography missed -> ABSTAIN.
        #   - lifted + delivered    -> the grasp+carry worked -> world model +1 SUCCESS.
        #   - lifted + SLIPPED      -> the grip lost the object mid-carry -> world model +1 FAILURE.
        #   - lifted, held, off-goal-> the place AIM was wrong though the grip held -> POLICY -> ABSTAIN.
        # The outcome label is the agent's OWN verdict (step 1 SelfEval) -> fully self-supervised.
        # ACT23_WORLD_LABEL=welt forces the privileged label; ACT23_CREDIT=0 restores the FSM-only gate.
        maxcz = float(getattr(act16.run_combined, "_maxcz", 0.0))
        slipped = bool(getattr(act16.run_combined, "_slipped", False))
        rest_z = float(snap[body][1]) if body in snap else 0.012
        lifted = maxcz > rest_z + 0.02                          # object clearly left the table = grasp tested
        imit_tol = float(os.environ.get("ACT23_IMIT_TOL", "0.015"))
        # ASYMMETRIC confidence bars (user request 2026-07-18; measured on the 415-ep session log):
        # the judge's DISTANCE estimate is nearly unbiased (median |self-true| 0-3mm) but a single
        # 15mm bar discarded 48% of TRUE deliveries (77/159) -- exactly the "sieht fuer mich OK
        # abgelegt aus, Log sagt unsicher" episodes the user watched.  In the 15-25mm band the
        # judge's "geliefert" is right 85-100% per object EXCEPT the U, so:  WORLD-MODEL success
        # label accepts up to ACT23_WORLD_TOL (25mm; the ensemble tolerates the ~13% label noise,
        # and positives were the measured yield bottleneck), SELF-IMITATION keeps the strict
        # imit_tol bar (an imitated failure poisons the policy directly), and the U keeps the strict
        # bar for BOTH.  The U band was briefly un-clamped after the 32mm slot (498-ep run showed
        # 92%, 12/13) but that did NOT replicate: the 746-ep run 2026-07-21 measured 54% (7/13,
        # pooled 73%) with 6 false-positive success labels leaking in -- U's blob still merges with
        # the claw, and U's bottleneck is mechanical (5 dose runs), not the action, so extra U
        # labels have low value.  Clamp re-instated.
        world_tol = float(os.environ.get("ACT23_WORLD_TOL", "0.025"))
        if body == "obj_U":
            # U was clamped to imit_tol (15mm) after the 746-run's 6 false-positives (U blob merges with
            # the claw).  But the U-densegrasp fix (2026-07-24) delivers the U FLAT at ~18-20mm -- real wins
            # (self==Welt) that the 15mm bar discarded, starving the world model of exactly the grasps the
            # fix enabled.  User decision: loosen the WORLD-MODEL bar to 22mm to credit them (the ensemble
            # tolerates the noise); SELF-IMITATION keeps the strict 15mm imit_tol below (a borderline U grip
            # must not be imitated straight into the policy).  FP risk re-opened -> WATCH the next full run.
            world_tol = float(os.environ.get("ACT23_U_WORLD_TOL", "0.022"))
        if os.environ.get("ACT23_WORLD_LABEL", "selbst") == "welt" or s_ok is None:
            delivered = bool(res.get("ok", False)); confident = delivered; lbl_src = "Welt"
            world_conf = delivered
        else:                                                   # self-judged (step 1) -> self-supervised
            delivered = bool(s_ok)
            confident = delivered and s_d is not None and s_d < imit_tol
            world_conf = delivered and s_d is not None and s_d < world_tol
            lbl_src = "Selbst"
        attempted = bool(getattr(act16.run_combined, "_attempted", False))
        # the attempted-failure route only under the RELIABLE (FSM) choreography: there a close at
        # the object that never lifts isolates the ACTION's grasp geometry (wrist/grip).  Under the
        # LEARNED choreography the same signal is AMBIGUOUS -- the policy grazes the object and
        # closes at the wrong moment, and the wrist gets the blame.  MEASURED in the user's live
        # netz run: ~38 failure labels in 120 eps flooded the world model (798->886, mostly
        # negative), ensemble sigma inflated 0.5-0.9 -> 0.9-1.6, LCB wrist choice churned
        # (user-observed diagonal grips) and the Bilanz slid 18/30 -> 10/30 -- the fd6e526
        # poisoning symptom through a physically-gated door.  Ambiguity -> abstain (the credit
        # principle); ACT23_ATTEMPT_NETZ=1 re-enables for experiments.
        # FEHLGRIFF-LABEL UNTER NETZ, ABER GEDAEMPFT (2026-07-27).  Messung 610-Ep-Lauf: das Welt-Modell
        # sieht 36% der Episoden (220 Fehlgriffe) GAR NICHT, weil sie hier abstrahiert werden -- und lernt
        # die Ausrichtungs-Regel dadurch VERKEHRT (Puffer: schraeg Label 0.813 vs ausgerichtet 0.768,
        # waehrend die Realitaet 17% vs 35% Lieferung sagt).  Die Information sitzt NICHT in einer
        # Teilmenge: geschobene und unberuehrte Fehlgriffe sind gleich schraeg (34% vs 32%, p=1.0), aber
        # BEIDE liegen bei ~33% gegen nur 15% bei den Erfolgen -- die Fehlgriffe als GANZES tragen sie.
        # Das historische Problem beim Einschalten war nicht Falschheit, sondern FLUT: ~38 fast durchweg
        # negative Labels blaehten Sigma 0.5-0.9 -> 0.9-1.6 und liessen die LCB-Wahl flattern.  Deshalb
        # kommt das Label jetzt mit GEWICHT ACT23_FAIL_W (default 0.3) statt gar nicht: das Signal ist da,
        # die unsichere Kausalzuordnung (Anfahrt vs Griffgeometrie) steckt im Gewicht.  ACT23_FAIL_W=0
        # schaltet es faktisch ab, ACT23_ATTEMPT_NETZ=1 gibt volles Gewicht (altes Experiment).
        obs_w = 1.0                                    # fit weight of THIS episode's world-model row
        # SENSOR-BELEGTER GRIFF-FEHLSCHLAG (Fingerdruck-Streifen).  Gemessen (50 Ep): wenn der Druck
        # waehrend des HEBENS durchgehend 0 bleibt UND beim Zufassen unter 1 N lag, hat die Klaue das
        # Objekt nie gehalten -- in 92% der Faelle folgt daraus kein Erfolg.  Das ist ein KAUSAL
        # EINDEUTIGES Negativ fuer die AKTION: es haengt nur am Griff, nicht an Transport, Ablage oder
        # einem Nachbarobjekt.  Genau die Eindeutigkeit, die dem attempted-Label fehlt (dort musste die
        # unsichere Zuordnung ueber ein Gewicht von 0.3 abgefedert werden) -- hier gibt es volles
        # Gewicht.  `not delivered` als Schutz: eine Episode, die trotz Druckeinbruch liefert (kurzes
        # Nachfassen), darf kein Negativ bekommen.  ACT23_GRIPLABEL=0 schaltet es ab.
        _grip_lost = (os.environ.get("ACT23_GRIPLABEL", "1") != "0"
                      and bool(_g)                       # Sensor hat ueberhaupt gemessen
                      and _lift_m < 0.01 and _close_m < 1.0)   # oben aus run_combined._grip gelesen
        # 423-Ep-Lauf ausgewertet (2026-07-28) -- und meine erste Bewertung KORRIGIERT.
        # Ich hatte das Label fuer schaedlich erklaert (Ausrichtungs-Praeferenz -0.010 -> +0.017,
        # Sigma 0.297 -> 0.395) und dabei gegen ein BACKUP verglichen, das sich nicht nur um die 86
        # Fehlgriff-Zeilen unterscheidet, sondern um 264 neue Zeilen des Laufs -- die ~178
        # zusaetzlichen ERFOLGS-Zeilen verschoben die Praeferenz, nicht das Label.  Der saubere Test
        # (derselbe Zustand, gleicher Fit-Seed, NUR die 86 Zeilen variiert, beide frisch trainiert):
        #   ohne die Zeilen  schraeg-Praeferenz +0.060, Sigma 0.155
        #   mit  den Zeilen  schraeg-Praeferenz +0.001, Sigma 0.140
        # Das Label VERBESSERT die Ausrichtungs-Bewertung also und senkt Sigma leicht -- der User
        # hatte mit seinem Eindruck recht ("die Ausrichtung sieht nicht mehr so zufaellig aus").
        # OFFEN und NICHT dem Label zuzuordnen: die Lieferrate fiel im Lauf 47% -> 35% (nicht durch
        # die Curiosity-Zuteilung erklaert) und die L-Form von 52% auf 13% (n=15).  Ursache ungeklaert;
        # ein Kandidat ist die graduelle Imitation (23% der 12000 Demos stammen aus Ablagen, die
        # frueher verworfen worden waeren, mit 15% der Fit-Zugkraft).  LEHRE: einen Label-Effekt NUR
        # gegen denselben Datensatz messen, nie gegen einen mitgewachsenen Backup-Stand.
        fail_w = float(os.environ.get("ACT23_FAIL_W", "0.3"))
        att_full = (not use_net) or os.environ.get("ACT23_ATTEMPT_NETZ", "0") == "1"
        att_ok = att_full or fail_w > 0.0
        if os.environ.get("ACT23_CREDIT", "1") == "1":
            if _grip_lost and not delivered:
                # der Streifen BELEGT, dass die Klaue nie gehalten hat -> Aktion war schlecht
                route, outcome = "Griff hielt nicht (Drucksensor)", False
                obs_w = 1.0
            elif not lifted and attempted and not delivered and att_ok:
                # the claw CLOSED at the object and it never rose: the choreography ARRIVED, the
                # ACTION's grasp geometry (wrist/grip) failed -> the action gets a FAILURE label.
                # Without this route a grasp-PREVENTING wrist was unfalsifiable (always "nicht
                # gegriffen" -> abstain) and the world model froze on it (L-Form wrist-112 deadlock).
                # `not delivered` guard (measured): a never-lifted episode can still SHOVE the object
                # onto the goal -- that must not label the action a failure (abstain below instead).
                route, outcome = "Griff am Objekt fehlgeschlagen (Aktion)", False
                obs_w = 1.0 if att_full else fail_w     # gedaempft, solange die Zuordnung unsicher ist
            elif world_conf and os.environ.get("ACT23_CREDIT_FLAT", "1") != "0":
                # A CONFIDENT delivery (self-judge <world_tol; U=15mm) is a SUCCESS even when the object
                # never rose >20mm.  The U-densegrasp A/B (2026-07-24) exposed this: the base grip carries
                # the U FLAT to the goal (dyaw +-30-60, PlaceAB Weg ~65mm), delivering ~20mm WITHOUT tripping
                # the lift gate -> the old "elif not lifted -> abstain" discarded the win (12 of 25 on-arm
                # deliveries), starving the world model of exactly the grasps the fix enabled.  Guarded by
                # world_conf (a shove-to-goal rarely lands <15mm) + reversible (ACT23_CREDIT_FLAT=0).
                route, outcome = "sicher geliefert", True
            elif not lifted:
                route, outcome = "nicht gegriffen (Policy)", None
            elif world_conf:
                route, outcome = "sicher geliefert", True
            elif slipped:
                route, outcome = "verrutscht (Griff)", False
            elif delivered:                                     # judged delivered but NOT confident ->
                route, outcome = "unsichere Lieferung", None    #   don't credit the action either way
            else:
                route, outcome = "daneben platziert (Policy)", None
        else:                                                   # old gate: FSM only, privileged label
            outcome = bool(res.get("ok", False)) if not use_net else None
            route = "FSM" if not use_net else "Netz (aus)"
        if fe is not None and outcome is not None:
            if a_exec is not None:
                a_obs, src = a_exec, "Selbst"
            else:
                w_obs = getattr(act16.run_combined, "_wrist_tgt", None)
                a_obs = None if w_obs is None else action_vec(
                    0.0, 0.0, float(w_obs), grip=(0.3 if u_cmd else 0.0), gentle=float(u_cmd))
                src = "Teacher"
            if a_obs is not None:
                # GRADED: pass the SELF-JUDGED distance so a success is scored by how well it landed
                # (world_model.quality) instead of a flat 1.0.  Only when the agent judged it itself --
                # under ACT23_WORLD_LABEL=welt there is no self-distance and the label stays binary.
                _qd = s_d if (lbl_src == "Selbst" and s_d is not None) else None
                world.observe(fe, a_obs, outcome, dist=_qd, weight=obs_w)
                world.train(epochs=600)
                _qs = ("" if (_qd is None or not outcome)
                       else f", Guete {wm_quality(_qd):.2f} bei {_qd*1000:.0f}mm")
                if obs_w != 1.0:
                    _qs += f", Gewicht {obs_w:.2f}"
                print(f"    [Kredit] {route} -> Welt-Modell +1 ({src}, Label {lbl_src}: Wrist "
                      f"{np.degrees(wrist_of(a_obs)) % 180.0:.0f} Grad, Grip {a_obs[4]:.2f}"
                      f"{', sanft' if a_obs[5] > 0.5 else ''}, "
                      f"{'geliefert' if outcome else 'nicht geliefert'}{_qs}) -> {world.n()} Versuche",
                      flush=True)
        elif fe is not None:
            print(f"    [Kredit] {route} -- Welt-Modell enthält sich (Aktion nicht schuld)", flush=True)
        # STEP 3: SELF-IMITATION GATE.  On a Netz episode the POLICY drove; if the agent self-judges a
        # CONFIDENT delivery (the STRICT imit_tol bar -- deliberately tighter than the world-model's
        # world_tol since the asymmetric split, + not-slipped) the
        # (state, action) pairs the policy actually took become its OWN demonstrations, reinforcing what
        # worked FOR IT (blended with DAgger at fit time).  A skipped real success just loses a sample;
        # an imitated failure would poison -- hence the tight bar.  ACT23_SELFIMIT=0 disables.
        # GRADED (user's idea): the flat imit_tol bar discarded 11 of 43 genuine hits (<=25mm) in the
        # 120-ep log.  Graded, a demo no longer has to be all-or-nothing -- it enters with a WEIGHT
        # (world_model.quality: 5mm ~0.96, 15mm 0.70, 24mm ~0.40), so a merely-ok placement pulls the
        # policy proportionally less instead of being thrown away.  The admission bar widens to
        # ACT23_IMIT_BAR (25mm).  ACT23_IMIT_GRADED=0 restores the flat imit_tol gate.
        _gimit = os.environ.get("ACT23_IMIT_GRADED", "1") != "0"
        imit_bar = float(os.environ.get("ACT23_IMIT_BAR", "0.025")) if _gimit else imit_tol
        imit_ok = delivered and s_d is not None and s_d < imit_bar
        imitated = False
        if (use_net and pol_trace and lifted and imit_ok and not slipped
                and os.environ.get("ACT23_SELFIMIT", "1") == "1"):
            _q = wm_quality(s_d) if _gimit else 1.0
            added = runtime.imitate([s for s, _a in pol_trace], [a for _s, a in pol_trace],
                                    key=body, qual=_q)
            imitated = added > 0
            mix = ", ".join(f"{k or 'alt'} {v}" for k, v in
                            sorted(runtime.imit_mix().items(), key=lambda kv: -kv[1]))
            print(f"    [Selbst-Imitation] Lieferung {s_d * 1000:.0f}mm (Gewicht {_q:.2f}) -> +{added} "
                  f"Demo-Schritte ({runtime.n_imit()} im Selbst-Puffer: {mix})"
                  f"{'; Teacher-Zeilen verworfen (eigener Erfolg zählt)' if confident else ''}",
                  flush=True)
        elif use_net and pol_trace and lifted and delivered:
            print(f"    [Selbst-Imitation] Lieferung zu unsicher ({(s_d or 0) * 1000:.0f}mm) -- "
                  f"nicht imitiert", flush=True)
        # ENTKOPPELT: the widened bar must NOT also widen which episodes DISPLACE the teacher.  Dropping
        # the teacher's correction rows stays tied to the STRICT confident bar (imit_tol) -- a merely-ok
        # episode now contributes its own demos AND keeps the teacher's correction, which is exactly the
        # regime where both signals are useful.  keep-behaviour is therefore unchanged from before.
        runtime.end_episode(keep=not (imitated and confident))   # failure/uncertain -> the teacher's
        #   correction rows enter DAgger; a self-validated success keeps ONLY its own actions
        # STAGE 2 lifelong: refit the choreography on the aggregated teacher labels; report the SHADOW
        # divergence |policy - teacher| over this episode's VISITED states in BOTH modes -- on FSM
        # episodes it says how close the net is to the teacher, on NETZ episodes it says how far the
        # policy drifted from the teacher ALONG ITS OWN TRAJECTORY (the oscillating-Bilanz diagnostic:
        # a Bilanz trough with a Schatten spike = the lifelong refit moved the policy, not bad luck).
        div = runtime.shadow_divergence_mm()
        if modviz is not None:                                 # Zusammenspiel-Kurven (passiv)
            try:
                _fv = vc.surprise()
                # EINHEIT: body.last_surprise ist der FK-Fehler in METERN (pc_act14:307, Norm des
                # Vorhersagefehlers), die Kurve heisst "Koerper (mm)".  Ohne die Umrechnung landen
                # ~0.0008 auf einer Achse, die sich die Kurve mit dem Fovea-Fehler (~0.3-0.9) teilt
                # -> sie liegt optisch KONSTANT auf 0 (vom Nutzer beobachtet, 2026-08-02).
                _bs = getattr(bm.body, "last_surprise", None)
                modviz.push(fovea=(None if _fv is None else _fv.get("sensor")),
                            body_mm=(None if _bs is None else float(_bs) * 1000.0),
                            wm_mu=locals().get("_mu_a"), wm_sd=locals().get("_sd_a"),
                            pol_div_mm=div,
                            place_mm=(None if s_d is None else s_d * 1000.0),
                            tilt_deg=(np.degrees(locals().get("_tilt") or 0.0)
                                      if TILT_ACTION else None),
                            nat_deg=(np.degrees(world.natural_tilt(world.radius_of(fe)))
                                     if (TILT_ACTION and fe is not None) else None))
            except Exception as _e:
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [ModulViz] push uebersprungen: {_e}", flush=True)
        runtime.train(epochs=200)                              # act19's DAgger refits used 300; 80 underfit
        #   the shifting aggregate (user watched the net under-CLOSE the gripper -- the BC smoothing
        #   artefact that stronger refits + DAgger labels at the visited close-states sharpen)
        if np.isfinite(div):
            print(f"    [Stufe 2] Choreo-Schatten ({'Netz' if use_net else 'FSM'}-Lauf): "
                  f"|Netz-Teacher| {div:.0f} mm ({runtime.n()} DAgger + {runtime.n_imit()} Selbst, "
                  f"nachtrainiert)", flush=True)
        save_state()                                           # lifelong progress survives a restart
        if os.environ.get("ACT23_ZEIT", "1") != "0":
            _now = _time.perf_counter()
            _ges = _now - _T["gesamt"]
            _wahr = _T.get("vor_ausfuehrung", _now) - _T["gesamt"]
            _aus = _T.get("nach_ausfuehrung", _now) - _T.get("vor_ausfuehrung", _now)
            _lern = _now - _T.get("nach_ausfuehrung", _now)    # Kredit + Welt-Fit + Selbst-Imitation
            _ft = getattr(vc.fovea, "t_step", 0.0) - _fov0[0]  #   + Runtime-Refit + Speichern
            _fn = getattr(vc.fovea, "n_step", 0) - _fov0[1]
            print(f"    [Zeit] gesamt {_ges:5.1f}s | Wahrnehmung {_wahr:4.1f} | Ausfuehrung {_aus:5.1f} "
                  f"(davon Fovea {_ft:4.1f} in {_fn} Schritten"
                  f"{f', {1e3*_ft/_fn:.0f}ms/Schritt' if _fn else ''}) | Lernen {_lern:4.1f}", flush=True)
        return res.get("ok", False), res.get("err", float("nan")) * 1000.0

    # CURIOSITY-driven auto-run (the act21 researcher pattern, user request): instead of a random pick
    # the agent practices what it KNOWS LEAST.  Object = the one whose CURRENT perceived situation has
    # the highest ensemble DISAGREEMENT sigma of the outcome model over the wrist candidates (epistemic
    # uncertainty -- exactly where one more own trial teaches the model most; a freshly discovered form
    # starts data-poor -> gets practiced automatically).  Target = DISTANCE-NOVELTY over the targets
    # already practiced (coverage, act21's dreamed goals -- no reward anywhere, both signals are the
    # agent's own: model disagreement + visit history).  ACT23_AUTO_CURIOUS=0 restores the random pick.
    AUTO_CURIOUS = os.environ.get("ACT23_AUTO_CURIOUS", "1") == "1"
    tgt_visited = [state.marker_xy(i) for i in range(len(state.MARKERS))]
    sig_hist = {}                                              # label -> recent sigma readings (progress signal)

    def curious_pick():
        """Pick object + target by curiosity; returns a status line, or None -> caller picks randomly.
        LEARNING PROGRESS, not raw uncertainty (the noisy-TV fix, user-observed): a stochastic outcome
        keeps the ensemble sigma HIGH forever (aleatoric noise looks like epistemic uncertainty), so
        argmax-sigma FIXATED on the freshly discovered form and practiced nothing else.  Score = the
        recent DROP of sigma (practice is paying off) + a small sigma term (young objects start
        data-poor and must be tried at all); the object is DRAWN proportional to score -- fixation
        impossible, mastered skills keep a small maintenance share."""
        from pc_cvnn.pc_act14 import _rand_xy
        from pc_cvnn.pc_act16 import BASE_CLEAR
        scores = []
        for k, (_l, nm, _m) in enumerate(state.OBJECTS):
            fe = situation_feats(nm)
            if fe is None:
                continue                                       # camera can't find it -> not a candidate
            _mu, sd = world.predict(fe, world.candidates(0, yaw=world.yaw_of(fe)))   # sigma over the
            #   action grid HERE -- same OBJECT-RELATIVE grid the choice uses, so the curiosity score
            #   measures uncertainty over the actions actually available (not a different world-frame set)
            s = float(sd.max())
            h = sig_hist.setdefault(_l, []); h.append(s); del h[:-8]
            lp = float(np.mean(h[:len(h) // 2]) - np.mean(h[len(h) // 2:])) if len(h) >= 6 else 0.0
            scores.append((max(lp, 0.0) + 0.25 * s, lp, s, k, _l))
        if not scores or world.n() == 0:
            return None
        w = np.array([sc[0] for sc in scores]) + 1e-3
        _sc, lp_best, sd_best, k, lbl = scores[int(crng.choice(len(scores), p=w / w.sum()))]
        state.sel = k
        bodies = [nm for _l2, nm, _m2 in state.OBJECTS]
        best_p, best_z, best_nov = None, None, -1.0
        for _ in range(24):                                    # target = most NOVEL reachable spot;
            p = _rand_xy(crng)                                 #   4b: novelty in the GOAL-LATENT space
            if float(np.linalg.norm(p)) < BASE_CLEAR or any(
                    float(np.linalg.norm(p - sim.obj_pos(o)[:2])) < 0.05 for o in bodies):
                continue
            if DREAM:
                z = lgoal.encode_world(p)                      # the candidate's latent on the shared
                nov = dream_nov.score(z)                       #   dream/act manifold
            else:
                z, nov = None, min(float(np.linalg.norm(p - q)) for q in tgt_visited)
            if nov > best_nov:
                best_p, best_z, best_nov = p, z, nov
        if best_p is not None:
            state.target_idx = int(crng.integers(len(state.MARKERS)))
            state.set_marker_xy(state.target_idx, best_p); state.sync_active()
            if DREAM:
                lgoal.set_goal_vector(best_z)
                dream_nov.visit(best_z); del dream_nov.seen[:-40]   # bounded like tgt_visited: old
                #   practice fades, the workspace stays forever explorable (no novelty starvation)
            else:
                lgoal.set_goal(best_p)
                tgt_visited.append(np.asarray(best_p, float)); del tgt_visited[:-40]
        verb = "träumt Ziel" if DREAM else "neues Ziel"
        lang_info = f" | {lgoal_lang.format_latent_message(best_z, tag='z_g')}" if DREAM and best_z is not None else ""
        return (f"[curiosity] übt '{lbl}' (Fortschritt {lp_best:+.2f}, σ={sd_best:.2f})"
                + (f", {verb} [{best_p[0]:.2f},{best_p[1]:.2f}]"
                   + (f" (Latent-Neuheit {best_nov:.2f}){lang_info}" if DREAM else "")
                   if best_p is not None else ""))

    def bilanz_line(bilanz, obj_hist):
        """Rolling scoreboard, per MODE + per OBJECT (worst first).  MEASURED (150-ep run with the
        Schatten diagnostic): the Bilanz swings 13-43% while the policy's shadow stays flat ~10-12mm --
        the oscillation is mostly the CURIOSITY OBJECT MIX (corr Bilanz vs U+L share -0.68; a fixed-
        per-object-rate expectation reproduces it at r=+0.70), NOT learning instability.  Without the
        per-object split the scoreboard conflates task difficulty mix with skill."""
        parts = [f"{lbl} {sum(bilanz[md][-30:])}/{len(bilanz[md][-30:])}"
                 for md, lbl in (("fsm", "FSM"), ("netz", "Netz")) if bilanz[md]]
        per = {}
        for o, okv in obj_hist[-30:]:
            s, t = per.get(o, (0, 0)); per[o] = (s + okv, t + 1)
        objs = " · ".join(
            f"{o.replace(' Wuerfel', '').replace(' Objekt', '').replace('Neue Form ', 'Form-')} {s}/{t}"
            for o, (s, t) in sorted(per.items(), key=lambda kv: kv[1][0] / kv[1][1]))
        return ("    [Bilanz] letzte 30 je Modus: " + ", ".join(parts)
                + (f"  |  je Objekt: {objs}" if objs else ""))

    if headless and int(os.environ.get("ACT23_AUTO_N", "0")) > 0:
        # HEADLESS AUTO-RUN (for A/B measurement without the GUI): run N curiosity-picked episodes in
        # the requested choreo mode with the rolling Bilanz scoreboard -- the same loop the GUI Auto
        # button drives, minus rendering.  ACT23_CHOREO=netz + this = a long self-improvement run.
        N = int(os.environ.get("ACT23_AUTO_N"))
        state.auto = True
        print(f"  headless AUTO-Lauf: {N} Episoden, Choreo {state.choreo}, "
              f"Selbst-Imitation {'aus' if os.environ.get('ACT23_SELFIMIT','1')=='0' else 'an'}", flush=True)
        bilanz = {"fsm": [], "netz": []}
        obj_hist = []
        force_list = [s.strip() for s in os.environ.get("ACT23_AUTO_OBJ", "").split(",") if s.strip()]
        #   measurement knob: pin the auto pick to one object (label substring) or CYCLE a comma list
        #   ("U-Form,Gruenes" = interleaved practice, the interference probe); curiosity mix confounds
        #   per-object trends.  ACT23_AUTO_PLACE=0 keeps the scene AS THE LAST EPISODE LEFT IT (the
        #   inheritance probe: failures shove/wedge the object and the next episode starts from that).
        for ep in range(N):
            if force_list:
                want = force_list[ep % len(force_list)]
                ks = [k for k, (l, _n, _m) in enumerate(state.OBJECTS) if want.lower() in l.lower()]
                if not ks:
                    raise SystemExit(f"ACT23_AUTO_OBJ '{want}' matcht kein Objekt")
                state.sel = ks[0]
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                if os.environ.get("ACT23_AUTO_PLACE", "1") == "1":
                    state.place_selected_random(crng)          # random target MARKER position ...
                    # ... and MOVE THE OBJECT ITSELF to a random clear pose: place_selected_random
                    # only places the target, objects otherwise sit at their XML slots forever in a
                    # pinned probe (measured: the L stayed at the top-edge slot across ALL probes --
                    # a spot where even the guarded teacher cannot ARRIVE -- and every per-object
                    # probe silently measured that one unreachable pose).
                    from pc_cvnn.pc_act14 import _rand_xy
                    from pc_cvnn.pc_act16 import BASE_CLEAR
                    _pb = state.OBJECTS[state.sel][1]
                    _others = [nm for _l, nm, _m in state.OBJECTS if nm != _pb]
                    for _ in range(200):
                        _p = _rand_xy(crng)
                        if float(np.linalg.norm(_p)) >= BASE_CLEAR and all(
                                float(np.linalg.norm(_p - sim.obj_pos(o)[:2])) > 0.05 for o in _others):
                            break
                    sim.set_object(_pb, [float(_p[0]), float(_p[1])],
                                   yaw=float(crng.uniform(0.0, np.pi)))
                    mujoco.mj_forward(sim.m, sim.d)
                pick = None
            else:
                pick = curious_pick() if AUTO_CURIOUS else None
            if pick is None and not force_list:
                state.sel = int(crng.integers(len(state.OBJECTS)))
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                state.place_selected_random(crng)
            elif pick is not None:
                print(f"    {pick}", flush=True)
            print(f"  [Auto {ep}] {state.label()} ...", flush=True)
            ok, err = run_one()
            print(f"  [Auto {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand {err:.0f} mm",
                  flush=True)
            bilanz["netz" if state.choreo in ("netz", "attractor") else "fsm"].append(bool(ok))
            obj_hist.append((state.OBJECTS[state.sel][0], bool(ok)))
            if (ep + 1) % 10 == 0:
                print(bilanz_line(bilanz, obj_hist), flush=True)
        return

    if headless:
        def _intro_and_command():
            print("  open-set: das nie trainierte obj_T taucht auf ...")
            introduce_object()
            if NOVEL_BODY not in state.SHAPE_KEY:
                print(f"    NICHT entdeckt/registriert (Klassen: {shape_clf.open_names}, "
                      f"buffer={len(shape_clf._novel_buf)}, th={shape_clf.novel_th:.2f}) -- EXPECTED at mini "
                      f"ACT23_SHAPE_STEPS (manifold too sparse: at 250 steps known/novel OVERLAP, >=1200 "
                      f"separates; GUI default 2500 discovers).", flush=True)
                return
            print(f"    entdeckt + selbst benannt: '{state.SHAPE_KEY[NOVEL_BODY]}'  "
                  f"(Klassen: {shape_clf.open_names})", flush=True)
            state.sel = len(state.OBJECTS) - 1
            ok, err = run_one()
            print(f"    {state.OBJECTS[state.sel][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)",
                  flush=True)

        intro_first = os.environ.get("ACT23_INTRO_FIRST", "0") == "1"
        if intro_first:                                        # the USER'S race: introduce while the long I
            _intro_and_command()                               # is still undiscovered -- its class is born
        print("  headless self-test: one command per object")  # FIRST from the same glances and must NOT
        for k, _o in enumerate(CommandState23.OBJECTS):        # get bound to the T's button
            state.sel = k; ok, err = run_one()
            print(f"    {state.OBJECTS[k][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)", flush=True)
        if not intro_first:
            _intro_and_command()
        for _ in range(3):                                     # exercise the curiosity pick (GUI auto path)
            print(f"    curiosity: {curious_pick()}  -> sel={state.OBJECTS[state.sel][0]}", flush=True)
        state.choreo = "netz"                                  # STAGE 2: the LEARNED choreography drives
        print(f"  Stufe 2: Choreo-NETZ fährt die Kommandos ({runtime.n()} Teacher-Samples) ...")
        for k, _o in enumerate(CommandState23.OBJECTS):
            state.sel = k; ok, err = run_one()
            print(f"    {state.OBJECTS[k][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)", flush=True)
        return

    act16.run_combined._quiet = True
    panel.update(sim.render(CAM), "bereit — Objekt wählen, Greifer Teacher/Selbst-gelernt, Ausführen")
    ep = 0
    bilanz = {"fsm": [], "netz": []}                           # rolling per-mode delivery record: without
    #   a scoreboard slow DAgger progress is indistinguishable from noise (user: "so la la")
    obj_hist = []                                              # (object, ok) for the per-object split
    while not state.exit:
        if not (state.go or state.auto):
            panel.plt.pause(0.05); continue
        if state.auto:                                         # AUTO-Lauf: CURIOSITY picks what to practice
            pick = curious_pick() if AUTO_CURIOUS else None    #   (model uncertainty + goal novelty); random
            if pick is None:                                   #   fallback if perception/model isn't ready
                state.sel = int(crng.integers(len(state.OBJECTS)))
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                state.place_selected_random(crng)
            else:
                print(f"    {pick}", flush=True)
            panel._refresh()                                   # "Auto: aus" stoppt nach der Episode
        state.go = False
        tag = "Auto" if state.auto else "Befehl"
        print(f"  [{tag} {ep}] {state.label()} ...")
        state.busy = True
        try:
            ok, err = run_one()
        finally:
            state.busy = False
        line = f"[{tag} {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand {err:.0f} mm"
        print("  " + line); panel.update(sim.render(CAM), line); ep += 1
        bilanz["netz" if state.choreo == "netz" else "fsm"].append(bool(ok))
        obj_hist.append((state.OBJECTS[state.sel][0], bool(ok)))
        if ep % 10 == 0:                                       # rolling last-30 scoreboard per mode+object
            print(bilanz_line(bilanz, obj_hist), flush=True)
        if panel._pending_randomize:                           # deferred mid-episode clicks run NOW,
            panel._pending_randomize = False                   #   between episodes (see state.busy)
            randomize_objects(); panel.update(sim.render(CAM), "Objekte neu gewürfelt"); panel._refresh()
        if panel._pending_introduce:
            panel._pending_introduce = False
            introduce_object(); panel._refresh()
    print("  Steering beendet.")


#  Kernschalter, die IMMER protokolliert werden -- die Stellschrauben der laufenden Untersuchungen.
#  Alles andere erscheint nur, wenn es von der Vorgabe abweicht (s. _print_run_settings).
_CORE_KNOBS = ("ACT23_SEED", "ACT23_CHOREO", "ACT23_POLICY", "ACT23_STATE_PATH",
               "ACT23_GRASP_CANDS", "ACT23_GRASP_CANDS_NETZ", "ACT23_GRASP_CAND_CAP",
               "ACT23_GRIPLABEL", "ACT23_U_DENSEGRASP", "ACT23_CREDIT",
               "ACT23_TILT_ACTION", "ACT23_TILT_CURIOSITY", "ACT23_WRIST_REL",
               "ACT23_LAM", "ACT23_HOME_Z_MIN", "ACT14_DOF")


def _source_defaults():
    """Vorgabewerte ALLER Schalter direkt aus dem Quelltext lesen (os.environ.get("ACT..", "..")).

    Aus dem Quelltext statt aus einer gepflegten Liste, damit die Ausgabe nicht veraltet, sobald
    ein neuer Schalter dazukommt -- in diesem Projekt passiert das staendig.  Faellt still auf
    'nur gesetzte Variablen zeigen' zurueck, wenn die Dateien nicht lesbar sind."""
    import glob
    import re as _re
    pat = _re.compile(r'os\.environ\.get\(\s*["\'](ACT\d*[A-Z0-9_]*)["\']\s*(?:,\s*["\']([^"\']*)["\'])?')
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    try:
        files = ([os.path.join(here, n) for n in ("pc_act23.py", "pc_act16.py", "pc_act14.py")]
                 + sorted(glob.glob(os.path.join(here, "arm_modules", "*.py"))))
        for f in files:
            if not os.path.exists(f):
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                for m in pat.finditer(fh.read()):
                    out.setdefault(m.group(1), m.group(2))
    except Exception:
        pass
    return out


def _print_run_settings():
    """Die EINSTELLUNGEN des Laufs ins Log schreiben (Nutzerwunsch 2026-08-02: im Log war nicht
    nachvollziehbar, mit welchen Schaltern die GUI lief).

    Zwei Bloecke, weil ein Vollabzug aller ~138 Schalter das Log zumuellen wuerde:
      ABWEICHUNGEN  jeder Schalter, dessen Umgebungswert von der Quelltext-Vorgabe abweicht.  Das
                    ist die eigentliche Antwort auf "womit lief der Lauf" und faengt AUCH Schalter,
                    an die beim Schreiben dieser Funktion niemand gedacht hat.
      KERN          die Stellschrauben der laufenden Untersuchungen, immer sichtbar, damit man den
                    Stand auch dann sieht, wenn alles auf Vorgabe steht.
    Dazu Commit + Arbeitsbaum-Zustand, damit ein Log-Fund spaeter reproduzierbar bleibt."""
    try:
        import subprocess
        d = os.path.dirname(os.path.abspath(__file__))
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=d, capture_output=True,
                           text=True, timeout=5)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True,
                            text=True, timeout=5)
        if h.returncode == 0:
            dirty = " + ungespeicherte Aenderungen" if st.stdout.strip() else ""
            print(f"  [Lauf] Commit {h.stdout.strip()}{dirty}", flush=True)
    except Exception:
        pass
    defs = _source_defaults()
    diff = []
    for k, dv in sorted(defs.items()):
        v = os.environ.get(k)
        if v is not None and v != dv:
            diff.append(f"{k}={v} (Vorgabe {dv!r})")
    for k, v in sorted(os.environ.items()):          # gesetzt, aber im Quelltext nicht gefunden
        if k.startswith("ACT") and k not in defs:
            diff.append(f"{k}={v} (keine Vorgabe im Quelltext)")
    if diff:
        print("  [Lauf] Abweichungen von der Vorgabe:", flush=True)
        for line in diff:
            print(f"           {line}", flush=True)
    else:
        print("  [Lauf] alle Schalter auf Vorgabe", flush=True)
    core = [f"{k.replace('ACT23_', '').replace('ACT14_', '')}={os.environ.get(k, defs.get(k))}"
            for k in _CORE_KNOBS if (k in os.environ or k in defs)]
    print("  [Lauf] Kern: " + "  ".join(core), flush=True)


class _Tee:
    """Mirror a console stream into a log file (user request: every session leaves a log).
    The FILE skips carriage-return progress spam (warmup/train tickers), PREFIXES every line with
    a wall-clock timestamp and writes UTF-8 regardless of the console codepage; the CONSOLE stream
    is passed through untouched (unstamped -- the timestamps are for post-hoc log analysis).

    WARUM DIE ZEITSTEMPEL (2026-08-02): der Nutzer sah die Kamera-Anzeige stehen und konnte nicht
    entscheiden, ob der Lauf haengt oder nur das Fenster nicht neu zeichnet -- und das LOG konnte
    es auch nicht, weil keine Uhrzeit drinstand.  Mit Stempel je Zeile sieht man sofort, ob die
    Episoden zum fraglichen Zeitpunkt weiterliefen (Anzeige-Problem) oder nicht (echter Haenger),
    und nebenbei, welche Phase wieviel Zeit kostet.  ACT23_LOG_TIME=0 schaltet es ab."""

    STAMP = os.environ.get("ACT23_LOG_TIME", "1") != "0"

    def __init__(self, stream, fh):
        self._s = stream
        self._f = fh
        self._bol = True                               # steht der Schreibkopf am Zeilenanfang?

    def _stamped(self, data):
        """Zeitstempel an jeden ZEILENANFANG.  write() bekommt beliebige Bruchstuecke (print gibt
        Text und '\\n' getrennt aus), darum wird der Zeilenanfang ueber Aufrufe hinweg gemerkt --
        sonst landete der Stempel mitten in der Zeile.  Leerzeilen bleiben leer."""
        if not self.STAMP:
            return data
        import time
        out = []
        for part in data.splitlines(keepends=True):
            if self._bol and part not in ("\n", "\r\n"):
                out.append(time.strftime("%H:%M:%S "))
            out.append(part)
            self._bol = part.endswith("\n")
        return "".join(out)

    def write(self, data):
        try:                                           # a dying console pipe (e.g. truncated by the
            self._s.write(data)                        # shell) must not kill the FILE log, and vice
        except Exception:                              # versa -- each side fails independently
            pass
        if "\r" not in data:
            try:
                self._f.write(self._stamped(data))
                self._f.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self._s.flush()
        except Exception:
            pass
        try:
            self._f.flush()
        except Exception:
            pass

    def __getattr__(self, name):                       # encoding, isatty, buffer, ...
        return getattr(self._s, name)


def _start_session_log():
    """Tee stdout+stderr into log/pc_act23_<timestamp>.txt at the repo root (ACT23_LOG=0 off)."""
    if os.environ.get("ACT23_LOG", "1") != "1":
        return
    import datetime
    d = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "log"))
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"pc_act23_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.txt")
    fh = open(path, "a", encoding="utf-8", errors="replace")
    sys.stdout = _Tee(sys.stdout, fh)
    sys.stderr = _Tee(sys.stderr, fh)
    print(f"  [Log] Konsole wird mitgeschrieben: {path}", flush=True)


if __name__ == "__main__":
    _start_session_log()
    if os.environ.get("ACT23_VIZ", "0") == "1":
        run_self_learning_steering(headless=(os.environ.get("ACT23_VIZ_HEADLESS", "0") == "1"))
    elif os.environ.get("ACT23_MODE", "diag").lower() == "shapes":
        main()
    else:
        main_diag()
