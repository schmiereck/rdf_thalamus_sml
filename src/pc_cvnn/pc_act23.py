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

from pc_cvnn.pc_act14 import BracketArmSim, HOME
from pc_cvnn.pc_act18 import F as HEX_F
from pc_cvnn.arm_modules.body_model import BodyModelModule
from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule
from pc_cvnn.arm_modules.object_orientation import ObjectOrientationModule
from pc_cvnn.arm_modules.world_model import WorldModelModule, feats_from, action_vec, wrist_of
import pc_cvnn.pc_act16 as act16

CAM = "overview"
BODY = {"cube": "obj_red", "L": "obj_L", "U": "obj_U"}
ALL = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
TARGET = np.array([0.0, 0.10])


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
    return np.array([rng.uniform(-0.09, 0.09), rng.uniform(0.10, 0.18)])


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
               "obj_L": "#d98a2b", "obj_U": "#27b3b3"}

    def __init__(self, sim):
        self.sim = sim; self.sel = 0; self.action = "grasp"; self.target_idx = 0
        self.policy = "self"          # "self" -> world-model wrist (long obj); "teacher" -> WRIST_ALIGN
        self.go = False; self.exit = False

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
        return f"{self.selected()[0]} | {act} | Greifer: {pol} | Ziel {self.target_idx + 1}"


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
        # grasp-policy toggle
        axPol = self.fig.add_axes([0.62, 0.150, 0.155, 0.055])
        self.bPol = Button(axPol, "", color="#3a5a44", hovercolor="#4a7256"); self.bPol.on_clicked(self._toggle_policy)
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
        self._randomize_fn(); self.update(self.state.sim.render(self._cam), "Objekte neu gewürfelt"); self._refresh()

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
    RES = int(os.environ.get("ACT23_RES", "240"))
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    NPOS = int(os.environ.get("ACT23_NPOS", "10")); NTRIAL = int(os.environ.get("ACT23_NTRIAL", "5"))
    LONG = "obj_blue"; LONG_HALF = (0.034, 0.009, 0.012)   # clearly a LONG thin bar (not a cube)
    CUBE_BODIES = ["obj_red", "obj_green"]

    print("act23 [viz] — self-learning grasper command-steering" + (" (headless self-test)" if headless else ""))
    sim = BracketArmSim(render_wh=(RES, RES)); sim.set_reach_site("contact")
    shape_half0 = {nm: sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]].copy()
                   for nm in ("obj_L", "obj_U")}           # pristine XML first-geom half-extents (repair below)
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    state = CommandState23(sim)
    panel = None
    if not headless:
        panel = CommandPanel23(state, CAM, RES, rng=np.random.default_rng(7))
        panel.update(sim.render(CAM), "Training: Farb-Wahrnehmung (Würfel + Formen als Distraktoren streuen) ...")
    os.environ["ACT18_SCATTER_EXTRA"] = "obj_L,obj_U"   # scatter the shapes too during vc warmup (consistency)
    vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=True,
                                         viz=(panel.fov_viz if panel is not None else None))
    if panel is not None:
        panel.update(sim.render(CAM), "Form-Wahrnehmung wird trainiert ...")
    shape_clf = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
    saved = sim.d.mocap_pos.copy(); shape_clf.calibrate(sim)

    def _shape_viz(i, steps, shp):                             # show the form-training live (one shape at a time)
        panel.update(sim.render(CAM), f"Form-Wahrnehmung: {i}/{steps}  (lernt gerade: {shp})")

    shape_clf.train(sim, steps=int(os.environ.get("ACT23_SHAPE_STEPS", "2500")), rng=np.random.default_rng(1),
                    viz_fn=(_shape_viz if panel is not None else None),
                    viz_every=int(os.environ.get("ACT23_SHAPE_VIZ_EVERY", "40")))
    sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)

    # self-supervised world model for the GRASP WRIST (collect own trials, then train).
    # OPEN-WORLD situation features -- ONE camera perception path (|F| pipeline) for EVERY object:
    #   [pos(2), cos/sin(2*yaw), cos/sin(4*yaw4), desc_embed(NH)]
    # yaw (k=2 phase, mod pi) carries an ELONGATED object's axis; yaw4 (k=4 phase, mod pi/2) carries a
    # SQUARE's orientation -- k=2 is DEGENERATE on a cube, and the fixed teacher wrist (WRIST_TGT mod
    # 90deg) is exactly what slips off DIAGONAL cubes now that the continuous scene keeps their random
    # yaw (scatter() used to re-place them axis-aligned each episode, masking the gap).  The descriptor
    # embedding (no class one-hot) lets this ONE model absorb trials from any form.  (The former
    # ObjectOrientationModule features are subsumed by the k=2 phase -- one perception path, no oo.)
    world = WorldModelModule(k=5, off_max=0.0, rng=np.random.default_rng(2), feat_dim=6 + shape_clf.NH)

    def situation_feats(cmd):
        """PERCEIVED situation of `cmd` for the world model (None if the camera can't find it).  The
        privileged position is only a MATCHING aid; the features themselves are the detection's."""
        p_ref = sim.obj_pos(cmd)[:2]
        saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        dets = [d for d in dets if d["pos"] is not None]
        if not dets:
            return None
        best = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - p_ref)))
        if float(np.linalg.norm(np.asarray(best["pos"]) - p_ref)) > 0.05:
            return None                                    # nearest blob is a DIFFERENT object -> no honest read
        y2, y4 = float(best["yaw"]), float(best["yaw4"])
        return np.concatenate([np.asarray(best["pos"], float),
                               [np.cos(2 * y2), np.sin(2 * y2), np.cos(4 * y4), np.sin(4 * y4)],
                               shape_clf.desc_embed(best["desc"])])

    bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, LONG)
    crng = np.random.default_rng(7); act16.run_combined._quiet = True

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

    def grasp_trial(cmd, wrist, gxy):
        wf = None if wrist is None else (lambda s, _w=wrist: _w)
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=cmd, force="grasp",
                                  perceive_fn=lambda c: (gxy, None, "grasp"), policy_fn=None, servo=False,
                                  goal_fn=lambda c, o: TARGET, rescatter=False, wrist_fn=wf)
        return int(d)

    def collect_trials(cmd, label, yaw_hi):
        """Self-supervised wrist trials on `cmd`: random pose + yaw, RANDOM wrist, the OWN delivered/not
        outcome as the only label.  act16.OBJS=[cmd]: this object IS the scene -- park_all() parks the
        others OUTSIDE run_combined's stray bounds, and with them in OBJS reposition_strays() would drop
        them back onto the table as surprise distractors.  (Restored to all 5 for the steering scene.)"""
        act16.OBJS = [cmd]
        print(f"  collecting OWN trials: {label} ({NPOS}x{NTRIAL}) ...")
        for j in range(NPOS):
            p = rand_pos(crng); yaw = crng.uniform(0, yaw_hi); setup_obj(cmd, p, yaw)
            fe = situation_feats(cmd)
            if fe is None:
                continue                                       # camera can't see it here -> no honest trial
            for _ in range(NTRIAL):
                w = crng.uniform(0, np.pi); setup_obj(cmd, p, yaw)
                world.observe(fe, action_vec(0, 0, w), grasp_trial(cmd, w, sim.obj_pos(cmd)[:2]))
            if panel is not None and j % 2 == 0:
                panel.update(sim.render(CAM), f"Selbst-Lernen ({label}): {(j + 1) * NTRIAL}/{NPOS * NTRIAL} Versuche")

    collect_trials(LONG, "langes Objekt", np.pi)
    collect_trials("obj_red", "Würfel, auch diagonal", np.pi / 2)   # cube yaw mod pi/2 (square symmetry);
    #   the descriptor is COLOUR-agnostic, so red-cube trials transfer to the green cube too
    world.train(epochs=600)
    print(f"  world model trained on {world.n()} own trials.")

    scene = {}                                                 # intended (body -> (xy, z, yaw)); the scene is FIXED
    #   after placement and restored per command, so only the commanded object moves.
    # DETERMINISTIC well-spread SLOTS: the workspace (x +-0.11, y 0.07..0.21, minus the base-clear disk) is too
    # small for random rejection-sampling to reliably separate 5 biggish objects -- it fails and falls back to a
    # central clump.  Fixed slots (shuffled onto the objects + small jitter) GUARANTEE a spread, non-dense scene.
    # SPACING matters: the L spans 56mm (reach ~35mm from its centre), so two shapes pointing at each other need
    # ~70mm of centre clearance or their geoms INTERPENETRATE at placement.  mj_forward doesn't resolve contacts,
    # so an overlap is INVISIBLE in the placed render -- then the first sim.step in run_combined ejects the
    # overlapping shape ("a segment snaps/twists shortly after Ausfuehren").  These slots keep every pair >=87mm
    # apart; with the small jitter below the worst case stays ~76mm > 70mm, so no overlap can occur.
    SLOTS = [(-0.09, 0.20), (0.0, 0.20), (0.09, 0.20), (-0.055, 0.12), (0.055, 0.12)]

    def randomize_objects():
        sim.reset_home()
        order = list(range(len(SLOTS))); crng.shuffle(order)   # random object<->slot assignment (variety)
        for (_l, nm, m), si in zip(state.OBJECTS, order):
            p = np.array(SLOTS[si], float) + crng.uniform(-0.004, 0.004, 2)   # small jitter
            z = float(LONG_HALF[2]) if m == "long" else 0.012
            yaw = crng.uniform(0, np.pi) if m == "long" else crng.uniform(0, 2 * np.pi)
            scene[nm] = (p, z, float(yaw))
        place_all()
        if panel is not None:                                  # show the placed scene immediately (decide from it)
            panel.update(sim.render(CAM), "Szene platziert — Objekt wählen und Ausführen")

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

    if panel is not None:
        panel._randomize_fn = randomize_objects     # wire "Objekte neu" (panel built before randomize_objects existed)
    randomize_objects()
    # CONTINUITY: make run_combined treat ALL 5 objects as its scene -> with SCENE_N = all, keep=all so it never
    # PARKS a distractor off-table, and reposition_strays never fires (nothing is a stray) -> nothing teleports.
    # The scene just evolves: only the commanded object is grasped + delivered (and STAYS), like real life.
    act16.OBJS = [nm for _l, nm, _m in state.OBJECTS]
    act16.SCENE_N = len(act16.OBJS)

    def perceive(cmd):
        _l, body, method = state.selected()
        if method == "shape":                                  # L/U: FORM perception (shape classifier)
            saved = sim.d.mocap_pos.copy()                     # select() PARKS the mocap markers -> restore the
            det = shape_clf.select(sim, state.SHAPE_KEY[body])  #   target markers, else goal_fn returns a parked goal
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if det is not None:
                return np.asarray(det["grasp_xy"], float), None, "grasp"
            return sim.obj_pos(body)[:2], None, "grasp"        # perception missed -> privileged fallback
        if method == "long":                                   # the elongated obj is OOD for the colour vc;
            return sim.obj_pos(body)[:2], None, "grasp"        #   localise privileged (act23 point = the WRIST)
        return vc.perceive(body), None, None                   # cubes: the net localises by colour

    def plot_surprise():
        if panel is not None:
            s = vc.surprise()
            q3 = sim.arm3_angles()                             # body-model FK surprise: predicted vs real hand
            bmm = float(np.linalg.norm(bm.body.fk(q3) - sim.grasp_pos())) * 1000.0   # (was always 0: wrong attr)
            if s is not None:
                panel.surp_viz.push(s["sensor"], s["state"], s["total"], s["relax"], bmm)

    def track_and_plot():
        obs = vc.track()
        plot_surprise()
        return obs

    def make_shape_track(body):
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
        The hex net can't be command-keyed to a FORM, so the form tracker DRIVES the hex view itself:
        one perception step at the followed px (fovea.step: lifelong hex learning + surprise stay alive)
        and the viz drawn at the SAME gaze -- box and cells consistent, no colour-keyed follow step to
        fight the pin, no zoom-out spiral (v1 called vc.track() from the pin: the colour drive walked the
        box away from the sampled crop and zoomed out every frame -- the user's frozen/mismatched views)."""
        key = state.SHAPE_KEY[body]
        mem = {"xy": None, "px": None}                         # world belief (servo) + image belief (display)
        vc.fovea.z = 1.0                                       # defined DETAIL zoom for the form view

        def _track():
            saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
            dets = shape_clf.perceive_all(sim)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            obs, conf = None, 0.0
            cands = [d for d in dets if d["shape"] == key and d["pos"] is not None]
            if cands:
                best = (max(cands, key=lambda d: d["prob"]) if mem["xy"] is None
                        else min(cands, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - mem["xy"]))))
                if mem["xy"] is None or float(np.linalg.norm(np.asarray(best["pos"]) - mem["xy"])) <= 0.05:
                    obs = np.asarray(best["grasp_xy"], float)  # correct toward the GRASP point (what the belief
                    conf = float(best["prob"])                 #   holds), not the centroid (off-material on L/U)
                    mem["xy"] = np.asarray(best["pos"], float); mem["px"] = np.asarray(best["px"], float)
            if obs is None and mem["px"] is not None and dets:  # class match failed (lifted/mis-class) ->
                near = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["px"]) - mem["px"])))
                if float(np.linalg.norm(np.asarray(near["px"]) - mem["px"])) < 40.0:   # follow the blob in px
                    mem["px"] = np.asarray(near["px"], float)
            if mem["px"] is not None:                          # form tracker drives the hex fovea view
                gaze = np.clip(mem["px"], HEX_F * vc.fovea.K, RES - HEX_F * vc.fovea.K)
                vc._P["state"]["gaze"] = gaze
                img = sim.render(CAM)
                arr = vc.fovea.step(img, gaze, vc._P["state"]["cmd"], True)
                if vc.viz is not None:
                    vc.viz.fovea(img, gaze, vc.fovea._ek(), np.clip(arr[:, :, 1:], 0, 1),
                                 f"Form-Tracker folgt {key}")
                plot_surprise()
            else:
                track_and_plot()                               # nothing tracked yet -> the colour follow frame
            return obs, conf

        return _track

    HOME_Q3 = np.array([HOME[j] for j in ("joint_0", "joint_1", "joint_2")])

    def drive_home():
        """CONTINUOUS episode transition: after the release the arm DRIVES back to (near) its home posture
        under its normal actuators (the same reach primitive the episode uses) instead of the qpos teleport
        arm_home() does -- a physical robot can't teleport, and the user wants sim runs to stay connectable
        to the real rig.  Two legs: RAISE the claw first (a low sideways retreat could sweep the just-placed
        object), then bounded joint-space steps toward home.  NEAR home is enough (0.05 rad/joint): the next
        episode starts from a SIMILAR pose, not a bit-identical one (run_combined gets arm_reset=False)."""
        sim.target("joint_5", act16.J5_OPEN)
        for k in range(60):                                    # leg 1: straight up to carry height
            q3 = sim.arm3_angles(); h = sim.grasp_pos()
            if h[2] > act16.CARRY_Z - 0.01:
                break
            sim.set_arm3_targets(q3 + bm.body.reach_velocity(q3, np.array([h[0], h[1], act16.CARRY_Z]),
                                                             gain=2.0, max_dq=0.026))
            sim.step(2)
            if panel is not None and k % 8 == 0:
                panel.update(sim.render(CAM), "Arm hebt ab ...")
        for k in range(240):                                   # leg 2: drive the joints home, bounded speed
            q3 = sim.arm3_angles()
            if float(np.max(np.abs(q3 - HOME_Q3))) < 0.05:
                break
            sim.set_arm3_targets(q3 + np.clip(HOME_Q3 - q3, -0.03, 0.03))
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
        _l, body, method = state.selected()
        # SNAPSHOT every object's pose before acting.  run_combined parks distractor cubes off-table and the
        # arm can knock objects -> afterwards restore all NON-commanded objects to exactly here, so the scene
        # stays put and only the commanded object moves (to the target).  No more surprise re-scatter.
        snap = {nm: (sim.obj_pos(nm)[:2].copy(), float(sim.obj_pos(nm)[2]), float(sim.obj_yaw(nm)))
                for _l2, nm, _m in state.OBJECTS}
        if _dbg: print(f"    [dbg] before  : {_pos()}", flush=True)
        _save(f"{body}_0before")
        if method in ("color", "long"):                        # drive the FOVEA to the commanded object (display);
            try:                                               #   the grasp itself uses perceive() above
                vc.perceive(body)
                if panel is not None:
                    track_and_plot(); panel.update(sim.render(CAM), f"Fovea -> {_l}")
            except Exception:
                pass
        u_cmd = (body == "obj_U"); wf = None
        fe = situation_feats(body)                               # perceived situation for the LIFELONG loop
        w_exec = None                                            # wrist this episode actually runs (self mode)
        # SELF-LEARNED wrist: the long object AND the colour cubes.  The teacher's cube wrist is a FIXED
        # world angle (WRIST_TGT mod 90deg) -- exactly what slips off a DIAGONAL cube; the model instead
        # conditions on the perceived k=4 orientation.  L/U keep the teacher wrist (no own L/U trials
        # yet), but their episodes DO feed the model below, so that data accumulates for later.
        if state.policy == "self" and method in ("color", "long") and fe is not None:
            a, _, _ = world.select_action(fe, n=0, lam=LAM); w_exec = wrist_of(a)
            wf = (lambda s, _w=w_exec: _w)
        # CLOSED-LOOP fovea: servo=True lets the live tracker CORRECT the grasp-target belief during the
        # reach (+ occlusion memory).  COLOUR cubes track via the hex fovea (vc.track); L/U now track via
        # the FORM-aware tracker (make_shape_track: perceive_all per frame, matched by SHAPE class) -- the
        # user's fovea goal: the fovea supports approach+grasp for the shapes too, instead of sitting on
        # whatever colour was last commanded.  Only the long object stays servo=False (not a class the
        # form tracker can key on; its colour is OOD for the hex fovea -> both trackers would mislead).
        track_fn = make_shape_track(body) if method == "shape" else track_and_plot
        act16.run_combined(sim, bm.body, panel, CAM, episodes=1, cmd_fixed=state.cmd_fn, force=state.force_fn,
                           goal_fn=state.goal_fn, perceive_fn=perceive, track_fn=track_fn,
                           policy_fn=None, servo=(method in ("color", "shape")), rescatter=False, episode_end_fn=ep_end,
                           lifelong=True, carry_gentle=u_cmd, grip_close=(0.3 if u_cmd else None), wrist_fn=wf,
                           arm_reset=False)
        _save(f"{body}_1after_runcombined")
        drive_home()                          # retreat FIRST: restoring an object under the still-lowered arm
        #   could re-create contact under the claw; and the next episode then starts from ~home WITHOUT a reset
        # CONTINUITY + keep the shapes UPRIGHT: leave the COMMANDED object where the action left it (delivered
        # + staying), but put every NON-commanded object back on its pre-command pose.  set_object writes a pure
        # z-rotation, so this also UN-TIPS any shape the arm nudged onto its side (the thin 24mm-tall L/U bars
        # tip easily).  No teleport (OBJS=all5 above), no full reset -- the scene just evolves as you command.
        _set_sizes()
        for _l2, nm, _m in state.OBJECTS:
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
        if panel is not None:                                  # refresh the hex fovea views with the RESTORED
            try:                                               #   scene: they last rendered a pre-restore frame,
                track_and_plot()                               #   so after the object snap-back the views showed
            except Exception:                                  #   an inconsistent (stale) object layout
                pass
        if _dbg:
            print(f"    [dbg] after ep : {_pos()}", flush=True)
            hs = {nm: np.round(sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] * 1000, 1).tolist()
                  for nm in ("obj_L", "obj_U")}            # the exact failure mode: a resized L/U first geom
            print(f"    [dbg] L/U half : {hs}  (XML: L [7,28,12] U [7,14,12])", flush=True)
        _save(f"{body}_2after_restore")
        # LIFELONG loop (EVERY object): every command IS a trial.  Log the perceived situation, the wrist
        # that actually ran (self-selected, OR the teacher's -- run_combined exposes it as _wrist_tgt, so
        # Teacher commands keep feeding the model as demonstrations; for L/U that is currently the only
        # source) and the OWN outcome, then refit the ensemble.  The model keeps learning from its acting:
        # a wrist it currently believes in but that is unreliable (e.g. the squeeze-rotate long-side grip,
        # or a diagonal-cube slip) gets corrected by its own failures over time.
        if fe is not None:
            w_obs = w_exec if w_exec is not None else getattr(act16.run_combined, "_wrist_tgt", None)
            if w_obs is not None:
                world.observe(fe, action_vec(0.0, 0.0, float(w_obs)), res.get("ok", False))
                world.train(epochs=600)
                print(f"    [lifelong] Welt-Modell +1 Versuch ({'Selbst' if w_exec is not None else 'Teacher'}"
                      f"-Wrist {np.degrees(float(w_obs)) % 180.0:.0f} Grad, "
                      f"{'geliefert' if res.get('ok', False) else 'nicht geliefert'}) -> "
                      f"{world.n()} Versuche, nachtrainiert", flush=True)
        return res.get("ok", False), res.get("err", float("nan")) * 1000.0

    if headless:
        print("  headless self-test: one command per object")
        for k in range(len(state.OBJECTS)):
            state.sel = k; ok, err = run_one()
            print(f"    {state.OBJECTS[k][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)", flush=True)
        return

    act16.run_combined._quiet = True
    panel.update(sim.render(CAM), "bereit — Objekt wählen, Greifer Teacher/Selbst-gelernt, Ausführen")
    ep = 0
    while panel.wait() != "exit":
        state.go = False
        print(f"  [Befehl {ep}] {state.label()} ...")
        ok, err = run_one()
        line = f"[Befehl {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand {err:.0f} mm"
        print("  " + line); panel.update(sim.render(CAM), line); ep += 1
    print("  Steering beendet.")


if __name__ == "__main__":
    if os.environ.get("ACT23_VIZ", "0") == "1":
        run_self_learning_steering(headless=(os.environ.get("ACT23_VIZ_HEADLESS", "0") == "1"))
    elif os.environ.get("ACT23_MODE", "diag").lower() == "shapes":
        main()
    else:
        main_diag()
