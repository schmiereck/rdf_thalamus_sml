"""Run one disposable ACT23 D0 evaluation and reject in-process learner mutation.

Usage (after the parallel ACT23 run has released the machine)::

    ..\\rdf_thalamus_sml\\.venv\\Scripts\\python.exe src\\pc_cvnn\\act23_d0_evaluation_runner.py \
        --state src\\pc_cvnn\\state\\dream_rsi_d0_20260917\\base.pkl --episodes 4

The runner copies the input state below ``log/d0-preflight/`` and never points ACT23 at the
source file.  It is a preflight, not a learning run: its successful outcome is *no learner
mutation*.  If it reports mutation, that is the result to fix before a D0 comparison is run.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.arm_modules.d0_integrity import changed_components


ROOT = Path(__file__).resolve().parents[2]
ACT23 = ROOT / "src" / "pc_cvnn" / "pc_act23.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_assignment(text: str) -> tuple[str, str]:
    key, sep, value = text.partition("=")
    if not sep or not key.startswith("ACT"):
        raise argparse.ArgumentTypeError("--set erwartet ACT23_NAME=Wert")
    return key, value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path, required=True, help="existing source state; read and copied only")
    parser.add_argument("--episodes", type=int, default=1, help="fixed AUTO episode count (default: 1)")
    parser.add_argument("--output", type=Path, default=None, help="new or empty result directory")
    parser.add_argument("--python", type=Path, default=Path(sys.executable), help="venv Python executable")
    parser.add_argument("--set", action="append", type=parse_assignment, default=[], metavar="ACT23_X=V")
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error("--episodes muss mindestens 1 sein")
    source = args.state.resolve()
    if not source.is_file():
        parser.error(f"Zustand fehlt: {source}")
    if not args.python.is_file():
        parser.error(f"Python fehlt: {args.python}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or ROOT / "log" / "d0-preflight" / stamp).resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"Ausgabe ist nicht leer: {output}")
    output.mkdir(parents=True, exist_ok=True)
    manifests = output / "manifests"
    copied = output / "state-input.pkl"
    shutil.copy2(source, copied)
    input_hash = sha256(source)
    copied_hash_before = sha256(copied)

    env = os.environ.copy()
    env.update({
        "ACT23_VIZ": "1", "ACT23_VIZ_HEADLESS": "1", "ACT23_STATE_HEADLESS": "1",
        "ACT23_AUTO_N": str(args.episodes), "ACT23_STATE_PATH": str(copied),
        "ACT23_NO_PERSIST": "1", "ACT23_D0_MANIFEST_DIR": str(manifests),
        "ACT23_D0_CREDIT_JSONL": str(output / "credit.jsonl"),
        "ACT23_CHOREO": "fsm", "ACT23_AUTO_CURIOUS": "0", "ACT23_AUTO_OBJ": "L",
    })
    env.update(dict(args.set))
    command = [str(args.python), str(ACT23)]
    with (output / "act23.log").open("w", encoding="utf-8", newline="\n") as log:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   check=False)

    result = {"schema": "act23-d0-preflight-v1", "created_at": datetime.now(timezone.utc).isoformat(),
              "command": command, "returncode": completed.returncode, "source_state": str(source),
              "source_sha256": input_hash, "copied_sha256_before": copied_hash_before,
              "copied_sha256_after": sha256(copied), "episodes": args.episodes,
              "settings": {key: env[key] for key in sorted(env) if key.startswith("ACT23_D0_")}}
    try:
        before = json.loads((manifests / "before.json").read_text(encoding="utf-8"))
        after = json.loads((manifests / "after.json").read_text(encoding="utf-8"))
        result["changed_components"] = changed_components(before, after)
        result["passed"] = completed.returncode == 0 and not result["changed_components"] and \
            result["copied_sha256_before"] == result["copied_sha256_after"]
    except FileNotFoundError as error:
        result["passed"] = False
        result["error"] = f"missing manifest: {error.filename}"
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"D0 preflight: {'PASS' if result['passed'] else 'FAIL'} -> {output}")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
