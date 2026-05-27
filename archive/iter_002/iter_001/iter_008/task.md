Implement the evaluation module in `src/eval_phase1.py`.

It should define:
```python
def evaluate_hierarchical_encoder(encoder, dataset, seed=42):
    """
    Evaluate a trained hierarchical encoder.
    
    Parameters:
    -----------
    encoder : HierarchicalEncoder
    dataset : dict
        with keys 'train_x', 'train_y', 'test_x', 'test_y'
    seed : int
    
    Returns:
    --------
    dict containing:
        - 'train_accuracy': float
        - 'test_accuracy': float
        - 'sparsity': float (average fraction of elements in test codes below 1e-3 in absolute magnitude)
        - 'recon_mse_per_layer': list of 3 floats (reconstruction MSE of layer 0, 1, 2 on test_x)
        - 'n_params': int (total unique parameters in encoder)
    """
```

Make sure to:
- Import `SimpleLogisticRegression` from `src.harness`.
- Encode the dataset's `train_x` and `test_x` to get `train_codes` and `test_codes`.
- Fit `SimpleLogisticRegression(n_classes=5, n_features=train_codes.shape[1], lr=0.1, max_iter=500, seed=seed)` on `train_codes` and `dataset['train_y']`.
- Compute train accuracy, test accuracy.
- Compute the code sparsity on `test_codes` with threshold `1e-3`.
- Compute reconstruction MSEs per layer on `test_x` by calling `encoder.compute_reconstruction_mse(dataset['test_x'])`.
- Obtain parameter count using `encoder.get_parameter_count()`.

Add a simple self-test in `if __name__ == "__main__":` to generate the dataset and evaluate an untrained encoder (which is one of our control baselines!). Run it and verify that it works without any crashes, then save the file.