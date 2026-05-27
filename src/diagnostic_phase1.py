"""
Diagnostic experiments for Phase 1 root cause analysis.

Runs 5 quick diagnostic experiments to determine why the local
reconstruction objective fails to produce class-discriminative codes.
"""

from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from dataset_phase1 import generate_phase1_dataset
from eval_phase1 import evaluate_hierarchical_encoder
from hierarchical_encoder import HierarchicalEncoder
from node import UniversalNode
from harness import SimpleLogisticRegression


SEEDS = [42, 43, 44, 45, 46]
OUTPUT_DIR = "phase_1"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "diagnostic_results.csv")


# ---------------------------------------------------------------------------
# Helper: linear probe
# ---------------------------------------------------------------------------

def linear_probe_accuracy(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    test_y: np.ndarray,
    seed: int = 42,
) -> tuple[float, float]:
    """Fit softmax logistic regression and return (train_acc, test_acc)."""
    probe = SimpleLogisticRegression(
        n_classes=5,
        n_features=train_x.shape[1],
        lr=0.1,
        max_iter=500,
        seed=seed,
    )
    probe.fit(train_x, train_y)
    train_acc = float(probe.score(train_x, train_y))
    test_acc = float(probe.score(test_x, test_y))
    return train_acc, test_acc


# ---------------------------------------------------------------------------
# Experiment 1: Random Embedding Baseline
# ---------------------------------------------------------------------------

def run_exp1(dataset: dict, seed: int = 42) -> dict:
    """Random Normal(0,1) embedding → flatten → linear probe."""
    rng = np.random.default_rng(seed)
    d = 8
    embedding = rng.standard_normal((2, d)) * 1.0  # Normal(0,1)

    train_embed = embedding[dataset["train_x"].astype(int)]  # (N, 16, 8)
    test_embed = embedding[dataset["test_x"].astype(int)]

    train_x = train_embed.reshape(train_embed.shape[0], -1)  # (N, 128)
    test_x = test_embed.reshape(test_embed.shape[0], -1)

    train_acc, test_acc = linear_probe_accuracy(
        train_x, dataset["train_y"], test_x, dataset["test_y"], seed=seed
    )
    sparsity = float(np.mean(np.abs(test_x) < 1e-3))

    return {
        "test_accuracy": test_acc,
        "train_accuracy": train_acc,
        "sparsity": sparsity,
        "recon_mse_per_layer": [float("nan"), float("nan"), float("nan")],
        "n_params": embedding.size,
    }


# ---------------------------------------------------------------------------
# Experiment 2: Single-Layer (No Hierarchy) Baseline
# ---------------------------------------------------------------------------

