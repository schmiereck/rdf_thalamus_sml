"""Bewertet das Welt-Modell IN DEM BEREICH, IN DEM DER AGENT ARBEITET.

WARUM DAS NOETIG IST (gemessen 2026-08-11):
Das Modell erreicht auf ausgelassenen Pufferzeilen AUC 0.860 -- auf den Episoden, die es selbst
faehrt, aber nur 0.489.  Teilt man die Testzeilen nach der Bewertung auf, die das Modell der
Aktion gibt, zerfaellt die Unterscheidungskraft monoton: 0.855 / 0.752 / 0.634 / 0.581 ueber die
mu-Quartile.  Die 0.86 stammen also fast vollstaendig daraus, SCHLECHTE Aktionen zu erkennen --
und genau die waehlt der Agent nie, weil er das Maximum nimmt.  Jede Kennzahl ueber den ganzen
Puffer misst damit den leichten Teil des Problems.

ERGEBNIS (2026-08-11, 6732 Zeilen) -- die Vermutung oben hat sich NICHT bestaetigt:
Im Arbeitsbereich erreicht das Modell 0.816 gegen 0.860 insgesamt, und 76% aller Zeilen liegen
ohnehin darin.  Die Faehigkeit sitzt also NICHT ausserhalb des Arbeitsbereichs.  Gewichtung
(x3/x10/x30), Vergessen und Binarisieren des Labels aendern nichts (0.810-0.814 gegen 0.816).

Gefunden wurde stattdessen ein LECK IN DER BEWERTUNG (Abschnitt [5]): aufeinanderfolgende
Pufferzeilen stammen aus demselben GUI-Lauf, und dort bleibt die Szene STEHEN -- nur das
kommandierte Objekt bewegt sich.  Die Testzeilen haben deshalb Beinah-Duplikate im Training.
Legt man eine Luecke dazwischen, faellt die AUC von 0.860 auf 0.656.  Das ist vertraeglich mit
dem, was im echten Lauf gemessen wurde (0.489 bzw. 0.569 gegen das Selbst-Urteil, 95% bis 0.73)
-- die 0.86 waren also nie die Verallgemeinerung, sondern die Naehe.
FOLGE: jede Merkmalsbewertung, die ueber einen benachbarten Halteteil lief, ist zu optimistisch.

DER ARBEITSBEREICH wird hier NICHT ueber eine mu-Schwelle definiert (die waere zirkulaer und
haengt am Niveau, das stark mit dem Radius koppelt -- gemessen -0.475, obwohl der Radius nichts
mehr vorhersagt).  Stattdessen ueber den RANG DER AKTION INNERHALB IHRER EIGENEN SITUATION: fuer
jede Zeile wird der Kandidatensatz dieser Situation bewertet und geschaut, in welchem Perzentil
die tatsaechlich gefahrene Aktion liegt.  Damit faellt das Situationsniveau heraus, und die Frage
lautet genau: "haette der Agent so etwas gewaehlt?"

Der Bewerter fuer den Rang wird auf einem FRUEHEREN, disjunkten Abschnitt trainiert, damit die
Regime-Definition nicht vom selben Fit stammt, der anschliessend bewertet wird.

    python src/pc_cvnn/act23_wm_regime.py [pfad/zum/state.pkl]
"""
import copy
import os
import pickle
import sys
import time

import numpy as np

os.environ.setdefault("ACT14_DOF", "4")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SCORER_END = 4000        # Zeilen [0, SCORER_END) trainieren den unabhaengigen Rang-Bewerter
TEST = 500               # die letzten TEST Zeilen sind die Testmenge
TOP = 0.90               # Arbeitsbereich = Aktion im obersten (1-TOP) des Kandidatensatzes
EPOCHS = 600


def auc(score, label):
    """AUC gegen ein BINARISIERTES Label (Y ist abgestuft, s. Modul-Kopf)."""
    lab = np.asarray(label, float) > 0.5
    pos, neg = np.asarray(score, float)[lab], np.asarray(score, float)[~lab]
    if len(pos) < 3 or len(neg) < 3:
        return float("nan")
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


def fit(proto, X, Y, W, idx, epochs=EPOCHS):
    m = copy.deepcopy(proto)
    m._X = [x for x in X[idx]]
    m._Y = [y for y in Y[idx]]
    m._W = [v for v in W[idx]]
    m.train(epochs=epochs)
    return m


def score_rows(m, X, fd):
    return np.array([m.predict(X[i, :fd], X[i, fd:][None])[0][0] for i in range(len(X))])


def action_rank(scorer, X, fd, rows):
    """Perzentil der gefahrenen Aktion im Kandidatensatz IHRER Situation (0 = schlechteste)."""
    out = np.empty(len(rows))
    for j, i in enumerate(rows):
        f = X[i, :fd]
        A = scorer.candidates(0, yaw=scorer.yaw_of(f), r=scorer.radius_of(f))
        mu_c, _ = scorer.predict(f, A)
        mu_r = float(scorer.predict(f, X[i, fd:][None])[0][0])
        out[j] = float((mu_c <= mu_r).mean())
    return out


