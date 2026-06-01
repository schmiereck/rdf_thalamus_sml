"""
test_pc_gen1.py — Moving-dot sequences through a PC graph using PatternGenerator.

Architecture:
  Layer 0 (sensor):   8 SensorNodes, dim=2 each  [position, value]
  Layer 1 (hidden):   8 PCNodes,     dim=8 each  + lateral neighbours
  Layer 2 (abstract): 1 PCNode,      dim=16      connected to all hidden

Training uses PatternGenerator to produce an endless variety of 1D motion
sequences. Evaluation compares errors on train-distribution vs. novel-distribution
sequences (different RNG seed → different random parameters).
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.pattern_generator import PatternGenerator, SequenceSpec

def _positions(n: int) -> list[float]:
    """Evenly spaced sensor positions in (0, 1], length n."""
    step = 1.0 / n
    return [round(step * (i + 1), 4) for i in range(n)]

POSITIONS = _positions(8)  # default; overridden in set_frame via sensor list length

# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(rng: np.random.Generator, n_inputs: int = 8) -> tuple[PCNetwork, list[SensorNode]]:
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
    for i in range(n_inputs):
        s = net.add(SensorNode(f"s{i}", dim=2))
        sensors.append(s)

    for i in range(n_inputs):
        net.add(PCNode(f"h{i}", dim=8, activation="tanh", rng=rng))

    net.add(PCNode("top", dim=n_inputs * 2, activation="tanh", rng=rng))

    for i in range(n_inputs):
        net.connect(f"h{i}", f"s{i}", ConnType.UP)

    for i in range(n_inputs):
        net.connect("top", f"h{i}", ConnType.UP, pressure_scale=0.1)

    for i in range(n_inputs - 1):
        net.connect(f"h{i}", f"h{i+1}", ConnType.LATERAL)
        net.connect(f"h{i+1}", f"h{i}", ConnType.LATERAL)

    return net, sensors


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def set_frame(sensors: list[SensorNode], values: list[float]) -> None:
    """Push one frame of n [position, value] vectors into the sensor nodes."""
    pos = _positions(len(sensors))
    for i, (s, v) in enumerate(zip(sensors, values)):
        s.set_input(np.array([pos[i], float(v)]))


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
    spec: SequenceSpec,
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
    n = len(frame_values)
    pos_str = "  ".join(f"{p:.2f}" for p in _positions(n))

    lines = []
    lines.append(f"Step {step:5d}/{total_steps}  pattern: {str(spec):<40s}  frame {frame_idx+1}/{n}")
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
# Per-pattern error measurement  (no learning)
# ---------------------------------------------------------------------------

def sample_named_patterns(
    gen: PatternGenerator,
    n_sequences: int,
) -> list[tuple[str, list[list[float]]]]:
    """
    Draw n_sequences from gen and return [(description, frames), ...].
    Uses a fresh copy of the generator state so the main training stream
    is not disturbed — caller should pass a generator with a fixed seed.
    """
    return [(str(spec), frames) for frames, spec in gen.stream(max_sequences=n_sequences)]


def measure_per_pattern_errors(
    net: PCNetwork,
    sensors: list[SensorNode],
    named_patterns: list[tuple[str, list[list[float]]]],
    n_passes: int = 3,
) -> list[tuple[str, dict[str, float]]]:
    """Run each named pattern n_passes times (no learning). Returns sorted results."""
    results = []
    for name, frames in named_patterns:
        s_errs, st_errs = [], []
        for _ in range(n_passes):
            for frame in frames:
                set_frame(sensors, frame)
                info = net.step(learn=False)
                s_errs.append(info["sensor_error"])
                st_errs.append(info["state_error"])
        results.append((name, {
            "sensor_error": float(np.mean(s_errs)),
            "state_error":  float(np.mean(st_errs)),
        }))
    results.sort(key=lambda x: x[1]["sensor_error"])
    return results


def measure_distribution_errors(
    net: PCNetwork,
    sensors: list[SensorNode],
    gen: PatternGenerator,
    n_sequences: int = 20,
) -> dict[str, float]:
    """Evaluate n_sequences random sequences (no learning). Returns mean errors."""
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


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def print_summary(
    step: int,
    sensor_history: list[float],
    state_history: list[float],
    net: PCNetwork,
    sensors: list[SensorNode],
    train_eval_patterns: list[tuple[str, list[list[float]]]],
    novel_eval_patterns: list[tuple[str, list[list[float]]]],
    train_gen: PatternGenerator,
    novel_gen: PatternGenerator,
    n_gen_patterns: int = 20,
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

    # Per-pattern breakdown
    print(f"\n{'='*60}")
    print(f"  Per-pattern errors  (fixed eval set, no learning, 3 passes)")
    print(f"{'='*60}")
    col = 40
    print(f"  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  type")
    for name, r in measure_per_pattern_errors(net, sensors, train_eval_patterns):
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [train]")

    print(f"\n  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  type")
    for name, r in measure_per_pattern_errors(net, sensors, novel_eval_patterns):
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [novel]")

    # Generalisation: fresh random sequences, per-pattern + distribution summary
    print(f"\n{'='*60}")
    print(f"  Generalisation  ({n_gen_patterns} random sequences each, no learning)")
    print(f"{'='*60}")
    gen_train_patterns = sample_named_patterns(train_gen, n_sequences=n_gen_patterns)
    gen_novel_patterns = sample_named_patterns(novel_gen, n_sequences=n_gen_patterns)

    print(f"  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  dist")
    train_results = measure_per_pattern_errors(net, sensors, gen_train_patterns)
    for name, r in train_results:
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [train]")

    print()
    novel_results = measure_per_pattern_errors(net, sensors, gen_novel_patterns)
    for name, r in novel_results:
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}  [novel]")

    tr_mean = float(np.mean([r["sensor_error"] for _, r in train_results]))
    nv_mean = float(np.mean([r["sensor_error"] for _, r in novel_results]))
    gap = nv_mean - tr_mean
    print(f"\n  {'train mean':28s}  {tr_mean:8.4f}")
    print(f"  {'novel mean':28s}  {nv_mean:8.4f}")
    print(f"  Novel−train gap  : {gap:+.4f}  ({'worse' if gap>0 else 'better'} on novel)")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---------------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------------
    N_INPUTS          = 8     # sensor positions (also sets PatternGenerator width)
    N_FRAMES          = 8     # frames per sequence
    TOTAL_STEPS       = 1500  # training steps
    REPEATS_PER_SEQ   = 3     # how often each generated sequence is repeated
    N_EVAL_PATTERNS   = 6     # fixed per-pattern eval set size (train + novel each)
    N_GEN_PATTERNS    = 20    # sequences per distribution in Generalisation section
    DELAY             = 0.0   # seconds between steps (0 = as fast as possible)
    # ---------------------------------------------------------------

    rng = np.random.default_rng(42)
    net, sensors = build_network(rng, n_inputs=N_INPUTS)

    # Training generator: bias toward simple patterns
    train_gen = PatternGenerator(n_inputs=N_INPUTS, n_frames=N_FRAMES, seed=0, bias_simple=True)
    # Novel generator: uniform distribution (tests broad generalisation)
    novel_gen = PatternGenerator(n_inputs=N_INPUTS, n_frames=N_FRAMES, seed=9999)

    # Fixed eval sets sampled once before training (separate generator instances
    # with offset seeds so they don't overlap with the training stream)
    train_eval_patterns = sample_named_patterns(
        PatternGenerator(n_inputs=N_INPUTS, n_frames=N_FRAMES, seed=1, bias_simple=True),
        n_sequences=N_EVAL_PATTERNS,
    )
    novel_eval_patterns = sample_named_patterns(
        PatternGenerator(n_inputs=N_INPUTS, n_frames=N_FRAMES, seed=10000),
        n_sequences=N_EVAL_PATTERNS,
    )

    sensor_history: list[float] = []
    state_history:  list[float] = []
    max_err = 5.0

    print(net.summary())
    print(f"\nTraining for {TOTAL_STEPS} steps  (generated patterns)\n")
    print("Press Ctrl+C to stop early.\n")

    prev_lines = 0
    step = 0

    try:
        for frames, spec in train_gen.stream(repeats_per_sequence=REPEATS_PER_SEQ):
            for frame_idx, frame_values in enumerate(frames):
                if step >= TOTAL_STEPS:
                    break

                set_frame(sensors, frame_values)
                info = net.step(learn=True)

                s_err  = info["sensor_error"]
                st_err = info["state_error"]
                sensor_history.append(s_err)
                state_history.append(st_err)
                max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                prev_lines = render(
                    step + 1, TOTAL_STEPS, spec, frame_idx, frame_values,
                    s_err, st_err, sensor_history, state_history,
                    max_err, prev_lines,
                )
                step += 1

                if DELAY > 0:
                    time.sleep(DELAY)

            if step >= TOTAL_STEPS:
                break

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    print_summary(
        step, sensor_history, state_history, net, sensors,
        train_eval_patterns, novel_eval_patterns,
        train_gen, novel_gen,
        n_gen_patterns=N_GEN_PATTERNS,
    )


if __name__ == "__main__":
    main()
