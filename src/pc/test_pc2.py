"""
test_pc2.py — Moving-dot sequences through a PC graph.

Architecture:
  Layer 0 (sensor):   8 SensorNodes, dim=2 each  [position, value]
  Layer 1 (hidden):   8 PCNodes,     dim=8 each  + lateral neighbours
  Layer 2 (abstract): 1 PCNode,      dim=16      connected to all hidden

Movement patterns feed one full sequence (8 frames) at a time.
After each frame the network does one PC step (relax + learn).
Terminal display shows live error bars and a scrolling history sparkline.
"""

from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.pattern_generator import PatternGenerator, SequenceSpec

# ---------------------------------------------------------------------------
# Movement patterns  (8 positions × N frames)
# Patterns used during training.
# ---------------------------------------------------------------------------

TRAIN_PATTERNS: dict[str, list[list[float]]] = {
    "one-dot L→R": [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
    ],
    "one-dot R→L": [
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
    ],
    "bounce L→mid": [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
    ],
    "bounce R→mid": [
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ],
    "two-dots L→R": [
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 1],
    ],
    "two-dots R→L": [
        [0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 1, 0, 0, 0],
    ],
}

# ---------------------------------------------------------------------------
# Novel patterns  (NOT seen during training — generalisation test)
# ---------------------------------------------------------------------------

NOVEL_PATTERNS: dict[str, list[list[float]]] = {
    # Three dots moving left-to-right
    "three-dots L→R [NEW]": [
        [1, 0, 0, 1, 0, 0, 1, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 1, 0, 0, 1, 0],
        [1, 0, 1, 0, 1, 0, 0, 1],
        [0, 1, 0, 1, 0, 1, 0, 0],
        [1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 1, 0, 1, 0, 1],
    ],
    # Two dots crossing: one L→R, one R→L simultaneously
    "crossing dots [NEW]": [
        [1, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 1],
    ],
    # Slow L→R: dot stays 2 frames before moving
    "slow L→R [NEW]": [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0,  1, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ],
    # Half intensity L→R
    "half-intensity L→R [NEW]": [
        [0.5, 0,   0,   0,   0,   0,   0,   0  ],
        [0,   0.5, 0,   0,   0,   0,   0,   0  ],
        [0,   0,   0.5, 0,   0,   0,   0,   0  ],
        [0,   0,   0,   0.5, 0,   0,   0,   0  ],
        [0,   0,   0,   0,   0.5, 0,   0,   0  ],
        [0,   0,   0,   0,   0,   0.5, 0,   0  ],
        [0,   0,   0,   0,   0,   0,   0.5, 0  ],
        [0,   0,   0,   0,   0,   0,   0,   0.5],
    ],
    # Fading intensity: starts bright, fades
    "fading L→R [NEW]": [
        [1.0, 0,   0,   0,   0,   0,   0,   0  ],
        [0,   0.85,0,   0,   0,   0,   0,   0  ],
        [0,   0,   0.7, 0,   0,   0,   0,   0  ],
        [0,   0,   0,   0.55,0,   0,   0,   0  ],
        [0,   0,   0,   0,   0.4, 0,   0,   0  ],
        [0,   0,   0,   0,   0,   0.3, 0,   0  ],
        [0,   0,   0,   0,   0,   0,   0.2, 0  ],
        [0,   0,   0,   0,   0,   0,   0,   0.1],
    ],
    # 2-pixel blob L→R
    "blob-2 L→R [NEW]": [
        [1,   0.5, 0,   0,   0,   0,   0,   0  ],
        [0.5, 1,   0.5, 0,   0,   0,   0,   0  ],
        [0,   0.5, 1,   0.5, 0,   0,   0,   0  ],
        [0,   0,   0.5, 1,   0.5, 0,   0,   0  ],
        [0,   0,   0,   0.5, 1,   0.5, 0,   0  ],
        [0,   0,   0,   0,   0.5, 1,   0.5, 0  ],
        [0,   0,   0,   0,   0,   0.5, 1,   0.5],
        [0,   0,   0,   0,   0,   0,   0.5, 1  ],
    ],
}

POSITIONS = [round(0.1 * (i + 1), 1) for i in range(8)]  # 0.1 … 0.8

# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(rng: np.random.Generator) -> tuple[PCNetwork, list[SensorNode]]:
    net = PCNetwork(
        eta_inf=0.02,
        n_relax=150,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=0.3,
        eta_learn=0.002,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )

    sensors: list[SensorNode] = []
    for i in range(8):
        s = net.add(SensorNode(f"s{i}", dim=2))
        sensors.append(s)

    for i in range(8):
        net.add(PCNode(f"h{i}", dim=8, activation="tanh", rng=rng))

    net.add(PCNode("top", dim=16, activation="tanh", rng=rng))

    for i in range(8):
        net.connect(f"h{i}", f"s{i}", ConnType.UP)

    for i in range(8):
        net.connect("top", f"h{i}", ConnType.UP, pressure_scale=0.1)

    for i in range(7):
        net.connect(f"h{i}", f"h{i+1}", ConnType.LATERAL)
        net.connect(f"h{i+1}", f"h{i}", ConnType.LATERAL)

    return net, sensors


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def set_frame(sensors: list[SensorNode], values: list[float]) -> None:
    """Push one frame of 8 [position, value] vectors into the sensor nodes."""
    for i, (s, v) in enumerate(zip(sensors, values)):
        s.set_input(np.array([POSITIONS[i], float(v)]))


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

BAR_WIDTH = 30
HISTORY_LEN = 60
SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"

def _bar(value: float, max_val: float, width: int = BAR_WIDTH) -> str:
    if not np.isfinite(value):
        return "N" * width
    filled = int(min(value / max(max_val, 1e-6), 1.0) * width)
    return "█" * filled + "░" * (width - filled)


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo or 1e-6
    chars = []
    for v in values:
        idx = int((v - lo) / span * (len(SPARKLINE_CHARS) - 1))
        chars.append(SPARKLINE_CHARS[idx])
    return "".join(chars)


def _clear_lines(n: int) -> None:
    for _ in range(n):
        sys.stdout.write("\x1b[1A\x1b[2K")


def render(
    step: int,
    total_steps: int,
    pattern_name: str | SequenceSpec,
    frame_idx: int,
    frame_values: list[float],
    sensor_err: float,
    state_err: float,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
) -> int:
    if prev_lines > 0:
        _clear_lines(prev_lines)

    dot_str = "".join(
        ("█" if v >= 0.9 else ("▓" if v >= 0.6 else ("░" if v >= 0.2 else "·")))
        for v in frame_values
    )
    pos_str = "  ".join(f"{POSITIONS[i]:.1f}" for i in range(8))

    lines = []
    lines.append(f"Step {step:5d}/{total_steps}  pattern: {pattern_name:<24s}  frame {frame_idx+1}/{len(frame_values) if hasattr(frame_values,'__len__') else 8}")
    lines.append(f"  Input:  [{dot_str}]   (█=1.0  ▓=0.6+  ░=0.2+  ·=0)")
    lines.append(f"  Pos:    [{pos_str}]")
    lines.append("")

    s_delta = ""
    st_delta = ""
    if len(sensor_history) > 1:
        d = sensor_err - sensor_history[-2]
        s_delta = f"  {'▼' if d < 0 else '▲'} {abs(d):.4f}"
    if len(state_history) > 1:
        d = state_err - state_history[-2]
        st_delta = f"  {'▼' if d < 0 else '▲'} {abs(d):.4f}"

    lines.append(f"  sensor_error  {_bar(sensor_err, max_err)}  {sensor_err:7.4f}{s_delta}")
    lines.append(f"  state_error   {_bar(state_err,  max_err)}  {state_err:7.4f}{st_delta}")
    lines.append("")

    h_sensor = sensor_history[-HISTORY_LEN:]
    h_state  = state_history[-HISTORY_LEN:]
    lines.append(f"  History (last {HISTORY_LEN} steps):")
    lines.append(f"    sensor █ {_sparkline(h_sensor)}")
    lines.append(f"    state  █ {_sparkline(h_state)}")
    lines.append("")

    print("\n".join(lines), end="", flush=True)
    return len(lines)


# ---------------------------------------------------------------------------
# Per-pattern error measurement  (no learning, no state reset)
# ---------------------------------------------------------------------------

def measure_generated_errors(
    net: PCNetwork,
    sensors: list[SensorNode],
    gen: PatternGenerator,
    n_sequences: int = 20,
) -> dict[str, float]:
    """
    Evaluate n_sequences random sequences (no learning).
    Returns mean sensor_error and state_error.
    """
    s_errs, st_errs = [], []
    for frames, _ in gen.stream(max_sequences=n_sequences):
        for frame in frames:
            set_frame(sensors, frame)
            info = net.step(learn=False)
            s_errs.append(info["sensor_error"])
            st_errs.append(info["state_error"])
    return {
        "sensor_error": float(np.mean(s_errs)),
        "state_error":  float(np.mean(st_errs)),
    }


