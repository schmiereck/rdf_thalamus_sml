Please do the following:
1. Optimize `src/spatiotemporal_encoder.py` by:
   - Modifying `_make_windows_3` to use slicing for `axis=1` (instead of `np.take`), which is extremely fast and avoids memory copies.
   - Simply returning `np.zeros_like(self.embedding)` for `dL_dembedding` in the backward pass since the embedding layer is non-learned and frozen.
2. Create `src/run_phase3_parallel.py` as designed to run all 4 variants (P3-A, P3-B, P3-C, Untrained) across the 5 seeds `[42, 43, 44, 45, 46]` for 200 epochs in parallel using `multiprocessing.Pool` (with 5 or 10 parallel worker processes).
3. Execute `src/run_phase3_parallel.py` to run the entire experimental suite.
4. Verify that all CSV files are successfully created and saved in `phase_3/`:
   - `phase_3/p3a_results.csv`
   - `phase_3/p3b_results.csv`
   - `phase_3/p3c_results.csv`
   - `phase_3/untrained_results.csv`
   - `phase_3/shortcut_results.csv`
   - `phase_3/param_comparison.csv`
5. Print the final summary of mean and standard deviation of accuracy for each variant.