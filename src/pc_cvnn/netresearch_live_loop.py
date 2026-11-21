"""Bruecke Stufe b (klein): die Blickschleife mit drei Zielen aus NetResearch LIVE im MuJoCo-Simulator, mit
bewegtem Arm. Pruefstand-Netze steuern den Blick; nach jedem Ziel faehrt der Arm ueber den Koerper, auf dem der
Blick liegt - die Hand ist danach im Bild, waehrend das naechste Ziel gesucht wird. Das kommt im Pruefstand nicht
vor (dort steht der Arm abseits; Bilder sind fest). Gefragt ist, ob der Pruefstand das Live-Ergebnis vorhersagt.

    # Netz-Seite (NetResearch-Umgebung mit torch):
    ..\\NetResearch\\.venv\\Scripts\\python.exe ..\\NetResearch\\scripts\\policy_server.py --port 6071
    # Simulator-Seite (diese Umgebung mit mujoco):
    .venv\\Scripts\\python.exe src\\pc_cvnn\\netresearch_live_loop.py --nets sp4:robot_loop_three_f32_24k:0 ...

Je Szene (eigene Saat, nicht die des Exports): drei Koerper gleicher Farbe, verschiedener Form (wie gazeshapec:
alle im inneren Ring, Ort = Flaechenschwerpunkt), Blick nahe ihrem Schwerpunkt, Arm in zufaelliger Ruhelage. Je
Koerper ein Zeigebild (der Koerper allein, andere Lage). Alle 12 Zielfolgen ohne direkte Wiederholung (A, B, C und
A, B, A), je Folge: drei Hinweis-Schritte mit den Zeigebildern, dann 3 Blickschritte je Ziel. Zwei Bedingungen:
    static  der Arm bleibt in der Ruhelage (entspricht dem Pruefstand, aber frische Szenen, live gerendert)
    live    nach den 3 Schritten eines Ziels fuehrt der Arm den Greifpunkt kinematisch (ohne Physik, die Koerper
            bleiben liegen) 5 cm ueber den Koerper, der dem Blickpunkt am naechsten ist, und bleibt dort, bis das
            naechste Ziel erledigt ist
    away    Kontrolle zu live: nach dem ersten Ziel faehrt der Arm 5 cm ueber eine freie Tischstelle derselben Szene
            (Hand im Bild im inneren Ring, im Bild moeglichst weit von allen Koerpern) und bleibt dort; die Hand ist im Bild, verdeckt
            aber keinen Koerper
Die Fovea (32 x 32, doppelt dichte Abtastung) wird bei jedem Schritt aus dem aktuellen Kamerabild neu abgetastet,
mit der Geometrie von NetResearch (netresearch/tasks/fovea.py, bitgenau zum Export). Gemessen wie in
NetResearch finds_loop_eval.py: am Ende jedes Ziels nahe (hoechstens eine Zelle) am Ziel, alle drei nahe.
Kein Lernzustand wird gelesen oder geschrieben; act23 wird nicht beruehrt.
-> ../NetResearch/results/robot_live_loop.jsonl (eine Zeile je Netz und Bedingung)
"""
import argparse
import importlib.util
import itertools
import json
import os
import sys
import time
from multiprocessing.connection import Client

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mujoco  # noqa: E402

import pc_cvnn.export_netresearch as ex  # noqa: E402

NR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "NetResearch"))
_spec = importlib.util.spec_from_file_location("nr_fovea", os.path.join(NR, "netresearch", "tasks", "fovea.py"))
fv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fv)

G, SEG = 3, 3
ORDERS = [o for o in itertools.product(range(3), repeat=G) if all(x != y for x, y in zip(o, o[1:]))]
HOVER = 0.05


def send(conn, head, arrays=None):
    arrays = arrays or {}
    head = dict(head, arrays=[[k, str(v.dtype), list(v.shape)] for k, v in arrays.items()])
    conn.send_bytes(json.dumps(head).encode())
    for v in arrays.values():
        conn.send_bytes(np.ascontiguousarray(v).tobytes())


def recv(conn):
    head = json.loads(conn.recv_bytes().decode())
    arrays = {}
    for name, dtype, shape in head.get("arrays", []):
        arrays[name] = np.frombuffer(conn.recv_bytes(), dtype=dtype).reshape(shape)
    return head, arrays


def ask(conn, head, arrays=None):
    send(conn, head, arrays)
    h, a = recv(conn)
    if not h.get("ok"):
        raise RuntimeError(h)
    return h, a


def measure(gaze, pos, k):
    """Wie NetResearch finds_loop_eval.measure: Schritt zum Koerper k, Pixelabstand der Mitte, falscher Koerper?"""
    c = fv.centre_px(gaze)
    dist = np.linalg.norm(pos - c, axis=-1)
    dx, dy, _ = fv.nearest_cell(gaze, pos[k])
    return dx, dy, float(dist[k]), bool(dist.argmin() != k and dist[k] > 8.0)


def inside(g):
    return 0 <= g[0] < fv.RES and 0 <= g[1] < fv.RES


