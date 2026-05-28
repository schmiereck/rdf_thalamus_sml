"""
Phase 3 VICReg Fix — Pooled VICReg gradient injection.

This runner implements the Pooled VICReg loss applied directly on the
mean-pooled representation z_pooled, and propagates its gradient back
into the encoder backward pass via the last temporal code gradient.

Six conditions across 5 seeds, run via multiprocessing.

Conditions:
  A: P3-C, no pooled VICReg, readout='pooled'
  B: P3-C, no pooled VICReg, readout='spatial_pooled_then_flat'
  C: P3-C, pooled VICReg, readout='pooled'
  D: P3-C, pooled VICReg, readout='spatial_pooled_then_flat'
  E: Untrained, no pooled VICReg, readout='pooled'
  F: Untrained, no pooled VICReg, readout='spatial_pooled_then_flat'
"""

from __future__ import annotations

import csv
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from spatiotemporal_dataset import generate_spatiotemporal_dataset, N_CLASSES
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression
from run_phase3 import (
    create_jepa_losses,
    reshape_for_spatial_jepa,
    reshape_spatial_grads_back,
    reshape_for_temporal_jepa,
    reshape_temporal_grads_back,
)


# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100
EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-3
ALPHA = 0.5
OUTPUT_DIR = "phase_3"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "pooled_vicreg_results.csv")
REPORT_MD = os.path.join(OUTPUT_DIR, "REPORT_vicreg_fix.md")


# ---------------------------------------------------------------------------
#  1. Pooled VICReg loss & gradient
# ---------------------------------------------------------------------------

def pooled_vicreg_loss(z_pooled: np.ndarray, eps: float = 1.0) -> dict:
    """
    Compute VICReg loss (variance + covariance) directly on the pooled
    representation, shape (B, d_out).

    Parameters
    ----------
    z_pooled : np.ndarray, shape (B, d_out)
    eps : float  -- minimum acceptable standard deviation

    Returns
    -------
    dict with keys 'loss', 'var_loss', 'cov_loss', 'std'.
    """
    b, d = z_pooled.shape  # (B, d_out)

    mean = z_pooled.mean(axis=0, keepdims=True)  # (1, d)
    std = np.sqrt(z_pooled.var(axis=0, ddof=0) + 1e-12)  # (d,)

    # Variance loss: mean_j max(0, eps - std_j)
    var_loss = float(np.mean(np.maximum(0.0, eps - std)))

    # Covariance loss: (1/d) * sum_{j!=k} C_{jk}^2
    zc = z_pooled - mean  # (B, d)
    cov = (zc.T @ zc) / b  # (d, d)
    mask = 1.0 - np.eye(d)
    cov_loss = float(np.sum(cov ** 2 * mask) / d)

    return {
        "loss": 25.0 * var_loss + 25.0 * cov_loss,
        "var_loss": var_loss,
        "cov_loss": cov_loss,
        "std": float(np.mean(std)),
    }


