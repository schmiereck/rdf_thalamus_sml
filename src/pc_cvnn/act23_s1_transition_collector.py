"""Collect safe direct-servo proprioceptive transitions for S1.

Each JSONL row is one observed transition ``(q, qvel, ctrl, ctrl_next, q_next,
qvel_next)``.  The fixture has no object, contact, pressure, teacher, IK, or Cartesian target
input.  Whole rollouts, never individual rows, define the held-out split.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.pc_act14 import ARM_JOINTS, BracketArmSim, HOME


# Actual encoders may lag and overshoot a direct position command. Commands use an inner box;
# every recorded encoder state must remain in the outer observation box.
OBS_LOW = np.array([0.80, 0.10, 0.10, 2.50, 0.80], dtype=float)
OBS_HIGH = np.array([2.30, 0.70, 0.70, 3.08, 2.30], dtype=float)
CTRL_LOW = OBS_LOW + 0.05
CTRL_HIGH = OBS_HIGH - 0.05
MAX_DELTA = 0.025
SETTLE_STEPS = 160
TRANSITION_STEPS = 10


def _q(sim: BracketArmSim) -> np.ndarray:
    return np.array([sim.d.qpos[sim.jqadr[joint]] for joint in ARM_JOINTS], dtype=float)


def _qvel(sim: BracketArmSim) -> np.ndarray:
    return np.array([sim.d.qvel[sim.m.jnt_dofadr[sim._jid(joint)]] for joint in ARM_JOINTS], dtype=float)


def _direct(sim: BracketArmSim, ctrl: np.ndarray) -> None:
    for joint, value in zip(ARM_JOINTS, ctrl):
        sim.target(joint, float(value))


def _assert_observed_safe(q: np.ndarray) -> None:
    if np.any(q < OBS_LOW) or np.any(q > OBS_HIGH):
        raise RuntimeError(f"encoder outside S1 observation box: {q.tolist()}")


def _park_objects(sim: BracketArmSim) -> None:
    # Fixed scene setup only.  Object state is never observed or emitted afterwards.
    for name in ("obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"):
        sim.set_object(name, (0.50, -0.60), z=0.012)


def collect(output: Path, rollouts: int, transitions: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "transitions.jsonl"
    sim = BracketArmSim()
    _park_objects(sim)
    rows = 0
    with path.open("w", encoding="utf-8") as handle:
        for rollout_id in range(rollouts):
            start_ctrl = rng.uniform(CTRL_LOW, CTRL_HIGH)
            _direct(sim, start_ctrl)
            sim.target("joint_5", HOME["joint_5"])
            sim.step(SETTLE_STEPS)
            for step_id in range(transitions):
                q, qvel, ctrl = _q(sim), _qvel(sim), sim.arm_targets().copy()
                _assert_observed_safe(q)
                ctrl_next = np.clip(ctrl + rng.uniform(-MAX_DELTA, MAX_DELTA, size=5), CTRL_LOW, CTRL_HIGH)
                _direct(sim, ctrl_next)
                sim.step(TRANSITION_STEPS)
                q_next, qvel_next = _q(sim), _qvel(sim)
                _assert_observed_safe(q_next)
                row = {
                    "schema": "act23-s1-proprio-transition-v1",
                    "rollout_id": rollout_id,
                    "split": "test" if rollout_id % 5 == 0 else "train",
                    "step_id": step_id,
                    "q_rad": q.tolist(),
                    "qvel_rad_s": qvel.tolist(),
                    "ctrl_rad": ctrl.tolist(),
                    "ctrl_next_rad": ctrl_next.tolist(),
                    "q_next_rad": q_next.tolist(),
                    "qvel_next_rad_s": qvel_next.tolist(),
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                rows += 1
    manifest = {
        "schema": "act23-s1-proprio-collection-v1",
        "rollouts": rollouts,
        "transitions_per_rollout": transitions,
        "rows": rows,
        "seed": seed,
        "joints": ARM_JOINTS,
        "observation_low_rad": OBS_LOW.tolist(),
        "observation_high_rad": OBS_HIGH.tolist(),
        "control_low_rad": CTRL_LOW.tolist(),
        "control_high_rad": CTRL_HIGH.tolist(),
        "max_delta_rad": MAX_DELTA,
        "settle_steps": SETTLE_STEPS,
        "transition_steps": TRANSITION_STEPS,
        "pressure_sensor_used": False,
        "teacher_or_ik_used": False,
        "object_or_contact_observed": False,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rollouts", type=int, default=50)
    parser.add_argument("--transitions", type=int, default=60)
    parser.add_argument("--seed", type=int, default=101)
    args = parser.parse_args()
    if args.rollouts < 5 or args.transitions < 2:
        raise SystemExit("rollouts >= 5 and transitions >= 2 required for a trajectory split")
    print(json.dumps(collect(args.output, args.rollouts, args.transitions, args.seed), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
