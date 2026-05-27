Please modify `src/training_objectives.py` and `src/test_objectives.py` to fix `JEPALoss` so that it implements spatial bidirectional neighbor prediction at each layer instead of cross-layer prediction.

### Mathematical Formulation for JEPALoss:

For each layer $l \in \{0, \dots, n\_layers-1\}$:
Let $Z = codes[l]$ of shape `(B, P, d)`.
The predictor for layer $l$ is `W_pred[l]` of shape `(d, d)` and `b_pred[l]` of shape `(d,)`, with its own Adam optimizer.

For each $p \in \{0, \dots, P-2\}$:
- $z_p = Z[:, p, :]$ (shape `(B, d)`)
- $z_{p+1} = Z[:, p+1, :]$ (shape `(B, d)`)
- $\hat{z}_{p+1} = z_p W_{pred}[l] + b_{pred}[l]$ (shape `(B, d)`)
- $\hat{z}_p = z_{p+1} W_{pred}[l] + b_{pred}[l]$ (shape `(B, d)`)

The prediction (invariance) loss for layer $l$ is:
$\mathcal{L}_{pred, l} = \frac{1}{B (P-1) d} \sum_{p=0}^{P-2} \left[ \frac{1}{2} \|\hat{z}_{p+1} - z_{p+1}\|_F^2 + \frac{1}{2} \|\hat{z}_p - z_p\|_F^2 \right]$ (which is exactly the mean squared error over all $2 B (P-1)$ prediction pairs).

Analytical gradients of $\mathcal{L}_{pred, l}$ w.r.t predictor parameters:
$dW_{pred}[l] = \frac{1}{2 B (P-1) d} \sum_{p=0}^{P-2} \left[ z_p^T (\hat{z}_{p+1} - z_{p+1}) + z_{p+1}^T (\hat{z}_p - z_p) \right]$
$db_{pred}[l] = \frac{1}{2 B (P-1) d} \sum_{p=0}^{P-2} \sum_{b=1}^B \left[ (\hat{z}_{p+1} - z_{p+1}) + (\hat{z}_p - z_p) \right]$

Analytical gradients of $\mathcal{L}_{pred, l}$ w.r.t the codes $Z$ of layer $l$:
Initialize $dZ_{\mathcal{L}, l}$ of shape `(B, P, d)` to 0.
For each $p \in \{0 \dots P-2\}$:
- Let $e_{1, p} = \hat{z}_{p+1} - z_{p+1}$
- Let $e_{2, p} = \hat{z}_p - z_p$
- $dZ_{\mathcal{L}, l}[:, p, :] += \frac{1}{2 B (P-1) d} e_{1, p} W_{pred}[l]^T$
- $dZ_{\mathcal{L}, l}[:, p+1, :] += -\frac{1}{2 B (P-1) d} e_{1, p}$
- $dZ_{\mathcal{L}, l}[:, p+1, :] += \frac{1}{2 B (P-1) d} e_{2, p} W_{pred}[l]^T$
- $dZ_{\mathcal{L}, l}[:, p, :] += -\frac{1}{2 B (P-1) d} e_{2, p}$

The total JEPA loss at layer $l$ is:
$\mathcal{L}_l = 1.0 \times \mathcal{L}_{pred, l} + 25.0 \times \mathcal{L}_{var, l} + 25.0 \times \mathcal{L}_{cov, l}$
where:
- $\mathcal{L}_{var, l}$ is the variance penalty of $Z$: $\max(0, 1.0 - \sigma_j)$ per dimension, averaged over all $d$ dimensions, where $\sigma_j$ is computed over all $M = B \times P$ elements of $Z[:, :, j]$.
- $\mathcal{L}_{cov, l}$ is the covariance penalty: $\frac{1}{d} \sum_{j \neq k} C_{j, k}^2$, where $C = \frac{1}{M} \bar{Z}^T \bar{Z}$ is the $d \times d$ covariance matrix of centered $Z$.

Analytical gradients of the total loss at layer $l$ w.r.t $Z$:
$dZ_l = dZ_{\mathcal{L}, l} + dZ_{var, l} + dZ_{cov, l}$
where:
- $dZ_{var, l}[:, :, j] = -25.0 \times \frac{1}{d} \times \frac{Z[:, :, j] - \mu_j}{M \sigma_j}$ if $\sigma_j < 1.0$ else 0.
- $dZ_{cov, l} = 25.0 \times \frac{4}{M d} \bar{Z} C_{off}$, where $C_{off}$ is $C$ with diagonal set to 0.

Please implement this spatial `JEPALoss` in `src/training_objectives.py` and update the unit test in `src/test_objectives.py` to match (which will now pass layer codes of shape `(B, P, d)`). Run the tests to make sure everything passes perfectly! Proceed directly to the edits using `write_file`. Thank you!