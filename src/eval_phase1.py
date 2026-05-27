"""
HSUN Phase 1 — Evaluation module.

Evaluates a trained (or untrained) hierarchical encoder on the Phase-1
5-category classification task, measuring downstream accuracy, code
sparsity, and reconstruction fidelity.
"""

from __future__ import annotations

import sys
import os

# Ensure the project root is on sys.path so that ``src.*`` imports work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from src.harness import SimpleLogisticRegression


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_hierarchical_encoder(
    encoder,
    dataset: dict,
    seed: int = 42,
) -> dict:
    """
    Evaluate a trained hierarchical encoder.

    Parameters
    ----------
    encoder : HierarchicalEncoder
        A (possibly trained) hierarchical encoder instance.
    dataset : dict
        With keys ``'train_x'``, ``'train_y'``, ``'test_x'``, ``'test_y'``.
    seed : int
        Random seed for the logistic-regression probe.

    Returns
    -------
    dict containing:
        - ``'train_accuracy'``: float
        - ``'test_accuracy'``: float
        - ``'sparsity'``: float
          Average fraction of elements in *test* codes below 1e-3 in
          absolute magnitude.
        - ``'recon_mse_per_layer'``: list of 3 floats
          Reconstruction MSE of layer 0, 1, 2 on ``test_x``.
        - ``'n_params'``: int
          Total unique parameters in the encoder.
    """
    # -- Encode the raw inputs --
    train_codes = encoder.encode(dataset["train_x"])   # (n_train, n_features)
    test_codes = encoder.encode(dataset["test_x"])     # (n_test, n_features)

    # -- Linear probe (logistic regression) --
    probe = SimpleLogisticRegression(
        n_classes=5,
        n_features=train_codes.shape[1],
        lr=0.1,
        max_iter=500,
        seed=seed,
    )
    probe.fit(train_codes, dataset["train_y"])

    train_accuracy = float(probe.score(train_codes, dataset["train_y"]))
    test_accuracy = float(probe.score(test_codes, dataset["test_y"]))

    # -- Code sparsity on test set (threshold = 1e-3) --
    sparsity = float(np.mean(np.abs(test_codes) < 1e-3))

    # -- Reconstruction MSE per layer (on test_x) --
    recon_mse_per_layer = encoder.compute_reconstruction_mse(dataset["test_x"])

    # -- Parameter count --
    n_params = encoder.get_parameter_count()

    return {
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "sparsity": sparsity,
        "recon_mse_per_layer": recon_mse_per_layer,
        "n_params": n_params,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.dataset_phase1 import generate_phase1_dataset
    from src.hierarchical_encoder import HierarchicalEncoder

    print("=" * 60)
    print("  eval_phase1 -- Self-Test (untrained encoder baseline)")
    print("=" * 60)

    # Generate the Phase-1 dataset
    dataset = generate_phase1_dataset(n_train=200, n_test=100, seed=42)
    print(f"  Dataset: train_x={dataset['train_x'].shape}, "
          f"test_x={dataset['test_x'].shape}")

    # Instantiate an untrained encoder (control baseline)
    encoder = HierarchicalEncoder(
        n_input=16,
        d=8,
        n_layers=3,
        sharing_mode="cross_layer",
        l1_lambda=0.002,
        seed=42,
    )
    print(f"  Encoder: sharing_mode={encoder.sharing_mode}, "
          f"n_params={encoder.get_parameter_count()}")

    # Evaluate the untrained encoder
    results = evaluate_hierarchical_encoder(encoder, dataset, seed=42)

    print("\n  Results:")
    print(f"    train_accuracy       = {results['train_accuracy']:.4f}")
    print(f"    test_accuracy        = {results['test_accuracy']:.4f}")
    print(f"    sparsity             = {results['sparsity']:.4f}")
    print(f"    recon_mse_per_layer  = {[f'{m:.6f}' for m in results['recon_mse_per_layer']]}")
    print(f"    n_params             = {results['n_params']}")

    # Basic sanity checks
    assert 0.0 <= results["train_accuracy"] <= 1.0
    assert 0.0 <= results["test_accuracy"] <= 1.0
    assert 0.0 <= results["sparsity"] <= 1.0
    assert len(results["recon_mse_per_layer"]) == 3
    assert all(isinstance(m, float) for m in results["recon_mse_per_layer"])
    assert isinstance(results["n_params"], int)
    assert results["n_params"] > 0

    print("\n  ALL CHECKS PASSED")
    print("=" * 60)
