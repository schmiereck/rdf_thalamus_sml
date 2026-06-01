# Implementation Plan: test_pc_act1.py

Active Inference demo — pyramidal PC network with a 1D fovea that tracks
moving blobs by minimising its own prediction error.

---

## Context & Goals

Build on the existing code in `src/pc/`:
- `PCNetwork`, `PCNode`, `SensorNode`, `PCConnection`, `ConnType` (unchanged)
- `PatternGenerator` with toroidal LTR/RTL wrap-around (unchanged)

New file: `src/pc/test_pc_act1.py`

The network perceives a 1D world through a sensor window. It can shift that
window left/right (eye velocity = the action). A motor sensor node receives
the current velocity as efference copy. The top layer predicts both the
visual scene and the next eye velocity.

---

## World & Fovea Mechanics

**World size = sensor window size = N_INPUTS** (no change to PatternGenerator).

Fovea state:
```
phi   : float   — left edge of view window in world coordinates, range [0, N_INPUTS)
v     : float   — current eye velocity (pixels/step), range [-MAX_V, +MAX_V]
```

At each step, before feeding sensors:
1. Shift the world frame by `phi` (circular): `shifted[i] = world[(i + round(phi)) % N_INPUTS]`
2. Feed `shifted` into the visual sensor nodes
3. Feed `v` into the motor sensor node (efference copy)

After each PC step:
4. Read the network's motor prediction (see Action Readout below)
5. Update: `v = clip(predicted_v, -MAX_V, +MAX_V)`
6. Update: `phi = (phi + v) % N_INPUTS`

**Anti-aliasing note**: use integer shift for simplicity (round phi).
Fractional shift with linear interpolation can be added later.

---

## Architecture: Configurable Pyramid

### Configuration block (top of `main()`)

```python
N_INPUTS        = 16    # visual sensor positions
N_LAYERS        = 3     # number of hidden pyramid layers (depth)
BASE_DIM        = 4     # state dimension at layer 1 (nearest sensors)
DIM_GROWTH      = 2     # dim increment per layer upward
LATERAL_STEPS   = 1     # how many lateral neighbours to connect (each side)
N_TRAIN_PATTERNS = 10
N_NOVEL_PATTERNS = 10
REPEATS_PER_SEQ  = 3
N_EPOCHS_PASSIVE = 30   # Phase 1: no action, learn motion
N_EPOCHS_ACTIVE  = 20   # Phase 2: action enabled
MAX_V            = 2.0  # max eye velocity in pixels/step
ETA_ACTION       = 0.5  # how strongly predicted v is applied (0=no action, 1=full)
DELAY            = 0.0
```

### Layer widths (pyramid)

```
Layer 0 (sensors): N_INPUTS visual nodes  +  1 motor node
Layer 1 (hidden):  N_INPUTS // 2          nodes
Layer 2 (hidden):  N_INPUTS // 4          nodes
Layer k (hidden):  N_INPUTS // 2**k       nodes
Top layer:         max(1, N_INPUTS // 2**N_LAYERS)  nodes
```

With N_INPUTS=16, N_LAYERS=3: widths are 8 → 4 → 2 (top has 2 nodes).
With N_LAYERS=4: widths are 8 → 4 → 2 → 1 (single top node).

### Layer dimensions

```
dim(layer k) = BASE_DIM + (k - 1) * DIM_GROWTH    (k = 1 … N_LAYERS)
```

Example (BASE_DIM=4, DIM_GROWTH=2):
- Layer 1: dim=4
- Layer 2: dim=6
- Layer 3: dim=8  (top layer with N_LAYERS=3)

### Node naming

```
Visual sensors:  "s0" … "s{N_INPUTS-1}"
Motor sensor:    "motor"
Hidden layer k, node j:  "h{k}_{j}"         (k=1..N_LAYERS)
```

### Connections

**Visual UP connections (each hidden node ← 2 adjacent nodes below):**

