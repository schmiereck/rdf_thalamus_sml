"""Run remaining Phase 3 seeds (43-46) and append to results CSV."""
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from run_phase3 import (
    run_single_experiment,
    run_shortcut_baselines,
    SEEDS,
    OUTPUT_DIR,
    RESULTS_CSV,
    SHORTCUT_CSV,
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
            "variant",
            "seed",
            "train_acc",
            "test_acc",
            "final_spatial_jepa_loss",
            "final_temporal_jepa_loss",
            "training_time_sec",
            "class_0_acc",
            "class_1_acc",
            "class_2_acc",
            "class_3_acc",
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
    shortcut_file_exists = os.path.exists(SHORTCUT_CSV)
    for seed in REMAINING_SEEDS:
        rows = run_shortcut_baselines(seed)
        # Append to shortcut CSV
        with open(SHORTCUT_CSV, "a", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"]
            )
            if not shortcut_file_exists:
                writer.writeheader()
                shortcut_file_exists = True
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
        print(
            f"  {variant:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  (n={len(rows)})"
        )


if __name__ == "__main__":
    main()
