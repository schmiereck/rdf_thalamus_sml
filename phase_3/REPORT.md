# Phase 3: Unified Spatiotemporal Grid -- Results Report

## Experiment Configuration
- Epochs: 30
- Train per class: 200
- Test per class: 100
- Batch size: 64
- Learning rate: 1e-3
- Seeds: 42-46
- Noise flip probability: 0.10
- Dataset: 4-class spatiotemporal binary grid (16 spatial x 32 temporal)

## Architecture Summary
| Variant | Description | Weight Sets | Params |
|---------|-------------|-------------|--------|
| P3-A | Sequential spatial->temporal | 2 (W_spatial, W_temporal) | 3,200 |
| P3-B | Joint training, separate weights | 2 (W_spatial, W_temporal) | 3,200 |
| P3-C | Unified, shared weights | 1 (W_shared) | 1,600 |
| Untrained | P3-B architecture, frozen weights | 2 (random, frozen) | 3,200 |

## Main Results

| Variant | Test Acc (mean+-std) | Train Acc (mean+-std) | Spatial Loss | Temporal Loss | Time (s) |
|---------|---------------------|----------------------|--------------|---------------|----------|
| P3-A | 0.4450+-0.0277 | 0.4502+-0.0297 | 15.0651+-0.2326 | 5.7340+-0.1138 | 412.6+-67.0 |
| P3-B | 0.4400+-0.0388 | 0.4645+-0.0278 | 15.9400+-0.2292 | 5.9354+-0.1997 | 158.3+-21.5 |
| P3-C | 0.4400+-0.0108 | 0.4593+-0.0135 | 15.7382+-0.1818 | 8.5090+-0.1626 | 141.4+-43.5 |
| Untrained | 0.4285+-0.0618 | 0.4280+-0.0650 | 20.5406+-0.6919 | 19.3339+-0.9514 | 75.7+-2.9 |

## Per-Class (Per-Task) Accuracies

| Variant | moving_blob | expanding_blob | periodic_st | object_permanence |
|---------|-------------|----------------|-------------|-------------------|
| P3-A | 0.6040 | 0.3000 | 0.1920 | 0.6840 |
| P3-B | 0.6000 | 0.2660 | 0.1940 | 0.7000 |
| P3-C | 0.5840 | 0.2740 | 0.2020 | 0.7000 |
| Untrained | 0.4920 | 0.4240 | 0.1060 | 0.6920 |

## Pre-Registration Falsification Tests

Criteria (from `src/pre_registration.md`):
- **F1**: P3-C mean test acc - Untrained mean test acc < 8pp OR p >= 0.05 OR Cohen's d < 1.0
- **F2**: P3-B mean test acc - P3-C mean test acc > 10pp
- **F3**: P3-C mean test acc < P3-A mean test acc - 20pp
- **F4**: P3-C JEPA training loss > 2x P3-B final JEPA loss
- If **ANY** criterion is triggered, the specific aspect of the hypothesis is **falsified**.

### F1: P3-C vs Untrained
- P3-C mean test accuracy: 0.4400
- Untrained mean test accuracy: 0.4285
- Gain: 1.15 percentage points
- Paired t-test: t = 0.4933, p = 0.6477
- Cohen's d: 0.2206
- Required: gain >= 8pp, p < 0.05, Cohen's d >= 1.0
- **Verdict: FAIL**

### F2: P3-B vs P3-C
- P3-B mean test accuracy: 0.4400
- P3-C mean test accuracy: 0.4400
- Penalty (P3-B - P3-C): 0.00 percentage points
- Required: penalty <= 10pp
- **Verdict: PASS**

### F3: P3-C vs P3-A
- P3-A mean test accuracy: 0.4450
- P3-C mean test accuracy: 0.4400
- Gap (P3-A - P3-C): 0.50 percentage points
- Required: gap < 20pp (i.e., P3-C >= P3-A - 20pp)
- **Verdict: PASS**

### F4: P3-C JEPA loss vs 2x P3-B JEPA loss
- P3-C mean combined JEPA loss (spatial + temporal): 24.2472
- P3-B mean combined JEPA loss (spatial + temporal): 21.8754
- 2x P3-B JEPA loss: 43.7507
- Required: P3-C loss <= 2x P3-B loss
- **Verdict: PASS**

### Overall Falsification Verdict
**At least one falsification criterion is TRIGGERED.**
Triggered criteria: F1.
Therefore, the specific aspect of the universal parameter hypothesis tested in Phase 3 is **falsified**.

## Shortcut Baseline Results

| Baseline | Train Acc (mean+-std) | Test Acc (mean+-std) |
|----------|----------------------|---------------------|
| single_frame_t0 | 0.3173+-0.0153 | 0.2305+-0.0067 |
| single_frame_t16 | 0.4330+-0.0071 | 0.3715+-0.0193 |
| single_frame_t24 | 0.3362+-0.0172 | 0.2755+-0.0190 |
| single_frame_t31 | 0.3457+-0.0088 | 0.2715+-0.0139 |
| single_frame_t8 | 0.3455+-0.0105 | 0.3020+-0.0289 |
| temporal_average | 0.3877+-0.0199 | 0.3260+-0.0384 |

## Per-Task Untrained Baseline Analysis

| Task | Untrained Accuracy | Flagged (>60%)? |
|------|-------------------|-----------------|
| moving_blob | 0.4920 | No |
| expanding_blob | 0.4240 | No |
| periodic_st | 0.1060 | No |
| object_permanence | 0.6920 | YES |

**Warning:** The following task(s) have Untrained per-class accuracy > 60%, which may indicate a potential shortcut or label leakage in the task design.

- **object_permanence**: 0.6920

## Key Findings

1. **Overall test accuracies are low (~41-48%)**, well above chance (25%) but far below what would constitute strong task learning.
2. **P3-C (unified/shared weights) underperforms P3-B (separate weights)** by 0.0pp, and is slightly below P3-A (sequential) by 0.5pp.
3. **P3-C does not demonstrate a statistically significant gain over Untrained** (gain = 1.1pp, p = 0.648, Cohen's d = 0.22).
4. **JEPA losses converge** for all variants, with P3-C's combined loss (24.25) within the 2x bound of P3-B (43.75).
5. **Shortcut baselines** achieve ~23-38% test accuracy, confirming that single-frame and temporal-average features are insufficient for the task.
6. **P3-C uses 50% fewer parameters** than P3-A/P3-B ({params_c:,} vs {params_b:,}), but this parameter efficiency does not translate into competitive accuracy.

## Conclusions

The Phase 3 experiment **fails to support** the universal parameter hypothesis.

The pre-registered falsification criteria were designed to test whether a single shared weight set (P3-C) could achieve performance competitive with sequential (P3-A) and joint-but-separate (P3-B) architectures. The results show:

- **F1 (Training Gain) is FAILED**: P3-C does not significantly outperform the untrained baseline, meaning the training procedure does not produce a meaningful learning signal for the unified weights.

Given these failures, the hypothesis that a single universal weight set can serve both spatial and temporal prediction while maintaining competitive classification accuracy is **not supported** by the Phase 3 data.

---
*Report generated automatically by phase_3/comprehensive_analysis.py*
