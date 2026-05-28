#!/usr/bin/env python3
"""
Phase 4 — Training Objective Comparison (8 objectives × 5 seeds).

Compares four training-objective families on the P3-C encoder with
spatial_pooled_then_flat readout:

    JEPA        : per-layer bidirectional prediction + local VICReg
    SFA         : slowness on final temporal output (+/- pooled VICReg)
    Hebbian     : variance maximisation on ALL intermediate codes (+/- pooled VICReg)
    Reconstruction: local sparse AE at every node (+/- pooled VICReg)

Each objective is run with and without pooled VICReg gradient injection.
An untrained baseline is included for reference.
"""

from __future__ import annotations

import argparse
import csv
import gc
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
LAMBDA_HEBB = 25.0
LAMBDA_L1 = 0.01
OUTPUT_DIR = "phase_4"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase4_results.csv")
REPORT_MD = os.path.join(OUTPUT_DIR, "REPORT.md")

OBJECTIVES = ["jepa", "sfa", "hebbian", "recon"]


# =============================================================================
#  1. Pooled VICReg loss & gradient  (reuse from run_phase3_vicreg_fix.py)
# =============================================================================

def pooled_vicreg_loss(z_pooled: np.ndarray, eps: float = 1.0) -> dict:
    """
    VICReg (variance + covariance) on pooled representation z_pooled, shape (B, d_out).
    """
    b, d = z_pooled.shape
    mean = z_pooled.mean(axis=0, keepdims=True)
    std = np.sqrt(z_pooled.var(axis=0, ddof=0) + 1e-12)
    var_loss = float(np.mean(np.maximum(0.0, eps - std)))
    zc = z_pooled - mean
    cov = (zc.T @ zc) / b
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
    """Gradient of pooled VICReg loss w.r.t. z_pooled."""
    B, d = z_pooled.shape
    mean = z_pooled.mean(axis=0, keepdims=True)
    std = np.sqrt(z_pooled.var(axis=0, ddof=0) + 1e-12)
    mask_var = (std < eps).astype(float)

    zc = z_pooled - mean
    dL_var_dz = (
        -lambda_var
        * mask_var[None, :]
        * zc
        / (B * d * std[None, :] + 1e-12)
    )

    zc_centered = z_pooled - mean
    cov = (zc_centered.T @ zc_centered) / B
    C_off = cov * (1.0 - np.eye(d))
    dL_cov_dz = (lambda_cov * 2.0 / (B * d)) * (zc_centered @ C_off)
    return dL_var_dz + dL_cov_dz


# =============================================================================
#  2. Objective-specific loss / gradient dispatchers
# =============================================================================

# ---------------------------------------------------------------------------
#  2a. JEPA — everything happens inside the epoch loop via JEPALoss classes
# ---------------------------------------------------------------------------

# (code gradients are handled inline by calling spatial_jepas[l].step() etc.)

# ---------------------------------------------------------------------------
#  2b. SFA — slowness on final temporal output
# ---------------------------------------------------------------------------

def sfa_loss_and_grad(z: np.ndarray) -> dict:
    """
    Compute SFA slowness loss and gradient for z of shape (B, T, S, d).

    L_slow = (1 / (B*(T-1)*S*d)) * Σ_{b,s,t≥1} ||z[b,t,s,:] - z[b,t-1,s,:]||²

    Returns dict with keys 'loss', 'grad' (same shape as z).
    """
    B, T, S, d = z.shape
    if T <= 1:
        return {"loss": 0.0, "grad": np.zeros_like(z)}

    denom = B * (T - 1) * S * d
    delta = z[:, 1:, :, :] - z[:, :-1, :, :]    # (B, T-1, S, d)
    loss = float(np.mean(delta ** 2))

    grad = np.zeros_like(z)
    coeff = 2.0 / denom
    grad[:, 1:, :, :] += coeff * delta
    grad[:, :-1, :, :] -= coeff * delta

    return {"loss": loss, "grad": grad}


# ---------------------------------------------------------------------------
#  2c. Hebbian — variance maximisation on ALL intermediate codes
# ---------------------------------------------------------------------------

def hebbian_loss_and_grad(z: np.ndarray, lambda_hebb: float = LAMBDA_HEBB) -> dict:
    """
    Variance maximisation (negative variance) for z of shape (B, P1, P2, d).

    L_Hebb = -(lambda_hebb/d) * Σ_j Var(z[:, :, :, j])

    Gradient: dL/dz = -(2*lambda_hebb/(M*d)) * (z - mean)
    where M = B*P1*P2.

    Returns dict with keys 'loss', 'grad'.
    """
    orig_shape = z.shape
    M = np.prod(orig_shape[:-1])
    d = orig_shape[-1]

    z_flat = z.reshape(-1, d)          # (M, d)
    mean = z_flat.mean(axis=0, keepdims=True)
    var = z_flat.var(axis=0, ddof=0).sum()

    loss = float(-(lambda_hebb / d) * var)
    grad_flat = -(2.0 * lambda_hebb / (M * d)) * (z_flat - mean)
    grad = grad_flat.reshape(orig_shape)

    return {"loss": loss, "grad": grad}


