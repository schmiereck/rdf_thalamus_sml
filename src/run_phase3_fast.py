"""
Phase 3 Fast Experiment Runner — reduced samples/epochs for speed.

Strategy:
  - n_train_per_class=200 (down from 500)
  - epochs=50 (down from 200)
  - batch_size=64 (up from 32)
  - seeds=[42, 43, 44, 45]
  - variants=["P3-A", "P3-B", "P3-C", "Untrained"]

This should reduce per-run time from ~58 min to ~5-7 min.
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

# Import helpers from run_phase3.py
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

SEEDS = [42, 43, 44, 45]
VARIANTS = ["P3-A", "P3-B", "P3-C", "Untrained"]
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 200
EPOCHS = 50
BATCH_SIZE = 64
LR = 1e-3

OUTPUT_DIR = "phase_3"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase3_fast_results.csv")
SHORTCUT_CSV = os.path.join(OUTPUT_DIR, "shortcut_baselines_fast.csv")


# ---------------------------------------------------------------------------
#  Fast experiment runner (adapted from run_phase3.py)
# ---------------------------------------------------------------------------

def run_single_experiment_fast(
    variant: str,
    seed: int,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    lr: float = LR,
    update_encoder: bool = True,
) -> dict:
    """
    Run a single fast experiment with reduced dataset size and epochs.
    """
    print(f"\n    Variant: {variant}, Seed: {seed}, Epochs: {epochs}")
    rng = np.random.default_rng(seed)

    # Generate reduced dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=seed,
    )
    train_grid = ds["train_grid"]  # (n_train, 16, 32)
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
            if epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1:
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
            if epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1:
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
            if epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1:
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


def run_shortcut_baselines_fast(seed: int) -> list[dict]:
    """Run shortcut baselines for a single seed with reduced dataset."""
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

    rows = []
    for name, res in results.items():
        rows.append({
            "seed": seed,
            "baseline_name": name,
            "train_acc": res["train_acc"],
            "test_acc": res["test_acc"],
        })
    return rows


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("  PHASE 3 FAST EXPERIMENT RUNNER")
    print(f"  Variants: {', '.join(VARIANTS)}")
    print(f"  Seeds: {SEEDS}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Train per class: {N_TRAIN_PER_CLASS}")
    print(f"  Test per class: {N_TEST_PER_CLASS}")
    print("=" * 70)

    all_results: list[dict] = []
    total_runs = len(VARIANTS) * len(SEEDS)
    run_idx = 0

    for variant in VARIANTS:
        print(f"\n{'-' * 70}")
        print(f"  Variant: {variant}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}")

            result = run_single_experiment_fast(
                variant=variant,
                seed=seed,
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                lr=LR,
                update_encoder=(variant != "Untrained"),
            )
            all_results.append(result)

    # Save main results
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

    print(f"\n  Main results saved to: {RESULTS_CSV}")

    # Run shortcut baselines
    print(f"\n{'-' * 70}")
    print("  Running Shortcut Baselines")
    print(f"{'-' * 70}")
    shortcut_rows: list[dict] = []
    for seed in SEEDS:
        print(f"\n    Seed {seed}...")
        rows = run_shortcut_baselines_fast(seed)
        shortcut_rows.extend(rows)
        for row in rows:
            print(f"      {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

    with open(SHORTCUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
        writer.writeheader()
        writer.writerows(shortcut_rows)

    print(f"\n  Shortcut baseline results saved to: {SHORTCUT_CSV}")

    # Summary
    print("\n" + "=" * 70)
    print("  ALL RUNS COMPLETE")
    print("=" * 70)

    print("\n  Summary (mean ± std test accuracy):")
    for variant in VARIANTS:
        rows = [r for r in all_results if r["variant"] == variant]
        if not rows:
            continue
        accs = [r["test_acc"] for r in rows]
        s_losses = [r["final_spatial_jepa_loss"] for r in rows]
        t_losses = [r["final_temporal_jepa_loss"] for r in rows]
        print(
            f"    {variant:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  "
            f"spatial_loss={np.mean(s_losses):.4f}±{np.std(s_losses):.4f}  "
            f"temporal_loss={np.mean(t_losses):.4f}±{np.std(t_losses):.4f}"
        )

    # Gaps
    p3c_accs = [r["test_acc"] for r in all_results if r["variant"] == "P3-C"]
    untrained_accs = [r["test_acc"] for r in all_results if r["variant"] == "Untrained"]
    p3b_accs = [r["test_acc"] for r in all_results if r["variant"] == "P3-B"]
    p3a_accs = [r["test_acc"] for r in all_results if r["variant"] == "P3-A"]

    if p3c_accs and untrained_accs:
        gap_c_untrained = np.mean(p3c_accs) - np.mean(untrained_accs)
        print(f"\n    P3-C vs Untrained gap: {gap_c_untrained:.4f}")
    if p3b_accs and p3c_accs:
        gap_b_c = np.mean(p3b_accs) - np.mean(p3c_accs)
        print(f"    P3-B vs P3-C gap: {gap_b_c:.4f}")
    if p3c_accs and p3a_accs:
        gap_c_a = np.mean(p3c_accs) - np.mean(p3a_accs)
        print(f"    P3-C vs P3-A gap: {gap_c_a:.4f}")

    # Per-class accuracy per variant
    print("\n  Per-class accuracy (mean across seeds):")
    for variant in VARIANTS:
        rows = [r for r in all_results if r["variant"] == variant]
        if not rows:
            continue
        print(f"    {variant}:")
        for cls in range(N_CLASSES):
            cls_accs = [r[f"class_{cls}_acc"] for r in rows]
            print(f"      Class {cls}: {np.mean(cls_accs):.4f}±{np.std(cls_accs):.4f}")

    return all_results


if __name__ == "__main__":
    main()
