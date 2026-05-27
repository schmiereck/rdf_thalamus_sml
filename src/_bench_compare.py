"""Benchmark: original (loop-based) vs vectorized"""
import os, sys, time, subprocess, numpy as np

# Save current vectorized version
with open("spatiotemporal_encoder.py", "r") as f:
    vectorized_code = f.read()

# Get original from git
result = subprocess.run(
    ["git", "show", "HEAD:src/spatiotemporal_encoder.py"],
    capture_output=True, text=True, check=True
)
original_code = result.stdout

# Write original temporarily
with open("_bench_original.py", "w") as f:
    f.write(original_code)

N_ITERS = 5
B, S, T = 4, 16, 32

print("=" * 55)
print("  BENCHMARK: Original (loop) vs Vectorized")
print("=" * 55)

# === ORIGINAL ===
import importlib, importlib.util

# Load original dynamically
spec_orig = importlib.util.spec_from_file_location("orig_mod", "_bench_original.py")
orig_mod = importlib.util.module_from_spec(spec_orig)
spec_orig.loader.exec_module(orig_mod)

rng = np.random.default_rng(7)

t0_orig = time.perf_counter()
for _ in range(N_ITERS):
    enc = orig_mod.SpatiotemporalEncoder(variant="P3-B", d=16, d_out=16, seed=42)
    x_binary = (rng.random((B, S, T)) < 0.5).astype(np.float64)
    fwd = enc.forward_with_intermediates(x_binary)
    dL_dspatial = [rng.standard_normal(fwd["spatial_outputs"][l].shape) for l in range(3)]
    dL_dtemporal = [rng.standard_normal(fwd["temporal_outputs"][l].shape) for l in range(3)]
    grads = enc.backward(fwd, dL_dspatial, dL_dtemporal, alpha=0.5)
    pooled_orig = fwd["pooled"].copy()
    grads_orig_enc = {k: v.copy() for k, v in grads["dL_dspatial"].items()}
    grads_orig_temp = {k: v.copy() for k, v in grads["dL_dtemporal"].items()}
    dL_de_orig = grads["dL_dembedding"].copy()
t1_orig = time.perf_counter()

# === VECTORIZED ===
spec_vec = importlib.util.spec_from_file_location("vec_mod", "spatiotemporal_encoder.py")
vec_mod = importlib.util.module_from_spec(spec_vec)
spec_vec.loader.exec_module(vec_mod)

rng2 = np.random.default_rng(7)

t0_vec = time.perf_counter()
for _ in range(N_ITERS):
    enc2 = vec_mod.SpatiotemporalEncoder(variant="P3-B", d=16, d_out=16, seed=42)
    x_binary2 = (rng2.random((B, S, T)) < 0.5).astype(np.float64)
    fwd2 = enc2.forward_with_intermediates(x_binary2)
    dL_dspatial2 = [rng2.standard_normal(fwd2["spatial_outputs"][l].shape) for l in range(3)]
    dL_dtemporal2 = [rng2.standard_normal(fwd2["temporal_outputs"][l].shape) for l in range(3)]
    grads2 = enc2.backward(fwd2, dL_dspatial2, dL_dtemporal2, alpha=0.5)
    pooled_vec = fwd2["pooled"].copy()
    grads_vec_enc = {k: v.copy() for k, v in grads2["dL_dspatial"].items()}
    grads_vec_temp = {k: v.copy() for k, v in grads2["dL_dtemporal"].items()}
    dL_de_vec = grads2["dL_dembedding"].copy()
t1_vec = time.perf_counter()

# Print results
elapsed_orig = (t1_orig - t0_orig) / N_ITERS
elapsed_vec = (t1_vec - t0_vec) / N_ITERS
speedup = elapsed_orig / elapsed_vec

print(f"\n  Original (loop):   {elapsed_orig:.4f}s per run")
print(f"  Vectorised:        {elapsed_vec:.4f}s per run")
print(f"  Speedup:           {speedup:.2f}x")

# --- Numerical equivalence check ---
print(f"\n  Pooled rel error:      {np.abs(pooled_orig - pooled_vec).max():.2e}")
for key in grads_orig_enc:
    rel_err = np.abs(grads_orig_enc[key] - grads_vec_enc[key]).max()
    print(f"  Spatial grad[{key:>5s}] abs diff: {rel_err:.2e}")
for key in grads_orig_temp:
    rel_err = np.abs(grads_orig_temp[key] - grads_vec_temp[key]).max()
    print(f"  Temporal grad[{key:>5s}] abs diff: {rel_err:.2e}")
print(f"  Embedding grad diff:   {np.abs(dL_de_orig - dL_de_vec).max():.2e}")

# Cleanup
os.remove("_bench_original.py")

print("\n" + "-" * 55)
if elapsed_vec < elapsed_orig * 1.1:
    print(f"  Vectorized is {'slower' if elapsed_vec > elapsed_orig else 'about the same'} or slightly faster")
else:
    print(f"  Vectorized is {speedup:.1f}x faster")
print("=" * 55)
