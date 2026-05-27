
# Phase 3: Unified Spatiotemporal Grid — Infrastructure + Experiments

You are executing Phase 3 of the HSUN (Hierarchical Sparse Universal Nodes) research project. Your task is to build the full spatiotemporal infrastructure and run all experiments.

## CRITICAL: Read the Pre-Registration File First

Before writing ANY code, read `src/pre_registration.md` and follow its methodology exactly. The falsification criteria are:
- Primary: P3-C mean 4-class accuracy < P3-B mean accuracy - 15pp
- Secondary: P3-C mean accuracy < P3-A mean accuracy - 20pp
- Tertiary: P3-C mean accuracy < 50% (2× chance)

## Research Manager's Strategic Requirements

1. **Dimension Constraint**: Every node in the spatiotemporal grid must have the same input shape (3×d → d). The raw binary pixels (dim=1) cannot be fed directly to UniversalNodes. You MUST implement a non-learned (or separately trained) **pixel embedding layer** that projects raw binary inputs into d-dimensional space BEFORE they enter spatial Layer 0.

2. **Guard Against Shortcut Features**: The four spatiotemporal classes must require BOTH spatial and temporal information to classify. Verify this by running "shortcut baselines":
   - Single-frame baseline: classify using only one frame (e.g., first frame)  
   - Temporal-average baseline: classify using only the mean across time
   These should achieve ≤50% accuracy (near chance for 4-class), confirming the dataset requires genuine spatiotemporal processing.

3. **Representation Pooling**: For the linear probe, clearly define how the final representation is aggregated. Suggest: average-pool across remaining spatial positions to get (T_out, d), then average-pool across time to get a single (d,) vector. Do NOT flatten the raw grid.

## Existing Codebase (DO NOT recreate, reuse these)

- `src/node.py` — UniversalNode class (3×d input → d_out output, with forward, compute_gradients, apply_gradients)
- `src/hierarchical_encoder.py` — HierarchicalEncoder (spatial, uses UniversalNode with kernel-3 stride-1)
- `src/temporal_encoder.py` — P2DEncoder (temporal sliding window, uses UniversalNode)
- `src/training_objectives.py` — JEPALoss class with VICReg (per-layer linear predictors, spatial bidirectional neighbor prediction). Has forward(), backward(), step(), loss_and_grads()
- `src/harness.py` — SimpleLogisticRegression, utility functions
- `src/temporal_dataset.py` — Temporal dataset generator (for reference)
- `src/dataset_phase1.py` — Phase 1 spatial dataset (for reference)

## Architecture Design

The spatiotemporal encoder processes (B, 16, 32) binary grids (16 spatial positions × 32 timesteps):

**Spatial pass**: 3 layers of kernel-3, stride-1 UniversalNodes over 16 input positions
- Layer 0: 14 positions, Layer 1: 12, Layer 2: 10 → top spatial code at each timestep
- Applied independently at EACH timestep (same spatial weights across timesteps)

**Temporal pass**: 3 layers of kernel-3, stride-1 UniversalNodes over 32 timesteps
- Applied to the 10 top-layer spatial codes at each spatial position
- Layer 0: 30 positions, Layer 1: 28, Layer 2: 26 → final temporal code

**Final representation**: Average-pool across spatial positions and timesteps → single d-dimensional vector

**Three variants (same architecture, different weight sharing)**:
- **P3-A (Separate training)**: W_spatial trained alone (200 epochs), then W_temporal trained alone (200 epochs). Separate parameter sets.
- **P3-B (Joint, anisotropic)**: W_spatial and W_temporal trained jointly with combined JEPA loss (200 epochs). Two separate weight matrices.
- **P3-C (Joint, shared)**: Single W_shared for BOTH spatial and temporal passes, trained jointly (200 epochs). The strong universal hypothesis.

All use d=16, d_out=16 (bottleneck), JEPA + VICReg objective.

## Spatiotemporal Dataset (4 classes)

Generate spatiotemporal patterns over a 16×32 binary grid:

**Class 0 — Moving blob**: Contiguous block of 1s that translates across spatial positions over time
- Vary: speed (1-3 positions/step), starting position (0-13), blob width (1-4)