class SingleLayerEncoder:
    """One layer of kernel-3 stride-1 nodes over embedded binary input."""

    def __init__(self, d: int = 8, d_out: int = 8, l1_lambda: float = 0.002, seed: int = 42):
        self.d = d
        self.d_out = d_out
        self.l1_lambda = l1_lambda
        rng = np.random.default_rng(seed)
        self.embedding = rng.standard_normal((2, d)) * 1.0
        self.node = UniversalNode(d=d, l1_lambda=l1_lambda, seed=seed, d_out=d_out)

    def _embed(self, x_binary: np.ndarray) -> np.ndarray:
        return self.embedding[x_binary.astype(int)]

    def train(
        self, dataset: np.ndarray, epochs: int = 100, lr: float = 0.01, batch_size: int = 32
    ) -> None:
        rng = np.random.default_rng(42)
        n_samples = dataset.shape[0]
        n_out = 14  # kernel-3 stride-1 on 16 positions

        for epoch in range(epochs):
            perm = rng.permutation(n_samples)
            x_shuffled = dataset[perm]
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_x = x_shuffled[start:end]
                B = end - start

                current = self._embed(batch_x)  # (B, 16, d)
                accum_grads: dict | None = None
                accum_embed_grad = np.zeros_like(self.embedding)

                for p in range(n_out):
                    x_3d = current[:, p : p + 3, :]
                    grads = self.node.compute_gradients(x_3d)

                    if accum_grads is None:
                        accum_grads = {k: grads[k].copy() for k in grads if k != "x_3d"}
                    else:
                        for k in accum_grads:
                            accum_grads[k] += grads[k]

                    # Embedding gradient
                    d_x = grads["x_3d"]  # (B, 3, d)
                    for k in range(3):
                        pos_global = p + k
                        idx_arr = batch_x[:, pos_global].astype(int)
                        for b in range(B):
                            accum_embed_grad[idx_arr[b]] += d_x[b, k, :]

                # Average over positions and apply
                for k in accum_grads:
                    accum_grads[k] /= n_out
                self.node.apply_gradients(accum_grads, lr)

                accum_embed_grad /= n_out
                self.embedding -= lr * accum_embed_grad

    def encode(self, x_binary: np.ndarray) -> np.ndarray:
        x = self._embed(x_binary)  # (B, 16, d)
        n_out = 14
        outputs: list[np.ndarray] = []
        for p in range(n_out):
            x_3d = x[:, p : p + 3, :]
            code = self.node.forward(x_3d)  # (B, d_out)
            outputs.append(code)
        x_out = np.stack(outputs, axis=1)  # (B, 14, d_out)
        return x_out.reshape(x_out.shape[0], -1)

    def compute_reconstruction_mse(self, x_binary: np.ndarray) -> list[float]:
        x = self._embed(x_binary)
        n_out = 14
        mse = 0.0
        for p in range(n_out):
            x_3d = x[:, p : p + 3, :]
            code = self.node.forward(x_3d)
            recon = self.node.reconstruct(code)
            mse += float(np.mean((x_3d - recon) ** 2))
        return [mse / n_out, float("nan"), float("nan")]

    def get_parameter_count(self) -> int:
        return (
            self.embedding.size
            + self.node.W_enc.size
            + self.node.b_enc.size
            + self.node.W_dec.size
            + self.node.b_dec.size
        )


def run_exp2(dataset: dict, seed: int = 42) -> dict:
    """Single layer baseline: 14 positions × d_out features."""
    encoder = SingleLayerEncoder(d=8, d_out=8, l1_lambda=0.002, seed=seed)
    encoder.train(dataset["train_x"], epochs=100, lr=0.01, batch_size=32)

    train_codes = encoder.encode(dataset["train_x"])
    test_codes = encoder.encode(dataset["test_x"])

    train_acc, test_acc = linear_probe_accuracy(
        train_codes, dataset["train_y"], test_codes, dataset["test_y"], seed=seed
    )
    sparsity = float(np.mean(np.abs(test_codes) < 1e-3))
    mses = encoder.compute_reconstruction_mse(dataset["test_x"])

    return {
        "test_accuracy": test_acc,
        "train_accuracy": train_acc,
        "sparsity": sparsity,
        "recon_mse_per_layer": mses,
        "n_params": encoder.get_parameter_count(),
    }


# ---------------------------------------------------------------------------
# Experiment 3: Simultaneous Training (all layers together)
# ---------------------------------------------------------------------------

