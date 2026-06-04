"""PCNode — single node in a Predictive Coding graph.

Each hidden node carries two learned weight sets (per predictive-coding.md):

  W  (hierarchical, in PCConnection) — top-down generative prediction
  V  (temporal, in PCNode)           — forward model: μ_t → predicted μ_{t+1}

Temporal lifecycle
------------------
Phase 1  (new frame arrives):
    mu ← predicted_next_mu          # warm-start from the node's own forward model
    receive / finalize hierarchical prediction π from connected nodes

Phase 2  compute ε = μ − π

Phase 3  relax: update μ using error pressure from all connections

Phase 4  learn hierarchical W (in PCConnection)
         learn temporal V:
             predicted_next_mu = f(V @ f(μ))     # forward-model output
             ΔV = η_V · (μ_target − predicted_next_mu) ⊗ f'(V @ f(μ)) ⊗ f(μ)
         The target for the forward model is the ACTUAL next-step μ, which is
         stored by commit_step() and used the following frame.
"""

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
    A single Predictive Coding node with a built-in temporal forward model.

    Internal vectors (shape [dim]):
        μ  (mu)       — current state / representation
        π  (pi)       — aggregated top-down prediction received from connections
        ε  (epsilon)  — prediction error  ε = μ − π

    Temporal forward model (shape [dim × dim]):
        V             — temporal weight matrix: maps f(μ_t) → predicted μ_{t+1}
        predicted_next_mu — output of forward model at step t, used to warm-start
                            μ at step t+1 (before hierarchical relaxation)

    Lifecycle per time step (called by PCNetwork):
        Phase 1  load_predicted_state()            ← warm-start μ from V's prediction
                 receive_prediction(p) / finalize_prediction()
        Phase 2  compute_error()
        Phase 3  add_pressure(dp) / update_state(eta, alpha)   [n_relax times]
        Phase 4  learn_temporal(eta_V, w_clip_V)   ← update V toward actual next μ
        commit_step()                               ← snapshot μ; run forward model
    """

    def __init__(
        self,
        node_id: str,
        dim: int,
        activation: str = "tanh",
        eta_temporal: float = 0.1,     # learning rate for V  (sweep optimum; diverges >~2.0)
        w_clip_V: float = 3.0,         # weight clip for V
        rng: np.random.Generator | None = None,
    ) -> None:
        if activation not in _ACTIVATIONS:
            raise ValueError(f"Unknown activation '{activation}'. Choose from {list(_ACTIVATIONS)}")

        self.id = node_id
        self.dim = dim
        self.eta_temporal = eta_temporal
        self.w_clip_V = w_clip_V
        self._act, self._act_deriv = _ACTIVATIONS[activation]

        rng = rng or np.random.default_rng()
        self.mu: np.ndarray = rng.normal(0.0, 0.01, dim)
        self.pi: np.ndarray = np.zeros(dim)
        self.epsilon: np.ndarray = np.zeros(dim)

        # Forward model  V: [dim × dim]
        # Initialised as near-identity so the forward model starts as a
        # persistence prior:  predicted_next ≈ f(I · f(μ)) ≈ μ  (for |μ|<1).
        # This is the correct inductive bias before any dynamics are learned
        # ("next state ≈ current state"); V then learns DEVIATIONS from it,
        # i.e. real motion dynamics.  A near-zero V would instead reset μ to 0
        # at the start of every frame.
        self.V: np.ndarray = np.eye(dim) + rng.normal(0.0, 0.01, (dim, dim))

        # Temporal buffers
        self._prev_mu: np.ndarray = np.zeros(dim)       # μ from end of previous step
        self._predicted_next_mu: np.ndarray = np.zeros(dim)  # V's prediction for next step
        self._prev_f_mu: np.ndarray = np.zeros(dim)    # f(μ_prev) saved for V learning

        # Phase accumulators
        self._pred_sum: np.ndarray = np.zeros(dim)
        self._pred_count: int = 0
        self._pressure: np.ndarray = np.zeros(dim)

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
        return self._act_deriv(self.mu)

    @property
    def prev_mu(self) -> np.ndarray:
        """μ at the end of the previous frame (read-only view)."""
        return self._prev_mu

    @property
    def prev_activation(self) -> np.ndarray:
        """f(μ_prev) — kept for any external RECURRENT connections that still use it."""
        return self._act(self._prev_mu)

    # ------------------------------------------------------------------
    # Phase 1: load warm-start + receive hierarchical prediction
    # ------------------------------------------------------------------

    def load_predicted_state(self) -> None:
        """
        Phase 1, first action: initialise μ from the forward model's prediction
        of this frame, computed at the end of the previous frame.

        Clamped nodes (sensors) are driven by external input — skip.
        """
        if self._clamped:
            return
        self.mu = self._predicted_next_mu.copy()

    def receive_prediction(self, pred: np.ndarray) -> None:
        """Called by each incoming connection with its top-down prediction."""
        self._pred_sum += pred
        self._pred_count += 1

    def finalize_prediction(self) -> None:
        """Average all received predictions into π."""
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
        """ε = μ − π"""
        self.epsilon = self.mu - self.pi

    # ------------------------------------------------------------------
    # Phase 3: Relax
    # ------------------------------------------------------------------

    def add_pressure(self, dp: np.ndarray) -> None:
        self._pressure += dp

    def update_state(self, eta_inf: float, alpha: float) -> None:
        """
        μ ← μ + η_inf · (−α·ε + accumulated connection pressure)
        Clamped nodes ignore this update.
        """
        if self._clamped:
            self._pressure = np.zeros(self.dim)
            return
        dmu = -alpha * self.epsilon + self._pressure
        new_mu = self.mu + eta_inf * dmu
        if not np.all(np.isfinite(new_mu)):
            self.mu = np.zeros(self.dim)
        else:
            self.mu = new_mu
        self._pressure = np.zeros(self.dim)

    # ------------------------------------------------------------------
    # Phase 4 (temporal): learn V and compute next prediction
    # ------------------------------------------------------------------

    def learn_temporal(self, modulation: float = 1.0) -> None:
        """
        Update the temporal weight matrix V.

        `modulation` is the global neuromodulator (default 1.0 = neutral); it
        scales the V update just like the connection W update, so reward shapes
        the forward model that drives anticipatory predictions (and actions).

        The forward model predicts: predicted_next = f(V @ f(μ_prev))
        The target is the ACTUAL μ at the current step (which IS the next step
        relative to the previous frame where the prediction was made).

        Error:  δ = μ_current − predicted_next_mu_from_prev
        ΔV    = η_V · δ · f'(pre) ⊗ f(μ_prev)^T
        where pre = V @ f(μ_prev)  (saved during commit_step).

        Clamped nodes have no V to learn.
        """
        if self._clamped:
            return
        # delta: how far off the forward model was
        delta = self.mu - self._predicted_next_mu   # shape [dim]
        # "single" mode: predicted = V @ f(mu_prev), gradient is just the outer product
        dV = np.outer(delta, self._prev_f_mu)
        if np.all(np.isfinite(dV)):
            self.V += self.eta_temporal * modulation * dV
        if self.w_clip_V > 0.0:
            np.clip(self.V, -self.w_clip_V, self.w_clip_V, out=self.V)

    # ------------------------------------------------------------------
    # commit_step: snapshot μ and run forward model for next frame
    # ------------------------------------------------------------------

    def commit_step(self) -> None:
        """
        End-of-frame bookkeeping:

        1. Save μ_relaxed as prev_mu (target for V learning next frame).
        2. Run the forward model: predicted_next_mu = f(V @ f(μ))
           This prediction warm-starts μ at the top of the NEXT frame,
           giving the node a head-start before hierarchical relaxation.

        Clamped nodes (sensors) just snapshot their current value.
        """
        if self._clamped:
            self._prev_mu = self.mu.copy()
            return
        # Save for V's learning target next frame
        self._prev_f_mu = self._act(self.mu).copy()   # f(μ_t)
        self._prev_mu = self.mu.copy()                 # μ_t (for external access)
        # Forward model: predict μ_{t+1}
        # "single" mode: V @ f(μ) — one activation, no double squashing.
        self._predicted_next_mu = self.V @ self._prev_f_mu   # V @ f(μ_t)

    # ------------------------------------------------------------------
    # Sensor clamping
    # ------------------------------------------------------------------

    def clamp(self, value: np.ndarray) -> None:
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
        """Re-initialise state to near-zero; keep weights."""
        rng = rng or np.random.default_rng()
        self.mu = rng.normal(0.0, 0.01, self.dim)
        self.pi = np.zeros(self.dim)
        self.epsilon = np.zeros(self.dim)
        self._prev_mu = np.zeros(self.dim)
        self._predicted_next_mu = np.zeros(self.dim)
        self._prev_f_mu = np.zeros(self.dim)
        self._pred_sum = np.zeros(self.dim)
        self._pred_count = 0
        self._pressure = np.zeros(self.dim)
        self._clamped = False

    def __repr__(self) -> str:
        clamp_str = " [CLAMPED]" if self._clamped else ""
        return f"PCNode(id={self.id!r}, dim={self.dim}){clamp_str}"


class SensorNode(PCNode):
    """
    Convenience subclass: always clamped, no temporal forward model.
    Call set_input() each time step.
    """

    def __init__(self, node_id: str, dim: int) -> None:
        super().__init__(node_id, dim, activation="identity")
        self._clamped = True

    def set_input(self, value: np.ndarray) -> None:
        self.clamp(value)
