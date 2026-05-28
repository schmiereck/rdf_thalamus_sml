"""
Phase 3 Variance Diagnostic + Pooling Comparison

Trains P3-C, measures per-epoch variance at every layer,
compares untrained baseline, and evaluates 4 pooling strategies
for downstream classification.
"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import numpy as np
import csv
import time

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
    train_jepa_epoch,
)

# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------
SEED = 42
D = 16
D_OUT = 16
N_EPOCHS = 30
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100
BATCH_SIZE = 64
LR = 1e-3
ALPHA = 0.5  # joint training for P3-C


def compute_mean_per_dim_std(arr: np.ndarray) -> float:
    """Flatten all but last axis, compute std per dim, return mean std."""
    arr_2d = arr.reshape(-1, arr.shape[-1])
    # ddof=0 to match population variance used by VICReg internally
    stds = np.sqrt(arr_2d.var(axis=0, ddof=0) + 1e-12)
    return float(np.mean(stds))


def compute_all_variance_metrics(fwd: dict) -> dict:
    """Compute mean per-dim std for pooled, each spatial layer, each temporal layer."""
    metrics = {}
    metrics["mean_pooled_std"] = compute_mean_per_dim_std(fwd["pooled"])
    for l in range(3):
        metrics[f"mean_spatial_l{l}_std"] = compute_mean_per_dim_std(
            fwd["spatial_outputs"][l]
        )
    for l in range(3):
        metrics[f"mean_temporal_l{l}_std"] = compute_mean_per_dim_std(
            fwd["temporal_outputs"][l]
        )
    return metrics


def fit_pca(X_train: np.ndarray, n_components: int):
    """
    Simple numpy PCA: center data, compute covariance, take top-n_components
    eigenvectors of the covariance matrix.
    """
    mean = X_train.mean(axis=0)
    Xc = X_train - mean
    # Covariance matrix: (D, D)
    cov = (Xc.T @ Xc) / max(1, Xc.shape[0] - 1)
    eigvals, eigvecs = np.linalg.eigh(cov)
    # Sort descending
    idx = np.argsort(eigvals)[::-1]
    eigvecs = eigvecs[:, idx]
    components = eigvecs[:, :n_components]
    return components, mean


def transform_pca(X: np.ndarray, components: np.ndarray, mean: np.ndarray) -> np.ndarray:
    return (X - mean) @ components


def evaluate_classifier(
    X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, seed: int = SEED
) -> tuple[float, float]:
    """Fit SimpleLogisticRegression and return train_acc, test_acc."""
    probe = SimpleLogisticRegression(
        n_classes=N_CLASSES,
        n_features=X_train.shape[1],
        lr=0.1,
        max_iter=2000,
        seed=seed,
    )
    probe.fit(X_train, y_train)
    train_acc = float(probe.score(X_train, y_train))
    test_acc = float(probe.score(X_test, y_test))
    return train_acc, test_acc


def main():
    rng = np.random.default_rng(SEED)

    # -----------------------------------------------------------------------
    #  Dataset
    # -----------------------------------------------------------------------
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=SEED,
    )
    train_grid = ds["train_grid"]  # (n_train, 16, 32)
    train_y = ds["train_y"]
    test_grid = ds["test_grid"]    # (n_test, 16, 32)
    test_y = ds["test_y"]

    n_train = train_grid.shape[0]
    n_test = test_grid.shape[0]
    print(f"Dataset loaded: train={n_train}, test={n_test}")

    # -----------------------------------------------------------------------
    #  Part A: Train P3-C and measure per-epoch variance
    # -----------------------------------------------------------------------
    encoder = SpatiotemporalEncoder(
        variant="P3-C",
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=SEED,
    )

    spatial_jepas = create_jepa_losses(encoder.n_spatial_layers, D_OUT, lr=LR)
    temporal_jepas = create_jepa_losses(encoder.n_temporal_layers, D_OUT, lr=LR)

    adam_spatial = _Adam(
        {
            "W_enc": encoder.master_spatial.W_enc,
            "b_enc": encoder.master_spatial.b_enc,
            "W_dec": encoder.master_spatial.W_dec,
            "b_dec": encoder.master_spatial.b_dec,
        },
        lr=LR,
    )
    # P3-C shares one master node; reuse the same Adam
    adam_temporal = adam_spatial

    epoch_records: list[dict] = []

    # --- Epoch 0 (before any training) ---
    fwd_test = encoder.forward_with_intermediates(test_grid)
    var_metrics = compute_all_variance_metrics(fwd_test)

    # Classification at epoch 0
    fwd_train = encoder.forward_with_intermediates(train_grid)
    train_acc_0, test_acc_0 = evaluate_classifier(
        fwd_train["pooled"], train_y, fwd_test["pooled"], test_y
    )

    record = {
        "epoch": 0,
        "mean_pooled_std": var_metrics["mean_pooled_std"],
        "mean_spatial_l0_std": var_metrics["mean_spatial_l0_std"],
        "mean_spatial_l1_std": var_metrics["mean_spatial_l1_std"],
        "mean_spatial_l2_std": var_metrics["mean_spatial_l2_std"],
        "mean_temporal_l0_std": var_metrics["mean_temporal_l0_std"],
        "mean_temporal_l1_std": var_metrics["mean_temporal_l1_std"],
        "mean_temporal_l2_std": var_metrics["mean_temporal_l2_std"],
        "spatial_loss": 0.0,
        "temporal_loss": 0.0,
        "train_acc": train_acc_0,
        "test_acc": test_acc_0,
    }
    epoch_records.append(record)
    print(
        f"Epoch 0 (init): pooled_std={var_metrics['mean_pooled_std']:.4f} "
        f"train_acc={train_acc_0:.4f} test_acc={test_acc_0:.4f}"
    )

    # --- Training loop ---
    t0 = time.time()
    for epoch in range(1, N_EPOCHS + 1):
        loss_metrics = train_jepa_epoch(
            encoder,
            spatial_jepas,
            temporal_jepas,
            train_grid,
            BATCH_SIZE,
            rng,
            alpha=ALPHA,
            adam_spatial=adam_spatial,
            adam_temporal=adam_temporal,
            adam_embedding=None,
        )

        # Variance on test set
        fwd_test = encoder.forward_with_intermediates(test_grid)
        var_metrics = compute_all_variance_metrics(fwd_test)

        # Classification on pooled representation
        fwd_train = encoder.forward_with_intermediates(train_grid)
        train_acc, test_acc = evaluate_classifier(
            fwd_train["pooled"], train_y, fwd_test["pooled"], test_y
        )

        record = {
            "epoch": epoch,
            "mean_pooled_std": var_metrics["mean_pooled_std"],
            "mean_spatial_l0_std": var_metrics["mean_spatial_l0_std"],
            "mean_spatial_l1_std": var_metrics["mean_spatial_l1_std"],
            "mean_spatial_l2_std": var_metrics["mean_spatial_l2_std"],
            "mean_temporal_l0_std": var_metrics["mean_temporal_l0_std"],
            "mean_temporal_l1_std": var_metrics["mean_temporal_l1_std"],
            "mean_temporal_l2_std": var_metrics["mean_temporal_l2_std"],
            "spatial_loss": loss_metrics["spatial_loss"],
            "temporal_loss": loss_metrics["temporal_loss"],
            "train_acc": train_acc,
            "test_acc": test_acc,
        }
        epoch_records.append(record)

        if epoch % 5 == 0 or epoch == 1:
            print(
                f"Epoch {epoch:02d}: spatial_loss={loss_metrics['spatial_loss']:.4f} "
                f"temporal_loss={loss_metrics['temporal_loss']:.4f} "
                f"pooled_std={var_metrics['mean_pooled_std']:.4f} "
                f"test_acc={test_acc:.4f}"
            )

    t1 = time.time()
    print(f"\nTraining completed in {t1 - t0:.1f}s")

    # Save epoch-level CSV
    csv_path = os.path.join(os.path.dirname(__file__), "variance_diagnostic_results.csv")
    fieldnames = [
        "epoch",
        "mean_pooled_std",
        "mean_spatial_l0_std",
        "mean_spatial_l1_std",
        "mean_spatial_l2_std",
        "mean_temporal_l0_std",
        "mean_temporal_l1_std",
        "mean_temporal_l2_std",
        "spatial_loss",
        "temporal_loss",
        "train_acc",
        "test_acc",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(epoch_records)
    print(f"Saved variance diagnostic CSV to {csv_path}")

    # -----------------------------------------------------------------------
    #  Part B: Untrained baseline variance
    # -----------------------------------------------------------------------
    print("\n=== Part B: Untrained Baseline Variance ===")
    untrained_encoder = SpatiotemporalEncoder(
        variant="P3-C",
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=SEED,
    )
    fwd_untrained = untrained_encoder.forward_with_intermediates(test_grid)
    untrained_vars = compute_all_variance_metrics(fwd_untrained)
    for k, v in untrained_vars.items():
        label = k.replace("mean_", "").replace("_std", "")
        print(f"  {label:25s}: {v:.4f}")

    # -----------------------------------------------------------------------
    #  Part C: Pooling comparison (using the TRAINED encoder)
    # -----------------------------------------------------------------------
    print("\n=== Part C: Pooling Comparison ===")

    # Re-extract fresh forward passes from trained encoder
    fwd_train = encoder.forward_with_intermediates(train_grid)
    fwd_test = encoder.forward_with_intermediates(test_grid)

    pooling_results: list[dict] = []

    # 1. pooled (N, 16)
    X_tr = fwd_train["pooled"]
    X_te = fwd_test["pooled"]
    tr_acc, te_acc = evaluate_classifier(X_tr, train_y, X_te, test_y)
    pooling_results.append(
        {
            "representation": "pooled",
            "n_features": X_tr.shape[1],
            "train_acc": tr_acc,
            "test_acc": te_acc,
        }
    )
    print(
        f"pooled                    : n_features={X_tr.shape[1]:4d}  "
        f"train_acc={tr_acc:.4f}  test_acc={te_acc:.4f}"
    )

    # 2. temporal_flat -> PCA 100
    temp_last_tr = fwd_train["temporal_outputs"][-1]  # (B, 26, 10, 16)
    temp_last_te = fwd_test["temporal_outputs"][-1]
    X_tr_flat = temp_last_tr.reshape(temp_last_tr.shape[0], -1)
    X_te_flat = temp_last_te.reshape(temp_last_te.shape[0], -1)
    pca_components, pca_mean = fit_pca(X_tr_flat, 100)
    X_tr_pca = transform_pca(X_tr_flat, pca_components, pca_mean)
    X_te_pca = transform_pca(X_te_flat, pca_components, pca_mean)
    tr_acc, te_acc = evaluate_classifier(X_tr_pca, train_y, X_te_pca, test_y)
    pooling_results.append(
        {
            "representation": "temporal_flat_pca100",
            "n_features": X_tr_pca.shape[1],
            "train_acc": tr_acc,
            "test_acc": te_acc,
        }
    )
    print(
        f"temporal_flat_pca100      : n_features={X_tr_pca.shape[1]:4d}  "
        f"train_acc={tr_acc:.4f}  test_acc={te_acc:.4f}"
    )

    # 3. spatial_pooled_then_flat: mean over spatial axis → (B, 26, 16)
    spat_pool_tr = temp_last_tr.mean(axis=2)  # (B, 26, 16)
    spat_pool_te = temp_last_te.mean(axis=2)
    X_tr_sp = spat_pool_tr.reshape(spat_pool_tr.shape[0], -1)
    X_te_sp = spat_pool_te.reshape(spat_pool_te.shape[0], -1)
    tr_acc, te_acc = evaluate_classifier(X_tr_sp, train_y, X_te_sp, test_y)
    pooling_results.append(
        {
            "representation": "spatial_pooled_then_flat",
            "n_features": X_tr_sp.shape[1],
            "train_acc": tr_acc,
            "test_acc": te_acc,
        }
    )
    print(
        f"spatial_pooled_then_flat  : n_features={X_tr_sp.shape[1]:4d}  "
        f"train_acc={tr_acc:.4f}  test_acc={te_acc:.4f}"
    )

    # 4. temporal_pooled_then_flat: mean over temporal axis → (B, 10, 16)
    tmp_pool_tr = temp_last_tr.mean(axis=1)  # (B, 10, 16)
    tmp_pool_te = temp_last_te.mean(axis=1)
    X_tr_tp = tmp_pool_tr.reshape(tmp_pool_tr.shape[0], -1)
    X_te_tp = tmp_pool_te.reshape(tmp_pool_te.shape[0], -1)
    tr_acc, te_acc = evaluate_classifier(X_tr_tp, train_y, X_te_tp, test_y)
    pooling_results.append(
        {
            "representation": "temporal_pooled_then_flat",
            "n_features": X_tr_tp.shape[1],
            "train_acc": tr_acc,
            "test_acc": te_acc,
        }
    )
    print(
        f"temporal_pooled_then_flat : n_features={X_tr_tp.shape[1]:4d}  "
        f"train_acc={tr_acc:.4f}  test_acc={te_acc:.4f}"
    )

    # Save pooling comparison CSV
    pooling_csv_path = os.path.join(
        os.path.dirname(__file__), "pooling_comparison_results.csv"
    )
    with open(pooling_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["representation", "n_features", "train_acc", "test_acc"]
        )
        writer.writeheader()
        writer.writerows(pooling_results)
    print(f"Saved pooling comparison CSV to {pooling_csv_path}")

    # -----------------------------------------------------------------------
    #  Part D: Summary report
    # -----------------------------------------------------------------------
    write_report(untrained_vars, epoch_records, pooling_results)


def write_report(
    untrained_vars: dict, epoch_records: list[dict], pooling_results: list[dict]
):
    report_dir = os.path.join(os.path.dirname(__file__), "..", "phase_3")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "diagnostic_report.md")

    first = epoch_records[0]
    last = epoch_records[-1]

    with open(report_path, "w") as f:
        f.write("# Phase 3 Variance Diagnostic & Pooling Comparison Report\n\n")

        f.write("## Configuration\n\n")
        f.write(f"- **Variant**: P3-C (single shared master node)\n")
        f.write(f"- **Seed**: {SEED}\n")
        f.write(f"- **Dimensions**: d={D}, d_out={D_OUT}\n")
        f.write(
            f"- **Training**: {N_EPOCHS} epochs, "
            f"{N_TRAIN_PER_CLASS} train/class, {N_TEST_PER_CLASS} test/class, "
            f"batch={BATCH_SIZE}, lr={LR}\n"
        )
        f.write(f"- **JEPA alpha**: {ALPHA} (joint spatial + temporal)\n\n")

        f.write("## Part A/B: Per-Epoch Variance (Trained vs Untrained)\n\n")
        f.write("| Representation | Init (Epoch 0) | After 30 Epochs | Change |\n")
        f.write("|----------------|---------------|-----------------|--------|\n")
        keys = [
            "mean_pooled_std",
            "mean_spatial_l0_std",
            "mean_spatial_l1_std",
            "mean_spatial_l2_std",
            "mean_temporal_l0_std",
            "mean_temporal_l1_std",
            "mean_temporal_l2_std",
        ]
        labels = [
            "pooled",
            "spatial_l0",
            "spatial_l1",
            "spatial_l2",
            "temporal_l0",
            "temporal_l1",
            "temporal_l2",
        ]
        for key, label in zip(keys, labels):
            v0 = first[key]
            v30 = last[key]
            change = v30 - v0
            f.write(f"| {label:14s} | {v0:13.4f} | {v30:15.4f} | {change:+6.4f} |\n")
        f.write("\n")

        f.write("### Untrained Baseline (separate fresh init)\n\n")
        for key, label in zip(keys, labels):
            f.write(f"- **{label}**: {untrained_vars[key]:.4f}\n")
        f.write("\n")

        f.write("## Part C: Pooling Comparison\n\n")
        f.write("| Representation          | N Features | Train Acc | Test Acc |\n")
        f.write("|-------------------------|-----------:|----------:|---------:|\n")
        for r in pooling_results:
            f.write(
                f"| {r['representation']:23s} | {r['n_features']:10d} | "
                f"{r['train_acc']:9.4f} | {r['test_acc']:8.4f} |\n"
            )
        f.write("\n")

        f.write("## Key Findings & Interpretation\n\n")

        # VICReg check
        all_spatial_ok = all(last[f"mean_spatial_l{i}_std"] >= 1.0 for i in range(3))
        all_temporal_ok = all(last[f"mean_temporal_l{i}_std"] >= 1.0 for i in range(3))
        f.write("### 1. VICReg Variance Dynamics\n\n")
        if all_spatial_ok and all_temporal_ok:
            f.write(
                "All hidden layers (spatial and temporal) maintain per-dimension standard "
                "deviation **≥ 1.0** after 30 epochs of training. This confirms the VICReg "
                "variance term (λ_var = 25) is active and correctly forcing representational "
                "variance above the clipping threshold (eps = 1.0).\n\n"
            )
        else:
            f.write(
                "**Warning**: Some layers fell below std = 1.0 despite VICReg. This suggests "
                "the variance penalty may be insufficiently strong or is competing with other "
                "gradient components (e.g., JEPA prediction loss, L1, or the covariance term).\n\n"
            )

        pooled_v0 = first["mean_pooled_std"]
        pooled_v30 = last["mean_pooled_std"]
        f.write(
            f"- **Pooled representation**: std moved from **{pooled_v0:.4f}** at init "
            f"to **{pooled_v30:.4f}** after training.\n"
        )
        if pooled_v30 < 0.5:
            f.write(
                "  The pooled std is well below 1.0, indicating that **mean-pooling across "
                "all spatial and temporal positions collapses the representation diversity** "
                "that VICReg preserved at the layer level. This is a critical bottleneck:\n"
                "  the encoder learns rich hidden codes, but the pooling operation averages "
                "them away, leaving a near-constant vector that carries little class-discriminative "
                "information.\n\n"
            )
        else:
            f.write(
                "  Pooled std is moderate, so some variance survives pooling.\n\n"
            )

        # Layer-wise trajectory
        f.write("### 2. Layer-wise Variance Trajectory\n\n")
        for key, label in zip(keys, labels):
            v0 = first[key]
            v30 = last[key]
            trend = "increased" if v30 > v0 else "decreased"
            f.write(f"- **{label}**: {v0:.4f} → {v30:.4f} ({ trend })\n")
        f.write("\n")

        # Pooling comparison
        f.write("### 3. Alternative Pooling Strategies\n\n")
        best = max(pooling_results, key=lambda x: x["test_acc"])
        baseline_pooled = next(r for r in pooling_results if r["representation"] == "pooled")[
            "test_acc"
        ]
        f.write(
            f"The best-performing representation is **`{best['representation']}`** with a "
            f"test accuracy of **{best['test_acc']:.4f}** ({best['n_features']} features).\n\n"
        )
        if best["test_acc"] > baseline_pooled + 0.02:
            f.write(
                f"This is a **substantial improvement** over the default mean-pooled baseline "
                f"({baseline_pooled:.4f}), confirming that the standard pooling strategy destroys "
                "task-relevant structure.\n\n"
            )
        elif best["test_acc"] > baseline_pooled:
            f.write(
                f"This is a modest improvement over the default mean-pooled baseline "
                f"({baseline_pooled:.4f}).\n\n"
            )
        else:
            f.write(
                f"Surprisingly, no alternative pooling strategy outperformed the baseline "
                f"({baseline_pooled:.4f}), suggesting the collapse is deeper than just the pooling "
                f"operation itself.\n\n"
            )

        # Classification verdict
        final_test_acc = baseline_pooled
        f.write("### 4. Overall Classification Verdict\n\n")
        if final_test_acc <= 0.28:
            f.write(
                f"Final pooled test accuracy = **{final_test_acc:.4f}**, which is essentially "
                f"at chance (25% for 4-class). The encoder is not learning representations that "
                f"are useful for this classification task.\n\n"
            )
        elif final_test_acc <= 0.40:
            f.write(
                f"Final pooled test accuracy = **{final_test_acc:.4f}**, slightly above chance "
                f"but still poor. The ~42.85% untrained baseline from prior work is not being "
                f"reliably exceeded, confirming the Phase 3 plateau.\n\n"
            )
        elif final_test_acc <= 0.50:
            f.write(
                f"Final pooled test accuracy = **{final_test_acc:.4f}**. This barely exceeds "
                f"the previously reported untrained baseline (~42.85%) but remains weak for a "
                f"learned representation.\n\n"
            )
        else:
            f.write(
                f"Final pooled test accuracy = **{final_test_acc:.4f}**, which is a meaningful "
                f"improvement over the baseline.\n\n"
            )

        if final_test_acc < 0.50 and best["test_acc"] > baseline_pooled + 0.02:
            f.write(
                "**Diagnostic conclusion**: The encoder *is* learning structured hidden "
                "representations (VICReg variance is high, JEPA losses decrease), but the "
                "standard mean-pooling readout is the critical failure point. The best fix "
                "is to replace mean-pooling with a task-adaptive readout (e.g., the spatial- "
                "or temporal-pooling variants tested above, or a small learned MLP head on top "
                "of un-pooled features).\n"
            )
        elif final_test_acc < 0.50:
            f.write(
                "**Diagnostic conclusion**: Even alternative pooling strategies do not rescue "
                "performance, suggesting the encoder's learned features are either (a) not "
                "class-relevant at all, or (b) so entangled that simple linear probes cannot "
                "disentangle them. Consider: stronger task-specific inductive biases, deeper "
                "temporal models, or supervised fine-tuning of the encoder.\n"
            )

    print(f"Saved diagnostic report to {report_path}")


if __name__ == "__main__":
    main()
