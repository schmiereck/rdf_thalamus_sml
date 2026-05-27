"""
UniversalNode -- single-layer auto-encoder unit for HSUN Phase 0-E.

Architecture
------------
  x_3d (batch, 3, d_in)  --> flatten --> (batch, 3*d_in)
  z    = tanh(x_flat @ W_enc + b_enc)          # (batch, d_out)  -- "code"
  xrec = z       @ W_dec + b_dec              # (batch, 3*d_in)
           --> reshape --> (batch, 3, d_in)

Loss  = MSE(x_3d, xrec) + l1_lambda * mean(|z|)

All analytical gradients are provided in ``compute_gradients`` and verified
below via a central-difference numerical check.
"""

from __future__ import annotations

from typing import Dict

import numpy as np


class UniversalNode:
    """A single universal node implementing an encoder --> decoder pair."""

    def __init__(
        self,
        d: int,
        l1_lambda: float = 0.01,
        seed: int = 42,
        d_out: int | None = None,
    ):
        """
        Parameters
        ----------
        d : int
            Input dimensionality *per channel*.  The flattened input has
            dimension ``3 * d`` (three channels).
        l1_lambda : float
            Weight for the L1 sparsity regulariser on the latent code.
        seed : int
            RNG seed for reproducible Xavier initialisation.
        d_out : int or None
            Latent code dimensionality.  If None, defaults to ``3 * d``.
        """
        self.d = d
        self.d_in = 3 * d                    # flattened input dimension
        self.d_out = d_out if d_out is not None else 3 * d
        self.l1_lambda = l1_lambda

        rng = np.random.default_rng(seed)

        # -- Xavier (Glorot) initialisation --
        # W_enc : (d_in, d_out)
        scale_enc = np.sqrt(2.0 / (self.d_in + self.d_out))
        self.W_enc = rng.standard_normal((self.d_in, self.d_out)) * scale_enc
        self.b_enc = np.zeros(self.d_out)

        # W_dec : (d_out, d_in)
        scale_dec = np.sqrt(2.0 / (self.d_out + self.d_in))
        self.W_dec = rng.standard_normal((self.d_out, self.d_in)) * scale_dec
        self.b_dec = np.zeros(self.d_in)

    # ------------------------------------------------------------------
    # Forward pass helpers
    # ------------------------------------------------------------------

    def forward(self, x_3d: np.ndarray) -> np.ndarray:
        """
        Encode x_3d --> latent code.

        Parameters
        ----------
        x_3d : np.ndarray, shape (batch, 3, d)

        Returns
        -------
        code : np.ndarray, shape (batch, d_out)
        """
        batch = x_3d.shape[0]
        x_flat = x_3d.reshape(batch, -1)           # (batch, d_in)
        z = x_flat @ self.W_enc + self.b_enc        # (batch, d_out)
        code = np.tanh(z)
        return code

    def reconstruct(self, code: np.ndarray) -> np.ndarray:
        """
        Decode latent code --> reconstructed x_3d.

        Parameters
        ----------
        code : np.ndarray, shape (batch, d_out)

        Returns
        -------
        x_rec : np.ndarray, shape (batch, 3, d)
        """
        batch = code.shape[0]
        x_hat_flat = code @ self.W_dec + self.b_dec  # (batch, d_in)
        x_rec = x_hat_flat.reshape(batch, 3, self.d)  # (batch, 3, d)
        return x_rec

    # ------------------------------------------------------------------
    # Loss
    # ------------------------------------------------------------------

    def local_loss(self, x_3d: np.ndarray) -> float:
        """
        Compute the local (per-node) loss value.

        Returns a scalar float: MSE + l1_lambda * mean(|code|).
        """
        code = self.forward(x_3d)
        recon = self.reconstruct(code)
        mse = float(np.mean((x_3d - recon) ** 2))
        l1 = float(self.l1_lambda * np.mean(np.abs(code)))
        return mse + l1

    # ------------------------------------------------------------------
    # Analytical gradients
    # ------------------------------------------------------------------

    def compute_gradients(self, x_3d: np.ndarray) -> Dict[str, np.ndarray]:
        r"""
        Compute analytical gradients of the local loss w.r.t. all four
        trainable parameters **and** the input x_3d.

        Returns a dict with keys:
            'W_enc', 'b_enc', 'W_dec', 'b_dec', 'x_3d'

        Notation (B = batch size):

            x  = x_3d.reshape(B, D_in)           where D_in = 3*d
            z  = x @ W_enc + b_enc                (B, D_out)
            a  = tanh(z)                          (B, D_out)  -- code
            r  = a @ W_dec + b_dec                (B, D_in)
            xhat = r.reshape(B, 3, d)

        Loss = mean((x_3d - xhat)^2) + lambda * mean(|a|)
             = 1/(B*D_in) * sum_{b,i}(r_bi - x_bi)^2
               + lambda/(B*D_out) * sum_{b,j}|a_bj|

        Chain rule:
            dL/dr   = 2/(B*D_in) * (r - x)                        (B, D_in)
            dL/dWdec = a^T @ dL/dr                                 (D_out, D_in)
            dL/dbdec = sum_b(dL/dr)                                (D_in,)
            dL/da   = dL/dr @ W_dec^T + lambda/(B*D_out)*sign(a)   (B, D_out)
            dL/dz   = dL/da * (1 - a^2)                           (B, D_out)
            dL/dWenc = x^T @ dL/dz                                 (D_in, D_out)
            dL/dbenc = sum_b(dL/dz)                                (D_out,)
            dL/dx   = dL/dz @ W_enc^T  --> reshape to (B, 3, d)
        """
        batch = x_3d.shape[0]
        D_in = self.d_in       # = 3 * d
        D_out = self.d_out

        # --- forward (need intermediates) ---
        x_flat = x_3d.reshape(batch, D_in)            # (B, D_in)
        z = x_flat @ self.W_enc + self.b_enc          # (B, D_out)
        a = np.tanh(z)                                 # (B, D_out)  -- code
        r = a @ self.W_dec + self.b_dec               # (B, D_in)

        # --- gradient of MSE w.r.t. flat recon r ---
        d_r = 2.0 / (batch * D_in) * (r - x_flat)     # (B, D_in)

        # --- W_dec, b_dec ---
        d_W_dec = a.T @ d_r                            # (D_out, D_in)
        d_b_dec = np.sum(d_r, axis=0)                  # (D_in,)

        # --- dL/da ---
        d_a = d_r @ self.W_dec.T                       # (B, D_out)
        # Add L1 gradient
        d_a += self.l1_lambda / (batch * D_out) * np.sign(a)

        # --- dL/dz (tanh derivative: d(tanh)/dz = 1 - tanh^2) ---
        d_z = d_a * (1.0 - a ** 2)                     # (B, D_out)

        # --- W_enc, b_enc ---
        d_W_enc = x_flat.T @ d_z                       # (D_in, D_out)
        d_b_enc = np.sum(d_z, axis=0)                  # (D_out,)

        # --- Gradient w.r.t. input x_3d ---
        d_x_flat = d_z @ self.W_enc.T                  # (B, D_in)
        d_x_3d = d_x_flat.reshape(batch, 3, self.d)    # (B, 3, d)

        return {
            "W_enc": d_W_enc,
            "b_enc": d_b_enc,
            "W_dec": d_W_dec,
            "b_dec": d_b_dec,
            "x_3d": d_x_3d,
        }

    # ------------------------------------------------------------------
    # Parameter updates
    # ------------------------------------------------------------------

    def apply_gradients(self, grads: Dict[str, np.ndarray], lr: float) -> None:
        """
        Subtract lr * grads[key] from each parameter.
        """
        self.W_enc -= lr * grads["W_enc"]
        self.b_enc -= lr * grads["b_enc"]
        self.W_dec -= lr * grads["W_dec"]
        self.b_dec -= lr * grads["b_dec"]

    # ------------------------------------------------------------------
    # Parameter sharing
    # ------------------------------------------------------------------

    def share_parameters_from(self, other_node: "UniversalNode") -> None:
        """Copy all parameters from other_node."""
        self.W_enc = other_node.W_enc.copy()
        self.b_enc = other_node.b_enc.copy()
        self.W_dec = other_node.W_dec.copy()
        self.b_dec = other_node.b_dec.copy()


