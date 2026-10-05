# -*- coding: utf-8 -*-
"""Ein eigener Lerner fuer EINEN Aspekt: jetzt loslassen? (s. ACT23_LOSLASS_KOPF).

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie HoehenSchaetzer).
"""
import numpy as np


class LoslassKopf:
    """p(loslassen | gehaltener Zustand) aus EINZELASPEKTEN statt aus dem ganzen Zustand.

    WARUM EIN EIGENER KOPF (Nutzeridee 2026-10-05: "nicht die ganze Situation bewerten, sondern
    einzelne Aspekte"): die gemeinsame Policy lernt Zielpunkt und Greiferwinkel in EINEM Netz.
    Loslassen ist ein seltener, scharfer Moment (1,7 % der Zeilen) und geht gegen Anfahren und
    Tragen unter -- auch mit korrigierten Etiketten oeffnet sie am Ziel nicht (Median j5 0,07).
    Phasen-Gewichtung im gemeinsamen Netz ist gemessen gescheitert (ACT23_PHASE_W).  Ein eigener
    Kopf konkurriert um keine Kapazitaet.

    WARUM EINZELASPEKTE: gemessen am gehaltenen Pruefsatz (wiki/befunde/loslassen.md) -- voller
    Zustand: oeffnet am Ziel 35 %, 22 % Fehlalarme weiter als 5 cm vom Ziel; Einzelaspekte: 99 %,
    0 % weiter als 5 cm (Fehlalarme nur 16-18 mm ueber der Ablagehoehe, Teacher 8-16 mm).  Das Netz
    muss "Hand ueber dem Ziel" nicht erst aus vier Koordinaten ausrechnen.

    Aspekte (alle aus dem Policy-Zustand, nichts Privilegiertes):
      Hand <-> eigenes Ziel (xy) | Hand ueber Ablagehoehe | Fingerdruck | Klauenwinkel |
      Objekt(glaube) <-> Ziel
    Etikett: das Teacher-Etikett (j5 >= 0,5 heisst oeffnen), mit ACT16_ABLAGE_FIX widerspruchsfrei.
    """

    MIN_ZEILEN = 200

    def __init__(self, rng=None):
        from pc_cvnn.pc_act19 import Policy
        self.net = Policy(din=5, dout=1, hid=16, rng=rng or np.random.default_rng(7))
        self.trained = False
        self.n_fit = 0

    @staticmethod
    def haelt(s):
        s = np.asarray(s, float)
        return len(s) > 13 and float(s[12]) > 0.3 and float(s[8]) < 0.27

    @staticmethod
    def aspekte(S):
        S = np.atleast_2d(np.asarray(S, float))
        return np.column_stack([np.linalg.norm(S[:, 0:2] - S[:, 6:8], axis=1),
                                S[:, 2] - S[:, 13],
                                S[:, 12],
                                S[:, 8],
                                np.linalg.norm(S[:, 3:5] - S[:, 6:8], axis=1)])

    def lernen(self, X, Y, epochs=150):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        if len(X) == 0 or X.shape[1] < 14:
            return False
        m = (X[:, 12] > 0.3) & (X[:, 8] < 0.27)
        if m.sum() < self.MIN_ZEILEN:
            return False
        y = (Y[m, 3] >= 0.5).astype(float)
        if y.sum() < 10:
            return False
        self.net.fit(self.aspekte(X[m]), y[:, None], epochs=epochs, quiet=True)
        self.trained = True; self.n_fit = int(m.sum())
        return True

    def p(self, s):
        if not self.trained:
            return 0.0
        return float(self.net.predict(self.aspekte(s)[0])[0])
