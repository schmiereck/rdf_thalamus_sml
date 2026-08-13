"""RuntimePolicyModule — STAGE 2 de-scripting: a LEARNED action policy replaces the scripted
choreography at runtime (the act19 pattern, wired lifelong into act23).

The policy is a small MLP  state(11) -> sub-goal(4) = [aim_xyz, gripper]  (pc_act19.Policy).  It
learns by DAgger from the MARKOVIAN reactive teacher: every state the arm actually VISITS -- no
matter whether the scripted FSM or the policy itself is driving -- gets labelled with
act16.reactive_subgoal(state) and aggregated here.  (act19 lesson: labels from the STATEFUL phase
machine degrade DAgger -- its hidden phase makes the mapping state->label inconsistent; the
reactive teacher is a pure function of state.)  The scripted choreography thus degrades to a
TRAINING teacher (the user's principle: scripting only in training); at runtime the NET decides
the sub-goals, including WHEN the gripper closes (verify with ACT16_CLOSE_GUARD=0 ACT16_REFLEX=0).

Ports
  in  : policy_state (11)  [hand xyz, obj xy, obj z, target xy, gripper, obj_h, obj_fp]
  out : subgoal      (4)   [aim_xyz, gripper]
"""
from __future__ import annotations

import numpy as np

from pc_cvnn.pc_act19 import Policy
from .base import ArmModule

CAP = 24000            # FIFO sample cap: newest ~50 episodes; enough for the teacher manifold,
#                        bounded refit cost (the buffer is refit lifelong after episodes)
SUBSAMPLE = 2          # keep every 2nd visited step (neighbouring steps are near-duplicates)
CORE = 8000            # the FIRST samples (teacher-driven demos) are PROTECTED from FIFO eviction:
#                        during long policy-driven (DAgger) stretches every episode FAILS at first, so a
#                        plain FIFO would wash the happy-path demos out of the buffer and the policy
#                        would forget the path it never visits (act19 anchored on the demos for the
#                        same reason).  Eviction only applies beyond the core.
IMIT_CAP = 12000       # SELF-IMITATION buffer (step 3): the (state, action) pairs the POLICY ITSELF
#                        drove on episodes the agent SELF-JUDGED a success -- reinforcement of what
#                        worked FOR IT, blended with the DAgger teacher labels at fit time.
IMIT_WEIGHT = int(__import__("os").environ.get("ACT23_SELFIMIT_W", "2"))   # how many times a self-
#                        imitation pair is repeated vs a DAgger sample (own validated successes count
#                        more; the teacher is training wheels, the baby's own working moves lead)
GRADED_IMIT = __import__("os").environ.get("ACT23_IMIT_GRADED", "1") != "0"   # weight each self-imitation
#                        demo by the episode's placement QUALITY instead of a flat in/out bar (see train)
_IMIT_BAL = __import__("os").environ.get("ACT23_IMIT_BAL", "0") == "1"     # per-key balanced imitation
#                        mass at fit time (see train).  DEFAULT OFF (measured, U/cube alternation
#                        ablations): the success-protection gate (end_episode) alone keeps the rare
#                        skill alive (U 7/20 vs 2/20) at LESS majority cost (cube 12/20 vs 9/20 with
#                        balancing on) -- the extra mass shift buys no provable minority gain.
SANE_M = 1.0           # POSITION SANITY BOUND (m): the hand/object/target all live on a <=0.3 m table,
#                        so any coord beyond 1 m is a PERCEPTION GLITCH, never a real state.  A grasp-
#                        belief servo fed px-as-metres (the 897ca5a bug) drove obj coords to ~50-176 m;
#                        DAgger logged those and a quarter of the buffer went absurd, wrecking the policy.
#                        Guard the buffer at the source + a load-time sanitize heal the damage.
_POS_COLS = (0, 1, 2, 3, 4, 6, 7)   # hand xyz, obj xy, target xy (cz/j5/obj_h/obj_fp are not positions)


