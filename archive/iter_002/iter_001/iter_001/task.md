Implement the UniversalNode class in `src/node.py` according to the prompt instructions.

Specifically:
- Implement `__init__(self, d, l1_lambda, seed, d_out=None)` so it supports P1-E. Use Xavier initialization.
- Implement `forward(self, x_3d)` where `x_3d` has shape `(batch, 3, d_in)`. Flatten to `(batch, 3 * d_in)`, apply W_enc + b_enc, and tanh.
- Implement `reconstruct(self, code)` where `code` has shape `(batch, d_out)`. Apply W_dec + b_dec and reshape to `(batch, 3, d_in)`.
- Implement `local_loss(self, x_3d) -> float` which computes MSE of reconstruction and L1 loss of code (with self.l1_lambda). Use `np.mean` for both terms, i.e., `mse = np.mean((x_3d - recon)**2)` and `l1 = self.l1_lambda * np.mean(np.abs(code))`.
- Implement `compute_gradients(self, x_3d) -> dict` returning a dict with keys `'W_enc'`, `'b_enc'`, `'W_dec'`, `'b_dec'`, and also `'x_3d'` (the gradient with respect to the input `x_3d` of shape `(batch, 3, d_in)`). Double-check and verify the gradients using analytical backprop.
- Implement `apply_gradients(self, grads, lr)` which subtracts `lr * grads[key]` from the parameters.
- Implement `share_parameters_from(self, other_node)` which copies the parameters of other_node.

Add a `__main__` block in `src/node.py` that runs an automated numerical gradient check (finite differences) to verify that the analytical gradients for all 4 parameters AND the input `x_3d` are extremely close to the numerical gradients (relative error < 1e-5). Ensure this test passes and prints output confirming it.