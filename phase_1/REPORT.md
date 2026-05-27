# Phase 1 Corrective Experiment Report

## Bug Fixes Applied

### 1. d_out Bottleneck Bug (Critical)

**Previous (WRONG):** `d_out = 3*d = 24` for all recursive configs  
→ Encoder 24→24, Decoder 24→24 — effectively an identity mapping with no compression.

**Fixed (CORRECT):** `d_out = d = 8` for recursive configs  
→ Encoder 24→8, Decoder 8→24 — true 3:1 compression bottleneck.

The recursive universal node form requires output dim = input dim **per slot**, meaning `d_out = d` (the per-slot dimension), not `d_out = 3*d` (the total flattened input dimension). The output of each node becomes ONE slot of dimension `d` that feeds into the next layer.

### 2. Embedding Initialization Fix

**Previous:** `Uniform[-0.01, 0.01]` — too small, causing representation collapse.  
**Fixed:** `Normal(0, 1.0)` — stronger initial representations.

### 3. Inter-layer Slicing Fix

**Previous:** Unconditional `x = x[:, :, :self.d]` between layers.  
**Fixed:** Conditional slicing — only when `d_out > d` (e.g., P1-E with d_out=16, d=8). For recursive configs (d_out == d), no slicing occurs.

### 4. k-WTA Support Added

New `kwta_k` parameter in `UniversalNode` and `HierarchicalEncoder`. When active:
- Only top-k absolute activations survive; rest are zeroed.
- L1 penalty is disabled (sparsity is structural).
- Gradients flow only through winning units.

---

## Experimental Setup

| Hyperparameter | Value |
|----------------|-------|
| d (per-slot dim) | 8 (or 4 for P1-D) |
| d_out (code dim) | 8 (recursive), 16 (P1-E), 4 (P1-D) |
| l1_lambda | 0.002 (L1 configs); 0 (k-WTA) |
| learning_rate | 0.01 |
| epochs_per_layer | 100 |
| batch_size | 32 |
| Seeds | 42, 43, 44, 45, 46 |
| kwta_k | 4 (for P1-B-kwta; 4 of 8 active = 50% sparsity) |

**Configs (7 × 5 seeds = 35 runs):**
- P1-A: within_layer sharing, d=8, d_out=8
- P1-B: cross_layer sharing, d=8, d_out=8
- P1-C: none (independent), d=8, d_out=8
- P1-D: cross_layer sharing, d=4, d_out=4
- P1-E: cross_layer sharing, d=8, d_out=16 (wider output, sliced to d=8 between layers)
- Untrained-P1-B: cross_layer sharing, d=8, d_out=8, no training
- P1-B-kwta: cross_layer sharing, d=8, d_out=8, kwta_k=4

---

## Results

### Summary Table (mean ± std over 5 seeds)

| Config | Test Accuracy | Sparsity | n_params | Recon MSE L0 | Recon MSE L1 | Recon MSE L2 |
|--------|--------------|----------|----------|--------------|--------------|--------------|
| P1-A | 0.3424 ± 0.0211 | 0.0033 ± 0.0031 | 1,264 | 0.0011 | 0.0021 | 0.0018 |
| P1-B | 0.3352 ± 0.0305 | 0.0003 ± 0.0005 | 1,264 | 0.1572 | 0.1255 | 0.0621 |
| P1-C | 0.3324 ± 0.0251 | 0.0023 ± 0.0025 | 14,992 | 0.0009 | 0.0020 | 0.0022 |
| P1-D | 0.2392 ± 0.0647 | 0.0007 ± 0.0015 | 344 | 0.1249 | 0.0637 | 0.0136 |
| P1-E | 0.3516 ± 0.0268 | 0.0039 ± 0.0030 | 2,440 | 0.1045 | 0.0850 | 0.0248 |
| Untrained-P1-B | 0.4844 ± 0.0413 | 0.0004 ± 0.0003 | 1,264 | 0.8458 | 0.4511 | 0.3839 |
| P1-B-kwta | 0.3572 ± 0.0749 | **0.5000 ± 0.0000** | 1,264 | 0.0570 | 0.0408 | 0.0292 |

### Per-Seed Raw Data

```
Config          Seed  Test_Acc  Train_Acc  Sparsity   n_params
P1-A            42    0.382     0.377      0.0083     1264
P1-A            43    0.324     0.362      0.0000     1264
P1-A            44    0.328     0.354      0.0033     1264
P1-A            45    0.346     0.367      0.0047     1264
P1-A            46    0.332     0.367      0.0000     1264
P1-B            42    0.374     0.369      0.0000     1264
P1-B            43    0.284     0.339      0.0000     1264
P1-B            44    0.322     0.345      0.0005     1264
P1-B            45    0.352     0.374      0.0012     1264
P1-B            46    0.344     0.334      0.0000     1264
P1-C            42    0.356     0.370      0.0008     14992
P1-C            43    0.312     0.336      0.0005     14992
P1-C            44    0.332     0.331      0.0029     14992
P1-C            45    0.298     0.353      0.0069     14992
P1-C            46    0.364     0.377      0.0005     14992
P1-D            42    0.232     0.212      0.0000     344
P1-D            43    0.196     0.203      0.0000     344
P1-D            44    0.202     0.202      0.0000     344
P1-D            45    0.200     0.200      0.0000     344
P1-D            46    0.366     0.399      0.0037     344
P1-E            42    0.344     0.390      0.0024     2440
P1-E            43    0.332     0.361      0.0075     2440
P1-E            44    0.362     0.358      0.0021     2440
P1-E            45    0.398     0.420      0.0074     2440
P1-E            46    0.322     0.358      0.0000     2440
Untrained-P1-B  42    0.516     0.519      0.0000     1264
Untrained-P1-B  43    0.462     0.552      0.0009     1264
Untrained-P1-B  44    0.468     0.491      0.0004     1264
Untrained-P1-B  45    0.546     0.605      0.0004     1264
Untrained-P1-B  46    0.430     0.463      0.0005     1264
P1-B-kwta       42    0.290     0.289      0.5000     1264
P1-B-kwta       43    0.338     0.403      0.5000     1264
P1-B-kwta       44    0.278     0.332      0.5000     1264
P1-B-kwta       45    0.400     0.439      0.5000     1264
P1-B-kwta       46    0.480     0.502      0.5000     1264
```

