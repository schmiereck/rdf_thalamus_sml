"""DIE DAEMPFUNGSFUNKTION: wie weit traegt eine vorgestellte Verschiebung?

DIE FRAGE (wiki/fragen/latente-augmentierung.md, Nutzeridee).  Aus einem bestaetigten Griff sollen
viele leicht verschobene Varianten erzeugt werden, "mit abnehmender Intensitaet".  Die Seite
verlangt ausdruecklich, die Voraussetzung zu MESSEN statt anzunehmen -- und nennt den Einwand, an
dem alles haengt: *die Daempfung muss vom KONTEXT abhaengen, nicht nur vom Betrag*, weil die
Aequivarianz in Nachbarnaehe und am Rand bricht.

WAS HIER GEMESSEN WIRD.  Eine Vorstellung ist nur so gut, wie der Zustand, den sie faelscht, dem
entspricht, den die Welt wirklich liefern wuerde.  Also: echte Laufszene nehmen, den Zustand
aufnehmen, EINEN Koerper um delta verschieben, neu wahrnehmen -- und vergleichen, was die
Vorstellung vorhergesagt haette:

    LAGE       vorhergesagt pos + delta        gemessen: Restfehler in mm
    FORM       vorhergesagt UNVERAENDERT       (desc_embed ist verschiebungsinvariant)
    WINKEL     vorhergesagt UNVERAENDERT       (Phasen aus yaw/yaw4)
    NACHBARN   vorhergesagt NICHTS -- der Block aendert sich, und genau das ist Einwand 1

Der Formfehler wird an der KLASSENTRENNUNG gemessen, nicht in abstrakten Einheiten: wie gross ist
die Drift verglichen mit dem typischen Abstand zwischen zwei VERSCHIEDENEN Koerpern?  Erst das
macht "0,4" zu einer Aussage.

Alles aufgeschluesselt nach dem NACHBARABSTAND der Ausgangsszene -- die zweite Achse der
Daempfungsfunktion, ohne die sie laut Seite falsch waere.

DIE SZENEN kommen aus `log/` (s. wiki/mechanismen/wiedervorlage.md), nicht aus einer
Handverteilung: eine selbstgebaute Sonde lag beim Nachbarabstand schon einmal um Faktor 15 daneben.

ZUSATZ, falls der Zustand ein `latent_goal` enthaelt: dieselbe Frage fuer das ZIEL-LATENT, das die
Augmentierung benutzen wuerde.  `encode_world` ist eine Gitter-Interpolation, keine reine
Phasendrehung -- ob die Verschiebung dort linear bleibt, ist eine eigene Messung und nicht aus dem
RoPE-Docstring abzulesen.

AUFRUF
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_daempfung.py

KNOEPFE
    DF_LOGS     Glob auf die Protokolle (Vorgabe log/pc_act23_*.txt) -- auf EINEN Lauf einengen
    DF_N        Szenen (Vorgabe 60)
    DF_STATE    Zustandsdatei -- immer eine KOPIE
    DF_SEED     Zufallsstrom (Vorgabe 5)
    DF_DELTAS   Verschiebungen in mm (Vorgabe "2,5,10,20,30,40")
    DF_RICHT    Richtungen je Koerper und delta (Vorgabe 3)

GRENZEN
  * Der Yaw steht nicht im Protokoll und wird je Szene neu gewuerfelt -- innerhalb einer Szene
    aber festgehalten, sonst waere der Vergleich vorher/nachher wertlos.
  * Verschiebungen, die den Koerper naeher als 25 mm an einen anderen bringen oder aus dem
    Arbeitsraum tragen, werden VERWORFEN -- sie waeren physisch unmoeglich, und eine Vorstellung
    davon waere kein Aequivarianz-Problem, sondern ein Szenenfehler.
  * Gemessen wird die WAHRNEHMUNG einer verschobenen Szene, nicht der Ausgang eines Griffs.  Ob
    ein Griff an der neuen Lage geglueckt WAERE, sagt diese Messung nicht.
"""
import glob
import os
import pickle
import re
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim, REACH_XY             # noqa: E402

LOGS = os.environ.get("DF_LOGS", "log/pc_act23_*.txt")
N = int(os.environ.get("DF_N", "60"))
STATE = os.environ.get("DF_STATE", "src/pc_cvnn/state/act23_state.pkl")
SEED = int(os.environ.get("DF_SEED", "5"))
DELTAS = [float(x) for x in os.environ.get("DF_DELTAS", "2,5,10,20,30,40").split(",")]
RICHT = int(os.environ.get("DF_RICHT", "3"))
PARKED_X = 0.4
MIN_ABSTAND = 0.025                   # naeher waere physisch unmoeglich -> Verschiebung verwerfen
NB_BAENDER = [(0.0, 0.06), (0.06, 0.09), (0.09, 9.9)]   # nah / mittel / frei

