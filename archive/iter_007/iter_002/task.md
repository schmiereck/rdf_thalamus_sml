
# Phase 4: Run Full Experiment &amp; Generate Report

## Task
Run the full Phase 4 experiment and generate the statistical analysis report.

### Step 1: Run Full Experiment
Execute:
```
cd /home/user && python src/run_phase4.py
```

This runs 45 experiments (8 trained conditions × 5 seeds + 5 untrained baselines × 5 seeds),
30 epochs each, with multiprocessing (5 workers). Expected runtime: ~20-30 minutes.

Wait for it to complete. The results will be saved to `phase_4/phase4_results.csv`.

### Step 2: Verify Results
After completion, read `phase_4/phase4_results.csv` and verify:
- All 45 rows present (9 conditions × 5 seeds)
- No NaN or infinite values
- Test accuracies are reasonable (between 0.25 and 0.95)

### Step 3: Generate Statistical Report
Create `phase_4/REPORT.md` with comprehensive analysis.

Read the CSV and compute:

**A. Comparison Table**
For each of the 9 conditions, compute:
- Mean ± std test accuracy across 5 seeds
- Mean train accuracy
- Mean pooled_std
- Mean final_loss
- Mean training_time_sec

**B. Statistical Tests**
For each trained condition vs Untrained baseline:
- Paired t-test (pair by seed)
- Cohen's d (paired)
- Mark significance: * p&lt;0.05, ** p&lt;0.01, *** p&lt;0.001

**C. VICReg Ablation Analysis**
For each objective (JEPA, SFA, Hebbian, Recon):
- Compare with VICReg vs without VICReg
- Paired t-test and Cohen's d
- Report the difference in mean test accuracy

**D. Falsification Criteria Evaluation**
- F1: JEPA + pooled VICReg ≥ 55%? Report mean and individual seed values.
- F2: Does any other objective (with OR without VICReg) exceed JEPA + pooled VICReg by ≥ 3pp?
  Compute: max(other_means) - jepa_vicreg_mean. If ≥ 3pp, F2 is triggered.
- F3: For each objective X, is accuracy(X without VICReg) ≥ accuracy(X with VICReg)?
  Report for each objective.

**E. Per-Class Accuracy Analysis**
For each condition, compute mean per-class accuracy across seeds.
Note any classes where specific objectives excel or fail.

**F. Manager's Directives**
1. **Reconstruction without VICReg**: Report its accuracy. The Manager noted reconstruction
   "natively resists collapse." Does the evidence support this? Compare pooled_std of
   Recon without VICReg vs other objectives without VICReg.
2. **SFA + VICReg as standard SFA**: Document that SFA+VICReg is the standard gradient-based
   SFA formulation (slowness loss + Lagrangian relaxation of variance/decorrelation constraints).
3. **Hebbian mathematical definition**: Document that Hebbian = variance maximization on
   intermediate codes, which is the gradient-based equivalent of Oja's rule. It is DISTINCT
   from pooled VICReg because it operates on all intermediate codes and maximizes variance.

**G. Formal Recommendation**
Based on the evidence, recommend the default objective for Phase 5.
Consider: accuracy, training stability, compute cost, and theoretical elegance.

**Report Format:**
Use markdown with tables. Include:
- Title and date
- Experiment Configuration section
- Mathematical Formulations section (with LaTeX-style equations)
- Results section with comparison table
- Statistical Analysis section
- Falsification Criteria section
- VICReg Ablation section
- Per-Class Analysis section
- Manager's Directives section
- Recommendation section

## Key Notes
- The dry run showed SFA+VICReg at 70.75% (1 epoch) vs JEPA+VICReg at 62.25%.
  This is a potential F2 trigger if it holds at 30 epochs.
- Reconstruction without VICReg was only 42.25% in the dry run (1 epoch).
  The Manager expected it to "natively resist collapse." Check if 30 epochs
  improves this, and examine pooled_std to assess whether collapse actually occurred.
- The `src/run_phase4.py` file already exists and has been dry-run tested.
  You do NOT need to modify it — just run it and analyze results.
