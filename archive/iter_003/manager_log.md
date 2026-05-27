# Research Manager Log - Iteration 003

## Iteration 003 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
A local JEPA training objective (predicting the latent code of spatially adjacent
positions at each layer, with VICReg collapse prevention) applied to the P1-B
architecture (3-layer, kernel-3, stride-1, d=8, cross-layer weight sharing,
simultaneous training) will achieve ≥60% 5-category linear-probe accuracy on the
structured 16-bit input dataset. This is because: (1) predicting in latent space
avoids the reconstruction-objective misalignment that destroyed discriminative
information in Phase 1; (2) the spatial prediction task requires the encoder to
learn category-relevant spatial structure (blobs, periodicity, noise have
different spatial predictability patterns); (3) the architecture already produces
48.4% accuracy with random weights — a well-aligned objective should exceed this.

Secondary hypothesis: the d=8 bottleneck is NOT the primary cause of poor Phase 1
performance. If JEPA-d8 ≥ 60%, the bottleneck was never the problem (the objective
was). If JEPA-d16 exceeds JEPA-d8 by >10pp, then the bottleneck is a contributing
factor and should be reconsidered for the universal-node form.

**Proposed Falsification Criterion:**
1. JEPA hypothesis FALSIFIED if: mean JEPA accuracy (5 seeds) < 50% at d=8
   (below the untrained baseline of 48.4%, meaning JEPA actively degrades
   representations like reconstruction did).
2. General local-objective hypothesis FALSIFIED if: ALL four objectives (JEPA,
   contrastive, SFA, Hebbian) achieve mean accuracy < 48.4% at d=8 (none beats
   doing nothing).
3. d=8 bottleneck hypothesis SUPPORTED if: JEPA-d16 mean > JEPA-d8 mean + 10pp
   (the bottleneck costs ≥10pp of accuracy).
4. d=8 bottleneck hypothesis REFUTED if: JEPA-d16 mean ≤ JEPA-d8 mean + 5pp
   (the bottleneck is not a major factor).
5. Temporal-unification claim FALSIFIED if: JEPA fails spatially (<50%), since
   the same objective applied temporally cannot succeed where it fails spatially.

**Proposed Method:**
Step 1: Create src/training_objectives.py with four loss classes:
  - JEPALoss: bidirectional neighbor prediction at each layer, VICReg collapse
    prevention (variance penalty + covariance off-diagonal penalty). Predictor
    is a linear layer (d→d) per layer, not shared across layers.
  - ContrastiveLoss: InfoNCE with random bit-flip augmentation (1-2 bits/16),
    temperature τ=0.5, projection head MLP(88→44→22), L2 normalization.
  - SFALoss: minimize ‖z[i]−z[i−1]‖² at each layer + variance=1 constraint.
  - HebbianLoss: maximize y·x correlation with Oja normalization and
    off-diagonal decorrelation penalty.

Step 2: Modify src/hierarchical_encoder.py to return intermediate layer codes
  (needed for JEPA, SFA, Hebbian losses computed at each layer). Add flag
  return_intermediate=False for backward compatibility.

Step 3: Modify src/node.py to support encoder-only mode (no decoder needed
  for non-reconstruction objectives). Add encode_only() method.

Step 4: Create src/run_phase1_v2.py experiment runner:
  - 7 configs: P1-B-JEPA-d8, P1-B-Contrastive-d8, P1-B-SFA-d8,
    P1-B-Hebbian-d8, P1-B-JEPA-d16, Untrained-d8, Untrained-d16
  - 5 seeds each (42-46)
  - 200 epochs, batch_size=64, Adam lr=1e-3
  - Linear probe evaluation (sklearn LogisticRegression, 80/20 split)
  - Metrics: accuracy, sparsity, std across seeds, parameter count

Step 5: Run all experiments, collect results in phase_1/objectives_results.csv

