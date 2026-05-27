
# Phase 1: Spatial Hierarchy without Time — Full Implementation & Experiment

You are implementing Phase 1 of the HSUN project. Read the existing codebase first, then implement everything, run the experiments, and generate the report.

## Context

Phase 0 (smoke test) is complete. The existing codebase is in `src/`:
- `src/harness.py` — DatasetGenerator, SimilarityEvaluator, EncoderBase, SimpleLogisticRegression, utilities
- `src/encoders/` — 5 encoder implementations from Phase 0 (lookup_table, spatial_pooler, som, sparse_autoencoder, predictive_coding)
- `src/run_phase0.py` — the Phase 0 runner (pattern to follow)
- `src/pre_registration.md` — needs updating for Phase 1

## Manager's Strategic Requirements (MUST incorporate)

### 1. Untrained Baseline Control
- You MUST evaluate an **untrained (randomly initialized) control** of the exact same hierarchical architecture (including the input embedding layer).
- The trained P1-B encoder must outperform this untrained baseline by at least **15 percentage points** in linear-probe accuracy. If not, the hypothesis is partially falsified — we must prove the local training objective actually extracts structured features.

### 2. Sparsity Constraint
- The average code sparsity (fraction of elements below 10^-3 in magnitude) for the trained P1-B codes must be ≥ 50%. If the model achieves ≥ 80% accuracy but fails this sparsity threshold, the hypothesis is falsified.

### 3. Training Mechanics
- You must document the training strategy clearly. Two options:
  - **Progressive training**: Train layer 1 to convergence, copy weights to layers 2/3 (if sharing), freeze layer 1, train layer 2, etc.
  - **Simultaneous training**: Train all layers simultaneously with local reconstruction losses; for shared weights, average gradients.
- Choose one and document the rationale. The Manager warns that simultaneous training with gradient averaging causes "representation drift" (layer l+1 reconstructs a moving target from layer l). Progressive training is architecturally cleaner for shared weights: train layer 1, then copy the trained weights to layers 2 and 3, then run the full stack forward to compute top-layer codes for evaluation.

## Deliverables

### A. Update `src/pre_registration.md`
Update the pre-registration file with the Phase 1 hypothesis, including:
- The original falsification criteria (P1-B accuracy < 80%, or P1-C − P1-B > 15pp)
- NEW: Untrained baseline criterion (trained P1-B must beat untrained by ≥ 15pp)
- NEW: Sparsity criterion (P1-B code sparsity ≥ 50%)
- NEW: Training mechanics specification (document progressive vs simultaneous choice)

### B. Create `src/node.py` — UniversalNode class
```python
class UniversalNode:
    """Single kernel-3 node: maps 3 input slots (each dim d) to 1 output (dim d)."""
    
    # Encoder: Linear(3d, d) + tanh activation
    # Decoder: Linear(d, 3d) (for reconstruction training)
    # Loss: MSE(input_slots, reconstructed_slots) + lambda * L1(code)
    
    __init__(self, d, l1_lambda, seed):
        Initialize W_enc (3d x d), b_enc (d), W_dec (d x 3d), b_dec (3d)
        Xavier initialization
    
    forward(self, x_3d) -> code:
        x_3d: shape (batch, 3, d) — 3 input slots
        Flatten to (batch, 3d), apply W_enc + b_enc, tanh -> code (batch, d)
    
    reconstruct(self, code) -> x_hat_3d:
        Apply W_dec + b_dec -> (batch, 3d), reshape to (batch, 3, d)
    
    local_loss(self, x_3d) -> loss:
        code = forward(x_3d)
        recon = reconstruct(code)
        mse = mean((x_3d - recon)^2)
        l1 = l1_lambda * mean(|code|)
        return mse + l1
    
    compute_gradients(self, x_3d) -> dict:
        Compute gradients for W_enc, b_enc, W_dec, b_dec via backprop
        (This is per-layer local backprop, NOT end-to-end)
    
    apply_gradients(self, grads, lr):
        Update parameters
    
    share_parameters_from(self, other_node):
        Copy W_enc, b_enc, W_dec, b_dec from another node
```

