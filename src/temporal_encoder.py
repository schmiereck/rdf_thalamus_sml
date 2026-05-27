"""
Temporal Encoders for Phase 2.

Implements four temporal integration mechanisms:
  - P2DEncoder : Three-temporal-slot UniversalNode (sliding window over time)
  - P2AEncoder : Average-pool non-overlapping blocks of N=3 steps
  - P2BEncoder : Recurrent RNN with tanh update
  - P2CEncoder : Feedback previous code to 3-slot input

All encoders accept (B, T, d) and produce (B, T, d_out).
"""

from __future__ import annotations

import numpy as np

from node import UniversalNode


# ---------------------------------------------------------------------------
#  P2-D: Three-temporal-slot sliding-window node
# ---------------------------------------------------------------------------

class P2DEncoder:
    """
    Sliding-window temporal node.

    Accepts (B, T, d). Generates sliding window triplets of shape
    (B, T-2, 3, d). Feeds to a UniversalNode to produce (B*(T-2), d_out).
    Reshapes to (B, T-2, d_out) and pads with 2 steps of zeros at the
    beginning to yield (B, T, d_out).
    """

    def __init__(self, d: int = 16, d_out: int | None = None, seed: int = 42, l1_lambda: float = 0.0):
        self.d = d
        self.d_out = d_out if d_out is not None else 3 * d
        self.seed = seed
        self.node = UniversalNode(d=d, l1_lambda=l1_lambda, seed=seed, d_out=self.d_out)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Parameters
        ----------
        x : np.ndarray, shape (B, T, d)

        Returns
        -------
        codes : np.ndarray, shape (B, T, d_out)
        """
        B, T, d = x.shape
        assert d == self.d

        if T < 3:
            return np.zeros((B, T, self.d_out), dtype=x.dtype)

        # Build sliding windows: (B, T-2, 3, d)
        triplets = np.stack([x[:, :-2, :], x[:, 1:-1, :], x[:, 2:, :]], axis=2)
        triplets_flat = triplets.reshape(-1, 3, d)
        codes_flat = self.node.forward(triplets_flat)
        codes = codes_flat.reshape(B, T - 2, self.d_out)
        pad = np.zeros((B, 2, self.d_out), dtype=codes.dtype)
        return np.concatenate([pad, codes], axis=1)

    def compute_gradients(self, x: np.ndarray, dL_dcodes: np.ndarray) -> dict:
        """
        Backpropagate code gradients through the node.

        Parameters
        ----------
        x : np.ndarray, shape (B, T, d)
        dL_dcodes : np.ndarray, shape (B, T, d_out)

        Returns
        -------
        dict with keys 'W_enc', 'b_enc', 'x'
        """
        B, T, d = x.shape
        if T < 3:
            return {
                "W_enc": np.zeros_like(self.node.W_enc),
                "b_enc": np.zeros_like(self.node.b_enc),
                "x": np.zeros_like(x),
            }

        triplets = np.stack([x[:, :-2, :], x[:, 1:-1, :], x[:, 2:, :]], axis=2)
        triplets_flat = triplets.reshape(-1, 3, d)

        dL_dcodes_valid = dL_dcodes[:, 2:, :]
        dL_dcodes_flat = dL_dcodes_valid.reshape(-1, self.d_out)

        codes_flat = self.node.forward(triplets_flat)
        dL_dz = dL_dcodes_flat * (1.0 - codes_flat ** 2)

        x_flat = triplets_flat.reshape(-1, self.node.d_in)
        dW_enc = x_flat.T @ dL_dz / B
        db_enc = dL_dz.mean(axis=0)

        dL_dx_flat = dL_dz @ self.node.W_enc.T
        dL_dx_triplets = dL_dx_flat.reshape(B, T - 2, 3, d)

        dL_dx = np.zeros_like(x)
        dL_dx[:, :-2, :] += dL_dx_triplets[:, :, 0, :]
        dL_dx[:, 1:-1, :] += dL_dx_triplets[:, :, 1, :]
        dL_dx[:, 2:, :] += dL_dx_triplets[:, :, 2, :]

        return {
            "W_enc": dW_enc,
            "b_enc": db_enc,
            "x": dL_dx,
        }

    def apply_encoder_gradients(self, grads: dict, lr: float) -> None:
        self.node.W_enc -= lr * grads["W_enc"]
        self.node.b_enc -= lr * grads["b_enc"]


# ---------------------------------------------------------------------------
#  P2-A: Average-pool non-overlapping blocks of N=3
# ---------------------------------------------------------------------------

class P2AEncoder:
    """
    Average-pool non-overlapping blocks of N=3 steps.
    Receives (p_{k-2}, p_{k-1}, p_k) as 3-slot input.
    Repeats code over block steps to match shape (B, T, d_out).
    """

    def __init__(self, d: int = 16, d_out: int | None = None, N: int = 3, seed: int = 42, l1_lambda: float = 0.0):
        self.d = d
        self.N = N
        self.d_out = d_out if d_out is not None else 3 * d
        self.node = UniversalNode(d=d, l1_lambda=l1_lambda, seed=seed, d_out=self.d_out)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Parameters
        ----------
        x : np.ndarray, shape (B, T, d)

        Returns
        -------
        codes : np.ndarray, shape (B, T, d_out)
        """
        B, T, d = x.shape
        assert d == self.d

        pad_len = (self.N - T % self.N) % self.N
        if pad_len > 0:
            x_padded = np.concatenate([x, np.zeros((B, pad_len, d), dtype=x.dtype)], axis=1)
        else:
            x_padded = x

        T_pad = x_padded.shape[1]
        n_blocks = T_pad // self.N

        blocks = x_padded.reshape(B, n_blocks, self.N, d)
        pooled = blocks.mean(axis=2)
        pooled_expanded = np.repeat(pooled[:, :, None, :], self.N, axis=2)
        pooled_flat = pooled_expanded.reshape(-1, self.N, d)
        codes_flat = self.node.forward(pooled_flat)
        codes_blocks = codes_flat.reshape(B, n_blocks, self.d_out)
        codes_repeated = np.repeat(codes_blocks, self.N, axis=1)
        return codes_repeated[:, :T, :]


