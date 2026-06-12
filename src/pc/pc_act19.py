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
object on table vs lifted, hand near object vs target).  Perception is privileged here (Phase 1
covers it) so this isolates the learned ACTION policy.  Next steps: improve beyond the teacher
(RL/curiosity) + a hierarchical push-MPC.

  ACT19_HEADLESS=1   metrics      ACT19_COLLECT / ACT19_EPISODES   teacher / test episodes
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

    def fit(self, X, Y, epochs=500, bs=256, rng=None, set_norm=True, quiet=False):
        rng = rng or np.random.default_rng(1)
        if set_norm:                                          # fine-tuning keeps the original norm
            self.imu, self.isd = X.mean(0), X.std(0) + 1e-6
            self.omu, self.osd = Y.mean(0), Y.std(0) + 1e-6
        Xn = (X - self.imu) / self.isd; Yn = (Y - self.omu) / self.osd
        n = len(Xn)
        for ep in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb, yb = Xn[b], Yn[b]
                h = np.tanh(self.W1 @ xb.T + self.b1[:, None])          # hid x B
                yp = self.W2 @ h + self.b2[:, None]                    # dout x B
                err = (yp - yb.T) / len(b)
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

    # 3) BEYOND THE TEACHER: self-improvement — explore sub-goals with noise, KEEP the
    #    successful rollouts, and reinforce them (reward-driven self-imitation).
    SELF = os.environ.get("ACT19_SELF", "1") == "1"
    if SELF:
        N_ITERS = int(os.environ.get("ACT19_ITERS", "6")); BATCH = int(os.environ.get("ACT19_BATCH", "16"))
        nrng = np.random.default_rng(3); baseX, baseY = X.copy(), Y.copy()
        print("  self-improvement (explore + keep successes) ...")
        for it in range(N_ITERS):
            sd = 0.010 * (1 - it / N_ITERS) + 0.003          # decaying exploration on the sub-goal
            buf = {"cur": [], "X": [], "Y": []}

            def noisy(s, _sd=sd):
                return policy.predict(s) + nrng.normal(0, [_sd, _sd, _sd, _sd * 12])

            def log(s, aim, j5, _b=buf):
                _b["cur"].append((s.copy(), np.array([aim[0], aim[1], aim[2], j5])))

            def ep_end(ep, ok, _b=buf):
                if ok:
                    for s, y in _b["cur"]:
                        _b["X"].append(s); _b["Y"].append(y)
                _b["cur"] = []

            act16.run_combined._quiet = True
            act16.run_combined(sim, body, None, CAM, episodes=BATCH, policy_fn=noisy,
                               log_fn=log, episode_end_fn=ep_end)
            act16.run_combined._quiet = False
            if buf["X"]:                                       # fine-tune on own successes + anchor
                Xi = np.vstack([np.array(buf["X"]), baseX]); Yi = np.vstack([np.array(buf["Y"]), baseY])
                policy.fit(Xi, Yi, epochs=150, set_norm=False, quiet=True)
            d, m = evaluate()
            print(f"  iter {it}: kept {len(buf['X'])} success-steps  ->  delivered {d}/{m}")

    # 4) run with the NET deciding the sub-goals (FSM bypassed), now COUPLED with the act18
    #    LEARNED following-fovea perception (+ its live hex display) instead of privileged state
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
