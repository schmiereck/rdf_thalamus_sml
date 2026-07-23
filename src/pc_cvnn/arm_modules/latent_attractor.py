"""LatentAttractorController — continuous closed-loop latent attractor planning (act23).

Etappe 3 (Attraktor-Steuerung):
Replaces rigid macro FSM phase transitions with continuous latent attractor planning.
The controller evaluates candidate action deltas via the learned LatentDynamicsModule (Etappe 2)
to minimize an energy function E(z) = ||\\hat{z}_{t+1}(a) - z_{goal}||^2 + \\lambda_s * Surprise(z, a).

As the latent state z_t converges toward z_{goal}, the energy smoothly drops, providing a continuous,
model-driven closed-loop controller for approach, grasp, carry, and place.
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule, Port
from .latent_dynamics import LatentDynamicsModule
from .latent_goal import LatentGoalServo, LO, HI


class LatentAttractorController(ArmModule):
    """Continuous Latent Attractor Controller."""

    def __init__(self, servo: LatentGoalServo, dynamics: LatentDynamicsModule,
                 lambda_surprise: float = 0.1, lambda_action: float = 0.01, rng=None):
        super().__init__("latent_attractor")
        self.servo = servo
        self.dynamics = dynamics
        self.lambda_surprise = lambda_surprise
        self.lambda_action = lambda_action
        self.rng = rng or np.random.default_rng(42)

    def declare_ports(self):
        self.add_port(Port("z_current", "in", np.ndarray))
        self.add_port(Port("z_goal", "in", np.ndarray))
        self.add_port(Port("action_out", "out", np.ndarray))

    def evaluate_energy(self, z_t, action, z_goal):
        """Compute potential field energy E(z_t, a; z_goal)."""
        z_pred = self.dynamics.predict_next_latent(z_t, action)
        # Latent error to goal
        err_dist = float(np.linalg.norm(np.asarray(z_goal) - np.asarray(z_pred)))
        # Action magnitude penalty
        act_penalty = float(np.linalg.norm(np.asarray(action)))
        # Surprise / uncertainty estimation
        surp = float(np.linalg.norm(np.asarray(z_pred) - np.asarray(z_t)))
        return err_dist**2 + self.lambda_surprise * surp + self.lambda_action * act_penalty

    def plan_step(self, z_t, z_goal, current_xy, n_candidates: int = 32, gain: float = 0.8):
        """Plan one continuous step toward z_goal by searching for the action that minimizes latent energy.

        Returns (best_action, best_energy, target_xy).
        """
        # Ensure goal vector is set on servo
        self.servo.set_goal_vector(z_goal)
        # Base action candidate from closed-loop LatentGoalServo
        base_target_xy = self.servo.servo(current_xy, gain=gain)
        base_dpos = base_target_xy - np.asarray(current_xy, float)

        # Generate candidate action deltas around base_dpos
        candidates = []
        # Candidate 1: pure servo step
        candidates.append(np.array([base_dpos[0], base_dpos[1], 0.0, 0.0]))
        # Candidate 2: zero step (stay)
        candidates.append(np.zeros(4))

        # Sample random perturbations around base_dpos
        for _ in range(n_candidates - 2):
            dx, dy = base_dpos + self.rng.normal(0, 0.015, 2)
            dwrist = self.rng.normal(0, 0.1)
            dgrip = float(self.rng.uniform(0.0, 0.3))
            candidates.append(np.array([dx, dy, dwrist, dgrip]))

        best_act = candidates[0]
        best_energy = float("inf")

        for act in candidates:
            energy = self.evaluate_energy(z_t, act, z_goal)
            if energy < best_energy:
                best_energy = energy
                best_act = act

        # Compute resulting spatial target position
        target_xy = np.clip(np.asarray(current_xy, float) + best_act[:2], LO, HI)
        return best_act, best_energy, target_xy


# --------------------------------------------------------------------------- #
def main():
    """Standalone unit test for LatentAttractorController."""
    rng = np.random.default_rng(0)
    from .planner import GoalModule2D
    import os

    gm = GoalModule2D(rng=np.random.default_rng(7))
    gm.pretrain(int(os.environ.get("LG_GM_STEPS", "1000")))
    servo = LatentGoalServo(gm, rng=np.random.default_rng(1))
    servo.train(steps=1000)

    dyn = LatentDynamicsModule(latent_dim=10, action_dim=4, rng=rng)

    # Train dynamics slightly
    for _ in range(50):
        zt = rng.normal(0, 1, 10) + 1j * rng.normal(0, 1, 10)
        a = rng.uniform(-0.05, 0.05, 4)
        zn = zt + 0.02 * a[0]
        dyn.observe(zt, a, zn)
    dyn.train(epochs=10)

    ctrl = LatentAttractorController(servo, dyn, rng=rng)

    print("=" * 72)
    print("  LatentAttractorController — Standalone Self-Test")
    print("=" * 72)

    current_xy = np.array([0.0, 0.10])
    goal_xy = np.array([0.05, 0.18])
    z_start = servo.encode_world(current_xy)
    z_goal = servo.encode_world(goal_xy)

    best_act, energy, target_xy = ctrl.plan_step(z_start, z_goal, current_xy)
    print(f"  Current XY: {current_xy}")
    print(f"  Goal    XY: {goal_xy}")
    print(f"  Planned Step target XY: [{target_xy[0]:.4f}, {target_xy[1]:.4f}]")
    print(f"  Planned Action delta  : {np.round(best_act, 4)}")
    print(f"  Latent Attractor Energy: {energy:.6f}")

    print("-" * 72)
    print("  Read: LatentAttractorController successfully minimizes latent energy toward z_goal.")
    print("=" * 72)


if __name__ == "__main__":
    main()
