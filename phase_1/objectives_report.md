# Phase 1 v2 Results Report: Local Training Objectives

**Date:** 2025-01-20  
**Iteration:** 003  
**Experiments:** 7 configurations × 5 seeds (42–46), 200 epochs each

---

## Executive Summary

The JEPA local-objective hypothesis is **strongly validated**: JEPA-d8 achieves **62.1%** test accuracy, a **+15.96pp improvement** over the untrained baseline and a **+28.6pp improvement** over the best prior reconstruction-based result. The d=8 bottleneck is **refuted as the primary cause** of Phase 1 failure (JEPA-d16 only gains +3.1pp over JEPA-d8). Three of four objectives beat the untrained baseline, but **only JEPA meets the ≥5pp success bar**. The temporal-unification path to Phase 2 is **cleared**.

---

## Results Table

| Configuration | Test Accuracy | Train Accuracy | Sparsity | n_params |
|:---|:---|:---|:---|---:|
| **P1-B-JEPA-d8** | **62.12 ± 4.34%** | **70.58 ± 3.85%** | 0.010 ± 0.023% | 1,264 |
| **P1-B-JEPA-d16** | **65.20 ± 1.80%** | **80.50 ± 0.52%** | 0.003 ± 0.008% | 4,832 |
| P1-B-Contrastive-d8 | 50.64 ± 4.29% | 55.00 ± 5.38% | 0.112 ± 0.123% | 1,264 |
| P1-B-SFA-d8 | 50.56 ± 8.53% | 54.24 ± 7.26% | 0.008 ± 0.017% | 1,264 |
| P1-B-Hebbian-d8 | 23.96 ± 2.93% | 23.64 ± 4.61% | 0.000 ± 0.000% | 1,264 |
| Untrained-d8 | 46.16 ± 3.84% | 52.10 ± 5.23% | 0.169 ± 0.176% | 1,264 |
| Untrained-d16 | 54.60 ± 6.48% | 60.42 ± 5.36% | 0.121 ± 0.161% | 4,832 |

*All values are mean ± std across 5 random seeds.*

---

## Comparison vs Untrained Baseline

| Trained Config | Baseline | Mean Δ | t-stat | p-value | Significant? | RM Bar (≥5pp)? |
|:---|:---|---:|---:|---:|:---|:---|
| P1-B-JEPA-d8 | Untrained-d8 | **+15.96pp** | 5.713 | 0.0046 | **Yes** | **MEETS BAR** |
| P1-B-Contrastive-d8 | Untrained-d8 | +4.48pp | 1.664 | 0.1715 | No | FAILS BAR |
| P1-B-SFA-d8 | Untrained-d8 | +4.40pp | 1.023 | 0.3643 | No | FAILS BAR |
| P1-B-Hebbian-d8 | Untrained-d8 | **−22.20pp** | −8.262 | 0.0012 | **Yes (negative)** | FAILS BAR |
| P1-B-JEPA-d16 | Untrained-d16 | **+10.60pp** | 4.226 | 0.0134 | **Yes** | **MEETS BAR** |

*Paired t-tests, df=4. Significance threshold: p < 0.05.*

**Interpretation:** Only JEPA (both d=8 and d=16) produces a statistically significant and practically meaningful improvement over the corresponding untrained baseline. Contrastive and SFA show positive trends but fail to clear the 5pp bar and are not statistically significant at n=5. Hebbian learning catastrophically degrades performance, falling to ~24% (near chance for 5 categories = 20%).

---

## Evaluation of Pre-Registered Falsification Criteria

| Criterion | Description | Threshold | Actual | Verdict |
|:---|:---|:---|:---|:---|
| **C1** | JEPA hypothesis falsified if mean < 50% at d=8 | < 50% | **62.12%** | **NOT FALSIFIED** ✓ |
| **C2** | General local-objective falsified if ALL four < 48.4% at d=8 | All < 48.4% | JEPA 62.1%, Contrastive 50.6%, SFA 50.6%, Hebbian 24.0% | **NOT FALSIFIED** ✓ |
| **C3** | d=8 bottleneck SUPPORTED if d16 > d8 + 10pp | > 10pp | **3.08pp** | **NOT SUPPORTED** |
| **C4** | d=8 bottleneck REFUTED if d16 ≤ d8 + 5pp | ≤ 5pp | **3.08pp** | **REFUTED** ✓ |
| **C5** | Temporal-unification falsified if JEPA spatial < 50% | < 50% | **62.12%** | **NOT FALSIFIED** ✓ |

