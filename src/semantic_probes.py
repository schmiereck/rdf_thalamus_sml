"""
Semantic Probes for Phase 5 — Vector Semantics Investigation.

Computes 5 scalar semantic probe feature maps from raw (B, 16, 32) binary grids
and provides downsampling functions to match encoder layer resolutions.
"""

from __future__ import annotations

import numpy as np

PROBE_NAMES = ["magnitude", "gradient", "variance", "periodicity", "novelty"]


# ---------------------------------------------------------------------------
#  Individual probe computations
# ---------------------------------------------------------------------------

def _probe_magnitude(grid: np.ndarray) -> np.ndarray:
    """
    Local average activity in a 3x3 window.
    Spatial axis wraps modulo-16; temporal axis clamps at boundaries.
    """
    B, S, T = grid.shape
    out = np.zeros_like(grid, dtype=np.float64)
    for s in range(S):
        s_start = (s - 1) % S
        s_end = (s + 2) % S
        t_start = max(0, s - 1)  # not used — we handle per-t below
        # Build spatial slice with wrapping
        if s_start < s_end:
            s_slice = slice(s_start, s_end)
        else:
            # Wrap-around case
            pass
    
    # Vectorised approach
    for ds in range(-1, 2):
        s_src = (np.arange(S) + ds) % S
        for dt in range(-1, 2):
            t_src = np.clip(np.arange(T) + dt, 0, T - 1)
            # grid[:, s_src[:, None], t_src[None, :]] gives (B, S, T)
            out += grid[:, s_src[:, None], t_src[None, :]]
    out /= 9.0
    return out


def _probe_gradient(grid: np.ndarray) -> np.ndarray:
    """
    Right-minus-left spatial gradient with modulo-16 wrapping.
    mean(grid[(s+1)%16:(s+3)%16, t]) - mean(grid[(s-2)%16:s, t])
    """
    B, S, T = grid.shape
    out = np.zeros_like(grid, dtype=np.float64)
    
    for s in range(S):
        # Right window: positions (s+1)%S and (s+2)%S
        r1 = (s + 1) % S
        r2 = (s + 2) % S
        right_mean = (grid[:, r1, :] + grid[:, r2, :]) / 2.0
        
        # Left window: positions (s-2)%S and (s-1)%S
        l1 = (s - 2) % S
        l2 = (s - 1) % S
        left_mean = (grid[:, l1, :] + grid[:, l2, :]) / 2.0
        
        out[:, s, :] = right_mean - left_mean
    
    return out


def _probe_variance(grid: np.ndarray) -> np.ndarray:
    """
    Variance of grid[s, max(0,t-4):t+1] over the last 5 timesteps.
    If t < 4, use available timesteps. Variance of single element = 0.
    """
    B, S, T = grid.shape
    out = np.zeros_like(grid, dtype=np.float64)
    
    for t in range(T):
        t_start = max(0, t - 4)
        window = grid[:, :, t_start:t + 1]  # (B, S, n_steps)
        n_steps = t + 1 - t_start
        if n_steps <= 1:
            out[:, :, t] = 0.0
        else:
            out[:, :, t] = window.var(axis=2, ddof=0)
    
    return out


def _probe_periodicity(grid: np.ndarray) -> np.ndarray:
    """
    Autocorrelation at lag 2 of grid[s, max(0,t-7):t+1].
    Use at least 5 timesteps; if fewer, return 0.
    Pearson correlation between x and x_{lag=2}.
    """
    B, S, T = grid.shape
    out = np.zeros_like(grid, dtype=np.float64)
    
    for t in range(T):
        t_start = max(0, t - 7)
        n_steps = t + 1 - t_start
        if n_steps < 5:
            out[:, :, t] = 0.0
            continue
        
        window = grid[:, :, t_start:t + 1]  # (B, S, n_steps)
        x = window[:, :, :-2]   # (B, S, n_steps-2)
        y = window[:, :, 2:]    # (B, S, n_steps-2)
        
        # Pearson correlation per (b, s)
        mean_x = x.mean(axis=2, keepdims=True)
        mean_y = y.mean(axis=2, keepdims=True)
        dx = x - mean_x
        dy = y - mean_y
        
        num = (dx * dy).sum(axis=2)
        den = np.sqrt((dx ** 2).sum(axis=2) * (dy ** 2).sum(axis=2) + 1e-12)
        
        corr = num / den
        # Handle constant sequences
        corr = np.where(den < 1e-12, 0.0, corr)
        out[:, :, t] = corr
    
    return out


def _probe_novelty(grid: np.ndarray) -> np.ndarray:
    """
    |grid[s, t] - grid[s, max(0, t-1)]|.
    0 for t=0.
    """
    B, S, T = grid.shape
    out = np.zeros_like(grid, dtype=np.float64)
    
    out[:, :, 0] = 0.0
    if T > 1:
        out[:, :, 1:] = np.abs(grid[:, :, 1:] - grid[:, :, :-1])
    
    return out


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def compute_all_probes(grid: np.ndarray) -> dict:
    """
    Compute all 5 probe feature maps from raw (B, 16, 32) binary grid.
    Returns dict mapping probe_name -> (B, 16, 32) float array.
    """
    if grid.ndim == 2 and grid.shape[1] == 16 * 32:
        grid = grid.reshape(-1, 16, 32)
    
    return {
        "magnitude": _probe_magnitude(grid),
        "gradient": _probe_gradient(grid),
        "variance": _probe_variance(grid),
        "periodicity": _probe_periodicity(grid),
        "novelty": _probe_novelty(grid),
    }


