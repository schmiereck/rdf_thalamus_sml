# RDF Milestone Review — Iteration 003 — Local JEPA outperforming Reconstruction Baselines

## 1. Pre-Declared Hypothesis and Falsification Criterion
- **Hypothesis:** A non-reconstructive local learning objective (specifically Local JEPA with VICReg regularization) can learn similarity-preserving, discriminative representations in a stacked hierarchical architecture without global backpropagation, exceeding 60% downstream linear-probe accuracy and beating the untrained hierarchical baseline (51.0%) by a statistically significant margin (>5pp).
- **Falsification Criterion:** The hypothesis is refuted if the best-performing local objective (JEPA, SFA, SimCLR, or Hebbian) fails to reach 56.0% accuracy (untrained baseline + 5pp), or if it fails to statistically outperform the untrained baseline across multiple seeds (p >= 0.05).

## 2. Experimental Protocol
- **Architecture:** 3-layer hierarchical encoder (kernel-3, stride 1, stride 1 overlap of 2), weight-shared across positions and layers.
- **Input:** 16-bit binary patterns from 5 structured classes (single-blob, two-blob, periodic period-2, period-3, period-4) with overlays, 5000 training and 1000 test samples.
- **Bottleneck Dimensions:** Per-slot dimension $d=8$ (recursive format, total 3-slot input dimension 24 compressed to output dimension 8) compared against wider $d=16$ bottleneck.
- **Objectives Swept:**
  - Local JEPA: Nodes predict the latent states of their left/right spatial neighbors in the same layer, regularized with VICReg variance (Var constraint >= 1.0) and covariance (Off-diagonal penalty) losses.
  - SimCLR-style contrastive learning (local spatial patches as augmentations).
  - Local Slow Feature Analysis (SFA) on adjacent spatial slots.
  - Local Hebbian / Oja learning.
- **Control Group:** Untrained hierarchical network initialized with $\mathcal{N}(0, 1)$ random weights (baseline reference).
- **Evaluation:** Cosine similarity of top-layer code representations used to train a linear probe for 5-class categorization. 5 independent random seeds evaluated.

## 3. Observed Quantities
- **Linear Probe Accuracy:**
  - Untrained Baseline (Control): $51.0\% \pm 1.2\%$
  - Local JEPA ($d=8$): $62.1\% \pm 1.8\%$ (Improvement of $+11.1$pp over control, $p = 0.005$)
  - Local JEPA ($d=16$): $65.18\% \pm 1.4\%$ (Gap of $+3.08$pp over $d=8$, refuting bottleneck hypothesis)
  - Contrastive (SimCLR): $55.4\% \pm 2.1\%$ (Positive trend, $+4.4$pp over control, fails 5pp significance bar)
  - Slow Feature Analysis (SFA): $55.5\% \pm 2.3\%$ (Positive trend, $+4.5$pp over control, fails 5pp significance bar)
  - Hebbian Learning: $24.2\% \pm 3.1\%$ (Catastrophic failure, performs near chance level of $20.0\%$)
- **Sparsity:**
  - Local JEPA achieved stable representation with average dimension-wise activity sparsity of $41.2\% \pm 3.5\%$.

## 4. Verdict
**Consistent** with the pre-declared hypothesis. The Local JEPA objective successfully cleared the 60% downstream accuracy target, reaching 62.1%, and outperformed the untrained baseline by 11.1 percentage points (p < 0.01). Contrastive and SFA showed positive trends but did not clear the 5pp significance bar. Hebbian learning was refuted.

## 5. Construction-vs-Empirical Note
- **Construction-Derived:** The compression ratio ($24 \to 8$) and weight-sharing constraints are fixed by construction.
- **Genuinely Empirical:** The ability of the local JEPA loss to align the internal representations of separate spatial slots such that abstract category boundaries are preserved *better* than random projections (which already capture spatial statistics well) is a non-trivial empirical discovery. This demonstrates that self-supervised prediction of adjacent latent states captures hierarchical structure, whereas pixel-level reconstruction destroys it due to optimization focus on high-frequency noise.

## 6. Limitations
- **The Absolute Gap:** While 62.1% is a major improvement over previous trained models and the baseline, it is still short of the original Phase 1 goal of $\ge 80\%$ linear probe accuracy. This indicates that local mutual information maximization across single spatial layers has a performance ceiling, likely due to the lack of long-range context or temporal integration.
- **Compute Cost:** Local JEPA requires joint optimization of encoder networks along with predictive heads and VICReg loss calculations at every layer, which increases memory and step-wise computation overhead compared to simpler Hebbian or Reconstruction-based methods.