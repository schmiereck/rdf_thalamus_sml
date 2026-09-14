"""WIEDERVORLAGE: eine Wahrnehmungsaenderung auf den ECHTEN Szenen des Laufs pruefen -- ohne Lauf.

WARUM ES DAS GIBT (wiki/befunde/geburtenrate-chroma-phantome.md).  Sieben A/B-Laeufe
nacheinander blieben uneindeutig, weil die gemessenen Wirkungen unter der Nachweisgrenze eines
150- bis 300-Episoden-Laufs liegen (wiki/befunde/rechnerlast.md).  Handgebaute Sonden waren keine
Loesung: eine mit fuenf eng gestellten Koerpern ueberzeichnete die Verschmelzung um Faktor 15.

Die Szenen des Laufs liegen aber vor.  `pc_act23` schreibt je Episode eine Zeile

    [dbg] after ep : {'obj_red': [-0.082, 0.089], 'obj_green': [0.508, -0.599], ...}

nach `log/pc_act23_*.txt`.  Damit laesst sich jede Szene nachstellen und mit BEKANNTER WAHRHEIT
befragen -- auf der tatsaechlichen Lagenverteilung, beliebig viele Einstellungen auf DENSELBEN
Szenen, und ohne dass ein Lauf gefahren werden muss.

WAS GEMESSEN WIRD, und zwar beides zugleich -- das war der Fehler, der die Chroma-Linie zwei
Anlaeufe gekostet hat:

    VERFEHLT     kein Detektion naeher als 20 mm am Koerper      -> kostet privilegierten Rueckfall
    ZERTEILT     mehr als eine Detektion auf demselben Koerper    -> gebiert eine Phantomklasse
    NEU          Detektionen, die resolve() als novel meldet      -> das Rohmaterial der Geburt
                 aufgeteilt in "auf einem Koerper" / "Bruchstueck" / "bei keinem Koerper"

Der MITTELWERT der Detektionen je Koerper steht bewusst da, nicht der Median: eine Zerteilung, die
nur jede vierte Szene trifft, ist im Median unsichtbar (gemessen 4,0 bei 4,49 Mittel).

AUFRUF

    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_wiedervorlage.py

KNOEPFE
    WV_LOGS        Glob auf die Protokolle (Vorgabe: log/pc_act23_*.txt)
    WV_N           Szenen (Vorgabe 200, zufaellig gezogen)
    WV_STATE       Zustandsdatei -- IMMER eine Kopie angeben, nie die Live-Datei
    WV_SEED        Zufallsstrom fuer Auswahl und Drehung (Vorgabe 7)
    WV_VARIANTEN   was verglichen wird, "|"-getrennt, je "Name:VAR=WERT,VAR=WERT".
                   Die ERSTE ist der Bezug.  Vorgabe:
                     "Vorgabe:|Chroma:ACT_SHAPE_CHROMA_SPLIT=1"

BEISPIEL -- die Schranke des Chroma-Schnitts durchfahren:
    WV_VARIANTEN="aus:|t1.0:ACT_SHAPE_CHROMA_SPLIT=1,ACT_SHAPE_CHROMA_TRENNUNG=1.0|t2.2:ACT_SHAPE_CHROMA_SPLIT=1,ACT_SHAPE_CHROMA_TRENNUNG=2.2"

GRENZEN, die beim Lesen zu beachten sind:
  * Der YAW steht nicht im Protokoll und wird neu gewuerfelt.  Verschmelzung haengt ueberwiegend
    an den Lagen, aber nicht nur -- dieselbe Szene kann je nach Drehung verschmelzen oder nicht.
  * Die Protokollzeile faellt am EPISODENENDE.  Bei Episodenbeginn garantiert der Szenengenerator
    80 mm Mindestabstand (pc_act16.scatter), dort verfehlt auch die feste Segmentierung nichts.
    Wer den Nutzen einer Verschmelzungs-Reparatur sucht, findet ihn nur hier.
  * `resolve()` laeuft gegen den Exemplarbestand des GELADENEN Zustands.  Aendert eine Variante
    den Deskriptor, ist die Neuheitszahl relativ zu diesem Bestand zu lesen, nicht absolut.
  * DER GLOB IST WICHTIG.  `log/pc_act23_*.txt` trifft alle Protokolle seit Projektbeginn -- mit
    anderen Koerpersaetzen, anderer Greifergeometrie, anderer Szenengroesse.  Der Vergleich
    ZWISCHEN Varianten bleibt gueltig (alle sehen dieselben Szenen), aber die absoluten Zahlen
    vermischen Projektphasen.  Fuer eine Aussage ueber den heutigen Stand den Glob auf EINEN Lauf
    einengen, z.B. WV_LOGS="log/pc_act23_2026-09-14_07-22-23_*.txt".
  * Es wird NICHTS gespeichert; der Zustand wird nur gelesen.  WV_STATE trotzdem auf eine KOPIE
    zeigen lassen -- die Invariante "nie auf der Live-Pkl" gilt ohne Ausnahme.
"""
import glob
import math
import os
import pickle
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

