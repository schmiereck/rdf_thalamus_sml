"""FAELLT EIN NIE GESEHENER KOERPER IN DIE PASSENDE BESTEHENDE KATEGORIE?

Nutzeridee 2026-09-12: *"Unser Baby wuerde wahrscheinlich auch irgendwann nur noch 'die eher
langen' oder 'die viereckigen' unterscheiden und nicht jede Form einzeln auswendig lernen."*
Gemessen bestaetigt (wiki/befunde/geburtenrate-und-saettigung.md): die Formklassen SIND bereits
Grobkategorien -- `cube` fasst drei Koerper zusammen, und neu-9/neu-285 meinen beide "langer
duenner Balken".

DARAUS FOLGT EINE ANDERE ERFOLGSMETRIK.  "Mehr Geburten" ist kein gutes Ziel: eine Geburt heisst
"das kenne ich nicht", und in einer Welt mit vier Grobformen ist eine hohe Geburtenrate
UEBERSEGMENTIERUNG.  Die richtige Frage ist die nach VERALLGEMEINERUNG:

    stellt man eine nie gesehene Form hin -- faellt sie in die passende bestehende
    Kategorie, gebiert sie eine neue, oder landet sie in der FALSCHEN?

Drei Ausgaenge, drei Bedeutungen:
    RICHTIG    verallgemeinert -- das Ziel
    NEU        uebersegmentiert (oder echt neuartig; die Sollvorgabe unten trennt das)
    FALSCH     verwechselt -- der einzige echte Fehler

AUFBAU.  Der Probe-Koerper wird auf eine vorgegebene Proportion gesetzt und ueber viele Lagen und
Drehungen ALLEIN gezeigt (Verschmelzung ausgeschlossen).  Zu jeder Proportion gehoert eine
SOLLKATEGORIE, aus der Geometrie abgeleitet und VOR der Messung festgelegt:

    Laengenverhaeltnis >= 2.5     -> "langer duenner Balken"  (die Klasse von obj_T/obj_X)
    Laengenverhaeltnis <  1.4     -> "viereckig"              (die Klasse der Wuerfel)
    dazwischen                     -> kein Soll (offen, zaehlt nur als Beobachtung)

Die Zuordnung Kategorie -> Klassenname wird EMPIRISCH bestimmt: die bekannten Koerper werden
gezeigt und gefragt, wie die Wahrnehmung sie nennt.  Keine fest verdrahteten Namen.

NICHTS WIRD GELERNT UND NICHTS GESPEICHERT: observe/observe_scene werden nicht gerufen, der
Zustand bleibt unveraendert.  Es wird nur gefragt, was resolve() sagt.

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_form_rueckhalt.py
Knoepfe: FRH_STATE (KOPIE angeben), FRH_N (Lagen je Form, 12), FRH_SEED, FRH_BODY (obj_T)
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("FRH_STATE", "src/pc_cvnn/state/act23_state.pkl")
N = int(os.environ.get("FRH_N", "12"))
SEED = int(os.environ.get("FRH_SEED", "5"))
BODY = os.environ.get("FRH_BODY", "obj_T")
ALLE = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]

# Proportionen (Halbmasse in m).  Bewusst ueber den ganzen Bereich, nicht nur dort, wo Neuheit
# erwartet wird -- sonst misst man die eigene Erwartung.
PROBEN = [
    (0.034, 0.004, 0.012),   # 8.5:1  extrem lang    -> lang
    (0.030, 0.006, 0.012),   # 5.0:1                 -> lang
    (0.026, 0.009, 0.012),   # 2.9:1                 -> lang
    (0.022, 0.009, 0.012),   # 2.4:1  Grenzfall      -> offen
    (0.018, 0.011, 0.012),   # 1.6:1                 -> offen
    (0.016, 0.013, 0.012),   # 1.2:1                 -> viereckig
    (0.020, 0.018, 0.012),   # 1.1:1  gross+quadr.   -> viereckig
    (0.026, 0.024, 0.012),   # 1.1:1  sehr gross     -> viereckig
]


def soll(half):
    r = max(half[0], half[1]) / max(1e-9, min(half[0], half[1]))
    if r >= 2.5:
        return "lang"
    if r < 1.4:
        return "viereckig"
    return None


def main():
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc = st["shape_clf"]
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rng = np.random.default_rng(SEED)

    def zeige(body, half=None, n=N):
        """Koerper allein, n Lagen/Drehungen -> Liste der genannten Klassen."""
        aus = []
        for _ in range(n):
            for o in ALLE:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            if half is not None:
                sim.set_object_size(body, np.asarray(half, float))
            sim.set_object(body, [float(rng.uniform(-0.05, 0.05)),
                                  float(rng.uniform(0.14, 0.19))],
                           z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
            mujoco.mj_forward(sim.m, sim.d)
            sv = sim.d.mocap_pos.copy()
            ds = sc.perceive_all(sim)
            sim.d.mocap_pos[:] = sv
            mujoco.mj_forward(sim.m, sim.d)
            aus.append(str(max(ds, key=lambda x: float(x.get("area", 0))).get("shape"))
                       if ds else "None")
        return aus

    orig = sim.m.geom_size[sim.m.body_geomadr[
        mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, BODY)]].copy()

    # ---- Kategorien EMPIRISCH festlegen: wie nennt die Wahrnehmung die bekannten Koerper? ----
    from collections import Counter
    print(f"Zustand: {STATE}   Probe-Koerper: {BODY}   {N} Lagen je Form\n")
    print("Kategorien aus den BEKANNTEN Koerpern (nicht verdrahtet, gemessen):")
    kat = {"lang": set(), "viereckig": set()}
    for o, k in (("obj_red", "viereckig"), ("obj_green", "viereckig"), ("obj_blue", "viereckig"),
                 ("obj_T", "lang"), ("obj_X", "lang")):
        c = Counter(zeige(o, None, 6))
        nm = c.most_common(1)[0][0]
        kat[k].add(nm)
        print(f"  {o:10s} -> '{nm}'  ({dict(c)})")
    print(f"\n  Kategorie 'lang'      = {sorted(kat['lang'])}")
    print(f"  Kategorie 'viereckig' = {sorted(kat['viereckig'])}")

    # ---- der eigentliche Rueckhalte-Test ----
    print(f"\n{'Halbmasse [mm]':18s} {'Verh.':>6s} {'Soll':>10s} | {'richtig':>8s} {'neu':>5s}"
          f" {'falsch':>7s} | genannt")
    bil = {"richtig": 0, "neu": 0, "falsch": 0, "offen": 0}
    for half in PROBEN:
        s = soll(half)
        aus = zeige(BODY, half)
        c = Counter(aus)
        r = max(half[0], half[1]) / min(half[0], half[1])
        if s is None:
            bil["offen"] += len(aus)
            print(f"{str(np.round(1000*np.array(half),0)):18s} {r:5.1f}:1 {'--':>10s} |"
                  f" {'--':>8s} {'--':>5s} {'--':>7s} | {dict(c)}")
            continue
        ziel, gegen = kat[s], kat["viereckig" if s == "lang" else "lang"]
        ri = sum(v for k, v in c.items() if k in ziel)
        fa = sum(v for k, v in c.items() if k in gegen)
        ne = sum(v for k, v in c.items() if k == "None")
        rest = len(aus) - ri - fa - ne                      # andere bekannte Klasse (L, U, ...)
        bil["richtig"] += ri; bil["neu"] += ne; bil["falsch"] += fa + rest
        print(f"{str(np.round(1000*np.array(half),0)):18s} {r:5.1f}:1 {s:>10s} |"
              f" {ri:8d} {ne:5d} {fa+rest:7d} | {dict(c)}")

    sim.set_object_size(BODY, orig)
    ges = bil["richtig"] + bil["neu"] + bil["falsch"]
    print(f"\nBILANZ ueber die Formen MIT Sollvorgabe (n={ges}):")
    for k in ("richtig", "neu", "falsch"):
        print(f"  {k:8s} {bil[k]:4d} = {100*bil[k]/max(1,ges):5.1f} %")
    print(f"  (ohne Soll, nur beobachtet: {bil['offen']} Sichtungen)")
    print("\n  richtig = verallgemeinert  |  neu = uebersegmentiert  |  falsch = verwechselt")


if __name__ == "__main__":
    main()
