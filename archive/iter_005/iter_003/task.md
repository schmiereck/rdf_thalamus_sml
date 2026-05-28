# Phase 3: Complete Remaining Experiments

The optimized experiment runner script exists at `src/run_phase3_optimized.py`. Results so far are in `phase_3/phase3_full_results.csv` with 7 rows completed:
- Untrained: seeds 42, 43, 44, 45, 46 (5/5 done)
- P3-C: seeds 42, 43 (2/5 done, need 44, 45, 46)
- P3-B: 0/5 done
- P3-A: 0/5 done

Total remaining: 13 runs.

## Your Task

Write and run a simple Python script that completes the remaining 13 experiment runs, APPENDING results to the existing CSV file. Do NOT delete or overwrite the existing results.

## Script to Write

Create `src/run_remaining_phase3.py`:

```python
"""Complete remaining Phase 3 experiments, appending to existing CSV."""
import sys, os, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import numpy as np

# Import the experiment runner
from run_phase3_optimized import run_single_experiment_opt, save_result_incrementally, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS, EPOCHS, BATCH_SIZE, LR, RESULTS_CSV

# Read existing results to determine what's done
done = set()
if os.path.exists(RESULTS_CSV):
    with open(RESULTS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            done.add((row['variant'], int(row['seed'])))

# Remaining runs in priority order (P3-C first for hypothesis testing)
remaining = []
for variant in ["P3-C", "P3-B", "P3-A"]:  # Skip Untrained (all done)
    for seed in [42, 43, 44, 45, 46]:
        if (variant, seed) not in done:
            remaining.append((variant, seed))

print(f"Remaining runs: {len(remaining)}")
print(f"Runs: {remaining}")

for i, (variant, seed) in enumerate(remaining):
    print(f"\n{'='*70}")
    print(f"  [{i+1}/{len(remaining)}] {variant}, seed={seed}")
    print(f"{'='*70}")
    t0 = time.time()
    result = run_single_experiment_opt(
        variant=variant,
        seed=seed,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        lr=LR,
        update_encoder=(variant != "Untrained"),
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
    )
    save_result_incrementally(result, RESULTS_CSV)
    t1 = time.time()
    print(f"  Completed in {t1-t0:.1f}s. Test acc: {result['test_acc']:.4f}")
    print(f"  Saved to {RESULTS_CSV}")

print(f"\nAll {len(remaining)} runs completed!")
```

## Then Run It

```bash
cd C:\Users\thomas\Projekte\rdf_thalamus_sml
python src/run_remaining_phase3.py
```

## Also Run Shortcut Baselines

After the main experiments, also run shortcut baselines for all 5 seeds:

```python
from run_phase3_optimized import run_shortcut_baselines, SHORTCUT_CSV, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS, SEEDS
import csv

shortcut_rows = []
for seed in SEEDS:
    rows = run_shortcut_baselines(seed, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS)
    shortcut_rows.extend(rows)

with open(SHORTCUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)
```

## Expected Timing

- P3-C: ~95s/run × 3 remaining = ~285s
- P3-B: ~95s/run × 5 = ~475s  
- P3-A: ~190s/run × 5 = ~950s (2x due to sequential training)
- Shortcut baselines: ~30s
- Total: ~1740s ≈ 29 min

## Critical Notes

1. The script MUST append to the existing CSV, not overwrite it
2. Each run saves incrementally — if interrupted, we keep partial results
3. Working directory: C:\Users\thomas\Projekte\rdf_thalamus_sml
4. Python is on PATH
5. The `run_phase3_optimized.py` uses 30 epochs, 200 train/class, 100 test/class, batch=64, lr=1e-3

## Output Files

- `phase_3/phase3_full_results.csv` — complete with all 20 rows
- `phase_3/shortcut_baselines.csv` — shortcut baseline results
