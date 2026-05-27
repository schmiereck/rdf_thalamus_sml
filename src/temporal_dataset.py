"""
Temporal Dataset Generator for Phase 2.

Generates three categories of temporal sequences (periodic, random, irregular)
and maps discrete states to fixed d-dimensional embeddings using Xavier-scaled
standard normal initialisation.

All sequences have length T=64 and embedding dimension d=16 by default.

Categories (3-class classification):
  0 = periodic    -- repeating patterns with periods 3, 4, 7, or 11
  1 = random      -- independent uniform draws from a small state set
  2 = irregular   -- Markov chains with slowly varying transition probabilities

Additionally generates a held-out *irregular Markov chain* dataset for next-step
prediction evaluation (same state space, different transition dynamics).
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
#  Embedding helpers
# ---------------------------------------------------------------------------

def make_state_embeddings(n_states: int, d: int, seed: int) -> np.ndarray:
    """
    Generate Xavier-scaled standard normal embeddings.

    Parameters
    ----------
    n_states : int
        Number of discrete states.
    d : int
        Embedding dimension.
    seed : int
        RNG seed.

    Returns
    -------
    embeddings : np.ndarray, shape (n_states, d)
    """
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_states, d)) * np.sqrt(2.0 / d)


# ---------------------------------------------------------------------------
#  Sequence generators
# ---------------------------------------------------------------------------

def _generate_periodic_sequences(
    n_samples: int,
    n_states: int,
    length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate periodic sequences over discrete states."""
    seqs = np.zeros((n_samples, length), dtype=np.int64)
    for i in range(n_samples):
        period = rng.choice([3, 4, 7, 11])
        base = np.arange(period) % n_states
        phase = rng.integers(0, period)
        for t in range(length):
            seqs[i, t] = base[(t + phase) % period]
    return seqs


