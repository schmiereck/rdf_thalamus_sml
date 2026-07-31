"""WorldModelModule — a SELF-SUPERVISED outcome/world model for grasping (act23).

The agent's own grasp trials are the only training signal: it tries a grasp action in a
perceived situation, observes whether the object was DELIVERED (0/1 from run_combined), and
learns P(deliver | situation, action).  No scripted teacher labels -- the OUTCOME is the label.

Why an ENSEMBLE: a single learned model is imperfect, and picking actions by naive argmax over
it EXPLOITS its errors (the optimizer's curse -- it selects exactly the actions the model
over-predicts) and ends up WORSE than a safe default (measured in this project, see the
[[act-grasp-learning-ceiling]] note).  An ensemble of K regressors gives a MEAN mu (predicted
success) AND a STD sigma (epistemic uncertainty -> high where little data).  Acting on the
LOWER confidence bound (mu - lam*sigma) deviates from the default ONLY where the model is
CONFIDENT it is better -> it cannot underperform the default, and it still improves where it
has learned.  This is the fix for the model-exploitation failure.

Lifelong: observe() keeps buffering, train() refits -> the model gets better as the agent acts,
and generalises to NEW shapes/positions via the PERCEIVED features (no per-case tuning).

Situation features (perceived, NOT privileged): [pos_x, pos_y, cos2yaw, sin2yaw, <shape features>].
The shape features default to a CLASS one-hot (3, the diag drivers) but the module takes feat_dim, so a
caller can condition on the OPEN-WORLD |F| shape-descriptor embedding instead (ShapeClassifier.desc_embed,
act23 GUI): the one-hot is a CLOSED-WORLD assumption (a novel shape has no slot), the descriptor exists
for any object -- the model can then generalise its action knowledge across forms it never saw.
Action: [dx, dy, cos2w, sin2w, grip, gentle]  -- a grasp-point OFFSET (m), the wrist as a mod-pi unit
vector, the claw CLOSE-ANGLE the grip holds at (0 = full close .. ~0.4 = wide, for concave objects that
squirt out under full squeeze) and a 0/1 GENTLE-carry flag (slow transport for off-COM grips).  grip +
gentle used to be hand-coded per-object runtime rules in act23 (body=='obj_U' -> 0.3/gentle); as action
dims the MODEL decides them from the perceived situation (stage-1 de-scripting, user's no-runtime-rules
principle).
"""
from __future__ import annotations

import os

import numpy as np

from pc_cvnn.pc_act19 import Policy
from .base import ArmModule

# ALIGNMENT CROSS-FEATURE (ACT23_WORLD_CROSS, default ON since the measured overnight run
# 2026-07-17: 600 L self-play episodes -> 177 fresh labels -> netz eval 27/40 = 67.5% vs 45%
# baseline at the 70% forced ceiling; internal control: aligned picks deliver 89%, non-aligned
# 48% = baseline, so the gain is the CONDITIONING, not state maturation.  =0 restores): append the
# rotation INVARIANTS cos2(w-yaw), sin2(w-yaw) -- derived from the PERCEIVED yaw dims (feats 2,3)
# and the model's OWN wrist action dims, nothing privileged -- to the joint input at fit/predict
# time.  WHY (measured, capacity probe 2026-07-16): the wrist->success rule for the L-form lives
# in exactly this bilinear term; the plain MLP needs ~3000 clean rows to find it among ~20 input
# dims, but WITH the invariant as an explicit input it learns at n~150 (the user's rotation=phase
# insight applied to action conditioning -- representation, not depth, was the bottleneck).
# Stored _X rows stay RAW (no schema break); members with a stale input width are rebuilt+refit
# from _X on the next train() (handles state pickles from before this feature / knob toggles).
CROSS = os.environ.get("ACT23_WORLD_CROSS", "1") == "1"
SHARP = os.environ.get("ACT23_WORLD_SHARP", "1") != "0"   # add |cos2(w-yaw)| (see cross_augment)
ARMREL = os.environ.get("ACT23_WORLD_ARMREL", "1") != "0"  # wrist vs ARM direction (see cross_augment)

# GRADED OUTCOME (see observe()): a delivery is scored by its distance instead of a flat 1.0.
# sigma = the confidence bar the credit routing uses (ACT23_WORLD_TOL, 25mm), so a placement AT the
# bar still counts clearly positive (0.37) while a bullseye counts ~1.0 -- the model can finally tell
# a precise action from a lucky one.  Curve: 0mm->1.00, 10mm->0.85, 15mm->0.70, 20mm->0.53, 25mm->0.37.
GRADED = os.environ.get("ACT23_WORLD_GRADED", "1") != "0"
QUAL_SIGMA = float(os.environ.get("ACT23_WORLD_QUAL_SIGMA", "0.025"))


def quality(dist_m):
    """Graded outcome in (0, 1] from a placement distance in metres (1.0 = dead on target)."""
    return float(np.exp(-(float(dist_m) / QUAL_SIGMA) ** 2))


# OBJECT-RELATIVE WRIST GRID (see candidates()): span the structured wrist candidates around the
# perceived object axis instead of around the world frame, so parallel/perpendicular grips are
# always representable.  ACT23_WRIST_REL=0 restores the absolute grid.
WRIST_REL = os.environ.get("ACT23_WRIST_REL", "1") != "0"


