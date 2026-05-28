
# Phase 4: Fix Memory Issues + Run Full Experiment

## Context
The existing `src/run_phase4.py` crashes with a memory error when running the full 45-experiment Phase 4 objective comparison. The error occurs in `forward_with_intermediates` when processing batches — specifically the `windows.copy()` call allocates `(64, 14, 32, 3, 16)` = 10.5 MiB per array, but with multiprocessing (3 workers), memory runs out.

## Task
Fix the memory and timeout issues in `src/run_phase4.py`, then run the FULL 45-experiment sweep. The experiments should run SEQUENTIALLY in the main process (no multiprocessing).

### Required Fixes (apply ALL of these):

1. **Replace multiprocessing Pool with sequential execution**: In `main()`, remove `Pool(processes=n_workers)` and use a simple for-loop calling `run_single_experiment(task)` sequentially. This eliminates the 3× memory multiplication from child processes.

2. **Batched feature extraction for evaluation**: In `evaluate_classification()`, instead of doing `encoder.forward_with_intermediates(train_grid)` on the full 800-sample training set at once, process it in chunks of 64. Same for test_grid. Concatenate the spatial_pooled_then_flat features from all chunks. This avoids a ~1 GB memory spike from the full forward pass.

3. **Remove the redundant final_fwd**: In `run_single_experiment()`, remove the `final_fwd = encoder.forward_with_intermediates(train_grid)` call after training. Instead, use `metrics["pooled_std"]` from the last epoch's training metrics (already computed during training). This eliminates another full-dataset forward pass.

4. **Skip training loop for untrained baseline**: For `objective == "untrained"`, skip the 30-epoch training loop entirely. Just do evaluation directly. The encoder is randomly initialized and not updated, so there's no point running the training loop.

5. **Add gc.collect() between runs**: After each experiment, call `import gc; gc.collect()` to free memory before the next run.

6. **Add --objectives CLI argument**: Allow running a subset of objectives, e.g. `python src/run_phase4.py --objectives jepa sfa`. Default is all objectives. This supports split runs if needed.

7. **Append mode for results CSV**: Change `save_result()` to append mode so results from split runs accumulate. At the start of `main()`, only delete the CSV if `--objectives` is not specified (full run).

8. **Add --skip-existing flag**: If a (objective, seed, use_pooled_vicreg) combination already exists in the CSV, skip it. This enables resume after a partial run.

### Implementation Details

For fix #2 (batched evaluation), the key change is in `evaluate_classification()`:
```python
def evaluate_classification(encoder, train_grid, train_y, test_grid, test_y, seed, batch_size=64):
    # Process in chunks to avoid memory spike
    def extract_features(grid, batch_size):
        features = []
        for start in range(0, len(grid), batch_size):
            end = min(start + batch_size, len(grid))
            fwd = encoder.forward_with_intermediates(grid[start:end])
            feat = fwd["temporal_outputs"][-1].mean(axis=2).reshape(end - start, -1)
            features.append(feat)
        return np.concatenate(features, axis=0)
    
    tr = extract_features(train_grid, batch_size)
    te = extract_features(test_grid, batch_size)
    # ... rest is same
```

For fix #1 (sequential execution), replace the Pool section with:
```python
all_results = []
for i, task in enumerate(tasks):
    result = run_single_experiment(task)
    all_results.append(result)
    gc.collect()
    if (i + 1) % 5 == 0 or i == total_tasks - 1:
        elapsed = time.time() - t_start
        print(f"    Completed {i+1}/{total_tasks} tasks ({elapsed:.1f}s elapsed)")
```

For fix #3, replace the `final_fwd` section with:
```python
final_pooled_std = metrics.get("pooled_std", 0.0)
```

For fix #4, in `run_single_experiment()`, wrap the training loop:
```python
if objective != "untrained":
    for epoch in range(epochs):
        metrics = train_epoch(...)
else:
    # Untrained: skip training, compute a single forward pass for metrics
    fwd_sample = encoder.forward_with_intermediates(train_grid[:BATCH_SIZE])
    metrics = {"obj_loss": 0.0, "pooled_std": float(np.sqrt(fwd_sample["pooled"].var(axis=0, ddof=0).mean() + 1e-12))}
```

### After Fixing: Run the Full Experiment

After applying all fixes, run:
```bash
cd /home/user && python src/run_phase4.py
```

This should run all 45 experiments (4 objectives × 2 VICReg conditions × 5 seeds + 5 untrained) sequentially.

If it times out or fails, at minimum ensure we get results for JEPA (10 runs) + SFA (10 runs) + untrained (5 runs) = 25 runs by running:
```bash
cd /home/user && python src/run_phase4.py --objectives jepa sfa
```

Then the remaining objectives can be run in a follow-up.

### Important Notes
- Read `src/pre_registration.md` first and adhere to the registered hypotheses and falsification criteria.
- The experimental config is: P3-C architecture, d=16, d_out=16, 1,600 params, 30 epochs, batch=64, lr=1e-3, alpha=0.5, seeds [42,43,44,45,46].
- Save all results to `phase_4/phase4_results.csv`.
- Make sure the CSV has the correct fieldnames: objective, seed, use_pooled_vicreg, train_acc, test_acc, class_0_acc, class_1_acc, class_2_acc, class_3_acc, final_loss, final_pooled_std, training_time_sec.
- At the end, print a summary of mean ± std test accuracy for each condition.
