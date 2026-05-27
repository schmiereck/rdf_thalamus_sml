# Research Manager Log - Iteration 005

## Iteration 005 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
A single set of UniversalNode weights, trained jointly on both spatial and temporal
JEPA objectives applied to a spatiotemporal input grid (16 binary pixels × 32 timesteps),
can produce effective spatiotemporal representations. Specifically, P3-C (shared weights,
joint training) will achieve mean classification accuracy within 15 percentage points of
P3-B (separate spatial/temporal weights, joint training) on four spatiotemporal pattern
benchmarks (moving blob, expanding/contracting blob, periodic spatiotemporal, object
permanence). This would demonstrate that the zero-shot transfer failure was caused by
single-axis optimization, not by fundamental incompatibility between spatial and temporal
processing in the UniversalNode architecture.

**Proposed Falsification Criterion:**
Primary: P3-C mean 4-class classification accuracy < P3-B mean accuracy - 15pp
across the four spatiotemporal pattern benchmarks (each benchmark evaluated with
5 seeds, linear probe on final code vector). This would prove that even under
joint optimization, a single weight set cannot serve both spatial and temporal
processing — the strong universal hypothesis is falsified and the practical
conclusion is "same architecture, per-axis weights."

Secondary: P3-C mean accuracy < P3-A mean accuracy - 20pp, confirming that the
shared-weight model is not viable even compared to the separately-trained baseline.

Tertiary: P3-C mean accuracy < 2× chance (< 50% for 4-class), indicating that
shared weights under joint training produce representations barely above random.

**Proposed Method:**
STEP 1: Create spatiotemporal dataset generator (src/spatiotemporal_dataset.py)
- Generate 4 pattern classes over a 16×32 binary spatiotemporal grid:
  * Class 0 — Moving blob: contiguous block of 1s that translates across spatial
    positions over time (varying speed, starting position, blob width)
  * Class 1 — Expanding/contracting blob: blob whose spatial extent grows then
    shrinks over time (varying max width, expansion rate)
  * Class 2 — Periodic spatiotemporal: pattern repeating in both space and time
    (varying spatial and temporal periods)
  * Class 3 — Object permanence: blob present, disappears for k steps, reappears
    at same position (varying gap length, blob position, blob width)
- Each class: 500 training samples, 200 test samples (per seed)
- Add noise variants (10-20% pixel flip probability) for robustness testing

STEP 2: Create spatiotemporal encoder (src/spatiotemporal_encoder.py)
- Architecture: sequential spatial-then-temporal processing with UniversalNode
  * Spatial pass: 3 layers of kernel-3, stride-1 nodes over 16 input pixels
    Layer 0: 14 positions, Layer 1: 12, Layer 2: 10 → top spatial code
  * Temporal pass: 3 layers of kernel-3, stride-1 nodes over 32 timesteps
    applied to the 10 top-layer spatial codes at each timestep
    Layer 0: 30 positions, Layer 1: 28, Layer 2: 26 → final temporal code
  * Final representation: mean-pool the temporal top layer across spatial positions
- Three variants sharing the same architecture code:
  * P3A: W_spatial (trained separately) + W_temporal (trained separately)
  * P3B: W_spatial + W_temporal (both trained jointly with combined loss)
  * P3C: W_shared (single weight matrix for both passes, trained jointly)
- UniversalNode: same as Phase 1/2 (kernel-3, 3-slot input, d=16, JEPA + VICReg)

STEP 3: Implement combined JEPA training (src/run_phase3.py)
- JEPA objective for spatial axis: at each spatial layer, predict left and right
  neighbor node outputs from current node output (bidirectional)
- JEPA objective for temporal axis: at each temporal layer, predict past and
  future neighbor node outputs from current node output
- VICReg collapse prevention on all node outputs (variance, covariance penalties)
- Combined loss: alpha * spatial_jepa + (1-alpha) * temporal_jepa + vicreg
  with alpha=0.5 (equal weighting)
- Training: 200 epochs, Adam optimizer, lr=1e-3, batch_size=32
- For P3-A: train spatial JEPA alone (200 epochs), then freeze spatial weights
  and train temporal JEPA alone (200 epochs)
- For P3-B: train both losses jointly (200 epochs) with separate W_s and W_t
- For P3-C: train both losses jointly (200 epochs) with shared W

STEP 4: Evaluation protocol (src/evaluate_phase3.py)
- Linear probe: train a single linear classifier (no hidden layer) on the
  final code vectors, 4-class classification
- Per-benchmark evaluation: compute accuracy for each of the 4 pattern types
  separately, then compute mean accuracy
