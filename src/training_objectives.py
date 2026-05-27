"""
Training objectives for Phase 1 -- pure NumPy implementations.

Includes:
  - JEPALoss          : Spatial bidirectional JEPA with per-layer linear predictors + VICReg
  - ContrastiveLoss   : NT-Xent with 2-layer projection MLP
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
    * Per-layer linear predictors (d -> d)
    * Spatial bidirectional prediction between adjacent positions within each layer
    * VICReg-style variance + covariance penalties (weight 25.0 each)
    * Adam updates for predictors
    """

    def __init__(self, n_layers: int, d: int, lr: float = 1e-3):
        self.n_layers = n_layers
        self.d = d
        self.lr = lr

        # Per-layer linear predictors: W_pred (d, d), b_pred (d,)
        self.predictors: list[dict] = []
        self.adams: list[_Adam] = []
        rng = np.random.default_rng(42)
        for _ in range(n_layers):
            W_pred = rng.standard_normal((d, d)) * np.sqrt(2.0 / d)
            b_pred = np.zeros(d)
            params = {"W_pred": W_pred, "b_pred": b_pred}
            self.predictors.append(params)
            self.adams.append(_Adam(params, lr=lr))

    @staticmethod
    def _variance_loss(z: np.ndarray, eps: float = 1.0) -> float:
        """
        Variance penalty: mean over dimensions of max(0, 1 - std_j).
        z has shape (..., d); std is computed over all elements except the last dim.
        """
        M = np.prod(z.shape[:-1])
        z_flat = z.reshape(-1, z.shape[-1])
        std = np.sqrt(z_flat.var(axis=0, ddof=0) + 1e-12)
        return float(np.mean(np.maximum(0.0, eps - std)))

    @staticmethod
    def _covariance_loss(z: np.ndarray) -> float:
        """
        Covariance penalty: (1/d) * sum_{j!=k} C_{j,k}^2.
        z has shape (..., d); covariance is over all elements except the last dim.
        """
        M = np.prod(z.shape[:-1])
        d = z.shape[-1]
        z_flat = z.reshape(-1, d)
        zc = z_flat - z_flat.mean(axis=0, keepdims=True)
        cov = (zc.T @ zc) / M
        mask = 1.0 - np.eye(d)
        return float(np.sum(cov ** 2 * mask) / d)

    def forward(self, codes: list[np.ndarray]) -> dict:
        """
        Compute JEPA loss for a stack of layer codes.

        Parameters
        ----------
        codes : list of np.ndarray, length n_layers
            Each array has shape (B, P, d).

        Returns
        -------
        dict with loss, pred_loss, var_loss, cov_loss, and intermediates.
        """
        total_loss = 0.0
        total_pred = 0.0
        total_var = 0.0
        total_cov = 0.0

        all_pred_data = []

        for l in range(self.n_layers):
            Z = codes[l]  # (B, P, d)
            B, P, d = Z.shape
            W_pred = self.predictors[l]["W_pred"]  # (d, d)
            b_pred = self.predictors[l]["b_pred"]  # (d,)

            # Extract neighbor pairs
            z_p = Z[:, :-1, :]    # (B, P-1, d)
            z_p1 = Z[:, 1:, :]    # (B, P-1, d)

            # Flatten for matmul
            z_p_2d = z_p.reshape(B * (P - 1), d)    # (B*(P-1), d)
            z_p1_2d = z_p1.reshape(B * (P - 1), d)  # (B*(P-1), d)

            # Predictions
            zhat_p1 = z_p_2d @ W_pred + b_pred    # (B*(P-1), d)
            zhat_p = z_p1_2d @ W_pred + b_pred    # (B*(P-1), d)

            # Errors
            e1 = zhat_p1 - z_p1_2d  # predict p+1 from p
            e2 = zhat_p - z_p_2d    # predict p from p+1

            # Prediction loss = MSE over all 2*B*(P-1) prediction pairs
            pred_loss = 0.5 * np.mean(e1 ** 2) + 0.5 * np.mean(e2 ** 2)

            # VICReg on the raw codes Z
            var_loss = self._variance_loss(Z)
            cov_loss = self._covariance_loss(Z)

            loss = pred_loss + 25.0 * var_loss + 25.0 * cov_loss

            total_loss += loss
            total_pred += pred_loss
            total_var += var_loss
            total_cov += cov_loss

            all_pred_data.append({
                "Z": Z,
                "z_p_2d": z_p_2d,
                "z_p1_2d": z_p1_2d,
                "zhat_p1": zhat_p1,
                "zhat_p": zhat_p,
                "e1": e1,
                "e2": e2,
                "B": B,
                "P": P,
            })

        n_layers = self.n_layers
        if n_layers > 0:
            total_loss /= n_layers
            total_pred /= n_layers
            total_var /= n_layers
            total_cov /= n_layers

        return {
            "loss": float(total_loss),
            "pred_loss": float(total_pred),
            "var_loss": float(total_var),
            "cov_loss": float(total_cov),
            "intermediates": {
                "codes": codes,
                "pred_data": all_pred_data,
            },
        }

    def backward(self, cached: dict) -> tuple[list[dict], list[np.ndarray]]:
        """
        Compute gradients for all predictors and all layer codes.

        Returns
        -------
        predictor_grads : list of dict, length n_layers
            Each dict has keys "W_pred" and "b_pred".
        code_grads : list of np.ndarray, length n_layers
            Each array has shape (B, P, d).
        """
        codes = cached["codes"]
        pred_data = cached["pred_data"]

        predictor_grads: list[dict] = []
        code_grads: list[np.ndarray] = []

        for l in range(self.n_layers):
            data = pred_data[l]
            Z = data["Z"]
            z_p_2d = data["z_p_2d"]
            z_p1_2d = data["z_p1_2d"]
            e1 = data["e1"]
            e2 = data["e2"]
            B = data["B"]
            P = data["P"]
            d = self.d

            W_pred = self.predictors[l]["W_pred"]

            denom = B * (P - 1) * d

            # ---- Predictor gradients ----
            dW_pred = (z_p_2d.T @ e1 + z_p1_2d.T @ e2) / denom
            db_pred = (e1.sum(axis=0) + e2.sum(axis=0)) / denom

            predictor_grads.append({
                "W_pred": dW_pred,
                "b_pred": db_pred,
            })

            # ---- Code gradients from prediction loss ----
            dZ_pred = np.zeros_like(Z)  # (B, P, d)
            e1_3d = e1.reshape(B, P - 1, d)
            e2_3d = e2.reshape(B, P - 1, d)

            # dZ[:, p, :]   gets  (e1 @ W^T - e2) / denom
            # dZ[:, p+1, :] gets  (e2 @ W^T - e1) / denom
            dZ_pred[:, :-1, :] += (e1_3d @ W_pred.T - e2_3d) / denom
            dZ_pred[:, 1:, :] += (e2_3d @ W_pred.T - e1_3d) / denom

            # ---- Code gradients from variance loss ----
            M = B * P
            z_flat = Z.reshape(-1, d)
            mu = z_flat.mean(axis=0, keepdims=True)
            std = np.sqrt(z_flat.var(axis=0, ddof=0) + 1e-12)
            mask = (std < 1.0).astype(float)

            dz_var_flat = -(25.0 / d) * mask * (z_flat - mu) / (M * std + 1e-12)
            dZ_var = dz_var_flat.reshape(B, P, d)

            # ---- Code gradients from covariance loss ----
            zc = z_flat - mu  # (M, d)
            cov = (zc.T @ zc) / M  # (d, d)
            C_off = cov * (1.0 - np.eye(d))
            dz_cov_flat = (25.0 * 4.0 / (M * d)) * (zc @ C_off)  # (M, d)
            dZ_cov = dz_cov_flat.reshape(B, P, d)

            dZ_total = dZ_pred + dZ_var + dZ_cov
            code_grads.append(dZ_total)

        return predictor_grads, code_grads

    def step(self, codes: list[np.ndarray]) -> dict:
        """Forward, backward, Adam update for predictors, and return everything."""
        fwd = self.forward(codes)
        p_grads, c_grads = self.backward(fwd["intermediates"])

        for l in range(self.n_layers):
            self.adams[l].step(self.predictors[l], p_grads[l])

        return {**fwd, "predictor_grads": p_grads, "code_grads": c_grads}

    def loss_and_grads(self, codes: list[np.ndarray]) -> dict:
        """Convenience: forward + backward."""
        fwd = self.forward(codes)
        p_grads, c_grads = self.backward(fwd["intermediates"])
        return {**fwd, "grads": p_grads, "code_grads": c_grads}


