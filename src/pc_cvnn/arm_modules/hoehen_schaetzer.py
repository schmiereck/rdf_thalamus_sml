# -*- coding: utf-8 -*-
"""Die Oberkante einer Auflage aus der WAHRNEHMUNG (s. ACT23_HOEHE_SEHEN).

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird und der Zustand auch
ausserhalb von pc_act23.py ladbar bleibt.
"""
import numpy as np


class HoehenSchaetzer:
    """Die Oberkante einer Auflage AUS DER WAHRNEHMUNG.

    Merkmale sind ausschliesslich Groessen, die in DERSELBEN Detektion stehen, die die
    Zieladresse ohnehin aufloest: scheinbare Flaeche, Materialdicke und der wahrgenommene Ort.
    Kein `geom_size`, kein `obj_pos`.

    WARUM DER ORT DAZUGEHOERT und das kein Schummeln ist: die Flaeche allein ist zweideutig, weil
    die Perspektive sie ebenso veraendert wie die Hoehe (ein flacher Sockel nah an der Kamera
    liest groesser als ein hoher weit weg).  Der Ort ist das Erste, was jede Detektion liefert --
    er aufloest die Zweideutigkeit, ohne etwas hinzuzufuegen, was der Agent nicht ohnehin sieht.

    DAS GERUEST: gelabelt wird mit der privilegierten Oberkante.  Das ist der zulaessige Gebrauch
    nach laufzeit-regeln.md -- eine Regel darf Trainingsdaten stuetzen.  Zur Laufzeit liest
    ACT23_HOEHE_SEHEN=1 dann nur noch den Schaetzer, und das Privileg ist aus dem Pfad heraus.

    WARUM EIN LINEARES MODELL: die Sonde hat es mit genau diesem geschafft (1,31 mm,
    stellenweise gehalten).  Das ist die kleinste Fassung, die der Befund deckt -- eine groessere
    waere hier nicht belegt, sondern geraten.  Der Platz ist da, wenn eine Messung mehr verlangt.
    """

    MIN_ZEILEN = 12          # darunter wird nicht geschaetzt (die Sonde hatte 90)
    MAX_ZEILEN = 4000

    def __init__(self):
        self.X, self.y = [], []
        self.w = None
        self.mu = self.sd = None
        self.n_fit = 0

    @staticmethod
    def merkmale(det):
        """Die vier wahrgenommenen Zahlen, oder None wenn die Detektion sie nicht hergibt."""
        if det is None:
            return None
        _a, _d, _p = det.get("area"), det.get("dicke"), det.get("pos")
        if _a is None or _d is None or _p is None:
            return None
        return np.array([float(_a), float(_d), float(_p[0]), float(_p[1])], float)

    def merken(self, det, hoehe):
        m = self.merkmale(det)
        if m is None:
            return False
        self.X.append(m); self.y.append(float(hoehe))
        if len(self.X) > self.MAX_ZEILEN:
            self.X = self.X[-self.MAX_ZEILEN:]; self.y = self.y[-self.MAX_ZEILEN:]
        self.w = None                                  # neu gefittet wird beim naechsten Schaetzen
        return True

    def _fit(self):
        X = np.asarray(self.X, float); y = np.asarray(self.y, float)
        # STANDARDISIEREN, sonst ist die Ausgleichsrechnung schlecht konditioniert: die Flaeche
        # zaehlt in Tausenden, der Ort in Zehnteln.  Dasselbe Verfahren wie in Policy.fit (imu/isd).
        self.mu = X.mean(0); self.sd = X.std(0) + 1e-9
        Z = np.hstack([(X - self.mu) / self.sd, np.ones((len(X), 1))])
        # Ein kleiner Daempfer haelt den Fit ruhig, solange wenige Zeilen da sind.
        A = Z.T @ Z + 1e-3 * np.eye(Z.shape[1])
        self.w = np.linalg.solve(A, Z.T @ y)
        self.n_fit = len(X)

    def schaetzen(self, det):
        """Die Oberkante in m, oder None -- dann faellt der Aufrufer LAUT zurueck."""
        if len(self.X) < self.MIN_ZEILEN:
            return None
        m = self.merkmale(det)
        if m is None:
            return None
        if self.w is None or self.n_fit != len(self.X):
            try:
                self._fit()
            except Exception:
                return None
        z = np.concatenate([(m - self.mu) / self.sd, [1.0]])
        h = float(z @ self.w)
        # AUF DAS GESEHENE BAND BESCHRAENKEN.  Eine Extrapolation weit ueber alles, was der Agent
        # je gesehen hat, ist keine Schaetzung mehr -- und eine zu hohe Oberkante laesst die Klaue
        # in der Luft loslassen, eine zu tiefe rammt sie in die Auflage.
        _lo, _hi = float(min(self.y)), float(max(self.y))
        _rand = 0.25 * max(_hi - _lo, 0.002)
        return float(np.clip(h, _lo - _rand, _hi + _rand))
