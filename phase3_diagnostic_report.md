# Phase 3 Training Failure — Diagnostic Report

## Executive Summary

The Phase 3 spatiotemporal experiments suffer from **three critical bugs** in the backward pass and training loop that corrupt gradient flow, causing trained encoders to perform significantly worse than untrained baselines (28–34% vs. 49.5% test accuracy).

| Bug | Severity | Location | Impact |
|-----|----------|----------|--------|
| **BUG 1: Wrong master node in temporal backward** | Critical | `spatiotemporal_encoder.py:388` | P3-B, P3-A phase 2 |
| **BUG 2: Spurious average-pooling gradient** | Critical | `spatiotemporal_encoder.py:360` | All variants |
| **BUG 3: P3-C double parameter update** | Critical | `run_phase3.py:175-190` | P3-C only |

---

## Detailed Bug Analysis

---

### BUG 1: Temporal Backward Uses Spatial Master Node's Weights (CRITICAL)

**Location:** `src/spatiotemporal_encoder.py`, line 388 (temporal backward input-gradient computation)

**Code:**
```python
# Line 388 in temporal backward pass:
dL_dx_flat = dL_dz_flat @ self.master_spatial.W_enc.T   # (B*n_pos*S, 3*d)
```

**Problem:** The temporal backward pass computes the gradient w.r.t. layer input using **`self.master_spatial.W_enc.T`** instead of **`self.master_temporal.W_enc.T`**.

**Why this matters:**
- In P3-B, `master_spatial` and `master_temporal` are **different objects** with independent parameters.
- The temporal backward should propagate gradients through the temporal master's weights, but it uses the spatial master's weights instead.
- This means:
  1. The parameter gradients accumulated in `temporal_grads` are computed with the correct node (via `node_inputs` and `code_out`), but...
  2. The **input gradient** `dL_dx` that flows back to earlier temporal layers (and eventually to the spatial layers) is computed using the **wrong weight matrix**.
  3. For P3-A phase 2 (temporal-only training after freezing spatial), this corrupts the entire temporal gradient flow.

**Comparison with working Phase 2:**
In `temporal_encoder.py:97` (P2-D), the gradient is correctly computed as:
```python
dL_dx_flat = dL_dz @ self.node.W_enc.T
```
There is only one node, so there's no possibility of using the wrong one.

**Affected variants:** P3-B (joint training), P3-A phase 2 (temporal-only phase).

---

### BUG 2: Spurious Constant Gradient from Average Pooling (CRITICAL)

**Location:** `src/spatiotemporal_encoder.py`, lines 358–365

**Code:**
```python
# Gradient from average pooling
x_final = fwd["temporal_outputs"][-1]          # (B, T_final, S_final, d_out)
T_final, S_final = x_final.shape[1], x_final.shape[2]
dL_dx = np.full_like(x_final, 1.0 / (T_final * S_final))

# Add external temporal JEPA gradients for the last layer
dL_dx = dL_dx + dL_dtemporal_codes[-1] * (1.0 - alpha)
```

**Problem:** The backward pass initializes `dL_dx` with a **constant positive gradient** `1.0 / (T_final * S_final)` for every element of the final temporal output, then adds the actual JEPA gradients on top.

**Why this is wrong:**
- During training, **there is no loss computed on the pooled output**. The only losses are the JEPA losses on intermediate layer outputs.
- The average pooling is used **only during evaluation** (for the linear probe), not during training.
- The constant gradient `np.full_like(x_final, 1.0 / (T_final * S_final))` has **no basis in the loss function**.
- This constant acts as a persistent bias that:
  1. Pushes all final temporal codes in the **positive direction** (before tanh saturation).
  2. Corrupts the JEPA gradients that are supposed to guide representation learning.
  3. Flows backward through all temporal and spatial layers, contaminating all parameter gradients.

**What the correct code should be:**
```python
# No pooling gradient during training — only JEPA gradients matter
dL_dx = dL_dtemporal_codes[-1] * (1.0 - alpha)
```

**Analogy:** This is like adding a phantom loss term `L_pool = mean(final_output)` to every training step, even though no such loss exists. The optimizer is trying to minimize a loss that was never defined.

**Affected variants:** All variants (P3-A, P3-B, P3-C, and Untrained).

**Why Untrained also underperforms:** Even though the encoder is frozen for Untrained, the spurious pooling gradient still flows through the backward pass and would affect any trainable parameters (though in Untrained mode, the encoder params are not updated). However, the JEPA predictors are still trained with corrupted code gradients, which may explain why Untrained doesn't reach higher accuracy.

---

### BUG 3: P3-C Applies Spatial Gradients Twice (CRITICAL)

**Location:** `src/run_phase3.py`, lines 156–190 in `train_jepa_epoch()`

**Code:**
```python
# In run_single_experiment() for P3-C:
adam_temporal = adam_spatial   # SAME OBJECT

# In train_jepa_epoch():
if adam_spatial is not None:
    adam_spatial.step(
        {"W_enc": encoder.master_spatial.W_enc, ...},
        grads["dL_dspatial"],
    )

if adam_temporal is not None and encoder.variant == "P3-C":
    combined = {
        k: grads["dL_dspatial"][k] + grads["dL_dtemporal"][k]
        for k in grads["dL_dspatial"]
    }
    adam_temporal.step(
        {"W_enc": encoder.master_spatial.W_enc, ...},
        combined,
    )
```

**Problem:** For P3-C, `adam_temporal` and `adam_spatial` are the **same `_Adam` object**. The code calls `.step()` on this object **twice per batch**:

