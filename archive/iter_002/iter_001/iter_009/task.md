Implement and execute the Phase 1 experiment runner in `src/run_phase1.py`.

The script must:
1. Ensure the output directory `phase_1/` exists.
2. Define the list of seeds: `[42, 43, 44, 45, 46]`.
3. Define the list of configurations:
   - **P1-A**: `sharing_mode='within_layer'`, `d=8`, `d_out=24`, name = 'P1-A'
   - **P1-B**: `sharing_mode='cross_layer'`, `d=8`, `d_out=24`, name = 'P1-B' (PRIMARY)
   - **P1-C**: `sharing_mode='none'`, `d=8`, `d_out=24`, name = 'P1-C'
   - **P1-D**: `sharing_mode='cross_layer'`, `d=4`, `d_out=12`, name = 'P1-D'
   - **P1-E**: `sharing_mode='cross_layer'`, `d=8`, `d_out=16`, name = 'P1-E'
   - **Untrained**: `sharing_mode='cross_layer'`, `d=8`, `d_out=24`, name = 'Untrained-P1-B' (skip training)

4. For each configuration and seed:
   - Generate the Phase 1 dataset using `generate_phase1_dataset(seed=seed)`.
   - Instantiate `HierarchicalEncoder` with the respective configuration and seed.
   - If not the 'Untrained' config, train the encoder with `epochs_per_layer=100`, `lr=0.01`, `batch_size=32`.
   - Evaluate the encoder using `evaluate_hierarchical_encoder(encoder, dataset, seed=seed)`.
   - Save the metrics: `config`, `seed`, `test_accuracy`, `train_accuracy`, `sparsity`, `recon_mse_l0`, `recon_mse_l1`, `recon_mse_l2`, `n_params`.
   - Print the run progress and results.

5. Save all 30 run results to `phase_1/results.csv` using Python's `csv.DictWriter` (include columns for all saved metrics, plus `recon_mse_l0`, `recon_mse_l1`, `recon_mse_l2`).
6. Ensure that the script executes cleanly, without crashing, and saves the file. Run it now!