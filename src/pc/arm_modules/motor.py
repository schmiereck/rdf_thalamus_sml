"""MotorModule — the agent's action module (the 1D Premotor/Motor, ported to the arm).

Wraps the act19 LEARNED action policy (a small MLP, state(9) -> sub-goal(4)=[aim_xyz, gripper]),
imitated from the reactive teacher.  Not a PCNetwork, but it implements the SAME port interface
so it plugs into the ArmAgent identically.

Ports
  in  : state    (9)  [hand xyz, object xy, object z, target xy, gripper]
  out : subgoal  (4)  [aim_xyz, gripper target]  -- the sub-goal the FSM/executor then reaches for
"""
from __future__ import annotations

import numpy as np

from pc.pc_act19 import Policy
from .base import ArmModule


class MotorModule(ArmModule):
    def __init__(self, policy: Policy | None = None, name: str = "Motor", rng=None) -> None:
        super().__init__(name)
        self.policy = policy if policy is not None else Policy(rng=rng)
        self._last_cost = float("nan")
        (self.add_in("state", 9, "[hand xyz, object xy, object z, target xy, gripper]")
             .add_out("subgoal", 4, "[aim_xyz, gripper target]"))

    # -- training / persistence delegates so the agent owns the policy --
    def fit(self, X, Y, **kw):
        self.policy.fit(X, Y, **kw)

    def snapshot(self):
        return self.policy.snapshot()

    def restore(self, s):
        self.policy.restore(s)

    def predict(self, state):
        """The interface run_combined drives as policy_fn; also tracks the imitation residual."""
        out = self.policy.predict(state)
        self.set_in("state", state); self.set_out("subgoal", out)
        return out

    def step(self) -> None:
        s = self.get_in("state")
        if s is not None:
            self.set_out("subgoal", self.policy.predict(s))

    def surprise(self) -> dict:
        return {"cost": self._last_cost}