Layer 1 node `j` connects from sensors `s{2j}` and `s{2j+1}`:
```python
for j in range(width_layer_1):
    net.connect(f"h1_{j}", f"s{2*j}",   ConnType.UP)
    net.connect(f"h1_{j}", f"s{2*j+1}", ConnType.UP)
```

Layer k+1 node `j` connects from layer k nodes `h{k}_{2j}` and `h{k}_{2j+1}`:
```python
for j in range(width_layer_k1):
    net.connect(f"h{k+1}_{j}", f"h{k}_{2*j}",   ConnType.UP)
    net.connect(f"h{k+1}_{j}", f"h{k}_{2*j+1}", ConnType.UP)
```

**Lateral connections (within each hidden layer):**

Within layer k, connect node j to its LATERAL_STEPS nearest neighbours on each side:
```python
for j in range(width):
    for d in range(1, LATERAL_STEPS + 1):
        if j + d < width:
            net.connect(f"h{k}_{j}",   f"h{k}_{j+d}", ConnType.LATERAL)
            net.connect(f"h{k}_{j+d}", f"h{k}_{j}",   ConnType.LATERAL)
```

**Motor connection:**

Top layer node(s) → motor sensor (UP connection, predicts eye velocity):
```python
for j in range(width_top):
    net.connect(f"h{N_LAYERS}_{j}", "motor", ConnType.UP,
                pressure_scale=0.05)   # weak back-pressure, motor is narrow
```

**pressure_scale guidance:**
- All visual UP connections: pressure_scale=1.0 (default)
- Connections from the top layer down to the layer below: pressure_scale=0.1
  (same as current test_pc_gen1.py — prevents top node dominating)
- Motor connection: pressure_scale=0.05

### Motor sensor node

```python
motor = net.add(SensorNode("motor", dim=1))
```

At each step: `motor.set_input(np.array([v]))`

The motor sensor is clamped (like all SensorNodes). Its prediction error
measures how well the network predicted the eye velocity.

---

## Action Readout

After each `net.step()`, read the predicted motor value:

```python
def read_predicted_velocity(net: PCNetwork) -> float:
    """
    The prediction for the motor sensor comes from its connected hidden nodes
    (stored in motor.pi after _phase_predict).
    motor.pi is the aggregated prediction pushed to the motor node.
    Clip to [-MAX_V, MAX_V].
    """
    predicted = float(net.node("motor").pi[0])   # pi = aggregated prediction
    return predicted
```

Apply the action:
```python
if action_enabled:
    predicted_v = read_predicted_velocity(net)
    v = float(np.clip(ETA_ACTION * predicted_v + (1 - ETA_ACTION) * v,
                      -MAX_V, MAX_V))
    phi = (phi + v) % N_INPUTS
```

When `action_enabled=False` (Phase 1): phi stays 0, v stays 0.

---

## Two-Phase Training

### Phase 1 — Passive (no action)

- `phi = 0`, `v = 0` throughout
- `motor.set_input(np.array([0.0]))` every step
- `net.step(learn=True)` normally
- Goal: network learns the visual motion patterns

### Phase 2 — Active (action enabled)

- `phi` and `v` updated each step as described above
- `motor.set_input(np.array([v]))` — efference copy of current velocity
- `net.step(learn=True)` — continues learning with action
- Goal: network learns to predict eye velocity that keeps blobs in view

Training loop structure:
```python
for epoch in range(N_EPOCHS_PASSIVE + N_EPOCHS_ACTIVE):
    action_enabled = (epoch >= N_EPOCHS_PASSIVE)
    phi, v = 0.0, 0.0   # reset fovea each epoch
    for name, world_frames in train_patterns:
        for _ in range(REPEATS_PER_SEQ):
            for world_frame in world_frames:
                shifted = apply_fovea_shift(world_frame, phi, N_INPUTS)
                set_frame(visual_sensors, shifted)
                motor.set_input(np.array([v]))
                info = net.step(learn=True)
                if action_enabled:
                    predicted_v = read_predicted_velocity(net)
                    v = float(np.clip(ETA_ACTION * predicted_v
                                      + (1 - ETA_ACTION) * v,
                                      -MAX_V, MAX_V))
                    phi = (phi + v) % N_INPUTS
```

