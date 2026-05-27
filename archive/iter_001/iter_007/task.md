## Task: Fix Unicode encoding issue in run_phase0.py and regenerate the report

The Phase 0 experiment completed all 25 runs successfully and saved results to `phase_0/results.csv`. However, the Markdown report generation in `src/run_phase0.py` failed due to a Unicode encoding error on Windows (cp1252 codec can't encode the Greek letter ρ).

### Step 1: Fix `src/run_phase0.py`

Make TWO changes:

1. Replace ALL instances of the Greek letter ρ in the Python string literals within `generate_report()` with ASCII "rho". Search for `ρ` and `\\u03c1` in the file and replace with `rho`.

2. Change `open(filepath, "w")` to `open(filepath, "w", encoding="utf-8")` in the `generate_report` function AND the `write_csv` function. This is a defense-in-depth measure.

### Step 2: Regenerate the report

After fixing the code, run just the report generation. You can either:
- Run `python src/run_phase0.py` again (it will re-run all experiments AND generate the report), or
- Better: write a short script that reads the CSV and generates the report without re-running experiments

I recommend writing a short regeneration script and running it:
```python
import sys
sys.path.insert(0, 'src')
from run_phase0 import generate_report
import csv

results = []
with open('phase_0/results.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        r = {}
        r['encoder_id'] = row['encoder_id']
        r['seed'] = int(row['seed'])
        r['spearman_rho'] = float(row['spearman_rho']) if row['spearman_rho'] != 'nan' else float('nan')
        r['p_value'] = float(row['p_value']) if row['p_value'] != 'nan' else float('nan')
        r['sparsity'] = float(row['sparsity'])
        r['train_time_sec'] = float(row['train_time_sec'])
        r['final_loss'] = float(row['final_loss']) if row['final_loss'] != '' else float('nan')
        r['n_codes'] = int(row['n_codes'])
        r['dim_out'] = int(row['dim_out'])
        r['status'] = row['status']
        results.append(r)

generate_report(results, 'phase_0/REPORT.md')
print("Report generated successfully!")
```

### Step 3: Verify the report

Read and display the contents of `phase_0/REPORT.md` to verify it's complete and correct. Check that:
- P0-A is marked as "Exempt (negative control)"
- All rho values are correctly reported
- Success criteria are evaluated correctly
- The report contains the pass/fail status for each encoder
- No Greek letters remain that could cause issues
