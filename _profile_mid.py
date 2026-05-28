import sys, os, time
sys.path.insert(0, 'src')

print('Importing run_phase3...', flush=True)
from run_phase3 import run_single_experiment
print('Starting P3-B 10-epoch profiling (500 train/class, batch=64)...', flush=True)
t0 = time.time()
result = run_single_experiment('P3-B', 42, epochs=10, batch_size=64, lr=1e-3, update_encoder=True)
t1 = time.time()
elapsed = t1 - t0
print('10-epoch P3-B run: %.1fs' % elapsed, flush=True)
print('Estimated 50-epoch: %.1fs (%.1f min)' % (elapsed * 5, elapsed * 5 / 60), flush=True)
print('Estimated 100-epoch: %.1fs (%.1f min)' % (elapsed * 10, elapsed * 10 / 60), flush=True)
print('Estimated total 20 runs @ 50ep: %.1fs (%.1f min)' % (elapsed * 5 * 20, elapsed * 5 * 20 / 60), flush=True)