---

## Fovea Shift Helper

```python
def apply_fovea_shift(world_frame: list[float], phi: float,
                      n: int) -> list[float]:
    """Circular shift of world_frame by phi (integer pixels)."""
    offset = round(phi) % n
    if offset == 0:
        return world_frame
    arr = np.array(world_frame)
    return np.roll(arr, -offset).tolist()
```

---

## Input Helpers

```python
def set_frame(visual_sensors: list[SensorNode], values: list[float]) -> None:
    """Push [position, value] into visual sensor nodes.
    Positions are fixed retinal coordinates (unchanged by fovea shift)."""
    pos = [round((i + 1) / len(visual_sensors), 4) for i in range(len(visual_sensors))]
    for i, (s, v) in enumerate(zip(visual_sensors, values)):
        s.set_input(np.array([pos[i], float(v)]))
```

---

## Display / render()

Extend the existing `render()` signature with fovea info:

```python
def render(
    step: int,
    total_steps: int,
    pattern_name: str,
    frame_idx: int,
    frame_values: list[float],    # shifted (what sensors actually see)
    sensor_err: float,
    state_err: float,
    motor_err: float,             # NEW: prediction error of motor node
    phi: float,                   # NEW: current fovea position
    v: float,                     # NEW: current eye velocity
    action_enabled: bool,         # NEW
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
) -> int:
```

Display additions:
- Show fovea position: `φ={phi:.1f}  v={v:+.2f}`
- Show motor_err bar alongside sensor_err and state_err
- Annotate Phase 1 / Phase 2 in the header line

---

## Summary (print_summary)

Same structure as test_pc_gen1.py, plus:
- Separate start/end/Δ row for `motor_error`
- Note which epoch Phase 2 began
- In per-pattern table: add `motor` error column

---

## build_network() function signature

```python
def build_network(
    rng: np.random.Generator,
    n_inputs: int = 16,
    n_layers: int = 3,
    base_dim: int = 4,
    dim_growth: int = 2,
    lateral_steps: int = 1,
) -> tuple[PCNetwork, list[SensorNode], SensorNode]:
    """
    Returns (net, visual_sensors, motor_sensor).
    """
```

The function builds the pyramid as described above and returns:
- `visual_sensors`: list of N_INPUTS SensorNodes ("s0".."s{N_INPUTS-1}")
- `motor_sensor`: the single SensorNode("motor")

---

## File structure

```
src/pc/test_pc_act1.py
```

Imports:
```python
import os, sys, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.pattern_generator import PatternGenerator
```

Reuse from test_pc_gen1.py (copy, do not import):
- `sample_named_patterns()`
- `measure_per_pattern_errors()`
- `print_summary()` (extended as above)
- `_sparkline()`, `_bar()`, `_clear_lines()`

---

## PCNode.pi access

The action readout needs to read `motor.pi` (the aggregated prediction).
Check `src/pc/node.py` — `pi` should already be a public attribute on PCNode
set by `finalize_prediction()`. Confirm this before implementing the readout;
if it is named differently, adjust `read_predicted_velocity()`.

---

## Testing checklist

1. `python src/pc/test_pc_act1.py` runs without error for N_LAYERS=2,3,4
2. Phase 1: sensor_error decreases over passive epochs
3. Phase 2: motor_error is non-zero and decreases (network learns to predict v)
4. With action enabled and a single moving dot: phi tracks the dot position
   (visible in the display: phi should oscillate or drift in the direction of motion)
5. Novel patterns: lower motor_error than train patterns = bad; roughly equal = good generalisation

---

## Open questions / deferred

- Fractional fovea shift (linear interpolation at pixel edges)
- World larger than sensor window (requires PatternGenerator change)
- Temporal memory (recurrent connections or explicit delay taps)
- Curriculum: gradually increase MAX_V over active epochs
