r"""
pc_act13.py — act12 (coupled 2-link arm) + a GRAPHICAL arm visualisation (matplotlib).

Same agent and mechanics as act12; this stage adds a live top-down GRAPHICAL view that
draws the two arm segments (base → elbow → hand), the coloured objects, the target and the
fovea window, so the coupled mechanism is actually visible.  The ANSI terminal render and the
headless metrics mode are kept (handy for test runs).

  ACT13_VIZ=mpl   (default)   live matplotlib window with the arm drawn
  ACT13_VIZ=ansi              the old coloured-blob terminal render
  ACT13_HEADLESS=1            metrics only, no view (for batch test runs)

---- inherited from act12 ----
act11 drove the hand like a plotter: two independent motors set the hand's x and y
directly.  act12 replaces that with a more robot-like, COUPLED mechanism:

  * an upper arm of fixed length L1 on a rotating base (shoulder motor -> angle θ1),
  * a forearm of fixed length L2 hinged at the elbow (elbow motor -> angle θ2).

The hand (end-effector) position is the FORWARD KINEMATICS of the two joint angles.
The two motors can still reach every point of the field, but the control is coupled and
non-linear, and a given hand position has several joint solutions (elbow up/down).

How the agent copes (faithful to the learned/coordinate-free line):
  * FK is exactly LINEAR in the features ψ(θ)=[cosθ1,sinθ1,cos(θ1+θ2),sin(θ1+θ2)], so a
    LEARNED linear map  hand = b + W·ψ(θ)  recovers the kinematics by babbling (it
    discovers L1, L2, the base) — this is the body model, now in joint space.
  * Its analytic Jacobian J(θ)=W·dψ/dθ converts the existing CARTESIAN control (approach /
    carry / push) into joint velocities  dθ = J⁺·v  (damped pseudo-inverse), and corrects
    the felt joint angles from vision (precision-weighted, as in act11).

Everything above the hand (colour selection, target search, carry, push, surprise) is
UNCHANGED from act11 — only the hand actuation became joint-based.  No arm rendering yet.

Run:  python pc_act12.py                  (live colour top-down render)
      ACT12_HEADLESS=1 python ...          (metrics only)
      ACT12_MANIP=push python ...          (push the commanded object)
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule
from pc.test_pc_act10 import (G, F, CONTACT_R, GOAL_K, VMAX, APPROACH, TOL,
                              blob2d, com2d, hex_neighbors, window, gather,
                              Readout, Coupling, GoalPrior)

# distinct, well-separated hues; objects pick distinct ones so colour identifies them
PALETTE = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1],
                    [1, 1, 0], [1, 0, 1], [0, 1, 1]], float)
NAMES = ["R", "G", "B", "Y", "M", "C"]
N_OBJ = int(os.environ.get("ACT12_NOBJ", "3"))
MATCH_TH = 0.9                  # colour-cosine threshold for "this is the commanded colour"

# ---- 2-link arm geometry: base mounted just OUTSIDE a corner, reaching across the field
ARM_BASE = np.array([-4.0, -4.0])
L1, L2 = 21.0, 17.0             # upper arm + forearm; reach L1+L2=38 covers the 24x24 field
TH1_LO, TH1_HI = -1.0, 2.5      # generous joint limits (rad)
TH2_LO, TH2_HI = -2.9, 2.9
MAXDQ = 0.18                    # max joint speed per step (rad)
DAMP = 0.08                     # damped-least-squares regulariser for the (pseudo-)inverse
DQ_NOISE = 0.008               # motor noise per joint per step (rad)


def fk(theta, base=ARM_BASE):
    """Forward kinematics: joint angles -> hand (end-effector) position."""
    t1, t2 = float(theta[0]), float(theta[1])
    elbow = base + L1 * np.array([np.cos(t1), np.sin(t1)])
    return elbow + L2 * np.array([np.cos(t1 + t2), np.sin(t1 + t2)])


def ik(target, base=ARM_BASE, elbow_down=True):
    """Analytic inverse kinematics (one of the two solutions) — used to PLACE the arm at
    episode start; the running control never calls this (it is differential/learned)."""
    d = np.asarray(target, float) - base
    r = float(np.linalg.norm(d))
    r = float(np.clip(r, abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3))
    c2 = (r * r - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    t2 = float(np.arccos(np.clip(c2, -1, 1)))
    if not elbow_down:
        t2 = -t2
    t1 = float(np.arctan2(d[1], d[0]) - np.arctan2(L2 * np.sin(t2), L1 + L2 * np.cos(t2)))
    return np.array([np.clip(t1, TH1_LO, TH1_HI), np.clip(t2, TH2_LO, TH2_HI)])


def arm_psi(theta):
    """Kinematic feature map ψ(θ) in which FK is exactly linear."""
    t1, t12 = float(theta[0]), float(theta[0] + theta[1])
    return np.array([np.cos(t1), np.sin(t1), np.cos(t12), np.sin(t12)])


def arm_dpsi(theta):
    """dψ/dθ  (4x2): columns are ∂ψ/∂θ1 and ∂ψ/∂θ2."""
    t1, t12 = float(theta[0]), float(theta[0] + theta[1])
    s1, c1 = np.sin(t1), np.cos(t1)
    s12, c12 = np.sin(t12), np.cos(t12)
    return np.array([[-s1, 0.0],
                     [c1, 0.0],
                     [-s12, -s12],
                     [c12, c12]])


def color_match(rgb, cmd):
    a = rgb / (np.linalg.norm(rgb) + 1e-6)
    b = cmd / (np.linalg.norm(cmd) + 1e-6)
    return float(a @ b)


def selected_lum(rgb_win, cmd):
    """Colour-cued attention: per-cell luminance kept only where the colour matches the
    command — this is where the COMMANDED object is (distractors are suppressed)."""
    out = np.zeros((F, F))
    for r in range(F):
        for c in range(F):
            v = rgb_win[r, c]
            lum = float(v.sum())
            if lum > 0.2 and color_match(v, cmd) > MATCH_TH:
                out[r, c] = lum
    return out


# --------------------------------------------------------------------------- #
class WorldColor:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.lo, self.hi = G / 8.0, G * 7.0 / 8.0
        self.n = N_OBJ
        self.scatter(with_target=True)
        self.theta = ik(self.commanded_pos())             # the physical 2-link arm's joints

    # ---- the physical arm: joints -> hand, motors move the joints ----
    def hand(self):
        return np.clip(fk(self.theta), 0, G - 1)

    def move_joints(self, dtheta):
        self.theta = np.array([np.clip(self.theta[0] + dtheta[0], TH1_LO, TH1_HI),
                               np.clip(self.theta[1] + dtheta[1], TH2_LO, TH2_HI)])

    def place_hand(self, target, elbow_down=True):
        """Set the arm pose (via analytic IK) so the hand sits at `target` — used only to
        initialise the arm at episode start (a real robot would command a start pose)."""
        self.theta = ik(target, elbow_down=elbow_down)

    def _rand(self):
        return self.rng.uniform(self.lo, self.hi, 2)

    def scatter(self, with_target=False):
        self.pos, self.sig, self.shape = [], [], []
        for _ in range(self.n):
            p = self._rand()
            while any(np.linalg.norm(p - q) < 5.0 for q in self.pos):
                p = self._rand()
            self.pos.append(p)
            self.sig.append(float(self.rng.uniform(0.3, 1.1)))
            self.shape.append(str(self.rng.choice(["gaussian", "flat"])))
        self.colors = list(self.rng.choice(len(PALETTE), self.n, replace=False))  # distinct
        self.cmd = int(self.rng.integers(self.n))         # which object to transport
        if with_target:
            self.target = self._rand()

    def cmd_color(self):
        return PALETTE[self.colors[self.cmd]]

    def commanded_pos(self):
        return self.pos[self.cmd]

    def color_image(self):
        img = np.zeros((G, G, 3))
        for k in range(self.n):
            b = blob2d(self.pos[k], G, self.sig[k], self.shape[k])
            img += b[..., None] * PALETTE[self.colors[k]]
        return np.clip(img, 0, 1)

    def tgt_lum(self):
        return blob2d(self.target, G, 1.0)

    def ptr_lum(self, ptr):
        return blob2d(ptr, G, 0.6)

    def carry_commanded(self, vel):
        self.pos[self.cmd] = np.clip(self.pos[self.cmd] + vel, 0, G - 1)

    def shove_commanded(self, p_new, a, finger):
        """Genuine 2-D PUSH of the COMMANDED object (no carry): the hand can only push it
        AWAY in the motion direction; to move it you must get on its far side."""
        o = self.pos[self.cmd]; amag = np.linalg.norm(a)
        if finger > 0.5 and amag > 1e-6 and np.linalg.norm(p_new - o) < CONTACT_R:
            if np.dot(a, o - (p_new - a)) > 0:
                self.pos[self.cmd] = np.clip(p_new + (a / amag) * CONTACT_R * 0.9, 0, G - 1)
                return True
        return False


# --------------------------------------------------------------------------- #
# Body model in JOINT space: a LEARNED linear generative map  hand = b + W·ψ(θ).
# Babbling the arm recovers W,b (i.e. L1,L2,base).  Its analytic Jacobian converts
# Cartesian control to joint velocities and corrects the felt joints from vision.
# --------------------------------------------------------------------------- #
class ArmBodyModel:
    def __init__(self, lr=0.02, rng=None):
        self.rng = rng or np.random.default_rng()
        self.W = self.rng.normal(0, 0.1, (2, 4))          # hand = b + W·ψ(θ)
        self.b = np.zeros(2)
        self.lr = lr
        self.theta = np.zeros(2)                          # FELT joint angles
        self.last_surprise = None                         # EMA |seen hand - predicted hand|

    # ----- learning the kinematics -----
    def babble(self, steps):
        for _ in range(steps):
            th = np.array([self.rng.uniform(TH1_LO, TH1_HI),
                           self.rng.uniform(TH2_LO, TH2_HI)])
            self._fit(th, fk(th))

    def observe(self, theta, hand_obs, lr=0.004):         # lifelong refinement from real moves
        self._fit(theta, hand_obs, lr)

    def _fit(self, theta, hand_obs, lr=None):
        lr = self.lr if lr is None else lr
        psi = arm_psi(theta)
        err = (self.b + self.W @ psi) - np.asarray(hand_obs, float)
        self.W -= lr * np.outer(err, psi); self.b -= lr * err

    # ----- kinematics / Jacobian on the FELT joints -----
    def felt_hand(self):
        return self.b + self.W @ arm_psi(self.theta)

    def jacobian(self):
        return self.W @ arm_dpsi(self.theta)              # 2x2  ∂hand/∂θ

    def _dls(self, J, v):
        """Damped least-squares (pseudo-)inverse step:  dθ = Jᵀ(JJᵀ+λI)⁻¹ v."""
        JJt = J @ J.T + DAMP * np.eye(2)
        return J.T @ np.linalg.solve(JJt, np.asarray(v, float))

    def ik_velocity(self, v_cart):
        """Cartesian desired velocity -> joint velocity, clamped to the max joint speed."""
        dth = self._dls(self.jacobian(), v_cart)
        m = float(np.max(np.abs(dth)))
        if m > MAXDQ:
            dth *= MAXDQ / m
        return dth

    # ----- proprioception -----
    def sync(self, theta_true):
        self.theta = np.array(theta_true, float)          # re-sync at episode start

    def efference(self, dtheta):
        self.theta = np.array([np.clip(self.theta[0] + dtheta[0], TH1_LO, TH1_HI),
                               np.clip(self.theta[1] + dtheta[1], TH2_LO, TH2_HI)])

    def correct(self, hand_obs, eta):
        """Vision correction: nudge the felt joints so the predicted hand matches what is
        seen (Gauss-Newton through the learned Jacobian).  eta is precision-weighted."""
        if hand_obs is None or eta <= 0:
            return
        e = np.asarray(hand_obs, float) - self.felt_hand()
        s = float(np.sqrt(np.mean(e ** 2)))               # SURPRISE: predicted vs seen hand
        self.last_surprise = s if self.last_surprise is None else 0.9 * self.last_surprise + 0.1 * s
        dth = eta * self._dls(self.jacobian(), e)
        self.theta = np.array([np.clip(self.theta[0] + dth[0], TH1_LO, TH1_HI),
                               np.clip(self.theta[1] + dth[1], TH2_LO, TH2_HI)])


# --------------------------------------------------------------------------- #
def build_hexnet(rng):
    net = PCNetwork(eta_inf=0.05, n_relax=20, eps_tol=1e-5, eta_learn=0.006,
                    gamma=0.3, w_clip=3.0, rng=rng)
    cells = {}
    for r in range(F):
        for c in range(F):
            cells[(r, c)] = net.add(SensorNode(f"s_{r}_{c}", dim=5))   # [R,G,B,ptr,tgt]
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
    vc = PCModule("VisualCortex")
    vc.add_in_port("cells", [f"s_{r}_{c}" for r in range(F) for c in range(F)])
    vc.add_out_port("abstract", ["top"]); net.add_module(vc)
    return net, cells, h1


def set_sheet(cells, rgb_w, ptr_w, tgt_w):
    for r in range(F):
        for c in range(F):
            v = rgb_w[r, c]
            cells[(r, c)].set_input(np.array([v[0], v[1], v[2], ptr_w[r, c], tgt_w[r, c]]))


# --------------------------------------------------------------------------- #
ANSI = {0: "\x1b[91m", 1: "\x1b[92m", 2: "\x1b[94m",       # R G B
        3: "\x1b[93m", 4: "\x1b[95m", 5: "\x1b[96m"}        # Y M C
RESET = "\x1b[0m"


def render(step, total, world, phi, ptr, finger, info):
    ox, oy = int(round(phi[0])), int(round(phi[1]))
    img = world.color_image()
    glyph = [["·"] * G for _ in range(G)]
    for y in range(G):                                 # objects: COLOURED gaussian/flat blobs
        for x in range(G):
            v = img[y, x]; lum = float(v.max())
            ch = "█" if lum >= 0.85 else "▓" if lum >= 0.45 else "░" if lum >= 0.15 else None
            if ch is not None:
                k = int(np.argmax([color_match(v, PALETTE[j]) for j in range(len(PALETTE))]))
                glyph[y][x] = ANSI[k] + ch + RESET
    cx, cy = np.round(world.commanded_pos()).astype(int)   # mark the commanded object's centre
    if 0 <= cx < G and 0 <= cy < G:
        glyph[cy][cx] = ANSI[world.colors[world.cmd]] + NAMES[world.colors[world.cmd]] + RESET
    tx, ty = np.round(world.target).astype(int)
    if 0 <= tx < G and 0 <= ty < G and glyph[ty][tx] == "·":
        glyph[ty][tx] = "+"
    px, py = np.round(ptr).astype(int)
    if 0 <= px < G and 0 <= py < G:
        glyph[py][px] = "P" if finger else "p"
    c0, c1 = max(ox, 0), min(ox + F - 1, G - 1)
    cmd = NAMES[world.colors[world.cmd]]
    mode = info.get("mode", "")
    sp = info.get("surprise", {})
    def _s(v):
        return f"{v:.3f}" if v is not None else "  -  "
    sur = (f"  SURPRISE (pred vs actual):  vis-sens {_s(sp.get('vis_sens'))}  "
           f"vis-LATENT {_s(sp.get('vis_lat'))}  |  arm {_s(sp.get('body'))}  |  "
           f"{sp.get('dyn_name','dyn')} {_s(sp.get('dyn'))}")
    lines = [f"Step {step}/{total}  COMMAND=move '{cmd}'  tgt=({tx},{ty})  {mode}",
             f"  coloured blobs=objects (letter=commanded centre)  +=target  P/p=hand  [..]=fovea",
             sur]
    for r in range(G):
        win = oy <= r <= oy + F - 1 and c0 <= c1
        gaps = [" "] * (G + 1)
        if win:
            gaps[c0] = "["; gaps[c1 + 1] = "]"
        row = "".join(gaps[c] + glyph[r][c] for c in range(G)) + gaps[G]
        lines.append("  " + (" " if r % 2 == 1 else "") + row)
    sys.stdout.write("\x1b[H\x1b[2J"); print("\n".join(lines), flush=True)


# --------------------------------------------------------------------------- #
# Graphical top-down view that DRAWS the 2-link arm (matplotlib).
# --------------------------------------------------------------------------- #
class MplArmViz:
    def __init__(self):
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Circle
        self.plt = plt
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(6.4, 6.4))
        self.ax.set_xlim(ARM_BASE[0] - 2, G + 1)
        self.ax.set_ylim(G + 1, ARM_BASE[1] - 2)        # y down, to match the top-down terminal view
        self.ax.set_aspect("equal"); self.ax.set_facecolor("#0e0e12")
        self.ax.tick_params(colors="#666"); self.fig.patch.set_facecolor("#0e0e12")
        self.obj_patches = [Circle((0, 0), 1.0, color="w", alpha=0.92) for _ in range(N_OBJ)]
        for c in self.obj_patches:
            self.ax.add_patch(c)
        self.cmd_ring = Circle((0, 0), 1.0, fill=False, ec="white", lw=2.0)
        self.ax.add_patch(self.cmd_ring)
        (self.tgt,) = self.ax.plot([], [], marker="+", ms=15, mew=2.5, color="white", ls="")
        (self.arm,) = self.ax.plot([], [], "-", color="#9aa0aa", lw=4, solid_capstyle="round", zorder=4)
        (self.joints,) = self.ax.plot([], [], "o", color="#cfd3da", ms=8, zorder=5)
        (self.hand,) = self.ax.plot([], [], "o", ms=12, mfc="red", mec="white", mew=1.5, zorder=6)
        self.ax.plot([ARM_BASE[0]], [ARM_BASE[1]], "s", color="#555", ms=13, zorder=3)  # base mount
        self.fovea = Rectangle((0, 0), F, F, fill=False, ec="#33ccff", lw=1.5, ls="--")
        self.ax.add_patch(self.fovea)
        self.txt = self.ax.text(0.02, 0.985, "", transform=self.ax.transAxes, va="top",
                                color="white", fontsize=9, family="monospace")

    def update(self, step, total, world, phi, finger, mode):
        for k, c in enumerate(self.obj_patches):
            c.center = (float(world.pos[k][0]), float(world.pos[k][1]))
            c.set_radius(max(0.8, 1.8 * world.sig[k])); c.set_color(tuple(PALETTE[world.colors[k]]))
        cm = world.commanded_pos()
        self.cmd_ring.center = (float(cm[0]), float(cm[1]))
        self.cmd_ring.set_radius(max(0.8, 1.8 * world.sig[world.cmd]) + 0.7)
        self.tgt.set_data([world.target[0]], [world.target[1]])
        t1 = float(world.theta[0])
        elbow = ARM_BASE + L1 * np.array([np.cos(t1), np.sin(t1)])
        hand = world.hand()
        self.arm.set_data([ARM_BASE[0], elbow[0], hand[0]], [ARM_BASE[1], elbow[1], hand[1]])
        self.joints.set_data([elbow[0]], [elbow[1]])
        self.hand.set_data([hand[0]], [hand[1]]); self.hand.set_mfc("red" if finger else "none")
        self.fovea.set_xy((phi[0] - 0.5, phi[1] - 0.5))
        self.txt.set_text(f"step {step}/{total}   cmd '{NAMES[world.colors[world.cmd]]}'   {mode}")
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def hold(self):
        self.plt.ioff(); self.plt.show()


# --------------------------------------------------------------------------- #
def main():
    HEADLESS = os.environ.get("ACT13_HEADLESS", "0") == "1"
    SCALE = float(os.environ.get("ACT13_SCALE", "1.0"))
    DELAY = float(os.environ.get("ACT13_DELAY", "0.0"))
    GOAL = os.environ.get("ACT13_GOAL", "obj").lower()       # obj | none | scramble
    MANIP = os.environ.get("ACT13_MANIP", "carry").lower()   # carry | push
    LIFELONG = os.environ.get("ACT13_LIFELONG", "1") == "1"
    VIZ = os.environ.get("ACT13_VIZ", "mpl").lower()         # mpl | ansi  (ignored if HEADLESS)
    MPC_HORIZON = 3; MAG_PUSH = 1.6; STALL_K = 25
    GAIN = 3.0; SMOOTH = 0.3
    rng = np.random.default_rng(0)

    def prog(msg):
        sys.stdout.write("\r\x1b[2K  [setup] " + msg); sys.stdout.flush()

    print(f"act13 — 2-LINK ARM + graphical view  (N={N_OBJ}, viz={VIZ if not HEADLESS else 'headless'})")
    viz = None
    if not HEADLESS and VIZ == "mpl":
        try:
            viz = MplArmViz()
        except Exception as e:                               # no display / no matplotlib
            print(f"  [viz] matplotlib unavailable ({e}); falling back to ANSI"); VIZ = "ansi"
    net, cells, h1 = build_hexnet(rng)
    ro_ptr = Readout(len(h1) * 12, rng=np.random.default_rng(4))
    prog("arm kinematics babble ..."); arm = ArmBodyModel(rng=np.random.default_rng(5)); arm.babble(6000)
    coupling = Coupling(rng=np.random.default_rng(6))
    goalprior = GoalPrior(rng=np.random.default_rng(7))   # LEARNED signed object→goal error
    world = WorldColor(seed=1)
    prog("contact-coupling babble ...")
    # coupling babble needs a push world; reuse a tiny monochrome proxy via act10 World2D
    from pc.test_pc_act10 import World2D
    coupling.babble(World2D(seed=2), int(8000 * SCALE))
    prog("object-goal prior babble ..."); goalprior.babble(int(9000 * SCALE))
    pushmodel = mpc_plan = None
    if MANIP == "push":
        prog("2-D push-dynamics model babble ...")
        from pc.test_pc_push_policy_2d import PushModel2D, plan as mpc_plan
        pushmodel = PushModel2D(rng=np.random.default_rng(8)); pushmodel.babble(int(40000 * SCALE))
    if GOAL == "scramble":
        coupling.scramble(); goalprior.scramble()
        if pushmodel is not None:
            pushmodel.scramble()
    sys.stdout.write("\r\x1b[2K"); sys.stdout.flush()

    DEV = int(3000 * SCALE); ACTIVE = int(6000 * SCALE); total = DEV + ACTIVE
    phi = np.array([G/2.0 - F/2.0, G/2.0 - F/2.0])
    arm.sync(world.theta); ptr = world.hand()
    fov_v = np.zeros(2)
    se_hist = []
    # SURPRISE = prediction error (predicted vs actual); per-dimension RMS so modules compare
    N_SENS = F * F * 5                          # clamped sensor dims (hex sheet)
    N_LAT = len(h1) * 12 + 10                   # hidden latent dims (h1 + top)
    sur_vis_sens = sur_vis_lat = None
    in_view = act = 0
    sel_err, sel_n = 0.0, 0
    ptr_in, ptr_in_n, ptr_out, ptr_out_n = 0.0, 0, 0.0, 0
    deliveries = episodes = ep_steps = 0; ep_best = 1e9; ep_stall = 0; EP_CAP = 200
    scan_gaze = [np.array([gx, gy], float) for gy in (0, 8, 16) for gx in (0, 8, 16)]
    searching = False; scan_idx = 0; tgt_felt = None; obj_mem = None

    print(f"  world={G} fovea={F}  goal={GOAL}  dev={DEV} active={ACTIVE}  match_th={MATCH_TH}")

    for step in range(total):
        dev = step < DEV
        if dev and step % 100 == 0:
            se = np.mean(se_hist[-50:]) if se_hist else float("nan")
            sys.stdout.write(f"\r\x1b[2K  [learning the colour world]  {step}/{DEV} "
                             f"({100*step//DEV}%)   sensor_err {se:.3f}"); sys.stdout.flush()
            if step + 100 >= DEV:
                sys.stdout.write("\r\x1b[2K  [done — active phase]\n"); sys.stdout.flush()

        rgb_w = window(world.color_image(), phi)
        ptr_w = window(world.ptr_lum(ptr), phi)
        tgt_w = window(world.tgt_lum(), phi)
        set_sheet(cells, rgb_w, ptr_w, tgt_w)
        r = net.step(learn=True); net.commit_step()
        if np.isfinite(r["sensor_error"]):
            se_hist.append(r["sensor_error"])
        # VisualCortex surprise: input-reconstruction + LATENT (h1/top) prediction error, EMA
        if np.isfinite(r["sensor_error"]) and np.isfinite(r["state_error"]):
            vs = float(np.sqrt(r["sensor_error"] / N_SENS))
            vl = float(np.sqrt(r["state_error"] / N_LAT))
            sur_vis_sens = vs if sur_vis_sens is None else 0.9 * sur_vis_sens + 0.1 * vs
            sur_vis_lat = vl if sur_vis_lat is None else 0.9 * sur_vis_lat + 0.1 * vl

        x = gather(net, h1)
        off = np.array([int(round(phi[0])), int(round(phi[1]))])
        cmd = world.cmd_color()
        # SELECTION by colour-cued attention (the conditioning at work)
        sel = selected_lum(rgb_w, cmd)
        sc = com2d(sel); obj_seen = sc is not None
        obj_perc = (off + sc) if obj_seen else None
        # pointer perception (body model visual correction), PRECISION-WEIGHTED: a hand
        # seen near the fovea centre is decoded reliably (full trust); a peripheral sighting
        # is uncertain, so it only weakly nudges the felt hand instead of corrupting it
        # (inverse-variance weighting — the PC way; "vision grabs precisely at the centre").
        pc = com2d(ptr_w); ptr_vis = None; ptr_conf = 0.0
        if pc is not None:
            ro_ptr.train(x, pc / (F - 1)); pp, _ = ro_ptr.predict(x)
            ptr_vis = off + np.clip(pp * (F - 1), 0, F - 1)
            ptr_conf = float(max(0.0, 1.0 - np.linalg.norm(pc - (F - 1) / 2.0) / (F / 2.0)))
        # target perception
        tc = com2d(tgt_w); tgt_seen = tc is not None
        tgt_perc = (off + tc) if tgt_seen else None

        if dev:
            world.scatter(with_target=True)
            focus = world.commanded_pos() if rng.random() < 0.5 else world.target
            phi = np.clip(focus - np.array([F/2.0, F/2.0]) + rng.normal(0, 2, 2), -F/2.0, G - F/2.0)
            world.place_hand(world._rand()); arm.sync(world.theta); ptr = world.hand()
            continue

        # ---------------- active ----------------
        did_reset = False
        if step == DEV or (obj_mem is not None and np.linalg.norm(world.commanded_pos() - world.target) < TOL) \
                or ep_steps >= EP_CAP:
            did_reset = True
            if step > DEV:
                episodes += 1
                if np.linalg.norm(world.commanded_pos() - world.target) < TOL:
                    deliveries += 1
            ep_steps = 0; ep_best = 1e9; ep_stall = 0
            world.scatter(with_target=True)
            while np.linalg.norm(world.commanded_pos() - world.target) < 8:
                world.target = world._rand()
            phi = np.clip(world.commanded_pos() - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
            searching = True; scan_idx = 0; tgt_felt = None; obj_mem = None
            if MANIP == "push":                          # start the hand OFF the object
                ang = rng.uniform(0, 2*np.pi)
                start = np.clip(world.commanded_pos() + (CONTACT_R + 1.5) *
                                np.array([np.cos(ang), np.sin(ang)]), 0, G - 1)
            else:
                start = world.commanded_pos().copy()
            world.place_hand(start); arm.sync(world.theta); ptr = world.hand()

        act += 1; ep_steps += 1
        a = np.zeros(2); finger = False; mode = ""
        center = (F - 1) / 2.0

        if searching:
            mode = "SEARCH obj+target"
            # foveate the commanded-colour object, then the target; remember both
            if obj_seen and not did_reset and np.linalg.norm(sc - center) < 1.5 and obj_mem is None:
                obj_mem = obj_perc.copy()
            elif obj_seen and not did_reset and obj_mem is None:
                phi = np.clip(off + sc - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
            elif tgt_seen and not did_reset and np.linalg.norm(tc - center) < 1.3 and tgt_felt is None:
                tgt_felt = tgt_perc.copy()
            elif tgt_seen and not did_reset and tgt_felt is None:
                phi = np.clip(off + tc - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
            else:
                phi = np.clip(scan_gaze[scan_idx % len(scan_gaze)].copy(), -F/2.0, G - F/2.0)
                scan_idx += 1
            if obj_mem is not None and tgt_felt is not None:
                searching = False
                phi = np.clip(obj_mem - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
                fov_v = np.zeros(2)
        else:
            mode = f"CARRY '{NAMES[world.colors[world.cmd]]}' → target"
            in_view += int(obj_seen)
            here = obj_perc if obj_perc is not None else obj_mem
            if obj_perc is not None:
                obj_mem = obj_perc.copy()
                sel_err += float(np.linalg.norm(obj_perc - world.commanded_pos())); sel_n += 1
            hand = arm.felt_hand()                          # FELT hand = learned FK of felt joints
            grabbed = here is not None and np.linalg.norm(hand - here) < CONTACT_R
            goal = tgt_felt if tgt_felt is not None else world.target
            dist_now = float(np.linalg.norm(world.commanded_pos() - goal))
            obj_before = world.commanded_pos().copy()
            # fovea: colour-cued servo onto the commanded object (or back to its memory).
            # Gaze STAYS on the object — the hand is led there BLIND (felt) and corrected
            # by vision only when it arrives near the centre (TRUST_R), "to grab precisely".
            if obj_perc is not None:
                fov_v = (1 - SMOOTH) * (GAIN * (obj_perc - off - center)) + SMOOTH * fov_v
                fov_v = np.clip(fov_v, -2.0, 2.0)
                phi = np.clip(phi + fov_v, -F/2.0, G - F/2.0)
            elif obj_mem is not None:
                phi = np.clip(obj_mem - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
                fov_v = np.zeros(2)
            if dist_now < ep_best - 0.5:
                ep_best = dist_now; ep_stall = 0
            else:
                ep_stall += 1
            if here is not None and GOAL != "none":
                if MANIP == "push":
                    name = NAMES[world.colors[world.cmd]]
                    reach = CONTACT_R + 2.0               # the push model's valid babble range
                    hd = float(np.linalg.norm(hand - here))
                    if hd > reach:                        # LEASH: hand drifted out of range —
                        mode = f"APPROACH '{name}'"        # walk straight to the object first
                        u = here - hand
                        a = (u / hd) * APPROACH; finger = False
                        ep_stall = 0                      # approaching is progress, don't stall-escape
                    elif ep_stall >= STALL_K:             # break a stuck oscillation
                        mode = f"PUSH '{name}' → target"
                        ang = rng.uniform(0, 2*np.pi)
                        a = MAG_PUSH * np.array([np.cos(ang), np.sin(ang)]); finger = False
                        ep_stall = 0
                    else:                                 # in range — MPC push-side policy
                        mode = f"PUSH '{name}' → target"
                        av, fv = mpc_plan(pushmodel, here, hand, goal, MPC_HORIZON)
                        a = np.asarray(av, float); finger = fv > 0.5
                elif grabbed:
                    finger = True
                    eps = goalprior.error(here, goal)     # LEARNED signed object→goal error
                    J, _ = coupling.predict(0.0)
                    a = np.clip(-GOAL_K * (G - 1) * J * eps, -VMAX, VMAX)
                else:
                    a = np.clip(GOAL_K * (here - hand), -APPROACH, APPROACH)
            # --- ARM ACTUATION: the Cartesian command `a` becomes JOINT velocities through
            # the learned Jacobian; the real arm moves its joints, the hand follows FK.  What
            # the hand ACTUALLY did (a_act) drives the object physics and the lifelong models.
            ptr_prev = ptr
            dtheta = arm.ik_velocity(a) + rng.normal(0, DQ_NOISE, 2)   # +motor noise (joint space)
            world.move_joints(dtheta); ptr = world.hand()
            a_act = ptr - ptr_prev
            if finger:
                world.shove_commanded(ptr, a_act, 1.0) if MANIP == "push" else world.carry_commanded(a_act)
            arm.efference(dtheta)                            # felt joints integrate the command ...
            arm.correct(ptr_vis, eta=0.5 * ptr_conf)         # ... vision corrects them (precision-weighted)
            if LIFELONG and GOAL != "scramble":
                dobj_obs = world.commanded_pos() - obj_before
                if MANIP == "push" and pushmodel is not None:
                    pushmodel.observe(hand - here, a_act, 1.0 if finger else 0.0, dobj_obs)
                elif MANIP == "carry" and finger:
                    coupling.observe(float(np.linalg.norm(hand - here)),
                                     float(np.linalg.norm(dobj_obs)), float(np.linalg.norm(a_act)))
                if ptr_vis is not None:
                    arm.observe(arm.theta, ptr_vis)          # refine the learned kinematics
            e = np.linalg.norm(arm.felt_hand() - world.hand())
            if ptr_vis is not None:
                ptr_in += e; ptr_in_n += 1
            else:
                ptr_out += e; ptr_out_n += 1
            phi = np.clip(phi + (world.commanded_pos() - obj_before), -F/2.0, G - F/2.0)

        if not HEADLESS:
            if viz is not None:
                viz.update(step, total, world, phi, finger, mode)
            else:
                dyn_s = pushmodel.last_surprise if MANIP == "push" else coupling.last_surprise
                render(step, total, world, phi, ptr, finger, {
                    "mode": mode,
                    "surprise": {"vis_sens": sur_vis_sens, "vis_lat": sur_vis_lat,
                                 "body": arm.last_surprise,
                                 "dyn": dyn_s,
                                 "dyn_name": "push-model" if MANIP == "push" else "coupling"}})
            if DELAY > 0:
                time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    print("=" * 70)
    print(f"  act13 summary (2-LINK ARM + graphical view)  goal={GOAL}  N={N_OBJ}")
    print(f"  sensor_error: {np.mean(se_hist[:q]):.3f} → {np.mean(se_hist[-q:]):.3f}")
    print(f"  SELECTION (attended obj vs COMMANDED obj): {sel_err/max(1,sel_n):.2f}px"
          f"   [colour command picks the right object among distractors]")
    print(f"  ARM felt-hand vs true: in {ptr_in/max(1,ptr_in_n):.2f}px | out {ptr_out/max(1,ptr_out_n):.2f}px"
          f"   [learned FK of felt joints]")
    rate = f"{100.0*deliveries/episodes:.0f}% ({deliveries}/{episodes})" if episodes else f"{deliveries}"
    mech = "genuine learned 2-D PUSH-side (MPC)" if MANIP == "push" else "learned-coupling carry"
    print(f"  COMMANDED object DELIVERED: {rate} (cap {EP_CAP})   [{mech}, joint-actuated]")
    dyn_s = pushmodel.last_surprise if MANIP == "push" else coupling.last_surprise
    dn = "push-model" if MANIP == "push" else "coupling"

    def _s(v):
        return f"{v:.3f}" if v is not None else "n/a"
    print(f"  SURPRISE (pred vs actual latent):  vis-sens {_s(sur_vis_sens)}  "
          f"vis-LATENT {_s(sur_vis_lat)} | arm {_s(arm.last_surprise)} | "
          f"{dn} {_s(dyn_s)}")
    print("=" * 70)
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


if __name__ == "__main__":
    main()
