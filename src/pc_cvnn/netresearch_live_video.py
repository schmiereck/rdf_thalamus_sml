"""Video der Blickschleife mit drei Zielen aus NetResearch im MuJoCo-Simulator: ein Netz (oder das Orakel), einzelne
Szenen und Zielfolgen, Bild fuer Bild. Gleiche Szenen, Regeln und Bedingungen wie netresearch_live_loop.py (dieselbe
Saat ergibt dieselben Szenen), nur ein Lauf statt zwoelf im Gleichschritt und mit Bildern statt Zahlen. Misst nichts
und schreibt keine Ergebnisse; act23 wird nicht beruehrt.

    # Netz-Seite (NetResearch-Umgebung mit torch):
    ..\\NetResearch\\.venv\\Scripts\\python.exe ..\\NetResearch\\scripts\\policy_server.py --port 6071
    # Simulator-Seite:
    .venv\\Scripts\\python.exe src\\pc_cvnn\\netresearch_live_video.py --net layer_s_sp4+cell+refl+rez3:robot_loop_three_f32_24k:0 ^
        --scenes 0 1 2 --cond live --out log\\video\\sp4_live.mp4

Links das Kamerabild (480 x 480) mit den Abtastpunkten der Fovea (gelb), der Mitte (rot), der Blickspur (weiss) und
dem gesuchten Koerper (gruener Ring). Rechts die drei Zeigebilder in der Reihenfolge der Folge (das aktuelle Ziel
umrandet, darunter getroffen / verfehlt), die aktuelle Fovea (32 x 32) und der Stand. Bewegt sich der Arm, wird die
Bewegung in Zwischenbildern gezeigt (fuer die Messung springt er). Ausgabe .gif (Pillow) oder .mp4 (ffmpeg).
"""
import argparse
import os
import shutil
import subprocess
import sys
from multiprocessing.connection import Client

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mujoco  # noqa: E402

import pc_cvnn.export_netresearch as ex  # noqa: E402
from pc_cvnn.netresearch_live_loop import (G, HOVER, ORDERS, SEG, ask, fv, inside, make_scene, measure,  # noqa: E402
                                           show_scene)

S = 2                                                                          # Pixel der Kamera -> Pixel im Video
PANEL = 260
NAMES = "ABC"


def font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_BIG, F_SMALL = font(18), font(14)


def thumb(chw, size):
    return Image.fromarray(np.ascontiguousarray(chw.transpose(1, 2, 0))).resize((size, size), Image.NEAREST)


def frame(sc, s, st):
    """Ein Bild: Kamera mit Einblendungen links, Stand rechts."""
    cam = Image.fromarray(sc.render_fine())
    d = ImageDraw.Draw(cam)
    for k, p in enumerate(s["pos"]):                                           # Koerper (Schwerpunkt)
        x, y = p * S
        r = 18 if k == st["target"] else 4
        d.ellipse([x - r, y - r, x + r, y + r], outline=(60, 230, 60) if k == st["target"] else (255, 255, 255),
                  width=3 if k == st["target"] else 1)
    if len(st["trail"]) > 1:
        d.line([tuple(c * S) for c in st["trail"]], fill=(255, 255, 255), width=1)
    for x, y in fv.cell_px(st["gaze"]).reshape(-1, 2) * S:                     # Abtastpunkte der Fovea
        d.point((x, y), fill=(255, 230, 0))
    cx, cy = fv.centre_px(st["gaze"]) * S
    d.line([cx - 9, cy, cx + 9, cy], fill=(255, 40, 40), width=2)
    d.line([cx, cy - 9, cx, cy + 9], fill=(255, 40, 40), width=2)
    img = Image.new("RGB", (cam.width + PANEL, cam.height), (24, 24, 28))
    img.paste(cam, (0, 0))
    d = ImageDraw.Draw(img)
    x0 = cam.width + 14
    d.text((x0, 10), st["label"], font=F_SMALL, fill=(230, 230, 230))
    d.text((x0, 30), f"{st['cond']}  Szene {st['scene']}  Folge {st['order_name']}", font=F_SMALL, fill=(230, 230, 230))
    for k in range(G):                                                         # Zeigebilder in Folgen-Reihenfolge
        x, y = x0 + k * 78, 60
        img.paste(thumb(s["refs"][st["order"][k]], 64), (x, y))
        if k == st["goal"]:
            d.rectangle([x - 3, y - 3, x + 66, y + 66], outline=(60, 230, 60), width=3)
        d.text((x + 26, y + 70), NAMES[st["order"][k]], font=F_SMALL, fill=(230, 230, 230))
        r = st["result"][k]
        if r is not None:
            d.text((x + 8, y + 88), "getroffen" if r else "verfehlt", font=F_SMALL,
                   fill=(60, 230, 60) if r else (255, 80, 80))
    d.text((x0, 180), "Fovea", font=F_SMALL, fill=(180, 180, 180))
    if st["view"] is not None:
        img.paste(thumb(st["view"], 128), (x0, 200))
    d.text((x0, 345), st["phase"], font=F_BIG, fill=(255, 255, 255))
    if st["note"]:
        d.text((x0, 372), st["note"], font=F_SMALL, fill=(200, 200, 200))
    return img


def move_arm(sc, target, n_frames, emit):
    """Arm kinematisch zum Ziel wie in der Messung; dazwischen n_frames gerenderte Zwischenstellungen."""
    q0 = sc.arm()
    sc.reach_kinematic(target)
    q1 = sc.arm()
    for i in range(1, n_frames + 1):
        sc.set_arm(q0 + (q1 - q0) * i / n_frames)
        emit()
    sc.set_arm(q1)


