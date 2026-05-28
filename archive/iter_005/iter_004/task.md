# Phase 3: Complete P3-A Runs and Clean Up Results

The Phase 3 experiment results file `phase_3/phase3_full_results.csv` has duplicate rows from multiple background processes. P3-A runs (the slowest variant, ~3 min each) are not yet in the file. You need to:

## Task 1: Clean Up Duplicates

Read the current CSV, deduplicate by keeping only the FIRST occurrence of each (variant, seed) pair, and write a clean version back.

## Task 2: Run Missing P3-A Experiments

P3-A requires sequential training (spatial first 30 epochs, then temporal 30 epochs). Each run takes ~3 minutes. You need 5 runs (seeds 42-46).

Write a script that runs P3-A experiments and appends to the CLEANED CSV:

```python
import sys, os, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, 'src')

# First, deduplicate
import pandas as pd  # or use csv manually
# Read, deduplicate by (variant, seed) keeping first, write back

# Then run remaining P3-A experiments
from run_phase3_optimized import run_single_experiment_opt, save_result_incrementally
# ... check which P3-A seeds are missing and run them
```

IMPORTANT: The `run_phase3_optimized.py` uses:
- EPOCHS=30, N_TRAIN_PER_CLASS=200, N_TEST_PER_CLASS=100, BATCH_SIZE=64, LR=1e-3
- For P3-A: sequential training (spatial first 30 epochs, then temporal 30 epochs)
- The function is `run_single_experiment_opt(variant, seed, epochs, batch_size, lr, update_encoder, n_train_per_class, n_test_per_class)`

## Task 3: Run Shortcut Baselines

After P3-A is done, run shortcut baselines for all 5 seeds and save to `phase_3/shortcut_baselines.csv`.

## Task 4: Verify Final Results

After all runs, verify:
- Exactly 20 unique (variant, seed) rows in the CSV
- 4 variants × 5 seeds each
- No duplicate rows
- Reasonable accuracy values (all between 0 and 1)
- Save the clean final results to `phase_3/phase3_full_results.csv`

## Working Directory
`C:\Users\thomas\Projekte\rdf_thalamus_sml`

## Key Information
- The deduplication should keep the FIRST occurrence of each (variant, seed) pair
- P3-A runs take ~3 minutes each (sequential spatial then temporal training)
- All other variant runs (P3-B, P3-C, Untrained) should already be complete from prior runs
- If pandas is not available, use manual csv deduplication
- The shortcut baseline function is `evaluate_all_shortcut_baselines` from `src/spatiotemporal_dataset.py`

## Expected Timing
- Cleanup: ~1s
- P3-A runs: 5 × ~180s = ~900s = ~15 min
- Shortcut baselines: ~30s
- Total: ~16 min
