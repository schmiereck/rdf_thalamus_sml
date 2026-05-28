## Task: Implement Phase 5 — Vector Semantics Investigation (Code + Dry-Run)

You are implementing Phase 5 of the HSUN project. Your job is to create two Python modules and verify they work via a dry-run.

### Context
The project investigates a hierarchical sparse universal node architecture. Phase 4 found that **Reconstruction + pooled VICReg** achieves 83% classification accuracy on a 4-class spatiotemporal benchmark (16×32 binary grids). Phase 5 asks: *do the 16 code dimensions carry consistent, interpretable semantics across positions and layers?*

Key existing files in `src/`:
- `spatiotemporal_encoder.py` — P3-C encoder (SpatiotemporalEncoder class), forward_with_intermediates() returns dict with keys: embeddings, spatial_outputs (3 layers), spatial_inputs (3 layers), temporal_outputs (3 layers), temporal_inputs (3 layers), pooled
- `training_objectives.py` — JEPALoss, _Adam
- `run_phase4.py` — Phase 4 runner (reference for training loop structure, pooled_vicreg_loss, pooled_vicreg_grad, recon_loss_and_grad, etc.)
- `run_phase3.py` — Helper functions: create_jepa_losses, reshape_for_spatial_jepa, reshape_spatial_grads_back, reshape_for_temporal_jepa, reshape_temporal_grads_back
- `spatiotemporal_dataset.py` — generate_spatiotemporal_dataset(), N_CLASSES=4
- `harness.py` — SimpleLogisticRegression
- `node.py` — UniversalNode

Architecture details:
- Input: (B, 16, 32) binary grid → embedding → 3 spatial layers (16→14→12→10 positions) → transpose → 3 temporal layers (32→30→28→26 positions) → mean pool → (B, 16)
- Spatial outputs: layer 0 = (B, 14, 32, d), layer 1 = (B, 12, 32, d), layer 2 = (B, 10, 32, d)
- Temporal outputs: layer 0 = (B, 30, 10, d), layer 1 = (B, 28, 10, d), layer 2 = (B, 26, 10, d)
- d = d_out = 16

### FILE 1: src/semantic_probes.py

Implement 5 scalar semantic probes computed from the raw (B, 16, 32) binary grid. Each probe produces a (B, 16, 32) feature map (one scalar per spatial-temporal position).

**IMPORTANT: Manager's Correction #2 — Interpretability Threshold**
In the analysis, a dimension j at position (s,t) can only be assigned a dominant semantic if max_k |R(j, p_k)| ≥ 0.20 AND FDR-corrected q < 0.05. If it fails, label it "Unassigned/Null". This prevents inflating consistency from noise.

The 5 probes:

1. **MAGNITUDE**: For position (s, t), mean of grid[max(0,s-1):min(16,s+2), max(0,t-1):min(32,t+2)] — local average activity in a 3×3 window. Use modulo-16 spatial wrapping for boundary positions (wrap spatial axis only, NOT temporal — temporal boundaries use clamping).

2. **GRADIENT**: For position (s, t), mean(grid[(s+1)%16:(s+3)%16, t]) - mean(grid[(s-2)%16:s, t]) — right-minus-left spatial gradient. Explicit boundary handling with modulo-16 wrapping on the spatial axis.

3. **VARIANCE**: For position (s, t), variance of grid[s, max(0,t-4):t+1] over the last 5 timesteps (clamped at t=0). If t<4, use available timesteps. Variance of a single element = 0.

4. **PERIODICITY**: For position (s, t), autocorrelation at lag 2 of grid[s, max(0,t-7):t+1] — measures temporal repetitiveness. Use at least 5 timesteps; if fewer, return 0. Formula: Corr(x, x_{lag=2}) where Corr is Pearson correlation. Handle edge cases (constant sequences → return 0).

5. **NOVELTY**: For position (s, t), |grid[s, t] - grid[s, max(0, t-1)]| — pixel-level temporal change (0 for t=0).

