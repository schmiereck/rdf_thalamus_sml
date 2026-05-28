import sys, os, time
sys.path.insert(0, 'src')

print('Importing fast runner...', flush=True)
from run_phase3_fast import run_single_experiment_fast
print('Starting P3-B fast profiling (50 epochs, 200 train/class, batch=64)...', flush=True)
t0 = time.time()
result = run_single_experiment_fast('P3-B', 42, epochs=50, batch_size=64, lr=1e-3, update_encoder=True)
t1 = time.time()
elapsed = t1 - t0
print('50-epoch fast P3-B run: %.1fs' % elapsed, flush=True)
print('Estimated 5 seeds P3-B: %.1fs (%.1f min)' % (elapsed * 5, elapsed * 5 / 60), flush=True)
print('Estimated 5 seeds P3-A (2x): %.1fs (%.1f min)' % (elapsed * 10, elapsed * 10 / 60), flush=True)
print('Estimated total 20 runs: %.1fs (%.1f min)' % (elapsed * 35, elapsed * 35 / 60), flush=True)
