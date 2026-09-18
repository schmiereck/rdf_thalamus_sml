"""Run one isolated D0 wrist-training block and audit its self-credit coverage.

The runner never gives ACT23 the source checkpoint as its write target.  It copies that checkpoint
into a new result directory, runs exactly one pinned FSM-L block on the copy, and records whether
the block supplied enough eligible self-labelled wrist credits for the D0 pilot contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACT23 = ROOT / "src" / "pc_cvnn" / "pc_act23.py"
CAUSAL_ROUTES = {"Griff am Objekt fehlgeschlagen (Aktion)", "Griff hielt nicht (Drucksensor)"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wrist_bin(relative_wrist_deg: float) -> int:
    """Map a relative wrist angle to the eight object-symmetric half-turn bins."""
    return int((float(relative_wrist_deg) % 180.0) // 22.5) % 8


def read_credits(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"ungueltige Kreditzeile {number}: {error.msg}") from error
        if not isinstance(record, dict):
            raise ValueError(f"ungueltige Kreditzeile {number}: Objekt erwartet")
        records.append(record)
    return records


def credit_summary(records: list[dict]) -> dict:
    eligible = [record for record in records
                if record.get("action_source") == "Selbst"
                and record.get("label_source") == "Selbst"
                and float(record.get("weight", 0.0)) == 1.0
                and record.get("route") in CAUSAL_ROUTES]
    bins = sorted({wrist_bin(record["relative_wrist_deg"]) for record in eligible
                   if record.get("relative_wrist_deg") is not None})
    routes: dict[str, int] = {}
    for record in eligible:
        route = str(record.get("route"))
        routes[route] = routes.get(route, 0) + 1
    return {"all_records": len(records), "eligible_records": len(eligible),
            "wrist_bins": bins, "wrist_bin_count": len(bins), "routes": routes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path, required=True, help="read-only source checkpoint")
    parser.add_argument("--output", type=Path, required=True, help="new or empty training-line directory")
    parser.add_argument("--episodes", type=int, choices=(60, 120), required=True,
                        help="D0 contract block size")
    parser.add_argument("--seed", type=int, required=True, help="training scene seed")
    parser.add_argument("--python", type=Path, default=Path(sys.executable), help="venv Python executable")
    args = parser.parse_args()
    source, output = args.state.resolve(), args.output.resolve()
    if not source.is_file():
        parser.error(f"Zustand fehlt: {source}")
    if not args.python.is_file():
        parser.error(f"Python fehlt: {args.python}")
    if output.exists() and any(output.iterdir()):
        parser.error(f"Ausgabe ist nicht leer: {output}")
    if output == source.parent:
        parser.error("Ausgabe darf nicht das Quellzustandsverzeichnis sein")

    output.mkdir(parents=True, exist_ok=True)
    trained = output / "state-trained.pkl"
    credits = output / "credit.jsonl"
    shutil.copy2(source, trained)
    source_hash, before_hash = sha256(source), sha256(trained)
    env = os.environ.copy()
    env.update({
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1", "ACT23_STATE_HEADLESS": "1",
        "ACT23_STATE_PATH": str(trained), "ACT23_AUTO_N": str(args.episodes),
        "ACT23_AUTO_OBJ": "L-Form", "ACT23_AUTO_CURIOUS": "0", "ACT23_CHOREO": "fsm",
        "ACT23_SEED": str(args.seed), "ACT23_WRIST_REL": "1", "ACT23_D0_CREDIT_JSONL": str(credits),
        # Explicitly undo an inherited shell setting: this is the mutable training copy.
        "ACT23_NO_PERSIST": "0", "ACT23_D0_FREEZE": "0",
    })
    command = [str(args.python), str(ACT23)]
    with (output / "act23.log").open("w", encoding="utf-8", newline="\n") as log:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   check=False)
    records = read_credits(credits)
    summary = credit_summary(records)
    threshold = 20 if args.episodes == 60 else 40
    coverage_ok = summary["eligible_records"] >= threshold and summary["wrist_bin_count"] >= 4
    result = {
        "schema": "act23-d0-training-block-v1", "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command, "returncode": completed.returncode, "episodes": args.episodes,
        "seed": args.seed, "source_state": str(source), "source_sha256": source_hash,
        "training_copy": str(trained), "copy_sha256_before": before_hash,
        "copy_sha256_after": sha256(trained), "credit_summary": summary,
        "required_eligible_records": threshold, "required_wrist_bins": 4, "coverage_passed": coverage_ok,
        "settings": {key: env[key] for key in sorted(env) if key.startswith("ACT23_")},
    }
    result["passed"] = completed.returncode == 0 and coverage_ok
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"D0 training block: {'PASS' if result['passed'] else 'FAIL'} -> {output}")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