class SimultaneousHierarchicalEncoder(HierarchicalEncoder):
    """Hierarchical encoder where all layers train simultaneously."""

    def train(
        self,
        dataset: np.ndarray,
        epochs: int = 100,
        lr: float = 0.01,
        batch_size: int = 32,
    ) -> dict:
        # For true cross-layer sharing, make all layers point to the same object.
        if self.sharing_mode == "cross_layer":
            master = self.layer_nodes[0]
            for l in range(1, self.n_layers):
                self.layer_nodes[l] = master

        rng = self.rng
        n_samples = dataset.shape[0]
        loss_history: list[float] = []

        for epoch in range(epochs):
            perm = rng.permutation(n_samples)
            x_shuffled = dataset[perm]
            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_x = x_shuffled[start:end]
                B = end - start

                # ---- Forward pass through ALL layers ----
                current = self._embed(batch_x)  # (B, 16, d)
                layer_inputs: list[np.ndarray] = []

                for l in range(self.n_layers):
                    x_out, node_inputs = self._forward_layer(current, l)
                    layer_inputs.append(node_inputs)
                    current = x_out
                    if l < self.n_layers - 1 and current.shape[2] > self.d:
                        current = current[:, :, : self.d]

                # ---- Backward pass: compute and apply gradients ----
                embed_grad = np.zeros_like(self.embedding)

                if self.sharing_mode == "cross_layer":
                    master = self.layer_nodes[0]
                    master_grads: dict | None = None
                    total_positions = 0

                    for l in range(self.n_layers):
                        node_inputs = layer_inputs[l]
                        n_out = self.n_nodes_per_layer[l]

                        for p in range(n_out):
                            x_3d = node_inputs[:, p, :, :]
                            grads = master.compute_gradients(x_3d)

                            if master_grads is None:
                                master_grads = {
                                    k: grads[k].copy() for k in grads if k != "x_3d"
                                }
                            else:
                                for k in master_grads:
                                    master_grads[k] += grads[k]

                            # Embedding gradient from layer 0 only
                            if l == 0:
                                d_x = grads["x_3d"]  # (B, 3, d)
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        embed_grad[idx_arr[b]] += d_x[b, k, :]

                            total_positions += 1

                        epoch_loss += float(master.local_loss(node_inputs[:, 0, :, :]))
                        n_batches += 1

                    # Average over ALL positions across ALL layers
                    for k in master_grads:
                        master_grads[k] /= total_positions
                    master.apply_gradients(master_grads, lr)

                    embed_grad /= total_positions
                    self.embedding -= lr * embed_grad

                elif self.sharing_mode == "within_layer":
                    for l in range(self.n_layers):
                        node = self.layer_nodes[l]
                        node_inputs = layer_inputs[l]
                        n_out = self.n_nodes_per_layer[l]

                        accum_grads: dict | None = None
                        for p in range(n_out):
                            x_3d = node_inputs[:, p, :, :]
                            grads = node.compute_gradients(x_3d)

                            if accum_grads is None:
                                accum_grads = {
                                    k: grads[k].copy() for k in grads if k != "x_3d"
                                }
                            else:
                                for k in accum_grads:
                                    accum_grads[k] += grads[k]

                            if l == 0:
                                d_x = grads["x_3d"]
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        embed_grad[idx_arr[b]] += d_x[b, k, :]

                        for k in accum_grads:
                            accum_grads[k] /= n_out
                        node.apply_gradients(accum_grads, lr)

                        epoch_loss += float(node.local_loss(node_inputs[:, 0, :, :]))
                        n_batches += 1

                    embed_grad /= self.n_nodes_per_layer[0]
                    self.embedding -= lr * embed_grad

                else:  # none (independent nodes)
                    for l in range(self.n_layers):
                        node_inputs = layer_inputs[l]
                        n_out = self.n_nodes_per_layer[l]

                        for p in range(n_out):
                            x_3d = node_inputs[:, p, :, :]
                            node = self.nodes[l][p]
                            grads = node.compute_gradients(x_3d)
                            node_grads = {k: v for k, v in grads.items() if k != "x_3d"}
                            node.apply_gradients(node_grads, lr)

                            if l == 0:
                                d_x = grads["x_3d"]
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        embed_grad[idx_arr[b]] += d_x[b, k, :]

                        epoch_loss += float(
                            self.nodes[l][0].local_loss(node_inputs[:, 0, :, :])
                        )
                        n_batches += 1

                    embed_grad /= self.n_nodes_per_layer[0]
                    self.embedding -= lr * embed_grad

            loss_history.append(epoch_loss / max(n_batches, 1))

        return {"loss_history": loss_history}


def run_exp3(dataset: dict, seed: int = 42) -> dict:
    """Simultaneous training of all 3 layers."""
    encoder = SimultaneousHierarchicalEncoder(
        n_input=16,
        d=8,
        n_layers=3,
        sharing_mode="cross_layer",
        l1_lambda=0.002,
        seed=seed,
        d_out=24,
    )
    encoder.train(dataset["train_x"], epochs=100, lr=0.01, batch_size=32)
    return evaluate_hierarchical_encoder(encoder, dataset, seed=seed)


# ---------------------------------------------------------------------------
# Experiment 4: Predictive Coding Node (lateral inhibition + hard threshold)
# ---------------------------------------------------------------------------

