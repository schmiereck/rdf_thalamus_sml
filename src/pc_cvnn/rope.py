r"""rope.py — RoPE-style positional PHASE encoding for the complex (CVNN) PC engine.

Amplitude = "meaning" (here a constant token), PHASE = position:

    z_k = A · exp(i · p · θ_k)

with per-channel angular frequencies θ_k spread geometrically from COARSE (θ_0,
unambiguous over the working range [0, span] — we decode position from it) to
fine (higher channels add resolution and drive the phase-interference kernel).

Shifting position by m is a pure rotation (no new weights); the inner product of
two codes depends only on the relative displacement:

    <z(p_i), z(p_j)> = Σ_k exp(i (p_i − p_j) θ_k)   -> a relative-distance kernel.
"""
from __future__ import annotations

import numpy as np


def rope_freqs(n_freqs: int, span: float = 6.0, ratio: float = 1.7) -> np.ndarray:
    """Angular frequencies, COARSE -> fine.  θ_0 is unambiguous over [0, span]."""
    lo = 0.9 * np.pi / span
    return lo * (ratio ** np.arange(n_freqs))


def rope_encode_1d(p: float, theta: np.ndarray, amp: float = 1.0) -> np.ndarray:
    """Position p -> complex code  amp · exp(i · p · θ_k).  |z|=amp, phase carries p."""
    return amp * np.exp(1j * p * theta)


def rope_decode_1d(z: np.ndarray, theta: np.ndarray) -> float:
    """Recover p from the COARSEST frequency (θ_0, unambiguous over [0, span])."""
    return float(np.angle(z[0]) / theta[0])


def rope_encode_2d(pos, n_freqs: int = 8, span: float = 6.0, amp: float = 1.0) -> np.ndarray:
    """2-D position -> complex vector of length n_freqs (half the freqs per axis)."""
    x, y = float(pos[0]), float(pos[1])
    kf = n_freqs // 2
    th = rope_freqs(kf, span)
    return np.concatenate([rope_encode_1d(x, th, amp), rope_encode_1d(y, th, amp)])


def rope_decode_2d(z: np.ndarray, n_freqs: int = 8, span: float = 6.0) -> np.ndarray:
    """Recover the 2-D position from the reconstructed complex code's phase."""
    kf = n_freqs // 2
    th = rope_freqs(kf, span)
    z = np.asarray(z)
    x = rope_decode_1d(z[:kf], th)
    y = rope_decode_1d(z[kf:], th)
    return np.array([x, y])
