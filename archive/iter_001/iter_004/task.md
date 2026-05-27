## Task: Implement P0-D (Sparse Autoencoder) and P0-E (Predictive Coding) encoders

You are implementing the remaining two encoders for Phase 0 of the HSUN project.

First, READ `src/harness.py` to understand the EncoderBase interface, and READ `src/encoders/lookup_table.py` for the import pattern (the `sys.path` setup at the top).

### 1. Create `src/encoders/sparse_autoencoder.py` — P0-D: SparseAutoencoder

This is the GLOBAL-OPTIMIZATION BASELINE — expected to perform best.

Architecture: input(3) → hidden(16, ReLU) → output(3, linear)
Loss: MSE reconstruction + L1 sparsity penalty (lambda=0.01)
Training: full-batch gradient descent with backpropagation implemented in numpy

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np

class SparseAutoencoder(EncoderBase):
    def __init__(self, dim_in=3, dim_out=16, seed=42, lr=0.01, l1_lambda=0.01):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr = lr
        self.l1_lambda = l1_lambda
        rng = np.random.default_rng(seed)
        # Xavier initialization
        self.W1 = rng.standard_normal((dim_in, dim_out)) * np.sqrt(2.0 / dim_in)
        self.b1 = np.zeros(dim_out)
        self.W2 = rng.standard_normal((dim_out, dim_in)) * np.sqrt(2.0 / dim_out)
        self.b2 = np.zeros(dim_in)
    
    @staticmethod
    def _relu(x):
        return np.maximum(0, x)
    
    @staticmethod  
    def _relu_deriv(x):
        return (x > 0).astype(np.float64)
    
    def _forward(self, x):
        # x: shape (dim_in,) or (batch, dim_in)
        z1 = x @ self.W1 + self.b1  # pre-activation
        h = self._relu(z1)          # hidden code
        z2 = h @ self.W2 + self.b2  # reconstruction (linear)
        return z1, h, z2
    
    def train(self, inputs, epochs=50):
        n = inputs.shape[0]
        loss_history = []
        for epoch in range(epochs):
            # Forward pass (full batch)
            z1 = inputs @ self.W1 + self.b1
            h = self._relu(z1)
            recon = h @ self.W2 + self.b2
            
            # Loss: MSE + L1
            mse = np.mean((inputs - recon) ** 2)
            l1 = self.l1_lambda * np.mean(np.abs(h))
            loss = mse + l1
            loss_history.append(loss)
            
            # Backward pass
            # d_loss/d_recon = -2/n * (inputs - recon) = 2/n * (recon - inputs)
            d_recon = 2.0 / n * (recon - inputs)
            
            # d_loss/d_W2 = h^T @ d_recon
            d_W2 = h.T @ d_recon
            d_b2 = np.mean(d_recon, axis=0)
            
            # d_loss/d_h = d_recon @ W2^T
            d_h = d_recon @ self.W2.T
            
            # Add L1 gradient: d/dh of l1_lambda * mean(|h|) = l1_lambda * sign(h) / n
            d_h += self.l1_lambda * np.sign(h) / n
            
            # d_loss/d_z1 = d_h * relu_deriv(z1)
            d_z1 = d_h * self._relu_deriv(z1)
            
            d_W1 = inputs.T @ d_z1
            d_b1 = np.mean(d_z1, axis=0)
            
            # Gradient descent
            self.W1 -= self.lr * d_W1
            self.b1 -= self.lr * d_b1
            self.W2 -= self.lr * d_W2
            self.b2 -= self.lr * d_b2
        
        return {"final_loss": loss_history[-1], "loss_history": loss_history}
    
    def encode(self, inputs):
        z1 = inputs @ self.W1 + self.b1
        h = self._relu(z1)
        return h
    
    @property
    def dim_out(self):
        return self._dim_out
