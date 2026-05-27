import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class SpatialPoolerEncoder(EncoderBase):
    """
    P0-B: SDR / Spatial Pooler encoder.

    Uses competitive learning (k-means-like prototype learning) combined
    with a distance-based code.  Each of the dim_out columns learns a
    prototype in input space.  The code for an input is its (normalised)
    distance to **all** prototypes, making the code *distributed* and
    similarity-preserving: two inputs with small Hamming distance will
    have similar patterns of distances to the prototype set.

    Sparsification: only the top-k strongest activations are kept,
    preserving the SDR character of the encoding.
    """

    def __init__(self, dim_in=3, dim_out=16, k_winners=5, seed=42,
                 lr_init=0.2, lr_final=0.01, sparsity_k=5):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.k_winners = k_winners
        self.lr_init = lr_init
        self.lr_final = lr_final
        self.sparsity_k = sparsity_k
        rng = np.random.default_rng(seed)
        # Prototypes: each row = one column's centre in input space
        self.prototypes = rng.uniform(0.0, 1.0, size=(dim_out, dim_in))

    def _get_lr(self, epoch, max_epochs):
        t = epoch / max(max_epochs - 1, 1)
        return self.lr_init * (1 - t) + self.lr_final * t

    def _encode_dense(self, inputs):
        """Return inverse-Euclidean-distance to every prototype."""
        diff = inputs[:, np.newaxis, :] - self.prototypes[np.newaxis, :, :]
        dist = np.sqrt(np.sum(diff ** 2, axis=2) + 1e-8)
        return 1.0 / (1.0 + dist)

    def train(self, inputs, epochs=200):
        for epoch in range(epochs):
            lr = self._get_lr(epoch, epochs)
            for x in inputs:
                # Find the k nearest prototypes (BMU competition)
                dist = np.sum((self.prototypes - x) ** 2, axis=1)
                winners = np.argsort(dist)[:self.k_winners]
                # Move winners toward the input (Hebbian / competitive)
                for w in winners:
                    self.prototypes[w] += lr * (x - self.prototypes[w])
                # Clip prototypes to [0, 1]
                self.prototypes = np.clip(self.prototypes, 0.0, 1.0)
        return {"final_loss": 0.0}

    def encode(self, inputs):
        """
        Encode using inverse-distance, then apply top-k sparsification
        to preserve the SDR character.
        """
        dense = self._encode_dense(inputs)
        # Top-k sparsification per sample
        codes = np.zeros_like(dense)
        for i in range(dense.shape[0]):
            top_k = np.argsort(dense[i])[-self.sparsity_k:]
            codes[i, top_k] = dense[i, top_k]
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

    enc = SpatialPoolerEncoder(seed=42)
    metrics = enc.train(all_samples, epochs=200)
    print("[SpatialPoolerEncoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[SpatialPoolerEncoder] Encoded shape:", codes.shape)
    print("[SpatialPoolerEncoder] Codes:\n", np.round(codes, 3))

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[SpatialPoolerEncoder] Spearman rho={rho:.4f}, p={p_val:.4e}")
    print(f"[SpatialPoolerEncoder] Sparsity={compute_sparsity(codes):.4f}")
