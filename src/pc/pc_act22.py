r"""pc_act22.py — ONLINE policy learning over a long (lifelong) run.

The lifelong machinery so far only adapts the KINEMATICS (FK + the learned inverse kinematics); the
action POLICY was frozen, so a long run plateaued.  Here the policy KEEPS LEARNING online via
advantage-weighted regression (AWR), with the user's two enablers for slow learning:

  * an ENLARGED target (2.5x area, ~40mm tolerance) so success is reachable early, and
  * a GRADED reward that INCREASES toward the centre (dense signal, not a sparse 0/1) ->
    `R = 1 - min(1, residual / SCALE)`  (1 at the target centre, 0 far away).

Each iteration: roll out a batch with exploration noise on the sub-goals, score every rollout by the
graded reward, weight the explored (state -> sub-goal) steps by exp(beta*(R - baseline)) and refit the
policy (anchored on the imitation demos).  FK + IK keep adapting lifelong.  We plot the LEARNING CURVE
(mean reward + delivery over iterations) -> does the agent get BETTER the longer it runs?

Env: ACT22_HEADLESS  ACT22_ITERS  ACT22_BATCH  ACT22_COLLECT  ACT22_TOL (m)  ACT22_SCALE (m)
     ACT22_BETA  ACT22_RCAP  ACT22_EVAL
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim
import pc.pc_act16 as act16
from pc.pc_act19 import Policy
from pc.arm_modules import BodyModelModule


def main():
    HEADLESS = os.environ.get("ACT22_HEADLESS", "1") == "1"     # default headless (it is a metrics run)
    CAM = os.environ.get("ACT22_CAM", "overview").lower()
    COLLECT = int(os.environ.get("ACT22_COLLECT", "18"))
    ITERS = int(os.environ.get("ACT22_ITERS", "20"))
    BATCH = int(os.environ.get("ACT22_BATCH", "12"))
    EVAL = int(os.environ.get("ACT22_EVAL", "16"))
    TOL = float(os.environ.get("ACT22_TOL", "0.040"))          # ENLARGED target (~2.5x the 25mm area)
    SCALE = float(os.environ.get("ACT22_SCALE", "0.10"))       # graded-reward falloff (0 at this residual)
    BETA = float(os.environ.get("ACT22_BETA", "1.0"))
    RCAP = int(os.environ.get("ACT22_RCAP", "1600"))

    print("act22 — ONLINE policy learning (AWR) over a long run: graded reward + enlarged target + lifelong")
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    print(f"  learned inverse kinematics: babble {bm.learn_inverse(sim, rng=np.random.default_rng(11)):.2f} mm")
    motor = Policy(rng=np.random.default_rng(2))

    def grad_reward(ok, err):
        return 1.0 - min(1.0, float(err) / SCALE)               # increases toward the target centre

    # ---- imitation start (BC on the reactive teacher) ----
    Xs, Ys = [], []
    def log(s, aim, j5):
        Xs.append(s.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))
    print(f"  collecting reactive-teacher demos ({COLLECT} eps) ...")
    act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal,
                       log_fn=log, tol=TOL)
    baseX, baseY = np.array(Xs), np.array(Ys)
    motor.fit(baseX, baseY)

    def evaluate(n=EVAL):
        act16.run_combined._quiet = True
        d, m = act16.run_combined(sim, bm, None, CAM, episodes=n, policy_fn=motor.predict,
                                  tol=TOL, lifelong=True)
        act16.run_combined._quiet = False
        return d, m

    d0, m0 = evaluate(); print(f"  imitation start: delivered {d0}/{m0} (target {TOL*1000:.0f}mm)")

    # ---- ONLINE AWR: the policy keeps learning while it acts; FK/IK adapt lifelong ----
    nrng = np.random.default_rng(3); Vb = None
    curve = []
    print(f"  online learning: {ITERS} iters x {BATCH} eps  (graded reward, enlarged target, lifelong) ...")
    for it in range(ITERS):
        sd = 0.010 * (1 - it / ITERS) + 0.003                  # decaying sub-goal exploration
        eps = {"cur": [], "S": [], "Y": [], "R": [], "ok": 0, "n": 0}

        def noisy(s, _sd=sd):
            return motor.predict(s) + nrng.normal(0, [_sd, _sd, _sd, _sd * 12])

        def logx(s, aim, j5, _e=eps):
            _e["cur"].append((s.copy(), np.array([aim[0], aim[1], aim[2], j5])))

        def ep_end(ep, ok, err, _e=eps):                       # credit the whole rollout with its reward
            R = grad_reward(ok, err); _e["ok"] += int(ok); _e["n"] += 1
            for s, y in _e["cur"]:
                _e["S"].append(s); _e["Y"].append(y); _e["R"].append(R)
            _e["cur"] = []

        act16.run_combined._quiet = True
        act16.run_combined(sim, bm, None, CAM, episodes=BATCH, policy_fn=noisy,
                           log_fn=logx, episode_end_fn=ep_end, tol=TOL, lifelong=True, cap=RCAP)
        act16.run_combined._quiet = False
        if eps["S"]:
            S = np.array(eps["S"]); Yr = np.array(eps["Y"]); R = np.array(eps["R"])
            Vb = R.mean() if Vb is None else 0.7 * Vb + 0.3 * R.mean()
            w = np.exp(np.clip(BETA * (R - Vb) / (R.std() + 1e-6), -3, 3))   # advantage weights
            Xi = np.vstack([S, baseX]); Yi = np.vstack([Yr, baseY])         # anchor on the teacher demos
            wi = np.concatenate([w, np.full(len(baseX), float(w.mean()))])
            motor.fit(Xi, Yi, epochs=150, set_norm=False, quiet=True, w=wi)
        de, me = evaluate()
        rollR = float(np.mean(eps["R"])) if eps["R"] else float("nan")
        rollok = eps["ok"] / max(1, eps["n"])
        curve.append((rollR, rollok, de / max(1, me), bm._surprise_mm))
        print(f"  iter {it:2d}: meanR {rollR:+.2f}  rollout-deliv {eps['ok']}/{eps['n']}  ->  eval {de}/{me}")

    curve = np.array(curve); h = max(1, len(curve) // 3)
    print("=" * 72)
    print(f"  ONLINE LEARNING over {ITERS} iters (target {TOL*1000:.0f}mm, graded reward to centre):")
    print(f"    eval delivery   {np.mean(curve[:h,2]):.2f} -> {np.mean(curve[-h:,2]):.2f}   (first third -> last third)")
    print(f"    mean reward     {np.mean(curve[:h,0]):+.2f} -> {np.mean(curve[-h:,0]):+.2f}")
    print(f"    FK surprise     {np.nanmean(curve[:h,3]):.2f} -> {np.nanmean(curve[-h:,3]):.2f} mm  (lifelong kinematics)")
    print("  Read: if eval delivery / mean reward RISE, the policy is learning online -> the agent gets")
    print("  better the longer it runs.  (Honest: AWR is high-variance; the trend is what matters.)")
    print("=" * 72)
    try:
        _plot(curve, TOL, os.path.join(os.path.dirname(__file__), "act22_learning.png"))
    except Exception as e:
        print(f"  [viz] could not save the learning curve: {e}")


def _plot(curve, tol, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    it = np.arange(1, len(curve) + 1)
    fig, ax = plt.subplots(2, 1, figsize=(7, 5.5), sharex=True)
    fig.patch.set_facecolor("#0e0e12"); fig.suptitle(f"act22 online policy learning (target {tol*1000:.0f}mm)", color="w")
    for a in ax:
        a.set_facecolor("#0e0e12"); a.grid(True, color="#333", lw=0.4); a.tick_params(colors="w")
        [s.set_color("#555") for s in a.spines.values()]
    ax[0].plot(it, curve[:, 2], color="#33ccff", label="eval delivery"); ax[0].plot(it, curve[:, 1], color="#888", alpha=0.6, label="rollout delivery")
    ax[0].set_ylabel("delivery rate", color="w"); ax[0].legend(facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=8)
    ax[0].set_title("does the agent get better as it learns online?", color="w", fontsize=9)
    ax[1].plot(it, curve[:, 0], color="#88ff88"); ax[1].set_ylabel("mean graded reward", color="#88ff88")
    ax[1].set_xlabel("online iteration", color="w")
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] learning curve saved -> {path}")


if __name__ == "__main__":
    main()
