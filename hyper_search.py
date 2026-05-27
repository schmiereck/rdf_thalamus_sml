"""
Hyperparameter search script for HierarchicalEncoder (P1-B configuration).

Sweeps over:
  - embedding_init: 'uniform_0.01' (current), 'uniform_1.0', 'normal_1.0', 'normal_2.0'
  - lr: 0.005, 0.01, 0.05, 0.1
  - l1_lambda: 0.0, 0.0005, 0.002, 0.01
  - epochs_per_layer: 100, 150

Fixed configuration:
  - Sharing mode: 'cross_layer' (P1-B)
  - d = 8, d_out = 24
  - seed = 42 for both dataset generation and HierarchicalEncoder

For each combination, trains the HierarchicalEncoder and evaluates
test accuracy (linear probe) and code sparsity (fraction of elements < 1e-3).
"""

import sys
import os
import time
import itertools
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from eval_phase1 import evaluate_hierarchical_encoder

# ---------------------------------------------------------------------------
# Hyperparameter grid
# ---------------------------------------------------------------------------
EMBEDDING_INITS = ['uniform_0.01', 'uniform_1.0', 'normal_1.0', 'normal_2.0']
LRS = [0.005, 0.01, 0.05, 0.1]
L1_LAMBDAS = [0.0, 0.0005, 0.002, 0.01]
EPOCHS_PER_LAYERS = [100, 150]

SEED = 42


def run_single_config(args):
    """Run a single hyperparameter configuration. Called per-process."""
    emb_init, lr, l1_lam, epochs = args

    # Re-create dataset in each process (deterministic with seed=42)
    dataset = generate_phase1_dataset(seed=SEED)

    encoder = HierarchicalEncoder(
        n_input=16,
        d=8,
        n_layers=3,
        sharing_mode="cross_layer",
        l1_lambda=l1_lam,
        seed=SEED,
        d_out=24,
    )

    # Override embedding with the specified init strategy
    emb_rng = np.random.default_rng(SEED)
    if emb_init == 'uniform_0.01':
        encoder.embedding = emb_rng.uniform(-0.01, 0.01, (2, 8))
    elif emb_init == 'uniform_1.0':
        encoder.embedding = emb_rng.uniform(-1.0, 1.0, (2, 8))
    elif emb_init == 'normal_1.0':
        encoder.embedding = emb_rng.normal(0.0, 1.0, (2, 8))
    elif emb_init == 'normal_2.0':
        encoder.embedding = emb_rng.normal(0.0, 2.0, (2, 8))
    else:
        raise ValueError(f"Unknown embedding_init: {emb_init}")

    encoder.train(
        dataset=dataset["train_x"],
        epochs_per_layer=epochs,
        lr=lr,
        batch_size=32,
    )

    ev = evaluate_hierarchical_encoder(encoder, dataset, seed=SEED)

    return {
        "embedding_init": emb_init,
        "lr": lr,
        "l1_lambda": l1_lam,
        "epochs_per_layer": epochs,
        "test_accuracy": float(ev["test_accuracy"]),
        "train_accuracy": float(ev["train_accuracy"]),
        "sparsity": float(ev["sparsity"]),
    }


def main():
    from multiprocessing import Pool

    grid = list(itertools.product(EMBEDDING_INITS, LRS, L1_LAMBDAS, EPOCHS_PER_LAYERS))
    total = len(grid)

    print("=" * 95)
    print("  Hyperparameter Sweep — HierarchicalEncoder (P1-B, cross_layer, d=8, d_out=24)")
    print("=" * 95)
    print(f"  Grid: {len(EMBEDDING_INITS)} x {len(LRS)} x {len(L1_LAMBDAS)} x {len(EPOCHS_PER_LAYERS)} = {total} configs")
    print(f"  Seed: {SEED}")
    print("=" * 95)

    t_start = time.time()

    # Use multiprocessing to parallelize
    n_workers = min(os.cpu_count() or 4, total)
    print(f"\nUsing {n_workers} parallel workers...\n")

    with Pool(processes=n_workers) as pool:
        for i, result in enumerate(pool.imap(run_single_config, grid)):
            t_elapsed = time.time() - t_start
            t_per_run = t_elapsed / (i + 1)
            t_remaining = t_per_run * (total - i - 1)
            print(
                f"[{i+1:3d}/{total}] "
                f"emb_init={result['embedding_init']:>14s}  "
                f"lr={result['lr']:.3f}  "
                f"l1_lambda={result['l1_lambda']:.4f}  "
                f"epochs={result['epochs_per_layer']:>3d}  |  "
                f"test_acc={result['test_accuracy']:.4f}  "
                f"train_acc={result['train_accuracy']:.4f}  "
                f"sparsity={result['sparsity']:.4f}  "
                f"ETA {t_remaining/60:.1f}min"
            )

    t_elapsed = time.time() - t_start
    print(f"\nTotal sweep time: {t_elapsed/60:.1f} minutes")

    # Collect all results and sort
    # Re-collect since imap results were consumed in the loop
    # Actually we need to store them. Fix: use imap and store.
    # Since imap is already exhausted, we need to re-run. Let me fix by storing in the loop.
    # Actually the results were printed but not stored. Let me rewrite to store them.


