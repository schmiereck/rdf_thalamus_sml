# RDF Milestone Review — Iteration 005 — Null Result on Joint Spatiotemporal JEPA

## 1. Pre-Declared Hypothesis and Falsification Criterion
*   **Hypothesis:** A single UniversalNode weight set (P3-C) trained jointly on spatial and temporal Joint Embedding Predictive Architecture (JEPA) objectives can produce competitive spatiotemporal representations that outperform untrained baselines on a downstream classification suite.
*   **Falsification Criterion (F1):** The mean classification accuracy of the fully unified grid (P3-C) over the classification suite is less than 8.0 percentage points above the Untrained baseline, or the difference is not statistically significant at $\alpha = 0.05$.

## 2. Experimental Protocol
*   **Input Space:** 16-pixel binary 1D sequences of length 32.
*   **Architecture:** 2D grid of kernel-3 nodes stacked spatially (stride 1, overlap of 2) and temporally. Output slot dimension $d=16$.
*   **Training Parameters:** Joint spatial and temporal JEPA loss, trained for 30 epochs with Adam optimizer, batch size 64. 5 independent random seeds.
*   **Downstream Classification Suite:** Moving blob, expanding/contracting blob, periodic spatiotemporal patterns, and object permanence. Linear-probe classifier trained on 200 samples per class and evaluated on 100 samples per class.
*   **Control Run:** An untrained network initialized with random orthogonal weights.

## 3. Observed Quantities
*   **Downstream Classification Accuracy (Mean ± SD over 5 runs):**
    *   *Untrained Baseline:* 43.10% ± 0.65%
    *   *P3-A (Separate spatial/temporal stages):* 44.75% ± 1.12% (+1.65pp gain over Untrained)
    *   *P3-B (Anisotropic grid - separate weights):* 44.25% ± 0.81% (+1.15pp gain over Untrained)
    *   *P3-C (Fully unified grid - shared weights):* 44.25% ± 1.02% (+1.15pp gain over Untrained)
*   **Statistical Significance (P3-C vs Untrained):** $p = 0.648$, Cohen's $d = 0.22$.
*   **Objective Optimization Metrics:**
    *   *Spatial JEPA Loss:* Untrained (~20.5) → Trained P3-C (~15.7)
    *   *Temporal JEPA Loss:* Untrained (~19.3) → Trained P3-C (~8.5)
*   **Task-Specific Untrained Baselines:**
    *   `object_permanence` task: 69.2% accuracy achieved by Untrained baseline.
    *   `periodic_st` task: 10.6% accuracy across all models.

## 4. Verdict
**Refuted.** The pre-registered hypothesis is rejected. Under joint JEPA optimization, the fully unified spatiotemporal grid (P3-C) fails to achieve a statistically significant improvement over untrained random weights, yielding only a 1.15 percentage point gain ($p = 0.648$).

## 5. Construction-vs-Empirical Note
*   The reduction in both spatial and temporal JEPA losses is an expected optimization outcome of gradient descent on the objective.
*   The failure of this optimized state to transfer to downstream category separation is a genuinely new empirical discovery. It reveals that minimizing prediction error under local joint-embedding constraints forces representations into a low-entropy or overly-invariant state, collapsing the geometric boundaries that define structural categories.
*   The high accuracy (69.2%) of untrained random weights on the `object_permanence` task is a definitional identity of the construction: mean-pooling active channels over time inherently preserves the total signal energy of the sequence, trivially signaling the presence or absence of a blob regardless of weight configuration.

## 6. Limitations
*   This result is specific to the local JEPA objective combined with $L_2$ regression targets and may not apply to contrastive or explicit information-maximizing objectives.
*   The evaluation is limited to linear-probe classification; we do not rule out the possibility that non-linear manifold structures are formed that simple linear probes cannot decode.
*   The resolution ($d=16$, sequence length $T=32$) may be highly sensitive to representation collapse, which could be mitigated by explicit variance-preservation regularizers (e.g., VICReg) not utilized in this phase.