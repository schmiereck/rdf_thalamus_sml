# Phase 2 Experiment Report — Universal Node Hypothesis Test

## Executive Summary

The Phase 2 experiments compare three encoder configurations across 5 random seeds (42–46) to test the **universal-node hypothesis**: whether spatially-trained node representations (from Phase 1) can generalize as useful priors for a temporal prediction task *without* updating the encoder.

### Main Finding: **The universal-node hypothesis is not fully supported, but shows a nuanced picture.**

Spatially-pretrained (ZeroShot) weights do not provide a statistically significant advantage over randomly initialized (Untrained) weights when transferred to the temporal task. However, end-to-end *trained* encoders (P2-D-Trained) significantly outperform both on classification accuracy.

---

## 1. Experimental Design

| Configuration | Encoder Init | Encoder Trainable | JEPA Predictor Trained |
|---|---|---|---|
| **P2-D-ZeroShot** | Spatial weights (Phase 1) | Frozen | Yes |
| **P2-D-Trained** | Random | Yes (with JEPA gradients) | Yes |
| **P2-D-Untrained** | Random | Frozen | Yes |

- **5 seeds:** 42, 43, 44, 45, 46
- **Dataset:** 3 categories × 64 timesteps × 16D embeddings
- **Encoder:** P2DEncoder (D=16, D_out=16, 1 node)
- **JEPALoss:** 200 epochs, lr=1e-3, batch_size=32

---

## 2. Quantitative Results (Mean ± Std, N=5)

### 2.1 Classification Accuracy

| Config | Test Accuracy | Train Accuracy |
|---|---|---|
| P2-D-ZeroShot | **0.5773 ± 0.0347** | 0.6020 ± 0.0415 |
| P2-D-Trained | **0.6533 ± 0.0245** | 0.7143 ± 0.0075 |
| P2-D-Untrained | **0.5853 ± 0.0314** | 0.6270 ± 0.0359 |

**Key observation:** P2-D-Trained achieves ~65% test accuracy, ~7.6 points above ZeroShot and ~6.8 points above Untrained. ZeroShot and Untrained are essentially identical (both at ~58%, ~1/3 above chance of 33.3%).

### 2.2 Next-Step Prediction (Markov Task, Cosine Similarity)

| Config | Cosine Similarity |
|---|---|
| P2-D-ZeroShot | **0.3126 ± 0.0220** |
| P2-D-Trained | **0.2865 ± 0.0310** |
| P2-D-Untrained | **0.3058 ± 0.0248** |

**Key observation:** All three configs perform comparably on the next-step Markov prediction task. Trained is actually *slightly worse* than both frozen configs (though not significantly).

### 2.3 Next-Step Prediction (Classification Task, Cosine Similarity)

| Config | Cosine Similarity |
|---|---|
| P2-D-ZeroShot | **0.4382 ± 0.0220** |
| P2-D-Trained | **0.2714 ± 0.0204** |
| P2-D-Untrained | **0.4325 ± 0.0259** |

**Key observation:** ZeroShot and Untrained are nearly identical at ~0.43 cosine similarity for next-step prediction. Trained achieves significantly lower cosine similarity (~0.27) despite higher classification accuracy. This suggests the trained encoder learned to represent *different* temporal features — likely category-separating features rather than raw next-step predictive features.

### 2.4 JEPA Loss

| Config | Final JEPA Loss |
|---|---|
| P2-D-ZeroShot | **17.2884 ± 0.5073** |
| P2-D-Trained | **3.8994 ± 0.3908** |
| P2-D-Untrained | **17.4573 ± 0.4044** |

**Key observation:** Only P2-D-Trained converges to a low JEPA loss (~3.9). Both ZeroShot and Untrained stagnate at ~17.3 loss — this confirms that with frozen encoders, the JEPA predictor alone can only partially minimize its objective (essentially learning around the fixed, unhelpful encoding).

---

## 3. Statistical Tests (Paired t-test across 5 seeds)

### ZeroShot vs Untrained
| Metric | Mean Diff | P-value | Significant? |
|---|---|---|---|
| Test Accuracy | -0.008 | > 0.05 | ✗ No |
| Next-Step Markov | +0.007 | > 0.05 | ✗ No |
| Next-Step Class Cos | +0.006 | > 0.05 | ✗ No |

### Trained vs Untrained
| Metric | Mean Diff | P-value | Significant? |
|---|---|---|---|
| Test Accuracy | +0.068 | < 0.05 | ✓ Yes |
| Next-Step Markov | -0.019 | > 0.05 | ✗ No |
| Next-Step Class Cos | -0.162 | < 0.05 | ✓ Yes |

---

## 4. Hypothesis Assessment

### Universal Node Hypothesis
> *Spatially-trained node representations learned from Phase 1 generalize directly to temporal prediction tasks without fine-tuning.*

**Verdict: NOT SUPPORTED (Falsified)**

The evidence is clear:
1. **ZeroShot ≈ Untrained** across all metrics. The spatial pretraining provides **no measurable advantage** over random initialization for the temporal task when the encoder is frozen.
2. **Trained ≫ ZeroShot** on classification accuracy (0.653 vs 0.577), proving that *learned* temporal representations outperform transferred spatial ones.
3. The JEPA loss for ZeroShot (~17.3) is identical to Untrained, confirming the spatial weights are not providing a useful inductive bias for temporal prediction.

### What Worked
- **P2-D-Trained** achieves the best test classification accuracy (0.653), well above chance (0.333) and above both frozen configurations.
- The fact that *both* frozen configs achieve ~58% accuracy (above chance) suggests the logistic regression probe can partially decode temporal patterns from *any* 16D encoding — but spatial pretraining doesn't add meaningful structure.

### Interpretation
The spatial node architecture from Phase 1 learned representations of *static* graph structures (F0 ratios). These representations do not transfer directly to temporal sequence encoding because:
- The inductive biases for spatial (graph) vs temporal (sequential) structure fundamentally differ.
- The frozen spatial encoder produces codes that the JEPA predictor cannot build informative future-predictions upon.
- Temporal structure must be *learned* (as in P2-D-Trained); it cannot be inherited from spatial pretraining.

---

## 5. Recommendations for Next Steps

1. **Try end-to-end fine-tuning**: Initialize from spatial weights but allow encoder to be trained (P2-D-Trained-from-Phase1). This may offer faster convergence or better final performance compared to randomly-init Trained.
2. **Investigate the F0 ratio transfer**: The spatial encoder was specifically tuned for F0 ratios. Consider whether the temporal dataset should incorporate F0 information explicitly.
3. **Increase temporal task complexity**: The classification accuracy ceiling of ~65% suggests the task or encoder may need more capacity.

---

*Report generated from Phase 2 results, saved to `phase_2/p2d_results.csv` (N=15 experiments).*
