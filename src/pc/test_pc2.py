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

# ---------------------------------------------------------------------------
# Movement patterns  (8 positions × N frames)
# ---------------------------------------------------------------------------

PATTERNS: dict[str, list[list[int]]] = {
    "left→right": [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
    ],
    "right→left": [
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
    ],
    "bounce":  [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
    ],
    "two-dots": [
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 1],
    ],
}

POSITIONS = [round(0.1 * (i + 1), 1) for i in range(8)]  # 0.1 … 0.8

# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(rng: np.random.Generator) -> tuple[PCNetwork, list[SensorNode]]:
    net = PCNetwork(
        eta_inf=0.05,
        n_relax=80,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=0.5,
        eta_learn=0.005,
        lambda_decay=0.001,
        rng=rng,
    )

    # Layer 0 — sensor nodes  (dim=2: position, value)
    sensors: list[SensorNode] = []
    for i in range(8):
        s = net.add(SensorNode(f"s{i}", dim=2))
        sensors.append(s)

    # Layer 1 — hidden nodes  (dim=8 each)
    for i in range(8):
        net.add(PCNode(f"h{i}", dim=8, activation="tanh", rng=rng))

    # Layer 2 — single abstract node  (dim=16)
    net.add(PCNode("top", dim=16, activation="tanh", rng=rng))

    # Connections: hidden → sensor  (UP)
    for i in range(8):
        net.connect(f"h{i}", f"s{i}", ConnType.UP)

    # Connections: top → hidden  (UP)
    for i in range(8):
        net.connect("top", f"h{i}", ConnType.UP)

    # Lateral connections between adjacent hidden nodes
    for i in range(7):
        net.connect(f"h{i}", f"h{i+1}", ConnType.LATERAL)
        net.connect(f"h{i+1}", f"h{i}", ConnType.LATERAL)

    return net, sensors


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def set_frame(sensors: list[SensorNode], values: list[int]) -> None:
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
    """Move cursor up n lines and clear them."""
    for _ in range(n):
        sys.stdout.write("\x1b[1A\x1b[2K")


def render(
    step: int,
    total_steps: int,
    pattern_name: str,
    frame_idx: int,
    frame_values: list[int],
    sensor_err: float,
    state_err: float,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
) -> int:
    """Render the display, erase previous output. Returns number of lines printed."""
    if prev_lines > 0:
        _clear_lines(prev_lines)

    dot_str = "".join("█" if v else "·" for v in frame_values)
    pos_str = "  ".join(f"{POSITIONS[i]:.1f}" if frame_values[i] else "   " for i in range(8))

    lines = []
    lines.append(f"Step {step:5d}/{total_steps}  pattern: {pattern_name:<12s}  frame {frame_idx+1}/8")
    lines.append(f"  Input:  [{dot_str}]")
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

    output = "\n".join(lines)
    print(output, end="", flush=True)
    return len(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rng = np.random.default_rng(42)
    net, sensors = build_network(rng)

    pattern_names = list(PATTERNS.keys())
    total_steps = 800   # adjust for longer training
    delay = 0.0         # set > 0 (e.g. 0.05) to slow down for watching

    sensor_history: list[float] = []
    state_history: list[float] = []
    max_err = 5.0       # initial scale for bars; auto-adjusts

    print(net.summary())
    print(f"\nTraining for {total_steps} steps ({total_steps // 8} full sequences)\n")
    print("Press Ctrl+C to stop early.\n")

    prev_lines = 0
    step = 0

    try:
        while step < total_steps:
            # Pick a random pattern, repeat 3–4 times
            name = random.choice(pattern_names)
            frames = PATTERNS[name]
            repeats = random.randint(3, 4)

            for _ in range(repeats):
                for frame_idx, frame_values in enumerate(frames):
                    if step >= total_steps:
                        break

                    set_frame(sensors, frame_values)
                    info = net.step(learn=True)

                    s_err = info["sensor_error"]
                    st_err = info["state_error"]
                    sensor_history.append(s_err)
                    state_history.append(st_err)
                    max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                    prev_lines = render(
                        step + 1, total_steps, name, frame_idx, frame_values,
                        s_err, st_err,
                        sensor_history, state_history,
                        max_err, prev_lines,
                    )
                    step += 1

                    if delay > 0:
                        time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    # Final summary
    if sensor_history:
        n = len(sensor_history)
        first_q = sensor_history[:max(1, n // 10)]
        last_q  = sensor_history[-(n // 10):]
        print(f"\n{'='*50}")
        print(f"  Steps completed   : {step}")
        print(f"  Sensor error start: {np.mean(first_q):.4f}  (mean of first 10%)")
        print(f"  Sensor error end  : {np.mean(last_q):.4f}  (mean of last 10%)")
        print(f"  Improvement       : {np.mean(first_q) - np.mean(last_q):+.4f}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
