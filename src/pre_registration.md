# RDF Scientific Pre-Registration

*   **Iteration:** 007
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
Phase 4 (Training Objective Comparison) on the P3-C spatiotemporal benchmark:
(H1) JEPA + pooled VICReg achieves test accuracy ≥ 55% (reproducing the 61.55%
     reference from iter_006 with relaxed floor).
(H2) No other objective (with OR without pooled VICReg) exceeds JEPA + pooled
     VICReg by ≥ 3 percentage points.
(H3) For most objectives, pooled VICReg improves accuracy over the VICReg-free
     version. Reconstruction may violate H3 (it natively resists collapse).

## 2. Falsification Criterion
F1: JEPA + pooled VICReg achieves < 55% test accuracy (implementation broken).
F2: Any other objective exceeds JEPA + pooled VICReg by ≥ 3pp (JEPA not best).
F3: For any objective X (other than Reconstruction), accuracy(X without VICReg)
    ≥ accuracy(X with VICReg) — pooled VICReg does not generalise. F3 triggering
    for Reconstruction is expected and explicitly allowed.

## 3. Proposed Method
Step 1: Fix src/run_phase4.py to address memory and timeout failures:
  a) Replace multiprocessing Pool with sequential execution in main process
  b) Add batched feature extraction for evaluation (process in chunks of 64
     instead of full 800-sample forward pass — avoids ~1 GB memory spike)
  c) Remove the redundant final_fwd forward pass on full training set;
     use metrics["pooled_std"] from last epoch instead
  d) Skip training loop for untrained baseline (just do evaluation)
  e) Add gc.collect() between runs to free memory
  f) Add --objectives CLI argument to run subset of objectives
  g) Change results CSV to append mode (support split runs)

Step 2: Run experiments in two sequential sub-agents to stay within timeout:
  Sub-agent 7.2 (retry): Fix code + run JEPA (10) + SFA (10) + untrained (5) = 25 runs
  Sub-agent 7.3: Run Hebbian (10) + Reconstruction (10) = 20 runs, append to CSV

Step 3: Sub-agent 7.4 loads all 45 results from phase_4/phase4_results.csv,
  runs statistical analysis (paired t-tests, Cohen's d), evaluates F1/F2/F3
  falsification criteria, and generates phase_4/REPORT.md.

Step 4: Update current_state.md with Phase 4 results and recommendation for
  default training objective going forward.

Files to modify: src/run_phase4.py (major refactor), src/pre_registration.md (update iteration number)
Files to create: phase_4/phase4_results.csv, phase_4/REPORT.md
Files to update: current_state.md

Experimental config (unchanged from pre-registration):
- P3-C architecture, d=16, d_out=16, 1,600 params
- 4 objectives × 2 VICReg conditions × 5 seeds = 40 trained + 5 untrained = 45 runs
- 30 epochs, batch=64, lr=1e-3, alpha=0.5
- Readout: spatial_pooled_then_flat (416 dims)
- Seeds: [42, 43, 44, 45, 46]

---

## 4. Actual Results (post-experiment)

**All 45 runs completed successfully.** Full results: `phase_4/phase4_results.csv`. Detailed statistical report: `phase_4/REPORT.md`.

### 4.1 Test Accuracy Summary

| Objective | VICReg | Mean ± Std (%) |
|-----------|--------|----------------|
| JEPA | No | 53.50 ± 2.36 |
| JEPA | **Yes** | 61.55 ± 4.86 |
| SFA | No | 25.00 ± 0.00 |
| SFA | Yes | 82.15 ± 3.02 |
| Hebbian | No | 43.90 ± 6.33 |
| Hebbian | Yes | 48.55 ± 6.83 |
| Reconstruction | No | 49.55 ± 7.79 |
| Reconstruction | **Yes** | 83.00 ± 2.27 |
| Untrained | N/A | 52.10 ± 3.56 |

### 4.2 Hypothesis Evaluation

| Hypothesis | Prediction | Actual | Outcome |
|------------|------------|--------|---------|
| H1: JEPA+VICReg ≥ 55% | ≥ 55% | 61.55% | **Supported** |
| H2: No other objective exceeds JEPA+VICReg by ≥ 3pp | No other ≥ 64.55% | SFA+VICReg=82.15%, Recon+VICReg=83.00% | **Refuted** |
| H3: VICReg improves most objectives (Reconstruction may be exception) | VICReg helps most | VICReg helps ALL objectives, including Reconstruction (+33.45pp) | **Partially refuted** (Reconstruction also benefited enormously) |

### 4.3 Falsification Criteria

| Criterion | Result | Triggered? |
|-----------|--------|------------|
| F1: JEPA+VICReg < 55% | 61.55% | **No** |
| F2: Another objective exceeds JEPA+VICReg by ≥ 3pp | SFA+VICReg +20.60pp, Recon+VICReg +21.45pp | **Yes** |
| F3: VICReg does not help (non-Recon) | All objective means increase with VICReg; paired t-test (JEPA, SFA) significant | **No** |

### 4.4 Key Findings

1. **VICReg is the dominant factor**: Pooled VICReg contributes +57.15pp (SFA) and +33.45pp (Reconstruction) — far larger than any training objective effect.
2. **SFA without VICReg collapses to chance** (25.0% ± 0.00%), confirming theoretical predictions about representation collapse.
3. **Reconstruction + VICReg is the best overall** (83.00%), but the Research Manager's prediction that VICReg would NOT help reconstruction was wrong — the gap is +33.45pp (p < 0.001).
4. **Hebbian benefits least from VICReg** (+4.65pp, not statistically significant, p = 0.183), possibly because it already maximises variance.
5. **JEPA without VICReg is barely above untrained** (+1.40pp, p = 0.317), suggesting local VICReg alone is insufficient.

### 4.5 Recommendation

**Reconstruction + pooled VICReg** is recommended as the default training objective for future iterations (83.00% accuracy, lowest variance). SFA + VICReg (82.15%) is a close second.

### 4.6 Caveats

- All objectives used a shared hyperparameter envelope optimized for JEPA; SFA and Hebbian may outperform with dedicated tuning.
- Architecture is small (1,600 params); scaling to larger models may change the relative ranking.
- Results are on the P3-C benchmark only; generalisation to other spatiotemporal tasks is untested.

---
*Created automatically by the RDF Orchestrator prior to iteration execution.*
