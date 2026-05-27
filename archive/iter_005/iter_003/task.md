
# Fix Phase 3 Bugs and Rerun All Experiments

Three critical bugs were identified in the Phase 3 code. Fix all three, then run the complete experiment suite (4 variants × 5 seeds = 20 runs).

## Bug 1: Wrong Weight Matrix in Temporal Backward
File: `src/spatiotemporal_encoder.py`, line ~388

In the temporal backward pass, the code uses `self.master_spatial.W_enc.T` instead of `self.master_temporal.W_enc.T`. This corrupts gradient flow for P3-B and P3-A phase 2.

**Fix**: Replace `self.master_spatial.W_enc.T` with `self.master_temporal.W_enc.T` in the temporal backward section.

## Bug 2: Spurious Average-Pooling Gradient in Training
File: `src/spatiotemporal_encoder.py`, lines ~358-365

The backward() method adds a constant gradient from average pooling (`np.full_like(x_final, 1/(T*S))`) to `dL_dx` at the start of temporal backward. But average pooling is only used at evaluation time for the linear probe — it should NOT contribute a gradient during training. This phantom gradient pushes all representations in a direction unrelated to JEPA loss.

**Fix**: Remove the average-pooling gradient from backward(). The initial `dL_dx` at the start of temporal backward should be `np.zeros_like(x_final)`, not the constant from mean pooling. The only gradients should come from the JEPA code_grads passed in as arguments.

## Bug 3: Double Adam Step for P3-C
File: `src/run_phase3.py`, lines ~156-190

For P3-C variant, `adam_temporal` and `adam_spatial` are set to the same object. This means `.step()` is called twice on the same parameters per batch:
- First call: applies spatial gradients 
- Second call: applies spatial + temporal gradients COMBINED (because they share the same object)

This effectively applies spatial gradients twice and Adam's running statistics are corrupted.

**Fix**: For P3-C, use a SINGLE Adam optimizer for the shared master node, and call .step() ONCE per batch with the combined (spatial + temporal) gradients. Do NOT call step() separately for spatial and temporal.

## Implementation Steps

1. Fix all three bugs in `src/spatiotemporal_encoder.py` and `src/run_phase3.py`
2. Run the self-test in `src/spatiotemporal_encoder.py` to verify the shapes are still correct
3. Run the full experiment suite:
   ```
   cd src && python run_phase3.py
   ```
   This runs 4 variants (P3-A, P3-B, P3-C, Untrained) × 5 seeds (42-46) = 20 runs, 200 epochs each.
   It also runs shortcut baselines.

4. Save all results to `phase_3/phase3_results.csv` and `phase_3/shortcut_baselines.csv`

## Important Notes

- The dataset shortcut baselines should still pass (≤50% accuracy for 4-class)
- After the fix, trained variants should significantly outperform the untrained baseline
- All 5 seeds must be run for proper statistical analysis
- The training should converge to reasonable JEPA losses (not 20-25)
- If training seems unstable, consider reducing the learning rate or adjusting the training

## Expected Timing

Each run takes ~20-60 seconds for 200 epochs. 20 runs = ~10-20 minutes total.

## Output

After all runs complete:
- Print the summary table
- Verify that results are saved to `phase_3/phase3_results.csv`
- Verify shortcut baselines are saved to `phase_3/shortcut_baselines.csv`
