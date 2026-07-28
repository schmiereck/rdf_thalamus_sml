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
    return np.column_stack(cols)

FEAT_DIM = 7          # [pos(2), cos2yaw, sin2yaw, shape_onehot(3)]
ACT_DIM = 6           # [dx, dy, cos2w, sin2w, grip, gentle]
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


def action_vec(dx, dy, w, grip=0.0, gentle=0.0):
    return np.array([dx, dy, np.cos(2 * w), np.sin(2 * w), float(grip), float(gentle)], float)


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

    @staticmethod
    def yaw_of(feats):
        """Recover the perceived object axis (rad, mod pi) from the situation features' (cos2yaw,
        sin2yaw) pair -- so callers that already hold `feats` need not carry the yaw separately."""
        f = np.asarray(feats, float).ravel()
        if f.size < 4:
            return None
        return 0.5 * float(np.arctan2(f[3], f[2]))

    def train(self, epochs=500):
        if not self._X:
            return
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

    def candidates(self, n, offsets=None, yaw=None):
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
        A = [action_vec(0.0, 0.0, w, g, ge)
             for w in grid
             for g, ge in GRIP_MODES]
        if offsets is not None:
            A += [action_vec(float(o[0]), float(o[1]), w, g, ge)
                  for o in offsets if float(np.linalg.norm(np.asarray(o, float))) > 1e-9
                  for w in grid
                  for g, ge in GRIP_MODES]
        for _ in range(int(n)):
            dx, dy = self.rng.uniform(-self.off_max, self.off_max, 2)
            A.append(action_vec(dx, dy, self.rng.uniform(0, np.pi),
                                grip=self.rng.uniform(0.0, 0.4), gentle=float(self.rng.integers(2))))
        return np.array(A)

    def select_action(self, feats, n=40, lam=1.0, offsets=None):
        """Uncertainty-aware (LCB) action: argmax (mu - lam*sigma) over the candidate set.
        Returns (action, mu, sigma).  Untrained -> the offset-0 / wrist-0 default.
        The object axis is READ BACK from the situation features (cos2yaw, sin2yaw) and passed to
        candidates(), so the wrist grid is object-relative without changing this method's callers."""
        A = self.candidates(n, offsets=offsets, yaw=self.yaw_of(feats))
        if self.n() == 0:
            return A[0], 0.0, 0.0
        mu, sd = self.predict(feats, A)
        i = int(np.argmax(mu - lam * sd))
        return A[i], float(mu[i]), float(sd[i])

    def step(self) -> None:
        s = self.get_in("situation"); a = self.get_in("action")
        if s is not None and a is not None and self.n() > 0:
            mu, sd = self.predict(s, np.atleast_2d(a))
            self.set_out("p_success", mu[:1]); self.set_out("uncertainty", sd[:1])