- 5 seeds per variant for statistical significance
- Compute: mean accuracy, std, P3-C vs P3-B gap, P3-C vs P3-A gap
- Parameter count comparison across variants
- Paired t-test between P3-C and P3-B across seeds
- Also evaluate per-axis JEPA loss to diagnose any axis dominance

STEP 5: Create report (phase_3/REPORT.md)
- Comparison table: P3-A, P3-B, P3-C accuracy (mean ± std) per benchmark
- Gap analysis: P3-C - P3-B, P3-C - P3-A
- Parameter count: P3-C should have ~50% of P3-B parameters
- Per-axis JEPA loss analysis
- Statistical significance tests
- Recommendation: if P3-C within 15pp of P3-B → universality viable;
  if not → per-axis weights are the practical path

Files to create/modify:
- src/spatiotemporal_dataset.py (new)
- src/spatiotemporal_encoder.py (new, reuses UniversalNode from Phase 1/2)
- src/run_phase3.py (new)
- src/evaluate_phase3.py (new)
- src/test_spatiotemporal.py (new, self-tests)
- phase_3/REPORT.md (new)
- src/pre_registration.md (auto-generated from this plan)

---

## Iteration 005 -> Planner [Strategic Guidance]

# Manager's Note: Strategic Guidance for Phase 3 (Unified Spatiotemporal Grid)

I have reviewed your proposed research plan for Phase 3. The transition to a unified spatiotemporal grid is the logical next step, and your formulation of the **P3-A / P3-B / P3-C** comparison is excellent. It directly addresses the core tension of our project: **Is the universal node's parameter set truly unified across space and time, or is parameter specialization necessary?**

To ensure scientific rigour and prevent technical dead-ends, you must address the following three strategic points before proceeding to execution.

---

### 1. Strict Architectural Compatibility for Shared Weights (The Dimension Constraint)
In Phase 2, we established that the Universal Node operates on $3 \times d$ inputs and outputs a $d$-dimensional vector. For Phase 3's **P3-C (Fully Shared Weights)** to be mathematically viable:
*   **Every single node** in both the spatial and temporal hierarchies must have the exact same weight shape: $\mathbb{R}^{3d} \to \mathbb{R}^d$.
*   If your spatial Layer 0 operates directly on raw 1D binary pixels, its input dimension would be $3 \times 1$, making parameter sharing with higher layers or temporal layers impossible.
*   **Mandate:** You must implement an explicit, non-learned (or separately trained) **pixel-embedding layer** at the very bottom of the spatial pipeline to project the raw binary inputs into $d$-dimensional space *before* they enter spatial Layer 0. This ensures dimension homogeneity across the entire spatiotemporal grid.

### 2. The Construction-vs-Empirical Test: Guarding Against Shortcut Features
We must ensure that the four spatiotemporal classes (Moving Blob, Expanding/Contracting Blob, Periodic Spatiotemporal, Object Permanence) cannot be distinguished via trivial "shortcuts" (e.g., a spatial-only slice or a static temporal average):
*   **Design Check:** If a linear probe can classify the sequence with 90% accuracy using only the first frame, your dataset has a loophole. Ensure that the classes are balanced such that static spatial frames or non-spatial temporal averages are insufficient for high classification accuracy.
*   **Representation Pooling:** Clearly define how the final spatiotemporal grid representation is aggregated for the linear probe. I suggest average-pooling across the remaining spatial positions to obtain a temporal sequence of shape $(T_{out}, d)$, and then either flattening or temporally pooling this sequence. Do not allow high-dimensional flattening of the raw grid to bypass the bottleneck, as this would allow the linear probe to reconstruct the raw inputs and solve the task trivially.

### 3. Pre-Registration & Falsification Integrity
Your proposed pre-registration criteria are clear and quantitative. 
*   **Action:** Before running any training or evaluation scripts, you must write and commit your exact hypothesis and the three falsification criteria (Primary: $\text{Acc}_{\text{P3-C}} < \text{Acc}_{\text{P3-B}} - 15\text{pp}$; Secondary: $\text{Acc}_{\text{P3-C}} < \text{Acc}_{\text{P3-A}} - 20\text{pp}$; Tertiary: $\text{Acc}_{\text{P3-C}} < 50\%$) to `src/pre_registration.md`.
*   **Skeptic's Boundary:** If P3-C fails the primary falsification criterion, you must report this as an honest, clean null result for the *strong* universal parameter hypothesis. We will not engage in post-hoc parameter tuning or loss-weight tweaking to "rescue" P3-C. Failing P3-C simply means that while the **architectural type** is universal, **parameter specialization per physical axis is a biological and mathematical necessity**—which is itself a highly valuable, publishable scientific finding.

---

**You are cleared to write the pre-registration file and proceed to the implementation of Phase 3.** Keep your language sober, report your metrics honestly, and let the data speak.

---

