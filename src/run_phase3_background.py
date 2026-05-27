"""
Background runner for Phase 3 full experiment.
Runs all variants x all seeds and saves incremental progress.
"""
import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(__file__))

from run_phase3 import (
    run_single_experiment,
    run_shortcut_baselines,
    SEEDS,
    EPOCHS,
    BATCH_SIZE,
    LR,
    OUTPUT_DIR,
    RESULTS_CSV,
    SHORTCUT_CSV,
)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    variants = ["P3-A", "P3-B", "P3-C", "Untrained"]
    total_runs = len(variants) * len(SEEDS)
    run_idx = 0

    # Load existing progress
    existing_results = []
    completed_keys = set()
    if os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_results.append(row)
                completed_keys.add((row["variant"], int(row["seed"])))
        print(f"Loaded {len(existing_results)} existing results.")

    print("=" * 70)
    print("  PHASE 3 FULL EXPERIMENT RUNNER (Background)")
    print(f"  Variants: {variants}")
    print(f"  Seeds: {SEEDS}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Total runs: {total_runs}")
    print(f"  Already completed: {len(completed_keys)}")
    print("=" * 70)

    all_results = existing_results.copy()

    for variant in variants:
        for seed in SEEDS:
            key = (variant, seed)
            if key in completed_keys:
                print(f"\n  Skipping {variant} seed={seed} (already done)")
                continue

            run_idx += 1
            print(f"\n{'-' * 70}")
            print(f"  [{run_idx}/{total_runs}]  variant={variant}  seed={seed}")
            print(f"{'-' * 70}")

            t0 = time.time()
            try:
                result = run_single_experiment(
                    variant=variant,
                    seed=seed,
                    epochs=EPOCHS,
                    batch_size=BATCH_SIZE,
                    lr=LR,
                    update_encoder=(variant != "Untrained"),
                )
                all_results.append(result)

                # Save incremental progress
                fieldnames = [
                    "variant", "seed", "train_acc", "test_acc",
                    "final_spatial_jepa_loss", "final_temporal_jepa_loss",
                    "training_time_sec",
                    "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
                ]
                with open(RESULTS_CSV, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_results)

                t1 = time.time()
                print(f"  Saved progress. Elapsed: {t1-t0:.1f}s")

            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()

    # Run shortcut baselines if not already done
    if not os.path.exists(SHORTCUT_CSV) or os.path.getsize(SHORTCUT_CSV) == 0:
        print(f"\n{'-' * 70}")
        print("  Running Shortcut Baselines")
        print(f"{'-' * 70}")
        shortcut_rows = []
        for seed in SEEDS:
            print(f"\n    Seed {seed}...")
            try:
                rows = run_shortcut_baselines(seed)
                shortcut_rows.extend(rows)
                for row in rows:
                    print(f"      {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")
            except Exception as e:
                print(f"    ERROR: {e}")

        with open(SHORTCUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
            writer.writeheader()
            writer.writerows(shortcut_rows)
        print(f"\n  Shortcut baseline results saved to: {SHORTCUT_CSV}")

    # Final summary
    print("\n" + "=" * 70)
    print("  ALL RUNS COMPLETE")
    print("=" * 70)

    import numpy as np
    print("\n  Summary (mean ± std):")
    for variant in variants:
        rows = [r for r in all_results if r["variant"] == variant]
        if not rows:
            continue
        accs = [float(r["test_acc"]) for r in rows]
        s_losses = [float(r["final_spatial_jepa_loss"]) for r in rows]
        t_losses = [float(r["final_temporal_jepa_loss"]) for r in rows]
        print(
            f"    {variant:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  "
            f"spatial_loss={np.mean(s_losses):.4f}±{np.std(s_losses):.4f}  "
            f"temporal_loss={np.mean(t_losses):.4f}±{np.std(t_losses):.4f}"
        )


if __name__ == "__main__":
    main()
