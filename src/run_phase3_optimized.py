"""
Phase 3 Optimized Experiment Runner.

Settings: 30 epochs, 200 train/class, 100 test/class, batch=64, 5 seeds.
Saves results incrementally after each run.

Order: Untrained (fastest) → P3-C (primary hypothesis) → P3-B → P3-A (slowest).
"""

from __future__ import annotations

import csv
import os
import sys
import time
from typing import Dict, List

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from spatiotemporal_dataset import (
    generate_spatiotemporal_dataset,
    evaluate_all_shortcut_baselines,
    N_CLASSES,
    N_SPATIAL,
    N_TIMESTEPS,
)
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression

from run_phase3 import (
    create_jepa_losses,
    reshape_for_spatial_jepa,
    reshape_spatial_grads_back,
    reshape_for_temporal_jepa,
    reshape_temporal_grads_back,
    train_jepa_epoch,
    evaluate_classification,
)


# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]
VARIANTS = ["Untrained", "P3-C", "P3-B", "P3-A"]  # fastest first
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100
EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-3

OUTPUT_DIR = "phase_3"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase3_full_results.csv")
SHORTCUT_CSV = os.path.join(OUTPUT_DIR, "shortcut_baselines.csv")
CONFIG_TXT = os.path.join(OUTPUT_DIR, "experiment_config.txt")


# ---------------------------------------------------------------------------
#  Core experiment runner (parameterized dataset size)
# ---------------------------------------------------------------------------