class PredictiveCodingNode(UniversalNode):
    """
    UniversalNode with lateral inhibition and hard thresholding.
    Adapted from P0-E's competition mechanism.
    """

    def __init__(
        self,
        d: int = 8,
        l1_lambda: float = 0.0,
        seed: int = 42,
        d_out: int | None = None,
        competition_k: int = 4,
        hard_threshold: float = 0.01,
    ):
        super().__init__(d=d, l1_lambda=l1_lambda, seed=seed, d_out=d_out, kwta_k=None)
        self.competition_k = competition_k
        self.hard_threshold = hard_threshold

    def _activation_masks(self, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (raw_activations, mask)."""
        a = np.tanh(z)
        k = min(self.competition_k, self.d_out)
        abs_a = np.abs(a)
        top_k_mean = np.mean(np.sort(abs_a, axis=1)[:, -k:], axis=1, keepdims=True)
        mask_comp = abs_a > top_k_mean * 0.5
        mask_hard = abs_a > self.hard_threshold
        mask = mask_comp * mask_hard
        return a, mask

    def forward(self, x_3d: np.ndarray) -> np.ndarray:
        batch = x_3d.shape[0]
        x_flat = x_3d.reshape(batch, -1)
        z = x_flat @ self.W_enc + self.b_enc
        a, mask = self._activation_masks(z)
        return a * mask

    def compute_gradients(self, x_3d: np.ndarray) -> dict[str, np.ndarray]:
        batch = x_3d.shape[0]
        D_in = self.d_in
        D_out = self.d_out

        x_flat = x_3d.reshape(batch, D_in)
        z = x_flat @ self.W_enc + self.b_enc
        a_raw, mask = self._activation_masks(z)
        a = a_raw * mask

        r = a @ self.W_dec + self.b_dec
        d_r = 2.0 / (batch * D_in) * (r - x_flat)

        d_W_dec = a.T @ d_r
        d_b_dec = np.sum(d_r, axis=0)

        d_a = d_r @ self.W_dec.T
        # Straight-through estimator for threshold / competition
        d_a = d_a * mask

        if self.l1_lambda > 0:
            d_a += self.l1_lambda / (batch * D_out) * np.sign(a)

        d_z = d_a * (1.0 - np.tanh(z) ** 2)

        d_W_enc = x_flat.T @ d_z
        d_b_enc = np.sum(d_z, axis=0)

        d_x_flat = d_z @ self.W_enc.T - d_r
        d_x_3d = d_x_flat.reshape(batch, 3, self.d)

        return {
            "W_enc": d_W_enc,
            "b_enc": d_b_enc,
            "W_dec": d_W_dec,
            "b_dec": d_b_dec,
            "x_3d": d_x_3d,
        }

    def share_parameters_from(self, other: "PredictiveCodingNode") -> None:
        self.W_enc = other.W_enc.copy()
        self.b_enc = other.b_enc.copy()
        self.W_dec = other.W_dec.copy()
        self.b_dec = other.b_dec.copy()


def _make_pc_hierarchical_encoder(seed: int = 42) -> HierarchicalEncoder:
    """Create a standard HierarchicalEncoder but replace nodes with PC nodes."""
    enc = HierarchicalEncoder(
        n_input=16,
        d=8,
        n_layers=3,
        sharing_mode="cross_layer",
        l1_lambda=0.0,
        seed=seed,
        d_out=24,
    )
    # Replace every node with PredictiveCodingNode
    if enc.sharing_mode == "none":
        node_seed = seed
        for l_idx, layer_nodes in enumerate(enc.nodes):
            for p_idx, _ in enumerate(layer_nodes):
                enc.nodes[l_idx][p_idx] = PredictiveCodingNode(
                    d=8,
                    d_out=24,
                    seed=node_seed,
                    competition_k=4,
                    hard_threshold=0.01,
                )
                node_seed += 1
    else:
        for l_idx in range(enc.n_layers):
            enc.layer_nodes[l_idx] = PredictiveCodingNode(
                d=8,
                d_out=24,
                seed=seed + l_idx,
                competition_k=4,
                hard_threshold=0.01,
            )
    return enc


def run_exp4(dataset: dict, seed: int = 42) -> dict:
    """Predictive coding node with lateral inhibition and hard threshold."""
    encoder = _make_pc_hierarchical_encoder(seed=seed)
    # NOTE: We keep batch_size=32 for efficiency; competition/thresholding
    # are applied per-sample within the batch.
    encoder.train(dataset["train_x"], epochs_per_layer=100, lr=0.01, batch_size=32)
    return evaluate_hierarchical_encoder(encoder, dataset, seed=seed)


# ---------------------------------------------------------------------------
# Experiment 5: Increased L1 with Stronger Sparsity
# ---------------------------------------------------------------------------

def run_exp5(dataset: dict, seed: int = 42) -> dict:
    """Standard progressive training with l1_lambda = 0.05 (25× default)."""
    encoder = HierarchicalEncoder(
        n_input=16,
        d=8,
        n_layers=3,
        sharing_mode="cross_layer",
        l1_lambda=0.05,
        seed=seed,
        d_out=24,
    )
    encoder.train(dataset["train_x"], epochs_per_layer=100, lr=0.01, batch_size=32)
    return evaluate_hierarchical_encoder(encoder, dataset, seed=seed)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    experiments = [
        ("Exp1-Random-Embedding", run_exp1),
        ("Exp2-Single-Layer", run_exp2),
        ("Exp3-Simultaneous", run_exp3),
        ("Exp4-Predictive-Coding", run_exp4),
        ("Exp5-Strong-L1", run_exp5),
    ]

    all_results: list[dict] = []

    print("=" * 70)
    print("  Phase 1 Diagnostic Root Cause Analysis")
    print(f"  {len(experiments)} experiments × {len(SEEDS)} seeds = {len(experiments)*len(SEEDS)} runs")
    print("=" * 70)

    for exp_name, exp_func in experiments:
        print(f"\n{'-' * 70}")
        print(f"  Experiment: {exp_name}")
        print(f"{'-' * 70}")

        for seed in SEEDS:
            t0 = time.time()
            dataset = generate_phase1_dataset(seed=seed)
            res = exp_func(dataset, seed)
            elapsed = time.time() - t0

            row = {
                "config": exp_name,
                "seed": seed,
                "test_accuracy": res["test_accuracy"],
                "train_accuracy": res["train_accuracy"],
                "sparsity": res["sparsity"],
                "recon_mse_l0": res["recon_mse_per_layer"][0],
                "recon_mse_l1": res["recon_mse_per_layer"][1],
                "recon_mse_l2": res["recon_mse_per_layer"][2],
                "n_params": res["n_params"],
            }
            all_results.append(row)
            print(
                f"    seed={seed}  |  test_acc={row['test_accuracy']:.4f}  "
                f"train_acc={row['train_accuracy']:.4f}  sparsity={row['sparsity']:.4f}  "
                f"({elapsed:.1f}s)"
            )

    # -----------------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------------
    fieldnames = [
        "config",
        "seed",
        "test_accuracy",
        "train_accuracy",
        "sparsity",
        "recon_mse_l0",
        "recon_mse_l1",
        "recon_mse_l2",
        "n_params",
    ]

    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  Summary (mean ± std over seeds)")
    print("=" * 70)
    print(
        f"    {'Config':<25s} {'Test Acc':>12s} {'Train Acc':>12s} {'Sparsity':>12s}"
    )
    print("    " + "-" * 63)

    for exp_name, _ in experiments:
        rows = [r for r in all_results if r["config"] == exp_name]
        test_accs = [r["test_accuracy"] for r in rows]
        train_accs = [r["train_accuracy"] for r in rows]
        sparsities = [r["sparsity"] for r in rows]
        print(
            f"    {exp_name:<25s} {np.mean(test_accs):.4f}±{np.std(test_accs):.4f}  "
            f"{np.mean(train_accs):.4f}±{np.std(train_accs):.4f}  "
            f"{np.mean(sparsities):.4f}±{np.std(sparsities):.4f}"
        )

    print("\n" + "=" * 70)
    print(f"  Results saved to: {RESULTS_CSV}")
    print("=" * 70)


if __name__ == "__main__":
    main()
