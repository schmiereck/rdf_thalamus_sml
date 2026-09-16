"""ADRESS-WIEDERVORLAGE: die ADRESSIERUNG auf den echten Szenen des Laufs pruefen, ohne Lauf.

ABGRENZUNG, und sie ist der Grund fuer eine zweite Datei.  `act23_wiedervorlage.py` misst die
WAHRNEHMUNG (verfehlte und zerteilte Koerper) und laedt dafuer `shape_classifier` neu.  Schalter
wie ACT23_GROESSE_SPANNE oder ACT23_EIG_IDENT sitzen aber in `pc_act23` und beruehren
`perceive_all` ueberhaupt nicht -- sie aendern, wie aus einer Detektion eine ADRESSE wird.  Die
Wahrnehmungs-Wiedervorlage kann sie darum per Konstruktion nicht sehen; sie wuerde fuer alle
Einstellungen dieselben Zahlen liefern.

Hier wird deshalb eine Ebene hoeher gemessen, mit derselben Methode: Szenen aus `log/` nachstellen,
Wahrheit bekannt, alle Einstellungen auf DENSELBEN Szenen.

WAS GEMESSEN WIRD -- die Zielgroesse des siebten Anlaufs
(wiki/befunde/groessenachse-spanne.md):

    Fuer jeden Koerper wird die Adresse gebildet, die die Wuerfelei bilden wuerde
    (_auto_eig_umschreiben), und dann aufgeloest:

      GROB       die aufgeloeste Lage liegt > 20 mm vom gemeinten Koerper   -> falsches Objekt
      RUECKFALL  das Tripel trifft gar nichts                               -> privilegierter Pfad
      ACHSEN     wie viele der drei Achsen genannt werden mussten
      KEINE      es gibt keine verfolgbare Achse (Farbe/Form fehlen)        -> gar keine Adresse

ACHTUNG, EIGENE NACHBILDUNG: die Wuerfelei ist eine Closure in `run_combined` und nicht
importierbar.  `adresse_bilden` unten bildet sie Zeile fuer Zeile nach (Stand 2026-09-14,
pc_act23.py:1781-1854).  Aendert sich dort etwas, aendert sich hier nichts mit -- das ist die
Schwaeche dieses Werkzeugs und der Preis dafuer, dass es ohne Lauf auskommt.  Was NICHT
nachgebildet ist: die Neugier-Auswahl (welcher Koerper geuebt wird; hier werden ALLE genommen)
und die Farb-Mischung je Episode (hier gilt die Faerbung des geladenen Zustands).

AUFRUF
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_adress_wiedervorlage.py

KNOEPFE
    AW_LOGS        Glob auf die Protokolle (Vorgabe log/pc_act23_*.txt) -- auf EINEN Lauf einengen
    AW_N           Szenen (Vorgabe 150)
    AW_STATE       Zustandsdatei -- immer eine KOPIE
    AW_SEED        Zufallsstrom (Vorgabe 7)
    AW_ZIEHUNGEN   Achsen-Wuerfe je Koerper (Vorgabe 4) -- die Wuerfelei waehlt zufaellig, welche
                   Achsen genannt werden; mehrere Wuerfe mitteln das heraus
    AW_VARIANTEN   "Name:VAR=WERT,...|Name:..." -- die erste ist der Bezug.  Vorgabe:
                     "Vorgabe:|Spanne:ACT23_GROESSE_SPANNE=1|Ident:ACT23_EIG_IDENT=1|beide:ACT23_GROESSE_SPANNE=1,ACT23_EIG_IDENT=1"

GRENZEN wie bei der Wahrnehmungs-Wiedervorlage: der Yaw steht nicht im Protokoll und wird neu
gewuerfelt, die Zeile faellt am Episodenende, der Vorgabe-Glob vermischt Projektphasen.
Es wird NICHTS gespeichert.
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

LOGS = os.environ.get("AW_LOGS", "log/pc_act23_*.txt")
N = int(os.environ.get("AW_N", "150"))
STATE = os.environ.get("AW_STATE", "src/pc_cvnn/state/act23_state.pkl")
SEED = int(os.environ.get("AW_SEED", "7"))
ZIEHUNGEN = int(os.environ.get("AW_ZIEHUNGEN", "4"))
# VERSATZ 0 = Adresse in derselben stehenden Szene bilden UND aufloesen (bester Fall).
# 1 = auf Szene i bilden, auf Szene i+1 aufloesen -- der Fall des Laufs, wo das Tripel in
# state.EIGENSCHAFT steht und aufgeloest wird, nachdem sich die Szene bewegt hat.
VERSATZ = int(os.environ.get("AW_VERSATZ", "0"))
VARIANTEN = os.environ.get(
    "AW_VARIANTEN",
    "diskret:|stetig:STETIG=1")
PARKED_X = 0.4
# STETIGE ADRESSIERUNG (wiki/fragen/stetige-adressierung.md).  Statt drei Klassen-NAMEN traegt die
# Adresse dann drei MESSWERTE, und eine Detektion passt, wenn sie in allen genannten Achsen
# innerhalb der Toleranz liegt.  Alles andere -- Achsen-Wuerfelei, Nachlegen bis eindeutig,
# Identitaetspruefung, Aufloesung auf der Zielszene -- bleibt Zeile fuer Zeile gleich, damit der
# Vergleich die MATCHING-Regel misst und nicht die Strategie.
# Die Toleranzen sind probe-lokal und koennen in AW_VARIANTEN gesetzt werden (STETIG, EMB_TOL,
# SPAN_TOL); sie gehen NICHT als Umgebungsvariable an pc_act23, das kennt sie nicht.
LOKAL = {"STETIG": 0.0,       # 1 = stetig adressieren
         "EMB_TOL": 0.5,      # Formtoleranz als ANTEIL des Median-Abstands zweier VERSCHIEDENER
         #                      Koerper im Einbettungsraum -- relativ, damit keine nackte Zahl
         #                      festgeschrieben wird (der Bezug wird je Lauf gemessen)
         "SPAN_TOL": 0.005}   # Groessentoleranz in METERN (+/-)
GROB = 0.02                           # "grober Adressierungsfehler" in Metern -- wie im siebten Anlauf

RE_SZENE = re.compile(r"\[dbg\] after ep : \{(.*)\}")
RE_PAAR = re.compile(r"'(\w+)': \[([-\d.]+), ([-\d.]+)\]")


def szenen_lesen(muster, n, rng):
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


def lade_modul(zuweisungen):
    """Schalter setzen und pc_act23 NEU laden.  Die Schalter sind Modulkonstanten; ohne Neuladen
    wuerde die zweite Variante die Einstellung der ersten benutzen."""
    for k, v in zuweisungen.items():
        if k in LOKAL:
            LOKAL[k] = float(v)          # probe-lokal, gehoert nicht in die Umgebung
            continue
        os.environ[k] = v
    import importlib
    for m in [k for k in list(sys.modules) if "pc_act23" in k or "shape_classifier" in k]:
        del sys.modules[m]
    # NICHT `from pc_cvnn import pc_act23`: das liefert das ATTRIBUT des Paketobjekts zurueck --
    # also die ALTE Modulinstanz, auch wenn sys.modules geleert wurde.  Gemessen daran gescheitert:
    # alle vier Varianten lieferten zifferngenau dasselbe.  import_module sucht ueber den NAMEN.
    if hasattr(sys.modules.get("pc_cvnn"), "pc_act23"):
        delattr(sys.modules["pc_cvnn"], "pc_act23")
    mod = importlib.import_module("pc_cvnn.pc_act23")
    for k, v in zuweisungen.items():                 # Gegenprobe: ist der Schalter angekommen?
        if k in LOKAL:
            continue
        erwartet = {"ACT23_GROESSE_SPANNE": lambda: mod.GROESSE_SPANNE,
                    "ACT23_EIG_IDENT": lambda: mod.EIG_IDENT}.get(k)
        if erwartet is not None and bool(erwartet()) != (v == "1"):
            raise SystemExit(f"Schalter {k}={v} ist nicht angekommen -- Neuladen fehlgeschlagen.")
    return mod


def _passt(d, tri):
    """Passt eine Detektion auf die Adresse?  Eine Achse mit None ist "beliebig".

    DISKRET  Gleichheit der Namen -- so arbeitet finde_nach_eigenschaften heute.
    STETIG   Abstand unter Toleranz.  Die Farbschwelle ist NICHT geraten, sondern die schon
             kalibrierte des Farb-Offenmengen-Moduls (colour_openset.TH) -- dieselbe Zahl, die
             entscheidet, ob zwei Chromatizitaeten dieselbe Klasse waeren.  Die Formtoleranz ist
             RELATIV zum gemessenen Abstand zweier verschiedener Koerper (s. LOKAL), die
             Groessentoleranz in Millimetern."""
    if not LOKAL["STETIG"]:
        return ((tri[0] is None or d["_f"] == tri[0])
                and (tri[1] is None or str(d.get("shape")) == str(tri[1]))
                and (tri[2] is None or d["_g"] == tri[2]))
    if tri[0] is not None:
        if d.get("chroma") is None:
            return False
        if float(np.linalg.norm(np.asarray(d["chroma"], float) - tri[0])) > _TOL["chroma"]:
            return False
    if tri[1] is not None:
        if d.get("_e") is None:
            return False
        if float(np.linalg.norm(d["_e"] - tri[1])) > _TOL["emb"]:
            return False
    if tri[2] is not None:
        if d.get("span") is None:
            return False
        if abs(float(d["span"]) - tri[2]) > LOKAL["SPAN_TOL"]:
            return False
    return True


_TOL = {"chroma": 0.0, "emb": 0.0}      # je Variante gesetzt, s. eine_variante


def adresse_bilden(mod, sim, sc, colours, dets, body, rng, dets_ziel=None,
                   quell_lage=None):
    """Nachbildung von _auto_eig_umschreiben (pc_act23.py:1781-1854, Stand 2026-09-14).

    Gibt (tripel, pos, treffer, achsen) zurueck, oder (None, ...) wenn gar nicht umgeschrieben
    wuerde -- dann bliebe das Kommando beim Namen."""
    # Die Lage des Koerpers in der QUELL-Szene -- das Tripel wird dort gebildet.  Bei Versatz
    # steht der Simulator schon in der ZIEL-Szene; die Quelle kommt deshalb aus den Detektionen.
    p = (np.asarray(sim.obj_pos(body)[:2], float) if dets_ziel is None
         else np.asarray(quell_lage, float))
    nah = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - p)),
              default=None)
    if nah is None or float(np.linalg.norm(np.asarray(nah["pos"], float) - p)) >= 0.04:
        return None, None, [], 0                     # nichts Sichtbares auf dem Koerper
    if LOKAL["STETIG"]:
        # DIE ADRESSE IST DAS GEMESSENE, nicht sein Etikett: Chromatizitaet, Formeinbettung,
        # Ausdehnung.  Farbe und Form bleiben die "verfolgbaren" Achsen wie in der Wuerfelei.
        f = np.asarray(nah["chroma"], float) if nah.get("chroma") is not None else None
        fo = nah.get("_e")
        g = None if nah.get("span") is None else float(nah["span"])
    else:
        f = colours.classify(nah["chroma"])[0] if nah.get("chroma") is not None else None
        fo = nah.get("shape")
        g = mod.groessen_band(nah.get("dicke"), nah.get("span"))
    werte = (f, fo, g)
    verfolgbar = [i for i in (0, 1) if werte[i] is not None]
    if not verfolgbar:
        return None, None, [], 0                     # keine verfolgbare Achse -> keine Adresse
    mk = [bool(rng.integers(2)) for _ in range(3)]
    if not any(mk[i] for i in verfolgbar):
        mk[verfolgbar[int(rng.integers(len(verfolgbar)))]] = True
    tri, pos2, tr2 = None, None, []
    for _versuch in range(4):
        tri = tuple(w if m else None for w, m in zip(werte, mk))
        # AUFLOESUNG auf den ZWISCHENGESPEICHERTEN Detektionen statt ueber
        # finde_nach_eigenschaften -- das rendert je Aufruf neu, und bei vier Achsen-Versuchen mal
        # vier Wuerfen mal vier Koerpern waeren das ueber 60 Rendervorgaenge JE SZENE.  Die
        # Filterregel ist dieselbe: Achse None = beliebig, sonst Gleichheit, und von den Treffern
        # der flaechengroesste (pc_act23.finde_nach_eigenschaften).
        tr2 = [d for d in dets            # BILDUNG immer auf der QUELL-Szene -- die Wuerfelei
               if _passt(d, tri)]                         # sieht die Zukunft nicht
        pos2 = (np.asarray(max(tr2, key=lambda d: float(d.get("area", 0.0)))["pos"], float)
                if tr2 else None)
        trifft = True
        if mod.EIG_IDENT and pos2 is not None:
            trifft = float(np.linalg.norm(np.asarray(pos2, float) - p)) < 0.02
        if len(tr2) <= 1 and trifft:
            break
        fehlt = [i for i in range(3) if not mk[i] and werte[i] is not None]
        if not fehlt:
            break
        mk[fehlt[int(rng.integers(len(fehlt)))]] = True
    if dets_ziel is not None:
        # ERST JETZT die Zielszene: dort wird die fertige Adresse aufgeloest.  Alles davor lief auf
        # der Quell-Szene -- auch die Identitaetspruefung, die sonst die Zukunft kennen wuerde.
        tr2 = [d for d in dets_ziel if _passt(d, tri)]
        pos2 = (np.asarray(max(tr2, key=lambda d: float(d.get("area", 0.0)))["pos"], float)
                if tr2 else None)
    return tri, pos2, tr2, sum(1 for t in tri if t is not None)


def bezugsmass(sim, sc, koerper):
    """Median-Abstand der Formeinbettungen ZWEIER VERSCHIEDENER Koerper.

    Ohne ihn waere eine Formtoleranz eine nackte Zahl.  Mit ihm heisst "EMB_TOL 0,5": halb so weit
    wie zwei verschiedene Koerper typischerweise auseinanderliegen.  Gemessen je Lauf, weil der
    Deskriptor sich mit dem Lernen verschiebt."""
    solo = {}
    for b in koerper:
        for o in koerper:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object(b, [0.0, 0.16], z=0.012, yaw=0.0)
        mujoco.mj_forward(sim.m, sim.d)
        sv = sim.d.mocap_pos.copy()
        ds = [d for d in sc.perceive_all(sim) if d.get("desc") is not None]
        sim.d.mocap_pos[:] = sv
        mujoco.mj_forward(sim.m, sim.d)
        if ds:
            solo[b] = np.asarray(sc.desc_embed(
                max(ds, key=lambda x: float(x.get("area", 0)))["desc"]), float)
    n = sorted(solo)
    paare = [float(np.linalg.norm(solo[a] - solo[b]))
             for i, a in enumerate(n) for b in n[i + 1:]]
    return float(np.median(paare)) if paare else 1.0


def eine_variante(mod, sim, szenen, seed):
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc, colours = st["shape_clf"], st["colours"]
    if LOKAL["STETIG"]:
        from pc_cvnn.arm_modules.colour_openset import TH as _CTH
        _trenn = bezugsmass(sim, sc, sorted({o for s in szenen for o in s}))
        _TOL["chroma"] = float(_CTH)
        _TOL["emb"] = float(LOKAL["EMB_TOL"]) * _trenn
        print(f"      stetig: Chroma-Toleranz {_TOL['chroma']:.4f} (colour_openset.TH), "
              f"Form-Toleranz {_TOL['emb']:.3f} = {LOKAL['EMB_TOL']:.2f} x {_trenn:.3f}, "
              f"Groesse +/-{1000*LOKAL['SPAN_TOL']:.0f} mm", flush=True)
    rng = np.random.default_rng(seed)
    z = dict(adressen=0, grob=0, rueckfall=0, keine=0, achsen=0, eindeutig=0)
    fehler = []
    # ALLE Szenen einmal wahrnehmen.  Erst dann laesst sich eine Adresse auf Szene i bilden und auf
    # Szene i+VERSATZ aufloesen -- der Fall, den der Lauf tatsaechlich hat: das Tripel steht in
    # state.EIGENSCHAFT und wird aufgeloest, NACHDEM sich die Szene bewegt hat.
    stand = []
    for sz in szenen:
        for o, (x, y) in sz.items():
            sim.set_object(o, [x, y], z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
        mujoco.mj_forward(sim.m, sim.d)
        auf = [o for o, (x, y) in sz.items() if x < PARKED_X]
        sv = sim.d.mocap_pos.copy()
        dets = [d for d in sc.perceive_all(sim)
                if d.get("pos") is not None and float(d.get("area", 0)) >= 200.0]
        sim.d.mocap_pos[:] = sv
        mujoco.mj_forward(sim.m, sim.d)
        for d in dets:                      # Farbklasse, Band und Einbettung EINMAL je Detektion
            d["_f"] = (colours.classify(d["chroma"])[0]
                       if d.get("chroma") is not None else None)
            d["_g"] = mod.groessen_band(d.get("dicke"), d.get("span"))
            d["_e"] = (np.asarray(sc.desc_embed(d["desc"]), float)
                       if d.get("desc") is not None else None)
        stand.append((sz, auf, dets))
    for i, (sz, auf, dets) in enumerate(stand):
        j = i + VERSATZ
        if not dets or j >= len(stand):
            continue
        sz_ziel, _auf_ziel, dets_ziel = stand[j]
        if not dets_ziel:
            continue
        for o, (x, y) in sz_ziel.items():   # die ZIEL-Szene stellen: dort wird aufgeloest
            sim.set_object(o, [x, y], z=0.012)
        mujoco.mj_forward(sim.m, sim.d)
        for body in auf:
            if body not in sz_ziel or sz_ziel[body][0] >= PARKED_X:
                continue                     # in der Zielszene gar nicht auf dem Tisch
            for _ in range(ZIEHUNGEN):
                tri, pos2, tr2, na = adresse_bilden(mod, sim, sc, colours, dets, body, rng,
                                                    dets_ziel=dets_ziel if VERSATZ else None,
                                                    quell_lage=sz[body])
                if tri is None:
                    z["keine"] += 1
                    continue
                z["adressen"] += 1
                z["achsen"] += na
                z["eindeutig"] += (len(tr2) == 1)
                if pos2 is None:
                    z["rueckfall"] += 1
                    continue
                e = float(np.linalg.norm(np.asarray(pos2, float)
                                         - np.asarray(sim.obj_pos(body)[:2], float)))
                if e > GROB:
                    z["grob"] += 1
                    fehler.append((body, tri, 1000.0 * e, len(tr2)))
    z["fehler"] = fehler
    return z


def main():
    rng = np.random.default_rng(SEED)
    dateien, szenen = szenen_lesen(LOGS, N, rng)
    if not szenen:
        print(f"Keine 'after ep'-Zeilen in {LOGS} gefunden. Laeuft act23 mit ACT23_DEBUG=1?")
        return
    print(f"Protokolle: {len(dateien)} Datei(en) aus {LOGS}")
    print(f"Szenen: {len(szenen)}, {ZIEHUNGEN} Achsen-Wuerfe je Koerper, Seed {SEED}")
    print(f"Zustand: {STATE}")
    print("NACHBILDUNG der Wuerfelei (pc_act23.py:1781, Stand 2026-09-14) -- nicht der Code selbst.")
    print("Lagen vom Episodenende, Yaw neu gewuerfelt, Farben aus dem geladenen Zustand.\n")

    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")

    erg = []
    for teil in VARIANTEN.split("|"):
        name, _, rest = teil.partition(":")
        zuw = dict(kv.split("=", 1) for kv in rest.split(",") if "=" in kv)
        mod = lade_modul(zuw)
        z = eine_variante(mod, sim, szenen, SEED + 1)
        erg.append((name.strip() or "?", z))
        print(f"  {name.strip() or '?':10s} gemessen" + (f"   ({rest})" if rest else ""))

    print(f"\n{'Variante':10s} {'Adressen':>9s} {'grob >20mm':>16s} {'Rueckfall':>14s} "
          f"{'Achsen':>7s} {'eindeutig':>10s} {'keine Adr.':>11s}")
    for name, z in erg:
        a = max(1, z["adressen"])
        print(f"{name:10s} {z['adressen']:9d} {z['grob']:6d} = {100*z['grob']/a:5.1f} % "
              f"{z['rueckfall']:5d} = {100*z['rueckfall']/a:5.1f} % {z['achsen']/a:7.2f} "
              f"{100*z['eindeutig']/a:9.1f} % {z['keine']:11d}")

    if len(erg) > 1:
        b = erg[0][1]
        print(f"\ngegen '{erg[0][0]}' (Fisher):")
        for name, z in erg[1:]:
            pg = fisher(z["grob"], z["adressen"] - z["grob"], b["grob"], b["adressen"] - b["grob"])
            pr = fisher(z["rueckfall"], z["adressen"] - z["rueckfall"],
                        b["rueckfall"], b["adressen"] - b["rueckfall"])
            print(f"  {name:10s} grob p = {pg:.4f}   Rueckfall p = {pr:.4f}")
        print("\nBeide Spalten zusammen lesen: die Groessenachse hat im siebten Anlauf die groben")
        print("Fehler gesenkt und den Rueckfall verdoppelt -- das eine ist ohne das andere nicht")
        print("zu haben (wiki/befunde/groessenachse-spanne.md).")

    if os.environ.get("AW_FEHLER", "0") == "1":
        for name, z in erg:
            print(f"\n=== {name}: grobe Fehler ===")
            for body, tri, e, n in z["fehler"][:20]:
                print(f"  {body:10s} {str(tri):46s} {e:6.1f} mm  {n} Treffer")


if __name__ == "__main__":
    main()
