## Task: Fix two specific issues in src/run_phase0.py, then re-run to generate the report

### Fix 1: Replace ALL Greek letter rho with ASCII "rho"

In `src/run_phase0.py`, there are multiple instances of the Unicode character ρ (Greek small letter rho, U+03C1) in string literals within the `generate_report` function. These cause a UnicodeEncodeError on Windows with cp1252 encoding.

Use this approach to fix it:
```bash
cd /project/root && python -c "
content = open('src/run_phase0.py', 'r', encoding='utf-8').read()
content = content.replace('\u03c1', 'rho')
content = content.replace('\u03A1', 'Rho')
open('src/run_phase0.py', 'w', encoding='utf-8').write(content)
print('Replaced all Greek rho with ASCII rho')
"
```

### Fix 2: Add encoding='utf-8' to open() calls

In `src/run_phase0.py`, change:
- `open(filepath, "w")` to `open(filepath, "w", encoding="utf-8")` (in `generate_report` function)
- `open(filepath, "w", newline="")` to `open(filepath, "w", newline="", encoding="utf-8")` (in `write_csv` function)

Use this approach:
```bash
cd /project/root && python -c "
content = open('src/run_phase0.py', 'r', encoding='utf-8').read()
content = content.replace('open(filepath, \"w\")', 'open(filepath, \"w\", encoding=\"utf-8\")')
content = content.replace('open(filepath, \"w\", newline=\"\")', 'open(filepath, \"w\", newline=\"\", encoding=\"utf-8\")')
open('src/run_phase0.py', 'w', encoding='utf-8').write(content)
print('Added utf-8 encoding to file open calls')
"
```

### Step 3: Regenerate just the report (without re-running experiments)

Since the experiment already ran and `phase_0/results.csv` exists, write and run a small script that loads the CSV and calls generate_report:

```bash
cd /project/root && python -c "
import sys, os
sys.path.insert(0, 'src')
import csv
import numpy as np
from run_phase0 import generate_report

results = []
with open('phase_0/results.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        r = {}
        r['encoder_id'] = row['encoder_id']
        r['seed'] = int(row['seed'])
        r['spearman_rho'] = float(row['spearman_rho']) if row['spearman_rho'] not in ('nan', '') else float('nan')
        r['p_value'] = float(row['p_value']) if row['p_value'] not in ('nan', '') else float('nan')
        r['sparsity'] = float(row['sparsity'])
        r['train_time_sec'] = float(row['train_time_sec'])
        r['final_loss'] = float(row['final_loss']) if row['final_loss'] not in ('nan', '') else float('nan')
        r['n_codes'] = int(row['n_codes'])
        r['dim_out'] = int(row['dim_out'])
        r['status'] = row['status']
        results.append(r)

generate_report(results, 'phase_0/REPORT.md')
print('Report generated successfully!')
"
```

### Step 4: Display the report

Print the contents of `phase_0/REPORT.md`.

If Step 3 fails for any reason, try running the full experiment again:
```bash
cd /project/root && python src/run_phase0.py
```
