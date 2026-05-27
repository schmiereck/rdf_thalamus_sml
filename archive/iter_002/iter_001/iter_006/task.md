Write a small script `test_training.py` that:
1. Generates the Phase 1 dataset using `generate_phase1_dataset(n_train=200, n_test=100)`.
2. Instantiates a `HierarchicalEncoder` with config `sharing_mode='cross_layer', d=8`.
3. Stores the initial value of `self.embedding`.
4. Trains the encoder for 5 epochs per layer.
5. Prints the training loss history for each epoch.
6. Computes the absolute change in `self.embedding` (e.g. `np.max(np.abs(final_embedding - initial_embedding))`) to see if it actually learned and changed.
7. Prints these values.
Run the script and return the output.