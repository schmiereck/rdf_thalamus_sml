"""A small, pluggable MODULE FRAMEWORK for the arm agent — the act14-19 port of the
1D PCModule architecture.

In the 1D line (act5-act11) the agent was split into PCModules (VisualCortex, BodyModel,
Premotor/Motor) with declared, named PORTS, plus separate PC-net modules (GoalModule,
Planner) coupled over clean interfaces.  That "pluggable, talks-only-over-ports" structure
is what this module restores for the MuJoCo arm.

Design: every component is its own `ArmModule` with declared, typed in/out `Port`s; an
`ArmAgent` wires ports together ("zusammengesteckt") and can step the modules.  The
internals are heterogeneous — a `PCNetwork`, an analytic linear FK, an MLP — but they all
implement the SAME port interface, so they plug in identically.  PC-net-backed modules
additionally expose their `PCModule` node-port grouping via `pc_module()`: the literal 1D
PCModule lives INSIDE them.  New interfaces are just new ports.
"""
from __future__ import annotations

import numpy as np


class Port:
    """Ein benannter Datenkanal an einem Modul: haelt den letzten Wert, SEINE NUMMER und die
    Nummer der Eingabe, aus der er entstand (Nutzerplan 2026-08-23, Punkt 3).

    WOZU DIE NUMMERN.  Seit Modulen eine logische Rate haben (Punkt 4), liefert ein Port zwischen
    zwei gerechneten Takten seinen GEHALTENEN Stand -- und der Verbraucher kann das nicht
    unterscheiden.  Fuer einen Regler ist das harmlos; fuer alles KUMULATIVE ist es ein Fehler:
    derselbe Messwert zaehlt dann n-mal.

    Das ist kein erfundenes Risiko.  Live im Projekt: die Servo-Korrektur in pc_act16:412 lautet
        obj_belief += SERVO_K * conf * (obs - obj_belief)
    Bei PERCEPT_RATE=2 wird dieselbe gehaltene Sichtung ZWEIMAL angewendet und zieht den Glauben
    doppelt so stark zu einem veralteten Wert.  Dieselbe Bauart steckt in den Zaehlschwellen des
    Form-Klassifikators (NOVEL_CONFIRM=3, BIND_CONFIRM=3, STARVE_MIN_EX=6, OPEN_CAP=80): jede
    unterstellt, dass eine gezaehlte Sichtung eine FRISCHE, unabhaengige Sichtung ist.

    seq       Nummer des Erzeugers, als dieser Wert geschrieben wurde.  Aendert sich NUR, wenn
              wirklich gerechnet wurde -- ein gehaltener Takt laesst sie stehen.
    src_seq   Nummer der Eingabe, aus der dieser Wert entstand (ueber Kanten weitergereicht).
              Damit laesst sich beim Lernen eine Vorhersage mit dem PASSENDEN Ausgang paaren
              statt mit dem, der zufaellig gerade vorliegt.
    """

    def __init__(self, name: str, dim: int, desc: str = "") -> None:
        self.name = name
        self.dim = dim
        self.desc = desc
        self.value = None
        self.seq = 0                       # 0 = noch nie geschrieben
        self.src_seq = None
        self._gesehen: dict[str, int] = {}  # Verbraucher -> zuletzt verbrauchte Nummer
        self._geschrieben = False

    def __setstate__(self, d):
        """Alte Ports aus der Zustandsdatei nachruesten.

        Module werden MITSAMT ihrer Port-Objekte gepickelt; ein Port aus der Zeit vor Punkt 3 hat
        weder seq noch src_seq noch das Wasserzeichen.  Einmal beim Laden auffuellen ist billiger
        und sicherer als getattr an jeder Zugriffsstelle -- und es kann nicht vergessen werden.
        """
        self.__dict__.update(d)
        self.__dict__.setdefault("seq", 0)
        self.__dict__.setdefault("src_seq", None)
        self.__dict__.setdefault("_gesehen", {})
        self.__dict__.setdefault("_geschrieben", False)

    def set(self, v, seq: int | None = None, src_seq=None):
        """Wert setzen (atomar: erst umwandeln, dann zuweisen)."""
        neu = None if v is None else np.asarray(v, float)
        self.value = neu
        self._geschrieben = True           # fuer _stempeln: DIESER Takt hat den Port beschrieben
        if seq is not None:
            self.seq = int(seq)
        if src_seq is not None:
            self.src_seq = src_seq
        return self.value

    # ------------------------------------------------------------------
    def frisch_fuer(self, verbraucher: str) -> bool:
        """Hat `verbraucher` diese Nummer noch NICHT verbraucht?  Merkt sie sich dabei.

        Der Wasserzeichen-Zaehler steht JE VERBRAUCHER, weil derselbe Port mehrere haben kann und
        einer davon lernen darf, waehrend ein anderer nur regelt.  Genau die Regel aus Punkt 3:
        "Lernen nur auf geaenderter Nummer".
        """
        if self.seq == 0:
            return False                   # noch nie geschrieben -> nichts zu verbrauchen
        if self._gesehen.get(verbraucher) == self.seq:
            return False
        self._gesehen[verbraucher] = self.seq
        return True

    def passt_zu(self, anderer: "Port") -> bool:
        """Stammen beide Werte aus DERSELBEN Eingabe-Generation?  Die Paarungsregel aus Punkt 3.

        Fuer das Lernen aus (Vorhersage, Ausgang): stimmen die Herkunftsnummern nicht ueberein,
        gehoert der Ausgang zu einer anderen Vorhersage und das Paar ist WERTLOS -- nicht nur
        verrauscht, sondern falsch.
        """
        return (self.src_seq is not None and anderer.src_seq is not None
                and self.src_seq == anderer.src_seq)

    def __repr__(self) -> str:
        return f"Port({self.name!r}, dim={self.dim}, seq={self.seq})"