### C. Create `src/hierarchical_encoder.py` — HierarchicalEncoder class
```python
class HierarchicalEncoder:
    """Stacked kernel-3 stride-1 nodes over 16 binary inputs."""
    
    __init__(self, n_input=16, d=8, n_layers=3, sharing_mode='cross_layer', l1_lambda=0.002, seed=42):
        sharing_mode: 'within_layer' | 'cross_layer' | 'none'
        
        # Input embedding: map binary {0,1} to d-dimensional vectors
        # 2 embeddings (for 0 and 1), shape (2, d)
        self.embedding = learnable parameter shape (2, d)
        
        # Create nodes
        if sharing_mode == 'cross_layer':
            # One UniversalNode shared across ALL layers and positions
            self.shared_node = UniversalNode(d, l1_lambda, seed)
        elif sharing_mode == 'within_layer':
            # One UniversalNode per layer, shared across positions within layer
            self.layer_nodes = [UniversalNode(d, l1_lambda, seed+i) for i in range(n_layers)]
        elif sharing_mode == 'none':
            # Independent node per position per layer
            self.nodes = [[UniversalNode(d, l1_lambda, ...) for pos in range(positions)] 
                          for layer in range(n_layers)]
    
    forward(self, x_binary) -> top_codes:
        x_binary: shape (batch, 16) — binary inputs
        Step 1: Embed -> shape (batch, 16, d)
        Step 2: For each layer:
            positions = input_length - 2  (stride-1 kernel-3)
            Layer 0: 16 -> 14 positions
            Layer 1: 14 -> 12 positions  
            Layer 2: 12 -> 10 positions
            For each position p in [0, output_length-1]:
                Gather 3 slots: input[:, p:p+3, :] -> shape (batch, 3, d)
                Apply node.forward() -> code[:, p, :] shape (batch, d)
            Output: shape (batch, positions, d)
        Step 3: Return top-layer codes flattened: shape (batch, 10 * d)
    
    train_layer(self, layer_idx, input_activations, epochs, lr, batch_size):
        """Train a single layer using local reconstruction loss."""
        # Extract all triplets from input_activations
        # For each batch:
        #   Forward through node -> code
        #   Reconstruct -> x_hat
        #   Compute loss + gradients
        #   Apply gradients (averaging if shared across positions)
    
    train(self, dataset, epochs_per_layer=100, lr=0.01, batch_size=32):
        """Progressive training: train layer by layer."""
        # PROGRESSIVE TRAINING STRATEGY:
        # 1. Train layer 0: input is embedding activations
        #    For cross_layer sharing: after training, copy weights to layers 1, 2
        # 2. Train layer 1: input is layer-0 outputs (frozen, no gradient to layer 0)
        #    For cross_layer sharing: after training, copy weights to layer 2
        # 3. Train layer 2: input is layer-1 outputs (frozen)
    
    encode(self, x_binary) -> top_codes_flat:
        """Forward pass returning top-layer codes for evaluation."""
```

### D. Create `src/dataset_phase1.py` — Five structured 16-bit datasets
```python
def generate_phase1_dataset(n_train=200, n_test=100, seed=42):
    """Generate 5 categories of 16-bit inputs with labels."""
    
    Category 0: Uniform random bits
        - Each of 16 bits independently 0 or 1 with prob 0.5
        - Labels: 0
    
    Category 1: Single-blob
        - Pick random start position (0-12) and width (2-6)
        - Set bits in [start, start+width) to 1, rest to 0
        - Labels: 1
    
    Category 2: Two-blob
        - Pick two non-overlapping intervals of width 2-4 each
        - Set bits in both intervals to 1, rest to 0
        - Labels: 2
    
    Category 3: Periodic patterns
        - Pick period p in {2, 3, 4} and random phase offset
        - Pattern: bit[i] = 1 if (i + phase) % p < p//2 else 0
        - Add optional slight noise (5% bit flip)
        - Labels: 3
    
    Category 4: Mixed noise
        - Pick a structured base from categories 1-3
        - Flip 10-20% of bits randomly
        - Labels: 4
    
    Returns: dict with 'train_x', 'train_y', 'test_x', 'test_y'
    Total: 1000 train, 500 test
```