def cross_augment(X2d, fd):
    cy, sy = X2d[:, 2], X2d[:, 3]
    cw, sw = X2d[:, fd + 2], X2d[:, fd + 3]
    c = cw * cy + sw * sy                                  # cos2(w-yaw)  -- Re(z_w * conj(z_yaw))
    s = sw * cy - cw * sy                                  # sin2(w-yaw)  -- Im(...)
    cols = [X2d, c, s]
    if SHARP:
        # ALIGNMENT SHARPNESS |cos2(w-yaw)|: 1 when the claw is PARALLEL *or* PERPENDICULAR to the
        # object axis, 0 when it sits diagonally between them.  Measured (610-ep run 2026-07-27):
        # diagonal grasps (30-60deg) deliver 17% against 35% for aligned ones (p=0.015) -- the user
        # watched the claw "schraeg in die Zinken" grasp and the object slip out.  cos2 alone cannot
        # express this: it is +1 parallel, -1 perpendicular, 0 diagonal, so "good" is its MAGNITUDE,
        # a non-monotone function the MLP demonstrably did not extract -- a diagnosis on the stored
        # model showed the predicted quality varying only 0.038 over the WHOLE angle (6.3%) against
        # 0.289 for the grip mode alone, and even preferring 45deg.  Same medicine as the cross term
        # itself (comment above: with the invariant explicit it learns at n~150 instead of ~3000).
        # NOTE: sharpness says "aligned", not WHICH alignment -- the preferred direction is shape-
        # dependent and OPPOSITE between forms (U perpendicular 32% vs 13%, L parallel 56% vs 36%),
        # so the model still needs the shape features to pick the side.  ACT23_WORLD_SHARP=0 removes.
        cols.append(np.abs(c))
    if ARMREL:
        # GRIFFWINKEL RELATIV ZUR ARMRICHTUNG (User-Beobachtung 423-Ep-Lauf, Auto 351/370): "Objekt
        # weit weg, dadurch waere Wrist-Ausrichtung PARALLEL zum Workspace optimal gewesen; der Wrist
        # hat sich quer gedreht und dadurch rutscht der Griff weg."  Die Armbasis steht im Ursprung
        # (pc_act16 BASE_CLEAR misst |pos|), alpha = atan2(py, px) ist also die Richtung Base->Objekt
        # = die Armachse bei gestrecktem Arm.  cos(2a)/sin(2a) kommen ohne atan2 direkt aus den
        # Koordinaten: cos2a = (px^2-py^2)/r^2, sin2a = 2 px py / r^2.
        # Wie beim Objekt-Yaw ist die vollstaendige Beziehung das komplexe Produkt z_w * conj(z_alpha):
        #   cos2(w-a)  GERICHTET  (+1 parallel zur Armachse, -1 quer)  <- traegt die Beobachtung
        #   sin2(w-a)  orthogonale Komponente (vollstaendige Darstellung)
        #  |cos2(w-a)| Schaerfe (1 bei parallel ODER quer, 0 diagonal dazu)
        # DAZU der INTERAKTIONSTERM r*cos2(w-a): die Beobachtung ist DISTANZABHAENGIG ("weit weg"),
        # und genau dieses Produkt aus Distanz und Ausrichtung ist der bilineare Term, den das MLP
        # aus rohen Koordinaten nachweislich nicht bildet (siehe CROSS-Kommentar oben, n~150 statt
        # ~3000).  KEINE REGEL: nichts hiervon sagt, WELCHE Ausrichtung gut ist -- das Modell lernt
        # es aus seinen eigenen Outcomes.  ACT23_WORLD_ARMREL=0 entfernt die vier Spalten.
        px, py = X2d[:, 0], X2d[:, 1]
        r2 = np.maximum(px * px + py * py, 1e-12)
        ca, sa = (px * px - py * py) / r2, 2.0 * px * py / r2      # cos(2a), sin(2a)
        car = cw * ca + sw * sa                                    # cos2(w - alpha)
        sar = sw * ca - cw * sa                                    # sin2(w - alpha)
        cols += [car, sar, np.abs(car), np.sqrt(r2) * car]
    if TILT_ACTION and X2d.shape[1] >= fd + 8:
        # ABWEICHUNG der GEWUENSCHTEN Neigung von der KINEMATISCH ERZWUNGENEN, als komplexes
        # Produkt z_tilt * conj(z_kin) -> (cos d, sin d).  z_kin folgt aus dem Radius: gemessen
        # (2026-07-28, Reach-Controller ueber ein Positionsgitter) ist die erzwungene Neigung nahezu
        # exakt linear im Radius, Korrelation +1.00 -- 1 Grad bei 0.12m .. 45 Grad bei 0.27m, also
        # ~293 Grad/m ab ~0.117m.  Das ist eine KALIBRIERUNG dieses Arms, keine Regel: sie sagt nur,
        # welche Haltung der Arm hier von sich aus einnimmt, nicht welche gut ist.  Der Agent lernt
        # aus den Outcomes, ob es sich lohnt, davon abzuweichen (d nahe 0 = er nimmt die natuerliche
        # Haltung, |d| gross = er kaempft dagegen und zahlt mit Positionsfehler).
        ct, st_ = X2d[:, fd + 6], X2d[:, fd + 7]
        tk = np.clip((np.sqrt(r2) - TILT_R0) * np.radians(TILT_SLOPE), 0.0, np.pi / 2)
        ck, sk = np.cos(tk), np.sin(tk)
        cols += [ct * ck + st_ * sk, st_ * ck - ct * sk]       # cos(tilt-tk), sin(tilt-tk)
        if OPENING:
            # GREIFBARKEIT = wie FLACH die FINGER-OEFFNUNGSACHSE gegen die Arbeitsflaeche liegt.
            # User-Geometrie (2026-07-29): "So wie der Greifer aus seiner Ruheposition kommt, steht
            # die Oeffnung zwischen den zwei Fingern parallel zur Arbeitsflaeche.  Eine 90-Grad-
            # Drehung des Wrist stellt sie senkrecht -- aber nur, wenn der Arm sich weiter von der
            # Base weg bewegt.  Bei nahen Objekten greift er von oben, dann ist die Oeffnung bei
            # JEDEM Wrist-Drehwinkel fast parallel."
            # Hergeleitet: die Trennachse steht senkrecht auf der Klauenrichtung, also ist ihre
            # Neigung gegen die Horizontale  |arctan( tan(tilt) * cos(w - alpha) )|.  Das
            # reproduziert beide Aussagen exakt -- bei tilt=0 ist sie NULL fuer jeden Wrist, bei
            # gekippter Klaue maximal bei w=alpha und null bei 90 Grad dazu.
            # ENTSCHEIDEND, weil hier "greifbar" oder nicht entschieden wird: liegt die Oeffnung
            # schraeg, kommt "ein Finger von unten und einer von oben" (User) und ein flaches Objekt
            # auf dem Tisch ist nicht fassbar.  Das Modell kannte tilt und w bisher nur GETRENNT --
            # erst ihr Produkt bestimmt die Greifbarkeit, und claw_yaw() projiziert die Trennachse
            # auf die Tischebene und wirft genau diese Z-Komponente weg.
            # EINE Spalte genuegt: cos der Neigung = 1/sqrt(1 + (tan(tilt)*cos(w-a))^2), numerisch
            # stabil ohne arctan.  1 = Oeffnung waagerecht (greifbar), -> 0 = senkrecht.  Eine
            # Phasen-Darstellung waere hier REDUNDANT, denn die Neigung ist ein Betrag auf [0,90],
            # dort bestimmt der Cosinus den Sinus eindeutig.
            # ACHTUNG (Fehler im ersten Wurf, vom Sanity-Check gefangen): die Formel braucht
            # cos(w-alpha), NICHT das gespeicherte cos(2(w-alpha)) = car.  Da der Ausdruck ohnehin
            # quadriert wird, genuegt cos^2(w-a) = (1 + car)/2 -- das ist aus car exakt berechenbar
            # und umgeht, dass der Wrist nur mod pi bekannt ist (das Vorzeichen von cos(w-a) waere
            # unbestimmt, sein Quadrat nicht).
            tt = np.tan(np.clip(np.arctan2(st_, ct), 0.0, 1.45))       # tan(tilt), gegen 90 Grad geschuetzt
            cos2_rel = np.clip((1.0 + car) * 0.5, 0.0, 1.0)            # cos^2(w - alpha)
            cols.append(1.0 / np.sqrt(1.0 + (tt ** 2) * cos2_rel))
    return np.column_stack(cols)

