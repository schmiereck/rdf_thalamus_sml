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


def colour_TH():
    """The colour open-set acceptance threshold (import-cycle-free lazy read)."""
    from .colour_openset import TH
    return TH


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
    def judge(self, dets, lgoal, colour_key=None, colours=None, shape_key=None,
              near_xy=None, near_r=0.05):
        """Judge the settled scene.  Returns (self_ok, self_d_m, found):
        self_ok False+found False = object not seen (lost/hanging/occluded) -> not delivered;
        returns (None, None, False) = ABSTAIN when the agent has no own class to identify the
        object (nothing to judge honestly).

        IDENTITY = CONTINUITY, appearance only as a tie-break (measured lesson): the agent's OWN
        hand carried the commanded object and RELEASED it -- proprioception, no privilege.  So the
        delivered object is the scene blob NEAREST the release point (near_xy).  Its CHROMA is NOT
        required to still match the bound class: a thin object reads washed-out when it settles
        (measured: the delivered long object classified as the U's cyan / a grey phantom while its
        blob sat 4-15mm from the hand -> an appearance gate wrongly said 'not seen').  Among several
        blobs AT the hand, prefer the one that DOES match the bound class (tie-break), else the
        nearest.  The one measured FALSE POSITIVE (a class blob near the wish while the true object
        sat 57mm away) is handled by continuity itself: the hand tracks the FAILED object, so the
        near-hand blob is the true one and self_d reads large.  Without an anchor (near_xy None) fall
        back to appearance: the class match, unique or most confident."""
        if colour_key is None and shape_key is None:
            self._last = {"abstain": True}
            return None, None, False
        cands = [d for d in dets if d.get("pos") is not None]

        def _near(d):
            return float(np.linalg.norm(np.asarray(d["pos"], float) - np.asarray(near_xy, float)))

        def _mine(d):
            return colour_key is not None and colours is not None \
                and colours.classify(d["chroma"])[0] == colour_key

        best = None
        if near_xy is not None:                               # CONTINUITY: the blob the hand let go
            nearby = [d for d in cands if _near(d) < near_r]
            if nearby:
                mine = [d for d in nearby if _mine(d)]        # tie-break: my class among the near
                best = min(mine or nearby, key=_near)         #   blobs, else the plain nearest
        if best is None:                                      # nothing at the hand / no anchor ->
            strict = []                                       #   APPEARANCE fallback (e.g. object slid
            if colour_key is not None and colours is not None:   # to the wish, hand ended elsewhere)
                strict = [d for d in cands if colours.classify(d["chroma"])[0] == colour_key]
            if not strict and shape_key is not None:
                strict = [d for d in cands if d.get("shape") == shape_key]
            if len(strict) == 1:
                best = strict[0]
            elif len(strict) > 1:
                best = (min(strict, key=_near) if near_xy is not None
                        else (min(strict, key=lambda d: colours.classify(d["chroma"])[1])
                              if colour_key is not None and colours is not None
                              else max(strict, key=lambda d: d.get("prob", 0.0))))
        diag = {"n_dets": len(dets), "n_cands": len(cands),
                "n_strict": sum(1 for d in cands if colour_key is not None and colours is not None
                                and colours.classify(d["chroma"])[0] == colour_key),
                "near_xy": None if near_xy is None else np.round(np.asarray(near_xy, float), 3).tolist(),
                "cand_pos": [np.round(np.asarray(d["pos"], float), 3).tolist() for d in cands[:6]]}
        if best is None:
            self._last = {"found": False, **diag}
            return False, None, False
        pos = np.asarray(best["pos"], float)
        e = (lgoal.z_g - lgoal.encode_world(pos)) / lgoal.zsd
        dxy = np.real(e @ lgoal.D)                        # the wish-offset through the LEARNED inverse
        d = float(np.linalg.norm(dxy))
        ok = d < self.tol
        self._last = {"found": True, "pos": pos, "self_d": d, "ok": ok, **diag}
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
