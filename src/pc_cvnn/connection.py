"""PCConnection — weighted, directed edge between two COMPLEX-VALUED PCNodes (CVNN).

The weight matrix W is np.complex128.  Top-down prediction and error back-pressure
use ordinary complex matrix products; the LEARNING rule conjugates the pre-synaptic
activation (Wirtinger / conjugate-Hebbian) so the update does not diverge.  All
weight clipping is by MAGNITUDE (complex numbers have no order).
"""

from __future__ import annotations

from enum import Enum, auto

import numpy as np

from .node import PCNode


class ConnType(Enum):
    UP = auto()         # source is deeper (abstract), target is shallower (sensor-side)
    LATERAL = auto()    # source and target are in the same layer
    RECURRENT = auto()  # kept for backwards compatibility; treated like LATERAL


def _clip_mag(z: np.ndarray, clip: float) -> None:
    """Clip a complex array IN PLACE by magnitude (|z| ≤ clip), keeping phase."""
    if clip <= 0.0:
        return
    mag = np.abs(z)
    over = mag > clip
    if np.any(over):
        z[over] *= clip / mag[over]


class PCConnection:
    """
    A single directed connection  source → target  with COMPLEX weight matrix W.

    Shape of W:  [dim_source × dim_target], dtype complex128

    Prediction (Phase 1):
        pred = W^T · f(μ_source)        shape [dim_target]
        pushed to target.receive_prediction(pred)

    Error back-pressure (Phase 3):
        pressure = W · ε_target         shape [dim_source]
        scaled by beta (UP) or gamma (LATERAL/RECURRENT)

    Learning (Phase 4, local conjugate-Hebbian):
        ΔW = η · conj(f(μ_source)) ⊗ ε_target
        W  ← W + ΔW   (with optional L2 weight decay, magnitude clip)
    """

    def __init__(
        self,
        conn_id: str,
        source: PCNode,
        target: PCNode,
        conn_type: ConnType = ConnType.UP,
        eta_learn: float = 0.001,
        lambda_decay: float = 0.001,
        w_clip: float = 5.0,
        pressure_scale: float = 1.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.id = conn_id
        self.source = source
        self.target = target
        self.conn_type = conn_type
        self.eta_learn = eta_learn
        self.lambda_decay = lambda_decay
        self.w_clip = w_clip
        self.pressure_scale = pressure_scale

        rng = rng or np.random.default_rng()
        # Polar init: Xavier-scaled amplitude, phase uniform in [0, 2π) so the
        # complex weights have a proper phase distribution from the start.
        limit = np.sqrt(6.0 / (source.dim + target.dim))
        amp = rng.uniform(0.0, limit, (source.dim, target.dim))
        phi = rng.uniform(0.0, 2.0 * np.pi, (source.dim, target.dim))
        self.W: np.ndarray = (amp * np.exp(1j * phi)).astype(np.complex128)

    # ------------------------------------------------------------------
    # Phase 1: push prediction to target
    # ------------------------------------------------------------------

    def predict(self) -> None:
        """Compute prediction and push to target node."""
        pred = self.W.T @ self.source.activation   # [dim_target], complex
        self.target.receive_prediction(pred)

    # ------------------------------------------------------------------
    # Phase 3: push error back-pressure to source
    # ------------------------------------------------------------------

    def propagate_error(self, beta: float = 1.0, gamma: float = 1.0) -> None:
        """Back-propagate target error to source as state pressure."""
        scale = (beta if self.conn_type == ConnType.UP else gamma) * self.pressure_scale
        pressure = scale * (self.W @ self.target.epsilon)   # [dim_source], complex
        self.source.add_pressure(pressure)

    # ------------------------------------------------------------------
    # Phase 4: local conjugate-Hebbian weight update
    # ------------------------------------------------------------------

    def learn(self, modulation: float = 1.0) -> None:
        """ΔW = η · modulation · conj(f(μ_source)) ⊗ ε_target  (CVNN local rule)

        The PRE-SYNAPTIC activation f(μ_source) is CONJUGATED in the outer
        product — the complex gradient requires it; without the conjugate the
        weights diverge.  `modulation` is the global neuromodulator (1.0 =
        neutral).  Decay and clipping are NOT modulated.
        """
        dW = np.outer(np.conjugate(self.source.activation), self.target.epsilon)
        if np.all(np.isfinite(dW)):
            self.W += self.eta_learn * modulation * dW
        if self.lambda_decay > 0.0:
            self.W *= (1.0 - self.lambda_decay)
        _clip_mag(self.W, self.w_clip)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"PCConnection(id={self.id!r}, "
            f"{self.source.id!r}→{self.target.id!r}, "
            f"type={self.conn_type.name}, "
            f"W={self.W.shape} complex)"
        )
