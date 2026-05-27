import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder
from eval_phase1 import evaluate_hierarchical_encoder

dataset = generate_phase1_dataset(seed=42)
print(f"Dataset: train_x={dataset['train_x'].shape}", flush=True)

for epochs in [100, 150]:
    enc = HierarchicalEncoder(n_input=16, d=8, n_layers=3, sharing_mode="cross_layer", l1_lambda=0.002, seed=42, d_out=24)
    t0 = time.time()
    enc.train(dataset=dataset["train_x"], epochs_per_layer=epochs, lr=0.01, batch_size=32)
    t1 = time.time()
    ev = evaluate_hierarchical_encoder(enc, dataset, seed=42)
    t2 = time.time()
    print(f"epochs={epochs}: train={t1-t0:.2f}s, eval={t2-t1:.2f}s, acc={ev['test_accuracy']:.4f}, spars={ev['sparsity']:.4f}", flush=True)
