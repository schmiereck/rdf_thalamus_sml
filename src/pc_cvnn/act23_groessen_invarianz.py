"""FUENFTER ANLAUF ZUR GROESSEN-INVARIANZ DES FORMDESKRIPTORS.

Vier Anlaeufe sind gescheitert (wiki/befunde/formfaktorisierung.md), gemessen an der Kennzahl

    K = groesster GROESSEN-Abstand / kleinster FORM-Abstand        (unter 1,0 waere das Ziel)

    heute: |F|, feste Ringe                     2,54
    Ringe an der DICKE skaliert                 2,23
    je Ring durch den DC-Anteil geteilt         2,13
    durch die Gesamtfuellung geteilt            2,42

Die Diagnose dort: *"ein groesserer Arm fuellt mehr Kreisumfang JE RING, und das ueberlebt jede
Radien- oder Amplitudennormierung."*  Genau das ist der Hebel, den alle vier verfehlt haben:
sie haben AMPLITUDEN normiert oder die Radien GLOBAL skaliert.  Die Ringe liegen aber weiter an
festen WELTradien (RW = 4..46 mm), also misst Ring i bei einem doppelt so grossen Objekt eine
voellig andere Stelle der Form.

DER FUENFTE ANSATZ: die Ringe an der EIGENAUSDEHNUNG des Objekts aufhaengen, sodass Ring i immer
bei derselben RELATIVEN Position sitzt.  Dann ist "Ring 3 von 11" bei jeder Groesse dieselbe
Stelle der Form, und die Winkelfuellung dort ist eine Formaussage statt einer Groessenaussage.

Drei Masse fuer die Eigenausdehnung werden gegeneinander gestellt, weil die Wahl nicht von
vornherein klar ist:
    rms     Wurzel des mittleren quadratischen Abstands vom Schwerpunkt (robust, klassisch)
    sqrtA   Wurzel der Flaeche (robust gegen Ausreisser, blind fuer Form)
    rmax    95.-Perzentil des Abstands (empfindlich, folgt der laengsten Achse)

KONTROLLE: derselbe Aufbau rechnet die heutige Fassung mit, damit die Kennzahl direkt vergleichbar
ist und nicht gegen eine Zahl aus einem anderen Messaufbau steht.

NICHTS WIRD GELERNT UND NICHTS GESPEICHERT.  Gerechnet wird auf rohen Masken; der Zustand wird
nur gelesen (fuer fmu/fsd, die Standardisierung).

Aufruf:
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_groessen_invarianz.py
Knoepfe: GI_STATE (KOPIE), GI_N (Lagen je Koerper/Groesse, 10), GI_SEED
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ACT14_DOF", "4")

import mujoco                                                    # noqa: E402
from pc_cvnn.pc_act14 import BracketArmSim                       # noqa: E402

STATE = os.environ.get("GI_STATE", "src/pc_cvnn/state/act23_state.pkl")
N = int(os.environ.get("GI_N", "10"))
SEED = int(os.environ.get("GI_SEED", "5"))
ALLE = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]

# (Name, Formkennung, Halbmasse).  Gleiche Formkennung = dieselbe FORM in anderer GROESSE.
# Drei Formen x drei Groessen, damit "Form-Abstand" und "Groessen-Abstand" beide besetzt sind.
PROBEN = [
    ("balken_klein",  "balken",  (0.015, 0.005, 0.012)),
    ("balken_mittel", "balken",  (0.021, 0.007, 0.012)),
    ("balken_gross",  "balken",  (0.030, 0.010, 0.012)),
    ("quadrat_klein", "quadrat", (0.012, 0.012, 0.012)),
    ("quadrat_mittel","quadrat", (0.017, 0.017, 0.012)),
    ("quadrat_gross", "quadrat", (0.024, 0.024, 0.012)),
    ("flach_klein",   "flach",   (0.016, 0.010, 0.012)),
    ("flach_mittel",  "flach",   (0.022, 0.014, 0.012)),
    ("flach_gross",   "flach",   (0.030, 0.019, 0.012)),
]


def main():
    with open(STATE, "rb") as f:
        st = pickle.load(f)
    sc = st["shape_clf"]
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    rng = np.random.default_rng(SEED)
    B = "obj_T"
    orig = sim.m.geom_size[sim.m.body_geomadr[
        mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, B)]].copy()

    def maske_und_ctr(half):
        """Eine Sichtung: Maske der groessten Komponente + Weltschwerpunkt."""
        from scipy import ndimage
        for o in ALLE:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_object_size(B, np.asarray(half, float))
        sim.set_object(B, [float(rng.uniform(-0.04, 0.04)),
                           float(rng.uniform(0.145, 0.185))],
                       z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
        mujoco.mj_forward(sim.m, sim.d)
        sc._park_markers(sim)
        img = sc._render_u8(sim)
        m = sc._mask(img)
        lab, n = ndimage.label(m > 0)
        if n == 0:
            return None, None
        k = 1 + int(np.argmax([(lab == i).sum() for i in range(1, n + 1)]))
        comp = (lab == k)
        if comp.sum() < 30:
            return None, None
        ys, xs = np.nonzero(comp)
        W = sc._px_to_world(np.column_stack([xs, ys]))
        return comp.astype(np.float32), W

    def harm_relativ(comp, W, mass):
        """Harmonische auf Ringen, die an der EIGENAUSDEHNUNG haengen (der fuenfte Ansatz)."""
        ctr = W.mean(0)
        d = np.linalg.norm(W - ctr, axis=1)
        if mass == "rms":
            R = float(np.sqrt((d ** 2).mean()))
        elif mass == "sqrtA":
            R = float(np.sqrt(comp.sum()) * float(np.median(d) / max(1e-9, np.sqrt(len(d)))) * 2.0)
            R = float(np.sqrt((d ** 2).mean())) if not np.isfinite(R) or R <= 0 else R
        else:                                                    # rmax
            R = float(np.percentile(d, 95))
        if not np.isfinite(R) or R <= 1e-6:
            return None
        # RELATIVE Ringe: gleiche Anzahl wie heute, aber als Bruchteil der Eigenausdehnung
        rel = np.linspace(0.15, 1.35, len(sc.RW))
        H_, Wd = comp.shape
        th = np.arange(sc.NA) / sc.NA * 2 * np.pi
        ring = np.column_stack([np.cos(th), np.sin(th)])
        F = np.empty((len(rel), sc.NH), complex)
        for i, f in enumerate(rel):
            rp = sc._world_to_px(ctr + (f * R) * ring)
            py = np.clip(rp[:, 1].astype(int), 0, H_ - 1)
            px = np.clip(rp[:, 0].astype(int), 0, Wd - 1)
            F[i] = np.fft.fft(comp[py, px])[:sc.NH]
        return np.abs(F).ravel()

    def harm_heute(comp, W):
        ctr = W.mean(0)
        return np.abs(sc._harmonics_at(comp, ctr)).ravel()

    def harm_alt(comp, W, art):
        """Die DREI bereits gescheiterten Normierungen, IM SELBEN AUFBAU nachgerechnet.

        Ohne das waere der Vergleich unfair: dieser Pruefstand spannt eine groessere
        Groessenspanne auf als der urspruengliche (die heutige Fassung kommt hier auf 4,00 statt
        der dort berichteten 2,54).  Eine Verbesserung gegen eine Zahl aus einem anderen Aufbau
        waere keine."""
        ctr = W.mean(0)
        if art == "dicke":                                 # Ringe an der DICKE skaliert
            X = W - ctr
            C = X.T @ X / max(1, len(X))
            ev = np.linalg.eigvalsh(C)
            dick = float(np.sqrt(max(ev[0], 1e-12)))
            H_, Wd = comp.shape
            th = np.arange(sc.NA) / sc.NA * 2 * np.pi
            ring = np.column_stack([np.cos(th), np.sin(th)])
            F = np.empty((len(sc.RW), sc.NH), complex)
            skal = np.asarray(sc.RW) / float(max(sc.RW)) * (dick * 8.0)
            for i, r in enumerate(skal):
                rp = sc._world_to_px(ctr + r * ring)
                py = np.clip(rp[:, 1].astype(int), 0, H_ - 1)
                px = np.clip(rp[:, 0].astype(int), 0, Wd - 1)
                F[i] = np.fft.fft(comp[py, px])[:sc.NH]
            return np.abs(F).ravel()
        F = sc._harmonics_at(comp, ctr)
        if art == "dc":                                    # je Ring durch den DC-Anteil geteilt
            return np.abs(F / np.maximum(np.abs(F[:, 0:1]), 1e-9)).ravel()
        if art == "fuellung":                              # durch die Gesamtfuellung geteilt
            return (np.abs(F) / max(float(comp.sum()), 1.0)).ravel()
        raise ValueError(art)

    # ---- sammeln ----
    daten = {v: {} for v in ("heute", "dicke", "dc", "fuellung", "rms", "sqrtA", "rmax")}
    form_of = {}
    print(f"Zustand: {STATE}   {N} Lagen je Probe, {len(PROBEN)} Proben\n")
    for name, form, half in PROBEN:
        form_of[name] = form
        for v in daten:
            daten[v][name] = []
        for _ in range(N):
            comp, W = maske_und_ctr(half)
            if comp is None:
                continue
            daten["heute"][name].append(harm_heute(comp, W))
            for v in ("dicke", "dc", "fuellung"):
                try:
                    daten[v][name].append(harm_alt(comp, W, v))
                except Exception:
                    pass
            for v in ("rms", "sqrtA", "rmax"):
                h = harm_relativ(comp, W, v)
                if h is not None:
                    daten[v][name].append(h)
        print(f"  {name:15s} {len(daten['heute'][name]):2d} Sichtungen")
    sim.set_object_size(B, orig)

    # ---- Kennzahl je Variante ----
    print(f"\n{'Variante':10s} {'K = Groesse/Form':>18s} {'max Groessen-Abst.':>19s} "
          f"{'min Form-Abst.':>15s}")
    for v in ("heute", "dicke", "dc", "fuellung", "rms", "sqrtA", "rmax"):
        Z = {}
        for name, L in daten[v].items():
            if len(L) < 2:
                continue
            A = np.array(L)
            Z[name] = A.mean(0)
        if len(Z) < 4:
            print(f"  {v:10s} (zu wenig Daten)")
            continue
        mu = np.mean(list(Z.values()), axis=0)
        sd = np.std(list(Z.values()), axis=0) + 1e-9
        Zn = {k: (z - mu) / sd for k, z in Z.items()}
        gross, formd = [], []
        ks = list(Zn)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                d = float(np.linalg.norm(Zn[ks[i]] - Zn[ks[j]]))
                (gross if form_of[ks[i]] == form_of[ks[j]] else formd).append(d)
        K = max(gross) / min(formd) if formd and gross else float("nan")
        print(f"  {v:10s} {K:17.2f} {max(gross):18.2f} {min(formd):14.2f}")
    print("\n  K unter 1,0 = jede Groessenvariante liegt naeher an ihrer eigenen Form")
    print("  als die naechste FREMDE Form -> Groessen-Invarianz erreicht.")
    print("  heute/dicke/dc/fuellung = die vier GESCHEITERTEN Fassungen, hier im SELBEN Aufbau")
    print("  nachgerechnet; rms/sqrtA/rmax = der fuenfte Ansatz.")
    print("  Die Zahlen aus formfaktorisierung.md stammen aus einem ANDEREN Aufbau.")


if __name__ == "__main__":
    main()
