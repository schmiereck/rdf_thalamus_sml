# Current Research State — HSUN Project
**Last updated:** After Phase 6 (iter_006, sub-agents 6.1–6.3)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 3 (Unified Spatiotemporal Grid) is now RESOLVED.

## Confirmed (with iter/sub-agent references)

### Phase 3 Resolution (iter_006)
1. **VICReg was NOT omitted** — it was present in JEPALoss with λ_var=25, λ_cov=25
   (iter_006, 6.1 code audit). The original pre-registered hypothesis was factually
   incorrect.

2. **VICReg on intermediate codes is INEFFECTIVE** for the pooled representation
   (iter_006, 6.2 diagnostic):
   - Per-dim stds at intermediate layers: ~0.07-0.08 (target ≥1.0)
   - VICReg gradient per element ≈ 0.0008/elem vs prediction gradient ≈ 0.016/elem
   - The prediction gradient overwhelms VICReg by ~20×
   - Mathematical cause: M = B*T*S = 28,672 elements dilutes the gradient

3. **Mean-pooling destroys discriminative information** (iter_006, 6.2 diagnostic):
   - spatial_pooled_then_flat (53.5%) >> pooled (44.25%) = +9.25pp gap
   - Temporal structure is the primary discriminative signal
   - Mean-pooling over both space and time erases this signal

4. **Pooled VICReg fix is EFFECTIVE** (iter_006, 6.3 factorial experiment):
   - Applying VICReg directly to pooled representation (M=B=64) concentrates
     gradient 450× per element
   - Per-dim pooled std: 0.072 → 0.130 (+80.3%, p < 0.001)
   - Variance loss: 0.0 (inactive) → 0.87 (active)

5. **Combined fix PASSES all falsification criteria** (iter_006, 6.3):
   - P3-C + pooled VICReg + spatial_pooled_then_flat = 61.55% test accuracy
   - Gain over untrained: +9.45pp (threshold ≥8pp) ✅
   - p = 0.013 (threshold <0.05) ✅
   - Cohen's d = 1.91 (threshold ≥1.0) ✅
   - F2 (sharing penalty): 0.0pp ✅
   - F3 (within 20pp of P3-A): 61.55% >> 24.5% ✅
   - F4 (loss ratio): 27.4 < 43.75 ✅

6. **Both fixes are NECESSARY** (iter_006, 6.3 2×2 factorial):
   - Readout-only (no VICReg): +1.4pp over untrained (NOT significant)
   - VICReg-only (pooled readout): +7.75pp (just below 8pp threshold)
   - Both together: +9.45pp (significant, large effect)

### Phase 1-2 Carry-Forward (still valid)
- JEPA local objective works spatially: 62.12% (d=8), 65.20% (d=16) (iter_003)
- P2-D temporal JEPA: 65.33% ± 2.74% (iter_004)
- Weight sharing has zero expressivity penalty (iter_002, iter_005)
- Zero-shot spatial→temporal transfer is falsified (iter_004)
- Node type is universal, weights are axis-specific (iter_004)

## Refuted Hypotheses
- "VICReg was omitted from Phase 3 training": REFUTED — VICReg IS present (iter_006, 6.1)
- "VICReg omission caused collapse": PARTIALLY REFUTED — VICReg is present but
  INEFFECTIVE due to gradient dilution (iter_006, 6.2)
- "The spatiotemporal architecture fundamentally cannot learn": REFUTED — P3-C
  with pooled VICReg achieves 61.55% (iter_006, 6.3)

## Current Best Results
- **Spatial only**: JEPA-d16, 65.20% ± 1.80%, 4,832 params (iter_003)
- **Temporal only**: P2-D JEPA, 65.33% ± 2.74% (iter_004)
- **Spatiotemporal (P3-C, pooled VICReg, spatial_pooled readout)**: 61.55% ± 4.67%, 1,600 params (iter_006)
- **Spatiotemporal (P3-C, pooled VICReg, pooled readout)**: 49.15% ± 3.76% (iter_006)

## Experiment Configuration (Updated)
- Architecture: P3-C (shared weights), d=16, d_out=16, 1,600 params
- Training: 30 epochs, 200 train/class, 100 test/class, batch=64, lr=1e-3
- NEW: Pooled VICReg (λ_var=25, λ_cov=25) on final representation
- NEW: spatial_pooled_then_flat readout (416 features) for classification

## Files Created This Phase
- src/diagnostic_phase3_vicreg.py — Variance diagnostic + pooling comparison script
- src/variance_diagnostic_results.csv — Per-epoch variance metrics
- src/pooling_comparison_results.csv — Pooling strategy comparison
- src/run_phase3_vicreg_fix.py — Full experiment runner with pooled VICReg
- src/pre_registration.md — Updated with corrected hypothesis
- phase_3/pooled_vicreg_results.csv — 30 experiment results (6 conditions × 5 seeds)
- phase_3/REPORT_vicreg_fix.md — Comprehensive analysis report
- phase_3/diagnostic_report.md — Diagnostic analysis

## Open Questions (ordered by expected value)
1. **Should Phase 4 use pooled VICReg + spatial_pooled readout as standard?**
   Yes — this resolves the known training collapse and readout bottleneck.
2. **Can other training objectives (SFA, Hebbian, contrastive) also benefit
   from pooled VICReg?** This should be tested in Phase 4.
3. **Is the object_permanence shortcut (69.2% untrained with pooled readout)
   still present with spatial_pooled readout?** Untrained spatial readout:
   72.4% for class_3 (object_permanence) — shortcut persists.
4. **Would longer training improve results?** JEPA loss converges by epoch 30,
   but pooled VICReg might benefit from more epochs.
5. **Can we close the gap to spatial-only (65.2%) and temporal-only (65.3%)?**
   Currently at 61.55% — 3.7pp below single-axis performance.
6. **Would P3-A with pooled VICReg exceed P3-C?** The sequential training
   protocol might interact differently with pooled VICReg.
