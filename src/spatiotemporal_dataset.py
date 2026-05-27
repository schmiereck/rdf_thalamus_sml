"""
Spatiotemporal Dataset Generator for Phase 3.

Generates four categories of spatiotemporal sequences on a 16x32 binary grid
(16 spatial positions x 32 timesteps). Designed so that shortcut baselines
(single-frame and temporal-average projections) achieve at-chance performance,
forcing the model to reason about temporal dynamics.

Classes (4-class classification):
    0 = moving_blob       -- blob position follows a LINEAR trajectory
    1 = expanding_blob    -- blob width oscillates periodically in place
    2 = periodic_st       -- blob position oscillates back-and-forth sinusoidally
    3 = object_permanence -- blob stays put, vanishes then reappears at same spot

CRITICAL design property: all four classes draw their initial spatial position
and blob width from the SAME distribution.  The CLASS label is encoded ONLY in
the TEMPORAL TRAJECTORY of the blob.  Consequently:
  - The marginal spatial distribution per-frame is identical across classes
  - The temporal-average profile is nearly identical across classes
  - The only signal is the temporal correlation structure between frames

Shortcut baselines:
    - single_frame : classify based on a single timestep -> ~25% (chance)
    - temporal_avg : classify based on the mean over all timesteps -> ~25% (chance)
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

N_SPATIAL = 16       # number of spatial positions (S)
N_TIMESTEPS = 32     # number of timesteps (T)
N_PIXELS = N_SPATIAL * N_TIMESTEPS  # flattened length = 512

N_TRAIN_PER_CLASS = 500
N_TEST_PER_CLASS = 200
NOISE_FLIP_PROB = 0.10

N_CLASSES = 4


# ---------------------------------------------------------------------------
#  Noise helper
# ---------------------------------------------------------------------------

def _add_noise(grid: np.ndarray, flip_prob: float, rng: np.random.Generator) -> np.ndarray:
    """Flip each pixel independently with probability *flip_prob*."""
    mask = rng.random(grid.shape) < flip_prob
    noisy = grid.copy()
    noisy[mask] = 1.0 - noisy[mask]
    return noisy


# ---------------------------------------------------------------------------
#  Sequence generators: each returns  (n_samples, S, T)  float arrays
# ---------------------------------------------------------------------------

def _generate_moving_blob(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 0 -- A blob whose CENTRE follows a LINEAR trajectory across space.
    start_x and blob_width are sampled identically to ALL other classes.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(2, N_SPATIAL - 2)
        blob_width = rng.integers(2, 5)  # 2, 3, or 4 pixels
        # Random direction: left (-1) or right (+1), with speed
        direction = rng.choice([-1.0, 1.0])
        speed = rng.integers(0, 3) + 1   # 1-3 pixels per 32 timesteps total shift

        for t in range(N_TIMESTEPS):
            x = round(start_x + direction * speed * t / (N_TIMESTEPS - 1))
            x = np.clip(x, blob_width // 2, N_SPATIAL - blob_width + blob_width // 2)
            lo = np.clip(x - blob_width // 2, 0, N_SPATIAL)
            hi = np.clip(lo + blob_width, 0, N_SPATIAL)
            seqs[i, lo:hi, t] = 1.0
    return seqs


def _generate_expanding_blob(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 1 -- A blob centred at a FIXED spatial position, but its WIDTH
    periodically EXPANDS and CONTRACTS sinusoidally.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(2, N_SPATIAL - 2)
        blob_width = rng.integers(2, 5)
        period = rng.choice([8, 12, 16])
        base_half_w = blob_width // 2
        amplitude = rng.integers(1, 4)  # half-width oscillation range

        for t in range(N_TIMESTEPS):
            phase = (t % period) / period
            half_w = max(1, round(base_half_w + amplitude * (0.5 + 0.5 * np.sin(2 * np.pi * phase))))
            half_w = min(half_w, N_SPATIAL // 2)
            lo = np.clip(start_x - half_w, 0, N_SPATIAL)
            hi = np.clip(start_x + half_w + 1, 0, N_SPATIAL)
            seqs[i, lo:hi, t] = 1.0
    return seqs


def _generate_periodic_spatiotemporal(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 2 -- A blob whose centre OSCILLATES back-and-forth sinusoidally.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(2, N_SPATIAL - 2)
        blob_width = rng.integers(2, 5)
        period = rng.choice([6, 8, 10, 12, 14, 16])
        amplitude = rng.integers(1, min(4, N_SPATIAL // 4))

        for t in range(N_TIMESTEPS):
            phase = 2 * np.pi * t / period
            x = round(start_x + amplitude * np.sin(phase))
            x = np.clip(x, blob_width // 2, N_SPATIAL - blob_width + blob_width // 2)
            lo = np.clip(x - blob_width // 2, 0, N_SPATIAL)
            hi = np.clip(lo + blob_width, 0, N_SPATIAL)
            seqs[i, lo:hi, t] = 1.0
    return seqs


def _generate_object_permanence(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 3 -- A blob that stays in one place, then VANISHES for a period
    (the "occlusion" phase), then REAPPEARS at the same location.
    The temporal structure is a step function in brightness, not position.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(2, N_SPATIAL - 2)
        blob_width = rng.integers(2, 5)
        # Occlusion boundaries: varies per sample
        hide_start = rng.integers(8, 16)
        hide_end = hide_start + rng.integers(6, 14)
        hide_end = min(hide_end, N_TIMESTEPS)

        for t in range(N_TIMESTEPS):
            if hide_start <= t < hide_end:
                # Occluded: blob is invisible
                continue
            lo = np.clip(start_x - blob_width // 2, 0, N_SPATIAL)
            hi = np.clip(lo + blob_width, 0, N_SPATIAL)
            seqs[i, lo:hi, t] = 1.0
    return seqs


# ---------------------------------------------------------------------------
#  Main dataset builder
# ---------------------------------------------------------------------------

def generate_spatiotemporal_dataset(
    n_train_per_class: int = N_TRAIN_PER_CLASS,
    n_test_per_class: int = N_TEST_PER_CLASS,
    noise_flip_prob: float = NOISE_FLIP_PROB,
    seed: int = 42,
) -> dict:
    """
    Build the Phase-3 spatiotemporal classification dataset.

    Parameters
    ----------
    n_train_per_class : int
        Training samples per class.
    n_test_per_class : int
        Testing samples per class.
    noise_flip_prob : float
        Per-pixel flip probability.
    seed : int
        Master RNG seed.

    Returns
    -------
    dict with keys:
        'train_x'   : np.ndarray, shape (n_train, S*T) -- flattened binary grids
        'train_y'   : np.ndarray, shape (n_train,) -- class labels {0,1,2,3}
        'test_x'    : np.ndarray, shape (n_test, S*T)
        'test_y'    : np.ndarray, shape (n_test,)
        'train_grid': np.ndarray, shape (n_train, S, T) -- original 2-D form
        'test_grid' : np.ndarray, shape (n_test, S, T)
    """
    rng = np.random.default_rng(seed)

    generators = [
        _generate_moving_blob,
        _generate_expanding_blob,
        _generate_periodic_spatiotemporal,
        _generate_object_permanence,
    ]

    n_train_total = N_CLASSES * n_train_per_class
    n_test_total = N_CLASSES * n_test_per_class

    # -- Training set --
    train_grids: list[np.ndarray] = []
    train_labels: list[np.ndarray] = []
    for cls_idx, gen in enumerate(generators):
        grid = gen(n_train_per_class, rng)
        grid = _add_noise(grid, noise_flip_prob, rng)
        train_grids.append(grid)
        train_labels.append(np.full(n_train_per_class, cls_idx, dtype=np.int64))

    train_x = np.vstack([g.reshape(n_train_per_class, N_PIXELS) for g in train_grids])
    train_y = np.concatenate(train_labels)

    # -- Test set --
    test_grids: list[np.ndarray] = []
    test_labels: list[np.ndarray] = []
    for cls_idx, gen in enumerate(generators):
        grid = gen(n_test_per_class, rng)
        grid = _add_noise(grid, noise_flip_prob, rng)
        test_grids.append(grid)
        test_labels.append(np.full(n_test_per_class, cls_idx, dtype=np.int64))

    test_x = np.vstack([g.reshape(n_test_per_class, N_PIXELS) for g in test_grids])
    test_y = np.concatenate(test_labels)

    train_grid_all = np.concatenate(train_grids, axis=0)
    test_grid_all = np.concatenate(test_grids, axis=0)

    return {
        "train_x": train_x,
        "train_y": train_y,
        "test_x": test_x,
        "test_y": test_y,
        "train_grid": train_grid_all,
        "test_grid": test_grid_all,
    }


# ---------------------------------------------------------------------------
#  Shortcut baseline evaluators
# ---------------------------------------------------------------------------

def evaluate_single_frame_baseline(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    test_y: np.ndarray,
    frame_idx: int = 8,
) -> dict:
    """
    Evaluate the single-frame shortcut baseline.

    Uses only one timestep (frame_idx) of the spatiotemporal input as the
    feature vector for logistic regression.

    Parameters
    ----------
    train_x : np.ndarray, shape (n_train, S*T)
    train_y : np.ndarray, shape (n_train,)
    test_x  : np.ndarray, shape (n_test, S*T)
    test_y  : np.ndarray, shape (n_test,)
    frame_idx : int -- 0-based timestep index to extract.

    Returns
    -------
    dict with keys 'train_acc', 'test_acc', 'n_samples_train', 'n_samples_test'.
    """
    from harness import SimpleLogisticRegression

    n_train = train_x.shape[0]
    n_test = test_x.shape[0]

    def extract_frame(X: np.ndarray) -> np.ndarray:
        return X.reshape(-1, N_SPATIAL, N_TIMESTEPS)[:, :, frame_idx]

    X_train = extract_frame(train_x)
    X_test = extract_frame(test_x)

    n_classes = N_CLASSES
    n_features = N_SPATIAL

    model = SimpleLogisticRegression(n_classes, n_features, lr=0.1, max_iter=2000, seed=42)
    model.fit(X_train, train_y)

    train_acc = model.score(X_train, train_y)
    test_acc = model.score(X_test, test_y)

    return {
        "train_acc": train_acc,
        "test_acc": test_acc,
        "n_samples_train": n_train,
        "n_samples_test": n_test,
    }


def evaluate_temporal_average_baseline(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    test_y: np.ndarray,
) -> dict:
    """
    Evaluate the temporal-average shortcut baseline.

    Averages over all 32 timesteps to produce a single (S,) feature vector
    per sample, then applies logistic regression.

    Parameters
    ----------
    train_x : np.ndarray, shape (n_train, S*T)
    train_y : np.ndarray, shape (n_train,)
    test_x  : np.ndarray, shape (n_test, S*T)
    test_y  : np.ndarray, shape (n_test,)

    Returns
    -------
    dict with keys 'train_acc', 'test_acc', 'n_samples_train', 'n_samples_test'.
    """
    from harness import SimpleLogisticRegression

    n_train = train_x.shape[0]
    n_test = test_x.shape[0]

    def temporal_average(X: np.ndarray) -> np.ndarray:
        return X.reshape(-1, N_SPATIAL, N_TIMESTEPS).mean(axis=2)

    X_train = temporal_average(train_x)
    X_test = temporal_average(test_x)

    n_classes = N_CLASSES
    n_features = N_SPATIAL

    model = SimpleLogisticRegression(n_classes, n_features, lr=0.1, max_iter=2000, seed=42)
    model.fit(X_train, train_y)

    train_acc = model.score(X_train, train_y)
    test_acc = model.score(X_test, test_y)

    return {
        "train_acc": train_acc,
        "test_acc": test_acc,
        "n_samples_train": n_train,
        "n_samples_test": n_test,
    }


def evaluate_all_shortcut_baselines(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    test_y: np.ndarray,
    frames_to_test: list[int] | None = None,
) -> dict:
    """
    Run all shortcut baseline evaluations and return a summary.

    Parameters
    ----------
    train_x, train_y, test_x, test_y : as returned by generate_spatiotemporal_dataset.
    frames_to_test : list of frame indices to try for single-frame baseline
                     (default: [0, 8, 16, 24, 31]).

    Returns
    -------
    dict summarising all baseline accuracies.
    """
    if frames_to_test is None:
        frames_to_test = [0, 8, 16, 24, 31]

    results = {}

    # Temporal average
    avg = evaluate_temporal_average_baseline(train_x, train_y, test_x, test_y)
    results["temporal_average"] = avg

    # Single frame for each requested frame index
    for f in frames_to_test:
        sf = evaluate_single_frame_baseline(train_x, train_y, test_x, test_y, frame_idx=f)
        results[f"single_frame_t{f}"] = sf

    return results


# ---------------------------------------------------------------------------
#  Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  Spatiotemporal Dataset -- Self-Test")
    print("=" * 65)

    # 1. Generate dataset
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
        noise_flip_prob=NOISE_FLIP_PROB,
        seed=42,
    )
    n_train_total = N_CLASSES * N_TRAIN_PER_CLASS
    n_test_total = N_CLASSES * N_TEST_PER_CLASS

    assert ds["train_x"].shape == (n_train_total, N_PIXELS), \
        f"Expected train_x ({n_train_total}, {N_PIXELS}), got {ds['train_x'].shape}"
    assert ds["test_x"].shape == (n_test_total, N_PIXELS), \
        f"Expected test_x ({n_test_total}, {N_PIXELS}), got {ds['test_x'].shape}"
    assert ds["train_y"].shape == (n_train_total,)
    assert ds["test_y"].shape == (n_test_total,)
    assert ds["train_grid"].shape == (n_train_total, N_SPATIAL, N_TIMESTEPS)
    assert ds["test_grid"].shape == (n_test_total, N_SPATIAL, N_TIMESTEPS)
    assert set(np.unique(ds["train_y"])) == {0, 1, 2, 3}
    assert set(np.unique(ds["test_y"])) == {0, 1, 2, 3}
    print(f"  [OK] train_x: {ds['train_x'].shape}   test_x: {ds['test_x'].shape}")
    print(f"  [OK] train_grid: {ds['train_grid'].shape}   test_grid: {ds['test_grid'].shape}")
    print(f"  [OK] Labels: train={set(ds['train_y'].tolist())}  test={set(ds['test_y'].tolist())}")

    # 2. Verify binary values (0/1 after noise)
    assert set(np.unique(ds["train_x"])).issubset({0.0, 1.0}), "train_x not binary!"
    assert set(np.unique(ds["test_x"])).issubset({0.0, 1.0}), "test_x not binary!"
    print(f"  [OK] Binary values confirmed")

    # 3. Evaluate shortcut baselines
    print("\n  Evaluating shortcut baselines ...")
    results = evaluate_all_shortcut_baselines(
        ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"],
    )

    all_pass = True
    for name, res in results.items():
        test_acc = res["test_acc"]
        status = "PASS" if test_acc <= 0.50 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {name:30s}  train={res['train_acc']:.4f}  test={test_acc:.4f}")

    print()
    if all_pass:
        print("  ALL BASELINES <= 50% test accuracy -- GOOD")
    else:
        print("  WARNING: some baselines > 50% -- may need stronger randomisation")

    print("=" * 65)
    if all_pass:
        print("  ALL SELF-TESTS PASSED")
    else:
        print("  SELF-TESTS FAILED -- baselines exceed 50%")
    print("=" * 65)