1. First call: applies `grads["dL_dspatial"]` → spatial gradients applied once.
2. Second call: applies `combined = spatial + temporal` → spatial gradients applied **a second time**, temporal gradients applied once.

**Net effect:**
- Spatial gradients: applied **twice** per batch
- Temporal gradients: applied **once** per batch
- Adam's internal timestep `t` is incremented **twice** per batch, causing incorrect bias correction

**Why this destroys P3-C training:**
- P3-C is supposed to test whether a **single universal node** can handle both spatial and temporal processing.
- The correct behavior is to compute the combined gradient once and apply it once.
- Instead, spatial gradients are overweighted by 2×, and the Adam state is corrupted.

**What the correct code should be:**
```python
if encoder.variant == "P3-C":
    # Single Adam, single combined gradient, single step
    combined = {
        k: grads["dL_dspatial"][k] + grads["dL_dtemporal"][k]
        for k in grads["dL_dspatial"]
    }
    adam_spatial.step(
        {"W_enc": encoder.master_spatial.W_enc, ...},
        combined,
    )
```

**Affected variant:** P3-C only.

---

## Additional Issues (Non-Critical but Notable)

### ISSUE 4: Missing Decoder Gradients (Design Inconsistency)

**Location:** `src/spatiotemporal_encoder.py`, lines 378–381 and 433–436

**Code:**
```python
dW_dec = np.zeros_like(self.master_spatial.W_dec)
db_dec = np.zeros_like(self.master_spatial.b_dec)
temporal_grads["W_dec"] += dW_dec
temporal_grads["b_dec"] += db_dec
```

**Note:** The decoder parameters (`W_dec`, `b_dec`) are explicitly zeroed out in the gradient computation. While this is technically correct for JEPA-only training (the decoder isn't used in the JEPA loss), it is inconsistent with the UniversalNode design which includes a full autoencoder. If future experiments add a reconstruction loss term, these gradients would need to be computed properly.

**Comparison with Phase 1:** In `hierarchical_encoder.py:254-255`, the decoder gradients are also zeroed out, so this is consistent with the existing pattern.

---

### ISSUE 5: Alpha Scaling Asymmetry (Design Choice)

**Location:** `src/spatiotemporal_encoder.py`, lines 364 and 412

The JEPA code gradients are scaled by `alpha` (spatial) and `(1-alpha)` (temporal) in the backward pass:
```python
dL_dx = dL_dx + dL_dtemporal_codes[-1] * (1.0 - alpha)   # temporal
dL_dx_total = dL_dx + dL_dspatial_codes[l] * alpha        # spatial
```

While this is a valid way to balance objectives, it creates an asymmetry: the JEPA predictors are trained with **full-strength** losses, but the encoder only receives **scaled** gradients. This means the predictors and encoder are not co-adapting to the same effective loss landscape. For `alpha=0.5`, each objective only contributes half its gradient to the encoder, potentially slowing convergence.

This is more of a design choice than a clear bug, but it may contribute to suboptimal convergence.

---

## Root Cause Summary

The "worse than untrained" phenomenon is explained by the **three critical bugs** acting together:

1. **BUG 2 (spurious pooling gradient)** affects **all variants**. It adds a constant bias to all gradients, pushing representations in an arbitrary direction unrelated to the actual learning objective. This alone would degrade performance below random initialization.

2. **BUG 1 (wrong master node)** affects **P3-B and P3-A phase 2**. The temporal backward uses the spatial node's weights to compute input gradients, causing gradient misrouting. In P3-B (joint training), this means the temporal and spatial gradients interfere with each other through the wrong weight matrices.

3. **BUG 3 (P3-C double update)** affects **P3-C only**. Spatial gradients are applied twice, corrupting the Adam state and overweighting spatial relative to temporal learning.

**Why Untrained still outperforms trained variants:**
- The Untrained baseline uses a **randomly initialized but frozen encoder**.
- Random initialization with Xavier scaling produces reasonable feature representations.
- The linear probe can still find a decent decision boundary on these random features.
- In contrast, the trained variants have their encoders **actively corrupted** by the buggy gradients, making representations worse than random.

---

## Verification Steps

To confirm these bugs:

1. **For BUG 2:** Print the norm of `dL_dx` before and after adding the pooling gradient. The pooling contribution will be a constant `1.0/sqrt(T_final*S_final)` per element, independent of the data or loss.

2. **For BUG 1:** In P3-B, compare `id(self.master_spatial)` vs `id(self.master_temporal)` — they are different objects. Then verify that line 388 uses `self.master_spatial.W_enc.T` in the temporal backward block.

3. **For BUG 3:** In P3-C, verify `adam_temporal is adam_spatial` and check that `adam.step()` is called twice per batch, with `spatial + (spatial + temporal)` as the effective gradient.

---

## Recommended Fixes

| Bug | Fix |
|-----|-----|
| BUG 1 | Change line 388 to `dL_dx_flat @ self.master_temporal.W_enc.T` |
| BUG 2 | Remove the pooling gradient initialization; start with `dL_dx = dL_dtemporal_codes[-1] * (1.0 - alpha)` |
| BUG 3 | For P3-C, use a single Adam step with combined gradients; do not call both `adam_spatial.step()` and `adam_temporal.step()` |

---

*Report generated by code analysis of `src/spatiotemporal_encoder.py`, `src/run_phase3.py`, `src/training_objectives.py`, and comparison with working Phase 1 (`src/run_phase1_v2.py`, `src/hierarchical_encoder.py`) and Phase 2 (`src/run_phase2.py`, `src/temporal_encoder.py`) implementations.*