def pooled_vicreg_grad(
    z_pooled: np.ndarray,
    lambda_var: float = 25.0,
    lambda_cov: float = 25.0,
    eps: float = 1.0,
) -> np.ndarray:
    """
    Compute gradient of pooled VICReg loss w.r.t. z_pooled.

    Parameters
    ----------
    z_pooled : np.ndarray, shape (B, d_out)
    lambda_var : float  -- weight for variance term (default 25.0)
    lambda_cov : float  -- weight for covariance term (default 25.0)
    eps : float  -- minimum acceptable std

    Returns
    -------
    dL_dz_pooled : np.ndarray, shape (B, d_out)
    """
    B, d = z_pooled.shape

    mean = z_pooled.mean(axis=0, keepdims=True)  # (1, d)
    std = np.sqrt(z_pooled.var(axis=0, ddof=0) + 1e-12)  # (d,)
    mask_var = (std < eps).astype(float)  # (d,)

    # --- Gradient w.r.t. variance loss ---
    # L_var = (1/d) * sum_j max(0, eps - std_j)
    # dL_var/d(z_pooled[i,j]) = -(lambda_var / (B * d)) *
    #                            mask_var[j] * (z_pooled[i,j] - mean_j) / (B * std_j)
    # Wait, let me redo: L_var = mean_j max(0, eps - std_j)
    # dL_var/d std_j = -(1/d) * mask_var[j]
    # std_j = sqrt( (1/B) sum_i (z[i,j] - mean_j)^2 + eps2 )
    # d std_j / d z[i,j] = (z[i,j] - mean_j) / (B * std_j)
    # d mean_j / d z[i,j] = 1/B, but since z[i,j]-mean appears in std:
    # d std_j / d z[i,j] = (z[i,j] - mean_j) / (B * std_j) after chain rule

    # dL_var/d z[i,j] = (-1/d * mask_var[j]) * (z[i,j] - mean_j) / (B * std_j)
    # scaled by lambda_var:
    zc = z_pooled - mean  # (B, d)
    dL_var_dz = (
        -lambda_var
        * mask_var[None, :]   # (1, d) broadcast
        * zc
        / (B * d * std[None, :] + 1e-12)
    )  # (B, d)

    # --- Gradient w.r.t. covariance loss ---
    # L_cov = (1/d) sum_{j!=k} C_{jk}^2
    # C = zc^T @ zc / B, C_{jk} = (1/B) sum_i zc[i,j] * zc[i,k]
    # d L_cov / d zc[i,:] = (2 / (B * d)) * sum_{k != j} C_{jk} * zc[i,k]
    # = (2 / (B * d)) * (zc[i,:] @ C_off)_j  where C_off = off-diagonal C
    zc_centered = z_pooled - mean  # (B, d)
    cov = (zc_centered.T @ zc_centered) / B  # (d, d)
    C_off = cov * (1.0 - np.eye(d))  # (d, d), zero diagonal

    # dL_cov/dzc[i,:] = (lambda_cov * 2 / (B * d)) * C_off @ zc[i,:]^T
    # = (lambda_cov * 2 / (B * d)) * (zc_centered @ C_off.T)[i,:]
    # But C is symmetric so C_off.T = C_off
    dL_cov_dz = (lambda_cov * 2.0 / (B * d)) * (zc_centered @ C_off)  # (B, d)

    dL_dz = dL_var_dz + dL_cov_dz  # (B, d)
    return dL_dz


# ---------------------------------------------------------------------------
#  2. Training epoch with Pooled VICReg
# ---------------------------------------------------------------------------

