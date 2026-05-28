
# Phase 4: Training Objective Comparison — Implementation &amp; Full Experiment

## Context
Phase 3 is RESOLVED. P3-C with pooled VICReg + spatial_pooled_then_flat readout achieves 61.55% test accuracy (iter_006). We now compare training objectives on this benchmark.

The Research Manager issued three critical directives:
1. **Reconstruction natively resists collapse** — must test WITHOUT pooled VICReg too
2. **SFA + VICReg is the standard gradient-based SFA** — document it as Lagrangian relaxation
3. **Hebbian learning must be mathematically defined** — if using gradient loss, clarify why it's distinct from VICReg's variance term

## Your Task

### Step 1: Update Pre-Registration

Update `src/pre_registration.md` with:
- Precise mathematical formulations for ALL 4 objectives (see below)
- Refined falsification criteria (F1-F3 from approved plan + Manager refinements)
- Note that F3 is expected to trigger for Reconstruction per Manager's directive

### Step 2: Create `src/run_phase4.py`

Implement 4 objective families × 2 VICReg conditions = 8 trained conditions + untrained baseline.

**Objective Formulations:**

1. **JEPA** (existing, from `src/run_phase3_vicreg_fix.py`):
   - L = α * Σ_l L_spatial_JEPA(l) + (1-α) * Σ_l L_temporal_JEPA(l)
   - Uses existing JEPALoss class with per-layer linear predictors
   - Code gradients: spatial_code_grads + temporal_code_grads from JEPALoss.backward()

2. **SFA (Slow Feature Analysis)**:
   - Slowness loss on FINAL temporal output: z = temporal_outputs[-1], shape (B, T_final, S_final, d_out)
   - L_slow = (1/(B*(T-1)*S*d)) * Σ_{b,s,t≥1} ||z[b,t,s,:] - z[b,t-1,s,:]||²
   - WITHOUT pooled VICReg: pure slowness → will collapse to constant (trivial solution)
   - WITH pooled VICReg: standard gradient-based SFA formulation
     (slowness + variance constraint + covariance decorrelation via Lagrangian relaxation)
   - Code gradient: dL/dz[b,t,s,:] = 2*(z[b,t,s,:]-z[b,t-1,s,:])/(B*(T-1)*S*d) for t≥1
                     dL/dz[b,t-1,s,:] -= 2*(z[b,t,s,:]-z[b,t-1,s,:])/(B*(T-1)*S*d)
   - Only temporal_code_grads[-1] is non-zero; all spatial_code_grads are zeros
   - NOTE: SFA without any variance constraint collapses trivially. This is the expected
     negative result that validates the SFA formulation.

3. **Hebbian (Variance Maximization on Intermediate Codes)**:
   - L_Hebb = -(λ_hebb/d) * Σ_{layers} Σ_j Var(code_j)  [maximize output variance]
   - Applied to ALL intermediate codes (spatial layers 0-2 + temporal layers 0-2)
   - For each layer output Z of shape (B, P1, P2, d_out):
     - Flatten to (M, d_out) where M = B*P1*P2
     - mean = Z.mean(axis=0, keepdims=True)
     - std = sqrt(Var(Z, axis=0) + eps)
     - dL/dZ = (2*λ_hebb/(M*d)) * (Z - mean) / (std + eps)
   - WITHOUT pooled VICReg: variance maximization only (no decorrelation → codes may align)
   - WITH pooled VICReg: variance maximization on intermediates + decorrelation on pooled
   - IMPORTANT: This is the gradient-based formulation of Hebbian learning.
     It is mathematically equivalent to maximizing output variance, which is what
     Oja's rule converges to. It is DISTINCT from pooled VICReg because:
     (a) it operates on ALL intermediate codes, not just the pooled representation
     (b) it MAXIMIZES variance (opposite sign from VICReg which prevents collapse)
     (c) without decorrelation, it can produce aligned (redundant) codes

