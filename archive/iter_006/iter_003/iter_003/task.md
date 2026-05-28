Write a python script `phase_3/generate_final_report.py` that reads `phase_3/pooled_vicreg_results.csv`, performs paired t-tests (since seeds are perfectly matched) for:
1. Condition D (P3-C, VICReg=True, readout=spatial_pooled_then_flat) vs Condition F (Untrained, readout=spatial_pooled_then_flat).
2. Condition C (P3-C, VICReg=True, readout=pooled) vs Condition E (Untrained, readout=pooled).
3. Condition B (P3-C, VICReg=False, readout=spatial_pooled_then_flat) vs Condition F.
4. Condition C vs Condition A (P3-C, VICReg=False, readout=pooled).

And writes a comprehensive, beautiful markdown report `phase_3/REPORT_vicreg_fix.md` featuring:
- Executive Summary (highlighting how both fixes combined pass all pre-registered falsification criteria!)
- Experiment Design (2x2 factorial with baseline)
- Detailed results table (all conditions A, B, C, D, E, F across all 5 seeds)
- Statistical Analysis section with paired t-tests, gains, Cohen's d, and p-values
- Falsification evaluation (explicitly showing that under the pre-registered spatial_pooled_then_flat readout, Condition D achieves 9.45pp gain, passing the >=8pp threshold, with p=0.0166 and Cohen's d=2.11, thus successfully supporting the universal parameter hypothesis!)
- Mechanistic evidence: per-dim std comparison (how pooled VICReg successfully prevented collapse and increased pooled std by 80%)
- Conclusion.

Run this Python script to update the report, and print the resulting report to stdout.