def make_scene(sc, rng):
    """Suchszene wie gazeshapec (ohne gehaltene Form), dazu je Koerper ein Zeigebild. Gibt den Zustand der
    Suchszene (qpos), Blick, Pixelorte, Weltorte und Zeigebilder zurueck, oder None."""
    import colorsys
    pool = [ex.SHAPES[i] for i in rng.permutation(ex.N_TRAIN_SHAPES)]
    bodies = [pool[i] for i in rng.permutation(3)]
    while True:
        h = float(rng.uniform(0, 1))
        if not 0.78 <= h <= 0.92:
            break
    rgb = np.array(colorsys.hsv_to_rgb(h, float(rng.uniform(0.6, 1.0)), float(rng.uniform(0.7, 1.0))), np.float32)
    for o in ex.SHAPES:
        ex._paint(sc, o, rgb)
    ex._place(sc, rng, bodies)
    world = [ex.centroid(sc, o) for o in bodies]
    pos = np.array([sc.project(w) for w in world], np.float32)
    gaze = pos.mean(0) + rng.uniform(-3 * ex.K, 3 * ex.K, size=2)
    if not inside(gaze):
        return None
    for p in pos:
        ro, co, dist = ex.nearest_cell(gaze, p)
        if dist > 2 * ex.K or max(abs(co - ex.F // 2), abs(ro - ex.F // 2)) > ex.INNER_RING:
            return None
    qpos = sc.sim.d.qpos.copy()
    refs = []
    for o in bodies:
        ex._place(sc, rng, [o])
        refs.append(sc.fovea(sc.project(ex.centroid(sc, o)) + rng.uniform(-ex.K, ex.K, size=2)))
    sc.sim.d.qpos[:] = qpos
    mujoco.mj_forward(sc.sim.m, sc.sim.d)
    world = np.array(world)
    m, rr = world[:, :2].mean(0), np.linalg.norm(world[:, :2] - world[:, :2].mean(0), axis=1).max()
    best, free = -1.0, None
    for f in (1.0, 1.3, 0.7):
        for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
            w = np.array([m[0] + f * rr * np.cos(a), m[1] + f * rr * np.sin(a), world[:, 2].mean()])
            hp = sc.project(w + np.array([0, 0, HOVER]))                       # Pixelort der schwebenden Hand
            ro, co, _ = ex.nearest_cell(gaze, hp)
            if max(abs(co - ex.F // 2), abs(ro - ex.F // 2)) > ex.INNER_RING:
                continue
            d = float(np.linalg.norm(pos - hp, axis=1).min())
            if d > best:
                best, free = d, w
    if free is None:
        return None
    return {"qpos": qpos, "gaze": gaze, "pos": pos, "world": world, "refs": np.stack(refs), "free": free,
            "free_dist": best, "rgb": rgb}


def show_scene(sc, s):
    """Szene herstellen: Lage (qpos) und Farbe. Die Farbe steht nicht in qpos; ohne Neu-Malen haette jede Szene
    die Farbe der zuletzt erzeugten (bis 2026-11-21 so gemessen, Zeigebilder dagegen in der eigenen Farbe)."""
    for o in ex.SHAPES:
        ex._paint(sc, o, s["rgb"])
    sc.sim.d.qpos[:] = s["qpos"]
    mujoco.mj_forward(sc.sim.m, sc.sim.d)


def view(sc, gaze):
    big = sc.render_fine()
    return fv.sample_fine(fv.integral(big), gaze)


def run_scene(sc, s, conn, cond):
    """Alle 12 Folgen einer Szene im Gleichschritt. conn None = Orakel. Gibt seg_near [12, G] zurueck."""
    n = len(ORDERS)
    order = np.array(ORDERS)
    show_scene(sc, s)
    gaze = np.repeat(s["gaze"][None].astype(float), n, 0)
    arm = np.repeat(s["qpos"][None], n, 0)                                     # qpos je Lauf (Arm)
    if conn is not None:
        ask(conn, {"op": "cue"}, {"refs": np.stack([s["refs"][order[:, k]] for k in range(G)])})
    near = np.zeros((n, G), bool)
    out = np.zeros(n, bool)                                                    # Blick hat das Bild verlassen
    prev = np.full((n, G), -1)                                                 # Koerper am Blick am Ende der Strecke
    for t in range(G * SEG):
        j = t // SEG
        if conn is None:
            steps = np.array([measure(gaze[p], s["pos"], order[p, j])[:2] for p in range(n)], np.int64)
        else:
            if cond == "static":
                big = None
                sc.sim.d.qpos[:] = arm[0]
                mujoco.mj_forward(sc.sim.m, sc.sim.d)
                sat = fv.integral(sc.render_fine())
                views = np.stack([fv.sample_fine(sat, gaze[p]) for p in range(n)])
            else:                                                              # ein Bild je Armstellung
                sats = {}
                for p in range(n):
                    key = arm[p].tobytes()
                    if key not in sats:
                        sc.sim.d.qpos[:] = arm[p]
                        mujoco.mj_forward(sc.sim.m, sc.sim.d)
                        sats[key] = fv.integral(sc.render_fine())
                views = np.stack([fv.sample_fine(sats[arm[p].tobytes()], gaze[p]) for p in range(n)])
            _, a = ask(conn, {"op": "step"}, {"views": views})
            steps = a["steps"]
        for p in range(n):                                                     # wie finds_loop_eval: ein Schritt
            if out[p]:                                                         # aus dem Bild beendet den Lauf, alle
                continue                                                       # spaeteren Ziele zaehlen als verfehlt
            g = fv.shift(gaze[p], int(steps[p, 0]), int(steps[p, 1]))
            if inside(g):
                gaze[p] = g
            else:
                out[p] = True
        if (t + 1) % SEG == 0:
            for p in range(n):
                dx, dy = measure(gaze[p], s["pos"], order[p, j])[:2]
                near[p, j] = max(abs(dx), abs(dy)) <= 1 and not out[p]
                prev[p, j] = int(np.linalg.norm(s["pos"] - fv.centre_px(gaze[p]), axis=-1).argmin())
            if cond == "away" and j == 0:
                for p in range(n):
                    sc.sim.d.qpos[:] = arm[p]
                    mujoco.mj_forward(sc.sim.m, sc.sim.d)
                    sc.reach_kinematic(s["free"] + np.array([0, 0, HOVER]))
                    arm[p] = sc.sim.d.qpos.copy()
            if cond == "live" and j < G - 1:                                   # Arm ueber den angeblickten Koerper
                for p in range(n):
                    c = fv.centre_px(gaze[p])
                    k = int(np.linalg.norm(s["pos"] - c, axis=-1).argmin())
                    sc.sim.d.qpos[:] = arm[p]
                    mujoco.mj_forward(sc.sim.m, sc.sim.d)
                    sc.reach_kinematic(s["world"][k] + np.array([0, 0, HOVER]))
                    arm[p] = sc.sim.d.qpos.copy()
    return near, prev, out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nets", nargs="+", default=[], help="name:ckpt:seed (name = NetResearch-Modellname)")
    ap.add_argument("--scenes", type=int, default=150)
    ap.add_argument("--seed", type=int, default=77000)
    ap.add_argument("--port", type=int, default=6071)
    ap.add_argument("--conds", nargs="+", default=["static", "live"])
    ap.add_argument("--task", default="robot_loop_three_f32")
    ap.add_argument("--out", default=os.path.join(NR, "results", "robot_live_loop.jsonl"))
    a = ap.parse_args()
    sc, rng = ex.Scene(), np.random.default_rng(a.seed)
    scenes = []
    while len(scenes) < a.scenes:
        s = make_scene(sc, rng)
        if s is not None:
            scenes.append(s)
    print(f"{len(scenes)} Szenen", flush=True)
    conn = Client(("127.0.0.1", a.port), authkey=b"netresearch-live") if a.nets else None
    jobs = [("oracle", None)] + [(n, n.split(":")) for n in a.nets]
    with open(a.out, "a") as out:
        for label, spec in jobs:
            if spec is not None:
                ask(conn, {"op": "load", "task": a.task, "model": spec[0], "ckpt": spec[1], "seed": int(spec[2])})
            for cond in a.conds:
                t0 = time.time()
                res = [run_scene(sc, s, None if spec is None else conn, cond) for s in scenes]
                near = np.concatenate([r[0] for r in res])
                prev = np.concatenate([r[1] for r in res])
                n_out = int(np.concatenate([r[2] for r in res]).sum())
                # verfehlte Strecke j >= 1: Blick endet auf dem Koerper, auf dem er am Ende der Strecke davor lag
                stay = [round(float((prev[:, j] == prev[:, j - 1])[~near[:, j]].mean()), 4) if (~near[:, j]).any()
                        else None for j in range(1, G)]
                ret = np.tile(np.array(ORDERS)[:, 2] == np.array(ORDERS)[:, 0], len(scenes))
                row = {"task": a.task, "model": spec[0] if spec else "oracle", "ckpt": spec[1] if spec else None,
                       "seed": int(spec[2]) if spec else -1, "cond": cond, "scenes": len(scenes), "scene_seed": a.seed,
                       "near_goal": [round(float(x), 4) for x in near.mean(0)],
                       "near_all": round(float(near.all(1).mean()), 4),
                       "near_all_new": round(float(near.all(1)[~ret].mean()), 4),
                       "near_all_ret": round(float(near.all(1)[ret].mean()), 4),
                       "miss_stay_prev": stay, "out": n_out, "out_rule": "bench", "scene_colour": "own", "miss": [int((~near[:, j]).sum()) for j in range(G)]}
                out.write(json.dumps(row) + "\n")
                out.flush()
                print(f"{label:<45} {cond:<6} near_goal {row['near_goal']} near_all {row['near_all']:.3f} "
                      f"({time.time() - t0:.0f} s)", flush=True)
    if conn is not None:
        ask(conn, {"op": "quit"})


if __name__ == "__main__":
    main()
