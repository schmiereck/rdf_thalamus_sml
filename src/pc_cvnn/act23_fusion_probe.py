"""AB WELCHEM NACHBARABSTAND VERSAGT DER SPLIT?

Offener Faden seit August (wiki/fragen/offene-faeden-act23.md), inzwischen dreimal als Ursache
aufgetaucht: beim Eigenschafts-Kommando ("Eindeutigkeit ist nicht Richtigkeit", zwei Koerper in
~50mm ergeben EINE Detektion auf der Mitte), bei der Ablenker-Bindung und beim privilegierten
Rueckfall (wiki/befunde/keim-im-rueckfall.md: der gewaehlte Blob sass bei 21 gegen 23mm fast
genau zwischen zwei Koerpern).

AUFBAU.  Kein Lauf, kein Lernen -- die WAHRNEHMUNG wird direkt befragt (Methodenlehre aus
45fa0a4).  Zwei Koerper werden in kontrolliertem Mittenabstand d nebeneinander gestellt, alles
andere geparkt.  Je Abstand und Anordnung wird gemessen:

  verschmolzen   liefert perceive_all zwei Komponenten in der Naehe der beiden Koerper, oder eine?
                 Kriterium: gibt es eine Detektion naeher als d/2 am Zielkoerper?
  Farb-Split     rettet perceive_colour(cname) das Ziel, wenn der Blob verschmolzen ist?
  Form-Split     rettet perceive_colour(..., with_form=True) auch die FORMKLASSE?
  Fehler         Abstand der zurueckgegebenen Position zur Wahrheit, je Pfad

Die drei Pfade sind die drei, ueber die act23 tatsaechlich adressiert: Farbklasse (color/long),
Formklasse (shape) und das Eigenschafts-Tripel (eigenschaft).

WARUM DAS ZAEHLT.  Der Split ist der am besten belegte Gewinn der Wahrnehmungslinie
(wiki/mechanismen/wahrnehmungs-splits.md), aber seine GRENZE war nie beziffert.  Ohne die Grenze
laesst sich nicht sagen, ob ein Fehlgriff an der Verschmelzung lag oder woanders.

ACHTUNG: RES bleibt bei 240.  Die Homographie ist darauf geeicht; eine Probe mit 360x360 lag
36-159mm daneben (wiki/mechanismen/eigenschafts-kommando.md).

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_fusion_probe.py
Knoepfe:
    FUS_STATE   Zustandsdatei (Vorgabe: eine KOPIE angeben, nie die Live-Datei)
    FUS_N       Wiederholungen je Abstand (Vorgabe 24)
    FUS_PAARE   Koerperpaare "ziel:nachbar,..." (Vorgabe obj_red:obj_L,obj_green:obj_red,obj_T:obj_U)
    FUS_DMIN/DMAX/DSTEP   Abstandsgitter in mm (Vorgabe 15 / 95 / 10)
    FUS_SEED    Zufallsstrom fuer Lage und Drehung (Vorgabe 5)
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("FUS_STATE", "src/pc_cvnn/state/act23_state.pkl")
N = int(os.environ.get("FUS_N", "24"))
DMIN = float(os.environ.get("FUS_DMIN", "15"))
DMAX = float(os.environ.get("FUS_DMAX", "95"))
DSTEP = float(os.environ.get("FUS_DSTEP", "10"))
PAARE = os.environ.get("FUS_PAARE", "obj_red:obj_L,obj_green:obj_red,obj_T:obj_U")
SEED = int(os.environ.get("FUS_SEED", "5"))


def main():
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc, colours = st["shape_clf"], st["colours"]
    shape_key = dict(st.get("shape_key", {}))
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rng = np.random.default_rng(SEED)

    alle = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]
    paare = [tuple(p.split(":")) for p in PAARE.split(",")]
    gitter = np.arange(DMIN, DMAX + 1e-6, DSTEP)

    # Farb- UND Formklasse je Koerper EMPIRISCH bestimmen: Koerper allein hinstellen und fragen,
    # wie die Wahrnehmung ihn nennt.  Nicht aus shape_key lesen -- dort stehen nur die selbst
    # geborenen Klassen (obj_T, obj_X), die trainierten Formen (L, U) fehlen dort und die
    # Form-Spalte waere fuer sie stumm.
    def klassen(body):
        for o in alle:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object(body, [0.0, 0.16], z=0.012)
        mujoco.mj_forward(sim.m, sim.d)
        saved = sim.d.mocap_pos.copy()
        ds = sc.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        if not ds:
            return None, None
        d = max(ds, key=lambda x: float(x.get("area", 0)))
        return colours.classify(d["chroma"])[0], d.get("shape")

    print(f"Zustand: {STATE}")
    print(f"Gitter: {DMIN:.0f}..{DMAX:.0f}mm in {DSTEP:.0f}mm, {N} Lagen je Punkt, "
          f"Paare: {PAARE}\n")

    for ziel, nachbar in paare:
        ck, fk = klassen(ziel)
        if fk is None:
            fk = shape_key.get(ziel)          # Rueckfall: die persistierte Bindung
        print(f"=== {ziel} neben {nachbar}   (Farbklasse '{ck}', Formklasse '{fk}') ===")
        print(f"  {'d [mm]':>7s} {'verschmolzen':>13s} {'Farb-Split rettet':>18s} "
              f"{'Form erkannt':>13s} {'Fehler ganz':>12s} {'Fehler Split':>13s}")
        for d_mm in gitter:
            d = d_mm / 1000.0
            n_fus = n_rec = n_form = 0
            err_ganz, err_split = [], []
            for _ in range(N):
                for o in alle:
                    sim.set_object(o, [0.5, -0.6], z=0.012)
                p = np.array([rng.uniform(-0.07, 0.07), rng.uniform(0.12, 0.19)])
                ang = rng.uniform(0, 2 * np.pi)
                sim.set_object(ziel, p.tolist(), z=0.012,
                               yaw=float(rng.uniform(0, 2 * np.pi)))
                sim.set_object(nachbar, (p + d * np.array([np.cos(ang), np.sin(ang)])).tolist(),
                               z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                wahr = np.asarray(sim.obj_pos(ziel)[:2], float)

                saved = sim.d.mocap_pos.copy()
                dets = sc.perceive_all(sim)
                # VERSCHMOLZEN = keine Detektion, die naeher am Ziel liegt als die halbe Luecke.
                # Das Kriterium ist absichtlich abstandsrelativ: bei 15mm Luecke waeren 10mm
                # Fehler eine Verwechslung, bei 90mm nicht.
                nah = [x for x in dets if x.get("pos") is not None]
                e_ganz = (min(float(np.linalg.norm(np.asarray(x["pos"], float) - wahr))
                              for x in nah) if nah else float("nan"))
                fused = (not nah) or e_ganz > d / 2.0
                if fused:
                    n_fus += 1
                    if ck is not None:
                        teile = sc.perceive_colour(sim, colours, ck)
                        if teile:
                            b = min(teile, key=lambda x: float(np.linalg.norm(
                                np.asarray(x["pos"], float) - wahr)))
                            e = float(np.linalg.norm(np.asarray(b["pos"], float) - wahr))
                            if e <= d / 2.0:
                                n_rec += 1
                                err_split.append(1000.0 * e)
                        mit_form = sc.perceive_colour(sim, colours, ck, with_form=True)
                        if fk is not None and any(x.get("shape") == fk for x in mit_form):
                            n_form += 1
                else:
                    err_ganz.append(1000.0 * e_ganz)
                sim.d.mocap_pos[:] = saved
                mujoco.mj_forward(sim.m, sim.d)

            def m(v):
                return f"{np.median(v):.0f}" if v else "--"
            print(f"  {d_mm:7.0f} {n_fus:6d}/{N:<6d} {n_rec:10d}/{max(1,n_fus):<7d} "
                  f"{n_form:6d}/{max(1,n_fus):<6d} {m(err_ganz):>12s} {m(err_split):>13s}")
        print()


if __name__ == "__main__":
    main()
