"""WARUM ZERSPLITTERT EIN NEUES OBJEKT IN MEHRERE SELBST BENANNTE KLASSEN?

Anlass (2026-08-16, nach Commit 90e162a): das neue Kreuz obj_X gebiert im Lauf DREI Klassen
(neu-285/286/287) statt einer.  Die reparierte Knopf-Bindung sucht sich die brauchbarste heraus,
behebt die Zersplitterung aber nicht -- und eine Klasse, die sich staendig neu erfindet, kann sich
nicht festigen.  Genau das ist aber das Nutzerziel: neue Formen SCHNELL und DAUERHAFT dazulernen.

AUFBAU (Methodenlehre aus 45fa0a4: das Modell direkt befragen statt Episoden fahren).  Das Objekt
steht ALLEIN auf dem Tisch -- Verschmelzung mit Nachbarn ist damit ausgeschlossen, uebrig bleibt die
Eigenstreuung des Deskriptors.  Fuer ein Gitter aus Positionen x Drehungen wird |F| gemessen, in den
z-Raum des Klassifikators gebracht (dieselbe Standardisierung, die auch novel_th kalibriert hat) und
ausgewertet:

  Eigenstreuung   paarweise Abstaende derselben Form -- ueberschreiten sie novel_th, erkennen sich
                  zwei Sichtungen DESSELBEN Objekts gegenseitig nicht mehr und die Klasse MUSS
                  zerfallen.  Das waere ein struktureller Befund, kein Abstimmungsproblem.
  Ursache         dieselbe Position/andere Drehung  gegen  dieselbe Drehung/andere Position.
                  Trennt Perspektive (die versetzte Kamera) von Rotation (|F| ist rotations-
                  invariant KONSTRUIERT -- wenn hier trotzdem Streuung sitzt, stimmt die Annahme
                  fuer diese Form nicht).
  Kontrolle       dieselbe Messung an einer TRAINIERTEN Form (obj_L) und am Balken obj_T.  Ohne die
                  Kontrolle sagt ein grosser Zahlenwert nichts -- zerfielen alle Formen gleich
                  stark, waere novel_th schlicht zu eng und nicht das Kreuz besonders.

Aufruf:  ACT14_DOF=4 python src/pc_cvnn/act23_split_probe.py
Knoepfe: SPL_STATE, SPL_GRID (3 -> 3x3 Positionen), SPL_YAWS (6), SPL_OBJS, SPL_SEED
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("SPL_STATE", "src/pc_cvnn/state/act23_state.pkl")
GRID = int(os.environ.get("SPL_GRID", "3"))
YAWS = int(os.environ.get("SPL_YAWS", "6"))
OBJS = os.environ.get("SPL_OBJS", "obj_X,obj_T,obj_L").split(",")
SEED = int(os.environ.get("SPL_SEED", "5"))
ALL = ("obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X")
BOUNDS = (-0.115, 0.115, 0.075, 0.235)                           # der Blick-Ausschnitt aus pc_act23


def q(v, p):
    return float(np.quantile(v, p)) if len(v) else float("nan")


def main():
    with open(STATE, "rb") as fh:
        clf = pickle.load(fh)["shape_clf"]
    th = float(clf.novel_th)
    print(f"  Zustand {STATE}\n  novel_th = {th:.2f}   area_hi = {clf.area_hi:.0f}   "
          f"Trainingsformen {len(clf._ZX)} Belege\n", flush=True)

    proben = {}                                                  # Objekt -> z-Matrix, fuer den Vergleich
    #   ZWISCHEN den Formen: erst er entscheidet, ob ein groesserer Geburts-/Anspruchsradius ueberhaupt
    #   moeglich ist.  Liegt die Eigenstreuung so hoch wie der Abstand zu einer ANDEREN Form, trennt kein
    #   Schwellwert die beiden mehr -- dann ist der Deskriptor das Problem, nicht die Abstimmung.
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    xs = np.linspace(BOUNDS[0] + 0.02, BOUNDS[1] - 0.02, GRID)
    ys = np.linspace(BOUNDS[2] + 0.02, BOUNDS[3] - 0.02, GRID)
    yaws = np.linspace(0, np.pi, YAWS, endpoint=False)

    for obj in OBJS:
        sim.reset_home()
        for o in ALL:                                            # ALLEIN auf dem Tisch: keine
            if o != obj:                                         #   Verschmelzung moeglich
                sim.set_object(o, [0.5, -0.6], z=0.012)
        recs = []                                                # (ix, iy, iyaw, z, area, dk)
        for ix, x in enumerate(xs):
            for iy, y in enumerate(ys):
                for iw, w in enumerate(yaws):
                    sim.set_object(obj, [float(x), float(y)], z=0.012, yaw=float(w))
                    mujoco.mj_forward(sim.m, sim.d); sim.step(30)
                    dets = [d for d in clf.perceive_all(sim) if d["pos"] is not None]
                    if not dets:
                        continue
                    p = np.array([x, y])
                    d = min(dets, key=lambda t: float(np.linalg.norm(np.asarray(t["pos"]) - p)))
                    if float(np.linalg.norm(np.asarray(d["pos"]) - p)) > 0.05:
                        continue                                 # nichts am Objekt gefunden
                    z = clf._z(d["desc"])
                    recs.append((ix, iy, iw, z, float(d["area"]), clf._knn(z, clf._ZX)))

        if len(recs) < 4:
            print(f"  {obj}: nur {len(recs)} Sichtungen -- uebersprungen\n", flush=True)
            continue
        Z = np.array([r[3] for r in recs])
        alle, dreh, ort = [], [], []
        for i in range(len(recs)):
            for j in range(i + 1, len(recs)):
                dd = float(np.linalg.norm(Z[i] - Z[j]))
                alle.append(dd)
                gl_ort = recs[i][0] == recs[j][0] and recs[i][1] == recs[j][1]
                if gl_ort:
                    dreh.append(dd)                              # gleicher Ort, andere Drehung
                elif recs[i][2] == recs[j][2]:
                    ort.append(dd)                               # gleiche Drehung, anderer Ort
        ar = np.array([r[4] for r in recs]); dk = np.array([r[5] for r in recs])
        ueber = 100.0 * float(np.mean(np.array(alle) > th))
        print(f"  {obj}  ({len(recs)} Sichtungen, {len(alle)} Paare)", flush=True)
        print(f"    Eigenstreuung   p50 {q(alle,.5):5.2f}  p90 {q(alle,.9):5.2f}  max {max(alle):5.2f}"
              f"   |  ueber novel_th: {ueber:4.1f}% der Paare", flush=True)
        print(f"      nur Drehung   p50 {q(dreh,.5):5.2f}  p90 {q(dreh,.9):5.2f}"
              f"      (gleicher Ort, {len(dreh)} Paare)", flush=True)
        print(f"      nur Ort       p50 {q(ort,.5):5.2f}  p90 {q(ort,.9):5.2f}"
              f"      (gleiche Drehung, {len(ort)} Paare)", flush=True)
        print(f"    Abstand zum Trainings-Mannigfaltigen  p50 {np.median(dk):5.2f}"
              f"  (novel_th {th:.2f} -> {100.0*float(np.mean(dk>th)):4.1f}% lesen NEU)", flush=True)
        print(f"    Flaeche  p50 {np.median(ar):6.0f}  min {ar.min():6.0f}  max {ar.max():6.0f}"
              f"   (area_hi {clf.area_hi:.0f})\n", flush=True)
        proben[obj] = (Z, q(alle, .5), q(alle, .9))

    if len(proben) < 2:
        return
    print("  ABSTAND ZWISCHEN DEN FORMEN gegen die jeweilige Eigenstreuung", flush=True)
    print("  (Trennung nur moeglich, wenn zwischen > eigen -- sonst hilft kein Schwellwert)\n",
          flush=True)
    namen = list(proben)
    print("           " + "".join(f"{n:>12}" for n in namen) + "     eigen p50/p90", flush=True)
    for a in namen:
        Za, e50, e90 = proben[a]
        zeile = f"  {a:>8} "
        for b in namen:
            Zb = proben[b][0]
            if a == b:
                zeile += f"{'--':>12}"
                continue
            dd = np.sqrt(((Za[:, None, :] - Zb[None, :, :]) ** 2).sum(2))
            zeile += f"{np.median(dd):12.2f}"
        print(zeile + f"     {e50:5.2f} / {e90:5.2f}", flush=True)


if __name__ == "__main__":
    main()
