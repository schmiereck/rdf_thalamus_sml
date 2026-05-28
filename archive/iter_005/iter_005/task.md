# Phase 3: Run Final 2 P3-A Experiments + Cleanup + Shortcut Baselines

Working directory: `C:\Users\thomas\Projekte\rdf_thalamus_sml`

## Step 1: Clean Up CSV

The file `phase_3/phase3_full_results.csv` has duplicate rows for P3-A seed 44. Write a quick script to deduplicate (keep first occurrence of each variant+seed pair) and write back:

```python
import csv
INPUT = "phase_3/phase3_full_results.csv"
rows = []
seen = set()
with open(INPUT) as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['variant'], row['seed'])
        if key not in seen:
            seen.add(key)
            rows.append(row)

with open(INPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"Cleaned: {len(rows)} unique rows")
```

## Step 2: Run P3-A Seeds 45 and 46

Create and run a Python script that runs exactly 2 P3-A experiments:

```python
import sys, os, time, csv
sys.path.insert(0, 'src')
from run_phase3_optimized import run_single_experiment_opt, save_result_incrementally, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS, EPOCHS, BATCH_SIZE, LR

RESULTS_CSV = "phase_3/phase3_full_results.csv"

for seed in [45, 46]:
    print(f"\n=== P3-A seed={seed} ===")
    t0 = time.time()
    result = run_single_experiment_opt(
        variant="P3-A",
        seed=seed,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        lr=LR,
        update_encoder=True,
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
    )
    save_result_incrementally(result, RESULTS_CSV)
    t1 = time.time()
    print(f"  Done in {t1-t0:.1f}s. Test acc: {result['test_acc']:.4f}")

print("\nAll P3-A runs complete!")
```

IMPORTANT: P3-A is sequential training (spatial first 30 epochs, then temporal 30 epochs). Each run takes ~5-8 minutes. Total for 2 runs: ~10-16 minutes.

## Step 3: Run Shortcut Baselines

After P3-A is done, run shortcut baselines:

```python
import sys, os, csv
sys.path.insert(0, 'src')
from spatiotemporal_dataset import generate_spatiotemporal_dataset, evaluate_all_shortcut_baselines

SEEDS = [42, 43, 44, 45, 46]
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100

shortcut_rows = []
for seed in SEEDS:
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=seed,
    )
    results = evaluate_all_shortcut_baselines(
        ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"],
        frames_to_test=[0, 8, 16, 24, 31],
    )
    for name, res in results.items():
        shortcut_rows.append({
            "seed": seed,
            "baseline_name": name,
            "train_acc": res["train_acc"],
            "test_acc": res["test_acc"],
        })

with open("phase_3/shortcut_baselines.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)
print(f"Shortcut baselines saved: {len(shortcut_rows)} rows")
```

## Step 4: Final Verification

After all runs, verify the CSV has exactly 20 rows (4 variants × 5 seeds), no duplicates, and print the mean ± std test accuracy for each variant.

## Expected Timing
- Cleanup: ~1s
- P3-A seeds 45, 46: ~10-16 min
- Shortcut baselines: ~30s
- Total: ~11-17 min
