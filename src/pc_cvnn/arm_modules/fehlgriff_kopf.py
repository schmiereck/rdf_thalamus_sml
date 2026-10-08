# -*- coding: utf-8 -*-
"""Ein eigener Lerner fuer EINEN Aspekt: Fehlgriff -- Klaue wieder aufmachen? (s. ACT23_FEHLGRIFF_KOPF).

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie LoslassKopf).
"""
import numpy as np


class FehlgriffKopf:
    """p(aufmachen | Klaue geschlossen) aus EINZELASPEKTEN, nach dem Muster des LoslassKopf.

    WARUM EIN EIGENER KOPF (wiki/befunde/zwischen-zufassen-und-anheben.md): nach einem
    herausgerutschten Griff schwebt die gemeinsame Policy mit leerer, geschlossener Klaue genau an
    der Schwelle, an der der Teacher von "anheben" auf "aufmachen" springt.  Eine MSE-Regression
    mittelt an Sprungstellen; die Schwelle zu verschieben (ACT16_NACHGRIFF_FIX) verschob nur den
    Haengepunkt.  Ein Klassifikator fuer die eine Entscheidung mittelt nicht -- beim Loslassen traf
    er aus Einzelaspekten 99 % statt 35 %.

    ARCHITEKTUR: dasselbe kleine MLP wie der LoslassKopf (act19 Policy, 16 versteckte).  Erwogen
    (Nutzerprinzip 2026-10-09: andere Architektur nur bei begruendetem Zweifel) und beibehalten -- der
    Zweifel betrifft die gemeinsame Regressions-Policy, nicht kleine Entscheidungskoepfe.

    Aspekte (aus dem Policy-Zustand, nichts Privilegiertes):
      Fingerdruck | Klauenwinkel | Hand ueber dem Greifpunkt | Objektglaube ueber Ruhehoehe |
      Hand <-> Objektglaube (seitlich)
    Etikett: der Teacher (reactive_subgoal) mit vorgezogener Fehlgriff-Schwelle (ACT16_NACHGRIFF_FIX
    nur fuer die Etiketten dieses Kopfs, die Policy-Daten bleiben unberuehrt); j5 >= 0,45 = aufmachen.
    Nur Zeilen mit geschlossener Klaue und Hand mehr als ZIEL_ABSTAND vom Ziel -- am Ziel entscheidet
    der LoslassKopf.
    """

    MIN_ZEILEN = 200
    ZIEL_ABSTAND = 0.03

    def __init__(self, rng=None):
        from pc_cvnn.pc_act19 import Policy
        self.net = Policy(din=5, dout=1, hid=16, rng=rng or np.random.default_rng(23))
        self.trained = False
        self.n_fit = 0
        self.n_auf = 0

    @staticmethod
    def zustaendig(s):
        s = np.asarray(s, float)
        return (len(s) > 14 and float(s[8]) < 0.27
                and float(np.linalg.norm(s[0:2] - s[6:8])) > FehlgriffKopf.ZIEL_ABSTAND)

    @staticmethod
    def aspekte(S):
        S = np.atleast_2d(np.asarray(S, float))
        gz = S[:, 9] + 0.006 + np.maximum(0.0, S[:, 14] - 0.014)
        return np.column_stack([S[:, 12], S[:, 8], S[:, 2] - gz, S[:, 5] - S[:, 9],
                                np.linalg.norm(S[:, 0:2] - S[:, 3:5], axis=1)])

    def lernen(self, X, teacher_fn, epochs=150):
        """X: besuchte Zustaende (DAgger-Puffer); teacher_fn(s) -> Teacher-Etikett mit Fix."""
        X = np.asarray(X, float)
        if len(X) == 0 or X.shape[1] < 15:
            return False
        m = (X[:, 8] < 0.27) & (np.linalg.norm(X[:, 0:2] - X[:, 6:8], axis=1) > self.ZIEL_ABSTAND)
        if m.sum() < self.MIN_ZEILEN:
            return False
        Xm = X[m]
        y = np.array([1.0 if float(teacher_fn(x)[3]) >= 0.45 else 0.0 for x in Xm])
        if y.sum() < 10:
            return False
        self.net.fit(self.aspekte(Xm), y[:, None], epochs=epochs, quiet=True)
        self.trained = True; self.n_fit = int(m.sum()); self.n_auf = int(y.sum())
        return True

    def p(self, s):
        if not self.trained:
            return 0.0
        return float(self.net.predict(self.aspekte(s)[0])[0])
