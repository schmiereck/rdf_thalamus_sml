# -*- coding: utf-8 -*-
"""Haelt der Griff noch? (s. ACT23_HALT_SELBST) -- ein eigener Lerner fuer EINEN Aspekt.

Eigenes Modul, damit der Lerner unter seinem echten Pfad gepickelt wird (wie LoslassKopf).
"""
import numpy as np


class HaltKopf:
    """VORSCHLAG aus dem Tastsinn, VETO aus eigener Erfahrung (Muster vom Loslassen).

    WARUM (wiki/befunde/zufassen-selbst.md): in 11 von 80 Episoden fiel das Objekt beim Tragen
    heraus, der Druck fiel auf 0, die Klaue blieb zu, und der Arm fuhr 260-600 Schritte leer weiter.
    Der Tastsinn meldete den Verlust -- niemand hoerte hin.  Aber: auch gelieferte Episoden tragen
    teils mit 0 N (der Streifen sitzt an einem Finger, der Nagel traegt den Griff).  "Kein Druck"
    allein heisst also nicht "verloren".

    VORSCHLAG (fest, nur Sinnesdaten): es hat in diesem Griff schon getragen, die Klaue ist zu, die
    Hand ist oben, und seit VORSCHLAG_N Schritten kein Druck.
    VETO (gelernt): p(die Episode wird trotzdem geliefert | Aspekte).  Erwartet das Netz Lieferung,
    war es ein Fehlalarm -> nicht eingreifen.  Sonst: Klaue auf, die Policy greift neu.
    ETIKETT: das Selbst-Urteil der Kamera am Episodenende -- NUR fuer Vorschlaege, auf die NICHT
    gehandelt wurde (keine Selbstbestaetigung: nach dem Oeffnen ist "nicht geliefert" die Folge des
    Oeffnens, nicht des Zustands).

    Aspekte (aus dem Policy-Zustand plus eigener Zaehlung, nichts Privilegiertes):
      Schritte ohne Druck | Klauenwinkel | hoechster Druck in diesem Griff | Hand ueber Ruhehoehe |
      Hand <-> Ziel | Weg der Hand seit Druckverlust | Objekt-Kurzachse (geschaetzt) | Objekthoehe
    """

    VORSCHLAG_N = 10
    MIN_ZEILEN = 20
    MIN_KLASSE = 5

    def __init__(self):
        self.X, self.y = [], []
        self.net = None

    @staticmethod
    def aspekte(s, ohne, pmax, weg):
        s = np.asarray(s, float)
        return np.array([ohne / 100.0, float(s[8]), pmax, float(s[2]) - float(s[9]),
                         float(np.linalg.norm(s[0:2] - s[6:8])), weg,
                         float(s[10]), float(s[9])], float)

    def merken(self, a, geliefert):
        self.X.append(np.asarray(a, float)); self.y.append(1.0 if geliefert else 0.0)
        if len(self.X) > 4000:
            self.X = self.X[-4000:]; self.y = self.y[-4000:]

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
        self.net = Policy(din=8, dout=1, hid=16, rng=np.random.default_rng(17))
        self.net.fit(np.asarray(self.X, float), y[:, None], epochs=epochs, quiet=True)
        return True

    def p_geliefert(self, a):
        if self.net is None:
            return 1.0
        return float(self.net.predict(np.asarray(a, float))[0])


class HaltSehenKopf:
    """GELERNTER VORSCHLAG "ist das Objekt noch an der Hand?" (s. ACT23_HALT_SELBST=4).

    WARUM: der Vorschlag des HaltKopf ("10 Schritte kein Druck") ist eine feste Schwelle -- als
    Laufzeitregel unzulaessig (wiki/mechanismen/laufzeit-regeln.md), obwohl Neugreifen in der
    Richtung half (wiki/befunde/halt-kopf.md).  Hier lernt ein Netz dieselbe Entscheidung aus
    EIGENER Erfahrung.

    ETIKETT AUS DER KAMERA -- der Selbst/Fremd-Test: zweimal hinsehen, dazwischen faehrt die Hand.
    Wandert der Fleck in der Farbe des eigenen Objekts mit der Hand mit, haelt der Griff; bleibt er
    liegen, ist das Objekt verloren.  Keine Hoehe, kein Privileg, unempfindlich gegen die Parallaxe
    der schraegen Kamera (sie verschiebt beide Blicke gleich).  Die Farbe merkt sich der Agent selbst
    beim ersten Tragen (Fleck naechst der Hand).

    EINGANG des Netzes (nur Tastsinn + Propriozeption -- das Netz soll vorhersagen, was die Kamera
    saehe):  Druck | Schritte ohne Druck | hoechster Druck in diesem Griff | Klaue | Hand ueber Ruhe
    | Handgeschwindigkeit
    """

    MIN_ZEILEN = 20
    MIN_KLASSE = 5

    def __init__(self):
        self.X, self.y = [], []
        self.net = None

    @staticmethod
    def aspekte(s, ohne, pmax, v):
        s = np.asarray(s, float)
        return np.array([float(s[12]), min(ohne, 100) / 100.0, pmax, float(s[8]),
                         float(s[2]) - float(s[9]), v], float)

    def merken(self, a, haelt):
        self.X.append(np.asarray(a, float)); self.y.append(1.0 if haelt else 0.0)
        if len(self.X) > 4000:
            self.X = self.X[-4000:]; self.y = self.y[-4000:]

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
        self.net = Policy(din=6, dout=1, hid=16, rng=np.random.default_rng(19))
        self.net.fit(np.asarray(self.X, float), y[:, None], epochs=epochs, quiet=True)
        return True

    def p_haelt(self, a):
        if self.net is None:
            return 1.0
        return float(self.net.predict(np.asarray(a, float))[0])
