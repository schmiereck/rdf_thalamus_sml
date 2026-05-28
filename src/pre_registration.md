# RDF Scientific Pre-Registration — Phase 4

*   **Iteration:** 008
*   **Pre-Registration File:** src/pre_registration.md

## 1. Research Question
Which unsupervised training objective best extracts task-relevant features from
spatiotemporal binary-grid data when combined with a lightweight universal-node
encoder (P3-C, 1 600 parameters, spatial_pooled_then_flat readout)?

Specifically, we compare four objective families — JEPA, SFA, Hebbian variance
maximisation, and Sparse Reconstruction — each with and without a pooled
VICReg variance+covariance regulariser injected into the final temporal layer.

## 2. Mathematical Formulations

### Notation
- Input grid: `x ∈ {0,1}^{B×S×T}`  (B batch, S=16 spatial, T=32 temporal)
- Embedding: `e = embed(x) ∈ ℝ^{B×S×T×d}`  with d=16, frozen
- Spatial layer `l` output: `Z_l^{(s)} ∈ ℝ^{B×S_l×T×d_out}`  (post-tanh code)
- Temporal layer `l` output: `Z_l^{(t)} ∈ ℝ^{B×T_l×S_{final}×d_out}`  (post-tanh code)
- Pooled representation: `z̄ = mean_{s,t}(Z_{L_t-1}^{(t)}) ∈ ℝ^{B×d_out}`
- All objectives are minimised by gradient descent on encoder parameters.

---

### 2.1 JEPA (Joint Embedding Predictive Architecture)

Per-layer bidirectional prediction with linear predictors plus VICReg
penalties on the *layer codes* (not the pooled code).

For a single layer with code `Z ∈ ℝ^{N×P×d_out}` (N=minibatch positions):

Pred. pairs:  `ẑ_{p+1} = W_pred·z_p + b_pred`  and  `ẑ_p = W_pred·z_{p+1} + b_pred`

`L_pred(Z) = ½·mean((ẑ_{p+1} − z_{p+1})²) + ½·mean((ẑ_p − z_p)²)`

`L_var(Z)  = mean_j max(0, 1 − σ_j(Z))`  where `σ_j` is the std of dimension `j`

`L_cov(Z)  = (1/d_out) Σ_{j≠k} C_{jk}²`  where `C = cov(Z)`

`L_JEPA(l) = L_pred(Z_l) + 25·L_var(Z_l) + 25·L_cov(Z_l)`

Total objective (α = 0.5):

`L_JEPA = α · (1/L_s) Σ_{l=0}^{L_s-1} L_JEPA(Z_l^{(s)})`
         `+ (1−α) · (1/L_t) Σ_{l=0}^{L_t-1} L_JEPA(Z_l^{(t)})`

Code gradients come from `JEPALoss.backward()`:
- `∂L/∂Z_l^{(s)}` and `∂L/∂Z_l^{(t)}` computed analytically via predictor + VICReg terms.

---

### 2.2 SFA (Slow Feature Analysis — gradient-based formulation)

Slowness is imposed **only on the final temporal layer output**:

`z = Z_{L_t-1}^{(t)} ∈ ℝ^{B×T_{final}×S_{final}×d_out}`

`L_slow = (1 / (B·(T_{final}−1)·S_{final}·d_out)) Σ_{b,s,t≥1} ‖z_{b,t,s,:} − z_{b,t−1,s,:}‖²`

**Without pooled VICReg:**  `L = L_slow`  
→ expected to collapse to constant (trivial zero-velocity solution).

**With pooled VICReg:**  `L = L_slow + L_VICReg(z̄)`  
This is the standard gradient-based SFA formulation (slowness + variance +
covariance decorrelation via Lagrangian relaxation).

Code gradient (post-tanh):

`∂L/∂z_{b,t,s,:} = +2(z_{b,t,s,:} − z_{b,t−1,s,:}) / denom`   for `t ≥ 1`
`∂L/∂z_{b,t−1,s,:} = −2(z_{b,t,s,:} − z_{b,t−1,s,:}) / denom` for `t ≥ 1`

where `denom = B·(T_{final}−1)·S_{final}·d_out`.

Only `∂L/∂Z_{L_t-1}^{(t)}` is non-zero; all spatial code gradients are zero.

---

### 2.3 Hebbian (Variance Maximisation on Intermediate Codes)

Maximises the output variance at **every intermediate layer** (spatial 0…2 and
temporal 0…2).  This is the gradient-based equivalent of Oja’s rule: Oja’s
online update converges to the principal subspace, which maximises output
variance.

For any layer output `Z ∈ ℝ^{M×d_out}` (flattened over batch + axes):

`L_Hebb = −(λ_hebb / d_out) · Σ_{layers} Σ_{j=0}^{d_out−1} Var(Z_{:,j})`

where `λ_hebb = 25.0` (chosen so gradient magnitudes are comparable to JEPA).

**Why it is distinct from VICReg:**
1. It operates on **all intermediate codes**, not only the pooled representation.
2. It **maximises variance** (negative loss), whereas VICReg constrains variance
to a lower bound and penalises excess covariance.
3. Without an explicit decorrelation term, units may align and produce **redundant**
(highly correlated) codes.

Code gradient:

`∂L/∂Z = −(2·λ_hebb / (M·d_out)) · (Z − μ_Z)`

