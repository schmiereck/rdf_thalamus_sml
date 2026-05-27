"""Quick timing test for one variant."""
import sys
import time
sys.path.insert(0, 'src')
from run_phase3 import run_single_experiment

t0 = time.time()
result = run_single_experiment(variant="P3-B", seed=42, epochs=20, batch_size=32)
t1 = time.time()
print(f"\nP3-B, 20 epochs: {t1-t0:.1f}s")
print(f"Result: test_acc={result['test_acc']:.4f}")
