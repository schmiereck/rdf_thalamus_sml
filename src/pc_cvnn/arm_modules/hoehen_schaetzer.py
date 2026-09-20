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

    WARUM LOKAL UND NICHT GLOBAL LINEAR (2026-09-20, gemessen):
    Die erste Fassung war EIN globaler linearer Fit.  Der traegt, solange es EINEN Grundriss gibt,
    und bricht vollstaendig zusammen, sobald es zwei gibt -- 33 %, also Grundrate, und zwar AUCH
    dann, wenn er beide Grundrisse gesehen hat
    (wiki/befunde/zweiter-grundriss-bricht-die-hoehe.md).  Der Grund ist, dass der Grundriss die
    scheinbare Flaeche 7,5-mal so stark hebt wie die Hoehe (685 gegen 91): in einem Topf sind
    beide in der Flaeche ununterscheidbar vermengt, und eine einzige Ebene durch alles lernt den
    Mittelwert.

    Der Ausweg braucht KEINE neue Eingabe und keine Identitaet von aussen: die beiden Grundrisse
    liegen im Merkmalsraum weit auseinander (Flaeche 740 gegen 1425).  Ein Modell, das nur aus der
    NACHBARSCHAFT lernt, wird dadurch von selbst zu einem Modell je Grundriss, ohne dass ihm
    jemand sagt, dass es zwei gibt -- und es faengt zugleich die Kruemmung ueber den Ort mit.

        beide Grundrisse, stellenweise gehalten     global linear   lokal k=10
                                                         33 %          92 %
                                                       3,38 mm       0,73 mm
        je Grundriss ein eigener linearer Schaetzer: 68 % / 77 %  (also schlechter als lokal)

    K IST NICHT EINGESTELLT, sondern die uebliche Faustregel: doppelt so viele Nachbarn wie
    Parameter (4 Merkmale + Achsenabschnitt = 5, also 10).  Gemessen ist k = 10 und k = 12
    gleichauf (92 %, 0,73 mm); groessere Nachbarschaften fallen wieder ab (k = 45 -> 49 %), weil
    sie die Grundrisse wieder vermischen.

    ER BRAUCHT DAFUER ZEILEN, und das ist die ehrliche Kehrseite (Zeilen = Stellen x Hoehen x
    Grundrisse, stellenweise gehalten):

        24 Zeilen  36 %   |  60 Zeilen  74 %   |  174 Zeilen  93 %

    Ein einzelner 60-Episoden-Lauf liefert rund 32.  Der Schaetzer liegt deshalb im ZUSTAND und
    sammelt ueber Laeufe hinweg weiter -- genau dafuer ist die Persistenz da.
    """

    MIN_ZEILEN = 12          # darunter wird nicht geschaetzt (die Sonde hatte 90)
    MAX_ZEILEN = 4000
    NACHBARN = 10            # 2 x (4 Merkmale + Achsenabschnitt), s. oben -- nicht eingestellt

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
        """Nur die STANDARDISIERUNG vorbereiten -- gefittet wird je Anfrage, lokal.

        Der Massstab kommt aus allen Zeilen: sonst waere der Abstandsbegriff, mit dem die
        Nachbarn gesucht werden, von der Flaeche beherrscht (sie zaehlt in Tausenden, der Ort in
        Zehnteln) und die Nachbarschaft ignorierte den Ort vollstaendig.
        """
        X = np.asarray(self.X, float)
        self.mu = X.mean(0); self.sd = X.std(0) + 1e-9
        self.w = np.asarray(self.y, float)          # nur Merker, dass der Massstab steht
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
        X = (np.asarray(self.X, float) - self.mu) / self.sd
        y = np.asarray(self.y, float)
        z = (m - self.mu) / self.sd
        # DIE NAECHSTEN NACHBARN, und nur aus ihnen die Ebene.  Das ist der ganze Unterschied zur
        # ersten Fassung (s. Klassenkopf): zwei Auflagen verschiedenen Grundrisses liegen hier
        # weit auseinander, die Nachbarschaft enthaelt deshalb nur die eine -- ohne dass irgendwo
        # steht, dass es zwei gibt.
        idx = np.argsort(np.linalg.norm(X - z, axis=1))[:min(self.NACHBARN, len(X))]
        A = np.hstack([X[idx], np.ones((len(idx), 1))])
        try:
            wl = np.linalg.solve(A.T @ A + 1e-2 * np.eye(A.shape[1]), A.T @ y[idx])
        except Exception:
            return None
        h = float(np.concatenate([z, [1.0]]) @ wl)
        # AUF DAS GESEHENE BAND BESCHRAENKEN.  Eine Extrapolation weit ueber alles, was der Agent
        # je gesehen hat, ist keine Schaetzung mehr -- und eine zu hohe Oberkante laesst die Klaue
        # in der Luft loslassen, eine zu tiefe rammt sie in die Auflage.
        _lo, _hi = float(min(self.y)), float(max(self.y))
        _rand = 0.25 * max(_hi - _lo, 0.002)
        return float(np.clip(h, _lo - _rand, _hi + _rand))
