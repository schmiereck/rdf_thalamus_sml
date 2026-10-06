# -*- coding: utf-8 -*-
"""Ein eigener Lerner fuer EINEN Aspekt: lohnt es sich weiterzumachen? (s. ACT23_AUFGEBEN).

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie LoslassKopf).
"""
import numpy as np


class AufgebenKopf:
    """p(diese Episode gelingt noch | Momentaufnahme) aus Einzelaspekten, gelernt aus dem EIGENEN
    Ergebnis (Selbst-Urteil der Kamera am Episodenende).

    WARUM: rund ein Drittel der Episoden endete ueber das Zeitbudget (148 von 397, je ~900
    Schritte) -- der Agent merkte nicht, dass ein Versuch aussichtslos war.  Das Zeitbudget ist
    keine Entscheidung, nur eine Uhr.  Hier lernt er aus eigenen Episoden, wann Weitermachen nichts
    mehr bringt (wiki/befunde/aufgeben.md).

    Aspekte (aus dem Policy-Zustand plus der eigenen Schrittzahl, nichts Privilegiertes):
      Schritte | haelt etwas | Hand <-> Ziel | Hand <-> Objekt(glaube) | Objekt(glaube) <-> Ziel |
      Handhoehe | Fingerdruck | Klaue
    Etikett: das Selbst-Urteil am Ende DIESER Episode fuer jede ihrer Momentaufnahmen.
    """

    MIN_ZEILEN = 150
    MIN_KLASSE = 30

    def __init__(self):
        self.X, self.y = [], []
        self.net = None

    @staticmethod
    def aspekte(s, k):
        s = np.asarray(s, float)
        haelt = 1.0 if (len(s) > 12 and s[12] > 0.3 and s[8] < 0.27) else 0.0
        return np.array([k / 1000.0, haelt,
                         float(np.linalg.norm(s[0:2] - s[6:8])),
                         float(np.linalg.norm(s[0:2] - s[3:5])),
                         float(np.linalg.norm(s[3:5] - s[6:8])),
                         float(s[2]), float(s[12]) if len(s) > 12 else 0.0, float(s[8])], float)

    def merken(self, aufnahmen, ok):
        for a in aufnahmen:
            self.X.append(np.asarray(a, float)); self.y.append(1.0 if ok else 0.0)
        if len(self.X) > 6000:
            self.X = self.X[-6000:]; self.y = self.y[-6000:]

    @property
    def bereit(self):
        y = np.asarray(self.y, float)
        return (self.net is not None and len(y) >= self.MIN_ZEILEN
                and y.sum() >= self.MIN_KLASSE and (len(y) - y.sum()) >= self.MIN_KLASSE)

    def lernen(self, epochs=150):
        y = np.asarray(self.y, float)
        if len(y) < self.MIN_ZEILEN or y.sum() < self.MIN_KLASSE or len(y) - y.sum() < self.MIN_KLASSE:
            return False
        from pc_cvnn.pc_act19 import Policy
        self.net = Policy(din=8, dout=1, hid=16, rng=np.random.default_rng(13))
        self.net.fit(np.asarray(self.X, float), y[:, None], epochs=epochs, quiet=True)
        return True

    def p(self, a):
        if self.net is None:
            return 1.0
        return float(self.net.predict(np.asarray(a, float))[0])
