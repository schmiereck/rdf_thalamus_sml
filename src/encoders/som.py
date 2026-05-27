import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class SOMEncoder(EncoderBase):
    """
    P0-C: Kohonen Self-Organizing Map encoder.

    A 1-D SOM with dim_out=16 neurons is trained on the 3-bit input space.
    The *code* for an input is the vector of (normalised, clipped) Euclidean
    distances from the input to **every** SOM unit.  This makes the code
    distributed and topology-preserving: inputs that lie close in data space
    will have similar distance patterns across the map.
    """

    def __init__(self, dim_in=3, dim_out=16, seed=42, lr_init=0.5, lr_final=0.01,
                 radius_init=4.0, radius_final=0.5):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr_init = lr_init
        self.lr_final = lr_final
        self.radius_init = radius_init
        self.radius_final = radius_final
        rng = np.random.default_rng(seed)
        # Initialize weights randomly in [0, 1]
        self.weights = rng.uniform(0.0, 1.0, size=(dim_out, dim_in))
        # Grid positions for 1D SOM
        self.positions = np.arange(dim_out, dtype=np.float64)

    def _find_bmu(self, x):
        dists = np.sum((self.weights - x) ** 2, axis=1)
        return np.argmin(dists)

    def _neighborhood(self, bmu, radius):
        dists = np.abs(self.positions - bmu)
        return np.exp(-(dists ** 2) / (2 * radius ** 2))

    def train(self, inputs, epochs=200):
        n_samples = inputs.shape[0]
        for epoch in range(epochs):
            t = epoch / max(epochs - 1, 1)
            lr = self.lr_init * (1 - t) + self.lr_final * t
            radius = self.radius_init * (1 - t) + self.radius_final * t
            for x in inputs:
                bmu = self._find_bmu(x)
                h = self._neighborhood(bmu, radius)
                # Update: move weights toward input proportional to neighborhood
                self.weights += lr * h[:, np.newaxis] * (x - self.weights)
        return {"final_loss": 0.0}

    def encode(self, inputs):
        """
        Encode as the vector of inverse Euclidean distances to all SOM units.
        Similar inputs → similar distance vectors → high cosine similarity.
        """
        # inputs shape: (n_samples, dim_in)
        # self.weights shape: (dim_out, dim_in)
        diff = inputs[:, np.newaxis, :] - self.weights[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diff ** 2, axis=2) + 1e-8)  # (n_samples, dim_out)
        # Inverse distance: smaller raw distance → larger code value
        codes = 1.0 / (1.0 + dists)
        return codes

    @property
    def dim_out(self):
        return self._dim_out


# ---------------------------------------------------------------------------
# Standalone sanity test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from harness import DatasetGenerator, SimilarityEvaluator, compute_sparsity

    ds = DatasetGenerator(seed=42)
    base = ds.get_base_states()
    all_samples = ds.get_all_samples()

    enc = SOMEncoder(seed=42)
    metrics = enc.train(all_samples, epochs=200)
    print("[SOMEncoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[SOMEncoder] Encoded shape:", codes.shape)
    print("[SOMEncoder] Codes:\n", np.round(codes, 3))

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[SOMEncoder] Spearman rho={rho:.4f}, p={p_val:.4e}")
    print(f"[SOMEncoder] Sparsity={compute_sparsity(codes):.4f}")
