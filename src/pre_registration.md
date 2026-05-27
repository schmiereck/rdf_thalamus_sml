# RDF Scientific Pre-Registration

*   **Iteration:** 003
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
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

## 2. Falsification Criterion
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

## 3. Proposed Method
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
*Created automatically by the RDF Orchestrator prior to iteration execution.*

## Phase 1 v2 Results (Iteration 3)

**Date:** 2025-01-20

### Summary of Findings Against Each Criterion

| Criterion | Description | Threshold | Actual | Verdict |
|:---|:---|:---|:---|:---|
| C1 | JEPA hypothesis falsified if mean < 50% at d=8 | < 50% | **62.12%** | **NOT FALSIFIED** |
| C2 | General local-objective falsified if ALL four < 48.4% at d=8 | All < 48.4% | JEPA 62.1%, Contrastive 50.6%, SFA 50.6%, Hebbian 24.0% | **NOT FALSIFIED** |
| C3 | d=8 bottleneck SUPPORTED if d16 > d8 + 10pp | > 10pp | **3.08pp** | **NOT SUPPORTED** |
| C4 | d=8 bottleneck REFUTED if d16 ≤ d8 + 5pp | ≤ 5pp | **3.08pp** | **REFUTED** |
| C5 | Temporal-unification falsified if JEPA spatial < 50% | < 50% | **62.12%** | **NOT FALSIFIED** |

### Final Verdict on Each Hypothesis

1. **Primary JEPA hypothesis: CONFIRMED.** Mean JEPA-d8 test accuracy = 62.12% (5 seeds), exceeding both the 50% falsification threshold and the pre-registered ≥60% target. Paired t-test vs untrained baseline: +15.96pp, t(4)=5.713, p=0.0046. The JEPA objective successfully aligns the encoder with the discriminative structure of the data.

2. **General local-objective hypothesis: PARTIALLY CONFIRMED.** Three of four objectives (JEPA, Contrastive, SFA) exceed the untrained baseline of 46.16%, but only JEPA clears the ≥5pp practical success bar. Contrastive (+4.48pp, p=0.17) and SFA (+4.40pp, p=0.36) show positive trends but are not statistically significant at n=5. Hebbian learning catastrophically fails (−22.20pp, p=0.0012), indicating that not all local objectives are viable.

3. **d=8 bottleneck hypothesis: REFUTED.** The gain from d=8 to d=16 for JEPA is only 3.08pp (62.12% → 65.20%), well within the ≤5pp refutation band. A 3.8× increase in parameters (1,264 → 4,832) yields minimal test improvement. The bottleneck is **not** the primary cause of Phase 1 failure; objective misalignment was.

4. **Temporal-unification claim: CLEARED FOR PHASE 2.** Since JEPA succeeds spatially (62.12% ≫ 50%), Criterion 5 is not falsified. The same JEPA objective applied along the time axis is scientifically justified for Phase 2 temporal integration experiments.

### Additional Research Manager Criterion

| Objective | Δ vs Untrained | Verdict |
|:---|---:|:---|
| JEPA-d8 | +15.96pp | **SUCCESS** |
| JEPA-d16 | +10.60pp | **SUCCESS** |
| Contrastive-d8 | +4.48pp | FAIL (below 5pp bar) |
| SFA-d8 | +4.40pp | FAIL (below 5pp bar) |
| Hebbian-d8 | −22.20pp | FAIL (catastrophic) |

### Recommendation

**Proceed to Phase 2 with JEPA as the temporal integration objective.** Use the d=8 architecture (parameter-efficient, strong generalization). The JEPA formulation (bidirectional latent prediction + VICReg collapse prevention) should be applied along the time axis to learn temporal structure without labels.

---
*Results section appended after experiment completion.*
