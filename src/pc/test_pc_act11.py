r"""
test_pc_act11.py — act10 + COLOUR, MULTI-OBJECT, and the COLOUR-COMMAND conditioning (2D).

act10 ported the learned/error-driven/coordinate-free line to 2-D for ONE monochrome
object.  act11 adds the richness from the 1-D act8 line:

  * MULTIPLE coloured objects (a palette of distinct hues), as a 3-channel RGB hex
    sensor sheet [R,G,B,pointer,target]; the net learns the coloured scene.
  * The CONDITIONING module: a digital COLOUR COMMAND (assigned meaning = "transport the
    object of THIS colour") steers which object the agent acts on.
  * SELECTION by colour-cued attention: the agent matches the perceived colours against
    the command and attends to / searches for the commanded object; the others are
    visible DISTRACTORS.  Then it transports the SELECTED object to the (searched) target.

Reuses act10's proven parts (Readout, BodyModel, Coupling, hex helpers, target search,
blind-efference reach + vision-on-contact, lifelong learning).

Run:  python test_pc_act11.py            (live colour top-down render)
      ACT11_HEADLESS=1 python ...         (metrics only)
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
                              Readout, BodyModel, Coupling, GoalPrior)

# distinct, well-separated hues; objects pick distinct ones so colour identifies them
PALETTE = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1],
                    [1, 1, 0], [1, 0, 1], [0, 1, 1]], float)
NAMES = ["R", "G", "B", "Y", "M", "C"]
N_OBJ = int(os.environ.get("ACT11_NOBJ", "3"))
MATCH_TH = 0.9                  # colour-cosine threshold for "this is the commanded colour"


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
    lines = [f"Step {step}/{total}  COMMAND=move '{cmd}'  tgt=({tx},{ty})  {mode}",
             f"  coloured blobs=objects (letter=commanded centre)  +=target  P/p=hand  [..]=fovea"]
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
    HEADLESS = os.environ.get("ACT11_HEADLESS", "0") == "1"
    SCALE = float(os.environ.get("ACT11_SCALE", "1.0"))
    DELAY = float(os.environ.get("ACT11_DELAY", "0.0"))
    GOAL = os.environ.get("ACT11_GOAL", "obj").lower()       # obj | none | scramble
    LIFELONG = os.environ.get("ACT11_LIFELONG", "1") == "1"
    GAIN = 3.0; SMOOTH = 0.3
    rng = np.random.default_rng(0)

    def prog(msg):
        sys.stdout.write("\r\x1b[2K  [setup] " + msg); sys.stdout.flush()

    print(f"act11 — 2D colour / multi-object / colour-command conditioning  (N={N_OBJ})")
    net, cells, h1 = build_hexnet(rng)
    ro_ptr = Readout(len(h1) * 12, rng=np.random.default_rng(4))
    prog("body model babble ..."); body = BodyModel(("hand",), rng=np.random.default_rng(5)); body.babble(2000)
    coupling = Coupling(rng=np.random.default_rng(6))
    goalprior = GoalPrior(rng=np.random.default_rng(7))   # LEARNED signed object→goal error
    world = WorldColor(seed=1)
    prog("contact-coupling babble ...")
    # coupling babble needs a push world; reuse a tiny monochrome proxy via act10 World2D
    from pc.test_pc_act10 import World2D
    coupling.babble(World2D(seed=2), int(8000 * SCALE))
    prog("object-goal prior babble ..."); goalprior.babble(int(9000 * SCALE))
    if GOAL == "scramble":
        coupling.scramble(); goalprior.scramble()
    sys.stdout.write("\r\x1b[2K"); sys.stdout.flush()

    DEV = int(3000 * SCALE); ACTIVE = int(6000 * SCALE); total = DEV + ACTIVE
    phi = np.array([G/2.0 - F/2.0, G/2.0 - F/2.0])
    ptr = np.array([G/2.0, G/2.0]); body.set_felt("hand", ptr)
    fov_v = np.zeros(2)
    se_hist = []
    in_view = act = 0
    sel_err, sel_n = 0.0, 0
    ptr_in, ptr_in_n, ptr_out, ptr_out_n = 0.0, 0, 0.0, 0
    deliveries = episodes = ep_steps = 0; ep_best = 1e9; EP_CAP = 200
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

        x = gather(net, h1)
        off = np.array([int(round(phi[0])), int(round(phi[1]))])
        cmd = world.cmd_color()
        # SELECTION by colour-cued attention (the conditioning at work)
        sel = selected_lum(rgb_w, cmd)
        sc = com2d(sel); obj_seen = sc is not None
        obj_perc = (off + sc) if obj_seen else None
        # pointer perception (body model visual correction)
        pc = com2d(ptr_w); ptr_vis = None
        if pc is not None:
            ro_ptr.train(x, pc / (F - 1)); pp, _ = ro_ptr.predict(x)
            ptr_vis = off + np.clip(pp * (F - 1), 0, F - 1)
        # target perception
        tc = com2d(tgt_w); tgt_seen = tc is not None
        tgt_perc = (off + tc) if tgt_seen else None

        if dev:
            world.scatter(with_target=True)
            focus = world.commanded_pos() if rng.random() < 0.5 else world.target
            phi = np.clip(focus - np.array([F/2.0, F/2.0]) + rng.normal(0, 2, 2), -F/2.0, G - F/2.0)
            ptr = world._rand(); body.set_felt("hand", ptr)
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
            ep_steps = 0; ep_best = 1e9
            world.scatter(with_target=True)
            while np.linalg.norm(world.commanded_pos() - world.target) < 8:
                world.target = world._rand()
            phi = np.clip(world.commanded_pos() - np.array([F/2.0, F/2.0]), -F/2.0, G - F/2.0)
            searching = True; scan_idx = 0; tgt_felt = None; obj_mem = None
            ptr = world.commanded_pos().copy(); body.set_felt("hand", ptr)

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
            # fovea: colour-cued servo onto the commanded object
            if obj_perc is not None:
                fov_v = (1 - SMOOTH) * (GAIN * (obj_perc - off - center)) + SMOOTH * fov_v
                fov_v = np.clip(fov_v, -2.0, 2.0)
                phi = np.clip(phi + fov_v, -F/2.0, G - F/2.0)
            hand = body.felt("hand")
            grabbed = here is not None and np.linalg.norm(hand - here) < CONTACT_R
            goal = tgt_felt if tgt_felt is not None else world.target
            dist_now = float(np.linalg.norm(world.commanded_pos() - goal))
            if dist_now < ep_best - 0.5:
                ep_best = dist_now
            obj_before = world.commanded_pos().copy()
            if here is not None and GOAL != "none":
                if grabbed:
                    finger = True
                    eps = goalprior.error(here, goal)     # LEARNED signed object→goal error
                    J, _ = coupling.predict(0.0)
                    a = np.clip(-GOAL_K * (G - 1) * J * eps, -VMAX, VMAX)
                else:
                    a = np.clip(GOAL_K * (here - hand), -APPROACH, APPROACH)
            noise = rng.normal(0, 0.12, 2)
            ptr = np.clip(ptr + a + noise, 0, G - 1)
            if finger:
                world.carry_commanded(a)
            body.update("hand", a, ptr_vis)
            if LIFELONG and GOAL != "scramble" and finger:
                coupling.observe(float(np.linalg.norm(hand - here)),
                                 float(np.linalg.norm(world.commanded_pos() - obj_before)),
                                 float(np.linalg.norm(a)))
                if ptr_vis is not None:
                    body.learn("hand", ptr_vis)
            e = np.linalg.norm(body.felt("hand") - ptr)
            if ptr_vis is not None:
                ptr_in += e; ptr_in_n += 1
            else:
                ptr_out += e; ptr_out_n += 1
            phi = np.clip(phi + (world.commanded_pos() - obj_before), -F/2.0, G - F/2.0)

        if not HEADLESS:
            render(step, total, world, phi, ptr, finger, {"mode": mode})
            if DELAY > 0:
                time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    print("=" * 70)
    print(f"  act11 summary (2D colour / multi-object / conditioning)  goal={GOAL}  N={N_OBJ}")
    print(f"  sensor_error: {np.mean(se_hist[:q]):.3f} → {np.mean(se_hist[-q:]):.3f}")
    print(f"  SELECTION (attended obj vs COMMANDED obj): {sel_err/max(1,sel_n):.2f}px"
          f"   [colour command picks the right object among distractors]")
    print(f"  BODY felt-hand vs true: in {ptr_in/max(1,ptr_in_n):.2f}px | out {ptr_out/max(1,ptr_out_n):.2f}px")
    rate = f"{100.0*deliveries/episodes:.0f}% ({deliveries}/{episodes})" if episodes else f"{deliveries}"
    print(f"  COMMANDED object DELIVERED: {rate} (cap {EP_CAP})")
    print("=" * 70)


if __name__ == "__main__":
    main()