def record_run(sc, s, conn, cond, order, label, scene_id, arm_frames, hold):
    """Ein Lauf (eine Zielfolge) mit Bildern; Regeln wie run_scene in netresearch_live_loop.py."""
    show_scene(sc, s)
    frames = []
    st = {"label": label, "cond": cond, "scene": scene_id, "order": order,
          "order_name": " ".join(NAMES[k] for k in order), "goal": 0, "target": order[0],
          "result": [None] * G, "gaze": s["gaze"].astype(float).copy(), "view": None, "phase": "", "note": "",
          "trail": [fv.centre_px(s["gaze"])]}

    def emit(times=1):
        im = frame(sc, s, st)
        frames.extend([im] * times)

    if conn is not None:
        ask(conn, {"op": "cue"}, {"refs": np.stack([s["refs"][[order[k]]] for k in range(G)])})
    for k in range(G):                                                         # Hinweis-Schritte
        st.update(goal=k, target=order[k], phase=f"Hinweis {k + 1}: {NAMES[order[k]]}", note="Zeigebild merken")
        emit(hold)
    out = False
    for t in range(G * SEG):
        j = t // SEG
        st.update(goal=j, target=order[j], phase=f"Ziel {j + 1} ({NAMES[order[j]]}), Schritt {t % SEG + 1}/{SEG}",
                  note="")
        big = sc.render_fine()
        view = fv.sample_fine(fv.integral(big), st["gaze"])
        st["view"] = view
        if conn is None:
            step = measure(st["gaze"], s["pos"], order[j])[:2]
        else:
            _, a = ask(conn, {"op": "step"}, {"views": view[None]})
            step = a["steps"][0]
        emit()
        g = fv.shift(st["gaze"], int(step[0]), int(step[1]))
        if not inside(g):
            out = True
            st.update(note="Blick verlaesst das Bild: Lauf zu Ende")
            emit(hold)
            break
        st["gaze"] = g
        st["trail"].append(fv.centre_px(g))
        if (t + 1) % SEG == 0:
            dx, dy = measure(st["gaze"], s["pos"], order[j])[:2]
            st["result"][j] = max(abs(dx), abs(dy)) <= 1
            st.update(note="getroffen" if st["result"][j] else "verfehlt")
            emit(hold)
            if cond == "away" and j == 0:
                st.update(note="Arm faehrt an eine freie Stelle")
                move_arm(sc, s["free"] + np.array([0, 0, HOVER]), arm_frames, emit)
            if cond == "live" and j < G - 1:
                k = int(np.linalg.norm(s["pos"] - fv.centre_px(st["gaze"]), axis=-1).argmin())
                st.update(note=f"Arm faehrt ueber Koerper {NAMES[k]}")
                move_arm(sc, s["world"][k] + np.array([0, 0, HOVER]), arm_frames, emit)
    if out:
        for j in range(G):
            if st["result"][j] is None:
                st["result"][j] = False
    st.update(phase="alle drei getroffen" if all(st["result"]) else "Ende", note="")
    emit(2 * hold)
    return frames


def write(frames, path, fps):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if path.lower().endswith(".gif"):
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
        return
    ff = shutil.which("ffmpeg")
    if ff is None:
        raise SystemExit("ffmpeg nicht gefunden: .gif als Ausgabe waehlen")
    w, h = frames[0].size
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(fps), "-i", "-", "-vcodec", "libx264", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    for im in frames:
        p.stdin.write(im.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg fehlgeschlagen")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--net", default=None, help="name:ckpt:seed (ohne: Orakel, ohne policy_server)")
    ap.add_argument("--task", default="robot_loop_three_f32")
    ap.add_argument("--port", type=int, default=6071)
    ap.add_argument("--seed", type=int, default=77000, help="Szenen-Saat (77000 = die des Live-Tests)")
    ap.add_argument("--scenes", type=int, nargs="+", default=[0], help="Nummern der Szenen in dieser Saat")
    ap.add_argument("--orders", nargs="+", default=["ABC", "ABA"], help="Zielfolgen, z. B. ABC BCA ABA")
    ap.add_argument("--cond", default="live", choices=["static", "live", "away"])
    ap.add_argument("--fps", type=float, default=3.0)
    ap.add_argument("--hold", type=int, default=3, help="Bilder fuer Hinweise und Ergebnisse")
    ap.add_argument("--arm-frames", type=int, default=8)
    ap.add_argument("--out", required=True, help=".mp4 (ffmpeg) oder .gif")
    a = ap.parse_args()
    orders = [tuple(NAMES.index(c) for c in o.upper()) for o in a.orders]
    for o in orders:
        if o not in ORDERS:
            raise SystemExit(f"keine gueltige Folge: {o}")
    sc, rng = ex.Scene(), np.random.default_rng(a.seed)
    scenes = []
    while len(scenes) <= max(a.scenes):                                       # gleiche Reihenfolge wie die Messung
        s = make_scene(sc, rng)
        if s is not None:
            scenes.append(s)
    conn, label = None, "Orakel"
    if a.net:
        name, ckpt, seed = a.net.split(":")
        conn = Client(("127.0.0.1", a.port), authkey=b"netresearch-live")
        ask(conn, {"op": "load", "task": a.task, "model": name, "ckpt": ckpt, "seed": int(seed)})
        label = f"{name} s{seed}"
    frames = []
    for i in a.scenes:
        for o in orders:
            fr = record_run(sc, scenes[i], conn, a.cond, o, label, i, a.arm_frames, a.hold)
            print(f"Szene {i} Folge {''.join(NAMES[k] for k in o)}: {len(fr)} Bilder", flush=True)
            frames += fr
    if conn is not None:
        ask(conn, {"op": "quit"})
    write(frames, a.out, a.fps)
    print(f"{len(frames)} Bilder -> {a.out}")


if __name__ == "__main__":
    main()