# ---------------------------------------------------------------------------
#  2d. Reconstruction — local sparse AE at each node
# ---------------------------------------------------------------------------

def recon_loss_and_grad(
    code: np.ndarray,        # (B, P1, P2, d_out)  post-tanh code
    node_input: np.ndarray,  # (B, P1, P2, 3, d)   raw node inputs
    W_dec: np.ndarray,       # (d_out, 3*d)
    b_dec: np.ndarray,       # (3*d,)
    lambda_l1: float = LAMBDA_L1,
    eps: float = 1e-12,
) -> dict:
    """
    Local reconstruction: L = MSE(input, recon) + lambda_l1 * mean(|code|).

    code shape: (B, P1, P2, d_out)
    node_input shape: (B, P1, P2, 3, d)

    Returns dict with:
        'loss', 'code_grad', 'W_dec_grad', 'b_dec_grad'
    """
    B, P1, P2, d_out = code.shape
    _, _, _, three, d = node_input.shape
    D_in = three * d
    M = B * P1 * P2

    # Flatten
    code_flat = code.reshape(M, d_out)                 # (M, d_out)
    x_flat = node_input.reshape(M, D_in)               # (M, D_in)

    # Reconstruct
    recon_flat = code_flat @ W_dec + b_dec             # (M, D_in)

    # MSE
    diff = recon_flat - x_flat                         # (M, D_in)
    mse = float(np.mean(diff ** 2))

    # L1 sparsity
    l1 = lambda_l1 * float(np.mean(np.abs(code_flat)))

    loss = mse + l1

    # --- gradients ---
    dL_drecon = (2.0 / (M * D_in)) * diff              # (M, D_in)

    # code gradient
    dL_dcode = dL_drecon @ W_dec.T                     # (M, d_out)
    dL_dcode += (lambda_l1 / (M * d_out)) * np.sign(code_flat)
    code_grad = dL_dcode.reshape(B, P1, P2, d_out)

    # decoder gradients
    W_dec_grad = code_flat.T @ dL_drecon               # (d_out, D_in)
    b_dec_grad = dL_drecon.sum(axis=0)                 # (D_in,)

    return {
        "loss": loss,
        "code_grad": code_grad,
        "W_dec_grad": W_dec_grad,
        "b_dec_grad": b_dec_grad,
    }


# =============================================================================
#  3. Unified training epoch
# =============================================================================

