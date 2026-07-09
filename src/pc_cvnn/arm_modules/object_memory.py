"""ObjectMemoryModule — a PREDICTIVE belief about the commanded object's IMAGE position, so the
learned fovea gaze can follow the object through GRASP OCCLUSION and CARRY without a detector.

The measured limit of the detector-free gaze (c1cddbc): the active-inference drive can only centre
what is CURRENTLY under the fovea, so when the gripper occludes the object or the arm carries it out
of the fovea, the gaze loses it with no way to re-find it.  This module supplies the missing piece
with the SAME predict/correct idiom as the body model, but for the OBJECT and entirely from signals
the agent already owns -- vision + proprioception, no object detector:

  * CORRECT: while the object is visible (the hex net's sel/occupancy is strong under the fovea) the
    belief snaps to where the net sees it (the centred gaze) and confidence rises.
  * PREDICT: while the object is NOT visible AND the gripper is holding it (carrying), the belief
    follows the HAND's image position -- the thing I was looking at, now hidden in my closed gripper,
    is where my hand is.  Proprioceptive, so it works right through the occlusion and the carry.
  * HOLD: not visible and not carrying (e.g. briefly occluded on the table) -> hold the last belief.

The gaze then targets `belief_px`, so it stays on the object across the whole grasp->carry->place arc
with no detector re-anchor.  Confidence decays while unseen so a stale belief loosens its grip.

Ports (used imperatively via update(), like SelfEval / WorldModel)
  in  : obj_px_obs (2)  the net's own object px when visible (else pass None)
        hand_px    (2)  proprioceptive hand image position
        carrying   (1)  1.0 if the gripper holds the object
  out : belief_px  (2)  predicted object image position to gaze at
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule


class ObjectMemoryModule(ArmModule):
    def __init__(self, corr_gain: float = 0.6, name: str = "ObjectMemory") -> None:
        super().__init__(name)
        self.corr_gain = float(corr_gain)
        self.belief = None                                  # px (2,), or None until first sighting
        self.conf = 0.0                                     # [0,1] belief confidence
        self._last = None
        (self.add_in("obj_px_obs", 2, "net's object px when visible (else None)")
             .add_in("hand_px", 2, "proprioceptive hand image position")
             .add_in("carrying", 1, "1.0 if the gripper holds the object")
             .add_out("belief_px", 2, "predicted object image position to gaze at"))

    def reset(self) -> None:
        self.belief = None; self.conf = 0.0

    def update(self, obs_px, hand_px, carrying):
        """One frame.  Returns (belief_px, mode) where mode in {'sicht','getragen','gehalten'}."""
        hand_px = None if hand_px is None else np.asarray(hand_px, float)
        if obs_px is not None:                              # CORRECT from the net's own sighting
            o = np.asarray(obs_px, float)
            self.belief = o if self.belief is None else self.belief + self.corr_gain * (o - self.belief)
            self.conf = min(1.0, self.conf + 0.4)
            mode = "sicht"
        elif carrying and hand_px is not None:              # PREDICT: the held object is at the hand
            self.belief = hand_px if self.belief is None else self.belief + 0.5 * (hand_px - self.belief)
            self.conf = max(0.2, self.conf * 0.9)           # proprioception keeps a floor of confidence
            mode = "getragen"
        else:                                               # HOLD (brief table occlusion) -> decay
            self.conf *= 0.85
            mode = "gehalten"
        self._last = {"mode": mode, "conf": self.conf,
                      "belief": None if self.belief is None else np.round(self.belief, 1).tolist()}
        return (None if self.belief is None else self.belief.copy()), mode

    def step(self) -> None:
        obs = self.get_in("obj_px_obs"); hand = self.get_in("hand_px")
        car = self.get_in("carrying")
        b, _ = self.update(obs, hand, bool(car is not None and float(np.ravel(car)[0]) > 0.5))
        if b is not None:
            self.set_out("belief_px", b)

    def surprise(self) -> dict | None:
        return self._last