### E. Create `src/eval_phase1.py` — Evaluation module
```python
def evaluate_hierarchical_encoder(encoder, dataset, seed=42):
    """Evaluate a trained hierarchical encoder."""
    
    # 1. Encode train and test data
    train_codes = encoder.encode(dataset['train_x'])
    test_codes = encoder.encode(dataset['test_x'])
    
    # 2. Linear probe: train logistic regression on train codes, eval on test codes
    # Use SimpleLogisticRegression from harness.py or a new one with more iterations
    # lr=0.1, max_iter=500
    
    # 3. Compute code sparsity (fraction |code| < 1e-3)
    
    # 4. Compute per-layer reconstruction MSE
    
    # 5. Count total parameters
    
    return dict(test_accuracy, train_accuracy, sparsity, recon_mse_per_layer, n_params)
```

### F. Create `src/run_phase1.py` — Experiment runner

Run these configurations x 5 seeds (42-46):

| Config | sharing_mode    | d   | Description                          |
|--------|-----------------|-----|--------------------------------------|
| P1-A   | within_layer    | 8   | Standard CNN baseline                |
| P1-B   | cross_layer     | 8   | Strict universal node (PRIMARY)      |
| P1-C   | none            | 8   | Independent weights (upper bound)     |
| P1-D   | cross_layer     | 4   | Strict universal, smaller d          |
| P1-E   | cross_layer     | d_in=8, d_out=16 | Non-recursive: wider output       |

Plus **untrained baseline**: same architecture as P1-B, but skip training (just random init + encode + linear probe).

Each run:
1. Generate dataset with seed
2. Create HierarchicalEncoder with config
3. Train (progressive, epochs_per_layer=100, lr=0.01, batch_size=32)
4. Evaluate
5. Record: config, seed, test_accuracy, train_accuracy, sparsity, recon_mse, n_params

Save results to `phase_1/results.csv`.

### G. Generate `phase_1/REPORT.md`

Include:
- Summary table: config x metrics (test_accuracy mean +/- std, sparsity, params, recon_mse)
- Untrained baseline vs trained P1-B comparison
- P1-B vs P1-C gap analysis (primary hypothesis test: must be <= 15pp)
- P1-D vs P1-B dimension comparison
- P1-E vs P1-B recursive-constraint comparison
- P1-A vs P1-B within-layer vs cross-layer comparison
- Sparsity check: P1-B sparsity >= 50%?
- Pass/fail on ALL criteria:
  1. P1-B accuracy >= 80%
  2. P1-C - P1-B <= 15pp
  3. Trained P1-B - untrained baseline >= 15pp
  4. P1-B sparsity >= 50%

## Hyperparameters (fixed across all configs)
- d = 8 per slot (except P1-D: d=4, P1-E: d_out=16 but d_in=8 for embedding)
- l1_lambda = 0.002 (from Phase 0 P0-D tuning)
- learning_rate = 0.01
- epochs_per_layer = 100
- batch_size = 32
- 3 layers (output positions: 14, 12, 10)
- seeds: 42, 43, 44, 45, 46
- tanh activation in encoder
- Linear decoder (no activation)

## Important Implementation Notes

1. **No external ML libraries** — use only numpy, scipy (consistent with project constraints)
2. **Gradient computation**: You must implement manual backprop for the UniversalNode. The node has 3d->d encoder and d->3d decoder. Compute gradients analytically.
3. **Progressive training**: Train layer 0 first (on embedding activations), freeze it, then train layer 1 (on frozen layer-0 outputs), etc. For cross-layer sharing: after training each layer, copy weights to all subsequent layers. Then re-train the next layer.
4. **Weight sharing with gradient averaging**: When a node is shared across multiple positions, accumulate gradients from all positions, then average before applying the update.
5. **P1-E (non-recursive)**: The node's encoder takes 3 slots of d_in=8 (input dim = 24) and outputs d_out=16. The decoder reconstructs back to 3x8. The embedding is still d=8, but the top-layer codes are 10 x 16 = 160 dimensions.
6. **Embedding**: Use a learnable (2, d) lookup table for binary to d-dim. Initialize with small random values. The embedding IS trained during layer 0 training (gradients flow back through it).
7. **Batch training**: For efficiency, process all positions in a layer simultaneously using batched matrix operations.

## File paths
- All source code: `src/` directory
- Results: `phase_1/results.csv`
- Report: `phase_1/REPORT.md`
- Pre-registration: `src/pre_registration.md`

## Success Criterion
All 25+5 runs complete successfully (no crashes), results.csv is populated, and REPORT.md contains the complete comparison with pass/fail assessment.