Also implement downsampling functions:
- `downsample_probes_spatial(probe_map, layer_idx)`: Average probe values over the receptive field of each code position in spatial layer `layer_idx`. For spatial layer l, the output has shape (B, 16-2*(l+1), 32) = (B, 14|12|10, 32). The receptive field of spatial position p at layer l covers input positions [p, p+1, ..., p+2*(l+1)]. Use this for downsampling.
- `downsample_probes_temporal(probe_map, layer_idx)`: Similarly for temporal axis. After spatial processing, we have 10 spatial positions. Temporal layer l has T=32-2*(l+1) positions. Position p at temporal layer l covers input timesteps [p, p+1, ..., p+2*(l+1)].
- For temporal layers, also downsample the spatial axis from 16 to 10 positions (use average over [p, p+1, ..., p+6] for position p, covering the 3-layer spatial receptive field of 7 positions, but handle boundary positions by clamping).

Function signatures:
```python
PROBE_NAMES = ["magnitude", "gradient", "variance", "periodicity", "novelty"]

def compute_all_probes(grid: np.ndarray) -> dict:
    """Compute all 5 probe feature maps from raw (B, 16, 32) binary grid.
    Returns dict mapping probe_name -> (B, 16, 32) float array."""

def downsample_probes(probe_maps: dict, n_spatial_layers: int = 3, 
                      n_temporal_layers: int = 3) -> dict:
    """Downsample all probe maps to match encoder's layer resolutions.
    Returns dict with keys like 'spatial_0', 'spatial_1', 'spatial_2', 
    'temporal_0', 'temporal_1', 'temporal_2'.
    Each value is a dict mapping probe_name -> (B, n_pos1, n_pos2) shaped array
    where n_pos1 and n_pos2 match the code shape at that layer.
    For spatial: (B, S_l, 32)
    For temporal: (B, T_l, 10)
    """
```

### FILE 2: src/run_phase5.py

Implement the full Phase 5 experiment runner. This is the most complex file.

#### Training Variants (3 variants × 5 seeds + 5 untrained = 20 total):

**P5-A (Pure Emergence)**: Reconstruction + pooled VICReg, identical to Phase 4 best config.
- 30 epochs, lr=1e-3, batch=64, λ_var=25, λ_cov=25, λ_l1=0.01, alpha=0.5
- Same as run_phase4.py's "recon" + use_pooled_vicreg=True

**P5-B (Anchor Features)**: Reconstruction + pooled VICReg + anchor regularization.
- Add loss term: L_anchor = λ_anchor * (1/5) * Σ_{j=0}^{4} ||code[:, :, :, j] - probe_j(normalized)||² 
  at each spatial and temporal intermediate layer.
- λ_anchor = 0.1
- The first 5 code dimensions are softly anchored to the 5 normalized semantic probes.
- Remaining 11 dimensions are free.
- Probes are computed from raw input, downsampled to match each layer's resolution, 
  and L2-normalized (zero mean, unit variance per position) before computing anchor loss.

**IMPORTANT: Manager's Correction #1 — P5-B Evaluation**
When evaluating P5-B's semantic consistency, **segregate anchored dimensions (0-4) from free dimensions (5-15)**. The only genuine empirical questions for P5-B are:
  1. Does forcing 5 semantic alignments degrade classification accuracy vs P5-A?
  2. Does anchoring the first 5 dimensions IMPROVE emergent consistency in the remaining 11 free dimensions?
Report anchored-dim consistency and free-dim consistency separately.

**P5-C (Disentanglement Penalty)**: Reconstruction + pooled VICReg + correlation penalty.
- Add loss term: L_dis = β * Σ_{layers} (1/(d*(d-1))) * Σ_{j≠k} |Corr(code_j, code_k)|²
  at each intermediate layer. β = 0.01.
- This encourages dimensions to be decorrelated beyond pooled VICReg's effect.

**Untrained baseline**: Same architecture, no training, 5 seeds.

Seeds: [42, 43, 44, 45, 46]

#### Semantic Probing Analysis (for ALL 20 trained models):

For each model:
1. Forward-pass the FULL test set (400 samples, process in batches of 64) through the encoder, storing ALL intermediate codes at each (layer, s, t) position.
2. Compute 5 semantic probe feature maps from the raw test grids.
3. Downsample probes to match each layer's spatial/temporal resolution.
4. For each (layer, s, t, code_dim_j), compute Pearson R and R² between code_dim_j and each of the 5 semantic probes across the 400 samples.
5. **Interpretability threshold**: Assign dominant semantic only if max_k |R(j, p_k)| ≥ 0.20 AND FDR-corrected q < 0.05. Otherwise label "Unassigned/Null".
6. Apply FDR correction (Benjamini-Hochberg) across all d*5 = 80 tests at each position.