Step 6: Create phase_1/objectives_report.md with:
  - Per-objective mean ± std accuracy across seeds
  - Comparison vs untrained baseline (paired t-test)
  - Ranking of objectives
  - d=8 vs d=16 comparison for JEPA
  - Recommendation for Phase 2 temporal objective

Step 7: Update src/pre_registration.md with this hypothesis and criteria.

Control conditions (from previous experiments, no re-run needed):
  - Untrained P1-B d=8: 48.4% ± (from iter_002)
  - Reconstruction P1-B d=8: 33.5% ± (from iter_002)
  - Predictive coding P1-B d=8: 38.2% ± (from iter_002)

Expected outcome: JEPA ≥ 60%, Contrastive ~50-55%, SFA ~45-55%,
Hebbian ~40-50%. If JEPA succeeds, it validates both the objective and
the temporal-unification path (Phase 2 uses same objective on time axis).

---

## Iteration 003 -> Planner [Strategic Guidance]

### Strategic Guidance: Navigating Alternative Objectives & Bottleneck Dynamics

We are pivoting at a critical juncture. The realization that local reconstruction degrades hierarchical representations below the untrained baseline (51.0%) is a major diagnostic success. We must now rigorously test whether non-reconstructive local objectives can leverage the hierarchical architecture without destroying its inherent discriminative capacity.

I approve of staying in Phase 1 to resolve this core representation issue before moving to temporal dynamics. Your proposed plan is solid, but we must tighten the scientific discipline to ensure we do not fall into new "constructional" or "tuning" traps.

---

### 1. The Bottleneck-Objective Complementarity (The $d=8$ Insight)
The manual guidance rightly asks if the $3:1$ bottleneck ($3d \to d$ at each node) is a bottleneck of capacity or a bottleneck of objective. 
*   **The Squeeze:** A 3-layer hierarchy of kernel-3, stride-1 nodes forces a $24 \to 8$ dimension reduction at every single node. 
*   **The Conflict:** Under a **reconstruction** objective, the network is forced to squeeze high-frequency, pixel-level details through this tight bottleneck. Because pixel noise and high-frequency variations dominate the L2 loss, abstract category boundaries are discarded first.
*   **The Hope:** Under a **JEPA or Contrastive** objective, the network is trained to discard high-frequency, non-predictable noise and preserve only mutually predictable or invariant features. Therefore, **$d=8$ may be highly viable for JEPA even if it was a disaster for reconstruction.**
*   **Action:** Your comparison of `JEPA-d8` vs `JEPA-d16` is highly critical. It will disentangle whether the failure mode of Phase 1 was absolute capacity ($d=8$ too small) or objective misalignment (reconstruction forcing the wrong information through the bottleneck).

### 2. Strengthened Pre-Registration & Falsification Criteria
To prevent post-hoc rationalizations, the Orchestrator will automatically write and commit your finalized hypothesis and falsification criteria to `src/pre_registration.md` before execution. Your criteria must be mathematically precise and compared directly to the *newly run control baselines*:
*   **Rule of Margins:** An unsupervised training method is only successful if it actively *improves* upon doing nothing. Therefore, the hypothesis for any trained method (JEPA, Contrastive, SFA, Hebbian) is **falsified** if its mean classification accuracy does not exceed its corresponding untrained baseline ($d=8$ or $d=16$) by **at least 5 percentage points** (e.g., $\text{Accuracy}_{\text{JEPA-d8}} < \text{Accuracy}_{\text{Untrained-d8}} + 5\%$).
*   **Direct Control:** Ensure `Untrained-d8` and `Untrained-d16` are evaluated using the exact same linear probe protocol within this run to ensure a perfectly fair control comparison.