class ArmModule:
    """Base class: declares named in/out ports and a `step()`.  A subclass reads its
    in-ports, computes, and writes its out-ports inside `step()`."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.in_ports: dict[str, Port] = {}
        self.out_ports: dict[str, Port] = {}
        # LOGISCHE RATE (Nutzerplan 2026-08-23, Punkt 4).  rate=n heisst: dieses Modul rechnet nur
        # jeden n-ten Takt; dazwischen behalten seine Out-Ports ihren letzten Stand, und der
        # Verbraucher kann das nicht unterscheiden.  Genau das ist der Gegenstand von Punkt 4.
        # Durchgesetzt wird sie im ArmAgent, nicht im Modul -- sonst muesste jedes Modul dieselbe
        # Buchhaltung noch einmal schreiben (die erste Fassung im PerceptionModule tat genau das).
        self.rate = 1
        self._tick = 0
        self.seq = 0                       # tatsaechlich GERECHNETE Takte
        self.fresh = False                 # war der letzte Takt neu oder gehalten?
        self.n_gehalten = 0

    # -- logische Rate --
    def faellig(self) -> bool:
        """Rechnet dieses Modul im aktuellen Takt?  Zaehlt den Takt mit hoch.

        getattr statt direktem Zugriff: der Projektzustand enthaelt GEPICKELTE Modulinstanzen aus
        einer Zeit vor diesen Feldern -- __init__ laeuft beim Laden nicht, ein direkter Zugriff
        waere ein AttributeError mitten im Lauf.  Gleiche Lehre wie _ensure_ports im Welt-Modell.
        """
        r = max(1, int(getattr(self, "rate", 1)))
        t = int(getattr(self, "_tick", 0))
        self._tick = t + 1
        return (t % r) == 0

    def reset_takt(self) -> None:
        """Taktzaehler und Diagnose zuruecksetzen (z.B. zu Episodenbeginn)."""
        self._tick = 0
        self.seq = 0
        self.fresh = False
        self.n_gehalten = 0

    def _stempeln(self, seq: int) -> None:
        """Die Nummer dieses Takts auf die Ports schreiben, die DIESER Takt gesetzt hat.

        Nicht auf alle: ein Modul, dessen step() diesmal nichts geschrieben hat (fehlender
        Eingang, nicht trainiert, kein Glaube vorhanden), soll seine alte Nummer behalten --
        sonst saehe der Verbraucher einen unveraenderten Wert faelschlich als frisch an.  Genau
        diese stille Veralterung war der Anlass fuer Punkt 3 (s. die Anmerkung am Regelpfad).
        """
        for p in self.out_ports.values():
            if getattr(p, "_geschrieben", False):
                p.seq = int(seq)
                p._geschrieben = False

    # -- port declaration (chainable) --
    def add_in(self, name: str, dim: int, desc: str = "") -> "ArmModule":
        self.in_ports[name] = Port(name, dim, desc); return self

    def add_out(self, name: str, dim: int, desc: str = "") -> "ArmModule":
        self.out_ports[name] = Port(name, dim, desc); return self

    # -- value accessors --
    def get_in(self, name: str):
        return self.in_ports[name].value

    def set_in(self, name: str, v):
        return self.in_ports[name].set(v)

    def get_out(self, name: str):
        return self.out_ports[name].value

    def set_out(self, name: str, v):
        return self.out_ports[name].set(v)

    # -- overridables --
    def step(self) -> None:
        """Read in-ports, compute, write out-ports.  Override in subclasses."""
        raise NotImplementedError

    def surprise(self) -> dict | None:
        """Optional: the module's current surprise / diagnostics (for SurpriseViz), or None."""
        return None

    def pc_module(self):
        """Optional: the underlying PCModule node-port grouping (PC-net modules only)."""
        return None

    def __repr__(self) -> str:
        return (f"{type(self).__name__}({self.name!r}, "
                f"in={list(self.in_ports)}, out={list(self.out_ports)})")


