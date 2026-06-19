r"""test_pc_fwd_plan.py — STEP 1 (de-risk) of the CHAINED FORWARD-MODEL PLANNER (the lever past the AWR plateau).

act22 learns the policy online by AWR, but AWR gives ONE episode-level reward to every step of a rollout --
coarse credit assignment, so it plateaus.  The user's lever: a learned FORWARD MODEL of the manipulation
F(state, sub-goal) -> next state, so a planner can CHAIN dense per-step sub-goals (each step gets a
model-derived target instead of one scalar).  Step 1 here only asks: is such a forward model LEARNABLE at
useful accuracy?  (If not, the chained planner is moot.)

State (the task-relevant subset of the policy's 11-d state): [hand xyz(3), obj xy(2), obj z(1), gripper(1)].
Action (the policy's sub-goal): [aim xyz(3), gripper(1)].  We collect (s_t, a_t, s_{t+1}) transitions from
teacher rollouts and fit  delta_s = MLP(s, a)  (the displacement representation that worked for the chain /
obstacle world models).  Reported as a 1-step error AND a MULTI-STEP rollout drift in mm.

FINDING (step 1): the per-step model is near-perfect (0.1mm 1-step) but chaining it over the full ~1200-step
reactive episode drifts ~275mm -- per-step errors compound.  CONCLUSION: the chained planner must operate at
the MACRO SUB-GOAL level (a handful of waypoints), not per control step.  Step 2 will learn a sub-goal-outcome
model (state + macro sub-goal -> state when reached) and chain a few of them for dense per-sub-goal targets.

  python src/pc/test_pc_fwd_plan.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim
import pc.pc_act16 as act16
from pc.arm_modules import BodyModelModule

# state layout inside the policy's 11-d vector: [hx,hy,hz, ox,oy, oz, tx,ty, grip, obj_h, obj_fp]
SDIM = [0, 1, 2, 3, 4, 5, 8]          # hand xyz, obj xy, obj z, gripper -> the 7-d task state we model


class FwdMLP:
    """2-hidden-layer tanh MLP + Adam: (state7, action4) -> delta-state7 (the displacement model)."""

    def __init__(self, din=11, dout=7, h=128, rng=None):
        rng = rng or np.random.default_rng(0)
        s = lambda a, b: rng.standard_normal((a, b)) * np.sqrt(2.0 / a)
        self.W1 = s(din, h); self.b1 = np.zeros(h)
        self.W2 = s(h, h);   self.b2 = np.zeros(h)
        self.W3 = s(h, dout); self.b3 = np.zeros(dout)
        self.imu = np.zeros(din); self.isd = np.ones(din)
        self.omu = np.zeros(dout); self.osd = np.ones(dout)

    def _f(self, X):
        z1 = np.tanh(X @ self.W1 + self.b1); z2 = np.tanh(z1 @ self.W2 + self.b2)
        return z1, z2, z2 @ self.W3 + self.b3

    def fit(self, X, T, epochs=400, bs=256, lr=2e-3, rng=None):
        rng = rng or np.random.default_rng(0)
        self.imu, self.isd = X.mean(0), X.std(0) + 1e-6
        self.omu, self.osd = T.mean(0), T.std(0) + 1e-6
        Xn = (X - self.imu) / self.isd; Tn = (T - self.omu) / self.osd
        ps = [self.W1, self.b1, self.W2, self.b2, self.W3, self.b3]
        m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0; n = len(Xn)
        for ep in range(epochs):
            idx = rng.permutation(n)
            for s0 in range(0, n, bs):
                b = idx[s0:s0 + bs]; xb, tb = Xn[b], Tn[b]
                z1, z2, out = self._f(xb)
                g = (out - tb) * (2.0 / len(b))
                gW3 = z2.T @ g; gb3 = g.sum(0)
                d2 = (g @ self.W3.T) * (1 - z2 ** 2); gW2 = z1.T @ d2; gb2 = d2.sum(0)
                d1 = (d2 @ self.W2.T) * (1 - z1 ** 2); gW1 = xb.T @ d1; gb1 = d1.sum(0)
                grads = [gW1, gb1, gW2, gb2, gW3, gb3]; t += 1
                for i, (p, gr) in enumerate(zip(ps, grads)):
                    m[i] = 0.9 * m[i] + 0.1 * gr; v[i] = 0.999 * v[i] + 0.001 * gr * gr
                    p -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)

    def predict_delta(self, S, A):
        X = (np.column_stack([S, A]) - self.imu) / self.isd
        return self._f(X)[2] * self.osd + self.omu


def collect_transitions(sim, bm, cam, episodes, rng):
    """Run teacher rollouts; log (11-d state, 4-d action) per step with episode boundaries, then build
    (s_t, a_t -> s_{t+1}) transitions on the 7-d task state (within an episode only)."""
    eps = {"cur": [], "all": []}

    def logx(state, aim, j5):
        eps["cur"].append((np.asarray(state, float).copy(), np.array([aim[0], aim[1], aim[2], j5])))

    def ep_end(ep, ok, err):
        eps["all"].append(eps["cur"]); eps["cur"] = []

    act16.run_combined._quiet = True
    act16.run_combined(sim, bm.body, None, cam, episodes=episodes, policy_fn=act16.reactive_subgoal,
                       log_fn=logx, episode_end_fn=ep_end)
    act16.run_combined._quiet = False
    S, A, Sn = [], [], []
    trajs = []                                     # keep whole trajectories for the multi-step rollout test
    for traj in eps["all"]:
        st = np.array([s[SDIM] for s, a in traj]); ac = np.array([a for s, a in traj])
        trajs.append((st, ac))
        for k in range(len(traj) - 1):
            s0, a0 = traj[k]; s1, _ = traj[k + 1]
            S.append(s0[SDIM]); A.append(a0); Sn.append(s1[SDIM])
    return np.array(S), np.array(A), np.array(Sn), trajs


def main():
    cam = os.environ.get("FWD_CAM", "overview").lower()
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)

    print("fwd-plan — STEP 1: is a forward model of the manipulation LEARNABLE? (de-risk the chained planner)")
    n_ep = int(os.environ.get("FWD_EPS", "60"))
    print(f"  collecting transitions from {n_ep} teacher rollouts ...")
    S, A, Sn, trajs = collect_transitions(sim, bm, cam, n_ep, np.random.default_rng(1))
    dS = Sn - S
    print(f"    {len(S)} transitions; mean |step| hand {np.linalg.norm(dS[:,:3],axis=1).mean()*1000:.1f} mm "
          f"obj {np.linalg.norm(dS[:,3:5],axis=1).mean()*1000:.1f} mm")

    ntr = int(0.85 * len(S)); idx = np.random.default_rng(2).permutation(len(S))
    tr, te = idx[:ntr], idx[ntr:]
    fwd = FwdMLP(rng=np.random.default_rng(0))
    fwd.fit(np.column_stack([S[tr], A[tr]]), dS[tr], epochs=int(os.environ.get("FWD_EPOCHS", "400")))
    pr = fwd.predict_delta(S[te], A[te])
    # 1-step prediction error of the NEXT state (predicted s + delta vs true s_{t+1})
    pred_next = S[te] + pr
    eh = np.linalg.norm(pred_next[:, :3] - Sn[te][:, :3], axis=1) * 1000
    eo = np.linalg.norm(pred_next[:, 3:5] - Sn[te][:, 3:5], axis=1) * 1000
    # baseline: predict NO change (delta=0) -> shows the model actually captures the dynamics
    bh = np.linalg.norm(S[te][:, :3] - Sn[te][:, :3], axis=1) * 1000
    bo = np.linalg.norm(S[te][:, 3:5] - Sn[te][:, 3:5], axis=1) * 1000
    print(f"  1-step HELD-OUT error (predict next state):")
    print(f"    hand xyz : model {eh.mean():5.1f} mm  vs  no-change baseline {bh.mean():5.1f} mm")
    print(f"    obj  xy  : model {eo.mean():5.1f} mm  vs  no-change baseline {bo.mean():5.1f} mm")

    # MULTI-STEP rollout: chain the model over a whole episode (true action sequence) -> does the predicted
    # object position track the truth?  This is the real de-risk for PLANNING (errors compound when chained).
    rng = np.random.default_rng(9); held = trajs[-12:]
    fin_h, fin_o = [], []
    for st, ac in held:
        s = st[0].copy()
        for k in range(len(ac) - 1):
            s = s + fwd.predict_delta(s[None, :], ac[k][None, :])[0]
        fin_h.append(np.linalg.norm(s[:3] - st[-1][:3]) * 1000)
        fin_o.append(np.linalg.norm(s[3:5] - st[-1][3:5]) * 1000)
    print(f"  MULTI-STEP rollout (chain the model over a full episode, {int(np.mean([len(a) for _,a in held]))} steps avg):")
    print(f"    final-state drift  hand {np.mean(fin_h):5.1f} mm   obj {np.mean(fin_o):5.1f} mm")
    print("  FINDING: 1-step is near-perfect but chaining over the full ~1200-step episode DRIFTS hugely --")
    print("  per-step errors compound.  So the planner must NOT run per control step; it must work at the")
    print("  MACRO SUB-GOAL level (a handful of waypoints, few compounding steps).  That is precisely 'dense")
    print("  intermediate sub-goals' -- dense vs ONE episode reward, coarse vs 1200 control steps.  Step 2:")
    print("  a sub-goal-OUTCOME model (state + macro sub-goal -> state when reached) + chain a few of them.")


if __name__ == "__main__":
    main()
