
# Phase 1b: Corrective Experiment — Fix d_out Bottleneck Bug

## Critical Bug Identified

The Phase 1 implementation has a fundamental architectural error. The UniversalNode's `d_out` was set to `3*d` (24 for d=8) instead of `d` (8 for d=8). This means:

- **Current (WRONG)**: Encoder 24→24, Decoder 24→24 — NO bottleneck, identity-like
- **Correct (recursive form)**: Encoder 24→8, Decoder 8→24 — TRUE 3:1 compression

The recursive universal node form from goal.md states: "Output dim = input dim, fully recursive form" — meaning d_out = d (per-slot dimension), NOT d_out = 3*d (total input dimension). The output is ONE slot of dimension d, which feeds as a slot in the next layer.

Additionally, the embedding initialization scale (Uniform[-0.01, 0.01]) was too small, causing representation collapse.

## Task

### 1. Fix `src/run_phase1.py` — Correct the configurations

Change the CONFIGS to use d_out = d (true recursive bottleneck):

```python
CONFIGS = [
    {"name": "P1-A", "sharing_mode": "within_layer", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-B", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-C", "sharing_mode": "none", "d": 8, "d_out": 8, "train": True},
    {"name": "P1-D", "sharing_mode": "cross_layer", "d": 4, "d_out": 4, "train": True},
    {"name": "P1-E", "sharing_mode": "cross_layer", "d": 8, "d_out": 16, "train": True},
    {"name": "Untrained-P1-B", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": False},
]
```

Also add a k-WTA variant:
```python
    {"name": "P1-B-kwta", "sharing_mode": "cross_layer", "d": 8, "d_out": 8, "train": True, "kwta_k": 4},
```

### 2. Fix `src/hierarchical_encoder.py` — Two changes

#### 2a. Fix embedding initialization
Change from `Uniform[-0.01, 0.01]` to `Normal(0, 1.0)`:
```python
self.embedding = self.rng.standard_normal((2, d)) * 1.0
```

#### 2b. Remove the d_out slicing between layers
Since d_out = d for the recursive form, the slicing `x = x[:, :, :self.d]` is unnecessary (and harmful when d_out != d). For the recursive configs (d_out == d), remove the slice. For P1-E (d_out=16), the slice should take the first d=8 dims. Keep the slicing logic but make it conditional:
```python
if x.shape[2] > self.d:
    x = x[:, :, :self.d]
```
This way, when d_out == d (most configs), no slicing occurs. When d_out > d (P1-E), we slice back.

### 3. Add k-WTA support to `src/node.py`

Add a k-Winners-Take-All activation option alongside tanh:

In UniversalNode.__init__, add parameter `kwta_k=None`. If kwta_k is specified, after the tanh activation, zero out all but the top-k values:
```python
def forward(self, x_3d):
    batch = x_3d.shape[0]
    x_flat = x_3d.reshape(batch, -1)
    z = x_flat @ self.W_enc + self.b_enc
    a = np.tanh(z)   # base activation
    
    if self.kwta_k is not None:
        # k-WTA: keep only top-k activations per sample
        k = min(self.kwta_k, self.d_out)
        # For each sample, find top-k absolute values, zero rest
        threshold = np.sort(np.abs(a), axis=1)[:, -k:k][:, 0:1]  # k-th largest
        mask = np.abs(a) >= threshold
        a = a * mask
    
    return a
```

Also update compute_gradients to handle k-WTA: when k-WTA is active, the gradient through the zeroed-out units is zero. The tanh gradient `(1 - a^2)` should only be applied to the winning units:
```python
# In compute_gradients, after computing d_a (gradient w.r.t. code a):
if self.kwta_k is not None:
    # Recompute mask
    k = min(self.kwta_k, self.d_out)
    threshold = np.sort(np.abs(a), axis=1)[:, -k:k][:, 0:1]
    mask = np.abs(a) >= threshold
    d_a = d_a * mask  # zero gradient for losers

d_z = d_a * (1.0 - a ** 2)  # tanh derivative (only for winners when k-WTA)
```

For k-WTA, the L1 penalty is NOT needed (sparsity is enforced structurally). When kwta_k is set, use l1_lambda=0 for the loss computation (or just skip the L1 term).

### 4. Update `src/hierarchical_encoder.py` to pass kwta_k to nodes

In HierarchicalEncoder.__init__, add `kwta_k=None` parameter. Pass it through to UniversalNode:
```python
UniversalNode(d=self.d, l1_lambda=self.l1_lambda, seed=..., d_out=self.d_out, kwta_k=kwta_k)
```

In the train method, when kwta_k is set, use l1_lambda=0 (no L1, since k-WTA enforces sparsity).

### 5. Run the corrected experiment

Execute `python src/run_phase1.py` with the fixed configurations.

### 6. Generate an updated `phase_1/REPORT.md`

The report should include:
- A note explaining the d_out bug fix and embedding initialization fix
- The corrected results table
- All the same criteria checks as before:
  1. P1-B accuracy ≥ 80%
  2. P1-C − P1-B ≤ 15pp
  3. Trained P1-B − untrained ≥ 15pp
  4. P1-B sparsity ≥ 50%
- Plus new analysis for P1-B-kwta

### Key hyperparameters (same as before except where noted)
- d_out = d (FIXED — recursive bottleneck)
- Embedding: Normal(0, 1.0) (FIXED — was Uniform[-0.01, 0.01])
- l1_lambda = 0.002 (for L1 configs; 0 for k-WTA config)
- learning_rate = 0.01
- epochs_per_layer = 100
- batch_size = 32
- seeds: 42, 43, 44, 45, 46
- kwta_k = 4 (for P1-B-kwta, meaning 4 of 8 code dims active = 50% sparsity)

### Important notes
- The UniversalNode's gradient check (numerical vs analytical) must still pass after the k-WTA changes. The k-WTA gradient is straightforward: zero out gradient for losing units.
- For the k-WTA config, sparsity should be structurally ~50% (4/8 active), which meets the ≥50% threshold.
- The corrected architecture with d_out=8 means top-layer codes are 10×8 = 80 features (not 10×24 = 240 as before).
- P1-C (none sharing) will have many more parameters since each of the ~36 positions (14+12+10) has its own 24→8 encoder and 8→24 decoder.

### Success criterion
All 35 runs (7 configs × 5 seeds) complete successfully, results saved to phase_1/results.csv, and REPORT.md generated with corrected analysis.
