r"""
pc_act19.py — Phase 3, step 1: a LEARNED action policy replaces the scripted choreography.

Until now the arm's high-level ACTIONS were a hand-coded finite-state machine (over -> lower ->
close -> lift -> carry -> place -> release); only perception (act18) and kinematics (act14) were
learned.  Here a small NET learns the choreography by IMITATION of the scripted FSM:

    1. run the scripted FSM and LOG (state -> sub-goal): state = [hand xyz, object xy, object z,
       target xy, gripper], sub-goal = (aim xyz, gripper target);
    2. train a policy net  state -> sub-goal;
    3. run the arm with the NET deciding the sub-goals (the FSM is bypassed).

A reactive policy suffices because the "phase" is recoverable from the state (gripper open/closed,
object on table vs lifted, hand near object vs target).  The non-headless final run COUPLES the
policy with the act18 learned following-fovea perception (+ its live hex view).  Beyond imitation,
an ADVANTAGE-WEIGHTED-REGRESSION (AWR) loop tries to improve past the teacher.

  ACT19_HEADLESS=1   metrics      ACT19_COLLECT / ACT19_EPISODES   teacher / test episodes
  ACT19_SELF=0  skip RL    ACT19_ITERS / ACT19_BATCH / ACT19_RLCAP / ACT19_BETA   AWR knobs
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim, ArmBodyModel3D
import pc.pc_act16 as act16


class Policy:
    """Small MLP  state(9) -> sub-goal(4)=[aim_xyz, gripper], with input/output normalisation."""
    def __init__(self, din=9, dout=4, hid=96, lr=0.02, rng=None):
        rng = rng or np.random.default_rng(0)
        self.W1 = rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (dout, hid)); self.b2 = np.zeros(dout)
        self.lr = lr
        self.imu = np.zeros(din); self.isd = np.ones(din); self.omu = np.zeros(dout); self.osd = np.ones(dout)

    def fit(self, X, Y, epochs=500, bs=256, rng=None, set_norm=True, quiet=False, w=None):
        """Minibatch regression of state->sub-goal.  Optional per-sample weights `w` give
        ADVANTAGE-WEIGHTED regression (AWR): samples from better-than-baseline rollouts pull
        the policy more, worse-than-baseline ones less."""
        rng = rng or np.random.default_rng(1)
        if set_norm:                                          # fine-tuning keeps the original norm
            self.imu, self.isd = X.mean(0), X.std(0) + 1e-6
            self.omu, self.osd = Y.mean(0), Y.std(0) + 1e-6
        Xn = (X - self.imu) / self.isd; Yn = (Y - self.omu) / self.osd
        n = len(Xn); w = np.ones(n) if w is None else np.asarray(w, float)
        for ep in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb, yb, wb = Xn[b], Yn[b], w[b]
                h = np.tanh(self.W1 @ xb.T + self.b1[:, None])          # hid x B
                yp = self.W2 @ h + self.b2[:, None]                    # dout x B
                err = (yp - yb.T) * wb[None, :] / (wb.sum() + 1e-8)    # advantage-weighted residual
                self.W2 -= self.lr * err @ h.T; self.b2 -= self.lr * err.sum(1)
                dh = (self.W2.T @ err) * (1 - h ** 2)
                self.W1 -= self.lr * dh @ xb; self.b1 -= self.lr * dh.sum(1)
            if not quiet and ep % 100 == 0:
                h = np.tanh(self.W1 @ Xn.T + self.b1[:, None]); yp = (self.W2 @ h + self.b2[:, None]).T
                print(f"\r\x1b[2K  [train policy] {ep}/{epochs}  mse {np.mean((yp-Yn)**2):.4f}", end="")
        if not quiet:
            print("\r\x1b[2K", end="")

    def predict(self, x):
        xn = (np.asarray(x, float) - self.imu) / self.isd
        h = np.tanh(self.W1 @ xn + self.b1)
        return (self.W2 @ h + self.b2) * self.osd + self.omu

    def snapshot(self):                                       # weights + normalisation, for keep-best
        return tuple(a.copy() for a in (self.W1, self.b1, self.W2, self.b2,
                                        self.imu, self.isd, self.omu, self.osd))

    def restore(self, s):
        self.W1, self.b1, self.W2, self.b2, self.imu, self.isd, self.omu, self.osd = (a.copy() for a in s)


def main():
    HEADLESS = os.environ.get("ACT19_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT19_CAM", "overview").lower()
    COLLECT = int(os.environ.get("ACT19_COLLECT", "18"))
    EPISODES = int(os.environ.get("ACT19_EPISODES", "12"))
    RES = int(os.environ.get("ACT19_RES", "240"))             # camera render size (for the fovea)

    print("act19 — Phase 3.1: a LEARNED action policy by imitation of the scripted choreography")
    sim = BracketArmSim(render_wh=(RES, RES))
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5)); body.babble(sim, 4000)

    # 1) collect teacher data: run the scripted FSM, log (state -> sub-goal)
    Xs, Ys = [], []

    def log(state, aim, j5):
        Xs.append(state.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))

    print(f"  collecting teacher demonstrations ({COLLECT} eps of the scripted grasp) ...")
    act16.run_combined(sim, body, None, CAM, episodes=COLLECT, force="grasp", log_fn=log)
    X, Y = np.array(Xs), np.array(Ys)
    print(f"  collected {len(X)} (state -> sub-goal) samples")

    # 2) train the policy net (imitation -> capped at the teacher)
    policy = Policy(rng=np.random.default_rng(2))
    policy.fit(X, Y)

    def evaluate(n=14):
        act16.run_combined._quiet = True
        d, m = act16.run_combined(sim, body, None, CAM, episodes=n, policy_fn=policy.predict)
        act16.run_combined._quiet = False
        return d, m

    d0, m0 = evaluate()
    print(f"  imitation policy: delivered {d0}/{m0}")
    best = {"score": d0 / max(1, m0), "snap": policy.snapshot(), "tag": "imitation"}

    def consider(d, m, tag):                                  # keep the BEST policy seen, by eval score
        sc = d / max(1, m)
        if sc > best["score"]:
            best.update(score=sc, snap=policy.snapshot(), tag=tag)

    # 2b) DAgger: close the BEHAVIOR-CLONING gap.  A reactive BC policy drifts into states the
    #     demos never covered and has no guidance there.  DAgger rolls the policy out, has the
    #     teacher FSM LABEL its VISITED states (teacher_log_fn), and retrains on the AGGREGATED
    #     dataset.  HONEST: this DEGRADES here -- the FSM teacher is NOT Markovian (hidden `phase`),
    #     so its labels on policy-visited states are inconsistent and poison the set.  Off by
    #     default; a reactive (stateless) teacher would be needed to make DAgger valid.  (Beyond
    #     the teacher is blocked until we're AT it.)
    DAGGER = os.environ.get("ACT19_DAGGER", "0") == "1"
    RLCAP = int(os.environ.get("ACT19_RLCAP", "1200"))        # faster rollouts than the full place CAP
    if DAGGER:
        D_ITERS = int(os.environ.get("ACT19_DITERS", "4")); D_BATCH = int(os.environ.get("ACT19_DBATCH", "14"))
        aggX, aggY = [X], [Y]
        print("  DAgger: aggregate teacher labels on policy-visited states -> reach the teacher ...")
        for it in range(D_ITERS):
            dx, dy = [], []

            def tlog(s, aim, j5, _x=dx, _y=dy):
                _x.append(s.copy()); _y.append(np.array([aim[0], aim[1], aim[2], j5]))

            act16.run_combined._quiet = True
            act16.run_combined(sim, body, None, CAM, episodes=D_BATCH, policy_fn=policy.predict,
                               teacher_log_fn=tlog, cap=RLCAP)
            act16.run_combined._quiet = False
            aggX.append(np.array(dx)); aggY.append(np.array(dy))
            policy.fit(np.vstack(aggX), np.vstack(aggY), epochs=300, quiet=True)   # retrain on aggregate
            d, m = evaluate(n=18); consider(d, m, f"dagger{it}")
            print(f"  dagger {it}: +{len(dx)} teacher-labelled steps  ->  delivered {d}/{m}")

    # 3) BEYOND THE TEACHER: proper RL via ADVANTAGE-WEIGHTED REGRESSION (AWR).
    #    Explore sub-goals with decaying noise; score each rollout with a SHAPED reward
    #    R = 2*success - 8*residual-distance (signal even among failures); maintain a reward
    #    BASELINE V (EMA); weight every explored (state->sub-goal) step by exp(beta*(R-V)) so
    #    better-than-baseline rollouts pull the policy MORE and worse ones LESS (vs. the old
    #    binary keep-successes self-imitation).  Anchored on the teacher demos to avoid drift.
    SELF = os.environ.get("ACT19_SELF", "1") == "1"
    if SELF:
        N_ITERS = int(os.environ.get("ACT19_ITERS", "8")); BATCH = int(os.environ.get("ACT19_BATCH", "24"))
        BETA = float(os.environ.get("ACT19_BETA", "1.0"))
        nrng = np.random.default_rng(3); baseX, baseY = X.copy(), Y.copy(); Vb = None
        print("  RL beyond the teacher (advantage-weighted regression) ...")

        def reward(ok, err):
            return 2.0 * float(ok) - 8.0 * float(err)         # success bonus minus residual distance (m)

        for it in range(N_ITERS):
            sd = 0.010 * (1 - it / N_ITERS) + 0.003           # decaying sub-goal exploration
            eps = {"cur": [], "S": [], "Y": [], "R": []}

            def noisy(s, _sd=sd):
                return policy.predict(s) + nrng.normal(0, [_sd, _sd, _sd, _sd * 12])

            def log(s, aim, j5, _e=eps):
                _e["cur"].append((s.copy(), np.array([aim[0], aim[1], aim[2], j5])))

            def ep_end(ep, ok, err, _e=eps):                  # credit the whole rollout with its reward
                R = reward(ok, err)
                for s, y in _e["cur"]:
                    _e["S"].append(s); _e["Y"].append(y); _e["R"].append(R)
                _e["cur"] = []

            act16.run_combined._quiet = True
            act16.run_combined(sim, body, None, CAM, episodes=BATCH, policy_fn=noisy,
                               log_fn=log, episode_end_fn=ep_end, cap=RLCAP)
            act16.run_combined._quiet = False
            if eps["S"]:
                S = np.array(eps["S"]); Yr = np.array(eps["Y"]); R = np.array(eps["R"])
                Vb = R.mean() if Vb is None else 0.7 * Vb + 0.3 * R.mean()      # reward baseline (EMA)
                w = np.exp(np.clip(BETA * (R - Vb) / (R.std() + 1e-6), -3, 3))  # advantage weights
                Xi = np.vstack([S, baseX]); Yi = np.vstack([Yr, baseY])         # explored + teacher anchor
                wi = np.concatenate([w, np.full(len(baseX), float(w.mean()))])
                policy.fit(Xi, Yi, epochs=150, set_norm=False, quiet=True, w=wi)
            d, m = evaluate(n=18); consider(d, m, f"awr{it}")
            meanR = float(np.mean(eps["R"])) if eps["R"] else float("nan")
            print(f"  iter {it}: {len(eps['S'])} steps  meanR {meanR:+.2f}  ->  delivered {d}/{m}")

    # 4) run with the NET deciding the sub-goals (FSM bypassed), now COUPLED with the act18
    #    LEARNED following-fovea perception (+ its live hex display) instead of privileged state
    policy.restore(best["snap"])                              # show the BEST policy found, not the last
    print(f"  best policy: {best['tag']} (eval {best['score']:.2f})")
    print("  running with the LEARNED policy driving the actions ...")
    if HEADLESS:
        act16.run_combined(sim, body, None, CAM, episodes=EPISODES, policy_fn=policy.predict)
    else:
        print("  (coupling the policy with the act18 learned following-fovea + live hex view)")
        try:
            from pc.pc_act18 import setup_following_fovea
            P = setup_following_fovea(sim, CAM, RES, headless=False)
            act16.run_combined(sim, body, None, CAM, episodes=EPISODES, policy_fn=policy.predict,
                               perceive_fn=P["perceive"], track_fn=P["track"])
            if P["viz"] is not None:
                print("  [viz] close the window to exit."); P["viz"].hold()
        except Exception as e:
            print(f"  [viz/perception] {e}; falling back to privileged run")
            act16.run_combined(sim, body, None, CAM, episodes=EPISODES, policy_fn=policy.predict)


if __name__ == "__main__":
    main()
