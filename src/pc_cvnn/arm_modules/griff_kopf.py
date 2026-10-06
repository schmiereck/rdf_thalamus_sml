# -*- coding: utf-8 -*-
"""Zufassen aus dem eigenen Ergebnis (s. ACT23_GRIFF_SELBST): Einzelaspekte im Moment des
Zufassens -> hat sich Druck aufgebaut und beim Anheben gehalten?

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie LoslassKopf).
"""
import numpy as np


class GriffKopf:
    """Stufe 1: SAMMELN und pruefen, ob die Aspekte gelungene und misslungene Griffe trennen.

    Vorbehalt aus wiki/befunde/griff-glaube-und-tastsinn.md (geschlossen): der Zustand vor dem
    ersten Griffversuch war in gelieferten und gescheiterten Episoden gleich (Hoehe 12,8 gegen
    13,0 mm; seitlich 3,9 gegen 6,1 mm, p = 0,25).  Damals Etikett "geliefert", wenige Episoden.
    Hier: Etikett je VERSUCH aus dem eigenen Tastsinn ("trug": Druck > 0,3 N bei geschlossener
    Klaue und Hand ueber 40 mm, bevor die Klaue wieder aufgeht), und mehr Aspekte.

    Aspekte (aus dem Policy-Zustand, nichts Privilegiertes):
      seitlich Hand <-> Objekt(glaube) | Hand ueber Greifpunkt | Klauenwinkel | Fingerdruck |
      Objekt-Kurzachse (geschaetzt) | Objekthoehe (geschaetzt) | Versuchsnummer in der Episode
    """

    def __init__(self):
        self.X, self.y = [], []

    @staticmethod
    def aspekte(s, versuch):
        s = np.asarray(s, float)
        h_griff = max(0.0, float(s[14]) - 0.014) if len(s) > 14 else 0.0
        return np.array([float(np.linalg.norm(s[0:2] - s[3:5])),
                         float(s[2]) - (float(s[9]) + 0.006 + h_griff),
                         float(s[8]), float(s[12]) if len(s) > 12 else 0.0,
                         float(s[10]), float(s[9]), float(versuch)], float)

    def merken(self, a, ok):
        self.X.append(np.asarray(a, float)); self.y.append(1.0 if ok else 0.0)
        if len(self.X) > 4000:
            self.X = self.X[-4000:]; self.y = self.y[-4000:]
