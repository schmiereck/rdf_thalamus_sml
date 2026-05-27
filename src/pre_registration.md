# RDF Scientific Pre-Registration

*   **Iteration:** 001
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis

With 3 binary inputs (8 possible states), all five encoder types can be trained
end-to-end. Non-trivial distributed encoders (P0-B SDR, P0-C SOM, P0-D Sparse AE,
P0-E Predictive Coding) will produce codes where the Spearman rank correlation
between pairwise code cosine similarity and pairwise input inverse Hamming distance
is ≥ 0.6 when computed on **DISTINCT (off-diagonal) pairs only**.

**P0-A (lookup table / one-hot) is expected to FAIL this criterion (ρ ≈ 0)**
because one-hot vectors are mutually orthogonal — this failure is the **scientific
justification for requiring distributed representations**. One-hot vectors for distinct
inputs have cosine similarity = 0 regardless of Hamming distance, so no correlation
with inverse Hamming distance can exist.

Locally-trained encoders (P0-B, P0-C, P0-E) will achieve similarity preservation
within 0.15 (absolute ρ difference) of the globally-trained sparse autoencoder
(P0-D) baseline.

## 2. Falsification Criterion

The hypothesis is falsified if **EITHER**:

1.  Any non-trivial encoder (P0-B through P0-E) fails to achieve Spearman ρ ≥ 0.6
    on **OFF-DIAGONAL pairs** between code cosine similarity and input inverse
    Hamming distance, **OR**
2.  Any locally-trained encoder (P0-B, P0-C, P0-E) achieves ρ more than 0.15
    below the P0-D Sparse Autoencoder baseline on off-diagonal pairs.
3.  Additionally, if any implementation cannot run end-to-end (crashes, fails to
    converge, or produces NaN/constant outputs), the smoke test fails.

**P0-A expected result:** P0-A (one-hot lookup table) is **EXEMPT** from the
ρ ≥ 0.6 threshold. We expect ρ ≈ 0 because one-hot vectors for distinct inputs
are mutually orthogonal (cosine similarity = 0 regardless of Hamming distance).
This failure validates the need for distributed representations.

## 3. Critical Metric Detail

Spearman ρ is computed **STRICTLY on distinct pairs** (off-diagonal elements of
the pairwise similarity matrix). Self-pairs (diagonal, where cosine similarity =
1.0 for identical inputs) are **excluded** to avoid artificial inflation.

For 8 base states, the full pairwise matrix has 8×8 = 64 entries. Excluding the
8 diagonal entries leaves 56 off-diagonal pairs (28 unique unordered pairs counted
once each — upper triangle without diagonal).

## 4. Proposed Method

Step-by-step experiment:

1.  BUILD HARNESS (src/harness.py):
    - Dataset generator: enumerate all 8 binary-3-tuples, plus 10 noise variants
      per state (bit-flip probability 0.1), yielding 88 samples.
    - Similarity evaluator: compute all pairwise input Hamming distances (for the
      8 base states) and their inverse; compute all pairwise code cosine
      similarities; compute Spearman ρ **only on off-diagonal pairs**.
    - Abstract Encoder interface with train(), encode(), and dim_out property.
    - Utility functions: sparsity computation, reconstruction error (MSE),
      linear probe accuracy (logistic regression on codes).

2.  IMPLEMENT ENCODERS:
    - src/encoders/lookup_table.py (P0-A): One-hot embedding of 3-bit input.
      dim_out=8. Trivial — just maps each state to a unit vector.
    - src/encoders/spatial_pooler.py (P0-B): HTM-style SDR. Input projected via
      random matrix, k-WTA sparsification (k=5 for d=16). Hebbian-like permanence
      update. dim_out=16.
    - src/encoders/som.py (P0-C): Kohonen SOM on a 1D grid of size 16. Competitive
      winner-take-all with neighborhood update. dim_out=16 (grid node weights as code).
    - src/encoders/sparse_autoencoder.py (P0-D): Single-layer autoencoder with
      hidden dimension 16, ReLU activation, L1 sparsity penalty (λ=0.01).
      Trained via reconstruction loss (MSE + L1). This is the global-optimization
      baseline.
    - src/encoders/predictive_coding.py (P0-E): ngclearn-inspired local-error node.
      Single layer with top-down prediction error as local learning signal.
      Lateral inhibition for sparsity. dim_out=16.

3.  RUN EXPERIMENT (src/run_phase0.py):
    - Instantiate each encoder with dim_out=16 (except P0-A which is dim_out=8).
    - Train each on the dataset (50 epochs for iterative methods; 1 pass for P0-A).
    - Encode all 8 base states.
    - Compute pairwise cosine similarity of base-state codes.
    - Compute **Spearman ρ on OFF-DIAGONAL pairs only** between code cosine
      similarity and inverse Hamming distance.
    - Also compute: sparsity of codes (fraction of near-zero activations),
      reconstruction error (where applicable), training time.
    - Run 5 seeds (42, 43, 44, 45, 46) for each method to assess variance.

4.  GENERATE REPORT (phase_0/REPORT.md):
    - Table of Spearman ρ (mean ± std across seeds) for each method.
    - Table of code sparsity, reconstruction error, training time.
    - Scatter plots of cosine similarity vs inverse Hamming distance for each method.
    - Explicit pass/fail against success criteria.
    - Recommendation: which method(s) to carry forward as the Phase-1 baseline.

5.  FILES TO CREATE/MODIFY:
    - src/harness.py (new) — dataset, metrics, encoder interface
    - src/encoders/__init__.py (new) — registry
    - src/encoders/lookup_table.py (new) — P0-A
    - src/encoders/spatial_pooler.py (new) — P0-B
    - src/encoders/som.py (new) — P0-C
    - src/encoders/sparse_autoencoder.py (new) — P0-D
    - src/encoders/predictive_coding.py (new) — P0-E
    - src/run_phase0.py (new) — main experiment runner
    - phase_0/REPORT.md (generated) — comparison report
    - src/pre_registration.md (generated) — this plan, committed

## 5. Encoder Role Summary

| Encoder | Type | Training | dim_out | ρ ≥ 0.6 Required? |
|---------|------|----------|---------|-------------------|
| P0-A Lookup Table | Local | None | 8 | **No — exempt (expected ρ ≈ 0)** |
| P0-B SDR (Spatial Pooler) | Local | Hebbian | 16 | Yes |
| P0-C SOM | Local | Competitive | 16 | Yes |
| P0-D Sparse AE | Global | Backprop | 16 | Yes (baseline) |
| P0-E Predictive Coding | Local | Error-driven | 16 | Yes |

Control: P0-A (lookup table) is the **negative control** — it must **fail** ρ ≥ 0.6
trivially (since distinct one-hot vectors are mutually orthogonal, yielding
cosine similarity = 0 for all off-diagonal pairs regardless of Hamming distance).
This failure is expected and validates the scientific premise that distributed
representations are necessary for similarity-preserving codes.

P0-D (sparse AE, global optimization) is the upper-bound reference for local methods.
All encoders receive identical input data and are evaluated on identical metrics.

Key parameter: d = 16 for all non-trivial encoders. This is chosen to be large
enough for sparse distributed representations of 8 states (sparsity ~5/16 ≈ 31%)
while matching the recursability constraint (dim_out is a fixed vector dimension
that could equal a slot dimension in later phases).

---
*Created automatically by the RDF Orchestrator prior to iteration execution.*
