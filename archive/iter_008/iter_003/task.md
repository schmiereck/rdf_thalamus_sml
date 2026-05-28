## Task: Write src/run_phase5.py and execute full Phase 5 experiment

STEP 1: Write the following code to src/run_phase5.py (use your write_to_file tool or equivalent).

STEP 2: Run `cd src && python run_phase5.py --dry-run` to verify it works.

STEP 3: Run `cd src && python run_phase5.py` for the full 20-experiment suite.

STEP 4: After experiments complete, the report will be at phase_5/REPORT.md. Read it and report the key findings.

Here is the COMPLETE code to write to src/run_phase5.py:

```python
#!/usr/bin/env python3
"""
Phase 5 - Vector Semantics Investigation.

Compares three training variants + untrained baseline on the P3-C encoder:
  P5-A: Pure Emergence (Reconstruction + pooled VICReg)
  P5-B: Anchor Features (Recon + VICReg + anchor regularization)
  P5-C: Disentanglement (Recon + VICReg + correlation penalty)
  Untrained: random init

For each model, probes 16 code dimensions for correlation with 5 semantic
axes and computes consistency scores across positions and layers.
"""

from __future__ import annotations

import csv
import gc
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_probes import compute_all_probes, downsample_probes, PROBE_NAMES
from spatiotemporal_dataset import generate_spatiotemporal_dataset, N_CLASSES
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import _Adam
from harness import SimpleLogisticRegression
from run_phase3 import (
    create_jepa_losses,
    reshape_for_spatial_jepa,
    reshape_spatial_grads_back,
    reshape_for_temporal_jepa,
    reshape_temporal_grads_back,
)
from run_phase4 import (
    pooled_vicreg_loss,
    pooled_vicreg_grad,
    recon_loss_and_grad,
    sfa_loss_and_grad,
    hebbian_loss_and_grad,
    evaluate_classification,
)

# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]
D = 16
D_OUT = 16
N_TRAIN_PER_CLASS = 200
N_TEST_PER_CLASS = 100
EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-3
ALPHA = 0.5
LAMBDA_L1 = 0.01
LAMBDA_ANCHOR = 0.1
N_ANCHOR_DIMS = 5
BETA_DISENTANGLE = 0.01
R_THRESHOLD = 0.20
Q_THRESHOLD = 0.05

OUTPUT_DIR = "phase_5"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "phase5_results.csv")
CONSISTENCY_CSV = os.path.join(OUTPUT_DIR, "consistency_analysis.csv")
RSQUARED_CSV = os.path.join(OUTPUT_DIR, "r_squared_heatmap.csv")
REPORT_MD = os.path.join(OUTPUT_DIR, "REPORT.md")

VARIANTS = ["P5-A", "P5-B", "P5-C"]


# =============================================================================
#  Anchor loss and gradient (P5-B)
# =============================================================================

def anchor_loss_and_grad(
    code: np.ndarray,
    downsampled_probes: dict,
    k: int = N_ANCHOR_DIMS,
    lambda_anchor: float = LAMBDA_ANCHOR,
) -> dict:
    """
    Compute anchor loss and gradient for P5-B.
    
    L_anchor = lambda_anchor * (1/k) * sum_{j=0}^{k-1} ||code[:,:,:,j] - probe_j_norm||^2
    
    Probes are normalized to zero-mean, unit-variance across batch at each position.
    
    Parameters
    ----------
    code : (B, P1, P2, d) intermediate code
    downsampled_probes : dict mapping probe_name -> (B, P1, P2)
    k : number of anchor dimensions
    lambda_anchor : anchor loss weight
    
    Returns dict with 'loss', 'code_grad'
    """
    B, P1, P2, d = code.shape
    code_grad = np.zeros_like(code)
    total_loss = 0.0
    
    for j in range(k):
        probe_name = PROBE_NAMES[j]
        if probe_name not in downsampled_probes:
            continue
        probe_raw = downsampled_probes[probe_name]  # (B, P1, P2)
        
        # Normalize probe: zero mean, unit variance across batch at each (p1, p2)
        probe_mean = probe_raw.mean(axis=0, keepdims=True)  # (1, P1, P2)
        probe_std = np.sqrt(probe_raw.var(axis=0, ddof=0, keepdims=True) + 1e-8)  # (1, P1, P2)
        probe_norm = (probe_raw - probe_mean) / probe_std
        # Where std is too small, set probe to 0
        small_std = probe_std < 1e-8
        probe_norm = np.where(small_std, 0.0, probe_norm)
        
        # Code slice for dimension j
        code_j = code[:, :, :, j]  # (B, P1, P2)
        
        # MSE loss
        diff = code_j - probe_norm  # (B, P1, P2)
        M = B * P1 * P2
        loss_j = np.mean(diff ** 2)
        total_loss += loss_j
        
        # Gradient w.r.t. code_j
        grad_j = 2.0 * diff / M  # (B, P1, P2)
        code_grad[:, :, :, j] = lambda_anchor * (1.0 / k) * grad_j
    
    total_loss = lambda_anchor * (1.0 / k) * total_loss
    return {"loss": float(total_loss), "code_grad": code_grad}


# =============================================================================
#  Disentanglement loss and gradient (P5-C)
# =============================================================================

def disentangle_loss_and_grad(
    code: np.ndarray,
    beta: float = BETA_DISENTANGLE,
) -> dict:
    """
    Correlation penalty on code dimensions.
    
    L_dis = beta * (1/(d*(d-1))) * sum_{j!=k} Corr(code_j, code_k)^2
    
    Parameters
    ----------
    code : (B, P1, P2, d) intermediate code
    beta : disentanglement weight
    
    Returns dict with 'loss', 'code_grad'
    """
    B, P1, P2, d = code.shape
    M = B * P1 * P2
    z = code.reshape(M, d)  # (M, d)
    
    # Compute correlation matrix
    mu = z.mean(axis=0, keepdims=True)  # (1, d)
    std = np.sqrt(z.var(axis=0, ddof=0, keepdims=True) + 1e-12)  # (1, d)
    z_norm = (z - mu) / std  # (M, d) normalized
    
    C = (z_norm.T @ z_norm) / M  # (d, d) correlation matrix
    mask = 1.0 - np.eye(d)
    C_off = C * mask  # off-diagonal only
    
    loss = beta * np.sum(C_off ** 2) / (d * (d - 1))
    
    # Gradient: dL/dz
    # dL/dC = beta * 2 * C_off / (d*(d-1))
    # dC/dz_norm = 2 * z_norm / M (simplified)
    # dL/dz = dL/dz_norm * dz_norm/dz
    dL_dC = beta * 2.0 * C_off / (d * (d - 1))  # (d, d)
    dL_dz_norm = (2.0 / M) * (z_norm @ dL_dC)  # (M, d)
    
    # dz_norm/dz = (1/std) - z_norm * (z_norm * dL_dz_norm).sum(1,keepdims)/(M*std)
    # Simplified: dz/dz_norm = std, so dz_norm/dz = 1/std
    # But we need dz/dL = dz/dz_norm * dz_norm/dL
    # Actually: z_norm = (z - mu) / std, so dz_norm/dz = (I - 1/M) / std
    # Full gradient: dL/dz = dL/dz_norm * dz_norm/dz
    # dz_norm/dz per sample: (1/std) * (I - 1/M * 11^T) ≈ 1/std for large M
    
    # More precise gradient:
    # dz_norm/dz_i = (1/std) * (e_i - mean_batch_grad/M)
    # For simplicity with large M:
    dL_dz = dL_dz_norm / std  # (M, d)
    
    code_grad = dL_dz.reshape(B, P1, P2, d)
    return {"loss": float(loss), "code_grad": code_grad}


# =============================================================================
#  Training epoch
# =============================================================================

def train_epoch(
    encoder: SpatiotemporalEncoder,
    train_grid: np.ndarray,
    batch_size: int,
    rng: np.random.Generator,
    variant: str = "P5-A",
    adam_spatial: _Adam | None = None,
    adam_decoder: _Adam | None = None,
) -> dict:
    """Train one epoch. Returns dict with losses and metrics."""
    n_samples = train_grid.shape[0]
    perm = rng.permutation(n_samples)
    
    total_recon_loss = 0.0
    total_anchor_loss = 0.0
    total_dis_loss = 0.0
    total_pooled_std = 0.0
    n_batches = 0
    
    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch = train_grid[perm[start:end]]
        
        fwd = encoder.forward_with_intermediates(batch)
        
        # --- Reconstruction loss + gradient (same for all variants) ---
        recon_losses = []
        spatial_code_grads = []
        temporal_code_grads = []
        dec_grads_all = []
        
        node = encoder.master_spatial
        W_dec = node.W_dec
        b_dec = node.b_dec
        
        for l in range(encoder.n_spatial_layers):
            code = fwd["spatial_outputs"][l]
            inp = fwd["spatial_inputs"][l]
            r = recon_loss_and_grad(code, inp, W_dec, b_dec, LAMBDA_L1)
            spatial_code_grads.append(r["code_grad"])
            recon_losses.append(r["loss"])
            dec_grads_all.append({"W_dec": r["W_dec_grad"], "b_dec": r["b_dec_grad"]})
        
        for l in range(encoder.n_temporal_layers):
            code = fwd["temporal_outputs"][l]
            inp = fwd["temporal_inputs"][l]
            r = recon_loss_and_grad(code, inp, W_dec, b_dec, LAMBDA_L1)
            temporal_code_grads.append(r["code_grad"])
            recon_losses.append(r["loss"])
            dec_grads_all.append({"W_dec": r["W_dec_grad"], "b_dec": r["b_dec_grad"]})
        
        # --- Pooled VICReg ---
        z_pooled = fwd["pooled"]
        dL_dzp = pooled_vicreg_grad(z_pooled)
        T_final, S_final = fwd["temporal_outputs"][-1].shape[1:3]
        dL_expanded = dL_dzp[:, None, None, :] / (T_final * S_final)
        dL_expanded = np.broadcast_to(dL_expanded, fwd["temporal_outputs"][-1].shape).copy()
        temporal_code_grads[-1] = temporal_code_grads[-1] + dL_expanded / (1.0 - ALPHA)
        
        pv = pooled_vicreg_loss(z_pooled)
        total_pooled_std += pv["std"]
        
        # --- Anchor loss (P5-B only) ---
        if variant == "P5-B":
            probes = compute_all_probes(batch)
            ds_probes = downsample_probes(probes)
            
            anchor_losses_batch = []
            
            # Spatial layers
            for l in range(encoder.n_spatial_layers):
                code = fwd["spatial_outputs"][l]
                layer_probes = ds_probes[f"spatial_{l}"]
                a_result = anchor_loss_and_grad(code, layer_probes)
                spatial_code_grads[l] = spatial_code_grads[l] + a_result["code_grad"]
                anchor_losses_batch.append(a_result["loss"])
            
            # Temporal layers
            for l in range(encoder.n_temporal_layers):
                code = fwd["temporal_outputs"][l]
                layer_probes = ds_probes[f"temporal_{l}"]
                a_result = anchor_loss_and_grad(code, layer_probes)
                temporal_code_grads[l] = temporal_code_grads[l] + a_result["code_grad"]
                anchor_losses_batch.append(a_result["loss"])
            
            total_anchor_loss += np.mean(anchor_losses_batch)
        
        # --- Disentanglement loss (P5-C only) ---
        if variant == "P5-C":
            dis_losses_batch = []
            n_total_layers = encoder.n_spatial_layers + encoder.n_temporal_layers
            
            for l in range(encoder.n_spatial_layers):
                code = fwd["spatial_outputs"][l]
                d_result = disentangle_loss_and_grad(code)
                spatial_code_grads[l] = spatial_code_grads[l] + d_result["code_grad"]
                dis_losses_batch.append(d_result["loss"])
            
            for l in range(encoder.n_temporal_layers):
                code = fwd["temporal_outputs"][l]
                d_result = disentangle_loss_and_grad(code)
                temporal_code_grads[l] = temporal_code_grads[l] + d_result["code_grad"]
                dis_losses_batch.append(d_result["loss"])
            
            total_dis_loss += np.mean(dis_losses_batch)
        
        # --- Encoder backward + update ---
        grads = encoder.backward(
            fwd,
            dL_dspatial_codes=spatial_code_grads,
            dL_dtemporal_codes=temporal_code_grads,
            alpha=ALPHA,
        )
        
        if encoder.variant == "P3-C":
            combined = {
                k: grads["dL_dspatial"][k] + grads["dL_dtemporal"][k]
                for k in grads["dL_dspatial"]
            }
            adam_spatial.step(
                {
                    "W_enc": encoder.master_spatial.W_enc,
                    "b_enc": encoder.master_spatial.b_enc,
                    "W_dec": encoder.master_spatial.W_dec,
                    "b_dec": encoder.master_spatial.b_dec,
                },
                combined,
            )
        
        # Update decoder
        if adam_decoder is not None:
            avg_W_dec_grad = (
                sum(g["W_dec"] for g in dec_grads_all)
                / len(dec_grads_all)
            )
            avg_b_dec_grad = (
                sum(g["b_dec"] for g in dec_grads_all)
                / len(dec_grads_all)
            )
            adam_decoder.step(
                {"W_dec": W_dec, "b_dec": b_dec},
                {"W_dec": avg_W_dec_grad, "b_dec": avg_b_dec_grad},
            )
        
        total_recon_loss += np.mean(recon_losses)
        n_batches += 1
    
    return {
        "recon_loss": total_recon_loss / n_batches,
        "anchor_loss": total_anchor_loss / n_batches if n_batches > 0 else 0.0,
        "dis_loss": total_dis_loss / n_batches if n_batches > 0 else 0.0,
        "pooled_std": total_pooled_std / n_batches,
    }


# =============================================================================
#  Semantic correlation analysis
# =============================================================================

def benjamini_hochberg(p_values: np.ndarray, q: float = 0.05) -> np.ndarray:
    """Apply Benjamini-Hochberg FDR correction. Returns boolean mask of significant tests."""
    n = len(p_values)
    if n == 0:
        return np.array([], dtype=bool)
    
    sorted_idx = np.argsort(p_values)
    sorted_p = p_values[sorted_idx]
    
    # BH threshold: p_(i) <= q * i / n
    thresholds = q * np.arange(1, n + 1) / n
    
    # Find largest i where p_(i) <= threshold
    significant = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= thresholds[i]:
            significant[:i + 1] = True
            break
    
    # Map back to original order
    result = np.zeros(n, dtype=bool)
    result[sorted_idx] = significant
    return result


def semantic_correlation_analysis(
    encoder: SpatiotemporalEncoder,
    test_grid: np.ndarray,
    batch_size: int = 64,
) -> dict:
    """
    Forward-pass test set, compute correlations between code dimensions
    and semantic probes at all layers.
    
    Returns dict with:
        'per_layer_dominant': dict mapping layer_key -> (n_pos1, n_pos2, d) int array
                              (probe index or -1 for Unassigned)
        'per_layer_r_squared': dict mapping layer_key -> (d, n_probes) R^2 matrix
        'per_layer_max_r': dict mapping layer_key -> (n_pos1, n_pos2, d) max |R|
        'per_layer_p_values': dict mapping layer_key -> (n_pos1, n_pos2, d, n_probes) p-values
    """
    # Compute probes once
    probes = compute_all_probes(test_grid)
    ds_probes = downsample_probes(probes)
    
    # Extract intermediate codes in batches
    all_codes = {}
    layer_keys = (
        [f"spatial_{l}" for l in range(encoder.n_spatial_layers)]
        + [f"temporal_{l}" for l in range(encoder.n_temporal_layers)]
    )
    
    for key in layer_keys:
        all_codes[key] = []
    
    for start in range(0, len(test_grid), batch_size):
        end = min(start + batch_size, len(test_grid))
        fwd = encoder.forward_with_intermediates(test_grid[start:end])
        
        for l in range(encoder.n_spatial_layers):
            all_codes[f"spatial_{l}"].append(fwd["spatial_outputs"][l])
        for l in range(encoder.n_temporal_layers):
            all_codes[f"temporal_{l}"].append(fwd["temporal_outputs"][l])
    
    for key in layer_keys:
        all_codes[key] = np.concatenate(all_codes[key], axis=0)
    
    # Compute correlations
    per_layer_dominant = {}
    per_layer_r_squared = {}
    per_layer_max_r = {}
    
    for key in layer_keys:
        codes = all_codes[key]  # (N, P1, P2, d)
        N, P1, P2, d = codes.shape
        
        # Get downsampled probes for this layer
        layer_probes = ds_probes[key]  # dict of (N, P1, P2)
        
        # Compute R and R^2 for each (position, dim, probe)
        # For efficiency, flatten samples
        r_squared_matrix = np.zeros((d, len(PROBE_NAMES)))  # averaged over positions
        dominant = np.full((P1, P2, d), -1, dtype=int)  # -1 = Unassigned
        max_r_map = np.zeros((P1, P2, d))
        
        n_assigned = 0
        n_total = 0
        
        for p1 in range(P1):
            for p2 in range(P2):
                code_slice = codes[:, p1, p2, :]  # (N, d)
                
                # Compute all p-values for this position
                all_r = np.zeros((d, len(PROBE_NAMES)))
                all_p = np.zeros((d, len(PROBE_NAMES)))
                
                for pi, probe_name in enumerate(PROBE_NAMES):
                    probe_slice = layer_probes[probe_name][:, p1, p2]  # (N,)
                    
                    for j in range(d):
                        c = code_slice[:, j]
                        # Pearson correlation
                        if np.std(c) < 1e-12 or np.std(probe_slice) < 1e-12:
                            r = 0.0
                            p = 1.0
                        else:
                            r = np.corrcoef(c, probe_slice)[0, 1]
                            if np.isnan(r):
                                r = 0.0
                            # p-value via t-distribution approximation
                            n_eff = len(c)
                            if abs(r) < 1.0:
                                t_stat = r * np.sqrt((n_eff - 2) / (1 - r**2 + 1e-12))
                                # Two-tailed p-value from |t|
                                p = 2.0 * (1.0 - _t_cdf_approx(abs(t_stat), n_eff - 2))
                            else:
                                p = 0.0 if abs(r) > 0.999 else 1.0
                            
                            all_r[j, pi] = r
                            all_p[j, pi] = p
                
                # FDR correction across d * n_probes = 80 tests
                flat_p = all_p.ravel()
                significant = benjamini_hochberg(flat_p, q=Q_THRESHOLD)
                significant = significant.reshape(d, len(PROBE_NAMES))
                
                for j in range(d):
                    max_r = np.max(np.abs(all_r[j]))
                    max_probe = np.argmax(np.abs(all_r[j]))
                    
                    # Interpretability threshold
                    if max_r >= R_THRESHOLD and np.any(significant[j]):
                        dominant[p1, p2, j] = max_probe
                        max_r_map[p1, p2, j] = max_r
                        n_assigned += 1
                    else:
                        dominant[p1, p2, j] = -1  # Unassigned
                    n_total += 1
                
                # Accumulate R^2 for position-averaged matrix
                for j in range(d):
                    for pi in range(len(PROBE_NAMES)):
                        r_squared_matrix[j, pi] += all_r[j, pi] ** 2
        
        r_squared_matrix /= (P1 * P2)
        per_layer_dominant[key] = dominant
        per_layer_r_squared[key] = r_squared_matrix
        per_layer_max_r[key] = max_r_map
    
    return {
        "per_layer_dominant": per_layer_dominant,
        "per_layer_r_squared": per_layer_r_squared,
        "per_layer_max_r": per_layer_max_r,
    }


def _t_cdf_approx(t: float, df: int) -> float:
    """Approximate CDF of t-distribution using normal approximation for large df."""
    if df >= 30:
        # Normal approximation
        from scipy.stats import norm
        return float(norm.cdf(t))
    else:
        # Use scipy if available
        try:
            from scipy.stats import t as t_dist
            return float(t_dist.cdf(t, df))
        except ImportError:
            # Rough approximation
            return 0.5 + 0.5 * np.sign(t) * min(1.0, abs(t) / np.sqrt(df + 1))


# =============================================================================
#  Consistency scoring
# =============================================================================

def compute_consistency_scores(
    semantic_result: dict,
    variant: str = "P5-A",
) -> dict:
    """
    Compute within-layer, cross-layer, and overall consistency scores.
    
    For P5-B, also compute anchored-dim and free-dim consistency separately.
    """
    dominant = semantic_result["per_layer_dominant"]
    spatial_keys = [k for k in dominant if k.startswith("spatial")]
    temporal_keys = [k for k in dominant if k.startswith("temporal")]
    
    # --- Within-layer spatial consistency ---
    # Fix timestep t (use middle for spatial layers with T=32)
    within_layer_scores = []
    for key in spatial_keys:
        dom = dominant[key]  # (P1, P2, d) — P2 = 32 for spatial
        P1, P2, d = dom.shape
        t_fixed = P2 // 2  # middle timestep
        
        for j in range(d):
            assigned_positions = []
            for p1 in range(P1):
                if dom[p1, t_fixed, j] >= 0:  # not Unassigned
                    assigned_positions.append(dom[p1, t_fixed, j])
            
            if len(assigned_positions) > 1:
                # Fraction agreeing on most common semantic
                counts = np.bincount(assigned_positions, minlength=len(PROBE_NAMES))
                agreement = counts.max() / len(assigned_positions)
                within_layer_scores.append(agreement)
    
    within_layer = float(np.mean(within_layer_scores)) if within_layer_scores else float("nan")
    
    # --- Cross-layer consistency ---
    # Match center positions: spatial layer 0 pos 7, layer 1 pos 6, layer 2 pos 5
    cross_layer_scores = []
    center_positions = [7, 6, 5]
    t_fixed_spatial = 16  # middle timestep
    
    if len(spatial_keys) == 3:
        for j in range(d):
            assignments = []
            all_assigned = True
            for l, key in enumerate(spatial_keys):
                dom = dominant[key]
                P1, P2, d_l = dom.shape
                pos = center_positions[l]
                if pos < P1 and dom[pos, t_fixed_spatial, j] >= 0:
                    assignments.append(dom[pos, t_fixed_spatial, j])
                else:
                    all_assigned = False
                    break
            
            if all_assigned and len(assignments) == 3:
                # All agree?
                if len(set(assignments)) == 1:
                    cross_layer_scores.append(1.0)
                else:
                    # Fraction of pairs that agree
                    n_agree = 0
                    n_pairs = 0
                    for a in range(len(assignments)):
                        for b in range(a+1, len(assignments)):
                            n_pairs += 1
                            if assignments[a] == assignments[b]:
                                n_agree += 1
                    cross_layer_scores.append(n_agree / n_pairs)
    
    cross_layer = float(np.mean(cross_layer_scores)) if cross_layer_scores else float("nan")
    
    # --- Overall consistency ---
    overall_scores = []
    all_keys = spatial_keys + temporal_keys
    
    for j in range(d):
        assigned_semantics = []
        for key in all_keys:
            dom = dominant[key]
            P1, P2, d_dim = dom.shape
            for p1 in range(P1):
                for p2 in range(P2):
                    if dom[p1, p2, j] >= 0:
                        assigned_semantics.append(dom[p1, p2, j])
        
        if len(assigned_semantics) > 1:
            counts = np.bincount(assigned_semantics, minlength=len(PROBE_NAMES))
            agreement = counts.max() / len(assigned_semantics)
            overall_scores.append(agreement)
    
    overall = float(np.mean(overall_scores)) if overall_scores else float("nan")
    
    # --- P5-B special: anchored vs free dimensions ---
    anchored_consistency = float("nan")
    free_consistency = float("nan")
    
    if variant == "P5-B":
        # Anchored dims (0-4)
        anchored_scores = []
        for j in range(N_ANCHOR_DIMS):
            assigned = []
            for key in all_keys:
                dom = dominant[key]
                P1, P2, d_dim = dom.shape
                for p1 in range(P1):
                    for p2 in range(P2):
                        if dom[p1, p2, j] >= 0:
                            assigned.append(dom[p1, p2, j])
            if len(assigned) > 1:
                counts = np.bincount(assigned, minlength=len(PROBE_NAMES))
                anchored_scores.append(counts.max() / len(assigned))
        
        # Free dims (5-15)
        free_scores = []
        for j in range(N_ANCHOR_DIMS, d):
            assigned = []
            for key in all_keys:
                dom = dominant[key]
                P1, P2, d_dim = dom.shape
                for p1 in range(P1):
                    for p2 in range(P2):
                        if dom[p1, p2, j] >= 0:
                            assigned.append(dom[p1, p2, j])
            if len(assigned) > 1:
                counts = np.bincount(assigned, minlength=len(PROBE_NAMES))
                free_scores.append(counts.max() / len(assigned))
        
        anchored_consistency = float(np.mean(anchored_scores)) if anchored_scores else float("nan")
        free_consistency = float(np.mean(free_scores)) if free_scores else float("nan")
    
    return {
        "within_layer": within_layer,
        "cross_layer": cross_layer,
        "overall": overall,
        "anchored": anchored_consistency,
        "free": free_consistency,
    }


# =============================================================================
#  Single experiment runner
# =============================================================================

def run_single_experiment(args: tuple) -> dict:
    """Run one experiment: train, evaluate classification, do semantic analysis."""
    variant, seed, epochs = args
    
    rng = np.random.default_rng(seed)
    
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=0.10,
        seed=seed,
    )
    train_grid = ds["train_grid"]
    train_y = ds["train_y"]
    test_grid = ds["test_grid"]
    test_y = ds["test_y"]
    
    encoder = SpatiotemporalEncoder(
        variant="P3-C",
        d=D,
        d_out=D_OUT,
        n_spatial_layers=3,
        n_temporal_layers=3,
        l1_lambda=0.0,
        seed=seed,
    )
    
    is_untrained = (variant == "untrained")
    
    # Setup optimizers
    if not is_untrained:
        params_enc = {
            "W_enc": encoder.master_spatial.W_enc,
            "b_enc": encoder.master_spatial.b_enc,
            "W_dec": encoder.master_spatial.W_dec,
            "b_dec": encoder.master_spatial.b_dec,
        }
        adam_spatial = _Adam(params_enc, lr=LR)
        adam_decoder = _Adam(
            {"W_dec": encoder.master_spatial.W_dec, "b_dec": encoder.master_spatial.b_dec},
            lr=LR,
        )
    else:
        adam_spatial = None
        adam_decoder = None
    
    # Training
    t0 = time.time()
    if not is_untrained:
        for epoch in range(epochs):
            metrics = train_epoch(
                encoder,
                train_grid,
                BATCH_SIZE,
                rng,
                variant=variant,
                adam_spatial=adam_spatial,
                adam_decoder=adam_decoder,
            )
    else:
        metrics = {"recon_loss": 0.0, "anchor_loss": 0.0, "dis_loss": 0.0, "pooled_std": 0.0}
    t1 = time.time()
    
    # Classification evaluation
    eval_res = evaluate_classification(
        encoder, train_grid, train_y, test_grid, test_y, seed=seed
    )
    
    # Semantic analysis
    semantic_result = semantic_correlation_analysis(encoder, test_grid)
    consistency = compute_consistency_scores(semantic_result, variant=variant)
    
    # Assign training gain
    training_gain = float("nan")  # will be computed after all runs
    
    return {
        "variant": variant,
        "seed": seed,
        "test_acc": eval_res["test_acc"],
        "train_acc": eval_res["train_acc"],
        "overall_consistency": consistency["overall"],
        "within_layer_consistency": consistency["within_layer"],
        "cross_layer_consistency": consistency["cross_layer"],
        "anchored_consistency": consistency["anchored"],
        "free_consistency": consistency["free"],
        "final_loss": metrics.get("recon_loss", 0.0),
        "anchor_loss": metrics.get("anchor_loss", 0.0),
        "dis_loss": metrics.get("dis_loss", 0.0),
        "pooled_std": metrics.get("pooled_std", 0.0),
        "training_time_sec": t1 - t0,
        "training_gain": training_gain,
        "_semantic_result": semantic_result,  # for report generation
    }


# =============================================================================
#  Report generation
# =============================================================================

def generate_report(results: list[dict]) -> None:
    """Generate comprehensive markdown report."""
    # Separate results by variant
    grouped = {}
    for r in results:
        v = r["variant"]
        grouped.setdefault(v, []).append(r)
    
    lines = []
    lines.append("# Phase 5 - Vector Semantics Investigation Report")
    lines.append("")
    lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Configuration
    lines.append("## Experiment Configuration")
    lines.append("")
    lines.append(f"- **Architecture**: P3-C (d={D}, d_out={D_OUT}), 1,600 params")
    lines.append(f"- **Training**: {EPOCHS} epochs, batch={BATCH_SIZE}, lr={LR}")
    lines.append(f"- **Base objective**: Reconstruction + pooled VICReg")
    lines.append(f"- **P5-B anchor**: lambda_anchor={LAMBDA_ANCHOR}, k={N_ANCHOR_DIMS}")
    lines.append(f"- **P5-C disentanglement**: beta={BETA_DISENTANGLE}")
    lines.append(f"- **Seeds**: {SEEDS}")
    lines.append(f"- **Semantic probes**: {PROBE_NAMES}")
    lines.append(f"- **Interpretability threshold**: |R| >= {R_THRESHOLD}, FDR q < {Q_THRESHOLD}")
    lines.append("")
    
    # Classification results
    lines.append("## Classification Accuracy")
    lines.append("")
    lines.append("| Variant | Mean Test Acc | Std |")
    lines.append("|---------|-------------:|----:|")
    for variant in VARIANTS + ["untrained"]:
        rows = grouped.get(variant, [])
        if rows:
            accs = [r["test_acc"] for r in rows]
            mean_a = np.mean(accs)
            std_a = np.std(accs, ddof=1) if len(accs) > 1 else 0.0
            lines.append(f"| {variant:9s} | {mean_a:.4f} | {std_a:.4f} |")
    lines.append("")
    
    # Consistency results
    lines.append("## Semantic Consistency Scores")
    lines.append("")
    lines.append("| Variant | Overall | Within-Layer | Cross-Layer |")
    lines.append("|---------|--------:|-------------:|------------:|")
    for variant in VARIANTS + ["untrained"]:
        rows = grouped.get(variant, [])
        if rows:
            overall = [r["overall_consistency"] for r in rows if not np.isnan(r["overall_consistency"])]
            within = [r["within_layer_consistency"] for r in rows if not np.isnan(r["within_layer_consistency"])]
            cross = [r["cross_layer_consistency"] for r in rows if not np.isnan(r["cross_layer_consistency"])]
            
            def fmt(vals):
                return f"{np.mean(vals):.3f}" if vals else "N/A"
            
            lines.append(f"| {variant:9s} | {fmt(overall)} | {fmt(within)} | {fmt(cross)} |")
    lines.append("")
    
    # P5-B anchored vs free
    lines.append("## P5-B Anchored vs Free Dimension Consistency")
    lines.append("")
    p5b_rows = grouped.get("P5-B", [])
    if p5b_rows:
        anchored = [r["anchored_consistency"] for r in p5b_rows if not np.isnan(r["anchored_consistency"])]
        free = [r["free_consistency"] for r in p5b_rows if not np.isnan(r["free_consistency"])]
        
        lines.append(f"- **Anchored dims (0-4)**: {np.mean(anchored):.3f}" if anchored else "- Anchored: N/A")
        lines.append(f"- **Free dims (5-15)**: {np.mean(free):.3f}" if free else "- Free: N/A")
        
        # Compare free-dim consistency to P5-A
        p5a_rows = grouped.get("P5-A", [])
        if p5a_rows:
            p5a_overall = [r["overall_consistency"] for r in p5a_rows if not np.isnan(r["overall_consistency"])]
            if p5a_overall and free:
                lines.append(f"- **P5-A overall for comparison**: {np.mean(p5a_overall):.3f}")
    lines.append("")
    
    # Training gain
    lines.append("## Training Gain (P5-A vs Untrained)")
    lines.append("")
    p5a_rows = grouped.get("P5-A", [])
    untrained_rows = grouped.get("untrained", [])
    if p5a_rows and untrained_rows:
        p5a_cons = [r["overall_consistency"] for r in p5a_rows if not np.isnan(r["overall_consistency"])]
        unt_cons = [r["overall_consistency"] for r in untrained_rows if not np.isnan(r["overall_consistency"])]
        if p5a_cons and unt_cons:
            gain = np.mean(p5a_cons) - np.mean(unt_cons)
            lines.append(f"- P5-A overall: {np.mean(p5a_cons):.3f}")
            lines.append(f"- Untrained overall: {np.mean(unt_cons):.3f}")
            lines.append(f"- **Training gain**: {gain:+.3f}")
    lines.append("")
    
    # Falsification criteria
    lines.append("## Falsification Criteria Evaluation")
    lines.append("")
    
    # Compute means for falsification
    p5a_overall = [r["overall_consistency"] for r in grouped.get("P5-A", []) if not np.isnan(r["overall_consistency"])]
    p5a_within = [r["within_layer_consistency"] for r in grouped.get("P5-A", []) if not np.isnan(r["within_layer_consistency"])]
    unt_overall = [r["overall_consistency"] for r in grouped.get("untrained", []) if not np.isnan(r["overall_consistency"])]
    p5b_accs = [r["test_acc"] for r in grouped.get("P5-B", [])]
    p5b_anchored = [r["anchored_consistency"] for r in grouped.get("P5-B", []) if not np.isnan(r["anchored_consistency"])]
    p5b_free = [r["free_consistency"] for r in grouped.get("P5-B", []) if not np.isnan(r["free_consistency"])]
    
    p5a_mean = np.mean(p5a_overall) if p5a_overall else 0.0
    p5a_within_mean = np.mean(p5a_within) if p5a_within else 0.0
    unt_mean = np.mean(unt_overall) if unt_overall else 0.0
    p5b_acc_mean = np.mean(p5b_accs) if p5b_accs else 0.0
    
    f1 = p5a_mean <= 0.30
    f2 = (p5a_mean - unt_mean) <= 0.05 if p5a_overall and unt_overall else True
    f3 = p5a_within_mean < 0.40
    f4 = p5b_acc_mean < 0.75
    f5_val = (np.mean(p5b_anchored) - p5a_mean) if p5b_anchored and p5a_overall else 0.0
    f5 = f5_val < 0.05
    
    lines.append("| Criterion | Description | Status | Detail |")
    lines.append("|-----------|-------------|--------|--------|")
    lines.append(f"| F1 | Overall consistency <= 0.30 | {'TRIGGERED' if f1 else 'PASS'} | P5-A = {p5a_mean:.3f} |")
    lines.append(f"| F2 | Training gain <= 0.05 | {'TRIGGERED' if f2 else 'PASS'} | Gain = {p5a_mean - unt_mean:+.3f} |")
    lines.append(f"| F3 | Within-layer consistency < 0.40 | {'TRIGGERED' if f3 else 'PASS'} | P5-A = {p5a_within_mean:.3f} |")
    lines.append(f"| F4 | P5-B accuracy < 75% | {'TRIGGERED' if f4 else 'PASS'} | P5-B = {p5b_acc_mean*100:.1f}% |")
    lines.append(f"| F5 | P5-B anchor improvement < 0.05 | {'TRIGGERED' if f5 else 'PASS'} | Improvement = {f5_val:+.3f} |")
    lines.append("")
    
    # R-squared heatmap summary
    lines.append("## R-squared Summary (Code Dimension x Semantic Axis)")
    lines.append("")
    lines.append("Average R-squared across all spatial positions, per layer:")
    lines.append("")
    for variant in VARIANTS + ["untrained"]:
        rows = grouped.get(variant, [])
        if not rows:
            continue
        lines.append(f"### {variant}")
        r_sq = rows[0]["_semantic_result"]["per_layer_r_squared"]
        for layer_key, matrix in r_sq.items():
            lines.append(f"\n**{layer_key}** (d x 5 probes):")
            header = "| dim | " + " | ".join(PROBE_NAMES) + " |"
            sep = "|-----|" + "|".join(["------" for _ in PROBE_NAMES]) + " |"
            lines.append(header)
            lines.append(sep)
            for j in range(min(16, matrix.shape[0])):
                vals = " | ".join(f"{matrix[j,pi]:.3f}" for pi in range(len(PROBE_NAMES)))
                lines.append(f"| {j:3d} | {vals} |")
        lines.append("")
    
    # Recommendation
    lines.append("## Summary and Recommendation")
    lines.append("")
    if not f1 and not f2 and not f3:
        lines.append("The primary hypothesis is **SUPPORTED**: code dimensions carry consistent, interpretable semantics.")
    else:
        lines.append("The primary hypothesis is **PARTIALLY REFUTED** or **REFUTED** based on falsification criteria.")
    lines.append("")
    
    if p5a_overall and p5a_within:
        lines.append(f"- P5-A overall consistency: {p5a_mean:.3f}")
        lines.append(f"- P5-A within-layer consistency: {p5a_within_mean:.3f}")
        lines.append(f"- Chance level: ~0.20")
    
    lines.append("")
    if p5b_accs:
        lines.append(f"- P5-B classification accuracy: {p5b_acc_mean*100:.1f}% (target >= 78%)")
    if p5b_anchored and p5b_free:
        lines.append(f"- P5-B anchored-dim consistency: {np.mean(p5b_anchored):.3f}")
        lines.append(f"- P5-B free-dim consistency: {np.mean(p5b_free):.3f}")
    
    # Write report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Report saved to {REPORT_MD}")


# =============================================================================
#  Main
# =============================================================================

def main(dry_run: bool = False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if os.path.exists(RESULTS_CSV) and not dry_run:
        os.remove(RESULTS_CSV)
    
    # Build task list
    tasks = []
    task_labels = []
    
    for variant in VARIANTS:
        seeds_to_use = [42] if dry_run else SEEDS
        ep = 1 if dry_run else EPOCHS
        for seed in seeds_to_use:
            tasks.append((variant, seed, ep))
            task_labels.append(f"{variant}_seed{seed}")
    
    # Untrained
    seeds_to_use = [42] if dry_run else SEEDS
    for seed in seeds_to_use:
        tasks.append(("untrained", seed, 1 if dry_run else EPOCHS))
        task_labels.append(f"UNTRAINED_seed{seed}")
    
    total_tasks = len(tasks)
    mode = "DRY-RUN" if dry_run else "FULL RUN"
    print("=" * 70)
    print(f"  PHASE 5 - Vector Semantics - {mode}")
    print(f"  Tasks: {total_tasks}")
    print(f"  Epochs: {1 if dry_run else EPOCHS}")
    print("=" * 70)
    
    t_start = time.time()
    all_results = []
    
    for i, task in enumerate(tasks):
        label = task_labels[i]
        print(f"  [{i+1}/{total_tasks}] {label}...", end=" ", flush=True)
        
        result = run_single_experiment(task)
        all_results.append(result)
        
        # Save to CSV (excluding _semantic_result)
        csv_result = {k: v for k, v in result.items() if not k.startswith("_")}
        file_exists = os.path.exists(RESULTS_CSV)
        fieldnames = [k for k in csv_result.keys()]
        with open(RESULTS_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(csv_result)
        
        gc.collect()
        elapsed = time.time() - t_start
        acc = result["test_acc"]
        cons = result["overall_consistency"]
        print(f"acc={acc:.4f}, consistency={cons:.3f if not np.isnan(cons) else 'N/A'} ({elapsed:.1f}s)")
    
    # Compute training gain
    p5a_cons = [r["overall_consistency"] for r in all_results if r["variant"] == "P5-A" and not np.isnan(r["overall_consistency"])]
    unt_cons = [r["overall_consistency"] for r in all_results if r["variant"] == "untrained" and not np.isnan(r["overall_consistency"])]
    if p5a_cons and unt_cons:
        training_gain = np.mean(p5a_cons) - np.mean(unt_cons)
        print(f"\n  Training gain (P5-A vs Untrained): {training_gain:+.3f}")
    
    # Generate report (only for full run)
    if not dry_run:
        generate_report(all_results)
    else:
        print("\n  Dry-run complete. No report generated for 1-epoch run.")
    
    # Quick summary
    print("\n  Summary:")
    for variant in VARIANTS + ["untrained"]:
        rows = [r for r in all_results if r["variant"] == variant]
        if rows:
            accs = [r["test_acc"] for r in rows]
            cons = [r["overall_consistency"] for r in rows if not np.isnan(r["overall_consistency"])]
            mean_a = np.mean(accs)
            mean_c = np.mean(cons) if cons else float("nan")
            print(f"    {variant:12s}: acc={mean_a:.4f}, consistency={mean_c:.3f if not np.isnan(mean_c) else 'N/A'}")
    
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
```

After writing this file, do:
1. Run `cd src && python run_phase5.py --dry-run` to verify it works. Fix any errors.
2. Then run `cd src && python run_phase5.py` for the full 20-experiment suite.
3. After completion, read phase_5/REPORT.md and report the key findings including: classification accuracy per variant, consistency scores, training gain, and all 5 falsification criteria outcomes.