class ArmAgent:
    """Holds module instances + the wiring between their ports, and runs them.

    `wire(src, 'out_port', dst, 'in_port')` connects an out-port to an in-port (dims must
    match).  `step(order)` propagates wired values then steps each module in `order`, so a
    downstream module sees the upstream module's fresh outputs.  `surprises()` collects the
    per-module surprise for the live viz; `summary()` prints the plugged-together wiring."""

    def __init__(self, name: str = "ArmAgent") -> None:
        self.name = name
        self.modules: dict[str, ArmModule] = {}
        self.edges: list[tuple[str, str, str, str]] = []   # (src_mod, src_port, dst_mod, dst_port)

    def add(self, module: ArmModule) -> ArmModule:
        if module.name in self.modules:
            raise ValueError(f"module {module.name!r} already added")
        self.modules[module.name] = module
        return module

    def wire(self, src, src_port: str, dst, dst_port: str) -> "ArmAgent":
        sm = self.modules[src] if isinstance(src, str) else src
        dm = self.modules[dst] if isinstance(dst, str) else dst
        sp, dp = sm.out_ports[src_port], dm.in_ports[dst_port]
        if sp.dim != dp.dim:
            raise ValueError(f"port dim mismatch: {sm.name}.{src_port}({sp.dim}) -> "
                             f"{dm.name}.{dst_port}({dp.dim})")
        self.edges.append((sm.name, src_port, dm.name, dst_port))
        return self

    def _propagate(self) -> None:
        """Werte ueber die Kanten reichen -- MITSAMT ihrer Herkunft.

        Der Zielport uebernimmt die Nummer der Quelle als seine src_seq: was hier ankommt, wurde
        aus GENAU dieser Generation der Quelle gebildet.  Damit kann ein Modul spaeter pruefen,
        ob eine Vorhersage und ein Ausgang zur selben Eingabe gehoeren (Port.passt_zu).
        """
        for (sm, sp, dm, dp) in self.edges:
            q = self.modules[sm].out_ports[sp]
            self.modules[dm].in_ports[dp].set(q.value, seq=q.seq, src_seq=q.seq)

    def step(self, order: list[str]) -> None:
        """Step the modules named in `order`, propagating wired port values before each.

        HAELT DIE LOGISCHE RATE EIN: ein Modul mit rate=n rechnet nur jeden n-ten Takt.  Faellt
        ein Takt aus, behalten seine Out-Ports einfach ihren letzten Stand -- es wird nichts
        geschrieben, also steht der alte Wert noch da.  Der Verbraucher liest ihn und kann NICHT
        unterscheiden, ob er frisch ist; `fresh` und `seq` am Modul machen den Unterschied fuer
        die MESSUNG wieder sichtbar (Vorgriff auf Punkt 3).
        """
        for nm in order:
            self._propagate()
            m = self.modules[nm]
            if m.faellig():
                m.step()
                m.seq = int(getattr(m, "seq", 0)) + 1
                m.fresh = True
                m._stempeln(m.seq)
            else:
                m.fresh = False
                m.n_gehalten = int(getattr(m, "n_gehalten", 0)) + 1
        self._propagate()

    def surprises(self) -> dict:
        return {nm: m.surprise() for nm, m in self.modules.items()}

    def summary(self) -> str:
        lines = [f"ArmAgent {self.name!r} — {len(self.modules)} modules, {len(self.edges)} wires"]
        for nm, m in self.modules.items():
            tag = "  (PC-net)" if m.pc_module() is not None else ""
            lines.append(f"  [{nm}]{tag}  in={list(m.in_ports)}  out={list(m.out_ports)}")
        lines.append("  wiring (plugged together):")
        for (sm, sp, dm, dp) in self.edges:
            lines.append(f"    {sm}.{sp}  ->  {dm}.{dp}")
        return "\n".join(lines)
