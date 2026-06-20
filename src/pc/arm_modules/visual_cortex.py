"""VisualCortexModule — the agent's perception module (the 1D VisualCortex, ported to the
MuJoCo camera).

Wraps the act18 learned hex-fovea PC-net (`HexFovea`) and its error-driven, object-following
gaze.  Internally a real `PCNetwork`, so its surprise is the genuine `sensor_error`
(prediction-vs-input) of the perception net.

It is a thin adapter over `setup_following_fovea` (warmup + world<->px calibration +
perceive/track closures + live hex view) that ALSO publishes its results on ports so the
module plugs into the ArmAgent:

Ports
  in  : command_color (3)  the commanded object's RGB (which object to look for)
  out : object_xy     (2)  perceived world xy of the commanded object
        object_in_view(1)  1.0 if confidently in view this frame, else 0.0
        gaze          (2)  current fovea centre (px)

`perceive(cmd)` (per episode) and `track()` (per frame) are the interface the executor
(`run_combined`) drives; both also refresh the out-ports.  `surprise()` returns the net's
last per-step diagnostics."""
from __future__ import annotations

import numpy as np

from pc.pc_act18 import setup_following_fovea
from .base import ArmModule


class VisualCortexModule(ArmModule):
    def __init__(self, setup: dict, cmd_color: dict, name: str = "VisualCortex") -> None:
        """`setup` = the dict returned by `setup_following_fovea`; `cmd_color` = CMD_COLOR."""
        super().__init__(name)
        self._P = setup
        self.fovea = setup["fovea"]
        self._cmd_color = cmd_color
        (self.add_in("command_color", 3, "commanded object RGB")
             .add_out("object_xy", 2, "perceived object world xy")
             .add_out("object_in_view", 1, "1.0 if confidently in view")
             .add_out("gaze", 2, "fovea centre (px)"))

    @classmethod
    def from_sim(cls, sim, CAM="overview", RES=240, headless=False, name="VisualCortex"):
        from pc.pc_act18 import CMD_COLOR
        P = setup_following_fovea(sim, CAM, RES, headless=headless)
        return cls(P, CMD_COLOR, name=name), P

    @property
    def viz(self):
        return self._P.get("viz")

    def perceive(self, cmd: str):
        """Saccade-and-follow to locate the commanded object; publish + return its world xy."""
        self.set_in("command_color", self._cmd_color[cmd])
        xy = self._P["perceive"](cmd)[0]
        self.set_out("object_xy", xy)
        self.set_out("object_in_view", [1.0])
        self.set_out("gaze", self._P["state"]["gaze"])
        return xy

    def track(self):
        """One follow frame (real view; gripper occludes -> memory); refresh ports.  Returns
        (world_xy, conf): conf>0 = a usable observation for the closed-loop grasp-target belief;
        xy=None / conf=0 when occluded (executor then acts on the last clean estimate)."""
        tr = self._P["track"]()
        xy, conf = tr if isinstance(tr, tuple) else (tr, 0.0)   # back-compat if track() returns xy
        self.set_out("object_in_view", [0.0 if xy is None else 1.0])
        self.set_out("gaze", self._P["state"]["gaze"])
        if xy is not None:
            self.set_out("object_xy", xy)
        return xy, conf

    def step(self) -> None:
        """Standalone agent step = one follow frame."""
        self.track()

    def surprise(self) -> dict | None:
        d = self.fovea.last_diag
        if d is None:
            return None
        return {"sensor": d["sensor_error"], "state": d["state_error"],
                "total": d["total_error"], "relax": d["relax_steps"]}
