"""One-off HEAL: drop the mis-attributed world-model FAILURE labels of the netz-attempted
regression session (rows 798..896 with outcome 0 -- the "Griff am Objekt fehlgeschlagen"
flood measured to inflate ensemble sigma 0.5-0.9 -> 0.9-2.0 and destabilise LCB; the netz
route is gated off since c61205b, but the noise STAYS in the data and does not dilute out:
it sits in the same feature region as the successes).  A few legitimate slip labels in the
window are lost too -- they re-accumulate.  Usage (with the GUI session STOPPED):

    python src/pc_cvnn/heal_world_noise.py src/pc_cvnn/state/act23_state.pkl

Writes a .vor-heal backup next to the file, filters, retrains the ensemble, saves."""
import os
import pickle
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # .../src
import numpy as np

LO, HI = 798, 897                                     # the poisoned observe-index window


def main(path):
    bak = path + ".vor-heal"
    shutil.copyfile(path, bak)
    with open(path, "rb") as f:
        blob = pickle.load(f)
    world = blob["world"]
    n0 = len(world._X)
    keep = [i for i in range(n0) if not (LO <= i < HI and float(world._Y[i][0]) < 0.5)]
    dropped = n0 - len(keep)
    world._X = [world._X[i] for i in keep]
    world._Y = [world._Y[i] for i in keep]
    world.train(epochs=600)
    with open(path, "wb") as f:
        pickle.dump(blob, f)
    print(f"Heal: {dropped} verrauschte Misserfolgs-Labels entfernt ({n0} -> {len(world._X)}), "
          f"Ensemble nachtrainiert.  Backup: {bak}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "src/pc_cvnn/state/act23_state.pkl")