def train_jepa_epoch_with_pooled_vicreg(
    encoder: SpatiotemporalEncoder,
    spatial_jepas: list[JEPALoss],
    temporal_jepas: list[JEPALoss],
    train_grid: np.ndarray,
    batch_size: int,
    rng: np.random.Generator,
    alpha: float = ALPHA,
    adam_spatial: _Adam | None = None,
    adam_temporal: _Adam | None = None,
    use_pooled_vicreg: bool = False,
    lambda_var: float = 25.0,
    lambda_cov: float = 25.0,
    eps: float = 1.0,
) -> dict:
    """
    Train one epoch, optionally adding pooled VICReg gradient to the
    last temporal code gradient.

    The key line: after computing pooled VICReg gradient dL_dz_pooled (B, d_out),
    we expand it to shape (B, T_final, S_final, d_out) by broadcasting
    (since pooled = mean over T_final and S_final), and add:

        temporal_code_grads[-1] += dL_dpooled_expanded / (1.0 - alpha)

    The division by (1 - alpha) corrects for the temporal backward pass
    weighting.
    """
    n_samples = train_grid.shape[0]
    perm = rng.permutation(n_samples)

    total_spatial_loss = 0.0
    total_temporal_loss = 0.0
    total_combined_loss = 0.0
    total_pooled_var_loss = 0.0
    total_pooled_cov_loss = 0.0
    total_pooled_std = 0.0
    n_batches = 0

    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch = train_grid[perm[start:end]]  # (B, S, T)

        fwd = encoder.forward_with_intermediates(batch)

        # --- Spatial JEPA ---
        spatial_losses = []
        spatial_code_grads = []
        for l in range(encoder.n_spatial_layers):
            out = fwd["spatial_outputs"][l]  # (B, S_l, T, d)
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
            out = fwd["temporal_outputs"][l]  # (B, T_l, S_final, d)
            B, T_l, S_f, d = out.shape
            jepa_in = reshape_for_temporal_jepa(out)
            result = temporal_jepas[l].step([jepa_in])
            temporal_losses.append(result["loss"])
            cg = result["code_grads"][0]
            cg_back = reshape_temporal_grads_back(cg, B, T_l, S_f, d)
            temporal_code_grads.append(cg_back)

        # --- Pooled VICReg gradient injection ---
        if use_pooled_vicreg:
            z_pooled = fwd["pooled"]  # (B, d_out)
            dL_dzp = pooled_vicreg_grad(z_pooled, lambda_var, lambda_cov, eps)  # (B, d_out)

            # Expand to last temporal output shape: (B, T_final, S_final, d_out)
            T_final, S_final = fwd["temporal_outputs"][-1].shape[1:3]
            # pooled = mean over axes 1 and 2 of temporal_outputs[-1]
            dL_dpooled_expanded = dL_dzp[:, None, None, :] / (T_final * S_final)  # (B,1,1,d_out) broadcast
            dL_dpooled_expanded = np.broadcast_to(
                dL_dpooled_expanded,
                fwd["temporal_outputs"][-1].shape,
            ).copy()  # (B, T_final, S_final, d_out)

            # Add to last temporal code gradient, scaled by 1/(1-alpha)
            temporal_code_grads[-1] = temporal_code_grads[-1] + dL_dpooled_expanded / (1.0 - alpha)

            # Record pooled VICReg metrics
            pv_metrics = pooled_vicreg_loss(z_pooled, eps)
            total_pooled_var_loss += pv_metrics["var_loss"]
            total_pooled_cov_loss += pv_metrics["cov_loss"]
            total_pooled_std += pv_metrics["std"]
        else:
            total_pooled_var_loss += 0.0
            total_pooled_cov_loss += 0.0
            total_pooled_std += float(np.sqrt(fwd["pooled"].var(axis=0, ddof=0).mean() + 1e-12))

        # --- Backprop through encoder ---
        if adam_spatial is not None or adam_temporal is not None:
            grads = encoder.backward(
                fwd,
                dL_dspatial_codes=spatial_code_grads,
                dL_dtemporal_codes=temporal_code_grads,
                alpha=alpha,
            )

            if encoder.variant == "P3-C":
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
        "pooled_var_loss": total_pooled_var_loss / n_batches,
        "pooled_cov_loss": total_pooled_cov_loss / n_batches,
        "pooled_std": total_pooled_std / n_batches,
    }


# ---------------------------------------------------------------------------
#  3. Classification v2 — supports multiple readout representations
# ---------------------------------------------------------------------------

