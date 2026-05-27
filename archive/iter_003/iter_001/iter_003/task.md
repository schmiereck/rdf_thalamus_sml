Please update `src/training_objectives.py` to match the exact requirements of the prompt and the simplified interfaces. Specifically, the loss classes should have these methods and properties:

### 1. `JEPALoss(self, n_layers, d, temp=0.5, lr=1e-3)`
- In `__init__`, initialize a predictor per layer (list of $W_{pred}$ of shape `(d, d)` and $b_{pred}$ of shape `(d,)` for each of the `n_layers` layers). Also initialize their Adam states.
- `forward(self, codes)`:
  - Takes `codes` (list of `n_layers` arrays of shape `(B, P, d)`).
  - Computes:
    - Bidirectional prediction loss at each layer $l$: for each $p \in \{0 \dots P-2\}$, predict $Z[:, p+1, :]$ from $Z[:, p, :]$ and $Z[:, p, :]$ from $Z[:, p+1, :]$ using the linear predictor of that layer.
    - VICReg variance loss at each layer $l$: standard deviation per dimension of `codes[l]` over all $B \times P$ elements should be $\ge 1.0$. Use coefficient $\lambda_{var}=25.0$.
    - VICReg covariance loss at each layer $l$: off-diagonal entries of the $d \times d$ covariance matrix of centered `codes[l]` should be minimized. Use coefficient $\mu_{cov}=25.0$.
  - Returns:
    - `loss_val`: total loss (scalar) across all layers
    - `dL_dcodes`: list of `n_layers` gradients, each of shape `(B, P, d)` matching the input `codes`.
  - Also updates the internal linear predictor weights and biases using Adam!

### 2. `ContrastiveLoss(self, d, temp=0.5, lr=1e-3)`
- In `__init__`, initialize a projection head MLP: $10*d \to 5*d \to 2.5*d$ (e.g. 80 -> 40 -> 20 for $d=8$, 160 -> 80 -> 40 for $d=16$). Hidden activation is ReLU, and output is L2-normalized. Also initialize Adam states.
- `forward(self, codes)`:
  - Takes `codes` (list of `n_layers` arrays). The final layer code `codes[-1]` has shape `(2*B, 10, d)` containing the stacked original and augmented batch.
  - Flattens the final layer code to shape `(2*B, 10*d)`.
  - Runs it through the MLP projection head to get `S` of shape `(2*B, proj_out)`.
  - Computes InfoNCE loss with temperature $\tau=0.5$ on `S` where original and augmented views of each sample are paired. Diagonal logits are masked with $-1e9$.
  - Returns:
    - `loss_val`: InfoNCE loss (scalar)
    - `dL_dcodes`: list of `n_layers` gradients. The gradients for layers $0 \dots L-2$ are zeros of shape `(2*B, P, d)`. The gradient for layer $L-1$ is the MLP/InfoNCE gradient backpropagated w.r.t the flattened code, reshaped to `(2*B, 10, d)`.
  - Also updates the projection MLP parameters using Adam!

### 3. `SFALoss(self, delta_order=1, lambda_var=25.0)`
- `forward(self, codes)`:
  - Takes `codes` (list of `n_layers` arrays of shape `(B, P, d)`).
  - For each layer $l$:
    - Slowness loss: mean squared differences between consecutive positions: $\|Z[:, p+1, :] - Z[:, p, :]\|^2$.
    - Variance penalty: $\lambda_{var} \times \max(0, 1.0 - \sigma_j)$ per dimension $j$, where $\sigma_j$ is the standard deviation of `codes[l][:, :, j]` across all $B \times P$ elements. Use $\lambda_{var}=25.0$.
  - Returns:
    - `loss_val`: total SFA loss (scalar) across all layers
    - `dL_dcodes`: list of analytical gradients w.r.t the codes.

### 4. `HebbianLoss(self, eta=1e-3)`
- `forward(self, codes, node_inputs, layer_nodes)`:
  - For each layer $l$:
    - Gets output $Y = codes[l]$ (reshaped to $(B \times P, d)$) and input $X = node\_inputs[l]$ (reshaped to $(B \times P, 3 \times d)$).
    - Centered output: $Y_{centered} = Y - \text{mean}(Y, \text{axis}=0)$.
    - Computes the Oja update for the node parameters of this layer:
      $\Delta W_{enc} = \frac{\eta}{B \times P} (X^T Y_{centered} - W_{enc} Y_{centered}^T Y_{centered})$.
    - Directly applies the update to `layer_nodes[l].W_enc += \Delta W_{enc}`!
    - Computes a proxy monitoring loss: negative correlation $-\text{mean}(Y_{centered} \cdot (X W_{enc}))$.
  - Returns:
    - `loss_val`: monitoring loss (scalar) across all layers
    - `dL_dcodes`: list of zeros (since Hebbian is not gradient-based).

Please write this implementation carefully, ensuring all analytical gradients are exact and correct. Update `src/test_objectives.py` to match and run it to verify everything passes! Use `write_file` tool directly to complete this task. Thank you!