# ---------------------------------------------------------------------------
#  P2-B: Recurrent RNN
# ---------------------------------------------------------------------------

class P2BEncoder:
    """
    Recurrent RNN with tanh update.
    h_t = tanh(x_t @ W_xh + h_{t-1} @ W_hh + b_h)
    """

    def __init__(self, d: int = 16, d_out: int | None = None, seed: int = 42):
        self.d = d
        self.d_out = d_out if d_out is not None else d
        rng = np.random.default_rng(seed)

        scale_xh = np.sqrt(2.0 / (d + self.d_out))
        scale_hh = np.sqrt(2.0 / (self.d_out + self.d_out))

        self.W_xh = rng.standard_normal((d, self.d_out)) * scale_xh
        self.W_hh = rng.standard_normal((self.d_out, self.d_out)) * scale_hh
        self.b_h = np.zeros(self.d_out)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Parameters
        ----------
        x : np.ndarray, shape (B, T, d)

        Returns
        -------
        codes : np.ndarray, shape (B, T, d_out)
        """
        B, T, d = x.shape
        codes = np.zeros((B, T, self.d_out), dtype=x.dtype)
        h = np.zeros((B, self.d_out), dtype=x.dtype)

        for t in range(T):
            h = np.tanh(x[:, t, :] @ self.W_xh + h @ self.W_hh + self.b_h)
            codes[:, t, :] = h

        return codes

    def compute_gradients(self, x: np.ndarray, dL_dcodes: np.ndarray) -> dict:
        """BPTT for the simple RNN."""
        B, T, d = x.shape
        dW_xh = np.zeros_like(self.W_xh)
        dW_hh = np.zeros_like(self.W_hh)
        db_h = np.zeros_like(self.b_h)
        dL_dx = np.zeros_like(x)

        dh_next = np.zeros((B, self.d_out))

        h_cache = np.zeros((B, T, self.d_out))
        h = np.zeros((B, self.d_out))
        for t in range(T):
            h = np.tanh(x[:, t, :] @ self.W_xh + h @ self.W_hh + self.b_h)
            h_cache[:, t, :] = h

        for t in reversed(range(T)):
            dh = dL_dcodes[:, t, :] + dh_next
            dtanh = dh * (1.0 - h_cache[:, t, :] ** 2)

            dW_xh += x[:, t, :].T @ dtanh / B
            if t > 0:
                dW_hh += h_cache[:, t - 1, :].T @ dtanh / B
            db_h += dtanh.mean(axis=0)

            dL_dx[:, t, :] = dtanh @ self.W_xh.T
            dh_next = dtanh @ self.W_hh.T

        return {
            "W_xh": dW_xh,
            "W_hh": dW_hh,
            "b_h": db_h,
            "x": dL_dx,
        }

    def apply_gradients(self, grads: dict, lr: float) -> None:
        self.W_xh -= lr * grads["W_xh"]
        self.W_hh -= lr * grads["W_hh"]
        self.b_h -= lr * grads["b_h"]


# ---------------------------------------------------------------------------
#  P2-C: Feedback previous code into 3-slot input
# ---------------------------------------------------------------------------

class P2CEncoder:
    """
    Feedback previous code to 3-slot input:
      slot 0 = code_{t-1} (previous output, d_out dim)
      slot 1 = embedding_{t-1}
      slot 2 = embedding_t

    The node expects 3 slots each of dimension d. We project code_{t-1}
    from d_out down to d via a learned linear projection W_proj.
    """

    def __init__(self, d: int = 16, d_out: int | None = None, seed: int = 42, l1_lambda: float = 0.0):
        self.d = d
        self.d_out = d_out if d_out is not None else 3 * d
        self.node = UniversalNode(d=d, l1_lambda=l1_lambda, seed=seed, d_out=self.d_out)

        rng = np.random.default_rng(seed + 1)
        scale = np.sqrt(2.0 / (self.d_out + d))
        self.W_proj = rng.standard_normal((self.d_out, d)) * scale

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Parameters
        ----------
        x : np.ndarray, shape (B, T, d)

        Returns
        -------
        codes : np.ndarray, shape (B, T, d_out)
        """
        B, T, d = x.shape
        codes = np.zeros((B, T, self.d_out), dtype=x.dtype)
        prev_code = np.zeros((B, self.d_out), dtype=x.dtype)

        for t in range(T):
            slot0 = prev_code @ self.W_proj
            slot1 = x[:, t, :] if t == 0 else x[:, t - 1, :]
            slot2 = x[:, t, :]

            triplet = np.stack([slot0, slot1, slot2], axis=1)
            code = self.node.forward(triplet)
            codes[:, t, :] = code
            prev_code = code

        return codes

    def compute_gradients(self, x: np.ndarray, dL_dcodes: np.ndarray) -> dict:
        """Backprop through the feedback loop."""
        B, T, d = x.shape
        dW_proj = np.zeros_like(self.W_proj)
        dW_enc = np.zeros_like(self.node.W_enc)
        db_enc = np.zeros_like(self.node.b_enc)
        dL_dx = np.zeros_like(x)

        # Forward cache
        codes = np.zeros((B, T, self.d_out))
        prev_code = np.zeros((B, self.d_out))
        triplet_list = []
        slot0_list = []

        for t in range(T):
            slot0 = prev_code @ self.W_proj
            slot1 = x[:, t, :] if t == 0 else x[:, t - 1, :]
            slot2 = x[:, t, :]
            triplet = np.stack([slot0, slot1, slot2], axis=1)
            triplet_list.append(triplet)
            slot0_list.append(slot0)
            code = self.node.forward(triplet)
            codes[:, t, :] = code
            prev_code = code

        # Backward through time
        d_prev_code = np.zeros((B, self.d_out))

        for t in reversed(range(T)):
            triplet = triplet_list[t]
            dL_da = dL_dcodes[:, t, :] + d_prev_code
            code = codes[:, t, :]
            dL_dz = dL_da * (1.0 - code ** 2)

            x_flat = triplet.reshape(B, -1)
            dW_enc += x_flat.T @ dL_dz / B
            db_enc += dL_dz.mean(axis=0)

            dL_dtriplet_flat = dL_dz @ self.node.W_enc.T
            dL_dtriplet = dL_dtriplet_flat.reshape(B, 3, d)

            # slot0 = prev_code @ W_proj
            if t > 0:
                # dW_proj += prev_code_{t-1}^T @ dL_dslot0
                prev_code_tminus1 = codes[:, t - 1, :]
                dW_proj += prev_code_tminus1.T @ dL_dtriplet[:, 0, :] / B
                d_prev_code = dL_dtriplet[:, 0, :] @ self.W_proj.T
            else:
                d_prev_code = np.zeros((B, self.d_out))

            # slot1 = x_{t-1} (or x_0 at t=0)
            if t > 0:
                dL_dx[:, t - 1, :] += dL_dtriplet[:, 1, :]
            # slot2 = x_t
            dL_dx[:, t, :] += dL_dtriplet[:, 2, :]

        return {
            "W_enc": dW_enc,
            "b_enc": db_enc,
            "W_proj": dW_proj,
            "x": dL_dx,
        }

    def apply_encoder_gradients(self, grads: dict, lr: float) -> None:
        self.node.W_enc -= lr * grads["W_enc"]
        self.node.b_enc -= lr * grads["b_enc"]
        self.W_proj -= lr * grads["W_proj"]


