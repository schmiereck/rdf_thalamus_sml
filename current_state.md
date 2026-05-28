# Current Research State — HSUN Project
**Last updated:** After Phase 4 (iter_007, sub-agents 7.1–7.2)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 4 (Training Objective Comparison) is now RESOLVED.

## Confirmed (with iter/sub-agent references)

### Phase 4 Resolution (iter_007)
1. **Reconstruction + pooled VICReg is the best training objective** at 83.00% ± 2.27%
   (iter_007, 7.1). This exceeds JEPA + pooled VICReg (61.55%) by 21.45pp.

2. **SFA + pooled VICReg is a close second** at 82.15% ± 3.02% (iter_007, 7.1).
   SFA without VICReg completely collapses to 25.00% (chance).

3. **Pooled VICReg is the DOMINANT anti-collapse factor** across all objectives
   (iter_007, 7.1 + 7.2):
   - SFA: +57.15pp (25.00% → 82.15%), p = 0.000002
   - Reconstruction: +33.45pp (49.55% → 83.00%), p = 0.000943
   - JEPA: +8.05pp (53.50% → 61.55%), p = 0.007
   - Hebbian: +4.65pp (43.90% → 48.55%), p = 0.183 (not significant)

4. **Falsification criteria** (iter_007, 7.2):
   - F1 (JEPA+VICReg < 55%): NOT triggered (61.55%) ✅
   - F2 (other objective beats JEPA+VICReg by ≥ 3pp): TRIGGERED ❌
     SFA+VICReg (+20.60pp) and Recon+VICReg (+21.45pp) both exceed
   - F3 (VICReg hurts non-Recon objectives): NOT triggered ✅

5. **Research Manager's prediction was WRONG**: VICReg massively helps
   Reconstruction (+33.45pp). The decoder's intrinsic anti-collapse mechanism
   is insufficient on this architecture.

6. **JEPA without pooled VICReg is barely above untrained**: 53.50% vs 52.10%
   (+1.40pp, p = 0.317, not significant). Local VICReg alone is insufficient.

7. **Hebbian is the weakest objective** even with VICReg (48.55%), below
   untrained baseline (52.10%). Variance maximisation without structured
   prediction or reconstruction is insufficient for discriminative features.

### Phase 3 Carry-Forward (still valid, iter_006)
- P3-C with pooled VICReg + spatial_pooled readout: 61.55% (now superseded by Phase 4)
- Pooled VICReg prevents collapse (+80.3% std increase)
- spatial_pooled_then_flat readout preserves temporal discriminative information

### Phase 1-2 Carry-Forward (still valid)
- JEPA local objective works spatially: 62.12% (d=8), 65.20% (d=16) (iter_003)
- P2-D temporal JEPA: 65.33% ± 2.74% (iter_004)
- Weight sharing has zero expressivity penalty (iter_002, iter_005)
- Zero-shot spatial→temporal transfer is falsified (iter_004)
- Node type is universal, weights are axis-specific (iter_004)

## Refuted Hypotheses
- "JEPA + pooled VICReg is the best training objective": REFUTED (iter_007)
- "Reconstruction natively resists collapse (VICReg won't help)": REFUTED (iter_007)
- "Local VICReg alone prevents collapse": REFUTED — JEPA without pooled VICReg
  is barely above untrained (53.5% vs 52.1%, iter_007)

## Current Best Results
- **Best overall**: Reconstruction + pooled VICReg, 83.00% ± 2.27%, 1,600 params (iter_007)
- **Second best**: SFA + pooled VICReg, 82.15% ± 3.02% (iter_007)
- **JEPA + pooled VICReg**: 61.55% ± 4.86% (iter_007, reproduces iter_006)
- **Spatial only**: JEPA-d16, 65.20% ± 1.80% (iter_003)
- **Temporal only**: P2-D JEPA, 65.33% ± 2.74% (iter_004)
- **Untrained baseline**: 52.10% ± 3.56% (iter_007)

## Experiment Configuration (Updated for Phase 5)
- Architecture: P3-C (shared weights), d=16, d_out=16, 1,600 params
- Training: 30 epochs, 200 train/class, 100 test/class, batch=64, lr=1e-3
- **NEW default objective**: Reconstruction + pooled VICReg
- Readout: spatial_pooled_then_flat (416 features)
- Pooled VICReg: λ_var=25, λ_cov=25 on final representation

## Files Created This Phase
- src/run_phase4.py — Full Phase 4 experiment runner (fixed memory issues)
- phase_4/phase4_results.csv — 45 experiment results
- phase_4/analysis.py — Statistical analysis script
- phase_4/REPORT.md — Comprehensive analysis report
- src/pre_registration.md — Updated with actual results

## Open Questions (ordered by expected value)
1. **Would dedicated hyperparameter tuning for SFA/Hebbian close the gap to
   Reconstruction+VICReg?** The shared envelope (lr=1e-3, 30 epochs) was optimised
   for JEPA. SFA and Hebbian deserve their own sweeps.
2. **Is the VICReg variance term or covariance term the dominant anti-collapse
   mechanism?** Ablating these would clarify the mechanism.
3. **Does Reconstruction+VICReg produce semantically consistent dimensions?**
   This is the Phase 5 question — do the 16 code dimensions carry interpretable
   and consistent semantics across positions and layers?
4. **Can we replace pooled VICReg with a cheaper anti-collapse mechanism?**
   Batch norm, projection head, or explicit code normalization?
5. **Would longer training (100+ epochs) further improve Reconstruction+VICReg
   beyond 83%?** JEPA converges by epoch 30 but Reconstruction might benefit.
6. **Does the Hebbian objective produce more semantically consistent dimensions?**
   Despite lower accuracy, Hebbian's local variance maximisation might yield
   more interpretable features.

## Recent Log (last 3 entries)
- iter_007: Phase 4 complete. Reconstruction+VICReg=83%, SFA+VICReg=82.15%,
  JEPA+VICReg=61.55%. F2 triggered. VICReg is dominant factor.
- iter_006: Phase 3 resolved. P3-C+pooled VICReg+spatial_pooled readout=61.55%.
- iter_005: Phase 3 initial failure. JEPA-to-classification transfer failure.
