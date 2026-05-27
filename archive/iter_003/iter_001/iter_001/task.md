Please implement:
1. `src/training_objectives.py` containing the four loss classes: `JEPALoss`, `ContrastiveLoss`, `SFALoss`, `HebbianLoss`.
2. Modify `src/hierarchical_encoder.py` to add `forward_with_intermediates(self, x_binary)` and `backward_from_code_grads(self, dL_dcodes, codes, node_inputs, x_binary)`.

Make sure to use only pure numpy. Here are the specific mathematical formulations for each class:

### 1. JEPALoss
- Bidirectional neighbor prediction per layer.
- Predictor for each layer $l$ is a linear layer (no sharing of predictors across layers):
  $\hat{z}_{p+1} = z_p W_{pred} + b_{pred}$ and $\hat{z}_p = z_{p+1} W_{pred} + b_{pred}$.
  Initialize weights using Xavier-like normal scaling ($1 / \sqrt{d}$) and biases to 0.
- Standard VICReg defaults for collapse prevention: $\lambda_{var}=25$, $\mu_{cov}=25$, $\nu_{inv}=1$.
  - Variance penalty: $V = \max(0, 1.0 - \sigma_j)$ for each dimension $j$, averaged over all $d$ dimensions.
    Standard deviation $\sigma_j$ is computed over the batch and positions: $M = B \times P$. Add $\epsilon=1e-8$ under the square root.
  - Covariance penalty: $C(Z) = \frac{1}{d} \sum_{j \neq k} C_{j, k}^2$, where $C$ is the covariance matrix of size $d \times d$ computed on centered codes over $M$ samples.
- The loss w.r.t the codes:
  Returns total loss (scalar) and the list of analytical gradients $dL/dcode$ at each layer.
- Update predictor parameters using a simple Adam step inside the loss class:
  $lr=1e-3, \beta_1=0.9, \beta_2=0.999, \epsilon=1e-8$.

### 2. ContrastiveLoss
- Bit-flip augmentation: for each sample, flip 1-2 random bits out of 16.
- Projection head: MLP(10*d -> 5*d -> 2.5*d (rounded, e.g. 20 for d=8, 40 for d=16)) on the final layer codes, with ReLU hidden activation and L2 normalization on the output.
- InfoNCE loss with temperature $\tau=0.5$.
- Compute analytical gradients of InfoNCE w.r.t projection outputs:
  $\frac{\partial \mathcal{L}}{\partial S} = \frac{1}{2B \tau} \left( P S + P^T S - 2 S^* \right)$ where $P_{k, m} = \text{softmax}(S S^T / \tau)$ with diagonal masked to $-\infty$, and $S^*$ is $S$ with original/augmented halves swapped.
- Backpropagate through L2 normalization and the MLP projection head to get the gradient w.r.t top-layer codes.
- Update projection head parameters using Adam ($lr=1e-3$).

### 3. SFALoss
- Slowness loss at each layer: $\text{mean}(\|z_{p+1} - z_p\|^2)$ across batch and positions.
- Variance penalty at each layer: $\lambda_{var} \times \max(0, 1.0 - \sigma_j)$ per dimension. Use $\lambda_{var}=25.0$.
- Return total SFA loss and the exact analytical gradients w.r.t codes at each layer.

### 4. HebbianLoss
- Compute Hebbian/Oja updates directly at each layer for the encoder weights (no gradients w.r.t codes propagated).
- $\Delta W_{enc} = \frac{\eta}{M} (X_{flat}^T Y_{centered} - W_{enc} Y_{centered}^T Y_{centered})$ where $Y$ is centered over the batch/positions, and $X_{flat}$ is the flattened sliding window input.
- Decorrelation: subtract mean of outputs over the batch and positions.
- Returns a monitoring loss: negative correlation $- \text{mean}(Y_{centered} \cdot (X_{flat} W_{enc}))$.

### 5. HierarchicalEncoder updates
- `forward_with_intermediates(self, x_binary)`: Returns list of codes at each layer, list of node inputs at each layer, and the final flattened code.
- `backward_from_code_grads(self, dL_dcodes, codes, node_inputs, x_binary)`: Reconstructs exact analytical gradients of the loss w.r.t `W_enc`, `b_enc` at each layer, and the input `embedding` using sliding-window gradient accumulation and chain rule through $\tanh$.

Please implement and verify with a quick unit test that everything is working properly!