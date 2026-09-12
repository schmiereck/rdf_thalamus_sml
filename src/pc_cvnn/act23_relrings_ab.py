"""FORM-RUECKHALTE-TEST MIT DEM NEUEN DESKRIPTOR -- feste gegen relative Ringe.

Die Kennzahl aus wiki/befunde/groessen-invarianz-fuenfter-anlauf.md (3,68 -> 2,08) ist eine
Eigenschaft des Deskriptors, keine des Betriebs.  Die Frage, die zaehlt, steht in
wiki/befunde/form-rueckhalt.md: **wird eine uebergrosse Form noch als ihre Form erkannt?**

AUFBAU.  Zwei Klassifikatoren, gleicher Seed, gleiche Trainingsschritte -- einer mit festen
Ringen (heute), einer mit relativen (ACT_SHAPE_RELRINGS).  Beide werden FRISCH angelernt, weil
ein geaenderter Deskriptor mit gespeicherten Exemplaren nicht vergleichbar ist.

Danach die direkte Frage, OHNE offene Klassen und ohne Sollvorgabe von Hand: die drei TRAINIERTEN
Formen (cube, L, U) werden in Groessen von 0,7x bis 2,0x ihres Trainingsmasses gezeigt, und
gezaehlt wird, ob resolve() sie noch ihre eigene Form nennt.  Die Sollkategorie ist hier
unstrittig -- ein doppelt so grosser Wuerfel IST ein Wuerfel.

Drei Ausgaenge:
    RICHTIG   die eigene Form   -> groessen-invariant
    NEU       None              -> uebersegmentiert (die gemessene Schwaeche)
    FALSCH    eine andere Form  -> verwechselt

NICHTS WIRD GESPEICHERT: beide Klassifikatoren leben nur im Speicher, der Live-Zustand wird
nicht angefasst.

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_relrings_ab.py
Knoepfe: RR_STEPS (Trainingsschritte je Arm, 2500), RR_N (Lagen je Form/Groesse, 8), RR_SEED
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STEPS = int(os.environ.get("RR_STEPS", "2500"))
N = int(os.environ.get("RR_N", "8"))
SEED = int(os.environ.get("RR_SEED", "5"))
FAKTOREN = [0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0]
ALLE = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]


def lauf(relrings):
    """Einen Klassifikator frisch anlernen und den Rueckhalte-Test fahren."""
    os.environ["ACT_SHAPE_RELRINGS"] = "1" if relrings else "0"
    for m in [k for k in list(sys.modules) if "shape_classifier" in k]:
        del sys.modules[m]                                   # Modul neu laden -> Schalter greift
    from pc_cvnn.arm_modules.shape_classifier import (ShapeClassifierModule, SHAPES,
                                                      SHAPE_BODY, RELRINGS)
    assert RELRINGS == relrings, "Schalter nicht angekommen"
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    sc = ShapeClassifierModule(rng=np.random.default_rng(SEED))
    acc = sc.train(sim, steps=STEPS, rng=np.random.default_rng(SEED))
    rng = np.random.default_rng(SEED + 1)

    bil = {}
    for form in SHAPES:
        body, half = SHAPE_BODY[form]
        bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
        basis = (np.asarray(half, float) if half is not None
                 else sim.m.geom_size[sim.m.body_geomadr[bid]].copy())
        for f in FAKTOREN:
            h = basis.copy(); h[:2] = basis[:2] * f           # nur in der Ebene skalieren
            aus = []
            for _ in range(N):
                for o in ALLE:
                    sim.set_object(o, [0.5, -0.6], z=0.012)
                sim.m.geom_size[sim.m.body_geomadr[bid]] = h
                sim.set_object(body, [float(rng.uniform(-0.04, 0.04)),
                                      float(rng.uniform(0.145, 0.185))],
                               z=float(h[2]), yaw=float(rng.uniform(0, 2 * np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                sv = sim.d.mocap_pos.copy()
                ds = sc.perceive_all(sim)
                sim.d.mocap_pos[:] = sv
                mujoco.mj_forward(sim.m, sim.d)
                aus.append(str(max(ds, key=lambda x: float(x.get("area", 0))).get("shape"))
                           if ds else "None")
            sim.m.geom_size[sim.m.body_geomadr[bid]] = basis
            r = sum(1 for x in aus if x == form)
            ne = sum(1 for x in aus if x == "None")
            bil[(form, f)] = (r, ne, len(aus) - r - ne)
    return acc, sc.novel_th, bil, SHAPES


def main():
    print(f"Trainingsschritte je Arm: {STEPS}, {N} Lagen je Form/Groesse, Seed {SEED}\n")
    erg = {}
    for tag, rel in (("fest", False), ("relativ", True)):
        acc, th, bil, SHAPES = lauf(rel)
        erg[tag] = bil
        print(f"  {tag:8s} Trainingsgenauigkeit {acc:.3f}, novel_th {th:.3f}")

    print(f"\n{'Form':6s} {'Faktor':>7s} | {'fest: ri/neu/fa':>18s} | {'relativ: ri/neu/fa':>20s}")
    ges = {"fest": [0, 0, 0], "relativ": [0, 0, 0]}
    for form in SHAPES:
        for f in FAKTOREN:
            a = erg["fest"][(form, f)]; b = erg["relativ"][(form, f)]
            for i in range(3):
                ges["fest"][i] += a[i]; ges["relativ"][i] += b[i]
            mark = "  <-" if (b[0] - a[0]) >= 2 else ""
            print(f"{form:6s} {f:6.2f}x | {a[0]:5d}/{a[1]:3d}/{a[2]:3d}      "
                  f"| {b[0]:5d}/{b[1]:3d}/{b[2]:3d}{mark}")
    print()
    for tag in ("fest", "relativ"):
        r, ne, fa = ges[tag]; n = r + ne + fa
        print(f"  {tag:8s} richtig {r:4d} = {100*r/n:5.1f} %   neu {ne:4d} = {100*ne/n:5.1f} %"
              f"   falsch {fa:4d} = {100*fa/n:5.1f} %")
    # nur die UEBERGROSSEN (>= 1,4x) -- dort sass die gemessene Schwaeche
    print("\n  nur die uebergrossen Faelle (>= 1,4x):")
    for tag in ("fest", "relativ"):
        r = ne = fa = 0
        for form in SHAPES:
            for f in FAKTOREN:
                if f < 1.4:
                    continue
                a = erg[tag][(form, f)]
                r += a[0]; ne += a[1]; fa += a[2]
        n = r + ne + fa
        print(f"    {tag:8s} richtig {r:3d}/{n:<3d} = {100*r/n:5.1f} %   neu {ne:3d}   falsch {fa:3d}")


if __name__ == "__main__":
    main()
