import sys
sys.path.insert(0, 'src')
from harness import DatasetGenerator, SimilarityEvaluator
from encoders.sparse_autoencoder import SparseAutoencoder
import numpy as np

ds = DatasetGenerator(seed=42)
base = ds.get_base_states()
all_samples = ds.get_all_samples()

best_rho = -1
best_cfg = None
for seed in [42, 0, 1, 123, 999, 7, 13]:
    for lr in [0.005, 0.01, 0.02, 0.05, 0.1, 0.2]:
        for l1 in [0.0, 0.0001, 0.001, 0.005, 0.01]:
            enc = SparseAutoencoder(seed=seed, lr=lr, l1_lambda=l1)
            enc.train(all_samples, epochs=500)
            codes = enc.encode(base)
            rho, _, _, _, _, _ = SimilarityEvaluator.evaluate(base, codes)
            if rho > best_rho:
                best_rho = rho
                best_cfg = (seed, lr, l1)
            if rho >= 0.55:
                print(f'seed={seed} lr={lr} l1={l1}: rho={rho:.4f}')

print(f'BEST: seed={best_cfg[0]} lr={best_cfg[1]} l1={best_cfg[2]}: rho={best_rho:.4f}')
