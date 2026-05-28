## Task: Implement src/run_phase5.py — Phase 5 Experiment Runner

Implement the Phase 5 experiment runner. This file handles training, semantic probing, and consistency analysis. The semantic probes module (`src/semantic_probes.py`) is already implemented.

### Key Reference Files (read them first!)
- `src/run_phase4.py` — The Phase 4 runner. **Base your code on this.** It has the training loop, pooled_vicreg_loss, pooled_vicreg_grad, recon_loss_and_grad, evaluate_classification, and the experiment orchestration.
- `src/spatiotemporal_encoder.py` — SpatiotemporalEncoder with forward_with_intermediates()
- `src/semantic_probes.py` — compute_all_probes() and downsample_probes()
- `src/run_phase3.py` — create_jepa_losses, reshape helpers
- `src/harness.py` — SimpleLogisticRegression
- `src/training_objectives.py` — _Adam class

### Architecture Details
- Input: (B, 16, 32) binary grid
- 3 spatial layers: outputs (B,14,32,d), (B,12,32,d), (B,10,32,d) where d=16
- 3 temporal layers: outputs (B,30,10,d), (B,28,10,d), (B,26,10,d) where d=16
- Pooled output: (B, 16)
- P3-C variant (shared weights), 1,600 params

### Training Variants

**P5-A (Pure Emergence)**: Reconstruction + pooled VICReg. Exactly same as run_phase4.py's "recon" + use_pooled_vicreg=True. Config: 30 epochs, lr=1e-3, batch=64, λ_var=25, λ_cov=25, λ_l1=0.01, alpha=0.5.

**P5-B (Anchor Features)**: Reconstruction + pooled VICReg + anchor regularization.
- Add loss: L_anchor = λ_anchor * (1/k) * Σ_{j=0}^{k-1} ||code[:,:,:,j] - probe_j_norm||² at EACH spatial and temporal intermediate layer. λ_anchor=0.1, k=5 (first 5 dims).
- Probes computed from raw input, downsampled using semantic_probes.downsample_probes().
- Normalize probes: zero-mean, unit-variance across batch dim at each (s,t) position. If std<1e-8, set normalized probe to 0.
- Anchor gradient for code[:,:,:,j] is 2*λ_anchor*(1/k)*(code[:,:,:,j] - probe_j_norm) / M where M = B*P1*P2. For dims j≥k, anchor gradient is zero.

**P5-C (Disentanglement Penalty)**: Reconstruction + pooled VICReg + correlation penalty.
- Add loss: L_dis = β * (1/n_layers) * Σ_{layers} (1/(d*(d-1))) * Σ_{j≠k} Corr(code_j, code_k)² at each intermediate layer. β=0.01.
- Compute Corr from flattened (M, d) codes. M = B*P1*P2.
- Gradient: ∂L_dis/∂code_j = β*(2/(d*(d-1)*n_layers*M)) * Σ_{k≠j} Corr_jk * (Δcode_k - Corr_jk*Δcode_j) where Δcode = (code - mean)/std. Use standard Pearson correlation gradient.

**Untrained**: Same architecture, no training, 5 seeds.

Seeds: [42, 43, 44, 45, 46]

### Semantic Probing Analysis

For each trained model (all 20 runs):
1. Forward-pass full test set (400 samples) in batches of 64, storing ALL intermediate codes.
2. Compute 5 semantic probe feature maps from raw test grids using compute_all_probes().
3. Downsample probes to match each layer's resolution using downsample_probes().
4. For each (layer, s, t, code_dim_j), compute Pearson R between code_dim_j and each of 5 probes across the 400 samples. Also compute R².
5. **Interpretability threshold (CRITICAL)**: Assign dominant semantic only if max_k |R| ≥ 0.20 AND FDR-corrected q < 0.05. Otherwise "Unassigned/Null". Apply Benjamini-Hochberg across all 16*5=80 tests at each (layer, s, t) position.
6. For FDR: collect all p-values for the 80 tests at a position, apply BH correction, then check q < 0.05.

### Consistency Scoring

For each dimension j (0-15):
a) **WITHIN-LAYER SPATIAL CONSISTENCY**: Fix timestep (t=15 for spatial, t≈14 for temporal). For each spatial layer l, fraction of spatial positions agreeing on dominant semantic. Average across layers. Only count positions where dominant semantic IS assigned.
b) **CROSS-LAYER CONSISTENCY**: Matched center positions across spatial layers (pos 7@L0, pos 6@L1, pos 5@L2). Fraction of dims where ALL layers agree. Only count dims with assigned semantics in ALL layers.
c) **OVERALL CONSISTENCY**: Fraction of ALL (layer, s, t) positions agreeing on the most common dominant semantic for dim j. Mean across j. Only include assigned positions.
d) **TRAINING GAIN**: P5-A overall consistency minus untrained overall consistency.

**P5-B special handling**: Report anchored-dim consistency (dims 0-4) and free-dim consistency (dims 5-15) SEPARATELY.

### Classification Evaluation
Same as Phase 4: spatial_pooled_then_flat readout, SimpleLogisticRegression, 4-class accuracy.

### Output Files
- `phase_5/phase5_results.csv` — columns: variant, seed, test_acc, overall_consistency, within_layer_consistency, cross_layer_consistency, training_gain, anchored_consistency (P5-B only), free_consistency (P5-B only)
- `phase_5/consistency_analysis.csv` — per-dimension detail
- `phase_5/r_squared_heatmap.csv` — R² for (code_dim × probe_axis) at each layer
- `phase_5/REPORT.md` — comprehensive analysis report

### Implementation Approach

Create `src/run_phase5.py` with these main sections:

1. **Imports and config** (copy structure from run_phase4.py)
2. **anchor_loss_and_grad(code, downsampled_probes, k=5, lambda_anchor=0.1)** function
3. **disentangle_loss_and_grad(code, beta=0.01)** function  
4. **Modified train_epoch()** supporting P5-A/B/C (add anchor and disentangle loss terms)
5. **extract_intermediate_codes()** — forward pass full dataset, return all codes
6. **semantic_correlation_analysis()** — compute R, R², p-values, FDR, dominant semantic assignment
7. **compute_consistency_scores()** — within-layer, cross-layer, overall consistency
8. **run_single_experiment()** — trains model, evaluates classification, runs semantic analysis
9. **generate_report()** — write phase_5/REPORT.md
10. **main()** with --dry-run flag and --skip-existing flag

**IMPORTANT**: The train_epoch function should be modified from Phase 4 to:
- For P5-A: same as Phase 4 recon+VICReg
- For P5-B: add anchor_loss_and_grad computation, add to code gradients
- For P5-C: add disentangle_loss_and_grad computation, add to code gradients
- Support all three by passing variant="P5-A"/"P5-B"/"P5-C"

### Dry-Run Verification

After implementation, run:
```bash
cd src && python run_phase5.py --dry-run
```

Verify all 4 variants run without error and produce CSV output. Fix any bugs.

### Language Discipline
In the report, use precise statistical language. Example: "Dimension 3 shows a statistically significant correlation (R=0.45, q<0.01) with local magnitude at 87% of spatial positions in layer 0." NOT "the network discovered the concept of activity."