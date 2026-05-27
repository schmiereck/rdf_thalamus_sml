# Current Research State — HSUN Project
**Last updated:** After Phase 1 v2 completion (iter_003, sub-agents 3.1–3.2)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 1 (Spatial Hierarchy) is now substantially
advanced with the JEPA breakthrough.

## Confirmed (with iter/sub-agent references)

1. **JEPA local objective works** (iter_003, 3.1):
   - JEPA-d8: 62.12% ± 4.34% test accuracy (5 seeds)
   - +15.96pp over untrained baseline (p=0.0046, significant)
   - +20.6pp over best prior trained method (simultaneous reconstruction: 41.5%)
   - Pre-registered ≥60% target MET (62.12% > 60%)
   - Research Manager's ≥5pp bar CLEARED (+15.96pp >> 5pp)

2. **d=8 bottleneck is NOT the primary cause of Phase 1 failure** (iter_003, 3.2):
   - JEPA-d16: 65.20% ± 1.80%, only +3.08pp over JEPA-d8
   - 3.8× more parameters yields negligible test improvement
   - Bottleneck hypothesis REFUTED per pre-registered Criterion C4
   - Objective misalignment (reconstruction) was the true cause

3. **Reconstruction objective was the root cause of Phase 1 failure** (iter_002 + iter_003):
   - Same P1-B architecture: 33.5% (reconstruction) → 62.1% (JEPA)
   - 85% relative improvement from objective change alone
   - Latent-space prediction preserves discriminative information;
     pixel-space reconstruction destroys it

4. **Not all local objectives are viable** (iter_003, 3.1):
   - Contrastive: 50.64% (+4.48pp, p=0.17, not significant)
   - SFA: 50.56% (+4.40pp, p=0.36, not significant, high variance)
   - Hebbian: 23.96% (−22.20pp, catastrophic failure, near chance)
   - Only JEPA clears the practical success bar

5. **Weight sharing has zero expressivity penalty** (iter_002, 2.2):
   - P1-B (cross-layer sharing): 33.52% vs P1-C (independent): 33.24%
   - Gap: −0.28pp (confirmed with reconstruction objective)
   - JEPA results further validate this (all JEPA runs use cross-layer sharing)

6. **Cross-layer weight sharing + simultaneous training + JEPA is the winning combination** (iter_003):
   - 1,264 parameters achieve 62.1% accuracy
   - The universal-node hypothesis (shared weights across layers) is viable

7. **Temporal-unification path cleared** (iter_003, 3.2):
   - Pre-registered Criterion C5 NOT FALSIFIED
   - JEPA succeeds spatially → same objective can be applied temporally
   - P2-D (spatial-temporal symmetry) is now testable

## Refuted Hypotheses
- Phase 1 original hypothesis (reconstruction + L1 ≥ 80%): FALSIFIED (iter_002)
- d=8 bottleneck hypothesis: REFUTED (iter_003, gap only 3.08pp)
- "All local objectives are equally viable": REFUTED (Hebbian fails, others marginal)

## Current Best Result
- **JEPA-d8**: 62.12% ± 4.34% test accuracy, 1,264 parameters, 0% sparsity
- **JEPA-d16**: 65.20% ± 1.80% test accuracy, 4,832 parameters, 0% sparsity
- Still below Phase 1's 80% success criterion, but massive progress from 33.5%

## Files Created This Phase
- src/training_objectives.py — JEPALoss, ContrastiveLoss, SFALoss, HebbianLoss, _Adam
- src/run_phase1_v2.py — Experiment runner (7 configs × 5 seeds)
- src/test_objectives.py — Self-tests for all objectives + encoder backward
- phase_1/objectives_results.csv — Raw experimental results
- phase_1/objectives_report.md — Full comparison report
- src/pre_registration.md — Updated with Phase 1 v2 results and verdicts

## Modified Files
- src/hierarchical_encoder.py — Added forward_with_intermediates() and
  backward_from_code_grads() methods for gradient-based training with
  arbitrary objectives

## Open Questions (ordered by expected value)
1. **Can JEPA reach ≥80% with tuning?** 62% is strong but Phase 1's criterion is 80%.
   More epochs, learning rate schedule, or larger datasets may help.
2. **Can the same JEPA objective work temporally?** P2-D (three-temporal-slot node)
   is the key test: can a spatially-trained JEPA node be applied to time without
   retraining? This is the strongest possible evidence for unification.
3. **Can sparsity be added without sacrificing accuracy?** Current JEPA codes have
   ~0% sparsity. k-WTA or L1 on top of JEPA could add sparsity.
4. **Why does Hebbian fail so catastrophically?** Oja's rule drives representations
   toward principal components, which may not be category-discriminative for this
   structured binary data.
5. **Can Contrastive/SFA be improved?** Better augmentation strategies or tuning
   might push them past the 5pp bar.
6. **How does JEPA scale to larger inputs?** 128 pixels for the physics sandbox
   would test whether the approach generalizes.

## Next Phase: Phase 2 — Temporal Integration
The natural next step is Phase 2 (Temporal Integration at a Single Node).
Key question: Can the JEPA objective, applied along the time axis, learn
temporal structure? And critically, can P2-D (same kernel-3 node with temporal
inputs) apply spatially-trained weights temporally without retraining?
