# Current Research State — HSUN Project
**Last updated:** After Phase 2 completion (iter_004, sub-agents 4.1–4.3)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 2 (Temporal Integration) is now complete.

## Confirmed (with iter/sub-agent references)

1. **Zero-shot spatial→temporal weight transfer is FALSIFIED** (iter_004, 4.1):
   - F0: JEPA loss ratio (spatial/untrained) = 0.9903 → TRIGGERED (≥0.85)
   - F1: Classification gap (ZeroShot - Untrained) = -0.80pp → TRIGGERED (≤5pp above)
   - Spatially-trained weights are indistinguishable from random weights on temporal data
   - Paired t-test: p=0.728, Cohen's d=-0.17 (no significant difference)

2. **Temporal JEPA training WORKS** (iter_004, 4.1):
   - P2-D trained from scratch: 65.33% ± 2.74% test accuracy
   - Significantly above 60% threshold (p=0.012, Cohen's d=1.95)
   - F2 NOT TRIGGERED

3. **P2-D is COMPETITIVE with dedicated temporal mechanisms** (iter_004, 4.2):
   - P2-D: 65.33% vs P2-A: 67.07% vs P2-B: 62.87% vs P2-C: 61.53%
   - Gap vs best (P2-A): -1.73pp → F3 NOT TRIGGERED (≥20pp would falsify)
   - P2-D outperforms P2-B (RNN) and P2-C (feedback loop)

4. **P2-D achieves the lowest JEPA loss** among all trained encoders (iter_004, 4.2):
   - P2-D: 3.90 < P2-B: 5.81 < P2-C: 8.00 < P2-A: 9.91
   - Kernel-3 sliding window creates the most locally predictable codes

5. **The node TYPE is universal, but weights are axis-specific** (iter_004):
   - Same kernel-3, 3-slot architecture + same JEPA objective works on both spatial
     (Phase 1: 65.2%) and temporal (Phase 2: 65.3%) data
   - But spatially-optimized W_enc does not transfer to temporal inputs

6. **Periodicity loophole confirmed** (iter_004, 4.1):
   - Untrained encoders achieve ~58% on periodic-vs-random classification (chance=33.3%)
   - Deterministic propagation preserves periodicity regardless of weights
   - Research Manager's concern fully validated

7. **Classification-prediction tradeoff** (iter_004, 4.3):
   - Trained encoders have LOWER next-step cosine but HIGHER classification accuracy
   - JEPA training reorganizes representation space; raw predictiveness ≠ usefulness

## Refuted Hypotheses
- Phase 2 original hypothesis (zero-shot transfer ≥10pp advantage): FALSIFIED by F0+F1
- "One node type, one set of weights, applicable along any axis": REFUTED — weights
  are axis-specific, though the node type is universal

## Phase 1 Carry-Forward (still valid)
- JEPA local objective works spatially: 62.12% (d=8), 65.20% (d=16) (iter_003)
- Weight sharing has zero expressivity penalty (iter_002)
- Reconstruction objective was the root cause of Phase 1 failure (iter_002–003)

## Current Best Results
- **Spatial**: JEPA-d16, 65.20% ± 1.80%, 4,832 parameters (iter_003)
- **Temporal**: P2-D JEPA, 65.33% ± 2.74%, single UniversalNode (iter_004)
- **Best temporal alternative**: P2-A, 67.07% ± 0.98% (iter_004)

## Files Created This Phase
- src/temporal_dataset.py — Periodic/random/irregular sequence generator
- src/temporal_encoder.py — P2DEncoder, P2AEncoder, P2BEncoder, P2CEncoder
- src/run_phase2.py — P2-D experiment runner
- src/run_phase2_baselines.py — P2-A/B/C baseline runner
- src/test_temporal.py — Self-tests for temporal infrastructure
- phase_2/p2d_results.csv — P2-D raw results (15 runs)
- phase_2/baseline_results.csv — Baseline raw results (30 runs)
- phase_2/REPORT.md — Full Phase 2 report

## Open Questions (ordered by expected value)
1. **Does fine-tuning from spatial weights help?** Zero-shot fails, but fine-tuning
   might converge faster or achieve better final performance than random init.
2. **Can joint spatio-temporal training produce universal weights?** Training on both
   axes simultaneously might find a shared representation.
3. **Why does lowest JEPA loss not yield highest classification?** P2-D has the best
   JEPA loss (3.9) but P2-A has the best accuracy (67.1%). Is this an objective-
   task misalignment or a capacity issue?
4. **How does P2-D scale to longer/complex sequences?** The current T=64 with 8 states
   is modest. Longer sequences and more complex dynamics would test scalability.
5. **Can the periodicity loophole be controlled?** Use gain-over-untrained as primary
   metric, or design tasks where deterministic propagation doesn't trivially succeed.
6. **Can the unified spatio-temporal grid work with per-axis weights?** Phase 3 in
   goal.md envisions a 2D grid; per-axis fine-tuning may be the practical path.
