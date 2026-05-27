import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class SpatialPoolerEncoder(EncoderBase):
    """P0-B: HTM-style SDR encoder — random projection + k-WTA + Hebbian updates."""

    def __init__(self, dim_in=3, dim_out=16, k=5, seed=42, permanence_threshold=0.5,
                 perm_inc=0.1, perm_dec=0.05):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.k = k
        self.permanence_threshold = permanence_threshold
        self.perm_inc = perm_inc
        self.perm_dec = perm_dec
        rng = np.random.default_rng(seed)
        # Permanence matrix: how strongly connected each input is to each output
        self.permanence = rng.uniform(0.4, 0.6, size=(dim_in, dim_out))
        # Random potential pool
        self.potential_pool = rng.random((dim_in, dim_out)) < 0.8  # 80% connectivity

    def _connected(self):
        return (self.permanence >= self.permanence_threshold) & self.potential_pool

    def _forward(self, x):
        connected = self._connected().astype(np.float64)
        overlap = x @ (connected * self.permanence)  # (dim_out,)
        return overlap

    def _kwta(self, activations):
        result = np.zeros_like(activations)
        if self.k > 0 and len(activations) > 0:
            top_k = np.argsort(activations)[-self.k:]
            result[top_k] = activations[top_k]
        return result

    def train(self, inputs, epochs=50):
        for epoch in range(epochs):
            for x in inputs:
                overlap = self._forward(x)
                active = self._kwta(overlap)
                active_indices = active > 0
                # Update permanences
                for j in range(self._dim_out):
                    if active_indices[j]:
                        for i in range(self._dim_in):
                            if self.potential_pool[i, j]:
                                if x[i] > 0.5:
                                    self.permanence[i, j] += self.perm_inc
                                else:
                                    self.permanence[i, j] -= self.perm_dec
                self.permanence = np.clip(self.permanence, 0.0, 1.0)
        return {"final_loss": 0.0}

    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, x in enumerate(inputs):
            overlap = self._forward(x)
            codes[i] = self._kwta(overlap)
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
    metrics = enc.train(all_samples, epochs=50)
    print("[SpatialPoolerEncoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[SpatialPoolerEncoder] Encoded shape:", codes.shape)
    print("[SpatialPoolerEncoder] Codes:\n", codes)

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[SpatialPoolerEncoder] Spearman rho={rho}, p={p_val}")
    print(f"[SpatialPoolerEncoder] Sparsity={compute_sparsity(codes):.4f}")
