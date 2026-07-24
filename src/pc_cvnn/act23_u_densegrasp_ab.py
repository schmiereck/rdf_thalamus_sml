"""A/B harness for the U grasp-point fix (ACT23_U_DENSEGRASP): thin-rim vs solid-base grip.

The 746-log U mechanism-ID (2026-07-24) showed U fails mostly as "greift ins Leere" (47%
nicht-gegriffen): select() returns grasp_xy = material nearest the CENTROID, and a U's centroid sits
in its concavity -> the grip lands on a 1-2px-thin inner rim (UDIAG: densest base point is 8px, 16-21mm
away).  This runs the SAME headless U-only auto-loop from a COPY of the same base state with the SAME
seed, differing ONLY in ACT23_U_DENSEGRASP:
  arm A ("off") -> grip the nearest-material point (current behaviour)
  arm B ("on")  -> grip the DENSEST (base) point (perceive_all grasp_dense)

Deliveries AND grasp-misses are parsed from the logs (episode + result pairing + the [Kredit]
"nicht gegriffen" line -- NEVER Select-String).  The live pkl is never touched.

Usage (repo root):
  python src/pc_cvnn/act23_u_densegrasp_ab.py --base src/pc_cvnn/state/act23_state.pkl \
      --episodes 80 --seed 11            # optional: --tag uDenseAB
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


def arm_env(state_path, densegrasp, episodes, seed):
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": "src",
        "ACT23_STATE_PATH": os.path.abspath(state_path),
        "ACT23_STATE_HEADLESS": "1",
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1",
        "ACT23_AUTO_N": str(episodes),
        "ACT23_AUTO_OBJ": "U-Form",             # U ONLY -- isolate the grasp-point change
        "ACT23_U_DENSEGRASP": "1" if densegrasp else "0",
        "ACT16_CLOSE_GUARD": "0", "ACT16_REFLEX": "0",
        "ACT23_YAW_AB": "1", "ACT_FOVEA_ZOOM": "1",
        "ACT23_SEED": str(seed),
    })
    return env


def parse(logpath):
    """Return (delivered, total, nicht_gegriffen) pairing [Auto i] header with its result + [Kredit]."""
    dev = tot = ng = 0
    cur = None
    cur_ng = False
    for line in open(logpath, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*\[Auto (\d+)\] .+ \| Greifen", line)
        if m:
            cur = int(m.group(1)); cur_ng = False; continue
        if cur is not None and "nicht gegriffen (Policy)" in line:
            cur_ng = True; continue
        m = re.match(r"\s*\[Auto (\d+)\] (GELIEFERT|NICHT geliefert)\s*\|\s*Abstand (\d+) mm", line)
        if m and cur is not None and int(m.group(1)) == cur:
            tot += 1; dev += (m.group(2) == "GELIEFERT"); ng += cur_ng
            cur = None; cur_ng = False
    return dev, tot, ng


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="start state pickle (copied, never written)")
    ap.add_argument("--episodes", type=int, default=80)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--tag", default="uDenseAB")
    args = ap.parse_args()

    os.makedirs(LOG, exist_ok=True)
    results = {}
    for name, dg in (("off", False), ("on", True)):
        cp = os.path.join(os.path.dirname(args.base), f"act23_{args.tag}_{name}.pkl")
        shutil.copyfile(args.base, cp)
        logf = os.path.join(LOG, f"{args.tag}_{name}.txt")
        print(f"Arm U_DENSEGRASP={name}: {args.episodes} Episoden, Seed {args.seed} -> {logf}", flush=True)
        env = arm_env(cp, dg, args.episodes, args.seed)
        with open(logf, "w", encoding="utf-8") as fh:
            subprocess.run([sys.executable, "src/pc_cvnn/pc_act23.py"], env=env,
                           stdout=fh, stderr=subprocess.STDOUT, cwd=os.getcwd())
        dev, tot, ng = parse(logf)
        results[name] = (dev, tot, ng, logf)
        pct = 100.0 * dev / tot if tot else 0.0
        print(f"  -> {dev}/{tot} = {pct:.0f}% geliefert; nicht-gegriffen {ng}/{tot}", flush=True)

    print("\n=== A/B ERGEBNIS (U-Griffpunkt: Kante vs Basis) ===")
    for name in ("off", "on"):
        dev, tot, ng, _ = results[name]
        pct = 100.0 * dev / tot if tot else 0.0
        ngp = 100.0 * ng / tot if tot else 0.0
        print(f"  DENSEGRASP={name:3s}: {dev:3d}/{tot:<3d} = {pct:4.1f}% geliefert   nicht-gegriffen {ng}/{tot} = {ngp:.0f}%")
    o_dev, o_tot, o_ng, _ = results["off"]
    n_dev, n_tot, n_ng, _ = results["on"]
    print(f"\n  Delta Basis - Kante: {n_dev - o_dev:+d} Lieferungen "
          f"({100.0*n_dev/max(n_tot,1) - 100.0*o_dev/max(o_tot,1):+.1f} pp)   "
          f"nicht-gegriffen {100.0*n_ng/max(n_tot,1) - 100.0*o_ng/max(o_tot,1):+.1f} pp")
    print("  (ein Lauf/Seed = suggestiv; bei Interesse mehrere Seeds mitteln)")


if __name__ == "__main__":
    main()
