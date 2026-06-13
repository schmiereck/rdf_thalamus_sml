r"""
pc_act18.py — Phase 1 of porting the 1D LEARNING core back onto the MuJoCo arm:
a LEARNED hex PC-net perceives the camera fovea, and the fovea FOLLOWS the commanded
object error-drivenly (active-inference `fovea_gradient`), instead of the scripted scan.

What this restores (lost in act14-17):
  * a real PC perception NET (hex sensor sheet) that LEARNS the camera scene (net.step learn),
    instead of hand-coded colour-COM;
  * the fovea sensors are HEX-arranged (odd-r offset), so we SAMPLE the camera image at hex
    positions (not a square grid) — matching the lateral hex wiring;
  * an error-driven, object-FOLLOWING fovea (`-fovea_gradient` on the conditioned `sel`
    channel) + saccadic search, instead of a one-shot scripted 5x5 scan.

Kept: the learned 3-D kinematics + the act16 grasp pipeline (the perceived object/target feed it).

  ACT18_HEADLESS=1   metrics   ACT18_PERCEPT=1   perception-only test (no grasping)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.test_pc_act10 import F, com2d, hex_neighbors, fovea_gradient
from pc.pc_act14 import BracketArmSim, ArmBodyModel3D, REACH_XY, _rand_xy, ARM3
import pc.pc_act16 as act16

CMD_COLOR = {"obj_red": np.array([0.9, 0.1, 0.1]), "obj_green": np.array([0.1, 0.85, 0.1]),
             "obj_blue": np.array([0.15, 0.3, 0.95])}
MAGENTA = np.array([1., 0, 1.])
MATCH_TH = 0.86
HEX_DY = 0.8660254              # row spacing of a hex lattice (sqrt(3)/2)


# --------------------------------------------------------------------------- #
def build_hexnet4(rng):
    """Hex sensor sheet, cells dim 4 = [sel, R, G, B]  (sel = conditioned/commanded colour)."""
    net = PCNetwork(eta_inf=0.05, n_relax=20, eps_tol=1e-5, eta_learn=0.006,
                    gamma=0.3, w_clip=3.0, rng=rng)
    cells = {}
    for r in range(F):
        for c in range(F):
            cells[(r, c)] = net.add(SensorNode(f"s_{r}_{c}", dim=4))
    for r in range(F):
        for c in range(F):
            for (rr, cc) in hex_neighbors(r, c, F, F):
                net.connect(f"s_{r}_{c}", f"s_{rr}_{cc}", ConnType.LATERAL, pressure_scale=0.1)
    h1 = []
    for r in range(0, F, 2):
        for c in range(0, F, 2):
            nid = f"h1_{r}_{c}"
            net.add(PCNode(nid, dim=12, activation="tanh", rng=rng)); h1.append(nid)
            for (rr, cc) in [(r, c)] + hex_neighbors(r, c, F, F):
                net.connect(nid, f"s_{rr}_{cc}", ConnType.UP, pressure_scale=1.0)
    net.add(PCNode("top", dim=10, activation="tanh", rng=rng))
    for nid in h1:
        net.connect("top", nid, ConnType.UP, pressure_scale=0.3)
    return net, cells, h1


def patch_mean(img, cx, cy, half):
    x0 = int(round(cx - half)); y0 = int(round(cy - half))
    sub = img[max(0, y0):y0 + 2 * half + 1, max(0, x0):x0 + 2 * half + 1]
    if sub.size == 0:
        return np.zeros(3)
    return sub.reshape(-1, 3).mean(0) / 255.0


def hex_sample(img, gaze, K, cmd_rgb):
    """Sample the camera image at the F×F HEX cell positions (odd rows offset half a cell) ->
    F×F×4 [sel,R,G,B].  sel = luminance where the cell colour matches the commanded colour."""
    out = np.zeros((F, F, 4)); cn = cmd_rgb / np.linalg.norm(cmd_rgb); half = max(1, K // 2)
    for r in range(F):
        cy = gaze[1] + (r - (F - 1) / 2) * K * HEX_DY
        for c in range(F):
            cx = gaze[0] + (c + 0.5 * (r & 1) - (F - 1) / 2) * K
            rgb = patch_mean(img, cx, cy, half); out[r, c, 1:] = rgb
            lum = rgb.sum()
            if lum > 0.18 and float(rgb @ cn) / (np.linalg.norm(rgb) + 1e-6) > MATCH_TH:
                out[r, c, 0] = lum
    return out


def set_sheet4(cells, arr):
    for r in range(F):
        for c in range(F):
            cells[(r, c)].set_input(arr[r, c])


# --------------------------------------------------------------------------- #
class HexFoveaViz:
    """Left: real camera + the fovea window and its HEX sample points.  Right: the cells the
    net sees, drawn in their HEX arrangement (odd rows offset half a cell)."""
    def __init__(self, cam, res):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        self.plt = plt; self._Rect = Rectangle; plt.ion()
        self.fig, (self.axI, self.axC) = plt.subplots(1, 2, figsize=(9.8, 5),
                                                      gridspec_kw={"width_ratios": [3, 1.4]})
        self.fig.patch.set_facecolor("#0e0e12")
        self.axI.set_title(f"act18 — {cam} camera (real view)", color="w"); self.axI.axis("off")
        self.axC.set_title("net sees (HEX cells)", color="w")
        self.axC.set_facecolor("#0e0e12"); self.axC.set_xticks([]); self.axC.set_yticks([])
        self.imI = self.axI.imshow(np.zeros((res, res, 3), np.uint8))
        self.rect = self._Rect((0, 0), 10, 10, fill=False, ec="#33ccff", lw=1.5, ls="--")
        self.axI.add_patch(self.rect)
        (self.gz,) = self.axI.plot([], [], "+", ms=12, mew=2, color="#33ccff")
        (self.dots,) = self.axI.plot([], [], ".", ms=2.5, color="#33ccff", alpha=0.6)
        self.axC.set_xlim(-1, F + 0.5); self.axC.set_ylim(F * HEX_DY, -1); self.axC.set_aspect("equal")
        self.cellp = [[self._Rect((c + 0.5 * (r % 2) - 0.5, r * HEX_DY - 0.5 * HEX_DY), 1.0, HEX_DY,
                                  ec="#222", lw=0.3) for c in range(F)] for r in range(F)]
        for row in self.cellp:
            for p in row:
                self.axC.add_patch(p)
        self.txt = self.axI.text(0.02, 0.98, "", transform=self.axI.transAxes, va="top",
                                 color="w", fontsize=9, family="monospace")

    def fovea(self, frame, gaze, K, cells_rgb, txt):
        self.imI.set_data(frame)
        w, h = F * K, F * K * HEX_DY
        self.rect.set_width(w); self.rect.set_height(h); self.rect.set_xy((gaze[0] - w / 2, gaze[1] - h / 2))
        self.gz.set_data([gaze[0]], [gaze[1]])
        xs, ys = [], []                                     # HEX sample points on the image
        for r in range(F):
            cy = gaze[1] + (r - (F - 1) / 2) * K * HEX_DY
            for c in range(F):
                xs.append(gaze[0] + (c + 0.5 * (r & 1) - (F - 1) / 2) * K); ys.append(cy)
        self.dots.set_data(xs, ys)
        for r in range(F):
            for c in range(F):
                self.cellp[r][c].set_facecolor(tuple(np.clip(cells_rgb[r, c], 0, 1)))
        self.txt.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def update(self, frame, txt=""):
        self.imI.set_data(frame); self.txt.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def hold(self):
        self.plt.ioff(); self.plt.show()


class SurpriseViz:
    """Live curves of the PC modules' SURPRISE (prediction error) over time.

    Grouped explicitly BY PC MODULE (the act14–19 line keeps the 1D separation as classes,
    not as registered PCModule ports):
      * VisualCortex  — the perception hex-net, a real PCNetwork: `sensor_error` is the
                        SURPRISE (squared prediction-vs-input error at the clamped sensor
                        nodes), plus `state_error` (belief nodes), `total_error`, and
                        `relax_steps` (a second surprise proxy: a familiar scene settles fast).
      * Körpermodell  — ArmBodyModel3D (learned linear FK, not a PCNetwork): its surprise is
                        the kinematics error in mm (||predicted hand - observed hand||).
      * Planner       — NOT present in act14–19 (it lived only in the 1D line); shown as a
                        labelled-but-empty channel so its absence is explicit, not a data gap.

    A live numeric readout shows the CURRENT value per module.  Call `push(...)` once per
    frame; it redraws (throttled) so you watch the curves grow."""

    def __init__(self, title="PC modules — surprise over time", redraw_every=3, window=600):
        import matplotlib.pyplot as plt
        self.plt = plt; plt.ion()
        self.fig, (self.axE, self.axR) = plt.subplots(2, 1, figsize=(7.6, 6.6), sharex=True)
        self.fig.patch.set_facecolor("#0e0e12"); self.fig.suptitle(title, color="w")
        self._k = 0; self._redraw_every = max(1, int(redraw_every)); self._win = int(window)
        self.t = []; self.sensor = []; self.state = []; self.total = []; self.relax = []; self.body = []
        for ax in (self.axE, self.axR):
            ax.set_facecolor("#0e0e12"); ax.grid(True, color="#333", lw=0.4)
            ax.tick_params(colors="w"); [s.set_color("#555") for s in ax.spines.values()]
        self.axE.set_title("MODULE: VisualCortex  (perception hex-net — a real PCNetwork)",
                           color="#ff8888", fontsize=9)
        (self.lS,) = self.axE.plot([], [], color="#ff5566", lw=1.4, label="sensor_error (SURPRISE)")
        (self.lT,) = self.axE.plot([], [], color="#ffaa33", lw=1.0, alpha=0.8, label="state_error")
        (self.lU,) = self.axE.plot([], [], color="#888", lw=0.8, alpha=0.6, label="total_error")
        self.axE.set_ylabel("squared error", color="w")
        self.axE.legend(loc="upper right", facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=7)
        self.axR.set_title("MODULE: Körpermodell (ArmBodyModel3D)   +   VisualCortex relax effort",
                           color="#88ff88", fontsize=9)
        (self.lR,) = self.axR.plot([], [], color="#33ccff", lw=1.2, label="relax_steps (VisualCortex)")
        self.axR.set_ylabel("relax steps", color="#33ccff"); self.axR.set_xlabel("perception step", color="w")
        self.axRb = self.axR.twinx(); self.axRb.tick_params(colors="#88ff88")
        (self.lB,) = self.axRb.plot([], [], color="#88ff88", lw=1.2, label="Körpermodell FK surprise (mm)")
        self.axRb.set_ylabel("body FK error (mm)", color="#88ff88")
        self.axR.legend(loc="upper left", facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=7)
        self.axRb.legend(loc="upper right", facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=7)
        self.readout = self.fig.text(0.012, 0.012, "", color="w", fontsize=7.5, family="monospace", va="bottom")
        self.fig.tight_layout(rect=(0, 0.085, 1, 0.95))

    def push(self, sensor, state, total, relax, body_mm=None):
        self._k += 1
        self.t.append(self._k); self.sensor.append(float(sensor)); self.state.append(float(state))
        self.total.append(float(total)); self.relax.append(float(relax))
        self.body.append(float(body_mm) if body_mm is not None else np.nan)
        if self._k % self._redraw_every == 0:
            self.redraw()

    def _readout_text(self):
        if not self.t:
            return ""
        b = self.body[-1]
        return ("current values per PC module\n"
                f"  VisualCortex  surprise(sensor)={self.sensor[-1]:7.3f}  state={self.state[-1]:7.3f}"
                f"  total={self.total[-1]:7.3f}  relax={self.relax[-1]:4.0f}\n"
                f"  Körpermodell  FK surprise={b:6.1f} mm" + ("" if np.isfinite(b) else " (n/a)") + "\n"
                "  Planner       — not instantiated in the act14–19 loop (1D-line module, not yet ported)")

    def redraw(self):
        w = self._win; t = self.t[-w:]
        self.lS.set_data(t, self.sensor[-w:]); self.lT.set_data(t, self.state[-w:])
        self.lU.set_data(t, self.total[-w:]); self.lR.set_data(t, self.relax[-w:])
        self.lB.set_data(t, self.body[-w:])
        for ax in (self.axE, self.axR, self.axRb):
            ax.relim(); ax.autoscale_view()
        self.readout.set_text(self._readout_text())
        try:
            self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()
        except Exception:
            pass

    def save(self, path):
        self.redraw(); self.fig.savefig(path, dpi=110, facecolor=self.fig.get_facecolor())

    def hold(self):
        self.plt.ioff(); self.plt.show()


# --------------------------------------------------------------------------- #
class HexFovea:
    """Learned hex PC-net on the camera fovea + an error-driven, object-following gaze."""
    def __init__(self, K=8, rng=None):
        self.K = K
        self.net, self.cells, self.h1 = build_hexnet4(rng or np.random.default_rng(0))
        self.se = []
        self.last_diag = None                                # most recent PC-step diagnostics
        self.hist = {"sensor": [], "state": [], "total": [], "relax": []}   # surprise time-series

    def step(self, img, gaze, cmd_rgb, learn=True):
        arr = hex_sample(img, gaze, self.K, cmd_rgb)
        set_sheet4(self.cells, arr)
        r = self.net.step(learn=learn); self.net.commit_step()
        self.last_diag = r                                   # expose surprise + relax for live plots
        if np.isfinite(r["sensor_error"]):
            self.se.append(r["sensor_error"])
            self.hist["sensor"].append(r["sensor_error"]); self.hist["state"].append(r["state_error"])
            self.hist["total"].append(r["total_error"]); self.hist["relax"].append(r["relax_steps"])
        return arr

    def warmup(self, render_fn, scenes, scatter_fn, rng, viz=None):
        """Pre-train the net so its reconstruction (and thus fovea_gradient) is meaningful."""
        cols = list(CMD_COLOR.values())
        for i in range(scenes):
            if i % 3 == 0:
                scatter_fn()
            img = render_fn(); rgb = cols[i % len(cols)]
            gaze = rng.uniform([F * self.K, F * self.K], [img.shape[1] - F * self.K, img.shape[0] - F * self.K])
            arr = self.step(img, gaze, rgb)
            if i % 20 == 0:
                se = np.mean(self.se[-30:]) if self.se else float("nan")
                sys.stdout.write(f"\r\x1b[2K  [warmup hex-net] {i}/{scenes} ({100*i//scenes}%)  "
                                 f"sensor_err {se:.2f}"); sys.stdout.flush()
                if viz is not None:
                    viz.fovea(img, gaze, self.K, np.clip(arr[:, :, 1:], 0, 1), f"warmup {i}/{scenes}")
        sys.stdout.write("\r\x1b[2K"); sys.stdout.flush()

    def track_step(self, img, gaze, cmd_rgb, learn=True, min_sel=1.5):
        """One frame: perceive, and (if the object is CONFIDENTLY in view) drive the gaze to
        FOLLOW it.  Returns (new_gaze, found, cells_rgb).  found=False when the object is gone
        OR only weakly visible (the gripper is occluding it) -> the caller keeps the last
        estimate (memory) -- the act11 gaze-on-object + memory pattern, so a partial occlusion
        never biases the estimate."""
        arr = self.step(img, gaze, cmd_rgb, learn)
        sel = arr[:, :, 0]; com = com2d(sel); center = (F - 1) / 2.0
        if com is None or sel.sum() < min_sel:              # occluded / too weak -> memory
            # still nudge the gaze toward the last seen blob if any (keeps it on the object)
            if com is not None:
                gaze = gaze + (com - center) * self.K * 0.5
            return gaze, False, arr
        drive = -fovea_gradient(self.cells)                 # net active-inference drive
        gaze = gaze + (com - center) * self.K + np.clip(drive * 6.0, -2, 2)
        return gaze, True, arr

    def locate(self, render_fn, cmd_rgb, gaze, grid, learn=True, viz=None, label=""):
        """SEARCH (saccade over `grid`) then FOLLOW (error-driven) the commanded-colour object;
        returns the foveated gaze (px) or None."""
        import time
        center = (F - 1) / 2.0; fov_v = np.zeros(2); seen = 0; saccade = 0; com = None
        for it in range(50):
            img = render_fn()                               # render ONCE per iteration, reuse below
            arr = self.step(img, gaze, cmd_rgb, learn)
            com = com2d(arr[:, :, 0])                       # conditioned (commanded) object in cells
            if com is not None:
                drive = -fovea_gradient(self.cells)         # active-inference fovea (net-driven)
                fov_v = 0.4 * fov_v + 0.6 * np.clip(drive * 6.0, -2, 2)
                # error-driven follow: also pull the gaze so the object sits at the fovea centre
                gaze = gaze + (com - center) * self.K + fov_v
                seen = seen + 1 if np.linalg.norm(com - center) < 1.2 else 0
                if seen >= 3:
                    break
            else:                                           # not in view -> saccadic search
                gaze = grid[saccade % len(grid)].copy(); saccade += 1
            gaze = np.clip(gaze, F * self.K, np.array([img.shape[1], img.shape[0]]) - F * self.K)
            if viz is not None:
                viz.fovea(img, gaze, self.K, np.clip(arr[:, :, 1:], 0, 1), f"search/follow {label}")
                time.sleep(0.02)
        return gaze if (seen >= 1 or com is not None) else None


# --------------------------------------------------------------------------- #
def setup_following_fovea(sim, CAM="overview", RES=240, headless=False, verbose=True):
    """Factored-out act18 perception: a LEARNED hex-fovea PC-net that perceives the camera + an
    error-driven FOLLOWING gaze, warmed up and calibrated (world<->px).  Returns a dict with
    `perceive`/`track`/`viz` ready for act16.run_combined, plus `fovea`/`render_perc`/`grid`/
    `px_to_world` for perception-only use.  This lets other acts (e.g. act19) reuse the FOLLOWING
    fovea AND its live hex display instead of privileged sim-state perception."""
    from pc.pc_act15 import detect_px
    fovea = HexFovea(K=8, rng=np.random.default_rng(7))
    perc_opt = mujoco.MjvOption(); perc_opt.geomgroup[1] = 0       # hide the arm -> clean object colour

    def render_perc():
        sim._renderer.update_scene(sim.d, camera=CAM, scene_option=perc_opt); return sim._renderer.render()

    # affine world<->px calibration (red cube at known spots, others parked aside)
    crng = np.random.default_rng(3); W, P = [], []
    sim.reset_home()
    for o in CMD_COLOR:
        if o != "obj_red":
            sim.set_object(o, [0.33, 0.33])
    for _ in range(16):
        p = _rand_xy(crng); sim.set_object("obj_red", p); mujoco.mj_forward(sim.m, sim.d)
        px = detect_px(render_perc(), CMD_COLOR["obj_red"])
        if px is not None:
            W.append([p[0], p[1], 1.0]); P.append(px)
    W, P = np.array(W), np.array(P)
    Hx = np.linalg.lstsq(W, P[:, 0], rcond=None)[0]; Hy = np.linalg.lstsq(W, P[:, 1], rcond=None)[0]
    A = np.array([Hx[:2], Hy[:2]]); b = np.array([Hx[2], Hy[2]]); Ainv = np.linalg.inv(A)
    px_to_world = lambda px: Ainv @ (np.asarray(px, float) - b)
    corners = np.array([[REACH_XY[i][0], REACH_XY[j][1]] for i in (0, 1) for j in (0, 1)])
    cpx = np.array([A @ c + b for c in corners])
    pmin = np.maximum(cpx.min(0) - 10, F * 8).astype(float); pmax = np.minimum(cpx.max(0) + 10, RES - F * 8).astype(float)
    grid = [np.array([x, y]) for y in np.linspace(pmin[1], pmax[1], 3) for x in np.linspace(pmin[0], pmax[0], 3)]

    def scatter_far():
        for o in CMD_COLOR:
            sim.set_object(o, _rand_xy(crng))
        mujoco.mj_forward(sim.m, sim.d)

    viz = None
    if not headless:
        try:
            viz = HexFoveaViz(CAM, RES)
        except Exception as e:
            print(f"  [viz] {e}")

    if verbose:
        print("  warming up the hex perception net on the camera ...")
    fovea.warmup(render_perc, 500, scatter_far, np.random.default_rng(9), viz=viz)
    if verbose:
        q = max(1, len(fovea.se) // 8)
        print(f"  net sensor_error (camera scene): {np.mean(fovea.se[:q]):.3f} -> {np.mean(fovea.se[-q:]):.3f}")

    state = {"gaze": np.array([RES / 2.0, RES / 2.0]), "rgb": CMD_COLOR["obj_red"]}

    def crop_rgb(arr):
        return np.clip(arr[:, :, 1:], 0, 1)

    def perceive(cmd):
        g = fovea.locate(render_perc, CMD_COLOR[cmd], np.array([RES / 2.0, RES / 2.0]), grid, viz=viz, label=cmd[4])
        state["gaze"] = g if g is not None else np.array([RES / 2.0, RES / 2.0])
        state["rgb"] = CMD_COLOR[cmd]
        cube = px_to_world(g) if g is not None else sim.obj_pos(cmd)[:2]
        return cube, None, "grasp"                            # target stays given (thin marker)

    def track():
        img = sim.render(CAM)                                 # REAL view: the arm genuinely occludes
        gaze, found, arr = fovea.track_step(img, state["gaze"], state["rgb"], learn=True)
        gaze = np.clip(gaze, F * fovea.K, RES - F * fovea.K); state["gaze"] = gaze
        if viz is not None:
            viz.fovea(img, gaze, fovea.K, crop_rgb(arr),
                      "fovea follows (real view; gripper occludes -> memory)")
        return px_to_world(gaze) if found else None           # None when occluded -> grasp uses memory

    return {"fovea": fovea, "perceive": perceive, "track": track, "viz": viz,
            "render_perc": render_perc, "grid": grid, "px_to_world": px_to_world}


# --------------------------------------------------------------------------- #
def main():
    HEADLESS = os.environ.get("ACT18_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT18_CAM", "overview").lower()
    CMD = os.environ.get("ACT18_CMD", "") or None
    RES = int(os.environ.get("ACT18_RES", "240"))
    EPISODES = int(os.environ.get("ACT18_EPISODES", "12"))
    PERCEPT = os.environ.get("ACT18_PERCEPT", "0") == "1"
    LIFELONG = os.environ.get("ACT18_LIFELONG", "1") == "1"     # Phase 2: refine kinematics online
    PERTURB = float(os.environ.get("ACT18_PERTURB", "0.0"))     # lengthen the forearm (m) post-babble
    TRACK = os.environ.get("ACT18_TRACK", "1") == "1"           # 0 = skip the (slow) fovea tracking
    rng = np.random.default_rng(0)

    print(f"act18 — learned hex-net camera fovea + error-driven following gaze  cam={CAM}")
    sim = BracketArmSim(render_wh=(RES, RES))
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5)); body.babble(sim, 4000)

    if PERTURB:                                                 # change the REAL arm AFTER babbling ->
        wid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "wrist_link")   # learned FK now STALE
        sim.m.body_pos[wid, 2] += PERTURB; mujoco.mj_forward(sim.m, sim.d)

    def fk_err(n=200):
        rng3 = sim.arm3_range(); g = np.random.default_rng(11); e = []
        for _ in range(n):
            q = g.uniform(rng3[:, 0], rng3[:, 1]); e.append(np.linalg.norm(body.fk(q) - sim.fk_truth(q)))
        sim.reset_home(); return float(np.mean(e))

    P = setup_following_fovea(sim, CAM, RES, headless=HEADLESS)
    fovea = P["fovea"]; perceive = P["perceive"]; track = P["track"]; viz = P["viz"]
    render_perc = P["render_perc"]; grid = P["grid"]; px_to_world = P["px_to_world"]

    if PERCEPT:                                              # perception-only accuracy test
        prng = np.random.default_rng(3); errs = 0.0; n = 0
        for ep in range(EPISODES):
            cmd = CMD or list(CMD_COLOR)[ep % 3]
            for o in CMD_COLOR:
                sim.set_object(o, _rand_xy(prng))
            mujoco.mj_forward(sim.m, sim.d)
            g = fovea.locate(render_perc, CMD_COLOR[cmd], np.array([RES / 2.0, RES / 2.0]), grid)
            if g is not None:
                w = px_to_world(g); e = np.linalg.norm(w - sim.obj_pos(cmd)[:2])
                errs += e; n += 1
                print(f"  ep {ep:2d} {cmd[4]}: follow-fovea loc err {e*1000:.0f} mm")
        print(f"  == following-fovea localisation: {errs/max(1,n)*1000:.1f} mm  (found {n}/{EPISODES}) ==")
        return

    # the following fovea (perceive up front + track during the action) feeds the grasp; its live
    # hex display is driven by perceive()/track() from setup_following_fovea
    if PERTURB:
        print(f"  learned-kinematics FK error after perturb (+{PERTURB*1000:.0f}mm forearm): "
              f"{fk_err()*1000:.1f} mm  ({'lifelong will adapt' if LIFELONG else 'frozen'})")
    # viz is driven by track() (live arm view + following fovea); don't let run_combined overwrite it
    act16.run_combined(sim, body, None if viz is not None else viz, CAM, episodes=EPISODES,
                       cmd_fixed=CMD, perceive_fn=perceive, track_fn=(track if TRACK else None),
                       lifelong=LIFELONG)
    if PERTURB:
        print(f"  learned-kinematics FK error after episodes ({'LIFELONG on' if LIFELONG else 'frozen'}):"
              f" {fk_err()*1000:.1f} mm")


if __name__ == "__main__":
    main()
