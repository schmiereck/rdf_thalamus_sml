## Task: Implement P0-A, P0-B, P0-C encoders and src/encoders/__init__.py

You are implementing encoders for Phase 0 of the HSUN project. The harness already exists at `src/harness.py`.

First, READ `src/harness.py` to understand the EncoderBase interface you must inherit from.

### 1. Create `src/encoders/__init__.py`
```python
ENCODER_REGISTRY = {}

def register_encoder(encoder_id, encoder_class):
    ENCODER_REGISTRY[encoder_id] = encoder_class

def get_encoder(encoder_id):
    return ENCODER_REGISTRY.get(encoder_id)
```

### 2. Create `src/encoders/lookup_table.py` — P0-A: LookupTableEncoder

```python
from harness import EncoderBase
import numpy as np

class LookupTableEncoder(EncoderBase):
    """P0-A: One-hot lookup table — NEGATIVE CONTROL (expected rho ~ 0)."""
    
    def __init__(self, dim_in=3, dim_out=8, seed=None):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self._mapping = {}  # state tuple -> one-hot index
    
    def train(self, inputs, epochs=1):
        # Just enumerate unique states
        seen = set()
        idx = 0
        for row in inputs:
            key = tuple(row)
            if key not in self._mapping:
                self._mapping[key] = idx
                idx += 1
        return {"final_loss": 0.0, "n_states": len(self._mapping)}
    
    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, row in enumerate(inputs):
            key = tuple(row)
            if key in self._mapping:
                codes[i, self._mapping[key]] = 1.0
        return codes
    
    @property
    def dim_out(self):
        return self._dim_out
```

### 3. Create `src/encoders/spatial_pooler.py` — P0-B: SpatialPoolerEncoder

HTM-style SDR encoder:
- Random projection matrix: shape (dim_in=3, dim_out=16), seeded
- Permanence matrix: same shape, initialized at 0.5 + noise
- Connected synapses: permanence >= threshold (0.5)
- k-WTA: keep top k=5 activations, zero the rest
- Training: for each input, compute connected input, apply k-WTA, then update permanences:
  - For active output units: increase permanence for active inputs (+0.1), decrease for inactive (-0.05)
  - Clip permanences to [0, 1]

```python
from harness import EncoderBase
import numpy as np

class SpatialPoolerEncoder(EncoderBase):
    def __init__(self, dim_in=3, dim_out=16, k=5, seed=42, permanence_threshold=0.5,
                 perm_inc=0.1, perm_dec=0.05):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.k = k
        self.permanence_threshold = permanence_threshold
        self.perm_inc = perm_inc
        self.perm_dec = perm_dec
        rng = np.random.default_rng(seed)
        # Permanence matrix: how strongly connected each input is to each output
        self.permanence = rng.uniform(0.4, 0.6, size=(dim_in, dim_out))
        # Random potential pool
        self.potential_pool = rng.random((dim_in, dim_out)) < 0.8  # 80% connectivity
    
    def _connected(self):
        return (self.permanence >= self.permanence_threshold) & self.potential_pool
    
    def _forward(self, x):
        connected = self._connected().astype(np.float64)
        overlap = x @ (connected * self.permanence)  # (dim_out,)
        return overlap
    
    def _kwta(self, activations):
        result = np.zeros_like(activations)
        if self.k > 0 and len(activations) > 0:
            top_k = np.argsort(activations)[-self.k:]
            result[top_k] = activations[top_k]
        return result
    
    def train(self, inputs, epochs=50):
        for epoch in range(epochs):
            for x in inputs:
                overlap = self._forward(x)
                active = self._kwta(overlap)
                active_indices = active > 0
                # Update permanences
                for j in range(self._dim_out):
                    if active_indices[j]:
                        for i in range(self._dim_in):
                            if self.potential_pool[i, j]:
                                if x[i] > 0.5:
                                    self.permanence[i, j] += self.perm_inc
                                else:
                                    self.permanence[i, j] -= self.perm_dec
                self.permanence = np.clip(self.permanence, 0.0, 1.0)
        return {"final_loss": 0.0}
    
    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, x in enumerate(inputs):
            overlap = self._forward(x)
            codes[i] = self._kwta(overlap)
        return codes
    
    @property
    def dim_out(self):
        return self._dim_out
```

### 4. Create `src/encoders/som.py` — P0-C: SOMEncoder

Kohonen Self-Organizing Map:
- 1D grid of 16 units, each with weight vector of dim 3
- Training: for each input, find BMU (best matching unit), update BMU and neighbors
- Learning rate starts at 0.5, decays to 0.01
- Neighborhood radius starts at 4, decays to 0.5
- Encoding: compute activation across all 16 units using Gaussian around BMU

```python
from harness import EncoderBase
import numpy as np

class SOMEncoder(EncoderBase):
    def __init__(self, dim_in=3, dim_out=16, seed=42, lr_init=0.5, lr_final=0.01,
                 radius_init=4.0, radius_final=0.5):
        self._dim_in = dim_in
        self._dim_out = dim_out
        self.lr_init = lr_init
        self.lr_final = lr_final
        self.radius_init = radius_init
        self.radius_final = radius_final
        rng = np.random.default_rng(seed)
        # Initialize weights randomly in [0, 1]
        self.weights = rng.uniform(0.0, 1.0, size=(dim_out, dim_in))
        # Grid positions for 1D SOM
        self.positions = np.arange(dim_out, dtype=np.float64)
    
    def _find_bmu(self, x):
        dists = np.sum((self.weights - x) ** 2, axis=1)
        return np.argmin(dists)
    
    def _neighborhood(self, bmu, radius):
        dists = np.abs(self.positions - bmu)
        return np.exp(-(dists ** 2) / (2 * radius ** 2))
    
    def train(self, inputs, epochs=50):
        total_updates = epochs * len(inputs)
        update_count = 0
        for epoch in range(epochs):
            t = epoch / max(epochs - 1, 1)
            lr = self.lr_init * (1 - t) + self.lr_final * t
            radius = self.radius_init * (1 - t) + self.radius_final * t
            for x in inputs:
                bmu = self._find_bmu(x)
                h = self._neighborhood(bmu, radius)
                # Update: move weights toward input proportional to neighborhood
                self.weights += lr * h[:, np.newaxis] * (x - self.weights)
                update_count += 1
        return {"final_loss": 0.0}
    
    def encode(self, inputs):
        codes = np.zeros((len(inputs), self._dim_out))
        for i, x in enumerate(inputs):
            bmu = self._find_bmu(x)
            # Activation pattern: Gaussian around BMU
            codes[i] = self._neighborhood(bmu, radius=1.0)  # narrow encoding
        return codes
    
    @property
    def dim_out(self):
        return self._dim_out
```

### IMPORTANT DETAILS:
- Each file must have `import sys; sys.path.insert(0, '.')` or use relative imports that work when run from the project root
- Use `from harness import EncoderBase` (not `from src.harness`)
- Register each encoder in `__init__.py` after the class definition
- Each constructor MUST accept a `seed` parameter for reproducibility
- Verify each encoder works standalone: create a small test at the bottom of each file that can be run with `python src/encoders/lookup_table.py` etc.
- Make sure all code is in `src/` directory, NOT in `archive/`

Create all four files. Do NOT modify harness.py (it's already fixed).
