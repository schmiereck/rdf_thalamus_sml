# Current Research State — HSUN Project

**Last updated:** After Phase 0 completion (iter_1, agents 1.1–1.9)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 0 (harness & smoke test) is now complete.

## Confirmed (with iter/sub-agent references)

1. **Harness works end-to-end** (iter_1, 1.1–1.2):
   - DatasetGenerator produces 8 base states + 80 noise variants
   - SimilarityEvaluator computes off-diagonal Spearman rho correctly
   - EncoderBase ABC defines train(), encode(), dim_out interface

2. **P0-A (Lookup Table) is a valid negative control** (iter_1, 1.6):
   - rho = NaN (one-hot vectors mutually orthogonal)
   - Confirms distributed representations are necessary

3. **P0-C (SOM) achieves best topology preservation** (iter_1, 1.6):
   - rho = 0.8811 ± 0.018 across 5 seeds
   - Uses inverse Euclidean distance to ALL SOM units as code
   - Zero sparsity (dense distributed code)
   - Fastest training (~0.24s)

4. **P0-E (Predictive Coding) outperforms global baseline** (iter_1, 1.6):
   - rho = 0.7221 ± 0.025 (ABOVE P0-D baseline 0.6173)
   - Local error-driven learning with lateral inhibition
   - Most stable across seeds (lowest std among all methods)

5. **P0-D (Sparse Autoencoder) is the global baseline** (iter_1, 1.4–1.6):
   - rho = 0.6173 ± 0.084 (tuned: lr=0.15, l1_lambda=0.002)
   - Had backprop bug (bias gradient np.mean→np.sum), fixed
   - Higher variance across seeds than SOM or Predictive Coding

6. **P0-B (Spatial Pooler) fails rho>=0.6 criterion** (iter_1, 1.6):
   - rho = 0.5807 ± 0.079 (mean fails, but some seeds pass)
   - Competitive prototype learning + inverse-distance codes + top-k
   - Replaced original HTM-style permanence updates (which gave rho≈0.16)
   - Within 0.037 of P0-D baseline (Criterion 3 PASS)

7. **All local methods within 0.15 of P0-D baseline** (iter_1, 1.6):
   - P0-B gap = +0.037 (below P0-D)
   - P0-C gap = -0.264 (above P0-D)
   - P0-E gap = -0.105 (above P0-D)

## Refuted Hypotheses
- Pre-registered Phase 0 hypothesis partially falsified: P0-B fails rho>=0.6
  on mean across seeds (0.5807). This is an honest negative result about
  competitive learning's stability at this trivial scale (3-bit inputs, 8 states).

## Current Best Result
- **P0-C (SOM):** rho = 0.8811 (highest topology preservation)
- **P0-E (Predictive Coding):** rho = 0.7221 (best local-only method)
- **P0-D (Sparse AE):** rho = 0.6173 (global baseline for Phase 1)

## In Progress
- Phase 1 (Spatial Hierarchy) — not yet started

## Open Questions (ordered by expected value)
1. **Universal-node expressivity:** Does forcing shared weights across all layers
   and positions, plus dim_out = dim_in, sacrifice too much expressivity?
   (Phase 1 will answer; success criterion: within 15% of per-layer upper bound.)
2. **SOM sparsity vs topology:** Can SOM's inverse-distance code be made sparse
   (e.g., k-WTA on distance vector) without losing its rho=0.88 advantage?
   This matters for the "sparse universal node" requirement.
3. **Predictive Coding stacking:** Can P0-E's local-error learning be applied
   hierarchically with shared weights? This is the most architecturally
   interesting candidate for the universal node.
4. **Spatial Pooler scalability:** Will P0-B's competitive learning stabilize
   with 16-bit inputs (Phase 1) or is it fundamentally less stable?
5. **Minimum viable d:** What dim_out supports recursion (dim_out = dim_in_per_slot)
   while remaining expressive for 16-bit inputs? Phase 1 P1-D vs P1-E will inform.
6. **Spatial-temporal symmetry:** Can the same kernel-3 node trained spatially
   be applied temporally without retraining? (Phase 2, central value proposition.)
7. **Local training feasibility:** P0-E already outperforms P0-D (rho 0.72 vs 0.62),
   suggesting local objectives can work. Phase 4 will test systematically.

## Critical Design Decisions Deferred to Experiments
- Which encoder to stack for Phase 1 (P0-D recommended as baseline; P0-C, P0-E as alternatives)
- Output dimension d (recursive vs wider) — Phase 1
- Cross-layer weight sharing — Phase 1
- Temporal mechanism — Phase 2
- Unified vs separate spatial/temporal — Phase 3
- Training objective — Phase 4
- Semantic regularisation strategy — Phase 5

## Files Created This Phase
- src/pre_registration.md — pre-registered hypothesis and falsification criteria
- src/harness.py — DatasetGenerator, SimilarityEvaluator, EncoderBase, utilities
- src/encoders/__init__.py — encoder registry
- src/encoders/lookup_table.py — P0-A (one-hot, negative control)
- src/encoders/spatial_pooler.py — P0-B (competitive learning SDR)
- src/encoders/som.py — P0-C (Kohonen SOM, inverse-distance codes)
- src/encoders/sparse_autoencoder.py — P0-D (global baseline, lr=0.15)
- src/encoders/predictive_coding.py — P0-E (local error learning)
- src/run_phase0.py — experiment runner (5 encoders × 5 seeds)
- phase_0/results.csv — raw experimental results (25 runs)
- phase_0/REPORT.md — comparison report with pass/fail evaluation
