"""WARUM VERLIERT DER SPLIT DIE FORMKLASSE, WAEHREND ER DIE POSITION RETTET?

Anlass: wiki/befunde/verschmelzung-abstandskurve.md.  Der Farb-Split holt ab 35mm Nachbarabstand
die POSITION zu 100% zurueck, die FORMKLASSE aber nur zu 42% -- und erst ab 65mm sicher.  Die
Lieferquote folgt der Formklasse, nicht der Position (wiki/befunde/nachbarnaehe-im-lauf.md).

ZWEI KANDIDATEN, die verschiedene Reparaturen verlangen:

  A  BESCHNITTENE SILHOUETTE.  perceive_colour behaelt nur Pixel, deren naechster Farbprototyp
     die gesuchte Klasse ist UND die innerhalb TH liegen -- Naht-, Schatten- und Mischpixel
     fallen weg (der Docstring sagt es selbst: "it drops shaded/edge pixels").  Dann ist der
     Fussabdruck kleiner und verformt, |F| verschiebt sich, und resolve() faellt aus.
     -> Reparatur muesste den FUSSABDRUCK retten (Morphologie, Naht schliessen).

  B  KNAPP UEBER DER SCHWELLE.  Die Silhouette ist im Wesentlichen richtig, der Deskriptor liegt
     aber knapp jenseits von novel_th, weil eine verschmolzene Szene nun einmal verrauschter ist.
     -> Reparatur waere eine KONTEXTABHAENGIGE Schwelle: wer weiss, dass gesplittet wurde, darf
     nicht dieselbe Passgenauigkeit verlangen.

Diese Probe misst BEIDE Groessen gegeneinander, je Konstellation:
    Flaeche solo  gegen  Flaeche des Splitteils      (Kandidat A)
    kNN-Abstand des Splitteils zu den Exemplaren, in EINHEITEN von novel_th   (Kandidat B)
    und was resolve() stattdessen sagt (None = neuartig, oder eine fremde Klasse)

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_formsplit_probe.py
Knoepfe: FSP_STATE, FSP_N (Lagen je Abstand, 24), FSP_DS (Abstaende in mm, "25,35,45,55"),
         FSP_PAARE, FSP_SEED
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("FSP_STATE", "src/pc_cvnn/state/act23_state.pkl")
N = int(os.environ.get("FSP_N", "24"))
DS = [float(x) for x in os.environ.get("FSP_DS", "25,35,45,55").split(",")]
PAARE = os.environ.get("FSP_PAARE", "obj_L:obj_U,obj_T:obj_U,obj_U:obj_L")
SEED = int(os.environ.get("FSP_SEED", "5"))
ALLE = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]


def main():
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc, colours = st["shape_clf"], st["colours"]
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rng = np.random.default_rng(SEED)
    print(f"Zustand: {STATE}   novel_th = {sc.novel_th:.3f}\n")

    def park():
        for o in ALLE:
            sim.set_object(o, [0.5, -0.6], z=0.012)

    def solo(body, p, yaw):
        park()
        sim.set_object(body, p.tolist(), z=0.012, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d)
        saved = sim.d.mocap_pos.copy()
        ds = sc.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        if not ds:
            return None
        return max(ds, key=lambda x: float(x.get("area", 0)))

    for paar in PAARE.split(","):
        ziel, nachbar = paar.split(":")
        print(f"=== {ziel} neben {nachbar} ===")
        print(f"  {'d [mm]':>7s} {'n':>4s} | {'Flaeche solo':>12s} {'Split':>8s} {'Anteil':>7s}"
              f" | {'kNN/novel_th solo':>18s} {'Split':>8s} | {'resolve richtig':>15s} {'novel':>6s}")
        for d_mm in DS:
            d = d_mm / 1000.0
            fl_solo, fl_spl, kn_solo, kn_spl = [], [], [], []
            richtig = novel = fremd = n_used = 0
            for _ in range(N):
                p = np.array([rng.uniform(-0.07, 0.07), rng.uniform(0.12, 0.19)])
                yaw = float(rng.uniform(0, 2 * np.pi))
                ang = rng.uniform(0, 2 * np.pi)
                s0 = solo(ziel, p, yaw)
                if s0 is None or s0.get("desc") is None:
                    continue
                klasse = s0["shape"]                      # so heisst der Koerper ALLEIN gesehen
                ck = colours.classify(s0["chroma"])[0]
                if klasse is None or ck is None:
                    continue
                # jetzt mit Nachbarn, im Abstand d
                park()
                sim.set_object(ziel, p.tolist(), z=0.012, yaw=yaw)
                sim.set_object(nachbar,
                               (p + d * np.array([np.cos(ang), np.sin(ang)])).tolist(),
                               z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                wahr = np.asarray(sim.obj_pos(ziel)[:2], float)
                saved = sim.d.mocap_pos.copy()
                dets = sc.perceive_all(sim)
                nah = [x for x in dets if x.get("pos") is not None]
                e = (min(float(np.linalg.norm(np.asarray(x["pos"], float) - wahr))
                         for x in nah) if nah else 9.9)
                if e <= d / 2.0:                          # nicht verschmolzen -> nicht der Fall hier
                    sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                    continue
                teile = sc.perceive_colour(sim, colours, ck, with_form=True)
                sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                if not teile:
                    continue
                t = min(teile, key=lambda x: float(np.linalg.norm(
                    np.asarray(x["pos"], float) - wahr)))
                if t.get("desc") is None:
                    continue
                n_used += 1
                fl_solo.append(float(s0["area"])); fl_spl.append(float(t["area"]))
                # kNN-Abstand in Einheiten von novel_th -- <=1 heisst "innerhalb der Basisklassen"
                kn_solo.append(float(sc._knn(sc._z(s0["desc"]), sc._ZX)) / sc.novel_th)
                kn_spl.append(float(sc._knn(sc._z(t["desc"]), sc._ZX)) / sc.novel_th)
                if t["shape"] == klasse:
                    richtig += 1
                elif t["shape"] is None:
                    novel += 1
                else:
                    fremd += 1

            if not n_used:
                print(f"  {d_mm:7.0f} {0:4d} | (keine verschmolzenen Faelle)")
                continue
            print(f"  {d_mm:7.0f} {n_used:4d} | {np.median(fl_solo):12.0f} {np.median(fl_spl):8.0f}"
                  f" {np.median(fl_spl)/np.median(fl_solo):6.2f}"
                  f" | {np.median(kn_solo):18.2f} {np.median(kn_spl):8.2f}"
                  f" | {richtig:6d}/{n_used:<7d} {novel:4d}   (fremd {fremd})")
        print()


if __name__ == "__main__":
    main()
