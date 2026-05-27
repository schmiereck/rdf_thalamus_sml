"""
Training objectives for Phase 1 -- pure NumPy implementations.

Includes:
  - JEPALoss          : Bidirectional JEPA with per-layer predictors + VICReg
  - ContrastiveLoss   : NT-Xent with 3-layer projection MLP
  - SFALoss           : Slowness (temporal difference) + variance penalty
  - HebbianLoss       : Oja's rule online updates on encoder nodes
"""

from __future__ import annotations

import numpy as np


# ==============================================================================
#  Adam helper
# ==============================================================================

class _Adam:
    """Simple Adam optimizer for a dict of parameters."""

    def __init__(
        self,
        params: dict,
        lr: float = 1e-3,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}

    def step(self, params: dict, grads: dict) -> None:
        self.t += 1
        for k in params:
            self.m[k] = self.beta1 * self.m[k] + (1.0 - self.beta1) * grads[k]
            self.v[k] = self.beta2 * self.v[k] + (1.0 - self.beta2) * (grads[k] ** 2)
            m_hat = self.m[k] / (1.0 - self.beta1 ** self.t)
            v_hat = self.v[k] / (1.0 - self.beta2 ** self.t)
            params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


# ==============================================================================
#  JEPA Loss
# ==============================================================================