FEAT_DIM = 7          # [pos(2), cos2yaw, sin2yaw, shape_onehot(3)]
# TILT = die ANFAHR-NEIGUNG der Klaue gegen die Senkrechte, als AKTION (ACT23_TILT_ACTION).
# WARUM (User-Beobachtung 423-Ep-Lauf + Messung 2026-07-28): dir_ref stand FEST auf senkrecht
# (0,0,-1), und bei grossem Radius ist das kinematisch unerreichbar -- die Klaue kippt zwangslaeufig
# (gemessen, Korrelation +1.00: 1 Grad bei r=0.12m, 25 bei 0.21, 45 bei 0.27).  Dann kommt "ein
# Finger von unten und einer von oben" (User) und der Griff scheitert.  Das Gewicht hochzudrehen
# erzwingt zwar die Senkrechte, kostet aber die Position (WDIR 0.4 -> 53mm Reach-Fehler), ist also
# kein Weg.  Stattdessen wird das ZIEL waehlbar: waehlt der Agent eine Neigung, die bei diesem
# Radius ohnehin erreichbar ist, entfaellt der Konflikt und er bekommt die Haltung OHNE
# Positionsverlust.  Er erleidet die Neigung nicht mehr, sondern waehlt sie.
# ALS PHASE kodiert (User-Wunsch, konsistent zum Wrist und zur RoPE-Linie des Projekts):
# z_tilt = e^{i*tilt} -> (cos tilt, sin tilt).  Anders als der Wrist ist die Neigung NICHT mod pi
# (30 Grad nach aussen ist nicht dasselbe wie 30 nach innen), daher die volle Phase statt 2*Winkel.
# ANGEHAENGT statt eingefuegt, damit bestehende Zeilen migrierbar bleiben: alte Zeilen bekommen
# (1,0) = 0 Grad = exakt das bisherige Verhalten.  ACT23_TILT_ACTION=0 schaltet die Dimension ab.
TILT_ACTION = os.environ.get("ACT23_TILT_ACTION", "1") != "0"
TILT_MAX = float(os.environ.get("ACT23_TILT_MAX", "55"))     # Grad, Obergrenze des Kandidatengitters
TILT_GRID = int(os.environ.get("ACT23_TILT_GRID", "4"))      # Stufen (nur ohne Radius-Info)
TILT_OFFSETS = [float(x) for x in os.environ.get("ACT23_TILT_OFFSETS", "-12,0,12,25").split(",")]
TILT_NOV = os.environ.get("ACT23_TILT_NOVELTY", "dichte")   # "dichte" | "sigma" (s. tilt_novelty)
TILT_VETO_N = int(os.environ.get("ACT23_TILT_VETO_N", "8"))       # ab so vielen Zeilen gilt eine Zelle
TILT_VETO_Q = float(os.environ.get("ACT23_TILT_VETO_Q", "0.35"))  # als belegt; darunter = belegt schlecht
T_EDGES = np.array([0, 8, 16, 24, 32, 40, 48, 90.1])       # Neigungs-Bins in Grad
R_EDGES = np.array([0.0, 0.16, 0.21, 9.9])                 # Radius-Bins in Metern
TILT_CURIOSITY = float(os.environ.get("ACT23_TILT_CURIOSITY", "0"))   # Anteil Neugier-Zuege.
#   AUF 0 GESETZT (2026-07-31): die Frage ist beantwortet.  Mit 249 gekippten Zeilen sagen die Daten
#   eindeutig, dass Neigen SCHLECHTER liefert (ferne Objekte: Guete 0.66 senkrecht vs 0.42 geneigt,
#   p<0.0001), und das Modell hat das gelernt.  Die Exploration kostete nur noch: Lauf mit 22%
#   Exploration lieferte 45%, mit 48% nur 36% (p=0.033).  Die Aktionsdimension bleibt -- das Modell
#   waehlt jetzt von sich aus ueberwiegend die Senkrechte.  >0 nimmt die Erkundung wieder auf.
#   Kurze Geschichte dieses Reglers, damit er nicht wieder falsch gedreht wird: er stand auf 0.35,
#   wurde auf 0.6 erhoeht, weil der 0-Grad-Anteil trotz der SLACK-Korrektur bei 75% klebte -- die
#   Diagnose zeigte dann aber, dass nicht die RATE band, sondern erst die MARGIN-Bedingung (sigma
#   differenzierte die Neigungen nicht) und danach die mu-Schranke (sie sperrte alles Unerprobte
#   aus).  Beide sind mit dd99215 behoben (Dichte-Neuheit + datenbasiertes Veto).  Seither GREIFT
#   die Neugier wirklich, und 0.6 hiesse: 60% aller Griffe explorieren.  Zurueck auf 0.35, weil die
#   Erhoehung nur eine Kompensation fuer den defekten Mechanismus war.
TILT_CUR_MARGIN = float(os.environ.get("ACT23_TILT_CUR_MARGIN", "1.2"))  # nur wenn deutlich unsicherer
OPENING = os.environ.get("ACT23_WORLD_OPENING", "1") != "0"   # Greifbarkeit der Fingeroeffnung
TILT_CUR_SLACK = float(os.environ.get("ACT23_TILT_CUR_SLACK", "0.25"))  # erlaubter Guete-Rueckstand
#   eines Neugier-Kandidaten gegenueber der besten Neigung (Plausibilitaets-Schranke, s. select_action).
#   0.10 war ZU ENG (gemessen 165-Ep-Lauf 2026-07-29): weil 0 Grad die mit Abstand meisten Daten hat,
#   sieht es fast immer am besten aus, und bei 0.10 fielen die Alternativen durch die Schranke -- die
#   erzwungene Senkrechte STIEG bei fernen Objekten von 50% auf 75%, der Abstand zur natuerlichen
#   Haltung wuchs 25.5 -> 30.0 Grad.  Die Schranke sollte nur die SCHAEDLICHEN Raender abschneiden
#   (>45 Grad, dort 0% Lieferung), nicht die mittlere Exploration, in der die natuerliche Haltung liegt.
#   Grad RELATIV zur natuerlichen Neigung; 0 = die kostenlose Haltung, negativ = gegen die Kinematik
TILT_R0 = float(os.environ.get("ACT23_TILT_R0", "0.117"))    # Radius, ab dem die Klaue zu kippen beginnt
TILT_SLOPE = float(os.environ.get("ACT23_TILT_SLOPE", "293"))  # Grad pro Meter (gemessen, s. cross_augment)
ACT_DIM = 8 if TILT_ACTION else 6     # [dx, dy, cos2w, sin2w, grip, gentle] (+ cos_tilt, sin_tilt)
GRIP_MODES = ((0.0, 0.0), (0.3, 1.0))   # structured grip regimes in the candidate grid: firm full-close
#   vs wide-hold + gentle carry (the regime a concave object needs) -- like the offset-0 wrist grid this
#   only makes the regimes REPRESENTABLE; the model decides which one wins by predicted success.
SHAPE_ID = {"cube": 0, "L": 1, "U": 2}