def run_single_experiment_opt(
    variant: str,
    seed: int,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    lr: float = LR,
    update_encoder: bool = True,
    n_train_per_class: int = N_TRAIN_PER_CLASS,
    n_test_per_class: int = N_TEST_PER_CLASS,
) -> dict:
    """
    Run a single experiment with configurable dataset size.
    """
    print(f"\n    Variant: {variant}, Seed: {seed}, Epochs: {epochs}")
    rng = np.random.default_rng(seed)

    # Generate dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=n_train_per_class,
        n_test_per_class=n_test_per_class,
        noise_flip_prob=0.10,
        seed=seed,
    )
    train_grid = ds["train_grid"]
    train_y = ds["train_y"]
    test_grid = ds["test_grid"]
    test_y = ds["test_y"]
    print(f"      Dataset: train={train_grid.shape}, test={test_grid.shape}")

    # Create encoder
    if variant == "Untrained":
        enc_variant = "P3-B"
    else:
        enc_variant = variant

    encoder = SpatiotemporalEncoder(
        variant=enc_variant,
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=seed,
    )
    print(f"      Encoder: {enc_variant}, params={encoder.get_parameter_count()}")

    # Create JEPA losses
    spatial_jepas = create_jepa_losses(encoder.n_spatial_layers, D_OUT, lr=lr)
    temporal_jepas = create_jepa_losses(encoder.n_temporal_layers, D_OUT, lr=lr)

    # Set up Adam optimizers for encoder
    adam_spatial = None
    adam_temporal = None
    if update_encoder:
        adam_spatial = _Adam(
            {
                "W_enc": encoder.master_spatial.W_enc,
                "b_enc": encoder.master_spatial.b_enc,
                "W_dec": encoder.master_spatial.W_dec,
                "b_dec": encoder.master_spatial.b_dec,
            },
            lr=lr,
        )
        if encoder.variant != "P3-C":
            adam_temporal = _Adam(
                {
                    "W_enc": encoder.master_temporal.W_enc,
                    "b_enc": encoder.master_temporal.b_enc,
                    "W_dec": encoder.master_temporal.W_dec,
                    "b_dec": encoder.master_temporal.b_dec,
                },
                lr=lr,
            )
        else:
            adam_temporal = adam_spatial

    # Training
    loss_history = []
    t0 = time.time()

    if variant == "P3-A":
        # Phase 1: spatial only (alpha=1.0)
        print(f"      Phase 1: Spatial-only training (alpha=1.0) for {epochs} epochs...")
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=1.0,
                adam_spatial=adam_spatial,
                adam_temporal=None,
                adam_embedding=None,
            )
            loss_history.append(metrics)
            if epoch % max(1, epochs // 5) == 0 or epoch == epochs - 1:
                print(f"        Epoch {epoch}: spatial_loss={metrics['spatial_loss']:.4f}, "
                      f"temporal_loss={metrics['temporal_loss']:.4f}")

        # Phase 2: freeze spatial, temporal only (alpha=0.0)
        print(f"      Phase 2: Freeze spatial, temporal-only training (alpha=0.0) for {epochs} epochs...")
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=0.0,
                adam_spatial=None,
                adam_temporal=adam_temporal,
                adam_embedding=None,
            )
            loss_history.append(metrics)
            if epoch % max(1, epochs // 5) == 0 or epoch == epochs - 1:
                print(f"        Epoch {epoch}: spatial_loss={metrics['spatial_loss']:.4f}, "
                      f"temporal_loss={metrics['temporal_loss']:.4f}")

    else:
        # P3-B, P3-C, or Untrained: joint training with alpha=0.5
        alpha = 0.5
        print(f"      Joint training (alpha={alpha}) for {epochs} epochs...")
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=alpha,
                adam_spatial=adam_spatial if update_encoder else None,
                adam_temporal=adam_temporal if update_encoder else None,
                adam_embedding=None,
            )
            loss_history.append(metrics)
            if epoch % max(1, epochs // 5) == 0 or epoch == epochs - 1:
                print(f"        Epoch {epoch}: spatial_loss={metrics['spatial_loss']:.4f}, "
                      f"temporal_loss={metrics['temporal_loss']:.4f}, "
                      f"combined={metrics['combined_loss']:.4f}")

    t1 = time.time()
    print(f"      Training completed in {t1 - t0:.1f}s")

    # Final losses
    if variant == "P3-A":
        final_spatial_loss = loss_history[epochs - 1]["spatial_loss"]
        final_temporal_loss = loss_history[2 * epochs - 1]["temporal_loss"]
    else:
        final_spatial_loss = loss_history[-1]["spatial_loss"]
        final_temporal_loss = loss_history[-1]["temporal_loss"]

    print(f"      Final spatial JEPA loss: {final_spatial_loss:.6f}")
    print(f"      Final temporal JEPA loss: {final_temporal_loss:.6f}")

    # Evaluate classification
    eval_results = evaluate_classification(
        encoder, train_grid, train_y, test_grid, test_y, seed=seed
    )
    print(f"      Classification: train={eval_results['train_acc']:.4f}, "
          f"test={eval_results['test_acc']:.4f}")
    for cls in range(N_CLASSES):
        print(f"        Class {cls} accuracy: {eval_results[f'class_{cls}_acc']:.4f}")

    result = {
        "variant": variant,
        "seed": seed,
        "train_acc": eval_results["train_acc"],
        "test_acc": eval_results["test_acc"],
        "final_spatial_jepa_loss": final_spatial_loss,
        "final_temporal_jepa_loss": final_temporal_loss,
        "training_time_sec": t1 - t0,
    }
    for cls in range(N_CLASSES):
        result[f"class_{cls}_acc"] = eval_results[f"class_{cls}_acc"]

    return result


def save_result_incrementally(result: dict, csv_path: str) -> None:
    """Append a single result row to the CSV, creating header if needed."""
    fieldnames = [
        "variant", "seed", "train_acc", "test_acc",
        "final_spatial_jepa_loss", "final_temporal_jepa_loss",
        "training_time_sec",
        "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
    ]
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)


def run_shortcut_baselines(seed: int, n_train_per_class: int, n_test_per_class: int) -> list[dict]:
    """Run shortcut baselines for a single seed and return rows."""
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=n_train_per_class,
        n_test_per_class=n_test_per_class,
        noise_flip_prob=0.10,
        seed=seed,
    )
    results = evaluate_all_shortcut_baselines(
        ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"],
        frames_to_test=[0, 8, 16, 24, 31],
    )

    rows = []
    for name, res in results.items():
        rows.append({
            "seed": seed,
            "baseline_name": name,
            "train_acc": res["train_acc"],
            "test_acc": res["test_acc"],
        })
    return rows


