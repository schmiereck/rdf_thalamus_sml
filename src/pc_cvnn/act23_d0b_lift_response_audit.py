"""Evaluate the preregistered fixed-gaze D0b lift-response rule.

The classifier consumes only the agent-visible frame trace.  Evaluation truth is
joined afterwards solely to score the already emitted labels.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


POSITIVE_THRESHOLD = 1.5
NEGATIVE_THRESHOLD = 0.75


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _label(score: float) -> str:
    if score >= POSITIVE_THRESHOLD:
        return "carried"
    if score <= NEGATIVE_THRESHOLD:
        return "not_carried"
    return "abstain"


def audit(run_dir: Path) -> dict:
    frames = _load_jsonl(run_dir / "fovea_frames.jsonl")
    truth = _load_jsonl(run_dir / "eval_truth.jsonl")
    if len(frames) != len(truth):
        raise ValueError(f"frame/truth count differs: {len(frames)} != {len(truth)}")
    for index, (frame, evaluation) in enumerate(zip(frames, truth)):
        if (frame["episode_id"], frame["phase"]) != (evaluation["episode_id"], evaluation["phase"]):
            raise ValueError(f"frame/truth mismatch at row {index}")

    lifts: dict[int, list[dict]] = defaultdict(list)
    lift_truth: dict[int, bool] = {}
    for frame, evaluation in zip(frames, truth):
        if frame["phase"] != "lift":
            continue
        if not frame.get("lift_probe_fixed_gaze"):
            raise ValueError("lift frame without fixed gaze")
        if frame.get("selection_cell_com") is not None:
            lifts[frame["episode_id"]].append(frame)
        lift_truth[frame["episode_id"]] = bool(evaluation["truth_lifted"])

    rows: list[dict] = []
    for episode_id, sequence in sorted(lifts.items()):
        if len(sequence) < 2:
            continue
        start, end = sequence[0]["selection_cell_com"], sequence[-1]["selection_cell_com"]
        score = math.dist(start, end)
        rows.append({
            "episode_id": episode_id,
            "frames": len(sequence),
            "response_cells": score,
            "label": _label(score),
            "truth_lifted": lift_truth[episode_id],
        })

    labels = Counter(row["label"] for row in rows)
    decided = [row for row in rows if row["label"] != "abstain"]
    tp = sum(row["label"] == "carried" and row["truth_lifted"] for row in decided)
    fp = sum(row["label"] == "carried" and not row["truth_lifted"] for row in decided)
    fn = sum(row["label"] == "not_carried" and row["truth_lifted"] for row in decided)
    tn = sum(row["label"] == "not_carried" and not row["truth_lifted"] for row in decided)
    positives = sum(row["truth_lifted"] for row in rows)
    return {
        "schema": "act23-d0b-lift-response-audit-v1",
        "run_dir": str(run_dir),
        "thresholds_cells": {"carried_at_least": POSITIVE_THRESHOLD, "not_carried_at_most": NEGATIVE_THRESHOLD},
        "lift_episodes": len(lifts),
        "valid_trajectories": len(rows),
        "labels": dict(labels),
        "confusion_decided": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision_carried": None if tp + fp == 0 else tp / (tp + fp),
        "recall_carried": None if positives == 0 else tp / positives,
        "abstention_rate": None if not rows else labels["abstain"] / len(rows),
        "trajectories": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.run_dir)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