def train_epoch(
    encoder: SpatiotemporalEncoder,
    train_grid: np.ndarray,
    batch_size: int,
    rng: np.random.Generator,
    objective: str = "jepa",
    adam_spatial: _Adam | None = None,
    adam_temporal: _Adam | None = None,
    adam_decoder: _Adam | None = None,
    spatial_jepas: list[JEPALoss] | None = None,
    temporal_jepas: list[JEPALoss] | None = None,
    use_pooled_vicreg: bool = False,
) -> dict:
    """
    Train one epoch with the specified objective.

    Returns dict with losses and metrics.
    """
    n_samples = train_grid.shape[0]
    perm = rng.permutation(n_samples)

    total_obj_loss = 0.0
    total_pooled_var = 0.0
    total_pooled_cov = 0.0
    total_pooled_std = 0.0
    n_batches = 0

    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch = train_grid[perm[start:end]]

        fwd = encoder.forward_with_intermediates(batch)

        # =====================================================================
        #  Objective-specific code-gradient computation
        # =====================================================================

        if objective == "untrained":
            # No training — zero code gradients for backward pass
            spatial_code_grads = [np.zeros_like(fwd["spatial_outputs"][l])
                                   for l in range(encoder.n_spatial_layers)]
            temporal_code_grads = [np.zeros_like(fwd["temporal_outputs"][l])
                                    for l in range(encoder.n_temporal_layers)]
            obj_loss = 0.0
        elif objective == "jepa":
            # ---- Spatial JEPA ----
            spatial_code_grads = []
            spatial_losses = []
            for l in range(encoder.n_spatial_layers):
                out = fwd["spatial_outputs"][l]         # (B, S_l, T, d)
                B, S_l, T, d = out.shape
                jepa_in = reshape_for_spatial_jepa(out) # (B*T, S_l, d)
                result = spatial_jepas[l].step([jepa_in])
                spatial_losses.append(result["loss"])
                cg = result["code_grads"][0]
                spatial_code_grads.append(reshape_spatial_grads_back(cg, B, S_l, T, d))

            # ---- Temporal JEPA ----
            temporal_code_grads = []
            temporal_losses = []
            for l in range(encoder.n_temporal_layers):
                out = fwd["temporal_outputs"][l]         # (B, T_l, S_f, d)
                B, T_l, S_f, d = out.shape
                jepa_in = reshape_for_temporal_jepa(out) # (B*S_f, T_l, d)
                result = temporal_jepas[l].step([jepa_in])
                temporal_losses.append(result["loss"])
                cg = result["code_grads"][0]
                temporal_code_grads.append(reshape_temporal_grads_back(cg, B, T_l, S_f, d))

            obj_loss = ALPHA * np.mean(spatial_losses) + (1.0 - ALPHA) * np.mean(temporal_losses)

        elif objective == "sfa":
            # Slowness on FINAL temporal output only
            z = fwd["temporal_outputs"][-1]  # (B, T_f, S_f, d_out)
            sfa = sfa_loss_and_grad(z)

            spatial_code_grads = [np.zeros_like(fwd["spatial_outputs"][l])
                                   for l in range(encoder.n_spatial_layers)]
            temporal_code_grads = [np.zeros_like(fwd["temporal_outputs"][l])
                                    for l in range(encoder.n_temporal_layers)]
            temporal_code_grads[-1] = sfa["grad"]

            obj_loss = sfa["loss"]

        elif objective == "hebbian":
            # Variance maximisation on ALL intermediate codes
            hebb_losses = []
            spatial_code_grads = []
            temporal_code_grads = []

            for l in range(encoder.n_spatial_layers):
                z = fwd["spatial_outputs"][l]
                h = hebbian_loss_and_grad(z, LAMBDA_HEBB)
                spatial_code_grads.append(h["grad"])
                hebb_losses.append(h["loss"])

            for l in range(encoder.n_temporal_layers):
                z = fwd["temporal_outputs"][l]
                h = hebbian_loss_and_grad(z, LAMBDA_HEBB)
                temporal_code_grads.append(h["grad"])
                hebb_losses.append(h["loss"])

            obj_loss = np.mean(hebb_losses)

        elif objective == "recon":
            # Reconstruction + sparsity on ALL layers
            recon_losses = []
            spatial_code_grads = []
            temporal_code_grads = []
            dec_grads_spatial = []
            dec_grads_temporal = []

            node = encoder.master_spatial
            W_dec = node.W_dec
            b_dec = node.b_dec

            for l in range(encoder.n_spatial_layers):
                code = fwd["spatial_outputs"][l]
                inp = fwd["spatial_inputs"][l]
                r = recon_loss_and_grad(code, inp, W_dec, b_dec, LAMBDA_L1)
                spatial_code_grads.append(r["code_grad"])
                recon_losses.append(r["loss"])
                dec_grads_spatial.append({"W_dec": r["W_dec_grad"], "b_dec": r["b_dec_grad"]})

            for l in range(encoder.n_temporal_layers):
                code = fwd["temporal_outputs"][l]
                inp = fwd["temporal_inputs"][l]
                r = recon_loss_and_grad(code, inp, W_dec, b_dec, LAMBDA_L1)
                temporal_code_grads.append(r["code_grad"])
                recon_losses.append(r["loss"])
                dec_grads_temporal.append({"W_dec": r["W_dec_grad"], "b_dec": r["b_dec_grad"]})

            obj_loss = np.mean(recon_losses)

            # Update decoder separately (encoder.backward() gives zero decoder grads)
            if adam_decoder is not None:
                avg_W_dec_grad = (
                    sum(g["W_dec"] for g in dec_grads_spatial + dec_grads_temporal)
                    / (encoder.n_spatial_layers + encoder.n_temporal_layers)
                )
                avg_b_dec_grad = (
                    sum(g["b_dec"] for g in dec_grads_spatial + dec_grads_temporal)
                    / (encoder.n_spatial_layers + encoder.n_temporal_layers)
                )
                adam_decoder.step(
                    {"W_dec": W_dec, "b_dec": b_dec},
                    {"W_dec": avg_W_dec_grad, "b_dec": avg_b_dec_grad},
                )

        else:
            raise ValueError(f"Unknown objective: {objective}")

        # =====================================================================
        #  Pooled VICReg injection (same mechanism as Phase 3)
        # =====================================================================
        if use_pooled_vicreg:
            z_pooled = fwd["pooled"]  # (B, d_out)
            dL_dzp = pooled_vicreg_grad(z_pooled)  # (B, d_out)

            T_final, S_final = fwd["temporal_outputs"][-1].shape[1:3]
            dL_expanded = dL_dzp[:, None, None, :] / (T_final * S_final)
            dL_expanded = np.broadcast_to(
                dL_expanded, fwd["temporal_outputs"][-1].shape
            ).copy()

            # Scale by 1/(1−α) to match temporal backward weighting
            temporal_code_grads[-1] = temporal_code_grads[-1] + dL_expanded / (1.0 - ALPHA)

            pv = pooled_vicreg_loss(z_pooled)
            total_pooled_var += pv["var_loss"]
            total_pooled_cov += pv["cov_loss"]
            total_pooled_std += pv["std"]
        else:
            total_pooled_std += float(
                np.sqrt(fwd["pooled"].var(axis=0, ddof=0).mean() + 1e-12)
            )

        # =====================================================================
        #  Encoder backward + update
        # =====================================================================
        if adam_spatial is not None or adam_temporal is not None:
            grads = encoder.backward(
                fwd,
                dL_dspatial_codes=spatial_code_grads,
                dL_dtemporal_codes=temporal_code_grads,
                alpha=ALPHA,
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

        total_obj_loss += obj_loss
        n_batches += 1

    return {
        "obj_loss": total_obj_loss / n_batches,
        "pooled_var": total_pooled_var / n_batches,
        "pooled_cov": total_pooled_cov / n_batches,
        "pooled_std": total_pooled_std / n_batches,
    }


# =============================================================================
#  4. Classification evaluation
# =============================================================================

def evaluate_classification(
    encoder: SpatiotemporalEncoder,
    train_grid: np.ndarray,
    train_y: np.ndarray,
    test_grid: np.ndarray,
    test_y: np.ndarray,
    seed: int,
    batch_size: int = 64,
) -> dict:
    """
    Fit SimpleLogisticRegression on spatial_pooled_then_flat readout.
    Process feature extraction in chunks to avoid memory spike.
    """
    def extract_features(grid, batch_size):
        features = []
        for start in range(0, len(grid), batch_size):
            end = min(start + batch_size, len(grid))
            fwd = encoder.forward_with_intermediates(grid[start:end])
            feat = fwd["temporal_outputs"][-1].mean(axis=2).reshape(end - start, -1)
            features.append(feat)
        return np.concatenate(features, axis=0)

    tr = extract_features(train_grid, batch_size)
    te = extract_features(test_grid, batch_size)

    probe = SimpleLogisticRegression(
        n_classes=N_CLASSES,
        n_features=tr.shape[1],
        lr=0.1,
        max_iter=2000,
        seed=seed,
    )
    probe.fit(tr, train_y)

    train_acc = float(probe.score(tr, train_y))
    test_acc = float(probe.score(te, test_y))

    per_class = {}
    for cls in range(N_CLASSES):
        mask = test_y == cls
        per_class[f"class_{cls}_acc"] = float(probe.score(te[mask], test_y[mask])) if mask.sum() > 0 else 0.0

    return {
        "train_acc": train_acc,
        "test_acc": test_acc,
        **per_class,
    }


# =============================================================================
#  5. Single experiment runner
# =============================================================================

def run_single_experiment(args: tuple) -> dict:
    """
    args = (objective, seed, use_pooled_vicreg, epochs)

    objective: 'jepa' | 'sfa' | 'hebbian' | 'recon' | 'untrained'
    """
    objective, seed, use_pooled_vicreg, epochs = args

    rng = np.random.default_rng(seed)

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

    encoder = SpatiotemporalEncoder(
        variant="P3-C",
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=seed,
    )

    update_encoder = (objective != "untrained")

    # JEPA losses (only used by jepa objective)
    spatial_jepas = None
    temporal_jepas = None
    if objective == "jepa" and update_encoder:
        spatial_jepas = create_jepa_losses(encoder.n_spatial_layers, D_OUT, lr=LR)
        temporal_jepas = create_jepa_losses(encoder.n_temporal_layers, D_OUT, lr=LR)

    # Adam optimisers
    adam_spatial = None
    adam_temporal = None
    adam_decoder = None
    if update_encoder:
        params_enc = {
            "W_enc": encoder.master_spatial.W_enc,
            "b_enc": encoder.master_spatial.b_enc,
            "W_dec": encoder.master_spatial.W_dec,
            "b_dec": encoder.master_spatial.b_dec,
        }
        adam_spatial = _Adam(params_enc, lr=LR)
        adam_temporal = adam_spatial  # P3-C: shared

        if objective == "recon":
            adam_decoder = _Adam(
                {"W_dec": encoder.master_spatial.W_dec,
                 "b_dec": encoder.master_spatial.b_dec},
                lr=LR,
            )

    # Training
    t0 = time.time()
    if objective != "untrained":
        for epoch in range(epochs):
            metrics = train_epoch(
                encoder,
                train_grid,
                BATCH_SIZE,
                rng,
                objective=objective,
                adam_spatial=adam_spatial if update_encoder else None,
                adam_temporal=adam_temporal if update_encoder else None,
                adam_decoder=adam_decoder if update_encoder else None,
                spatial_jepas=spatial_jepas,
                temporal_jepas=temporal_jepas,
                use_pooled_vicreg=use_pooled_vicreg,
            )
    else:
        # Untrained: skip training, compute a single forward pass for metrics
        fwd_sample = encoder.forward_with_intermediates(train_grid[:BATCH_SIZE])
        metrics = {
            "obj_loss": 0.0,
            "pooled_std": float(np.sqrt(fwd_sample["pooled"].var(axis=0, ddof=0).mean() + 1e-12)),
        }
    t1 = time.time()

    # Final pooled std from last epoch (avoids redundant full-dataset forward pass)
    final_pooled_std = metrics.get("pooled_std", 0.0)

    # Classification
    eval_res = evaluate_classification(encoder, train_grid, train_y,
                                       test_grid, test_y, seed=seed)

    return {
        "objective": objective,
        "seed": seed,
        "use_pooled_vicreg": use_pooled_vicreg,
        "train_acc": eval_res["train_acc"],
        "test_acc": eval_res["test_acc"],
        "class_0_acc": eval_res["class_0_acc"],
        "class_1_acc": eval_res["class_1_acc"],
        "class_2_acc": eval_res["class_2_acc"],
        "class_3_acc": eval_res["class_3_acc"],
        "final_loss": metrics["obj_loss"],
        "final_pooled_std": final_pooled_std,
        "training_time_sec": t1 - t0,
    }


# =============================================================================
#  6. CSV writer
# =============================================================================

FIELDNAMES = [
    "objective", "seed", "use_pooled_vicreg", "train_acc", "test_acc",
    "class_0_acc", "class_1_acc", "class_2_acc", "class_3_acc",
    "final_loss", "final_pooled_std", "training_time_sec",
]


def save_result(result: dict, csv_path: str) -> None:
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)


