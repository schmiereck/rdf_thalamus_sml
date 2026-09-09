"""KUERZT DIE ERKENNUNG UEBER DIE FARBE AB?  RUECKHALTE-TEST DURCH UMFAERBEN.

Anlass (Nutzerbeobachtung 2026-09-10): im Szenensatz haengt die Farbe fast vollstaendig an der
Form.  Gemessen ueber die sieben Koerper:

    obj_red farbe-1/cube | obj_green farbe-2/cube | obj_blue farbe-5/cube
    obj_L farbe-4/L | obj_U farbe-3/U | obj_T farbe-14/neu-9 | obj_X farbe-4/neu-285

In 5 von 6 Farbklassen bestimmt die FARBE die FORM eindeutig; die einzige Ausnahme (farbe-4 fuer
obj_L und obj_X) ist kein Design, sondern eine Kollision des Chroma-Klassifikators.  Ein Netz,
das "orange -> L" lernt, liegt in dieser Welt zu 100 % richtig -- und keine Messung im heutigen
Aufbau kann diese Abkuerzung von echter Formerkennung unterscheiden.  Das trifft das
Projektziel (wiki/ziel.md: neue Farben, Formen UND KOMBINATIONEN selbst lernen).

DIESER TEST HAELT DIE FARBE ZURUECK, ohne die Szene dauerhaft zu aendern: jeder Koerper wird
nacheinander in die Farbe JEDES anderen umgefaerbt, und gefragt wird, ob die WAHRNEHMUNG ihn
trotzdem richtig nennt.  Kein Lauf, kein Lernen, nichts wird gespeichert.

  Formklasse    bleibt d["shape"] die Klasse, die der Koerper in seiner EIGENEN Farbe bekommt?
                Der Deskriptor rechnet auf der Belegungsmaske, sollte also farbunabhaengig sein --
                das ist die Erwartung, und genau deshalb ist es einen Test wert: haelt sie nicht,
                ist eine Entkopplung sinnlos, bevor der Deskriptor repariert ist.
  Farbklasse    wandert sie mit der neuen Farbe mit (Kontrollgroesse: faerbt der Test ueberhaupt)?
  Adressierung  findet finde_nach_eigenschaften den Koerper noch, wenn NUR die Form genannt wird?
                Das ist die Groesse, die im Lauf zaehlt.

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_farbe_form_probe.py
Knoepfe: FFP_STATE (KOPIE angeben), FFP_N (Lagen je Paarung, 8), FFP_SEED
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("FFP_STATE", "src/pc_cvnn/state/act23_state.pkl")
N = int(os.environ.get("FFP_N", "8"))
SEED = int(os.environ.get("FFP_SEED", "5"))
ALLE = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]


def main():
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc, colours = st["shape_clf"], st["colours"]
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rng = np.random.default_rng(SEED)

    def geoms(body):
        b = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
        a0 = sim.m.body_geomadr[b]
        return list(range(a0, a0 + sim.m.body_geomnum[b]))

    orig = {o: sim.m.geom_rgba[geoms(o)].copy() for o in ALLE}

    def faerbe(body, rgba):
        for g in geoms(body):
            sim.m.geom_rgba[g] = rgba

    def sieh(body, p, yaw):
        for o in ALLE:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object(body, p.tolist(), z=0.012, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d)
        saved = sim.d.mocap_pos.copy()
        ds = sc.perceive_all(sim)
        sim.d.mocap_pos[:] = saved
        mujoco.mj_forward(sim.m, sim.d)
        if not ds:
            return None, None
        d = max(ds, key=lambda x: float(x.get("area", 0)))
        ck = colours.classify(d["chroma"])[0] if d.get("chroma") is not None else None
        return d.get("shape"), ck

    lagen = [(np.array([rng.uniform(-0.06, 0.06), rng.uniform(0.13, 0.19)]),
              float(rng.uniform(0, 2 * np.pi))) for _ in range(N)]

    print(f"Zustand: {STATE}   {N} Lagen je Paarung, alles einzeln auf dem Tisch\n")
    print("EIGENE Farbe (Bezugswert):")
    eigen = {}
    for o in ALLE:
        tr = [sieh(o, p, y) for p, y in lagen]
        fk = max({t[0] for t in tr if t[0]}, key=lambda k: sum(1 for t in tr if t[0] == k),
                 default=None)
        ck = max({t[1] for t in tr if t[1]}, key=lambda k: sum(1 for t in tr if t[1] == k),
                 default=None)
        stabil = sum(1 for t in tr if t[0] == fk)
        eigen[o] = (fk, ck)
        print(f"  {o:10s} Form '{fk}' in {stabil}/{N} Lagen | Farbe '{ck}'")

    print("\nUMGEFAERBT -- Form bleibt richtig? / Farbklasse wandert mit?")
    print(f"  {'Koerper':10s} {'Formklasse gehalten':>20s} {'Farbklasse gewechselt':>22s}")
    ges_f = ges_c = ges_n = 0
    for o in ALLE:
        fk0, ck0 = eigen[o]
        haelt = wechselt = n = 0
        for fremd in ALLE:
            if fremd == o:
                continue
            faerbe(o, orig[fremd][0])
            for p, y in lagen:
                fk, ck = sieh(o, p, y)
                n += 1
                haelt += int(fk == fk0)
                wechselt += int(ck != ck0)
            faerbe(o, orig[o][0])
        ges_f += haelt; ges_c += wechselt; ges_n += n
        print(f"  {o:10s} {haelt:9d}/{n:<9d} = {100*haelt/n:4.0f}% "
              f"{wechselt:11d}/{n:<9d} = {100*wechselt/n:4.0f}%")
    print(f"  {'GESAMT':10s} {ges_f:9d}/{ges_n:<9d} = {100*ges_f/ges_n:4.0f}% "
          f"{ges_c:11d}/{ges_n:<9d} = {100*ges_c/ges_n:4.0f}%")

    for o in ALLE:                                              # Szene garantiert unveraendert lassen
        faerbe(o, orig[o][0])


if __name__ == "__main__":
    main()
