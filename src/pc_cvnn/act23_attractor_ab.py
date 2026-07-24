"""A/B harness for Etappe 3 (latent-attractor place planning) vs the plain latent servo.

Both arms run the SAME headless curiosity auto-loop (ACT23_AUTO_N) from a COPY of the same
base state with the SAME seed, differing ONLY in ACT23_CHOREO:
  arm N ("netz")      -> place target driven by lgoal.servo (the current baseline)
  arm A ("attractor") -> place target driven by LatentAttractorController.plan_step (Etappe 3)

In both arms the runtime policy drives the grasp (attractor is a netz-family mode); only the
carry PLACE target differs, so the A/B isolates exactly what Etappe 3 changes.  The live pkl is
never touched (each arm writes its own copy).  Deliveries are parsed from the logs (episode +
result pairing -- NEVER Select-String, the case-insensitive trap).

Usage (repo root):
  python src/pc_cvnn/act23_attractor_ab.py --base src/pc_cvnn/state/act23_state.pkl \
      --episodes 120 --seed 7            # optional: --obj L-Form   --tag attrAB
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(os.path.dirname(REPO), "log") if REPO.endswith("src") else os.path.join(REPO, "log")


def arm_env(state_path, choreo, episodes, seed, obj):
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": "src",
        "ACT23_STATE_PATH": os.path.abspath(state_path),
        "ACT23_STATE_HEADLESS": "1",
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1",
        "ACT23_AUTO_N": str(episodes),
        "ACT23_CHOREO": choreo,
        "ACT16_CLOSE_GUARD": "0", "ACT16_REFLEX": "0",
        "ACT23_YAW_AB": "1", "ACT_FOVEA_ZOOM": "1",
        "ACT23_SEED": str(seed),
    })
    if obj:
        env["ACT23_AUTO_OBJ"] = obj
    return env


def deliveries(logpath):
    """Return (delivered, total) parsed by pairing [Auto i] header with its result line."""
    dev = tot = 0
    cur = None
    for line in open(logpath, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*\[Auto (\d+)\] .+ \| Greifen", line)
        if m:
            cur = int(m.group(1)); continue
        m = re.match(r"\s*\[Auto (\d+)\] (GELIEFERT|NICHT geliefert)\s*\|\s*Abstand (\d+) mm", line)
        if m and cur is not None and int(m.group(1)) == cur:
            tot += 1; dev += (m.group(2) == "GELIEFERT"); cur = None
    return dev, tot


def dyn_active(logpath):
    """How many episodes actually trained the latent dynamics (Etappe 2 alive-check)."""
    return sum(1 for ln in open(logpath, encoding="utf-8", errors="replace")
               if "[Latent-Dynamics] Übergang beobachtet" in ln)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="start state pickle (copied, never written)")
    ap.add_argument("--episodes", type=int, default=120)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--obj", default="", help="optional ACT23_AUTO_OBJ label substring / comma list")
    ap.add_argument("--tag", default="attrAB")
    args = ap.parse_args()

    os.makedirs(LOG, exist_ok=True)
    results = {}
    for choreo in ("netz", "attractor"):
        cp = os.path.join(os.path.dirname(args.base), f"act23_{args.tag}_{choreo}.pkl")
        shutil.copyfile(args.base, cp)
        logf = os.path.join(LOG, f"{args.tag}_{choreo}.txt")
        print(f"Arm {choreo}: {args.episodes} Episoden, Seed {args.seed} -> {logf}", flush=True)
        env = arm_env(cp, choreo, args.episodes, args.seed, args.obj)
        with open(logf, "w", encoding="utf-8") as fh:
            subprocess.run([sys.executable, "src/pc_cvnn/pc_act23.py"], env=env,
                           stdout=fh, stderr=subprocess.STDOUT, cwd=os.getcwd())
        dev, tot = deliveries(logf)
        results[choreo] = (dev, tot, dyn_active(logf), logf)
        print(f"  -> {dev}/{tot} geliefert; Latent-Dynamics aktiv in {results[choreo][2]} Ep", flush=True)

    print("\n=== A/B ERGEBNIS (netz-Servo vs Attraktor-Platzierung) ===")
    for choreo in ("netz", "attractor"):
        dev, tot, dyn, logf = results[choreo]
        pct = 100.0 * dev / tot if tot else 0.0
        print(f"  {choreo:10s}: {dev:3d}/{tot:<3d} = {pct:4.1f}%   (Latent-Dynamics aktiv {dyn}/{tot})")
    n_dev, n_tot, _, _ = results["netz"]
    a_dev, a_tot, _, _ = results["attractor"]
    print(f"\n  Delta Attraktor - Netz: {a_dev - n_dev:+d} Lieferungen "
          f"({100.0*a_dev/max(a_tot,1) - 100.0*n_dev/max(n_tot,1):+.1f} Prozentpunkte)")
    print("  (ein Lauf/Seed = suggestiv; bei Interesse mehrere Seeds mitteln)")


if __name__ == "__main__":
    main()
