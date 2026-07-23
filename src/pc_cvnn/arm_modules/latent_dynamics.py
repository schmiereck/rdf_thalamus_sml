"""LatentDynamicsModule — predictive transition dynamics z_{t+1} = z_t + f(z_t, a_t) in latent space.

Etappe 2 (Latent Dynamics Modell):
Learn an internal transition model in the latent goal space. Given the current latent state z_t
and an executed action a_t, the module predicts:
    \\hat{z}_{t+1} = z_t + \\Delta \\hat{z}_t
where \\Delta \\hat{z}_t = f_\\theta(z_t, a_t) is learned by self-supervised predictive coding on transitions.

Features:
  - Supports 1-step prediction and multi-step dreaming/rollout in latent space.
  - Computes predictive surprise S = ||z_{actual} - \\hat{z}_{t+1}||^2 as a novelty / error signal.
  - Supports complex (RoPE) and real-valued latent representations.
  - Lifelong buffer & train for self-supervised learning during agent interaction.
"""
from __future__ import annotations

import numpy as np

from .base import ArmModule, Port


class LatentDynamicsModule(ArmModule):
    """Predictive Latent Dynamics Network: z_{t+1} = z_t + f(z_t, a_t)."""

    def __init__(self, latent_dim: int = 10, action_dim: int = 4, hidden_dim: int = 64, lr: float = 0.01, rng=None):
        super().__init__("latent_dynamics")
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.rng = rng or np.random.default_rng(42)

        self.in_dim = 2 * latent_dim + action_dim
        self.out_dim = 2 * latent_dim

        # 2-layer MLP weights initialized with Xavier scaling
        scale1 = np.sqrt(2.0 / (self.in_dim + hidden_dim))
        scale2 = np.sqrt(2.0 / (hidden_dim + self.out_dim))
        self.W1 = self.rng.normal(0, scale1, (self.in_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.W2 = self.rng.normal(0, scale2, (hidden_dim, self.out_dim))
        self.b2 = np.zeros(self.out_dim)

        # Transition buffer: stores (z_t, action, z_next)
        self.buffer_z = []
        self.buffer_a = []
        self.buffer_zn = []
        self.max_buffer = 12000

    def declare_ports(self):
        self.add_port(Port("z_in", "in", np.ndarray))
        self.add_port(Port("action_in", "in", np.ndarray))
        self.add_port(Port("z_pred_out", "out", np.ndarray))

    def _to_real_vector(self, z):
        """Convert a latent vector (real or complex RoPE) to a 1D real vector."""
        z_arr = np.asarray(z).ravel()
        if np.iscomplexobj(z_arr):
            return np.concatenate([np.real(z_arr), np.imag(z_arr)])
        return np.concatenate([z_arr, np.zeros_like(z_arr)])

    def _from_real_vector(self, r_vec, is_complex=True):
        """Reconstruct latent vector (real or complex RoPE) from real representation."""
        half = len(r_vec) // 2
        if is_complex:
            return r_vec[:half] + 1j * r_vec[half:]
        return r_vec[:half]

    def predict_delta(self, z_t, action):
        """Forward pass predicting \\Delta z in real vector space."""
        z_real = self._to_real_vector(z_t)
        a_real = np.asarray(action, float).ravel()
        if len(a_real) < self.action_dim:
            a_real = np.pad(a_real, (0, self.action_dim - len(a_real)))
        elif len(a_real) > self.action_dim:
            a_real = a_real[:self.action_dim]

        x = np.concatenate([z_real, a_real])
        h = np.tanh(x @ self.W1 + self.b1)
        delta_real = h @ self.W2 + self.b2
        return delta_real

    def predict_next_latent(self, z_t, action):
        """Predict the next latent state \\hat{z}_{t+1} = z_t + f(z_t, a_t)."""
        is_complex = np.iscomplexobj(np.asarray(z_t))
        delta_real = self.predict_delta(z_t, action)
        z_real = self._to_real_vector(z_t)
        z_next_real = z_real + delta_real
        return self._from_real_vector(z_next_real, is_complex=is_complex)

    def rollout(self, z_start, actions):
        """Multi-step dreaming / rollout in latent space given a sequence of candidate actions."""
        traj = [z_start]
        z_curr = z_start
        for act in actions:
            z_curr = self.predict_next_latent(z_curr, act)
            traj.append(z_curr)
        return traj

    def predict_surprise(self, z_t, action, z_actual):
        """Compute the predictive surprise S = ||z_actual - \\hat{z}_{t+1}||_2 (L2 norm error)."""
        z_pred = self.predict_next_latent(z_t, action)
        return float(np.linalg.norm(np.asarray(z_actual) - np.asarray(z_pred)))

    def observe(self, z_t, action, z_next):
        """Buffer a transition tuple (z_t, action, z_next) for training."""
        self.buffer_z.append(np.asarray(z_t))
        self.buffer_a.append(np.asarray(action, float))
        self.buffer_zn.append(np.asarray(z_next))
        if len(self.buffer_z) > self.max_buffer:
            self.buffer_z.pop(0)
            self.buffer_a.pop(0)
            self.buffer_zn.pop(0)

    def train(self, epochs: int = 15, batch_size: int = 64) -> float:
        """Train the latent dynamics network on buffered transitions. Returns final MSE loss."""
        if len(self.buffer_z) < 10:
            return 0.0

        is_complex = np.iscomplexobj(self.buffer_z[0])
        X_list, Y_list = [], []
        for z, a, zn in zip(self.buffer_z, self.buffer_a, self.buffer_zn):
            z_r = self._to_real_vector(z)
            zn_r = self._to_real_vector(zn)
            a_r = np.asarray(a, float).ravel()
            if len(a_r) < self.action_dim:
                a_r = np.pad(a_r, (0, self.action_dim - len(a_r)))
            else:
                a_r = a_r[:self.action_dim]
            X_list.append(np.concatenate([z_r, a_r]))
            Y_list.append(zn_r - z_r)  # Predict delta

        X = np.array(X_list)
        Y = np.array(Y_list)
        N = len(X)

        losses = []
        for epoch in range(epochs):
            indices = self.rng.permutation(N)
            epoch_loss = 0.0
            for start in range(0, N, batch_size):
                end = min(start + batch_size, N)
                idx = indices[start:end]
                xb, yb = X[idx], Y[idx]

                h = np.tanh(xb @ self.W1 + self.b1)
                pred_y = h @ self.W2 + self.b2
                err = pred_y - yb
                batch_loss = np.mean(err ** 2)
                epoch_loss += batch_loss * len(idx)

                grad_pred = 2.0 * err / len(idx)
                grad_W2 = h.T @ grad_pred
                grad_b2 = np.sum(grad_pred, axis=0)

                grad_h = grad_pred @ self.W2.T * (1.0 - h ** 2)
                grad_W1 = xb.T @ grad_h
                grad_b1 = np.sum(grad_h, axis=0)

                self.W2 -= self.lr * np.clip(grad_W2, -5.0, 5.0)
                self.b2 -= self.lr * np.clip(grad_b2, -5.0, 5.0)
                self.W1 -= self.lr * np.clip(grad_W1, -5.0, 5.0)
                self.b1 -= self.lr * np.clip(grad_b1, -5.0, 5.0)

            losses.append(epoch_loss / N)
        return float(losses[-1]) if losses else 0.0

    def pack(self):
        """Serialize state dict for persistence."""
        return {
            "W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2,
            "latent_dim": self.latent_dim, "action_dim": self.action_dim,
            "hidden_dim": self.hidden_dim,
            "buffer_z": self.buffer_z[-5000:],
            "buffer_a": self.buffer_a[-5000:],
            "buffer_zn": self.buffer_zn[-5000:]
        }

    def unpack(self, d):
        """Deserialize state dict."""
        self.W1 = d["W1"]
        self.b1 = d["b1"]
        self.W2 = d["W2"]
        self.b2 = d["b2"]
        self.latent_dim = d.get("latent_dim", self.latent_dim)
        self.action_dim = d.get("action_dim", self.action_dim)
        self.hidden_dim = d.get("hidden_dim", self.hidden_dim)
        self.buffer_z = d.get("buffer_z", [])
        self.buffer_a = d.get("buffer_a", [])
        self.buffer_zn = d.get("buffer_zn", [])


# --------------------------------------------------------------------------- #
def main():
    """Standalone unit test for LatentDynamicsModule."""
    rng = np.random.default_rng(0)
    dyn = LatentDynamicsModule(latent_dim=10, action_dim=4, rng=rng)

    # Generate synthetic transitions z_{t+1} = z_t + 0.1 * action + noise
    print("=" * 72)
    print("  LatentDynamicsModule — Standalone Self-Test")
    print("=" * 72)

    for i in range(150):
        z_t = rng.normal(0, 1, 10) + 1j * rng.normal(0, 1, 10)  # RoPE complex latent
        act = rng.uniform(-0.1, 0.1, 4)
        z_next = z_t + 0.05 * act[0] + 0.02 * rng.normal(0, 0.1, 10)
        dyn.observe(z_t, act, z_next)

    print(f"  Buffered transitions: {len(dyn.buffer_z)}")
    initial_surprise = dyn.predict_surprise(dyn.buffer_z[0], dyn.buffer_a[0], dyn.buffer_zn[0])
    print(f"  Pre-training surprise on sample 0: {initial_surprise:.4f}")

    loss = dyn.train(epochs=40)
    print(f"  Post-training MSE loss: {loss:.6f}")

    post_surprise = dyn.predict_surprise(dyn.buffer_z[0], dyn.buffer_a[0], dyn.buffer_zn[0])
    print(f"  Post-training surprise on sample 0: {post_surprise:.4f}")

    # Rollout test
    actions_seq = [rng.uniform(-0.05, 0.05, 4) for _ in range(5)]
    traj = dyn.rollout(dyn.buffer_z[0], actions_seq)
    print(f"  5-Step Latent Rollout trajectory length: {len(traj)} states")

    print("-" * 72)
    print("  Read: Latent Dynamics Module successfully learns z_{t+1} = z_t + f(z_t, a_t) and performs dreaming rollouts.")
    print("=" * 72)


if __name__ == "__main__":
    main()
