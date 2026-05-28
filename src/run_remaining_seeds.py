"""Run remaining seeds for Phase 3 experiments."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from run_phase3 import run_single_experiment, run_shortcut_baselines, SEEDS, RESULTS_CSV, SHORTCUT_CSV
import csv

# Seeds already completed: 42
completed_seeds = [42]
remaining_seeds = [s for s in SEEDS if s not in completed_seeds]

print("=" * 70)
print("  RUNNING REMAINING SEEDS:", remaining_seeds)
print("=" * 70)

all_results = []
for seed in remaining_seeds:
    for variant in ["P3-A", "P3-B", "P3-C", "Untrained"]:
        print(f"\n--- Running {variant}, seed={seed} ---")
        result = run_single_experiment(
            variant=variant,
            seed=seed,
            epochs=200,
            batch_size=32,
            lr=1e-3,
            update_encoder=(variant != "Untrained"),
        )
        all_results.append(result)

# Append to existing CSV
fieldnames = [
    "variant", "seed", "train_acc", "test_acc",
    "final_spatial_jepa_loss", "final_temporal_jepa_loss",
    "training_time_sec",
    "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
]

with open(RESULTS_CSV, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writerows(all_results)

print(f"\n  Results appended to: {RESULTS_CSV}")

# Run shortcut baselines
print(f"\n{'-' * 70}")
print("  Running Shortcut Baselines")
print(f"{'-' * 70}")
shortcut_rows = []
for seed in remaining_seeds:
    print(f"\n    Seed {seed}...")
    rows = run_shortcut_baselines(seed)
    shortcut_rows.extend(rows)
    for row in rows:
        print(f"      {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

with open(SHORTCUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)

print(f"\n  Shortcut baseline results saved to: {SHORTCUT_CSV}")
