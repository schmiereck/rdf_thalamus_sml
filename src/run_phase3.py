"""
Phase 3 Experiment Runner for HSUN.

Runs all three spatiotemporal variants (P3-A, P3-B, P3-C) plus untrained
baseline and shortcut baselines across 5 seeds.

Training protocol:
  - P3-A: alpha=1.0 (spatial only) for 200 epochs,
          then freeze spatial master node, alpha=0.0 (temporal only) for 200 epochs.
  - P3-B/C: alpha=0.5 jointly for 200 epochs.
  - Untrained: random init, freeze encoder, train only JEPA predictors.

Evaluation:
  - Linear probe (SimpleLogisticRegression, max_iter=2000) on pooled representations.
  - Test accuracy + per-class (per-benchmark) accuracies.
  - Shortcut baselines: single-frame and temporal-average.

Results saved to phase_3/ directory.
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
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase3_results.csv")
SHORTCUT_CSV = os.path.join(OUTPUT_DIR, "shortcut_baselines.csv")


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def create_jepa_losses(n_layers: int, d: int, lr: float = LR) -> list[JEPALoss]:
    """Create a JEPALoss object per layer."""
    return [JEPALoss(n_layers=1, d=d, lr=lr) for _ in range(n_layers)]


def reshape_for_spatial_jepa(x: np.ndarray) -> np.ndarray:
    """
    Reshape spatial layer output (B, S, T, d) -> (B*T, S, d) for JEPA.
    JEPA expects (batch, positions, d).
    """
    B, S, T, d = x.shape
    return x.transpose(0, 2, 1, 3).reshape(B * T, S, d)


def reshape_spatial_grads_back(grad: np.ndarray, B: int, S: int, T: int, d: int) -> np.ndarray:
    """Reshape JEPA code gradients (B*T, S, d) back to (B, S, T, d)."""
    return grad.reshape(B, T, S, d).transpose(0, 2, 1, 3)


def reshape_for_temporal_jepa(x: np.ndarray) -> np.ndarray:
    """
    Reshape temporal layer output (B, T, S, d) -> (B*S, T, d) for JEPA.
    """
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
    adam_embedding: _Adam | None,
) -> dict:
    """
    Train one epoch of JEPA on spatiotemporal data.

    Returns dict with spatial_loss, temporal_loss, total_loss.
    """
    n_samples = train_grid.shape[0]
    perm = rng.permutation(n_samples)

    total_spatial_loss = 0.0
    total_temporal_loss = 0.0
    total_combined_loss = 0.0
    n_batches = 0

    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch = train_grid[perm[start:end]]  # (B, S, T)

        # Forward pass
        fwd = encoder.forward_with_intermediates(batch)

        # --- Spatial JEPA ---
        spatial_losses = []
        spatial_code_grads = []
        for l in range(encoder.n_spatial_layers):
            out = fwd["spatial_outputs"][l]  # (B, S_l, T, d)
            B, S_l, T, d = out.shape
            jepa_in = reshape_for_spatial_jepa(out)  # (B*T, S_l, d)
            result = spatial_jepas[l].step([jepa_in])
            spatial_losses.append(result["loss"])
            # Gradient back to encoder
            cg = result["code_grads"][0]  # (B*T, S_l, d)
            cg_back = reshape_spatial_grads_back(cg, B, S_l, T, d)
            spatial_code_grads.append(cg_back)

        # --- Temporal JEPA ---
        temporal_losses = []
        temporal_code_grads = []
        for l in range(encoder.n_temporal_layers):
            out = fwd["temporal_outputs"][l]  # (B, T_l, S_final, d)
            B, T_l, S_f, d = out.shape
            jepa_in = reshape_for_temporal_jepa(out)  # (B*S_f, T_l, d)
            result = temporal_jepas[l].step([jepa_in])
            temporal_losses.append(result["loss"])
            cg = result["code_grads"][0]  # (B*S_f, T_l, d)
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

            if encoder.variant == "P3-C":
                # P3-C: spatial and temporal share the same master node.
                # Use a SINGLE Adam step with combined gradients.
                combined = {
                    k: grads["dL_dspatial"][k] + grads["dL_dtemporal"][k]
                    for k in grads["dL_dspatial"]
                }
                adam_spatial.step(
                    {
                        "W_enc": encoder.master_spatial.W_enc,
                        "b_enc": encoder.master_spatial.b_enc,
                        "W_dec": encoder.master_spatial.W_dec,
                        "b_dec": encoder.master_spatial.b_dec,
                    },
                    combined,
                )
            else:
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

                if adam_temporal is not None:
                    adam_temporal.step(
                        {
                            "W_enc": encoder.master_temporal.W_enc,
                            "b_enc": encoder.master_temporal.b_enc,
                            "W_dec": encoder.master_temporal.W_dec,
                            "b_dec": encoder.master_temporal.b_dec,
                        },
                        grads["dL_dtemporal"],
                    )

            if adam_embedding is not None:
                # Embedding is frozen per design, but we keep the hook
                pass

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
    """
    Fit linear probe on pooled representations and compute accuracies.

    Returns dict with train_acc, test_acc, and per-class test accuracies.
    """
    # Forward pass to get pooled representations
    fwd_train = encoder.forward_with_intermediates(train_grid)
    fwd_test = encoder.forward_with_intermediates(test_grid)

    train_pooled = fwd_train["pooled"]  # (n_train, d_out)
    test_pooled = fwd_test["pooled"]    # (n_test, d_out)

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

    # Per-class accuracies
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


def run_single_experiment(
    variant: str,
    seed: int,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    lr: float = LR,
    update_encoder: bool = True,
) -> dict:
    """
    Run a single experiment configuration.

    Parameters
    ----------
    variant : str
        One of "P3-A", "P3-B", "P3-C", or "Untrained".
    seed : int
        Random seed.
    epochs : int
        Number of training epochs.
    batch_size : int
        Batch size.
    lr : float
        Learning rate.
    update_encoder : bool
        If False, freeze encoder and only train JEPA predictors.

    Returns
    -------
    dict with all metrics.
    """
    print(f"\n    Variant: {variant}, Seed: {seed}, Epochs: {epochs}")
    rng = np.random.default_rng(seed)

    # Generate dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=500,
        n_test_per_class=200,
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
        enc_variant = "P3-B"  # Use P3-B architecture for untrained baseline
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
            # P3-C: spatial and temporal share the same master node,
            # so we use a single Adam optimizer.
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
                adam_temporal=None,  # Don't update temporal during phase 1
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
                adam_spatial=None,  # Freeze spatial
                adam_temporal=adam_temporal,
                adam_embedding=None,
            )
            loss_history.append(metrics)
            if epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1:
                print(f"        Epoch {epoch}: spatial_loss={metrics['spatial_loss']:.4f}, "
                      f"temporal_loss={metrics['temporal_loss']:.4f}")

    else:
        # P3-B, P3-C, or Untrained: joint training with alpha=0.5
        alpha = 0.5 if update_encoder else 0.5  # For untrained, alpha doesn't matter for encoder
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
#  Main
# ---------------------------------------------------------------------------

def main(smoke_test: bool = False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if smoke_test:
        print("=" * 70)
        print("  PHASE 3 SMOKE TEST (2 epochs, 1 seed)")
        print("=" * 70)
        test_seeds = [42]
        test_epochs = 2
        test_variants = ["P3-A", "P3-B", "P3-C", "Untrained"]
    else:
        print("=" * 70)
        print("  PHASE 3 FULL EXPERIMENT RUNNER")
        print(f"  Variants: P3-A, P3-B, P3-C, Untrained")
        print(f"  Seeds: {SEEDS}")
        print(f"  Epochs: {EPOCHS}")
        print("=" * 70)
        test_seeds = SEEDS
        test_epochs = EPOCHS
        test_variants = ["P3-A", "P3-B", "P3-C", "Untrained"]

    all_results: list[dict] = []
    total_runs = len(test_variants) * len(test_seeds)
    run_idx = 0

    for variant in test_variants:
        print(f"\n{'-' * 70}")
        print(f"  Variant: {variant}")
        print(f"{'-' * 70}")

        for seed in test_seeds:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}")

            result = run_single_experiment(
                variant=variant,
                seed=seed,
                epochs=test_epochs,
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

    # Run shortcut baselines (only once per seed, not per variant)
    if not smoke_test:
        print(f"\n{'-' * 70}")
        print("  Running Shortcut Baselines")
        print(f"{'-' * 70}")
        shortcut_rows: list[dict] = []
        for seed in test_seeds:
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

    # Summary
    print("\n" + "=" * 70)
    if smoke_test:
        print("  SMOKE TEST COMPLETE")
    else:
        print("  ALL RUNS COMPLETE")
    print("=" * 70)

    print("\n  Summary (mean ± std):")
    for variant in test_variants:
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

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 3 Experiment Runner")
    parser.add_argument("--smoke-test", action="store_true", help="Run quick smoke test (2 epochs, 1 seed)")
    args = parser.parse_args()
    main(smoke_test=args.smoke_test)
