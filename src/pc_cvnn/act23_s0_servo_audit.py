"""S0 audit: bounded direct position-servo pulses without IK, teacher, or pressure.

This fixture is deliberately outside ACT23.  It establishes the actual actuator contract and
the proprioceptive transition signal before a learning motor module is considered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.pc_act14 import ARM_JOINTS, BracketArmSim, HOME


# HOME lies at the lower stop of joint_1, so its excitation must point inward.
PULSE = np.array([0.06, 0.04, 0.04, -0.03, 0.05], dtype=float)
SETTLE_STEPS = 120


def _angles(sim: BracketArmSim) -> np.ndarray:
    return np.array([sim.d.qpos[sim.jqadr[joint]] for joint in ARM_JOINTS], dtype=float)


def run() -> dict:
    sim = BracketArmSim()
    initial_q = _angles(sim)
    initial_ctrl = sim.arm_targets().copy()
    limits = np.array([sim.m.jnt_range[sim._jid(joint)] for joint in ARM_JOINTS], dtype=float)
    desired_ctrl = np.clip(initial_ctrl + PULSE, limits[:, 0], limits[:, 1])

    # This is the direct S0 command.  No BodyModel, reach_velocity, target position, teacher,
    # object state, contact state, or pressure reading is queried on this path.
    for joint, value in zip(ARM_JOINTS, desired_ctrl):
        sim.target(joint, value)
    sim.step(SETTLE_STEPS)
    final_q = _angles(sim)

    return {
        "schema": "act23-s0-servo-audit-v1",
        "actuators": ["m" + joint[-1] for joint in ARM_JOINTS],
        "joints": ARM_JOINTS,
        "gripper_excluded": True,
        "pressure_sensor_used": False,
        "teacher_or_ik_used": False,
        "settle_steps": SETTLE_STEPS,
        "timestep_s": float(sim.m.opt.timestep),
        "joint_limits_rad": limits.tolist(),
        "initial_q_rad": initial_q.tolist(),
        "initial_ctrl_rad": initial_ctrl.tolist(),
        "command_delta_rad": (desired_ctrl - initial_ctrl).tolist(),
        "final_q_rad": final_q.tolist(),
        "tracking_residual_rad": (desired_ctrl - final_q).tolist(),
        "home_gripper_rad": float(HOME["joint_5"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(run(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
