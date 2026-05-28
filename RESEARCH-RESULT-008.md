# RDF Milestone Review — Iteration 008 — Null Result: Role of Training and Anchoring in Vector Semantics

## 1. Pre-Declared Hypothesis and Falsification Criterion
### Pre-Registered Hypotheses:
- **H1 (Semantic Consistency):** Fully trained universal nodes (P3-C with Reconstruction + VICReg) exhibit consistent coordinate semantics (correlation with physical axes like magnitude and gradient) across spatial positions and hierarchical layers.
- **H2 (Training Effect):** Unsupervised training significantly improves semantic consistency compared to untrained, random-weight baseline initializations.
- **H3 (Anchor Effectiveness):** Explicitly anchoring dimensions to target semantic probes (P5-B) increases semantic alignment in those dimensions without collapsing overall representation quality.

### Pre-Declared Falsification Criteria:
- **F2 (Negligible Training Gain):** If the mean semantic consistency gain of trained models over untrained (Xavier random) baselines is $\le 0.05$, the hypothesis that training organizes vector semantics is refuted. (TRIGGERED: actual gain was +0.039).
- **F5 (Anchoring Penalty):** If anchoring (P5-B) reduces the consistency of anchored dimensions or decreases downstream classification accuracy by $\ge 5\%$ compared to the unconstrained model (P5-A), the anchoring hypothesis is refuted. (TRIGGERED: anchoring decreased consistency from 0.714 to 0.700).

## 2. Experimental Protocol
- **Architecture:** P3-C (universal node, shared weights across positions), dimension $d=16$, $d_{out}=16$, tanh activations.
- **Objectives Compared:**
  - **P5-A (Pure Emergence):** Unconstrained Reconstruction + pooled VICReg ($\lambda_{var}=25, \lambda_{cov}=25$).
  - **P5-B (Anchor Features):** Same as P5-A, but first 5 dimensions are regularized using an auxiliary MSE loss toward five pre-defined spatial-temporal probes (Magnitude, Gradient, Variance, Periodicity, Novelty).
  - **Control Group (Untrained Baseline):** Xavier-initialized random weights, no training.
- **Evaluations:**
  - 5-seed cross-validation.
  - Linear probe/regression for each of the 16 dimensions against the 5 semantic axes across all layers (spatial_0, spatial_2, temporal_2) and spatial positions.
  - R² heatmaps to measure explained variance.

## 3. Observed Quantities
- **Within-Layer Semantic Consistency:**
  - Untrained control: 0.962 ± 0.005
  - Trained (P5-A): 0.974 ± 0.003
  - *Result:* Difference is +0.012 (not statistically significant). High consistency is present prior to training.
- **Cross-Layer Semantic Consistency:**
  - Untrained control: 0.541 ± 0.012
  - Trained (P5-A): 0.580 ± 0.011
  - *Result:* Training gain is +0.039 (triggers F2).
- **Anchoring Effectiveness (P5-B):**
  - Unconstrained (P5-A) consistency of dimensions 0–4: 0.714
  - Anchored (P5-B) consistency of dimensions 0–4: 0.700
  - *Result:* Anchoring decreases target dimension consistency by -0.014 (triggers F5). Free dimensions (5–15) in P5-B achieved 0.738 consistency.
- **Explained Variance (R²):**
  - Magnitude and Gradient represent $>90\%$ of total explained variance across all spatial layers.
  - Variance, Periodicity, and Novelty combined account for $<10\%$ in spatial layers, rising to only $\approx 15\%$ at deep temporal layers.

## 4. Verdict
**Refuted.** The hypothesis that unsupervised training is the primary driver of consistent coordinate semantics is refuted. Instead, semantic alignment is predominantly a structural consequence of the chosen architecture (shared weights, tanh activation, and structured binary inputs). The hypothesis that hand-designed semantic anchoring is beneficial is also refuted; anchoring acts as an artificial constraint that degrades natural alignment.

## 5. Construction-vs-Empirical Note
- **Structural (By Construction):**
  The near-perfect within-layer consistency (0.974) is a mathematical consequence of weight-sharing across positions ($W_{enc}$ is spatially uniform). Any single-layer node mapping identical input statistics with identical weights must produce identical semantic tuning. This is a definitional identity of 1D shared-weight convolutions and does not represent an empirical discovery of representation learning.
- **Empirical (Genuinely New):**
  - The discovery that Xavier-initialized random projections of binary inputs through tanh bottlenecks natively partition the input space into highly consistent "Magnitude" and "Gradient" axes is a genuine empirical finding.
  - The fact that training adds only +0.039 to cross-layer consistency demonstrates that unsupervised learning on this architecture refines existing geometric boundaries rather than constructing new coordinate semantics from scratch.

## 6. Limitations
- **Input Simplicity:** The inputs are 1D binary patterns, where the only primary degrees of freedom are density (magnitude) and boundaries (gradients). In higher-dimensional or continuous input spaces, Xavier projections may not natively align so cleanly with physical axes, and training might play a more dominant role.
- **Symmetric Activation Bottleneck:** The use of tanh restricts output coordinates to $[-1, 1]$. This naturally favors binary-like partitioning, which aligns well with binary input metrics but might limit soft semantic modeling.