"""RateWrapper — eine beliebige Callable mit EIGENER RATE hinter Ports.

WOZU.  Nicht jeder Teil des Agenten ist ein Modul.  Manches ist eine act23-Closure, die mehrere
Module orchestriert (der Bild-Tracker) oder ein Objekt ohne Portschicht (der latente Ziel-Servo,
der aus einem Persistenz-Blob per __new__ wiederhergestellt wird und deshalb GAR KEINE Ports
hat).  Um so etwas trotzdem takten zu koennen -- fuer Punkt 4 des Nutzerplans -- braucht es eine
Huelle: Argument in den In-Port, Callable rufen, Ergebnis in den Out-Port; faellt der Takt aus,
behaelt der Out-Port seinen letzten Stand.

WARUM GENERISCH.  Das PerceptionModule fuehrte die Taktbuchhaltung anfangs selbst; beim zweiten
Modul mit Rate wanderte sie nach ArmModule/ArmAgent.  Diese Huelle ist der dritte Fall, und sie
schreibt die Mechanik NICHT noch einmal auf -- sie erbt sie.  `rate` und die Frische-Nummern
kommen vollstaendig aus der Basis.

Ports
  in  : arg       (dim_in)   das Argument des Aufrufs
  out : ergebnis  (dim_out)  der letzte gerechnete Rueckgabewert
"""
from __future__ import annotations

from .base import ArmModule


class RateWrapper(ArmModule):
    def __init__(self, dim_in: int, dim_out: int, rate: int = 1,
                 name: str = "RateWrapper") -> None:
        super().__init__(name)
        self.rate = max(1, int(rate))
        self._fn = None
        (self.add_in("arg", dim_in, "Argument des gekapselten Aufrufs")
             .add_out("ergebnis", dim_out, "letzter gerechneter Rueckgabewert"))

    def bind(self, fn) -> "RateWrapper":
        """Die Callable dieser Episode einhaengen und den Takt zuruecksetzen."""
        self._fn = fn
        self.reset_takt()
        return self

    def step(self) -> None:
        """EINEN Takt rechnen.  Ob dieser Takt drankommt, entscheidet die Rate im ArmAgent --
        faellt er aus, wird step() gar nicht gerufen und der Out-Port behaelt seinen Stand."""
        if self._fn is None:
            return
        a = self.get_in("arg")
        if a is None:
            return
        self.set_out("ergebnis", self._fn(a))

    def surprise(self) -> dict | None:
        if self._fn is None:
            return None
        return {"seq": self.seq, "rate": self.rate, "gehalten": self.n_gehalten}
