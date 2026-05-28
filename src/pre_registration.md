# RDF Scientific Pre-Registration

*   **Iteration:** 005
*   **Phase:** 3 — Unified Spatiotemporal Grid

## 1. Hypothesis

A single set of UniversalNode weights, trained jointly on both spatial and temporal JEPA objectives applied to a spatiotemporal input grid (16 binary pixels × 32 timesteps), can produce effective spatiotemporal representations. Specifically:

- **H1 (Training Gain):** Trained P3-C will outperform Untrained P3-C by ≥ 10 percentage points (pp) on 4-class spatiotemporal classification (with p < 0.05 and Cohen's d ≥ 1.0 across 5 seeds).
- **H2 (Anisotropy Penalty):** The performance gap between P3-B (separate spatial/temporal weights) and P3-C (shared weights) will be ≤ 10pp.
- **H3 (Viability):** P3-C mean accuracy will be within 15pp of P3-B mean accuracy.

## 2. Falsification Criteria

- **F1:** Trained P3-C mean test accuracy minus Untrained P3-C mean test accuracy < 10pp → training does not produce useful representations beyond what the architecture provides for free.
- **F2:** P3-B mean test accuracy minus P3-C mean test accuracy > 10pp → the shared-weight constraint imposes a significant expressivity penalty, falsifying the strong universal parameter hypothesis.
- **F3:** P3-C mean test accuracy < P3-A mean test accuracy - 20pp → the shared-weight model is not viable even compared to the separately-trained baseline.
- **F4:** P3-C mean accuracy < 50% (2× chance for 4 classes) → representations are barely above random.

If F1 or F2 is triggered, the strong universal parameter hypothesis is falsified and the practical conclusion is "same architecture, per-axis weights."

## 3. Proposed Method

- **Architecture:** Sequential spatial (3 layers, kernel-3, stride-1) → transpose → temporal (3 layers, kernel-3, stride-1), with d=16 throughout.
- **Variants:**
  - P3-A: Separate spatial + temporal nodes, trained sequentially (spatial first, then temporal)
  - P3-B: Separate spatial + temporal nodes, trained jointly (alpha=0.5)
  - P3-C: Single shared node for both axes, trained jointly (alpha=0.5)
  - Untrained: P3-B architecture with frozen random weights (only JEPA predictors trained)
- **Training:** JEPA objective (bidirectional neighbor prediction + VICReg collapse prevention) on each layer's codes, Adam optimizer, lr=1e-3, 200 epochs, batch_size=32.
- **Dataset:** 4 spatiotemporal pattern classes (moving blob, expanding blob, periodic spatiotemporal, object permanence) on 16×32 binary grids, 500 train/200 test per class per seed.
- **Evaluation:** Linear probe (SimpleLogisticRegression) on mean-pooled final codes, 4-class classification accuracy.
- **Seeds:** 5 seeds (42, 43, 44, 45, 46) per variant.
- **Statistics:** Paired t-tests, Cohen's d, per-class accuracies, shortcut baselines (single-frame and temporal-average).

---
*Pre-registered before experiment execution.*
