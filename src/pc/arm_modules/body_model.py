"""BodyModelModule — the agent's proprioceptive / kinematics module (the 1D BodyModel,
ported to the arm).

Wraps `ArmBodyModel3D` (act14): a LEARNED linear-in-features forward kinematics whose
analytic Jacobian drives damped-least-squares reach control.  It is not a PCNetwork, but
it implements the SAME port interface so it plugs into the ArmAgent identically.

Ports
  in  : hand_target_xyz (3)  desired hand position
        joint_angles    (3)  current 3-motor angles q3
  out : hand_xyz        (3)  predicted hand position  fk(q3)
        joint_dq        (3)  reach velocity toward hand_target_xyz

Surprise = the kinematics prediction error in mm: ||fk(q3) - observed hand||, fed from the
loop (read-only via `note_surprise`, or learned online via `observe`)."""
from __future__ import annotations

import numpy as np

from pc.pc_act14 import ArmBodyModel3D
from .base import ArmModule


class BodyModelModule(ArmModule):
    def __init__(self, body: ArmBodyModel3D | None = None, name: str = "BodyModel",
                 rng=None) -> None:
        super().__init__(name)
        self.body = body if body is not None else ArmBodyModel3D(rng=rng)
        self._surprise_mm = float("nan")
        (self.add_in("hand_target_xyz", 3, "desired hand position")
             .add_in("joint_angles", 3, "current 3-motor angles")
             .add_out("hand_xyz", 3, "predicted hand position fk(q3)")
             .add_out("joint_dq", 3, "reach velocity toward the target"))

    # -- training delegate (babbling), kept on the module so the agent owns it --
    def babble(self, sim, steps: int) -> None:
        self.body.babble(sim, steps)

    def step(self) -> None:
        q3 = self.get_in("joint_angles")
        if q3 is not None:
            self.set_out("hand_xyz", self.body.fk(q3))
            tgt = self.get_in("hand_target_xyz")
            if tgt is not None:
                self.set_out("joint_dq", self.body.reach_velocity(q3, tgt))

    def note_surprise(self, q3, hand_obs) -> float:
        """Record the FK surprise (read-only, no learning): ||fk(q3) - observed hand|| in mm."""
        self._surprise_mm = float(np.linalg.norm(self.body.fk(q3) - np.asarray(hand_obs, float))) * 1000.0
        return self._surprise_mm

    def observe(self, q3, hand_obs, lr: float = 0.02) -> None:
        """Lifelong refinement: adapt W toward the observed hand and update the surprise EMA."""
        self.body.observe(q3, hand_obs, lr=lr)
        self._surprise_mm = float(np.linalg.norm(self.body.fk(q3) - np.asarray(hand_obs, float))) * 1000.0

    def surprise(self) -> dict:
        return {"fk_mm": self._surprise_mm}
