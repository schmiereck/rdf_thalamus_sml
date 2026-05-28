"""Time a single Phase 3 run with 100 epochs."""
import time
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from run_phase3 import run_single_experiment

t0 = time.time()
result = run_single_experiment(variant="P3-B", seed=43, epochs=100, batch_size=32, lr=1e-3)
t1 = time.time()
print(f"\nSingle run (100 epochs) took {t1-t0:.1f}s")
print(f"test_acc={result['test_acc']:.4f}")
