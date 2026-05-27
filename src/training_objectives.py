"""
Training objectives for Phase 1 -- pure NumPy implementations.

Includes:
  - JEPALoss          : Bidirectional JEPA with VICReg variance + covariance
  - ContrastiveLoss   : InfoNCE with projection MLP
  - SFALoss           : Slowness (temporal difference) loss
  - HebbianLoss       : Oja's rule online updates
"""

from __future__ import annotations

import numpy as np


# ==============================================================================
#  JEPA Loss — Bidirectional Prediction + VICReg
# ==============================================================================

class JEPALoss:
    """
    Joint Embedding Predictive Architecture (JEPA) loss with:
    * Bidirectional predictor networks (context -> target, target -> context)
    * VICReg-style variance + covariance penalties
    """

    def __init__(
        self,
        d: int,
        predictor_hidden: int = 256,
        var_eps: float = 1.0,
        cov_coeff: float = 1.0,
        var_coeff: float = 1.0,
        sim_coeff: float = 1.0,
    ):
        """
        Parameters
        ----------
        d : int
            Dimension of the embeddings being compared.
        predictor_hidden : int
            Hidden size of the predictor MLPs.
        var_eps : float
            Target standard deviation for the variance loss (default 1.0).
        cov_coeff : float
            Weight for the covariance loss term.
        var_coeff : float
            Weight for the variance loss term.
        sim_coeff : float
            Weight for the MSE similarity (prediction) loss term.
        """
        self.d = d
        self.predictor_hidden = predictor_hidden
        self.var_eps = var_eps
        self.cov_coeff = cov_coeff
        self.var_coeff = var_coeff
        self.sim_coeff = sim_coeff

        rng = np.random.default_rng(42)

        # Predictor: context -> target  (ProjNet)
        self.W1_ct = rng.standard_normal((d, predictor_hidden)) * np.sqrt(2.0 / d)
        self.b1_ct = np.zeros(predictor_hidden)
        self.W2_ct = rng.standard_normal((predictor_hidden, d)) * np.sqrt(
            2.0 / predictor_hidden
        )
        self.b2_ct = np.zeros(d)

        # Predictor: target -> context  (ProjNet)
        self.W1_tc = rng.standard_normal((d, predictor_hidden)) * np.sqrt(2.0 / d)
        self.b1_tc = np.zeros(predictor_hidden)
        self.W2_tc = rng.standard_normal((predictor_hidden, d)) * np.sqrt(
            2.0 / predictor_hidden
        )
        self.b2_tc = np.zeros(d)

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _l2_norm(x: np.ndarray) -> np.ndarray:
        """L2-normalise along the last axis."""
        norm = np.linalg.norm(x, axis=-1, keepdims=True)
        return x / np.maximum(norm, 1e-12)

    def _predict(self, x: np.ndarray, direction: str) -> np.ndarray:
        """
        Projection MLP:  x -> Linear -> ReLU -> Linear -> L2-norm

        direction : 'ct' (context->target) or 'tc' (target->context)
        """
        if direction == "ct":
            W1, b1, W2, b2 = self.W1_ct, self.b1_ct, self.W2_ct, self.b2_ct
        else:
            W1, b1, W2, b2 = self.W1_tc, self.b1_tc, self.W2_tc, self.b2_tc

        h = np.maximum(x @ W1 + b1, 0.0)          # ReLU
        out = h @ W2 + b2                         # Linear
        return self._l2_norm(out)

    # -- loss terms -----------------------------------------------------

    @staticmethod
    def _variance_loss(z: np.ndarray, eps: float) -> float:
        """VICReg variance loss: encourage std of each dim to be ~eps."""
        std = np.sqrt(z.var(axis=0, ddof=0) + 1e-12)
        return float(np.mean(np.maximum(0.0, eps - std)))

    @staticmethod
    def _covariance_loss(z: np.ndarray) -> float:
        """VICReg covariance loss: off-diagonal covariance should be zero."""
        # Centre
        zc = z - z.mean(axis=0, keepdims=True)
        batch_size = z.shape[0]
        cov = (zc.T @ zc) / (batch_size - 1) if batch_size > 1 else zc.T @ zc
        d = cov.shape[0]
        # Sum of squared off-diagonal entries
        mask = 1.0 - np.eye(d)
        return float(np.sum(cov ** 2 * mask) / d)

    # -- forward / backward ---------------------------------------------

    def forward(self, context: np.ndarray, target: np.ndarray) -> dict:
        """
        Compute all loss terms.

        Parameters
        ----------
        context : np.ndarray, shape (B, d)
        target  : np.ndarray, shape (B, d)

        Returns
        -------
        dict with keys:
            'loss', 'sim_loss', 'var_loss', 'cov_loss',
            'pred_ct', 'pred_tc',             # predicted embeddings
            'intermediates'                   # cached for backward
        """
        # Stop-gradient on targets (standard JEPA practice)
        target_sg = target.copy()

        pred_ct = self._predict(context, "ct")          # predict target from context
        pred_tc = self._predict(target_sg, "tc")        # predict context from target

        # Similarity = negative cosine similarity = MSE on L2-normalised vectors
        sim_ct = np.mean((pred_ct - target_sg) ** 2)
        sim_tc = np.mean((pred_tc - context) ** 2)
        sim_loss = 0.5 * (sim_ct + sim_tc)

        # VICReg on the *predicted* representations
        var_loss = self._variance_loss(pred_ct, self.var_eps) + self._variance_loss(
            pred_tc, self.var_eps
        )
        cov_loss = self._covariance_loss(pred_ct) + self._covariance_loss(pred_tc)

        loss = (
            self.sim_coeff * sim_loss
            + self.var_coeff * var_loss
            + self.cov_coeff * cov_loss
        )

        # Cache intermediates for backward
        # Recompute hidden activations for gradient flow
        h_ct = np.maximum(context @ self.W1_ct + self.b1_ct, 0.0)
        h_tc = np.maximum(target @ self.W1_tc + self.b1_tc, 0.0)

        return {
            "loss": float(loss),
            "sim_loss": float(sim_loss),
            "var_loss": float(var_loss),
            "cov_loss": float(cov_loss),
            "pred_ct": pred_ct,
            "pred_tc": pred_tc,
            "intermediates": {
                "context": context,
                "target": target,
                "h_ct": h_ct,
                "h_tc": h_tc,
                "pred_ct": pred_ct,
                "pred_tc": pred_tc,
                "target_sg": target_sg,
            },
        }

    def backward(self, cached: dict) -> dict:
        """
        Compute gradients w.r.t. predictor weights and the two embeddings.

        Parameters
        ----------
        cached : dict from forward()['intermediates']

        Returns
        -------
        grads : dict with keys for each weight matrix / bias and
                'd_context', 'd_target'
        """
        context = cached["context"]          # (B, d)
        target = cached["target"]            # (B, d)
        target_sg = cached["target_sg"]      # (B, d)
        h_ct = cached["h_ct"]                # (B, H)
        h_tc = cached["h_tc"]                # (B, H)
        pred_ct = cached["pred_ct"]          # (B, d)
        pred_tc = cached["pred_tc"]          # (B, d)

        B = context.shape[0]
        d = self.d
        H = self.predictor_hidden

        # --- Similarity loss gradient (MSE on L2-normalised vectors) ---
        # dL_sim/d_pred_ct = 2 * (pred_ct - target_sg) / B  (mean -> average)
        d_pred_ct = 2.0 * (pred_ct - target_sg) / B * self.sim_coeff * 0.5
        # dL_sim/d_pred_tc = 2 * (pred_tc - context) / B
        d_pred_tc = 2.0 * (pred_tc - context) / B * self.sim_coeff * 0.5

        # --- Variance loss gradient ---
        # d/dz (max(0, eps - std_i)) = -1/(2*std_i) * d/dz var_i   when std_i < eps
        def _var_grad(z: np.ndarray, eps: float) -> np.ndarray:
            std = np.sqrt(z.var(axis=0, ddof=0) + 1e-12)          # (d,)
            mask = (std < eps).astype(z.dtype)                    # (d,)
            # var_i = 1/B * sum_b (z_bi - mu_i)^2
            # d var_i / dz = 2/B * (z - mu)
            dz = -(1.0 / (std + 1e-12)) * mask * (z - z.mean(axis=0, keepdims=True)) * 2.0 / B
            return dz / d                                            # average over dims

        d_pred_ct += _var_grad(pred_ct, self.var_eps) * self.var_coeff
        d_pred_tc += _var_grad(pred_tc, self.var_eps) * self.var_coeff

        # --- Covariance loss gradient ---
        # L_cov = sum_{i!=j} cov_ij^2 / d
        # dL/dz = 2/d * (C - diag(C)) @ z_centred / (B-1)
        def _cov_grad(z: np.ndarray) -> np.ndarray:
            zc = z - z.mean(axis=0, keepdims=True)
            denom = max(B - 1, 1)
            C = (zc.T @ zc) / denom
            mask = 1.0 - np.eye(z.shape[1])
            dC = 2.0 * C * mask / z.shape[1]          # (d, d)
            return (zc @ (dC + dC.T)) / denom         # (B, d)

        d_pred_ct += _cov_grad(pred_ct) * self.cov_coeff
        d_pred_tc += _cov_grad(pred_tc) * self.cov_coeff

        # --- Backprop through L2 normalisation ---
        # y = x / ||x||
        # dy = (I - y y^T) @ dx / ||x||
        def _l2_backward(dy: np.ndarray, y: np.ndarray) -> np.ndarray:
            # dy: (B, d), y: (B, d)
            # dx = dy @ (I - y y^T) / ||x||  but ||x|| = 1/||y||
            # Since y = x/||x||, we have ||x|| = 1 when ||y||=1 (but numerically...)
            # Simpler: grad w.r.t pre-norm vector
            norm = np.linalg.norm(y, axis=-1, keepdims=True)
            # Pre-norm = y * norm, so ||pre_norm|| = norm
            # Using standard formula: d(x/||x||) = (I - xx^T/||x||^2)/||x|| * dx_pre
            # So dx_pre = (I - yy^T) * dy * norm
            return (dy - y * np.sum(dy * y, axis=-1, keepdims=True)) * norm

        # pre-norm outputs
        pre_ct = h_ct @ self.W2_ct + self.b2_ct
        pre_tc = h_tc @ self.W2_tc + self.b2_tc

        d_pre_ct = _l2_backward(d_pred_ct, pred_ct)
        d_pre_tc = _l2_backward(d_pred_tc, pred_tc)

        # --- Linear 2 (W2, b2) ---
        dW2_ct = h_ct.T @ d_pre_ct / B
        db2_ct = d_pre_ct.mean(axis=0)
        dW2_tc = h_tc.T @ d_pre_tc / B
        db2_tc = d_pre_tc.mean(axis=0)

        d_h_ct = d_pre_ct @ self.W2_ct.T
        d_h_tc = d_pre_tc @ self.W2_tc.T

        # --- ReLU ---
        d_h_ct *= (h_ct > 0).astype(float)
        d_h_tc *= (h_tc > 0).astype(float)

        # --- Linear 1 (W1, b1) ---
        dW1_ct = context.T @ d_h_ct / B
        db1_ct = d_h_ct.mean(axis=0)
        dW1_tc = target.T @ d_h_tc / B
        db1_tc = d_h_tc.mean(axis=0)

        d_context = d_h_ct @ self.W1_ct.T
        d_target = d_h_tc @ self.W1_tc.T

        # Also gradient from sim_loss direct path: pred_tc should match context
        d_context += -d_pred_tc * 2.0 / B * self.sim_coeff * 0.5  # From sim_tc gradient w.r.t context
        d_target += -d_pred_ct * 2.0 / B * self.sim_coeff * 0.5   # From sim_ct gradient w.r.t target

        return {
            "W1_ct": dW1_ct,
            "b1_ct": db1_ct,
            "W2_ct": dW2_ct,
            "b2_ct": db2_ct,
            "W1_tc": dW1_tc,
            "b1_tc": db1_tc,
            "W2_tc": dW2_tc,
            "b2_tc": db2_tc,
            "d_context": d_context,
            "d_target": d_target,
        }

    def loss_and_grads(self, context: np.ndarray, target: np.ndarray) -> dict:
        """Convenience: forward + backward in one call."""
        fwd = self.forward(context, target)
        grads = self.backward(fwd["intermediates"])
        return {**fwd, **grads}