def feats_from(sel, shape):
    """Build the perceived situation feature vector from a ShapeClassifier detection."""
    pos = np.asarray(sel["pos"], float)
    yaw = float(sel.get("yaw", 0.0) or 0.0)
    oh = np.zeros(3); oh[SHAPE_ID[shape]] = 1.0
    return np.concatenate([pos, [np.cos(2 * yaw), np.sin(2 * yaw)], oh])


def action_vec(dx, dy, w, grip=0.0, gentle=0.0, tilt=0.0):
    """Action vector; `tilt` = desired claw tilt off vertical (rad), carried as the phase
    (cos tilt, sin tilt) when TILT_ACTION is on (see the block above)."""
    a = [dx, dy, np.cos(2 * w), np.sin(2 * w), float(grip), float(gentle)]
    if TILT_ACTION:
        a += [np.cos(float(tilt)), np.sin(float(tilt))]
    return np.array(a, float)


def tilt_of(a):
    """Decode the desired claw tilt (rad, >=0) from an action; 0 when the dimension is off."""
    a = np.asarray(a, float).ravel()
    if not TILT_ACTION or a.size < 8:
        return 0.0
    return float(np.arctan2(a[7], a[6]))


def wrist_of(a):
    """Decode the wrist angle (rad, mod pi) from an action's (cos2w, sin2w)."""
    return 0.5 * np.arctan2(a[3], a[2])