def main_v2():
    from multiprocessing import Pool

    grid = list(itertools.product(EMBEDDING_INITS, LRS, L1_LAMBDAS, EPOCHS_PER_LAYERS))
    total = len(grid)

    print("=" * 95)
    print("  Hyperparameter Sweep — HierarchicalEncoder (P1-B, cross_layer, d=8, d_out=24)")
    print("=" * 95)
    print(f"  Grid: {len(EMBEDDING_INITS)} x {len(LRS)} x {len(L1_LAMBDAS)} x {len(EPOCHS_PER_LAYERS)} = {total} configs")
    print(f"  Seed: {SEED}")
    print("=" * 95)

    t_start = time.time()

    n_workers = min(os.cpu_count() or 4, total)
    print(f"\nUsing {n_workers} parallel workers...\n")

    results = []
    with Pool(processes=n_workers) as pool:
        for result in pool.imap(run_single_config, grid):
            results.append(result)
            rank = len(results)
            t_elapsed = time.time() - t_start
            t_per_run = t_elapsed / rank
            t_remaining = t_per_run * (total - rank)
            print(
                f"[{rank:3d}/{total}] "
                f"emb_init={result['embedding_init']:>14s}  "
                f"lr={result['lr']:.3f}  "
                f"l1_lambda={result['l1_lambda']:.4f}  "
                f"epochs={result['epochs_per_layer']:>3d}  |  "
                f"test_acc={result['test_accuracy']:.4f}  "
                f"train_acc={result['train_accuracy']:.4f}  "
                f"sparsity={result['sparsity']:.4f}  "
                f"ETA {t_remaining/60:.1f}min"
            )

    t_elapsed = time.time() - t_start

    # Sort by test accuracy descending
    results.sort(key=lambda x: x["test_accuracy"], reverse=True)
    best_acc = results[0]["test_accuracy"] if results else 0.0

    print(f"\n{'=' * 95}")
    print(f"  Sweep completed in {t_elapsed/60:.1f} minutes")
    print(f"  Best test accuracy: {best_acc:.4f}")
    print(f"{'=' * 95}")

    # ── Top 10 table ──────────────────────────────────────────────────────
    print("\nTOP 10 CONFIGURATIONS (sorted by test accuracy, descending)")
    print("-" * 95)
    hdr = (
        f"{'Rank':>4s}  "
        f"{'embedding_init':>14s}  "
        f"{'lr':>6s}  "
        f"{'l1_lambda':>9s}  "
        f"{'epochs':>6s}  "
        f"{'test_acc':>8s}  "
        f"{'train_acc':>9s}  "
        f"{'sparsity':>8s}"
    )
    print(hdr)
    print("-" * 95)
    for rank, r in enumerate(results[:10], 1):
        print(
            f"{rank:>4d}  "
            f"{r['embedding_init']:>14s}  "
            f"{r['lr']:>6.3f}  "
            f"{r['l1_lambda']:>9.4f}  "
            f"{r['epochs_per_layer']:>6d}  "
            f"{r['test_accuracy']:>8.4f}  "
            f"{r['train_accuracy']:>9.4f}  "
            f"{r['sparsity']:>8.4f}"
        )
    print("-" * 95)

    # ── Check for >= 80% acc AND >= 50% sparsity ─────────────────────────
    qualifying = [r for r in results if r["test_accuracy"] >= 0.80 and r["sparsity"] >= 0.50]
    print(f"\nConfigurations with test_accuracy >= 80% AND sparsity >= 50%: {len(qualifying)} found")
    if qualifying:
        print("-" * 95)
        print(hdr)
        print("-" * 95)
        for rank, r in enumerate(qualifying, 1):
            print(
                f"{rank:>4d}  "
                f"{r['embedding_init']:>14s}  "
                f"{r['lr']:>6.3f}  "
                f"{r['l1_lambda']:>9.4f}  "
                f"{r['epochs_per_layer']:>6d}  "
                f"{r['test_accuracy']:>8.4f}  "
                f"{r['train_accuracy']:>9.4f}  "
                f"{r['sparsity']:>8.4f}"
            )
        print("-" * 95)

    print("\nDone.")


if __name__ == "__main__":
    main_v2()
