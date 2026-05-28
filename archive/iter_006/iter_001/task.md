## Task: Phase 3 VICReg Diagnostic — Verify Collapse Status and Pooling Impact

You are running a diagnostic experiment for the HSUN project. The critical context is:

**Background**: Phase 3 (iter_005) showed that ALL spatiotemporal variants (P3-A, P3-B, P3-C) barely exceed the untrained baseline (~42.85%) on 4-class classification, with only ~1.15pp gain. The pre-registration hypothesized that VICReg was omitted, but code review reveals that VICReg IS already present in `JEPALoss` (λ_var=25, λ_cov=25) in `src/training_objectives.py`. So the hypothesis about "omission" is factually incorrect.

**Your task**: Run a comprehensive diagnostic to determine WHY representations don't carry discriminative signal despite VICReg being present.

### Step 1: Update pre-registration

Read `src/pre_registration.md` and update it with a CORRECTED hypothesis. The new hypothesis should be:

"Phase 3's failure is NOT caused by VICReg omission (VICReg is present with λ_var=25, λ_cov=25). The likely cause is either (a) representation pooling destroys discriminative position-specific information (Phase 3 uses mean-pooled (B,16) representation while Phase 1 used flattened (B,80+)), or (b) VICReg applied per-layer to intermediate codes doesn't prevent collapse of the final pooled representation. The diagnostic will determine which mechanism is at fault."

### Step 2: Write and run diagnostic script

Create `src/diagnostic_phase3_vicreg.py` that:

1. Creates P3-C encoder with seed=42, d=16, d_out=16
2. Generates spatiotemporal dataset (200 train/class, 100 test/class, seed=42)
3. Trains for 30 epochs using the existing training infrastructure (import from run_phase3.py and run_phase3_optimized.py)
4. After each epoch (and before training at epoch 0), measures and logs:
   a. **Per-dimension std** of the pooled representation on the TEST set
   b. **Per-dimension std** of each spatial layer's output (reshaped to 2D before computing)
   c. **Per-dimension std** of each temporal layer's output
   d. **VICReg var_loss** and **cov_loss** from the JEPA step (these are already returned by JEPALoss)
   e. **Prediction loss** from JEPA
   f. **Classification accuracy** (train + test) using pooled representation
5. After training, also creates an untrained P3-C encoder (same seed) and measures:
   a. Per-dim std of pooled representation
   b. Per-dim std of each layer's output
6. **Pooling comparison**: After training, try classification with alternative representations:
   a. **Pooled** (current): mean over all positions → (B, 16)
   b. **Spatial-temporal flatten (final temporal layer)**: reshape (B, T_final, S_final, d) → (B, T_final*S_final*d) — but this may be too large. If > 2000 features, use PCA to reduce to 100 features first, then classify.
   c. **Per-timestep pooled**: mean over spatial only → (B, T_final, d) → flatten → (B, T_final*d) = (B, 416) 
   d. **Per-position pooled**: mean over temporal only → (B, S_final, d) → flatten → (B, S_final*d) = (B, 160)
   For each representation, fit a SimpleLogisticRegression (from harness.py) and report test accuracy.
7. Save all results to `src/variance_diagnostic_results.csv` (epoch-level data) and `src/pooling_comparison_results.csv` (representation comparison)

### Step 3: Analysis and Report

After running the diagnostic, write a clear analysis to `phase_3/diagnostic_report.md` answering:
1. **Is VICReg active?** Report var_loss and cov_loss values during training. Are they decreasing? Are per-dim stds ≥ 1.0 at intermediate layers?
2. **Is the pooled representation collapsed?** Compare trained vs untrained per-dim std at the pooled level.
3. **Does pooling destroy discriminative information?** Compare classification accuracy across the 4 representation strategies.
4. **What is the most likely cause of failure?** Based on the evidence.

### Important implementation details:
- Import from `src/spatiotemporal_dataset.py`, `src/spatiotemporal_encoder.py`, `src/training_objectives.py`, `src/run_phase3.py`, `src/harness.py`
- Use the SAME training protocol as iter_005: 30 epochs, 200 train/class, 100 test/class, batch=64, lr=1e-3
- For the per-epoch variance measurement, you need to run the encoder forward on the test set and compute std per dimension. Do this efficiently (don't re-run the full training loop).
- Run the script with `python src/diagnostic_phase3_vicreg.py` and capture output
- The whole diagnostic should take ~10-15 minutes for one seed

### Success criteria:
- All diagnostic metrics computed and saved
- Clear determination of whether collapse is happening at the pooled representation level
- Clear comparison of pooling strategies
- Updated pre-registration with corrected hypothesis