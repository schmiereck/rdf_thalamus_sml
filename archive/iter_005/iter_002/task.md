# Phase 3: Optimized Experiment Execution

You must run the Phase 3 spatiotemporal grid experiments efficiently. The previous attempt showed that 200-epoch/500-sample runs take ~28 min each, making 20 runs impossible. You need to optimize and complete all experiments within ~45 minutes.

## CRITICAL: Pre-Registration Compliance

Before running ANY code, read `src/pre_registration.md` to understand the pre-registered falsification criteria. The revised F2 criterion requires paired t-test with p < 0.05 and Cohen's d ≥ 1.0 across 5 seeds. You MUST use 5 seeds for statistical validity.

## Your Mission

Run 4 variants × 5 seeds = 20 experiments and save results to `phase_3/phase3_full_results.csv`.

## Strategy for Speed

### Option A: Reduce epochs and training samples
- Use **30 epochs** (JEPA converges fast; loss drops ~24% in first 20 epochs)
- Use **200 train/class** (800 total; sufficient for d=16 linear probe)  
- Use **100 test/class** (400 total)
- Use **batch_size=64** (fewer batches per epoch)
- Expected time per P3-B/C run: ~90s
- Expected time per P3-A run: ~180s (2× sequential)
- Expected time per Untrained run: ~40s (no backward pass)
- Total: ~90×10 + 180×5 + 40×5 = 900 + 900 + 200 = 2000s ≈ 33 min

### Option B (fallback): If Option A still too slow, reduce to 3 seeds and 20 epochs

## Implementation Steps

### Step 1: Create an optimized runner script

Write `src/run_phase3_optimized.py` that:

```python
"""
Phase 3 Optimized Experiment Runner.
Settings: 30 epochs, 200 train/class, 100 test/class, batch=64, 5 seeds.
Saves results incrementally after each run.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from spatiotemporal_dataset import generate_spatiotemporal_dataset, N_CLASSES
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression
from run_phase3 import (
    create_jepa_losses, reshape_for_spatial_jepa, reshape_spatial_grads_back,
    reshape_for_temporal_jepa, reshape_temporal_grads_back,
    train_jepa_epoch, evaluate_classification
)

SEEDS = [42, 43, 44, 45, 46]
VARIANTS = ["P3-A", "P3-B", "P3-C", "Untrained"]
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100
EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-3
OUTPUT_CSV = "phase_3/phase3_full_results.csv"

def run_single_opt(variant, seed, epochs, batch_size, lr, update_encoder):
    # [similar to run_phase3.py but with reduced dataset]
    rng = np.random.default_rng(seed)
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=seed,
    )
    # ... rest of training logic from run_phase3.py ...
```

### Step 2: Run a quick profiling test FIRST

Before the full suite, run a SINGLE 30-epoch P3-B experiment (seed=42) to verify timing:
```bash
cd C:\Users\thomas\Projekte\rdf_thalamus_sml
python -c "
import sys, os, time
sys.path.insert(0, 'src')
from run_phase3 import run_single_experiment
t0 = time.time()
result = run_single_experiment('P3-B', 42, epochs=30, batch_size=64, lr=1e-3, update_encoder=True)
t1 = time.time()
print(f'30-epoch P3-B: {t1-t0:.1f}s')
# The run_single_experiment uses 500 train/class by default
# We need to modify to use 200 train/class for speed
"
```

If this takes > 120s, we need to further reduce settings. If < 90s, we're good.

### Step 3: Create the full optimized runner and execute

Write the complete `src/run_phase3_optimized.py` that:
- Uses N_TRAIN_PER_CLASS=200, N_TEST_PER_CLASS=100
- Uses EPOCHS=30, BATCH_SIZE=64
- Saves results incrementally to CSV after EACH run (so data isn't lost if interrupted)
- Runs Untrained FIRST (fastest) to get baseline data quickly
- Then runs P3-C (the primary hypothesis test)
- Then P3-B and P3-A

IMPORTANT: The `run_single_experiment` function in run_phase3.py generates data with 500 train/class. You need to modify the call or write a new function that uses 200 train/class. The simplest approach: copy the `run_single_experiment` function into your optimized script and change the dataset generation parameters.

### Step 4: Run shortcut baselines

After the main experiments, run shortcut baselines using `evaluate_all_shortcut_baselines` from spatiotemporal_dataset.py:
```python
from spatiotemporal_dataset import evaluate_all_shortcut_baselines
ds = generate_spatiotemporal_dataset(n_train_per_class=200, n_test_per_class=100, ...)
results = evaluate_all_shortcut_baselines(ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"])
```
Save to `phase_3/shortcut_baselines.csv`.

### Step 5: Document experiment configuration

Write `phase_3/experiment_config.txt` with the actual settings used.

## Working Directory

`C:\Users\thomas\Projekte\rdf_thalamus_sml`

## Key Code Details

- The `generate_spatiotemporal_dataset` function accepts `n_train_per_class` and `n_test_per_class` parameters
- The `run_single_experiment` function hardcodes 500/200 — you need to parameterize or copy it
- For P3-A: sequential training (spatial first for EPOCHS epochs, then temporal for EPOCHS epochs)
- For P3-B/C: joint training (alpha=0.5) for EPOCHS epochs
- For Untrained: forward pass + JEPA predictors trained, but no encoder backward pass
- The evaluate_classification function takes the encoder, train/test grids, and labels

## Output Files Required

1. `phase_3/phase3_full_results.csv` — 20 rows (4 variants × 5 seeds), with columns:
   variant, seed, train_acc, test_acc, final_spatial_jepa_loss, final_temporal_jepa_loss, training_time_sec, class_0_acc, class_1_acc, class_2_acc, class_3_acc

2. `phase_3/shortcut_baselines.csv` — shortcut baseline results

3. `phase_3/experiment_config.txt` — settings documentation

## Success Criteria

- All 20 experiment rows present in the CSV
- No NaN or infinite values
- Each variant has exactly 5 seeds
- Shortcut baselines computed
- Total execution time < 45 minutes