```

IMPORTANT: The sparse autoencoder MUST use enough epochs and an appropriate learning rate to converge well. With only 88 samples of 3 dimensions, convergence should be fast. Try:
- lr=0.05 (faster convergence for tiny problem)
- epochs=200 (more epochs for convergence)
- l1_lambda=0.005 (slightly less aggressive sparsity to preserve similarity structure)

If the initial learning rate causes divergence, add gradient clipping or reduce lr.

### 2. Create `src/encoders/predictive_coding.py` — P0-E: PredictiveCodingEncoder

ngclearn-inspired local-error node:
- Forward weights: W_f (3 → 16) for bottom-up input
- Backward/prediction weights: W_b (16 → 3) for top-down prediction
- Error = input - prediction (local learning signal)
- Learning: update W_f proportional to error * pre-synaptic activity
- Lateral inhibition: after activation, apply soft winner-take-all
- Sparsity: apply threshold to keep only significant activations

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from harness import EncoderBase
import numpy as np

class PredictiveCodingEncoder(EncoderBase):
    def __init__(self, dim_in=3, dim_out=16, seed=42, lr=0.01, sparsity_threshold=0.1):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr = lr
        self.sparsity_threshold = sparsity_threshold
        rng = np.random.default_rng(seed)
        # Forward (bottom-up) weights
        self.W_f = rng.standard_normal((dim_in, dim_out)) * 0.1
        self.b_f = np.zeros(dim_out)
        # Backward (top-down / prediction) weights  
        self.W_b = rng.standard_normal((dim_out, dim_in)) * 0.1
        self.b_b = np.zeros(dim_in)
        # Lateral inhibition weights (self-inhibition within the layer)
        self.W_lat = -0.1 * np.eye(dim_out)  # self-inhibition
        # Add some off-diagonal inhibition
        off_diag = rng.standard_normal((dim_out, dim_out)) * 0.01
        np.fill_diagonal(off_diag, 0)
        self.W_lat += off_diag
    
    def _activate(self, x):
        """Bottom-up activation with lateral inhibition."""
        # Bottom-up drive
        h = x @ self.W_f + self.b_f  # shape (dim_out,) or (batch, dim_out)
        # Apply ReLU
        h = np.maximum(0, h)
        # Lateral inhibition (single step, not iterative)
        if h.ndim == 1:
            h_inhibited = h + h @ self.W_lat
        else:
            h_inhibited = h + h @ self.W_lat
        h_inhibited = np.maximum(0, h_inhibited)  # ReLU again
        return h_inhibited
    
    def _predict(self, h):
        """Top-down prediction from hidden state."""
        return h @ self.W_b + self.b_b
    
    def train(self, inputs, epochs=50):
        n = inputs.shape[0]
        loss_history = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for x in inputs:
                # Forward pass
                h = self._activate(x)
                pred = self._predict(h)
                
                # Prediction error (local learning signal)
                error = x - pred
                loss = np.mean(error ** 2)
                epoch_loss += loss
                
                # Update forward weights: Hebbian-like, driven by prediction error
                # dW_f ~ error * h^T (outer product for single sample)
                d_W_b = np.outer(h, error)  # (dim_out, dim_in) - update prediction weights
                d_b_b = error
                
                # Update forward weights using error signal
                d_W_f = np.outer(x, h) * np.mean(error ** 2)  # modulated by error magnitude
                d_b_f = h * np.mean(error ** 2)
                
                # Gradient step
                self.W_b += self.lr * d_W_b / n
                self.b_b += self.lr * d_b_b / n
                self.W_f += self.lr * d_W_f / n
                self.b_f += self.lr * d_b_f / n
            
            loss_history.append(epoch_loss / n)
        
        return {"final_loss": loss_history[-1], "loss_history": loss_history}
    
    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, x in enumerate(inputs):
            h = self._activate(x)
            # Apply sparsity threshold
            h = np.where(np.abs(h) > self.sparsity_threshold, h, 0.0)
            codes[i] = h
        return codes
    
    @property
    def dim_out(self):
        return self._dim_out
```

IMPORTANT for P0-E: The predictive coding encoder's learning dynamics need to be right. Key tuning:
- lr should be small enough for stability (try 0.01-0.05)
- The key insight is that prediction error should decrease over training
- Sparsity threshold should be set so that about 30-50% of units are active (not too sparse, not too dense)

### 3. Register both encoders in `src/encoders/__init__.py`

Update the `__init__.py` to also import and register these two new encoders.

### 4. Test each encoder

For each new encoder, run a quick test:
```python
python -c "import sys; sys.path.insert(0, 'src'); from encoders.sparse_autoencoder import SparseAutoencoder; import numpy as np; e = SparseAutoencoder(seed=42); ds_inputs = np.array([[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]], dtype=np.float64); metrics = e.train(ds_inputs, epochs=200); codes = e.encode(ds_inputs); print(f'SparseAE: rho? codes shape={codes.shape}, sparsity={np.mean(np.abs(codes)<0.01):.3f}, loss={metrics[\"final_loss\"]:.4f}')"
```

And similar for PredictiveCodingEncoder. Also run through the SimilarityEvaluator to get Spearman rho.

CRITICAL: These encoders must actually produce similarity-preserving codes (rho >= 0.6 expected for the global-optimization P0-D at least). If they don't, investigate and fix the learning dynamics:
- For P0-D: if loss doesn't decrease, try different lr (0.01, 0.05, 0.1)
- For P0-D: if codes are all zero (dead ReLU), try smaller initialization or add small bias
- For P0-E: if prediction error doesn't decrease, adjust the learning rule

The SUCCESS of Phase 0 depends on P0-D (the global baseline) achieving rho >= 0.6. If it doesn't, there's a bug that must be fixed.
