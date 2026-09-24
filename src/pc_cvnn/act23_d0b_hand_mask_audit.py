"""Offline D0b audit for a learned visual self-motion mask.

The model is a spatially shared linear patch readout, trained only on RGB camera frames and their
own executed gripper-motion fields.  The position split is by complete probe pose.  Private claw
geometry is read only after prediction from the separately written evaluator JSONL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _downsample(array: np.ndarray, side: int = 40) -> np.ndarray:
    """Area-average an image batch to a square map without external image dependencies."""
    n, height, width = array.shape[:3]
    if height % side or width % side:
        raise ValueError(f"{height}x{width} cannot be area-reduced to {side}x{side}")
    return array.reshape(n, side, height // side, side, width // side, *array.shape[3:]).mean(axis=(2, 4))


def _patch_features(rgb: np.ndarray) -> np.ndarray:
    """3x3 RGB patches at each pixel; the same weights apply at every image position."""
    padded = np.pad(rgb.astype(np.float64) / 255.0, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
    patches = [padded[:, 1 + dy:1 + dy + rgb.shape[1], 1 + dx:1 + dx + rgb.shape[2], :]
               for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    return np.concatenate(patches + [np.ones((*rgb.shape[:3], 1))], axis=3)


def _fit(features: np.ndarray, target: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    x, y = features.reshape(-1, features.shape[-1]), target.reshape(-1)
    gram = x.T @ x + ridge * np.eye(x.shape[1])
    return np.linalg.solve(gram, x.T @ y)


def _predict(features: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, np.einsum("nhwf,f->nhw", features, weights))


def _centroid(mask: np.ndarray, full_side: int = 240) -> list[float] | None:
    mass = float(mask.sum())
    if mass <= 1e-12:
        return None
    side = mask.shape[0]
    yy, xx = np.mgrid[:side, :side]
    scale = full_side / side
    return [float((xx * mask).sum() / mass * scale + 0.5 * scale),
            float((yy * mask).sum() / mass * scale + 0.5 * scale)]


def _load_truth(path: Path) -> dict[int, list[float] | None]:
    return {int(row["pose_id"]): row["truth_claw_px"]
            for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())}


def run(frames_path: Path, eval_path: Path, output: Path):
    data = np.load(frames_path)
    pose_id = data["pose_id"].astype(int)
    # Only complete poses enter either split.  This fixed modulo split cannot leak adjacent frames.
    test = pose_id % 3 == 0
    rgb = _downsample(data["open_rgb"], side=40)
    target = _downsample(data["motion_rgb_l1"][..., None], side=40)[..., 0] / 765.0
    features = _patch_features(rgb)
    weights = _fit(features[~test], target[~test])
    prediction = _predict(features, weights)
    truth = _load_truth(eval_path)
    records, errors = [], []
    base = float(target[~test].mean())
    for i, pid in enumerate(pose_id):
        if not test[i]:
            continue
        landmark = _centroid(prediction[i])
        expected = truth.get(int(pid))
        error = None if landmark is None or expected is None else float(np.linalg.norm(np.subtract(landmark, expected)))
        if error is not None:
            errors.append(error)
        records.append({"schema": "act23-d0b-hand-mask-prediction-v1", "pose_id": int(pid),
                        "motion_landmark_px": landmark, "truth_claw_px": expected, "error_px": error,
                        "mask_mse": float(np.mean((prediction[i] - target[i]) ** 2)),
                        "constant_mse": float(np.mean((base - target[i]) ** 2))})
    output.mkdir(parents=True, exist_ok=True)
    with (output / "predictions.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    result = {"schema": "act23-d0b-hand-mask-result-v1", "train_poses": int((~test).sum()),
              "test_poses": int(test.sum()), "paired_test_poses": len(errors),
              "median_error_px": None if not errors else float(np.median(errors)),
              "within_20px": int(sum(error <= 20.0 for error in errors)),
              "mask_mse": float(np.mean([r["mask_mse"] for r in records])),
              "constant_mse": float(np.mean([r["constant_mse"] for r in records])),
              "frames": str(frames_path), "evaluation": str(eval_path)}
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Audit a learned D0b hand self-motion mask")
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.frames, args.evaluation, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
