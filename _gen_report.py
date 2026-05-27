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