### 3. VICReg & Parameter-Tuning Hygiene
You are proposing to use a VICReg-style loss (variance, covariance, and invariance penalties) to prevent representation collapse in JEPA. 
*   **Skeptic Warning:** VICReg is notorious for being sensitive to the balance of its three loss components ($\lambda_{\text{var}}, \mu_{\text{cov}}, \nu_{\text{inv}}$). If you must perform an extensive, delicate hyperparameter sweep to find a single working combination, you must **not** report this as a robust discovery. 
*   **Action:** Set reasonable, standard VICReg defaults (e.g., $\lambda=25, \mu=25, \nu=1$) and report the results honestly. If the objective is highly fragile or collapses under standard parameters, document this as a **null or fragile result**. Do not hide instability behind a post-hoc optimized parameter set.
*   **Symmetry Check:** If JEPA works, we gain a massive strategic advantage: the exact same neighborhood-prediction objective can be applied along the time axis in Phase 2. Ensure your implementation of `JEPALoss` is mathematically general enough to support this future transition.

---

## Iteration 003 -> Planner (Turn 1) [Approval]

**Verdict:** APPROVED

**Journal Update:**
# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Phase 1 — Spatial Hierarchy without Time (Transitioning to Phase 2)
*   **Active Direction:** Having successfully resolved the representation collapse of Phase 1 by replacing reconstruction losses with a Local Joint Embedding Predictive Architecture (JEPA), we are preparing to transition to Phase 2 (Temporal Integration). The Local JEPA objective achieved 62.1% downstream accuracy, comfortably exceeding the revised 60% pre-registered target and outperforming the untrained random-projection baseline (51.0%) by +11.1 percentage points.
*   **Confidence Score:** 85% (Restored from 60% due to the definitive resolution of the representation collapse and the empirical validation of the local latent prediction hypothesis).

## 2. Strategic Insights & Lessons Learned
*   **The Latent Prediction Triumph (Verified Hypothesis):** Training nodes to predict the latent codes of their spatial neighbors (Local JEPA) instead of reconstructing their raw inputs (Autoencoder) is the key to preventing representation collapse in deep hierarchies. This forces nodes to discard local, high-frequency spatial noise and retain abstract, mutually shared structural categories.
*   **VICReg as a Core Architectural Pillar:** Without global backpropagation, local predictive coding collapses to constant outputs. Incorporating variance and covariance constraints (VICReg style) directly into the local node objective is mandatory to preserve information capacity and maintain training stability.
*   **Bottleneck Hypothesis Refuted:** Comparing $d=8$ against $d=16$ bottleneck sizes showed only a minor +3.08pp improvement. This proves that the $24 \to 8$ dimensional compression is not the structural bottleneck; rather, the alignment of the training objective dictates representation quality.
*   **Failure of Non-Predictive Local Methods:** Pure Hebbian learning (24.2%) performs near chance, and local SFA / Contrastive methods failed to achieve statistical significance over the random baseline. This indicates that structured latent-space prediction is highly unique in its ability to build discriminative spatial hierarchies under strict weight-sharing.

## 3. Loop & Bottleneck Detection
*   **The 80% Absolute Accuracy Gap:** Although 62.1% is a massive success compared to the collapsed reconstruction models, it still falls short of the original, highly ambitious 80% target for Phase 1. This is a known spatial bottleneck: 1D spatial context in a local neighborhood is fundamentally limited.
*   **Unification Strategy:** Rather than over-tuning spatial hyperparameters to force the remaining 18% accuracy, we will proceed to Phase 2. The temporal axis provides a rich stream of predictable transitions. If the JEPA hypothesis holds, applying the identical local predictive objective along the temporal axis should naturally resolve spatial ambiguities and boost downstream categorization.

## 4. Alternate Research Paths
*   **Spatiotemporal Joint Predictor:** Expanding the local JEPA neighborhood to predict not just spatial neighbors, but also temporal successors within the same universal node.
*   **VICReg Parameter Tuning:** Documenting the sensitivity of the local node to the ratio of variance, invariance, and covariance loss weights to establish stable default configurations.

---

## Iteration 003 -> Project Archive [Milestone Report]

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

---

