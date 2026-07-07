"""SelfEvalModule — the agent JUDGES ITS OWN OUTCOME (self-supplied valence, step 1 of 3).

Until now the delivered/not verdict came from the DESIGNER: privileged `sim.obj_pos` + a rested
check inside run_combined.  This module builds the agent's OWN judge (the "übergeordnete Instanz"
the user asked for): after an episode it looks at the settled scene through the agent's OWN
perception, finds the commanded object by its SELF-LABELLED identity, and measures how far the
object's GOAL-LATENT is from the episode's goal latent (stage 4a) — mapped into metres through the
LEARNED latent-inverse D, so the verdict reads as a self-perceived "wie weit weg von meinem Wunsch".

    found    : detection whose self-labelled COLOUR class (first choice) or SHAPE class (fallback)
               matches the commanded object — no body handles, no privileged positions
    self_d   : | Re( (z_goal - z(perceived xy)) / zsd @ D ) |   (metres, via the learned inverse)
    success  : found AND self_d < tol   (tol mirrors run_combined's delivery tolerance, the one
               piece that stays task DEFINITION, not judgement)
    valence  : -self_d  (the affective signal: wish latent vs perceived reality)

No privilege anywhere in the verdict: localisation = camera->table homography, identity = the
agent's own open-set classes, distance = latent difference through the learned inverse.  A HANGING
object (still in the claw, off the table plane) is naturally judged NOT delivered — the homography
is a TABLE-plane map, so an off-plane blob mis-localises far from the goal; likewise an occluded /
lost object is simply NOT FOUND.

This step only INSTALLS the judge and MEASURES its agreement with the privileged verdict per
episode (rolling tally).  Steps 2/3 (checkpoint credit routing, self-imitation gating) may hand the
learners' outcome labels over to it once the agreement is proven.

Ports
  in  : obj_xy   (2)  perceived object world xy (the judged detection)
  out : valence  (1)  -self_d (metres, negative = away from the wish)
  out : success  (1)  1.0 / 0.0 self-judged delivered
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule


class SelfEvalModule(ArmModule):
    def __init__(self, tol: float = 0.025, name: str = "SelfEval") -> None:
        super().__init__(name)
        self.tol = float(tol)
        self.n = 0                                        # judged episodes (abstentions not counted)
        self.agree = 0                                    # ... where self == privileged verdict
        self.recent: list[tuple[bool, bool]] = []         # (self_ok, world_ok), capped
        self._last = None                                 # last judgement diagnostics
        (self.add_in("obj_xy", 2, "perceived object world xy")
             .add_out("valence", 1, "-self_d: latent distance to the wish, metres")
             .add_out("success", 1, "self-judged delivered (1/0)"))

    # ------------------------------------------------------------------ #
    def judge(self, dets, lgoal, colour_key=None, colours=None, shape_key=None):
        """Judge the settled scene.  Returns (self_ok, self_d_m, found):
        self_ok False+found False = object not seen (lost/hanging/occluded) -> not delivered;
        returns (None, None, False) = ABSTAIN when the agent has no own class to identify the
        object with (nothing to judge honestly)."""
        cands = []
        if colour_key is not None and colours is not None:
            cands = [d for d in dets if d.get("pos") is not None
                     and colours.classify(d["chroma"])[0] == colour_key]
            if cands:
                best = min(cands, key=lambda d: colours.classify(d["chroma"])[1])
        if not cands and shape_key is not None:
            cands = [d for d in dets if d.get("pos") is not None and d.get("shape") == shape_key]
            if cands:
                best = max(cands, key=lambda d: d.get("prob", 0.0))
        if colour_key is None and shape_key is None:
            self._last = {"abstain": True}
            return None, None, False
        if not cands:
            self._last = {"found": False}
            return False, None, False
        pos = np.asarray(best["pos"], float)
        e = (lgoal.z_g - lgoal.encode_world(pos)) / lgoal.zsd
        dxy = np.real(e @ lgoal.D)                        # the wish-offset through the LEARNED inverse
        d = float(np.linalg.norm(dxy))
        ok = d < self.tol
        self._last = {"found": True, "pos": pos, "self_d": d, "ok": ok}
        self.set_out("valence", [-d]); self.set_out("success", [1.0 if ok else 0.0])
        return ok, d, True

    def record(self, self_ok, world_ok) -> str:
        """Tally agreement of the self-judgement with the privileged verdict; returns the tally."""
        self.n += 1
        self.agree += int(bool(self_ok) == bool(world_ok))
        self.recent.append((bool(self_ok), bool(world_ok))); del self.recent[:-200]
        r = self.recent[-30:]
        ra = sum(int(a == b) for a, b in r)
        return f"{ra}/{len(r)} zuletzt, {self.agree}/{self.n} gesamt"

    def step(self) -> None:
        ox = self.get_in("obj_xy")
        if ox is not None and self._last and self._last.get("found"):
            self.set_out("valence", [-self._last["self_d"]])
            self.set_out("success", [1.0 if self._last["ok"] else 0.0])