LOGS = os.environ.get("WV_LOGS", "log/pc_act23_*.txt")
N = int(os.environ.get("WV_N", "200"))
STATE = os.environ.get("WV_STATE", "src/pc_cvnn/state/act23_state.pkl")
SEED = int(os.environ.get("WV_SEED", "7"))
VARIANTEN = os.environ.get("WV_VARIANTEN", "Vorgabe:|Chroma:ACT_SHAPE_CHROMA_SPLIT=1")
PARKED_X = 0.4                        # Koerper jenseits davon sind geparkt, nicht im Bild
NAH = 0.02                            # "am Koerper" in Metern
GANZ = 0.6                            # Flaechenanteil, ab dem eine Detektion den Koerper BEDECKT

RE_SZENE = re.compile(r"\[dbg\] after ep : \{(.*)\}")
RE_PAAR = re.compile(r"'(\w+)': \[([-\d.]+), ([-\d.]+)\]")


def szenen_lesen(muster, n, rng):
    """Alle `after ep`-Zeilen der passenden Protokolle einlesen und n davon ziehen."""
    aus = []
    dateien = sorted(glob.glob(muster))
    for f in dateien:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = RE_SZENE.search(ln)
                if m:
                    aus.append({k: (float(a), float(b))
                                for k, a, b in RE_PAAR.findall(m.group(1))})
    rng.shuffle(aus)
    return dateien, aus[:n]


def fisher(a, b, c, d):
    """Zweiseitiger exakter Test auf der 2x2-Tafel (wie ueberall sonst im Projekt)."""
    lf = math.lgamma

    def p(a, b, c, d):
        return math.exp(lf(a + b + 1) + lf(c + d + 1) + lf(a + c + 1) + lf(b + d + 1)
                        - lf(a + 1) - lf(b + 1) - lf(c + 1) - lf(d + 1) - lf(a + b + c + d + 1))
    p0 = p(a, b, c, d)
    tot = 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k, l = a + b - i, a + c - i, d - (a - i)
        if j < 0 or k < 0 or l < 0:
            continue
        q = p(i, j, k, l)
        if q <= p0 * (1 + 1e-9):
            tot += q
    return min(1.0, tot)


def lade_klassifikator(zuweisungen):
    """Schalter setzen, shape_classifier NEU laden, Klassifikator aus dem Zustand holen.

    Die Schalter sind Modulkonstanten und werden beim Import gelesen -- ohne Neuladen wuerde die
    zweite Variante die Einstellung der ersten benutzen.  Dasselbe Verfahren wie in
    act23_relrings_ab.py."""
    for k, v in zuweisungen.items():
        os.environ[k] = v
    for m in [k for k in list(sys.modules) if "shape_classifier" in k]:
        del sys.modules[m]
    from pc_cvnn.arm_modules import shape_classifier as sc_mod   # noqa: F401  (Neuladen erzwingen)
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    return st["shape_clf"]


def eine_variante(sim, sc, szenen, rng):
    """Eine Einstellung auf allen Szenen befragen.  Gibt die Zaehlungen zurueck."""
    # Bezugsflaeche je Koerper: allein hingestellt, MIT dieser Einstellung gemessen.
    # Konservativ: wird ein allein stehender Koerper selbst zerteilt, faellt der Bezug kleiner
    # aus und Bruchstuecke werden als "ganz" gezaehlt -- die Bruchstueckzahl ist eher zu niedrig.
    alle = sorted({o for s in szenen for o in s})
    solo = {}
    for b in alle:
        for o in alle:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object(b, [0.0, 0.16], z=0.012)
        mujoco.mj_forward(sim.m, sim.d)
        sv = sim.d.mocap_pos.copy()
        ds = sc.perceive_all(sim)
        sim.d.mocap_pos[:] = sv
        mujoco.mj_forward(sim.m, sim.d)
        solo[b] = max((float(d.get("area", 0.0)) for d in ds), default=0.0)

    z = dict(koerper=0, verfehlt=0, zerteilt=0, neu=0, neu_ganz=0, neu_bruch=0, neu_nirgends=0)
    lok, je_koerper = [], []
    for sz in szenen:
        for o, (x, y) in sz.items():
            sim.set_object(o, [x, y], z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
        mujoco.mj_forward(sim.m, sim.d)
        auf = [o for o, (x, y) in sz.items() if x < PARKED_X]
        sv = sim.d.mocap_pos.copy()
        dets = [d for d in sc.perceive_all(sim) if d.get("pos") is not None]
        sim.d.mocap_pos[:] = sv
        mujoco.mj_forward(sim.m, sim.d)
        if not dets or not auf:
            continue
        je_koerper.append(len(dets) / len(auf))
        # jede Detektion ihrem naechsten Koerper zuordnen -- einmal, nicht je Koerper neu
        zuord = []
        for d in dets:
            w = np.asarray(d["pos"], float)
            nah = min(auf, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - w)))
            zuord.append((nah, float(np.linalg.norm(sim.obj_pos(nah)[:2] - w)), d))
        for o in auf:
            w = np.asarray(sim.obj_pos(o)[:2], float)
            e = min(float(np.linalg.norm(np.asarray(d["pos"], float) - w)) for d in dets)
            z["koerper"] += 1
            lok.append(1000.0 * e)
            z["verfehlt"] += (e > NAH)
            z["zerteilt"] += (sum(1 for b, dist, _ in zuord if b == o and dist < NAH) > 1)
        for b, dist, d in zuord:
            if d.get("shape") is not None:
                continue
            z["neu"] += 1
            if dist >= NAH:
                z["neu_nirgends"] += 1
            elif float(d.get("area", 0.0)) / max(1.0, solo.get(b, 1.0)) < GANZ:
                z["neu_bruch"] += 1
            else:
                z["neu_ganz"] += 1
    z["lok_median"] = float(np.median(lok)) if lok else float("nan")
    z["lok_p90"] = float(np.percentile(lok, 90)) if lok else float("nan")
    z["det_je_koerper"] = float(np.mean(je_koerper)) if je_koerper else float("nan")
    return z