**Class 1 — Expanding/contracting blob**: Blob whose spatial extent grows then shrinks over time  
- Vary: max width (4-10), expansion rate (1-2 positions/step), center position

**Class 2 — Periodic spatiotemporal**: Pattern repeating in both space and time
- Vary: spatial period (2-5), temporal period (3-7), phase

**Class 3 — Object permanence**: Blob present, disappears for k steps, reappears at same position
- Vary: gap length (3-10), blob position, blob width (1-3)

Each class: 500 training, 200 test samples. Add 10-15% noise (random pixel flips).

**IMPORTANT**: Verify shortcut baselines as described above.

## JEPA Training for Spatiotemporal Data

The JEPA objective must work on BOTH axes:

**Spatial JEPA**: At each spatial layer, for each timestep independently:
- Predict left neighbor code from current code, and right neighbor from current code
- Bidirectional prediction using per-layer linear predictors

**Temporal JEPA**: At each temporal layer, for each spatial position independently:
- Predict past neighbor code from current code, and future neighbor from current code
- Bidirectional prediction using per-layer linear predictors

**VICReg**: Apply variance + covariance penalties on ALL node outputs (both spatial and temporal layers)

**Combined loss**: alpha * spatial_jepa + (1-alpha) * temporal_jepa + vicreg
- Use alpha = 0.5 (equal weighting)
- For P3-A: first train alpha=1.0 (spatial only), then alpha=0.0 (temporal only)
- For P3-B and P3-C: train alpha=0.5 jointly

**Training details**: 200 epochs, Adam lr=1e-3, batch_size=32, 5 seeds [42,43,44,45,46]

## Evaluation Protocol

1. Linear probe: Train a single linear classifier (SimpleLogisticRegression from harness.py) on the final d-dimensional code vectors
2. 4-class classification accuracy on test set
3. Per-benchmark accuracy (accuracy on each of the 4 classes separately)
4. Compute: mean accuracy ± std across 5 seeds
5. Parameter count for each variant
6. Per-axis JEPA loss (spatial and temporal) at the end of training
7. Shortcut baselines (single-frame, temporal-average)

## Files to Create

1. `src/spatiotemporal_dataset.py` — Dataset generator with 4 spatiotemporal pattern classes + shortcut baseline evaluation
2. `src/spatiotemporal_encoder.py` — Spatiotemporal encoder with P3-A, P3-B, P3-C variants
3. `src/run_phase3.py` — Main experiment runner (3 variants × 5 seeds + baselines)
4. `src/test_spatiotemporal.py` — Self-tests for the new infrastructure
5. Save all raw results to `phase_3/` directory as CSV files

## Implementation Notes

- Use ONLY numpy — no ML libraries
- Follow the pattern from existing code (e.g., how run_phase1_v2.py and run_phase2.py work)
- The UniversalNode from node.py should be reused directly (not modified)
- For the spatial pass, you can adapt the logic from HierarchicalEncoder but for a single timestep
- For the temporal pass, you can adapt P2DEncoder logic but for a single spatial position
- The pixel embedding should be a simple (2, d) lookup table (one row for pixel=0, one for pixel=1), initialized with Xavier scaling — NOT learned during JEPA training (to keep it non-learned as the Research Manager mandates)
- For P3-C (shared weights), the SAME UniversalNode object is used for both spatial and temporal passes — gradient contributions from both axes are summed before the Adam update
- Run untrained baselines too (random init, no training) for reference
- Save per-seed results so statistical analysis can be done later

## Expected Runtime

Each training run (200 epochs, batch_size=32, ~2000 samples) should take ~2-5 minutes on CPU.
15 training runs + baselines = ~30-60 minutes total.

## Output

Save results to:
- `phase_3/p3a_results.csv` — P3-A results per seed
- `phase_3/p3b_results.csv` — P3-B results per seed  
- `phase_3/p3c_results.csv` — P3-C results per seed
- `phase_3/untrained_results.csv` — Untrained baseline per seed
- `phase_3/shortcut_results.csv` — Shortcut baseline results
- `phase_3/param_comparison.csv` — Parameter count comparison
