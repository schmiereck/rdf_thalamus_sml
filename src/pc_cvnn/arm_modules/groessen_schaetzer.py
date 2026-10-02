# -*- coding: utf-8 -*-
"""Grundflaeche und Hoehe des GREIFOBJEKTS aus der Wahrnehmung (s. ACT23_GROESSE_SEHEN).

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie HoehenSchaetzer).
"""
import numpy as np


class GroessenSchaetzer:
    """(obj_fp, obj_h) eines Koerpers AUS SEINER DETEKTION.

    WOFUER: der Policy-Zustand traegt in den Spalten 9/10 die halbe Hoehe und die halbe
    Kurzachse des kommandierten Objekts.  Beide kamen aus `geom_size`, also aus MuJoCo -- die
    Policy bekam "Wuerfel 12 / Balken 9 / Form 6-7 mm" gesagt, auf dem echten Roboter gibt es
    diese Zahl nicht (wiki/mechanismen/laufzeit-regeln.md, Bestandsaufnahme 2026-10-02).

    MERKMALE: nur was in derselben Detektion steht -- scheinbare Flaeche, Materialdicke (px,
    Distanztransformation), Material-Halbspanne (m) und der wahrgenommene Ort.  Der Ort gehoert
    dazu, weil die Perspektive Flaeche und Dicke ebenso veraendert wie die Groesse (dieselbe
    Begruendung wie beim HoehenSchaetzer).

    VERFAHREN: dasselbe wie HoehenSchaetzer -- lokal linear aus den naechsten Nachbarn, k = 2 x
    (Merkmale + 1).  Lokal statt global, weil die Koerper in Gruppen liegen (Wuerfel, Balken,
    Formen) und eine globale Ebene sie vermengt; gemessen ist das am HoehenSchaetzer
    (33 % global gegen 92 % lokal), hier uebernommen, nicht neu gemessen.

    GERUEST: gelabelt wird zunaechst mit der privilegierten Geometrie.  Zulaessig nach
    laufzeit-regeln.md (eine Regel darf Trainingsdaten stuetzen); zur Laufzeit liest die Policy
    mit ACT23_GROESSE_SEHEN=1 nur noch die Schaetzung.
    """

    MIN_ZEILEN = 24
    MAX_ZEILEN = 4000
    NACHBARN = 12            # 2 x (5 Merkmale + Achsenabschnitt)

    def __init__(self):
        self.X, self.y = [], []
        self.mu = self.sd = None
        self.n_fit = 0

    @staticmethod
    def merkmale(det):
        if det is None:
            return None
        _a, _d, _s, _p = det.get("area"), det.get("dicke"), det.get("span"), det.get("pos")
        if _a is None or _d is None or _s is None or _p is None:
            return None
        return np.array([float(_a), float(_d), float(_s), float(_p[0]), float(_p[1])], float)

    def merken(self, det, fp, h):
        m = self.merkmale(det)
        if m is None:
            return False
        self.X.append(m); self.y.append([float(fp), float(h)])
        if len(self.X) > self.MAX_ZEILEN:
            self.X = self.X[-self.MAX_ZEILEN:]; self.y = self.y[-self.MAX_ZEILEN:]
        return True

    def schaetzen(self, det):
        """(obj_fp, obj_h) in m, oder None -- dann faellt der Aufrufer LAUT zurueck."""
        if len(self.X) < self.MIN_ZEILEN:
            return None
        m = self.merkmale(det)
        if m is None:
            return None
        X = np.asarray(self.X, float); Y = np.asarray(self.y, float)
        if self.n_fit != len(X):                       # Massstab aus allen Zeilen (s. HoehenSchaetzer)
            self.mu = X.mean(0); self.sd = X.std(0) + 1e-9; self.n_fit = len(X)
        Xs = (X - self.mu) / self.sd
        z = (m - self.mu) / self.sd
        idx = np.argsort(np.linalg.norm(Xs - z, axis=1))[:min(self.NACHBARN, len(X))]
        A = np.hstack([Xs[idx], np.ones((len(idx), 1))])
        try:
            W = np.linalg.solve(A.T @ A + 1e-2 * np.eye(A.shape[1]), A.T @ Y[idx])
        except Exception:
            return None
        g = np.concatenate([z, [1.0]]) @ W
        # AUF DAS GESEHENE BAND BESCHRAENKEN -- keine Extrapolation ueber alles je Gesehene hinaus
        lo, hi = Y.min(0), Y.max(0)
        rand = 0.25 * np.maximum(hi - lo, 0.002)
        g = np.clip(g, lo - rand, hi + rand)
        return float(g[0]), float(g[1])
