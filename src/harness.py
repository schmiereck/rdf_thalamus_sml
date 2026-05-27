"""
HSUN Phase 0 — Experimental Harness

Dataset generator, similarity evaluator, encoder interface, and utility functions
for the smoke-test of hierarchical sparse universal nodes.

Dependencies: numpy, scipy only — no external ML libraries.
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import spearmanr


# ---------------------------------------------------------------------------
# Dataset Generator
# ---------------------------------------------------------------------------

class DatasetGenerator:
    """
    Generates the Phase 0 dataset:
      - 8 base states: all 3-bit binary tuples (0,0,0) … (1,1,1)
      - 10 noise variants per base state (bit-flip prob 0.1)
      - Total: 88 samples
    """

    NUM_BITS = 3
    NOISE_VARIANTS_PER_STATE = 10
    FLIP_PROB = 0.1

    def __init__(self, seed: int | None = None) -> None:
        self.rng = np.random.default_rng(seed)

    @property
    def base_states(self) -> np.ndarray:
        """Return the 8 canonical 3-bit states as an (8, 3) array."""
        states = np.array(
            list(itertools.product([0, 1], repeat=self.NUM_BITS)), dtype=np.float64
        )
        return states

    def _noisy_variants(self, state: np.ndarray, n: int) -> np.ndarray:
        """Generate n noise variants of a single state by flipping bits."""
        flip_mask = self.rng.random((n, self.NUM_BITS)) < self.FLIP_PROB
        variants = state.astype(np.float64) + flip_mask.astype(np.float64)
        variants = np.mod(variants, 2)
        return variants

    def get_base_states(self) -> np.ndarray:
        """Return just the 8 base states — shape (8, 3)."""
        return self.base_states.copy()

    def get_all_samples(self) -> np.ndarray:
        """Return all 88 samples — shape (88, 3)."""
        base = self.base_states
        samples: List[np.ndarray] = [base.copy()]
        for i in range(base.shape[0]):
            variants = self._noisy_variants(base[i], self.NOISE_VARIANTS_PER_STATE)
            samples.append(variants)
        return np.vstack(samples)


# ---------------------------------------------------------------------------
# Similarity Evaluator
# ---------------------------------------------------------------------------

class SimilarityEvaluator:
    """
    Computes pairwise input inverse Hamming distance and pairwise code
    cosine similarity for the 8 base states, then calculates Spearman ρ
    STRICTLY on off-diagonal (distinct) pairs.
    """

    @staticmethod
    def pairwise_hamming(states: np.ndarray) -> np.ndarray:
        """Return an (N, N) matrix of Hamming distances between binary states."""
        n = states.shape[0]
        dist = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(i + 1, n):
                d = np.sum(states[i] != states[j])
                dist[i, j] = d
                dist[j, i] = d
        return dist

    @staticmethod
    def inverse_hamming(hamming: np.ndarray) -> np.ndarray:
        """Return 1 / (1 + hamming_distance)."""
        return 1.0 / (1.0 + hamming)

    @staticmethod
    def pairwise_cosine(codes: np.ndarray) -> np.ndarray:
        """Return an (N, N) matrix of cosine similarities between code vectors."""
        norms = np.linalg.norm(codes, axis=1, keepdims=True)
        # Guard against zero-norm vectors
        norms = np.where(norms < 1e-12, 1.0, norms)
        normalized = codes / norms
        return normalized @ normalized.T

    @classmethod
    def evaluate(
        cls, states: np.ndarray, codes: np.ndarray
    ) -> Tuple[float, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Spearman ρ on OFF-DIAGONAL pairs between code cosine similarity
        and input inverse Hamming distance.

        Parameters
        ----------
        states : np.ndarray, shape (N, 3)
            The base input states (typically 8).
        codes : np.ndarray, shape (N, dim_out)
            The encoded codes for the base states.

        Returns
        -------
        spearman_rho : float
            Spearman rank correlation (off-diagonal only).
        p_value : float
            Two-sided p-value from spearmanr.
        inv_ham_pairs : np.ndarray
            Flattened inverse Hamming distances (off-diagonal).
        cos_sim_pairs : np.ndarray
            Flattened cosine similarities (off-diagonal).
        row_indices : np.ndarray
            Row indices for each off-diagonal pair.
        col_indices : np.ndarray
            Column indices for each off-diagonal pair.
        """
        assert states.shape[0] == codes.shape[0], (
            f"states ({states.shape[0]}) and codes ({codes.shape[0]}) must match"
        )

        ham_dist = cls.pairwise_hamming(states)
        inv_ham = cls.inverse_hamming(ham_dist)
        cos_sim = cls.pairwise_cosine(codes)

        n = states.shape[0]
        # Extract upper-triangle indices (off-diagonal)
        row_indices, col_indices = np.triu_indices(n, k=1)

        inv_ham_pairs = inv_ham[row_indices, col_indices]
        cos_sim_pairs = cos_sim[row_indices, col_indices]

        rho, p_value = spearmanr(inv_ham_pairs, cos_sim_pairs)

        return rho, p_value, inv_ham_pairs, cos_sim_pairs, row_indices, col_indices


