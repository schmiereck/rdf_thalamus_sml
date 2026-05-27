import csv
import numpy as np

results = {}
with open('phase_1/results.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        config = row['config']
        if config not in results:
            results[config] = {'test_acc': [], 'sparsity': [], 'recon_mse_l0': [], 'n_params': [], 'train_acc': []}
        results[config]['test_acc'].append(float(row['test_accuracy']))
        results[config]['sparsity'].append(float(row['sparsity']))
        results[config]['recon_mse_l0'].append(float(row['recon_mse_l0']))
        results[config]['n_params'].append(int(row['n_params']))
        results[config]['train_acc'].append(float(row['train_accuracy']))

for c in ['P1-A','P1-B','P1-C','P1-D','P1-E','Untrained-P1-B']:
    r = results[c]
    print(f"{c}: acc={np.mean(r['test_acc']):.4f}+/-{np.std(r['test_acc']):.4f} spar={np.mean(r['sparsity']):.4f}+/-{np.std(r['sparsity']):.4f} l0={np.mean(r['recon_mse_l0']):.2e} train_acc={np.mean(r['train_acc']):.4f} n={r['n_params'][0]}")

pb = np.mean(results['P1-B']['test_acc'])
pc = np.mean(results['P1-C']['test_acc'])
pd = np.mean(results['P1-D']['test_acc'])
pe = np.mean(results['P1-E']['test_acc'])
pa = np.mean(results['P1-A']['test_acc'])
ut = np.mean(results['Untrained-P1-B']['test_acc'])
pb_sp = np.mean(results['P1-B']['sparsity'])
pb_sp_std = np.std(results['P1-B']['sparsity'])

print(f"\n=== Criteria ===")
print(f"P1B >= 80%? mean={pb:.4f} -> {'PASS' if pb>=0.80 else 'FAIL'} (chance=0.20)")
print(f"P1B vs P1C gap: {(pc-pb)*100:.2f}pp")
print(f"P1B vs Untrained: {(pb-ut)*100:.1f}pp -> {'PASS' if (pb-ut)>=0.15 else 'FAIL'}")
print(f"P1B spar >= 50%? mean={pb_sp:.4f}+/-{pb_sp_std:.4f} -> {'PASS' if pb_sp>=0.50 else 'FAIL'}")
print(f"P1D-B: {(pd-pb)*100:.2f}pp  P1E-B: {(pe-pb)*100:.2f}pp  P1A-B: {(pa-pb)*100:.2f}pp")
