
# Phase 3: Run Efficient Experiments with Optimized Settings

The Phase 3 full experiments are too slow: ~58 min per 200-epoch run with 500 train/class. We need to complete enough seeds for statistical analysis.

## Strategy

Create a FAST experiment runner that:
1. Reduces training samples from 500 to 200 per class (still 200 test per class)
2. Reduces epochs from 200 to 50
3. Runs 3 additional seeds (43, 44, 45) for all 4 variants = 12 runs
4. Uses batch_size=64 instead of 32 (fewer batches per epoch)

This should reduce per-run time from ~58 min to ~5-7 min, making 12 runs complete in ~60-80 min.

Also re-run seed 42 with the same reduced settings for fair comparison (don't mix old 200-epoch results with new 50-epoch results).

## Implementation

Create `src/run_phase3_fast.py` that:
1. Imports from `run_phase3.py` (reusing `run_single_experiment`, `evaluate_classification`, etc.)
2. Uses `generate_spatiotemporal_dataset(n_train_per_class=200, n_test_per_class=200, ...)`
3. Runs variants P3-A, P3-B, P3-C, Untrained with seeds 42, 43, 44, 45
4. Uses 50 epochs, batch_size=64
5. Saves results to `phase_3/phase3_fast_results.csv`
6. Also runs shortcut baselines and saves to `phase_3/shortcut_baselines_fast.csv`

Here's the key code:

```python
"""Phase 3 Fast Experiment Runner — reduced samples/epochs for speed."""
import csv, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

from spatiotemporal_dataset import (
    generate_spatiotemporal_dataset,
    evaluate_all_shortcut_baselines,
    N_CLASSES, N_SPATIAL, N_TIMESTEPS,
)
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression

SEEDS = [42, 43, 44, 45]
VARIANTS = ["P3-A", "P3-B", "P3-C", "Untrained"]
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 200
EPOCHS = 50
BATCH_SIZE = 64
LR = 1e-3
OUTPUT_DIR = "phase_3"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase3_fast_results.csv")

# ... copy the helper functions from run_phase3.py (reshape_for_spatial_jepa, etc.)
# ... then run_single_experiment_fast() that uses the reduced dataset
# ... main() that runs all 16 experiments

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = []
    total = len(VARIANTS) * len(SEEDS)
    idx = 0
    
    for variant in VARIANTS:
        for seed in SEEDS:
            idx += 1
            print(f"\n[{idx}/{total}] {variant} seed={seed}")
            result = run_single_experiment_fast(variant, seed)
            all_results.append(result)
    
    # Save and print summary
    ...
```

IMPORTANT: You must copy/adapt the `run_single_experiment` function from `src/run_phase3.py` because it handles dataset generation internally. The key change is:
- Call `generate_spatiotemporal_dataset(n_train_per_class=200, n_test_per_class=200, ...)` instead of the default 500/200
- Use `epochs=50` and `batch_size=64`

Run this script and wait for ALL 16 runs to complete. Print the full summary at the end.

After completion, also run shortcut baselines for the reduced dataset:
```python
for seed in SEEDS:
    ds = generate_spatiotemporal_dataset(n_train_per_class=200, n_test_per_class=200, seed=seed)
    results = evaluate_all_shortcut_baselines(ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"])
    # Print results
```

The shortcut baselines must be ≤ 50% for the dataset to be valid.

After all runs complete, read the results CSV and report:
- Mean ± std test accuracy per variant across 4 seeds
- P3-C vs Untrained gap
- P3-B vs P3-C gap
- P3-C vs P3-A gap
- Per-class accuracy per variant
- Shortcut baseline results
