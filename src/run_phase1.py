"""
Phase 1 Experiment Runner for HSUN.

Runs 7 configurations x 5 seeds = 35 total runs.
Saves metrics to phase_1/results.csv
"""

import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from eval_phase1 import evaluate_hierarchical_encoder


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]

CONFIGS = [
    {"name": "P1-A", "sharing_mode": "within_layer", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-B", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-C", "sharing_mode": "none", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-D", "sharing_mode": "cross_layer", "d": 4, "d_out": 4, "train": True},
    {"name": "P1-E", "sharing_mode": "cross_layer", "d": 8, "d_out": 16, "train": True},
    {"name": "Untrained-P1-B", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": False},
    {"name": "P1-B-kwta", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": True, "kwta_k": 4},
]

OUTPUT_DIR = "phase_1"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "results.csv")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = []
    total_runs = len(CONFIGS) * len(SEEDS)
    run_idx = 0

    print("=" * 70)
    print("  Phase 1 Experiment Runner")
    print(f"  {len(CONFIGS)} configurations x {len(SEEDS)} seeds = {total_runs} runs")
    print("=" * 70)

    for cfg in CONFIGS:
        print(f"\n{'-' * 70}")
        print(f"  Configuration: {cfg['name']}")
        print(f"    sharing_mode={cfg['sharing_mode']}, d={cfg['d']}, d_out={cfg['d_out']}")
        print(f"    train={cfg['train']}")
        if "kwta_k" in cfg:
            print(f"    kwta_k={cfg['kwta_k']}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            run_idx += 1
            print(f"\n  [{run_idx}/{total_runs}]  seed={seed}  --  {cfg['name']}")

            # 1. Generate dataset
            dataset = generate_phase1_dataset(seed=seed)
            print(f"       Dataset: train={dataset['train_x'].shape}, test={dataset['test_x'].shape}")

            # 2. Instantiate encoder
            encoder_kwargs = {
                "n_input": 16,
                "d": cfg["d"],
                "n_layers": 3,
                "sharing_mode": cfg["sharing_mode"],
                "l1_lambda": 0.002,
                "seed": seed,
                "d_out": cfg["d_out"],
            }
            if "kwta_k" in cfg:
                encoder_kwargs["kwta_k"] = cfg["kwta_k"]

            encoder = HierarchicalEncoder(**encoder_kwargs)
            print(f"       Encoder: n_params={encoder.get_parameter_count()}")

            # 3. Train (if not untrained)
            if cfg["train"]:
                print(f"       Training (epochs_per_layer=100, lr=0.01, batch_size=32) ...")
                train_info = encoder.train(
                    dataset=dataset["train_x"],
                    epochs_per_layer=100,
                    lr=0.01,
                    batch_size=32,
                )
                final_loss = train_info["loss_history"][-1] if train_info["loss_history"] else float("nan")
                print(f"       Training done. Final loss: {final_loss:.6f}")
            else:
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
                "recon_mse_l0": results["recon_mse_per_layer"][0],
                "recon_mse_l1": results["recon_mse_per_layer"][1],
                "recon_mse_l2": results["recon_mse_per_layer"][2],
                "n_params": results["n_params"],
            }
            all_results.append(row)

            print(f"       Results:")
            print(f"         test_accuracy  = {row['test_accuracy']:.4f}")
            print(f"         train_accuracy = {row['train_accuracy']:.4f}")
            print(f"         sparsity       = {row['sparsity']:.4f}")
            print(f"         recon_mse      = L0={row['recon_mse_l0']:.6f}, L1={row['recon_mse_l1']:.6f}, L2={row['recon_mse_l2']:.6f}")

    # -----------------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------------
    fieldnames = [
        "config", "seed", "test_accuracy", "train_accuracy",
        "sparsity", "recon_mse_l0", "recon_mse_l1", "recon_mse_l2", "n_params",
    ]

    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 70)
    print(f"  All {total_runs} runs completed successfully!")
    print(f"  Results saved to: {RESULTS_CSV}")
    print("=" * 70)

    # Quick summary per config
    print("\n  Summary (mean ± std over seeds):")
    for cfg_name in [c["name"] for c in CONFIGS]:
        cfg_rows = [r for r in all_results if r["config"] == cfg_name]
        accs = [r["test_accuracy"] for r in cfg_rows]
        spas = [r["sparsity"] for r in cfg_rows]
        print(f"    {cfg_name:15s}: test_acc={np.mean(accs):.4f}±{np.std(accs):.4f}  "
              f"sparsity={np.mean(spas):.4f}±{np.std(spas):.4f}")


if __name__ == "__main__":
    main()