# ---------------------------------------------------------------------------
#  Downsampling
# ---------------------------------------------------------------------------

def downsample_probes_spatial(probe_map: np.ndarray, layer_idx: int) -> np.ndarray:
    """
    Average probe values over the receptive field of each code position
    in spatial layer `layer_idx`.
    
    For spatial layer l, output shape is (B, 16 - 2*(l+1), 32).
    Position p covers input positions [p, p+1, ..., p+2*(l+1)].
    """
    B, S_in, T = probe_map.shape
    kernel_size = 2 * (layer_idx + 1) + 1
    S_out = S_in - 2 * (layer_idx + 1)
    
    out = np.zeros((B, S_out, T), dtype=np.float64)
    for p in range(S_out):
        window = probe_map[:, p:p + kernel_size, :]  # (B, kernel_size, T)
        out[:, p, :] = window.mean(axis=1)
    
    return out


def downsample_probes_temporal(probe_map: np.ndarray, layer_idx: int) -> np.ndarray:
    """
    Average probe values over the receptive field of each code position
    in temporal layer `layer_idx`.
    
    For temporal layer l, output has T_out = 32 - 2*(l+1) temporal positions.
    Position p covers input timesteps [p, p+1, ..., p+2*(l+1)].
    
    Also downsample spatial axis from 16 to 10 positions using average over
    [p, p+1, ..., p+6] for position p (7-position spatial receptive field).
    Boundary positions are clamped.
    """
    B, S_in, T_in = probe_map.shape
    assert S_in == 16, f"Expected S_in=16, got {S_in}"
    
    # First downsample spatial axis from 16 to 10
    S_out = 10
    spatial_down = np.zeros((B, S_out, T_in), dtype=np.float64)
    for p in range(S_out):
        s_end = min(p + 7, S_in)
        window = probe_map[:, p:s_end, :]  # (B, up_to_7, T_in)
        spatial_down[:, p, :] = window.mean(axis=1)
    
    # Then downsample temporal axis
    kernel_size = 2 * (layer_idx + 1) + 1
    T_out = T_in - 2 * (layer_idx + 1)
    
    out = np.zeros((B, T_out, S_out), dtype=np.float64)
    for p in range(T_out):
        window = spatial_down[:, :, p:p + kernel_size]  # (B, S_out, kernel_size)
        out[:, p, :] = window.mean(axis=2)
    
    return out


def downsample_probes(probe_maps: dict, n_spatial_layers: int = 3,
                      n_temporal_layers: int = 3) -> dict:
    """
    Downsample all probe maps to match encoder's layer resolutions.
    
    Returns dict with keys like 'spatial_0', 'spatial_1', 'spatial_2',
    'temporal_0', 'temporal_1', 'temporal_2'.
    Each value is a dict mapping probe_name -> (B, n_pos1, n_pos2) shaped array.
    For spatial: (B, S_l, 32)
    For temporal: (B, T_l, 10)
    """
    result = {}
    
    for l in range(n_spatial_layers):
        key = f"spatial_{l}"
        result[key] = {}
        for probe_name, probe_map in probe_maps.items():
            ds = downsample_probes_spatial(probe_map, l)
            result[key][probe_name] = ds
    
    for l in range(n_temporal_layers):
        key = f"temporal_{l}"
        result[key] = {}
        for probe_name, probe_map in probe_maps.items():
            ds = downsample_probes_temporal(probe_map, l)
            result[key][probe_name] = ds
    
    return result


# ---------------------------------------------------------------------------
#  Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  Semantic Probes -- Self-Test")
    print("=" * 65)
    
    rng = np.random.default_rng(42)
    B = 4
    grid = (rng.random((B, 16, 32)) < 0.5).astype(np.float64)
    
    probes = compute_all_probes(grid)
    
    for name, pmap in probes.items():
        assert pmap.shape == (B, 16, 32), f"Probe {name}: expected (4,16,32), got {pmap.shape}"
        assert not np.any(np.isnan(pmap)), f"Probe {name} contains NaN"
        print(f"  {name:12s}: shape={pmap.shape}, min={pmap.min():.4f}, max={pmap.max():.4f}, mean={pmap.mean():.4f}")
    
    # Test downsampling
    ds = downsample_probes(probes)
    
    for l in range(3):
        key = f"spatial_{l}"
        S_expected = 16 - 2 * (l + 1)
        for name, pmap in ds[key].items():
            assert pmap.shape == (B, S_expected, 32), f"{key}/{name}: expected (4,{S_expected},32), got {pmap.shape}"
        print(f"  {key}: shapes OK (S={S_expected})")
    
    for l in range(3):
        key = f"temporal_{l}"
        T_expected = 32 - 2 * (l + 1)
        for name, pmap in ds[key].items():
            assert pmap.shape == (B, T_expected, 10), f"{key}/{name}: expected (4,{T_expected},10), got {pmap.shape}"
        print(f"  {key}: shapes OK (T={T_expected})")
    
    print("\n  ALL SELF-TESTS PASSED")
    print("=" * 65)