RE_SZENE = re.compile(r"\[dbg\] after ep : \{(.*)\}")
RE_PAAR = re.compile(r"'(\w+)': \[([-\d.]+), ([-\d.]+)\]")


def szenen_lesen(muster, n, rng):
    aus = []
    for f in sorted(glob.glob(muster)):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = RE_SZENE.search(ln)
                if m:
                    aus.append({k: (float(a), float(b))
                                for k, a, b in RE_PAAR.findall(m.group(1))})
    rng.shuffle(aus)
    return aus[:n]


def zustand_von(sim, sc, koerper, lage):
    """Den Wahrnehmungszustand des Koerpers aufnehmen: Lage, Winkelphasen, Formeinbettung.

    Gibt None, wenn nichts auf dem Koerper sitzt -- dann ist gar keine Vorstellung zu pruefen."""
    sv = sim.d.mocap_pos.copy()
    dets = [d for d in sc.perceive_all(sim)
            if d.get("pos") is not None and float(d.get("area", 0)) >= 200.0]
    sim.d.mocap_pos[:] = sv
    mujoco.mj_forward(sim.m, sim.d)
    if not dets:
        return None
    p = np.asarray(lage, float)
    best = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - p)))
    if float(np.linalg.norm(np.asarray(best["pos"], float) - p)) > 0.02:
        return None                                  # verfehlt -- kein brauchbarer Ausgangszustand
    if best.get("desc") is None:
        return None
    y2, y4 = float(best.get("yaw", 0.0)), float(best.get("yaw4", 0.0))
    return dict(pos=np.asarray(best["pos"], float),
                phase=np.array([np.cos(2 * y2), np.sin(2 * y2),
                                np.cos(4 * y4), np.sin(4 * y4)]),
                emb=np.asarray(sc.desc_embed(best["desc"]), float),
                dets=dets)


