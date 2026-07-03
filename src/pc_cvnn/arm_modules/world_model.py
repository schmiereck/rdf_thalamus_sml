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

import numpy as np

from pc_cvnn.pc_act19 import Policy
from .base import ArmModule

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
    def observe(self, feats, action, delivered):
        self._X.append(np.concatenate([np.asarray(feats, float), np.asarray(action, float)]))
        self._Y.append([float(delivered)])

    def n(self):
        return len(self._X)

    def train(self, epochs=500):
        if not self._X:
            return
        X = np.array(self._X); Y = np.array(self._Y); m = len(X)
        for member in self.members:
            idx = self.rng.integers(0, m, m)          # bootstrap resample -> ensemble diversity
            member.fit(X[idx], Y[idx], epochs=epochs, quiet=True)

    # -- prediction with uncertainty --
    def predict(self, feats, actions):
        """actions: (N, ACT_DIM) -> (mu (N,), sigma (N,)) over the ensemble."""
        actions = np.atleast_2d(actions)
        X = np.column_stack([np.tile(np.asarray(feats, float), (len(actions), 1)), actions])
        P = np.array([[float(member.predict(x)[0]) for x in X] for member in self.members])  # (K, N)
        return P.mean(0), P.std(0)

    def candidates(self, n):
        """Structured GRID (offset-0 wrists x grip regimes, so teacher-like actions are always
        representable) + n random (offset, wrist, grip, gentle) samples."""
        A = [action_vec(0.0, 0.0, w, g, ge)
             for w in np.linspace(0, np.pi, self.wrist_grid, endpoint=False)
             for g, ge in GRIP_MODES]
        for _ in range(int(n)):
            dx, dy = self.rng.uniform(-self.off_max, self.off_max, 2)
            A.append(action_vec(dx, dy, self.rng.uniform(0, np.pi),
                                grip=self.rng.uniform(0.0, 0.4), gentle=float(self.rng.integers(2))))
        return np.array(A)

    def select_action(self, feats, n=40, lam=1.0):
        """Uncertainty-aware (LCB) action: argmax (mu - lam*sigma) over the candidate set.
        Returns (action, mu, sigma).  Untrained -> the offset-0 / wrist-0 default."""
        A = self.candidates(n)
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
