## Task: Implement All Five Encoders and the Experiment Runner

You are implementing Phase 0 of the HSUN project. The harness (`src/harness.py`) and pre-registration (`src/pre_registration.md`) already exist.

READ `src/pre_registration.md` and `src/harness.py` first to understand the encoder interface, dataset format, and evaluation metrics.

### 1. Fix harness.py unicode issue
In `src/harness.py`, the self-test function uses the Unicode character ρ (rho) in a print statement which causes UnicodeEncodeError on Windows. Replace ALL instances of 'ρ' in print/format strings with 'rho'. Also check for any other non-ASCII characters that could cause issues on cp1252 consoles.

### 2. Create `src/encoders/__init__.py`
Create the registry with an ENCODER_REGISTRY dict that maps encoder IDs to encoder classes. Leave it importable but the actual classes will be registered as they're created.

### 3. Implement All Five Encoders

Each encoder must inherit from `src.harness.EncoderBase` and implement `train()`, `encode()`, and `dim_out` property.

#### P0-A: `src/encoders/lookup_table.py` — LookupTableEncoder
- dim_out=8
- Maps each unique 3-bit input to a one-hot vector
- train(): just stores the mapping (no actual training needed)
- encode(): returns one-hot for known states, zero vector for unknown
- This is the NEGATIVE CONTROL — expected to fail ρ ≥ 0.6

#### P0-B: `src/encoders/spatial_pooler.py` — SpatialPoolerEncoder  
- dim_out=16
- HTM-style SDR (Sparse Distributed Representation)
- Input projected via random connection matrix (3→16), then k-WTA sparsification (k=5)
- Hebbian-like permanence update: strengthen connections to active inputs
- train(): iterate over inputs, update permanences, reinforce active connections
- encode(): project input, apply k-WTA (top k activations kept, rest zeroed)
- Use a seed-dependent random matrix for the projection
- Initialize permanences at 0.5 with some noise; only connections above threshold (0.5) are connected

#### P0-C: `src/encoders/som.py` — SOMEncoder
- dim_out=16
- Kohonen Self-Organizing Map on a 1D grid of 16 units
- Each unit has a weight vector of dimension 3 (matching input)
- The "code" for an input is the weight vectors of ALL 16 units (flattened = 16*3=48? No, use a different approach)
- Actually, let's make it cleaner: the code is the activation pattern across the 16 grid units. For each input, compute the distance to each unit's weight vector, then apply a Gaussian neighborhood around the winner. The 16-dimensional output is this activation pattern.
- train(): standard SOM training with decreasing learning rate and neighborhood radius
- encode(): compute activation pattern (Gaussian neighborhood around BMU)
- Use cosine distance or Euclidean distance for BMU selection

#### P0-D: `src/encoders/sparse_autoencoder.py` — SparseAutoencoder
- dim_out=16
- Single hidden layer autoencoder: input(3) → hidden(16, ReLU) → output(3, linear)
- Loss: MSE reconstruction + L1 sparsity penalty (lambda=0.01)
- Train via gradient descent (implement backprop manually in numpy — no torch/tf)
- train(): run gradient descent for specified epochs
- encode(): return the hidden layer activations (the 16-dimensional code)
- This is the GLOBAL-OPTIMIZATION BASELINE — expected to perform best

#### P0-E: `src/encoders/predictive_coding.py` — PredictiveCodingEncoder
- dim_out=16
- ngclearn-inspired local-error node
- Architecture: input(3) → hidden(16) with local learning
- Learning rule: weight update proportional to prediction error (top-down signal)
- Add lateral inhibition for sparsity: after activation, suppress nearby units
- train(): for each input, compute prediction, error, update weights locally
- encode(): forward pass through learned weights with sparsification (k-WTA or threshold)
- This tests whether local error signals can produce good codes

### Important Implementation Notes

1. **All encoders use numpy only** — no torch, tensorflow, or sklearn.
2. **Each encoder must accept a `seed` parameter** in its constructor for reproducibility. The experiment runner will pass different seeds.
3. **Handle edge cases**: zero-norm vectors in encode(), numerical stability in softmax/exp, etc.
4. **Return training metrics**: each train() method should return a dict with at least 'final_loss' or equivalent metric.
5. For gradient descent (P0-D), implement proper backprop. Learning rate ~0.01, use vectorized operations.
6. For P0-B, make sure the random projection matrix is seeded properly.
7. For P0-C, start with learning rate 0.5 and neighborhood radius that starts at 4 and decays.

### 4. Create `src/run_phase0.py`

The experiment runner that:
1. Reads pre-registration criteria from `src/pre_registration.md`
2. For each of 5 seeds (42, 43, 44, 45, 46):
   - Create a DatasetGenerator with that seed
   - Get base states (8) and all samples (88)
   - For each encoder (P0-A through P0-E):
     - Instantiate encoder with the current seed
     - Train on all 88 samples for 50 epochs
     - Encode the 8 base states
     - Compute: Spearman ρ (off-diagonal), sparsity, reconstruction error (where applicable), training time
     - Store all metrics
3. After all seeds: compute mean and std for each metric per encoder
4. Write results to `phase_0/REPORT.md` containing:
   - Summary table: Encoder | rho_mean ± rho_std | sparsity | recon_error | train_time | Pass/Fail
   - Note that P0-A is exempt from ρ ≥ 0.6
   - Comparison of local methods vs P0-D baseline
   - Recommendation for Phase 1
5. Also save raw results as `phase_0/results.csv` for later analysis

### 5. Run the experiment

Execute `python src/run_phase0.py` and verify that:
- All 5 encoders × 5 seeds = 25 runs complete without error
- P0-A gets ρ ≈ 0 (or NaN, handled gracefully) — confirming the negative control
- P0-B through P0-E achieve ρ ≥ 0.6 on off-diagonal pairs
- The report is generated at `phase_0/REPORT.md`
- Raw results saved at `phase_0/results.csv`

### Files to create/modify:
- src/harness.py (fix unicode)
- src/encoders/__init__.py (new)
- src/encoders/lookup_table.py (new)
- src/encoders/spatial_pooler.py (new)
- src/encoders/som.py (new)
- src/encoders/sparse_autoencoder.py (new)
- src/encoders/predictive_coding.py (new)
- src/run_phase0.py (new)
- phase_0/REPORT.md (generated)
- phase_0/results.csv (generated)

### Critical: Adhere to pre-registration
Read `src/pre_registration.md` first. The Spearman ρ MUST be computed on off-diagonal pairs only (as implemented in the harness). P0-A is exempt from ρ ≥ 0.6. Report honest results even if methods fail criteria.
