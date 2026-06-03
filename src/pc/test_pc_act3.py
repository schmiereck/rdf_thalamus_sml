"""
test_pc_act3.py — Active Inference demo: 1D fovea + a movable POINTER.

Builds on test_pc_act2.py (bouncing patterns, fovea tracking) and adds a
second "pointer" row to the world and to the sensors.

World (two rows):
  Object-row :  the moving blob patterns (as before)
  Pointer-row:  a visible 2-pixel pointer with physical mass/acceleration

Sensors (one shared sensor layer, two rows, hexagonally coupled):
      so0--so1--so2-- ...        (object-row sensors,  dim=2 [pos, value])
     /  \ /  \ /  \
   sp0--sp1--sp2--sp3 ...        (pointer-row sensors, dim=2 [pos, value])
  Each object sensor is laterally connected to its two diagonal pointer
  neighbours (hexagon), so the network learns the joint object/pointer layout
  and the pointer-row prediction error ε drives the pointer's active inference.

Two independent effectors, both gradient-driven (∂E/∂·):
  Fovea  : velocity-controlled window over the world          (as in act2)
  Pointer: force-controlled (mass + acceleration), pulled by a weak spring
           toward the centre of gaze; otherwise free to roam the whole world.

Motor sensor is now 2-dim [v_fovea, v_pointer] (extensible to a 2-D image).

Pointer Phase 1 (this file): no goal is prescribed — we just let the pointer
loose and observe what its gradient action does.

Pointer Phase 2 (future): add a y-action into the object row, give objects
real mass so the pointer can nudge them.

Architecture:
  Layer 0 (sensors):  N_INPUTS object + N_INPUTS pointer SensorNodes, dim=2
                    + 1 MotorSensor, dim=2  [v_fovea, v_pointer]
  Layer k (hidden):   N_INPUTS // 2**k nodes, dim = BASE_DIM + (k-1)*DIM_GROWTH
                      each fed by 2 adjacent object + 2 adjacent pointer sensors
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
    eta_inf: float = 0.05,
    n_relax: int = 40,
    eta_learn: float = 0.002,
    gamma: float = 0.3,
) -> tuple[PCNetwork, list[SensorNode], list[SensorNode], SensorNode]:
    """
    Build a pyramidal PC network with two sensor rows (object + pointer),
    hexagonally coupled, and a 2-dim motor sensor [v_fovea, v_pointer].

    Temporal memory is handled by each PCNode's internal V forward model.

    Returns (net, object_sensors, pointer_sensors, motor_sensor).
    """
    net = PCNetwork(
        eta_inf=eta_inf,
        n_relax=n_relax,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=gamma,
        eta_learn=eta_learn,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )

    # Layer 0: two sensor rows in one shared sensor layer.
    #   so{i} = object-row sensor   [retinal_pos, object_value]
    #   sp{i} = pointer-row sensor  [retinal_pos, pointer_value]
    object_sensors: list[SensorNode] = []
    pointer_sensors: list[SensorNode] = []
    for i in range(n_inputs):
        object_sensors.append(net.add(SensorNode(f"so{i}", dim=2)))
    for i in range(n_inputs):
        pointer_sensors.append(net.add(SensorNode(f"sp{i}", dim=2)))

    # Hexagonal lateral coupling between the two rows: object sensor j is tied
    # to its two diagonal pointer neighbours (j and j+1).  Reciprocal LATERAL
    # connections let each row predict the other; the pointer-row prediction
    # error then drives the pointer's active inference.
    # pressure_scale=0.1: weak cross-row back-pressure keeps state_error bounded;
    # the rows have very different content so full-strength coupling explodes state_error.
    HEX_PS = 0.1
    for j in range(n_inputs):
        for jp in (j, j + 1):
            if 0 <= jp < n_inputs:
                net.connect(f"so{j}", f"sp{jp}", ConnType.LATERAL, pressure_scale=HEX_PS)
                net.connect(f"sp{jp}", f"so{j}", ConnType.LATERAL, pressure_scale=HEX_PS)

    # Motor sensor: efference copy of both effector velocities.
    motor_sensor = net.add(SensorNode("motor", dim=2))

    # Hidden layers
    layer_widths = [max(1, n_inputs // (2 ** k)) for k in range(1, n_layers + 1)]
    layer_dims   = [base_dim + (k - 1) * dim_growth for k in range(1, n_layers + 1)]

    for k, (width, dim) in enumerate(zip(layer_widths, layer_dims), start=1):
        for j in range(width):
            net.add(PCNode(f"h{k}_{j}", dim=dim, activation="tanh", rng=rng))

    # UP connections: each layer-1 hidden node ← 2 adjacent object sensors
    # AND the 2 corresponding pointer sensors (joint receptive field).
    width1 = layer_widths[0]
    for j in range(width1):
        ps = 1.0
        net.connect(f"h1_{j}", f"so{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"so{2*j+1}", ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j+1}", ConnType.UP, pressure_scale=ps)

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

    # Motor connections: top layer → motor sensor (now 2-dim)
    width_top = layer_widths[-1]
    for j in range(width_top):
        net.connect(f"h{n_layers}_{j}", "motor", ConnType.UP, pressure_scale=0.05)

    return net, object_sensors, pointer_sensors, motor_sensor


# ---------------------------------------------------------------------------
# Fovea helpers
# ---------------------------------------------------------------------------

def apply_fovea_shift(world_frame: list[float], phi: float, n_inputs: int) -> list[float]:
    """Extract n_inputs-wide window from world_frame starting at pixel round(phi).

    phi=0 means the sensor window is exactly aligned with the world (full view).
    Negative phi shifts the window left (world content enters from right side, zeros on left).
    Positive phi shifts the window right (world content exits to left, zeros on right).
    Pixels outside world bounds are zero-padded.
    """
    offset = round(phi)
    world_len = len(world_frame)
    result = []
    for i in range(n_inputs):
        wi = offset + i
        result.append(float(world_frame[wi]) if 0 <= wi < world_len else 0.0)
    return result


def world_com(frame: list[float]) -> float | None:
    """Intensity-weighted centre of mass of a world frame, or None if empty."""
    arr = np.asarray(frame, dtype=float)
    total = arr.sum()
    if total < 1e-6:
        return None
    return float((np.arange(arr.size) * arr).sum() / total)


def retinal_com(values: list[float] | np.ndarray) -> float | None:
    """Intensity-weighted centre of mass of a retinal image, in pixel units.

    Returns None if the image is essentially empty (no object visible).
    """
    arr = np.asarray(values, dtype=float)
    arr = np.clip(arr, 0.0, None)   # ignore negative activations
    total = arr.sum()
    if total < 1e-4:
        return None
    return float((np.arange(arr.size) * arr).sum() / total)


def compute_action_pred_com(
    visual_sensors: list[SensorNode],
    n_inputs: int,
    target_frac: float = 0.5,
) -> float:
    """
    Predictive-COM action signal.

    After phase_predict(), each sensor s has s.pi[1] = the network's top-down
    prediction of the value at that retinal position, derived from the previous
    frame's hidden state via the learned recurrent connections.

    We compute the centre of mass of this *predicted* retinal image and drive
    the fovea toward it:

        v_target = GAIN · (com_pred − target_pixel)

    where target_pixel = target_frac · n_inputs  (default: centre of retina).

    This is fundamentally different from the gradient approach: we are using
    the prediction as a STEERING TARGET rather than differentiating through it.
    If the recurrent connections have learned that the object moves rightward,
    com_pred will already be shifted right, and the fovea will follow.

    Returns the raw displacement (com_pred − target_pixel); the caller
    multiplies by a gain.  Returns 0.0 if the prediction is empty.
    """
    pi = np.array([s.pi[1] for s in visual_sensors])
    com = retinal_com(pi)
    if com is None:
        return 0.0
    target_px = target_frac * n_inputs
    return float(com - target_px)


def compute_action_velocity_com(
    image: list[float],
    prev_com_world: float | None,
    phi: float,
    n_inputs: int,
    target_frac: float = 0.5,
    lookahead: float = 1.0,
) -> tuple[float, float | None]:
    """
    Velocity-extrapolation (smooth-pursuit) action signal — in WORLD coordinates.

    Key insight: retinal velocity = world velocity − eye velocity.  Tracking
    retinal velocity directly creates a positive-feedback loop (the eye chases
    its own motion).  Instead we convert to world coordinates first:

        com_world  = com_retinal + phi
        v_world    = com_world_t − com_world_{t-1}   # pure object velocity
        predicted  = com_world_t + lookahead · v_world

    Displacement to target (in retinal pixels):
        displacement = predicted − (phi + target_px)
                     = com_retinal + lookahead · v_world − target_px

    Returns (displacement, com_world_t).  displacement=0 when no object visible.
    """
    com_retinal = retinal_com(image)
    if com_retinal is None:
        return 0.0, None
    com_world = com_retinal + phi
    target_px = target_frac * n_inputs
    v_world = (com_world - prev_com_world) if prev_com_world is not None else 0.0
    displacement = com_retinal + lookahead * v_world - target_px
    return float(displacement), com_world


def compute_action_gradient(
    visual_sensors: list[SensorNode],
    image: list[float],
    anticipatory: bool = True,
) -> float:
    """
    Active-inference action signal:  ∂E/∂φ  for  E = ½ Σ (value error)².

    Must be called *after* phase_predict + phase_error but *before* relaxation.
    The sensor value-channel error  ε = μ − π  is the network's temporal
    prediction error: the carried-over hidden state predicts the new frame and
    the residual encodes the retinal slip.

    anticipatory=True  (default):
        Use the spatial gradient of the PREDICTION (s.pi[1]) rather than the
        raw image.  This closes the loop between the temporal hierarchy and the
        fovea: the recurrent/leaky hidden state predicts where the object will
        be, and we move toward that prediction.
            ∂E/∂φ = Σ_i ε_i · ∂π_i/∂φ

    anticipatory=False  (reactive, original behaviour):
        Use the spatial gradient of the current retinal image.
            ∂E/∂φ = Σ_i ε_i · ∂img_i/∂φ
    """
    e    = np.array([s.epsilon[1] for s in visual_sensors])  # value-channel error
    base = np.array([s.pi[1]      for s in visual_sensors]) if anticipatory \
           else np.array(image)
    grad = (np.roll(base, -1) - np.roll(base, 1)) * 0.5     # centred spatial gradient
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


def render_pointer_row(p: float, world_len: int, width: int = 2) -> list[float]:
    """
    Render the pointer-row world frame: a `width`-pixel flat blob centred at
    world position `p` (sub-pixel anti-aliased, like the object blobs).
    """
    frame = np.zeros(world_len)
    half = (width - 1) / 2.0
    lo, hi = p - half, p + half
    for i in range(world_len):
        if lo <= i <= hi:
            frame[i] = 1.0
        elif lo - 1 < i < lo:
            frame[i] = i - (lo - 1)
        elif hi < i < hi + 1:
            frame[i] = (hi + 1) - i
    return frame.tolist()


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
    world_frame: list[float],
    sensor_err: float,
    state_err: float,
    motor_err: float,
    phi: float,
    v: float,
    action_enabled: bool,
    oracle_enabled: bool,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
    n_inputs: int,
    ptr_world: list[float] | None = None,
    ptr_shifted: list[float] | None = None,
    p: float = 0.0,
    vp: float = 0.0,
    f_action: float = 0.0,
    f_spring: float = 0.0,
) -> int:
    if prev_lines > 0:
        _clear_lines(prev_lines)

    n = len(frame_values)
    world_len = len(world_frame)
    phase_str = ("Phase 2 [ACTIVE]" if action_enabled
                 else "Phase 1.5 [ORACLE]" if oracle_enabled
                 else "Phase 1 [passive]")

    # Display: show [N zeros][world N px][N zeros] = 3N px strip
    # The fovea window of N_inputs can slide across this entire strip.
    # phi=0 → window aligned with world center segment.
    # phi<0 → window sees zeros on left + left portion of world.
    # phi>0 → window sees right portion of world + zeros on right.
    pad = n_inputs
    padded = [0.0] * pad + list(world_frame) + [0.0] * pad  # length = 3*n_inputs
    win_start_disp = pad + round(phi)        # window start in padded coords
    win_end_disp   = win_start_disp + n_inputs - 1  # last visible pixel (inclusive)

    def _ch(val: float) -> str:
        return "█" if val >= 0.9 else ("▓" if val >= 0.6 else ("░" if val >= 0.2 else "·"))

    disp_chars = [_ch(v) for v in padded]
    # Insert bracket markers *around* the window (not overwriting content).
    # Build the string with brackets between pixels so all N pixels stay visible.
    out = []
    for i, ch in enumerate(disp_chars):
        if i == win_start_disp:
            out.append("[")
        out.append(ch)
        if i == win_end_disp:
            out.append("]")
    world_display = "".join(out)

    # Sensor window content (object row)
    dot_str = "".join(_ch(val) for val in frame_values)

    # Pointer row: same padded/windowed display as the object row.
    ptr_world_display = ptr_sensor_display = None
    if ptr_world is not None:
        ptr_padded = [0.0] * pad + list(ptr_world) + [0.0] * pad
        out_p = []
        for i, val in enumerate(ptr_padded):
            if i == win_start_disp:
                out_p.append("[")
            out_p.append(_ch(val))
            if i == win_end_disp:
                out_p.append("]")
        ptr_world_display = "".join(out_p)
    if ptr_shifted is not None:
        ptr_sensor_display = "".join(_ch(val) for val in ptr_shifted)

    lines = []
    lines.append(
        f"Step {step:5d}/{total_steps}  {phase_str}  "
        f"pattern: {pattern_name:<36s}  frame {frame_idx+1}"
    )
    lines.append(f"  Obj world:  {world_display}   (φ={phi:+.1f}  v={v:+.2f})")
    lines.append(f"  Obj sensor: {' ' * win_start_disp}[{dot_str}]")
    if ptr_world_display is not None:
        # Show which force dominates: action (network/drift) vs spring (to centre).
        arrow = "→net" if abs(f_action) > abs(f_spring) else "→spring"
        lines.append(f"  Ptr world:  {ptr_world_display}   (p={p:+.1f}  vp={vp:+.2f})")
        lines.append(f"  Ptr sensor: {' ' * win_start_disp}[{ptr_sensor_display}]")
        # Force readout on its own line with a fixed prefix, so the columns do
        # NOT slide with the fovea window — values stay readable frame to frame.
        lines.append(f"  Ptr force:  f_act={f_action:+.3f}  f_spr={f_spring:+.3f}  [{arrow}]")
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


def sample_bounce_patterns(
    n_inputs: int,
    seed: int,
    n_sequences: int,
) -> list[tuple[str, list[list[float]]]]:
    """
    Bounce-only pattern set: only bouncing-direction sequences, 1 or 2 objects,
    blob sizes 1–3 pixels, three speeds: normal (1.0), slow (0.5), very slow
    (0.25 px/frame).  Returns [(description, frames), ...].
    """
    gen = PatternGenerator(n_inputs=n_inputs, seed=seed)
    rng = np.random.default_rng(seed)
    patterns: list[tuple[str, list[list[float]]]] = []
    while len(patterns) < n_sequences:
        n_blobs = int(rng.integers(1, 3))      # 1 or 2
        blob_size = int(rng.integers(1, 4))    # 1, 2, or 3
        # 1 = normal (1.0), 2 = slow (0.5), 3 = very slow (0.25 px/frame)
        speed = int(rng.choice([1, 2, 3], p=[0.5, 0.3, 0.2]))
        blob_shape = "flat" if blob_size > 1 else "point"
        frames, spec = gen.build_sequence(
            n_blobs=n_blobs,
            blob_size=blob_size,
            blob_shape=blob_shape,
            direction="bounce",
            intensity_envelope="constant",
            speed=speed,
        )
        patterns.append((str(spec), frames))
    return patterns


def measure_per_pattern_errors(
    net: PCNetwork,
    object_sensors: list[SensorNode],
    pointer_sensors: list[SensorNode],
    motor_sensor: SensorNode,
    named_patterns: list[tuple[str, list[list[float]]]],
    n_inputs: int,
    n_passes: int = 3,
) -> list[tuple[str, dict[str, float]]]:
    """Run each named pattern n_passes times (no action, no learning).

    The pointer is parked at the world centre so the object-row errors stay
    comparable to the act2 baseline.
    """
    results = []
    centre = (n_inputs - 1) / 2.0
    ptr_win = apply_fovea_shift(render_pointer_row(centre, n_inputs), 0, n_inputs)
    for name, frames in named_patterns:
        s_errs, st_errs, m_errs = [], [], []
        for _ in range(n_passes):
            for frame in frames:
                # phi=0: sensor window aligned with world (full view, no offset)
                win = apply_fovea_shift(frame, 0, n_inputs)
                set_frame(object_sensors, win)
                set_frame(pointer_sensors, ptr_win)
                motor_sensor.set_input(np.array([0.0, 0.0]))
                info = net.step(learn=False)
                net.commit_step()
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
    object_sensors: list[SensorNode],
    pointer_sensors: list[SensorNode],
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

    for name, r in measure_per_pattern_errors(net, object_sensors, pointer_sensors,
                                               motor_sensor, train_patterns, n_inputs):
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}"
              f"  {r['motor_error']:8.4f}  [train]")

    print(f"\n  {'Pattern':<{col}s}  {'sensor':>8s}  {'state':>8s}  {'motor':>8s}  type")
    novel_results = measure_per_pattern_errors(net, object_sensors, pointer_sensors,
                                               motor_sensor, novel_patterns, n_inputs)
    for name, r in novel_results:
        print(f"  {name:<{col}s}  {r['sensor_error']:8.4f}  {r['state_error']:8.4f}"
              f"  {r['motor_error']:8.4f}  [novel]")

    tr_mean = float(np.mean([r["sensor_error"]
                             for _, r in measure_per_pattern_errors(
                                 net, object_sensors, pointer_sensors,
                                 motor_sensor, train_patterns, n_inputs)]))
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
    N_INPUTS          = 16   # visual sensor window width = world width (pixels)
    N_LAYERS          = 3    # hidden pyramid layers (depth)
    BASE_DIM          = 4    # state dim at layer 1
    DIM_GROWTH        = 2    # dim increment per layer
    LATERAL_STEPS     = 0    # lateral neighbours per side (sweep_act2: lat0 = +19% tracking)
    ACTION_MODE       = "gradient"   # "gradient"  — reactive ∂E/∂φ (uses the network)
                                     # "pred_com"  — steer toward COM of network π (uses the network)
                                     # "vel_com"   — smooth-pursuit: extrapolate COM velocity
                                     #               (kinematic centroid trick — bypasses the network)
    PRED_COM_TARGET   = 0.5          # desired retinal fraction (pred_com and vel_com)
    PRED_COM_GAIN     = 1.5          # v = PRED_COM_GAIN · displacement  (pred_com)
    VEL_COM_GAIN      = 1.2          # v = VEL_COM_GAIN · displacement   (vel_com)
    VEL_COM_LOOKAHEAD = 1.0          # frames to extrapolate ahead (1.0 = one step)
    N_TRAIN_PATTERNS  = 10   # how many different patterns to train on
    N_NOVEL_PATTERNS  = 10   # how many different patterns for evaluation only
    REPEATS_PER_SEQ   = 3    # repeats of each pattern per epoch
    N_EPOCHS_PASSIVE  = 8    # Phase 1: no action, learn to predict motion
                             #   (motor_error is trivially 0 here: v=0, nothing to predict)
    N_EPOCHS_ORACLE   = 8    # Phase 1.5: oracle pursuit — fovea perfectly tracks the
                             #   object's centre of mass so the V forward model learns
                             #   real object dynamics (and the motor learns the
                             #   efference-copy → retinal-shift mapping under motion)
    N_EPOCHS_ACTIVE   = 34   # Phase 2: action enabled (visual-error gradient)
    MAX_V             = 2.0  # max eye velocity in pixels/step
    ACTION_GAIN       = 1.5  # gradient → velocity gain (v = -gain · ∂E/∂φ);
                             #   higher = tighter tracking, less lag (risk: oscillation).
                             #   sweep_act2 focused (3 seeds): g1.5 eta.004 = best (0.287),
                             #   g1.2 close behind (0.266); no overshooting observed at 1.5
    ETA_LEARN         = 0.004 # hierarchical W learning rate; sweep_act2: 0.004 halves the
                             #   sensor error vs 0.002 with no tracking cost (clear win)
    ACTION_SMOOTH     = 0.2  # velocity momentum (0 = none, blends previous v)
    SPRING_K          = 0.05 # centering spring: pulls fovea toward φ=0 each step
                             #   (v_spring = -SPRING_K * phi, like eye muscle at rest)
    PASSIVE_DRIFT     = 0.3  # std of Gaussian velocity noise in Phase 1 (pixels/step)
                             #   gives the motor something to learn before Phase 2 starts
    PASSIVE_SPRING_K  = 0.30 # centering spring during Phase 1 — stronger than the
                             #   active spring because it must counteract the random
                             #   walk and keep the fovea inside the world region
    ORACLE_TARGET     = 0.35 # oracle pursuit keeps the object's centre of mass at this
                             #   fraction of the retina (0.5 = centred; <0.5 = left-biased,
                             #   matching where the active controller naturally settles)
    DELAY             = 0.0  # seconds between steps

    # ---- Pointer (Phase 1): a movable 2-px effector with physical mass ----
    POINTER_WIDTH       = 2      # pointer blob width in pixels
    POINTER_MASS        = 1.0    # inertia: a = F / mass
    POINTER_DAMPING     = 0.05   # velocity damping per step (low friction = more momentum)
    POINTER_ACTION_GAIN = 1.5    # gradient → force gain (F = -gain · ∂E/∂p)
    POINTER_SPRING_K    = 0.02   # weak spring pulling the pointer toward gaze centre
    POINTER_DRIFT       = 0.3    # std of force noise before the pointer action is on
    MAX_VP              = 2.0    # max pointer velocity in pixels/step
    # "self"   = pure active inference, pointer descends its own prediction error
    #            (network decides; object-following is emergent, not imposed).
    # "object" = taught: pointer reuses the object gradient (shares fovea's goal).
    POINTER_DRIVE       = "self"

    # Fovea range: the sensor window can slide from -N_INPUTS (fully left of world)
    # to +N_INPUTS (fully right of world).  phi=0 = world fully in view.
    PHI_MIN = float(-N_INPUTS)
    PHI_MAX = float(N_INPUTS)
    # The pointer lives in world coordinates and may roam the whole world.
    P_MIN = 0.0
    P_MAX = float(N_INPUTS - 1)
    # ---------------------------------------------------------------

    rng = np.random.default_rng(42)
    net, object_sensors, pointer_sensors, motor_sensor = build_network(
        rng,
        n_inputs=N_INPUTS,
        n_layers=N_LAYERS,
        base_dim=BASE_DIM,
        dim_growth=DIM_GROWTH,
        lateral_steps=LATERAL_STEPS,
        eta_learn=ETA_LEARN,
    )

    # Sample fixed pattern sets once — patterns are N_INPUTS wide (world size)
    # Bouncing-only: 1–2 objects, blob sizes 1–3 pixels.
    train_patterns = sample_bounce_patterns(
        n_inputs=N_INPUTS, seed=0, n_sequences=N_TRAIN_PATTERNS,
    )
    novel_patterns = sample_bounce_patterns(
        n_inputs=N_INPUTS, seed=9999, n_sequences=N_NOVEL_PATTERNS,
    )

    total_steps = (
        sum(len(frames) for _, frames in train_patterns)
        * REPEATS_PER_SEQ
        * (N_EPOCHS_PASSIVE + N_EPOCHS_ORACLE + N_EPOCHS_ACTIVE)
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
    print(f"\nWorld:   {N_INPUTS}px  |  Sensor window: {N_INPUTS}px  |  φ ∈ [{PHI_MIN:.0f}, {PHI_MAX:.0f}]")
    print(f"Phase 1: {N_EPOCHS_PASSIVE} epochs (passive, φ=0, learn to predict)")
    print(f"Phase 1.5: {N_EPOCHS_ORACLE} epochs (oracle pursuit, φ tracks object COM "
          f"@ {ORACLE_TARGET:.0%} retina)")
    act_mode_str = {
        "gradient": "reactive gradient ∂E/∂φ",
        "pred_com": f"pred-COM (gain={PRED_COM_GAIN}, target={PRED_COM_TARGET:.0%})",
        "vel_com":  f"vel-COM smooth-pursuit (gain={VEL_COM_GAIN}, lookahead={VEL_COM_LOOKAHEAD})",
    }.get(ACTION_MODE, ACTION_MODE)
    print(f"Phase 2: {N_EPOCHS_ACTIVE} epochs  (active, [{act_mode_str}])")
    print(f"Total  : ≈{total_steps} steps\n")
    print("Press Ctrl+C to stop early.\n")

    oracle_start_epoch = N_EPOCHS_PASSIVE
    active_start_epoch = N_EPOCHS_PASSIVE + N_EPOCHS_ORACLE

    prev_lines = 0
    step = 0
    passive_steps = 0
    phi = 0.0
    v   = 0.0
    p   = (N_INPUTS - 1) / 2.0   # pointer world position (starts at centre)
    vp  = 0.0                    # pointer velocity
    prev_retinal_com: float | None = None   # for vel_com smooth pursuit
    pointer_history: list[float] = []        # retinal pointer position over time
    ptr_f_action = 0.0   # last pointer steering force (network/drift)
    ptr_f_spring = 0.0   # last pointer spring force (toward gaze centre)
    ptr_net_steps   = 0  # steps where |f_act| > |f_spr| (active phase)
    ptr_total_steps = 0  # total active steps with pointer
    ptr_toward_obj  = 0  # steps where f_act points toward the object COM
    ptr_abs_vp_sum  = 0.0  # accumulated |vp| during active phase
    ptr_descent_ok  = 0  # (a)-test: steps where the action reduces pointer-row error

    try:
        for epoch in range(N_EPOCHS_PASSIVE + N_EPOCHS_ORACLE + N_EPOCHS_ACTIVE):
            oracle_enabled = (oracle_start_epoch <= epoch < active_start_epoch)
            action_enabled = (epoch >= active_start_epoch)
            phi = 0.0
            v   = 0.0
            p   = (N_INPUTS - 1) / 2.0   # reset pointer to centre each epoch
            vp  = 0.0
            prev_retinal_com = None   # reset at epoch boundary

            if epoch == active_start_epoch:
                passive_steps = step

            for name, world_frames in train_patterns:
                for _ in range(REPEATS_PER_SEQ):
                    for frame_idx, world_frame in enumerate(world_frames):
                        # Extract sensor windows from the wider world (zero-padded at edges)
                        shifted     = apply_fovea_shift(world_frame, phi, N_INPUTS)
                        ptr_world   = render_pointer_row(p, N_INPUTS, POINTER_WIDTH)
                        ptr_shifted = apply_fovea_shift(ptr_world, phi, N_INPUTS)
                        set_frame(object_sensors, shifted)
                        set_frame(pointer_sensors, ptr_shifted)
                        # efference copy of both effectors, each in [-1, 1]
                        motor_sensor.set_input(np.array([v / MAX_V, vp / MAX_VP]))

                        # Pre-relaxation action signals (need phase_predict+error first).
                        # vel_com only needs the current image — no phase call needed.
                        _disp  = 0.0   # fovea displacement signal
                        _pdisp = 0.0   # pointer displacement signal
                        if action_enabled:
                            if ACTION_MODE == "vel_com":
                                _disp, prev_retinal_com = compute_action_velocity_com(
                                    shifted, prev_retinal_com, phi, N_INPUTS,
                                    PRED_COM_TARGET, VEL_COM_LOOKAHEAD,
                                )
                            else:
                                net.phase_predict()
                                net.phase_error()
                                if ACTION_MODE == "pred_com":
                                    _disp = compute_action_pred_com(
                                        object_sensors, N_INPUTS, PRED_COM_TARGET
                                    )
                                else:
                                    _disp = -compute_action_gradient(object_sensors, shifted)
                                # Pointer active inference.  Two modes:
                                #   "self"   — architecturally pure: descend the pointer
                                #              row's OWN prediction error.  The network
                                #              alone decides where the pointer goes; any
                                #              object-following (or fleeing) is emergent.
                                #   "object" — taught/biased: reuse the object gradient so
                                #              the pointer shares the fovea's goal.
                                if POINTER_DRIVE == "object":
                                    _pdisp = -compute_action_gradient(
                                        object_sensors, shifted, anticipatory=True
                                    )
                                else:
                                    _pdisp = -compute_action_gradient(
                                        pointer_sensors, ptr_shifted, anticipatory=False
                                    )

                                # (a) architectural correctness: does moving the pointer
                                # in the action direction actually REDUCE the pointer-row
                                # value-channel prediction error?  Finite difference against
                                # the predictions pi just computed — object-independent.
                                pi_val = np.array([s.pi[1] for s in pointer_sensors])
                                e_cur = float(np.sum(
                                    (np.array(ptr_shifted) - pi_val) ** 2))
                                p_pert = float(np.clip(
                                    p + 0.5 * np.sign(_pdisp), P_MIN, P_MAX))
                                pert_world = render_pointer_row(
                                    p_pert, N_INPUTS, POINTER_WIDTH)
                                pert_shifted = apply_fovea_shift(
                                    pert_world, phi, N_INPUTS)
                                e_new = float(np.sum(
                                    (np.array(pert_shifted) - pi_val) ** 2))
                                if e_new < e_cur:
                                    ptr_descent_ok += 1

                        # Full PC step (predict/error/relax/learn) — clean diagnostics
                        info = net.step(learn=True)
                        net.commit_step()   # advance temporal memory by one frame

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
                            world_frame, s_err, st_err, m_err, phi, v, action_enabled,
                            oracle_enabled,
                            sensor_history, state_history, max_err, prev_lines, N_INPUTS,
                            ptr_world=ptr_world, ptr_shifted=ptr_shifted, p=p, vp=vp,
                            f_action=ptr_f_action, f_spring=ptr_f_spring,
                        )
                        step += 1

                        # Phase 1:   gentle random drift (motor learns efference copy).
                        # Phase 1.5: oracle pursuit (fovea tracks object COM exactly).
                        # Phase 2:   network-driven steering.
                        if action_enabled:
                            if ACTION_MODE == "vel_com":
                                v_target = VEL_COM_GAIN * _disp - SPRING_K * phi
                            elif ACTION_MODE == "pred_com":
                                v_target = PRED_COM_GAIN * _disp - SPRING_K * phi
                            else:
                                v_target = _disp * ACTION_GAIN - SPRING_K * phi
                            v = float(np.clip(
                                (1.0 - ACTION_SMOOTH) * v_target + ACTION_SMOOTH * v,
                                -MAX_V, MAX_V,
                            ))
                        elif oracle_enabled:
                            com = world_com(world_frame)
                            if com is not None:
                                target_phi = com - ORACLE_TARGET * N_INPUTS
                                v = float(np.clip(target_phi - phi, -MAX_V, MAX_V))
                                # warm vel_com buffer: store world COM
                                rc = retinal_com(shifted)
                                prev_retinal_com = (rc + phi) if rc is not None else None
                            else:
                                v = 0.0
                                prev_retinal_com = None
                        else:
                            # Passive drift + centering spring so the random walk
                            # stays bounded around φ=0 instead of wandering out of
                            # the world region.
                            v = float(np.clip(
                                rng.normal(0.0, PASSIVE_DRIFT) - PASSIVE_SPRING_K * phi,
                                -MAX_V, MAX_V,
                            ))
                            rc = retinal_com(shifted)
                            prev_retinal_com = (rc + phi) if rc is not None else None
                        phi = float(np.clip(phi + v, PHI_MIN, PHI_MAX))

                        # ---- Pointer physics (mass + acceleration) ----
                        # Weak spring pulls the pointer toward the gaze centre
                        # (world coord of the fovea-window centre).  In Phase 2 the
                        # network's pointer-row gradient adds a steering force; before
                        # that the pointer only drifts so its motor channel is learnt.
                        gaze_centre = phi + N_INPUTS / 2.0
                        f_spring = -POINTER_SPRING_K * (p - gaze_centre)
                        if action_enabled and ACTION_MODE != "vel_com":
                            f_action = POINTER_ACTION_GAIN * _pdisp
                        else:
                            f_action = rng.normal(0.0, POINTER_DRIFT)
                        accel = (f_action + f_spring) / POINTER_MASS
                        ptr_f_action, ptr_f_spring = f_action, f_spring   # for next render
                        if action_enabled:
                            ptr_total_steps += 1
                            if abs(f_action) > abs(f_spring):
                                ptr_net_steps += 1
                            # Does f_act push toward the object? (world coords)
                            com = world_com(world_frame)
                            if com is not None and abs(com - p) > 0.3:
                                if np.sign(f_action) == np.sign(com - p):
                                    ptr_toward_obj += 1
                        vp = float(np.clip((vp + accel) * (1.0 - POINTER_DAMPING),
                                           -MAX_VP, MAX_VP))
                        p = float(np.clip(p + vp, P_MIN, P_MAX))
                        if action_enabled:
                            ptr_abs_vp_sum += abs(vp)
                        pointer_history.append(p - phi)   # retinal pointer position

                        if DELAY > 0:
                            time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    if ptr_total_steps > 0:
        net_pct = 100.0 * ptr_net_steps / ptr_total_steps
        toward_pct = 100.0 * ptr_toward_obj / ptr_total_steps
        mean_vp = ptr_abs_vp_sum / ptr_total_steps
        print(
            f"\n  Pointer force dominance (active phase): "
            f"→net {ptr_net_steps}/{ptr_total_steps} steps  ({net_pct:.1f}%)"
            f"   →spring {ptr_total_steps - ptr_net_steps}/{ptr_total_steps} steps"
            f"  ({100 - net_pct:.1f}%)"
        )
        print(
            f"  f_act points TOWARD object : {ptr_toward_obj}/{ptr_total_steps} steps"
            f"  ({toward_pct:.1f}%)   "
            f"[>50% = correct sign, ~50% = random, <50% = WRONG sign]"
        )
        print(f"  mean |vp| (active)         : {mean_vp:.3f} px/step"
              f"   [near 0 = pointer barely moves]")
        descent_pct = 100.0 * ptr_descent_ok / ptr_total_steps
        print(
            f"  (a) action REDUCES ptr-error: {ptr_descent_ok}/{ptr_total_steps} steps"
            f"  ({descent_pct:.1f}%)"
            f"   [>50% = active inference works as designed]"
        )

    print_summary(
        step, sensor_history, state_history, motor_history,
        net, object_sensors, pointer_sensors, motor_sensor,
        train_patterns, novel_patterns,
        N_INPUTS, passive_steps,
    )


if __name__ == "__main__":
    main()
