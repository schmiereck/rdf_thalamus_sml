"""
Hierarchical Encoder for Phase 1 — Spatial Hierarchy without Time.

Stacks 3 layers of kernel-3 stride-1 UniversalNodes over 16 binary
inputs, with configurable weight sharing and progressive layer-by-layer
training.

Configurations:
  - P1-A: within_layer sharing
  - P1-B: cross_layer sharing + recursive d=8
  - P1-C: none (independent weights)
  - P1-D: recursive d=4
  - P1-E: wider output (d_out != 3*d)
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from node import UniversalNode


# ---------------------------------------------------------------------------
# Hierarchical Encoder
# ---------------------------------------------------------------------------

class HierarchicalEncoder:
    """Stacked kernel-3 stride-1 UniversalNodes over a 1-D binary input."""

    def __init__(
        self,
        n_input: int = 16,
        d: int = 8,
        n_layers: int = 3,
        sharing_mode: str = "cross_layer",
        l1_lambda: float = 0.002,
        seed: int = 42,
        d_out: int | None = None,
        kwta_k: int | None = None,
    ):
        """
        Parameters
        ----------
        n_input : int
            Number of input slots (16 binary pixels).
        d : int
            Dimensionality ``d`` per slot.  Three adjacent slots form the
            node input ``(batch, 3, d)``.
        n_layers : int
            Number of stacked layers.
        sharing_mode : str
            One of ``'within_layer'``, ``'cross_layer'``, ``'none'``.
        l1_lambda : float
            L1 sparsity coefficient passed to each UniversalNode.
        seed : int
            Master RNG seed.
        d_out : int | None
            Latent code dimensionality per node.  Defaults to ``3*d``.
        kwta_k : int | None
            If set, apply k-Winners-Take-All in each node.
        """
        if sharing_mode not in ("within_layer", "cross_layer", "none"):
            raise ValueError(
                f"sharing_mode must be one of ('within_layer', 'cross_layer', 'none'), "
                f"got '{sharing_mode}'"
            )

        self.n_input = n_input
        self.d = d
        self.n_layers = n_layers
        self.sharing_mode = sharing_mode
        self.l1_lambda = l1_lambda
        self.seed = seed
        self.d_out = d_out if d_out is not None else 3 * d
        self.kwta_k = kwta_k

        self.rng = np.random.default_rng(seed)

        # -- Learnable binary embedding (2, d) --
        # Use Normal(0, 1.0) for stronger initial representations
        self.embedding: np.ndarray = self.rng.standard_normal((2, d)) * 1.0

        # Number of nodes per layer (kernel-3 stride-1 sliding window)
        # Layer 0: 14, Layer 1: 12, Layer 2: 10 (for n_input=16, n_layers=3)
        self.n_nodes_per_layer = [
            self.n_input - 2 * l - 2 for l in range(self.n_layers)
        ]

        # -- Instantiate nodes --
        if sharing_mode == "none":
            # Unique UniversalNode for every (layer, position) pair
            self.nodes: list[list[UniversalNode]] = []
            node_seed = seed
            for l_idx in range(self.n_layers):
                layer_nodes: list[UniversalNode] = []
                for _p in range(self.n_nodes_per_layer[l_idx]):
                    layer_nodes.append(
                        UniversalNode(
                            d=self.d,
                            l1_lambda=self.l1_lambda,
                            seed=node_seed,
                            d_out=self.d_out,
                            kwta_k=kwta_k,
                        )
                    )
                    node_seed += 1
                self.nodes.append(layer_nodes)
        else:
            # within_layer  → one node per layer (shared across positions)
            # cross_layer   → one node per layer (weights copied during training)
            self.layer_nodes: list[UniversalNode] = []
            for l_idx in range(self.n_layers):
                self.layer_nodes.append(
                    UniversalNode(
                        d=self.d,
                        l1_lambda=self.l1_lambda,
                        seed=seed + l_idx,
                        d_out=self.d_out,
                        kwta_k=kwta_k,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_node(self, layer_idx: int, pos: int = 0) -> UniversalNode:
        """Return the node responsible for a given layer and position."""
        if self.sharing_mode == "none":
            return self.nodes[layer_idx][pos]
        return self.layer_nodes[layer_idx]

    def _embed(self, x_binary: np.ndarray) -> np.ndarray:
        """Binary → embedding lookup.  ``(batch, 16)`` → ``(batch, 16, d)``."""
        return self.embedding[x_binary.astype(int)]

    def _forward_layer(
        self, x_in: np.ndarray, layer_idx: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Forward pass through one layer, returning both output and node inputs.

        Parameters
        ----------
        x_in : np.ndarray, shape (batch, n_in_pos, d)
        layer_idx : int

        Returns
        -------
        x_out : np.ndarray, shape (batch, n_in_pos-2, d_out)
        node_inputs : np.ndarray, shape (batch, n_in_pos-2, 3, d)
        """
        n_out = x_in.shape[1] - 2

        outputs: list[np.ndarray] = []
        inputs: list[np.ndarray] = []
        for p in range(n_out):
            x_3d = x_in[:, p : p + 3, :]          # (batch, 3, d)
            inputs.append(x_3d)
            node = self._get_node(layer_idx, p)
            outputs.append(node.forward(x_3d))     # (batch, d_out)

        x_out = np.stack(outputs, axis=1)          # (batch, n_out, d_out)
        node_inputs = np.stack(inputs, axis=1)     # (batch, n_out, 3, d)
        return x_out, node_inputs

    def _forward_layer_only(
        self, x_in: np.ndarray, layer_idx: int
    ) -> np.ndarray:
        """Light-weight forward pass returning only the layer output."""
        x_out, _ = self._forward_layer(x_in, layer_idx)
        return x_out

    # ------------------------------------------------------------------
    # Forward / Encode
    # ------------------------------------------------------------------

    def forward(self, x_binary: np.ndarray) -> np.ndarray:
        """
        Full forward pass through all layers.

        Parameters
        ----------
        x_binary : np.ndarray, shape (batch, 16)

        Returns
        -------
        codes : np.ndarray, shape (batch, 10 * d_out)
        """
        x = self._embed(x_binary)                  # (batch, 16, d)

        for l in range(self.n_layers):
            x, _ = self._forward_layer(x, l)       # (batch, n_pos, d_out)
            if l < self.n_layers - 1:
                # Only slice when d_out > d (e.g., P1-E with d_out=16, d=8)
                # For recursive configs (d_out == d), no slicing needed
                if x.shape[2] > self.d:
                    x = x[:, :, : self.d]

        batch = x.shape[0]
        return x.reshape(batch, -1)                # (batch, 10 * d_out)

    def encode(self, x_binary: np.ndarray) -> np.ndarray:
        """Alias for :meth:`forward`."""
        return self.forward(x_binary)

    # ------------------------------------------------------------------
    # Progressive Training
    # ------------------------------------------------------------------

    def train(
        self,
        dataset: np.ndarray,
        epochs_per_layer: int = 100,
        lr: float = 0.01,
        batch_size: int = 32,
    ) -> dict:
        """
        Progressive layer-by-layer training.

        1. Train Layer 0 (embedding + nodes),  copy weights to L1/L2 if
           ``cross_layer``.
        2. Compute L0 outputs, train Layer 1, copy weights to L2 if
           ``cross_layer``.
        3. Compute L1 outputs, train Layer 2.
        4. Final sync so all layers share identical weights when
           ``cross_layer``.

        Parameters
        ----------
        dataset : np.ndarray, shape (N, 16)
            Binary training inputs.
        epochs_per_layer : int
        lr : float
            Learning rate for both embedding and node updates.
        batch_size : int

        Returns
        -------
        info : dict
            Contains ``'loss_history'`` (list of average loss per epoch).
        """
        x_train = dataset
        n_samples = x_train.shape[0]

        loss_history: list[float] = []

        # When k-WTA is active, skip L1 penalty (sparsity is structural)
        effective_l1 = 0.0 if self.kwta_k is not None else self.l1_lambda

        for layer_idx in range(self.n_layers):
            for epoch in range(epochs_per_layer):
                perm = self.rng.permutation(n_samples)
                x_shuffled = x_train[perm]
                epoch_loss = 0.0
                n_batches = 0

                for start in range(0, n_samples, batch_size):
                    end = min(start + batch_size, n_samples)
                    batch_x = x_shuffled[start:end]
                    B = end - start  # actual batch size

                    # ------ Propagate to current layer ------
                    current = self._embed(batch_x)   # (B, 16, d)
                    for prev_l in range(layer_idx):
                        current = self._forward_layer_only(current, prev_l)
                        if current.shape[2] > self.d:
                            current = current[:, :, : self.d]

                    n_out = self.n_nodes_per_layer[layer_idx]

                    if self.sharing_mode != "none":
                        # --- Shared node: accumulate & average gradients ---
                        node = self.layer_nodes[layer_idx]
                        accum_grads: dict | None = None
                        accum_embed_grad: np.ndarray | None = None

                        if layer_idx == 0:
                            accum_embed_grad = np.zeros_like(self.embedding)

                        for p in range(n_out):
                            x_3d = current[:, p : p + 3, :]
                            grads = node.compute_gradients(x_3d)

                            # Node parameter gradients (exclude x_3d)
                            if accum_grads is None:
                                accum_grads = {
                                    k: grads[k].copy()
                                    for k in grads
                                    if k != "x_3d"
                                }
                            else:
                                for k in accum_grads:
                                    accum_grads[k] += grads[k]

                            # Embedding gradient (layer 0 only)
                            if layer_idx == 0:
                                d_x = grads["x_3d"]  # (B, 3, d)
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        accum_embed_grad[idx_arr[b]] += d_x[b, k, :]

                        # Average over positions and apply
                        for k in accum_grads:
                            accum_grads[k] /= n_out
                        node.apply_gradients(accum_grads, lr)

                        # Embedding update
                        if layer_idx == 0:
                            accum_embed_grad /= n_out
                            self.embedding -= lr * accum_embed_grad

                        epoch_loss += float(node.local_loss(current[:, 0:3, :]))
                        n_batches += 1

                    else:
                        # --- Independent nodes: update each separately ---
                        accum_embed_grad: np.ndarray | None = None
                        if layer_idx == 0:
                            accum_embed_grad = np.zeros_like(self.embedding)

                        for p in range(n_out):
                            x_3d = current[:, p : p + 3, :]
                            node = self.nodes[layer_idx][p]
                            grads = node.compute_gradients(x_3d)
                            node_grads = {
                                k: v for k, v in grads.items() if k != "x_3d"
                            }
                            node.apply_gradients(node_grads, lr)

                            if layer_idx == 0:
                                d_x = grads["x_3d"]
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        accum_embed_grad[idx_arr[b]] += d_x[b, k, :]

                        if layer_idx == 0:
                            accum_embed_grad /= n_out
                            self.embedding -= lr * accum_embed_grad

                        epoch_loss += float(
                            self.nodes[layer_idx][0].local_loss(
                                current[:, 0:3, :]
                            )
                        )
                        n_batches += 1

                loss_history.append(epoch_loss / max(n_batches, 1))

            # --- Cross-layer weight copy after this layer's training ---
            if self.sharing_mode == "cross_layer":
                for l in range(self.n_layers):
                    if l != layer_idx:
                        self.layer_nodes[l].share_parameters_from(
                            self.layer_nodes[layer_idx]
                        )

        return {"loss_history": loss_history}

    # ------------------------------------------------------------------
    # Parameter Count
    # ------------------------------------------------------------------

    def get_parameter_count(self) -> int:
        """
        Count of trainable parameters in the embedding plus all *unique*
        node parameters (accounting for the sharing mode).
        """
        count = self.embedding.size  # 2 * d

        if self.sharing_mode == "none":
            for layer_nodes in self.nodes:
                for node in layer_nodes:
                    count += node.W_enc.size + node.b_enc.size
                    count += node.W_dec.size + node.b_dec.size
        else:
            for node in self.layer_nodes:
                count += node.W_enc.size + node.b_enc.size
                count += node.W_dec.size + node.b_dec.size

        return count

    # ------------------------------------------------------------------
    # Reconstruction MSE
    # ------------------------------------------------------------------

    def compute_reconstruction_mse(self, x_binary: np.ndarray) -> list[float]:
        """
        Compute the per-layer mean-squared reconstruction error.

        Returns
        -------
        mse_list : list[float]
            ``[mse_layer0, mse_layer1, mse_layer2]``
        """
        x = self._embed(x_binary)
        mse_list: list[float] = []

        for layer_idx in range(self.n_layers):
            n_out = self.n_nodes_per_layer[layer_idx]
            layer_mse = 0.0

            for p in range(n_out):
                x_3d = x[:, p : p + 3, :]
                node = self._get_node(layer_idx, p)
                code = node.forward(x_3d)
                recon = node.reconstruct(code)
                layer_mse += float(np.mean((x_3d - recon) ** 2))

            mse_list.append(layer_mse / n_out)

            # Propagate to next layer
            if layer_idx < self.n_layers - 1:
                x, _ = self._forward_layer(x, layer_idx)
                if x.shape[2] > self.d:
                    x = x[:, :, : self.d]

        return mse_list


