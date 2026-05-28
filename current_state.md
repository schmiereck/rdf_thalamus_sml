# Current Research State — HSUN Project
**Last updated:** After Phase 3 completion (iter_005, sub-agents 5.1–5.6)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 3 (Unified Spatiotemporal Grid) is now complete.

## Confirmed (with iter/sub-agent references)

1. **P3-C (shared weights) fails to outperform Untrained** (iter_005, 5.6):
   - Gain: 1.15pp (required ≥8pp)
   - p=0.648 (required <0.05)
   - Cohen's d=0.22 (required ≥1.0)
   - **F1 TRIGGERED — universal parameter hypothesis falsified on training gain**

2. **Weight sharing imposes zero expressivity penalty** (iter_005, 5.6):
   - P3-B (separate weights): 44.0% vs P3-C (shared weights): 44.0%
   - Penalty = 0.0pp → F2 NOT triggered
   - Consistent with Phase 1 finding (iter_002-003)

3. **P3-C is within 0.5pp of P3-A** (iter_005, 5.6):
   - P3-A: 44.5% vs P3-C: 44.0% → gap 0.5pp → F3 NOT triggered

4. **JEPA optimization succeeds for all variants** (iter_005, 5.6):
   - P3-C combined loss: ~24.2, P3-B: ~21.9 (ratio 1.11×) → F4 NOT triggered
   - Training reduces temporal loss from ~19.3 to ~8.5 (P3-C)
   - Training reduces spatial loss from ~20.5 to ~15.7 (P3-C)

5. **ALL variants barely exceed Untrained baseline** (iter_005, 5.6):
   - P3-A: 44.5% (+1.65pp vs Untrained 42.85%)
   - P3-B: 44.0% (+1.15pp)
   - P3-C: 44.0% (+1.15pp)
   - This is NOT specific to P3-C — it affects ALL trained variants

6. **Object permanence task has shortcut** (iter_005, 5.6):
   - Untrained accuracy: 69.2% (>60% threshold)
   - FLAGGED: deterministic propagation trivially captures blob presence
   - periodic_st: only 10.6% untrained (genuinely hard)
   - moving_blob: 49.2% untrained, expanding_blob: 42.4% untrained

7. **Classification-prediction tradeoff confirmed spatiotemporal** (iter_005):
   - JEPA training reduces prediction loss substantially (temporal: 19.3→8.5)
   - But classification accuracy barely improves
   - Echoes Phase 2 finding (iter_004, 4.3)

## Refuted Hypotheses
- Phase 3 universal parameter hypothesis: FALSIFIED on F1 (training gain insufficient)
- "JEPA training produces useful spatiotemporal representations": REFUTED — gain is
  marginal across ALL variants, not just P3-C

## Phase 1-2 Carry-Forward (still valid)
- JEPA local objective works spatially: 62.12% (d=8), 65.20% (d=16) (iter_003)
- P2-D temporal JEPA: 65.33% ± 2.74% (iter_004)
- Weight sharing has zero expressivity penalty (iter_002)
- Zero-shot spatial→temporal transfer is falsified (iter_004)
- Node type is universal, weights are axis-specific (iter_004)

## Current Best Results
- **Spatial only**: JEPA-d16, 65.20% ± 1.80%, 4,832 params (iter_003)
- **Temporal only**: P2-D JEPA, 65.33% ± 2.74% (iter_004)
- **Spatiotemporal**: All variants ~44%, barely above untrained ~42.85% (iter_005)

## Experiment Configuration
- Epochs: 30, train/class: 200, test/class: 100, batch=64, lr=1e-3
- Reduced from original 200 epochs / 500 train/class due to compute constraints

## Files Created This Phase
- src/spatiotemporal_dataset.py — 4-class spatiotemporal dataset generator
- src/spatiotemporal_encoder.py — P3-A, P3-B, P3-C architectures
- src/run_phase3.py — Full experiment runner
- src/run_phase3_optimized.py — Optimized runner (30 epochs, 200/class)
- src/pre_registration.md — Updated with revised F1-F4 criteria
- phase_3/phase3_full_results.csv — 20 experiment results
- phase_3/shortcut_baselines.csv — 30 shortcut baseline results
- phase_3/REPORT.md — Phase 3 analysis report
- phase_3/experiment_config.txt — Configuration documentation

## Open Questions (ordered by expected value)
1. **Why does JEPA prediction improvement NOT transfer to classification?**
   Confirmed across Phase 2 and Phase 3. The objective produces locally
   predictable codes but these don't carry discriminative signal for the
   downstream task. This is the central bottleneck.
2. **Can a different training objective fix this?** Phase 4 (training objective
   comparison) is the direct next step. SFA, Hebbian, contrastive, and
   reconstruction objectives should be tested on the SAME architecture.
3. **Is the object_permanence shortcut solvable?** Need to redesign the task
   so that blob presence is not trivially correlated with permanence.
4. **Would longer training or larger d improve results?** The current 30-epoch
   runs may be undertrained. But JEPA loss converges by epoch 30, suggesting
   the problem is in the objective, not training duration.
5. **Can gain-over-untrained be the primary metric?** Yes, this should be
   adopted as the standard metric to control for architectural shortcuts.
6. **Does the spatiotemporal grid need a different pooling strategy?** Mean-pool
   across (10, 26) positions may lose critical temporal structure.