def main():
    rng = np.random.default_rng(SEED)
    szenen = szenen_lesen(LOGS, N, rng)
    if not szenen:
        print(f"Keine 'after ep'-Zeilen in {LOGS}.  Laeuft act23 mit ACT23_DEBUG=1?")
        return
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc = st["shape_clf"]
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    lo, hi = REACH_XY

    print(f"Szenen: {len(szenen)} aus {LOGS}")
    print(f"Verschiebungen: {DELTAS} mm, {RICHT} Richtungen je Koerper, Seed {SEED}")
    print(f"Zustand: {STATE}\n")

    # BEZUGSMASS fuer die Formdrift: wie weit liegen die Einbettungen VERSCHIEDENER Koerper
    # auseinander?  Ohne das ist eine Drift von 0,4 keine Aussage.
    alle = sorted({o for s in szenen for o in s})
    solo = {}
    for b in alle:
        for o in alle:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object(b, [0.0, 0.16], z=0.012, yaw=0.0)
        mujoco.mj_forward(sim.m, sim.d)
        z = zustand_von(sim, sc, b, [0.0, 0.16])
        if z is not None:
            solo[b] = z["emb"]
    paare = [float(np.linalg.norm(solo[a] - solo[b]))
             for i, a in enumerate(sorted(solo)) for b in sorted(solo)[i + 1:]]
    trenn = float(np.median(paare)) if paare else 1.0
    print(f"Bezugsmass Formdrift: Median-Abstand zwischen VERSCHIEDENEN Koerpern = {trenn:.2f}")
    print(f"  (eine Drift von {trenn:.2f} entspricht also einem ganzen Koerperwechsel)\n")

    z = defaultdict(lambda: dict(n=0, lage=[], form=[], phase=[], nb=[]))
    verworfen = 0
    for sz in szenen:
        yaws = {o: float(rng.uniform(0, 2 * np.pi)) for o in sz}
        auf = [o for o, (x, y) in sz.items() if x < PARKED_X]
        for koerper in auf:
            for o, (x, y) in sz.items():
                sim.set_object(o, [x, y], z=0.012, yaw=yaws[o])
            mujoco.mj_forward(sim.m, sim.d)
            p0 = np.asarray(sz[koerper], float)
            andere = [np.asarray(sz[o], float) for o in auf if o != koerper]
            nb0 = min((float(np.linalg.norm(p0 - q)) for q in andere), default=9.9)
            band = next(i for i, (a, b) in enumerate(NB_BAENDER) if a <= nb0 < b)
            z0 = zustand_von(sim, sc, koerper, p0)
            if z0 is None:
                continue
            for dmm in DELTAS:
                for _ in range(RICHT):
                    w = rng.uniform(0, 2 * np.pi)
                    dxy = (dmm / 1000.0) * np.array([np.cos(w), np.sin(w)])
                    p1 = p0 + dxy
                    if np.any(p1 < lo) or np.any(p1 > hi) or any(
                            float(np.linalg.norm(p1 - q)) < MIN_ABSTAND for q in andere):
                        verworfen += 1
                        continue
                    sim.set_object(koerper, p1.tolist(), z=0.012, yaw=yaws[koerper])
                    mujoco.mj_forward(sim.m, sim.d)
                    z1 = zustand_von(sim, sc, koerper, p1)
                    sim.set_object(koerper, p0.tolist(), z=0.012, yaw=yaws[koerper])
                    mujoco.mj_forward(sim.m, sim.d)
                    if z1 is None:
                        # Die Welt liefert an der vorgestellten Lage GAR KEINEN Zustand -- die
                        # Vorstellung waere vollstaendig falsch.  Als Maximalfehler zaehlen.
                        e = z[(dmm, band)]
                        e["n"] += 1; e["lage"].append(np.nan)
                        e["form"].append(np.nan); e["phase"].append(np.nan)
                        continue
                    e = z[(dmm, band)]
                    e["n"] += 1
                    e["lage"].append(1000.0 * float(np.linalg.norm(
                        (z1["pos"] - z0["pos"]) - dxy)))          # Rest nach Abzug von delta
                    e["form"].append(float(np.linalg.norm(z1["emb"] - z0["emb"])))
                    e["phase"].append(float(np.linalg.norm(z1["phase"] - z0["phase"])))

    print(f"{'delta':>6s} {'Nachbar':>9s} {'n':>5s} {'Lagerest':>16s} {'Formdrift':>20s} "
          f"{'Winkeldrift':>12s} {'verloren':>9s}")
    namen = ["< 60 mm", "60-90 mm", "> 90 mm"]
    for dmm in DELTAS:
        for band in range(len(NB_BAENDER)):
            e = z.get((dmm, band))
            if not e or not e["n"]:
                continue
            la = np.array(e["lage"], float); fo = np.array(e["form"], float)
            ph = np.array(e["phase"], float)
            verl = int(np.isnan(la).sum())
            ok = ~np.isnan(la)
            if ok.sum() == 0:
                continue
            print(f"{dmm:6.0f} {namen[band]:>9s} {e['n']:5d} "
                  f"{np.median(la[ok]):7.2f} mm (p90 {np.percentile(la[ok], 90):5.2f}) "
                  f"{np.median(fo[ok]):7.3f} = {100*np.median(fo[ok])/trenn:4.0f} % Trennung "
                  f"{np.median(ph[ok]):12.3f} {verl:9d}")
    print(f"\nverworfene Verschiebungen (unmoeglich oder ausserhalb): {verworfen}")

    lg = st.get("latent_goal")
    if lg is not None:
        print("\n=== ZIEL-LATENT (encode_world) -- ist die Verschiebung dort linear? ===")
        try:
            from pc_cvnn.arm_modules.latent_goal import LatentGoalServo
            if isinstance(lg, dict):
                # Im Zustand liegt das Servo GEPACKT (pc_act23._lg_pack).  Hier dieselbe
                # Entpackung, ohne das ganze Modul zu laden -- sie ist vier Zeilen lang.
                _o = LatentGoalServo.__new__(LatentGoalServo)
                _o.gm = None; _o.rng = np.random.default_rng(3); _o.z_g = None
                _o._gx = lg["gx"]; _o._grid_z = lg["grid_z"]; _o.D = lg["D"]
                _o.zmu = 0.0; _o.zsd = lg["zsd"]
                lg = _o
            D = getattr(lg, "D", None)
            enc = getattr(lg, "encode_world", None)
            if enc is None or D is None:
                print("  (im Zustand liegt kein benutzbares Servo -- uebersprungen)")
            else:
                zsd = float(getattr(lg, "zsd", 1.0))
                for dmm in DELTAS:
                    err = []
                    for _ in range(200):
                        p = rng.uniform(lo + 0.02, hi - 0.02)
                        w = rng.uniform(0, 2 * np.pi)
                        dp = (dmm / 1000.0) * np.array([np.cos(w), np.sin(w)])
                        q = np.clip(p + dp, lo, hi)
                        dz = (np.asarray(enc(q)) - np.asarray(enc(p))) / zsd
                        err.append(1000.0 * float(np.linalg.norm(
                            np.real(dz @ D) - (q - p))))
                    print(f"  delta {dmm:5.0f} mm   Rueckrechnung-Fehler Median "
                          f"{np.median(err):6.2f} mm = {100*np.median(err)/dmm:4.0f} % von delta")
        except Exception as exc:                                  # noqa: BLE001
            print(f"  (uebersprungen: {exc})")


if __name__ == "__main__":
    main()
