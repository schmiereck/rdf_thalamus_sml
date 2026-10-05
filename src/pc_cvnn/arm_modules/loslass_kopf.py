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

    # ---- AUS DEM EIGENEN ERGEBNIS LERNEN (ACT23_LOSLASS_SELBST, Nutzeridee 2026-10-06) ----------
    # Der Teacher-Kopf oben ahmt einen grosszuegigen Teacher nach und raet in Halteposen, die der
    # Teacher nie etikettiert hat (im Lauf: ruhig, 14 mm hoch, 30 mm neben dem Ziel).  Hier lernt ein
    # ZWEITES Netz aus DERSELBEN Pose, in der tatsaechlich losgelassen wurde, und dem SELBST-URTEIL
    # der Kamera danach: "Loslassen hier hat geklappt / nicht geklappt".  Genau die Posen, die im
    # Lauf vorkommen -- und kein Teacher.
    ERFOLG_MIN = 20                  # Faelle, ab denen das Erfolgsnetz entscheidet
    ERFOLG_MIN_KLASSE = 5            # je Ausgang mindestens

    def erfolg_merken(self, s, ok):
        if getattr(self, "Xe", None) is None:
            self.Xe, self.ye = [], []
        self.Xe.append(self.aspekte(s)[0]); self.ye.append(1.0 if ok else 0.0)
        if len(self.Xe) > 2000:
            self.Xe = self.Xe[-2000:]; self.ye = self.ye[-2000:]

    @property
    def erfolg_bereit(self):
        y = np.asarray(getattr(self, "ye", None) or [], float)
        return (len(y) >= self.ERFOLG_MIN and y.sum() >= self.ERFOLG_MIN_KLASSE
                and (len(y) - y.sum()) >= self.ERFOLG_MIN_KLASSE and getattr(self, "net_e", None) is not None)

    def erfolg_lernen(self, epochs=150):
        y = np.asarray(getattr(self, "ye", None) or [], float)
        if len(y) < self.ERFOLG_MIN or y.sum() < self.ERFOLG_MIN_KLASSE or len(y) - y.sum() < self.ERFOLG_MIN_KLASSE:
            return False
        from pc_cvnn.pc_act19 import Policy
        self.net_e = Policy(din=5, dout=1, hid=16, rng=np.random.default_rng(11))
        self.net_e.fit(np.asarray(self.Xe, float), y[:, None], epochs=epochs, quiet=True)
        return True

    def p_erfolg(self, s):
        if getattr(self, "net_e", None) is None:
            return 0.0
        return float(self.net_e.predict(self.aspekte(s)[0])[0])
