"""
pattern_generator.py — Procedural generator for 1D motion patterns.

Generates sequences of frames (each frame = list of float values, length = n_inputs)
by randomly combining:
  - Motion direction: left→right, right→left, bounce
  - Number of blobs: 1, 2, 3  (with automatic spacing constraint)
  - Blob shape: point, flat block, Gaussian soft edge
  - Blob size: 1–5 pixels
  - Intensity envelope: constant, fade-out, fade-in, fade-out-in
  - Speed: 1 pixel/frame (normal) or 0.5 pixel/frame (slow)

Frame count is computed dynamically per sequence so that one sequence equals
exactly one complete motion cycle.  Repeating the same sequence is therefore
seamless: blobs return to their start position after every cycle.

  LTR / RTL : blobs start at the entry edge (left for LTR, right for RTL) and
              traverse the full array.  n_frames = ceil(n_inputs / pxspeed).
  Bounce    : blobs start at the left edge and make one full back-and-forth.
              n_frames = round(2 * (n_inputs - 1) / pxspeed).

Usage
-----
    gen = PatternGenerator(n_inputs=16, seed=42)

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
from dataclasses import dataclass
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
        if lo <= i <= hi:
            frame[i] = 1.0
        elif lo - 1 < i < lo:
            frame[i] = i - (lo - 1)
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

def _ltr_positions(start: float, n_frames: int, speed: float) -> list[float]:
    return [start + i * speed for i in range(n_frames)]


def _rtl_positions(start: float, n_frames: int, speed: float) -> list[float]:
    return [start - i * speed for i in range(n_frames)]


def _bounce_positions(start: float, n_frames: int, n_inputs: int, speed: float) -> list[float]:
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
SPEED_OPTIONS = [1, 2]   # 1 = normal (1 px/frame), 2 = slow (0.5 px/frame)


@dataclass
class SequenceSpec:
    """Description of what was generated — useful for logging."""
    n_blobs:    int
    blob_size:  int
    blob_shape: str
    direction:  str
    envelope:   str
    speed:      int
    n_frames:   int       # actual frame count for this sequence
    starts:     list[float]

    def __str__(self) -> str:
        blobs_str = f"{self.n_blobs}×{self.blob_shape}{self.blob_size}"
        return (
            f"{blobs_str} {self.direction} env={self.envelope} "
            f"speed={self.speed} frames={self.n_frames}"
        )


class PatternGenerator:
    """
    Generates seamlessly-loopable 1-D motion sequences for a PC sensor array.

    The frame count per sequence is computed dynamically so that each sequence
    covers exactly one complete motion cycle.  Repeating a sequence is therefore
    seamless: every blob returns to its start position after every cycle.

    Parameters
    ----------
    n_inputs : int
        Number of sensor positions (e.g. 8 or 16).
    seed : int | None
        RNG seed for reproducibility.  None = non-deterministic.
    max_blob_fill : float
        Safety threshold: total blob pixels / n_inputs.
        Default 0.65 keeps blobs from merging.
    bias_simple : bool
        When True, use weighted sampling to prefer simpler patterns:
        fewer blobs, sharper shapes, smaller sizes, stronger intensity,
        and normal speed over slow.  Default False = uniform sampling.
    """

    def __init__(
        self,
        n_inputs: int = 8,
        seed: int | None = None,
        max_blob_fill: float = 0.65,
        bias_simple: bool = False,
    ) -> None:
        self.n_inputs      = n_inputs
        self.max_blob_fill = max_blob_fill
        self.bias_simple   = bias_simple
        self._rng          = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def random_sequence(self) -> tuple[list[list[float]], SequenceSpec]:
        """Return (frames, spec) with fully random parameters."""
        rng = self._rng
        bs  = self.bias_simple

        direction = str(rng.choice(DIRECTIONS))

        # blob_shape: point > flat > gauss  (sharper preferred when bias_simple)
        shape_p = np.array([0.50, 0.30, 0.20]) if bs else None
        blob_shape = str(rng.choice(BLOB_SHAPES, p=shape_p))

        # envelope: constant/fade_in preferred (stronger average intensity)
        env_p = np.array([0.40, 0.20, 0.20, 0.10, 0.10]) if bs else None
        envelope = str(rng.choice(ENVELOPES, p=env_p))

        # speed: normal (1px/frame) preferred over slow
        speed_p = np.array([0.70, 0.30]) if bs else None
        speed = int(rng.choice(SPEED_OPTIONS, p=speed_p))

        if blob_shape == "point":
            blob_size = 1
        elif blob_shape == "flat":
            if bs:
                w = np.array([5.0, 4.0, 3.0, 2.0, 1.0]); w /= w.sum()
                blob_size = int(rng.choice([1, 2, 3, 4, 5], p=w))
            else:
                blob_size = int(rng.integers(1, 6))
        else:  # gauss
            if bs:
                w = np.array([3.0, 2.0, 1.0]); w /= w.sum()
                blob_size = int(rng.choice([3, 4, 5], p=w))
            else:
                blob_size = int(rng.integers(3, 6))

        max_blobs = self._max_blobs(blob_size)
        cap = min(4, max_blobs + 1)
        if bs and cap > 2:
            options = list(range(1, cap))
            w = np.array([1.0 / k for k in options], dtype=float); w /= w.sum()
            n_blobs = int(rng.choice(options, p=w))
        else:
            n_blobs = int(rng.integers(1, cap))

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
        Build a loopable sequence from explicit parameters.

        Frame count is computed so that blobs complete exactly one full cycle
        and return to their start position, making repeats seamless.

        Returns
        -------
        frames : list of n_frames lists of n_inputs floats (values in [0, 1])
        spec   : SequenceSpec describing what was generated
        """
        rng     = self._rng
        n       = self.n_inputs
        pxspeed = 1.0 if speed == 1 else 0.5

        # Compute n_frames for exactly one complete cycle
        if direction in ("ltr", "rtl"):
            # Toroidal traversal: blobs wrap around, period = n / pxspeed
            # (always an integer for our speed options)
            n_frames = int(n / pxspeed)
        else:  # bounce
            # one full back-and-forth: left→right→left
            n_frames = round(2 * (n - 1) / pxspeed)

        # Place blob start positions at the entry edge (no random jitter,
        # ensures all blobs return to their starts after n_frames)
        starts = self._place_starts_at_edge(n_blobs, blob_size, n, direction)

        # Compute per-blob trajectory
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
        # LTR/RTL use toroidal rendering: each blob is also drawn as a ghost at
        # center ± n so that blobs wrap around the edges continuously instead of
        # disappearing and reappearing all at once when the sequence restarts.
        sigma = blob_size / 2.5
        toroidal = direction in ("ltr", "rtl")
        raw_frames: list[np.ndarray] = []
        for fi in range(n_frames):
            frame = np.zeros(n)
            for traj in trajectories:
                center = traj[fi]
                draw_at = [center, center - n, center + n] if toroidal else [center]
                for c in draw_at:
                    if blob_shape == "point" or blob_size == 1:
                        blob = _flat_blob(c, 1, n)
                    elif blob_shape == "flat":
                        blob = _flat_blob(c, blob_size, n)
                    else:  # gauss
                        blob = _gauss_blob(c, sigma, n)
                    frame = np.clip(frame + blob, 0.0, 1.0)
            raw_frames.append(frame)

        enveloped = _apply_envelope(raw_frames, intensity_envelope, rng)
        frames_out = [f.tolist() for f in enveloped]

        spec = SequenceSpec(
            n_blobs=n_blobs,
            blob_size=blob_size,
            blob_shape=blob_shape,
            direction=direction,
            envelope=intensity_envelope,
            speed=speed,
            n_frames=n_frames,
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
        min_spacing = blob_size + 1
        return max(1, self.n_inputs // min_spacing)

    def _place_starts_at_edge(
        self, n_blobs: int, blob_size: int, n: int, direction: str
    ) -> list[float]:
        """
        Place n_blobs at the entry edge with minimum spacing = blob_size + 1.
        LTR and bounce start at the left edge; RTL starts at the right edge.
        Falls back to fewer blobs if the array is too small.
        """
        half    = (blob_size - 1) / 2.0
        min_gap = blob_size + 1

        # Reduce n_blobs until they all fit
        while n_blobs > 1 and (n_blobs - 1) * min_gap + blob_size > n:
            n_blobs -= 1

        if direction == "rtl":
            # Pack from right edge inward
            starts = [n - 1 - half - k * min_gap for k in range(n_blobs)]
        else:
            # LTR and bounce: pack from left edge
            starts = [half + k * min_gap for k in range(n_blobs)]

        return starts
