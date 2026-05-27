
# Monitor Phase 3 Experiment Run and Verify Results

The Phase 3 experiment run was launched in the background. Your job is to:

1. Wait for the background run to complete by checking the log file at `src/phase3_run.log` periodically.
2. Once the run completes, verify the results file at `phase_3/phase3_results.csv` has all 20 rows (4 variants × 5 seeds).
3. Read the results and print a summary.
4. If the background process has not finished yet, wait up to 30 minutes and keep checking.
5. Also check `phase_3/shortcut_baselines.csv` for shortcut baseline results.

## How to Check

```bash
# Check if the process is still running
ps aux | grep run_phase3

# Check the log file
cat src/phase3_run.log

# Count rows in results CSV
wc -l phase_3/phase3_results.csv
```

## What to Look For

- All 4 variants (P3-A, P3-B, P3-C, Untrained) should have 5 seeds each
- Trained variants should significantly outperform the Untrained baseline (this was the bug symptom)
- Shortcut baselines should be ≤50% (near chance for 4-class)
- JEPA losses should converge to reasonable values (much lower than 20-25)

## If the Run Hasn't Started or Failed

If the background process isn't running and no results exist, run the experiment yourself:
```bash
cd src && python run_phase3.py
```

This will take approximately 20-40 minutes for 20 runs.

## Output

Print the complete summary table of results. Specifically report:
- Mean ± std test accuracy for each variant across 5 seeds
- Per-class accuracy for each variant
- Shortcut baseline results
- Whether the Untrained baseline is now properly below trained variants
