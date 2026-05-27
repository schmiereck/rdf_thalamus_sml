"""
Phase 1 v2 Experimental Runner — Simultaneous training with objective functions.

Runs 7 configurations x 5 seeds = 35 total runs.
Saves metrics to phase_1/objectives_results.csv
"""

import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from eval_phase1 import evaluate_hierarchical_encoder
from training_objectives import _Adam, JEPALoss, ContrastiveLoss, SFALoss, HebbianLoss


SEEDS = [42, 43, 44, 45, 46]

CONFIGS = [
    {"name": "P1-B-JEPA-d8", "d": 8, "objective": "jepa"},
    {"name": "P1-B-Contrastive-d8", "d": 8, "objective": "contrastive"},
    {"name": "P1-B-SFA-d8", "d": 8, "objective": "sfa"},
    {"name": "P1-B-Hebbian-d8", "d": 8, "objective": "hebbian"},
    {"name": "P1-B-JEPA-d16", "d": 16, "objective": "jepa"},
    {"name": "Untrained-d8", "d": 8, "objective": None},
    {"name": "Untrained-d16", "d": 16, "objective": None},
]

OUTPUT_DIR = "phase_1"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "objectives_results.csv")
EPOCHS = 200
BATCH_SIZE = 64


def bit_flip_augment(batch_x, rng):
    """Apply 1-2 random bit-flips per sample."""
    batch_x_aug = batch_x.copy()
    B = batch_x_aug.shape[0]
    for i in range(B):
        n_flips = rng.integers(1, 3)  # 1 or 2 flips
        flip_positions = rng.choice(batch_x_aug.shape[1], size=n_flips, replace=False)
        batch_x_aug[i, flip_positions] = 1.0 - batch_x_aug[i, flip_positions]
    return batch_x_aug


