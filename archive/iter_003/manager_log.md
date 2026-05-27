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