**Summary:**
- **C1 (JEPA hypothesis):** NOT FALSIFIED. JEPA-d8 at 62.12% comfortably exceeds the 50% threshold and even surpasses the pre-registered ≥60% target.
- **C2 (General local-objective):** NOT FALSIFIED. Three of four objectives exceed the 48.4% untrained baseline; only Hebbian fails.
- **C3/C4 (Bottleneck):** The d=8 bottleneck hypothesis is **REFUTED**. The gain from d=8 to d=16 is only 3.08pp, well within the ≤5pp refutation band. The bottleneck is **not** the primary cause of Phase 1 failure.
- **C5 (Temporal-unification):** NOT FALSIFIED. Since JEPA succeeds spatially (62.12% ≫ 50%), the same objective applied temporally in Phase 2 is not pre-emptively ruled out.

---

## d=8 vs d=16 Analysis

| Metric | JEPA-d8 | JEPA-d16 | Δ (d16 − d8) |
|:---|---:|---:|---:|
| Test Accuracy | 62.12 ± 4.34% | 65.20 ± 1.80% | **+3.08pp** |
| Train Accuracy | 70.58 ± 3.85% | 80.50 ± 0.52% | +9.92pp |
| Sparsity | 0.010 ± 0.023% | 0.003 ± 0.008% | −0.007pp |
| Parameters | 1,264 | 4,832 | +3,568 (+282%) |

**Key observations:**
1. **Diminishing returns:** A 3.8× parameter increase yields only a 3.1pp test-accuracy gain. The d=8 architecture is remarkably parameter-efficient.
2. **Lower variance at d=16:** Std drops from 4.34% to 1.80%, suggesting the wider bottleneck stabilizes training across seeds.
3. **Larger train-test gap at d=16:** The d=16 model overfits more (train 80.5% vs test 65.2%, gap = 15.3pp) compared to d=8 (train 70.6% vs test 62.1%, gap = 8.5pp). The extra capacity is not fully generalizing.
4. **Verdict:** The bottleneck is a minor factor. The **objective alignment** (JEPA vs reconstruction) is the dominant driver of performance.

---

## Objective Ranking

| Rank | Objective | Test Accuracy | Δ vs Untrained | RM Bar | Assessment |
|:---|:---|---:|---:|:---|:---|
| 1 | **JEPA** | **62.12%** | **+15.96pp** | **PASS** | Clear winner; strong, significant, generalizes |
| 2 | Contrastive | 50.64% | +4.48pp | FAIL | Marginal improvement; high variance across seeds |
| 3 | SFA | 50.56% | +4.40pp | FAIL | Similar to contrastive; one strong seed (61.2%) pulls mean up |
| 4 | Hebbian | 23.96% | −22.20pp | FAIL | Catastrophic failure; objective is misaligned with task |

**Note:** The gap between JEPA and the next-best objective is **11.5pp** — a large margin that underscores the importance of the spatial-prediction-in-latent-space formulation.

---

## Previous Results Comparison (Iter 002)

| Method | Test Accuracy | vs JEPA-d8 | vs JEPA-d16 |
|:---|---:|---:|---:|
| **JEPA-d8 (this work)** | **62.12%** | — | −3.1pp |
| **JEPA-d16 (this work)** | **65.20%** | +3.1pp | — |
| Untrained-P1-B (iter 002) | 48.44% | −13.7pp | −16.8pp |
| Simultaneous reconstruction (iter 002) | 41.52% | −20.6pp | −23.7pp |
| Predictive coding (iter 002) | 38.16% | −24.0pp | −27.0pp |
| Strong L1 (iter 002) | 37.12% | −25.0pp | −28.1pp |
| k-WTA (iter 002) | 35.72% | −26.4pp | −29.5pp |
| Reconstruction P1-B (iter 002) | 33.52% | −28.6pp | −31.7pp |