def evaluate_classification_v2(
    encoder: SpatiotemporalEncoder,
    train_grid: np.ndarray,
    train_y: np.ndarray,
    test_grid: np.ndarray,
    test_y: np.ndarray,
    seed: int = 42,
    readout: str = "pooled",
) -> dict:
    """
    Fit linear probe on representations and compute accuracies.

    readout : str
        - 'pooled': use fwd["pooled"] (B, d_out)
        - 'spatial_pooled_then_flat': mean over spatial axis of last
          temporal output, then flatten.
          fwd["temporal_outputs"][-1].mean(axis=2).reshape(len(y), -1)
    """
    fwd_train = encoder.forward_with_intermediates(train_grid)
    fwd_test = encoder.forward_with_intermediates(test_grid)

    if readout == "pooled":
        train_feats = fwd_train["pooled"]  # (n_train, d_out)
        test_feats = fwd_test["pooled"]   # (n_test, d_out)
    elif readout == "spatial_pooled_then_flat":
        temp_last_tr = fwd_train["temporal_outputs"][-1]  # (B, T_final, S_final, d_out)
        temp_last_te = fwd_test["temporal_outputs"][-1]
        # Mean over spatial axis (axis=2), then flatten
        train_feats = temp_last_tr.mean(axis=2).reshape(len(train_y), -1)
        test_feats = temp_last_te.mean(axis=2).reshape(len(test_y), -1)
    else:
        raise ValueError(f"Unknown readout type: {readout}")

    probe = SimpleLogisticRegression(
        n_classes=N_CLASSES,
        n_features=train_feats.shape[1],
        lr=0.1,
        max_iter=2000,
        seed=seed,
    )
    probe.fit(train_feats, train_y)

    train_acc = float(probe.score(train_feats, train_y))
    test_acc = float(probe.score(test_feats, test_y))

    per_class = {}
    for cls in range(N_CLASSES):
        mask = test_y == cls
        if mask.sum() > 0:
            cls_acc = float(probe.score(test_feats[mask], test_y[mask]))
        else:
            cls_acc = 0.0
        per_class[f"class_{cls}_acc"] = cls_acc

    return {
        "train_acc": train_acc,
        "test_acc": test_acc,
        **per_class,
    }


# ---------------------------------------------------------------------------
#  4. Single experiment runner (parameterized)
# ---------------------------------------------------------------------------

def run_single_experiment_with_fixes(args: tuple) -> dict:
    """
    Run one experiment.

    args : tuple (
        condition, seed, use_pooled_vicreg, readout_type,
        epochs, batch_size, lr
    )

    condition : str  -- 'P3-C' or 'Untrained'
    """
    (condition, seed, use_pooled_vicreg, readout_type,
     epochs, batch_size, lr) = args

    rng = np.random.default_rng(seed)

    # Generate dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=seed,
    )
    train_grid = ds["train_grid"]
    train_y = ds["train_y"]
    test_grid = ds["test_grid"]
    test_y = ds["test_y"]

    # Create encoder
    enc_variant = "P3-C" if condition == "P3-C" else "P3-C"  # Untrained also uses P3-C architecture
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

    # Set up Adam optimizers
    adam_spatial = None
    adam_temporal = None
    update_encoder = (condition != "Untrained")
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
        adam_temporal = adam_spatial  # P3-C: shared node -> shared Adam

    # Training
    t0 = time.time()
    for epoch in range(epochs):
        metrics = train_jepa_epoch_with_pooled_vicreg(
            encoder,
            spatial_jepas,
            temporal_jepas,
            train_grid,
            batch_size,
            rng,
            alpha=ALPHA,
            adam_spatial=adam_spatial if update_encoder else None,
            adam_temporal=adam_temporal if update_encoder else None,
            use_pooled_vicreg=use_pooled_vicreg,
        )
    t1 = time.time()
    training_time = t1 - t0

    # Final losses (from last batch avg — recompute on full train set for accuracy)
    final_fwd = encoder.forward_with_intermediates(train_grid)
    spatial_codes_full = [
        reshape_for_spatial_jepa(final_fwd["spatial_outputs"][l])
        for l in range(encoder.n_spatial_layers)
    ]
    temporal_codes_full = [
        reshape_for_temporal_jepa(final_fwd["temporal_outputs"][l])
        for l in range(encoder.n_temporal_layers)
    ]
    s_fwd = spatial_jepas[0].forward(spatial_codes_full)
    t_fwd = temporal_jepas[0].forward(temporal_codes_full)

    final_spatial_loss = s_fwd["loss"]
    final_temporal_loss = t_fwd["loss"]

    if use_pooled_vicreg:
        pv = pooled_vicreg_loss(final_fwd["pooled"])
        final_pooled_var_loss = pv["var_loss"]
        final_pooled_cov_loss = pv["cov_loss"]
        final_pooled_std = pv["std"]
    else:
        final_pooled_std = float(np.sqrt(final_fwd["pooled"].var(axis=0, ddof=0) + 1e-12).mean())
        final_pooled_var_loss = 0.0
        final_pooled_cov_loss = 0.0

    # Classification evaluation
    eval_results = evaluate_classification_v2(
        encoder, train_grid, train_y, test_grid, test_y, seed=seed,
        readout=readout_type,
    )

    return {
        "condition": condition,
        "seed": seed,
        "use_pooled_vicreg": use_pooled_vicreg,
        "readout_type": readout_type,
        "train_acc": eval_results["train_acc"],
        "test_acc": eval_results["test_acc"],
        "final_spatial_jepa_loss": final_spatial_loss,
        "final_temporal_jepa_loss": final_temporal_loss,
        "final_pooled_std": final_pooled_std,
        "final_pooled_var_loss": final_pooled_var_loss,
        "final_pooled_cov_loss": final_pooled_cov_loss,
        "training_time_sec": training_time,
        "param_count": param_count,
        "class_0_acc": eval_results["class_0_acc"],
        "class_1_acc": eval_results["class_1_acc"],
        "class_2_acc": eval_results["class_2_acc"],
        "class_3_acc": eval_results["class_3_acc"],
    }


