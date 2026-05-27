Implement `src/hierarchical_encoder.py` with the class `HierarchicalEncoder`.

Import `UniversalNode` from `src.node`.

Define `HierarchicalEncoder`:
```python
class HierarchicalEncoder:
    def __init__(self, n_input=16, d=8, n_layers=3, sharing_mode='cross_layer', l1_lambda=0.002, seed=42, d_out=None):
        ...
```
Make sure:
- It supports `sharing_mode` in `('within_layer', 'cross_layer', 'none')`.
- It instantiates nodes correctly based on the sharing mode and seeds:
  - For `sharing_mode == 'none'`: list of lists of `UniversalNode` instances (e.g. `self.nodes[layer_idx][pos]`), where each node has a unique seed.
  - For `sharing_mode == 'within_layer'` or `'cross_layer'`: list of 3 nodes `self.layer_nodes = [...]` (one per layer). For `'cross_layer'`, during initialization you can still instantiate one per layer and copy weights during progressive training as specified.
- It initializes the `self.embedding` parameter with shape `(2, d)` (using Xavier-like or small uniform values, e.g. `rng.uniform(-0.01, 0.01, (2, d))`).
- It implements `forward(self, x_binary) -> np.ndarray` which does:
  - Embeds binary inputs of shape `(batch, 16)` using `self.embedding`.
  - Runs layer-by-layer forward passes.
  - At each layer, slices the input to the next layer to its first `d_in` (which is `d`) dimensions (to support P1-E's non-recursive wider output).
  - Flattens the top-layer codes (positions=10) to `(batch, 10 * d_out)`.
- It implements `encode(self, x_binary) -> np.ndarray` which just calls `forward`.
- It implements `train(self, dataset, epochs_per_layer=100, lr=0.01, batch_size=32)` which does progressive training as described. Specifically, train Layer 0 (including the embedding update), copy weights to subsequent layers if `cross_layer` sharing, compute Layer 0 outputs, train Layer 1, copy weights to Layer 2 if `cross_layer` sharing, compute Layer 1 outputs, and train Layer 2.
- It implements `get_parameter_count(self) -> int` to return the count of unique parameters in the embedding and unique nodes.
- It implements `compute_reconstruction_mse(self, x_binary) -> list` to return a list of reconstruction MSEs for layer 0, 1, and 2.

Add a simple self-test in `if __name__ == "__main__":` that instantiates `HierarchicalEncoder`, runs a forward pass on a dummy batch of binary inputs, computes parameter counts, and prints them. Ensure it works and save the file.