def measure_named_errors(
    net: PCNetwork,
    sensors: list[SensorNode],
    patterns: dict[str, list[list[float]]],
    n_passes: int = 3,
) -> dict[str, dict[str, float]]:
    """Run each named pattern n_passes times (no learning)."""
    results = {}
    for name, frames in patterns.items():
        s_errs, st_errs = [], []
        for _ in range(n_passes):
            for frame in frames:
                set_frame(sensors, frame)
                info = net.step(learn=False)
                s_errs.append(info["sensor_error"])
                st_errs.append(info["state_error"])
        results[name] = {
            "sensor_error": float(np.mean(s_errs)),
            "state_error":  float(np.mean(st_errs)),
        }
    return results


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def print_summary(
    step: int,
    sensor_history: list[float],
    state_history: list[float],
    net: PCNetwork,
    sensors: list[SensorNode],
    train_gen: PatternGenerator,
    novel_gen: PatternGenerator,
) -> None:
    n = len(sensor_history)
    q = max(1, n // 10)
    first_s, last_s   = sensor_history[:q], sensor_history[-q:]
    first_st, last_st = state_history[:q],  state_history[-q:]

    print(f"\n{'='*60}")
    print(f"  Training summary")
    print(f"{'='*60}")
    print(f"  Steps completed    : {step}")
    print(f"  {'':20s}  {'start':>8s}  {'end':>8s}  {'Δ':>8s}")
    print(f"  {'sensor_error':20s}  {np.mean(first_s):8.4f}  {np.mean(last_s):8.4f}  {np.mean(first_s)-np.mean(last_s):+8.4f}")
    print(f"  {'state_error':20s}  {np.mean(first_st):8.4f}  {np.mean(last_st):8.4f}  {np.mean(first_st)-np.mean(last_st):+8.4f}")

    # Per-category breakdown on fixed named patterns
    print(f"\n{'='*60}")
    print(f"  Per-pattern errors  (fixed patterns, no learning, 3 passes)")
    print(f"{'='*60}")
    print(f"  {'Pattern':<28s}  {'sensor':>8s}  {'state':>8s}  type")
    train_r = measure_named_errors(net, sensors, TRAIN_PATTERNS)
    for name, r in sorted(train_r.items(), key=lambda x: x[1]["sensor_error"]):
        print(f"  {name:<28s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [train]")

    print(f"\n  {'Pattern':<28s}  {'sensor':>8s}  {'state':>8s}  type")
    novel_r = measure_named_errors(net, sensors, NOVEL_PATTERNS)
    for name, r in sorted(novel_r.items(), key=lambda x: x[1]["sensor_error"]):
        print(f"  {name:<28s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [novel]")

    # Generalisation: generated random sequences
    print(f"\n{'='*60}")
    print(f"  Generalisation  (20 random sequences each, no learning)")
    print(f"{'='*60}")
    tr = measure_generated_errors(net, sensors, train_gen, n_sequences=10)
    nv = measure_generated_errors(net, sensors, novel_gen, n_sequences=10)
    print(f"  {'':28s}  {'sensor':>8s}  {'state':>8s}")
    print(f"  {'train distribution':28s}  {tr['sensor_error']:8.4f}  {tr['state_error']:8.4f}")
    print(f"  {'novel distribution':28s}  {nv['sensor_error']:8.4f}  {nv['state_error']:8.4f}")
    gap = nv["sensor_error"] - tr["sensor_error"]
    print(f"  Novel−train gap  : {gap:+.4f}  ({'worse' if gap>0 else 'better'} on novel)")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rng = np.random.default_rng(42)
    net, sensors = build_network(rng)

    # Training generator: all pattern types, seeds 0–999
    train_gen = PatternGenerator(n_inputs=8, n_frames=8, seed=0)
    # Novel generator: different seed → different random parameters
    novel_gen = PatternGenerator(n_inputs=8, n_frames=8, seed=9999)

    total_steps = 8000
    repeats_per_seq = 3
    delay = 0.0

    sensor_history: list[float] = []
    state_history:  list[float] = []
    max_err = 5.0

    print(net.summary())
    print(f"\nTraining for {total_steps} steps  (generated patterns)\n")
    print("Press Ctrl+C to stop early.\n")

    prev_lines = 0
    step = 0

    try:
        for frames, spec in train_gen.stream(repeats_per_sequence=repeats_per_seq):
            for frame_idx, frame_values in enumerate(frames):
                if step >= total_steps:
                    break

                set_frame(sensors, frame_values)
                info = net.step(learn=True)

                s_err  = info["sensor_error"]
                st_err = info["state_error"]
                sensor_history.append(s_err)
                state_history.append(st_err)
                max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                prev_lines = render(
                    step + 1, total_steps, str(spec), frame_idx, frame_values,
                    s_err, st_err, sensor_history, state_history,
                    max_err, prev_lines,
                )
                step += 1

                if delay > 0:
                    time.sleep(delay)

            if step >= total_steps:
                break

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    print_summary(step, sensor_history, state_history, net, sensors, train_gen, novel_gen)


if __name__ == "__main__":
    main()