# ---------------------------------------------------------------------------
#  Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Temporal Encoders -- Self-Test")
    print("=" * 60)

    rng = np.random.default_rng(7)
    B, T, d = 4, 64, 16
    x = rng.standard_normal((B, T, d))

    # --- P2-D ---
    print("\n--- P2-D ---")
    enc_d = P2DEncoder(d=d, d_out=16, seed=42)
    out_d = enc_d.forward(x)
    assert out_d.shape == (B, T, 16), f"Expected (4, 64, 16), got {out_d.shape}"
    print(f"  Input: {x.shape} -> Output: {out_d.shape}  [OK]")
    assert np.allclose(out_d[:, :2, :], 0.0), "First 2 timesteps should be zero-padded"
    print("  Zero-padding at t=0,1: PASS")

    dL = rng.standard_normal(out_d.shape)
    grads = enc_d.compute_gradients(x, dL)
    assert grads["W_enc"].shape == enc_d.node.W_enc.shape
    assert grads["b_enc"].shape == enc_d.node.b_enc.shape
    assert grads["x"].shape == x.shape
    print("  Gradient shapes: PASS")

    # --- P2-A ---
    print("\n--- P2-A ---")
    enc_a = P2AEncoder(d=d, d_out=16, N=3, seed=42)
    out_a = enc_a.forward(x)
    assert out_a.shape == (B, T, 16), f"Expected (4, 64, 16), got {out_a.shape}"
    print(f"  Input: {x.shape} -> Output: {out_a.shape}  [OK]")

    # --- P2-B ---
    print("\n--- P2-B ---")
    enc_b = P2BEncoder(d=d, d_out=16, seed=42)
    out_b = enc_b.forward(x)
    assert out_b.shape == (B, T, 16), f"Expected (4, 64, 16), got {out_b.shape}"
    print(f"  Input: {x.shape} -> Output: {out_b.shape}  [OK]")

    grads_b = enc_b.compute_gradients(x, dL[:, :, :16])
    assert grads_b["W_xh"].shape == enc_b.W_xh.shape
    assert grads_b["W_hh"].shape == enc_b.W_hh.shape
    print("  Gradient shapes: PASS")

    # --- P2-C ---
    print("\n--- P2-C ---")
    enc_c = P2CEncoder(d=d, d_out=16, seed=42)
    out_c = enc_c.forward(x)
    assert out_c.shape == (B, T, 16), f"Expected (4, 64, 16), got {out_c.shape}"
    print(f"  Input: {x.shape} -> Output: {out_c.shape}  [OK]")

    grads_c = enc_c.compute_gradients(x, dL[:, :, :16])
    assert grads_c["W_enc"].shape == enc_c.node.W_enc.shape
    assert grads_c["W_proj"].shape == enc_c.W_proj.shape
    print("  Gradient shapes: PASS")

    print("\n" + "-" * 60)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 60)
