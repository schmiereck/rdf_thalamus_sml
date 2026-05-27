import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class PredictiveCodingEncoder(EncoderBase):
    """
    P0-E: Predictive Coding Encoder — local-error / Hebbian baseline.

    A single hidden layer learns to predict the input via top-down weights.
    The local prediction error drives learning in both forward and backward
    pathways.  Lateral inhibition competes activations, producing a sparse,
    distributed code.
    """

    def __init__(self, dim_in=3, dim_out=16, seed=42, lr=0.1, sparsity_threshold=0.05):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr = lr
        self.sparsity_threshold = sparsity_threshold
        rng = np.random.default_rng(seed)
        # Forward (bottom-up) weights
        self.W_f = rng.standard_normal((dim_in, dim_out)) * 0.1
        self.b_f = np.zeros(dim_out)
        # Backward (top-down / prediction) weights
        self.W_b = rng.standard_normal((dim_out, dim_in)) * 0.1
        self.b_b = np.zeros(dim_in)
        # Lateral inhibition matrix (constant, not learned)
        self.W_lat = -0.1 * np.eye(dim_out)
        off_diag = rng.standard_normal((dim_out, dim_out)) * 0.01
        np.fill_diagonal(off_diag, 0)
        self.W_lat += off_diag
        self._L = np.eye(dim_out) + self.W_lat
        self._L_T = self._L.T

    def _activate(self, x):
        """Bottom-up activation with lateral inhibition."""
        z1 = x @ self.W_f + self.b_f
        h1 = np.maximum(0, z1)
        z2 = h1 @ self._L
        h = np.maximum(0, z2)
        return h

    def _predict(self, h):
        """Top-down prediction from hidden state."""
        return h @ self.W_b + self.b_b

    def train(self, inputs, epochs=200):
        n = inputs.shape[0]
        loss_history = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            for x in inputs:
                # Forward pass
                z1 = x @ self.W_f + self.b_f
                h1 = np.maximum(0, z1)
                z2 = h1 @ self._L
                h = np.maximum(0, z2)
                pred = self._predict(h)

                # Prediction error (local learning signal)
                error = x - pred
                loss = np.mean(error ** 2)
                epoch_loss += loss

                # Update prediction (backward) weights
                d_W_b = np.outer(h, error)
                d_b_b = error

                # Backpropagate error to hidden layer
                d_h = error @ self.W_b.T
                d_z2 = d_h * (z2 > 0).astype(float)
                d_h1 = d_z2 @ self._L_T
                d_z1 = d_h1 * (z1 > 0).astype(float)

                # Update forward weights
                d_W_f = np.outer(x, d_z1)
                d_b_f = d_z1

                # Gradient descent
                self.W_b += self.lr * d_W_b / n
                self.b_b += self.lr * d_b_b / n
                self.W_f += self.lr * d_W_f / n
                self.b_f += self.lr * d_b_f / n

            loss_history.append(epoch_loss / n)

        return {"final_loss": float(loss_history[-1]), "loss_history": loss_history}

    def encode(self, inputs):
        h = self._activate(inputs)
        h = np.where(np.abs(h) > self.sparsity_threshold, h, 0.0)
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

    enc = PredictiveCodingEncoder(seed=42)
    metrics = enc.train(all_samples, epochs=200)
    print("[PredictiveCodingEncoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[PredictiveCodingEncoder] Encoded shape:", codes.shape)
    print("[PredictiveCodingEncoder] Codes:\n", codes)
    print("[PredictiveCodingEncoder] Sparsity:", np.mean(np.abs(codes) < 0.01))

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[PredictiveCodingEncoder] Spearman rho={rho:.4f}, p={p_val:.4e}")