# ==============================================================================
#  Contrastive Loss — InfoNCE with Projection MLP
# ==============================================================================

class ContrastiveLoss:
    """
    Standard InfoNCE (NT-Xent) contrastive loss with a projection MLP.

    Given two augmented views of the same sample, we feed them through an
    encoder, apply a projection head, and maximise agreement between positive
    pairs while pushing negatives apart.
    """

    def __init__(
        self,
        d: int,
        proj_hidden: int = 256,
        temperature: float = 0.07,
    ):
        """
        Parameters
        ----------
        d : int
            Encoder output dimension.
        proj_hidden : int
            Hidden dimension of the 2-layer projection MLP.
        temperature : float
            Temperature parameter tau for the softmax.
        """
        self.d = d
        self.proj_hidden = proj_hidden
        self.temperature = temperature

        rng = np.random.default_rng(43)

        # Projection MLP: d -> proj_hidden -> d
        self.W1 = rng.standard_normal((d, proj_hidden)) * np.sqrt(2.0 / d)
        self.b1 = np.zeros(proj_hidden)
        self.W2 = rng.standard_normal((proj_hidden, d)) * np.sqrt(2.0 / proj_hidden)
        self.b2 = np.zeros(d)

    def _project(self, z: np.ndarray) -> np.ndarray:
        """Projection MLP with ReLU and L2-normalisation."""
        h = np.maximum(z @ self.W1 + self.b1, 0.0)
        out = h @ self.W2 + self.b2
        # L2-normalise
        norm = np.linalg.norm(out, axis=-1, keepdims=True)
        return out / np.maximum(norm, 1e-12)

    def forward(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """
        Compute InfoNCE loss between two sets of embeddings.

        Parameters
        ----------
        z1, z2 : np.ndarray, shape (B, d)
            Encoded representations of the two augmented views.

        Returns
        -------
        dict with keys 'loss', 'proj1', 'proj2', 'intermediates'
        """
        B = z1.shape[0]

        p1 = self._project(z1)          # (B, d)
        p2 = self._project(z2)          # (B, d)

        # Similarity matrix: (B, B)
        # pos[i,j] = p1[i] @ p2[j]
        logits = p1 @ p2.T / self.temperature    # (B, B)

        # For each item in view 1, the positive is the diagonal in view 2
        # Loss = -log( exp(pos) / sum_j exp(logits[i,j]) )
        logits_max = np.max(logits, axis=1, keepdims=True)
        logits_stable = logits - logits_max       # numerical stability
        exp_logits = np.exp(logits_stable)
        sum_exp = np.sum(exp_logits, axis=1)

        # Positive logits (diagonal)
        pos_logits = np.diag(logits_stable)
        log_prob = pos_logits - np.log(sum_exp)
        loss = -np.mean(log_prob)

        # Cache for backward
        h1 = np.maximum(z1 @ self.W1 + self.b1, 0.0)
        h2 = np.maximum(z2 @ self.W1 + self.b1, 0.0)
        pre_norm1 = h1 @ self.W2 + self.b2
        pre_norm2 = h2 @ self.W2 + self.b2

        return {
            "loss": float(loss),
            "proj1": p1,
            "proj2": p2,
            "intermediates": {
                "z1": z1,
                "z2": z2,
                "p1": p1,
                "p2": p2,
                "logits": logits,
                "exp_logits": exp_logits,
                "sum_exp": sum_exp,
                "h1": h1,
                "h2": h2,
                "pre_norm1": pre_norm1,
                "pre_norm2": pre_norm2,
            },
        }

    def backward(self, cached: dict) -> dict:
        """
        Compute gradients of InfoNCE w.r.t. projection weights and encodings.

        Returns
        -------
        grads : dict
        """
        z1 = cached["z1"]              # (B, d)
        z2 = cached["z2"]              # (B, d)
        p1 = cached["p1"]              # (B, d)
        p2 = cached["p2"]              # (B, d)
        logits = cached["logits"]      # (B, B)
        exp_logits = cached["exp_logits"]  # (B, B)
        sum_exp = cached["sum_exp"]    # (B,)
        h1 = cached["h1"]              # (B, H)
        h2 = cached["h2"]              # (B, H)
        pre_norm1 = cached["pre_norm1"]
        pre_norm2 = cached["pre_norm2"]

        B = z1.shape[0]
        d = self.d
        H = self.proj_hidden

        # --- Gradient of loss w.r.t. logits ---
        # softmax(logits) along axis=1
        softmax = exp_logits / (sum_exp[:, None] + 1e-12)      # (B, B)
        # For positive pairs (diagonal), subtract 1
        softmax[np.arange(B), np.arange(B)] -= 1.0
        # Average over batch
        d_logits = softmax / B                                  # (B, B)

        # d_logits[i,j] = d/d(logits_ij) of loss
        # logits = p1 @ p2^T / tau
        # dL/dp1 = dL/d_logits @ p2 / tau
        # dL/dp2 = dL/d_logits.T @ p1 / tau
        d_p1 = d_logits @ p2 / self.temperature                  # (B, d)
        d_p2 = d_logits.T @ p1 / self.temperature                # (B, d)

        # --- Backprop through L2 normalisation ---
        def _l2_backward(dy, y):
            norm = np.linalg.norm(y, axis=-1, keepdims=True)
            return (dy - y * np.sum(dy * y, axis=-1, keepdims=True)) * norm

        d_pre1 = _l2_backward(d_p1, p1)
        d_pre2 = _l2_backward(d_p2, p2)

        # --- Linear 2 (W2, b2) ---
        dW2 = (h1.T @ d_pre1 + h2.T @ d_pre2) / B
        db2 = (d_pre1 + d_pre2).mean(axis=0)

        d_h1 = d_pre1 @ self.W2.T
        d_h2 = d_pre2 @ self.W2.T

        # --- ReLU ---
        d_h1 *= (h1 > 0).astype(float)
        d_h2 *= (h2 > 0).astype(float)

        # --- Linear 1 (W1, b1) ---
        dW1 = (z1.T @ d_h1 + z2.T @ d_h2) / B
        db1 = (d_h1 + d_h2).mean(axis=0)

        d_z1 = d_h1 @ self.W1.T
        d_z2 = d_h2 @ self.W1.T

        return {
            "W1": dW1,
            "b1": db1,
            "W2": dW2,
            "b2": db2,
            "d_z1": d_z1,
            "d_z2": d_z2,
        }

    def loss_and_grads(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """Convenience: forward + backward in one call."""
        fwd = self.forward(z1, z2)
        grads = self.backward(fwd["intermediates"])
        return {**fwd, **grads}


# ==============================================================================
#  SFA Loss — Slowness (temporal difference)
# ==============================================================================

class SFALoss:
    """
    Slow Feature Analysis loss.

    Encourages consecutive temporal representations to change slowly:
        L = mean( ||z[t] - z[t-1]||^2 )

    Optionally includes a decorrelation / whitening term to avoid the
    trivial solution z = constant.
    """

    def __init__(self, delta_order: int = 1, whitening_coeff: float = 0.01):
        """
        Parameters
        ----------
        delta_order : int
            Temporal difference order (1 = first difference, 2 = second, ...).
        whitening_coeff : float
            Weight for the covariance decorrelation penalty
            (encourages features with unit variance and zero cross-covariance).
        """
        self.delta_order = delta_order
        self.whitening_coeff = whitening_coeff

    def forward(self, z: np.ndarray) -> dict:
        """
        Parameters
        ----------
        z : np.ndarray, shape (T, d) or (B, T, d)
            Temporal sequence of representations.
            If 3-D, slowness is computed per-sample and averaged.

        Returns
        -------
        dict with 'loss', 'slowness', 'whitening', 'dL_dz'
        """
        if z.ndim == 2:
            z = z[None, ...]           # (1, T, d)
            squeeze = True
        else:
            squeeze = False

        B, T, d = z.shape

        # --- Slowness: mean squared temporal difference ---
        deltas = z[:, self.delta_order :, :] - z[:, : T - self.delta_order, :]
        slowness = float(np.mean(deltas ** 2))

        # --- Whitening: encourage Cov(z) ≈ I ---
        # Pool across batch and time
        z_flat = z.reshape(-1, d)
        zc = z_flat - z_flat.mean(axis=0, keepdims=True)
        denom = max(z_flat.shape[0] - 1, 1)
        cov = (zc.T @ zc) / denom
        # Frobenius distance to identity
        whitening = float(np.mean((cov - np.eye(d)) ** 2))

        loss = slowness + self.whitening_coeff * whitening

        # --- Gradient w.r.t. z ---
        dL_dz = np.zeros_like(z)

        # Slowness gradient
        # L_slow = 1/(B*(T-delta)*d) * sum (z[t] - z[t-delta])^2
        coeff = 2.0 / (B * (T - self.delta_order) * d)
        dL_dz[:, self.delta_order :, :] += coeff * deltas
        dL_dz[:, : T - self.delta_order, :] -= coeff * deltas

        # Whitening gradient
        # L_white = mean((C - I)^2)
        # dL/dz = 4/denom * zc @ (C - I)  (averaged properly)
        if self.whitening_coeff > 0:
            d_white = (4.0 / (denom * d)) * zc @ (cov - np.eye(d))
            dL_dz += self.whitening_coeff * d_white.reshape(B, T, d)

        if squeeze:
            dL_dz = dL_dz[0]

        return {
            "loss": float(loss),
            "slowness": float(slowness),
            "whitening": float(whitening),
            "dL_dz": dL_dz,
        }


# ==============================================================================
#  Hebbian Loss — Oja's Rule
# ==============================================================================

class HebbianLoss:
    """
    Online Hebbian learning via Oja's rule.

    Instead of a global loss, this maintains weight matrices that are updated
    with each batch using Oja's rule:

        W <- W + lr * (y x^T - W y y^T)

    where x is the input, y = W x is the output, and the second term provides
    the stabilising decay that prevents unbounded growth.

    This is useful for unsupervised feature extraction in an online setting.
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        lr: float = 0.001,
        seed: int = 44,
    ):
        """
        Parameters
        ----------
        in_dim : int
            Input dimensionality.
        out_dim : int
            Output dimensionality (number of features to learn).
        lr : float
            Learning rate for Oja's updates.
        seed : int
            RNG seed for weight initialisation.
        """
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.lr = lr

        rng = np.random.default_rng(seed)
        # Small random initial weights
        scale = np.sqrt(1.0 / in_dim)
        self.W = rng.standard_normal((out_dim, in_dim)) * scale

    def forward(self, x: np.ndarray) -> dict:
        """
        Compute the Hebbian output y = W @ x.

        Parameters
        ----------
        x : np.ndarray, shape (B, in_dim) or (in_dim,)

        Returns
        -------
        dict with 'y', 'x'
        """
        if x.ndim == 1:
            x = x[None, :]            # (1, in_dim)
        y = x @ self.W.T              # (B, out_dim)
        return {"y": y, "x": x}

    def update(self, x: np.ndarray) -> dict:
        """
        Apply one Oja's rule update step.

        Parameters
        ----------
        x : np.ndarray, shape (B, in_dim)

        Returns
        -------
        dict with 'delta_W', 'y'
        """
        if x.ndim == 1:
            x = x[None, :]

        B = x.shape[0]
        y = x @ self.W.T              # (B, out_dim)

        # Oja's rule:  dW = y^T x - y^T y W   (averaged over batch)
        # In matrix form:
        #   dW = (y^T @ x) / B  -  ((y^T @ y) / B) @ W
        yTx = y.T @ x / B             # (out_dim, in_dim)
        yTy = y.T @ y / B             # (out_dim, out_dim)

        delta_W = yTx - yTy @ self.W
        self.W += self.lr * delta_W

        return {
            "delta_W": delta_W,
            "y": y,
            "W_new": self.W.copy(),
        }

    def loss(self, x: np.ndarray) -> float:
        """
        A proxy "loss" that can be monitored: negative signal variance
        (we want features with maximal variance, subject to orthogonality).

        Returns the negative mean output variance so that *lower* is better
        (conventional loss semantics).
        """
        if x.ndim == 1:
            x = x[None, :]
        y = x @ self.W.T
        per_feature_var = y.var(axis=0)
        return float(-np.mean(per_feature_var))