# ==============================================================================
#  Contrastive Loss
# ==============================================================================

class ContrastiveLoss:
    """
    NT-Xent contrastive loss with a 2-layer projection MLP:
    10*d -> 5*d -> 2.5*d, with ReLU and L2 normalization.
    """

    def __init__(self, d: int, temp: float = 0.5, lr: float = 1e-3):
        self.d = d  # base d (e.g. d=8 => input_dim=80, hidden=40, output=20)
        self.temp = temp
        self.lr = lr

        self.input_dim = 10 * d
        self.hidden = 5 * d
        self.d_proj = int(2.5 * d)

        rng = np.random.default_rng(43)

        self.W1 = rng.standard_normal((self.input_dim, self.hidden)) * np.sqrt(2.0 / self.input_dim)
        self.b1 = np.zeros(self.hidden)
        self.W2 = rng.standard_normal((self.hidden, self.d_proj)) * np.sqrt(2.0 / self.hidden)
        self.b2 = np.zeros(self.d_proj)

        params = {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }
        self.adam = _Adam(params, lr=lr)

    def _project(
        self, z: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Projection MLP with ReLU and L2 normalization.
        Returns (proj, h1, pre_norm).
        """
        h1 = np.maximum(z @ self.W1 + self.b1, 0.0)
        pre_norm = h1 @ self.W2 + self.b2
        norm = np.linalg.norm(pre_norm, axis=-1, keepdims=True)
        proj = pre_norm / np.maximum(norm, 1e-12)
        return proj, h1, pre_norm

    def forward(self, z1: np.ndarray, z2: np.ndarray) -> dict:
        """
        Compute NT-Xent loss between two augmented views.

        Parameters
        ----------
        z1, z2 : np.ndarray, shape (B, 10 * d)

        Returns
        -------
        dict with loss, proj, and intermediates.
        """
        B = z1.shape[0]

        # Stack views: original + augmented
        z = np.concatenate([z1, z2], axis=0)  # (2B, 10*d)

        p, h1, pre_norm = self._project(z)  # (2B, d_proj)

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
        pre_norm = cached["pre_norm"]
        exp_logits = cached["exp_logits"]
        sum_exp = cached["sum_exp"]
        pos_indices = cached["pos_indices"]

        B_total = z.shape[0]  # 2B
        H1 = self.hidden
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

        # Linear 2
        dW2 = h1.T @ d_pre / B_total
        db2 = d_pre.mean(axis=0)
        d_h1 = d_pre @ self.W2.T

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
