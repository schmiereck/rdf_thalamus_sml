r"""
test_pc_tap_diag.py — Diagnostic: can the reward modulator learn a CONDITIONAL tap?

Motivation
----------
In test_pc_act5 the network never learns goal-directed pushing.  Three reward /
scaffold experiments changed nothing or made it worse, pointing at a structural
limit: "action" is just a premotor node (pm_0) whose tap gate is read from its
top-down prediction, and learning is a *global scalar* neuromodulator
(neuromod = 1 + gain·reward) scaling the local PC/Hebbian weight updates.

This script strips EVERYTHING else away (no fovea, no pointer, no multi-step
physics) and asks the minimal question:

    Can that learning rule teach pm_0 to FIRE on a GO cue and WITHHOLD on a
    NOGO cue, purely from reward?

It mirrors the act5 mechanism faithfully:
  * a top node `h` predicts both the clamped `cue` sensor and the premotor `pm`,
  * the tap gate is read as  (tanh(pm.pi[0]) + 1) / 2   (exactly as in act5),
  * the executed action is fed back as an efference copy on a clamped `motor`
    sensor that pm predicts,
  * reward = +1 for a correct GO-tap / NOGO-withhold, else -1, sent via
    net.set_reward() before the modulated net.step(learn=True).

Because PC inference is deterministic (no built-in policy exploration), we also
test an optional exploration noise on the decision — if learning ONLY works with
it, that tells us act5 is missing exploration, not learning capacity.

Run:  python test_pc_tap_diag.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType


GO   = np.array([1.0, 0.0, 0.0, 0.0])
NOGO = np.array([0.0, 1.0, 0.0, 0.0])
CUE_DIM = 4


def build_tap_net(rng: np.random.Generator, pm_pressure: float) -> tuple:
    """Minimal cue → h → pm → motor network mirroring the act5 premotor path."""
    net = PCNetwork(
        eta_inf=0.05,
        n_relax=40,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=0.3,
        eta_learn=0.004,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )
    cue   = net.add(SensorNode("cue",   dim=CUE_DIM))
    h     = net.add(PCNode("h", dim=6, activation="tanh", rng=rng))
    # pm dim=1 so its single state IS the motor-coupled dimension (the tap read
    # from pm.pi[0] is exactly what pm→motor predicts — no dimension confound).
    pm    = net.add(PCNode("pm", dim=1, activation="tanh", rng=rng))
    motor = net.add(SensorNode("motor", dim=1))

    # h (top) predicts the cue and the premotor node — same wiring sense as act5
    # (hierarchy top → pm_0, sensors below the hierarchy).
    net.connect("h", "cue", ConnType.UP, pressure_scale=1.0)
    net.connect("h", "pm",  ConnType.UP, pressure_scale=pm_pressure)
    # pm predicts the motor efference copy (act5: pm_0 → motor).
    net.connect("pm", "motor", ConnType.UP, pressure_scale=1.0)
    return net, cue, pm, motor


def run_condition(
    name: str,
    *,
    gain: float,
    expl: float,
    pm_pressure: float,
    supervised: bool = False,
    n_trials: int = 6000,
    seed: int = 0,
    block: int = 1000,
) -> dict:
    """Run one go/no-go training condition; print a learning curve.

    gain        — REWARD_GAIN  (neuromod = 1 + gain·reward; >1 enables reversal)
    expl        — std of Gaussian exploration noise added to the decision
    pm_pressure — pressure_scale of the h→pm connection (act5 uses 0.1)
    supervised  — CONTROL: clamp motor to the CORRECT action (teacher) and learn
                  with neuromod=1 (plain PC, no reward).  Tests whether the
                  cue→pm pathway is learnable AT ALL, independent of reward.
    """
    rng = np.random.default_rng(seed)
    net, cue, pm, motor = build_tap_net(rng, pm_pressure)
    net.reward_gain = gain

    correct_hist: list[int] = []
    go_taps = go_n = nogo_taps = nogo_n = 0
    blocks: list[tuple] = []

    for t in range(n_trials):
        is_go = bool(rng.integers(0, 2))
        cue.set_input(GO if is_go else NOGO)

        # Read the premotor decision AFTER relaxation, so the current cue has
        # informed the state.  (act5 reads pre-relax but relies on temporal
        # continuity to carry cue info; with iid trials we must relax first.)
        net.phase_predict()
        net.phase_error()
        net.phase_relax()
        tap_gate = float(np.clip((np.tanh(pm.pi[0]) + 1.0) / 2.0, 0.0, 1.0))

        # Optional exploration on the executed action.
        noisy = tap_gate + (rng.normal(0.0, expl) if expl > 0 else 0.0)
        tapped = noisy > 0.5

        if supervised:
            # Teacher signal: clamp motor to the CORRECT action; plain PC learning.
            target = 1.0 if is_go else 0.0
            motor.set_input(np.array([target]))
            net.set_reward(0.0)          # neuromod = 1 (no reward modulation)
        else:
            # Efference copy of the EXECUTED action (reward shapes what was done).
            motor.set_input(np.array([1.0 if tapped else 0.0]))
            correct = (is_go and tapped) or ((not is_go) and not tapped)
            net.set_reward(1.0 if correct else -1.0)
        net.step(learn=True)
        net.commit_step()

        correct = (is_go and tapped) or ((not is_go) and not tapped)

        correct_hist.append(int(correct))
        if is_go:
            go_n += 1;  go_taps += int(tapped)
        else:
            nogo_n += 1; nogo_taps += int(tapped)

        if (t + 1) % block == 0:
            acc = 100.0 * np.mean(correct_hist[-block:])
            blocks.append((t + 1, acc))

    final_acc = 100.0 * np.mean(correct_hist[-block:])
    go_rate   = 100.0 * go_taps / max(1, go_n)
    nogo_rate = 100.0 * nogo_taps / max(1, nogo_n)
    curve = "  ".join(f"{acc:4.0f}" for _, acc in blocks)
    print(f"  {name:34s} | acc/block: {curve} | "
          f"final={final_acc:5.1f}%  GO-tap={go_rate:4.0f}%  NOGO-tap={nogo_rate:4.0f}%")

    # Probe: after training, does h separate the cues, and does pm.pi follow?
    def _probe(pattern):
        cue.set_input(pattern)
        net.phase_predict(); net.phase_error(); net.phase_relax()
        return float(pm.pi[0]), net.node("h").mu.copy()
    pi_go,  h_go  = _probe(GO)
    pi_nogo, h_nogo = _probe(NOGO)
    print(f"  {'':34s}   probe: pm.pi[0] GO={pi_go:+.3f} NOGO={pi_nogo:+.3f} "
          f"(Δ={pi_go-pi_nogo:+.3f})   |h.μ(GO)-h.μ(NOGO)|={np.linalg.norm(h_go-h_nogo):.3f}")
    return {"final_acc": final_acc, "go_rate": go_rate, "nogo_rate": nogo_rate}


def main() -> None:
    print("=" * 78)
    print("  Tap-learning diagnostic — go/no-go (chance = 50%)")
    print("  Question: can neuromod = 1+gain·reward teach pm to tap on GO only?")
    print("=" * 78)
    print(f"  {'condition':34s} | learning curve (acc% per 1000 trials) ...")
    print("-" * 78)

    # CONTROL: supervised teacher, plain PC (no reward).  Establishes whether the
    # cue→pm pathway is learnable at all.
    run_condition("CONTROL supervised (pm=1.0)",
                  gain=1.0, expl=0.0, pm_pressure=1.0, supervised=True)
    run_condition("CONTROL supervised (pm=0.1)",
                  gain=1.0, expl=0.0, pm_pressure=0.1, supervised=True)

    # act5-faithful: weak premotor coupling, gain=1, NO exploration.
    run_condition("act5-like (g=1, expl=0, pm=0.1)",
                  gain=1.0, expl=0.0, pm_pressure=0.1)
    # Add exploration noise.
    run_condition("+ exploration (g=1, expl=0.3, pm=0.1)",
                  gain=1.0, expl=0.3, pm_pressure=0.1)
    # Stronger premotor coupling.
    run_condition("+ strong pm  (g=1, expl=0.3, pm=1.0)",
                  gain=1.0, expl=0.3, pm_pressure=1.0)
    # Gain > 1 (genuine un-learning of wrong actions).
    run_condition("+ gain>1     (g=2, expl=0.3, pm=1.0)",
                  gain=2.0, expl=0.3, pm_pressure=1.0)
    # Gain>1, strong pm, no exploration — does reversal alone suffice?
    run_condition("gain>1 no-expl (g=2, expl=0, pm=1.0)",
                  gain=2.0, expl=0.0, pm_pressure=1.0)
    # Best recipe, longer + more exploration — find the ceiling.
    run_condition("BEST (g=2, expl=0.5, pm=1.0, 12k)",
                  gain=2.0, expl=0.5, pm_pressure=1.0, n_trials=12000, block=2000)

    print("-" * 78)
    print("  Read: final ~50% = cannot learn the conditional tap;")
    print("        GO-tap→100 & NOGO-tap→0 = learned it.  Compare which knob unlocks it.")
    print("=" * 78)


if __name__ == "__main__":
    main()
