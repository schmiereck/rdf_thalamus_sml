## Task: Implement Alternative Training Objectives for HSUN Phase 1

### Context
The HSUN project has a hierarchical encoder with UniversalNodes (kernel-3, stride-1) over 16 binary inputs. Phase 1 found that reconstruction training DEGRADES representations below the untrained baseline (48.4%). We need to test alternative local objectives to see if any can beat the untrained baseline.

### CRITICAL: Read Pre-Registration First
Before writing any code, read `src/pre_registration.md` for the hypothesis and falsification criteria. All implementations must adhere to these criteria.

### What to Implement

#### 1. Create `src/training_objectives.py` with four loss classes:

**JEPALoss**: Bidirectional neighbor prediction at each layer
- At each layer l, for each position p: predict code_{p+1} from code_p and predict code_p from code_{p+1} (bidirectional)
- Predictor: linear layer (d→d) per layer, NOT shared across layers
- VICReg collapse prevention with standard defaults: λ_var=25, μ_cov=25, ν_inv=1
  - Variance term: max(0, γ - std(code)) for each dimension (γ=1.0 target std)
  - Covariance term: sum of off-diagonal elements of covariance matrix of codes
  - Invariance term: MSE between predicted and target codes
- Total JEPA loss = ν_inv * prediction_loss + λ_var * variance_penalty + μ_cov * covariance_penalty
- Must return: loss value, gradient of loss w.r.t. codes at each layer (needed for backprop)

**ContrastiveLoss**: InfoNCE with bit-flip augmentation
- For each sample x (16 binary pixels), create augmented version by flipping 1-2 random bits
- Encode both original and augmented through the encoder
- Projection head: MLP(80→40→20) for d=8 (top layer has 10 positions × 8 = 80 features), L2 normalize
- InfoNCE loss with temperature τ=0.5
- Operates only on the FINAL (top) layer codes, not per-layer

**SFALoss**: Slow Feature Analysis at each layer
- At each layer, minimize ||code_{p+1} - code_p||² (adjacent positions should have similar codes)
- Variance constraint: std of codes across positions should be ≥ 1.0 (penalize if below)
- Total SFA loss = slowness_loss + λ_var * max(0, 1 - std(codes))

**HebbianLoss**: Oja-style local learning
- NOT gradient-based — use Oja's rule directly for online updates
- ΔW_enc += η * (y * x^T - y * y^T * W_enc)  where y = tanh(W_enc @ x + b_enc)
- Decorrelation penalty: subtract mean(y) from y before applying Oja's rule
- Apply per-position per-layer, then average (similar to shared-weight training)
- The "loss" is a monitoring quantity: negative correlation between y and x means things are going wrong

#### 2. Modify `src/hierarchical_encoder.py`:

Add a `forward_with_intermediates()` method that returns:
- codes at each layer: list of (batch, n_positions, d) arrays
- the node inputs at each layer: list of (batch, n_positions, 3, d) arrays
- the final flattened code

Add a `backward_from_code_grads()` method that takes:
- dL/d_code at each layer (from the training objective)
- The stored forward pass intermediates
And computes:
- Gradient of the loss w.r.t. W_enc, b_enc at each layer
- Gradient of the loss w.r.t. the embedding

This requires implementing the chain rule through the tanh activation:
Given dL/da (gradient w.r.t. code = tanh(z)):
  dL/dz = dL/da * (1 - tanh(z)²)
  dL/dW_enc = x_flat.T @ dL/dz
  dL/db_enc = sum(dL/dz, axis=0)
  dL/dx = dL/dz @ W_enc.T  (propagate to previous layer)

For shared weights (cross_layer), accumulate gradients across all positions and layers before applying.

#### 3. Create `src/run_phase1_v2.py` experiment runner:

