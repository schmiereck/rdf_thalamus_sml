"""
test_pc_act1.py — Active Inference demo: pyramidal PC network with a 1D fovea.

Architecture:
  Layer 0 (sensors):  N_INPUTS SensorNodes, dim=2 each  [position, value]
                    + 1 MotorSensor,        dim=1        [eye velocity]
  Layer k (hidden):   N_INPUTS // 2**k nodes, dim = BASE_DIM + (k-1)*DIM_GROWTH
                      each connected to 2 adjacent nodes below + LATERAL_STEPS neighbours
  Top layer:          max(1, N_INPUTS // 2**N_LAYERS) nodes

Two-phase training:
  Phase 1 (passive): fovea fixed at phi=0, network learns visual motion
  Phase 2 (active):  fovea follows the network's own motor prediction
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.pattern_generator import PatternGenerator


# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(
    rng: np.random.Generator,
    n_inputs: int = 16,
    n_layers: int = 3,
    base_dim: int = 4,
    dim_growth: int = 2,
    lateral_steps: int = 1,
) -> tuple[PCNetwork, list[SensorNode], SensorNode]:
    """
    Build a pyramidal PC network with a motor sensor.

    Returns (net, visual_sensors, motor_sensor).
    """
    net = PCNetwork(
        eta_inf=0.05,
        n_relax=40,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=0.3,
        eta_learn=0.002,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )

    # Layer 0: visual sensors
    visual_sensors: list[SensorNode] = []
    for i in range(n_inputs):
        s = net.add(SensorNode(f"s{i}", dim=2))
        visual_sensors.append(s)

    # Motor sensor (efference copy of eye velocity)
    motor_sensor = net.add(SensorNode("motor", dim=1))

    # Hidden layers
    layer_widths = [max(1, n_inputs // (2 ** k)) for k in range(1, n_layers + 1)]
    layer_dims   = [base_dim + (k - 1) * dim_growth for k in range(1, n_layers + 1)]

    for k, (width, dim) in enumerate(zip(layer_widths, layer_dims), start=1):
        for j in range(width):
            net.add(PCNode(f"h{k}_{j}", dim=dim, activation="tanh", rng=rng))

    # UP connections: each hidden node ← 2 adjacent nodes in the layer below
    # Layer 1 ← sensors
    width1 = layer_widths[0]
    for j in range(width1):
        ps = 1.0
        net.connect(f"h1_{j}", f"s{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"s{2*j+1}", ConnType.UP, pressure_scale=ps)

    # Layer k+1 ← layer k  (with weakened back-pressure for top connections)
    for k in range(1, n_layers):
        width_above = layer_widths[k]
        is_top_connection = (k == n_layers - 1)
        ps = 0.1 if is_top_connection else 1.0
        for j in range(width_above):
            net.connect(f"h{k+1}_{j}", f"h{k}_{2*j}",   ConnType.UP, pressure_scale=ps)
            net.connect(f"h{k+1}_{j}", f"h{k}_{2*j+1}", ConnType.UP, pressure_scale=ps)

    # Lateral connections within each hidden layer
    for k in range(1, n_layers + 1):
        width = layer_widths[k - 1]
        for j in range(width):
            for d in range(1, lateral_steps + 1):
                if j + d < width:
                    net.connect(f"h{k}_{j}",   f"h{k}_{j+d}", ConnType.LATERAL)
                    net.connect(f"h{k}_{j+d}", f"h{k}_{j}",   ConnType.LATERAL)

    # Motor connections: top layer → motor sensor
    width_top = layer_widths[-1]
    for j in range(width_top):
        net.connect(f"h{n_layers}_{j}", "motor", ConnType.UP, pressure_scale=0.05)

    return net, visual_sensors, motor_sensor


# ---------------------------------------------------------------------------
# Fovea helpers
# ---------------------------------------------------------------------------

def apply_fovea_shift(world_frame: list[float], phi: float, n: int) -> list[float]:
    """Circular shift of world_frame by phi (integer pixels)."""
    offset = round(phi) % n
    if offset == 0:
        return world_frame
    arr = np.array(world_frame)
    return np.roll(arr, -offset).tolist()


def compute_action_gradient(
    visual_sensors: list[SensorNode],
    image: list[float],
) -> float:
    """
    Active-inference action signal:  ∂E/∂φ  for  E = ½ Σ (value error)².

    Must be called *after* phase_predict + phase_error but *before* relaxation,
    so that the sensor value-channel error is the network's temporal prediction
    error (the carried-over hidden state predicts the new frame → the residual
    is the retinal slip).

    Moving the eye right by δφ slides the retinal image left, so
        ∂image[i]/∂φ ≈ image[i+1] - image[i]   (circular forward difference).
    Hence
        ∂E/∂φ = Σ_i e_i · (image[i+1] - image[i]).

    Gradient descent on the eye position then drives:  v = -gain · ∂E/∂φ,
    which (verified by sign analysis) makes the eye follow the object's motion.
    """
    e = np.array([s.epsilon[1] for s in visual_sensors])   # value-channel error
    img = np.array(image)
    grad = np.roll(img, -1) - img                          # spatial gradient
    return float(np.sum(e * grad))


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _positions(n: int) -> list[float]:
    """Retinal positions: evenly spaced in (0, 1], length n."""
    step = 1.0 / n
    return [round(step * (i + 1), 4) for i in range(n)]


def set_frame(visual_sensors: list[SensorNode], values: list[float]) -> None:
    """Push [retinal_position, value] into visual sensor nodes."""
    pos = _positions(len(visual_sensors))
    for i, (s, v) in enumerate(zip(visual_sensors, values)):
        s.set_input(np.array([pos[i], float(v)]))


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

BAR_WIDTH = 28
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
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return "?" * len(values)
    lo, hi = min(finite), max(finite)
    span = hi - lo or 1e-6
    chars = []
    for v in values:
        if not np.isfinite(v):
            chars.append("?")
        else:
            idx = int((v - lo) / span * (len(SPARKLINE_CHARS) - 1))
            chars.append(SPARKLINE_CHARS[idx])
    return "".join(chars)


def _clear_lines(n: int) -> None:
    for _ in range(n):
        sys.stdout.write("\x1b[1A\x1b[2K")


def render(
    step: int,
    total_steps: int,
    pattern_name: str,
    frame_idx: int,
    frame_values: list[float],
    sensor_err: float,
    state_err: float,
    motor_err: float,
    phi: float,
    v: float,
    action_enabled: bool,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
) -> int:
    if prev_lines > 0:
        _clear_lines(prev_lines)

    n = len(frame_values)
    dot_str = "".join(
        ("█" if val >= 0.9 else ("▓" if val >= 0.6 else ("░" if val >= 0.2 else "·")))
        for val in frame_values
    )
    pos_str = "  ".join(f"{p:.2f}" for p in _positions(n))
    phase_str = "Phase 2 [ACTIVE]" if action_enabled else "Phase 1 [passive]"

    lines = []
    lines.append(
        f"Step {step:5d}/{total_steps}  {phase_str}  "
        f"pattern: {pattern_name:<36s}  frame {frame_idx+1}/{n}"
    )
    lines.append(f"  Input:  [{dot_str}]   (█=1.0  ▓=0.6+  ░=0.2+  ·=0)")
    lines.append(f"  Pos:    [{pos_str}]")
    lines.append(f"  Fovea:  φ={phi:5.1f}  v={v:+.2f}")
    lines.append("")

    s_delta = st_delta = m_delta = ""
    if len(sensor_history) > 1:
        d = sensor_err - sensor_history[-2]
        s_delta = f"  {'▼' if d < 0 else '▲'} {abs(d):.4f}"
    if len(state_history) > 1:
        d = state_err - state_history[-2]
        st_delta = f"  {'▼' if d < 0 else '▲'} {abs(d):.4f}"

    lines.append(f"  sensor_error  {_bar(sensor_err, max_err)}  {sensor_err:7.4f}{s_delta}")
    lines.append(f"  state_error   {_bar(state_err,  max_err)}  {state_err:7.4f}{st_delta}")
    lines.append(f"  motor_error   {_bar(motor_err,  max_err)}  {motor_err:7.4f}{m_delta}")
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
    """Draw n_sequences from gen and return [(description, frames), ...]."""
    return [(str(spec), frames) for frames, spec in gen.stream(max_sequences=n_sequences)]


def measure_per_pattern_errors(
    net: PCNetwork,
    visual_sensors: list[SensorNode],
    motor_sensor: SensorNode,
    named_patterns: list[tuple[str, list[list[float]]]],
    n_inputs: int,
    n_passes: int = 3,
) -> list[tuple[str, dict[str, float]]]:
    """Run each named pattern n_passes times (no action, no learning)."""
    results = []
    for name, frames in named_patterns:
        s_errs, st_errs, m_errs = [], [], []
        for _ in range(n_passes):
            for frame in frames:
                set_frame(visual_sensors, frame)
                motor_sensor.set_input(np.array([0.0]))
                info = net.step(learn=False)
                m_err = float(np.sum(net.node("motor").epsilon ** 2))
                s_errs.append(info["sensor_error"] - m_err)   # visual only
                st_errs.append(info["state_error"])
                m_errs.append(m_err)
        results.append((name, {
            "sensor_error": float(np.mean(s_errs)),
            "state_error":  float(np.mean(st_errs)),
            "motor_error":  float(np.mean(m_errs)),
        }))
    results.sort(key=lambda x: x[1]["sensor_error"])
    return results


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def print_summary(
    step: int,
    sensor_history: list[float],
    state_history: list[float],
    motor_history: list[float],
    net: PCNetwork,
    visual_sensors: list[SensorNode],
    motor_sensor: SensorNode,
    train_patterns: list[tuple[str, list[list[float]]]],
    novel_patterns: list[tuple[str, list[list[float]]]],
    n_inputs: int,
    passive_steps: int,
) -> None:
    n = len(sensor_history)
    q = max(1, n // 10)
    first_s,  last_s  = sensor_history[:q], sensor_history[-q:]
    first_st, last_st = state_history[:q],  state_history[-q:]
    first_m,  last_m  = motor_history[:q],  motor_history[-q:]

    print(f"\n{'='*62}")
    print(f"  Training summary")
    print(f"{'='*62}")
    print(f"  Steps completed    : {step}  (Phase 2 started at step {passive_steps})")
    print(f"  {'':20s}  {'start':>8s}  {'end':>8s}  {'Δ':>8s}")
    for label, first, last in [
        ("sensor_error", first_s, last_s),
        ("state_error",  first_st, last_st),
        ("motor_error",  first_m,  last_m),
    ]:
        print(f"  {label:20s}  {np.mean(first):8.4f}  {np.mean(last):8.4f}"
              f"  {np.mean(first)-np.mean(last):+8.4f}")

    col = 40
    print(f"\n{'='*62}")
    print(f"  Per-pattern errors  ({len(train_patterns)} train / {len(novel_patterns)} novel,"
          f" no learning, 3 passes)")
    print(f"{'='*62}")
    print(f"  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  {'motor':>8s}  type")

    for name, r in measure_per_pattern_errors(net, visual_sensors, motor_sensor,
                                               train_patterns, n_inputs):
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}"
              f"  {r['motor_error']:8.4f}  [train]")

    print(f"\n  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  {'motor':>8s}  type")
    novel_results = measure_per_pattern_errors(net, visual_sensors, motor_sensor,
                                               novel_patterns, n_inputs)
    for name, r in novel_results:
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}"
              f"  {r['motor_error']:8.4f}  [novel]")

    tr_mean = float(np.mean([r["sensor_error"]
                             for _, r in measure_per_pattern_errors(
                                 net, visual_sensors, motor_sensor, train_patterns, n_inputs)]))
    nv_mean = float(np.mean([r["sensor_error"] for _, r in novel_results]))
    gap = nv_mean - tr_mean
    print(f"\n  {'train mean (sensor)':28s}  {tr_mean:8.4f}")
    print(f"  {'novel mean (sensor)':28s}  {nv_mean:8.4f}")
    print(f"  Novel−train gap  : {gap:+.4f}  ({'worse' if gap>0 else 'better'} on novel)")
    print(f"{'='*62}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---------------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------------
    N_INPUTS          = 16   # visual sensor positions
    N_LAYERS          = 3    # hidden pyramid layers (depth)
    BASE_DIM          = 4    # state dim at layer 1
    DIM_GROWTH        = 2    # dim increment per layer
    LATERAL_STEPS     = 1    # lateral neighbours per side
    N_TRAIN_PATTERNS  = 10   # how many different patterns to train on
    N_NOVEL_PATTERNS  = 10   # how many different patterns for evaluation only
    REPEATS_PER_SEQ   = 3    # repeats of each pattern per epoch
    N_EPOCHS_PASSIVE  = 12   # Phase 1: no action, learn to predict motion
                             #   (motor_error is trivially 0 here: v=0, nothing to predict)
    N_EPOCHS_ACTIVE   = 38   # Phase 2: action enabled (visual-error gradient)
    MAX_V             = 2.0  # max eye velocity in pixels/step
    ACTION_GAIN       = 0.7  # gradient → velocity gain (v = -gain · ∂E/∂φ);
                             #   higher = tighter tracking, less lag (risk: oscillation)
    ACTION_SMOOTH     = 0.2  # velocity momentum (0 = none, blends previous v)
    DELAY             = 0.0  # seconds between steps
    # ---------------------------------------------------------------

    rng = np.random.default_rng(42)
    net, visual_sensors, motor_sensor = build_network(
        rng,
        n_inputs=N_INPUTS,
        n_layers=N_LAYERS,
        base_dim=BASE_DIM,
        dim_growth=DIM_GROWTH,
        lateral_steps=LATERAL_STEPS,
    )

    # Sample fixed pattern sets once
    train_patterns = sample_named_patterns(
        PatternGenerator(n_inputs=N_INPUTS, seed=0, bias_simple=True),
        n_sequences=N_TRAIN_PATTERNS,
    )
    novel_patterns = sample_named_patterns(
        PatternGenerator(n_inputs=N_INPUTS, seed=9999),
        n_sequences=N_NOVEL_PATTERNS,
    )

    total_steps = (
        sum(len(frames) for _, frames in train_patterns)
        * REPEATS_PER_SEQ
        * (N_EPOCHS_PASSIVE + N_EPOCHS_ACTIVE)
    )

    sensor_history: list[float] = []
    state_history:  list[float] = []
    motor_history:  list[float] = []
    max_err = 5.0

    print(net.summary())
    print(f"\nPyramid: {N_INPUTS} inputs → "
          + " → ".join(str(max(1, N_INPUTS // 2**k)) for k in range(1, N_LAYERS + 1))
          + " (top)")
    print(f"Dims:    2 → "
          + " → ".join(str(BASE_DIM + (k-1)*DIM_GROWTH) for k in range(1, N_LAYERS + 1)))
    print(f"\nPhase 1: {N_EPOCHS_PASSIVE} epochs (passive, φ=0, learn to predict)")
    print(f"Phase 2: {N_EPOCHS_ACTIVE} epochs  (active, fovea = -gain·∂E/∂φ)")
    print(f"Total  : ≈{total_steps} steps\n")
    print("Press Ctrl+C to stop early.\n")

    prev_lines = 0
    step = 0
    passive_steps = 0
    phi = 0.0
    v   = 0.0

    try:
        for epoch in range(N_EPOCHS_PASSIVE + N_EPOCHS_ACTIVE):
            action_enabled = (epoch >= N_EPOCHS_PASSIVE)
            phi = 0.0
            v   = 0.0

            if epoch == N_EPOCHS_PASSIVE:
                passive_steps = step

            for name, world_frames in train_patterns:
                for _ in range(REPEATS_PER_SEQ):
                    for frame_idx, world_frame in enumerate(world_frames):
                        # Apply fovea shift and feed sensors
                        shifted = apply_fovea_shift(world_frame, phi, N_INPUTS)
                        set_frame(visual_sensors, shifted)
                        motor_sensor.set_input(np.array([v / MAX_V]))  # efference copy, [-1, 1]

                        # Capture the action signal from the temporal prediction
                        # error (pre-relaxation): the carried-over hidden state
                        # predicts the new frame, so the residual is the slip.
                        action_grad = 0.0
                        if action_enabled:
                            net.phase_predict()
                            net.phase_error()
                            action_grad = compute_action_gradient(visual_sensors, shifted)

                        # Full PC step (predict/error/relax/learn) — clean diagnostics
                        info = net.step(learn=True)

                        m_err  = float(np.sum(net.node("motor").epsilon ** 2))
                        s_err  = info["sensor_error"] - m_err   # visual only
                        st_err = info["state_error"]

                        # Guard against transient non-finite values in the history
                        s_err  = s_err  if np.isfinite(s_err)  else max_err
                        st_err = st_err if np.isfinite(st_err) else max_err
                        m_err  = m_err  if np.isfinite(m_err)  else max_err

                        sensor_history.append(s_err)
                        state_history.append(st_err)
                        motor_history.append(m_err)
                        max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                        prev_lines = render(
                            step + 1, total_steps, name, frame_idx, shifted,
                            s_err, st_err, m_err, phi, v, action_enabled,
                            sensor_history, state_history, max_err, prev_lines,
                        )
                        step += 1

                        # Apply the action: descend the visual-error gradient.
                        if action_enabled:
                            v_target = -ACTION_GAIN * action_grad
                            v = float(np.clip(
                                (1.0 - ACTION_SMOOTH) * v_target + ACTION_SMOOTH * v,
                                -MAX_V, MAX_V,
                            ))
                            phi = (phi + v) % N_INPUTS

                        if DELAY > 0:
                            time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    print_summary(
        step, sensor_history, state_history, motor_history,
        net, visual_sensors, motor_sensor,
        train_patterns, novel_patterns,
        N_INPUTS, passive_steps,
    )


if __name__ == "__main__":
    main()
