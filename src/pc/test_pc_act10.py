r"""
test_pc_act10.py — 2D port of the act8b learned / error-driven / coordinate-free line.

act9 was a 2D world but with a SCRIPTED coordinate carry.  act10 ports the act8b
mechanisms that are genuinely LEARNED and error-driven, to 2D:

  * Two-channel HEX sensor sheet: each F×F cell carries [object_lum, pointer_lum],
    coupled to its 6 odd-r hex neighbours; the hidden layer learns to predict it.
  * LEARNED perception: a readout maps the net's hidden beliefs -> the RETINAL (in-
    window) position of the object AND of the hand; world = gaze φ + retinal.  Self-
    supervised against the colour/luminance COM teacher during a developmental phase.
  * ERROR-DRIVEN fovea: moves along the 2-D prediction-error gradient (no oracle).
  * BODY MODEL (own PC module, 2-D): the hand's FELT position, moved by EFFERENCE and
    corrected by vision when in view -> the agent knows its hand even out of sight.
  * LEARNED manipulation: a goal prior on the object + a learned contact coupling carry
    the object to the target by error-driven action (no K·(goal−obj) controller).

This is v1 (foundation + learned-coupling manipulation).  The genuine 2-D PUSH-side
policy (MPC through a learned 2-D push model) is the next milestone on top.

Run:  python test_pc_act10.py            (live top-down render)
      ACT10_HEADLESS=1 python ...        (metrics only)
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

G        = 24          # world is G×G
F        = 8           # fovea window is F×F
CONTACT_R = 1.6
GOAL_K   = 0.15        # carry gain
VMAX     = 1.2
APPROACH = 2.0
TOL      = 1.6


def blob2d(pos, n, sigma=1.0):
    cx = pos[0] / (G - 1) * (n - 1); cy = pos[1] / (G - 1) * (n - 1)
    xs = np.arange(n)
    return np.outer(np.exp(-0.5 * ((xs - cy) / sigma) ** 2),
                    np.exp(-0.5 * ((xs - cx) / sigma) ** 2))   # [row=y, col=x]


def com2d(w):
    w = np.clip(w, 0.0, None); s = w.sum()
    if s < 1e-4:
        return None
    ys, xs = np.mgrid[0:w.shape[0], 0:w.shape[1]]
    return np.array([(xs * w).sum() / s, (ys * w).sum() / s])


def hex_neighbors(r, c, rows, cols):
    if r % 2 == 0:
        cand = [(r, c-1), (r, c+1), (r-1, c-1), (r-1, c), (r+1, c-1), (r+1, c)]
    else:
        cand = [(r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c+1)]
    return [(rr, cc) for rr, cc in cand if 0 <= rr < rows and 0 <= cc < cols]


def window(field, phi):
    ox, oy = int(round(phi[0])), int(round(phi[1]))
    out = np.zeros((F, F) + field.shape[2:])
    for r in range(F):
        wy = oy + r
        if 0 <= wy < G:
            for c in range(F):
                wx = ox + c
                if 0 <= wx < G:
                    out[r, c] = field[wy, wx]
    return out


# --------------------------------------------------------------------------- #
# 2-D world: one object (push-on-touch), a pointer, a target.
# --------------------------------------------------------------------------- #
class World2D:
    def __init__(self, seed=0, obj_min=0.6, obj_max=2.0):
        self.rng = np.random.default_rng(seed)
        self.lo, self.hi = G / 8.0, G * 7.0 / 8.0
        self.obj_min, self.obj_max = obj_min, obj_max     # object gaussian size (≈1–5px)
        self.obj = self._rand(); self.target = self._rand()
        self.obj_sigma = self._rand_sigma()

    def _rand(self):
        return self.rng.uniform(self.lo, self.hi, 2)

    def _rand_sigma(self):
        return float(self.rng.uniform(self.obj_min, self.obj_max))

    def scatter(self, with_target=False):
        self.obj = self._rand(); self.obj_sigma = self._rand_sigma()   # fresh size each time
        if with_target:
            self.target = self._rand()

    def push(self, ptr, ptr_vel):
        if np.linalg.norm(ptr - self.obj) < CONTACT_R:
            self.obj = np.clip(self.obj + ptr_vel, 0, G - 1)
            return True
        return False

    def obj_lum(self):
        return blob2d(self.obj, G, sigma=self.obj_sigma)   # gaussian, size = obj_sigma

    def ptr_lum(self, ptr):
        return blob2d(ptr, G, sigma=0.9)


# --------------------------------------------------------------------------- #
# Hex sensor sheet (two channels: object, pointer) + hidden layers.
# --------------------------------------------------------------------------- #
def build_hexnet(rng):
    net = PCNetwork(eta_inf=0.05, n_relax=20, eps_tol=1e-5, eta_learn=0.006,
                    gamma=0.3, w_clip=3.0, rng=rng)
    cells = {}
    for r in range(F):
        for c in range(F):
            cells[(r, c)] = net.add(SensorNode(f"s_{r}_{c}", dim=2))   # [obj, ptr]
    for r in range(F):
        for c in range(F):
            for (rr, cc) in hex_neighbors(r, c, F, F):
                net.connect(f"s_{r}_{c}", f"s_{rr}_{cc}", ConnType.LATERAL,
                            pressure_scale=0.1)
    h1 = []
    for r in range(0, F, 2):
        for c in range(0, F, 2):
            nid = f"h1_{r}_{c}"
            net.add(PCNode(nid, dim=10, activation="tanh", rng=rng)); h1.append(nid)
            for (rr, cc) in [(r, c)] + hex_neighbors(r, c, F, F):
                net.connect(nid, f"s_{rr}_{cc}", ConnType.UP, pressure_scale=1.0)
    net.add(PCNode("top", dim=8, activation="tanh", rng=rng))
    for nid in h1:
        net.connect("top", nid, ConnType.UP, pressure_scale=0.3)
    vc = PCModule("VisualCortex")
    vc.add_in_port("cells", [f"s_{r}_{c}" for r in range(F) for c in range(F)])
    vc.add_out_port("abstract", ["top"]); net.add_module(vc)
    return net, cells, h1


def set_sheet(cells, obj_w, ptr_w):
    for r in range(F):
        for c in range(F):
            cells[(r, c)].set_input(np.array([obj_w[r, c], ptr_w[r, c]]))


def gather(net, ids):
    return np.concatenate([net.node(i).mu for i in ids])


def fovea_gradient(cells):
    """2-D active-inference fovea drive on the OBJECT channel: ∂E/∂(φx,φy)."""
    e = np.array([[cells[(r, c)].epsilon[0] for c in range(F)] for r in range(F)])
    pi = np.array([[cells[(r, c)].pi[0] for c in range(F)] for r in range(F)])
    gx = (np.roll(pi, -1, 1) - np.roll(pi, 1, 1)) * 0.5
    gy = (np.roll(pi, -1, 0) - np.roll(pi, 1, 0)) * 0.5
    return np.array([float((e * gx).sum()), float((e * gy).sum())])


# --------------------------------------------------------------------------- #
# Learned readout: hidden beliefs -> RETINAL (in-window) 2-D position.
# --------------------------------------------------------------------------- #
class Readout:
    def __init__(self, in_dim, hid=64, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 1/np.sqrt(in_dim), (hid, in_dim)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1/np.sqrt(hid), (2, hid)); self.b2 = np.zeros(2)
        self.lr = lr; self.err_ema = None

    def predict(self, x):
        h = np.tanh(self.W1 @ x + self.b1)
        return self.W2 @ h + self.b2, h

    def train(self, x, target_win_norm):
        y, h = self.predict(x)
        err = y - target_win_norm
        e = float(np.linalg.norm(err))
        self.err_ema = e if self.err_ema is None else 0.99*self.err_ema + 0.01*e
        self.W2 -= self.lr * np.outer(err, h); self.b2 -= self.lr * err
        dh = (self.W2.T @ err) * (1 - h**2)
        self.W1 -= self.lr * np.outer(dh, x); self.b1 -= self.lr * dh


# --------------------------------------------------------------------------- #
# Body model (own PC module), 2-D: belief(dim2) -> obs(dim2), per body part.
# --------------------------------------------------------------------------- #
class BodyModel:
    def __init__(self, parts=("hand",), rng=None):
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.25, n_relax=20, eps_tol=1e-6, eta_learn=0.02,
                        gamma=0.3, w_clip=3.0, rng=self.rng)
        self.b, self.s, self.conn = {}, {}, {}
        for p in parts:
            self.b[p] = net.add(PCNode(f"b_{p}", dim=2, activation="identity",
                                       eta_temporal=0.0, rng=self.rng))
            self.s[p] = net.add(SensorNode(f"s_{p}", dim=2))
            self.conn[p] = net.connect(f"b_{p}", f"s_{p}", ConnType.UP, pressure_scale=1.0)
        mod = PCModule("BodyModel")
        for p in parts:
            mod.add_in_port(f"{p}_obs", [f"s_{p}"]).add_out_port(f"{p}_belief", [f"b_{p}"])
        net.add_module(mod)
        self.net, self.parts = net, parts

    def babble(self, steps):
        for _ in range(steps):
            for p in self.parts:
                v = self.rng.uniform(0, 1, 2)
                self.b[p].clamp(v); self.s[p].set_input(v)
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()
        for p in self.parts:
            self.b[p].unclamp()

    def set_felt(self, part, pos):
        self.b[part].mu = np.asarray(pos, float) / (G - 1)

    def update(self, part, a, obs, eta=0.5):
        b = self.b[part]
        b.mu = np.clip(b.mu + np.asarray(a, float) / (G - 1), 0.0, 1.0)   # efference (limb-limited)
        if obs is not None:
            Wm = self.conn[part].W
            err = np.asarray(obs, float) / (G - 1) - (Wm @ b.mu)
            b.mu = b.mu + eta * (Wm.T @ err)                              # vision correction

    def felt(self, part):
        return self.b[part].mu * (G - 1)


# --------------------------------------------------------------------------- #
# Learned contact coupling J(|d|): does my motion move the object? (babble)
# --------------------------------------------------------------------------- #
class Coupling:
    def __init__(self, hid=24, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 0.6, (hid, 1)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 0.3, hid); self.b2 = 0.0
        self.lr = lr; self.rng = rng

    def predict(self, dist):
        h = np.tanh(self.W1 @ np.array([dist / CONTACT_R]) + self.b1)
        return float(self.W2 @ h + self.b2), h

    def babble(self, world, steps):
        for _ in range(steps):
            obj = world._rand(); ang = self.rng.uniform(0, 2*np.pi)
            dist = self.rng.uniform(0, CONTACT_R + 2)
            d = dist * np.array([np.cos(ang), np.sin(ang)])
            a = self.rng.uniform(-1, 1, 2)
            world.obj = obj.copy()
            moved = world.push(obj + d, a)
            dobj = np.linalg.norm(world.obj - obj)
            amag = np.linalg.norm(a)
            target = dobj / amag if amag > 1e-3 else 0.0
            y, h = self.predict(dist)
            err = y - target
            self.W2 -= self.lr * err * h; self.b2 -= self.lr * err
            dh = (self.W2 * err) * (1 - h**2)
            self.W1 -= self.lr * np.outer(dh, np.array([dist / CONTACT_R])); self.b1 -= self.lr * dh

    def scramble(self):
        self.W1 = self.rng.normal(0, 0.6, self.W1.shape); self.W2 = self.rng.normal(0, 0.6, self.W2.shape)


# --------------------------------------------------------------------------- #
# Object-goal prior (2-D proprio-style): signed object→target error per axis.
# --------------------------------------------------------------------------- #
class GoalPrior:
    def __init__(self, rng=None):
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=40, eps_tol=1e-6, eta_learn=0.02,
                        gamma=0.3, w_clip=3.0, rng=self.rng)
        self.goal = net.add(SensorNode("goal", dim=2))
        self.belief = net.add(PCNode("belief", dim=4, activation="identity",
                                     eta_temporal=0.0, rng=self.rng))
        self.pos = net.add(SensorNode("pos", dim=2))
        net.connect("goal", "belief", ConnType.UP, pressure_scale=1.0)
        net.connect("belief", "pos", ConnType.UP, pressure_scale=1.0)
        self.net = net

    def babble(self, steps):
        for _ in range(steps):
            v = self.rng.uniform(0, 1, 2)
            self.goal.set_input(v); self.pos.set_input(v)
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()

    def error(self, pos, goal):
        self.goal.set_input(np.asarray(goal, float) / (G - 1))
        self.pos.set_input(np.asarray(pos, float) / (G - 1))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self.net.node("pos").epsilon.copy()      # signed (pos - goal), normalised

    def scramble(self):
        conns = self.net._connections
        for c in (conns.values() if hasattr(conns, "values") else conns):
            c.W = self.rng.normal(0, 0.5, c.W.shape)


# --------------------------------------------------------------------------- #
def render(step, total, world, phi, perceived, ptr, finger, info):
    """Top-down HEX grid: cells space-separated, odd rows shifted half a cell (odd-r
    offset lattice the net is wired on); the F×F fovea window is shown by '[' ']' placed
    IN the inter-cell gaps so the grid never shifts.  The object is drawn with its
    gaussian falloff (█▓░ by luminance), + target, P/p hand."""
    ox, oy = int(round(phi[0])), int(round(phi[1]))
    lum = world.obj_lum()
    glyph = [["·"] * G for _ in range(G)]
    for y in range(G):                                  # object: gaussian shading
        for xc in range(G):
            v = lum[y, xc]
            if v >= 0.85:   glyph[y][xc] = "█"
            elif v >= 0.45: glyph[y][xc] = "▓"
            elif v >= 0.15: glyph[y][xc] = "░"
    tx, ty = np.round(world.target).astype(int)
    if 0 <= tx < G and 0 <= ty < G and glyph[ty][tx] == "·":
        glyph[ty][tx] = "+"
    px, py = np.round(ptr).astype(int)
    if 0 <= px < G and 0 <= py < G:
        glyph[py][px] = "P" if finger else "p"

    c0, c1 = max(ox, 0), min(ox + F - 1, G - 1)
    lines = [f"Step {step}/{total}  obj=({world.obj[0]:.0f},{world.obj[1]:.0f}) "
             f"size={world.obj_sigma:.1f}  tgt=({tx},{ty})  finger={finger}",
             "  █▓░=object(gaussian)  +=target  P/p=hand  [..]=fovea"]
    for r in range(G):
        win = oy <= r <= oy + F - 1 and c0 <= c1
        gaps = [" "] * (G + 1)
        if win:
            gaps[c0] = "["; gaps[c1 + 1] = "]"
        row = "".join(gaps[c] + glyph[r][c] for c in range(G)) + gaps[G]
        lines.append("  " + (" " if r % 2 == 1 else "") + row)
    sys.stdout.write("\x1b[H\x1b[2J"); print("\n".join(lines), flush=True)


# --------------------------------------------------------------------------- #
def main():
    HEADLESS = os.environ.get("ACT10_HEADLESS", "0") == "1"
    SCALE = float(os.environ.get("ACT10_SCALE", "1.0"))
    DELAY = float(os.environ.get("ACT10_DELAY", "0.0"))
    GOAL = os.environ.get("ACT10_GOAL", "obj").lower()      # obj | none | scramble
    GAIN = 3.0; SMOOTH = 0.3
    rng = np.random.default_rng(0)

    def prog(msg):
        sys.stdout.write("\r\x1b[2K  [setup] " + msg); sys.stdout.flush()

    print("act10 — 2D port: constructing & pre-training the modules ...")
    net, cells, h1 = build_hexnet(rng)
    ro_obj = Readout(len(h1) * 10, rng=np.random.default_rng(3))
    ro_ptr = Readout(len(h1) * 10, rng=np.random.default_rng(4))
    prog("body model babble ...");      body = BodyModel(("hand",), rng=np.random.default_rng(5)); body.babble(2000)
    coupling = Coupling(rng=np.random.default_rng(6))
    goalprior = GoalPrior(rng=np.random.default_rng(7))
    world = World2D(seed=1)
    prog("contact-coupling babble ..."); coupling.babble(world, int(8000 * SCALE))
    prog("object-goal prior babble ..."); goalprior.babble(int(9000 * SCALE))
    if GOAL == "scramble":
        coupling.scramble(); goalprior.scramble()       # control: break the learned models
    sys.stdout.write("\r\x1b[2K"); sys.stdout.flush()

    DEV = int(3000 * SCALE); ACTIVE = int(6000 * SCALE); total = DEV + ACTIVE
    phi = np.array([G/2.0 - F/2.0, G/2.0 - F/2.0])
    ptr = np.array([G/2.0, G/2.0]); body.set_felt("hand", ptr)
    fov_v = np.zeros(2)
    obj_err, obj_n = 0.0, 0
    ptr_in, ptr_in_n, ptr_out, ptr_out_n = 0.0, 0, 0.0, 0
    in_view = act = 0
    deliveries = episodes = ep_steps = 0; ep_best = 1e9; EP_CAP = 160
    se_hist = []

    print(f"act10 — 2D port of act8b (learned perception + error-driven action + body model)")
    print(f"  world={G} fovea={F}  goal={GOAL}  dev={DEV} active={ACTIVE}")

    for step in range(total):
        dev = step < DEV
        if dev and step % 100 == 0:                     # developmental-phase progress
            se = np.mean(se_hist[-50:]) if se_hist else float("nan")
            sys.stdout.write(f"\r\x1b[2K  [learning the 2D world model]  "
                             f"{step}/{DEV} ({100*step//DEV}%)   sensor_err {se:.3f}")
            sys.stdout.flush()
            if step + 100 >= DEV:
                sys.stdout.write("\r\x1b[2K  [done — active phase]\n"); sys.stdout.flush()
        obj_w = window(world.obj_lum(), phi)
        ptr_w = window(world.ptr_lum(ptr), phi)
        set_sheet(cells, obj_w, ptr_w)
        r = net.step(learn=True); net.commit_step()
        if np.isfinite(r["sensor_error"]):
            se_hist.append(r["sensor_error"])

        x = gather(net, h1)
        off = np.array([int(round(phi[0])), int(round(phi[1]))])
        # object perception
        oc = com2d(obj_w); obj_seen = oc is not None
        if obj_seen:
            ro_obj.train(x, oc / (F - 1))
        op, _ = ro_obj.predict(x)
        obj_perc = off + np.clip(op * (F - 1), 0, F - 1) if obj_seen else None
        # pointer perception (for the body model's visual correction)
        pc = com2d(ptr_w); ptr_seen = pc is not None
        ptr_vis = None
        if ptr_seen:
            ro_ptr.train(x, pc / (F - 1))
            pp, _ = ro_ptr.predict(x)
            ptr_vis = off + np.clip(pp * (F - 1), 0, F - 1)

        if dev:
            world.scatter()
            ti = world.obj - np.array([F/2.0, F/2.0]) + rng.normal(0, 2, 2)
            phi = np.clip(ti, -F/2.0, G - F/2.0)
            ptr = world._rand(); body.set_felt("hand", ptr)
        else:
            if step == DEV or np.linalg.norm(world.obj - world.target) < TOL or ep_steps >= EP_CAP:
                if step > DEV:
                    episodes += 1
                    if np.linalg.norm(world.obj - world.target) < TOL:
                        deliveries += 1
                ep_steps = 0; ep_best = 1e9
                world.scatter(with_target=True)
                while np.linalg.norm(world.obj - world.target) < 8:
                    world.target = world._rand()
                phi = np.clip(world.obj - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
                ptr = world.obj.copy(); body.set_felt("hand", ptr)
            # error-driven fovea on the object
            disp = -fovea_gradient(cells)
            fov_v = (1 - SMOOTH) * (GAIN * disp) + SMOOTH * fov_v
            fov_v = np.clip(fov_v, -2.0, 2.0)
            phi = np.clip(phi + fov_v, -F/2.0, G - F/2.0)
            act += 1; in_view += int(obj_seen); ep_steps += 1
            if obj_perc is not None:
                obj_err += np.linalg.norm(obj_perc - world.obj); obj_n += 1

            obj_before = world.obj.copy()
            a = np.zeros(2); finger = False
            if obj_perc is not None and GOAL != "none":
                hand = body.felt("hand")                 # act on the FELT hand
                eps_obj = goalprior.error(obj_perc, world.target)   # signed obj→tgt error
                grabbed = np.linalg.norm(hand - obj_perc) < CONTACT_R
                if grabbed:
                    finger = True
                    J, _ = coupling.predict(0.0)
                    a = np.clip(-GOAL_K * (G - 1) * J * eps_obj, -VMAX, VMAX)
                else:
                    a = np.clip(GOAL_K * (obj_perc - hand), -APPROACH, APPROACH)
            # physical execution (with noise) + body model update
            noise = rng.normal(0, 0.12, 2)
            ptr = np.clip(ptr + a + noise, 0, G - 1)
            world.push(ptr, a) if finger else None
            body.update("hand", a, ptr_vis)
            e = np.linalg.norm(body.felt("hand") - ptr)
            if ptr_vis is not None:
                ptr_in += e; ptr_in_n += 1
            else:
                ptr_out += e; ptr_out_n += 1
            # efference gaze pursuit (object moved by our own push)
            phi = np.clip(phi + (world.obj - obj_before), -F/2.0, G - F/2.0)
            info = {"finger": finger}
            if not HEADLESS:
                render(step, total, world, phi, obj_perc, ptr, finger, info)
                if DELAY > 0:
                    time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    print("=" * 70)
    print(f"  act10 summary (2D port)  goal={GOAL}")
    print(f"  sensor_error: {np.mean(se_hist[:q]):.3f} → {np.mean(se_hist[-q:]):.3f}"
          f"   [hex net learns the 2D image]")
    print(f"  fovea (error-driven) object in view: {100.0*in_view/max(1,act):.1f}%")
    print(f"  object perceived (net) vs true: {obj_err/max(1,obj_n):.2f}px")
    print(f"  BODY felt-hand vs true: in-view {ptr_in/max(1,ptr_in_n):.2f}px | "
          f"out {ptr_out/max(1,ptr_out_n):.2f}px")
    rate = f"{100.0*deliveries/episodes:.0f}% ({deliveries}/{episodes})" if episodes else f"{deliveries}"
    print(f"  object DELIVERED: {rate} (cap {EP_CAP})   [learned-coupling manipulation]")
    print("=" * 70)


if __name__ == "__main__":
    main()
