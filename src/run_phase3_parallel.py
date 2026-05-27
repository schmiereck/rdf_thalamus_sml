"""
Phase 3 Parallel Experiment Runner for HSUN.

Runs all four spatiotemporal variants (P3-A, P3-B, P3-C, Untrained)
across 5 seeds [42, 43, 44, 45, 46] for 200 epochs in parallel
using multiprocessing.Pool.

Results are saved to individual CSV files per variant, plus shortcut
baselines and a parameter comparison summary.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from multiprocessing import Pool
from typing import Dict, List

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from spatiotemporal_dataset import (
    generate_spatiotemporal_dataset,
    evaluate_all_shortcut_baselines,
    N_CLASSES,
)
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression


# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]
D = 16
D_OUT = 16
BATCH_SIZE = 32
EPOCHS = 200
LR = 1e-3

OUTPUT_DIR = "phase_3"

# CSV output paths
P3A_CSV = os.path.join(OUTPUT_DIR, "p3a_results.csv")
P3B_CSV = os.path.join(OUTPUT_DIR, "p3b_results.csv")
P3C_CSV = os.path.join(OUTPUT_DIR, "p3c_results.csv")
UNTRAINED_CSV = os.path.join(OUTPUT_DIR, "untrained_results.csv")
SHORTCUT_CSV = os.path.join(OUTPUT_DIR, "shortcut_results.csv")
PARAM_CSV = os.path.join(OUTPUT_DIR, "param_comparison.csv")


# ---------------------------------------------------------------------------
#  Helpers (replicated here for picklability in multiprocessing)
# ---------------------------------------------------------------------------

def create_jepa_losses(n_layers: int, d: int, lr: float = LR) -> list[JEPALoss]:
    """Create a JEPALoss object per layer."""
    return [JEPALoss(n_layers=1, d=d, lr=lr) for _ in range(n_layers)]


def reshape_for_spatial_jepa(x: np.ndarray) -> np.ndarray:
    """Reshape spatial layer output (B, S, T, d) -> (B*T, S, d) for JEPA."""
    B, S, T, d = x.shape
    return x.transpose(0, 2, 1, 3).reshape(B * T, S, d)


def reshape_spatial_grads_back(grad: np.ndarray, B: int, S: int, T: int, d: int) -> np.ndarray:
    """Reshape JEPA code gradients (B*T, S, d) back to (B, S, T, d)."""
    return grad.reshape(B, T, S, d).transpose(0, 2, 1, 3)


def reshape_for_temporal_jepa(x: np.ndarray) -> np.ndarray:
    """Reshape temporal layer output (B, T, S, d) -> (B*S, T, d) for JEPA."""
    B, T, S, d = x.shape
    return x.transpose(0, 2, 1, 3).reshape(B * S, T, d)


def reshape_temporal_grads_back(grad: np.ndarray, B: int, T: int, S: int, d: int) -> np.ndarray:
    """Reshape JEPA code gradients (B*S, T, d) back to (B, T, S, d)."""
    return grad.reshape(B, S, T, d).transpose(0, 2, 1, 3)


def train_jepa_epoch(
    encoder: SpatiotemporalEncoder,
    spatial_jepas: list[JEPALoss],
    temporal_jepas: list[JEPALoss],
    train_grid: np.ndarray,
    batch_size: int,
    rng: np.random.Generator,
    alpha: float,
    adam_spatial: _Adam | None,
    adam_temporal: _Adam | None,
) -> dict:
    """Train one epoch of JEPA on spatiotemporal data."""
    n_samples = train_grid.shape[0]
    perm = rng.permutation(n_samples)

    total_spatial_loss = 0.0
    total_temporal_loss = 0.0
    total_combined_loss = 0.0
    n_batches = 0

    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch = train_grid[perm[start:end]]

        # Forward pass
        fwd = encoder.forward_with_intermediates(batch)

        # --- Spatial JEPA ---
        spatial_losses = []
        spatial_code_grads = []
        for l in range(encoder.n_spatial_layers):
            out = fwd["spatial_outputs"][l]
            B, S_l, T, d = out.shape
            jepa_in = reshape_for_spatial_jepa(out)
            result = spatial_jepas[l].step([jepa_in])
            spatial_losses.append(result["loss"])
            cg = result["code_grads"][0]
            cg_back = reshape_spatial_grads_back(cg, B, S_l, T, d)
            spatial_code_grads.append(cg_back)

        # --- Temporal JEPA ---
        temporal_losses = []
        temporal_code_grads = []
        for l in range(encoder.n_temporal_layers):
            out = fwd["temporal_outputs"][l]
            B, T_l, S_f, d = out.shape
            jepa_in = reshape_for_temporal_jepa(out)
            result = temporal_jepas[l].step([jepa_in])
            temporal_losses.append(result["loss"])
            cg = result["code_grads"][0]
            cg_back = reshape_temporal_grads_back(cg, B, T_l, S_f, d)
            temporal_code_grads.append(cg_back)

        # --- Backprop through encoder ---
        if adam_spatial is not None or adam_temporal is not None:
            grads = encoder.backward(
                fwd,
                dL_dspatial_codes=spatial_code_grads,
                dL_dtemporal_codes=temporal_code_grads,
                alpha=alpha,
            )

            if adam_spatial is not None:
                adam_spatial.step(
                    {
                        "W_enc": encoder.master_spatial.W_enc,
                        "b_enc": encoder.master_spatial.b_enc,
                        "W_dec": encoder.master_spatial.W_dec,
                        "b_dec": encoder.master_spatial.b_dec,
                    },
                    grads["dL_dspatial"],
                )

            if adam_temporal is not None and encoder.variant != "P3-C":
                adam_temporal.step(
                    {
                        "W_enc": encoder.master_temporal.W_enc,
                        "b_enc": encoder.master_temporal.b_enc,
                        "W_dec": encoder.master_temporal.W_dec,
                        "b_dec": encoder.master_temporal.b_dec,
                    },
                    grads["dL_dtemporal"],
                )
            elif adam_temporal is not None and encoder.variant == "P3-C":
                combined = {
                    k: grads["dL_dspatial"][k] + grads["dL_dtemporal"][k]
                    for k in grads["dL_dspatial"]
                }
                adam_temporal.step(
                    {
                        "W_enc": encoder.master_spatial.W_enc,
                        "b_enc": encoder.master_spatial.b_enc,
                        "W_dec": encoder.master_spatial.W_dec,
                        "b_dec": encoder.master_spatial.b_dec,
                    },
                    combined,
                )

        avg_spatial = float(np.mean(spatial_losses)) if spatial_losses else 0.0
        avg_temporal = float(np.mean(temporal_losses)) if temporal_losses else 0.0
        combined = alpha * avg_spatial + (1.0 - alpha) * avg_temporal

        total_spatial_loss += avg_spatial
        total_temporal_loss += avg_temporal
        total_combined_loss += combined
        n_batches += 1

    return {
        "spatial_loss": total_spatial_loss / n_batches,
        "temporal_loss": total_temporal_loss / n_batches,
        "combined_loss": total_combined_loss / n_batches,
    }


def evaluate_classification(
    encoder: SpatiotemporalEncoder,
    train_grid: np.ndarray,
    train_y: np.ndarray,
    test_grid: np.ndarray,
    test_y: np.ndarray,
    seed: int = 42,
) -> dict:
    """Fit linear probe on pooled representations and compute accuracies."""
    fwd_train = encoder.forward_with_intermediates(train_grid)
    fwd_test = encoder.forward_with_intermediates(test_grid)

    train_pooled = fwd_train["pooled"]
    test_pooled = fwd_test["pooled"]

    probe = SimpleLogisticRegression(
        n_classes=N_CLASSES,
        n_features=encoder.d_out,
        lr=0.1,
        max_iter=2000,
        seed=seed,
    )
    probe.fit(train_pooled, train_y)

    train_acc = float(probe.score(train_pooled, train_y))
    test_acc = float(probe.score(test_pooled, test_y))

    per_class = {}
    for cls in range(N_CLASSES):
        mask = test_y == cls
        if mask.sum() > 0:
            cls_acc = float(probe.score(test_pooled[mask], test_y[mask]))
        else:
            cls_acc = 0.0
        per_class[f"class_{cls}_acc"] = cls_acc

    return {
        "train_acc": train_acc,
        "test_acc": test_acc,
        **per_class,
    }


def run_single_experiment(args: tuple) -> dict:
    """
    Worker function for a single (variant, seed) experiment.

    Parameters
    ----------
    args : tuple (variant, seed, epochs, batch_size, lr, update_encoder)

    Returns
    -------
    dict with all metrics.
    """
    variant, seed, epochs, batch_size, lr, update_encoder = args

    print(f"[START] Variant: {variant}, Seed: {seed}, Epochs: {epochs}")
    rng = np.random.default_rng(seed)

    # Generate dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=500,
        n_test_per_class=200,
        noise_flip_prob=0.10,
        seed=seed,
    )
    train_grid = ds["train_grid"]
    train_y = ds["train_y"]
    test_grid = ds["test_grid"]
    test_y = ds["test_y"]

    # Create encoder
    enc_variant = "P3-B" if variant == "Untrained" else variant
    encoder = SpatiotemporalEncoder(
        variant=enc_variant,
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=seed,
    )
    param_count = encoder.get_parameter_count()

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
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=1.0,
                adam_spatial=adam_spatial,
                adam_temporal=None,
            )
            loss_history.append(metrics)

        # Phase 2: freeze spatial, temporal only (alpha=0.0)
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=0.0,
                adam_spatial=None,
                adam_temporal=adam_temporal,
            )
            loss_history.append(metrics)
    else:
        # P3-B, P3-C, or Untrained: joint training with alpha=0.5
        alpha = 0.5
        for epoch in range(epochs):
            metrics = train_jepa_epoch(
                encoder, spatial_jepas, temporal_jepas,
                train_grid, batch_size, rng,
                alpha=alpha,
                adam_spatial=adam_spatial if update_encoder else None,
                adam_temporal=adam_temporal if update_encoder else None,
            )
            loss_history.append(metrics)

    t1 = time.time()
    training_time = t1 - t0

    # Final losses
    if variant == "P3-A":
        final_spatial_loss = loss_history[epochs - 1]["spatial_loss"]
        final_temporal_loss = loss_history[2 * epochs - 1]["temporal_loss"]
    else:
        final_spatial_loss = loss_history[-1]["spatial_loss"]
        final_temporal_loss = loss_history[-1]["temporal_loss"]

    # Evaluate classification
    eval_results = evaluate_classification(
        encoder, train_grid, train_y, test_grid, test_y, seed=seed
    )

    print(f"[DONE]  Variant: {variant}, Seed: {seed} -> test_acc={eval_results['test_acc']:.4f} ({training_time:.1f}s)")

    return {
        "variant": variant,
        "seed": seed,
        "train_acc": eval_results["train_acc"],
        "test_acc": eval_results["test_acc"],
        "final_spatial_jepa_loss": final_spatial_loss,
        "final_temporal_jepa_loss": final_temporal_loss,
        "training_time_sec": training_time,
        "param_count": param_count,
        "class_0_acc": eval_results["class_0_acc"],
        "class_1_acc": eval_results["class_1_acc"],
        "class_2_acc": eval_results["class_2_acc"],
        "class_3_acc": eval_results["class_3_acc"],
    }


def run_shortcut_baselines(seed: int) -> list[dict]:
    """Run shortcut baselines for a single seed and return rows."""
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=500,
        n_test_per_class=200,
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
#  Main parallel runner
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("  PHASE 3 PARALLEL EXPERIMENT RUNNER")
    print(f"  Variants: P3-A, P3-B, P3-C, Untrained")
    print(f"  Seeds: {SEEDS}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Workers: 5 (one per seed, all variants parallelised)")
    print("=" * 70)

    # Build the full task list: 4 variants × 5 seeds = 20 tasks
    variants = ["P3-A", "P3-B", "P3-C", "Untrained"]
    tasks = []
    for variant in variants:
        for seed in SEEDS:
            update_encoder = (variant != "Untrained")
            tasks.append((variant, seed, EPOCHS, BATCH_SIZE, LR, update_encoder))

    total_tasks = len(tasks)
    print(f"\n  Total experiments to run: {total_tasks}")
    print(f"  Starting parallel execution...\n")

    t_start = time.time()

    # Run all experiments in parallel with 5 workers
    with Pool(processes=5) as pool:
        all_results = pool.map(run_single_experiment, tasks)

    t_end = time.time()
    print(f"\n  All experiments completed in {t_end - t_start:.1f}s")

    # ------------------------------------------------------------------
    #  Save per-variant CSVs
    # ------------------------------------------------------------------
    fieldnames = [
        "variant", "seed", "train_acc", "test_acc",
        "final_spatial_jepa_loss", "final_temporal_jepa_loss",
        "training_time_sec", "param_count",
        "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
    ]

    variant_csv_map = {
        "P3-A": P3A_CSV,
        "P3-B": P3B_CSV,
        "P3-C": P3C_CSV,
        "Untrained": UNTRAINED_CSV,
    }

    for variant in variants:
        rows = [r for r in all_results if r["variant"] == variant]
        csv_path = variant_csv_map[variant]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Saved {variant} results -> {csv_path}")

    # ------------------------------------------------------------------
    #  Run shortcut baselines (sequential, fast)
    # ------------------------------------------------------------------
    print(f"\n{'-' * 70}")
    print("  Running Shortcut Baselines")
    print(f"{'-' * 70}")
    shortcut_rows: list[dict] = []
    for seed in SEEDS:
        print(f"    Seed {seed}...")
        rows = run_shortcut_baselines(seed)
        shortcut_rows.extend(rows)
        for row in rows:
            print(f"      {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

    with open(SHORTCUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
        writer.writeheader()
        writer.writerows(shortcut_rows)
    print(f"\n  Shortcut baseline results saved to: {SHORTCUT_CSV}")

    # ------------------------------------------------------------------
    #  Parameter comparison CSV
    # ------------------------------------------------------------------
    param_rows = []
    for variant in variants:
        rows = [r for r in all_results if r["variant"] == variant]
        if rows:
            param_rows.append({
                "variant": variant,
                "param_count": rows[0]["param_count"],
                "n_seeds": len(rows),
                "mean_test_acc": float(np.mean([r["test_acc"] for r in rows])),
                "std_test_acc": float(np.std([r["test_acc"] for r in rows])),
                "mean_train_acc": float(np.mean([r["train_acc"] for r in rows])),
                "std_train_acc": float(np.std([r["train_acc"] for r in rows])),
            })

    with open(PARAM_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variant", "param_count", "n_seeds",
            "mean_test_acc", "std_test_acc",
            "mean_train_acc", "std_train_acc",
        ])
        writer.writeheader()
        writer.writerows(param_rows)
    print(f"  Parameter comparison saved to: {PARAM_CSV}")

    # ------------------------------------------------------------------
    #  Final summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY — Mean ± Std of Test Accuracy")
    print("=" * 70)
    for variant in variants:
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

    print("\n" + "=" * 70)
    print("  ALL RUNS COMPLETE")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    main()
