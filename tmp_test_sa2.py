import sys
sys.path.insert(0, 'src')
from harness import DatasetGenerator, SimilarityEvaluator
from encoders.sparse_autoencoder import SparseAutoencoder

ds = DatasetGenerator(seed=42)
base = ds.get_base_states()
all_samples = ds.get_all_samples()

best_rho = -1
best_cfg = None
for lr in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.15, 0.2]:
    for l1 in [0.0, 0.0001, 0.0005, 0.001, 0.002, 0.005, 0.007, 0.01, 0.015, 0.02]:
        for epochs in [200, 500, 1000]:
            enc = SparseAutoencoder(seed=42, lr=lr, l1_lambda=l1)
            enc.train(all_samples, epochs=epochs)
            codes = enc.encode(base)
            rho, _, _, _, _, _ = SimilarityEvaluator.evaluate(base, codes)
            if rho > best_rho:
                best_rho = rho
                best_cfg = (lr, l1, epochs)
            if rho >= 0.6:
                print(f'lr={lr} l1={l1} epochs={epochs}: rho={rho:.4f}')

print(f'BEST: lr={best_cfg[0]} l1={best_cfg[1]} epochs={best_cfg[2]}: rho={best_rho:.4f}')
