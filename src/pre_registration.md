# RDF Scientific Pre-Registration

*   **Iteration:** 005
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
A single UniversalNode weight set trained jointly on both spatial and temporal
JEPA objectives in a unified 2D grid (P3-C) achieves ≥80% of the accuracy of
the two-stage architecture with separate spatial and temporal weights (P3-A) on
four spatiotemporal benchmark tasks. Specifically, if P3-A achieves mean
accuracy A% across the four tasks, P3-C achieves A_C ≥ A - 20 percentage points.
The underlying mechanism is that joint training allows the shared weights to
discover a representation subspace where both spatial and temporal neighbor
prediction are simultaneously well-served, avoiding the axis-specific overfitting
that caused zero-shot transfer failure in Phase 2.

## 2. Falsification Criteria
The hypothesis is falsified if ANY of the following hold:

**F1 — Training gain insufficient:**
P3-C mean test accuracy - Untrained mean test accuracy < 8pp OR p >= 0.05
(via paired t-test across 5 seeds) OR Cohen's d < 1.0.
This means P3-C fails to outperform the Untrained baseline with statistical
significance (p < 0.05), strong effect size (Cohen's d ≥ 1.0), and absolute
mean accuracy gain over untrained of at least 8pp. If P3-C fails this test,
the unified weight hypothesis is falsified.

**F2 — Shared-weight expressivity penalty too large:**
P3-B mean test accuracy - P3-C mean test accuracy > 10pp.
The shared-weight constraint in P3-C costs more than 10 percentage points
relative to the anisotropic but jointly-trained P3-B baseline.

**F3 — Not viable vs sequential baseline:**
P3-C mean test accuracy < P3-A mean test accuracy - 20pp.
The unified representation is not competitive with the sequential
spatial-then-temporal baseline.

**F4 — Optimization failure:**
P3-C JEPA training loss > 2× P3-B final JEPA loss.
The shared weights fail to optimize due to conflicting axis objectives.

## 3. Proposed Method
Phase 3: Unified Spatiotemporal Grid experiment.

STEP 0 — Resume interrupted work:
- Check archive/iter_005/ for any completed artifacts from the interrupted
  iteration 005.7. If significant implementation progress exists, resume from
  there; otherwise start fresh.

STEP 1 — Implement spatiotemporal dataset (src/spatiotemporal_dataset.py):
- Four benchmark generators, each producing (T=32, S=16) binary matrices:
  a) Moving blob: blob of width 3-5 translating left/right/stationary/random-walk
     across S positions over T timesteps. 4-class classification.
  b) Expanding/contracting blob: blob centered at a position, size changes
     (expanding, contracting, steady, pulsating). 4-class classification.
  c) Periodic spatiotemporal: patterns with periods (2,3,4) in time and/or
     space, plus aperiodic random. 4-class classification.
  d) Object permanence: blob at fixed position, disappears for k∈{0,2,4,8}
     timesteps mid-sequence, then reappears. 4-class classification.
- Training set: 2000 samples per task (balanced classes)
- Test set: 500 samples per task (balanced classes, held-out seeds)

STEP 2 — Implement grid architectures (src/spatiotemporal_grid.py):
- UniversalGrid base class with configurable axis-weight sharing
- P3-A (SeparateStagesEncoder):
  * Spatial encoder: 3 spatial-only UniversalNode layers applied at each
    time step independently (S=16→14→12→10, d=16)
  * Temporal encoder: 3 temporal-only UniversalNode layers applied at each
    spatial position independently on spatial codes (T=32→30→28→26)
  * Spatial weights trained first, frozen; then temporal weights trained
  * Total: 2 weight sets (W_spatial, W_temporal)
- P3-B (AnisotropicGridEncoder):
  * 3 alternating spatial+temporal pass pairs (6 passes total)
  * Spatial passes use W_spatial, temporal passes use W_temporal
  * Both trained jointly with combined JEPA loss
  * Total: 2 weight sets (W_spatial, W_temporal)
- P3-C (UnifiedGridEncoder):
  * Same architecture as P3-B but W_spatial = W_temporal = W_shared
  * Single weight set trained with combined spatial+temporal JEPA loss
  * Total: 1 weight set (W_shared)
- Use d=16 throughout (best from Phase 1)
- Use existing UniversalNode class from Phase 1/2

STEP 3 — Implement JEPA training for 2D grid (src/train_grid.py):
- For each spatial pass node output z(s,t): bidirectional JEPA loss
  predicting z(s-1,t) and z(s+1,t) from z(s,t)
- For each temporal pass node output z(s,t): bidirectional JEPA loss
  predicting z(s,t-1) and z(s,t+1) from z(s,t)
- VICReg variance + covariance regularization at each layer
- Total loss = λ_s · L_spatial_JEPA + λ_t · L_temporal_JEPA + λ_v · L_VICReg
- For P3-C: both spatial and temporal losses contribute gradients to W_shared
- For P3-A: sequential training (spatial first, then temporal)
- Training: Adam, lr=1e-3, 200 epochs, batch_size=64

STEP 4 — Implement evaluation (src/eval_grid.py):
- Extract top-layer codes: (T', S', d) → mean-pool → d-dimensional code
- Linear probe: logistic regression on codes for each of 4 tasks
- Also evaluate untrained baseline (random-init weights, no training)
- Report: per-task accuracy, aggregate accuracy, parameter counts,
  JEPA loss curves, gain-over-untrained

STEP 5 — Run experiments (src/run_phase3.py):
- 3 architectures (P3-A, P3-B, P3-C) × 5 seeds = 15 training runs
- + 1 untrained baseline × 5 seeds = 5 runs
- Total: 20 runs
- For each run: train JEPA → extract codes → 4 linear probes
- Save raw results to phase_3/results.csv

STEP 6 — Statistical analysis and report (phase_3/REPORT.md):
- Mean ± std accuracy per architecture per task
- Paired t-test: P3-C vs P3-A (primary falsification test)
- Gain-over-untrained for each architecture (periodicity-loophole control)
- Parameter count comparison (P3-C should be ~50% of P3-A/B)
- JEPA loss comparison (convergence, final values)
- Clear pass/fail verdict for each falsification criterion

Files to create/modify:
- src/spatiotemporal_dataset.py (NEW)
- src/spatiotemporal_grid.py (NEW — P3-A, P3-B, P3-C architectures)
- src/train_grid.py (NEW — JEPA training for 2D grid)
- src/eval_grid.py (NEW — linear probe evaluation)
- src/run_phase3.py (NEW — experiment runner)
- src/test_phase3.py (NEW — self-tests for grid architecture and dataset)
- phase_3/REPORT.md (OUTPUT — comparison report)
- phase_3/results.csv (OUTPUT — raw results)

---
*Created automatically by the RDF Orchestrator prior to iteration execution.*
*Updated with revised F2 criterion per Research Manager directive.*