where `μ_Z` is the per-dimension mean.  Under gradient descent on this loss,
`Z` is pushed **away** from its mean, i.e. variance increases.

---

### 2.4 Reconstruction (Sparse Autoencoder)

Local reconstruction at each node using the decoder `W_dec / b_dec` already
present in `UniversalNode`.

For spatial layer `l`:
- code    `a = Z_l^{(s)} ∈ ℝ^{B·S_l·T×d_out}`   (flattened)
- input   `x = spatial_inputs[l] ∈ ℝ^{B·S_l·T×3d}`   (flattened)
- recon   `r = a·W_dec + b_dec ∈ ℝ^{B·S_l·T×3d}`

`L_recon^{(s)}(l) = MSE(x, r) + λ_l1 · mean(|a|)`

with `λ_l1 = 0.01`.  Same expression for every temporal layer.

Total objective:

`L_recon = Σ_{l=0}^{L_s-1} L_recon^{(s)}(l) + Σ_{l=0}^{L_t-1} L_recon^{(t)}(l)`

Code gradient:

`∂L/∂a = (2/(M·D_in))·(r − x)·W_dec^T + (λ_l1/(M·d_out))·sign(a)`

where `M = B·positions` and `D_in = 3d`.

Decoder gradients (updated by a **separate Adam**, because
`encoder.backward()` sets `∂L/∂W_dec = 0`):

`∂L/∂W_dec = a^T·(2/(M·D_in))·(r − x)`
`∂L/∂b_dec = Σ_i (2/(M·D_in))·(r_i − x_i)`

---

### 2.5 Pooled VICReg injection (common to all objectives when enabled)

Computed directly on `z̄ ∈ ℝ^{B×d_out}`:

`L_VICReg = 25·mean_j max(0, 1 − σ_j(z̄)) + (25/d_out)·Σ_{j≠k} C_{jk}²`

Gradient `∂L_VICReg/∂z̄` is expanded to the shape of `Z_{L_t-1}^{(t)}` by
broadcasting and divided by `T_{final}·S_{final}` (since `z̄` is the mean over
those axes).  The expanded gradient is added to `∂L/∂Z_{L_t-1}^{(t)}` with a
`1/(1−α)` rescaling to match the temporal backward-pass weighting (`α=0.5`).

## 3. Hypothesis

(H1) JEPA + pooled VICReg achieves test accuracy ≥ 55 % (it was 61.55 % in
     iter_006, so 55 % is a relaxed reproducibility floor).

(H2) No other objective (with pooled VICReg) exceeds JEPA + pooled VICReg
     by more than 3 percentage points.

(H3) For **most** objectives, pooled VICReg improves accuracy over the
     VICReg-free version.  However, we explicitly anticipate that
     **Reconstruction may violate H3** because reconstruction contains an
     intrinsic anti-collapse mechanism (the decoder must reconstruct the
     input), so the added VICReg regulariser may provide no benefit and
     can even hurt by constraining the pooled representation unnecessarily.

## 4. Falsification Criteria

The hypothesis is falsified if ANY of the following hold:

| ID | Criterion | Expected outcome |
|----|-----------|-----------------|
| **F1** | JEPA + pooled VICReg achieves `< 55 %` test accuracy. | Should **NOT** trigger (reference is ~61.55 %). If it does, the implementation is broken. |
| **F2** | Any other objective (with OR without pooled VICReg) exceeds JEPA + pooled VICReg by `≥ 3` percentage points. | Should **NOT** trigger if JEPA is the best objective. |
| **F3** | For any objective X, `accuracy(X without VICReg) ≥ accuracy(X with VICReg)`. | Expected to trigger for **Reconstruction** (per Research Manager directive). If it triggers for JEPA, SFA, or Hebbian as well, that is an additional falsification event worth documenting. |

## 5. Experimental Design

* **Architecture:** P3-C (single universal node, d=16, d_out=16)
* **Encoder layers:** 3 spatial + 3 temporal (kernel-3, stride-1)
* **Readout:** `spatial_pooled_then_flat` for **all** conditions (26×16 = 416 dims)
* **Train/test split:** 200 per class train, 100 per class test, noise_flip=0.10
* **Optimiser:** Adam, lr = 1e-3, 30 epochs, batch_size = 64
* **Seeds:** [42, 43, 44, 45, 46]
* **Classifier:** `SimpleLogisticRegression(n_classes=4, lr=0.1, max_iter=2000)`
* **Total runs:** 8 trained conditions × 5 seeds + 5 untrained = **45 runs**

### Conditions

| ID | Objective | Pooled VICReg | Expected behaviour |
|----|-----------|---------------|-------------------|
| 1  | JEPA      | Yes           | Reference (~61.55 %) |
| 2  | JEPA      | No            | Baseline control |
| 3  | SFA       | Yes           | Standard gradient SFA |
| 4  | SFA       | No            | Collapse (trivial constant solution) |
| 5  | Hebbian   | Yes           | Variance max + decorrelation |
| 6  | Hebbian   | No            | Variance max only (aligned codes possible) |
| 7  | Recon     | Yes           | Sparse AE + pooled VICReg |
| 8  | Recon     | No            | Pure sparse AE (natively resists collapse) |
| 9  | Untrained | No            | Random init baseline |

## 6. Results Files

* `phase_4/phase4_results.csv` — per-run raw results
* `phase_4/REPORT.md` — statistical summary, hypothesis checks, recommendation

---
*Updated for Phase 4 objective comparison.*
