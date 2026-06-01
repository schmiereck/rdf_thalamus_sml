"""
pattern_generator.py — Procedural generator for 1D motion patterns.

Generates sequences of frames (each frame = list of float values, length = n_inputs)
by randomly combining:
  - Motion direction: left→right, right→left, bounce
  - Number of blobs: 1, 2, 3  (with automatic spacing constraint)
  - Blob shape: point, flat block, Gaussian soft edge
  - Blob size: 1–5 pixels
  - Intensity envelope: constant, fade-out, fade-in, fade-out-in
  - Speed: 1 pixel/frame (normal) or 0.5 pixel/frame (slow, stays 2 frames)

Usage
-----
    gen = PatternGenerator(n_inputs=8, n_frames=8, seed=42)

    # One random sequence (list of frames):
    frames, description = gen.random_sequence()

    # Or specify components explicitly:
    frames, description = gen.build_sequence(
        n_blobs=2,
        blob_size=3,
        blob_shape="gauss",
        direction="bounce",
        intensity_envelope="fade_out",
        speed=1,
    )

    # Infinite stream for training:
    for frames, desc in gen.stream(max_sequences=1000):
        ...
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np


# ---------------------------------------------------------------------------
# Internal blob-shape helpers
# ---------------------------------------------------------------------------

def _flat_blob(center: float, size: int, n: int) -> np.ndarray:
    """
    Flat-top blob of given pixel width centred at fractional position `center`.
    Uses linear interpolation at the edges for sub-pixel smoothness.
    """
    frame = np.zeros(n)
    half = (size - 1) / 2.0
    lo = center - half
    hi = center + half
    for i in range(n):
        # full coverage
        if lo <= i <= hi:
            frame[i] = 1.0
        # left edge anti-alias
        elif lo - 1 < i < lo:
            frame[i] = i - (lo - 1)
        # right edge anti-alias
        elif hi < i < hi + 1:
            frame[i] = (hi + 1) - i
    return frame


def _gauss_blob(center: float, sigma: float, n: int, threshold: float = 0.05) -> np.ndarray:
    """Gaussian blob; pixels below `threshold` are zeroed."""
    frame = np.zeros(n)
    for i in range(n):
        v = math.exp(-0.5 * ((i - center) / sigma) ** 2)
        frame[i] = v if v >= threshold else 0.0
    return frame


def _apply_envelope(frames: list[np.ndarray], envelope: str, rng: np.random.Generator) -> list[np.ndarray]:
    """
    Scale per-frame intensity by an envelope curve.

    envelope:
        "constant"    — no change
        "fade_out"    — 1.0 → 0.25 linearly
        "fade_in"     — 0.25 → 1.0 linearly
        "fade_out_in" — 1.0 → 0.25 → 1.0 (V-shape)
        "random_start_fade_out"  — random start intensity, fades to 0.25
    """
    n = len(frames)
    if envelope == "constant":
        return frames
    elif envelope == "fade_out":
        scales = np.linspace(1.0, 0.25, n)
    elif envelope == "fade_in":
        scales = np.linspace(0.25, 1.0, n)
    elif envelope == "fade_out_in":
        half = n // 2
        scales = np.concatenate([np.linspace(1.0, 0.25, half), np.linspace(0.25, 1.0, n - half)])
    elif envelope == "random_start_fade_out":
        start = rng.uniform(0.4, 1.0)
        scales = np.linspace(start, 0.25, n)
    else:
        return frames
    return [f * s for f, s in zip(frames, scales)]


# ---------------------------------------------------------------------------
# Motion trajectory helpers
# ---------------------------------------------------------------------------

def _ltr_positions(start: float, n_frames: int, speed: float = 1.0) -> list[float]:
    """Left-to-right: start → start + (n_frames-1)*speed, wraps."""
    return [start + i * speed for i in range(n_frames)]


def _rtl_positions(start: float, n_frames: int, speed: float = 1.0) -> list[float]:
    """Right-to-left: start → start - (n_frames-1)*speed."""
    return [start - i * speed for i in range(n_frames)]


def _bounce_positions(start: float, n_frames: int, n_inputs: int, speed: float = 1.0) -> list[float]:
    """Bounce back and forth within [0, n_inputs-1]."""
    positions = []
    pos = start
    direction = 1
    for _ in range(n_frames):
        positions.append(pos)
        pos += direction * speed
        if pos >= n_inputs - 1:
            pos = n_inputs - 1
            direction = -1
        elif pos <= 0:
            pos = 0
            direction = 1
    return positions


# ---------------------------------------------------------------------------
# Main generator class
# ---------------------------------------------------------------------------

DIRECTIONS    = ["ltr", "rtl", "bounce"]
BLOB_SHAPES   = ["point", "flat", "gauss"]
ENVELOPES     = ["constant", "fade_out", "fade_in", "fade_out_in", "random_start_fade_out"]
SPEED_OPTIONS = [1, 2]   # 1 = normal (1 px/frame), 2 = slow (stays 2 frames)


@dataclass
class SequenceSpec:
    """Description of what was generated — useful for logging."""
    n_blobs:    int
    blob_size:  int
    blob_shape: str
    direction:  str
    envelope:   str
    speed:      int
    starts:     list[float]

    def __str__(self) -> str:
        blobs_str = f"{self.n_blobs}×{self.blob_shape}{self.blob_size}"
        return (
            f"{blobs_str} {self.direction} env={self.envelope} "
            f"speed={self.speed} starts={[round(s,1) for s in self.starts]}"
        )


class PatternGenerator:
    """
    Generates 1-D motion sequences for a PC sensor array.

    Parameters
    ----------
    n_inputs : int
        Number of sensor positions (e.g. 8).
    n_frames : int
        Frames per sequence (e.g. 8 or 16).
    seed : int | None
        RNG seed for reproducibility.  None = non-deterministic.
    max_blob_fill : float
        Safety threshold: total blob pixels / n_inputs.
        If a candidate configuration would exceed this, reduce n_blobs.
        Default 0.65 keeps blobs from merging.
    """

    def __init__(
        self,
        n_inputs: int = 8,
        n_frames: int = 8,
        seed: int | None = None,
        max_blob_fill: float = 0.65,
    ) -> None:
        self.n_inputs      = n_inputs
        self.n_frames      = n_frames
        self.max_blob_fill = max_blob_fill
        self._rng          = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def random_sequence(self) -> tuple[list[list[float]], SequenceSpec]:
        """Return (frames, spec) with fully random parameters."""
        rng = self._rng

        direction  = str(rng.choice(DIRECTIONS))
        blob_shape = str(rng.choice(BLOB_SHAPES))
        envelope   = str(rng.choice(ENVELOPES))
        speed      = int(rng.choice(SPEED_OPTIONS))

        # Blob size depends on shape
        if blob_shape == "point":
            blob_size = 1
        elif blob_shape == "flat":
            blob_size = int(rng.integers(1, 6))   # 1–5
        else:  # gauss
            blob_size = int(rng.integers(3, 6))   # 3–5

        # How many blobs can we fit?
        max_blobs = self._max_blobs(blob_size)
        n_blobs = int(rng.integers(1, min(4, max_blobs + 1)))

        return self.build_sequence(
            n_blobs=n_blobs,
            blob_size=blob_size,
            blob_shape=blob_shape,
            direction=direction,
            intensity_envelope=envelope,
            speed=speed,
        )

    def build_sequence(
        self,
        n_blobs:            int   = 1,
        blob_size:          int   = 1,
        blob_shape:         str   = "point",
        direction:          str   = "ltr",
        intensity_envelope: str   = "constant",
        speed:              int   = 1,
    ) -> tuple[list[list[float]], SequenceSpec]:
        """
        Build a deterministic sequence from explicit parameters.

        Returns
        -------
        frames : list of n_frames lists of n_inputs floats (values in [0, 1])
        spec   : SequenceSpec describing what was generated
        """
        rng        = self._rng
        n          = self.n_inputs
        n_frames   = self.n_frames if speed == 1 else self.n_frames * 2
        pxspeed    = 1.0 if speed == 1 else 0.5   # pixels per frame

        # Place blob start positions with minimum spacing
        starts = self._place_starts(n_blobs, blob_size, n)

        # Compute per-blob trajectory (sequence of center positions)
        trajectories: list[list[float]] = []
        for s in starts:
            if direction == "ltr":
                traj = _ltr_positions(s, n_frames, pxspeed)
            elif direction == "rtl":
                traj = _rtl_positions(s, n_frames, pxspeed)
            else:
                traj = _bounce_positions(s, n_frames, n, pxspeed)
            trajectories.append(traj)

        # Render frames
        sigma = blob_size / 2.5   # Gaussian sigma
        raw_frames: list[np.ndarray] = []
        for fi in range(n_frames):
            frame = np.zeros(n)
            for traj in trajectories:
                center = traj[fi]
                if blob_shape == "point" or blob_size == 1:
                    blob = _flat_blob(center, 1, n)
                elif blob_shape == "flat":
                    blob = _flat_blob(center, blob_size, n)
                else:  # gauss
                    blob = _gauss_blob(center, sigma, n)
                frame = np.clip(frame + blob, 0.0, 1.0)
            raw_frames.append(frame)

        # Apply intensity envelope
        enveloped = _apply_envelope(raw_frames, intensity_envelope, rng)

        # Truncate to n_frames if slow doubled the length
        frames_out = [f.tolist() for f in enveloped[:self.n_frames]]

        spec = SequenceSpec(
            n_blobs=n_blobs,
            blob_size=blob_size,
            blob_shape=blob_shape,
            direction=direction,
            envelope=intensity_envelope,
            speed=speed,
            starts=[round(float(s), 2) for s in starts],
        )
        return frames_out, spec

    def stream(
        self,
        max_sequences: int | None = None,
        repeats_per_sequence: int = 1,
    ) -> Iterator[tuple[list[list[float]], SequenceSpec]]:
        """
        Infinite (or bounded) stream of random sequences.

        Each sequence is yielded `repeats_per_sequence` times in a row
        (useful for PC learning: repeat so the network can relax into each pattern).
        """
        count = 0
        while max_sequences is None or count < max_sequences:
            frames, spec = self.random_sequence()
            for _ in range(repeats_per_sequence):
                yield frames, spec
            count += 1

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _max_blobs(self, blob_size: int) -> int:
        """Maximum blobs that still fit with at least 1-pixel gap between them."""
        min_spacing = blob_size + 1   # blob width + 1 gap pixel
        return max(1, self.n_inputs // min_spacing)

    def _place_starts(self, n_blobs: int, blob_size: int, n: int) -> list[float]:
        """
        Place n_blobs start positions with minimum spacing = blob_size + 1.
        Uses random jitter within the available slots.
        Falls back to fewer blobs if the array is too small.
        """
        rng = self._rng
        min_gap = blob_size + 1   # minimum distance between blob centres

        # Reduce n_blobs until they all fit
        while n_blobs > 1 and (n_blobs - 1) * min_gap + blob_size > n:
            n_blobs -= 1

        if n_blobs == 1:
            half = (blob_size - 1) / 2.0
            lo   = half
            hi   = n - 1 - half
            start = float(rng.uniform(lo, max(lo, hi)))
            return [start]

        # Distribute evenly with random jitter
        half    = (blob_size - 1) / 2.0
        lo      = half
        hi      = n - 1 - half
        spacing = (hi - lo) / (n_blobs - 1)
        jitter  = max(0.0, (spacing - min_gap) / 2.0)

        starts = []
        for k in range(n_blobs):
            base  = lo + k * spacing
            delta = float(rng.uniform(-jitter, jitter))
            starts.append(base + delta)
        return starts