---

## Criteria Checks

### 1. P1-B accuracy ≥ 80%
**Result: FAIL** — P1-B mean test accuracy = **33.52%** (range: 28.4%–37.4%).

The true bottleneck (24→8) with tanh activation and weak L1 regularization (λ=0.002) does not produce representations discriminative enough for 80% accuracy on the 5-class task. The model learns to reconstruct but loses category-discriminating information through the compression.

### 2. P1-C − P1-B ≤ 15 percentage points
**Result: PASS** — P1-C (33.24%) − P1-B (33.52%) = **−0.28 pp**.

The sharing-mode penalty is negligible. Both within-layer (P1-A) and cross-layer (P1-B) sharing achieve similar accuracy to independent weights (P1-C), confirming that weight sharing does not harm performance.

### 3. Trained P1-B − untrained P1-B ≥ 15 percentage points
**Result: FAIL** — Trained P1-B (33.52%) − Untrained (48.44%) = **−14.92 pp**.

Training actually **hurts** performance relative to the untrained baseline. The untrained encoder with Normal(0,1) embeddings produces richer random features (48.4% accuracy) than the trained autoencoder (33.5%). This indicates that the autoencoder training objective (reconstruction + L1) is not aligned with the downstream classification task. The model learns to compress and reconstruct inputs but discards class-discriminating information.

### 4. P1-B sparsity ≥ 50%
**Result: FAIL** — P1-B mean sparsity = **0.03%** (essentially no sparsity).

With `l1_lambda = 0.002` and `Normal(0, 1.0)` embeddings, the L1 penalty is too weak to push tanh activations below the 1e-3 threshold. The embeddings produce large-magnitude inputs, and the tanh outputs remain well above the sparsity threshold.

---

## k-WTA Analysis (P1-B-kwta)

| Metric | Value |
|--------|-------|
| Test Accuracy | 35.72% ± 7.49% |
| Sparsity | **50.00% ± 0.00%** (structurally guaranteed) |
| Recon MSE (L0/L1/L2) | 0.057 / 0.041 / 0.029 |

**Observations:**
- **Sparsity is exactly 50%** by construction (4 of 8 code dimensions active), satisfying the ≥50% threshold structurally.
- **Accuracy is comparable to L1-based P1-B** (35.7% vs 33.5%), with higher variance.
- **Reconstruction MSE is lower than P1-B** (0.057 vs 0.157 at L0), suggesting k-WTA produces more stable codes.
- The k-WTA mechanism successfully enforces sparsity without needing an L1 penalty, but does not improve classification accuracy over the untrained baseline.

---

## Key Findings

1. **The d_out bug fix is architecturally correct.** The recursive form now has a true 3:1 bottleneck (24→8). Top-layer codes are 10×8 = 80 features (not 240 as before).

2. **The embedding fix improves the untrained baseline.** Normal(0,1) embeddings give the untrained encoder ~48% accuracy vs ~30% with the old Uniform[-0.01,0.01] initialization.

3. **Autoencoder training is misaligned with classification.** The reconstruction objective drives the encoder to preserve all input information, but the bottleneck (24→8) forces lossy compression. The result is codes that reconstruct well but are not class-discriminative.

4. **L1 regularization is ineffective at λ=0.002.** With Normal(0,1) embeddings, tanh activations are too large for such a weak L1 penalty to induce sparsity. Sparsity remains near 0% for all L1-based configs.

5. **k-WTA successfully enforces sparsity.** P1-B-kwta achieves exactly 50% sparsity structurally, without needing L1. However, it does not solve the accuracy problem.

6. **P1-D (d=4) underperforms.** The 12→4 bottleneck is too aggressive; accuracy drops to ~24%.

7. **P1-E (d_out=16) performs best among trained configs.** The wider code dimension (16) with slicing back to d=8 between layers gives slightly better accuracy (35.2%) than the strict recursive form.

---

## Architectural Notes

- **P1-C (none sharing)** has 14,992 parameters vs 1,264 for P1-A/B, yet achieves similar accuracy. The extra capacity does not help, confirming that the bottleneck (not parameter count) is the limiting factor.
- **Cross-layer sharing** (P1-B) works correctly: all 3 layers share identical weights after training.
- **Gradient checks pass** for both standard and k-WTA modes (numerical vs analytical relative error < 1e-5).

---

## Conclusion

The corrective fixes (d_out=d, Normal embedding, conditional slicing, k-WTA) are **architecturally sound and correctly implemented**. All 35 runs completed successfully.

However, the **success criteria are not met** because:
- The true bottleneck (24→8) is too aggressive for the simple tanh autoencoder to learn class-discriminative features in 100 epochs per layer.
- The L1 penalty (λ=0.002) is too weak to induce sparsity with Normal(0,1) embeddings.
- Autoencoder reconstruction training is not aligned with downstream classification.

**Recommendations for Phase 2:**
1. Increase `l1_lambda` to ~0.01–0.1 to achieve actual sparsity with L1.
2. Consider task-supervised or contrastive pretraining instead of pure reconstruction.
3. Add residual connections or skip connections to preserve discriminative signals.
4. Explore deeper architectures or alternative activation functions (e.g., ReLU with stronger regularization).
