In `src/node.py`, modify `compute_gradients` so that the gradient with respect to the input `x_3d` is correctly computed.
Specifically, change:
```python
        # --- Gradient w.r.t. input x_3d ---
        d_x_flat = d_z @ self.W_enc.T                  # (B, D_in)
        d_x_3d = d_x_flat.reshape(batch, 3, self.d)    # (B, 3, d)
```
to:
```python
        # --- Gradient w.r.t. input x_3d ---
        # The loss MSE = mean((recon - x)**2) depends on x directly (with gradient -d_r)
        # as well as indirectly through the encoder (with gradient d_z @ W_enc^T)
        d_x_flat = d_z @ self.W_enc.T - d_r            # (B, D_in)
        d_x_3d = d_x_flat.reshape(batch, 3, self.d)    # (B, 3, d)
```
Then run `python src/node.py` to verify that all gradient checks pass (including `x_3d` with relative error < 1e-5). Ensure that the file is saved properly.