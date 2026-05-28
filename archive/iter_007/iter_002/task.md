
# Phase 4: Statistical Analysis + Report Generation

## Context
All 45 Phase 4 experiments have completed. Results are in `phase_4/phase4_results.csv`. The pre-registration is in `src/pre_registration.md`. Read both files first.

## Key Results Summary (from the experiment run)
- JEPA (no VICReg): 53.50% ± 2.36%
- JEPA + VICReg: 61.55% ± 4.86%
- SFA (no VICReg): 25.00% ± 0.00% (complete collapse)
- SFA + VICReg: 82.15% ± 3.02%
- Hebbian (no VICReg): 43.90% ± 6.33%
- Hebbian + VICReg: 48.55% ± 6.83%
- Reconstruction (no VICReg): 49.55% ± 7.79%
- Reconstruction + VICReg: 83.00% ± 2.27%
- Untrained: 52.10% ± 3.56%

## Task
Create a comprehensive statistical analysis and write `phase_4/REPORT.md`. The report must:

### 1. Schema Validation
Assert that the CSV has exactly 45 rows: 4 objectives × 2 VICReg conditions × 5 seeds + 5 untrained = 45. Verify each (objective, seed, use_pooled_vicreg) combination exists exactly once.

### 2. Statistical Analysis
For each condition vs untrained:
- Paired t-test (paired by seed) on test accuracy
- Cohen's d effect size
- Report p-value, gain in percentage points

### 3. Falsification Criteria Evaluation (per pre-registration)
**F1**: JEPA + VICReg < 55% → NOT triggered (61.55%)
**F2**: Any other objective exceeds JEPA + VICReg by ≥ 3pp → TRIGGERED (SFA+VICReg=82.15%, Recon+VICReg=83.00%)
**F3**: For any objective X, accuracy(X without VICReg) ≥ accuracy(X with VICReg) → Check with paired t-tests per the Research Manager's directive. The Manager demanded that F3 requires the gap to be positive AND either statistically significant (p < 0.05 via paired t-test) or exceed 1.5× the pooled standard error. Apply this rigorous version of F3.

### 4. VICReg Ablation Analysis
For each objective, compare with vs without pooled VICReg:
- Paired t-test (paired by seed) on test accuracy
- Effect size
- For Reconstruction specifically: the Manager predicted that VICReg would NOT help (reconstruction natively resists collapse). This prediction was WRONG — Recon+VICReg is 83% vs 49.55% without. Document this.

### 5. Parameter Hygiene Caveat
Per the Research Manager's directive, include this critical caveat:
"Under the shared spatiotemporal hyperparameter envelope optimized for JEPA (lr=1e-3, 30 epochs, batch=64), method X does not yield a competitive representation. This may reflect a failure of the shared envelope rather than a fundamental limitation of the learning rule itself."

### 6. Key Observations to Document
- SFA without VICReg completely collapses to 25% (chance), confirming the theoretical prediction
- SFA + VICReg at 82.15% is the standard gradient-based SFA formulation (slowness + variance + decorrelation)
- Reconstruction + VICReg at 83.00% is the best overall
- The massive gap between VICReg and non-VICReg versions (30+ pp for SFA and Reconstruction) suggests pooled VICReg is the dominant factor, not the training objective
- Hebbian benefits least from pooled VICReg (+4.65pp), possibly because it already maximises variance at all layers
- JEPA without pooled VICReg (53.5%) is barely above untrained (52.1%), suggesting local VICReg alone is insufficient

### 7. Write the Report
Write `phase_4/REPORT.md` with:
- Experiment configuration
- Mathematical formulations of each objective
- Results table with mean ± std test accuracy
- VICReg ablation analysis table
- Statistical tests table (paired t-tests vs untrained, paired t-tests with/without VICReg)
- Falsification criteria evaluation table
- Per-class accuracy table
- Training stability and compute cost
- Manager's directives addressed
- Recommendation for default training objective

### 8. Update pre_registration.md
Update `src/pre_registration.md` to add the actual results section at the bottom documenting what was found vs what was hypothesised.

Use Python/scipy for statistical analysis. Write the analysis script, run it, and produce the report.
