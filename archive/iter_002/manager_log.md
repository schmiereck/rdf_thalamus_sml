# Research Manager Log - Iteration 002

## Iteration 002 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
A hierarchical encoder using kernel-3 stride-1 Sparse Autoencoder nodes
(3 layers over 16 binary inputs, d=8 per slot) with cross-layer weight
sharing and recursive dimensions (dim_out = dim_in per slot = 8) achieves:
(a) linear-probe accuracy ≥ 80% on five structured 16-bit input categories,
and (b) accuracy within 15 percentage points of an independent-weights-per-node
upper bound (P1-C), when both are trained with local reconstruction objectives
(MSE + L1 sparsity) without end-to-end backpropagation.

Specifically, the strict universal-node form (single weight matrix shared across
all layers and positions, recursive d=8) does NOT sacrifice more than 15pp of
classification accuracy relative to the fully independent per-node weights
upper bound, confirming that the universal-node architecture is expressively
viable for spatial hierarchy.

**Proposed Falsification Criterion:**
The hypothesis is falsified if EITHER:
(1) P1-B (cross-layer sharing, d=8) achieves linear-probe accuracy < 80%
    on the 5-category classification task, OR
(2) The accuracy gap P1-C − P1-B exceeds 15 percentage points (e.g.,
    P1-C ≥ 80% and P1-B < 65%), demonstrating that cross-layer weight
    sharing sacrifices too much expressivity for the universal-node
    architecture to be viable.

Additionally, P1-D (d=4) is expected to underperform P1-B (d=8), and
P1-E (wider output) is expected to outperform P1-B; if P1-D matches or
exceeds P1-B, or if P1-E provides no improvement over P1-B, these
secondary predictions are falsified (informing dimension design choices).

**Proposed Method:**
EXPERIMENTAL PROTOCOL — Phase 1: Spatial Hierarchy without Time

1. CREATE src/node.py — UniversalNode class
   - Encoder: Linear(3d, d) + tanh activation
   - Decoder: Linear(d, 3d) (reconstruction)
   - Loss: MSE(input, reconstruction) + λ * L1(code)
   - Methods: forward(x_3d) → code, reconstruct(code) → x_hat
   - Support weight sharing: parameters can be shared across instances

2. CREATE src/hierarchical_encoder.py — HierarchicalEncoder class
   - Input: 16 binary pixels → learnable embedding (2×d lookup table)
   - Stack 3 layers of kernel-3 stride-1 nodes
   - Configurable weight_sharing mode: 'within_layer' | 'cross_layer' | 'none'
   - Configurable d per slot (8 for P1-A/B/C, 4 for P1-D)
   - For P1-E: support d_in=8, d_out=16 (non-recursive)
   - Training: layer-by-layer local reconstruction loss, no cross-layer gradient flow
   - For shared weights: average gradients across layers before update
   - Forward: returns top-layer codes (10 × d flattened)

3. CREATE src/dataset_phase1.py — Five structured 16-bit datasets
   - Category 1: Uniform random bits (control)
   - Category 2: Single-blob (one contiguous run of 1s, random position & width)
   - Category 3: Two-blob (two separate runs of 1s)
   - Category 4: Periodic patterns (periods 2, 3, 4, with random phase)
   - Category 5: Mixed noise (structured base + random bit flips at 10-20% rate)
   - Each category: 200 train + 100 test samples = 1000 train + 500 test total
   - Labels: category index (0-4) for linear probe evaluation

4. CREATE src/eval_phase1.py — Evaluation module
   - Linear probe: fit sklearn-free logistic regression on top-layer codes
     (simple gradient descent, 200 epochs, lr=0.1, no regularization)
   - Train on train-set codes, evaluate accuracy on test-set codes
   - Also compute: per-layer reconstruction MSE, code sparsity, parameter count
   - Report per-config, per-seed results

5. CREATE src/run_phase1.py — Experiment runner
   - 5 configurations (P1-A through P1-E) × 5 seeds (42-46) = 25 runs
   - Each run: instantiate HierarchicalEncoder, train unsupervised, evaluate
   - Save results to phase_1/results.csv
   - Generate phase_1/REPORT.md with comparison table and pass/fail assessment