**7 configurations × 5 seeds (42–46) = 35 total runs:**
1. P1-B-JEPA-d8: cross_layer sharing, d=8, d_out=8, JEPA loss
2. P1-B-Contrastive-d8: cross_layer sharing, d=8, d_out=8, Contrastive loss
3. P1-B-SFA-d8: cross_layer sharing, d=8, d_out=8, SFA loss
4. P1-B-Hebbian-d8: cross_layer sharing, d=8, d_out=8, Hebbian updates
5. P1-B-JEPA-d16: cross_layer sharing, d=16, d_out=16, JEPA loss (test d=8 vs d=16)
6. Untrained-d8: cross_layer sharing, d=8, d_out=8, no training (same-session baseline)
7. Untrained-d16: cross_layer sharing, d=16, d_out=16, no training (same-session baseline)

**Training parameters:**
- 200 epochs (simultaneous training of all layers, not progressive)
- batch_size=64
- For JEPA/Contrastive/SFA: Adam-like optimizer (or plain SGD with momentum)
  - Since we're numpy-only, implement simple Adam: m = β1*m + (1-β1)*g, v = β2*v + (1-β2)*g², param -= lr * m / (sqrt(v) + ε)
  - lr=1e-3, β1=0.9, β2=0.999, ε=1e-8
- For Hebbian: use Oja's rule with η=1e-3
- No L1 penalty for non-reconstruction objectives
- No k-WTA for non-reconstruction objectives (unless explicitly tested)

**Evaluation:**
- After training, encode train_x and test_x
- Linear probe: SimpleLogisticRegression from src/harness.py (5 classes, lr=0.1, max_iter=500)
- Metrics: test_accuracy, train_accuracy, sparsity (fraction |code|<1e-3), n_params
- For untrained baselines: use same dataset generation and evaluation protocol

**Output:** Save results to `phase_1/objectives_results.csv` with columns:
config, seed, test_accuracy, train_accuracy, sparsity, n_params

### Implementation Notes

1. **KEEP IT SIMPLE.** Use pure numpy. No external ML libraries.

2. **The UniversalNode already has W_enc, b_enc, W_dec, b_dec.** For non-reconstruction objectives, W_dec and b_dec are not trained (they remain at initialization). The evaluation function `evaluate_hierarchical_encoder` calls `compute_reconstruction_mse` which uses W_dec — this will give high MSE for non-reconstruction objectives but that's fine, we just need accuracy.

3. **Embedding:** Use Normal(0, 1) initialization (confirmed working from Phase 1 diagnostics).

4. **Simultaneous training:** All layers train at once (confirmed better than progressive in iter_002). For cross_layer sharing, all layer_nodes point to the same master node (like in SimultaneousHierarchicalEncoder).

5. **For ContrastiveLoss**, the projection head parameters must be trained alongside the encoder. Use Adam for the projection head too.

6. **For JEPALoss**, the predictor (linear d→d per layer) parameters must be trained alongside the encoder. Use Adam for predictors too.

7. **Crucial:** Run Untrained-d8 and Untrained-d16 IN THE SAME SESSION as the trained configs. Do NOT reuse old results. This ensures perfectly fair comparison (same dataset generation, same evaluation code, same random seeds).

8. **Code must work end-to-end.** After implementation, run the full experiment and save results to CSV. If there are bugs, fix them and re-run.

9. **Existing files to read for context:**
   - src/node.py — UniversalNode class with forward, compute_gradients, apply_gradients
   - src/hierarchical_encoder.py — HierarchicalEncoder with forward, train, _forward_layer
   - src/dataset_phase1.py — generate_phase1_dataset
   - src/eval_phase1.py — evaluate_hierarchical_encoder
   - src/harness.py — SimpleLogisticRegression, compute_sparsity
   - src/diagnostic_phase1.py — SimultaneousHierarchicalEncoder (good reference for simultaneous training)

10. **Run from the project root directory** (not from src/). The scripts use `sys.path` manipulation for imports.

### Success Criteria
- All 7 configs × 5 seeds = 35 runs complete without errors
- Results saved to phase_1/objectives_results.csv
- At minimum, the untrained baselines reproduce known values (~48% for d=8)