def main():
    rng = np.random.default_rng(SEED)
    dateien, szenen = szenen_lesen(LOGS, N, rng)
    if not szenen:
        print(f"Keine 'after ep'-Zeilen in {LOGS} gefunden.")
        print("Laeuft act23 mit ACT23_DEBUG=1?  Ohne das schreibt es die Szenen nicht.")
        return
    print(f"Protokolle: {len(dateien)} Datei(en) aus {LOGS}")
    print(f"Szenen: {len(szenen)} gezogen, Seed {SEED}, Zustand {STATE}")
    print("Die Lagen stammen vom EPISODENENDE; der Yaw steht nicht im Protokoll und wird "
          "neu gewuerfelt.\n")

    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")

    erg = []
    for teil in VARIANTEN.split("|"):
        name, _, rest = teil.partition(":")
        zuw = dict(kv.split("=", 1) for kv in rest.split(",") if "=" in kv)
        sc = lade_klassifikator(zuw)
        z = eine_variante(sim, sc, szenen, np.random.default_rng(SEED + 1))
        erg.append((name.strip() or "?", zuw, z))
        print(f"  {name.strip() or '?':12s} gemessen" + (f"   ({rest})" if rest else ""))

    n = erg[0][2]["koerper"]
    print(f"\n{'Variante':12s} {'verfehlt':>14s} {'zerteilt':>14s} {'Lok-Med':>8s} {'p90':>7s} "
          f"{'Det/Koerper':>12s}")
    for name, _z, z in erg:
        print(f"{name:12s} {z['verfehlt']:5d} = {100*z['verfehlt']/max(1,z['koerper']):5.1f} % "
              f"{z['zerteilt']:5d} = {100*z['zerteilt']/max(1,z['koerper']):5.1f} % "
              f"{z['lok_median']:7.2f} {z['lok_p90']:7.2f} {z['det_je_koerper']:12.2f}")

    print(f"\n{'Variante':12s} {'neu gesamt':>11s} {'auf Koerper':>12s} {'Bruchstueck':>12s} "
          f"{'nirgends':>9s}")
    for name, _z, z in erg:
        print(f"{name:12s} {z['neu']:11d} {z['neu_ganz']:12d} {z['neu_bruch']:12d} "
              f"{z['neu_nirgends']:9d}")

    if len(erg) > 1:
        b = erg[0][2]
        print(f"\ngegen '{erg[0][0]}' (Fisher, {n} Koerper):")
        for name, _z, z in erg[1:]:
            pv = fisher(z["verfehlt"], z["koerper"] - z["verfehlt"],
                        b["verfehlt"], b["koerper"] - b["verfehlt"])
            pz = fisher(z["zerteilt"], z["koerper"] - z["zerteilt"],
                        b["zerteilt"], b["koerper"] - b["zerteilt"])
            print(f"  {name:12s} verfehlt p = {pv:.4f}   zerteilt p = {pz:.4f}")
        print("\nBeide Spalten zusammen lesen: ein Gewinn bei 'verfehlt', der 'zerteilt' "
              "mitzieht,\nist keiner -- ein verfehlter Koerper kostet einen privilegierten "
              "Rueckfall,\nein zerteilter gebiert eine Phantomklasse.")


if __name__ == "__main__":
    main()
