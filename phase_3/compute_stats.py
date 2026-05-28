import numpy as np
from scipy import stats
import sys

# All conditions by seed (matched by seed order 42,43,44,45,46)
A = np.array([0.4425, 0.4375, 0.4250, 0.4400, 0.4550])  # P3-C, VICReg=False, pooled
B = np.array([0.5350, 0.5725, 0.5075, 0.5275, 0.5325])  # P3-C, VICReg=False, spatial_pooled_then_flat
C = np.array([0.4900, 0.5300, 0.4775, 0.4325, 0.5275])  # P3-C, VICReg=True, pooled
D = np.array([0.5800, 0.6825, 0.5950, 0.5700, 0.6500])  # P3-C, VICReg=True, spatial_pooled_then_flat
E = np.array([0.4625, 0.3850, 0.4200, 0.3800, 0.4225])  # Untrained, pooled
F = np.array([0.5650, 0.5425, 0.4800, 0.4900, 0.5275])  # Untrained, spatial_pooled_then_flat

def paired_analysis(name, x, y):
    diffs = x - y
    n = len(diffs)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    t_stat, p_val = stats.ttest_rel(x, y)
    d_cohen = mean_diff / std_diff if std_diff > 0 else 0.0
    gain_pp = mean_diff * 100
    print(f'=== {name} ===', flush=True)
    print(f'  X = {x}', flush=True)
    print(f'  Y = {y}', flush=True)
    print(f'  Diffs = {diffs}', flush=True)
    print(f'  Mean diff = {mean_diff:.6f}', flush=True)
    print(f'  Std diff = {std_diff:.6f}', flush=True)
    print(f'  Gain (pp) = {gain_pp:.2f}', flush=True)
    print(f'  t({n-1}) = {t_stat:.4f}', flush=True)
    print(f'  p = {p_val:.6f}', flush=True)
    print(f"  Cohen's d (dz) = {d_cohen:.4f}", flush=True)
    print(f'  X mean = {np.mean(x):.4f}, Y mean = {np.mean(y):.4f}', flush=True)
    print(flush=True)
    return mean_diff, gain_pp, t_stat, p_val, d_cohen

paired_analysis('D vs F (spatial_pooled_then_flat: VICReg=True vs Untrained)', D, F)
paired_analysis('C vs E (pooled: VICReg=True vs Untrained)', C, E)
paired_analysis('B vs F (spatial_pooled_then_flat: VICReg=False vs Untrained)', B, F)
paired_analysis('C vs A (pooled: VICReg=True vs VICReg=False)', C, A)

# Also compute pooled_std stats
print('\n=== Pooled Std Stats ===', flush=True)
std_no = np.array([0.07274529323071374, 0.07039510208025884, 0.08839668914997581, 0.060122353015351626, 0.06931246457443763])
std_vi = np.array([0.12100194626454026, 0.13158482887957126, 0.14261169108926033, 0.13203897778437595, 0.12353603861439841])
print(f'No VICReg pooled_std: mean={np.mean(std_no):.6f}, std={np.std(std_no, ddof=1):.6f}', flush=True)
print(f'VICReg pooled_std: mean={np.mean(std_vi):.6f}, std={np.std(std_vi, ddof=1):.6f}', flush=True)
print(f'Relative increase: {(np.mean(std_vi)-np.mean(std_no))/np.mean(std_no)*100:.2f}%', flush=True)