# ---------------------------------------------------------------------------
#  5. Incremental CSV writer
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "condition", "seed", "use_pooled_vicreg", "readout_type",
    "train_acc", "test_acc",
    "final_spatial_jepa_loss", "final_temporal_jepa_loss",
    "final_pooled_std", "final_pooled_var_loss", "final_pooled_cov_loss",
    "training_time_sec", "param_count",
    "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
]


def save_result_incrementally(result: dict, csv_path: str) -> None:
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)


# ---------------------------------------------------------------------------
#  6. Main with conditions and multiprocessing
# ---------------------------------------------------------------------------

def main(dry_run: bool = False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Remove old results file to start fresh
    if os.path.exists(RESULTS_CSV):
        os.remove(RESULTS_CSV)

    # Define conditions
    conditions = [
        # (condition, use_pooled_vicreg, readout_type, label)
        ("P3-C", False, "pooled", "A: P3-C, no VICReg, readout=pooled"),
        ("P3-C", False, "spatial_pooled_then_flat", "B: P3-C, no VICReg, readout=spatial_pooled"),
        ("P3-C", True, "pooled", "C: P3-C, VICReg, readout=pooled"),
        ("P3-C", True, "spatial_pooled_then_flat", "D: P3-C, VICReg, readout=spatial_pooled"),
        ("Untrained", False, "pooled", "E: Untrained, readout=pooled"),
        ("Untrained", False, "spatial_pooled_then_flat", "F: Untrained, readout=spatial_pooled"),
    ]

    if dry_run:
        seeds_to_use = [42]
        ep = 1
    else:
        seeds_to_use = SEEDS
        ep = EPOCHS

    # Build task list
    tasks = []
    labels = []
    for (cond, use_pv, readout, label) in conditions:
        for seed in seeds_to_use:
            tasks.append((cond, seed, use_pv, readout, ep, BATCH_SIZE, LR))
            labels.append(label)

    total_tasks = len(tasks)
    mode = "DRY-RUN" if dry_run else "FULL RUN"
    print("=" * 70)
    print(f"  PHASE 3 VICREG FIX — {mode}")
    print(f"  Tasks: {total_tasks}")
    print(f"  Epochs: {ep}, Batch size: {BATCH_SIZE}, LR: {LR}")
    print(f"  Seeds: {seeds_to_use}")
    print(f"  Conditions: {len(conditions)}")
    print("=" * 70)

    t_start = time.time()

    if dry_run:
        # Single-threaded for debug
        all_results = [run_single_experiment_with_fixes(t) for t in tasks]
    else:
        # Multiprocessing
        n_workers = min(5, total_tasks)  # parallel across seeds
        with Pool(processes=n_workers) as pool:
            all_results = pool.map(run_single_experiment_with_fixes, tasks)

    t_end = time.time()
    print(f"\n  All runs completed in {t_end - t_start:.1f}s")

    # Save all results incrementally
    for r in all_results:
        save_result_incrementally(r, RESULTS_CSV)
    print(f"  Results saved to {RESULTS_CSV}")

    # Summary
    print("\n  Summary (mean ± std):")
    for label in [c[3] for c in conditions]:
        cond_key = label.split(":")[0].strip()
        rows = [r for r in all_results if r["condition"] == cond_key
                and (not use_pv or r["use_pooled_vicreg"] == use_pv)
                and r["readout_type"] == readout]
        # Better matching
        pass

    for (cond, use_pv, readout, label) in conditions:
        rows = [r for r in all_results
                if r["condition"] == cond
                and r["use_pooled_vicreg"] == use_pv
                and r["readout_type"] == readout]
        if rows:
            test_accs = [r["test_acc"] for r in rows]
            print(
                f"    {label:50s}: test_acc={np.mean(test_accs):.4f}±{np.std(test_accs, ddof=1 if len(test_accs)>1 else 0):.4f}"
            )

    print("=" * 70)
    return all_results


# ---------------------------------------------------------------------------
#  7. Statistical Analysis & Report
# ---------------------------------------------------------------------------

def run_statistical_analysis(results: list[dict]) -> None:
    """
    Run paired t-test and Cohen's d between Condition D and Untrained+spatial_pooled.
    Generate comprehensive markdown report.
    """
    from scipy import stats

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extract Condition D: P3-C, use_pooled_vicreg=True, readout='spatial_pooled_then_flat'
    d_rows = [r for r in results
              if r["condition"] == "P3-C"
              and r["use_pooled_vicreg"] is True
              and r["readout_type"] == "spatial_pooled_then_flat"]
    d_rows.sort(key=lambda x: x["seed"])

    # Extract Untrained+spatial_pooled: Untrained, readout='spatial_pooled_then_flat'
    u_rows = [r for r in results
              if r["condition"] == "Untrained"
              and r["readout_type"] == "spatial_pooled_then_flat"]
    u_rows.sort(key=lambda x: x["seed"])

    assert len(d_rows) == 5, f"Expected 5 Condition D results, got {len(d_rows)}"
    assert len(u_rows) == 5, f"Expected 5 Untrained results, got {len(u_rows)}"

    # Pair by seed
    d_accs = np.array([r["test_acc"] for r in d_rows])
    u_accs = np.array([r["test_acc"] for r in u_rows])

    # Paired t-test
    t_stat, p_val = stats.ttest_rel(d_accs, u_accs)

    # Gain in percentage points
    gain = float(d_accs.mean() - u_accs.mean())

    # Cohen's d (paired)
    diff = d_accs - u_accs
    cohens_d = float(diff.mean() / (diff.std(ddof=1) + 1e-12))

    # Criteria checks
    gain_ok = gain >= 0.08    # >= 8 percentage points
    p_ok = p_val < 0.05
    d_ok = cohens_d >= 0.8
    all_pass = gain_ok and p_ok and d_ok

    # Also collect per-condition summaries
    cond_data = {}
    for (cond, use_pv, readout, label) in [
        ("P3-C", False, "pooled", "A"),
        ("P3-C", False, "spatial_pooled_then_flat", "B"),
        ("P3-C", True, "pooled", "C"),
        ("P3-C", True, "spatial_pooled_then_flat", "D"),
        ("Untrained", False, "pooled", "E: Untrained+pooled"),
        ("Untrained", False, "spatial_pooled_then_flat", "F: Untrained+spatial_pooled"),
    ]:
        rows = [r for r in results
                if r["condition"] == cond
                and r["use_pooled_vicreg"] == use_pv
                and r["readout_type"] == readout]
        if rows:
            accs = np.array([r["test_acc"] for r in rows])
            pstd = np.array([r["final_pooled_std"] for r in rows])
            sl = np.array([r["final_spatial_jepa_loss"] for r in rows])
            tl = np.array([r["final_temporal_jepa_loss"] for r in rows])
            cond_data[label] = {
                "mean_acc": float(accs.mean()),
                "std_acc": float(np.std(accs, ddof=1)),
                "mean_pooled_std": float(pstd.mean()),
                "mean_spatial_loss": float(sl.mean()),
                "mean_temporal_loss": float(tl.mean()),
                "individual_accs": accs.tolist(),
            }

    # Build report
    report_lines = []
    report_lines.append("# Phase 3 VICReg Fix — Comprehensive Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Experiment setup
    report_lines.append("## Experiment Setup")
    report_lines.append("")
    report_lines.append(f"- **Epochs**: {EPOCHS}")
    report_lines.append(f"- **Batch size**: {BATCH_SIZE}")
    report_lines.append(f"- **Learning rate**: {LR}")
    report_lines.append(f"- **Seeds**: {SEEDS}")
    report_lines.append(f"- **Train per class**: {N_TRAIN_PER_CLASS}")
    report_lines.append(f"- **Test per class**: {N_TEST_PER_CLASS}")
    report_lines.append(f"- **Alpha**: {ALPHA}")
    report_lines.append("")
    report_lines.append("## Conditions")
    report_lines.append("")
    report_lines.append("| Label | Encoder | Pooled VICReg | Readout |")
    report_lines.append("|-------|---------|---------------|---------|")
    report_lines.append("| A | P3-C | No | pooled |")
    report_lines.append("| B | P3-C | No | spatial_pooled_then_flat |")
    report_lines.append("| C | P3-C | Yes | pooled |")
    report_lines.append("| D | P3-C | Yes | spatial_pooled_then_flat |")
    report_lines.append("| E | Untrained | No | pooled |")
    report_lines.append("| F | Untrained | No | spatial_pooled_then_flat |")
    report_lines.append("")

    # Results table
    report_lines.append("## Results Summary")
    report_lines.append("")
    report_lines.append("| Condition | Mean Test Acc | Std Acc | Pooled Std | Spatial Loss | Temporal Loss |")
    report_lines.append("|-----------|--------------:|--------:|-----------:|-------------:|--------------:|")
    for label in ["A", "B", "C", "D", "E: Untrained+pooled", "F: Untrained+spatial_pooled"]:
        if label in cond_data:
            d = cond_data[label]
            report_lines.append(
                f"| {label} | {d['mean_acc']:.4f} | {d['std_acc']:.4f} | "
                f"{d['mean_pooled_std']:.4f} | {d['mean_spatial_loss']:.4f} | {d['mean_temporal_loss']:.4f} |"
            )
    report_lines.append("")

    # Per-seed detail
    report_lines.append("### Per-seed Detail")
    report_lines.append("")
    report_lines.append("| Seed | D (P3-C+VICReg+spatial) | F (Untrained+spatial) | Diff |")
    report_lines.append("|------|-------------------------|-----------------------|------|")
    for r_d, r_u in zip(d_rows, u_rows):
        assert r_d["seed"] == r_u["seed"], "Seed mismatch"
        diff = r_d["test_acc"] - r_u["test_acc"]
        report_lines.append(
            f"| {r_d['seed']} | {r_d['test_acc']:.4f} | {r_u['test_acc']:.4f} | {diff:+.4f} |"
        )
    report_lines.append("")

    # Statistical analysis
    report_lines.append("## Statistical Analysis: Condition D vs Untrained+spatial_pooled")
    report_lines.append("")
    report_lines.append(f"- **Mean accuracy (D)**: {d_accs.mean():.4f}")
    report_lines.append(f"- **Mean accuracy (Untrained+spatial_pooled)**: {u_accs.mean():.4f}")
    report_lines.append(f"- **Gain**: {gain:.4f} ({gain*100:.2f} percentage points)")
    report_lines.append(f"- **Paired t-test**: t = {t_stat:.4f}, p = {p_val:.6f}")
    report_lines.append(f"- **Cohen's d (paired)**: {cohens_d:.4f}")
    report_lines.append("")

    # Criteria checks
    report_lines.append("### Criteria Checks")
    report_lines.append("")
    report_lines.append(f"| Criterion | Threshold | Observed | Status |")
    report_lines.append(f"|-----------|-----------|----------|--------|")
    report_lines.append(
        f"| D gain ≥ 8pp | ≥ 0.08 | {gain:.4f} | {'PASS' if gain_ok else 'FAIL'} |"
    )
    report_lines.append(
        f"| p-value < 0.05 | < 0.05 | {p_val:.6f} | {'PASS' if p_ok else 'FAIL'} |"
    )
    report_lines.append(
        f"| Cohen's d ≥ 0.8 | ≥ 0.8 | {cohens_d:.4f} | {'PASS' if d_ok else 'FAIL'} |"
    )
    report_lines.append("")

    # Verdict
    report_lines.append("## Falsification Verdict")
    report_lines.append("")
    if all_pass:
        report_lines.append(
            "**✅ PASSED** — All three criteria are met. The Pooled VICReg + "
            "spatial_pooled_then_flat readout (Condition D) significantly outperforms "
            "the untrained baseline with spatial_pooled_then_flat readout, "
            "with a gain of {:.2f}pp, p = {:.6f}, and Cohen's d = {:.4f}.".format(
                gain * 100, p_val, cohens_d
            )
        )
    else:
        report_lines.append("**❌ FAILED** — Not all criteria are met. The hypothesis that "
                            "Pooled VICReg training significantly improves downstream "
                            "classification is **not falsified** (i.e. the specific claim "
                            "that Condition D beats Untrained+spatial_pooled by ≥8pp with "
                            "p<0.05 and d≥0.8 is not supported by these results.)")
        if not gain_ok:
            report_lines.append(f"  - Gain {gain*100:.2f}pp < 8pp threshold")
        if not p_ok:
            report_lines.append(f"  - p-value {p_val:.6f} ≥ 0.05")
        if not d_ok:
            report_lines.append(f"  - Cohen's d {cohens_d:.4f} < 0.8")
    report_lines.append("")

    # Interpretation
    report_lines.append("## Interpretation")
    report_lines.append("")
    # Additional comparisons
    if "C" in cond_data and "A" in cond_data:
        c_gain = cond_data["C"]["mean_acc"] - cond_data["A"]["mean_acc"]
        report_lines.append(
            f"- **C vs A** (VICReg effect on pooled readout): {c_gain*100:+.2f}pp"
        )
    if "D" in cond_data and "B" in cond_data:
        d_gain_b = cond_data["D"]["mean_acc"] - cond_data["B"]["mean_acc"]
        report_lines.append(
            f"- **D vs B** (VICReg effect on spatial_pooled readout): {d_gain_b*100:+.2f}pp"
        )
    if "D" in cond_data and "C" in cond_data:
        d_vs_c = cond_data["D"]["mean_acc"] - cond_data["C"]["mean_acc"]
        report_lines.append(
            f"- **D vs C** (spatial_pooled vs pooled with VICReg): {d_vs_c*100:+.2f}pp"
        )
    if "B" in cond_data and "A" in cond_data:
        b_vs_a = cond_data["B"]["mean_acc"] - cond_data["A"]["mean_acc"]
        report_lines.append(
            f"- **B vs A** (spatial_pooled vs pooled without VICReg): {b_vs_a*100:+.2f}pp"
        )
    if "F: Untrained+spatial_pooled" in cond_data and "E: Untrained+pooled" in cond_data:
        f_vs_e = cond_data["F: Untrained+spatial_pooled"]["mean_acc"] - cond_data["E: Untrained+pooled"]["mean_acc"]
        report_lines.append(
            f"- **F vs E** (readout effect on untrained): {f_vs_e*100:+.2f}pp"
        )
    report_lines.append("")

    # Write report
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\n  Statistical analysis complete. Report saved to: {REPORT_MD}")
    print(f"  Gain: {gain*100:.2f}pp, p={p_val:.6f}, d={cohens_d:.4f}")
    print(f"  Verdict: {'PASS' if all_pass else 'FAIL'}")


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Single seed, 1 epoch debug run")
    args = parser.parse_args()

    results = main(dry_run=args.dry_run)

    if not args.dry_run:
        run_statistical_analysis(results)