def _generate_random_sequences(
    n_samples: int,
    n_states: int,
    length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate random i.i.d. sequences."""
    return rng.integers(0, n_states, size=(n_samples, length))


def _generate_irregular_sequences(
    n_samples: int,
    n_states: int,
    length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate irregular Markov sequences with slowly varying transition probs."""
    seqs = np.zeros((n_samples, length), dtype=np.int64)
    for i in range(n_samples):
        # Time-varying transition matrix: slowly drift between two matrices
        P0 = _stochastic_matrix(n_states, rng)
        P1 = _stochastic_matrix(n_states, rng)
        state = rng.integers(0, n_states)
        for t in range(length):
            alpha = t / max(length - 1, 1)
            # Interpolate kernels (pointwise) and renormalise
            P = (1 - alpha) * P0 + alpha * P1
            P /= P.sum(axis=1, keepdims=True)
            state = rng.choice(n_states, p=P[state])
            seqs[i, t] = state
    return seqs


def _stochastic_matrix(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a random row-stochastic matrix."""
    M = rng.random((n, n))
    M /= M.sum(axis=1, keepdims=True)
    return M


# ---------------------------------------------------------------------------
#  Main dataset builder
# ---------------------------------------------------------------------------

def generate_temporal_dataset(
    n_train_per_cat: int = 200,
    n_test_per_cat: int = 100,
    length: int = 64,
    d: int = 16,
    n_states: int = 8,
    seed: int = 42,
) -> dict:
    """
    Build the Phase-2 temporal classification dataset.

    Parameters
    ----------
    n_train_per_cat : int
        Training samples per category.
    n_test_per_cat : int
        Testing samples per category.
    length : int
        Sequence length (T).
    d : int
        Embedding dimension.
    n_states : int
        Number of discrete states.
    seed : int
        Master RNG seed.

    Returns
    -------
    dict with keys:
        'train_seqs'   : np.ndarray, shape (n_train, length) -- discrete state indices
        'train_emb'    : np.ndarray, shape (n_train, length, d) -- embeddings
        'train_y'      : np.ndarray, shape (n_train,) -- class labels {0,1,2}
        'test_seqs'    : np.ndarray, shape (n_test, length)
        'test_emb'     : np.ndarray, shape (n_test, length, d)
        'test_y'       : np.ndarray, shape (n_test,)
        'embeddings'   : np.ndarray, shape (n_states, d) -- state embedding table
    """
    rng = np.random.default_rng(seed)
    embeddings = make_state_embeddings(n_states, d, seed)

    # -- Training sequences --
    train_periodic = _generate_periodic_sequences(n_train_per_cat, n_states, length, rng)
    train_random = _generate_random_sequences(n_train_per_cat, n_states, length, rng)
    train_irregular = _generate_irregular_sequences(n_train_per_cat, n_states, length, rng)

    train_seqs = np.vstack([train_periodic, train_random, train_irregular])
    train_y = np.repeat(np.arange(3), n_train_per_cat)
    train_emb = embeddings[train_seqs]

    # -- Test sequences --
    test_periodic = _generate_periodic_sequences(n_test_per_cat, n_states, length, rng)
    test_random = _generate_random_sequences(n_test_per_cat, n_states, length, rng)
    test_irregular = _generate_irregular_sequences(n_test_per_cat, n_states, length, rng)

    test_seqs = np.vstack([test_periodic, test_random, test_irregular])
    test_y = np.repeat(np.arange(3), n_test_per_cat)
    test_emb = embeddings[test_seqs]

    return {
        "train_seqs": train_seqs,
        "train_emb": train_emb,
        "train_y": train_y,
        "test_seqs": test_seqs,
        "test_emb": test_emb,
        "test_y": test_y,
        "embeddings": embeddings,
    }


# ---------------------------------------------------------------------------
#  Held-out irregular Markov dataset for next-step prediction
# ---------------------------------------------------------------------------

def generate_irregular_markov_dataset(
    n_train: int = 200,
    n_test: int = 100,
    length: int = 64,
    d: int = 16,
    n_states: int = 8,
    seed: int = 42,
) -> dict:
    """
    Generate a held-out irregular Markov dataset for next-step prediction.
    Uses DIFFERENT transition dynamics than the classification Markov generator.

    Parameters
    ----------
    n_train : int
        Number of training sequences.
    n_test : int
        Number of testing sequences.
    length : int
        Sequence length.
    d : int
        Embedding dimension.
    n_states : int
        Number of discrete states.
    seed : int
        RNG seed.

    Returns
    -------
    dict with keys:
        'train_seqs', 'train_emb', 'test_seqs', 'test_emb', 'embeddings'
    """
    rng = np.random.default_rng(seed + 999)  # different seed offset
    embeddings = make_state_embeddings(n_states, d, seed + 999)

    train_seqs = _generate_irregular_sequences_v2(n_train, n_states, length, rng)
    test_seqs = _generate_irregular_sequences_v2(n_test, n_states, length, rng)

    return {
        "train_seqs": train_seqs,
        "train_emb": embeddings[train_seqs],
        "test_seqs": test_seqs,
        "test_emb": embeddings[test_seqs],
        "embeddings": embeddings,
    }


def _generate_irregular_sequences_v2(
    n_samples: int,
    n_states: int,
    length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Different irregular dynamics: periodic switching between 3 regimes."""
    seqs = np.zeros((n_samples, length), dtype=np.int64)
    for i in range(n_samples):
        # Three distinct regimes
        regimes = [_stochastic_matrix(n_states, rng) for _ in range(3)]
        regime_period = rng.choice([10, 15, 20])
        state = rng.integers(0, n_states)
        for t in range(length):
            regime_idx = (t // regime_period) % 3
            P = regimes[regime_idx]
            state = rng.choice(n_states, p=P[state])
            seqs[i, t] = state
    return seqs


# ---------------------------------------------------------------------------
#  Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Temporal Dataset -- Self-Test")
    print("=" * 60)

    ds = generate_temporal_dataset(seed=42)
    print(f"  Train sequences: {ds['train_seqs'].shape}")
    print(f"  Train embeddings: {ds['train_emb'].shape}")
    print(f"  Train labels: {ds['train_y'].shape}")
    print(f"  Test sequences: {ds['test_seqs'].shape}")
    print(f"  Test embeddings: {ds['test_emb'].shape}")
    print(f"  Test labels: {ds['test_y'].shape}")
    print(f"  Embedding table: {ds['embeddings'].shape}")

    # Sanity checks
    assert ds["train_seqs"].shape == (600, 64)
    assert ds["train_emb"].shape == (600, 64, 16)
    assert ds["train_y"].shape == (600,)
    assert set(np.unique(ds["train_y"])) == {0, 1, 2}
    assert ds["embeddings"].shape == (8, 16)

    # Verify embedding lookup
    for i in range(8):
        mask = ds["train_seqs"] == i
        if mask.any():
            emb_vals = ds["train_emb"][mask]
            assert np.allclose(emb_vals, ds["embeddings"][i])
    print("  Embedding lookup consistency: PASS")

    # Held-out dataset
    markov = generate_irregular_markov_dataset(seed=42)
    assert markov["train_seqs"].shape == (200, 64)
    assert markov["test_seqs"].shape == (100, 64)
    print("  Held-out Markov dataset: PASS")

    print("\n  ALL SELF-TESTS PASSED")
    print("=" * 60)
