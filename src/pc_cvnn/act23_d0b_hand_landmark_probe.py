"""D0b visual hand-landmark preflight.

This is a diagnostic fixture, not an ACT23 controller.  It uses a small *executed* gripper
open/close pulse and the difference of the two camera frames as the self-supervised signal.
The evaluator renders the two claw geoms in a private colour into a separate JSONL file; that
geometry is never returned by :func:`motion_landmark` and is not usable by a future learner.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mujoco
import numpy as np

from pc_cvnn.pc_act14 import BracketArmSim, HOME, reach_step


# A small, fixed measurement grid.  The reached pose, rather than this requested position, is
# written to the record because the body model can miss a requested point at the workspace edge.
POSES = ((-0.08, 0.10, 0.10), (0.00, 0.12, 0.10), (0.08, 0.14, 0.10),
         (-0.06, 0.18, 0.11), (0.06, 0.18, 0.11), (0.00, 0.20, 0.10))
OPEN, CLOSED = 0.54, 0.05


def motion_landmark(open_img: np.ndarray, closed_img: np.ndarray, threshold: float = 35.0):
    """Return only the camera-derived difference centroid and its support.

    A future head may use the whole difference field.  This deliberately weak centroid is a
    baseline: it establishes whether the controlled self-motion reaches the image at all.
    """
    delta = np.abs(open_img.astype(np.int16) - closed_img.astype(np.int16)).sum(axis=2)
    yy, xx = np.where(delta > threshold)
    if not len(xx):
        return None, 0
    weights = delta[yy, xx].astype(float)
    return [float(np.average(xx, weights=weights)), float(np.average(yy, weights=weights))], int(len(xx))


def _freeze_arm(sim: BracketArmSim):
    for joint in HOME:
        sim.target(joint, sim.d.qpos[sim.jqadr[joint]])


def _frame_at_grip(sim: BracketArmSim, grip: float) -> np.ndarray:
    sim.target("joint_5", grip)
    sim.step(80)  # actual actuator motion; no qpos edit is used for the self-supervised observation
    return sim.render("overview")


def external_claw_landmark(sim: BracketArmSim):
    """Evaluator only: render claw geoms in magenta and return their visible centroid."""
    original = sim.m.geom_rgba.copy()
    try:
        sim.m.geom_rgba[:, 3] = 0.0
        for name in ("claw_left", "claw_right"):
            gid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_GEOM, name)
            sim.m.geom_rgba[gid] = (1.0, 0.0, 1.0, 1.0)
        image = sim.render("overview")
        mask = (image[:, :, 0] > 150) & (image[:, :, 2] > 150) & (image[:, :, 1] < 50)
        yy, xx = np.where(mask)
        return None if not len(xx) else [float(xx.mean()), float(yy.mean())]
    finally:
        sim.m.geom_rgba[:] = original


def _park_objects(sim: BracketArmSim):
    for name in ("obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"):
        sim.set_object(name, (0.50, -0.60), z=0.012)


def run(output: Path, poses=POSES):
    output.mkdir(parents=True, exist_ok=True)
    visual_path, eval_path = output / "visual.jsonl", output / "eval.jsonl"
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rows = []
    try:
        for pose_id, requested in enumerate(poses, 1):
            sim.reset_home(); sim.set_reach_site("contact"); _park_objects(sim)
            for _ in range(320):
                reach_step(sim, np.asarray(requested, float), gain=2.0, max_dq=0.03)
                sim.step(2)
            _freeze_arm(sim)
            open_img = _frame_at_grip(sim, OPEN)
            closed_img = _frame_at_grip(sim, CLOSED)
            landmark, support = motion_landmark(open_img, closed_img)
            truth = external_claw_landmark(sim)
            record = {"schema": "act23-d0b-hand-visual-v1", "pose_id": pose_id,
                      "requested_xyz": list(requested), "reached_xyz": [float(x) for x in sim.grasp_pos()],
                      "open_angle": OPEN, "closed_angle": CLOSED,
                      "motion_landmark_px": landmark, "motion_support_px": support}
            evaluation = {"schema": "act23-d0b-hand-eval-v1", "pose_id": pose_id,
                          "truth_claw_px": truth}
            with visual_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
            with eval_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(evaluation, sort_keys=True) + "\n")
            if landmark is not None and truth is not None:
                rows.append(float(np.linalg.norm(np.asarray(landmark) - np.asarray(truth))))
    finally:
        sim._renderer.close()
    result = {"poses": len(poses), "paired_visible": len(rows),
              "median_error_px": None if not rows else float(np.median(rows)),
              "max_error_px": None if not rows else float(max(rows)),
              "within_20px": int(sum(error <= 20.0 for error in rows)),
              "visual": str(visual_path), "evaluation": str(eval_path)}
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="D0b camera-only gripper-motion landmark audit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-poses", type=int, default=0,
                        help="additional fixed-seed workspace samples after the six diagnostic poses")
    parser.add_argument("--seed", type=int, default=101)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    extra = tuple(tuple(float(x) for x in row) for row in np.column_stack((
        rng.uniform(-0.08, 0.08, args.random_poses),
        rng.uniform(0.10, 0.18, args.random_poses),
        rng.uniform(0.10, 0.14, args.random_poses),
    )))
    print(json.dumps(run(args.output, POSES + extra), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
