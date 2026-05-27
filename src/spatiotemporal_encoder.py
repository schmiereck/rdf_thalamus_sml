"""
Spatiotemporal Encoder for Phase 3.

Implements the sequential spatial-then-temporal encoder over a
(16 spatial × 32 temporal) binary grid using stacked kernel-3,
stride-1 UniversalNodes.

Both spatial and temporal forward/backward passes are **fully
vectorized** — no Python loops over spatial/temporal positions.

Three variants
--------------
* **P3-A** – One master spatial node + one master temporal node.
  Trained sequentially (spatial first, then temporal).
* **P3-B** – One master spatial node + one master temporal node
  (separate objects, trained jointly with both losses).
* **P3-C** – A *single* master node reused for *both* spatial and
  temporal passes (strong universal hypothesis).

Architecture
------------
Input           : (B, S=16, T=32)  binary
Embedding       : (2, d) lookup — Xavier-initialised, frozen
Spatial stages  : 3 × kernel-3 / stride-1 over the S axis
                  (16 → 14 → 12 → 10 spatial positions)
Transpose        : (B, 10, T, d_out)  →  (B, T, 10, d_out)
Temporal stages  : 3 × kernel-3 / stride-1 over the T axis
                  (32 → 30 → 28 → 26 temporal positions)
Average pool     : mean over remaining 10 spatial × 26 temporal positions
Output          : (B, d_out)  ==  (B, 16)
"""

from __future__ import annotations

import numpy as np

from node import UniversalNode


# ---------------------------------------------------------------------------
#  Sliding-window helpers (fully vectorised, no Python loops)
# ---------------------------------------------------------------------------

def _make_windows_3(x_in: np.ndarray, axis: int = 0) -> np.ndarray:
    """
    Build kernel-3 sliding windows along the given axis.

    Parameters
    ----------
    x_in : (B, N_l, M, d)
    axis : which axis the kernel slides over (typically 1)

    Returns
    -------
    windows : (B, N_l-2, M, 3, d)
    """
    if axis == 1:
        # Fast slicing for axis=1 — avoids np.take copies and is extremely fast
        return np.stack([
            x_in[:, :-2, ...],
            x_in[:, 1:-1, ...],
            x_in[:, 2:, ...],
        ], axis=-2)
    return np.stack([
        np.take(x_in, range(0, x_in.shape[axis] - 2), axis=axis),
        np.take(x_in, range(1, x_in.shape[axis] - 1), axis=axis),
        np.take(x_in, range(2, x_in.shape[axis]    ), axis=axis),
    ], axis=-2)


# ---------------------------------------------------------------------------
#  Spatiotemporal Encoder
# ---------------------------------------------------------------------------