#### Consistency Scoring:

For each dimension j (0-15):
a) **WITHIN-LAYER SPATIAL CONSISTENCY**: For each spatial layer l, fix timestep t (use middle, e.g. t=15). Compute fraction of spatial positions agreeing on dominant semantic. Average across layers. **Only count positions where a dominant semantic IS assigned** (pass interpretability threshold). If no positions pass the threshold for a dimension, mark consistency as N/A.
b) **CROSS-LAYER CONSISTENCY**: For matched center positions across spatial layers (position 7→6→5 at layers 0→1→2), compute fraction of dimensions where all layers agree on dominant semantic. Only count dimensions where ALL layers assign a semantic (not Null).
c) **OVERALL CONSISTENCY**: Fraction of ALL (layer, s, t) positions that agree on the most common dominant semantic for dimension j. Mean across j. Only include positions with assigned semantics.
d) **TRAINING GAIN**: P5-A overall consistency minus untrained overall consistency.

**IMPORTANT: Manager's Correction #3 — Language Discipline**
Use precise, statistical language. E.g., "dimension j shows a correlation of R=X with local temporal change at Y% of spatial positions" — NOT "the network organically discovered the concept of motion".

#### Classification Evaluation:
Same as Phase 4: spatial_pooled_then_flat readout, SimpleLogisticRegression, 4-class accuracy. Confirm P5-A reproduces ~83%, P5-B ≥ 78%, P5-C ≥ 78%.

#### Output Files:
- `phase_5/phase5_results.csv` — Raw results (accuracy, consistency scores per variant/seed)
- `phase_5/consistency_analysis.csv` — Per-dimension consistency detail
- `phase_5/r_squared_heatmap.csv` — R² values for (code_dim × semantic_axis) at each layer  
- `phase_5/REPORT.md` — Comprehensive analysis report

#### Structure of run_phase5.py:
1. Import semantic_probes
2. Implement anchor_loss_and_grad() function  
3. Implement disentanglement_loss_and_grad() function
4. Modify train_epoch() from run_phase4.py to support P5-A/B/C
5. Implement run_single_experiment() that trains AND does semantic analysis
6. Implement consistency_scoring() function  
7. Implement report generation
8. Main function with --dry-run flag

**CRITICAL**: For the anchor loss, the probes need to be downsampled to match each layer's code resolution. The code at spatial layer l has shape (B, n_spatial, n_temporal, d_out). The probe at the same resolution should be (B, n_spatial, n_temporal). We match code[:,:,:,j] with probe[:,:,:] for dimension j (first 5 dims only). The normalized probe should be L2-normalized to zero mean and unit variance across the batch dimension at each spatial-temporal position.

**CRITICAL**: The anchor loss gradient must flow through to the encoder. When we compute L_anchor = ||code[:,:,:,j] - probe_j||², the gradient of L_anchor w.r.t. code[:,:,:,j] is 2*(code[:,:,:,j] - probe_j) / (n_elements). This gets added to the code gradients before backward(). For dims j≥5, the anchor gradient is zero.

For the disentanglement penalty: 
∂L_dis/∂code_j = β * (2/(d*(d-1))) * Σ_{k≠j} |Corr_jk| * sign(Corr_jk) * ∂Corr_jk/∂code_j
Where ∂Corr_jk/∂code_j is the standard Pearson correlation gradient.
Compute Corr_jk from flattened (M, d) code at each layer. M = B*P1*P2.

#### DRY-RUN VERIFICATION:
After implementing both files, run:
```bash
cd src && python run_phase5.py --dry-run
```

This should run 1 seed, 1 epoch for each variant (P5-A, P5-B, P5-C, untrained) and produce initial results. Verify:
1. All 4 variants run without errors
2. Semantic probes produce valid values (not NaN, not all zero)
3. Anchor loss is non-zero for P5-B
4. Disentanglement loss is non-zero for P5-C
5. Consistency scores are computed (may be N/A for dry-run due to few epochs)
6. Output CSV is created

If any issues, fix them before reporting completion. Save the dry-run output as evidence.