6. GENERATE phase_1/REPORT.md — Comparison report including:
   - Table: config × metric (accuracy, params, sparsity, recon_loss)
   - P1-B vs P1-C gap analysis (primary hypothesis test)
   - P1-D vs P1-B dimension comparison
   - P1-E vs P1-B recursive-constraint comparison
   - P1-A vs P1-B within-layer vs cross-layer comparison
   - Pass/fail on each Phase 1 success criterion

CONTROL CONDITIONS:
- P1-C (no sharing, d=8) serves as the expressivity upper bound
- P1-A (within-layer sharing) serves as the standard CNN baseline
- Random-init untrained encoder serves as chance-level baseline (~20% for 5 classes)
- All configs use the same training budget (100 epochs per layer), same dataset,
  same seeds, same embedding initialization

HYPERPARAMETERS (fixed across all configs):
- d = 8 per slot (except P1-D: d=4, P1-E: d_out=16)
- λ_L1 = 0.002 (sparsity penalty, from Phase 0 P0-D tuning)
- learning_rate = 0.01
- epochs = 100 per layer
- batch_size = 32
- 3 layers (depths: 14, 12, 10 positions)
- seeds: 42, 43, 44, 45, 46

FILES MODIFIED: None (all new files; existing src/ files are read-only references)
FILES CREATED: src/node.py, src/hierarchical_encoder.py, src/dataset_phase1.py,
               src/eval_phase1.py, src/run_phase1.py, phase_1/REPORT.md

---

## Iteration 002 -> Planner [Strategic Guidance]

# Manager's Note: Strategic Guidance for Phase 1

Welcome to Phase 1. Moving from the 3-bit smoke test to a 16-bit spatial hierarchy is the first true test of the Universal Node hypothesis. To ensure we do not fall into self-deception, we must apply strict scientific discipline to our experimental design. 

Please refine your research plan and ensure that your automatically generated `src/pre_registration.md` includes the following corrections and rigorous criteria before execution.

### 1. The Untrained Baseline Control (Construction-vs-Empirical Test)
*   **The Trap:** A linear probe operating on a flattened 10-position $\times\ d$-dimensional representation (e.g., $10 \times 8 = 80$ dimensions) of a simple 16-bit input can easily achieve high classification accuracy $(\ge 80\%)$ purely due to random projection and embedding-level separation, without *any* unsupervised representation learning occurring.
*   **The Mandate:** You must evaluate an **untrained (randomly initialized) control** of the exact same hierarchical architecture (including the input embedding layer). Your hypothesis is partially falsified if the trained P1-B encoder does not outperform this untrained baseline by at least **15 percentage points** in linear-probe accuracy. We must prove our local training objective actually extracts structured features rather than merely serving as a random projector.

### 2. Tightening the Sparsity Constraint
*   **The Trap:** An autoencoder can easily preserve information by utilizing dense continuous values, essentially bypassing the bottleneck. Our project is explicitly about *Sparse* Universal Nodes (HSUN).
*   **The Mandate:** Your falsification criteria must explicitly reject models that achieve high classification at the cost of representation sparsity. You must define a quantitative sparsity threshold: **The average code sparsity (fraction of elements below $10^{-3}$ in magnitude) for the trained P1-B codes must be $\ge 50\%$.** If the model achieves $\ge 80\%$ accuracy but fails this sparsity threshold, the hypothesis is falsified.

### 3. Dissecting Weight Sharing & Representation Drift
*   **The Trap:** In a hierarchical model where weights are shared across layers, training all layers simultaneously with local reconstruction losses leads to extreme representation drift. Layer $l+1$ is trying to reconstruct an input from Layer $l$ that is changing dynamically, while both layers are constrained to use the exact same weight matrix.
*   **The Mandate:** In your pre-registration, explicitly define the training mechanics. If you use simultaneous training with gradient averaging, explain how you stabilize the moving-target problem. If you use progressive training (e.g., training layer 1, copying to layers 2/3, freezing, then training layer 2, etc.), explain how that complies with the "universal node" sharing constraint. This choice must be documented clearly as a controlled variable.

### Language & Reporting Discipline
When compiling `phase_1/REPORT.md`, strictly adhere to our non-sensationalist language guidelines. Report the raw statistical realities. If the cross-layer weight sharing (P1-B) fails to remain within 15% of the unshared baseline (P1-C), document this as a highly valuable **honest null result** that challenges the strict universal-node hypothesis. Do not attempt to tune hyperparameters post-hoc to force a pass. Proceed with these modifications.

---

