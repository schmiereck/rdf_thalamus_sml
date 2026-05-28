
# Phase 3: Run Fixed Experiments and Produce Results

The Phase 3 spatiotemporal code has had three critical bugs fixed (by previous sub-agents 5.2 and 5.3). Now you need to:

1. **Fill in the pre-registration file** at `src/pre_registration.md` with the following content:

```markdown
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
```

2. **Run the full experiment suite.** Execute:
```
cd <project_root> && python src/run_phase3.py
```
This runs 4 variants × 5 seeds = 20 training runs plus shortcut baselines. Each run is ~20-40 seconds, so the full suite should take ~15-30 minutes.

If it takes too long or seems stuck, you can try a smoke test first with `python src/run_phase3.py --smoke-test` to verify the pipeline works.

3. **After experiments complete**, read the results CSV at `phase_3/phase3_results.csv` and `phase_3/shortcut_baselines.csv`, and compute:
   - Mean ± std test accuracy per variant
   - Per-class accuracy per variant
   - P3-C vs Untrained gap (H1/F1)
   - P3-B vs P3-C gap (H2/F2)
   - P3-C vs P3-A gap (F3)
   - Statistical significance (paired t-test across seeds, Cohen's d)
   - Shortcut baseline accuracies

4. **Write a summary report** to `phase_3/REPORT.md` containing:
   - Comparison table: P3-A, P3-B, P3-C, Untrained accuracy (mean ± std) per benchmark
   - Gap analysis: P3-C - Untrained, P3-B - P3-C, P3-C - P3-A
   - Parameter count comparison
   - Per-axis JEPA loss analysis
   - Statistical significance tests
   - Pre-registration verdict: which criteria are triggered/not triggered
   - Shortcut baseline results (must be ≤ 50% to validate the dataset)

5. **Save the final results CSV** if not already saved.

IMPORTANT: The three bugs were already fixed by sub-agent 5.3:
- Bug 1: Temporal backward now uses `self.master_temporal.W_enc.T` (was `self.master_spatial.W_enc.T`)
- Bug 2: `dL_dx` starts as `np.zeros_like(x_final)` (was `np.full_like(x_final, 1/(T*S))`)
- Bug 3: P3-C now uses a SINGLE Adam step with combined gradients

Verify these fixes are in place before running. If any fix is missing, apply it.
