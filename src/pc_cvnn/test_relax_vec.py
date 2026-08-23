"""RECHNET DIE GEBUENDELTE RELAXATION DASSELBE WIE DIE OBJEKT-SCHLEIFE?

`relax_vec` ersetzt Phase 3 des PC-Netzes durch gestapelte Arrays.  Das ist eine Aenderung am
Herzen der Maschine -- sie braucht einen Beweis, keinen Rauchtest.

WIE HIER GEPRUEFT WIRD, UND WARUM SO.  Ein erster Anlauf verglich zwei getrennt laufende Netze
ueber mehrere LERNschritte hinweg.  Das war das falsche Kriterium: gemessen weichen `einsum`
und BLAS-Matrixprodukt um ~1e-15 voneinander ab (unvermeidlich -- sie fassen intern anders
zusammen), und das lernende Netz verstaerkt diesen Unterschied chaotisch, bis nach sechs
Schritten 1e-2 dasteht.  Das ist keine Aussage ueber die Richtigkeit der Buendelung, sondern
ueber die Lyapunov-Empfindlichkeit des Netzes.

Geprueft werden deshalb DIE GEAENDERTEN PHASEN SELBST -- Phase 3 (Relaxation) und Phase 4
(Lernen): bei jedem Schritt eines echten Laufs werden beide Fassungen AUS DEMSELBEN ZUSTAND
gestartet und ihre Ergebnisse verglichen; danach laeuft der Lauf mit dem Objekt-Ergebnis
weiter.  So wird ueber viele, im Lauf immer weiter gelernte Zustaende hinweg jedes Mal exakt
die geaenderte Phase gemessen, ohne dass sich Rundungsunterschiede aufschaukeln und den Befund
verdecken.  Verglichen wird der volle Zustand: mu/pi/eps, die gelernten W und V, die
Zeitpuffer und die Diagnose (relax_steps, sensor_error, state_error).

Schranke: 1e-12 RELATIV.  Maschinengenauigkeit liegt bei ~1e-15; alles darueber waere ein
echter Rechenfehler und kein Rundungsrest.

Faelle:
  A  das echte Fovea-Netz (321 Knoten, 1883 Verbindungen)
  B  gemischt: verschiedene Aktivierungen, GLEICHE Dimension bei verschiedener Aktivierung
     (der Fall, an dem eine nach Dimensionen gruppierende Fassung still falsch rechnet),
     Knoten ohne Eingang, Mehrfach-Fan-in, LATERAL neben UP, ungleiche pressure_scale
  C  Klemmen/Loesen mitten im Lauf (die Sensorzellen tun das je Bild)
  D  nicht-endliche Werte, in BEIDEN Phasen einzeln vergiftet -- die Regeln arbeiten auf dem
     GANZEN Knotenvektor bzw. der GANZEN dW-Matrix, nicht elementweise
  G  W und pressure_scale werden zwischen den Schritten von aussen veraendert (planner_chain)
  H  der Betrags-Deckel greift wirklich -- ohne diesen Fall besteht eine Fassung ganz OHNE
     Deckelung alle uebrigen
  E  der Plan darf nicht in die Zustandsdatei wandern und muss nach dem Laden neu greifen
  F  DETERMINISMUS: zwei getrennte Prozesse muessen bitgleiche Ergebnisse liefern -- daran
     haengt das gepaarte Seed-Verfahren des Projekts

JEDE Regel ist durch eine Sabotage abgesichert: Zerfall weglassen, Endlichkeits-Pruefung
elementweise statt je Verbindung, W-Deckel weg, V-Deckel weg, Modulation ignorieren,
pressure_scale einfrieren -- alle sechs lassen mindestens einen Fall fehlschlagen (geprueft
2026-08-23).  Ein Test, der nicht fehlschlagen kann, prueft nichts.

Aufruf:  python src/pc_cvnn/test_relax_vec.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

from pc_cvnn.connection import ConnType                      # noqa: E402
from pc_cvnn.network import PCNetwork                         # noqa: E402
from pc_cvnn.node import PCNode, SensorNode                   # noqa: E402

SCHRANKE = 1e-12
# Zustand UND Gewichte: seit Phase 4 ebenfalls gebuendelt laeuft, muessen W (Verbindungen) und
# V (zeitliches Vorwaertsmodell je Knoten) mitverglichen werden -- sonst prueft der Test die
# Lernphase gar nicht.  _prev_f_mu/_predicted_next_mu sind ihre Eingaenge und gehoeren dazu.
FELDER = ("mu", "pi", "epsilon", "V", "_prev_f_mu", "_predicted_next_mu")


def _sichern(net):
    d = {k: tuple(getattr(n, f).copy() for f in FELDER) for k, n in net._nodes.items()}
    d["__W__"] = tuple(c.W.copy() for c in net._connections)
    return d


def _laden(net, snap):
    for k, n in net._nodes.items():
        for f, v in zip(FELDER, snap[k]):
            setattr(n, f, v.copy())
    for c, W in zip(net._connections, snap["__W__"]):
        c.W = W.copy()


def _vergleich(net, snap_a, snap_b):
    """RELATIVER groesster Unterschied.  Absolut zu messen waere hier irrefuehrend: in Fall D
    wachsen die Werte bis 1e29, und 1e14 Unterschied darauf ist immer noch Maschinengenauigkeit.
    Nenner max(1,|a|,|b|), damit kleine Werte nicht kuenstlich aufgeblasen werden."""
    m = 0.0
    paare = [(snap_a[k], snap_b[k]) for k in net._nodes]
    paare.append((snap_a["__W__"], snap_b["__W__"]))
    for ta, tb in paare:
        for xa, xb in zip(ta, tb):
            if not xa.size:
                continue
            # Gleichheit ZUERST, dann erst der Abstand: nan == nan ist falsch, zwei gleiche
            # Nans sind aber dasselbe Ergebnis; und inf - inf ergibt nan, waere also ohne diese
            # Vorab-Pruefung ein scheinbarer Unterschied.
            gleich = (xa == xb) | (np.isnan(xa) & np.isnan(xb))
            with np.errstate(invalid="ignore"):
                nenner = np.maximum(1.0, np.maximum(np.abs(xa), np.abs(xb)))
                d = np.abs(xa - xb) / nenner
            d = np.where(gleich, 0.0, d)
            d = np.where(np.isnan(d), np.inf, d)          # verbleibendes nan = echter Unterschied
            m = max(m, float(np.max(d)))
    return m


def _lauf(bau, schritte, eingabe, name, klemm_spiel=False):
    """Bei JEDEM Schritt beide Relaxationen aus demselben Zustand fahren und vergleichen."""
    from pc_cvnn.relax_vec import RelaxPlan

    net, sens = bau(0)
    plan = RelaxPlan(net)                       # erzwungen, auch fuer kleine Netze
    schlimmst, schritte_ungleich = 0.0, 0

    for t in range(schritte):
        for nd, v in zip(sens, eingabe(t)):
            nd.clamp(v)
        if klemm_spiel and t == schritte // 2:
            sens[0].unclamp()

        # -- Phase 1, aus demselben Zustand ----------------------------------------------
        net._plan = None
        vor_p = _sichern(net)
        net.phase_predict()
        nach_p_obj = _sichern(net)
        _laden(net, vor_p)
        plan.predict(net)
        schlimmst = max(schlimmst, _vergleich(net, nach_p_obj, _sichern(net)))
        _laden(net, nach_p_obj)

        net.phase_error()                       # Phase 2 ist unveraendert (eps = mu - pi)

        # -- Phase 3 --------------------------------------------------------------------
        vorher = _sichern(net)
        r_obj = net.phase_relax()               # Objekt-Pfad (net._plan ist None)
        nach_obj = _sichern(net)

        _laden(net, vorher)                     # exakt derselbe Ausgangszustand
        r_vec = plan.relax(net)
        nach_vec = _sichern(net)

        if r_obj != r_vec:
            schritte_ungleich += 1
        schlimmst = max(schlimmst, _vergleich(net, nach_obj, nach_vec))

        # -- Phase 4, ebenso aus demselben Zustand ---------------------------------------
        _laden(net, nach_obj)                   # Lauf mit dem Objekt-Ergebnis fortsetzen
        vor_l = _sichern(net)
        mod = 1.0 + 0.25 * ((t % 5) - 2)        # Neuromodulator mit durchfahren, auch negativ
        net._plan = None
        net.neuromod = mod
        net.phase_learn()
        nach_l_obj = _sichern(net)

        _laden(net, vor_l)
        plan.learn(net, mod)
        schlimmst = max(schlimmst, _vergleich(net, nach_l_obj, _sichern(net)))

        _laden(net, nach_l_obj)
        net.commit_step()

    ok = schlimmst < SCHRANKE and schritte_ungleich == 0
    zus = f"max |Delta| = {schlimmst:.2e}"
    if schritte_ungleich:
        zus += f"   relax_steps ungleich in {schritte_ungleich} Schritten"
    print(f"  {name:<54} {'OK ' if ok else 'FEHLER'}  {zus}")
    return ok


# ----------------------------------------------------------------------------------------------
def fall_A():
    from pc_cvnn.pc_act18 import build_hexnet4, F

    def bau(seed):
        net, cells, _h1 = build_hexnet4(np.random.default_rng(seed))
        return net, [cells[(r, c)] for r in range(F) for c in range(F)]

    rng = np.random.default_rng(7)
    daten = [rng.random((256, 4)) for _ in range(10)]
    return _lauf(bau, 10, lambda t: daten[t], "A  Fovea-Netz (321 Knoten, 1883 Verb.)")


def fall_B():
    def bau(seed):
        rng = np.random.default_rng(seed)
        net = PCNetwork(eta_inf=0.07, n_relax=12, eps_tol=1e-12, gamma=0.4, beta=0.9,
                        eta_learn=0.01, lambda_decay=0.002, w_clip=2.5, rng=rng)
        sens = [net.add(SensorNode(f"s{i}", dim=3)) for i in range(6)]
        mid = [net.add(PCNode(f"m{i}", dim=5, activation="tanh", rng=rng)) for i in range(4)]
        net.add(PCNode("r", dim=5, activation="relu", rng=rng))      # GLEICHE dim, andere Aktivierung
        net.add(PCNode("id", dim=5, activation="identity", rng=rng))  # und noch eine
        net.add(PCNode("taub", dim=4, activation="tanh", rng=rng))    # OHNE jeden Eingang
        for i, m in enumerate(mid):
            for j in range(6):
                net.connect(m.id, f"s{j}", ConnType.UP, pressure_scale=0.2 + 0.1 * j)
            net.connect("r", m.id, ConnType.UP, pressure_scale=0.7)
            net.connect("id", m.id, ConnType.UP, pressure_scale=0.3)   # 5->5 wie oben, andere Quelle
            net.connect(f"m{(i + 1) % 4}", m.id, ConnType.LATERAL, pressure_scale=0.5)
        net.connect("r", "id", ConnType.LATERAL)
        return net, sens

    rng = np.random.default_rng(11)
    daten = [rng.random((6, 3)) for _ in range(12)]
    return _lauf(bau, 12, lambda t: daten[t], "B  gleiche Dim / andere Aktivierung, taube Knoten")


def fall_C():
    def bau(seed):
        rng = np.random.default_rng(seed)
        net = PCNetwork(eta_inf=0.05, n_relax=10, eps_tol=1e-12, rng=rng)
        sens = [net.add(SensorNode(f"s{i}", dim=4)) for i in range(8)]
        for i in range(3):
            net.add(PCNode(f"h{i}", dim=6, activation="tanh", rng=rng))
            for j in range(8):
                net.connect(f"h{i}", f"s{j}", ConnType.UP, pressure_scale=0.4)
        return net, sens

    rng = np.random.default_rng(3)
    daten = [rng.random((8, 4)) for _ in range(10)]
    return _lauf(bau, 10, lambda t: daten[t], "C  Klemmen/Loesen mitten im Lauf", klemm_spiel=True)


def fall_D():
    """Die ZEILENWEISE Nullungs-Regel wirklich ausloesen.

    Ein blosses Hochdrehen von eta_inf laesst die Werte nur bis ~1e29 wachsen, ohne je
    nicht-endlich zu werden -- die Regel bliebe ungetestet.  Deshalb wird EIN Element von EINEM
    Knoten gezielt auf inf gesetzt: beide Fassungen muessen daraufhin DIESEN GANZEN Knoten
    nullen und alle anderen unangetastet lassen.  Eine elementweise Fassung wuerde hier nur das
    eine Element nullen und sichtbar auseinanderlaufen.
    """
    # n_relax=1: die Relaxation endet unmittelbar nach der Nullung, der genullte Knoten ist am
    # Ende also noch null und nachpruefbar.  Bei mehreren Iterationen laeuft er wieder hoch und
    # die Regel waere von aussen nicht mehr zu sehen.
    from pc_cvnn.relax_vec import RelaxPlan
    rng = np.random.default_rng(5)
    net = PCNetwork(eta_inf=0.05, n_relax=1, eps_tol=1e-12, rng=rng)
    sens = [net.add(SensorNode(f"s{i}", dim=3)) for i in range(4)]
    for i in range(2):
        net.add(PCNode(f"h{i}", dim=4, activation="tanh", rng=rng))
        for j in range(4):
            net.connect(f"h{i}", f"s{j}", ConnType.UP, pressure_scale=0.5)
    plan = RelaxPlan(net)

    schlimmst, ausgeloest, lern_ausgeloest = 0.0, 0, 0
    with np.errstate(over="ignore", invalid="ignore"):
        for t in range(6):
            for nd, v in zip(sens, rng.random((4, 3))):
                nd.clamp(v)
            net._plan = None
            net.phase_predict(); net.phase_error()
            # gezielt vergiften: ein Element, ein Knoten -- abwechselnd inf und nan
            gift = np.inf if t % 2 == 0 else np.nan
            net._nodes[f"h{t % 2}"].epsilon[1] = gift
            ausgeloest += 1

            vorher = _sichern(net)
            net.phase_relax()
            nach_obj = _sichern(net)
            _laden(net, vorher)
            plan.relax(net)
            nach_vec = _sichern(net)
            schlimmst = max(schlimmst, _vergleich(net, nach_obj, nach_vec))
            # der vergiftete Knoten MUSS als Ganzes genullt sein -- sonst prueft der Fall nichts
            if np.any(nach_obj[f"h{t % 2}"][0] != 0):
                print(f"  D: Regel nicht ausgeloest bei t={t} -- Fall ist wirkungslos")
                return False

            # -- und dasselbe fuer PHASE 4 --------------------------------------------------
            # compute_error am Ende der Relaxation hat das Gift oben laengst ueberschrieben,
            # bis zum Lernen ist alles wieder endlich.  Die Endlichkeits-Regel der Lernphase
            # (GANZE dW-Matrix je Verbindung, nicht einzelne Elemente) braucht deshalb eine
            # EIGENE Vergiftung -- ohne sie bleibt sie ungeprueft.
            _laden(net, nach_obj)
            net._nodes["s0"].epsilon[0] = np.inf     # Ziel-Fehler -> dW ganzer Verbindungen
            net._nodes["h1"].mu[2] = np.nan          # Quell-Aktivierung + dV desselben Knotens
            betroffen = sum(
                1 for c in net._connections
                if not np.all(np.isfinite(np.outer(np.conjugate(c.source.activation),
                                                   c.target.epsilon))))
            if betroffen == 0:
                print(f"  D: Lern-Regel nicht ausgeloest bei t={t} -- Fall ist wirkungslos")
                return False
            lern_ausgeloest += betroffen

            vor_l = _sichern(net)
            net._plan = None
            net.neuromod = 1.0 + 0.2 * t
            net.phase_learn()
            nach_l = _sichern(net)
            _laden(net, vor_l)
            plan.learn(net, 1.0 + 0.2 * t)
            schlimmst = max(schlimmst, _vergleich(net, nach_l, _sichern(net)))

            _laden(net, nach_l)
            net.commit_step()

    ok = schlimmst < SCHRANKE
    print(f"  {'D  nicht-endliche Werte (zeilenweise Nullung)':<54} {'OK ' if ok else 'FEHLER'}  "
          f"max |Delta| = {schlimmst:.2e}   ({ausgeloest}x Zustand, {lern_ausgeloest}x Lernen)")
    return ok


def fall_G():
    """W und pressure_scale werden ZWISCHEN den Schritten von aussen veraendert.

    planner_chain.py:369-378 tut genau das je Planung: es setzt W direkt neu und diskontiert die
    Fehler ueber die Kette mit pressure_scale = gamma^k.  Eine Fassung, die diese Werte beim
    Bauen des Plans einfriert, rechnet dort still mit der VORIGEN Planung weiter -- ohne Absturz,
    ohne Warnung.  Genau dieser Fehler steckte in der ersten Fassung.
    """
    from pc_cvnn.relax_vec import RelaxPlan
    rng = np.random.default_rng(17)
    net = PCNetwork(eta_inf=0.06, n_relax=9, eps_tol=1e-12, gamma=0.5, rng=rng)
    sens = [net.add(SensorNode(f"s{i}", dim=4)) for i in range(5)]
    for i in range(3):
        net.add(PCNode(f"h{i}", dim=6, activation="tanh", rng=rng))
        for j in range(5):
            net.connect(f"h{i}", f"s{j}", ConnType.UP, pressure_scale=1.0)
    plan = RelaxPlan(net)

    schlimmst = 0.0
    for t in range(8):
        for k, c in enumerate(net._connections):           # beides je Schritt neu setzen
            c.pressure_scale = 0.5 ** (k % 4) * (1.0 + 0.3 * t)
            if t % 2 == 0:
                c.W = c.W * 0.97 + 0.01                    # REBINDING, nicht in-place
        for nd, v in zip(sens, rng.random((5, 4))):
            nd.clamp(v)
        net._plan = None
        net.phase_predict(); net.phase_error()
        vorher = _sichern(net)
        r_obj = net.phase_relax(); nach_obj = _sichern(net)
        _laden(net, vorher)
        r_vec = plan.relax(net); nach_vec = _sichern(net)
        if r_obj != r_vec:
            print(f"  G: relax_steps ungleich bei t={t} ({r_obj} != {r_vec})")
            return False
        schlimmst = max(schlimmst, _vergleich(net, nach_obj, nach_vec))
        _laden(net, nach_obj)
        net.phase_learn(); net.commit_step()

    ok = schlimmst < SCHRANKE
    print(f"  {'G  W / pressure_scale von aussen veraendert':<54} {'OK ' if ok else 'FEHLER'}  "
          f"max |Delta| = {schlimmst:.2e}")
    return ok


def fall_H():
    """Der BETRAGS-DECKEL muss wirklich greifen.

    In den Faellen A-G bleiben die Gewichte unter ihrem Deckel, `_clip_mag` laeuft also nie --
    eine Fassung ganz OHNE Deckelung besteht sie alle (nachgeprueft).  Hier wird der Deckel
    gezielt niedrig und die Lernrate hoch gesetzt, so dass W und V ihn in jedem Schritt
    ueberschreiten; zusaetzlich wird gezaehlt, wie viele Elemente tatsaechlich gekappt wurden --
    ein Fall, der nichts ausloest, prueft nichts.
    """
    from pc_cvnn.relax_vec import RelaxPlan
    rng = np.random.default_rng(23)
    net = PCNetwork(eta_inf=0.05, n_relax=6, eps_tol=1e-12, eta_learn=0.9, eta_temporal=0.9,
                    lambda_decay=0.0, w_clip=0.05, rng=rng)      # Deckel absichtlich winzig
    sens = [net.add(SensorNode(f"s{i}", dim=4)) for i in range(5)]
    for i in range(3):
        net.add(PCNode(f"h{i}", dim=5, activation="tanh", rng=rng))
        for j in range(5):
            net.connect(f"h{i}", f"s{j}", ConnType.UP, pressure_scale=0.6)
    plan = RelaxPlan(net)

    schlimmst, gekappt = 0.0, 0
    for t in range(8):
        for nd, v in zip(sens, rng.random((5, 4)) * 4.0):
            nd.clamp(v)
        net._plan = None
        net.phase_predict(); net.phase_error(); net.phase_relax()

        gekappt += sum(int(np.sum(np.abs(c.W) > net.w_clip)) for c in net._connections)
        gekappt += sum(int(np.sum(np.abs(n.V) > n.w_clip_V))
                       for n in net._nodes.values() if not n.is_clamped)

        vor_l = _sichern(net)
        net.neuromod = 1.0
        net.phase_learn()
        nach_l = _sichern(net)
        _laden(net, vor_l)
        plan.learn(net, 1.0)
        schlimmst = max(schlimmst, _vergleich(net, nach_l, _sichern(net)))
        _laden(net, nach_l)
        net.commit_step()

    ok = schlimmst < SCHRANKE and gekappt > 0
    print(f"  {'H  Betrags-Deckel greift (W und V)':<54} {'OK ' if ok else 'FEHLER'}  "
          f"max |Delta| = {schlimmst:.2e}   ({gekappt} Elemente ueber dem Deckel)")
    return ok


def fall_E():
    """Der Plan darf NICHT in die Zustandsdatei wandern und muss danach neu greifen."""
    import pickle
    from pc_cvnn.pc_act18 import build_hexnet4, F
    net, cells, _ = build_hexnet4(np.random.default_rng(0))
    for r in range(F):
        for c in range(F):
            cells[(r, c)].clamp(np.zeros(4))
    net.step(learn=True); net.commit_step()
    roh = pickle.dumps(net)
    net2 = pickle.loads(roh)
    net2.step(learn=True); net2.commit_step()
    ok = b"RelaxPlan" not in roh and net2._relax_plan() is not None
    print(f"  {'E  Pickle ohne Plan, danach wieder gebuendelt':<54} {'OK ' if ok else 'FEHLER'}  "
          f"Plan im Pickle: {b'RelaxPlan' in roh}, nach Laden aktiv: {net2._relax_plan() is not None}")
    return ok


def fall_F():
    """DETERMINISMUS ueber Prozessgrenzen -- daran haengt das gepaarte Seed-Verfahren."""
    import subprocess
    code = (
        "import os,sys;sys.path.insert(0,'src');os.environ['ACT14_DOF']='4';"
        "import numpy as np;from pc_cvnn.pc_act18 import build_hexnet4,F;"
        "net,cells,_=build_hexnet4(np.random.default_rng(0));"
        "rng=np.random.default_rng(7);"
        "h=[]\n"
        "for t in range(8):\n"
        "    x=rng.random((256,4));i=0\n"
        "    for r in range(F):\n"
        "        for c in range(F):\n"
        "            cells[(r,c)].clamp(x[i]);i+=1\n"
        "    d=net.step(learn=True);net.commit_step();h.append(d['total_error'])\n"
        "print(repr([float(v) for v in h]))"
    )
    outs = []
    for _ in range(2):
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        outs.append(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:])
    ok = outs[0] == outs[1] and outs[0].startswith("[")
    print(f"  {'F  zwei Prozesse, bitgleiches Ergebnis':<54} {'OK ' if ok else 'FEHLER'}  "
          f"{'identisch' if ok else outs[0][:120]}")
    return ok


if __name__ == "__main__":
    print("\n  GEBUENDELTE gegen OBJEKT-Relaxation -- je Schritt aus DEMSELBEN Zustand\n")
    ergebnisse = [fall_A(), fall_B(), fall_C(), fall_D(), fall_G(), fall_H(), fall_E(), fall_F()]
    print()
    if all(ergebnisse):
        print(f"  alle {len(ergebnisse)} Faelle bestanden (Schranke {SCHRANKE:g})\n")
    else:
        print(f"  {ergebnisse.count(False)} von {len(ergebnisse)} FEHLGESCHLAGEN\n")
        sys.exit(1)
