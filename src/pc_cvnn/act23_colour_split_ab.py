"""A/B harness for the merged-blob colour recovery (ACT23_COLOUR_SPLIT).

Mechanism-ID (log/red_l_diag.png, 2026-07-24): perceive_all averages chroma over a whole connected
component, so two objects closer than ~40mm fuse into ONE component whose mean lands on whichever
object has MORE pixels -- the red cube beside the larger orange L reads as the L's class.  The red
command then finds ZERO candidates, loses its fovea servo for the entire episode (the user's 24-ep
GUI log: red missing the [Fovea-Servo] line in 5 of 6 episodes) and drops through to the old trained
vc hex code, which grasps the L (user-observed).  Measured centroid error over gaps 70/50/38/28mm:
whole-component 0/0/25/20mm, pixel colour split 6/6/6/5mm.

Unlike the U A/B this runs the MIXED auto loop (all objects): the fusion only happens when a
neighbour is close, which a single-object loop almost never produces -- a red-only run showed the
colour path succeeding 15/15 with no fusion at all, so it cannot measure this fix.

Both arms start from a COPY of the same base state with the same seed and differ ONLY in
ACT23_COLOUR_SPLIT.  Parsed per arm: deliveries overall and per object, how often the split actually
fired, and how often an episode ran BLIND (no [Fovea-Servo] line at all).  The live pkl is never
touched.  NEVER Select-String (case-insensitive trap) -- parsing is done here.

Usage (repo root):
  python src/pc_cvnn/act23_colour_split_ab.py --base src/pc_cvnn/state/act23_state.pkl \
      --episodes 60 --seed 11            # optional: --tag colSplitAB
"""
from __future__ import annotations

import argparse
import collections
import io
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(os.path.dirname(REPO), "log") if REPO.endswith("src") else os.path.join(REPO, "log")

HDR = re.compile(r"^\s*\[Auto (\d+)\] (.+?) \| (Greifen|Schieben)")
RES = re.compile(r"^\s*\[Auto (\d+)\] (GELIEFERT|NICHT geliefert)\s*\|\s*Abstand (\d+) mm")


def arm_env(state_path, split, episodes, seed):
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": "src",
        "ACT23_STATE_PATH": os.path.abspath(state_path),
        "ACT23_STATE_HEADLESS": "1",
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1",
        "ACT23_AUTO_N": str(episodes),
        "ACT23_COLOUR_SPLIT": "1" if split else "0",
        "ACT23_DEBUG": "1",                     # so the split-fired line is loggable
        "ACT16_CLOSE_GUARD": "0", "ACT16_REFLEX": "0",
        "ACT23_YAW_AB": "1", "ACT_FOVEA_ZOOM": "1",
        "ACT23_SEED": str(seed),
    })
    env.pop("ACT23_AUTO_OBJ", None)              # MIXED loop: fusion needs neighbours
    return env


def parse(logpath):
    """Per-episode blocks -> (per-object [n, delivered, blind], n_split_fired)."""
    per = collections.defaultdict(lambda: [0, 0, 0])
    split_fired = 0
    cur = None
    for ln in io.open(logpath, encoding="utf-8", errors="replace"):
        m = HDR.match(ln)
        if m:
            cur = {"obj": m.group(2).strip(), "i": int(m.group(1)), "fovea": False}
            continue
        m = RES.match(ln)
        if m and cur is not None and int(m.group(1)) == cur["i"]:
            r = per[cur["obj"]]
            r[0] += 1
            r[1] += 1 if m.group(2) == "GELIEFERT" else 0
            r[2] += 0 if cur["fovea"] else 1
            cur = None
            continue
        if cur is not None:
            if "[Fovea-Servo]" in ln:
                cur["fovea"] = True
            if "Farb-Pixel-Split" in ln:
                split_fired += 1
    return per, split_fired


def report(name, per, split_fired):
    tot = sum(v[0] for v in per.values())
    dl = sum(v[1] for v in per.values())
    bl = sum(v[2] for v in per.values())
    print(f"\n  --- COLOUR_SPLIT={name} ---")
    print(f"  {'Objekt':18s} {'n':>4s} {'geliefert':>12s} {'blind (kein Fovea-Log)':>24s}")
    for o in sorted(per, key=lambda k: -per[k][0]):
        n, d, b = per[o]
        print(f"  {o:18s} {n:4d} {d:4d} = {100*d/max(n,1):3.0f}% {b:12d} = {100*b/max(n,1):3.0f}%")
    print(f"  {'GESAMT':18s} {tot:4d} {dl:4d} = {100*dl/max(tot,1):3.0f}% {bl:12d} = {100*bl/max(tot,1):3.0f}%")
    print(f"  Farb-Pixel-Split ausgeloest: {split_fired}x")
    return tot, dl, bl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="start state pickle (copied, never written)")
    ap.add_argument("--episodes", type=int, default=60)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--tag", default="colSplitAB")
    args = ap.parse_args()

    os.makedirs(LOG, exist_ok=True)
    results = {}
    for name, sp in (("off", False), ("on", True)):
        cp = os.path.join(os.path.dirname(args.base), f"act23_{args.tag}_{name}.pkl")
        shutil.copyfile(args.base, cp)
        logf = os.path.join(LOG, f"{args.tag}_{name}.txt")
        print(f"Arm COLOUR_SPLIT={name}: {args.episodes} Episoden (gemischt), Seed {args.seed} -> {logf}",
              flush=True)
        with open(logf, "w", encoding="utf-8") as fh:
            subprocess.run([sys.executable, "src/pc_cvnn/pc_act23.py"],
                           env=arm_env(cp, sp, args.episodes, args.seed),
                           stdout=fh, stderr=subprocess.STDOUT, cwd=os.getcwd())
        per, sf = parse(logf)
        results[name] = (per, sf)
        tot = sum(v[0] for v in per.values()); dl = sum(v[1] for v in per.values())
        print(f"  -> {dl}/{tot} geliefert; Split {sf}x ausgeloest", flush=True)

    print("\n=== A/B ERGEBNIS (verschmolzener Blob: vc-Rueckfall vs Farb-Pixel-Split) ===")
    agg = {}
    for name in ("off", "on"):
        per, sf = results[name]
        agg[name] = report(name, per, sf)
    (t0, d0, b0), (t1, d1, b1) = agg["off"], agg["on"]
    print(f"\n  Delta Split - Rueckfall: {d1 - d0:+d} Lieferungen "
          f"({100.0*d1/max(t1,1) - 100.0*d0/max(t0,1):+.1f} pp)   "
          f"blinde Episoden {100.0*b1/max(t1,1) - 100.0*b0/max(t0,1):+.1f} pp")
    ro = results["off"][0].get("Rotes Wuerfel", [0, 0, 0])
    rn = results["on"][0].get("Rotes Wuerfel", [0, 0, 0])
    print(f"  davon Rotes Wuerfel: {ro[1]}/{ro[0]} -> {rn[1]}/{rn[0]}")
    print("  (ein Lauf/Seed = suggestiv; der Effekt greift NUR in Episoden mit nahem Nachbarn,")
    print("   die Split-Ausloeserate oben sagt, wie viele Episoden ueberhaupt betroffen waren)")


if __name__ == "__main__":
    main()
