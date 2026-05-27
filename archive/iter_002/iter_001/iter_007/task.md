In `src/hierarchical_encoder.py`, look at how `accum_embed_grad` is scaled before updating `self.embedding`:
```python
                        # Embedding update
                        if layer_idx == 0:
                            accum_embed_grad /= n_out * B
                            self.embedding -= lr * accum_embed_grad
```
Since `grads["x_3d"]` returned by `compute_gradients` is already scaled by `1/B` (from MSE and L1 definitions inside the node), summing it over the batch size `B` yields the true average gradient over the batch. Dividing by `B` again scales it by `1/B^2` which is incorrect and makes learning extremely slow.

Please change `accum_embed_grad /= n_out * B` to `accum_embed_grad /= n_out` in both the shared mode block and the `'none'` mode block.
After making this change, run the self-test inside `src/hierarchical_encoder.py` and ensure everything passes perfectly. Then save the file.