def main(path):
    with open(path, "rb") as fh:
        w = pickle.load(fh)["world"]
    X = np.asarray(w._X, float)
    Y = np.asarray(w._Y, float).ravel()
    W = (np.asarray(w._W, float).ravel() if getattr(w, "_W", None) is not None
         else np.ones(len(Y)))
    fd = w.feat_dim
    n = len(Y)
    te = np.arange(n - TEST, n)
    tr = np.arange(0, n - TEST)
    print(f"  Puffer {n} Zeilen, feat_dim {fd}; Test = die letzten {TEST} "
          f"(Lieferrate {100 * (Y[te] > 0.5).mean():.0f}%)")

    # --- 1. Arbeitsbereich bestimmen ----------------------------------------------------------
    t0 = time.perf_counter()
    scorer = fit(w, X, Y, W, np.arange(0, SCORER_END))
    rank = action_rank(scorer, X, fd, te)
    reg = rank >= TOP
    print(f"  Rang-Bewerter aus Zeilen 0-{SCORER_END} ({time.perf_counter() - t0:.0f}s)")
    print(f"  ARBEITSBEREICH (Aktion im obersten {100 * (1 - TOP):.0f}% ihrer Situation): "
          f"{reg.sum()} von {TEST} Testzeilen, Lieferrate {100 * (Y[te][reg] > 0.5).mean():.0f}% "
          f"(Grundrate {100 * max((Y[te][reg] > 0.5).mean(), 1 - (Y[te][reg] > 0.5).mean()):.0f}%)")

    def report(name, m):
        s = score_rows(m, X[te], fd)
        a_all, a_reg = auc(s, Y[te]), auc(s[reg], Y[te][reg])
        print(f"    {name:<38} AUC gesamt {a_all:.3f}   IM ARBEITSBEREICH {a_reg:.3f}")
        return a_all, a_reg

    print("\n  [0] Ausgangslage")
    base = fit(w, X, Y, W, tr)
    report("heutiger Fit (alle Zeilen davor)", base)

    # --- 2. Vergessen, unter der RICHTIGEN Kennzahl neu geprueft ------------------------------
    print("\n  [1] Vergessen  (an der Gesamt-AUC sah es schaedlich aus -- gilt das im Bereich?)")
    for keep in (3000, 1500, 800):
        report(f"nur die letzten {keep} Zeilen", fit(w, X, Y, W, tr[-keep:]))

    # --- 3. Gewichtung statt Beschraenkung ----------------------------------------------------
    print("\n  [2] Gewichtung  (alle Zeilen behalten, Arbeitsbereich im Verlust hochgewichten)")
    rank_tr = action_rank(scorer, X, fd, tr)
    in_tr = rank_tr >= TOP
    print(f"      Trainingszeilen im Arbeitsbereich: {in_tr.sum()} von {len(tr)} "
          f"({100 * in_tr.mean():.0f}%)")
    for f_ in (3.0, 10.0, 30.0):
        Wg = W[tr].copy()
        Wg[in_tr] *= f_
        m = copy.deepcopy(w)
        m._X = [x for x in X[tr]]; m._Y = [y for y in Y[tr]]; m._W = [v for v in Wg]
        m.train(epochs=EPOCHS)
        report(f"Arbeitsbereich x{f_:g} gewichtet", m)

    # --- 4. Label: abgestuft (wie heute) gegen binaer -----------------------------------------
    print("\n  [3] Label  (heute abgestuft; hilft oder schadet die Abstufung im Bereich?)")
    report("binarisiert (0/1 statt Guete)", fit(w, X, (Y > 0.5).astype(float), W, tr))

    # --- 5. Merkmalsbloecke: nur dort, wo sie ueberhaupt gesetzt waren -------------------------
    print("\n  [4] Merkmalsbloecke  (Gueltig-Flag nur in ~10% der Zeilen gesetzt)")
    for name, a, c in (("Nachbarn", 14, 19), ("Fovea", 19, 31), ("Koerper", 31, 38)):
        have_te = (X[te, a] > 0.5) & reg
        have_tr = X[tr, a] > 0.5
        y_te = Y[te][have_te] > 0.5
        if have_te.sum() < 20 or y_te.all() or not y_te.any():
            print(f"    {name:<12} NICHT PRUEFBAR: nur {have_te.sum()} Testzeilen im "
                  f"Arbeitsbereich haben den Block (Training {have_tr.sum()})")
            continue
        Xa = X.copy(); Xa[:, a:c] = 0.0
        m1 = fit(w, Xa, Y, W, tr)                    # `base` ist der Fit MIT allen Bloecken
        s0 = score_rows(base, X[te][have_te], fd); s1 = score_rows(m1, Xa[te][have_te], fd)
        print(f"    {name:<12} n={have_te.sum():3d}  mit {auc(s0, Y[te][have_te]):.3f}  "
              f"ohne {auc(s1, Y[te][have_te]):.3f}")


    # --- 6. DAS LECK: Naehe zwischen Training und Test --------------------------------------
    print("")
    print("  [5] Naehe-Leck  (Szene bleibt im GUI-Lauf STEHEN -> Beinah-Duplikate im Training)")
    for gap in (0, 500, 1500, 3000):
        idx = np.arange(0, n - TEST - gap)
        s_ = score_rows(fit(w, X, Y, W, idx), X[te], fd)
        print(f"    Luecke {gap:4d} Zeilen (Training bis {n - TEST - gap:4d})   "
              f"AUC {auc(s_, Y[te]):.3f}")
    print("    -> faellt die AUC mit der Luecke, war der benachbarte Halteteil zu leicht.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else os.path.join(os.path.dirname(__file__), "state", "act23_state.pkl"))
