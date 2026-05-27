import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np


class LookupTableEncoder(EncoderBase):
    """P0-A: One-hot lookup table — NEGATIVE CONTROL (expected rho ~ 0)."""

    def __init__(self, dim_in=3, dim_out=8, seed=None):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self._mapping = {}  # state tuple -> one-hot index

    def train(self, inputs, epochs=1):
        # Just enumerate unique states
        for row in inputs:
            key = tuple(row)
            if key not in self._mapping:
                idx = len(self._mapping)
                self._mapping[key] = idx
        return {"final_loss": 0.0, "n_states": len(self._mapping)}

    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, row in enumerate(inputs):
            key = tuple(row)
            if key in self._mapping:
                codes[i, self._mapping[key]] = 1.0
        return codes

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

    enc = LookupTableEncoder(seed=42)
    metrics = enc.train(all_samples)
    print("[LookupTableEncoder] Train metrics:", metrics)

    codes = enc.encode(base)
    print("[LookupTableEncoder] Encoded shape:", codes.shape)
    print("[LookupTableEncoder] Codes:\n", codes)

    rho, p_val, *_ = SimilarityEvaluator.evaluate(base, codes)
    print(f"[LookupTableEncoder] Spearman rho={rho}, p={p_val}")
