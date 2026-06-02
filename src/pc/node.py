"""PCNode — single node in a Predictive Coding graph."""

from __future__ import annotations

import numpy as np


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


def _tanh_deriv(x: np.ndarray) -> np.ndarray:
    return 1.0 - np.tanh(x) ** 2


_ACTIVATIONS = {
    "tanh": (_tanh, _tanh_deriv),
    "relu": (lambda x: np.maximum(0.0, x), lambda x: (x > 0).astype(float)),
    "identity": (lambda x: x, lambda x: np.ones_like(x)),
}


class PCNode:
    """
    A single Predictive Coding node.

    Internal vectors (all shape [dim]):
        μ  (state)      — current representation
        π  (prediction) — aggregated prediction received from connected nodes
        ε  (error)      — μ - π

    Lifecycle per time step (called by PCNetwork):
        Phase 1  receive_prediction(p) / finalize_prediction()
        Phase 2  compute_error()
        Phase 3  add_pressure(dp) / update_state(eta_inf)   [repeated n_relax times]
        Phase 4  (learning happens in PCConnection, not here)
    """

    def __init__(
        self,
        node_id: str,
        dim: int,
        activation: str = "tanh",
        tau: float = 0.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        if activation not in _ACTIVATIONS:
            raise ValueError(f"Unknown activation '{activation}'. Choose from {list(_ACTIVATIONS)}")

        self.id = node_id
        self.dim = dim
        self.tau = tau                                       # leaky persistence (0=fast, →1=slow)
        self._act, self._act_deriv = _ACTIVATIONS[activation]

        rng = rng or np.random.default_rng()
        self.mu: np.ndarray = rng.normal(0.0, 0.01, dim)   # state μ
        self.pi: np.ndarray = np.zeros(dim)                 # prediction π
        self.epsilon: np.ndarray = np.zeros(dim)            # error ε
        self.prev_mu: np.ndarray = np.zeros(dim)            # state μ at the previous frame

        # Accumulators reset each phase
        self._pred_sum: np.ndarray = np.zeros(dim)
        self._pred_count: int = 0
        self._pressure: np.ndarray = np.zeros(dim)          # dμ from connections

        self._clamped: bool = False

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def activation(self) -> np.ndarray:
        """f(μ) — what this node broadcasts to connected nodes."""
        return self._act(self.mu)

    @property
    def activation_deriv(self) -> np.ndarray:
        """f'(μ) — used for precise error back-pressure."""
        return self._act_deriv(self.mu)

    @property
    def prev_activation(self) -> np.ndarray:
        """f(μ_prev) — the node's activation at the previous frame (temporal memory)."""
        return self._act(self.prev_mu)

    # ------------------------------------------------------------------
    # Phase 1: Predict
    # ------------------------------------------------------------------

    def receive_prediction(self, pred: np.ndarray) -> None:
        """Called by each incoming connection with its prediction contribution."""
        self._pred_sum += pred
        self._pred_count += 1

    def finalize_prediction(self) -> None:
        """Compute mean prediction; call once after all connections have pushed."""
        if self._pred_count > 0:
            self.pi = self._pred_sum / self._pred_count
        else:
            self.pi = np.zeros(self.dim)
        self._pred_sum = np.zeros(self.dim)
        self._pred_count = 0

    # ------------------------------------------------------------------
    # Phase 2: Error
    # ------------------------------------------------------------------

    def compute_error(self) -> None:
        """ε = μ - π"""
        self.epsilon = self.mu - self.pi

    # ------------------------------------------------------------------
    # Phase 3: Relax
    # ------------------------------------------------------------------

    def add_pressure(self, dp: np.ndarray) -> None:
        """Called by each outgoing connection with its error back-pressure."""
        self._pressure += dp

    def update_state(self, eta_inf: float, alpha: float) -> None:
        """
        μ ← μ + η_inf · (−α·ε  +  accumulated pressure from connections)

        Clamped nodes (sensors) ignore this update.
        NaN/Inf guard: if the update produces non-finite values, reset to zero.
        """
        if self._clamped:
            self._pressure = np.zeros(self.dim)
            return

        dmu = -alpha * self.epsilon + self._pressure
        new_mu = self.mu + eta_inf * dmu
        if not np.all(np.isfinite(new_mu)):
            # Numerical explosion — reset this node's state
            self.mu = np.zeros(self.dim)
        else:
            self.mu = new_mu
        self._pressure = np.zeros(self.dim)

    # ------------------------------------------------------------------
    # Temporal memory: commit one frame
    # ------------------------------------------------------------------

    def commit_step(self) -> None:
        """
        End-of-frame bookkeeping for temporal hierarchy:

          1. Leaky persistence — deeper layers (higher τ) keep more of their
             previous state, so they evolve on a slower timescale:
                 μ ← (1 − τ) · μ_relaxed  +  τ · μ_prev
          2. Snapshot — store the (blended) μ as prev_mu for the next frame,
             so recurrent self-connections can read it as temporal context.

        Clamped nodes (sensors) carry no memory; they are skipped.
        """
        if self._clamped:
            self.prev_mu = self.mu.copy()
            return
        if self.tau > 0.0:
            self.mu = (1.0 - self.tau) * self.mu + self.tau * self.prev_mu
        self.prev_mu = self.mu.copy()

    # ------------------------------------------------------------------
    # Sensor clamping
    # ------------------------------------------------------------------

    def clamp(self, value: np.ndarray) -> None:
        """Fix state to an external input value (sensor node behaviour)."""
        assert value.shape == (self.dim,), f"Expected shape ({self.dim},), got {value.shape}"
        self.mu = value.copy()
        self._clamped = True

    def unclamp(self) -> None:
        self._clamped = False

    @property
    def is_clamped(self) -> bool:
        return self._clamped

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def reset(self, rng: np.random.Generator | None = None) -> None:
        """Re-initialise state to near-zero; keep weights (in connections)."""
        rng = rng or np.random.default_rng()
        self.mu = rng.normal(0.0, 0.01, self.dim)
        self.pi = np.zeros(self.dim)
        self.epsilon = np.zeros(self.dim)
        self.prev_mu = np.zeros(self.dim)
        self._pred_sum = np.zeros(self.dim)
        self._pred_count = 0
        self._pressure = np.zeros(self.dim)
        self._clamped = False

    def __repr__(self) -> str:
        clamp_str = " [CLAMPED]" if self._clamped else ""
        return f"PCNode(id={self.id!r}, dim={self.dim}){clamp_str}"


class SensorNode(PCNode):
    """
    Convenience subclass: always clamped.  Call set_input() each time step.
    """

    def __init__(self, node_id: str, dim: int) -> None:
        super().__init__(node_id, dim, activation="identity")
        self._clamped = True

    def set_input(self, value: np.ndarray) -> None:
        self.clamp(value)
