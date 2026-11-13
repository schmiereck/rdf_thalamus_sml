"""Stufe a der Bruecke zu NetResearch (wiki/fragen/netresearch-bruecke.md): Fovea-Bilder mit Etiketten
exportieren, damit Netze aus NetResearch auf echter Roboter-Wahrnehmung antreten koennen.

    .venv/Scripts/python.exe src/pc_cvnn/export_netresearch.py --out ../NetResearch/data/robot

Je Beispiel eine frische Szene (rot / gruen / blau Wuerfel, L, U an zufaelligen Orten und Lagen), die
Uebersichtskamera MIT sichtbarem Arm (kein Privileg im Bild), abgetastet mit der Hex-Fovea von act18
(hex_sample, F = 16, K = 4, abgestufte Peripherie). Zwei Aufgaben, Etikett je ein Schritt in Fovea-Zellen:
    gaze    Wo liegt der rote Wuerfel relativ zur Bildmitte? (dx, dy) = Zelle des Wuerfels - Mitte, -8..7.
            Das ist die Blickverschiebung, die ihn zentriert.
    gazemulti  wie gaze, alle drei Wuerfel im Blickfeld; cells traegt den Schritt fuer rot, gruen und blau
    gazecolor  wie gazemulti, aber die drei Wuerfel tragen je Szene zufaellige Farben (Farbton ausserhalb
            eines zurueckgehaltenen Bands); cells = Schritt je Wuerfel (6), dann die drei Farben
            (9 Werte, RGB x 255 - 128) und ein Index. Die Farbe ist die stetige ADRESSE des Ziels.
    gazecolorheld  dasselbe, ein Wuerfel (Index im letzten Wert) traegt einen zurueckgehaltenen Farbton
    gazecolorref / gazecolorrefheld  wie gazecolor(held), dazu refs uint8 [N, 3, 3, 16, 16]: je Wuerfel ein
            ZEIGEBILD (der Wuerfel allein in einer anderen Szene, Blick auf ihm). Damit kann das Ziel durch ein
            Bild des Objekts genannt werden statt durch seine Farbe.
    gazeshape / gazeshapeheld  drei Koerper gleicher Farbe und verschiedener Form (Wuerfel, L, U, T, Kreuz;
            held: einer ist das Y, das im Training nie vorkommt), beliebig gedreht; refs uint8
            [N, 3, 2, 3, 16, 16]: je Koerper ZWEI Zeigebilder. Die Adresse muss hier die FORM tragen.
            cands uint8 [N, 3, 3, 16, 16]: dieselbe Suchszene, der Blick auf jedem der drei Koerper
            (Anschauen und Vergleichen: ist das, was ich gerade ansehe, das Gezeigte?).
    reach   Hand und roter Wuerfel sind im Bild. (dx, dy) = Zelle des Wuerfels - Zelle des Greifpunkts.
Die Etiketten kommen aus dem Simulator (Projektion der wahren Orte) und gehen NUR in die Etiketten, nie ins
Bild. Train und Test stammen aus getrennten Szenen (getrennte Zufallsstroeme), nie zeilenweise geteilt.
Ausgabe je Aufgabe und Teil: <task>_<split>.npz mit obs uint8 [N, 3, 16, 16], target int8 [N, 2] (dx, dy),
gaze float32 [N, 2] (Blickpunkt in Pixeln), cells int8 [N, 4] (Spalte, Zeile der Hand bzw. Bezugszelle, dann des
Wuerfels; nur fuer Diagnosen, z. B. ob ein Netz die Hand oder den Wuerfel nicht findet).
Kein Lernzustand wird gelesen oder geschrieben; der Lauf beruehrt act23 nicht.
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mujoco  # noqa: E402

from pc_cvnn.pc_act14 import ARM_JOINTS, HOME, REACH_XY, BracketArmSim  # noqa: E402
from pc_cvnn.pc_act18 import F, HEX_DY, _warp, _warp_spacing, hex_sample, patch_mean  # noqa: E402

RES, CAM, K = 240, "overview", 4
OBJECTS = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
TARGET = "obj_red"
CTR = (F - 1) / 2.0


def cell_px(gaze):
    """Pixelorte aller F x F Abtastpunkte der Fovea [F, F, 2] (x, y) - dieselbe Geometrie wie hex_sample."""
    out = np.zeros((F, F, 2))
    for r in range(F):
        for c in range(F):
            out[r, c] = (gaze[0] + _warp(c + 0.5 * (r & 1) - CTR) * K, gaze[1] + _warp(r - CTR) * K * HEX_DY)
    return out


def nearest_cell(gaze, px):
    """Zelle (r, c), deren Abtastpunkt dem Pixel am naechsten liegt, und der Abstand dorthin in Pixeln."""
    d = np.linalg.norm(cell_px(gaze) - np.asarray(px), axis=-1)
    r, c = np.unravel_index(int(d.argmin()), d.shape)
    return int(r), int(c), float(d[r, c])


class Scene:
    def __init__(self):
        self.sim = BracketArmSim(render_wh=(RES, RES))
        self.cid = mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_CAMERA, CAM)
        self.f = (RES / 2) / np.tan(np.radians(self.sim.m.cam_fovy[self.cid]) / 2)
        self.jlo = np.array([self.sim.m.jnt_range[self.sim._jid(j)][0] for j in ARM_JOINTS])
        self.jhi = np.array([self.sim.m.jnt_range[self.sim._jid(j)][1] for j in ARM_JOINTS])

    def project(self, w):
        """Weltpunkt -> Pixel (x, y) der Kamera (Lochkamera: Blick entlang -z, x rechts, y oben)."""
        p = self.sim.d.cam_xmat[self.cid].reshape(3, 3).T @ (np.asarray(w) - self.sim.d.cam_xpos[self.cid])
        return np.array([RES / 2 + self.f * p[0] / -p[2], RES / 2 - self.f * p[1] / -p[2]])

    def set_arm(self, q):
        s = self.sim
        q = np.clip(q, self.jlo, self.jhi)
        for j, v in zip(ARM_JOINTS, q):
            s.d.qpos[s.jqadr[j]] = v
            s.d.ctrl[s.act[j]] = v
        mujoco.mj_forward(s.m, s.d)

    def arm(self):
        return np.array([self.sim.d.qpos[self.sim.jqadr[j]] for j in ARM_JOINTS])

    def layout(self, rng):
        """Objekte an zufaellige, nicht ueberlappende Orte (Mindestabstand 45 mm), zufaellige Lage."""
        s = self.sim
        s.reset_home()
        placed = []
        for o in OBJECTS:
            for _ in range(200):
                p = rng.uniform(REACH_XY[0], REACH_XY[1])
                if all(np.linalg.norm(p - q) > 0.045 for q in placed):
                    break
            placed.append(p)
            s.set_object(o, p, z=0.012, yaw=float(rng.uniform(0, np.pi)))
        mujoco.mj_forward(s.m, s.d)

    def reach_kinematic(self, xyz, iters=60):
        """Greifpunkt kinematisch (ohne Physik, die Objekte bleiben liegen) an einen Weltpunkt fuehren."""
        s = self.sim
        for _ in range(iters):
            err = np.asarray(xyz) - s.grasp_pos()
            if np.linalg.norm(err) < 0.002:
                break
            J = s.site_jacobian()
            dq = J.T @ np.linalg.solve(J @ J.T + 0.02 * np.eye(3), err)
            m = float(np.max(np.abs(dq)))
            self.set_arm(self.arm() + dq * min(1.0, 0.15 / max(m, 1e-9)))
        return float(np.linalg.norm(np.asarray(xyz) - s.grasp_pos()))

    def render_fine(self):
        """Dieselbe Szene mit doppelter Kameraaufloesung (2 * RES): eigener Simulator, Zustand und Farben
        werden vom ersten uebernommen. Pixelorte sind dort doppelt so gross."""
        if not hasattr(self, "fine"):
            self.fine = BracketArmSim(render_wh=(2 * RES, 2 * RES))
        f = self.fine
        f.m.geom_rgba[:] = self.sim.m.geom_rgba
        f.d.qpos[:] = self.sim.d.qpos
        mujoco.mj_forward(f.m, f.d)
        return f.render(CAM)

    def fovea(self, gaze):
        img = self.sim.render(CAM)
        cells = hex_sample(img, gaze, K)[:, :, 1:]                       # F, F, 3 in 0..1
        return np.round(cells * 255).astype(np.uint8).transpose(2, 0, 1)


def fine_sample(img, gaze, n):
    """(n * F) x (n * F) Zellen ueber DASSELBE Blickfeld wie die Fovea, also n-fach dichter (gleiche Verzerrung
    zum Rand hin). img: Bild mit doppelter Aufloesung, gaze in dessen Pixeln."""
    N, k = n * F, 2 * K
    out, ctr = np.zeros((N, N, 3)), (N - 1) / 2.0
    for r in range(N):
        ir = (r - ctr) / n
        cy, sy = gaze[1] + _warp(ir) * k * HEX_DY, _warp_spacing(ir) * k * HEX_DY / n
        for c in range(N):
            ic = (c + 0.5 * (r & 1) - ctr) / n
            half = max(1, int(round(0.25 * (_warp_spacing(ic) * k / n + sy))))
            out[r, c] = patch_mean(img, gaze[0] + _warp(ic) * k, cy, half)
    return np.round(out * 255).astype(np.uint8).transpose(2, 0, 1)


def sample_shapeview(sc, rng):
    """AUFLOESUNG: drei Koerper gleicher Farbe und verschiedener Form (wie gazeshape), der Blick liegt auf
    einem davon (bis +-1 Zelle daneben). Etikett = seine Form (cells[0], Index in SHAPES). Dasselbe in vier
    Abtastungen: obs = Fovea wie bisher (16 x 16, 4 px je Zelle); z2 / z4 = 16 x 16 mit doppelter / vierfacher
    Vergroesserung (kleineres Blickfeld); f32 = 32 x 32 ueber das Blickfeld von obs (doppelt so dicht).
    z2, z4, f32 stammen aus einem Bild mit doppelter Kameraaufloesung."""
    import colorsys
    bodies = [SHAPES[i] for i in rng.permutation(N_TRAIN_SHAPES)][:3]
    while True:
        h = float(rng.uniform(0, 1))
        if not 0.78 <= h <= 0.92:
            break
    rgb = np.array(colorsys.hsv_to_rgb(h, float(rng.uniform(0.6, 1.0)), float(rng.uniform(0.7, 1.0))), np.float32)
    for o in SHAPES:
        _paint(sc, o, rgb)
    _place(sc, rng, bodies)
    gaze = sc.project(sc.sim.obj_pos(bodies[0])) + rng.uniform(-K, K, size=2)
    if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
        return None
    big = sc.render_fine()
    z2 = np.round(hex_sample(big, 2 * gaze, K)[:, :, 1:] * 255).astype(np.uint8).transpose(2, 0, 1)
    z4 = np.round(hex_sample(big, 2 * gaze, K / 2)[:, :, 1:] * 255).astype(np.uint8).transpose(2, 0, 1)
    return sc.fovea(gaze), (0, 0), gaze, (SHAPES.index(bodies[0]),), {"z2": z2, "z4": z4,
                                                                      "f32": fine_sample(big, 2 * gaze, 2)}


def sample_shapeedge(sc, rng):
    """AUFLOESUNG AM RAND: wie shapeview, aber der Koerper liegt irgendwo im Blickfeld, bis 7 Zellen neben der
    Mitte (ab 5 Zellen werden die Zellen groeber), und er ist der einzige im Blickfeld. cells = (Form, Ring), Ring = max(|Spalte|, |Zeile|) des
    Koerpers relativ zur Mitte, gerundet. obs = Fovea wie bisher, f32 = 32 x 32 ueber dasselbe Blickfeld."""
    r = sample_shapeview(sc, rng)                                        # malt und stellt die Szene
    if r is None:
        return None
    body = SHAPES[r[3][0]]
    off = rng.uniform(-7.0, 7.0, size=2)
    gaze = sc.project(sc.sim.obj_pos(body)) - np.array([_warp(off[0]) * K, _warp(off[1]) * K * HEX_DY])
    if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
        return None
    for o in SHAPES:                                                     # nur EIN Koerper im Blickfeld, sonst
        d = np.abs(sc.project(sc.sim.obj_pos(o)) - gaze)                 # ist offen, welcher gemeint ist
        if o != body and d[0] < 16 * K and d[1] < 16 * K * HEX_DY:
            return None
    big = sc.render_fine()
    return sc.fovea(gaze), (0, 0), gaze, (r[3][0], int(round(np.abs(off).max()))), {
        "f32": fine_sample(big, 2 * gaze, 2)}


def sample_gaze(sc, rng):
    sc.layout(rng)
    home = np.array([HOME[j] for j in ARM_JOINTS])
    sc.set_arm(home + rng.uniform(-0.25, 0.25, size=len(home)))          # Arm sichtbar, Stellung variiert
    px = sc.project(sc.sim.obj_pos(TARGET))
    r, c = (int(x) for x in rng.integers(0, F, size=2))                  # Zelle, in der der Wuerfel liegen soll
    gaze = px - np.array([_warp(c + 0.5 * (r & 1) - CTR) * K, _warp(r - CTR) * K * HEX_DY])
    if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
        return None
    return sc.fovea(gaze), (c - F // 2, r - F // 2), gaze, (c, r, c, r)


def sample_gazemulti(sc, rng):
    """Wie gaze, aber alle drei Wuerfel muessen im Blickfeld liegen; cells = Schritt zur Mitte fuer rot, gruen,
    blau (je dx, dy), danach L und U (Koerperursprung; -128, wenn ausserhalb). Damit lassen sich bei GLEICHEN
    Bildern verschiedene Ziele abfragen. Die Datei traegt ausserdem colors [5, 3]: die Farbe jedes Koerpers (rgba
    seiner ersten Geometrie) als moegliche stetige Adresse des Ziels."""
    r = sample_gaze(sc, rng)
    if r is None:
        return None
    img, tgt, gaze, _ = r
    cells = list(tgt)
    for o in ("obj_green", "obj_blue"):
        ro, co, dist = nearest_cell(gaze, sc.project(sc.sim.obj_pos(o)))
        if dist > 2 * K:
            return None
        cells += [co - F // 2, ro - F // 2]
    for o in ("obj_L", "obj_U"):                                         # Formen: nur mitgefuehrt, -128 = nicht im Bild
        ro, co, dist = nearest_cell(gaze, sc.project(sc.sim.obj_pos(o)))
        cells += [co - F // 2, ro - F // 2] if dist <= 2 * K else [-128, -128]
    return img, tgt, gaze, tuple(cells)


CUBES = ["obj_red", "obj_green", "obj_blue"]
HELD = (0.25, 0.40)            # zurueckgehaltenes Farbton-Band (gruen): nie im Training, nur in gazecolorheld
AVOID = [(0.78, 0.92), (0.04, 0.14), (0.46, 0.56)]   # Zielscheiben (magenta), L (orange), U (cyan)


def _hue_ok(h, held):
    if any(lo <= h <= hi for lo, hi in AVOID):
        return False
    return (HELD[0] <= h <= HELD[1]) == held


def _hues(rng, n_held):
    """Drei Farbtoene mit Mindestabstand 0.08 (zyklisch); die ersten n_held aus dem zurueckgehaltenen Band."""
    import colorsys
    while True:
        hs = []
        for i in range(3):
            while True:
                h = float(rng.uniform(0, 1))
                if _hue_ok(h, i < n_held):
                    break
            hs.append(h)
        d = [min(abs(a - b), 1 - abs(a - b)) for a in hs for b in hs if a is not b]
        if min(d) >= 0.08:
            break
    order = rng.permutation(3)
    cols = [colorsys.hsv_to_rgb(hs[i], float(rng.uniform(0.6, 1.0)), float(rng.uniform(0.7, 1.0))) for i in order]
    return np.array(cols, np.float32), int(np.flatnonzero(order == 0)[0])


def _sample_gazecolor(sc, rng, n_held):
    """Wie gazemulti, aber die drei Wuerfel bekommen je Szene zufaellige Farben. Rueckgabe-Zellen: Schritt zur
    Mitte je Wuerfel, danach die drei Farben (RGB x 255) und der Index des Wuerfels mit zurueckgehaltenem
    Farbton (nur bei n_held = 1 von Bedeutung)."""
    m = sc.sim.m
    cols, held = _hues(rng, n_held)
    for o, c in zip(CUBES, cols):
        m.geom_rgba[m.body_geomadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, o)], :3] = c
    r = sample_gazemulti(sc, rng)
    if r is None:
        return None
    img, tgt, gaze, cells = r
    return img, tgt, gaze, tuple(cells[:6]) + tuple(int(round(255 * v)) - 128 for v in cols.ravel()) + (held,)


def _show(sc, rng, k):
    """Den Wuerfel k ALLEIN zeigen: neue Szene, die anderen Koerper weit weg geparkt, Arm in neuer Stellung, der
    Blick auf dem Wuerfel (bis +-1 Zelle daneben). Das ist das Bild, mit dem man dem Netz sagt, WAS gemeint
    ist - aus einer anderen Szene als die Suchaufgabe, damit nur das Objekt selbst die Adresse tragen kann."""
    s = sc.sim
    s.reset_home()
    for i, o in enumerate(OBJECTS):
        s.set_object(o, [0.58 + 0.05 * i, -0.6])
    s.set_object(CUBES[k], rng.uniform(REACH_XY[0], REACH_XY[1]), z=0.012, yaw=float(rng.uniform(0, np.pi)))
    home = np.array([HOME[j] for j in ARM_JOINTS])
    sc.set_arm(home + rng.uniform(-0.25, 0.25, size=len(home)))
    px = sc.project(s.obj_pos(CUBES[k]))
    return sc.fovea(px + rng.uniform(-K, K, size=2))


def _sample_gazecolorref(sc, rng, n_held):
    r = _sample_gazecolor(sc, rng, n_held)                               # setzt die Farben, rendert die Suchszene
    if r is None:
        return None
    refs = np.stack([_show(sc, rng, k) for k in range(3)])               # danach: je Wuerfel ein Zeigebild
    return (*r, refs)


def sample_gazecolorref(sc, rng):
    return _sample_gazecolorref(sc, rng, 0)


def sample_gazecolorrefheld(sc, rng):
    return _sample_gazecolorref(sc, rng, 1)


def sample_gazecolor(sc, rng):
    return _sample_gazecolor(sc, rng, 0)


def sample_gazecolorheld(sc, rng):
    return _sample_gazecolor(sc, rng, 1)


SHAPES = ["obj_red", "obj_L", "obj_U", "obj_T", "obj_X", "obj_Y"]     # Wuerfel, L, U, T, Kreuz, Y
N_TRAIN_SHAPES = 5                                                    # das Y ist die zurueckgehaltene Form
ALL_BODIES = SHAPES + ["obj_green", "obj_blue"]


def _paint(sc, body, rgb):
    m = sc.sim.m
    b = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body)
    m.geom_rgba[m.body_geomadr[b]:m.body_geomadr[b] + m.body_geomnum[b], :3] = rgb


def _place(sc, rng, bodies):
    """Alle Koerper wegparken, die genannten an zufaellige Orte (Mindestabstand 60 mm) in beliebiger Drehung."""
    s = sc.sim
    s.reset_home()
    for i, o in enumerate(ALL_BODIES):
        s.set_object(o, [0.50 + 0.07 * i, -0.6])
    placed = []
    for o in bodies:
        for _ in range(200):
            q = rng.uniform(REACH_XY[0], REACH_XY[1])
            if all(np.linalg.norm(q - r) > 0.06 for r in placed):
                break
        placed.append(q)
        s.set_object(o, q, z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
    home = np.array([HOME[j] for j in ARM_JOINTS])
    sc.set_arm(home + rng.uniform(-0.25, 0.25, size=len(home)))


def _sample_gazeshape(sc, rng, held, inner=False):
    """Drei Koerper VERSCHIEDENER Form und GLEICHER Farbe (ein zufaelliger Farbton je Szene): nur die Form
    unterscheidet sie. Dazu je Koerper ZWEI Zeigebilder (allein, andere Szene, andere Drehung).
    held: einer der drei ist das Y, das im Training nie vorkommt.
    cells: Schritt zur Mitte je Koerper (6), Farbe (3, RGB x 255 - 128), Form je Koerper (3, Index in SHAPES),
    Index des Y unter den dreien (bzw. 0).
    inner: alle drei Koerper liegen im voll aufgeloesten Teil der Fovea (hoechstens INNER_RING Zellen neben der
    Mitte); der Blick liegt dazu nahe am Schwerpunkt der drei."""
    import colorsys
    pool = [SHAPES[i] for i in rng.permutation(N_TRAIN_SHAPES)]
    bodies = [SHAPES[5]] + pool[:2] if held else pool[:3]
    bodies = [bodies[i] for i in rng.permutation(3)]
    while True:
        h = float(rng.uniform(0, 1))
        if not 0.78 <= h <= 0.92:                                         # Magenta gehoert den Zielscheiben
            break
    rgb = np.array(colorsys.hsv_to_rgb(h, float(rng.uniform(0.6, 1.0)), float(rng.uniform(0.7, 1.0))), np.float32)
    for o in SHAPES:
        _paint(sc, o, rgb)
    _place(sc, rng, bodies)
    px = sc.project(sc.sim.obj_pos(bodies[0]))
    if inner:
        gaze = np.mean([sc.project(sc.sim.obj_pos(o)) for o in bodies], 0) + rng.uniform(-3 * K, 3 * K, size=2)
        if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
            return None
        cells = []
        for o in bodies:
            ro, co, dist = nearest_cell(gaze, sc.project(sc.sim.obj_pos(o)))
            if dist > 2 * K or max(abs(co - F // 2), abs(ro - F // 2)) > INNER_RING:
                return None
            cells += [co - F // 2, ro - F // 2]
    else:
        r, c = (int(x) for x in rng.integers(0, F, size=2))
        gaze = px - np.array([_warp(c + 0.5 * (r & 1) - CTR) * K, _warp(r - CTR) * K * HEX_DY])
        if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
            return None
        cells = [c - F // 2, r - F // 2]
        for o in bodies[1:]:
            ro, co, dist = nearest_cell(gaze, sc.project(sc.sim.obj_pos(o)))
            if dist > 2 * K:
                return None
            cells += [co - F // 2, ro - F // 2]
    img = sc.fovea(gaze)
    f32 = fine_sample(sc.render_fine(), 2 * gaze, 2)                      # Suchszene doppelt so dicht (ohne rng)
    # ANSCHAUEN: dieselbe Szene, der Blick nacheinander auf jedem der drei Koerper (bis +-1 Zelle daneben)
    cands = np.stack([sc.fovea(sc.project(sc.sim.obj_pos(o)) + rng.uniform(-K, K, size=2)) for o in bodies])
    refs = []
    for o in bodies:                                                     # danach: zwei Zeigebilder je Koerper
        views = []
        for _ in range(2):
            _place(sc, rng, [o])
            views.append(sc.fovea(sc.project(sc.sim.obj_pos(o)) + rng.uniform(-K, K, size=2)))
        refs.append(np.stack(views))
    cells += [int(round(255 * v)) - 128 for v in rgb] + [SHAPES.index(o) for o in bodies]
    cells += [bodies.index(SHAPES[5]) if held else 0]
    return img, tuple(cells[:2]), gaze, tuple(cells), {"refs": np.stack(refs), "cands": cands, "f32": f32}


def sample_gazeshape(sc, rng):
    return _sample_gazeshape(sc, rng, False)


def sample_gazeshapeheld(sc, rng):
    return _sample_gazeshape(sc, rng, True)


INNER_RING = 5


def sample_gazeshapein(sc, rng):
    return _sample_gazeshape(sc, rng, False, inner=True)


def sample_gazeshapeinheld(sc, rng):
    return _sample_gazeshape(sc, rng, True, inner=True)


def sample_reach(sc, rng):
    sc.layout(rng)
    obj = sc.sim.obj_pos(TARGET)
    aim = np.array([*(obj[:2] + rng.uniform(-0.05, 0.05, size=2)), rng.uniform(0.03, 0.08)])
    if sc.reach_kinematic(aim) > 0.01:
        return None
    hand, px = sc.project(sc.sim.grasp_pos()), sc.project(obj)
    rh, ch = (int(x) for x in rng.integers(3, F - 3, size=2))            # Zelle, in der die Hand liegen soll
    gaze = hand - np.array([_warp(ch + 0.5 * (rh & 1) - CTR) * K, _warp(rh - CTR) * K * HEX_DY])
    if not (0 <= gaze[0] < RES and 0 <= gaze[1] < RES):
        return None
    ro, co, dist = nearest_cell(gaze, px)
    dx, dy = co - ch, ro - rh
    if dist > 2 * K or not (-8 <= dx <= 7 and -8 <= dy <= 7):            # Wuerfel ausserhalb des Blickfelds
        return None
    return sc.fovea(gaze), (dx, dy), gaze, (ch, rh, co, ro)


def collect(fn, n, seed):
    sc, rng = Scene(), np.random.default_rng(seed)
    obs, tgt, gz, cl, ex, tried, t0 = [], [], [], [], [], 0, time.time()
    while len(obs) < n:
        tried += 1
        r = fn(sc, rng)
        if r is None:
            continue
        obs.append(r[0]); tgt.append(r[1]); gz.append(r[2]); cl.append(r[3])
        if len(r) > 4:
            ex.append(r[4] if isinstance(r[4], dict) else {"refs": r[4]})
        if len(obs) % 2000 == 0:
            print(f"  {len(obs)}/{n}  ({tried} Versuche, {time.time() - t0:.0f} s)", flush=True)
    extra = {k: np.stack([e[k] for e in ex]) for k in ex[0]} if ex else {}
    return np.stack(obs), np.array(tgt, np.int8), np.array(gz, np.float32), np.array(cl, np.int8), extra


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join("..", "NetResearch", "data", "robot"))
    ap.add_argument("--n-train", type=int, default=20000)
    ap.add_argument("--n-test", type=int, default=4000)
    ap.add_argument("--tasks", nargs="+", default=["gaze", "reach"])
    ap.add_argument("--part", type=int, default=0, help="Teil k eines in mehreren Prozessen erzeugten Satzes: "
                    "Seed + 100 * k, Dateiname <task>_<split>_p<k>.npz (k = 0: wie bisher)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fns = {"gaze": sample_gaze, "reach": sample_reach, "gazemulti": sample_gazemulti,
           "gazecolor": sample_gazecolor, "gazecolorheld": sample_gazecolorheld,
           "gazecolorref": sample_gazecolorref, "gazecolorrefheld": sample_gazecolorrefheld,
           "gazeshape": sample_gazeshape, "gazeshapeheld": sample_gazeshapeheld, "shapeview": sample_shapeview,
           "shapeedge": sample_shapeedge,
           "gazeshapein": sample_gazeshapein, "gazeshapeinheld": sample_gazeshapeinheld}
    for task in a.tasks:
        ti = list(fns).index(task)                               # Seed haengt an der Aufgabe, nicht an der Reihenfolge
        for split, n, seed in (("train", a.n_train, 1000 + ti + 100 * a.part),
                               ("test", a.n_test, 9000 + ti + 100 * a.part)):
            if n == 0:
                continue
            print(f"{task} {split}: {n} Beispiele, Seed {seed}", flush=True)
            obs, tgt, gz, cl, extra = collect(fns[task], n, seed)
            m = Scene().sim.m
            cols = np.array([m.geom_rgba[m.body_geomadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, o)]][:3]
                             for o in OBJECTS], np.float32)
            np.savez_compressed(os.path.join(a.out, f"{task}_{split}" + (f"_p{a.part}" if a.part else "") + ".npz"), obs=obs, target=tgt, gaze=gz, cells=cl,
                                colors=cols, **extra)


if __name__ == "__main__":
    main()
