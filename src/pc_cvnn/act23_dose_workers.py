"""Worker-merge scaffold for act23 dose runs (parallel label harvest).

The serial dose runs (learnD/learnE, 2026-07-17) used ONE core for ~14h because lifelong
episodes are sequential.  This scaffold trades strict on-policy adaptivity for throughput:

  round r:  copy the current merged state -> W worker copies (distinct ACT23_SEED each)
            run W pc_act23.py headless self-play processes in parallel (M episodes each)
            MERGE: append every worker's NEW world-model rows (_X/_Y beyond the row count
            the round started with) onto the merged state's world model, retrain once
  repeat R rounds (the sync point refreshes each worker's exploration model -- the classic
  actor pattern; more rounds = closer to on-policy, 1 round = pure batch harvest)
  finally: optional netz eval phase on the merged state.

ONLY the world model merges.  Every other learner (runtime policy DAgger, self-imitation,
colour classes, fovea) advances on worker 0's copy alone and the others' progress is
DISCARDED -- merging open-set class births from divergent workers would need identity
resolution this scaffold deliberately does not attempt.  For wrist/grasp dose questions the
world model is the target; document any other use accordingly.

Usage (PowerShell, repo root):
  $env:PYTHONPATH='src'
  python src/pc_cvnn/act23_dose_workers.py --base src/pc_cvnn/state/act23_state.pkl `
      --out src/pc_cvnn/state/act23_doseU.pkl --obj U-Form --workers 6 --episodes 25 `
      --rounds 4 --eval 40 --tag doseU
Logs: log/<tag>_r<round>_w<worker>.txt, merge summary on stdout, eval log log/<tag>_eval.txt.
"""
from __future__ import annotations

import argparse
import os
import pickle
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../src -> repo root
LOG = os.path.join(os.path.dirname(REPO), "log") if REPO.endswith("src") else os.path.join(REPO, "log")


def load(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def worker_env(state_path, obj, episodes, seed, choreo="fsm", cross=None):
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": "src",
        "ACT23_STATE_PATH": os.path.abspath(state_path),
        "ACT23_STATE_HEADLESS": "1",
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1",
        "ACT23_AUTO_OBJ": obj, "ACT23_AUTO_N": str(episodes),
        "ACT23_CHOREO": choreo,
        "ACT16_CLOSE_GUARD": "0", "ACT16_REFLEX": "0",
        "ACT23_LOG": "0", "ACT23_YAW_AB": "1", "ACT_FOVEA_ZOOM": "1",
        "ACT23_SEED": str(seed),
    })
    if cross is not None:
        env["ACT23_WORLD_CROSS"] = cross
    return env


def run_workers(procs):
    """Wait for all workers; report per-worker exit codes."""
    codes = []
    for i, (p, logf) in enumerate(procs):
        p.wait()
        codes.append(p.returncode)
        if p.returncode != 0:
            print(f"  Worker {i}: EXIT {p.returncode} (siehe {logf})", flush=True)
    return codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="start state pickle (copied, never written)")
    ap.add_argument("--out", required=True, help="merged state pickle to write")
    ap.add_argument("--obj", default="L-Form", help="ACT23_AUTO_OBJ label substring (comma list ok)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--episodes", type=int, default=25, help="episodes per worker per round")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--eval", type=int, default=0, help="netz eval episodes on the merged state at the end")
    ap.add_argument("--tag", default="dose")
    ap.add_argument("--cross", default=None, help="ACT23_WORLD_CROSS override for workers+eval ('0'/'1')")
    ap.add_argument("--seed0", type=int, default=100)
    args = ap.parse_args()

    os.makedirs(LOG, exist_ok=True)
    shutil.copyfile(args.base, args.out)
    t0 = time.time()
    total_new = 0
    for r in range(args.rounds):
        n0 = len(load(args.out)["world"]._X)                 # row count every worker starts from
        wpaths = []
        procs = []
        for wi in range(args.workers):
            wp = args.out + f".w{wi}"
            shutil.copyfile(args.out, wp)
            wpaths.append(wp)
            logf = os.path.join(LOG, f"{args.tag}_r{r}_w{wi}.txt")
            env = worker_env(wp, args.obj, args.episodes, seed=args.seed0 + r * 100 + wi,
                             cross=args.cross)
            procs.append((subprocess.Popen([sys.executable, "src/pc_cvnn/pc_act23.py"],
                                           env=env, stdout=open(logf, "w", encoding="utf-8"),
                                           stderr=subprocess.STDOUT, cwd=os.getcwd()), logf))
        print(f"Runde {r}: {args.workers} Worker x {args.episodes} Episoden gestartet "
              f"(Basis {n0} Welt-Zeilen) ...", flush=True)
        run_workers(procs)
        # MERGE: worker 0's whole state carries forward (its non-world learners advanced M
        # episodes); the OTHER workers contribute only their new world rows on top.
        blob = load(wpaths[0])
        new = len(blob["world"]._X) - n0
        for wp in wpaths[1:]:
            wb = load(wp)["world"]
            blob["world"]._X.extend(wb._X[n0:])
            blob["world"]._Y.extend(wb._Y[n0:])
            new += len(wb._X) - n0
        blob["world"].train(epochs=600)
        with open(args.out, "wb") as f:
            pickle.dump(blob, f)
        for wp in wpaths:
            os.remove(wp)
        total_new += new
        print(f"Runde {r}: +{new} Welt-Zeilen (gesamt neu {total_new}), Modell nachtrainiert, "
              f"{(time.time() - t0) / 60:.0f} min", flush=True)
    if args.eval:
        logf = os.path.join(LOG, f"{args.tag}_eval.txt")
        env = worker_env(args.out, args.obj, args.eval, seed=args.seed0 + 9999,
                         choreo="netz", cross=args.cross)
        print(f"Eval: {args.eval} Netz-Episoden -> {logf}", flush=True)
        subprocess.run([sys.executable, "src/pc_cvnn/pc_act23.py"], env=env,
                       stdout=open(logf, "w", encoding="utf-8"), stderr=subprocess.STDOUT,
                       cwd=os.getcwd())
    print(f"FERTIG: {total_new} neue Welt-Zeilen in {args.out} "
          f"({(time.time() - t0) / 60:.0f} min)", flush=True)


if __name__ == "__main__":
    main()
