r"""
test_pc_act9.py — 2D top-down world: colour-conditioned, multi-object transport on a
HEXAGONAL sensor sheet.

The act5→act8 line lived in 1-D.  act9 lifts the whole validated pipeline to a 2-D
top-down world (chosen scope: full 2-D + colour + multi-object at once):

  * World        : G×G top-down field; several coloured objects lie around.
  * Fovea        : an F×F window slides over the world at offset (phi_x, phi_y).
  * Sensor sheet : F×F cells, each [lum, R, G, B, ptr], coupled HEXAGONALLY — every
                   cell to its 6 offset-row neighbours (odd-r), and the input PC net
                   (sensor laterals + hidden receptive fields) is built on that hex
                   neighbourhood (the user's geometry, realised in 2-D).
  * Perception   : a colour COMMAND selects which object to fetch; a hue-matched 2-D
                   centre-of-mass + the fovea offset gives its world position.  Object-
                   permanence memory + a 2-D raster SEARCH re-acquire it when lost.
  * Transport    : a pointer approaches the commanded object, the finger grips it (the
                   nearest object of ANY colour → it can grab the wrong one; a wrong
                   grab is detected by colour and released), and carries it to the goal.
  * Goal/planner : a 2-D GoalModule (dreamable latent) + a planner producing 2-D goals
                   (curiosity / learned-conditioned).  Command colour cycles per
                   delivery, so the agent must keep finding new objects.
  * Physics      : objects never self-propel; they lie at rest and are shoved when hit
                   (2-D collision, held object dominates); wall bounce; grippable.

A passive phase lets the hex PC net learn to predict the 2-D coloured image (sensor
error drops); the active phase runs the goal-directed control above.

Run:  python test_pc_act9.py        (live top-down render)
      ACT9_HEADLESS=1 python ...     (metrics only)
Env:  ACT9_PLAN=curiosity|learned  ACT9_COND=0|1  ACT9_NOBJ=N  ACT9_GRIP=0|1
      ACT9_CYCLE=0|1  ACT9_EPISODES_SCALE=f  ACT9_LOG_EVERY=n
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

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
G        = 24          # world is G×G
F        = 8           # fovea window is F×F
FING_R   = 1.6         # finger grip radius (world units)
COLLIDE  = 2.0         # object-object touch distance
GOAL_K   = 0.15        # carry/approach gain
VMAX     = 1.2         # carry speed cap (so the fovea keeps up)
APPROACH_VMAX = 2.0    # free approach speed cap
TOL      = 1.6         # success distance (object at goal)
N_OBJ_COLOR = 3
OBJECT_COLORS = [
    ("red",     (1.0, 0.0, 0.0)),
    ("green",   (0.0, 1.0, 0.0)),
    ("blue",    (0.0, 0.0, 1.0)),
    ("yellow",  (1.0, 1.0, 0.0)),
    ("cyan",    (0.0, 1.0, 1.0)),
    ("magenta", (1.0, 0.0, 1.0)),
]
COLOR_INITIAL = {n: n[0].upper() for n, _ in OBJECT_COLORS}


# --------------------------------------------------------------------------- #
# Hexagonal geometry (odd-r offset rows): each cell has up to 6 neighbours.
# --------------------------------------------------------------------------- #
def hex_neighbors(r: int, c: int, rows: int, cols: int) -> list[tuple[int, int]]:
    """6 hex neighbours of cell (r,c) on an odd-r offset grid, clipped to bounds."""
    if r % 2 == 0:
        cand = [(r, c - 1), (r, c + 1), (r - 1, c - 1), (r - 1, c),
                (r + 1, c - 1), (r + 1, c)]
    else:
        cand = [(r, c - 1), (r, c + 1), (r - 1, c), (r - 1, c + 1),
                (r + 1, c), (r + 1, c + 1)]
    return [(rr, cc) for rr, cc in cand if 0 <= rr < rows and 0 <= cc < cols]


def blob2d(pos, n: int, sigma: float = 1.0) -> np.ndarray:
    """(n,n) gaussian blob centred at world pos=(x,y) scaled into an n×n image."""
    cx = pos[0] / (G - 1) * (n - 1)
    cy = pos[1] / (G - 1) * (n - 1)
    xs = np.arange(n)
    gx = np.exp(-0.5 * ((xs - cx) / sigma) ** 2)
    gy = np.exp(-0.5 * ((xs - cy) / sigma) ** 2)
    return np.outer(gy, gx)            # [row=y, col=x]


def com2d(weight: np.ndarray):
    """Intensity-weighted (x,y) centre of mass of a 2-D map, or None if empty."""
    w = np.clip(weight, 0.0, None)
    s = w.sum()
    if s < 1e-4:
        return None
    ys, xs = np.mgrid[0:w.shape[0], 0:w.shape[1]]
    return np.array([(xs * w).sum() / s, (ys * w).sum() / s])


# --------------------------------------------------------------------------- #
# 2-D physics world
# --------------------------------------------------------------------------- #
class World2D:
    def __init__(self, n_objects=3, command_color=None, grippable=True,
                 cycle_command=True, collide=True, friction=0.08, seed=0):
        self.n_objects = n_objects
        self.grippable = grippable
        self.cycle_command = cycle_command
        self.collide = collide
        self.friction = friction
        self.rng = np.random.default_rng(seed)
        self.lo, self.hi = G / 8.0, G * 7.0 / 8.0
        pal = dict(OBJECT_COLORS)
        cmd = command_color if command_color in pal else OBJECT_COLORS[0][0]
        self.command_color_name = cmd
        self.command_color = np.array(pal[cmd], float)
        self.target_pos = self._rand_pos()
        self.target_provider = None
        self.held_idx = None
        self.collisions = 0
        self.flash_timer = 0
        self.dwell_timer = 0
        self.dwell_steps = 12
        self.objects = []
        self._spawn()

    def _rand_pos(self):
        return self.rng.uniform(self.lo, self.hi, 2)

    def _spawn(self):
        centre = np.array([G / 2.0, G / 2.0])
        spread = 0.25 * (self.hi - self.lo)
        others = [i for i in range(len(OBJECT_COLORS))
                  if OBJECT_COLORS[i][0] != self.command_color_name]
        self.rng.shuffle(others)
        self.objects = [{"pos": self._rand_pos(), "vel": np.zeros(2),
                         "color": self.command_color.copy(),
                         "name": self.command_color_name}]
        for k in range(self.n_objects - 1):
            name, rgb = OBJECT_COLORS[others[k % len(others)]]
            pos = np.clip(centre + self.rng.uniform(-spread, spread, 2), self.lo, self.hi)
            self.objects.append({"pos": pos, "vel": np.zeros(2),
                                 "color": np.array(rgb, float), "name": name})
        self.target_idx = 0

    @property
    def obj_pos(self): return self.objects[self.target_idx]["pos"]

    def relocate_target(self):
        if self.target_provider is not None:
            self.target_pos = np.clip(self.target_provider(), self.lo, self.hi)
        else:
            self.target_pos = self._rand_pos()

    def _cycle(self):
        if len(self.objects) <= 1:
            return
        idxs = [i for i in range(len(self.objects)) if i != self.target_idx]
        j = int(self.rng.choice(idxs))
        self.target_idx = j
        self.command_color_name = self.objects[j]["name"]
        self.command_color = self.objects[j]["color"].copy()

    def render_lum(self):
        f = np.zeros((G, G))
        for o in self.objects:
            f = np.maximum(f, blob2d(o["pos"], G))
        return f

    def render_rgb(self):
        rgb = np.zeros((G, G, 3))
        for o in self.objects:
            b = blob2d(o["pos"], G)
            rgb += b[:, :, None] * o["color"][None, None, :]
        return np.clip(rgb, 0.0, 1.0)

    def _resolve_collisions(self, held):
        if not self.collide:
            return
        objs = self.objects
        for i in range(len(objs)):
            for j in range(i + 1, len(objs)):
                a, b = objs[i], objs[j]
                d = b["pos"] - a["pos"]
                dist = float(np.linalg.norm(d))
                if dist >= COLLIDE or dist < 1e-9:
                    continue
                self.collisions += 1
                u = d / dist
                push = COLLIDE - dist
                if held == i:
                    b["pos"] = a["pos"] + u * COLLIDE; b["vel"] = a["vel"].copy()
                elif held == j:
                    a["pos"] = b["pos"] - u * COLLIDE; a["vel"] = b["vel"].copy()
                else:
                    a["vel"], b["vel"] = b["vel"].copy(), a["vel"].copy()
                    a["pos"] = a["pos"] - u * push / 2
                    b["pos"] = b["pos"] + u * push / 2

    def step(self, finger_down: bool, ptr, ptr_vel):
        ptr = np.asarray(ptr, float); ptr_vel = np.asarray(ptr_vel, float)
        contact = False
        # ---- dwell on the goal after a hit ----
        if self.dwell_timer > 0:
            self.dwell_timer -= 1
            self.objects[self.target_idx]["pos"] = self.target_pos.copy()
            self.objects[self.target_idx]["vel"] = np.zeros(2)
            if self.flash_timer > 0:
                self.flash_timer -= 1
            if self.dwell_timer == 0:
                if self.cycle_command:
                    self._cycle()
                self.relocate_target()
            return {"contact": False, "success": True, "flash": self.flash_timer > 0}
        # ---- grip ----
        if finger_down:
            if self.held_idx is None:
                if self.grippable:
                    cand = [(np.linalg.norm(ptr - o["pos"]), i)
                            for i, o in enumerate(self.objects)
                            if np.linalg.norm(ptr - o["pos"]) < FING_R]
                    self.held_idx = min(cand)[1] if cand else None
                elif np.linalg.norm(ptr - self.obj_pos) < FING_R:
                    self.held_idx = self.target_idx
            contact = self.held_idx is not None
        else:
            self.held_idx = None
        # ---- integrate all objects ----
        for i, o in enumerate(self.objects):
            if i == self.held_idx:
                o["vel"] = ptr_vel.copy()
                o["pos"] = o["pos"] + o["vel"]
            else:
                o["vel"] *= (1.0 - self.friction)
                o["pos"] = o["pos"] + o["vel"]
            for k in (0, 1):                       # wall bounce
                if o["pos"][k] <= 0.0:
                    o["pos"][k] = 0.0; o["vel"][k] = abs(o["vel"][k]) * 0.85
                elif o["pos"][k] >= G - 1:
                    o["pos"][k] = G - 1.0; o["vel"][k] = -abs(o["vel"][k]) * 0.85
        self._resolve_collisions(self.held_idx)
        # ---- success ----
        tobj = self.objects[self.target_idx]
        success = (np.linalg.norm(tobj["pos"] - self.target_pos) < TOL
                   and np.linalg.norm(tobj["vel"]) < 0.3)
        if success and self.flash_timer == 0:
            self.flash_timer = 8
            self.dwell_timer = self.dwell_steps
        if self.flash_timer > 0:
            self.flash_timer -= 1
        return {"contact": contact, "success": success, "flash": self.flash_timer > 0}


# --------------------------------------------------------------------------- #
# Fovea windowing + colour-matched perception
# --------------------------------------------------------------------------- #
def window(field: np.ndarray, phi) -> np.ndarray:
    """Extract the F×F (or F×F×C) window at integer offset round(phi)=(ox,oy)."""
    ox, oy = int(round(phi[0])), int(round(phi[1]))
    out = np.zeros((F, F) + field.shape[2:], dtype=float)
    for r in range(F):
        wy = oy + r
        if 0 <= wy < G:
            for c in range(F):
                wx = ox + c
                if 0 <= wx < G:
                    out[r, c] = field[wy, wx]
    return out


def color_match_map(rgb_win: np.ndarray, command_color, thr=0.85) -> np.ndarray:
    """Per-cell weight = cell intensity where its HUE matches the command (cos>thr)."""
    c = np.asarray(command_color, float)
    cn = c / (np.linalg.norm(c) + 1e-9)
    norms = np.linalg.norm(rgb_win, axis=2)
    cos = (rgb_win @ cn) / (norms + 1e-9)
    return np.where(cos > thr, norms, 0.0)


# --------------------------------------------------------------------------- #
# 2-D Goal module (dreamable latent autoencoder over object world-position)
# --------------------------------------------------------------------------- #
class GoalModule2D:
    def __init__(self, img=12, latent=10, rng=None):
        self.M = img
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=50, eps_tol=1e-6, eta_learn=0.01,
                        gamma=0.3, w_clip=3.0, rng=self.rng)
        self.img = net.add(SensorNode("g_img", dim=img * img))
        self.z = net.add(PCNode("g_z", dim=latent, activation="identity",
                                eta_temporal=0.0, rng=self.rng))
        net.connect("g_z", "g_img", ConnType.UP, pressure_scale=1.0)
        self.net = net

    def _blob(self, pos):
        return blob2d(pos, self.M).reshape(-1)

    def _com(self, flat):
        w = np.clip(flat, 0.0, None).reshape(self.M, self.M)
        c = com2d(w)
        if c is None:
            return np.array([G / 2.0, G / 2.0])
        return c / (self.M - 1) * (G - 1)

    def pretrain(self, steps=8000):
        pos = self.rng.uniform(0, G - 1, 2)
        for _ in range(steps):
            pos = np.clip(pos + self.rng.normal(0, G * 0.05, 2), 0, G - 1)
            self.img.set_input(self._blob(pos))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()

    def encode(self, pos):
        self.z.unclamp(); self.img.set_input(self._blob(pos))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self.z.mu.copy()

    def decode_dream(self, z):
        self.img.unclamp(); self.z.clamp(z)
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        out = self._com(self.net.node("g_img").pi)
        self.z.unclamp(); self.img.set_input(self._blob(np.array([G / 2.0, G / 2.0])))
        return out

    def decode_error(self, n=12):
        errs = []
        for _ in range(n):
            p = self.rng.uniform(G * 0.1, G * 0.9, 2)
            self.z.unclamp(); self.img.set_input(self._blob(p))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            errs.append(np.linalg.norm(self._com(self.net.node("g_img").pi) - p))
        return float(np.mean(errs))


# --------------------------------------------------------------------------- #
# 2-D planner: curiosity (novelty) or learned state->goal (conditioned)
# --------------------------------------------------------------------------- #
class Planner2D:
    def __init__(self, gm, lo, hi, mode="curiosity", cond=0, k=24, memory=16, rng=None):
        self.gm, self.lo, self.hi = gm, lo, hi
        self.mode, self.cond, self.k, self.memory = mode, cond, k, memory
        self.rng = rng or np.random.default_rng()
        self.visited = []
        self.state = None

    def set_state(self, pos):
        if pos is not None:
            self.state = np.asarray(pos, float)

    def _rule(self, pos):
        c = np.array([G / 2.0, G / 2.0])
        return (2 * c - pos) if self.cond == 0 else c   # mirror (flag0) / centre (flag1)

    def next_goal(self):
        if self.mode == "learned":
            base = self.state if self.state is not None else np.array([G / 2.0, G / 2.0])
            return np.clip(self._rule(base), self.lo, self.hi)
        cands = self.rng.uniform(self.lo, self.hi, (self.k, 2))
        if not self.visited:
            g = cands[0]
        else:
            nov = [min(np.linalg.norm(c - s) for s in self.visited) for c in cands]
            g = cands[int(np.argmax(nov))]
        self.visited.append(g)
        if len(self.visited) > self.memory:
            self.visited.pop(0)
        return np.clip(g, self.lo, self.hi)


# --------------------------------------------------------------------------- #
# Hex PC perception net (the user's geometry): F×F sensor sheet, 6-neighbour
# lateral coupling, hidden nodes with hex receptive fields.
# --------------------------------------------------------------------------- #
def build_hexnet(rng):
    net = PCNetwork(eta_inf=0.05, n_relax=20, eps_tol=1e-5, eta_learn=0.003,
                    gamma=0.3, w_clip=3.0, rng=rng)
    CH = 5                                       # [lum, R, G, B, ptr]
    cells = {}
    for r in range(F):
        for c in range(F):
            cells[(r, c)] = net.add(SensorNode(f"s_{r}_{c}", dim=CH))
    # hex lateral coupling among sensor cells (each ↔ its 6 offset-row neighbours)
    HEX_PS = 0.1
    for r in range(F):
        for c in range(F):
            for (rr, cc) in hex_neighbors(r, c, F, F):
                net.connect(f"s_{r}_{c}", f"s_{rr}_{cc}", ConnType.LATERAL,
                            pressure_scale=HEX_PS)
    # hidden layer 1: a node at every stride-2 cell, hex receptive field
    centers = [(r, c) for r in range(0, F, 2) for c in range(0, F, 2)]
    h1 = []
    for (r, c) in centers:
        nid = f"h1_{r}_{c}"
        net.add(PCNode(nid, dim=6, activation="tanh", rng=rng))
        h1.append(nid)
        rf = [(r, c)] + hex_neighbors(r, c, F, F)
        for (rr, cc) in rf:
            net.connect(nid, f"s_{rr}_{cc}", ConnType.UP, pressure_scale=1.0)
    # top layer: one node pooling all of h1
    net.add(PCNode("top", dim=8, activation="tanh", rng=rng))
    for nid in h1:
        net.connect("top", nid, ConnType.UP, pressure_scale=0.2)
    vc = PCModule("VisualCortex2D")
    vc.add_in_port("cells", [f"s_{r}_{c}" for r in range(F) for c in range(F)])
    vc.add_out_port("abstract", ["top"])
    net.add_module(vc)
    return net, cells


def set_sheet(cells, lum_w, rgb_w, ptr_w):
    """Clamp the F×F sensor sheet from windowed luminance, RGB and pointer maps."""
    for r in range(F):
        for c in range(F):
            cells[(r, c)].set_input(np.array([
                lum_w[r, c], rgb_w[r, c, 0], rgb_w[r, c, 1], rgb_w[r, c, 2], ptr_w[r, c]]))


# --------------------------------------------------------------------------- #
# Rendering (top-down)
# --------------------------------------------------------------------------- #
def render(step, total, world, phi, ptr, finger, info, headless_skip=False):
    ox, oy = int(round(phi[0])), int(round(phi[1]))
    grid = [["·"] * G for _ in range(G)]
    tx, ty = int(round(world.target_pos[0])), int(round(world.target_pos[1]))
    if 0 <= tx < G and 0 <= ty < G:
        grid[ty][tx] = "+"
    for i, o in enumerate(world.objects):
        x, y = int(round(o["pos"][0])), int(round(o["pos"][1]))
        if 0 <= x < G and 0 <= y < G:
            ch = COLOR_INITIAL[o["name"]]
            grid[y][x] = ch if i != world.target_idx else ch.lower()
    px, py = int(round(ptr[0])), int(round(ptr[1]))
    if 0 <= px < G and 0 <= py < G:
        grid[py][px] = "P" if finger else "p"
    lines = [f"Step {step}/{total}  cmd={world.command_color_name}"
             f"  tgt=({tx},{ty})  held={world.held_idx}"
             f"{'  [FLASH]' if info.get('flash') else ''}"]
    objs = " ".join(f"{'*' if i==world.target_idx else ''}{o['name'][0]}"
                    f"({o['pos'][0]:.0f},{o['pos'][1]:.0f})"
                    for i, o in enumerate(world.objects))
    lines.append("  " + objs)
    for r in range(G):
        row = "".join(grid[r])
        mark = "  <" if oy <= r < oy + F else ""
        # show fovea column span with brackets on the marked rows
        if oy <= r < oy + F:
            rr = list(row)
            if 0 <= ox <= G:
                rr.insert(min(ox, G), "[")
            if 0 <= ox + F <= G:
                rr.insert(min(ox + F + 1, G + 1), "]")
            row = "".join(rr)
        lines.append("  " + row + mark)
    sys.stdout.write("\x1b[H\x1b[2J")
    print("\n".join(lines), flush=True)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    HEADLESS = os.environ.get("ACT9_HEADLESS", "0") == "1"
    PLAN = os.environ.get("ACT9_PLAN", "curiosity").lower()
    COND = int(os.environ.get("ACT9_COND", "0"))
    NOBJ = int(os.environ.get("ACT9_NOBJ", "3"))
    GRIP = os.environ.get("ACT9_GRIP", "1") == "1"
    CYCLE = os.environ.get("ACT9_CYCLE", "1") == "1"
    SCALE = float(os.environ.get("ACT9_EPISODES_SCALE", "1.0"))
    LOG_EVERY = int(os.environ.get("ACT9_LOG_EVERY", "2000"))
    DELAY = float(os.environ.get("ACT9_DELAY", "0.0"))

    rng = np.random.default_rng(42)
    net, cells = build_hexnet(rng)
    gm = GoalModule2D(img=12, latent=10, rng=np.random.default_rng(7))
    gm.pretrain(int(8000 * SCALE) if SCALE < 1 else 8000)

    world = World2D(n_objects=NOBJ, command_color=os.environ.get("ACT9_COLOR"),
                    grippable=GRIP, cycle_command=CYCLE, seed=0)
    planner = Planner2D(gm, world.lo, world.hi, mode=PLAN, cond=COND,
                        rng=np.random.default_rng(11))
    world.target_provider = planner.next_goal

    PASSIVE = int(2000 * SCALE)
    ACTIVE = int(8000 * SCALE)
    total = PASSIVE + ACTIVE

    phi = np.array([G / 2.0 - F / 2.0, G / 2.0 - F / 2.0])
    ptr = np.array([G / 2.0, G / 2.0])
    ptr_vel = np.zeros(2)
    obj_mem = None; mem_age = 0; MEM_TTL = 40; SEARCH_AFTER = 5
    scan = np.array([0.0, 0.0]); scan_dir = 1.0
    last_cmd = world.command_color_name

    print(f"act9 — 2D top-down  world={G}x{G}  fovea={F}x{F}  hex sensor sheet")
    print(f"  plan={PLAN} cond={COND}  objects={NOBJ}  grip={GRIP} cycle={CYCLE}")
    print(f"  goal-module decode_err={gm.decode_error():.2f}px  (2D)")

    se_hist = []
    succ = 0; steps_active = 0; collisions0 = 0
    grip_steps = 0; grip_wrong = 0; sel_total = 0; sel_correct = 0
    seen_steps = 0; act_steps = 0
    win = dict(n=0, dist=0.0, succ=0)

    for step in range(total):
        active = step >= PASSIVE
        lum = world.render_lum(); rgb = world.render_rgb()
        ptr_field = blob2d(ptr, G)
        lum_w = window(lum, phi); rgb_w = window(rgb, phi); ptr_w = window(ptr_field, phi)
        set_sheet(cells, lum_w, rgb_w, ptr_w)

        match_w = color_match_map(rgb_w, world.command_color)

        finger = False
        if active:
            # command switched → drop stale memory, search the new colour
            if world.command_color_name != last_cmd:
                last_cmd = world.command_color_name; obj_mem = None; mem_age = MEM_TTL + 1
            com = com2d(match_w)          # (x,y) within the F×F window
            seen = com is not None
            perceived = None
            # perceived world pos = window offset (round phi) + in-window (x,y) COM
            if seen:
                perceived = np.array([int(round(phi[0])) + com[0],
                                      int(round(phi[1])) + com[1]])
                obj_mem = perceived; mem_age = 0
            elif obj_mem is not None:
                mem_age += 1
                if mem_age > MEM_TTL:
                    obj_mem = None
            obj_ctrl = obj_mem
            seen_steps += int(seen)
            # selection check
            if seen and len(world.objects) > 1:
                d_t = np.linalg.norm(perceived - world.objects[world.target_idx]["pos"])
                d_d = min(np.linalg.norm(perceived - o["pos"])
                          for i, o in enumerate(world.objects) if i != world.target_idx)
                sel_total += 1; sel_correct += int(d_t < d_d)

            planner.set_state(obj_ctrl)
            desired = world.target_pos
            goal_v = np.zeros(2)
            if obj_ctrl is not None:
                act_steps += 1
                wrong = (world.grippable and world.held_idx is not None
                         and world.held_idx != world.target_idx)
                grabbed = np.linalg.norm(ptr - obj_ctrl) < FING_R
                if wrong:
                    grip_steps += 1; grip_wrong += 1
                    finger = False
                    goal_v = np.clip(GOAL_K * (obj_ctrl - ptr), -APPROACH_VMAX, APPROACH_VMAX)
                elif grabbed:
                    if world.grippable and world.held_idx == world.target_idx:
                        grip_steps += 1
                    finger = True
                    goal_v = np.clip(GOAL_K * (desired - obj_ctrl), -VMAX, VMAX)
                else:
                    finger = False
                    goal_v = np.clip(GOAL_K * (obj_ctrl - ptr), -APPROACH_VMAX, APPROACH_VMAX)
            ptr_vel = goal_v
            # Grip is checked at the CURRENT pointer (where 'grabbed' was decided);
            # THEN the pointer and the held object move together by ptr_vel — a rigid
            # grasp.  (Moving the pointer first would carry it off the object before
            # the grip is evaluated → the grasp would miss; the 1-D code only got away
            # with it because one-axis VMAX < FING_R, which fails on the 2-D diagonal.)
            info = world.step(finger, ptr, ptr_vel)
            ptr = np.clip(ptr + ptr_vel, 0, G - 1)
            if os.environ.get("ACT9_DEBUG") == "1" and steps_active < 60:
                _d = np.linalg.norm(ptr - obj_ctrl) if obj_ctrl is not None else -1
                print(f"[dbg a{steps_active}] ptr={np.round(ptr,1)} "
                      f"octrl={np.round(obj_ctrl,1) if obj_ctrl is not None else None} "
                      f"d={_d:.2f} finger={finger} held={world.held_idx} "
                      f"tgt_obj={np.round(world.obj_pos,1)} goal={np.round(world.target_pos,1)}",
                      flush=True)
            if info["success"]:
                succ += 1
            steps_active += 1
            # ---- fovea: track the colour-target; search (raster) when lost ----
            if obj_mem is not None and mem_age <= SEARCH_AFTER:
                tgt_phi = obj_mem - np.array([F / 2.0, F / 2.0])
                phi = np.clip(phi + np.clip(0.8 * (tgt_phi - phi), -2.0, 2.0),
                              -F / 2.0, G - F / 2.0)
            else:
                # raster scan: sweep x, step y at the edges
                phi[0] += scan_dir * 2.0
                if phi[0] >= G - F / 2.0:
                    phi[0] = G - F / 2.0; scan_dir = -1.0; phi[1] += 2.0
                elif phi[0] <= -F / 2.0:
                    phi[0] = -F / 2.0; scan_dir = 1.0; phi[1] += 2.0
                if phi[1] >= G - F / 2.0:
                    phi[1] = -F / 2.0
        else:
            # passive: wander the gaze so the hex net learns the 2-D image
            phi = np.clip(phi + rng.normal(0, 1.0, 2), -F / 2.0, G - F / 2.0)
            info = {"flash": False, "success": False, "contact": False}

        r = net.step(learn=True); net.commit_step()
        se = r["sensor_error"]
        if np.isfinite(se):
            se_hist.append(se)

        if active:
            win["n"] += 1; win["dist"] += float(np.linalg.norm(world.obj_pos - world.target_pos))
            win["succ"] += int(info["success"])
            if HEADLESS and win["n"] >= LOG_EVERY:
                print(f"[active {steps_active:6d}] meanDist={win['dist']/win['n']:5.1f}"
                      f"  succ={win['succ']:4d}"
                      f"  in-view={100.0*seen_steps/max(1,act_steps):4.1f}%"
                      f"  sel={100.0*sel_correct/max(1,sel_total):5.1f}%", flush=True)
                win = dict(n=0, dist=0.0, succ=0)

        if not HEADLESS and active:
            render(step, total, world, phi, ptr, finger, info)
            if DELAY > 0:
                time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    print("=" * 70)
    print(f"  act9 summary  (2D, hex sensor sheet)")
    print(f"  sensor_error: start {np.mean(se_hist[:q]):.3f} → end {np.mean(se_hist[-q:]):.3f}"
          f"   [drops → the hex PC net learned to predict the 2D image]")
    print(f"  active steps : {steps_active}   task successes (flash): {succ}"
          f" ({100.0*succ/max(1,steps_active):.1f}%)")
    print(f"  colour-select: {100.0*sel_correct/max(1,sel_total):.1f}%   "
          f"object-in-view: {100.0*seen_steps/max(1,act_steps):.1f}%   "
          f"could-act: {100.0*act_steps/max(1,steps_active):.1f}%")
    if world.grippable and grip_steps:
        print(f"  grip-steps: {grip_steps}  wrong-colour: {grip_wrong}"
              f" ({100.0*grip_wrong/grip_steps:.1f}%)")
    print(f"  object-object shoves: {world.collisions}"
          f"   command cycling: {world.cycle_command}")
    print("=" * 70)


if __name__ == "__main__":
    main()
