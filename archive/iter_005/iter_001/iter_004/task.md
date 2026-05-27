Create the main Phase 3 experiment runner at `src/run_phase3.py`.
It should:
1. Run all three variants (P3-A, P3-B, P3-C) + Untrained baseline + Shortcut baselines for the 5 seeds `[42, 43, 44, 45, 46]`.
2. Follow the exact JEPA training protocol described:
   - 200 epochs, Adam with lr=1e-3, batch_size=32.
   - For P3-A: train alpha=1.0 for 200 epochs, then freeze spatial and train alpha=0.0 for 200 epochs.
   - For P3-B/C: train alpha=0.5 jointly for 200 epochs.
   - Save the per-axis final JEPA losses.
3. Fit a SimpleLogisticRegression (linear probe) with max_iter=2000 on the final pooled d-dimensional representations to compute test accuracy and per-benchmark accuracies.
4. Save all results per seed to CSV files in the `phase_3/` directory.
5. Write a comprehensive statistical report.
Please run a quick smoke-test (e.g. 2 epochs, 1 seed) to verify that everything works before running the full suite.