# ======================================================================
#  Numerical gradient check
# ======================================================================

def _numerical_gradient(
    node: UniversalNode,
    x_3d: np.ndarray,
    eps: float = 1e-6,
) -> Dict[str, np.ndarray]:
    """
    Compute numerical gradients via central differences for all
    trainable parameters + the input x_3d.
    """
    grads: Dict[str, np.ndarray] = {}

    for key in ("W_enc", "b_enc", "W_dec", "b_dec"):
        param = getattr(node, key)
        num_grad = np.zeros_like(param)
        flat = param.ravel()
        for idx in range(flat.size):
            original = flat[idx]
            flat[idx] = original + eps
            loss_hi = node.local_loss(x_3d)
            flat[idx] = original - eps
            loss_lo = node.local_loss(x_3d)
            flat[idx] = original
            num_grad.ravel()[idx] = (loss_hi - loss_lo) / (2.0 * eps)
        grads[key] = num_grad

    # --- gradient w.r.t x_3d ---
    # Temporarily perturb x_3d (node is stateless w.r.t x_3d).
    num_x = np.zeros_like(x_3d)
    flat_x = x_3d.ravel()
    for idx in range(flat_x.size):
        original = flat_x[idx]
        flat_x[idx] = original + eps
        loss_hi = node.local_loss(x_3d)
        flat_x[idx] = original - eps
        loss_lo = node.local_loss(x_3d)
        flat_x[idx] = original
        num_x.ravel()[idx] = (loss_hi - loss_lo) / (2.0 * eps)
    grads["x_3d"] = num_x

    return grads


def _relative_error(a: np.ndarray, b: np.ndarray) -> float:
    """Compute the element-wise maximum relative error."""
    diff = np.abs(a - b)
    denom = np.maximum(np.abs(a), np.abs(b))
    denom = np.where(denom < 1e-15, 1.0, denom)   # avoid div-by-zero
    return float(np.max(diff / denom))


if __name__ == "__main__":
    print("=" * 60)
    print("  UniversalNode -- Numerical Gradient Check")
    print("=" * 60)

    rng = np.random.default_rng(7)
    BATCH = 4
    D = 5
    D_OUT = 7

    node = UniversalNode(d=D, l1_lambda=0.01, seed=42, d_out=D_OUT)
    x_3d = rng.standard_normal((BATCH, 3, D))

    analytical = node.compute_gradients(x_3d)
    numerical = _numerical_gradient(node, x_3d)

    all_pass = True
    for key in ("W_enc", "b_enc", "W_dec", "b_dec", "x_3d"):
        a = analytical[key]
        n = numerical[key]
        rel_err = _relative_error(a, n)
        ok = rel_err < 1e-5
        status = "PASS" if ok else "FAIL"
        all_pass = all_pass and ok
        print(f"  {key:>8s}:  rel_err = {rel_err:.2e}  {status}")

    print("-" * 60)
    if all_pass:
        print("  ALL GRADIENTS VERIFIED -- analytical approx numerical")
    else:
        print("  SOME GRADIENTS FAILED -- check the derivation!")
    print("=" * 60)
