"""PerceptionModule — die Bild-fuer-Bild-Wahrnehmung als echtes Modul mit EIGENER RATE.

ANLASS (Nutzerplan 2026-08-23, Punkt 2/4).  `track_fn` war der wichtigste der 15 Closure-
Callbacks, mit denen act23 `run_combined` verdrahtet -- und der einzige, der sich NICHT einfach
umstecken liess.  Die anderen Kanten (ObjectMemory, RuntimePolicy, WorldModel-Aktionswahl) waren
Modulaufrufe mit Argumenten: Werte in die In-Ports, Modul takten, Ergebnis aus dem Out-Port.
`track_fn` dagegen IST kein Modulaufruf, sondern act23-Code, der intern die Fovea, den
Form-Klassifikator, den Farb-Split und das Objektgedaechtnis orchestriert.  Den Rueckgabewert in
einen Port zu schreiben und sofort zurueckzulesen waere ein zusaetzlicher Sprung ohne entfernte
Kopplung gewesen -- eine Attrappe.

WAS DIESES MODUL ANDERS MACHT.  Es besitzt die RATE.  Nicht der Aufrufer entscheidet, ob dieser
Takt gerechnet wird, sondern das Modul: bei `rate > 1` rechnet es nur jeden n-ten Takt und
liefert dazwischen den GEHALTENEN letzten Stand aus seinen Ports.  Damit ist es kein Umweg mehr,
sondern die Stelle, an der Punkt 4 ansetzt -- "logische Raten, seriell und deterministisch".

WARUM DAS NICHT AUS DER LUFT GEGRIFFEN IST.  run_combined taktet die Wahrnehmung heute schon
hart kodiert mit `k % 4 == 0` (pc_act16:403) und `s % 2 == 0` (:679).  Die Multi-Raten-Struktur
EXISTIERT also bereits -- nur unsichtbar, unveraenderlich und nie gegen eine Alternative
gemessen.  Dieses Modul macht sie sichtbar und einstellbar; die Modul-Rate MULTIPLIZIERT sich mit
der von act16 (rate=2 heisst: jedes 8. Bild statt jedes 4.).

VORGRIFF AUF PUNKT 3 (bewusst klein gehalten): `seq` zaehlt die tatsaechlich gerechneten Takte,
`fresh` sagt, ob der letzte Takt neu gerechnet oder gehalten wurde.  Ohne diese beiden waere eine
Rate > 1 von aussen gar nicht beobachtbar -- man saehe nur, dass sich Zahlen nicht aendern, und
koennte das nicht von "die Welt steht still" unterscheiden.  Genau diese Unterscheidbarkeit ist
der Kern von Punkt 3.

Ports
  out : object_xy (2)  wahrgenommene Weltposition des kommandierten Objekts (None = nicht gesehen)
        obs_conf  (1)  abgestufte Verlaesslichkeit dieser Sichtung, [0,1]
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule


class PerceptionModule(ArmModule):
    def __init__(self, rate: int = 1, name: str = "Perception") -> None:
        super().__init__(name)
        self.rate = max(1, int(rate))
        self._tracker = None                       # die act23-Closure, je Episode neu gebunden
        self._tick = 0                             # Takte seit dem letzten bind()
        self.seq = 0                               # tatsaechlich GERECHNETE Takte
        self.fresh = False                         # war der letzte Takt neu oder gehalten?
        self.n_gehalten = 0                        # Diagnose: wie oft gehalten wurde
        (self.add_out("object_xy", 2, "wahrgenommene Objekt-Weltposition (None = nicht gesehen)")
             .add_out("obs_conf", 1, "abgestufte Verlaesslichkeit der Sichtung [0,1]"))

    # ------------------------------------------------------------------
    def bind(self, tracker) -> "PerceptionModule":
        """Den Bild-Tracker dieser Episode einhaengen und den Takt zuruecksetzen.

        act23 waehlt je Episode einen anderen Tracker (form-, farb- oder blob-gefuehrt).  Das
        Modul bleibt dasselbe -- es kapselt die RATE und die Ports, nicht die Wahrnehmungsart.
        """
        self._tracker = tracker
        self._tick = 0
        self.fresh = False
        self.n_gehalten = 0
        return self

    def step(self) -> None:
        if self._tracker is None:
            return
        gerechnet = (self._tick % self.rate) == 0
        self._tick += 1
        if not gerechnet:                          # HALTEN: die Ports behalten ihren letzten Stand
            self.fresh = False
            self.n_gehalten += 1
            return
        tr = self._tracker()
        obs, conf = tr if isinstance(tr, tuple) else (tr, 0.0)
        self.set_out("object_xy", obs)             # None-faehig: Port.set(None) -> value None
        self.set_out("obs_conf", [float(conf)])
        self.seq += 1
        self.fresh = True

    # ------------------------------------------------------------------
    def observation(self):
        """Was der Aufrufer sieht: (object_xy, obs_conf) aus den PORTS -- bei gehaltenem Takt
        also der letzte gerechnete Stand.  Genau diese Ununterscheidbarkeit ist der Gegenstand
        von Punkt 4; `fresh`/`seq` machen sie fuer die Messung wieder unterscheidbar."""
        xy = self.get_out("object_xy")
        c = self.get_out("obs_conf")
        return xy, (0.0 if c is None else float(np.ravel(c)[0]))

    def surprise(self) -> dict | None:
        if self._tracker is None:
            return None
        return {"seq": self.seq, "rate": self.rate, "gehalten": self.n_gehalten,
                "fresh": float(self.fresh)}
