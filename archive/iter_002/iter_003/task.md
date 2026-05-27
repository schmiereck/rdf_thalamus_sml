
# Phase 1 Diagnostic: Root Cause Analysis for Training Objective Failure

## Context

Phase 1 experiments (both original and corrected) show a fundamental problem:
- All trained hierarchical configs (P1-A, P1-B, P1-C, P1-D, P1-E, P1-B-kwta) achieve ~33-36% accuracy
- The untrained baseline achieves ~48% accuracy
- P1-C (independent weights, upper bound) performs no better than P1-B (shared weights)
- This means the weight sharing constraint is NOT the bottleneck — the training objective is

The reconstruction objective (MSE + L1) optimizes for local input reconstruction, which doesn't preserve class-discriminative information. We need to determine: is the architecture fundamentally limited, or is the reconstruction objective the problem?

## Diagnostic Experiments

Run these quick diagnostic experiments to identify the root cause. Use the EXISTING code in src/ — read node.py, hierarchical_encoder.py, dataset_phase1.py, eval_phase1.py first.

### Experiment 1: Embedding-Only Baseline
Just use the binary → d-dimensional embedding as features (no hierarchical processing). Train the embedding, then use the 16×d flattened embedding as features for the linear probe. This tells us: is the embedding itself sufficient for classification?

Implementation: Create a simple script that:
1. Generates the Phase 1 dataset
2. Creates just the embedding (2, d) with Normal(0,1) init
3. Trains the embedding for 100 epochs by minimizing reconstruction loss (each d-dim embedding vector reconstructs the binary input — but actually this doesn't make sense since there's only 1 bit per position)
4. Actually, just use RANDOM embedding (Normal(0,1)), embed the 16 binary inputs, flatten to 16×8=128 features, run linear probe
5. This gives us the "flat random projection" baseline

### Experiment 2: Single-Layer (No Hierarchy) Baseline
Use just one layer of UniversalNodes (kernel-3 stride-1) on the embedded input. Output: 14 positions × 8 dims = 112 features. Train with reconstruction + L1. This tells us: is the DEPTH the problem?

### Experiment 3: Simultaneous Training
Modify the HierarchicalEncoder to train all layers simultaneously rather than progressively. All 3 layers train at the same time, with local reconstruction losses at each layer. For shared weights, gradients from all layers are averaged. This tests: does inter-layer coordination help?

### Experiment 4: Predictive Coding Node
Replace the UniversalNode's reconstruction objective with a predictive coding objective that includes lateral inhibition (adapted from P0-E which achieved rho=0.72 in Phase 0). The key differences:
- Add lateral inhibition to the code: after tanh, apply a competition step that suppresses weakly-activated neurons
- Use online (per-sample) gradient updates instead of batch
- Apply a hard threshold to zero out very small activations

For the lateral inhibition, after computing code = tanh(z), apply:
```python
# Competition: subtract mean of top-k activations
# This creates a form of k-WTA soft competition
top_k_mean = np.mean(np.sort(np.abs(code), axis=1)[:, -k:], axis=1, keepdims=True)
code = code * (np.abs(code) > top_k_mean * 0.5)
```

### Experiment 5: Increased L1 with Stronger Sparsity
Try l1_lambda = 0.05 (25x the default) with the corrected architecture. This tests whether stronger L1 can create meaningful sparse codes without collapse (since Normal(0,1) embeddings prevent the previous collapse issue).

## Implementation

Create a single script `src/diagnostic_phase1.py` that runs all 5 experiments with seeds [42, 43, 44, 45, 46]. For each experiment, report:
- Test accuracy (mean ± std)
- Code sparsity
- Reconstruction MSE (where applicable)

The script should use the existing `src/dataset_phase1.py` and `src/eval_phase1.py` infrastructure.

For Experiment 3 (simultaneous training), you can modify HierarchicalEncoder's train() method or create a subclass. The key change: instead of training layer-by-layer progressively, run all layers for each batch:
1. Forward pass through all layers to get activations
2. Compute reconstruction loss at each layer
3. Compute gradients at each layer
4. For shared weights, average gradients across layers before applying
5. Apply embedding gradients from layer 0

For Experiment 4 (predictive coding), modify the UniversalNode to add lateral inhibition in the forward pass and use online (per-sample) gradient updates in training.

## Output
Save results to `phase_1/diagnostic_results.csv` and print a summary table.

## Success Criterion
All 5 experiments complete and produce interpretable results. We need to determine:
- Can ANY local training objective reach ≥60% accuracy?
- Is the hierarchy itself the problem (compare Exp 1 vs Exp 2 vs full hierarchy)?
- Does simultaneous training help over progressive training?
- Does lateral inhibition/predictive coding help?
- Can stronger L1 create meaningful sparse codes?
