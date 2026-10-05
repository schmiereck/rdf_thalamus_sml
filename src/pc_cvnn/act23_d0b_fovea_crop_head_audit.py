"""D0b-F1a: isolated learned crop head for the agent's own gripper-motion signal.

This script does not load or alter an ACT23 checkpoint.  It samples RGB with the same hex-Fovea
geometry, trains a fresh NumPy MLP on the agent-visible pulse-difference target, and reads private
claw geometry only after its test-time saccade choice is fixed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.pc_act18 import hex_sample

GRID = np.asarray([(72.0, 72.0), (120.0, 72.0), (168.0, 72.0),
                   (72.0, 120.0), (120.0, 120.0), (168.0, 120.0),
                   (72.0, 168.0), (120.0, 168.0), (168.0, 168.0)])


def _truth(path: Path) -> dict[int, list[float] | None]:
    return {int(row["pose_id"]): row["truth_claw_px"]
            for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())}


def _mass_at(motion: np.ndarray, gaze: np.ndarray, radius: float = 24.0) -> float:
    yy, xx = np.mgrid[:motion.shape[0], :motion.shape[1]]
    inside = (xx - gaze[0]) ** 2 + (yy - gaze[1]) ** 2 <= radius ** 2
    return float(motion[inside].sum() / (motion.sum() + 1e-12))


def _crop_features(images: np.ndarray) -> np.ndarray:
    """8x8xRGB spatial crops; pooling preserves layout while keeping the fresh head small."""
    rows = []
    for image in images:
        per_pose = []
        for gaze in GRID:
            rgb = hex_sample(image, gaze, 4.0)[:, :, 1:] / 255.0
            per_pose.append(rgb.reshape(8, 2, 8, 2, 3).mean(axis=(1, 3)).reshape(-1))
        rows.append(per_pose)
    return np.asarray(rows)


def _sigmoid(value):
    return 1.0 / (1.0 + np.exp(-np.clip(value, -40.0, 40.0)))


def _train(x: np.ndarray, y: np.ndarray, seed: int, hidden: int = 32, epochs: int = 600, lr: float = 0.08):
    rng = np.random.default_rng(seed)
    mean, scale = x.mean(0), x.std(0)
    scale[scale < 1e-8] = 1.0
    x = (x - mean) / scale
    w1 = rng.normal(0.0, 1.0 / np.sqrt(x.shape[1]), (x.shape[1], hidden)); b1 = np.zeros(hidden)
    w2 = rng.normal(0.0, 1.0 / np.sqrt(hidden), hidden); b2 = 0.0
    pos = max(float(y.mean()), 1e-3); weights = np.where(y > 0.5, 0.5 / pos, 0.5 / (1.0 - pos))
    for _ in range(epochs):
        pre = x @ w1 + b1; h = np.maximum(pre, 0.0); score = _sigmoid(h @ w2 + b2)
        grad_score = weights * (score - y) / len(y)
        grad_w2 = h.T @ grad_score; grad_b2 = float(grad_score.sum())
        grad_h = grad_score[:, None] * w2[None, :]
        grad_pre = grad_h * (pre > 0.0)
        w1 -= lr * (x.T @ grad_pre); b1 -= lr * grad_pre.sum(0); w2 -= lr * grad_w2; b2 -= lr * grad_b2
    return mean, scale, w1, b1, w2, b2


def _score(x, model):
    mean, scale, w1, b1, w2, b2 = model
    h = np.maximum((x - mean) / scale @ w1 + b1, 0.0)
    return _sigmoid(h @ w2 + b2)


def run(frames: Path, evaluation: Path, output: Path, seeds=(11, 17, 23)):
    data = np.load(frames); pose_id, images, motion = data["pose_id"].astype(int), data["open_rgb"], data["motion_rgb_l1"]
    features = _crop_features(images)
    mass = np.asarray([[_mass_at(item, gaze) for gaze in GRID] for item in motion])
    labels = (mass >= 0.10).astype(float)
    test = pose_id % 3 == 0
    truth = _truth(evaluation); output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for seed in seeds:
        model = _train(features[~test].reshape(-1, features.shape[-1]), labels[~test].reshape(-1), seed)
        scores = _score(features.reshape(-1, features.shape[-1]), model).reshape(len(pose_id), len(GRID))
        rows, errors = [], []
        for i, pid in enumerate(pose_id):
            if not test[i]:
                continue
            choice = int(np.argmax(scores[i])); expected = truth.get(int(pid)); selected = GRID[choice].tolist()
            error = None if expected is None else float(np.linalg.norm(np.subtract(selected, expected)))
            if error is not None:
                errors.append(error)
            rows.append({"schema": "act23-d0b-fovea-crop-head-prediction-v1", "seed": seed,
                         "pose_id": int(pid), "selected_gaze_px": selected, "truth_claw_px": expected,
                         "error_px": error, "self_motion_mass": float(mass[i, choice]),
                         "scores": [float(v) for v in scores[i]]})
        with (output / f"predictions-seed{seed}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        summaries.append({"seed": seed, "paired_test_poses": len(errors),
                          "median_error_px": None if not errors else float(np.median(errors)),
                          "within_24px": int(sum(error <= 24.0 for error in errors))})
    passed = [row for row in summaries if row["median_error_px"] is not None
              and row["median_error_px"] <= 40.0 and row["within_24px"] >= 9]
    result = {"schema": "act23-d0b-fovea-crop-head-result-v1", "train_poses": int((~test).sum()),
              "test_poses": int(test.sum()), "seeds": summaries, "contract_passes": len(passed),
              "contract_pass": len(passed) >= 2, "frames": str(frames), "evaluation": str(evaluation)}
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="D0b-F1a isolated learned Fovea-crop head audit")
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.frames, args.evaluation, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