# ---------------------------------------------------------------------------
# Encoder Interface
# ---------------------------------------------------------------------------

class EncoderBase(ABC):
    """Abstract base class for all Phase 0 encoders."""

    @abstractmethod
    def train(self, inputs: np.ndarray, epochs: int = 50) -> dict:
        """
        Train the encoder on inputs.

        Parameters
        ----------
        inputs : np.ndarray, shape (n_samples, 3)
        epochs : int

        Returns
        -------
        metrics : dict
            Training metrics (e.g., loss history).
        """
        pass

    @abstractmethod
    def encode(self, inputs: np.ndarray) -> np.ndarray:
        """
        Encode inputs into code vectors.

        Parameters
        ----------
        inputs : np.ndarray, shape (n_samples, 3)

        Returns
        -------
        codes : np.ndarray, shape (n_samples, dim_out)
        """
        pass

    @property
    @abstractmethod
    def dim_out(self) -> int:
        """Output dimension of the encoder."""
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def compute_sparsity(codes: np.ndarray, threshold: float = 0.01) -> float:
    """
    Compute the fraction of code activations below a given threshold.

    Parameters
    ----------
    codes : np.ndarray, shape (n_samples, dim_out)
    threshold : float
        Below this value an activation is considered "inactive".

    Returns
    -------
    sparsity : float in [0, 1]
    """
    return float(np.mean(np.abs(codes) < threshold))


def compute_reconstruction_error(
    original: np.ndarray, reconstructed: np.ndarray
) -> float:
    """Compute mean-squared reconstruction error."""
    return float(np.mean((original - reconstructed) ** 2))


class SimpleLogisticRegression:
    """
    Minimal softmax logistic regression implemented in numpy.
    Suitable for a linear-probe baseline with no sklearn dependency.
    """

    def __init__(self, n_classes: int, n_features: int, lr: float = 0.1,
                 max_iter: int = 1000, seed: int = 42):
        self.n_classes = n_classes
        self.n_features = n_features
        self.lr = lr
        self.max_iter = max_iter
        rng = np.random.default_rng(seed)
        self.W = rng.standard_normal((n_features, n_classes)) * 0.01
        self.b = np.zeros(n_classes)

    @staticmethod
    def _softmax(z: np.ndarray) -> np.ndarray:
        z_shifted = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z_shifted)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SimpleLogisticRegression":
        n = X.shape[0]
        # One-hot encode labels
        y_oh = np.zeros((n, self.n_classes))
        y_oh[np.arange(n), y.astype(int)] = 1.0

        for _ in range(self.max_iter):
            probs = self._softmax(X @ self.W + self.b)
            grad_W = X.T @ (probs - y_oh) / n
            grad_b = np.mean(probs - y_oh, axis=0)
            self.W -= self.lr * grad_W
            self.b -= self.lr * grad_b
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self._softmax(X @ self.W + self.b)
        return np.argmax(probs, axis=1)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        preds = self.predict(X)
        return float(np.mean(preds == y))


