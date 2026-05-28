Create the file `src/run_phase3_vicreg_fix.py` implementing the Pooled VICReg loss, Pooled VICReg grad, custom training epoch, classification v2 function, and a multiprocessing parallel runner for the 5-seed experiment.

Specifically, write:
1. `pooled_vicreg_loss(z_pooled, eps=1.0)` and `pooled_vicreg_grad(z_pooled, lambda_var=25.0, lambda_cov=25.0, eps=1.0)` as described in the prompt.
2. `train_jepa_epoch_with_pooled_vicreg(...)` that performs training of JEPA with optional pooled VICReg. Make sure it adds `dL_dpooled_expanded / (1.0 - alpha)` to `temporal_code_grads[-1]` where `alpha = 0.5`, to correctly propagate the pooled VICReg gradients back through the encoder backward pass.
3. `evaluate_classification_v2(encoder, train_grid, train_y, test_grid, test_y, seed, readout)` supporting:
   - `'pooled'`: `fwd["pooled"]`
   - `'spatial_pooled_then_flat'`: `fwd["temporal_outputs"][-1].mean(axis=2).reshape(len(y), -1)`
4. `run_single_experiment_with_fixes(args)` which takes a tuple `(condition, seed, use_pooled_vicreg, readout_type, epochs, batch_size, lr)` and runs the dataset generation, SpatiotemporalEncoder (variant P3-C, or Untrained/P3-C), JEPALoss training, and classification evaluation.
5. In the training loop, compute and record the final epoch metrics including final spatial JEPA loss, final temporal JEPA loss, final pooled variance std, final pooled VICReg var/cov loss, etc.
6. Run a fast dry-run first (e.g. 1 epoch, 1 seed per condition) if you'd like to verify correctness, then run the full experiment:
   - Conditions:
     - Condition A: P3-C, use_pooled_vicreg=False, readout='pooled'
     - Condition B: P3-C, use_pooled_vicreg=False, readout='spatial_pooled_then_flat'
     - Condition C: P3-C, use_pooled_vicreg=True, readout='pooled'
     - Condition D: P3-C, use_pooled_vicreg=True, readout='spatial_pooled_then_flat'
     - Untrained+pooled: Untrained, use_pooled_vicreg=False, readout='pooled'
     - Untrained+spatial_pooled: Untrained, use_pooled_vicreg=False, readout='spatial_pooled_then_flat'
   - Running across seeds: [42, 43, 44, 45, 46]
   - Hyperparams: 30 epochs, BATCH_SIZE=64, LR=1e-3, 200 train/class, 100 test/class.
7. Save results incrementally to `phase_3/pooled_vicreg_results.csv`.
8. Once all runs are complete, run a statistical analysis (paired t-test and Cohen's d) between Condition D and Untrained+spatial_pooled, and write a comprehensive markdown report `phase_3/REPORT_vicreg_fix.md` as requested. Ensure all criteria (D gain >= 8pp, p < 0.05, Cohen's d >= 0.8) are explicitly checked and the falsification verdict is rendered.

Do not delete or overwrite the original files like `src/run_phase3_optimized.py` or `src/run_phase3.py` since we want to keep them as-is. Just build the new runner and execute it.