def write_config() -> None:
    """Write experiment configuration to text file."""
    config = f"""Phase 3 Optimized Experiment Configuration
============================================
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

Dataset:
  n_train_per_class: {N_TRAIN_PER_CLASS}
  n_test_per_class:  {N_TEST_PER_CLASS}
  noise_flip_prob:   0.10
  total_train:       {N_CLASSES * N_TRAIN_PER_CLASS}
  total_test:        {N_CLASSES * N_TEST_PER_CLASS}

Model:
  d:                 {D}
  d_out:             {D_OUT}
  n_spatial_layers:  3
  n_temporal_layers: 3

Training:
  epochs:            {EPOCHS}
  batch_size:        {BATCH_SIZE}
  lr:                {LR}
  seeds:             {SEEDS}
  variants:          {VARIANTS}

Pre-registration Compliance:
  - 5 seeds used for statistical validity (paired t-test, Cohen's d)
  - F1: P3-C vs Untrained (gain >= 8pp, p < 0.05, d >= 1.0)
  - F2: P3-B vs P3-C (penalty <= 10pp)
  - F3: P3-C vs P3-A (within 20pp of sequential baseline)
  - F4: P3-C loss <= 2x P3-B loss

Output Files:
  - {RESULTS_CSV}
  - {SHORTCUT_CSV}
  - {CONFIG_TXT}
"""
    with open(CONFIG_TXT, "w") as f:
        f.write(config)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Remove old results file to start fresh
    if os.path.exists(RESULTS_CSV):
        os.remove(RESULTS_CSV)

    print("=" * 70)
    print("  PHASE 3 OPTIMIZED EXPERIMENT RUNNER")
    print(f"  Settings: {EPOCHS} epochs, {N_TRAIN_PER_CLASS} train/class, {N_TEST_PER_CLASS} test/class, batch={BATCH_SIZE}")
    print(f"  Seeds: {SEEDS}")
    print(f"  Variants (order): {VARIANTS}")
    print("=" * 70)

    total_runs = len(VARIANTS) * len(SEEDS)
    run_idx = 0
    overall_t0 = time.time()

    all_results: list[dict] = []

    for variant in VARIANTS:
        print(f"\n{'-' * 70}")
        print(f"  Variant: {variant}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}")

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
            all_results.append(result)
            save_result_incrementally(result, RESULTS_CSV)
            print(f"  -> Saved to {RESULTS_CSV}")

    overall_t1 = time.time()

    # Run shortcut baselines (once per seed)
    print(f"\n{'-' * 70}")
    print("  Running Shortcut Baselines")
    print(f"{'-' * 70}")
    shortcut_rows: list[dict] = []
    for seed in SEEDS:
        print(f"\n    Seed {seed}...")
        rows = run_shortcut_baselines(seed, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS)
        shortcut_rows.extend(rows)
        for row in rows:
            print(f"      {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

    with open(SHORTCUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
        writer.writeheader()
        writer.writerows(shortcut_rows)

    print(f"\n  Shortcut baseline results saved to: {SHORTCUT_CSV}")

    # Write config
    write_config()
    print(f"  Experiment config saved to: {CONFIG_TXT}")

    # Summary
    print("\n" + "=" * 70)
    print("  ALL RUNS COMPLETE")
    print(f"  Total elapsed time: {overall_t1 - overall_t0:.1f}s ({(overall_t1 - overall_t0)/60:.1f} min)")
    print("=" * 70)

    print("\n  Summary (mean ± std) per variant:")
    for variant in VARIANTS:
        rows = [r for r in all_results if r["variant"] == variant]
        if not rows:
            continue
        accs = [r["test_acc"] for r in rows]
        s_losses = [r["final_spatial_jepa_loss"] for r in rows]
        t_losses = [r["final_temporal_jepa_loss"] for r in rows]
        times = [r["training_time_sec"] for r in rows]
        print(
            f"    {variant:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  "
            f"spatial_loss={np.mean(s_losses):.4f}±{np.std(s_losses):.4f}  "
            f"temporal_loss={np.mean(t_losses):.4f}±{np.std(t_losses):.4f}  "
            f"time={np.mean(times):.1f}s"
        )

    # Pre-registration falsification check
    print("\n  --- Pre-registration Falsification Checks ---")
    p3c_rows = [r for r in all_results if r["variant"] == "P3-C"]
    p3b_rows = [r for r in all_results if r["variant"] == "P3-B"]
    p3a_rows = [r for r in all_results if r["variant"] == "P3-A"]
    untrained_rows = [r for r in all_results if r["variant"] == "Untrained"]

    if len(p3c_rows) == 5 and len(untrained_rows) == 5:
        # F1: P3-C vs Untrained
        p3c_acc = np.array([r["test_acc"] for r in p3c_rows])
        unt_acc = np.array([r["test_acc"] for r in untrained_rows])
        gain = p3c_acc.mean() - unt_acc.mean()
        diff = p3c_acc - unt_acc
        from scipy import stats
        t_stat, p_val = stats.ttest_rel(p3c_acc, unt_acc)
        cohens_d = diff.mean() / (diff.std(ddof=1) + 1e-12)
        f1_pass = (gain >= 0.08) and (p_val < 0.05) and (cohens_d >= 1.0)
        print(f"    F1 (P3-C vs Untrained): gain={gain:.4f}, p={p_val:.4f}, d={cohens_d:.4f} -> {'PASS' if f1_pass else 'FAIL'}")

    if len(p3b_rows) == 5 and len(p3c_rows) == 5:
        # F2: P3-B vs P3-C
        p3b_acc = np.array([r["test_acc"] for r in p3b_rows])
        p3c_acc = np.array([r["test_acc"] for r in p3c_rows])
        penalty = p3b_acc.mean() - p3c_acc.mean()
        f2_pass = penalty <= 0.10
        print(f"    F2 (P3-B vs P3-C): penalty={penalty:.4f} -> {'PASS' if f2_pass else 'FAIL'}")

    if len(p3a_rows) == 5 and len(p3c_rows) == 5:
        # F3: P3-C vs P3-A
        p3a_acc = np.array([r["test_acc"] for r in p3a_rows])
        p3c_acc = np.array([r["test_acc"] for r in p3c_rows])
        gap = p3a_acc.mean() - p3c_acc.mean()
        f3_pass = gap <= 0.20
        print(f"    F3 (P3-C vs P3-A): gap={gap:.4f} -> {'PASS' if f3_pass else 'FAIL'}")

    if len(p3b_rows) == 5 and len(p3c_rows) == 5:
        # F4: P3-C loss vs P3-B loss
        p3c_sloss = np.array([r["final_spatial_jepa_loss"] for r in p3c_rows])
        p3c_tloss = np.array([r["final_temporal_jepa_loss"] for r in p3c_rows])
        p3b_sloss = np.array([r["final_spatial_jepa_loss"] for r in p3b_rows])
        p3b_tloss = np.array([r["final_temporal_jepa_loss"] for r in p3b_rows])
        f4_pass = (p3c_sloss.mean() <= 2 * p3b_sloss.mean()) and (p3c_tloss.mean() <= 2 * p3b_tloss.mean())
        print(f"    F4 (Loss ratio): P3-C spatial={p3c_sloss.mean():.4f} vs P3-B={p3b_sloss.mean():.4f}, "
              f"temporal={p3c_tloss.mean():.4f} vs P3-B={p3b_tloss.mean():.4f} -> {'PASS' if f4_pass else 'FAIL'}")

    print("=" * 70)
    return all_results


if __name__ == "__main__":
    main()
