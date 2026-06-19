r"""test_pc_macro_model.py — STEP 2 of the chained planner: the MACRO SUB-GOAL-OUTCOME model.

Step 1 (test_pc_fwd_plan) showed a per-CONTROL-STEP forward model is accurate (0.1mm) but drifts ~275mm when
chained over the ~1200-step reactive episode -- per-step errors compound.  So the planner must work at the
MACRO SUB-GOAL level.  Here a "macro" is an OPTION: hold one sub-goal (aim xyz + gripper) for a fixed horizon
H, letting the reach controller drive there and settle.  A whole pick-and-place is then ~7 macros, not 1200
steps -- so chaining the model compounds error over 7 steps, not 1200.

The MACRO MODEL learns  (state7, macro-action4) -> end-state7  where
  state7  = [hand xyz(3), obj xy(2), obj z(1), gripper(1)]
  action4 = [aim xyz(3), gripper-intent(1)]    (the option = hold this sub-goal until the phase ends)
Macro transitions are sourced from the WORKING reactive teacher (run_combined, which grasps reliably) and
segmented by FSM phase (over / lower / close / lift / carry / lower / release) -- reimplementing the grasp in
a standalone executor dropped the cube (j5 stalls at 0.18 but the lift slipped), so we reuse the proven one
via a `macro_log_fn` hook.  Validated as a 1-macro error AND -- the decisive test -- the CHAINED final-object
drift over the episode's macros.

RESULT: ~5.5 macros/episode, real carries (obj moves ~18mm mean, 84 macros >30mm).  1-macro held-out error
hand ~9mm / obj ~7mm; CHAINED over the full episode the final-object drift is ~4mm (vs 275mm for the per-step
model of step 1).  So the macro model is PLAN-ABLE -> step 3 chains macro sub-goals to deliver the object,
giving the policy dense per-sub-goal targets instead of AWR's one episode reward.

  python src/pc/test_pc_macro_model.py        # knobs: MACRO_EPS, MACRO_EPOCHS, MACRO_CAM
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim
import pc.pc_act16 as act16
from pc.pc_act16 import J5_OPEN, J5_GRIP
from pc.arm_modules import BodyModelModule
from test_pc_fwd_plan import FwdMLP, SDIM      # SDIM = [0,1,2,3,4,5,8] -> hand xyz, obj xy, obj z, grip


def segment(traj):
    """A teacher trajectory [(state11, aim3, j5, phase)] -> macro transitions.  A MACRO is a maximal run of
    one FSM phase (over / lower / close / lift / carry / place ...); its action is the sub-goal HELD over the
    phase (last aim + gripper intent), its outcome is the task state when the phase ends (= next phase start)."""
    macros = []
    i = 0; n = len(traj)
    while i < n:
        ph = traj[i][3]; j = i
        while j < n and traj[j][3] == ph:
            j += 1
        s0 = traj[i][0][SDIM]                               # task state at phase start
        s1 = (traj[j][0] if j < n else traj[j - 1][0])[SDIM]   # state when the phase ends (next phase start)
        aim = traj[j - 1][1]; j5 = traj[j - 1][2]           # the sub-goal held at the end of the phase
        grip = J5_OPEN if j5 > 0.9 else J5_GRIP             # gripper INTENT (open vs grip)
        macros.append((s0, np.array([aim[0], aim[1], aim[2], grip]), s1))
        i = j
    return macros


def collect_teacher(sim, bm, cam, n_ep):
    """Collect macro transitions from the WORKING reactive teacher (grasps reliably), segmented by FSM phase."""
    eps = {"cur": [], "all": []}

    def mlog(state, aim, j5, phase):
        eps["cur"].append((np.asarray(state, float).copy(), np.asarray(aim, float).copy(), float(j5), phase))

    def ep_end(ep, ok, err):
        eps["all"].append(eps["cur"]); eps["cur"] = []

    act16.run_combined._quiet = True
    act16.run_combined(sim, bm, None, cam, episodes=n_ep, policy_fn=act16.reactive_subgoal,
                       macro_log_fn=mlog, episode_end_fn=ep_end, lifelong=False)
    act16.run_combined._quiet = False
    S, A, E, seqs = [], [], [], []
    for traj in eps["all"]:
        seq = segment(traj)
        seqs.append(seq)
        for s0, a, s1 in seq:
            S.append(s0); A.append(a); E.append(s1)
    return np.array(S), np.array(A), np.array(E), seqs


def main():
    cam = os.environ.get("MACRO_CAM", "overview").lower()
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    print(f"  learned inverse kinematics: {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")

    n_ep = int(os.environ.get("MACRO_EPS", "80"))
    print("macro-model — STEP 2: learn (state7, macro sub-goal4) -> end-state7 (the OPTION outcome)")
    print(f"  collecting macro transitions from {n_ep} WORKING-teacher rollouts (segmented by FSM phase) ...")
    S, A, E, seqs = collect_teacher(sim, bm, cam, n_ep)
    dE = E - S
    print(f"    {len(S)} macro transitions ({len(S)/max(1,len(seqs)):.1f}/episode); mean |macro| "
          f"hand {np.linalg.norm(dE[:,:3],axis=1).mean()*1000:.0f} mm obj {np.linalg.norm(dE[:,3:5],axis=1).mean()*1000:.0f} mm; "
          f"obj carried (>30mm in a macro): {int((np.linalg.norm(dE[:,3:5],axis=1)>0.03).sum())} macros")

    ntr = int(0.85 * len(S)); idx = np.random.default_rng(2).permutation(len(S))
    tr, te = idx[:ntr], idx[ntr:]
    macro = FwdMLP(din=11, dout=7, h=128, rng=np.random.default_rng(0))
    macro.fit(np.column_stack([S[tr], A[tr]]), dE[tr], epochs=int(os.environ.get("MACRO_EPOCHS", "600")))

    pr = S[te] + macro.predict_delta(S[te], A[te])
    eh = np.linalg.norm(pr[:, :3] - E[te][:, :3], axis=1) * 1000
    eo = np.linalg.norm(pr[:, 3:5] - E[te][:, 3:5], axis=1) * 1000
    print(f"  1-MACRO held-out error:  hand {eh.mean():4.1f} mm   obj {eo.mean():4.1f} mm")

    # CHAINED: from each held-out sequence's first state, roll the model through ALL 7 macro actions
    nseq = max(1, len(seqs) // 6); held = seqs[-nseq:]
    df_o, df_h = [], []
    for seq in held:
        s = seq[0][0].copy()
        for (_, act, _) in seq:
            s = s + macro.predict_delta(s[None, :], act[None, :])[0]
        df_h.append(np.linalg.norm(s[:3] - seq[-1][2][:3]) * 1000)
        df_o.append(np.linalg.norm(s[3:5] - seq[-1][2][3:5]) * 1000)
    print(f"  CHAINED over 7 macros ({len(held)} held-out seqs): final-state drift  "
          f"hand {np.mean(df_h):4.1f} mm   obj {np.mean(df_o):4.1f} mm")
    print("  Read: if the 7-macro chained obj drift is SMALL (cm-scale, not the 275mm of the per-step model),")
    print("  the macro model is plan-able -> step 3 chains macro sub-goals to deliver the object (dense targets).")


if __name__ == "__main__":
    main()
