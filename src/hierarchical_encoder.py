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
        self.embedding: np.ndarray = self.rng.standard_normal((2, d)) * 1.0

        self.n_nodes_per_layer = [
            self.n_input - 2 * l - 2 for l in range(self.n_layers)
        ]

        # -- Instantiate nodes --
        if sharing_mode == "none":
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
        if self.sharing_mode == "none":
            return self.nodes[layer_idx][pos]
        return self.layer_nodes[layer_idx]

    def _embed(self, x_binary: np.ndarray) -> np.ndarray:
        return self.embedding[x_binary.astype(int)]

    def _forward_layer(
        self, x_in: np.ndarray, layer_idx: int
    ) -> tuple[np.ndarray, np.ndarray]:
        n_out = x_in.shape[1] - 2

        outputs: list[np.ndarray] = []
        inputs: list[np.ndarray] = []
        for p in range(n_out):
            x_3d = x_in[:, p : p + 3, :]
            inputs.append(x_3d)
            node = self._get_node(layer_idx, p)
            outputs.append(node.forward(x_3d))

        x_out = np.stack(outputs, axis=1)
        node_inputs = np.stack(inputs, axis=1)
        return x_out, node_inputs

    def _forward_layer_only(
        self, x_in: np.ndarray, layer_idx: int
    ) -> np.ndarray:
        x_out, _ = self._forward_layer(x_in, layer_idx)
        return x_out

    # ------------------------------------------------------------------
    # Forward / Encode
    # ------------------------------------------------------------------

    def forward(self, x_binary: np.ndarray) -> np.ndarray:
        x = self._embed(x_binary)
        for l in range(self.n_layers):
            x, _ = self._forward_layer(x, l)
            if l < self.n_layers - 1:
                if x.shape[2] > self.d:
                    x = x[:, :, : self.d]
        batch = x.shape[0]
        return x.reshape(batch, -1)

    def encode(self, x_binary: np.ndarray) -> np.ndarray:
        return self.forward(x_binary)

    # ------------------------------------------------------------------
    # NEW: Forward with intermediates
    # ------------------------------------------------------------------

    def forward_with_intermediates(self, x_binary: np.ndarray) -> dict:
        x = self._embed(x_binary)
        embeddings = x.copy()

        layer_outputs = []
        node_inputs_list = []
        all_codes_3d = []

        for l in range(self.n_layers):
            x_out, node_ins = self._forward_layer(x, l)
            all_codes_3d.append(x_out.copy())
            node_inputs_list.append(node_ins.copy())

            if l < self.n_layers - 1:
                if x_out.shape[2] > self.d:
                    x = x_out[:, :, : self.d]
                else:
                    x = x_out
            else:
                x = x_out
            layer_outputs.append(x.copy())

        batch = x.shape[0]
        codes = x.reshape(batch, -1)

        return {
            "codes": codes,
            "embeddings": embeddings,
            "layer_outputs": layer_outputs,
            "node_inputs": node_inputs_list,
            "all_codes_3d": all_codes_3d,
        }

    # ------------------------------------------------------------------
    # NEW: Backward from code-level gradients
    # ------------------------------------------------------------------

    def backward_from_code_grads(
        self,
        dL_dcodes: np.ndarray | list[np.ndarray],
        codes: np.ndarray,
        node_inputs: list[np.ndarray],
        x_binary: np.ndarray,
    ) -> dict:
        batch = codes.shape[0]

        dL_dcodes_is_list = isinstance(dL_dcodes, list)
        n_nodes_last = self.n_nodes_per_layer[-1]

        if dL_dcodes_is_list:
            dL_dx_prop = np.zeros((batch, n_nodes_last, self.d_out))
        else:
            dL_dx_prop = dL_dcodes.reshape(batch, n_nodes_last, self.d_out)

        if self.sharing_mode == "none":
            dL_dnodes = [
                [{} for _ in range(self.n_nodes_per_layer[l])]
                for l in range(self.n_layers)
            ]
        else:
            dL_dnodes_layer: list[dict | None] = [None for _ in range(self.n_layers)]

        dL_dembed = np.zeros_like(self.embedding)

        for l in reversed(range(self.n_layers)):
            if dL_dcodes_is_list:
                dL_dx_total = dL_dx_prop + dL_dcodes[l]
            else:
                dL_dx_total = dL_dx_prop

            n_nodes = self.n_nodes_per_layer[l]
            node_ins = node_inputs[l]

            n_in_pos = node_ins.shape[1] + 2
            dL_dlayer_input = np.zeros((batch, n_in_pos, self.d))
            count_overlap = np.zeros((n_in_pos,))

            for p in range(n_nodes):
                x_3d = node_ins[:, p, :, :]
                node = self._get_node(l, p)
                code = node.forward(x_3d)

                dL_da = dL_dx_total[:, p, :].copy()

                if node.kwta_k is not None:
                    k = min(node.kwta_k, node.d_out)
                    z_raw = x_3d.reshape(batch, -1) @ node.W_enc + node.b_enc
                    abs_a_raw = np.abs(np.tanh(z_raw))
                    threshold = np.sort(abs_a_raw, axis=1)[:, -k][:, None]
                    mask = abs_a_raw >= threshold
                    dL_da *= mask

                dL_dz = dL_da * (1.0 - code ** 2)

                x_flat = x_3d.reshape(batch, -1)

                dW_enc = x_flat.T @ dL_dz / batch
                db_enc = dL_dz.mean(axis=0)
                dW_dec = np.zeros_like(node.W_dec)
                db_dec = np.zeros_like(node.b_dec)

                dL_dx_flat = dL_dz @ node.W_enc.T
                dL_dx_3d = dL_dx_flat.reshape(batch, 3, self.d)

                if self.sharing_mode == "none":
                    dL_dnodes[l][p] = {
                        "W_enc": dW_enc,
                        "b_enc": db_enc,
                        "W_dec": dW_dec,
                        "b_dec": db_dec,
                        "x_3d": dL_dx_3d,
                    }
                else:
                    if p == 0:
                        accum = {
                            "W_enc": dW_enc.copy(),
                            "b_enc": db_enc.copy(),
                            "W_dec": dW_dec.copy(),
                            "b_dec": db_dec.copy(),
                            "x_3d": dL_dx_3d.copy(),
                        }
                    else:
                        accum["W_enc"] += dW_enc
                        accum["b_enc"] += db_enc
                        accum["x_3d"] += dL_dx_3d

                for k_shift in range(3):
                    pos = p + k_shift
                    dL_dlayer_input[:, pos, :] += dL_dx_3d[:, k_shift, :]
                    count_overlap[pos] += 1

            if self.sharing_mode != "none":
                for key in ("W_enc", "b_enc", "W_dec", "b_dec"):
                    accum[key] /= n_nodes  # type: ignore[index]
                dL_dnodes_layer[l] = accum  # type: ignore[index]

            valid = count_overlap > 0
            dL_dlayer_input[:, valid, :] /= count_overlap[valid][None, :, None]

            if l > 0:
                n_nodes_prev = self.n_nodes_per_layer[l - 1]
                if self.d_out > self.d:
                    dL_dx_prop = np.zeros((batch, n_nodes_prev, self.d_out))
                    dL_dx_prop[:, :, : self.d] = dL_dlayer_input
                else:
                    dL_dx_prop = dL_dlayer_input
            else:
                for pos in range(self.n_input):
                    idx_arr = x_binary[:, pos].astype(int)
                    for b in range(batch):
                        dL_dembed[idx_arr[b]] += dL_dlayer_input[b, pos, :]
                dL_dembed /= batch
                dL_dx_prop = dL_dlayer_input

        return {
            "dL_dembedding": dL_dembed,
            "dL_dnodes": dL_dnodes if self.sharing_mode == "none" else dL_dnodes_layer,
            "dL_dx_binary": dL_dx_prop,
        }

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
        x_train = dataset
        n_samples = x_train.shape[0]
        loss_history: list[float] = []

        for layer_idx in range(self.n_layers):
            for epoch in range(epochs_per_layer):
                perm = self.rng.permutation(n_samples)
                x_shuffled = x_train[perm]
                epoch_loss = 0.0
                n_batches = 0

                for start in range(0, n_samples, batch_size):
                    end = min(start + batch_size, n_samples)
                    batch_x = x_shuffled[start:end]
                    B = end - start

                    current = self._embed(batch_x)
                    for prev_l in range(layer_idx):
                        current = self._forward_layer_only(current, prev_l)
                        if current.shape[2] > self.d:
                            current = current[:, :, : self.d]

                    n_out = self.n_nodes_per_layer[layer_idx]

                    if self.sharing_mode != "none":
                        node = self.layer_nodes[layer_idx]
                        accum_grads: dict | None = None
                        accum_embed_grad: np.ndarray | None = None

                        if layer_idx == 0:
                            accum_embed_grad = np.zeros_like(self.embedding)

                        for p in range(n_out):
                            x_3d = current[:, p : p + 3, :]
                            grads = node.compute_gradients(x_3d)

                            if accum_grads is None:
                                accum_grads = {
                                    k: grads[k].copy()
                                    for k in grads
                                    if k != "x_3d"
                                }
                            else:
                                for k in accum_grads:
                                    accum_grads[k] += grads[k]

                            if layer_idx == 0:
                                d_x = grads["x_3d"]
                                for k in range(3):
                                    pos_global = p + k
                                    idx_arr = batch_x[:, pos_global].astype(int)
                                    for b in range(B):
                                        accum_embed_grad[idx_arr[b]] += d_x[b, k, :]

                        for k in accum_grads:
                            accum_grads[k] /= n_out
                        node.apply_gradients(accum_grads, lr)

                        if layer_idx == 0:
                            accum_embed_grad /= n_out
                            self.embedding -= lr * accum_embed_grad

                        epoch_loss += float(node.local_loss(current[:, 0:3, :]))
                        n_batches += 1

                    else:
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
        count = self.embedding.size
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

    for mode in ("none", "within_layer", "cross_layer"):
        enc = HierarchicalEncoder(d=8, sharing_mode=mode, seed=42)
        print(f"\n[Mode: {mode}]")
        print(f"  d_out = {enc.d_out}")
        print(f"  n_nodes_per_layer = {enc.n_nodes_per_layer}")
        print(f"  embedding shape = {enc.embedding.shape}")

        batch_size = 4
        dummy = (rng.random((batch_size, 16)) < 0.5).astype(np.float64)
        codes = enc.encode(dummy)
        expected_shape = (batch_size, 10 * enc.d_out)
        assert codes.shape == expected_shape
        print(f"  Forward pass: {dummy.shape} -> {codes.shape}  [OK]")

        n_params = enc.get_parameter_count()
        print(f"  Parameter count = {n_params}")

        mses = enc.compute_reconstruction_mse(dummy)
        assert len(mses) == 3
        print(f"  Reconstruction MSEs = {[f'{m:.4f}' for m in mses]}")

        dataset = (rng.random((64, 16)) < 0.5).astype(np.float64)
        info = enc.train(dataset, epochs_per_layer=3, lr=0.01, batch_size=16)
        assert len(info["loss_history"]) == 3 * 3
        print(f"  Training completed, {len(info['loss_history'])} loss entries  [OK]")

        if mode == "cross_layer":
            weights_0 = enc.layer_nodes[0].W_enc.copy()
            for l in range(1, enc.n_layers):
                assert np.allclose(enc.layer_nodes[l].W_enc, weights_0)
            print("  Cross-layer weight sync verified  [OK]")

    print("\n" + "-" * 60)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 60)
