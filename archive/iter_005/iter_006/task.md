
# Run Remaining Phase 3 Seeds (43-46) for All Variants

The Phase 3 spatiotemporal experiments have seed 42 completed. You need to run seeds 43, 44, 45, 46 for all 4 variants (P3-A, P3-B, P3-C, Untrained) — that's 16 more runs.

Each run takes about 15-35 seconds. Total should be ~5-10 minutes.

## Approach

Create a simple Python script that runs only the remaining seeds and APPENDS results to the existing CSV. Then run it.

The existing results file is at `phase_3/phase3_results.csv` with these columns:
variant,seed,train_acc,test_acc,final_spatial_jepa_loss,final_temporal_jepa_loss,training_time_sec,class_0_acc,class_1_acc,class_2_acc,class_3_acc

Here's the script to create (save as `src/run_remaining_seeds.py`):

```python
"""Run remaining Phase 3 seeds (43-46) and append to results CSV."""
import csv, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

from run_phase3 import (
    run_single_experiment, run_shortcut_baselines,
    SEEDS, OUTPUT_DIR, RESULTS_CSV, SHORTCUT_CSV
)

REMAINING_SEEDS = [43, 44, 45, 46]
VARIANTS = ["P3-A", "P3-B", "P3-C", "Untrained"]

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check which (variant, seed) combos already exist
    existing = set()
    if os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add((row["variant"], int(row["seed"])))
    
    all_results = []
    for variant in VARIANTS:
        for seed in REMAINING_SEEDS:
            if (variant, seed) in existing:
                print(f"  Skipping {variant} seed={seed} (already done)")
                continue
            print(f"\n  Running {variant} seed={seed}...")
            result = run_single_experiment(
                variant=variant,
                seed=seed,
                epochs=200,
                batch_size=32,
                lr=1e-3,
                update_encoder=(variant != "Untrained"),
            )
            all_results.append(result)
            print(f"  → test_acc={result['test_acc']:.4f}")
    
    # Append to existing CSV
    if all_results:
        fieldnames = [
            "variant", "seed", "train_acc", "test_acc",
            "final_spatial_jepa_loss", "final_temporal_jepa_loss",
            "training_time_sec",
            "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
        ]
        file_exists = os.path.exists(RESULTS_CSV)
        with open(RESULTS_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            # Only write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            writer.writerows(all_results)
        print(f"\n  Appended {len(all_results)} results to {RESULTS_CSV}")
    
    # Also run shortcut baselines for remaining seeds
    for seed in REMAINING_SEEDS:
        rows = run_shortcut_baselines(seed)
        # Append to shortcut CSV
        with open(SHORTCUT_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
            writer.writerows(rows)
    
    # Print summary of all results
    all_data = []
    with open(RESULTS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_data.append(row)
    
    print("\n" + "=" * 70)
    print("  FULL RESULTS SUMMARY")
    print("=" * 70)
    for variant in VARIANTS:
        rows = [r for r in all_data if r["variant"] == variant]
        if not rows:
            continue
        accs = [float(r["test_acc"]) for r in rows]
        print(f"  {variant:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  (n={len(rows)})")

if __name__ == "__main__":
    main()
```

Then run it:
```
cd <project_root> && python src/run_remaining_seeds.py
```

Wait for it to complete. After it's done, read the full results CSV and report all numbers.

IMPORTANT: If it's taking too long, you can reduce epochs from 200 to 100 for speed. But 200 is preferred for consistency with the seed 42 results.
