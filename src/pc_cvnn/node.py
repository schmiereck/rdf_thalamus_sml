"""PCNode — single node in a COMPLEX-VALUED Predictive Coding graph (CVNN).

This is the complex-valued (phase-space) refactor of the pure-NumPy PC engine.
All state vectors (mu, pi, epsilon, _prev_mu, ...) and weight matrices (V here,
W in PCConnection) are np.complex128.  The representational density doubles
(amplitude + phase) and the prediction error ε = μ − π is the natural
superposition / destructive interference of two complex waves.

Each hidden node carries two learned weight sets (per predictive-coding.md):

  W  (hierarchical, in PCConnection) — top-down generative prediction
  V  (temporal, in PCNode)           — forward model: μ_t → predicted μ_{t+1}

CVNN specifics
--------------
* Initialisation is in POLAR form  Z = A·exp(iφ)  (random amplitude, random
  phase in [0, 2π)) so the phase is properly distributed from the start.
* Activations are MODULUS non-linearities (modTanh / modReLU): the squashing
  acts on the amplitude only, the phase passes through unchanged.  Plain
  tanh/relu are not analytic and diverge for complex argument.
* Learning uses the COMPLEX CONJUGATE of the pre-synaptic activation in the
  Hebbian outer product (Wirtinger gradient).  Omitting the conjugate makes
  the network diverge.
* All magnitude tests / clips use np.abs() — complex numbers have no order.

Temporal lifecycle (unchanged from the real engine, complex arithmetic):
Phase 1  μ ← predicted_next_mu ; receive/finalize hierarchical π
Phase 2  ε = μ − π
Phase 3  relax μ under error pressure
Phase 4  learn W (PCConnection) and V (here):
             predicted_next_mu = f(V @ f(μ))
             ΔV = η_V · (μ_target − predicted_next) ⊗ conj(f(μ))
"""

from __future__ import annotations

import numpy as np


# ----------------------------------------------------------------------
# Complex initialisation (polar form)
# ----------------------------------------------------------------------

def _polar(rng: np.random.Generator, shape, sigma: float = 0.01) -> np.ndarray:
    """Z = A·exp(iφ) with A ~ N(0, sigma) and φ ~ U[0, 2π).  dtype complex128."""
    amp = rng.normal(0.0, sigma, shape)
    phi = rng.uniform(0.0, 2.0 * np.pi, shape)
    return (amp * np.exp(1j * phi)).astype(np.complex128)


def _clip_mag(z: np.ndarray, clip: float) -> None:
    """Clip a complex array IN PLACE by magnitude (|z| ≤ clip), keeping phase."""
    if clip <= 0.0:
        return
    mag = np.abs(z)
    over = mag > clip
    if np.any(over):
        z[over] *= clip / mag[over]


# ----------------------------------------------------------------------
# Modulus activations (mod-ReLU / mod-tanh) and their amplitude derivatives
# ----------------------------------------------------------------------

def _mod_tanh(z: np.ndarray) -> np.ndarray:
    """tanh applied to the AMPLITUDE only, phase preserved."""
    amp = np.abs(z)
    phase = np.angle(z)
    return np.tanh(amp) * np.exp(1j * phase)


def _mod_tanh_deriv(z: np.ndarray) -> np.ndarray:
    """Derivative acting on the amplitude (phase preserved)."""
    amp = np.abs(z)
    return (1.0 - np.tanh(amp) ** 2) * np.exp(1j * np.angle(z))


def _mod_relu(z: np.ndarray) -> np.ndarray:
    """ReLU applied to the AMPLITUDE only, phase preserved."""
    amp = np.abs(z)
    phase = np.angle(z)
    return np.maximum(0.0, amp) * np.exp(1j * phase)


def _mod_relu_deriv(z: np.ndarray) -> np.ndarray:
    amp = np.abs(z)
    return (amp > 0.0).astype(np.float64) * np.exp(1j * np.angle(z))


def _identity(z: np.ndarray) -> np.ndarray:
    return z


def _identity_deriv(z: np.ndarray) -> np.ndarray:
    return np.ones_like(z)


# "tanh"/"relu" keys are mapped to their MODULUS versions so existing callers
# (PCNode(..., activation="tanh")) transparently get the complex-safe variant.
_ACTIVATIONS = {
    "tanh": (_mod_tanh, _mod_tanh_deriv),
    "modtanh": (_mod_tanh, _mod_tanh_deriv),
    "relu": (_mod_relu, _mod_relu_deriv),
    "modrelu": (_mod_relu, _mod_relu_deriv),
    "identity": (_identity, _identity_deriv),
}


