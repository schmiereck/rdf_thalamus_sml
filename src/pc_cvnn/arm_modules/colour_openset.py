"""ColourOpenSetModule — STAGE 3: OPEN-SET colour classes, fully SELF-LABELLED.

Purer than the shape open-set: there is NO trained colour manifold and NO teacher label anywhere --
every class the module knows was discovered by itself.  A sighting is the CHROMATICITY of a scene
component (brightness-normalised mean RGB, rgb/sum(rgb)): shading and position cancel out (measured:
within-object spread <= 0.075, minimum between-object distance 0.197 over the act23 object set, so
TH=0.12 separates with margin on both sides).

Mechanics mirror the shape open-set (same guards, simpler space):
  * classify(chroma): nearest class centroid; farther than TH from all -> (None, d) = a NOVEL colour;
  * observe(chroma):  matches REFINE the centroid (running mean); novel sightings buffer, and
    NOVEL_CONFIRM mutually-consistent ones COMMIT a self-named class ("farbe-1", ...);
  * centroids that drift within TH of each other CONSOLIDATE (the older name survives -- it may be
    bound to GUI plumbing).

Ports
  in  : chroma       (3)  brightness-normalised component colour
  out : colour_id    (1)  index into names() (-1 = novel)
"""
from __future__ import annotations

import os

import numpy as np

from .base import ArmModule

TH = float(os.environ.get("ACT_COLOUR_TH", "0.12"))     # accept<=within-spread(0.075) / reject>=between(0.197)
NOVEL_CONFIRM = int(os.environ.get("ACT_COLOUR_CONFIRM", "3"))
BUF_CAP = 12


class ColourOpenSetModule(ArmModule):
    def __init__(self, name: str = "ColourOpenSet") -> None:
        super().__init__(name)
        self.classes: dict[str, dict] = {}                  # name -> {"mu": chroma(3), "n": sightings}
        self.names: list[str] = []                          # creation order (ids)
        self._buf: list[np.ndarray] = []                    # novel sightings awaiting consistency
        (self.add_in("chroma", 3, "brightness-normalised component colour")
             .add_out("colour_id", 1, "index into names() (-1 = novel)"))

    def classify(self, chroma):
        """(name, distance) of the nearest self-labelled colour class; (None, d) if NOVEL."""
        c = np.asarray(chroma, float)
        best, bd = None, np.inf
        for nm, cl in self.classes.items():
            d = float(np.linalg.norm(c - cl["mu"]))
            if d < bd:
                best, bd = nm, d
        if best is None or bd > TH:
            return None, bd
        return best, bd

    def observe(self, chroma):
        """One sighting: refine a matching class, or buffer a novel one until NOVEL_CONFIRM
        consistent sightings commit a new self-named class.  Returns newly created names."""
        c = np.asarray(chroma, float)
        nm, _d = self.classify(c)
        born = []
        if nm is not None:
            cl = self.classes[nm]; cl["n"] += 1
            cl["mu"] += (c - cl["mu"]) / min(cl["n"], 200)  # running mean, bounded adaptation
        else:
            near = [b for b in self._buf if float(np.linalg.norm(b - c)) < TH]
            if len(near) + 1 >= NOVEL_CONFIRM:
                name = f"farbe-{len(self.names) + 1}"
                self.names.append(name)
                self.classes[name] = {"mu": np.mean(near + [c], axis=0), "n": len(near) + 1}
                self._buf = [b for b in self._buf if not any(b is q for q in near)]
                born.append(name)
            else:
                self._buf.append(c)
        self._buf = self._buf[-BUF_CAP:]
        # CONSOLIDATE: two centroids inside TH are the same colour seen twice -- older name survives
        for a in list(self.names):
            for b in list(self.names):
                if (self.names.index(a) < self.names.index(b) and a in self.classes and b in self.classes
                        and float(np.linalg.norm(self.classes[a]["mu"] - self.classes[b]["mu"])) < TH):
                    self.classes[a]["n"] += self.classes[b]["n"]
                    del self.classes[b]; self.names.remove(b)
                    born = [x for x in born if x != b]
        return born

    def step(self) -> None:
        ch = self.get_in("chroma")
        if ch is not None:
            nm, _ = self.classify(ch)
            self.set_out("colour_id", [self.names.index(nm) if nm is not None else -1])
