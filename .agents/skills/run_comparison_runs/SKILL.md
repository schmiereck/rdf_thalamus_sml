---
name: run-comparison-runs
description: Instructions for running headless benchmark/comparison runs, setting env variables like ACT21_HEADLESS, and writing probe scripts with macro_log_fn hooks to verify changes.
---

# Headless Comparison Runs (Predictive Coding Simulation)

Use this skill when you need to run comparison simulations (without matplotlib visualization) to verify the impact of code changes, parameter changes, or environment configurations on the predictive coding simulation (ACT16 / ACT21).

## General Mechanism

- **Headless Mode**: Set environment variable `ACT21_HEADLESS=1` (or pass `headless=True` in script calls). This runs the simulation in text-only mode (headless) which executes very quickly and outputs directly to stdout.
- **Python Executable**: Always run python via the virtual environment: `.venv/Scripts/python.exe`.
- **PowerShell Syntax**:
  ```powershell
  $env:ACT21_HEADLESS="1"
  .venv/Scripts/python.exe src/pc/pc_act21.py
  ```

## Pattern A: Default Headless Run with Environment Switches

The default simulation script `src/pc/pc_act21.py` prints summary metrics at the end (A/B/C lines). Use these to compare baseline and modified behaviors:
```
recovery-DAgger polish (...): frozen FIXED-goal delivery 2/12 -> 8/12
A) frozen, FIXED goals (post-perturb): delivered 1/10
B) lifelong + CURIOSITY (24 eps): delivered 19/24
C) frozen, SAME FIXED goals (after)  : delivered 8/10
```

### Key Environment Variables

| Variable | Description |
| :--- | :--- |
| `ACT21_HEADLESS=1` | Runs text-only, without UI visualization window. |
| `ACT21_STEER=1` | Command interface (runs headless self-test, prints self-test ... 8/12). |
| `ACT21_EPISODES`, `ACT21_BASE` | Number of explore and A/C episodes. |
| `ACT21_RECOVER=0` | Disables Recovery-DAgger (useful to isolate effects). |
| `ACT16_CARRY_Z` | Carry height parameter. |
| `ACT16_WRIST=0/1` | Wrist orientation option. |
| `ACT_CONTRAST_SEL`, `ACT_VERIFY` | Perception-tail fix toggles. |
| `ACT16_PERSIST=1` | Keep scene between episodes. |
| `ACT16_ELONG`, `ACT16_SCENE_N` | Elongated objects / Distractor counts. |

Example command for A/B testing variables:
```powershell
$env:ACT16_CARRY_Z="0.055"; .venv/Scripts/python.exe src/pc/pc_act21.py
$env:ACT16_CARRY_Z="0.09";  .venv/Scripts/python.exe src/pc/pc_act21.py
```

## Pattern B: Probe Scripts with Measurement Hooks

To measure values not printed by default (e.g., specific fovea fixations, exact carry heights), create temporary probe scripts (e.g., `src/pc/_probe.py`) importing components and calling `run_combined` with callback hooks.

### Simulation Hooks in `run_combined`

| Hook | Arguments | Purpose |
| :--- | :--- | :--- |
| `log_fn` | `(state, aim, j5)` | Runs every execution step (useful to collect demonstrations). |
| `macro_log_fn` | `(state, aim, j5, phase)` | Runs every step + FSM phase (e.g., filter/measure only during carry phase). |
| `episode_end_fn` | `(ep, ok, err)` | Runs at the end of each episode (delivers success status + error distance). |
| `teacher_log_fn` | `(state, aim, j5)` | Visited state (DAgger). |

### Quiet Output & Monkeypatching
- Set `act16.run_combined._quiet = True` to suppress the verbose per-episode stdout.
- Monkeypatch constants to test multiple conditions dynamically (e.g., `act16.CARRY_Z = cz`).

### Skeleton Script (`src/pc/_probe.py`)

```python
import os, sys
sys.path.insert(0, "src")
import numpy as np
from pc.pc_act14 import BracketArmSim
from pc.arm_modules import BodyModelModule
import pc.pc_act16 as act16

sim = BracketArmSim(render_wh=(240, 240))
sim.set_reach_site("contact")
bm = BodyModelModule(rng=np.random.default_rng(5))
bm.babble(sim, 3000)
act16.run_combined._quiet = True

for cz in (0.055, 0.090):  # A/B loop
    act16.CARRY_Z = cz
    bottoms = []
    
    def mlog(state, aim, j5, phase):
        hx, hy, hz, cx, cy, cz_, tx, ty, j5_, obj_h, obj_fp = state
        if phase == "carry":
            bottoms.append(cz_ - obj_h)  # calculate bottom height of carried cube
            
    d, m = act16.run_combined(sim, bm.body, None, "overview",
                              episodes=6, macro_log_fn=mlog, cap=1500)
    b = np.array(bottoms)
    print(f"CARRY_Z={cz}: delivered {d}/{m} | bottom mean {b.mean()*1000:.0f} mm "
          f"| clears 24mm {np.mean(b>0.024)*100:.0f}%")
```

Run via PowerShell:
```powershell
$env:ACT21_HEADLESS="1"
.venv/Scripts/python.exe src/pc/_probe.py
```

> [!NOTE]
> `run_combined` internally seeds with `np.random.default_rng(1)`, meaning consecutive runs with different parameters evaluate identical episode sequences.

## Analyzing Results in PowerShell

For long runs, redirect output to a file or stream and filter key metrics using `Select-String`:
```powershell
.venv/Scripts/python.exe src/pc/pc_act21.py 2>&1 | Select-String -Pattern "delivered|recovery-DAgger|SAME FIXED"
```

## Caveats and Best Practices
- **Temporary Probes**: Always clean up probe scripts (e.g., `src/pc/_probe.py`) after usage so they don't pollute the git repository.
- **Self-Test Constraints**: Headless self-test runs (with `ACT21_STEER=1`) can yield more pessimistic metrics compared to full default runs because they lack Lifelong adaptation, Recovery-DAgger, and fixed goals. Benchmark key statements using the full default run where possible.
