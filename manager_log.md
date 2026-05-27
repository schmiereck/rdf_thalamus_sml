# Research Manager Log

## Iteration 001 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
With 3 binary inputs (8 possible states), all five encoder types can be trained
end-to-end, and each non-trivial encoder (P0-B SDR, P0-C SOM, P0-D Sparse AE,
P0-E Predictive Coding) will produce codes where the Spearman rank correlation
between pairwise code cosine similarity and pairwise input inverse Hamming distance
is ≥ 0.6. Furthermore, the locally-trained encoders (P0-B, P0-C, P0-E) will
achieve similarity preservation within 0.15 (absolute ρ difference) of the
globally-trained sparse autoencoder (P0-D) baseline at this trivial scale.

**Proposed Falsification Criterion:**
The hypothesis is falsified if EITHER:
(1) Any non-trivial encoder (P0-B through P0-E) fails to achieve Spearman ρ ≥ 0.6
    between code cosine similarity and input inverse Hamming distance, OR
(2) Any locally-trained encoder (P0-B SDR, P0-C SOM, P0-E Predictive Coding)
    achieves ρ more than 0.15 below the P0-D Sparse Autoencoder baseline.
Additionally, if any implementation cannot run end-to-end (crashes, fails to
converge, or produces NaN/constant outputs), the smoke test fails.

**Proposed Method:**
Step-by-step experiment:

1. BUILD HARNESS (src/harness.py):
   - Dataset generator: enumerate all 8 binary-3-tuples, plus 10 noise variants
     per state (bit-flip probability 0.1), yielding ~88 samples.
   - Similarity evaluator: compute all 28 unique pairwise input Hamming distances
     (for the 8 base states) and their inverse; compute all pairwise code cosine
     similarities; return Spearman ρ.
   - Abstract Encoder interface with train(), encode(), and dim_out property.
   - Linear probe helper: simple logistic regression on codes to classify input
     category (for later phases, but scaffolded now).

2. IMPLEMENT ENCODERS:
   - src/encoders/lookup_table.py (P0-A): One-hot embedding of 3-bit input.
     dim_out=8. Trivial — just maps each state to a unit vector.
   - src/encoders/spatial_pooler.py (P0-B): HTM-style SDR. Input projected via
     random matrix, k-WTA sparsification (k=5 for d=16). Hebbian-like permanence
     update to input. dim_out=16.
   - src/encoders/som.py (P0-C): Kohonen SOM on a 1D grid of size 16. Competitive
     winner-take-all with neighborhood update. dim_out=16 (grid node weights as code).
   - src/encoders/sparse_autoencoder.py (P0-D): Single-layer autoencoder with
     hidden dimension 16, ReLU activation, L1 sparsity penalty (λ=0.01).
     Trained via reconstruction loss (MSE + L1). This is the global-optimization
     baseline.
   - src/encoders/predictive_coding.py (P0-E): ngclearn-inspired local-error node.
     Single layer with top-down prediction error as local learning signal.
     Lateral inhibition for sparsity. dim_out=16.

3. RUN EXPERIMENT (src/run_phase0.py):
   - Instantiate each encoder with dim_out=16 (except P0-A which is dim_out=8).
   - Train each on the dataset (50 epochs for iterative methods; 1 pass for P0-A).
   - Encode all 8 base states and 80 noise variants.
   - Compute pairwise cosine similarity of base-state codes.
   - Compute Spearman ρ between code cosine similarity and inverse Hamming distance.
   - Also compute: sparsity of codes (fraction of near-zero activations),
     reconstruction error (where applicable), training time.
   - Run 5 seeds (42, 43, 44, 45, 46) for each method to assess variance.

4. GENERATE REPORT (phase_0/REPORT.md):
   - Table of Spearman ρ (mean ± std across seeds) for each method.
   - Table of code sparsity, reconstruction error, training time.
   - Scatter plots of cosine similarity vs inverse Hamming distance for each method.
   - Explicit pass/fail against success criteria.
   - Recommendation: which method(s) to carry forward as the Phase-1 baseline.

5. FILES TO CREATE/MODIFY:
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

Control: P0-A (lookup table) is the lower bound — it must pass ρ ≥ 0.6 trivially
(since identical inputs → identical one-hot → cosine=1, different inputs → different
one-hot → cosine=0, and Hamming distance perfectly orders the off-diagonal).
P0-D (sparse AE, global optimization) is the upper-bound reference for local methods.
All encoders receive identical input data and are evaluated on identical metrics.

Key parameter: d = 16 for all non-trivial encoders. This is chosen to be large
enough for sparse distributed representations of 8 states (sparsity ~5/16 ≈ 31%)
while matching the recursability constraint (dim_out is a fixed vector dimension
that could equal a slot dimension in later phases).

---

## Iteration 001 -> Planner [Strategic Guidance]

### Manager's Note: Strategic Guidance for Phase 0

As we bootstrap the HSUN project, we must establish flawless experimental hygiene. I have reviewed your proposed plan for Phase 0 and detected a significant mathematical fallacy, alongside a potential loophole in your metric evaluation. You must address these points before writing the pre-registration and initiating execution.

---

#### 1. The One-Hot Similarity Fallacy (Scientific Discipline)
In your draft, you state: *"P0-A (lookup table) is the lower bound — it must pass $\rho \ge 0.6$ trivially ... and Hamming distance perfectly orders the off-diagonal."* 

This is mathematically incorrect. Because one-hot vectors are mutually orthogonal, the cosine similarity between any two *distinct* input states is always exactly $0.0$, regardless of whether their Hamming distance is 1, 2, or 3. There is no gradient. A flat vector of off-diagonal similarities cannot order or correlate with Hamming distances; the correlation will be mathematically degenerate or zero. 

*   **Direction:** Reframe P0-A's expected result. P0-A is a control that *should fail* the similarity-preservation test ($\rho \approx 0$). This failure is the exact scientific justification for why we require distributed representations (P0-B through P0-E) rather than simple lookup tables. Do not expect P0-A to pass $\rho \ge 0.6$.

#### 2. Strict Off-Diagonal Evaluation (Metric Hygiene)
If you calculate the Spearman correlation ($\rho$) across all pairwise combinations *including self-pairs* (the diagonal of the similarity matrix), the correlation coefficient will be artificially inflated because identical inputs always map to identical codes (cosine similarity $1.0$). 

*   **Direction:** Your pre-registration and evaluation code must explicitly calculate the Spearman $\rho$ **strictly on distinct pairs (the off-diagonal elements)**. This ensures we are measuring the true topological preservation of the representation space rather than self-identity.

#### 3. Pre-Registration Mandate
The Orchestrator will automatically write and commit your finalized hypothesis and quantitative falsification criteria to `src/pre_registration.md` before execution. 

*   **Direction:** Update your hypothesis and falsification criteria to:
    1.  Exempt P0-A from the $\rho \ge 0.6$ success threshold (expecting it to fail/be degenerate).
    2.  Explicitly state that $\rho$ is computed only on distinct (off-diagonal) pairs.
    3.  Ensure the sub-agents read and strictly adhere to this pre-registered protocol during code implementation and evaluation. Do not alter thresholds post-hoc if a local method falls short of the autoencoder baseline; report the null or negative result honestly.

---

