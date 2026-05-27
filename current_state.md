# Current Research State — HSUN Project

**Last updated:** Bootstrap (no experiments yet)

## Goal

Investigate an architecture for unsupervised representation learning built from
a **single, universal node type** that:

1. Maps 3 input slots (each a vector of dimension d) → 1 output vector of dimension d.
2. Stacks hierarchically via kernel-3 stride-1 1D convolution semantics (shared weights).
3. Applies identically along the time axis (spatial-temporal symmetry).
4. Is trained via a **local, label-free objective** so the same node works everywhere.

The architecture must produce similarity-preserving codes whose dimensions carry
**consistent semantics across positions and layers**.

## Known Constraints

- Python 3.10/3.11 only; no SaaS dependencies; no global ML library installs.
- Isolated virtual environments per phase; all runs local (CPU acceptable early).
- File naming: `snake_case` modules, `PascalCase` classes.
- Each component swappable behind a small explicit interface.
- Each phase produces a numerical comparison report committed to the repo.
- No 2D data, no end-to-end backprop across the full hierarchy, no motor/action loops.

## Gated Phase Plan (summary)

| Phase | Purpose | Key Question |
|-------|---------|-------------|
| 0 | Harness & smoke test | Can all five encoders run end-to-end? (Spearman ρ ≥ 0.6) |
| 1 | Spatial hierarchy | Does weight sharing + dim_out=dim_in cost >15% vs per-layer weights? |
| 2 | Temporal integration | Can P2-D (same node, temporal slots) work without retraining? |
| 3 | Unified spatiotemporal grid | Is P3-C (full universal) within 20% of P3-A (separate stages)? |
| 4 | Training objective comparison | Which local objective is best for the chosen architecture? |
| 5 | Vector semantics | Do code dimensions carry consistent semantics across positions/layers? |

**Phase gating rule:** Do not advance until success criteria are met, or a
rigorous justification for skipping is documented here.

## Confirmed Results

(none yet — no experiments run)

## Refuted Hypotheses

(none yet)

## Current Best Result

(no baseline established yet)

## In Progress

(nothing yet — awaiting Phase 0 launch)

## Open Questions (ordered by expected value)

1. **Universal-node expressivity:** Does forcing shared weights across all layers
   and positions, plus dim_out = dim_in, sacrifice too much expressivity?
   (Phase 1 will answer; success criterion: within 15% of per-layer upper bound.)
2. **Spatial-temporal symmetry:** Can the same kernel-3 node trained spatially
   be applied temporally without retraining? (Phase 2, P2-D test. This is the
   central value proposition of the architecture.)
3. **Training objective:** Which local, label-free objective (PC, JEPA, SFA,
   Hebbian, reconstruction) produces the best codes for a universal node?
   (Phase 4, but depends on architecture decision from Phase 3.)
4. **Semantic consistency:** Do code dimensions carry consistent meaning across
   positions and layers? Does this require explicit regularisation or does it
   emerge? (Phase 5, the final validation of the architecture's claim.)
5. **Minimum viable dimension d:** What is the smallest d that supports
   recursion (dim_out = dim_in) while remaining expressive for 16-bit inputs?
   (Explored across Phases 0–1; P1-D vs P1-E will inform this.)
6. **Spatiotemporal unification cost:** How much accuracy does the fully
   unified grid (P3-C) sacrifice versus a two-stage pipeline (P3-A)?
   (Phase 3, success criterion: within 20%.)
7. **Local training feasibility:** Can local objectives converge without
   global credit assignment? (Phases 0–2 provide early signal; Phase 4 is the
   systematic comparison.)

## Critical Design Decisions Deferred to Experiments

- Output dimension d (recursive vs wider) — Phase 1
- Cross-layer weight sharing — Phase 1
- Temporal mechanism (tick-rate vs recurrent vs output-loop vs temporal-slot) — Phase 2
- Unified vs separate spatial/temporal — Phase 3
- Training objective — Phase 4
- Semantic regularisation strategy — Phase 5
