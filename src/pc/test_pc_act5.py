r"""
test_pc_act5.py — Phase 2 active inference: push object to target.

Upgrades from test_pc_act4:
  physics      : 1-D physics world with mass, friction, wall bounce
  tap action   : PremotorModule issues tap commands driven by HiddenHierarchy
  task         : push the single object to a fixed target; hold it there
  RGB sensors  : object row carries 3 channels [pos, object_val, target_val]
  flash sensor : 1 dedicated sensor node (1.0 = success, else 0.0)
  motor dim=3  : [v_fovea/MAX_V, v_ptr/MAX_VP, tap_gate]
  reward       : RPE = normalised proximity to target − EMA baseline

Architecture additions over act4:
  PremotorModule — one PCNode "pm_0" connected from HiddenHierarchy abstract
                   output via UP connections.  After phase_predict, pm_0.pi[0]
                   encodes the hierarchy's intended tap command; the tap gate is
                   derived from it.  PremotorModule sits between the abstract
                   hierarchy and the motor sensor — it never connects directly to
                   the raw visual sensors.

  Flash sensor   — connected from the top hidden layer (hierarchy predicts success).

World schematic
---------------
  Object row  [pos, obj, tgt]  ← 3-channel, dim=3 each pixel
  Pointer row [pos, ptr]       ← 2-channel, dim=2 each pixel
  Flash sensor[flash]          ← 1-channel, 1.0 when success

  Target is fixed at 3/4 of the world (world pixel 12 for N_INPUTS=16).
  Object starts near left edge, bounces with light friction.
  Pointer (force-controlled) can TAP the object: if tap_gate > TAP_THRESHOLD
  and the pointer is within TAP_RANGE of the object, the object receives an
  impulse that pushes it away from the pointer (billiard-ball model).
  Success = object at rest within 1.5 px of target → flash + reward bonus.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule


# ---------------------------------------------------------------------------
# 1-D Physics World
# ---------------------------------------------------------------------------

TAP_THRESHOLD = 0.4   # minimum tap_gate to apply impulse


class PhysicsWorld1D:
    """
    1-D physics world: one moving object, one fixed target, tap interaction.

    Object dynamics: velocity integration with friction; elastic wall bounce
    (with a little energy loss so the object eventually settles).

    Tap: if tap_gate > TAP_THRESHOLD and pointer within TAP_RANGE of object,
    the object receives an impulse that pushes it away from the pointer.
    """

    def __init__(
        self,
        n: int,
        obj_friction:    float = 0.025,
        tap_impulse:     float = 2.5,
        tap_range:       float = 2.5,
        flash_duration:  int   = 8,
        target_frac:     float = 0.75,
        kick_after:      int   = 150,   # steps of near-idleness before auto-kick
        kick_idle_thr:   float = 1.5,   # total displacement below this = idle
        kick_vel:        float = 4.0,   # strong push toward opposite side of world
        seed:            int   = 0,
    ) -> None:
        self.n             = n
        self.obj_friction  = obj_friction
        self.tap_impulse   = tap_impulse
        self.tap_range     = tap_range
        self.kick_after    = kick_after
        self.kick_idle_thr = kick_idle_thr
        self.kick_vel      = kick_vel
        self.flash_duration = flash_duration
        self.target_pos    = float(round(target_frac * (n - 1)))
        self._rng          = np.random.default_rng(seed)

        self.obj_pos:    float = 0.0
        self.obj_vel:    float = 0.0
        self.flash_timer: int  = 0
        self._ep_step:   int   = 0     # steps since last reset
        self._start_pos: float = 0.0   # object position at episode start
        self._kicked:    bool  = False  # only kick once per episode
        self.reset()

    def reset(self, fixed: bool = False, static: bool = False) -> None:
        """Reset object position.

        fixed  — deterministic start (left quarter, vel=0.8) for diagnostics.
        static — random position but zero initial velocity; the object only
                 moves when the pointer taps it.  Used in the active phase to
                 isolate intentional pushing from spontaneous bouncing.
        """
        if fixed:
            self.obj_pos = float(self.n // 4)
            self.obj_vel = 0.8
        elif static:
            self.obj_pos = float(self._rng.integers(1, max(2, self.n // 3)))
            self.obj_vel = 0.0
        else:
            self.obj_pos = float(self._rng.integers(1, max(2, self.n // 3)))
            self.obj_vel = float(
                self._rng.uniform(0.4, 1.2) * self._rng.choice([-1.0, 1.0])
            )
        self.flash_timer = 0
        self._ep_step    = 0
        self._start_pos  = self.obj_pos
        self._kicked     = False

    def step(self, tap_gate: float, pointer_pos: float) -> dict:
        """Advance physics one frame.  Returns {tapped, success, flash}."""
        tapped = False
        if tap_gate > TAP_THRESHOLD:
            dist = abs(pointer_pos - self.obj_pos)
            if 0.1 < dist < self.tap_range:
                impulse_dir = np.sign(self.obj_pos - pointer_pos)
                self.obj_vel += self.tap_impulse * tap_gate * float(impulse_dir)
                tapped = True

        self.obj_vel *= (1.0 - self.obj_friction)
        self.obj_pos += self.obj_vel

        # Elastic wall bounce with slight energy loss
        if self.obj_pos <= 0.0:
            self.obj_pos = 0.0
            self.obj_vel = abs(self.obj_vel) * 0.85
        elif self.obj_pos >= self.n - 1:
            self.obj_pos = float(self.n - 1)
            self.obj_vel = -abs(self.obj_vel) * 0.85

        at_target = abs(self.obj_pos - self.target_pos) < 1.5
        at_rest   = abs(self.obj_vel) < 0.3
        success   = at_target and at_rest
        if success and self.flash_timer == 0:
            self.flash_timer = self.flash_duration
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Auto-kick: if the object has barely moved after kick_after steps,
        # give it a strong push toward the opposite side of the world.
        # Fires at most once per episode so the network always gets a chance
        # to see a moving object and learns what a pushed object looks like.
        kicked = False
        self._ep_step += 1
        if (not self._kicked
                and self._ep_step >= self.kick_after
                and abs(self.obj_pos - self._start_pos) < self.kick_idle_thr):
            # Push toward the far side: if left half → kick right, else ← left
            kick_dir = 1.0 if self.obj_pos < self.n / 2.0 else -1.0
            self.obj_vel += self.kick_vel * kick_dir
            self._kicked = True
            kicked = True

        return {"tapped": tapped, "success": success,
                "flash": self.flash_timer > 0, "kicked": kicked}

    # ------------------------------------------------------------------

    def render_obj_channel(self) -> list[float]:
        """2-pixel blob at object position (best-behaving width in act4)."""
        return _flat_blob(self.obj_pos, self.n, width=2)

    def render_target_channel(self) -> list[float]:
        """2-pixel marker at target position (always visible)."""
        return _flat_blob(self.target_pos, self.n, width=2)

    def world_com(self) -> float:
        """Centre-of-mass of the object in world coords."""
        return self.obj_pos


def _flat_blob(center: float, n: int, width: int = 1) -> list[float]:
    """Anti-aliased flat blob of given width in a world of n pixels."""
    frame = np.zeros(n)
    half = (width - 1) / 2.0
    lo, hi = center - half, center + half
    for i in range(n):
        if lo <= i <= hi:
            frame[i] = 1.0
        elif lo - 1 < i < lo:
            frame[i] = i - (lo - 1)
        elif hi < i < hi + 1:
            frame[i] = (hi + 1) - i
    return frame.tolist()


# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(
    rng: np.random.Generator,
    n_inputs:      int   = 16,
    n_layers:      int   = 3,
    base_dim:      int   = 4,
    dim_growth:    int   = 2,
    lateral_steps: int   = 0,
    eta_inf:       float = 0.05,
    n_relax:       int   = 40,
    eta_learn:     float = 0.002,
    gamma:         float = 0.3,
) -> tuple[PCNetwork, list[SensorNode], list[SensorNode],
           SensorNode, SensorNode]:
    """
    Build the act5 network with four PCModules:

      VisualCortex    — 3-channel obj sensors + 2-channel ptr sensors, hexagonally
                        coupled; plus flash (dim=1) and motor (dim=3) sensors.
                        in-ports : obj_input [dim=3], ptr_input [dim=2], flash_in, motor_in
                        out-ports: obj_row, ptr_row

      HiddenHierarchy — pyramidal hidden layers receiving from VisualCortex.
                        in-ports : visual_in (layer-1 nodes)
                        out-ports: abstract_out (top layer)

      PremotorModule  — one PCNode "pm_0" (dim=2, tanh) receiving from the top
                        of HiddenHierarchy.  pm_0.pi[0] drives the tap gate.
                        in-ports : abstract_in (top hidden IDs)
                        out-ports: tap_out (["pm_0"])

      MotorModule     — 1 SensorNode, dim=3: [v_fovea, v_ptr, tap_gate].
                        in-ports : efference_in

    Returns (net, object_sensors, pointer_sensors, flash_sensor, motor_sensor).
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

    # ------------------------------------------------------------------
    # VisualCortex
    # ------------------------------------------------------------------
    visual_cortex = PCModule("VisualCortex")

    # Object sensors: dim=3 = [retinal_pos, object_val, target_val]
    object_sensors: list[SensorNode] = [
        net.add(SensorNode(f"so{i}", dim=3)) for i in range(n_inputs)
    ]
    # Pointer sensors: dim=2 = [retinal_pos, pointer_val]
    pointer_sensors: list[SensorNode] = [
        net.add(SensorNode(f"sp{i}", dim=2)) for i in range(n_inputs)
    ]
    obj_ids = [f"so{i}" for i in range(n_inputs)]
    ptr_ids = [f"sp{i}" for i in range(n_inputs)]

    # Hexagonal coupling inside VisualCortex
    HEX_PS = 0.1
    for j in range(n_inputs):
        for jp in (j, j + 1):
            if 0 <= jp < n_inputs:
                net.connect(f"so{j}", f"sp{jp}", ConnType.LATERAL, pressure_scale=HEX_PS)
                net.connect(f"sp{jp}", f"so{j}", ConnType.LATERAL, pressure_scale=HEX_PS)

    # Flash sensor (dim=1) and motor sensor (dim=3)
    flash_sensor = net.add(SensorNode("flash", dim=1))
    motor_sensor = net.add(SensorNode("motor", dim=3))

    (visual_cortex
        .add_in_port("obj_input",  obj_ids)
        .add_out_port("obj_row",   obj_ids)
        .add_in_port("ptr_input",  ptr_ids)
        .add_out_port("ptr_row",   ptr_ids)
        .add_in_port("flash_in",   ["flash"])
        .add_in_port("motor_in",   ["motor"])
    )
    net.add_module(visual_cortex)

    # ------------------------------------------------------------------
    # HiddenHierarchy
    # ------------------------------------------------------------------
    hidden = PCModule("HiddenHierarchy")

    layer_widths = [max(1, n_inputs // (2 ** k)) for k in range(1, n_layers + 1)]
    layer_dims   = [base_dim + (k - 1) * dim_growth for k in range(1, n_layers + 1)]

    for k, (width, dim) in enumerate(zip(layer_widths, layer_dims), start=1):
        for j in range(width):
            net.add(PCNode(f"h{k}_{j}", dim=dim, activation="tanh", rng=rng))

    h1_ids  = [f"h1_{j}"          for j in range(layer_widths[0])]
    top_ids = [f"h{n_layers}_{j}" for j in range(layer_widths[-1])]

    hidden.add_in_port("visual_in",     h1_ids)
    hidden.add_out_port("abstract_out", top_ids)

    # VisualCortex → HiddenHierarchy: joint receptive field (obj + ptr)
    for j in range(layer_widths[0]):
        ps = 1.0
        net.connect(f"h1_{j}", f"so{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"so{2*j+1}", ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j+1}", ConnType.UP, pressure_scale=ps)

    # Layer k+1 ← layer k (within HiddenHierarchy)
    for k in range(1, n_layers):
        width_above = layer_widths[k]
        ps = 0.1 if k == n_layers - 1 else 1.0
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

    # Flash visible to top of hierarchy (hierarchy learns to predict success)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "flash", ConnType.UP, pressure_scale=0.3)

    net.add_module(hidden)

    # ------------------------------------------------------------------
    # PremotorModule
    # ------------------------------------------------------------------
    premotor_mod = PCModule("PremotorModule")
    net.add(PCNode("pm_0", dim=2, activation="tanh", rng=rng))

    premotor_mod.add_in_port("abstract_in", top_ids)
    premotor_mod.add_out_port("tap_out",    ["pm_0"])
    net.add_module(premotor_mod)

    # HiddenHierarchy → PremotorModule (top-down: hierarchy predicts premotor state)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "pm_0", ConnType.UP, pressure_scale=0.1)

    # PremotorModule → MotorModule (efference copy of tap command)
    net.connect("pm_0", "motor", ConnType.UP, pressure_scale=0.05)

    # ------------------------------------------------------------------
    # MotorModule
    # ------------------------------------------------------------------
    motor_mod = PCModule("MotorModule")
    motor_mod.add_in_port("efference_in", ["motor"])
    net.add_module(motor_mod)

    # HiddenHierarchy → MotorModule (efference copy of fovea/pointer commands)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "motor", ConnType.UP, pressure_scale=0.05)

    return net, object_sensors, pointer_sensors, flash_sensor, motor_sensor


# ---------------------------------------------------------------------------
# Fovea helpers  (unchanged from act4)
# ---------------------------------------------------------------------------

def apply_fovea_shift(world_frame: list[float], phi: float, n_inputs: int) -> list[float]:
    """Extract n_inputs-wide window from world_frame at offset round(phi)."""
    offset = round(phi)
    world_len = len(world_frame)
    result = []
    for i in range(n_inputs):
        wi = offset + i
        result.append(float(world_frame[wi]) if 0 <= wi < world_len else 0.0)
    return result


def retinal_com(values: list[float] | np.ndarray) -> float | None:
    """Intensity-weighted centre of mass of a retinal image."""
    arr = np.asarray(values, dtype=float)
    arr = np.clip(arr, 0.0, None)
    total = arr.sum()
    if total < 1e-4:
        return None
    return float((np.arange(arr.size) * arr).sum() / total)


def compute_action_gradient(
    visual_sensors: list[SensorNode],
    image: list[float],
    anticipatory: bool = True,
    channel: int = 1,
) -> float:
    """
    Active-inference action signal: ∂E/∂φ.

    `channel` selects which sensor dimension to use for the gradient
    (default 1 = the object/value channel, valid for both dim=2 and dim=3 sensors).
    """
    e    = np.array([s.epsilon[channel] for s in visual_sensors])
    base = (np.array([s.pi[channel] for s in visual_sensors]) if anticipatory
            else np.array(image))
    grad = (np.roll(base, -1) - np.roll(base, 1)) * 0.5
    return float(np.sum(e * grad))


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _positions(n: int) -> list[float]:
    """Evenly-spaced retinal positions in (0, 1], length n."""
    step = 1.0 / n
    return [round(step * (i + 1), 4) for i in range(n)]


def set_frame_obj(
    object_sensors: list[SensorNode],
    obj_vals:    list[float],
    target_vals: list[float],
) -> None:
    """Push [retinal_pos, object_value, target_value] into dim=3 object sensor nodes."""
    pos = _positions(len(object_sensors))
    for i, s in enumerate(object_sensors):
        s.set_input(np.array([pos[i], float(obj_vals[i]), float(target_vals[i])]))


def set_frame_ptr(
    pointer_sensors: list[SensorNode],
    values: list[float],
) -> None:
    """Push [retinal_pos, pointer_value] into dim=2 pointer sensor nodes."""
    pos = _positions(len(pointer_sensors))
    for i, (s, v) in enumerate(zip(pointer_sensors, values)):
        s.set_input(np.array([pos[i], float(v)]))


def render_pointer_row(p: float, world_len: int, width: int = 2) -> list[float]:
    """Anti-aliased pointer blob (world frame)."""
    return _flat_blob(p, world_len, width=width)


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

BAR_WIDTH      = 28
HISTORY_LEN    = 60
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


def _ch(val: float) -> str:
    return "█" if val >= 0.9 else ("▓" if val >= 0.6 else ("░" if val >= 0.2 else "·"))


def render(
    step: int,
    total_steps: int,
    episode: int,
    world: PhysicsWorld1D,
    phi: float,
    v: float,
    p: float,
    vp: float,
    tap_gate: float,
    tapped: bool,
    kicked: bool,
    n_inputs: int,
    action_enabled: bool,
    oracle_enabled: bool,
    pursuit_enabled: bool,
    sensor_err: float,
    state_err: float,
    motor_err: float,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
    f_action: float = 0.0,
    f_spring: float = 0.0,
) -> int:
    if prev_lines > 0:
        _clear_lines(prev_lines)

    phase_str = ("Phase 2 [ACTIVE]" if action_enabled
                 else "Phase 1.75 [PURSUIT]" if pursuit_enabled
                 else "Phase 1.5 [ORACLE]" if oracle_enabled
                 else "Phase 1 [passive]")
    flash_str = " [FLASH!]" if world.flash_timer > 0 else ""
    kick_str  = " [KICK]"  if kicked else ""

    pad = n_inputs
    obj_world    = world.render_obj_channel()
    target_world = world.render_target_channel()
    ptr_world    = render_pointer_row(p, n_inputs)

    # Padded display [pad zeros][world][pad zeros]
    def _pad_display(frame: list[float], bracket_at: int) -> str:
        padded = [0.0] * pad + list(frame) + [0.0] * pad
        win_s  = pad + bracket_at
        win_e  = win_s + n_inputs - 1
        out = []
        for i, val in enumerate(padded):
            if i == win_s:
                out.append("[")
            out.append(_ch(val))
            if i == win_e:
                out.append("]")
        return "".join(out)

    phi_r = round(phi)

    # Object world: object as block chars, with the fixed target overlaid as a
    # caret "‸" wherever there is no object pixel.  When the pointer TAPS, its
    # contact pixel is flashed into this row as "✸" so the interaction is visible.
    tap_world = render_pointer_row(p, n_inputs) if tapped else [0.0] * n_inputs

    def _pad_obj_display(obj_f: list[float], tgt_f: list[float],
                         tap_f: list[float], bracket_at: int) -> str:
        obj_p = [0.0] * pad + list(obj_f) + [0.0] * pad
        tgt_p = [0.0] * pad + list(tgt_f) + [0.0] * pad
        tap_p = [0.0] * pad + list(tap_f) + [0.0] * pad
        win_s = pad + bracket_at
        win_e = win_s + n_inputs - 1
        out = []
        for i, ov in enumerate(obj_p):
            if i == win_s:
                out.append("[")
            ch = _ch(ov)
            if tap_p[i] >= 0.5:
                ch = "✸"            # pointer tap contact flash (overlays everything)
            elif ch == "·" and tgt_p[i] >= 0.5:
                ch = "‸"            # target marker shows through empty pixels
            out.append(ch)
            if i == win_e:
                out.append("]")
        return "".join(out)

    obj_disp = _pad_obj_display(obj_world, target_world, tap_world, phi_r)
    ptr_disp = _pad_display(ptr_world, phi_r)

    # Sensor window string (object channel + target overlaid as "‸")
    def _obj_sensor_str() -> str:
        obj_sh = apply_fovea_shift(obj_world,    phi, n_inputs)
        tgt_sh = apply_fovea_shift(target_world, phi, n_inputs)
        chars = []
        for ov, tv in zip(obj_sh, tgt_sh):
            ch = _ch(ov)
            if ch == "·" and tv >= 0.5:
                ch = "‸"
            chars.append(ch)
        return "".join(chars)

    win_start_disp = pad + phi_r
    arrow = "→net" if abs(f_action) > abs(f_spring) else "→spring"
    tap_str = f"  TAP!" if tapped else ""

    lines = []
    lines.append(
        f"Step {step:5d}/{total_steps}  {phase_str}  "
        f"ep={episode}  obj={world.obj_pos:+.1f}  vel={world.obj_vel:+.2f}"
        f"  tgt={world.target_pos:.0f}{flash_str}{kick_str}"
    )
    lines.append(f"  Obj world:  {obj_disp}   (φ={phi:+.1f}  v={v:+.2f})  ‸=target")
    lines.append(f"  Obj sensor: {' ' * win_start_disp}[{_obj_sensor_str()}]")
    lines.append(f"  Ptr world:  {ptr_disp}   (p={p:+.1f}  vp={vp:+.2f})")
    lines.append(
        f"  Ptr force:  f_act={f_action:+.3f}  f_spr={f_spring:+.3f}  [{arrow}]"
        f"  tap={tap_gate:.2f}{tap_str}"
    )
    lines.append("")
    lines.append(f"  sensor_error  {_bar(sensor_err, max_err)}  {sensor_err:7.4f}")
    lines.append(f"  state_error   {_bar(state_err,  max_err)}  {state_err:7.4f}")
    lines.append(f"  motor_error   {_bar(motor_err,  max_err)}  {motor_err:7.4f}")
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
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    step: int,
    sensor_history: list[float],
    state_history: list[float],
    motor_history: list[float],
    passive_steps: int,
    success_count: int,
    total_active_steps: int,
    tap_count: int,
    reward_sum: float,
    reward_steps: int,
    reward_pos: int,
    reward_neg: int,
    ptr_toward_obj: int,
    ptr_total_steps: int,
    ptr_descent_ok: int,
    pursuit_toward_obj: int = 0,
    pursuit_total_steps: int = 0,
    push_side_ok: int = 0,
    push_side_total: int = 0,
    tap_toward_target: int = 0,
    tap_total: int = 0,
) -> None:
    n = len(sensor_history)
    q = max(1, n // 10)
    first_s,  last_s  = sensor_history[:q], sensor_history[-q:]
    first_st, last_st = state_history[:q],  state_history[-q:]
    first_m,  last_m  = motor_history[:q],  motor_history[-q:]

    print(f"\n{'='*64}")
    print(f"  Training summary — act5 (push-to-target)")
    print(f"{'='*64}")
    print(f"  Steps completed    : {step}  (active started at step {passive_steps})")
    print(f"  {'':20s}  {'start':>8s}  {'end':>8s}  {'Δ':>8s}")
    for label, first, last in [
        ("sensor_error", first_s, last_s),
        ("state_error",  first_st, last_st),
        ("motor_error",  first_m,  last_m),
    ]:
        if first and last:
            print(f"  {label:20s}  {np.mean(first):8.4f}  {np.mean(last):8.4f}"
                  f"  {np.mean(first)-np.mean(last):+8.4f}")

    if pursuit_total_steps > 0:
        pursuit_pct = 100.0 * pursuit_toward_obj / pursuit_total_steps
        print(f"\n{'='*64}")
        print(f"  Pursuit-phase (object-following) statistics")
        print(f"{'='*64}")
        print(
            f"  ptr-action→object  : {pursuit_toward_obj}/{pursuit_total_steps}"
            f"  ({pursuit_pct:.1f}%)"
            f"   [>50% = following re-learned]"
        )

    if total_active_steps > 0:
        print(f"\n{'='*64}")
        print(f"  Active-phase statistics")
        print(f"{'='*64}")
        print(f"  Task successes     : {success_count}"
              f"   ({100.0 * success_count / max(1, total_active_steps):.2f}% of active steps in flash)")
        tap_pct = 100.0 * tap_count / total_active_steps
        print(f"  Tap events         : {tap_count}/{total_active_steps}"
              f"  ({tap_pct:.1f}% of steps)   [>0 = premotor fires]")

    if ptr_total_steps > 0:
        toward_pct  = 100.0 * ptr_toward_obj / ptr_total_steps
        descent_pct = 100.0 * ptr_descent_ok / ptr_total_steps
        print(
            f"  f_act→object       : {ptr_toward_obj}/{ptr_total_steps}"
            f"  ({toward_pct:.1f}%)"
            f"   [>50% = object-following]"
        )
        print(
            f"  (a) ptr-error ↓    : {ptr_descent_ok}/{ptr_total_steps}"
            f"  ({descent_pct:.1f}%)"
            f"   [>50% = active inference OK]"
        )

    if push_side_total > 0:
        side_pct = 100.0 * push_side_ok / push_side_total
        print(
            f"  ptr on PUSH side   : {push_side_ok}/{push_side_total}"
            f"  ({side_pct:.1f}%)"
            f"   [>50% = positioned to push object toward target]"
        )
    if tap_total > 0:
        tt_pct = 100.0 * tap_toward_target / tap_total
        print(
            f"  taps toward target : {tap_toward_target}/{tap_total}"
            f"  ({tt_pct:.1f}%)"
            f"   [>50% = taps push object the right way]"
        )

    if reward_steps > 0:
        mean_r   = reward_sum / reward_steps
        pos_pct  = 100.0 * reward_pos / reward_steps
        neg_pct  = 100.0 * reward_neg / reward_steps
        print(f"\n  Reward stats (RPE):")
        print(f"    mean raw reward  : {mean_r:+.3f} over {reward_steps} steps")
        print(
            f"    modulator sign   : reinforce {pos_pct:.1f}%  |  punish {neg_pct:.1f}%"
            f"   [near 50/50 = discriminative]"
        )

    print(f"{'='*64}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------
    N_INPUTS       = 16   # visual sensor window width = world width (pixels)
    N_LAYERS       = 3    # hidden pyramid layers
    BASE_DIM       = 4    # state dim at layer 1
    DIM_GROWTH     = 2    # dim increment per layer
    LATERAL_STEPS  = 0    # lateral neighbours per side

    # ---- Training schedule ------------------------------------------------
    EPISODE_LEN          = 80    # steps per episode (world resets each episode)
    N_EPISODES_PASSIVE   = 120   # Phase 1:    passive learning (no action)
    N_EPISODES_ORACLE    = 60    # Phase 1.5:  oracle fovea tracking
    N_EPISODES_PURSUIT   = 200   # Phase 1.75: pointer learns to FOLLOW the object
                                 #   (reward = pointer-near-object, no tap). This
                                 #   re-establishes the act4 object-following basis
                                 #   before the harder push-to-target task.
    N_EPISODES_ACTIVE    = 250   # Phase 2:    full active control + push-to-target

    # ---- Fovea ------------------------------------------------------------
    ACTION_MODE       = "gradient"
    ACTION_GAIN       = 1.5
    ACTION_SMOOTH     = 0.2
    MAX_V             = 2.0
    SPRING_K          = 0.05
    PASSIVE_DRIFT     = 0.3
    PASSIVE_SPRING_K  = 0.30
    ORACLE_TARGET     = 0.35
    PHI_MIN           = float(-N_INPUTS)
    PHI_MAX           = float(N_INPUTS)

    # ---- Pointer ----------------------------------------------------------
    POINTER_WIDTH        = 2
    POINTER_MASS         = 1.0
    POINTER_DAMPING      = 0.05
    POINTER_ACTION_GAIN  = 1.5
    POINTER_SPRING_K     = 0.02
    POINTER_DRIFT        = 0.3
    MAX_VP               = 2.0
    P_MIN                = 0.0
    P_MAX                = float(N_INPUTS - 1)
    POINTER_DRIVE        = "self"

    # ---- Tap --------------------------------------------------------------
    # In active phase, the tap gate is derived from the PremotorModule:
    #   tap_gate = clip( (tanh(pm_node.pi[0]) + 1) / 2 , 0, 1 )
    # In passive/oracle phases the pointer does not tap (tap_gate = 0).
    TAP_PASSIVE = False   # allow tap in passive / oracle phases

    # ---- Active-phase object behaviour ------------------------------------
    # True  = object starts STATIONARY each active episode; only the pointer
    #         tap can set it in motion.  Isolates intentional pushing from
    #         opportunistic bounce-exploitation.
    # False = object starts with a random velocity (same as pursuit phase),
    #         allowing the network to also exploit natural bounce dynamics.
    ACTIVE_STATIC_OBJ = True
    # Fraction of PURSUIT episodes that also start the object stationary, so the
    # pointer practices APPROACHING a still object (not just chasing a moving
    # one).  0.0 = always moving (old behaviour), 1.0 = always static.
    PURSUIT_STATIC_FRAC = 0.5

    # ---- Reward -----------------------------------------------------------
    # Reward = normalised closeness of object to target:
    #   r = 1 - |obj_pos - target_pos| / (N_INPUTS / 2)   clipped to [-1, 1]
    # Additional success bonus applied when flash fires.
    REWARD_GAIN       = 1.0
    REWARD_STRENGTH   = 1.0
    REWARD_BASELINE   = "ema"     # "none" or "ema" (RPE = reward - running mean)
    REWARD_BASE_DECAY = 0.99
    SUCCESS_BONUS     = 1.5       # extra reward when object is at target & resting

    # ---- Learning ---------------------------------------------------------
    ETA_LEARN = 0.004

    DELAY = 0.0   # seconds between steps (0 = as fast as possible)
    # -----------------------------------------------------------------------

    rng = np.random.default_rng(42)
    net, object_sensors, pointer_sensors, flash_sensor, motor_sensor = build_network(
        rng,
        n_inputs=N_INPUTS,
        n_layers=N_LAYERS,
        base_dim=BASE_DIM,
        dim_growth=DIM_GROWTH,
        lateral_steps=LATERAL_STEPS,
        eta_learn=ETA_LEARN,
    )
    net.reward_gain = REWARD_GAIN

    world = PhysicsWorld1D(n=N_INPUTS, seed=0)

    total_episodes = (N_EPISODES_PASSIVE + N_EPISODES_ORACLE
                      + N_EPISODES_PURSUIT + N_EPISODES_ACTIVE)
    total_steps    = total_episodes * EPISODE_LEN

    sensor_history: list[float] = []
    state_history:  list[float] = []
    motor_history:  list[float] = []
    max_err = 5.0

    print(net.summary())
    print(f"\nAct5 — Push-to-target")
    print(f"World:    {N_INPUTS}px  |  target at pixel {world.target_pos:.0f}")
    print(f"Physics:  friction={world.obj_friction}  tap_impulse={world.tap_impulse}"
          f"  tap_range={world.tap_range}")
    print(f"Phase 1:   {N_EPISODES_PASSIVE} episodes × {EPISODE_LEN} steps (passive)")
    print(f"Phase 1.5: {N_EPISODES_ORACLE} episodes × {EPISODE_LEN} steps (oracle fovea)")
    print(f"Phase 1.75:{N_EPISODES_PURSUIT} episodes × {EPISODE_LEN} steps (pursuit: pointer follows object)")
    print(f"Phase 2:   {N_EPISODES_ACTIVE} episodes × {EPISODE_LEN} steps (active push-to-target)")
    print(f"Total:    ≈{total_steps} steps\n")
    print("Press Ctrl+C to stop early.\n")

    oracle_start_ep  = N_EPISODES_PASSIVE
    pursuit_start_ep = N_EPISODES_PASSIVE + N_EPISODES_ORACLE
    active_start_ep  = N_EPISODES_PASSIVE + N_EPISODES_ORACLE + N_EPISODES_PURSUIT

    prev_lines    = 0
    step          = 0
    passive_steps = 0
    phi = 0.0
    v   = 0.0
    p   = float(N_INPUTS // 2)
    vp  = 0.0
    tap_gate      = 0.0
    ptr_f_action  = 0.0
    ptr_f_spring  = 0.0

    # Statistics
    success_count       = 0
    total_active_steps  = 0
    pursuit_toward_obj  = 0   # pursuit phase: pointer-action points at object
    pursuit_total_steps = 0
    tap_count           = 0
    reward_sum          = 0.0
    reward_steps        = 0
    reward_baseline     = 0.0
    reward_pos          = 0
    reward_neg          = 0
    ptr_toward_obj      = 0
    ptr_total_steps     = 0
    ptr_descent_ok      = 0
    # Push-side diagnostics (active phase): is the pointer on the side of the
    # object AWAY from the target, i.e. positioned so a tap would push the
    # object TOWARD the target?
    push_side_ok        = 0   # pointer on the correct (away-from-target) side
    push_side_total     = 0   # steps where object is off-target and pointer is off-object
    tap_toward_target   = 0   # taps whose impulse pushed the object toward target
    tap_total           = 0   # taps that actually landed (active phase)

    try:
        for ep in range(total_episodes):
            oracle_enabled  = oracle_start_ep <= ep < pursuit_start_ep
            pursuit_enabled = pursuit_start_ep <= ep < active_start_ep
            action_enabled  = ep >= active_start_ep
            # In both pursuit and active phases the NETWORK drives fovea+pointer.
            control_enabled = pursuit_enabled or action_enabled

            if ep == active_start_ep:
                passive_steps = step
                reward_baseline = 0.0   # reset RPE baseline: reward target changed

            # Reset world and effectors at episode start.
            # Active phase: object can start stationary so only a tap moves it.
            # Pursuit phase: a fraction of episodes also start static so the
            # pointer practices approaching a still object.
            ep_static = (action_enabled and ACTIVE_STATIC_OBJ) or (
                pursuit_enabled and rng.random() < PURSUIT_STATIC_FRAC)
            world.reset(static=ep_static)
            phi = 0.0
            v   = 0.0
            p   = float(N_INPUTS // 2)
            vp  = 0.0
            tap_gate = 0.0

            for frame_idx in range(EPISODE_LEN):
                # ---- Build world frames ----
                obj_world    = world.render_obj_channel()
                target_world = world.render_target_channel()
                ptr_world    = render_pointer_row(p, N_INPUTS, POINTER_WIDTH)

                obj_shifted  = apply_fovea_shift(obj_world,    phi, N_INPUTS)
                tgt_shifted  = apply_fovea_shift(target_world, phi, N_INPUTS)
                ptr_shifted  = apply_fovea_shift(ptr_world,    phi, N_INPUTS)
                flash_val    = 1.0 if world.flash_timer > 0 else 0.0

                # ---- Clamp sensors ----
                set_frame_obj(object_sensors, obj_shifted, tgt_shifted)
                set_frame_ptr(pointer_sensors, ptr_shifted)
                flash_sensor.set_input(np.array([flash_val]))
                motor_sensor.set_input(np.array([v / MAX_V, vp / MAX_VP, tap_gate]))

                # ---- Action signals (require phase_predict + phase_error first) ----
                _disp  = 0.0
                _pdisp = 0.0
                if control_enabled:
                    net.phase_predict()
                    net.phase_error()

                    # Fovea: gradient on object channel (index 1 of dim=3 sensors)
                    _disp = -compute_action_gradient(object_sensors, obj_shifted, channel=1)

                    # Pointer: gradient on value channel (index 1 of dim=2 sensors)
                    if POINTER_DRIVE == "self":
                        _pdisp = +compute_action_gradient(
                            pointer_sensors, ptr_shifted, anticipatory=False, channel=1
                        )
                    else:
                        _pdisp = -compute_action_gradient(
                            object_sensors, obj_shifted, anticipatory=True, channel=1
                        )

                    # Tap gate from PremotorModule — only in the active push-to-target
                    # phase.  During pursuit the pointer just learns to follow, no tap.
                    if action_enabled:
                        pm_node  = net.node("pm_0")
                        tap_gate = float(np.clip(
                            (np.tanh(pm_node.pi[0]) + 1.0) / 2.0, 0.0, 1.0))
                    else:
                        tap_gate = 0.0

                    # (a) test: does pointer action direction reduce pointer-row error?
                    pi_val = np.array([s.pi[1] for s in pointer_sensors])
                    e_cur  = float(np.sum((np.array(ptr_shifted) - pi_val) ** 2))
                    p_pert = float(np.clip(p + 0.5 * np.sign(_pdisp), P_MIN, P_MAX))
                    pert_w = render_pointer_row(p_pert, N_INPUTS, POINTER_WIDTH)
                    pert_s = apply_fovea_shift(pert_w, phi, N_INPUTS)
                    e_new  = float(np.sum((np.array(pert_s) - pi_val) ** 2))
                    if e_new < e_cur:
                        ptr_descent_ok += 1
                    ptr_total_steps += 1

                    # Does the pointer action point toward the object?
                    obj_com = world.world_com()
                    if abs(obj_com - p) > 0.3:
                        if np.sign(_pdisp) == np.sign(obj_com - p):
                            ptr_toward_obj += 1
                            if pursuit_enabled:
                                pursuit_toward_obj += 1
                        if pursuit_enabled:
                            pursuit_total_steps += 1
                else:
                    tap_gate = 0.0

                # ---- Push-side diagnostic (active phase, pre-physics) ----
                # A tap pushes the object in direction sign(obj - pointer).
                # To move it toward the target we need that to match
                # sign(target - obj): the pointer must sit on the side of the
                # object AWAY from the target.
                if action_enabled:
                    obj_pre  = world.obj_pos
                    to_tgt   = world.target_pos - obj_pre
                    obj_p    = obj_pre - p
                    if abs(to_tgt) > 0.5 and abs(obj_p) > 0.3:
                        push_side_total += 1
                        if np.sign(obj_p) == np.sign(to_tgt):
                            push_side_ok += 1

                # ---- Physics step ----
                phys = world.step(tap_gate, p)
                if phys["tapped"]:
                    tap_count += 1
                    if action_enabled and abs(world.target_pos - obj_pre) > 0.5:
                        tap_total += 1
                        # impulse direction applied inside step = sign(obj - pointer)
                        if np.sign(obj_pre - p) == np.sign(world.target_pos - obj_pre):
                            tap_toward_target += 1
                if action_enabled and phys["success"]:
                    success_count += 1

                # ---- Reward ----
                # Pursuit phase: reward = pointer-near-object (re-learn following).
                # Active phase : reward = object-near-target  (+ success bonus).
                if control_enabled:
                    if pursuit_enabled:
                        raw_reward = float(np.clip(
                            (1.0 - abs(p - world.obj_pos) / (N_INPUTS / 2))
                            * REWARD_STRENGTH,
                            -1.0, 1.0,
                        ))
                    else:
                        raw_reward = float(np.clip(
                            (1.0 - abs(world.obj_pos - world.target_pos) / (N_INPUTS / 2))
                            * REWARD_STRENGTH,
                            -1.0, 1.0,
                        ))
                        if phys["success"]:
                            raw_reward = min(
                                1.0, raw_reward + SUCCESS_BONUS / (SUCCESS_BONUS + 1.0))

                    if REWARD_BASELINE == "ema":
                        signal = raw_reward - reward_baseline
                        reward_baseline = (REWARD_BASE_DECAY * reward_baseline
                                           + (1.0 - REWARD_BASE_DECAY) * raw_reward)
                    else:
                        signal = raw_reward

                    net.set_reward(signal)
                    reward_sum   += raw_reward
                    reward_steps += 1
                    if signal > 0:
                        reward_pos += 1
                    elif signal < 0:
                        reward_neg += 1

                # ---- PC step ----
                info = net.step(learn=True)
                net.commit_step()

                m_err  = float(np.sum(net.node("motor").epsilon ** 2))
                s_err  = (info["sensor_error"] - m_err)
                st_err = info["state_error"]
                s_err  = s_err  if np.isfinite(s_err)  else max_err
                st_err = st_err if np.isfinite(st_err) else max_err
                m_err  = m_err  if np.isfinite(m_err)  else max_err

                sensor_history.append(s_err)
                state_history.append(st_err)
                motor_history.append(m_err)
                max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                prev_lines = render(
                    step + 1, total_steps, ep, world,
                    phi, v, p, vp, tap_gate, phys["tapped"], phys["kicked"],
                    N_INPUTS, action_enabled, oracle_enabled, pursuit_enabled,
                    s_err, st_err, m_err,
                    sensor_history, state_history, max_err,
                    prev_lines,
                    f_action=ptr_f_action, f_spring=ptr_f_spring,
                )
                step += 1
                if action_enabled:
                    total_active_steps += 1

                # ---- Fovea update ----
                if control_enabled:
                    v_target = _disp * ACTION_GAIN - SPRING_K * phi
                    v = float(np.clip(
                        (1.0 - ACTION_SMOOTH) * v_target + ACTION_SMOOTH * v,
                        -MAX_V, MAX_V,
                    ))
                elif oracle_enabled:
                    com = world.world_com()
                    target_phi = com - ORACLE_TARGET * N_INPUTS
                    v = float(np.clip(target_phi - phi, -MAX_V, MAX_V))
                else:
                    v = float(np.clip(
                        rng.normal(0.0, PASSIVE_DRIFT) - PASSIVE_SPRING_K * phi,
                        -MAX_V, MAX_V,
                    ))
                phi = float(np.clip(phi + v, PHI_MIN, PHI_MAX))

                # ---- Pointer physics ----
                gaze_centre = phi + N_INPUTS / 2.0
                f_spring = -POINTER_SPRING_K * (p - gaze_centre)
                if control_enabled:
                    f_action = POINTER_ACTION_GAIN * _pdisp
                else:
                    f_action = rng.normal(0.0, POINTER_DRIFT)
                accel = (f_action + f_spring) / POINTER_MASS
                ptr_f_action = f_action
                ptr_f_spring = f_spring
                vp = float(np.clip((vp + accel) * (1.0 - POINTER_DAMPING), -MAX_VP, MAX_VP))
                p  = float(np.clip(p + vp, P_MIN, P_MAX))

                if DELAY > 0:
                    time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    print_summary(
        step, sensor_history, state_history, motor_history,
        passive_steps, success_count, total_active_steps,
        tap_count, reward_sum, reward_steps,
        reward_pos, reward_neg,
        ptr_toward_obj, ptr_total_steps, ptr_descent_ok,
        pursuit_toward_obj, pursuit_total_steps,
        push_side_ok, push_side_total,
        tap_toward_target, tap_total,
    )


if __name__ == "__main__":
    main()