# ======================================================================
#  Self-test
# ======================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  HierarchicalEncoder -- Self-Test")
    print("=" * 60)

    rng = np.random.default_rng(7)

    # -- 1. Instantiate in each sharing mode --
    for mode in ("none", "within_layer", "cross_layer"):
        enc = HierarchicalEncoder(d=8, sharing_mode=mode, seed=42)
        print(f"\n[Mode: {mode}]")
        print(f"  d_out = {enc.d_out}")
        print(f"  n_nodes_per_layer = {enc.n_nodes_per_layer}")
        print(f"  embedding shape = {enc.embedding.shape}")

        # -- 2. Forward pass on dummy batch --
        batch_size = 4
        dummy = (rng.random((batch_size, 16)) < 0.5).astype(np.float64)
        codes = enc.encode(dummy)
        expected_shape = (batch_size, 10 * enc.d_out)
        assert codes.shape == expected_shape, (
            f"Expected {expected_shape}, got {codes.shape}"
        )
        print(f"  Forward pass: input {dummy.shape} -> output {codes.shape}  [OK]")

        # -- 3. Parameter count --
        n_params = enc.get_parameter_count()
        print(f"  Parameter count = {n_params}")

        # -- 4. Reconstruction MSE --
        mses = enc.compute_reconstruction_mse(dummy)
        assert len(mses) == 3
        print(f"  Reconstruction MSEs = {[f'{m:.4f}' for m in mses]}")

        # -- 5. Quick training (just a few epochs to verify it runs) --
        dataset = (rng.random((64, 16)) < 0.5).astype(np.float64)
        info = enc.train(dataset, epochs_per_layer=3, lr=0.01, batch_size=16)
        assert len(info["loss_history"]) == 3 * 3  # 3 layers × 3 epochs
        print(f"  Training completed, {len(info['loss_history'])} loss entries  [OK]")

        # -- 6. Verify cross-layer weight sharing --
        if mode == "cross_layer":
            weights_0 = enc.layer_nodes[0].W_enc.copy()
            for l in range(1, enc.n_layers):
                assert np.allclose(
                    enc.layer_nodes[l].W_enc, weights_0
                ), f"Layer {l} weights differ after sync!"
            print("  Cross-layer weight sync verified  [OK]")

    print("\n" + "-" * 60)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 60)
