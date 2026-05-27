"""
Phase 2 Baseline Experiment Runner for P2-A, P2-B, P2-C.

Trains each encoder type on temporal data with JEPA as the training objective.
Also runs untrained baselines (random weights, freeze encoder, only train JEPA).

Saves metrics to phase_2/baseline_results.csv
"""

import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from temporal_dataset import generate_temporal_dataset, generate_irregular_markov_dataset
from temporal_encoder import P2AEncoder, P2BEncoder, P2CEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression


# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]
D = 16
D_OUT = 16
TEMPORAL_LENGTH = 64
BATCH_SIZE = 32
TEMPORAL_EPOCHS = 200

OUTPUT_DIR = "phase_2"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "baseline_results.csv")


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def train_temporal_jepa(
    encoder,
    train_emb,
    epochs=TEMPORAL_EPOCHS,
    lr=1e-3,
    batch_size=BATCH_SIZE,
    seed=42,
    update_encoder=False,
):
    """Train JEPALoss on temporal sequences."""
    rng = np.random.default_rng(seed)
    jepa = JEPALoss(n_layers=1, d=encoder.d_out, lr=lr)

    # Set up Adam for encoder parameters if training encoder
    adam_enc = None
    if update_encoder:
        if isinstance(encoder, P2AEncoder):
            adam_enc = _Adam(
                {"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc},
                lr=lr,
            )
        elif isinstance(encoder, P2BEncoder):
            adam_enc = _Adam(
                {"W_xh": encoder.W_xh, "W_hh": encoder.W_hh, "b_h": encoder.b_h},
                lr=lr,
            )
        elif isinstance(encoder, P2CEncoder):
            adam_enc = _Adam(
                {
                    "W_enc": encoder.node.W_enc,
                    "b_enc": encoder.node.b_enc,
                    "W_proj": encoder.W_proj,
                },
                lr=lr,
            )

    n_samples = train_emb.shape[0]
    loss_history = []

    for epoch in range(epochs):
        perm = rng.permutation(n_samples)
        epoch_loss = 0.0
        n_batches = 0

        for start in range(0, n_samples, batch_size):
            end = min(start + batch_size, n_samples)
            batch = train_emb[perm[start:end]]

            codes = encoder.forward(batch)
            result = jepa.step([codes])
            epoch_loss += result["loss"]
            n_batches += 1

            if update_encoder:
                code_grads = result["code_grads"][0]
                enc_grads = encoder.compute_gradients(batch, code_grads)

                if isinstance(encoder, P2AEncoder):
                    adam_enc.step(
                        {"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc},
                        {"W_enc": enc_grads["W_enc"], "b_enc": enc_grads["b_enc"]},
                    )
                elif isinstance(encoder, P2BEncoder):
                    adam_enc.step(
                        {"W_xh": encoder.W_xh, "W_hh": encoder.W_hh, "b_h": encoder.b_h},
                        {
                            "W_xh": enc_grads["W_xh"],
                            "W_hh": enc_grads["W_hh"],
                            "b_h": enc_grads["b_h"],
                        },
                    )
                elif isinstance(encoder, P2CEncoder):
                    adam_enc.step(
                        {
                            "W_enc": encoder.node.W_enc,
                            "b_enc": encoder.node.b_enc,
                            "W_proj": encoder.W_proj,
                        },
                        {
                            "W_enc": enc_grads["W_enc"],
                            "b_enc": enc_grads["b_enc"],
                            "W_proj": enc_grads["W_proj"],
                        },
                    )

        loss_history.append(epoch_loss / max(n_batches, 1))
        if epoch % 50 == 0 or epoch == epochs - 1:
            print(f"    Epoch {epoch}: loss={loss_history[-1]:.4f}")

    return jepa, loss_history


def evaluate_classification(encoder, train_emb, train_y, test_emb, test_y, seed=42):
    """Evaluate classification accuracy using mean-pooled codes."""
    train_codes = encoder.forward(train_emb)
    test_codes = encoder.forward(test_emb)

    train_mean = train_codes.mean(axis=1)
    test_mean = test_codes.mean(axis=1)

    probe = SimpleLogisticRegression(
        n_classes=3, n_features=encoder.d_out, lr=0.1, max_iter=1000, seed=seed
    )
    probe.fit(train_mean, train_y)

    train_acc = float(probe.score(train_mean, train_y))
    test_acc = float(probe.score(test_mean, test_y))
    return train_acc, test_acc


def evaluate_next_step_prediction(encoder, train_emb, test_emb, ridge_lambda=1.0):
    """Evaluate next-step prediction via Ridge regression."""
    train_codes = encoder.forward(train_emb)
    test_codes = encoder.forward(test_emb)

    B_train, T, d_out = train_codes.shape
    d = train_emb.shape[2]

    X_train = train_codes[:, :-1, :].reshape(-1, d_out)
    y_train = train_emb[:, 1:, :].reshape(-1, d)

    X_test = test_codes[:, :-1, :].reshape(-1, d_out)
    y_test = test_emb[:, 1:, :].reshape(-1, d)

    XtX = X_train.T @ X_train + ridge_lambda * np.eye(d_out)
    Xty = X_train.T @ y_train
    W = np.linalg.solve(XtX, Xty)

    y_pred = X_test @ W

    norms_pred = np.linalg.norm(y_pred, axis=1)
    norms_true = np.linalg.norm(y_test, axis=1)
    cos_sim = np.sum(y_pred * y_test, axis=1) / (norms_pred * norms_true + 1e-12)

    return float(cos_sim.mean())


def create_encoder(encoder_type, d, d_out, seed):
    """Factory for creating encoders by type."""
    if encoder_type == "P2-A":
        return P2AEncoder(d=d, d_out=d_out, N=3, seed=seed, l1_lambda=0.0)
    elif encoder_type == "P2-B":
        return P2BEncoder(d=d, d_out=d_out, seed=seed)
    elif encoder_type == "P2-C":
        return P2CEncoder(d=d, d_out=d_out, seed=seed, l1_lambda=0.0)
    else:
        raise ValueError(f"Unknown encoder type: {encoder_type}")


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = []
    configs = [
        {"name": "P2-A-Trained", "encoder_type": "P2-A", "train_encoder": True},
        {"name": "P2-B-Trained", "encoder_type": "P2-B", "train_encoder": True},
        {"name": "P2-C-Trained", "encoder_type": "P2-C", "train_encoder": True},
        {"name": "P2-A-Untrained", "encoder_type": "P2-A", "train_encoder": False},
        {"name": "P2-B-Untrained", "encoder_type": "P2-B", "train_encoder": False},
        {"name": "P2-C-Untrained", "encoder_type": "P2-C", "train_encoder": False},
    ]
    total_runs = len(configs) * len(SEEDS)
    run_idx = 0

    print("=" * 70)
    print("  Phase 2 Baseline Experiment Runner (P2-A, P2-B, P2-C)")
    print(f"  {len(configs)} configurations x {len(SEEDS)} seeds = {total_runs} runs")
    print("=" * 70)

    for cfg in configs:
        print(f"\n{'-' * 70}")
        print(f"  Configuration: {cfg['name']}")
        print(f"    encoder_type={cfg['encoder_type']}, train_encoder={cfg['train_encoder']}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}  --  {cfg['name']}")

            # Generate datasets
            temporal_ds = generate_temporal_dataset(
                n_train_per_cat=200,
                n_test_per_cat=100,
                length=TEMPORAL_LENGTH,
                d=D,
                n_states=8,
                seed=seed,
            )
            markov_ds = generate_irregular_markov_dataset(
                n_train=200,
                n_test=100,
                length=TEMPORAL_LENGTH,
                d=D,
                n_states=8,
                seed=seed,
            )
            print(
                f"       Dataset: train={temporal_ds['train_emb'].shape}, "
                f"test={temporal_ds['test_emb'].shape}"
            )

            # Create encoder
            encoder = create_encoder(cfg["encoder_type"], D, D_OUT, seed)
            print(f"       Encoder: {cfg['encoder_type']}, d_out={encoder.d_out}")

            # Train JEPA
            print(f"       Training temporal JEPA ({TEMPORAL_EPOCHS} epochs)...")
            t0 = time.time()
            jepa, loss_history = train_temporal_jepa(
                encoder=encoder,
                train_emb=temporal_ds["train_emb"],
                epochs=TEMPORAL_EPOCHS,
                lr=1e-3,
                batch_size=BATCH_SIZE,
                seed=seed,
                update_encoder=cfg["train_encoder"],
            )
            t1 = time.time()
            print(f"       Training completed in {t1 - t0:.1f}s")
            print(f"       Final JEPA loss: {loss_history[-1]:.6f}")

            # Evaluate
            train_acc, test_acc = evaluate_classification(
                encoder,
                temporal_ds["train_emb"],
                temporal_ds["train_y"],
                temporal_ds["test_emb"],
                temporal_ds["test_y"],
                seed=seed,
            )
            next_step_cos = evaluate_next_step_prediction(
                encoder,
                markov_ds["train_emb"],
                markov_ds["test_emb"],
            )
            next_step_cos_cls = evaluate_next_step_prediction(
                encoder,
                temporal_ds["train_emb"],
                temporal_ds["test_emb"],
            )

            print(f"       Classification: train={train_acc:.4f}, test={test_acc:.4f}")
            print(f"       Next-step (Markov): cos={next_step_cos:.4f}")
            print(f"       Next-step (Class):  cos={next_step_cos_cls:.4f}")

            row = {
                "config": cfg["name"],
                "seed": seed,
                "test_accuracy": test_acc,
                "train_accuracy": train_acc,
                "next_step_cosine_markov": next_step_cos,
                "next_step_cosine_classification": next_step_cos_cls,
                "final_jepa_loss": loss_history[-1],
            }
            all_results.append(row)

    # Save CSV
    fieldnames = [
        "config",
        "seed",
        "test_accuracy",
        "train_accuracy",
        "next_step_cosine_markov",
        "next_step_cosine_classification",
        "final_jepa_loss",
    ]

    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 70)
    print(f"  All {total_runs} runs completed!")
    print(f"  Results saved to: {RESULTS_CSV}")
    print("=" * 70)

    print("\n  Summary (mean ± std):")
    for cfg_name in [c["name"] for c in configs]:
        cfg_rows = [r for r in all_results if r["config"] == cfg_name]
        accs = [r["test_accuracy"] for r in cfg_rows]
        cos_m = [r["next_step_cosine_markov"] for r in cfg_rows]
        cos_c = [r["next_step_cosine_classification"] for r in cfg_rows]
        losses = [r["final_jepa_loss"] for r in cfg_rows]
        print(
            f"    {cfg_name:20s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  "
            f"next_step_m={np.mean(cos_m):.4f}±{np.std(cos_m):.4f}  "
            f"next_step_c={np.mean(cos_c):.4f}±{np.std(cos_c):.4f}  "
            f"jepa_loss={np.mean(losses):.4f}±{np.std(losses):.4f}"
        )


if __name__ == "__main__":
    main()
