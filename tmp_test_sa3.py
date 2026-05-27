import sys
sys.path.insert(0, 'src')
from harness import DatasetGenerator, SimilarityEvaluator
from encoders.sparse_autoencoder import SparseAutoencoder

ds = DatasetGenerator(seed=42)
base = ds.get_base_states()
all_samples = ds.get_all_samples()

for lr in [0.05, 0.1, 0.15]:
    for l1 in [0.001, 0.002, 0.005]:
        for epochs in [200, 500]:
            enc = SparseAutoencoder(seed=42, lr=lr, l1_lambda=l1)
            enc.train(all_samples, epochs=epochs)
            codes = enc.encode(base)
            rho, _, _, _, _, _ = SimilarityEvaluator.evaluate(base, codes)
            print(f'lr={lr} l1={l1} epochs={epochs}: rho={rho:.4f}')