class PCNode:
    """
    A single COMPLEX-VALUED Predictive Coding node with a temporal forward model.

    Internal vectors (shape [dim], dtype complex128):
        μ  (mu)       — current state / representation
        π  (pi)       — aggregated top-down prediction received from connections
        ε  (epsilon)  — prediction error  ε = μ − π  (complex superposition)

    Temporal forward model (shape [dim × dim], complex128):
        V             — maps f(μ_t) → predicted μ_{t+1}
        predicted_next_mu — V's prediction, used to warm-start μ next frame

    Lifecycle per time step (called by PCNetwork) — identical to the real engine.
    """

    def __init__(
        self,
        node_id: str,
        dim: int,
        activation: str = "tanh",
        eta_temporal: float = 0.1,     # learning rate for V
        w_clip_V: float = 3.0,         # MAGNITUDE clip for V
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
        self.mu: np.ndarray = _polar(rng, dim)
        self.pi: np.ndarray = np.zeros(dim, dtype=np.complex128)
        self.epsilon: np.ndarray = np.zeros(dim, dtype=np.complex128)

        # Forward model  V: [dim × dim], complex128.
        # Near-identity persistence prior PLUS a small complex (polar) noise so
        # predicted_next ≈ f(I · f(μ)) ≈ μ before any dynamics are learned; V
        # then learns DEVIATIONS (real motion dynamics) on top.
        self.V: np.ndarray = np.eye(dim, dtype=np.complex128) + _polar(rng, (dim, dim))

        # Temporal buffers (complex128)
        self._prev_mu: np.ndarray = np.zeros(dim, dtype=np.complex128)
        self._predicted_next_mu: np.ndarray = np.zeros(dim, dtype=np.complex128)
        self._prev_f_mu: np.ndarray = np.zeros(dim, dtype=np.complex128)

        # Phase accumulators
        self._pred_sum: np.ndarray = np.zeros(dim, dtype=np.complex128)
        self._pred_count: int = 0
        self._pressure: np.ndarray = np.zeros(dim, dtype=np.complex128)

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
        """Initialise μ from the forward model's prediction (clamped nodes skip)."""
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
            self.pi = np.zeros(self.dim, dtype=np.complex128)
        self._pred_sum = np.zeros(self.dim, dtype=np.complex128)
        self._pred_count = 0

    # ------------------------------------------------------------------
    # Phase 2: Error (complex superposition / destructive interference)
    # ------------------------------------------------------------------

    def compute_error(self) -> None:
        """ε = μ − π  (complex128 natively resolves this as two waves with a π phase shift)."""
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
            self._pressure = np.zeros(self.dim, dtype=np.complex128)
            return
        dmu = -alpha * self.epsilon + self._pressure
        new_mu = self.mu + eta_inf * dmu
        # np.isfinite on complex is True iff BOTH real and imag parts are finite.
        if not np.all(np.isfinite(new_mu)):
            self.mu = np.zeros(self.dim, dtype=np.complex128)
        else:
            self.mu = new_mu
        self._pressure = np.zeros(self.dim, dtype=np.complex128)

    # ------------------------------------------------------------------
    # Phase 4 (temporal): learn V and compute next prediction
    # ------------------------------------------------------------------

    def learn_temporal(self, modulation: float = 1.0) -> None:
        """
        Update the temporal weight matrix V (complex, conjugate Hebbian rule).

        predicted_next = f(V @ f(μ_prev)) ;  target = actual μ at this step.
            δ  = μ_current − predicted_next
            ΔV = η_V · modulation · δ ⊗ conj(f(μ_prev))
        The CONJUGATE of the pre-synaptic activation is REQUIRED in the CVNN
        outer product (Wirtinger gradient); without it the network diverges.

        Clamped nodes have no V to learn.
        """
        if self._clamped:
            return
        delta = self.mu - self._predicted_next_mu                # [dim], complex
        dV = np.outer(delta, np.conjugate(self._prev_f_mu))      # conjugate pre-synaptic
        if np.all(np.isfinite(dV)):
            self.V += self.eta_temporal * modulation * dV
        _clip_mag(self.V, self.w_clip_V)

    # ------------------------------------------------------------------
    # commit_step: snapshot μ and run forward model for next frame
    # ------------------------------------------------------------------

    def commit_step(self) -> None:
        """
        End-of-frame bookkeeping:
          1. Save μ_relaxed as prev_mu (target for V learning next frame).
          2. Forward model: predicted_next_mu = V @ f(μ) — warm-starts μ next frame.
        Clamped nodes (sensors) just snapshot their current value.
        """
        if self._clamped:
            self._prev_mu = self.mu.copy()
            return
        self._prev_f_mu = self._act(self.mu).copy()   # f(μ_t)
        self._prev_mu = self.mu.copy()                 # μ_t
        self._predicted_next_mu = self.V @ self._prev_f_mu   # V @ f(μ_t)

    # ------------------------------------------------------------------
    # Sensor clamping
    # ------------------------------------------------------------------

    def clamp(self, value: np.ndarray) -> None:
        assert value.shape == (self.dim,), f"Expected shape ({self.dim},), got {value.shape}"
        # Real sensor input is lifted into the complex plane (zero imaginary part).
        self.mu = value.astype(np.complex128)
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
        """Re-initialise state to near-zero (polar); keep weights."""
        rng = rng or np.random.default_rng()
        self.mu = _polar(rng, self.dim)
        self.pi = np.zeros(self.dim, dtype=np.complex128)
        self.epsilon = np.zeros(self.dim, dtype=np.complex128)
        self._prev_mu = np.zeros(self.dim, dtype=np.complex128)
        self._predicted_next_mu = np.zeros(self.dim, dtype=np.complex128)
        self._prev_f_mu = np.zeros(self.dim, dtype=np.complex128)
        self._pred_sum = np.zeros(self.dim, dtype=np.complex128)
        self._pred_count = 0
        self._pressure = np.zeros(self.dim, dtype=np.complex128)
        self._clamped = False

    def __repr__(self) -> str:
        clamp_str = " [CLAMPED]" if self._clamped else ""
        return f"PCNode(id={self.id!r}, dim={self.dim}, complex){clamp_str}"


class SensorNode(PCNode):
    """
    Convenience subclass: always clamped, no temporal forward model.
    Call set_input() each time step.  Real input is lifted to complex128 on clamp.
    """

    def __init__(self, node_id: str, dim: int) -> None:
        super().__init__(node_id, dim, activation="identity")
        self._clamped = True

    def set_input(self, value: np.ndarray) -> None:
        self.clamp(value)