def train_encoder(encoder, objective, dataset, seed):
    """Train encoder with the specified objective."""
    rng = np.random.default_rng(seed)
    x_train = dataset["train_x"]
    n_samples = x_train.shape[0]

    # Setup simultaneous weight sharing
    if encoder.sharing_mode == "cross_layer":
        master = encoder.layer_nodes[0]
        for l in range(1, encoder.n_layers):
            encoder.layer_nodes[l] = master

    # Setup objective module
    if objective == "jepa":
        loss_module = JEPALoss(n_layers=encoder.n_layers, d=encoder.d_out, lr=1e-3)
    elif objective == "contrastive":
        loss_module = ContrastiveLoss(d=encoder.d, temp=0.5, lr=1e-3)
    elif objective == "sfa":
        loss_module = SFALoss(delta_order=1, lambda_var=25.0)
    elif objective == "hebbian":
        loss_module = HebbianLoss(eta=1e-3)
    else:
        raise ValueError(f"Unknown objective: {objective}")

    # Setup Adam for encoder params (master node + embedding)
    if objective in ("jepa", "contrastive", "sfa"):
        encoder_params = {
            "W_enc": master.W_enc,
            "b_enc": master.b_enc,
            "embedding": encoder.embedding,
        }
        encoder_adam = _Adam(encoder_params, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8)

    for epoch in range(EPOCHS):
        perm = rng.permutation(n_samples)
        epoch_loss = 0.0
        n_batches = 0

        for start in range(0, n_samples, BATCH_SIZE):
            end = min(start + BATCH_SIZE, n_samples)
            batch_idx = perm[start:end]
            batch_x = x_train[batch_idx]
            B = batch_x.shape[0]

            if objective == "contrastive":
                # 1. Augment and stack
                batch_x_aug = bit_flip_augment(batch_x, rng)
                batch_x_stacked = np.concatenate([batch_x, batch_x_aug], axis=0)

                # 2. Forward pass
                fwd = encoder.forward_with_intermediates(batch_x_stacked)
                z = fwd["codes"]
                z1 = z[:B]
                z2 = z[B:]

                # 3. Contrastive loss + projector grads
                loss_res = loss_module.loss_and_grads(z1, z2)

                # 4. Update projector
                proj_params = {
                    "W1": loss_module.W1,
                    "b1": loss_module.b1,
                    "W2": loss_module.W2,
                    "b2": loss_module.b2,
                }
                proj_grads = {k: loss_res[k] for k in proj_params}
                loss_module.adam.step(proj_params, proj_grads)

                # 5. Backprop through encoder
                dL_dcodes = np.concatenate([loss_res["d_z1"], loss_res["d_z2"]], axis=0)
                grads = encoder.backward_from_code_grads(
                    dL_dcodes, fwd["codes"], fwd["node_inputs"], batch_x_stacked
                )
                epoch_loss += loss_res["loss"]

            elif objective == "jepa":
                # 1. Forward pass
                fwd = encoder.forward_with_intermediates(batch_x)
                codes = fwd["all_codes_3d"]

                # 2. JEPA loss + predictor update
                loss_res = loss_module.step(codes)

                # 3. Backprop through encoder
                grads = encoder.backward_from_code_grads(
                    loss_res["code_grads"], fwd["codes"], fwd["node_inputs"], batch_x
                )
                epoch_loss += loss_res["loss"]

            elif objective == "sfa":
                # 1. Forward pass
                fwd = encoder.forward_with_intermediates(batch_x)
                codes = fwd["all_codes_3d"]

                # 2. Layer-wise SFA loss and gradients
                dL_dcodes = []
                total_loss = 0.0
                for l in range(encoder.n_layers):
                    sfa_res = loss_module.forward(codes[l])
                    dL_dcodes.append(sfa_res["dL_dz"])
                    total_loss += sfa_res["loss"]

                # 3. Backprop through encoder
                grads = encoder.backward_from_code_grads(
                    dL_dcodes, fwd["codes"], fwd["node_inputs"], batch_x
                )
                epoch_loss += total_loss / encoder.n_layers

            elif objective == "hebbian":
                # Hebbian updates weights directly; no backprop
                loss_module.update(encoder, batch_x)
                continue  # Skip Adam update

            # Average parameter gradients across all layers and update master node
            if objective in ("jepa", "contrastive", "sfa"):
                dW_enc_accum = np.zeros_like(master.W_enc)
                db_enc_accum = np.zeros_like(master.b_enc)
                for l in range(encoder.n_layers):
                    dW_enc_accum += grads["dL_dnodes"][l]["W_enc"]
                    db_enc_accum += grads["dL_dnodes"][l]["b_enc"]
                dW_enc_accum /= encoder.n_layers
                db_enc_accum /= encoder.n_layers

                grad_dict = {
                    "W_enc": dW_enc_accum,
                    "b_enc": db_enc_accum,
                    "embedding": grads["dL_dembedding"],
                }
                encoder_adam.step(encoder_params, grad_dict)

            n_batches += 1

        if n_batches > 0:
            epoch_loss /= n_batches

        if (epoch + 1) % 20 == 0 or epoch == 0:
            print(f"       Epoch {epoch + 1}/{EPOCHS}, loss={epoch_loss:.6f}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = []
    total_runs = len(CONFIGS) * len(SEEDS)
    run_idx = 0

    print("=" * 70)
    print("  Phase 1 v2 Experiment Runner")
    print(f"  {len(CONFIGS)} configurations x {len(SEEDS)} seeds = {total_runs} runs")
    print("=" * 70)

    for cfg in CONFIGS:
        print(f"\n{'-' * 70}")
        print(f"  Configuration: {cfg['name']}")
        print(f"    d={cfg['d']}, objective={cfg['objective']}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}  --  {cfg['name']}")

            # 1. Generate dataset
            dataset = generate_phase1_dataset(seed=seed)
            print(f"       Dataset: train={dataset['train_x'].shape}, test={dataset['test_x'].shape}")

            # 2. Instantiate encoder
            encoder = HierarchicalEncoder(
                n_input=16,
                d=cfg["d"],
                n_layers=3,
                sharing_mode="cross_layer",
                l1_lambda=0.0,       # No L1 penalty
                seed=seed,
                d_out=cfg["d"],      # d_out = d
                kwta_k=None,         # No k-WTA
            )
            print(f"       Encoder: n_params={encoder.get_parameter_count()}")

            # 3. Train (if not untrained)
            if cfg["objective"] is not None:
                t0 = time.time()
                train_encoder(encoder, cfg["objective"], dataset, seed)
                print(f"       Training done in {time.time() - t0:.1f}s")
            else:
                # Setup weight sharing for untrained baselines too
                if encoder.sharing_mode == "cross_layer":
                    master = encoder.layer_nodes[0]
                    for l in range(1, encoder.n_layers):
                        encoder.layer_nodes[l] = master
                print(f"       Skipping training (untrained baseline).")

            # 4. Evaluate
            results = evaluate_hierarchical_encoder(encoder, dataset, seed=seed)

            # 5. Store metrics
            row = {
                "config": cfg["name"],
                "seed": seed,
                "test_accuracy": results["test_accuracy"],
                "train_accuracy": results["train_accuracy"],
                "sparsity": results["sparsity"],
                "n_params": results["n_params"],
            }
            all_results.append(row)

            print(f"       Results:")
            print(f"         test_accuracy  = {row['test_accuracy']:.4f}")
            print(f"         train_accuracy = {row['train_accuracy']:.4f}")
            print(f"         sparsity       = {row['sparsity']:.4f}")
            print(f"         n_params       = {row['n_params']}")

    # -----------------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------------
    fieldnames = [
        "config", "seed", "test_accuracy", "train_accuracy", "sparsity", "n_params"
    ]

    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 70)
    print(f"  All {total_runs} runs completed successfully!")
    print(f"  Results saved to: {RESULTS_CSV}")
    print("=" * 70)

    # Summary table
    print("\n  Summary (mean ± std over seeds):")
    print(f"  {'Config':<25s} {'Test Acc':>12s} {'Train Acc':>12s} {'Sparsity':>10s}")
    print("  " + "-" * 65)
    for cfg_name in [c["name"] for c in CONFIGS]:
        cfg_rows = [r for r in all_results if r["config"] == cfg_name]
        test_accs = [r["test_accuracy"] for r in cfg_rows]
        train_accs = [r["train_accuracy"] for r in cfg_rows]
        spas = [r["sparsity"] for r in cfg_rows]
        print(
            f"  {cfg_name:<25s} "
            f"{np.mean(test_accs):.4f}±{np.std(test_accs):.4f}  "
            f"{np.mean(train_accs):.4f}±{np.std(train_accs):.4f}  "
            f"{np.mean(spas):.4f}±{np.std(spas):.4f}"
        )


if __name__ == "__main__":
    main()