def linear_probe_accuracy(
    codes: np.ndarray, labels: np.ndarray
) -> Tuple[float, SimpleLogisticRegression]:
    """
    Fit a simple logistic regression classifier on codes and return accuracy.

    Parameters
    ----------
    codes : np.ndarray, shape (n_samples, dim_out)
    labels : np.ndarray, shape (n_samples,) — integer class labels

    Returns
    -------
    accuracy : float
    model : fitted SimpleLogisticRegression instance
    """
    n_classes = len(np.unique(labels))
    n_features = codes.shape[1]
    model = SimpleLogisticRegression(n_classes, n_features)
    model.fit(codes, labels)
    accuracy = float(model.score(codes, labels))
    return accuracy, model


# ---------------------------------------------------------------------------
# Quick self-test (run with: python src/harness.py)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    print("=== Harness Self-Test ===")

    # 1. Dataset
    ds = DatasetGenerator(seed=42)
    base = ds.get_base_states()
    all_samples = ds.get_all_samples()
    assert base.shape == (8, 3), f"Expected (8, 3), got {base.shape}"
    assert all_samples.shape == (88, 3), f"Expected (88, 3), got {all_samples.shape}"
    print(f"[OK] Dataset: base={base.shape}, all={all_samples.shape}")

    # 2. Similarity evaluator (dummy codes: one-hot)
    #    One-hot codes are orthogonal → cosine similarity = 0 for all off-diagonal.
    #    Spearman ρ should be near 0 or undefined (constant cos_sim).
    dummy_codes = np.eye(8)
    rho, p_val, inv_h, cos_s, _, _ = SimilarityEvaluator.evaluate(base, dummy_codes)
    n_pairs = inv_h.shape[0]
    assert n_pairs == 28, f"Expected 28 off-diagonal pairs, got {n_pairs}"
    # With one-hot codes, all off-diagonal cosine similarities are 0 → constant.
    # spearmanr may return NaN for constant inputs, which is expected.
    print(f"[OK] Similarity eval: ρ={rho}, p={p_val}, pairs={n_pairs}")
    print(f"     Note: ρ=NaN is expected for orthogonal (one-hot) codes.")

    # 3. Utility: sparsity
    sparsity = compute_sparsity(dummy_codes)
    # One-hot has 7/8 entries = 0.875 below any small threshold
    assert sparsity == 7 / 8, f"Expected {7/8}, got {sparsity}"
    print(f"[OK] Sparsity (one-hot): {sparsity:.4f}")

    # 4. Utility: reconstruction error
    recon_err = compute_reconstruction_error(base, base)
    assert recon_err == 0.0
    print(f"[OK] Reconstruction error (identity): {recon_err}")

    # 5. Utility: linear probe
    labels = np.arange(8)  # each state is its own class
    acc, model = linear_probe_accuracy(dummy_codes, labels)
    assert acc == 1.0, f"Expected 100% accuracy on identity, got {acc}"
    print(f"[OK] Linear probe accuracy (one-hot): {acc:.4f}")

    # 6. Verify inverse Hamming distances for 3-bit states
    ham = SimilarityEvaluator.pairwise_hamming(base)
    inv_h_full = SimilarityEvaluator.inverse_hamming(ham)
    # Diagonal should be 1.0 (distance=0)
    assert np.allclose(np.diag(inv_h_full), 1.0)
    # Max inverse Hamming (distance=1) should be 0.5
    assert 0.5 in inv_h_full
    # Min inverse Hamming (distance=3) should be 0.25
    assert 0.25 in inv_h_full
    print(f"[OK] Inverse Hamming distances verified")

    # 7. Test with a code set that should show positive correlation
    #    Create codes proportional to inverse Hamming structure
    #    (trivial test: just verify the pipeline runs on non-orthogonal codes)
    rng = np.random.default_rng(123)
    random_codes = rng.standard_normal((8, 16))
    # Normalize
    random_codes = random_codes / np.linalg.norm(random_codes, axis=1, keepdims=True)
    rho2, p2, _, _, _, _ = SimilarityEvaluator.evaluate(base, random_codes)
    print(f"[OK] Random codes ρ={rho2:.4f}, p={p2:.4e}")

    print("=== All self-tests passed ===")


if __name__ == "__main__":
    _self_test()