class WorldModelModule(ArmModule):
    """Ensemble outcome model P(deliver | feats, action) with uncertainty-aware action selection."""

    def __init__(self, k=5, hid=64, off_max=0.012, wrist_grid=8, rng=None, name="WorldModel", feat_dim=FEAT_DIM):
        super().__init__(name)
        self.rng = rng or np.random.default_rng(0)
        self.off_max = float(off_max)
        self.wrist_grid = int(wrist_grid)
        self.feat_dim = int(feat_dim)                # situation size: 4 + one-hot(3) OR 4 + descriptor embedding
        self.members = [Policy(din=self.feat_dim + ACT_DIM, dout=1, hid=hid,
                               rng=np.random.default_rng(int(self.rng.integers(1 << 30))))
                        for _ in range(int(k))]
        self._X: list[np.ndarray] = []
        self._Y: list[list[float]] = []
        (self.add_in("situation", self.feat_dim, "perceived [pos, cos2yaw, sin2yaw, shape features]")
             .add_in("action", ACT_DIM, "[dx, dy, cos2w, sin2w, grip, gentle]")
             .add_out("p_success", 1, "ensemble-mean predicted delivery prob")
             .add_out("uncertainty", 1, "ensemble-std (epistemic)"))

    # -- self-supervised data --
    def observe(self, feats, action, delivered, dist=None, weight=1.0):
        """One outcome for (situation, action).  `dist` = the SELF-JUDGED placement distance (m).

        GRADED LABEL (the user's idea, 2026-07-25): with `dist` a SUCCESS is scored by HOW WELL it
        landed instead of a flat 1.0 -- quality() below.  The members are MSE regressors on a scalar
        target, so this needs no architecture change; it only stops throwing away the difference
        between a 5mm and a 24mm placement, which is exactly the information the wrist/grip choice
        needs (which action places PRECISELY, not merely "somewhere near").

        Measured motivation (120-ep run): the self-judge tracks the true distance almost perfectly
        (r=0.98, median bias +0mm), so `dist` is trustworthy -- yet every success collapsed onto the
        same 1.0.  FAILURES stay a hard 0.0: the credit routing already decides WHETHER an outcome
        is the action's fault, and softening negatives would blunt exactly the falsifying signal a
        bad grip geometry needs.  So: the routing decides IF, the distance decides HOW MUCH.
        ACT23_WORLD_GRADED=0 restores flat 0/1 labels.

        NOTE on the existing buffer: rows logged before this are flat 0/1.  They stay valid (0 and 1
        are the endpoints of the same scale), but old successes read as "perfect"; the bias dilutes
        as graded rows accumulate."""
        if GRADED and dist is not None and delivered:
            y = quality(dist)
        else:
            y = float(delivered)
        self._X.append(np.concatenate([np.asarray(feats, float), np.asarray(action, float)]))
        self._Y.append([y])
        self._weights(len(self._X) - 1).append(float(weight))

    def _weights(self, upto):
        """Per-row fit weight, padded to `upto` entries with 1.0 -- migrates pre-weight pickles."""
        if getattr(self, "_W", None) is None:
            self._W = []
        while len(self._W) < upto:
            self._W.append(1.0)
        return self._W

    def n(self):
        return len(self._X)

    def tilt_novelty(self, tilts_deg, r):
        """NEUHEIT einer Neigung = wie wenig Erfahrung in dieser (Neigung, Radius)-Zelle steckt.

        WARUM NICHT Ensemble-sigma (gemessen 2026-07-30): sigma misst, wie UNEINIG die Member sind.
        Fuer eine NEUE Aktionsdimension funktioniert das nicht -- bei 144 gekippten gegen ~3800
        senkrechte Zeilen sind sich die Member schlicht einig, egal welche Neigung, das
        sigma-Verhaeltnis lag im Median bei 1.00 und die Neugier wurde in 137 von 200 Faellen
        abgewiesen.  Ein Henne-Ei, das keine Reglerstellung aufloest: ohne Daten kein sigma-Kontrast,
        ohne sigma-Kontrast keine Exploration, ohne Exploration keine Daten.
        DATENDICHTE ist davon unabhaengig -- sie misst direkt, wo der Agent noch nicht war.  Das ist
        dasselbe Prinzip wie DistanceNovelty (das im Projekt schon die OBJEKTwahl steuert), nur auf
        einem Histogramm statt auf kNN, weil der Raum hier zweidimensional und klein ist.
        (Neigung, Radius) genuegt als Raum: die Neigung wirkt ueber den Radius (die natuerliche
        Haltung ist eine Funktion von r), Form und Objektwinkel bleiben bewusst draussen -- sonst
        waeren die Zellen bei 3800 Zeilen durchweg leer und die Neuheit truege keine Information.
        """
        H = self._tilt_hist()
        ri = int(np.clip(np.searchsorted(R_EDGES, float(r), side="right") - 1, 0, len(R_EDGES) - 2))
        out = []
        for td in np.atleast_1d(tilts_deg):
            ti = int(np.clip(np.searchsorted(T_EDGES, float(td), side="right") - 1, 0, len(T_EDGES) - 2))
            out.append(1.0 / (1.0 + float(H[ti, ri])))
        return np.asarray(out, float)

    def tilt_veto(self, tilts_deg, r):
        """True fuer Neigungen, die MIT DATEN belegt schlecht sind (nicht bloss vom Modell vermutet).

        WARUM NICHT die mu-Schranke (gemessen 2026-07-30): das Modell haelt JEDE unerprobte Neigung
        fuer deutlich schlechter -- Gueterueckstand median 0.63 -- weil es aus den 0-Grad-Daten glatt
        extrapoliert.  Eine Schranke auf mu vertraut dieser Extrapolation und sperrt damit genau das
        aus, was die Neugier erkunden soll: in 123 von 200 fernen Situationen blieb nach der Schranke
        NUR 0 Grad uebrig.  mu-Veto und Dichte-Neuheit arbeiten gegeneinander.
        Datenbasiert loest sich der Konflikt: eine Zelle wird nur verworfen, wenn sie GENUG Zeilen
        hat UND diese im Mittel schlecht ausgingen.  Unerprobtes bleibt erlaubt (das ist der Zweck),
        belegt Schlechtes -- der Rand >45 Grad mit 0-25% Lieferung -- fliegt raus."""
        H, L = self._tilt_hist(), self._tilt_labels()
        ri = int(np.clip(np.searchsorted(R_EDGES, float(r), side="right") - 1, 0, len(R_EDGES) - 2))
        out = []
        for td in np.atleast_1d(tilts_deg):
            ti = int(np.clip(np.searchsorted(T_EDGES, float(td), side="right") - 1, 0, len(T_EDGES) - 2))
            n = float(H[ti, ri])
            out.append(bool(n >= TILT_VETO_N and (L[ti, ri] / max(n, 1.0)) < TILT_VETO_Q))
        return np.asarray(out, bool)

    def _tilt_labels(self):
        """Summe der Outcome-Labels je (Neigung x Radius)-Zelle -- Zaehler fuer die mittlere Guete."""
        self._tilt_hist()                                  # fuellt/aktualisiert den Cache mit
        return self._lsum

    def _tilt_hist(self):
        """(Neigung x Radius)-Histogramm der gespeicherten Zeilen; neu gerechnet, wenn Zeilen dazukamen."""
        n = len(self._X)
        if getattr(self, "_hist_n", -1) == n and getattr(self, "_hist", None) is not None:
            return self._hist
        H = np.zeros((len(T_EDGES) - 1, len(R_EDGES) - 1))
        L = np.zeros_like(H)
        if n:
            X = np.array(self._X)
            if X.shape[1] >= self.feat_dim + 8:
                t = np.degrees(np.arctan2(X[:, self.feat_dim + 7], X[:, self.feat_dim + 6]))
                r = np.hypot(X[:, 0], X[:, 1])
                H, _, _ = np.histogram2d(t, r, bins=[T_EDGES, R_EDGES])
                L, _, _ = np.histogram2d(t, r, bins=[T_EDGES, R_EDGES],
                                         weights=np.array(self._Y, float).ravel())
        self._hist, self._lsum, self._hist_n = H, L, n
        return H

    @staticmethod
    def natural_tilt(r):
        """Die Neigung, die der Reach-Controller bei diesem Radius von sich aus einnimmt (rad).
        Kalibrierung s. cross_augment; das ist eine EIGENSCHAFT DES ARMS, keine Bewertung."""
        return float(np.clip((float(r) - TILT_R0) * np.radians(TILT_SLOPE), 0.0, np.pi / 2))

    @staticmethod
    def radius_of(feats):
        """Abstand des Objekts von der Armbasis (Ursprung) aus den Situations-Features."""
        f = np.asarray(feats, float).ravel()
        return float(np.hypot(f[0], f[1])) if f.size >= 2 else None

    @staticmethod
    def yaw_of(feats):
        """Recover the perceived object axis (rad, mod pi) from the situation features' (cos2yaw,
        sin2yaw) pair -- so callers that already hold `feats` need not carry the yaw separately."""
        f = np.asarray(feats, float).ravel()
        if f.size < 4:
            return None
        return 0.5 * float(np.arctan2(f[3], f[2]))

    def _migrate_tilt(self):
        """Pad rows logged before the tilt dims with (cos0, sin0) = (1,0) = 0 deg = the old behaviour."""
        if not TILT_ACTION or not self._X:
            return
        want = self.feat_dim + ACT_DIM
        for i, r in enumerate(self._X):
            if len(r) == want - 2:
                self._X[i] = np.concatenate([np.asarray(r, float), [1.0, 0.0]])

    def train(self, epochs=500):
        if not self._X:
            return
        self._migrate_tilt()
        X = np.array(self._X); Y = np.array(self._Y); m = len(X)
        if CROSS:
            X = cross_augment(X, self.feat_dim)
        if self.members[0].W1.shape[1] != X.shape[1]:  # knob toggled / pre-cross pickle: rebuild
            self.members = [Policy(din=X.shape[1], dout=1, hid=64,
                                   rng=np.random.default_rng(int(self.rng.integers(1 << 30))))
                            for _ in self.members]
        W = np.asarray(self._weights(m), float)
        for member in self.members:
            idx = self.rng.integers(0, m, m)          # bootstrap resample -> ensemble diversity
            member.fit(X[idx], Y[idx], epochs=epochs, quiet=True,
                       w=(W[idx] if not np.allclose(W, 1.0) else None))

    # -- prediction with uncertainty --
    def predict(self, feats, actions):
        """actions: (N, ACT_DIM) -> (mu (N,), sigma (N,)) over the ensemble."""
        actions = np.atleast_2d(actions)
        X = np.column_stack([np.tile(np.asarray(feats, float), (len(actions), 1)), actions])
        if CROSS:
            Xc = cross_augment(X, self.feat_dim)
            if self.members[0].W1.shape[1] == Xc.shape[1]:
                X = Xc                                # members not yet rebuilt -> raw until train()
        if self.members[0].W1.shape[1] != X.shape[1] and self._X:
            self.train(epochs=300)                    # pickle from the OTHER knob setting: one lazy
            return self.predict(feats, actions)       #   rebuild+refit, then answer normally
        P = np.array([[float(member.predict(x)[0]) for x in X] for member in self.members])  # (K, N)
        return P.mean(0), P.std(0)

    def candidates(self, n, offsets=None, yaw=None, r=None):
        """Structured GRID (offset-0 wrists x grip regimes, so teacher-like actions are always
        representable) + n random (offset, wrist, grip, gentle) samples.  `offsets` = optional
        PERCEPTION-GROUNDED grasp-point candidates (dx,dy relative to the heuristic point, e.g.
        sampled from the perceived material mask): each is crossed with the wrist x grip grid, so
        the model SCORES real places on the object instead of blind random nudges -- the user's
        self-discovered-grasp-points goal.  The offset-0 grid always stays in the set (the
        heuristic point remains the prior, and untrained models keep returning it).

        `yaw` = the PERCEIVED object axis (rad).  With it the wrist grid is spanned RELATIVE to the
        object, so gripping PARALLEL and PERPENDICULAR to its axis are always in the candidate set.

        WHY (measured, 610-ep run 2026-07-27): the grid used to be 8 ABSOLUTE world angles, and 100%
        of chosen wrists sat exactly on it -- the random candidates never won.  Since the object yaw
        is arbitrary, the RELATIVE angle was therefore not freely selectable and 27% of grasps landed
        in the 30-60deg "diagonal" band, which delivers 17% against 35% for aligned grasps (p=0.015;
        the user watched exactly this: "greift schraeg in die Zinken und das Objekt rutscht heraus").
        The preferred alignment is SHAPE-dependent and opposite between forms (U better perpendicular
        32% vs 13%, L better parallel 56% vs 36%), so this does NOT hard-code an angle: it only makes
        both alignments REPRESENTABLE -- the model still decides which wins by predicted success,
        exactly as GRIP_MODES above.  ACT23_WRIST_REL=0 restores the absolute grid."""
        w0 = float(yaw) if (yaw is not None and WRIST_REL) else 0.0
        grid = w0 + np.linspace(0, np.pi, self.wrist_grid, endpoint=False)
        if not TILT_ACTION:
            tilts = np.array([0.0])
        elif r is None:
            tilts = np.radians(np.linspace(0.0, TILT_MAX, TILT_GRID))
        else:
            # RELATIV zur natuerlichen Haltung (dieselbe Lehre wie beim objekt-relativen Wrist-Gitter,
            # 45fa0a4): ein festes Winkelgitter verfehlt die kinematisch erzwungene Neigung um bis zu
            # 9 Grad, weil diese stetig mit dem Radius waechst.  Relativ aufgespannt ist die
            # natuerliche Haltung IMMER exakt waehlbar (Offset 0, kostet keine Position), dazu das
            # Erzwingen der Senkrechten (0 absolut) und Abweichungen nach beiden Seiten.
            tk = self.natural_tilt(r)
            tilts = np.clip(np.concatenate([[0.0], tk + np.radians(TILT_OFFSETS)]),
                            0.0, np.radians(TILT_MAX))
            tilts = np.unique(np.round(tilts, 4))
        A = [action_vec(0.0, 0.0, w, g, ge, t)
             for w in grid
             for g, ge in GRIP_MODES
             for t in tilts]
        if offsets is not None:
            A += [action_vec(float(o[0]), float(o[1]), w, g, ge, t)
                  for o in offsets if float(np.linalg.norm(np.asarray(o, float))) > 1e-9
                  for w in grid
                  for g, ge in GRIP_MODES
                  for t in tilts]
        for _ in range(int(n)):
            dx, dy = self.rng.uniform(-self.off_max, self.off_max, 2)
            A.append(action_vec(dx, dy, self.rng.uniform(0, np.pi),
                                grip=self.rng.uniform(0.0, 0.4), gentle=float(self.rng.integers(2)),
                                tilt=(self.rng.uniform(0.0, np.radians(TILT_MAX)) if TILT_ACTION else 0.0)))
        return np.array(A)

    def select_action(self, feats, n=40, lam=1.0, offsets=None, curiosity=0.0, rng=None):
        """Uncertainty-aware (LCB) action: argmax (mu - lam*sigma) over the candidate set.
        Returns (action, mu, sigma).  Untrained -> the offset-0 / wrist-0 default.
        The object axis is READ BACK from the situation features (cos2yaw, sin2yaw) and passed to
        candidates(), so the wrist grid is object-relative without changing this method's callers."""
        A = self.candidates(n, offsets=offsets, yaw=self.yaw_of(feats), r=self.radius_of(feats))
        if self.n() == 0:
            return A[0], 0.0, 0.0
        mu, sd = self.predict(feats, A)
        i = int(np.argmax(mu - lam * sd))
        if TILT_ACTION and curiosity > 0.0:
            # NEUGIER AUF DER NEIGUNGS-ACHSE.  Das Problem (gemessen im Rauchtest): die LCB-Wahl
            # mu - lam*sigma BESTRAFT Unsicherheit, und die neue Tilt-Dimension hat anfangs 3386
            # Zeilen bei 0 Grad gegen ~0 bei allen anderen -- also gewinnt 0 Grad immer und die
            # Dimension wird nie erprobt (Henne-Ei).  Hier greift dasselbe Neuheitsmass, das die
            # Objektwahl schon benutzt (dort: sd.max() als Curiosity-Score): unter den Kandidaten,
            # die sich NUR in der Neigung unterscheiden, wird die UNSICHERSTE gewaehlt.
            # CHIRURGISCH: Wrist/Grip/Offset bleiben bei der LCB-besten Wahl, nur die Neigung wird
            # erkundet -- ein schlechter Wrist wuerde die Episode ruinieren, eine ungewohnte Neigung
            # kostet im schlimmsten Fall diesen einen Griff.
            # SELBST-LIMITIEREND: nur wenn die unsicherste Variante DEUTLICH unsicherer ist
            # (TILT_CUR_MARGIN).  Sind die Neigungen erprobt, gleicht sich sigma an und die
            # Neugier verstummt von selbst -- kein Abkling-Zeitplan noetig.
            _rng = rng if rng is not None else self.rng
            if float(_rng.random()) < curiosity:
                base = A[i]
                same = np.array([j for j in range(len(A))
                                 if np.allclose(A[j][:6], base[:6], atol=1e-9)], dtype=int)
                if same.size > 1:
                    # PLAUSIBILITAETS-SCHRANKE (gemessen 214-Ep-Lauf 2026-07-28): reine
                    # Unsicherheits-Maximierung geht systematisch an den RAND des Bereichs, denn dort
                    # war noch nie jemand -- alle 8 Griffe am Oberrand (>=54 Grad) waren fern und ALLE
                    # gescheitert, der Block >45 Grad lieferte 0% (n=12).  Die Neugier verbrannte also
                    # Griffe dort, wo das Modell bereits WEISS, dass es schlecht ist.  Jetzt wird nur
                    # unter den PLAUSIBLEN Varianten erkundet: deren vorhergesagte Guete darf hoechstens
                    # TILT_CUR_SLACK unter der besten liegen.  Das ist optimistische Exploration statt
                    # blinder Neugier -- erkundet wird, wo das Modell UNSICHER ist, nicht wo es sicher
                    # ablehnt.  Bleibt selbst-limitierend (TILT_CUR_MARGIN).
                    mu_s = mu[same]
                    ok = same[mu_s >= float(mu_s.max()) - TILT_CUR_SLACK]
                    if ok.size:
                        if TILT_NOV == "dichte" and feats is not None:
                            rr = self.radius_of(feats)
                            # DATENBASIERTES VETO statt mu-Schranke (s. tilt_veto)
                            td_all = np.degrees([tilt_of(A[k]) for k in same])
                            keep = ~self.tilt_veto(td_all, rr if rr is not None else 0.0)
                            ok = same[keep] if keep.any() else same
                            td = np.degrees([tilt_of(A[k]) for k in ok])
                            score = self.tilt_novelty(td, rr if rr is not None else 0.0)
                            base = float(self.tilt_novelty(
                                [np.degrees(tilt_of(A[i]))], rr if rr is not None else 0.0)[0])
                        else:
                            score, base = sd[ok], float(sd[i])
                        j = int(ok[int(np.argmax(score))])
                        if float(np.max(score)) > TILT_CUR_MARGIN * base:
                            i = j
        return A[i], float(mu[i]), float(sd[i])

    def step(self) -> None:
        s = self.get_in("situation"); a = self.get_in("action")
        if s is not None and a is not None and self.n() > 0:
            mu, sd = self.predict(s, np.atleast_2d(a))
            self.set_out("p_success", mu[:1]); self.set_out("uncertainty", sd[:1])
