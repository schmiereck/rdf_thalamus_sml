# RDF Scientific Pre-Registration

*   **Iteration:** 006-DIAGNOSTIC
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
Phase 3's failure (P3-C gain of only ~1.15pp over untrained baseline on 4-class
classification) is NOT caused by VICReg omission. Code review confirms that
VICReg IS already present in `JEPALoss` (λ_var=25, λ_cov=25) in
`src/training_objectives.py`, applied per-layer to intermediate codes during
the spatial and temporal JEPA steps. The pre-registered hypothesis about
"VICReg omission" is factually incorrect.

The likely cause of Phase 3's failure is one of two mechanisms:

**(a) Representation pooling destroys discriminative position-specific information.**
Phase 3 uses mean-pooled (B, 16) representation, while Phase 1 used flattened
(B, 80+) representation. The global average pool over all spatial × temporal
positions may collapse class-discriminative structure that exists in the
intermediate layer outputs.

**(b) VICReg applied per-layer to intermediate codes does not prevent collapse
of the final pooled representation.** Even if intermediate layers maintain
variance, the final mean-pooling step may produce a collapsed representation
where all samples map to nearly identical vectors, because VICReg is not
explicitly applied to the pooled output.

This diagnostic will determine which mechanism is at fault by:
1. Measuring per-dimension std at intermediate layers and at the pooled level
   (trained vs. untrained) to detect collapse.
2. Comparing classification accuracy across 4 representation strategies
   (pooled, spatial-temporal flatten, per-timestep pooled, per-position pooled)
   to quantify how much discriminative information is lost by pooling.
3. Tracking VICReg var_loss and cov_loss during training to confirm VICReg
   is active and whether it prevents collapse.

## 2. Falsification Criterion
If the pooled representation shows per-dimension std ≥ 1.0 (no collapse) AND
alternative pooling strategies do NOT significantly improve classification
accuracy over the pooled baseline, then pooling is NOT the problem. In that
case, the failure is likely due to the architecture fundamentally being unable
to learn discriminative spatiotemporal representations, regardless of pooling.

If the pooled representation shows per-dimension std << 1.0 (collapsed) BUT
intermediate layers show per-dimension std ≥ 1.0, then mechanism (b) is
confirmed: VICReg on intermediates does not prevent final pooling collapse.

If alternative representations (especially spatial-temporal flatten or
per-timestep pooled) achieve ≥8pp gain over untrained while pooled does not,
then mechanism (a) is confirmed: pooling destroys discriminative information.

## 3. Proposed Method
DIAGNOSTIC ITERATION — single seed (42), P3-C only, 30 epochs.

Step 1: Create P3-C encoder with seed=42, d=16, d_out=16.

Step 2: Generate spatiotemporal dataset (200 train/class, 100 test/class, seed=42).

Step 3: Train for 30 epochs using the existing training infrastructure
(imported from run_phase3.py / run_phase3_optimized.py) with batch=64, lr=1e-3.

Step 4: After each epoch (and before training at epoch 0), measure and log:
  a. Per-dimension std of the pooled representation on the TEST set
  b. Per-dimension std of each spatial layer's output (reshaped to 2D)
  c. Per-dimension std of each temporal layer's output
  d. VICReg var_loss and cov_loss from the JEPA step
  e. Prediction loss from JEPA
  f. Classification accuracy (train + test) using pooled representation

Step 5: After training, create an untrained P3-C encoder (same seed) and measure:
  a. Per-dim std of pooled representation
  b. Per-dim std of each layer's output

Step 6: Pooling comparison — after training, try classification with:
  a. Pooled (current): mean over all positions → (B, 16)
  b. Spatial-temporal flatten (final temporal layer): reshape (B, 26, 10, 16)
     → flatten → (B, 4160). Use PCA to reduce to 100 features, then classify.
  c. Per-timestep pooled: mean over spatial only → (B, 26, 16) → flatten → (B, 416)
  d. Per-position pooled: mean over temporal only → (B, 10, 16) → flatten → (B, 160)
  For each, fit SimpleLogisticRegression and report test accuracy.

Step 7: Save results to:
  - src/variance_diagnostic_results.csv (epoch-level data)
  - src/pooling_comparison_results.csv (representation comparison)

Step 8: Write analysis to phase_3/diagnostic_report.md answering:
  1. Is VICReg active? (var_loss, cov_loss trends; per-dim stds ≥ 1.0?)
  2. Is the pooled representation collapsed? (trained vs untrained std)
  3. Does pooling destroy discriminative information? (4 strategies compared)
  4. What is the most likely cause of failure?

Files to create/modify:
  - src/pre_registration.md (UPDATE — corrected hypothesis)
  - src/diagnostic_phase3_vicreg.py (NEW — diagnostic script)
  - phase_3/diagnostic_report.md (NEW — analysis and conclusions)

---
*Updated after code review revealed VICReg is already present in JEPALoss.*