4. **Reconstruction (Sparse Autoencoder)**:
   - Local reconstruction at each node using W_dec/b_dec from UniversalNode
   - For each spatial layer l:
     - code = spatial_outputs[l]  shape (B, S_l, T, d_out)
     - node_input = spatial_inputs[l]  shape (B, S_l, T, 3, d) → flatten to (B*S_l*T, 3*d)
     - code_flat = code.reshape(B*S_l*T, d_out)
     - recon_flat = code_flat @ W_dec_spatial + b_dec_spatial  shape (B*S_l*T, 3*d)
     - L_recon_l = MSE(input_flat, recon_flat) + λ_l1 * mean(|code_flat|)
   - Same for each temporal layer (using temporal W_dec/b_dec, which in P3-C = spatial)
   - Total: L_recon = Σ_l L_recon_spatial(l) + Σ_l L_recon_temporal(l)
   - Code gradient: dL/dcode = dL/dr @ W_dec.T  where dL/dr = 2/(B*D_in) * (recon - input)
   - Also need to update W_dec/b_dec with separate Adam optimizer
   - λ_l1 = 0.01 for sparsity
   - WITHOUT pooled VICReg: pure sparse reconstruction (natively resists collapse — Manager's key point)
   - WITH pooled VICReg: reconstruction + pooled VICReg (may or may not help)

**Training Loop Pattern (same for all objectives):**
1. Forward pass → get fwd = encoder.forward_with_intermediates(batch)
2. Compute objective-specific loss and code gradients (spatial_code_grads, temporal_code_grads)
3. If use_pooled_vicreg: compute pooled VICReg gradient, inject into temporal_code_grads[-1]
   (same mechanism as run_phase3_vicreg_fix.py: expand to (B,T_final,S_final,d_out) and add)
4. Backward pass → grads = encoder.backward(fwd, spatial_code_grads, temporal_code_grads, alpha)
5. Adam update on encoder parameters (for P3-C: combined spatial+temporal grads)
6. For Reconstruction: also update W_dec/b_dec via separate Adam

**Experiment Configuration:**
- Architecture: P3-C, d=16, d_out=16, n_spatial_layers=3, n_temporal_layers=3, l1_lambda=0.0
- Training: 30 epochs, batch_size=64, lr=1e-3, alpha=0.5
- Seeds: [42, 43, 44, 45, 46]
- Train: 200 per class, Test: 100 per class, noise_flip=0.10
- Readout: spatial_pooled_then_flat for ALL conditions (416 features)
- Classification: SimpleLogisticRegression(n_classes=4, lr=0.1, max_iter=2000)

**Conditions to Run:**
| ID | Objective | Pooled VICReg | Description |
|----|-----------|---------------|-------------|
| 1  | JEPA      | Yes           | Reference (should reproduce ~61.55%) |
| 2  | JEPA      | No            | JEPA-only control |
| 3  | SFA       | Yes           | Standard gradient SFA |
| 4  | SFA       | No            | Slowness only (expected to collapse) |
| 5  | Hebbian   | Yes           | Variance max + decorrelation |
| 6  | Hebbian   | No            | Variance max only |
| 7  | Recon     | Yes           | Sparse AE + pooled VICReg |
| 8  | Recon     | No            | Pure sparse AE (natively resists collapse) |
| 9  | Untrained | No            | Random init baseline |

= 8 trained × 5 seeds + 5 untrained = 45 runs total

**Results CSV (phase_4/phase4_results.csv):**
Columns: objective, seed, use_pooled_vicreg, train_acc, test_acc,
         class_0_acc, class_1_acc, class_2_acc, class_3_acc,
         final_loss, pooled_std, training_time_sec

**Falsification Criteria (from approved plan + Manager refinements):**
- F1: JEPA + pooled VICReg &lt; 55% → implementation broken
- F2: Any other objective (with OR without VICReg) exceeds JEPA + pooled VICReg by ≥ 3pp → JEPA not best
- F3: For any objective X, accuracy(X without VICReg) ≥ accuracy(X with VICReg) → pooled VICReg doesn't help X
  (Expected to trigger for Reconstruction per Manager's directive)

### Step 3: Dry Run

Run `python src/run_phase4.py --dry-run` to verify:
- All 9 conditions produce valid outputs (no NaN, no crash)
- Shapes are correct
- Classification accuracy is computed
- Results CSV is written

### Step 4: Run Full Experiment

Run `python src/run_phase4.py` with multiprocessing (5 workers).
This should take ~10-20 minutes with parallel execution.

### Step 5: Generate Report

After all runs complete, generate `phase_4/REPORT.md` containing:
- Experiment configuration
- Mathematical formulations for all 4 objectives (precise equations)
- Comparison table: all 9 conditions, mean ± std test accuracy
- VICReg ablation analysis: for each objective, with vs without pooled VICReg
- Statistical tests: paired t-tests vs untrained, effect sizes
- Falsification criteria evaluation (F1, F2, F3)
- Per-class accuracy analysis
- Training stability observations
- Compute cost comparison
- Manager's directives addressed:
  1. Reconstruction without VICReg result
  2. SFA + VICReg as standard gradient SFA
  3. Hebbian mathematical definition
- Formal recommendation for default objective

## Key Code Files to Reference
- `src/run_phase3_vicreg_fix.py`: Pooled VICReg injection, classification evaluation, experiment structure
- `src/training_objectives.py`: JEPALoss class (reuse for JEPA objective)
- `src/spatiotemporal_encoder.py`: SpatiotemporalEncoder.forward_with_intermediates, .backward
- `src/spatiotemporal_dataset.py`: generate_spatiotemporal_dataset
- `src/node.py`: UniversalNode with W_enc, b_enc, W_dec, b_dec
- `src/harness.py`: SimpleLogisticRegression

## Important Implementation Notes
1. For Reconstruction, W_dec/b_dec are NOT trained by encoder.backward() (gradients are zeros).
   You MUST add a separate mechanism to train them.
2. For SFA, code gradients go ONLY into temporal_code_grads[-1]. All spatial gradients are zeros.
3. For Hebbian, λ_hebb should be chosen so variance gradients are comparable in magnitude to
   JEPA gradients. Start with λ_hebb = 25.0 (same as VICReg lambda).
4. The encoder backward pass expects gradients w.r.t. post-tanh code outputs.
5. Pooled VICReg injection: same mechanism as run_phase3_vicreg_fix.py
   (expand (B, d_out) → (B, T_final, S_final, d_out), divide by T_final*S_final, add to temporal_code_grads[-1])
6. For P3-C, master_spatial and master_temporal are the SAME object.
   Use a single Adam optimizer with combined gradients.
7. Create `phase_4/` directory before writing results.
8. Use multiprocessing.Pool for parallel execution across seeds.
