"""
Spatiotemporal Dataset Generator for Phase 3.

Generates four categories of spatiotemporal sequences on a 16x32 binary grid
(16 spatial positions x 32 timesteps). Designed so that shortcut baselines
(single-frame and temporal-average projections) achieve at-chance performance,
forcing the model to reason about temporal dynamics.

Classes (4-class classification):
    0 = moving_blob       -- blob position follows a LINEAR trajectory (wrapped mod 16)
    1 = expanding_blob    -- blob width oscillates periodically in place (wrapped mod 16)
    2 = periodic_st       -- blob position oscillates back-and-forth sinusoidally (wrapped mod 16)
    3 = object_permanence -- blob stays put (wrapped mod 16), disappears for some steps

CRITICAL design property: all four classes draw their initial spatial position
from the SAME distribution (uniformly 0..15) and their base blob width from
the SAME distribution (uniformly 2..4).  The CLASS label is encoded ONLY in
the TEMPORAL TRAJECTORY of the blob.  Consequently:
  - The marginal spatial distribution per-frame is IDENTICAL across classes
  - The temporal-average profile is nearly identical across classes
  - The only signal is the temporal correlation structure between frames

ALL generators use MODULO-16 WRAPPING for positions, so the spatial marginal
is truly uniform and there is NO boundary/bias signal for shortcut baselines.
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
#  Blob drawing helper with modulo-16 wrapping
# ---------------------------------------------------------------------------

def _draw_wrapped_blob(
    seq: np.ndarray,          # shape (S, T), float array
    t: int,
    centre: int,
    width: int,
    n_spatial: int = N_SPATIAL,
) -> None:
    """
    Draw a blob of given *width* centred at *centre* (mod n_spatial) into
    ``seq[:, t]``, handling wrap-around via modulo arithmetic.

    Parameters
    ----------
    seq : np.ndarray, shape (S, T)
        The spatiotemporal grid (written in-place).
    t : int
        Timestep index.
    centre : int
        Centre pixel position (will be taken mod n_spatial).
    width : int
        Full width of the blob in pixels.
    n_spatial : int
        Number of spatial positions (default N_SPATIAL = 16).
    """
    half_w = width // 2
    c = centre % n_spatial

    # The blob covers positions [c - half_w, ..., c - half_w + width - 1] mod S
    for offset in range(width):
        pos = (c - half_w + offset) % n_spatial
        seq[pos, t] = 1.0


# ---------------------------------------------------------------------------
#  Sequence generators: each returns  (n_samples, S, T)  float arrays
# ---------------------------------------------------------------------------

def _generate_moving_blob(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 0 -- A blob whose CENTRE follows a LINEAR trajectory across space,
    wrapped modulo 16.

    Starting position: uniform 0..15
    Base width: uniform 2..4
    Direction: random (left or right)
    Speed: random integer 1..3 per timestep
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(0, N_SPATIAL)            # uniform 0..15
        blob_width = rng.integers(2, 5)                  # 2, 3, or 4
        direction = rng.choice([-1, 1])                  # left or right
        speed = rng.integers(1, 4)                      # 1, 2, or 3 pixels/step

        for t in range(N_TIMESTEPS):
            x = int((start_x + direction * speed * t) % N_SPATIAL)
            _draw_wrapped_blob(seqs[i], t, x, blob_width)
    return seqs


def _generate_expanding_blob(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 1 -- A blob centred at a FIXED spatial position (mod 16), but its
    WIDTH periodically oscillates.

    Starting position (centre): uniform 0..15
    Base width: uniform 2..4
    Oscillation: sinusoidal with period and amplitude chosen randomly.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        centre = rng.integers(0, N_SPATIAL)              # uniform 0..15
        base_width = rng.integers(2, 5)                  # 2, 3, or 4
        period = rng.choice([8, 12, 16])
        amplitude = rng.integers(1, 3)                   # ±1..2 additional half-width

        for t in range(N_TIMESTEPS):
            phase = 2 * np.pi * t / period
            # Width oscillates around base_width
            w = base_width + amplitude * np.sin(phase)
            w = max(1, round(w))                         # min width 1, max ~base+amplitude
            w = min(w, N_SPATIAL)                        # cap at N_SPATIAL
            _draw_wrapped_blob(seqs[i], t, centre, w)
    return seqs


def _generate_periodic_spatiotemporal(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 2 -- A blob whose centre OSCILLATES back-and-forth sinusoidally,
    with the centre position wrapped modulo 16.

    Starting position: uniform 0..15
    Base width: uniform 2..4
    Centre trajectory: centre(t) = (start_x + round(amplitude * sin(2*pi*t/period))) mod 16
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        start_x = rng.integers(0, N_SPATIAL)             # uniform 0..15
        blob_width = rng.integers(2, 5)                  # 2, 3, or 4
        period = rng.choice([8, 12, 16, 20])
        amplitude = rng.integers(2, 6)                   # oscillation range 2..5 pixels

        for t in range(N_TIMESTEPS):
            phase = 2 * np.pi * t / period
            displacement = round(amplitude * np.sin(phase))
            x = int((start_x + displacement) % N_SPATIAL)
            _draw_wrapped_blob(seqs[i], t, x, blob_width)
    return seqs


def _generate_object_permanence(
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Class 3 -- A blob that stays in one place (mod 16), then VANISHES for a
    contiguous block of timesteps (the "occlusion" phase), then REAPPEARS at
    the same location.

    Starting position: uniform 0..15
    Base width: uniform 2..4
    Occlusion: random start frame and random duration.  Outside the occlusion
    window the blob is fully visible at the same position.
    """
    seqs = np.zeros((n_samples, N_SPATIAL, N_TIMESTEPS), dtype=np.float64)
    for i in range(n_samples):
        centre = rng.integers(0, N_SPATIAL)              # uniform 0..15
        blob_width = rng.integers(2, 5)                  # 2, 3, or 4
        hide_start = rng.integers(5, 18)                 # occlusion begins between t=5..17
        hide_duration = rng.integers(5, 16)              # occlusion lasts 5..15 frames
        hide_end = min(hide_start + hide_duration, N_TIMESTEPS)

        for t in range(N_TIMESTEPS):
            if hide_start <= t < hide_end:
                # Occluded: blob is invisible (do nothing)
                continue
            _draw_wrapped_blob(seqs[i], t, centre, blob_width)
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
