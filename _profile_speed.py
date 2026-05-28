import sys, os, time
sys.path.insert(0, 'src')

print('Importing run_phase3...', flush=True)
from run_phase3 import run_single_experiment
print('Starting P3-B 10-epoch profiling...', flush=True)
t0 = time.time()
result = run_single_experiment('P3-B', 42, epochs=10, batch_size=32, lr=1e-3, update_encoder=True)
t1 = time.time()
elapsed = t1 - t0
print('10-epoch P3-B run: %.1fs' % elapsed, flush=True)
print('Estimated 200-epoch: %.1fs' % (elapsed * 20), flush=True)
print('Estimated 100-epoch: %.1fs' % (elapsed * 10), flush=True)
print('Estimated 50-epoch: %.1fs' % (elapsed * 5), flush=True)
