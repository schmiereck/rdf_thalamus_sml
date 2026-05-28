"""Complete remaining Phase 3 experiments, appending to existing CSV."""
import sys, os, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import numpy as np

# Import the experiment runner
from run_phase3_optimized import run_single_experiment_opt, save_result_incrementally, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS, EPOCHS, BATCH_SIZE, LR, RESULTS_CSV, SHORTCUT_CSV, SEEDS

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

# Run shortcut baselines for all 5 seeds
print(f"\n{'='*70}")
print("  Running Shortcut Baselines")
print(f"{'='*70}")
from run_phase3_optimized import run_shortcut_baselines

shortcut_rows = []
for seed in SEEDS:
    print(f"\n  Seed {seed}...")
    rows = run_shortcut_baselines(seed, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS)
    shortcut_rows.extend(rows)
    for row in rows:
        print(f"    {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

with open(SHORTCUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)

print(f"\nShortcut baseline results saved to: {SHORTCUT_CSV}")
