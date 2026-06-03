"""
test_pc_forward.py — does the temporal forward model V actually anticipate?

Minimal sequence: a single "on" pixel travels across a 3-pixel retina,
cyclically:

        frame 0   [1, 0, 0]
        frame 1   [0, 1, 0]
        frame 2   [0, 0, 1]   -> back to frame 0 ...

If the per-node forward model V learns the temporal transition, then at the
START of each frame (Phase 1, before any hierarchical relaxation) the network's
top-down prediction should already anticipate the upcoming pixel.  We measure
the "initial surprise" = sensor prediction error right after Phase 1.

A working forward model must produce LOWER initial surprise on the ordered
(predictable) sequence than on a SCRAMBLED order of the very same frames —
because only the ordered sequence has a learnable next-state structure.

Run:  python src/pc/test_pc_forward.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType


def build_net(rng: np.random.Generator) -> tuple[PCNetwork, SensorNode]:
    """Tiny 2-layer net: 3-pixel sensor <- one 6-dim hidden node."""
    net = PCNetwork(
        eta_inf=0.1,
        n_relax=30,
        eps_tol=1e-6,
        alpha=1.0,
        beta=1.0,
        gamma=1.0,
        eta_learn=0.01,
        eta_temporal=0.01,
        lambda_decay=0.0,
        w_clip=5.0,
        rng=rng,
    )
    sensor = net.add(SensorNode("i1", dim=3))
    net.add(PCNode("a1", dim=6, activation="tanh", rng=rng))
    net.connect("a1", "i1", ConnType.UP)
    return net, sensor


def initial_surprise(net: PCNetwork, sensor: SensorNode, frame: np.ndarray) -> float:
    """
    Drive one frame and return the sensor error measured AFTER Phase 1
    (prediction warm-start + top-down predict) but BEFORE relaxation.
    Then finish the full cycle (relax + learn + commit) so the forward
    model still advances normally.
    """
    sensor.set_input(frame)
    net.phase_predict()                 # load V prediction + hierarchical pi
    net.phase_error()                   # epsilon = mu - pi
    surprise = float(np.sum(sensor.epsilon ** 2))
    net.phase_relax()
    net.phase_learn()
    net.commit_step()
    return surprise


def main() -> None:
    rng = np.random.default_rng(0)
    net, sensor = build_net(rng)

    frames = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
    ]

    # ---- Train on the ordered travelling pulse ----
    N_CYCLES = 400
    for _ in range(N_CYCLES):
        for f in frames:
            sensor.set_input(f)
            net.step(learn=True)
            net.commit_step()

    # ---- Evaluate: ordered vs scrambled initial surprise (no learning bias) ----
    # Ordered: continue the learned cycle for several laps.
    ordered = []
    for _ in range(20):
        for f in frames:
            ordered.append(initial_surprise(net, sensor, f))

    # Scrambled: same three frames, but in a randomised order each step so the
    # learned next-state transition no longer matches what actually arrives.
    scrambled = []
    order = rng.integers(0, 3, size=60)
    for idx in order:
        scrambled.append(initial_surprise(net, sensor, frames[idx]))

    mo, ms = float(np.mean(ordered)), float(np.mean(scrambled))

    print("=" * 60)
    print("  Forward-model anticipation test (travelling 3-pixel pulse)")
    print("=" * 60)
    print(f"  initial surprise  ORDERED   sequence : {mo:.4f}")
    print(f"  initial surprise  SCRAMBLED sequence : {ms:.4f}")
    print(f"  anticipation gain (scrambled/ordered): {ms / mo:.2f}x")
    print("-" * 60)

    # ---- Direct readout: what does the net predict the NEXT frame to be? ----
    # Seed with frame 0, then read the top-down reconstruction the net settles
    # on for each subsequent step of one clean lap.
    print("  One clean lap — top-down sensor prediction pi vs. truth:")
    sensor.set_input(frames[0])
    net.step(learn=False)
    net.commit_step()
    for step, f in enumerate([frames[1], frames[2], frames[0]], start=1):
        sensor.set_input(f)
        net.phase_predict()
        net.phase_error()
        pi = sensor.pi.copy()           # network's expectation for this frame
        net.phase_relax()
        net.commit_step()
        pred_pos = int(np.argmax(pi))
        true_pos = int(np.argmax(f))
        hit = "OK " if pred_pos == true_pos else "MISS"
        print(f"    step {step}: pi={np.round(pi, 3)}  argmax={pred_pos}  "
              f"truth={true_pos}  [{hit}]")
    print("=" * 60)

    if ms > mo * 1.15:
        print(f"  PASS: ordered sequence is anticipated "
              f"({ms / mo:.2f}x less surprising than scrambled)")
    else:
        print(f"  WEAK: forward model gives little anticipation "
              f"(gain only {ms / mo:.2f}x)")


if __name__ == "__main__":
    main()
