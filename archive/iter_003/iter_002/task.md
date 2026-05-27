## Task: Analyze Phase 1 v2 Results and Create Report

### Context
The Phase 1 v2 experiments have completed. Results are in `phase_1/objectives_results.csv`. 
Pre-registered hypothesis and falsification criteria are in `src/pre_registration.md`.

### What to Do

1. **Read the results CSV** at `phase_1/objectives_results.csv`
2. **Read the pre-registration** at `src/pre_registration.md`
3. **Read the previous Phase 1 results** at `phase_1/results.csv` and `phase_1/diagnostic_results.csv` for comparison context
4. **Compute statistics** for each configuration:
   - Mean ± std test accuracy across 5 seeds
   - Mean ± std train accuracy across 5 seeds
   - Mean ± std sparsity across 5 seeds
   - Compute paired t-tests (or Wilcoxon signed-rank if sample is too small) comparing each trained config vs the corresponding untrained baseline

5. **Evaluate each pre-registered falsification criterion:**

   Criterion 1: JEPA hypothesis FALSIFIED if: mean JEPA accuracy (5 seeds) < 50% at d=8
   - Report: FALSIFIED or NOT FALSIFIED, with the actual mean

   Criterion 2: General local-objective hypothesis FALSIFIED if: ALL four objectives achieve mean accuracy < 48.4% at d=8
   - Report: FALSIFIED or NOT FALSIFIED, with each objective's mean

   Criterion 3: d=8 bottleneck hypothesis SUPPORTED if: JEPA-d16 mean > JEPA-d8 mean + 10pp
   - Report: SUPPORTED or NOT SUPPORTED, with the actual gap

   Criterion 4: d=8 bottleneck hypothesis REFUTED if: JEPA-d16 mean ≤ JEPA-d8 mean + 5pp
   - Report: REFUTED or NOT REFUTED, with the actual gap

   Criterion 5: Temporal-unification claim FALSIFIED if: JEPA fails spatially (<50%)
   - Report: FALSIFIED or NOT FALSIFIED

   Additional Research Manager criterion: Any trained method is only successful if it exceeds its corresponding untrained baseline by ≥5pp
   - Report for each objective: whether it meets this bar

6. **Create `phase_1/objectives_report.md`** with:
   - Executive summary (2-3 sentences)
   - Results table (all 7 configs with mean±std accuracy and sparsity)
   - Comparison vs untrained baseline (with statistical significance)
   - Evaluation of each pre-registered criterion (PASS/FAIL with numbers)
   - d=8 vs d=16 analysis
   - Objective ranking
   - Previous results comparison (vs reconstruction at 33.5%, predictive coding at 38.2%, simultaneous reconstruction at 41.5%)
   - Recommendation for Phase 2 (which objective to use for temporal integration)
   - Key insight: what this phase teaches us about the HSUN architecture

7. **Update `src/pre_registration.md`** by APPENDING (not replacing) a section at the bottom:
   ```
   ## Phase 1 v2 Results (Iteration 3)
   [Date]
   [Summary of findings against each criterion]
   [Final verdict on each hypothesis]
   ```

### Previous Baseline Numbers (from iter_002, for comparison)
- Untrained P1-B d=8 (old): 48.4% ± (from iter_002)
- Reconstruction P1-B d=8: 33.5% ± (from iter_002)
- Simultaneous reconstruction: 41.5% ± (from iter_002)
- Predictive coding: 38.2% ± (from iter_002)
- k-WTA: 35.7% ± (from iter_002)
- Strong L1: 37.1% ± (from iter_002)

### Output
- phase_1/objectives_report.md (full report)
- Updated src/pre_registration.md (with results section appended)
