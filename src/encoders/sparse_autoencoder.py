import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class SparseAutoencoder(EncoderBase):
    """P0-D: Sparse Autoencoder — GLOBAL OPTIMIZATION BASELINE (expected rho >= 0.6)."""

    def __init__(self, dim_in=3, dim_out=16, seed=42, lr=0.05, l1_lambda=0.005):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr = lr
        self.l1_lambda = l1_lambda
        rng = np.random.default_rng(seed)
        # Xavier initialization
        self.W1 = rng.standard_normal((dim_in, dim_out)) * np.sqrt(2.0 / dim_in)
        self.b1 = np.zeros(dim_out)
        self.W2 = rng.standard_normal((dim_out, dim_in)) * np.sqrt(2.0 / dim_out)
        self.b2 = np.zeros(dim_in)

    @staticmethod
    def _relu(x):
        return np.maximum(0, x)

    @staticmethod
    def _relu_deriv(x):
        return (x > 0).astype(np.float64)

    def _forward(self, x):
        # x: shape (dim_in,) or (batch, dim_in)
        z1 = x @ self.W1 + self.b1  # pre-activation
        h = self._relu(z1)          # hidden code
        z2 = h @ self.W2 + self.b2  # reconstruction (linear)
        return z1, h, z2

    def train(self, inputs, epochs=200):
        n = inputs.shape[0]
        loss_history = []
        for epoch in range(epochs):
            # Forward pass (full batch)
            z1 = inputs @ self.W1 + self.b1
            h = self._relu(z1)
            recon = h @ self.W2 + self.b2

            # Loss: MSE + L1
            mse = np.mean((inputs - recon) ** 2)
            l1 = self.l1_lambda * np.mean(np.abs(h))
            loss = mse + l1
            loss_history.append(loss)

            # Backward pass
            # d_loss/d_recon = 2/n * (recon - inputs)
            d_recon = 2.0 / n * (recon - inputs)

            # d_loss/d_W2 = h^T @ d_recon
            d_W2 = h.T @ d_recon
            d_b2 = np.sum(d_recon, axis=0)

            # d_loss/d_h = d_recon @ W2^T
            d_h = d_recon @ self.W2.T

            # Add L1 gradient: d/dh of l1_lambda * mean(|h|) = l1_lambda * sign(h) / n
            d_h += self.l1_lambda * np.sign(h) / n

            # d_loss/d_z1 = d_h * relu_deriv(z1)
            d_z1 = d_h * self._relu_deriv(z1)

            d_W1 = inputs.T @ d_z1
            d_b1 = np.sum(d_z1, axis=0)

            # Gradient descent
            self.W1 -= self.lr * d_W1
            self.b1 -= self.lr * d_b1
            self.W2 -= self.lr * d_W2
            self.b2 -= self.lr * d_b2

        return {"final_loss": float(loss_history[-1]), "loss_history": loss_history}

    def encode(self, inputs):
        z1 = inputs @ self.W1 + self.b1
        h = self._relu(z1)
        return h

    @property
    def dim_out(self):
        return self._dim_out


# ---------------------------------------------------------------------------
# Standalone sanity test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from harness import DatasetGenerator, SimilarityEvaluator

    ds = DatasetGenerator(seed=42)
    base = ds.get_base_states()
    all_samples = ds.get_all_samples()

    enc = SparseAutoencoder(seed=42)
    metrics = enc.train(all_samples, epochs=200)
    print("[SparseAutoencoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[SparseAutoencoder] Encoded shape:", codes.shape)
    print("[SparseAutoencoder] Codes:\n", codes)
    print("[SparseAutoencoder] Sparsity:", np.mean(np.abs(codes) < 0.01))

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[SparseAutoencoder] Spearman rho={rho:.4f}, p={p_val:.4e}")