class RuntimePolicyModule(ArmModule):
    def __init__(self, name: str = "RuntimePolicy", rng=None) -> None:
        super().__init__(name)
        self.net = Policy(rng=rng or np.random.default_rng(4))
        self._X: list[np.ndarray] = []
        self._Y: list[np.ndarray] = []
        self._Xi: list[np.ndarray] = []               # self-imitation buffer (own self-judged successes)
        self._Yi: list[np.ndarray] = []
        self._k = 0                                   # subsample counter
        self.trained = False
        self._div: list[float] = []                   # shadow |aim_pred - aim_teacher| (m), per observe
        self._div_ph: dict[str, list[float]] = {}     # dieselbe Groesse, nach PHASE getrennt (s. _phase_of)
        (self.add_in("policy_state", 13, "[hand xyz, obj xy, obj z, target xy, gripper, obj_h, obj_fp, "
                                         "druck_gueltig, druck_N]")
             .add_out("subgoal", 4, "[aim_xyz, gripper]"))

    def ensure_state_dim(self, want: int = 13, neutral=(0.0, 0.0)) -> int:
        """DAgger- und Selbst-Puffer auf die TASTSINN-Dimensionen erweitern (11 -> 13).

        Alte Zeilen bekommen [gueltig=0, druck=0]: der Druck WAR bei ihren Episoden physisch da,
        wurde aber nicht aufgezeichnet -- ihn mit 0 zu behaupten, waere die Luege "Klaue leer",
        und das Netz lernte daraus, dass Tragen ohne Druck normal ist.  Mit dem Flag kann es die
        alten Zeilen konditioniert ignorieren; der rollende Puffer (CAP) waescht sie ohnehin aus.
        Idempotent, "mindestens"-Semantik wie world_model.ensure_feat_dim."""
        pad = np.asarray(neutral, float); n = 0
        for buf in (self._X, self._Xi):
            for i, r in enumerate(buf):
                r = np.asarray(r, float)
                if len(r) < want:
                    buf[i] = np.concatenate([r, pad[:want - len(r)]]); n += 1
        # NETZ VERBREITERN statt neu bauen: NULL-Spalten fuer die neuen Eingaenge lassen die Ausgabe
        # BITGLEICH (Migration ist verhaltensneutral); die Lifelong-Refits lernen die Druckspalten
        # dann allmaehlich.  Der erste Versuch (frisches Netz + 200 Epochen) vernichtete das ueber
        # tausende Episoden warm trainierte Netz -- Schatten-Divergenz 362mm statt 7-11mm.
        d0 = self.net.W1.shape[1]
        if d0 < want:
            self.net.W1 = np.concatenate([self.net.W1, np.zeros((self.net.W1.shape[0], want - d0))], axis=1)
            self.net.imu = np.concatenate([self.net.imu, np.zeros(want - d0)])
            self.net.isd = np.concatenate([self.net.isd, np.ones(want - d0)])
        p = self.in_ports.get("policy_state")
        if p is not None:
            p.dim = want
        return n

    # -- lifelong DAgger data --
    def observe(self, state, subgoal) -> None:
        """One VISITED state + the reactive teacher's label.  Also tracks the SHADOW divergence
        (what would the policy have done here?) so FSM-driven runs report how close the net is.
        Between begin_episode()/end_episode() the rows are PENDED instead of committed."""
        self._k += 1
        s = np.asarray(state, float)
        if np.any(np.abs(s[list(_POS_COLS)]) > SANE_M):   # perception-glitch state (off-table coords) ->
            return                                        # never log it: one bad servo frame must not
            #                                               poison the lifelong DAgger buffer (897ca5a)
        if self.trained:
            p = self.net.predict(state)
            _d = float(np.linalg.norm(p[:3] - np.asarray(subgoal, float)[:3]))
            self._div.append(_d)
            # LAZY: das Modul kommt aus dem Zustands-Pickle, __init__ lief dort nie (dasselbe
            # Muster wie world_model._weights).  getattr statt Attributzugriff.
            if getattr(self, "_div_ph", None) is None:
                self._div_ph = {}
            self._div_ph.setdefault(self._phase_of(s), []).append(_d)
        if self._k % SUBSAMPLE:
            return
        y = np.asarray(subgoal, float).copy()
        if getattr(self, "_hold", False):
            self._pend.append((s.copy(), y))
            return
        self._commit(s.copy(), y)

    def _commit(self, s, y) -> None:
        self._X.append(s); self._Y.append(y)
        if len(self._X) > CAP:                                # evict the oldest NON-core samples
            cut = len(self._X) - CAP
            del self._X[CORE:CORE + cut]; del self._Y[CORE:CORE + cut]

    # -- teacher-corrects-failures gating (the U unlearning fix) --
    def begin_episode(self) -> None:
        """PEND this episode's teacher rows instead of committing them (see end_episode)."""
        self._pend = []; self._hold = True

    def end_episode(self, keep=True) -> int:
        """Commit or DROP the pended teacher rows.  MEASURED (U/cube alternation, guard-free): the
        reactive teacher's labels at grasp states encode 'hover open for the reflex' -- guard-free a
        FAILING behaviour (FSM 1/20 vs the net's 12/20) -- and every refit pulled the policy back onto
        them (late U misses had shadow 5-11mm = the policy BECAME the teacher and thereby failed;
        buffer-balance alone could not hold against 24000 contradicting rows).  RULE: the teacher
        CORRECTS failures, it must not overwrite a SELF-VALIDATED success -- an episode contributes
        EITHER its own confident actions (self-imitation) OR the teacher's correction rows, never
        both contradicting sets on the same states.  Caller passes keep=False iff it imitated."""
        pend = getattr(self, "_pend", None) or []
        if keep:
            for s, y in pend:
                self._commit(s, y)
        self._pend = []; self._hold = False
        return len(pend)

    # -- self-imitation (step 3): reinforce the policy's OWN validated successes --
    def _quals(self):
        """Per-sample imitation QUALITY, migrating a pre-quality pickle to full weight (1.0)."""
        q = getattr(self, "_Xq", None)
        if q is None or len(q) != len(getattr(self, "_Xi", [])):
            q = [1.0] * len(getattr(self, "_Xi", []))
            self._Xq = q
        return np.asarray(q, float)

    def imitate(self, states, actions, key=None, qual=1.0) -> int:
        """Add (state, action) pairs the POLICY actually drove on a SELF-JUDGED successful episode.
        These are the agent's own working moves -- blended with the DAgger teacher labels at fit
        time and weighted IMIT_WEIGHT (own successes lead, the teacher is a floor).  Subsampled like
        DAgger (neighbouring steps are near-duplicates).  getattr guards a pre-step-3 pickled policy.

        `key` = the commanded object; eviction is BALANCED across keys.  MEASURED (U probes A/D/E,
        guard-free): this buffer CARRIES the beyond-teacher closing skill (clear it -> even the cube
        collapses 85%->12%, because the DAgger teacher labels encode the reflex-dependent choreography
        that itself delivers 1/20 guard-free) -- but a plain FIFO let FREQUENT successes (cube, ~250
        steps/delivery) flush out the RARE object's demos: alternating U/cube drove U 60%->10% while
        the cube held 85% (rich-get-richer).  Now the fullest key evicts first, so a minority skill's
        demos survive a flood of majority successes.  Legacy pickles load with key=None (one bucket,
        naturally displaced first)."""
        if getattr(self, "_Xi", None) is None:
            self._Xi, self._Yi = [], []
        if getattr(self, "_Xk", None) is None or len(self._Xk) != len(self._Xi):
            self._Xk = [None] * len(self._Xi)                 # migrate a pre-key pickle: unlabeled bucket
        qs = self._quals().tolist()                           # migrate a pre-quality pickle (all 1.0)
        added = 0
        for j, (s, a) in enumerate(zip(states, actions)):
            if j % SUBSAMPLE:
                continue
            self._Xi.append(np.asarray(s, float).copy())
            self._Yi.append(np.asarray(a, float).copy())
            self._Xk.append(key)
            qs.append(float(qual))                            # how GOOD this episode was (see train)
            added += 1
        from collections import Counter
        while len(self._Xi) > IMIT_CAP:                       # evict the OLDEST sample of the FULLEST key
            top = Counter(self._Xk).most_common(1)[0][0]
            i = self._Xk.index(top)
            del self._Xi[i]; del self._Yi[i]; del self._Xk[i]; del qs[i]
        self._Xq = qs
        return added

    def imit_mix(self) -> dict:
        """Per-key sample counts of the self-imitation buffer (for the scoreboard)."""
        from collections import Counter
        return dict(Counter(getattr(self, "_Xk", []) or []))

    def sanitize(self) -> int:
        """One-time HEAL of a buffer polluted by off-table (perception-glitch) states -- e.g. the 897ca5a
        px-as-metres servo bug drove ~26% of the DAgger buffer to |coord|~50-176 m and wrecked the fitted
        policy.  Drops every (state, label) pair whose positions exceed SANE_M, from BOTH the DAgger and the
        self-imitation buffers.  Returns the number of pairs removed; the caller retrains if it is > 0."""
        removed = 0
        for Xn, Yn in (("_X", "_Y"), ("_Xi", "_Yi")):
            X = getattr(self, Xn, None); Y = getattr(self, Yn, None)
            if not X:
                continue
            K = getattr(self, "_Xk", None) if Xn == "_Xi" else None
            if K is not None and len(K) != len(X):
                K = [None] * len(X)                           # pre-key pickle -> unlabeled
            keepX, keepY, keepK = [], [], []
            for i, (s, y) in enumerate(zip(X, Y)):
                if np.any(np.abs(np.asarray(s, float)[list(_POS_COLS)]) > SANE_M):
                    removed += 1
                else:
                    keepX.append(s); keepY.append(y)
                    if K is not None:
                        keepK.append(K[i])
            setattr(self, Xn, keepX); setattr(self, Yn, keepY)
            if K is not None:
                self._Xk = keepK
        return removed

    def n(self) -> int:
        return len(self._X)

    def n_imit(self) -> int:
        return len(getattr(self, "_Xi", []))

    def train(self, epochs=120, quiet=True) -> None:
        if self._X:
            _w = len(np.asarray(self._X[-1], float))
            if self.net.W1.shape[1] != _w:                 # Zustandsbreite gewachsen (Tastsinn 11->13):
                from pc_cvnn.pc_act19 import Policy as _P  #   Netz mit neuer Breite neu aufbauen; das
                self.net = _P(din=_w, rng=np.random.default_rng(4))   # folgende fit lernt aus dem
                self.trained = False                       #   MIGRIERTEN Puffer neu (Welt-Modell-Muster)
        if len(self._X) < 500:
            return                                    # too little to fit anything meaningful
        Xi, Yi = getattr(self, "_Xi", []), getattr(self, "_Yi", [])
        if Xi and GRADED_IMIT:
            # GRADED SELF-IMITATION (the user's idea, 2026-07-25): weight each demo by HOW WELL that
            # episode placed instead of letting a flat imit_tol bar decide in/out.  Measured on the
            # 120-ep log: the strict 15mm bar discards 11 of 43 genuine hits (<=25mm), while widening
            # it to 20mm would add 47% more demos at UNCHANGED one bad one -- graded weighting gets
            # that without the either/or, since a 24mm demo simply pulls ~half as hard as a 5mm one.
            # Uses the SAME AWR `w` hook as the key balance below and multiplies with it when both are
            # on, so the two effects compose instead of overriding each other.  ACT23_IMIT_GRADED=0
            # restores the flat behaviour.  Legacy pickles migrate at 1.0 (see _quals).
            q = self._quals()
            bal = np.ones(len(Xi))
            if _IMIT_BAL:
                from collections import Counter
                K = getattr(self, "_Xk", None)
                if K is None or len(K) != len(Xi):
                    K = [None] * len(Xi)
                cnt = Counter(K); mean = len(Xi) / len(cnt)
                bk = {k: min(mean / c, 4.0) for k, c in cnt.items()}   # balance factor WITHOUT the
                bal = np.array([bk[k] for k in K], float)              #   IMIT_WEIGHT (applied once below)
            X = np.array(self._X + Xi); Y = np.array(self._Y + Yi)
            w = np.concatenate([np.ones(len(self._X)), IMIT_WEIGHT * q * bal])
            self.net.fit(X, Y, epochs=epochs, quiet=quiet, w=w)
        elif Xi and _IMIT_BAL:                        # DAgger labels + PER-KEY BALANCED self-imitation.
            # MEASURED (U/cube alternation): balanced EVICTION alone does not save a rare skill -- its
            # few demos (~1-2% of the buffer) have no PULL against 24000 teacher rows whose labels
            # guard-free actively fight the learned close (the teacher hovers for the disabled reflex).
            # So every practiced key gets a comparable total imitation MASS via fit weights (the AWR
            # `w` hook, unused until now), capped at 4x IMIT_WEIGHT per sample so a couple of lucky
            # episodes cannot dominate the fit.
            from collections import Counter
            K = getattr(self, "_Xk", None)
            if K is None or len(K) != len(Xi):
                K = [None] * len(Xi)
            cnt = Counter(K)
            mean = len(Xi) / len(cnt)
            wk = {k: min(IMIT_WEIGHT * mean / c, 4.0 * IMIT_WEIGHT) for k, c in cnt.items()}
            X = np.array(self._X + Xi); Y = np.array(self._Y + Yi)
            w = np.concatenate([np.ones(len(self._X)), np.array([wk[k] for k in K], float)])
            self.net.fit(X, Y, epochs=epochs, quiet=quiet, w=w)
        elif Xi:                                      # ACT23_IMIT_BAL=0: the old flat replication
            X = np.array(self._X + Xi * IMIT_WEIGHT)
            Y = np.array(self._Y + Yi * IMIT_WEIGHT)
            self.net.fit(X, Y, epochs=epochs, quiet=quiet)
        else:
            X, Y = np.array(self._X), np.array(self._Y)
            self.net.fit(X, Y, epochs=epochs, quiet=quiet)
        self.trained = True

    # -- runtime --
    def predict(self, state):
        return self.net.predict(state)

    @staticmethod
    def _phase_of(s) -> str:   # noqa: C901
        """Phase AUS DEM ZUSTAND ableiten (nicht aus der FSM).

        Gleiche Lehre wie bei der Griffdruck-Messung (pc_act16, 2026-08-07): im Netz-Modus fuehrt die
        Policy den Arm, die FSM-Phase bleibt haengen und sortiert falsch ein.  Der Zustand traegt
        alles Noetige: [hx,hy,hz, cx,cy,cz, tx,ty, j5, obj_h, obj_fp, ...].
        Absicht ist NICHT eine exakte FSM-Nachbildung, sondern eine stabile Einteilung, unter der
        sich die Divergenz zwischen Policy und Teacher vergleichen laesst."""
        h = np.asarray(s[:3], float); c = np.asarray(s[3:6], float)
        t = np.asarray(s[6:8], float); j5 = float(s[8]); obj_h = float(s[9])
        from pc_cvnn.pc_act16 import J5_CLOSED_TH      # lokal: act16 importiert arm_modules (Zirkel)
        lifted = c[2] > obj_h + 0.02 and j5 < J5_CLOSED_TH
        if lifted:
            return "ablegen" if float(np.linalg.norm(h[:2] - t)) < 0.05 else "tragen"
        return "greifen" if float(np.linalg.norm(h[:2] - c[:2])) < 0.03 else "anfahren"

    def shadow_divergence_mm(self) -> float:
        """Mean |aim_policy - aim_teacher| (mm) since the last call; NaN if nothing accumulated."""
        if not self._div:
            return float("nan")
        d = float(np.mean(self._div)) * 1000.0
        self._div.clear()
        return d

    def shadow_divergence_by_phase(self) -> dict:
        """{Phase: (Mittel in mm, Anzahl Schritte)} seit dem letzten Aufruf; leert den Speicher.

        WOZU (2026-08-13): der Gesamtwert mittelt ueber die ganze Episode.  Gemessen ist aber, dass
        die Policy den GREIFpunkt auf Millimeter trifft und das ABLAGEziel um Zentimeter verfehlt
        (18mm bei Erfolg, 44mm bei Fehlschlag, waehrend ihr eigener Teacher ~11mm schafft) -- ein
        phasenweiser Vergleich zeigt, ob sie speziell dort auseinanderlaeuft."""
        d = getattr(self, "_div_ph", None) or {}
        out = {k: (float(np.mean(v)) * 1000.0, len(v)) for k, v in d.items() if v}
        d.clear()
        return out

    def step(self) -> None:
        s = self.get_in("policy_state")
        if s is not None and self.trained:
            self.set_out("subgoal", self.net.predict(s))