class JEPALoss:
    """
    Joint Embedding Predictive Architecture (JEPA) loss with:
    * Per-layer predictor networks (each layer has its own predictor)
    * Bidirectional prediction between adjacent layers
    * VICReg-style variance + covariance penalties (weight 25.0 each)
    * Adam updates for predictors
    """

    def __init__(self, n_layers: int, d: int, temp: float = 0.5, lr: float = 1e-3):
        self.n_layers = n_layers
        self.d = d
        self.temp = temp
        self.lr = lr
        self.hidden = 4 * d  # default hidden size for predictors

        # Per-layer predictors: each is a 2-layer MLP d -> hidden -> d
        self.predictors: list[dict] = []
        self.adams: list[_Adam] = []
        rng = np.random.default_rng(42)
        for _ in range(n_layers):
            W1 = rng.standard_normal((d, self.hidden)) * np.sqrt(2.0 / d)
            b1 = np.zeros(self.hidden)
            W2 = rng.standard_normal((self.hidden, d)) * np.sqrt(2.0 / self.hidden)
            b2 = np.zeros(d)
            params = {"W1": W1, "b1": b1, "W2": W2, "b2": b2}
            self.predictors.append(params)
            self.adams.append(_Adam(params, lr=lr))

    @staticmethod
    def _l2_norm(x: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(x, axis=-1, keepdims=True)
        return x / np.maximum(norm, 1e-12)

    def _predict(
        self, x: np.ndarray, l: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Forward pass through predictor l. Returns (prediction, hidden, pre_norm)."""
        p = self.predictors[l]
        h = np.maximum(x @ p["W1"] + p["b1"], 0.0)
        pre_norm = h @ p["W2"] + p["b2"]
        out = self._l2_norm(pre_norm)
        return out, h, pre_norm

    @staticmethod
    def _variance_loss(z: np.ndarray, eps: float = 1.0) -> float:
        std = np.sqrt(z.var(axis=0, ddof=0) + 1e-12)
        return float(np.mean(np.maximum(0.0, eps - std)))

    @staticmethod
    def _covariance_loss(z: np.ndarray) -> float:
        zc = z - z.mean(axis=0, keepdims=True)
        B = z.shape[0]
        cov = (zc.T @ zc) / max(B - 1, 1)
        d = cov.shape[0]
        mask = 1.0 - np.eye(d)
        return float(np.sum(cov ** 2 * mask) / d)

    def _predictor_grads(
        self,
        x: np.ndarray,
        target: np.ndarray,
        pred: np.ndarray,
        h: np.ndarray,
        pre_norm: np.ndarray,
        params: dict,
    ) -> dict:
        """Compute gradients for a single predictor."""
        B = x.shape[0]
        d = self.d
        H = self.hidden

        # MSE gradient on L2-normalised vectors
        d_pred = 2.0 * (pred - target) / B

        # Variance gradient
        std = np.sqrt(pred.var(axis=0, ddof=0) + 1e-12)
        mask = (std < 1.0).astype(float)
        dz_var = (
            -(1.0 / (std + 1e-12))
            * mask
            * (pred - pred.mean(axis=0, keepdims=True))
            * 2.0
            / B
        )
        dz_var = dz_var / d
        d_pred += 25.0 * dz_var

        # Covariance gradient
        zc = pred - pred.mean(axis=0, keepdims=True)
        denom = max(B - 1, 1)
        cov = (zc.T @ zc) / denom
        mask = 1.0 - np.eye(d)
        dC = 2.0 * cov * mask / d
        dz_cov = (zc @ (dC + dC.T)) / denom
        d_pred += 25.0 * dz_cov

        # Backprop through L2 norm
        norm = np.linalg.norm(pre_norm, axis=-1, keepdims=True)
        d_pre = (d_pred - pred * np.sum(d_pred * pred, axis=-1, keepdims=True)) * norm

        # Linear 2
        dW2 = h.T @ d_pre / B
        db2 = d_pre.mean(axis=0)
        d_h = d_pre @ params["W2"].T

        # ReLU
        d_h *= (h > 0).astype(float)

        # Linear 1
        dW1 = x.T @ d_h / B
        db1 = d_h.mean(axis=0)

        return {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}

    def forward(self, layer_reps: list[np.ndarray]) -> dict:
        """
        Compute JEPA loss for a stack of layer representations.

        Parameters
        ----------
        layer_reps : list of np.ndarray, length n_layers
            Each array has shape (B, d).

        Returns
        -------
        dict with loss, sim_loss, var_loss, cov_loss, and intermediates.
        """
        total_loss = 0.0
        total_sim = 0.0
        total_var = 0.0
        total_cov = 0.0

        all_preds = []
        all_hiddens = []
        all_pre_norms = []

        for l in range(self.n_layers - 1):
            rep_l = layer_reps[l]
            rep_l1 = layer_reps[l + 1]

            # Forward: predict l+1 from l
            pred_f, h_f, pre_f = self._predict(rep_l, l)
            # Backward: predict l from l+1
            pred_b, h_b, pre_b = self._predict(rep_l1, l + 1)

            # Similarity
            sim_f = np.mean((pred_f - rep_l1) ** 2)
            sim_b = np.mean((pred_b - rep_l) ** 2)
            sim_loss = 0.5 * (sim_f + sim_b)

            # VICReg
            var_loss = self._variance_loss(pred_f) + self._variance_loss(pred_b)
            cov_loss = self._covariance_loss(pred_f) + self._covariance_loss(pred_b)

            loss = sim_loss / self.temp + 25.0 * var_loss + 25.0 * cov_loss

            total_loss += loss
            total_sim += sim_loss
            total_var += var_loss
            total_cov += cov_loss

            all_preds.append((pred_f, pred_b))
            all_hiddens.append((h_f, h_b))
            all_pre_norms.append((pre_f, pre_b))

        n_pairs = self.n_layers - 1
        if n_pairs > 0:
            total_loss /= n_pairs
            total_sim /= n_pairs
            total_var /= n_pairs
            total_cov /= n_pairs

        return {
            "loss": float(total_loss),
            "sim_loss": float(total_sim),
            "var_loss": float(total_var),
            "cov_loss": float(total_cov),
            "intermediates": {
                "layer_reps": layer_reps,
                "preds": all_preds,
                "hiddens": all_hiddens,
                "pre_norms": all_pre_norms,
            },
        }

    def backward(self, cached: dict) -> list[dict | None]:
        """Compute gradients for all predictors."""
        layer_reps = cached["layer_reps"]
        all_preds = cached["preds"]
        all_hiddens = cached["hiddens"]
        all_pre_norms = cached["pre_norms"]

        all_grads: list[dict | None] = [None] * self.n_layers

        for l in range(self.n_layers - 1):
            rep_l = layer_reps[l]
            rep_l1 = layer_reps[l + 1]
            pred_f, pred_b = all_preds[l]
            h_f, h_b = all_hiddens[l]
            pre_f, pre_b = all_pre_norms[l]

            # Forward predictor gradients (predictor[l])
            grads_f = self._predictor_grads(
                rep_l, rep_l1, pred_f, h_f, pre_f, self.predictors[l]
            )

            # Backward predictor gradients (predictor[l+1])
            grads_b = self._predictor_grads(
                rep_l1, rep_l, pred_b, h_b, pre_b, self.predictors[l + 1]
            )

            if all_grads[l] is None:
                all_grads[l] = grads_f
            else:
                for k in grads_f:
                    all_grads[l][k] += grads_f[k]  # type: ignore[index]

            if all_grads[l + 1] is None:
                all_grads[l + 1] = grads_b
            else:
                for k in grads_b:
                    all_grads[l + 1][k] += grads_b[k]  # type: ignore[index]

        # Average gradients where predictors were used twice
        for l in range(1, self.n_layers - 1):
            if all_grads[l] is not None:
                for k in all_grads[l]:  # type: ignore[index]
                    all_grads[l][k] /= 2.0  # type: ignore[index]

        return all_grads

    def step(self, layer_reps: list[np.ndarray]) -> dict:
        """Forward, backward, and Adam update."""
        fwd = self.forward(layer_reps)
        grads = self.backward(fwd["intermediates"])

        for l in range(self.n_layers):
            if grads[l] is not None:
                self.adams[l].step(self.predictors[l], grads[l])

        return fwd

    def loss_and_grads(self, layer_reps: list[np.ndarray]) -> dict:
        """Convenience: forward + backward."""
        fwd = self.forward(layer_reps)
        grads = self.backward(fwd["intermediates"])
        return {**fwd, "grads": grads}


# ==============================================================================
#  Contrastive Loss
# ==============================================================================

class ContrastiveLoss:
    """
    NT-Xent contrastive loss with a 3-layer projection MLP:
    d -> 10*d -> 5*d -> 2.5*d, with ReLU and L2 normalization.
    """

    def __init__(self, d: int, temp: float = 0.5, lr: float = 1e-3):
        self.d = d
        self.temp = temp
        self.lr = lr
        self.h1 = 10 * d
        self.h2 = 5 * d
        self.d_proj = int(2.5 * d)

        rng = np.random.default_rng(43)

        self.W1 = rng.standard_normal((d, self.h1)) * np.sqrt(2.0 / d)
        self.b1 = np.zeros(self.h1)
        self.W2 = rng.standard_normal((self.h1, self.h2)) * np.sqrt(2.0 / self.h1)
        self.b2 = np.zeros(self.h2)
        self.W3 = rng.standard_normal((self.h2, self.d_proj)) * np.sqrt(2.0 / self.h2)
        self.b3 = np.zeros(self.d_proj)

        params = {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
            "W3": self.W3,
            "b3": self.b3,
        }
        self.adam = _Adam(params, lr=lr)

    def _project(
        self, z: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Projection MLP with ReLU and L2 normalization.
        Returns (proj, h1, h2, pre_norm).
        """
        h1 = np.maximum(z @ self.W1 + self.b1, 0.0)
        h2 = np.maximum(h1 @ self.W2 + self.b2, 0.0)
        pre_norm = h2 @ self.W3 + self.b3
        norm = np.linalg.norm(pre_norm, axis=-1, keepdims=True)
        proj = pre_norm / np.maximum(norm, 1e-12)
        return proj, h1, h2, pre_norm

    def forward(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """
        Compute NT-Xent loss between two augmented views.

        Parameters
        ----------
        z1, z2 : np.ndarray, shape (B, d)

        Returns
        -------
        dict with loss, proj, and intermediates.
        """
        B = z1.shape[0]

        # Stack views: original + augmented
        z = np.concatenate([z1, z2], axis=0)  # (2B, d)

        p, h1, h2, pre_norm = self._project(z)  # (2B, d_proj)

        # Similarity matrix
        logits = p @ p.T / self.temp  # (2B, 2B)

        # Mask out self-similarity
        mask_self = np.eye(2 * B, dtype=bool)
        logits_masked = np.where(mask_self, -1e9, logits)

        # Positive pairs: for i, positive is at (i+B) % 2B
        pos_indices = (np.arange(2 * B) + B) % (2 * B)

        # Numerical stability
        logits_max = np.max(logits_masked, axis=1, keepdims=True)
        logits_stable = logits_masked - logits_max

        exp_logits = np.exp(logits_stable)
        sum_exp = np.sum(exp_logits, axis=1)

        pos_logits = logits_stable[np.arange(2 * B), pos_indices]
        log_prob = pos_logits - np.log(sum_exp)
        loss = -np.mean(log_prob)

        return {
            "loss": float(loss),
            "proj": p,
            "intermediates": {
                "z1": z1,
                "z2": z2,
                "z": z,
                "p": p,
                "h1": h1,
                "h2": h2,
                "pre_norm": pre_norm,
                "logits": logits_masked,
                "exp_logits": exp_logits,
                "sum_exp": sum_exp,
                "pos_indices": pos_indices,
            },
        }

    def backward(self, cached: dict) -> dict:
        """Compute gradients for projection MLP and input representations."""
        z1 = cached["z1"]
        z2 = cached["z2"]
        z = cached["z"]
        p = cached["p"]
        h1 = cached["h1"]
        h2 = cached["h2"]
        pre_norm = cached["pre_norm"]
        exp_logits = cached["exp_logits"]
        sum_exp = cached["sum_exp"]
        pos_indices = cached["pos_indices"]

        B_total = z.shape[0]  # 2B
        d = self.d
        H1 = self.h1
        H2 = self.h2
        D_proj = self.d_proj

        # Gradient w.r.t. logits
        softmax = exp_logits / (sum_exp[:, None] + 1e-12)
        softmax[np.arange(B_total), pos_indices] -= 1.0
        d_logits = softmax / B_total

        # Gradient w.r.t. projected representations
        d_p = (d_logits @ p + d_logits.T @ p) / self.temp

        # Backprop through L2 norm
        norm = np.linalg.norm(pre_norm, axis=-1, keepdims=True)
        d_pre = (d_p - p * np.sum(d_p * p, axis=-1, keepdims=True)) * norm

        # Linear 3
        dW3 = h2.T @ d_pre / B_total
        db3 = d_pre.mean(axis=0)
        d_h2 = d_pre @ self.W3.T

        # ReLU 2
        d_h2 *= (h2 > 0).astype(float)

        # Linear 2
        dW2 = h1.T @ d_h2 / B_total
        db2 = d_h2.mean(axis=0)
        d_h1 = d_h2 @ self.W2.T

        # ReLU 1
        d_h1 *= (h1 > 0).astype(float)

        # Linear 1
        dW1 = z.T @ d_h1 / B_total
        db1 = d_h1.mean(axis=0)
        d_z = d_h1 @ self.W1.T

        d_z1 = d_z[: B_total // 2]
        d_z2 = d_z[B_total // 2 :]

        return {
            "W1": dW1,
            "b1": db1,
            "W2": dW2,
            "b2": db2,
            "W3": dW3,
            "b3": db3,
            "d_z1": d_z1,
            "d_z2": d_z2,
        }

    def step(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """Forward, backward, and Adam update."""
        fwd = self.forward(z1, z2)
        grads = self.backward(fwd["intermediates"])

        params = {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
            "W3": self.W3,
            "b3": self.b3,
        }
        grad_params = {k: grads[k] for k in params}
        self.adam.step(params, grad_params)

        return fwd

    def loss_and_grads(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """Convenience: forward + backward."""
        fwd = self.forward(z1, z2)
        grads = self.backward(fwd["intermediates"])
        return {**fwd, **grads}


# ==============================================================================
#  SFA Loss
# ==============================================================================

class SFALoss:
    """
    Slow Feature Analysis loss.

    Encourages consecutive temporal representations to change slowly:
        L_slowness = mean(||z[t] - z[t-delta]||^2)

    Includes a variance penalty to avoid the trivial solution:
        L_var = mean(max(0, 1 - std_i)^2)

    Total loss = L_slowness + lambda_var * L_var
    """

    def __init__(self, delta_order: int = 1, lambda_var: float = 25.0):
        self.delta_order = delta_order
        self.lambda_var = lambda_var

    def forward(self, z: np.ndarray) -> dict:
        """
        Parameters
        ----------
        z : np.ndarray, shape (T, d) or (B, T, d)

        Returns
        -------
        dict with loss, slowness, variance, dL_dz
        """
        if z.ndim == 2:
            z = z[None, ...]
            squeeze = True
        else:
            squeeze = False

        B, T, d = z.shape

        if T <= self.delta_order:
            slowness = 0.0
            var_penalty = 0.0
            loss = 0.0
            dL_dz = np.zeros_like(z)
            if squeeze:
                dL_dz = dL_dz[0]
            return {
                "loss": float(loss),
                "slowness": float(slowness),
                "variance": float(var_penalty),
                "dL_dz": dL_dz,
            }

        # Slowness: MSE of temporal differences
        deltas = z[:, self.delta_order :, :] - z[:, : T - self.delta_order, :]
        slowness = float(np.mean(deltas ** 2))

        # Variance penalty: encourage std of each dim to be ~1
        z_flat = z.reshape(-1, d)
        std = np.sqrt(z_flat.var(axis=0, ddof=0) + 1e-12)
        var_penalty = float(np.mean(np.maximum(0.0, 1.0 - std) ** 2))

        loss = slowness + self.lambda_var * var_penalty

        # Gradients
        dL_dz = np.zeros_like(z)

        # Slowness gradient
        coeff = 2.0 / (B * (T - self.delta_order) * d)
        dL_dz[:, self.delta_order :, :] += coeff * deltas
        dL_dz[:, : T - self.delta_order, :] -= coeff * deltas

        # Variance penalty gradient
        N = B * T
        mu = z_flat.mean(axis=0, keepdims=True)
        mask = (std < 1.0).astype(float)
        dz_var = (
            -2.0 * (1.0 - std) * mask / (std + 1e-12) * (z_flat - mu) / N
        )
        dz_var = dz_var / d
        dL_dz += self.lambda_var * dz_var.reshape(B, T, d)

        if squeeze:
            dL_dz = dL_dz[0]

        return {
            "loss": loss,
            "slowness": slowness,
            "variance": var_penalty,
            "dL_dz": dL_dz,
        }


# ==============================================================================
#  Hebbian Loss
# ==============================================================================

class HebbianLoss:
    """
    Online Hebbian learning via Oja's rule applied directly to encoder nodes.

    For each node in the encoder, updates W_enc using:
        W_enc <- W_enc + eta * (y^T @ x / B - (y^T @ y / B) @ W_enc)

    where x is the flattened node input and y is the node output (code).

    Returns negative mean output variance as a monitoring loss.
    """

    def __init__(self, eta: float = 1e-3):
        self.eta = eta

    def update(self, encoder, x_binary: np.ndarray) -> float:
        """
        Apply Oja's rule to all nodes in the encoder.

        Parameters
        ----------
        encoder : HierarchicalEncoder
        x_binary : np.ndarray, shape (B, n_input)

        Returns
        -------
        monitoring_loss : float
            Negative mean output variance across all nodes.
        """
        # Run forward pass with intermediates
        fwd = encoder.forward_with_intermediates(x_binary)
        node_inputs = fwd["node_inputs"]  # list of (B, n_nodes_l, 3, d)

        total_var = 0.0
        total_features = 0

        for l in range(encoder.n_layers):
            n_nodes = encoder.n_nodes_per_layer[l]
            layer_node_inputs = node_inputs[l]  # (B, n_nodes, 3, d)
            B = layer_node_inputs.shape[0]

            if encoder.sharing_mode == "none":
                for p in range(n_nodes):
                    x_3d = layer_node_inputs[:, p, :, :]  # (B, 3, d)
                    node = encoder.nodes[l][p]

                    # Forward to get code
                    y = node.forward(x_3d)  # (B, d_out)

                    # Flatten input
                    x_flat = x_3d.reshape(B, -1)  # (B, d_in)

                    # Oja's rule
                    yTx = y.T @ x_flat / B  # (d_out, d_in)
                    yTy = y.T @ y / B  # (d_out, d_out)

                    delta_W = yTx - yTy @ node.W_enc
                    node.W_enc += self.eta * delta_W
                    node.b_enc += self.eta * y.mean(axis=0)

                    # Monitoring: output variance
                    per_feature_var = y.var(axis=0)
                    total_var += np.sum(per_feature_var)
                    total_features += node.d_out
            else:
                node = encoder.layer_nodes[l]
                accum_delta_W = np.zeros_like(node.W_enc)
                accum_delta_b = np.zeros_like(node.b_enc)

                for p in range(n_nodes):
                    x_3d = layer_node_inputs[:, p, :, :]  # (B, 3, d)

                    # Forward to get code
                    y = node.forward(x_3d)  # (B, d_out)

                    # Flatten input
                    x_flat = x_3d.reshape(B, -1)  # (B, d_in)

                    # Oja's rule (accumulate, apply once)
                    yTx = y.T @ x_flat / B  # (d_out, d_in)
                    yTy = y.T @ y / B  # (d_out, d_out)

                    delta_W = yTx - yTy @ node.W_enc
                    accum_delta_W += delta_W
                    accum_delta_b += y.mean(axis=0)

                    # Monitoring: output variance
                    per_feature_var = y.var(axis=0)
                    total_var += np.sum(per_feature_var)
                    total_features += node.d_out

                node.W_enc += self.eta * accum_delta_W / n_nodes
                node.b_enc += self.eta * accum_delta_b / n_nodes

        monitoring_loss = -total_var / max(total_features, 1)
        return float(monitoring_loss)

    def __call__(self, encoder, x_binary: np.ndarray) -> float:
        return self.update(encoder, x_binary)
