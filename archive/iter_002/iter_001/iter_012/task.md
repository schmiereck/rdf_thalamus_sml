Write a hyperparameter search script `hyper_search.py` that sweeps over:
- `embedding_init`: 'uniform_0.01' (current), 'uniform_1.0', 'normal_1.0', 'normal_2.0'
- `lr`: 0.005, 0.01, 0.05, 0.1
- `l1_lambda`: 0.0, 0.0005, 0.002, 0.01
- `epochs_per_layer`: 100, 150

Use seed 42 for both the dataset generation and HierarchicalEncoder.
For each combination, train the `HierarchicalEncoder` in `cross_layer` mode (P1-B, d=8, d_out=24) and evaluate its test accuracy and code sparsity.
Keep track of the best test accuracy achieved, and print a table of the top 10 configurations sorted by test accuracy.
Also check if any configuration achieves both test accuracy >= 80% and code sparsity >= 50%.
Run this sweep and return the full output.