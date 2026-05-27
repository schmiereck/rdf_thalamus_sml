"""
test_scale.py -- Evaluate the effect of embedding initialization scale
on the performance of HierarchicalEncoder in Phase 1.

Tests 5 initialization methods:
  1. Uniform [-0.01, 0.01]  (current default)
  2. Uniform [-0.1,  0.1]
  3. Uniform [-1.0,  1.0]
  4. Standard normal (mean=0, std=1)
  5. Normal (mean=0, std=0.5)

For each: train for 50 epochs/layer, report test acc, train acc,
code sparsity (threshold 1e-3), avg code magnitude, and untrained baseline.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np

from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from harness import SimpleLogisticRegression


# ---------------------------------------------------------------------------
# Initialization methods
# ---------------------------------------------------------------------------

def init_uniform_01(rng, d):
    """Uniform in [-0.01, 0.01] -- current default."""
    return rng.uniform(-0.01, 0.01, (2, d))

def init_uniform_1(rng, d):
    """Uniform in [-0.1, 0.1]."""
    return rng.uniform(-0.1, 0.1, (2, d))

def init_uniform_10(rng, d):
    """Uniform in [-1.0, 1.0]."""
    return rng.uniform(-1.0, 1.0, (2, d))

def init_normal_std1(rng, d):
    """Standard normal (mean=0, std=1)."""
    return rng.standard_normal((2, d))

def init_normal_std05(rng, d):
    """Normal with std=0.5."""
    return rng.standard_normal((2, d)) * 0.5


INIT_METHODS = [
    ("Uniform [-0.01, 0.01]",   init_uniform_01),
    ("Uniform [-0.1,  0.1]",    init_uniform_1),
    ("Uniform [-1.0,  1.0]",    init_uniform_10),
    ("Normal(0, 1)",            init_normal_std1),
    ("Normal(0, 0.5)",          init_normal_std05),
]


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def linear_probe_accuracy(codes, labels):
    """Fit logistic regression and return accuracy on the SAME data."""
    n_classes = len(np.unique(labels))
    n_features = codes.shape[1]
    model = SimpleLogisticRegression(n_classes, n_features)
    model.fit(codes, labels)
    return float(model.score(codes, labels))


def evaluate_encoder(encoder, dataset, threshold=1e-3):
    """Evaluate a trained or untrained encoder on the dataset."""
    train_codes = encoder.encode(dataset["train_x"])
    test_codes  = encoder.encode(dataset["test_x"])

    # Linear probe accuracies
    train_acc = linear_probe_accuracy(train_codes, dataset["train_y"])
    test_acc  = linear_probe_accuracy(test_codes, dataset["test_y"])

    # Code sparsity on test set
    sparsity = float(np.mean(np.abs(test_codes) < threshold))

    # Average code magnitude on test set
    avg_magnitude = float(np.mean(np.abs(test_codes)))

    return {
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "sparsity": sparsity,
        "avg_code_magnitude": avg_magnitude,
    }


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main():
    # Fixed seed for fair comparison -- same dataset for all methods
    dataset = generate_phase1_dataset(n_train=200, n_test=100, seed=42)

    # Encoder config
    SHARING_MODE = "cross_layer"
    D = 8
    L1_LAMBDA = 0.002
    MASTER_SEED = 42
    EPOCHS_PER_LAYER = 50
    LR = 0.01
    BATCH_SIZE = 32

    total = len(INIT_METHODS) * 2  # trained + untrained
    run = 0

    print("=" * 85)
    print("  Embedding Initialization Scale Experiment -- Phase 1")
    print(f"  Config: sharing_mode='{SHARING_MODE}', d={D}, l1_lambda={L1_LAMBDA}, seed={MASTER_SEED}")
    print(f"  Training: {EPOCHS_PER_LAYER} epochs/layer, lr={LR}, batch_size={BATCH_SIZE}")
    print(f"  Dataset: train={dataset['train_x'].shape}, test={dataset['test_x'].shape}")
    print("=" * 85)

    rows = []

    for method_name, init_fn in INIT_METHODS:
        print(f"\n{'-' * 85}")
        print(f"  Method: {method_name}")
        print(f"{'-' * 85}")

        # -- Create a deterministic RNG for this method --
        rng = np.random.default_rng(MASTER_SEED)
        # Consume the same amount of RNG state for all methods by
        # drawing the embedding here, then re-init the encoder.
        # Actually, let's just override the embedding after creation.

        # ========== TRAINED ==========
        run += 1
        print(f"\n  [{run}/{total}] TRAINED  --  {method_name}")

        encoder = HierarchicalEncoder(
            n_input=16,
            d=D,
            n_layers=3,
            sharing_mode=SHARING_MODE,
            l1_lambda=L1_LAMBDA,
            seed=MASTER_SEED,
        )
        # Override embedding with the target initialization
        init_rng = np.random.default_rng(MASTER_SEED + 1234)
        encoder.embedding = init_fn(init_rng, D)

        train_info = encoder.train(
            dataset=dataset["train_x"],
            epochs_per_layer=EPOCHS_PER_LAYER,
            lr=LR,
            batch_size=BATCH_SIZE,
        )
        final_loss = train_info["loss_history"][-1]
        print(f"    Training done. Final loss: {final_loss:.6f}")

        results = evaluate_encoder(encoder, dataset)
        print(f"    test_accuracy        = {results['test_accuracy']:.4f}")
        print(f"    train_accuracy       = {results['train_accuracy']:.4f}")
        print(f"    sparsity (|c|<1e-3)  = {results['sparsity']:.4f}")
        print(f"    avg |code|           = {results['avg_code_magnitude']:.6f}")

        rows.append({
            "method": method_name,
            "mode": "trained",
            "test_accuracy": results["test_accuracy"],
            "train_accuracy": results["train_accuracy"],
            "sparsity": results["sparsity"],
            "avg_code_magnitude": results["avg_code_magnitude"],
            "final_loss": final_loss,
        })

        # ========== UNTRAINED BASELINE ==========
        run += 1
        print(f"\n  [{run}/{total}] UNTRAINED  --  {method_name}")

        encoder_untrained = HierarchicalEncoder(
            n_input=16,
            d=D,
            n_layers=3,
            sharing_mode=SHARING_MODE,
            l1_lambda=L1_LAMBDA,
            seed=MASTER_SEED,
        )
        # Use the SAME embedding as the trained version for fair comparison
        encoder_untrained.embedding = encoder.embedding.copy()

        results_untrained = evaluate_encoder(encoder_untrained, dataset)
        print(f"    test_accuracy        = {results_untrained['test_accuracy']:.4f}")
        print(f"    train_accuracy       = {results_untrained['train_accuracy']:.4f}")
        print(f"    sparsity (|c|<1e-3)  = {results_untrained['sparsity']:.4f}")
        print(f"    avg |code|           = {results_untrained['avg_code_magnitude']:.6f}")

        rows.append({
            "method": method_name,
            "mode": "untrained",
            "test_accuracy": results_untrained["test_accuracy"],
            "train_accuracy": results_untrained["train_accuracy"],
            "sparsity": results_untrained["sparsity"],
            "avg_code_magnitude": results_untrained["avg_code_magnitude"],
            "final_loss": float("nan"),
        })

    # -----------------------------------------------------------------------
    # Print comparison table
    # -----------------------------------------------------------------------
    print("\n\n" + "=" * 110)
    print("  EMBEDDING INITIALIZATION SCALE -- COMPARISON TABLE")
    print("=" * 110)

    header = (
        f"{'Method':<25s} {'Mode':<12s} "
        f"{'Test Acc':>9s} {'Train Acc':>10s} "
        f"{'Sparsity':>10s} {'Avg |Code|':>12s} {'Loss':>12s}"
    )
    print(header)
    print("-" * 110)

    for r in rows:
        loss_str = f"{r['final_loss']:.6f}" if not np.isnan(r['final_loss']) else "    --     "
        print(
            f"{r['method']:<25s} {r['mode']:<12s} "
            f"{r['test_accuracy']:>9.4f} {r['train_accuracy']:>10.4f} "
            f"{r['sparsity']:>10.4f} {r['avg_code_magnitude']:>12.6f} {loss_str:>12s}"
        )

    print("=" * 110)

    # -----------------------------------------------------------------------
    # Trained-only summary table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 110)
    print("  TRAINED ENCODERS ONLY -- QUICK LOOKUP")
    print("=" * 110)

    header2 = (
        f"{'Method':<25s} "
        f"{'Test Acc':>9s} {'vs Baseline':>12s} "
        f"{'Sparsity':>10s} {'Avg |Code|':>12s}"
    )
    print(header2)
    print("-" * 110)

    baseline = [x for x in rows if x["mode"] == "trained" and x["method"] == "Uniform [-0.01, 0.01]"][0]

    for r in rows:
        if r["mode"] != "trained":
            continue
        delta = r["test_accuracy"] - baseline["test_accuracy"]
        delta_str = f"{delta:+.4f}"
        print(
            f"{r['method']:<25s} "
            f"{r['test_accuracy']:>9.4f} {delta_str:>12s} "
            f"{r['sparsity']:>10.4f} {r['avg_code_magnitude']:>12.6f}"
        )

    print("=" * 110)
    print("\n  NOTE: vs Baseline = test_accuracy vs Uniform [-0.01, 0.01] baseline")
    print("  Higher sparsity + decent accuracy = sparse, informative codes (scientific goal!)")
    print("  If avg |code| -> 0 and accuracy approx 1/n_classes (0.20), we have representation collapse.\n")


if __name__ == "__main__":
    main()