"""MISST, WIEVIEL DES ERGEBNISSES AN DER AUSFUEHRUNG HAENGT statt an der Wahl.

Anlass (2026-08-06): das Welt-Modell steht bei R^2 ~ 0.19 am Deckel -- mehr Daten helfen nicht
(Lernkurve saettigt ab ~3000 Zeilen), eine andere Modellklasse auch nicht (kNN schlechter), und drei
zusaetzliche Merkmalsbloecke haben gemessen GESCHADET.  Zugleich traegt die AKTION nur +0.055 R^2.
Die offene Frage ist damit: liegen die verbleibenden ~81% in der AUSFUEHRUNG?

AUFBAU.  Fuer jede Szene wird ALLES fixiert, was die Wahl ausmacht -- Objekt, Pose, Greifpunkt,
Wrist, Griffweite -- und NUR die Startpose des Arms variiert, und zwar genau so weit, wie sie im
echten Lauf ohnehin variiert: run_combined laeuft dort mit arm_reset=False, und drive_home landet
laut seinem eigenen Docstring nur NAHE der Ruhepose (~0.05 rad je Gelenk).

  Arm A (Kontrolle): keine Stoerung -> muss identische Ergebnisse liefern (prueft Determinismus)
  Arm B            : +-JITTER rad je Positioniergelenk, sonst bitgleiche Bedingungen

Streuen die Ergebnisse in Arm B innerhalb einer Szene, dann entscheidet die gefahrene BAHN und nicht
die getroffene WAHL -- und weitere Situations-Merkmale koennen die Lieferquote nicht heben.
Bleiben sie konstant, ist die Ausfuehrung unschuldig und der Deckel sitzt wirklich in der Wahrnehmung.

Aufruf:  ACT14_DOF=4 python src/pc_cvnn/act23_exec_variance.py
Knoepfe: EXV_SCENES (12), EXV_REPS (8), EXV_JITTER (0.05 rad), EXV_SEED, EXV_OBJ
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn import pc_act16 as act16                            # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim, ARM3, HOME, _rand_xy  # noqa: E402
from pc_cvnn.arm_modules.body_model import BodyModelModule       # noqa: E402

SCENES = int(os.environ.get("EXV_SCENES", "12"))
REPS = int(os.environ.get("EXV_REPS", "8"))
JITTER = float(os.environ.get("EXV_JITTER", "0.05"))
SEED = int(os.environ.get("EXV_SEED", "3"))
OBJ = os.environ.get("EXV_OBJ", "obj_red")
CAM = "overview"


def main():
    rng = np.random.default_rng(SEED)
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    print("  Koerpermodell wird gebabbelt (kein Zustand noetig -- die Kinematik ist nicht die Frage) ...",
          flush=True)
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    act16.OBJS = [OBJ]
    act16.run_combined._quiet = True
    TARGET = np.array([0.0, 0.10])

    def park_others():
        for o in ("obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"):
            if o != OBJ:
                sim.set_object(o, [0.5, -0.6], z=0.012)

    def trial(p, yaw, wrist, jitter):
        """EINE Episode: Szene und Aktion fest, Startpose um `jitter` gestoert."""
        sim.reset_home(); park_others()
        sim.set_object(OBJ, p, z=0.012, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        if jitter > 0:                                           # exakt die Streuung, die drive_home
            for j in ARM3:                                       #   im echten Lauf uebrig laesst
                sim.d.qpos[sim.jqadr[j]] = HOME[j] + float(rng.uniform(-jitter, jitter))
            mujoco.mj_forward(sim.m, sim.d)
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=OBJ, force="grasp",
                                  perceive_fn=lambda c, g=p: (np.asarray(g, float), None, "grasp"),
                                  goal_fn=lambda c, o: TARGET, servo=False, rescatter=False,
                                  wrist_fn=(lambda s, _w=wrist: _w), arm_reset=False)
        return int(d)

    scenes = []
    for _ in range(SCENES):
        scenes.append((_rand_xy(rng), float(rng.uniform(0, np.pi)), float(rng.uniform(0, np.pi))))

    print(f"  {SCENES} Szenen x {REPS} Wiederholungen, Objekt {OBJ}, Jitter {JITTER} rad\n", flush=True)
    out = {}
    for arm, jit in (("A Kontrolle (kein Jitter)", 0.0), ("B Startpose gestoert", JITTER)):
        res = []
        for i, (p, yaw, wrist) in enumerate(scenes):
            r = [trial(p, yaw, wrist, jit) for _ in range(REPS)]
            res.append(r)
            print(f"    [{arm[0]}] Szene {i:2d}: {''.join(str(x) for x in r)}  ({sum(r)}/{REPS})",
                  flush=True)
        out[arm] = np.array(res)

    print("\n" + "=" * 72)
    for arm, R in out.items():
        rate = R.mean()
        einig = np.mean([(r.sum() == 0 or r.sum() == REPS) for r in R])   # Szene voll einig?
        # Anteil der Gesamtvarianz, der INNERHALB der Szenen sitzt (= Ausfuehrung, nicht Wahl)
        within = np.mean([r.var() for r in R])
        between = R.mean(1).var()
        frac = within / (within + between) if (within + between) > 0 else float("nan")
        print(f"  {arm}")
        print(f"     Lieferquote {100*rate:.0f}%   Szenen mit EINHEITLICHEM Ausgang {100*einig:.0f}%")
        print(f"     Varianz INNERHALB der Szene {within:.4f} | ZWISCHEN Szenen {between:.4f}"
              f"  -> {100*frac:.0f}% der Varianz sitzt in der AUSFUEHRUNG")
    print("=" * 72)


if __name__ == "__main__":
    main()
