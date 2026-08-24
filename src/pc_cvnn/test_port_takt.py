"""NUMMER UND FRISCHE AN DEN PORTS -- taugen sie gegen die Doppelzaehlung? (Nutzerplan, Punkt 3)

Seit Module eine logische Rate haben (Punkt 4), liefert ein Port zwischen zwei gerechneten
Takten seinen GEHALTENEN Stand, und der Verbraucher kann das nicht unterscheiden.  Fuer einen
Regler ist das harmlos, fuer alles KUMULATIVE ist es ein Fehler: derselbe Messwert zaehlt n-mal.

Das ist keine ausgedachte Gefahr.  Live im Projekt, pc_act16:412:
    obj_belief += SERVO_K * conf * (obs - obj_belief)
Bei PERCEPT_RATE=2 wuerde dieselbe gehaltene Sichtung zweimal angewendet.  Dieselbe Bauart
steckt in den Zaehlschwellen des Form-Klassifikators (NOVEL_CONFIRM, BIND_CONFIRM,
STARVE_MIN_EX, OPEN_CAP) -- jede unterstellt FRISCHE, unabhaengige Sichtungen.

Geprueft wird deshalb NICHT nur, dass die Felder existieren, sondern dass
  * die Nummer sich nur bei wirklich gerechneten Takten aendert,
  * ein Port, den ein Takt NICHT beschrieben hat, seine alte Nummer behaelt,
  * das Wasserzeichen jede Nummer je Verbraucher genau einmal herausgibt,
  * src_seq ueber Kanten weitergereicht wird und die Paarungsregel greift,
  * DIE DOPPELZAEHLUNG OHNE WACHE WIRKLICH AUFTRITT und mit Wache verschwindet.

Der letzte Punkt ist der wichtigste: eine Wache gegen ein Phantom waere wertlos.

Aufruf:  python src/pc_cvnn/test_port_takt.py
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

from pc_cvnn.arm_modules import ArmAgent, ArmModule           # noqa: E402


class Quelle(ArmModule):
    """Schreibt bei jedem gerechneten Takt einen neuen Messwert."""

    def __init__(self, rate=1, name="Quelle"):
        super().__init__(name)
        self.rate = rate
        self.k = 0.0
        self.add_out("wert", 1, "Messwert")

    def step(self):
        self.k += 1.0
        self.set_out("wert", [self.k])


class Stumm(ArmModule):
    """Rechnet, schreibt aber NICHTS -- der Fall 'Eingang fehlte, Ausgang bleibt alt'."""

    def __init__(self, name="Stumm"):
        super().__init__(name)
        self.laeufe = 0
        self.add_out("wert", 1, "wird nie gesetzt")

    def step(self):
        self.laeufe += 1


class Senke(ArmModule):
    def __init__(self, name="Senke"):
        super().__init__(name)
        self.add_in("wert", 1, "empfangen")

    def step(self):
        pass


def fall_nummer():
    a = ArmAgent()
    q = a.add(Quelle(rate=3))
    seqs = []
    for _ in range(9):
        a.step(["Quelle"])
        seqs.append(q.out_ports["wert"].seq)
    ok = seqs == [1, 1, 1, 2, 2, 2, 3, 3, 3] and q.k == 3.0
    print(f"  {'A  Nummer steigt nur bei gerechnetem Takt':<52} {'OK ' if ok else 'FEHLER'}  {seqs}")
    return ok


def fall_stumm():
    a = ArmAgent()
    s = a.add(Stumm())
    for _ in range(4):
        a.step(["Stumm"])
    p = s.out_ports["wert"]
    ok = s.laeufe == 4 and p.seq == 0 and not p.frisch_fuer("x")
    print(f"  {'B  nicht beschriebener Port bleibt unfrisch':<52} {'OK ' if ok else 'FEHLER'}  "
          f"laeufe={s.laeufe} seq={p.seq}")
    return ok


def fall_wasserzeichen():
    a = ArmAgent()
    q = a.add(Quelle(rate=2))
    p = q.out_ports["wert"]
    holt = []
    for _ in range(6):
        a.step(["Quelle"])
        holt.append(p.frisch_fuer("servo"))
    # zwei Verbraucher sind unabhaengig voneinander
    zweiter = p.frisch_fuer("lernen")
    ok = holt == [True, False, True, False, True, False] and zweiter is True
    print(f"  {'C  Wasserzeichen je Verbraucher, je Nummer einmal':<52} {'OK ' if ok else 'FEHLER'}  "
          f"{['f' if h else '-' for h in holt]}, zweiter Verbraucher: {zweiter}")
    return ok


def fall_herkunft():
    a = ArmAgent()
    a.add(Quelle(rate=2)); a.add(Senke())
    a.wire("Quelle", "wert", "Senke", "wert")
    a.step(["Quelle", "Senke"])
    e1 = a.modules["Senke"].in_ports["wert"].src_seq
    a.step(["Quelle", "Senke"])                                # gehaltener Takt
    e2 = a.modules["Senke"].in_ports["wert"].src_seq
    a.step(["Quelle", "Senke"])                                # wieder gerechnet
    e3 = a.modules["Senke"].in_ports["wert"].src_seq
    ok = (e1, e2, e3) == (1, 1, 2)
    # Paarungsregel: gleiche Herkunft = paarbar, verschiedene nicht
    p, r = a.modules["Senke"].in_ports["wert"], a.modules["Quelle"].out_ports["wert"]
    r.src_seq = e3
    paart = p.passt_zu(r)
    r.src_seq = 999
    paart_nicht = not p.passt_zu(r)
    ok = ok and paart and paart_nicht
    print(f"  {'D  src_seq wandert ueber die Kante, Paarung greift':<52} {'OK ' if ok else 'FEHLER'}  "
          f"src_seq je Takt {(e1, e2, e3)}")
    return ok


def fall_doppelzaehlung():
    """DIE GEFAHR SELBST -- erst ohne, dann mit Wache."""
    K, CONF = 0.6, 1.0
    ZIEL, ALT = 10.0, 0.0

    def servo(mit_wache):
        a = ArmAgent()
        q = a.add(Quelle(rate=2))
        q.step = lambda: q.set_out("wert", [ZIEL])              # jede Sichtung meldet dasselbe Ziel
        glaube = ALT
        for _ in range(6):
            a.step(["Quelle"])
            p = q.out_ports["wert"]
            if mit_wache and not p.frisch_fuer("servo"):
                continue
            glaube = glaube + K * CONF * (float(p.value[0]) - glaube)
        return glaube

    ohne = servo(False)
    mit = servo(True)
    # 6 Takte, rate=2 -> 3 echte Sichtungen.  Ohne Wache werden 6 Korrekturen gefahren.
    erwartet_mit = ALT
    for _ in range(3):
        erwartet_mit += K * (ZIEL - erwartet_mit)
    ok = (abs(mit - erwartet_mit) < 1e-12) and (ohne > mit + 0.5)
    print(f"  {'E  Doppelzaehlung tritt auf und Wache beseitigt sie':<52} {'OK ' if ok else 'FEHLER'}  "
          f"ohne Wache {ohne:.3f} (6 Korrekturen), mit Wache {mit:.3f} (3, erwartet {erwartet_mit:.3f})")
    return ok


def fall_alte_ports():
    """Ports aus der Zeit VOR Punkt 3 muessen sich nachruesten."""
    p = ArmModule("x").add_out("v", 1).out_ports["v"]
    d = dict(p.__dict__)
    for k in ("seq", "src_seq", "_gesehen", "_geschrieben"):    # kuenstlich auf alt zurueckbauen
        d.pop(k, None)
    roh = pickle.dumps(type(p)("v", 1))
    alt = pickle.loads(roh)
    alt.__setstate__(d)
    ok = alt.seq == 0 and alt.src_seq is None and alt.frisch_fuer("x") is False
    alt.set([1.0], seq=5)
    ok = ok and alt.frisch_fuer("x") is True
    print(f"  {'F  alte Ports aus der Zustandsdatei ruesten nach':<52} {'OK ' if ok else 'FEHLER'}")
    return ok


if __name__ == "__main__":
    print("\n  NUMMER UND FRISCHE AN DEN PORTS (Punkt 3)\n")
    erg = [fall_nummer(), fall_stumm(), fall_wasserzeichen(), fall_herkunft(),
           fall_doppelzaehlung(), fall_alte_ports()]
    print()
    if all(erg):
        print(f"  alle {len(erg)} Faelle bestanden\n")
    else:
        print(f"  {erg.count(False)} von {len(erg)} FEHLGESCHLAGEN\n")
        sys.exit(1)