**Key insight:** JEPA-d8 outperforms **every prior method** by at least 13.7pp, and outperforms the best prior trained method (simultaneous reconstruction) by **20.6pp**. This confirms that the failure of Phase 1 was **not** architecture or capacity, but **objective misalignment**: reconstruction objectives destroy the discriminative structure that JEPA preserves.

---

## Recommendation for Phase 2

**Use JEPA as the temporal integration objective.**

Rationale:
1. **Strongest spatial performance:** JEPA is the only objective that both (a) significantly exceeds the untrained baseline and (b) clears the 5pp success bar.
2. **Temporal-unification path cleared:** Criterion 5 is not falsified — JEPA succeeds spatially, so applying the same objective temporally is scientifically justified.
3. **d=8 is sufficient:** The bottleneck refutation means we do not need to increase dimensionality for Phase 2. The d=8 architecture (1,264 params) is parameter-efficient and generalizes well.
4. **Lower variance at d=16 is tempting but not decisive:** If Phase 2 training proves unstable, d=16 can be revisited, but d=8 should be the default.

**Proposed Phase 2 design:**
- Architecture: P1-B (3-layer, kernel-3, stride-1, d=8, cross-layer weight sharing)
- Objective: JEPA loss applied along the **time axis** (predict next timestep's latent from current)
- Same VICReg collapse prevention (variance + covariance penalties)
- Evaluation: Linear probe on 5-category structured dataset after temporal training

---

## Key Insight: What This Phase Teaches Us About the HSUN Architecture

1. **The architecture is not the bottleneck.** The same P1-B architecture that achieved 33.5% with reconstruction now achieves 62.1% with JEPA — an 85% relative improvement. The architecture has always had sufficient representational capacity; it was the **training signal** that was broken.

2. **Latent-space prediction >> pixel-space reconstruction.** Reconstruction forces the encoder to preserve every input detail, including noise and category-irrelevant structure. JEPA predicts in latent space, allowing the encoder to discard noise and compress into category-discriminative features.

3. **Spatial structure is learnable from local objectives.** The JEPA task (predict adjacent spatial positions) requires understanding blob shape, periodicity, and noise patterns — exactly the structure that distinguishes the 5 categories. The encoder learns this **without any labels**.

4. **Not all local objectives are equal.** Contrastive and SFA show promise but are noisy and inconsistent. Hebbian learning fails completely. The specific formulation of JEPA (bidirectional prediction + VICReg collapse prevention) appears to be the critical combination.

5. **Cross-layer weight sharing works.** The P1-B architecture with shared weights across layers achieves strong performance, validating the HSUN design principle of weight sharing as a strong prior for hierarchical structure.

---

## Raw Data

See `phase_1/objectives_results.csv` for per-seed raw values.

| Config | Seed 42 | Seed 43 | Seed 44 | Seed 45 | Seed 46 |
|:---|---:|---:|---:|---:|---:|
| P1-B-JEPA-d8 | 65.8% | 59.4% | 64.8% | 64.8% | 55.8% |
| P1-B-Contrastive-d8 | 55.6% | 53.2% | 45.4% | 47.0% | 52.0% |
| P1-B-SFA-d8 | 43.4% | 40.6% | 61.2% | 55.6% | 52.0% |
| P1-B-Hebbian-d8 | 27.8% | 20.0% | 23.4% | 23.0% | 25.6% |
| P1-B-JEPA-d16 | 67.8% | 63.6% | 65.4% | 63.4% | 65.8% |
| Untrained-d8 | 44.0% | 50.4% | 50.0% | 41.8% | 44.6% |
| Untrained-d16 | 54.8% | 50.0% | 61.2% | 46.4% | 60.6% |

---

*Report generated automatically from phase_1/objectives_results.csv*