# =============================================================================
#  7. Main experiment orchestration
# =============================================================================

def load_existing_results(csv_path: str) -> set:
    """Load existing (objective, seed, use_pooled_vicreg) tuples from CSV."""
    existing = set()
    if not os.path.exists(csv_path):
        return existing
    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (
                    row["objective"],
                    int(row["seed"]),
                    row["use_pooled_vicreg"].lower() == "true",
                )
                existing.add(key)
    except Exception:
        pass
    return existing


def main(dry_run: bool = False, objectives: list[str] | None = None, skip_existing: bool = False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Determine which objectives to run
    selected_objectives = objectives if objectives else OBJECTIVES
    # Include untrained if no --objectives filter is given or explicitly part of selection
    include_untrained = (objectives is None) or ("untrained" in objectives)

    # Only delete CSV for a full run (no --objectives)
    if objectives is None and os.path.exists(RESULTS_CSV):
        os.remove(RESULTS_CSV)

    existing = load_existing_results(RESULTS_CSV) if skip_existing else set()

    # Build task list
    tasks = []
    task_labels = []
    for objective in selected_objectives:
        if objective not in OBJECTIVES:
            print(f"  Warning: unknown objective '{objective}', skipping.")
            continue
        for use_pv in [False, True]:
            if dry_run:
                seeds_to_use = [42]
                ep = 1
            else:
                seeds_to_use = SEEDS
                ep = EPOCHS
            for seed in seeds_to_use:
                key = (objective, seed, use_pv)
                if skip_existing and key in existing:
                    continue
                label = f"{objective.upper()}{'+' if use_pv else '-'}VICReg_seed{seed}"
                tasks.append((objective, seed, use_pv, ep))
                task_labels.append(label)

    # Untrained baseline
    if include_untrained:
        if dry_run:
            key = ("untrained", 42, False)
            if not (skip_existing and key in existing):
                tasks.append(("untrained", 42, False, 1))
                task_labels.append("UNTRAINED_seed42")
        else:
            for seed in SEEDS:
                key = ("untrained", seed, False)
                if not (skip_existing and key in existing):
                    tasks.append(("untrained", seed, False, EPOCHS))
                    task_labels.append(f"UNTRAINED_seed{seed}")

    total_tasks = len(tasks)
    mode = "DRY-RUN" if dry_run else "FULL RUN"
    print("=" * 70)
    print(f"  PHASE 4 — Objective Comparison — {mode}")
    print(f"  Tasks: {total_tasks}")
    print(f"  Epochs: {ep if dry_run else EPOCHS}, Batch: {BATCH_SIZE}, LR: {LR}")
    print(f"  Seeds: {SEEDS if not dry_run else [42]}")
    print("=" * 70)

    t_start = time.time()

    all_results = []
    for i, task in enumerate(tasks):
        result = run_single_experiment(task)
        all_results.append(result)
        save_result(result, RESULTS_CSV)
        gc.collect()
        if (i + 1) % 5 == 0 or i == total_tasks - 1:
            elapsed = time.time() - t_start
            print(f"    Completed {i+1}/{total_tasks} tasks ({elapsed:.1f}s elapsed)")

    t_end = time.time()

    print(f"\n  All runs completed in {t_end - t_start:.1f}s")
    print(f"  Results saved to {RESULTS_CSV}")

    # Quick summary
    print("\n  Summary (mean ± std test accuracy):")
    for objective in OBJECTIVES + ["untrained"]:
        for use_pv in ([False, True] if objective != "untrained" else [False]):
            rows = [r for r in all_results
                    if r["objective"] == objective and r["use_pooled_vicreg"] == use_pv]
            if rows:
                accs = [r["test_acc"] for r in rows]
                mean_acc = np.mean(accs)
                std_acc = np.std(accs, ddof=1 if len(accs) > 1 else 0)
                label = f"{objective.upper()}{'+VICReg' if use_pv else ''}"
                print(f"    {label:22s}: {mean_acc:.4f} ± {std_acc:.4f}")

    print("=" * 70)
    return all_results


# =============================================================================
#  8. Statistical analysis & report
# =============================================================================

def run_statistical_analysis(results: list[dict]) -> None:
    """Generate comprehensive markdown report."""
    try:
        from scipy import stats
    except ImportError:
        print("  scipy not available — skipping statistical tests.")
        stats = None

    # Organise results
    grouped: dict[tuple, list[dict]] = {}
    for r in results:
        key = (r["objective"], r["use_pooled_vicreg"])
        grouped.setdefault(key, []).append(r)

    # Untrained baseline
    untrained_rows = grouped.get(("untrained", False), [])
    untrained_accs = np.array([r["test_acc"] for r in untrained_rows])

    # ---- Summary table ----
    summary: dict[tuple, dict] = {}
    for key, rows in grouped.items():
        accs = np.array([r["test_acc"] for r in rows])
        times = np.array([r["training_time_sec"] for r in rows])
        stds = np.array([r["final_pooled_std"] for r in rows])
        summary[key] = {
            "mean_acc": float(accs.mean()),
            "std_acc": float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0,
            "mean_time": float(times.mean()),
            "mean_std": float(stds.mean()),
            "accs": accs,
            "rows": rows,
        }

    # ---- Paired t-tests vs untrained ----
    ttest_results: dict[tuple, dict] = {}
    if stats is not None and len(untrained_accs) > 0:
        for key, s in summary.items():
            if key[0] == "untrained":
                continue
            accs = s["accs"]
            # Pair by seed
            paired_untrained = []
            paired_obj = []
            for r in s["rows"]:
                for u in untrained_rows:
                    if r["seed"] == u["seed"]:
                        paired_obj.append(r["test_acc"])
                        paired_untrained.append(u["test_acc"])
                        break
            if len(paired_obj) > 1:
                t_stat, p_val = stats.ttest_rel(paired_obj, paired_untrained)
                gain = float(np.mean(paired_obj) - np.mean(paired_untrained))
                diff = np.array(paired_obj) - np.array(paired_untrained)
                cohens_d = float(diff.mean() / (diff.std(ddof=1) + 1e-12))
                ttest_results[key] = {
                    "gain": gain,
                    "t": t_stat,
                    "p": p_val,
                    "cohens_d": cohens_d,
                }

    # ---- Falsification criteria ----
    jepa_pv_key = ("jepa", True)
    jepa_mean = summary.get(jepa_pv_key, {}).get("mean_acc", 0.0)

    f1_triggered = jepa_mean < 0.55

    f2_triggered = False
    f2_obj = None
    for key, s in summary.items():
        if key[0] == "untrained":
            continue
        if s["mean_acc"] > jepa_mean + 0.03:
            f2_triggered = True
            f2_obj = key

    f3_results: dict[str, bool] = {}
    for obj in OBJECTIVES:
        with_key = summary.get((obj, True), {"mean_acc": 0.0})["mean_acc"]
        without_key = summary.get((obj, False), {"mean_acc": 0.0})["mean_acc"]
        f3_results[obj] = without_key >= with_key

    # ---- Build report ----
    lines = []
    lines.append("# Phase 4 — Training Objective Comparison Report")
    lines.append("")
    lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Config
    lines.append("## Experiment Configuration")
    lines.append("")
    lines.append(f"- **Architecture**: P3-C (d={D}, d_out={D_OUT})")
    lines.append(f"- **Encoder layers**: 3 spatial + 3 temporal")
    lines.append(f"- **Readout**: spatial_pooled_then_flat (26×16=416 dims)")
    lines.append(f"- **Train/test**: {N_TRAIN_PER_CLASS} / {N_TEST_PER_CLASS} per class")
    lines.append(f"- **Epochs**: {EPOCHS}, Batch size: {BATCH_SIZE}, LR: {LR}")
    lines.append(f"- **Alpha**: {ALPHA}")
    lines.append(f"- **Lambda Hebb**: {LAMBDA_HEBB}")
    lines.append(f"- **Lambda L1 (recon)**: {LAMBDA_L1}")
    lines.append(f"- **Seeds**: {SEEDS}")
    lines.append("")

    # Mathematical formulations
    lines.append("## Mathematical Formulations")
    lines.append("")
    lines.append("### 1. JEPA")
    lines.append("""
For each layer code `Z ∈ ℝ^{N×P×d}`:
- Prediction: `ẑ_{p+1} = W_pred·z_p + b_pred`
- `L_pred = ½·mean((ẑ_{p+1} − z_{p+1})²) + ½·mean((ẑ_p − z_p)²)`
- `L_var = mean_j max(0, 1 − σ_j(Z))`
- `L_cov = (1/d) Σ_{j≠k} C_{jk}²`
- `L_JEPA = L_pred + 25·L_var + 25·L_cov`
""")
    lines.append("### 2. SFA (Slow Feature Analysis)")
    lines.append("""
On final temporal output `z ∈ ℝ^{B×T×S×d}`:
- `L_slow = (1/(B·(T−1)·S·d)) Σ_{b,s,t≥1} ‖z_{b,t,s} − z_{b,t−1,s}‖²`
- With pooled VICReg: `L = L_slow + L_VICReg(z̄_pooled)` — standard gradient-based SFA (Lagrangian relaxation)
- Without VICReg: pure slowness (expected collapse to constant)
""")
    lines.append("### 3. Hebbian (Variance Maximisation)")
    lines.append("""
On ALL intermediate codes `Z ∈ ℝ^{M×d}`:
- `L_Hebb = −(λ_hebb/d) Σ_j Var(Z_j)`  where λ_hebb = 25.0
- Gradient: `∂L/∂Z = −(2·λ_hebb/(M·d))·(Z − μ_Z)`  (pushes Z away from mean)
- **Distinct from VICReg**: operates on ALL layers, MAXIMISES variance, has no decorrelation
""")
    lines.append("### 4. Reconstruction (Sparse AE)")
    lines.append("""
At every node: `x ∈ ℝ^{M×3d}`, `a = code ∈ ℝ^{M×d_out}`, `r = a·W_dec + b_dec`
- `L_recon = MSE(x, r) + λ_l1·mean(|a|)`  where λ_l1 = 0.01
- `∂L/∂a = (2/(M·D_in))(r−x)·W_dec^T + (λ_l1/(M·d_out))·sign(a)`
- Decoder updated separately (encoder.backward() leaves ∂L/∂W_dec = 0)
""")
    lines.append("### 5. Pooled VICReg (injected when enabled)")
    lines.append("""
On `z̄ ∈ ℝ^{B×d_out}` (mean-pooled from final temporal layer):
- `L_VICReg = 25·mean_j max(0, 1−σ_j) + (25/d)·Σ_{j≠k} C_{jk}²`
- Gradient expanded to (B, T_f, S_f, d_out) and added to `∂L/∂Z_{last}^{(t)}`
""")
    lines.append("")

    # Results table
    lines.append("## Results Summary")
    lines.append("")
    lines.append("| Objective | Pooled VICReg | Mean Test Acc | Std | Mean Pooled Std | Time (s) |")
    lines.append("|-----------|---------------|--------------:|----:|----------------:|---------:|")
    for obj in OBJECTIVES + ["untrained"]:
        for use_pv in ([False, True] if obj != "untrained" else [False]):
            s = summary.get((obj, use_pv))
            if s:
                pv_str = "Yes" if use_pv else "No"
                lines.append(
                    f"| {obj.upper():9s} | {pv_str:>13s} | {s['mean_acc']:.4f} | "
                    f"{s['std_acc']:.4f} | {s['mean_std']:.4f} | {s['mean_time']:.1f} |"
                )
    lines.append("")

    # VICReg ablation
    lines.append("## VICReg Ablation Analysis")
    lines.append("")
    lines.append("| Objective | With VICReg | Without VICReg | Δ |")
    lines.append("|-----------|------------:|---------------:|--:|")
    for obj in OBJECTIVES:
        with_acc = summary.get((obj, True), {}).get("mean_acc", 0.0)
        without_acc = summary.get((obj, False), {}).get("mean_acc", 0.0)
        delta = with_acc - without_acc
        lines.append(f"| {obj.upper():9s} | {with_acc:.4f} | {without_acc:.4f} | {delta:+.4f} |")
    lines.append("")

    # Statistical tests
    lines.append("## Statistical Tests vs Untrained Baseline")
    lines.append("")
    if ttest_results:
        lines.append("| Objective | VICReg | Gain (pp) | t-stat | p-value | Cohen's d |")
        lines.append("|-----------|--------|----------:|-------:|--------:|----------:|")
        for key, tr in ttest_results.items():
            obj, use_pv = key
            lines.append(
                f"| {obj.upper():9s} | {'Yes' if use_pv else 'No':>6s} | "
                f"{tr['gain']*100:>7.2f} | {tr['t']:>6.3f} | {tr['p']:>7.5f} | {tr['cohens_d']:>9.4f} |"
            )
    else:
        lines.append("No statistical tests available (scipy not installed or insufficient data).")
    lines.append("")

    # Falsification criteria
    lines.append("## Falsification Criteria Evaluation")
    lines.append("")
    lines.append("| Criterion | Description | Status | Detail |")
    lines.append("|-----------|-------------|--------|--------|")
    lines.append(
        f"| F1 | JEPA + VICReg < 55% | {'❌ TRIGGERED' if f1_triggered else '✅ PASS'} | "
        f"JEPA+VICReg = {jepa_mean*100:.2f}% |"
    )
    lines.append(
        f"| F2 | Another obj beats JEPA+VICReg by ≥3pp | {'❌ TRIGGERED' if f2_triggered else '✅ PASS'} | "
        f"{'by ' + f2_obj[0].upper() + ('+VICReg' if f2_obj[1] else '') if f2_triggered else 'No objective exceeded'} |"
    )
    for obj, triggered in f3_results.items():
        status = "❌ TRIGGERED" if triggered else "✅ PASS"
        lines.append(
            f"| F3 ({obj.upper()}) | {obj} w/o VICReg ≥ {obj} w/ VICReg | {status} | "
            f"{'Expected' if obj == 'recon' and triggered else 'Not expected' if triggered else 'OK'} |"
        )
    lines.append("")

    # Per-class accuracy
    lines.append("## Per-Class Accuracy")
    lines.append("")
    lines.append("| Objective | VICReg | Class 0 | Class 1 | Class 2 | Class 3 |")
    lines.append("|-----------|--------|---------|---------|---------|---------|")
    for obj in OBJECTIVES + ["untrained"]:
        for use_pv in ([False, True] if obj != "untrained" else [False]):
            rows = grouped.get((obj, use_pv), [])
            if rows:
                c0 = np.mean([r["class_0_acc"] for r in rows])
                c1 = np.mean([r["class_1_acc"] for r in rows])
                c2 = np.mean([r["class_2_acc"] for r in rows])
                c3 = np.mean([r["class_3_acc"] for r in rows])
                pv_str = "Yes" if use_pv else "No"
                lines.append(
                    f"| {obj.upper():9s} | {pv_str:>6s} | {c0:.4f} | {c1:.4f} | {c2:.4f} | {c3:.4f} |"
                )
    lines.append("")

    # Training stability
    lines.append("## Training Stability Observations")
    lines.append("")
    for obj in OBJECTIVES:
        for use_pv in [False, True]:
            rows = grouped.get((obj, use_pv), [])
            if rows:
                losses = [r["final_loss"] for r in rows]
                mean_loss = np.mean(losses)
                std_loss = np.std(losses, ddof=1) if len(losses) > 1 else 0.0
                label = f"{obj.upper()}{'+VICReg' if use_pv else ''}"
                lines.append(f"- **{label}**: final loss = {mean_loss:.4f} ± {std_loss:.4f}")
    lines.append("")

    # Compute cost
    lines.append("## Compute Cost")
    lines.append("")
    for obj in OBJECTIVES + ["untrained"]:
        for use_pv in ([False, True] if obj != "untrained" else [False]):
            s = summary.get((obj, use_pv))
            if s:
                label = f"{obj.upper()}{'+VICReg' if use_pv else ''}"
                lines.append(f"- **{label}**: {s['mean_time']:.1f}s per run ({EPOCHS} epochs)")
    lines.append("")

    # Manager's directives
    lines.append("## Manager's Directives Addressed")
    lines.append("")
    lines.append("### 1. Reconstruction without VICReg")
    recon_no = summary.get(("recon", False), {}).get("mean_acc", 0.0)
    recon_yes = summary.get(("recon", True), {}).get("mean_acc", 0.0)
    lines.append(f"- Reconstruction without VICReg: **{recon_no*100:.2f}%**")
    lines.append(f"- Reconstruction with VICReg: **{recon_yes*100:.2f}%**")
    lines.append(f"- Δ = {((recon_yes - recon_no) * 100):+.2f}pp")
    if recon_no >= recon_yes:
        lines.append("- ✅ **Manager's prediction confirmed**: reconstruction natively resists collapse; adding pooled VICReg provides no benefit (or hurts).")
    else:
        lines.append("- ⚠️ Pooled VICReg improved reconstruction — the anti-collapse property of the decoder was not decisive in this setting.")
    lines.append("")

    lines.append("### 2. SFA + VICReg as Standard Gradient SFA")
    lines.append("- SFA without pooled VICReg enforces only slowness, which has a trivial constant solution.")
    lines.append("- SFA WITH pooled VICReg adds variance and covariance constraints via the Lagrangian relaxation L = L_slow + L_VICReg(z̄_pooled).")
    lines.append("- This is precisely the gradient-based SFA formulation documented in the machine-learning literature.")
    sfa_no = summary.get(("sfa", False), {}).get("mean_acc", 0.0)
    sfa_yes = summary.get(("sfa", True), {}).get("mean_acc", 0.0)
    lines.append(f"- Empirical result: SFA w/o VICReg = {sfa_no*100:.2f}%, SFA + VICReg = {sfa_yes*100:.2f}%")
    lines.append("")

    lines.append("### 3. Hebbian Mathematical Definition")
    lines.append("- Our Hebbian objective is the gradient-based formulation of Oja's rule:")
    lines.append("  'L_Hebb = −(λ_hebb/d) Σ_j Var(code_j)' — maximise output variance.")
    lines.append("- This is DISTINCT from VICReg because:")
    lines.append("  1. It operates on **ALL intermediate codes**, not only the pooled code.")
    lines.append("  2. It **maximises variance** (opposite sign from VICReg's variance lower-bound).")
    lines.append("  3. Without decorrelation, it produces **redundant (aligned) codes**.")
    lines.append("")

    # Recommendation
    all_means = {key: s["mean_acc"] for key, s in summary.items() if key[0] != "untrained"}
    if all_means:
        best_key = max(all_means, key=all_means.get)
        best_obj, best_pv = best_key
        lines.append("## Recommendation")
        lines.append("")
        lines.append(f"**Best performing objective: {best_obj.upper()}{' + Pooled VICReg' if best_pv else ''}**")
        lines.append(f"- Mean test accuracy: **{all_means[best_key]*100:.2f}%**")
        lines.append("")
        if best_obj == "jepa":
            lines.append("JEPA + pooled VICReg is the recommended default training objective for Phase 3/P3-C architecture.")
        else:
            lines.append(f"Note: {best_obj.upper()} outperformed the JEPA reference. Consider integrating its principle into the default recipe.")
    lines.append("")

    # Write report
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Report saved to {REPORT_MD}")


# =============================================================================
#  Entry point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Single seed, 1 epoch debug run")
    parser.add_argument("--objectives", nargs="+", default=None,
                        help="Subset of objectives to run (e.g. jepa sfa)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip combinations already present in results CSV")
    args = parser.parse_args()

    results = main(dry_run=args.dry_run, objectives=args.objectives, skip_existing=args.skip_existing)

    if not args.dry_run and args.objectives is None:
        run_statistical_analysis(results)
