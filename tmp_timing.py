"""Quick timing test"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from eval_phase1 import evaluate_hierarchical_encoder

print("Generating dataset...", flush=True)
dataset = generate_phase1_dataset(seed=42)
print("Dataset done", flush=True)

encoder = HierarchicalEncoder(n_input=16, d=8, n_layers=3, sharing_mode='cross_layer', seed=42, d_out=24)
print("Encoder created, n_params=", encoder.get_parameter_count(), flush=True)

t0 = time.time()
print("Training 100 epochs per layer...", flush=True)
info = encoder.train(dataset['train_x'], epochs_per_layer=100, lr=0.01, batch_size=32)
t1 = time.time()
print(f"Training took {t1-t0:.1f}s", flush=True)

t0 = time.time()
results = evaluate_hierarchical_encoder(encoder, dataset, seed=42)
t1 = time.time()
print(f"Eval took {t1-t0:.1f}s", flush=True)
print("Results:", results, flush=True)