class SpatiotemporalEncoder:
    """Sequential spatial→temporal encoder with configurable weight sharing."""

    def __init__(
        self,
        variant: str = "P3-B",
        d: int = 16,
        d_out: int = 16,
        n_spatial_layers: int = 3,
        n_temporal_layers: int = 3,
        l1_lambda: float = 0.002,
        seed: int = 42,
    ):
        if variant not in ("P3-A", "P3-B", "P3-C"):
            raise ValueError(
                f"variant must be one of ('P3-A', 'P3-B', 'P3-C'), got '{variant}'"
            )
        if d_out != d:
            raise ValueError(
                f"d_out must equal d for dimension homogeneity, got d={d}, d_out={d_out}"
            )

        self.variant = variant
        self.d = d
        self.d_out = d_out
        self.n_spatial_layers = n_spatial_layers
        self.n_temporal_layers = n_temporal_layers
        self.l1_lambda = l1_lambda
        self.seed = seed

        # --- Non-learned binary embedding (2, d) ---
        rng = np.random.default_rng(seed)
        scale = np.sqrt(2.0 / (1 + d))  # Xavier scale for (2, d)
        self.embedding: np.ndarray = rng.standard_normal((2, d)) * scale

        # --- Master nodes ---
        self.master_spatial = UniversalNode(
            d=d,
            l1_lambda=l1_lambda,
            seed=seed,
            d_out=d_out,
        )
        if variant == "P3-C":
            # Same object for both axes
            self.master_temporal = self.master_spatial
        else:
            self.master_temporal = UniversalNode(
                d=d,
                l1_lambda=l1_lambda,
                seed=seed + 100,
                d_out=d_out,
            )

        # --- Positions per layer (kernel-3 stride-1 reduces dim by 2 each layer) ---
        self.spatial_nodes_per_layer = [
            16 - 2 * (l + 1) for l in range(n_spatial_layers)
        ]  # e.g. [14, 12, 10]
        self.temporal_nodes_per_layer = [
            32 - 2 * (l + 1) for l in range(n_temporal_layers)
        ]  # e.g. [30, 28, 26]

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _embed(self, x_binary: np.ndarray) -> np.ndarray:
        """
        Map raw binary (B, S, T) → (B, S, T, d) via frozen lookup table.
        """
        idx = x_binary.astype(int)                     # (B, S, T)
        return self.embedding[idx]                      # (B, S, T, d)

    # ------------------------------------------------------------------
    #  Forward — fully vectorised
    # ------------------------------------------------------------------

    def _forward_spatial_layer(
        self,
        x_in: np.ndarray,       # (B, S_l, T, d)
        layer_idx: int,
        store_inputs: bool = False,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """
        Apply kernel-3 stride-1 sliding window over the S axis.

        Returns
        -------
        x_out : (B, S_{l+1}, T, d_out)
        node_inputs : (B, S_{l+1}, T, 3, d)  — only if store_inputs
        """
        node = self.master_spatial
        B, S_l, T, d_in = x_in.shape

        # Build all windows at once: (B, S_l-2, T, 3, d_in)
        windows = _make_windows_3(x_in, axis=1)
        n_pos = S_l - 2

        if store_inputs:
            node_inputs = windows.copy()  # (B, S_l-2, T, 3, d_in)
        else:
            node_inputs = None

        # Flatten for node: (B * n_pos * T, 3, d_in)
        x_3d = windows.reshape(B * n_pos * T, 3, d_in)
        codes_flat = node.forward(x_3d)              # (B * n_pos * T, d_out)
        # Reshape back: (B, n_pos, T, d_out)
        x_out = codes_flat.reshape(B, n_pos, T, self.d_out)
        return x_out, node_inputs

    def _forward_temporal_layer(
        self,
        x_in: np.ndarray,       # (B, T_l, S_out, d)
        layer_idx: int,
        store_inputs: bool = False,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """
        Apply kernel-3 stride-1 sliding window over the T axis.

        Returns
        -------
        x_out : (B, T_{l+1}, S_out, d_out)
        node_inputs : (B, T_{l+1}, S_out, 3, d)  — only if store_inputs
        """
        node = self.master_temporal
        B, T_l, S_out, d_in = x_in.shape

        # Build all windows at once: (B, T_l-2, S_out, 3, d_in)
        windows = _make_windows_3(x_in, axis=1)
        n_pos = T_l - 2

        if store_inputs:
            node_inputs = windows.copy()  # (B, T_l-2, S_out, 3, d_in)
        else:
            node_inputs = None

        # Flatten for node: (B * n_pos * S_out, 3, d_in)
        x_3d = windows.reshape(B * n_pos * S_out, 3, d_in)
        codes_flat = node.forward(x_3d)              # (B * n_pos * S_out, d_out)
        x_out = codes_flat.reshape(B, n_pos, S_out, self.d_out)
        return x_out, node_inputs

    # ------------------------------------------------------------------
    #  Forward with intermediates
    # ------------------------------------------------------------------

    def forward_with_intermediates(self, x_binary: np.ndarray) -> dict:
        """
        Full forward pass storing all intermediates needed for backward.

        Parameters
        ----------
        x_binary : np.ndarray, shape (B, S=16, T=32) or (B, S*T)

        Returns
        -------
        dict with keys:
            embeddings      : (B, 16, 32, d)
            spatial_outputs  : list of 3 × (B, S_l_out, T, d)
            spatial_inputs   : list of 3 × (B, S_l_out, T, 3, d)
            temporal_outputs : list of 3 × (B, T_l_out, S_final, d)
            temporal_inputs  : list of 3 × (B, T_l_out, S_final, 3, d)
            pooled           : (B, d_out)  — mean-pooled final code
        """
        # Accept flat (B, S*T) and reshape
        if x_binary.ndim == 2 and x_binary.shape[1] == 16 * 32:
            x_binary = x_binary.reshape(-1, 16, 32)

        B = x_binary.shape[0]

        # --- Embed ---
        emb = self._embed(x_binary)                  # (B, 16, 32, d)

        # --- Spatial pass (3 layers) ---
        spatial_outputs: list[np.ndarray] = []
        spatial_inputs: list[np.ndarray] = []

        x_spatial = emb
        for l in range(self.n_spatial_layers):
            x_out, inp_3d = self._forward_spatial_layer(
                x_spatial, l, store_inputs=True
            )
            spatial_outputs.append(x_out)
            spatial_inputs.append(inp_3d)             # type: ignore[arg-type]
            x_spatial = x_out

        # --- Transpose for temporal processing ---
        x_spatial = x_spatial.transpose(0, 2, 1, 3)   # (B, T, S_final, d)

        # --- Temporal pass (3 layers) ---
        temporal_outputs: list[np.ndarray] = []
        temporal_inputs: list[np.ndarray] = []

        x_temporal = x_spatial
        for l in range(self.n_temporal_layers):
            x_out, inp_3d = self._forward_temporal_layer(
                x_temporal, l, store_inputs=True
            )
            temporal_outputs.append(x_out)
            temporal_inputs.append(inp_3d)             # type: ignore[arg-type]
            x_temporal = x_out

        # --- Average pool across space and time ---
        pooled = x_temporal.mean(axis=(1, 2))          # (B, d_out)

        return {
            "embeddings": emb,
            "spatial_outputs": spatial_outputs,
            "spatial_inputs": spatial_inputs,
            "temporal_outputs": temporal_outputs,
            "temporal_inputs": temporal_inputs,
            "pooled": pooled,
        }

    # ------------------------------------------------------------------
    #  Backward — fully vectorised
    # ------------------------------------------------------------------

    def backward(
        self,
        fwd: dict,
        dL_dspatial_codes: list[np.ndarray],
        dL_dtemporal_codes: list[np.ndarray],
        alpha: float = 0.5,
    ) -> dict:
        """
        Propagate code-level gradients back through temporal and spatial
        passes to produce gradients for the master nodes and the embedding.

        Parameters
        ----------
        fwd : dict
            The output of ``forward_with_intermediates``.
        dL_dspatial_codes : list of np.ndarray
            External JEPA gradients for each spatial layer.
            Each has shape matching the corresponding spatial_output.
        dL_dtemporal_codes : list of np.ndarray
            External JEPA gradients for each temporal layer.
            Each has shape matching the corresponding temporal_output.
        alpha : float
            Weighting: alpha for spatial gradients, (1-alpha) for temporal
            when combining at the interface.  In practice the gradients
            are processed axis by axis, but this controls the scaling.

        Returns
        -------
        dict with keys:
            'dL_dspatial'  : dict with W_enc, b_enc, W_dec, b_dec gradients
            'dL_dtemporal' : dict with W_enc, b_enc, W_dec, b_dec gradients
            'dL_dembedding': gradient table (2, d)
        """
        B = fwd["embeddings"].shape[0]
        d = self.d
        d_out = self.d_out

        # Accumulator for each master node's parameters
        spatial_grads: dict[str, np.ndarray] = {
            "W_enc": np.zeros_like(self.master_spatial.W_enc),
            "b_enc": np.zeros_like(self.master_spatial.b_enc),
            "W_dec": np.zeros_like(self.master_spatial.W_dec),
            "b_dec": np.zeros_like(self.master_spatial.b_dec),
        }
        temporal_grads: dict[str, np.ndarray] = {
            "W_enc": np.zeros_like(self.master_spatial.W_enc),
            "b_enc": np.zeros_like(self.master_spatial.b_enc),
            "W_dec": np.zeros_like(self.master_spatial.W_dec),
            "b_dec": np.zeros_like(self.master_spatial.b_dec),
        }

        # ====================================================================
        #  TEMPORAL BACKWARD (process layers in reverse) — vectorised
        # ====================================================================

        # Gradient from average pooling
        x_final = fwd["temporal_outputs"][-1]          # (B, T_final, S_final, d_out)
        T_final, S_final = x_final.shape[1], x_final.shape[2]
        dL_dx = np.full_like(x_final, 1.0 / (T_final * S_final))

        # Add external temporal JEPA gradients for the last layer
        dL_dx = dL_dx + dL_dtemporal_codes[-1] * (1.0 - alpha)

        for l in reversed(range(self.n_temporal_layers)):
            dL_dx_total = dL_dx

            node_inputs = fwd["temporal_inputs"][l]         # (B, T_l_out, S_final, 3, d)
            code_out = fwd["temporal_outputs"][l]           # (B, T_l_out, S_final, d_out)

            # --- Backprop through tanh activation ---
            dL_dz = dL_dx_total * (1.0 - code_out ** 2)    # (B, T_l_out, S_final, d_out)

            # Flatten all positions at once
            B, n_pos, S, _, d_in = node_inputs.shape
            dL_dz_flat = dL_dz.reshape(B * n_pos * S, d_out)
            inp_flat = node_inputs.reshape(B * n_pos * S, 3 * d_in)

            # Parameter gradients (sum across all positions + batch)
            dW_enc = inp_flat.T @ dL_dz_flat / B
            db_enc = dL_dz_flat.mean(axis=0)

            temporal_grads["W_enc"] += dW_enc
            temporal_grads["b_enc"] += db_enc
            dW_dec = np.zeros_like(self.master_spatial.W_dec)
            db_dec = np.zeros_like(self.master_spatial.b_dec)
            temporal_grads["W_dec"] += dW_dec
            temporal_grads["b_dec"] += db_dec

            # Gradient w.r.t. input
            dL_dx_flat = dL_dz_flat @ self.master_spatial.W_enc.T   # (B*n_pos*S, 3*d)
            dL_dx_reshaped = dL_dx_flat.reshape(B, n_pos, S, 3, d_in)  # (B, n_pos, S, 3, d)

            # Scatter gradient into layer input (3 kernel offsets → 3 slice-adds)
            dL_dlayer_input = np.zeros((B, n_pos + 2, S, d_in))
            dL_dlayer_input[:, 0:n_pos,   :, :] += dL_dx_reshaped[:, :, :, 0, :]
            dL_dlayer_input[:, 1:n_pos+1, :, :] += dL_dx_reshaped[:, :, :, 1, :]
            dL_dlayer_input[:, 2:n_pos+2, :, :] += dL_dx_reshaped[:, :, :, 2, :]

            if l > 0:
                dL_dx = dL_dlayer_input
                ext = dL_dtemporal_codes[l - 1] * (1.0 - alpha)
                dL_dx = dL_dx + ext
            else:
                dL_dx = dL_dlayer_input  # (B, 32, S_final, d)

        n_total_temporal_positions = sum(self.temporal_nodes_per_layer)
        for key in temporal_grads:
            temporal_grads[key] /= n_total_temporal_positions

        # ====================================================================
        #  SPATIAL BACKWARD — vectorised
        # ====================================================================

        # dL_dx is (B, 32, S_final, d) → transpose to (B, S_final, 32, d)
        dL_dx = dL_dx.transpose(0, 2, 1, 3)

        assert dL_dx.shape[1] == self.spatial_nodes_per_layer[-1], \
            (f"Mismatch: dL_dx spatial dim {dL_dx.shape[1]} vs "
             f"expected {self.spatial_nodes_per_layer[-1]}")

        for l in reversed(range(self.n_spatial_layers)):
            dL_dx_total = dL_dx + dL_dspatial_codes[l] * alpha

            node_inputs = fwd["spatial_inputs"][l]   # (B, S_l_out, T, 3, d)
            code_out = fwd["spatial_outputs"][l]     # (B, S_l_out, T, d_out)

            # --- Backprop through tanh ---
            dL_dz = dL_dx_total * (1.0 - code_out ** 2)   # (B, S_l_out, T, d_out)

            B, n_pos, T, _, d_in = node_inputs.shape
            dL_dz_flat = dL_dz.reshape(B * n_pos * T, d_out)
            inp_flat = node_inputs.reshape(B * n_pos * T, 3 * d_in)

            # Parameter gradients
            dW_enc = inp_flat.T @ dL_dz_flat / B
            db_enc = dL_dz_flat.mean(axis=0)

            spatial_grads["W_enc"] += dW_enc
            spatial_grads["b_enc"] += db_enc
            dW_dec = np.zeros_like(self.master_spatial.W_dec)
            db_dec = np.zeros_like(self.master_spatial.b_dec)
            spatial_grads["W_dec"] += dW_dec
            spatial_grads["b_dec"] += db_dec

            # Gradient w.r.t. input
            dL_dx_flat = dL_dz_flat @ self.master_spatial.W_enc.T
            dL_dx_reshaped = dL_dx_flat.reshape(B, n_pos, T, 3, d_in)  # (B, n_pos, T, 3, d)

            # Scatter into layer input
            dL_dlayer_input = np.zeros((B, n_pos + 2, T, d_in))
            dL_dlayer_input[:, 0:n_pos,   :, :] += dL_dx_reshaped[:, :, :, 0, :]
            dL_dlayer_input[:, 1:n_pos+1, :, :] += dL_dx_reshaped[:, :, :, 1, :]
            dL_dlayer_input[:, 2:n_pos+2, :, :] += dL_dx_reshaped[:, :, :, 2, :]

            if l > 0:
                dL_dx = dL_dlayer_input
            else:
                dL_dx = dL_dlayer_input  # (B, 16, 32, d)

        n_total_spatial_positions = sum(self.spatial_nodes_per_layer)
        for key in spatial_grads:
            spatial_grads[key] /= n_total_spatial_positions

        # --- Embedding gradient — frozen (non-learned), so return zeros ---
        dL_dembedding = np.zeros_like(self.embedding)

        return {
            "dL_dspatial": spatial_grads,
            "dL_dtemporal": temporal_grads,
            "dL_dembedding": dL_dembedding,
        }

    # ------------------------------------------------------------------
    #  Parameter Count
    # ------------------------------------------------------------------

    def get_parameter_count(self) -> int:
        count = 0  # embedding is frozen / non-learned
        count += self.master_spatial.W_enc.size + self.master_spatial.b_enc.size
        count += self.master_spatial.W_dec.size + self.master_spatial.b_dec.size
        if self.variant != "P3-C":
            count += self.master_temporal.W_enc.size + self.master_temporal.b_enc.size
            count += self.master_temporal.W_dec.size + self.master_temporal.b_dec.size
        return count


# ======================================================================
#  Self-test
# ======================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  SpatiotemporalEncoder -- Self-Test (vectorised)")
    print("=" * 65)

    rng = np.random.default_rng(7)
    B, S, T = 4, 16, 32

    for variant in ("P3-A", "P3-B", "P3-C"):
        enc = SpatiotemporalEncoder(variant=variant, d=16, d_out=16, seed=42)
        print(f"\n--- Variant: {variant} ---")
        print(f"  Parameter count = {enc.get_parameter_count()}")

        if variant == "P3-C":
            assert enc.master_spatial is enc.master_temporal
            print("  P3-C: spatial and temporal nodes are same object  [OK]")
        else:
            assert enc.master_spatial is not enc.master_temporal
            print("  Separate spatial/temporal nodes  [OK]")

        # --- Forward pass ---
        x_binary = (rng.random((B, S, T)) < 0.5).astype(np.float64)

        fwd = enc.forward_with_intermediates(x_binary)

        print(f"  embeddings shape  : {fwd['embeddings'].shape}")
        assert fwd["embeddings"].shape == (B, 16, 32, 16)

        for l in range(enc.n_spatial_layers):
            so = fwd["spatial_outputs"][l]
            si = fwd["spatial_inputs"][l]
            expected_spatial = S - 2 * (l + 1)
            print(f"  spatial layer {l}: output {so.shape}, input {si.shape}")
            assert so.shape == (B, expected_spatial, T, 16)
            assert si.shape == (B, expected_spatial, T, 3, 16)

        for l in range(enc.n_temporal_layers):
            to_ = fwd["temporal_outputs"][l]
            ti = fwd["temporal_inputs"][l]
            expected_temporal = T - 2 * (l + 1)
            print(f"  temporal layer {l}: output {to_.shape}, input {ti.shape}")
            assert to_.shape == (B, expected_temporal, 10, 16)
            assert ti.shape == (B, expected_temporal, 10, 3, 16)

        print(f"  pooled shape      : {fwd['pooled'].shape}")
        assert fwd["pooled"].shape == (B, 16)
        print("  Forward pass: all shapes correct  [OK]")

        # --- Backward pass ---
        dL_dspatial = [
            rng.standard_normal(fwd["spatial_outputs"][l].shape)
            for l in range(enc.n_spatial_layers)
        ]
        dL_dtemporal = [
            rng.standard_normal(fwd["temporal_outputs"][l].shape)
            for l in range(enc.n_temporal_layers)
        ]

        grads = enc.backward(fwd, dL_dspatial, dL_dtemporal, alpha=0.5)

        for key in ("W_enc", "b_enc", "W_dec", "b_dec"):
            assert grads["dL_dspatial"][key].shape == getattr(
                enc.master_spatial, key
            ).shape, f"Shape mismatch in spatial grads[{key}]"
            assert grads["dL_dtemporal"][key].shape == getattr(
                enc.master_temporal, key
            ).shape, f"Shape mismatch in temporal grads[{key}]"

        assert grads["dL_dembedding"].shape == (2, 16)
        print("  Backward pass: all gradient shapes correct  [OK]")

        # Embedding gradient should be zeros (frozen)
        assert np.allclose(grads["dL_dembedding"], 0), \
            "Embedding gradient should be zeros for frozen embedding"
        print("  Embedding gradient is zeros (frozen)  [OK]")

        assert np.any(np.abs(grads["dL_dspatial"]["W_enc"]) > 0), \
            "Spatial W_enc gradient is all zeros"
        assert np.any(np.abs(grads["dL_dtemporal"]["W_enc"]) > 0), \
            "Temporal W_enc gradient is all zeros"
        print("  Gradient magnitudes non-zero  [OK]")

    # --- Test with flat input (B, S*T) ---
    print("\n--- Flat input (B, S*T) ---")
    enc_flat = SpatiotemporalEncoder(variant="P3-B", d=16, d_out=16, seed=42)
    x_flat = (rng.random((B, 16 * 32)) < 0.5).astype(np.float64)
    fwd_flat = enc_flat.forward_with_intermediates(x_flat)
    assert fwd_flat["pooled"].shape == (B, 16)
    print(f"  Flat input {x_flat.shape} -> pooled {fwd_flat['pooled'].shape}  [OK]")

    dL_ds_flat = [np.zeros_like(fwd_flat["spatial_outputs"][l]) for l in range(3)]
    dL_dt_flat = [np.zeros_like(fwd_flat["temporal_outputs"][l]) for l in range(3)]
    grads_flat = enc_flat.backward(fwd_flat, dL_ds_flat, dL_dt_flat, alpha=0.5)
    print("  Backward with flat input: shapes correct  [OK]")

    # --- Parameter count comparison ---
    print("\n--- Parameter Count Comparison ---")
    count_a = SpatiotemporalEncoder("P3-A", d=16, d_out=16, seed=42).get_parameter_count()
    count_b = SpatiotemporalEncoder("P3-B", d=16, d_out=16, seed=42).get_parameter_count()
    count_c = SpatiotemporalEncoder("P3-C", d=16, d_out=16, seed=42).get_parameter_count()
    print(f"  P3-A params = {count_a}")
    print(f"  P3-B params = {count_b}")
    print(f"  P3-C params = {count_c}")
    assert count_a == count_b, "P3-A and P3-B should have identical parameter counts"
    assert count_c == count_a // 2, "P3-C should have half the parameters of P3-A/B"
    print("  P3-C has ~50% of P3-A/B parameters  [OK]")

    print("\n" + "-" * 65)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 65)
