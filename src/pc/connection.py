"""PCConnection — weighted, directed edge between two PCNodes."""

from __future__ import annotations

from enum import Enum, auto

import numpy as np

from .node import PCNode


class ConnType(Enum):
    UP = auto()       # source is deeper (abstract), target is shallower (sensor-side)
    LATERAL = auto()  # source and target are in the same layer


class PCConnection:
    """
    A single directed connection  source → target  with weight matrix W.

    Shape of W:  [dim_source × dim_target]

    Prediction (Phase 1):
        pred = W^T · f(μ_source)        shape [dim_target]
        pushed to target.receive_prediction(pred)

    Error back-pressure (Phase 3):
        pressure = W · ε_target         shape [dim_source]
        scaled by beta (UP) or gamma (LATERAL)
        pushed to source.add_pressure(pressure)

    Learning (Phase 4, local Hebbian):
        ΔW = η_learn · f(μ_source) ⊗ ε_target
        W  ← W - ΔW   (with optional L2 weight decay)
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
        self.pressure_scale = pressure_scale  # per-connection relaxation strength multiplier

        # Xavier initialisation
        rng = rng or np.random.default_rng()
        limit = np.sqrt(6.0 / (source.dim + target.dim))
        self.W: np.ndarray = rng.uniform(-limit, limit, (source.dim, target.dim))

    # ------------------------------------------------------------------
    # Phase 1: push prediction to target
    # ------------------------------------------------------------------

    def predict(self) -> None:
        """Compute prediction and push to target node."""
        pred = self.W.T @ self.source.activation   # [dim_target]
        self.target.receive_prediction(pred)

    # ------------------------------------------------------------------
    # Phase 3: push error back-pressure to source
    # ------------------------------------------------------------------

    def propagate_error(self, beta: float = 1.0, gamma: float = 1.0) -> None:
        """
        Back-propagate target error to source as state pressure.

        beta  — weight for UP connections
        gamma — weight for LATERAL connections
        """
        scale = (beta if self.conn_type == ConnType.UP else gamma) * self.pressure_scale
        pressure = scale * (self.W @ self.target.epsilon)   # [dim_source]
        self.source.add_pressure(pressure)

    # ------------------------------------------------------------------
    # Phase 4: local Hebbian weight update
    # ------------------------------------------------------------------

    def learn(self) -> None:
        """ΔW = η · f(μ_source) ⊗ ε_target  (outer product, local rule)"""
        dW = np.outer(self.source.activation, self.target.epsilon)  # [dim_source × dim_target]
        if np.all(np.isfinite(dW)):
            self.W += self.eta_learn * dW
        if self.lambda_decay > 0.0:
            self.W *= (1.0 - self.lambda_decay)
        if self.w_clip > 0.0:
            np.clip(self.W, -self.w_clip, self.w_clip, out=self.W)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"PCConnection(id={self.id!r}, "
            f"{self.source.id!r}→{self.target.id!r}, "
            f"type={self.conn_type.name}, "
            f"W={self.W.shape})"
        )
