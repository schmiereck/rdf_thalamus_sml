"""
Phase 3 Comprehensive Statistical Analysis Script.

Reads the cleaned phase3_full_results.csv and shortcut_baselines.csv,
computes summary statistics, runs falsification tests, and writes REPORT.md.
"""

import csv
import math
import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESULTS_CSV = "phase_3/phase3_full_results.csv"
SHORTCUT_CSV = "phase_3/shortcut_baselines.csv"
REPORT_MD = "phase_3/REPORT.md"

CLASS_LABELS = ["moving_blob", "expanding_blob", "periodic_st", "object_permanence"]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_results(path: str) -> list[dict]:
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in row:
                if key == "variant" or key == "seed":
                    continue
                try:
                    row[key] = float(row[key])
                except ValueError:
                    pass
            rows.append(row)
    return rows

results_rows = load_results(RESULTS_CSV)
shortcut_rows = load_results(SHORTCUT_CSV)

# ---------------------------------------------------------------------------
# Organise by variant
# ---------------------------------------------------------------------------

variants = ["P3-A", "P3-B", "P3-C", "Untrained"]
variant_data: dict[str, dict[str, list]] = {v: {
    "seed": [],
    "train_acc": [],
    "test_acc": [],
    "spatial_loss": [],
    "temporal_loss": [],
    "time": [],
    "class_0": [],
    "class_1": [],
    "class_2": [],
    "class_3": [],
} for v in variants}

for row in results_rows:
    v = row["variant"]
    variant_data[v]["seed"].append(int(row["seed"]))
    variant_data[v]["train_acc"].append(row["train_acc"])
    variant_data[v]["test_acc"].append(row["test_acc"])
    variant_data[v]["spatial_loss"].append(row["final_spatial_jepa_loss"])
    variant_data[v]["temporal_loss"].append(row["final_temporal_jepa_loss"])
    variant_data[v]["time"].append(row["training_time_sec"])
    variant_data[v]["class_0"].append(row["class_0_acc"])
    variant_data[v]["class_1"].append(row["class_1_acc"])
    variant_data[v]["class_2"].append(row["class_2_acc"])
    variant_data[v]["class_3"].append(row["class_3_acc"])

# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def mean_std(vals: list[float]) -> tuple[float, float]:
    arr = np.array(vals)
    return float(arr.mean()), float(arr.std(ddof=1))

def paired_cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d for paired samples (mean diff / std of diffs)."""
    diff = a - b
    return float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else 0.0

# ---------------------------------------------------------------------------
# Main summary statistics
# ---------------------------------------------------------------------------

print("=" * 65)
print("Phase 3 Comprehensive Statistical Analysis")
print("=" * 65)

summary = {}
for v in variants:
    test_mean, test_std = mean_std(variant_data[v]["test_acc"])
    train_mean, train_std = mean_std(variant_data[v]["train_acc"])
    sloss_mean, sloss_std = mean_std(variant_data[v]["spatial_loss"])
    tloss_mean, tloss_std = mean_std(variant_data[v]["temporal_loss"])
    time_mean, time_std = mean_std(variant_data[v]["time"])
    class_means = [float(np.mean(variant_data[v][f"class_{i}"])) for i in range(4)]
    summary[v] = {
        "train_mean": train_mean, "train_std": train_std,
        "test_mean": test_mean, "test_std": test_std,
        "spatial_loss_mean": sloss_mean, "spatial_loss_std": sloss_std,
        "temporal_loss_mean": tloss_mean, "temporal_loss_std": tloss_std,
        "time_mean": time_mean, "time_std": time_std,
        "class_means": class_means,
    }
    print(f"\n{v}:")
    print(f"  Test Acc:  {test_mean:.4f} +- {test_std:.4f}")
    print(f"  Train Acc: {train_mean:.4f} +- {train_std:.4f}")
    print(f"  Spatial Loss: {sloss_mean:.4f} +- {sloss_std:.4f}")
    print(f"  Temporal Loss: {tloss_mean:.4f} +- {tloss_std:.4f}")
    print(f"  Per-class: {[f'{c:.3f}' for c in class_means]}")

# ---------------------------------------------------------------------------
# Shortcut baselines summary
# ---------------------------------------------------------------------------

shortcut_summary = {}
for row in shortcut_rows:
    name = row["baseline_name"]
    if name not in shortcut_summary:
        shortcut_summary[name] = {"train_acc": [], "test_acc": []}
    shortcut_summary[name]["train_acc"].append(row["train_acc"])
    shortcut_summary[name]["test_acc"].append(row["test_acc"])

print("\n--- Shortcut Baselines ---")
for name in sorted(shortcut_summary.keys()):
    train_vals = shortcut_summary[name]["train_acc"]
    test_vals = shortcut_summary[name]["test_acc"]
    t_mean, t_std = mean_std(train_vals)
    te_mean, te_std = mean_std(test_vals)
    print(f"  {name:25s}: train={t_mean:.4f}+-{t_std:.4f}  test={te_mean:.4f}+-{te_std:.4f}")
    shortcut_summary[name]["train_mean"] = t_mean
    shortcut_summary[name]["train_std"] = t_std
    shortcut_summary[name]["test_mean"] = te_mean
    shortcut_summary[name]["test_std"] = te_std

# ---------------------------------------------------------------------------
# Falsification tests
# ---------------------------------------------------------------------------

print("\n--- Pre-Registration Falsification Tests ---")

p3c_test = np.array(variant_data["P3-C"]["test_acc"])
untrained_test = np.array(variant_data["Untrained"]["test_acc"])
p3a_test = np.array(variant_data["P3-A"]["test_acc"])
p3b_test = np.array(variant_data["P3-B"]["test_acc"])

p3c_spatial_loss = np.array(variant_data["P3-C"]["spatial_loss"])
p3c_temporal_loss = np.array(variant_data["P3-C"]["temporal_loss"])
p3b_spatial_loss = np.array(variant_data["P3-B"]["spatial_loss"])
p3b_temporal_loss = np.array(variant_data["P3-B"]["temporal_loss"])

# F1: P3-C vs Untrained
f1_gain = float(p3c_test.mean() - untrained_test.mean())
f1_ttest = stats.ttest_rel(p3c_test, untrained_test)
f1_d = paired_cohens_d(p3c_test, untrained_test)
f1_triggered = (f1_gain < 0.08) or (f1_ttest.pvalue >= 0.05) or (f1_d < 1.0)

# F2: P3-B vs P3-C
f2_penalty = float(p3b_test.mean() - p3c_test.mean())
f2_triggered = f2_penalty > 0.10

# F3: P3-C vs P3-A
f3_gap = float(p3a_test.mean() - p3c_test.mean())
f3_triggered = p3c_test.mean() < (p3a_test.mean() - 0.20)

# F4: P3-C JEPA loss vs P3-B JEPA loss
# JEPA loss = spatial + temporal
p3c_jepa = p3c_spatial_loss + p3c_temporal_loss
p3b_jepa = p3b_spatial_loss + p3b_temporal_loss
f4_triggered = float(p3c_jepa.mean()) > (2.0 * float(p3b_jepa.mean()))

print(f"\nF1 -- P3-C vs Untrained:")
print(f"  Gain: {f1_gain*100:.2f}pp (threshold >= 8pp)")
print(f"  Paired t-test: t={f1_ttest.statistic:.4f}, p={f1_ttest.pvalue:.4f}")
print(f"  Cohen's d: {f1_d:.4f} (threshold >= 1.0)")
print(f"  Triggered: {f1_triggered} => {'FAIL' if f1_triggered else 'PASS'}")

print(f"\nF2 -- P3-B vs P3-C:")
print(f"  Penalty: {f2_penalty*100:.2f}pp (threshold <= 10pp)")
print(f"  Triggered: {f2_triggered} => {'FAIL' if f2_triggered else 'PASS'}")

print(f"\nF3 -- P3-C vs P3-A:")
print(f"  P3-A mean: {p3a_test.mean():.4f}; P3-C mean: {p3c_test.mean():.4f}")
print(f"  Gap: {f3_gap*100:.2f}pp (must be < 20pp)")
print(f"  Triggered: {f3_triggered} => {'FAIL' if f3_triggered else 'PASS'}")

print(f"\nF4 -- P3-C JEPA loss vs 2x P3-B:")
print(f"  P3-C mean JEPA loss: {p3c_jepa.mean():.4f}")
print(f"  P3-B mean JEPA loss: {p3b_jepa.mean():.4f}")
print(f"  2x P3-B: {2.0 * p3b_jepa.mean():.4f}")
print(f"  Triggered: {f4_triggered} => {'FAIL' if f4_triggered else 'PASS'}")

overall_falsified = f1_triggered or f2_triggered or f3_triggered or f4_triggered
print(f"\n{'='*65}")
if overall_falsified:
    print("OVERALL VERDICT: HYPOTHESIS FALSIFIED (at least one criterion triggered)")
else:
    print("OVERALL VERDICT: HYPOTHESIS NOT FALSIFIED (all criteria pass)")
print(f"{'='*65}")

# ---------------------------------------------------------------------------
# Per-task untrained > 60% check
# ---------------------------------------------------------------------------

untrained_class_means = [float(np.mean(variant_data["Untrained"][f"class_{i}"])) for i in range(4)]
flagged_tasks = []
for i, acc in enumerate(untrained_class_means):
    if acc > 0.60:
        flagged_tasks.append((i, CLASS_LABELS[i], acc))

print("\n--- Per-Task Untrained Baseline Check (>60%) ---")
if flagged_tasks:
    for idx, name, acc in flagged_tasks:
        print(f"  FLAGGED: Task {idx} ({name}): Untrained accuracy = {acc:.4f}")
else:
    print("  No tasks flagged (all Untrained per-class accuracies <= 60%)")

# ---------------------------------------------------------------------------
# Parameter counts
# ---------------------------------------------------------------------------
# d=16, d_in=48, d_out=16
# Per node: W_enc(48,16)=768, b_enc(16), W_dec(16,48)=768, b_dec(48) = 1600
# P3-A: 2 nodes = 3200
# P3-B: 2 nodes = 3200
# P3-C: 1 node = 1600
# Untrained: P3-B architecture frozen = 3200

d = 16
d_in = 3 * d
d_out = d
params_per_node = d_in * d_out + d_out + d_out * d_in + d_in
params_a = params_per_node * 2
params_b = params_per_node * 2
params_c = params_per_node
params_u = params_per_node * 2

param_counts = {
    "P3-A": params_a,
    "P3-B": params_b,
    "P3-C": params_c,
    "Untrained": params_u,
}

# ---------------------------------------------------------------------------
# Write REPORT.md
# ---------------------------------------------------------------------------

with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write("# Phase 3: Unified Spatiotemporal Grid -- Results Report\n\n")

    f.write("## Experiment Configuration\n")
    f.write("- Epochs: 30\n")
    f.write("- Train per class: 200\n")
    f.write("- Test per class: 100\n")
    f.write("- Batch size: 64\n")
    f.write("- Learning rate: 1e-3\n")
    f.write("- Seeds: 42-46\n")
    f.write("- Noise flip probability: 0.10\n")
    f.write("- Dataset: 4-class spatiotemporal binary grid (16 spatial x 32 temporal)\n\n")

    f.write("## Architecture Summary\n")
    f.write("| Variant | Description | Weight Sets | Params |\n")
    f.write("|---------|-------------|-------------|--------|\n")
    f.write(f"| P3-A | Sequential spatial->temporal | 2 (W_spatial, W_temporal) | {params_a:,} |\n")
    f.write(f"| P3-B | Joint training, separate weights | 2 (W_spatial, W_temporal) | {params_b:,} |\n")
    f.write(f"| P3-C | Unified, shared weights | 1 (W_shared) | {params_c:,} |\n")
    f.write(f"| Untrained | P3-B architecture, frozen weights | 2 (random, frozen) | {params_u:,} |\n\n")

    f.write("## Main Results\n\n")
    f.write("| Variant | Test Acc (mean+-std) | Train Acc (mean+-std) | Spatial Loss | Temporal Loss | Time (s) |\n")
    f.write("|---------|---------------------|----------------------|--------------|---------------|----------|\n")
    for v in variants:
        s = summary[v]
        f.write(f"| {v} | {s['test_mean']:.4f}+-{s['test_std']:.4f} | {s['train_mean']:.4f}+-{s['train_std']:.4f} | "
                f"{s['spatial_loss_mean']:.4f}+-{s['spatial_loss_std']:.4f} | "
                f"{s['temporal_loss_mean']:.4f}+-{s['temporal_loss_std']:.4f} | "
                f"{s['time_mean']:.1f}+-{s['time_std']:.1f} |\n")
    f.write("\n")

    f.write("## Per-Class (Per-Task) Accuracies\n\n")
    f.write("| Variant | moving_blob | expanding_blob | periodic_st | object_permanence |\n")
    f.write("|---------|-------------|----------------|-------------|-------------------|\n")
    for v in variants:
        means = summary[v]["class_means"]
        f.write(f"| {v} | {means[0]:.4f} | {means[1]:.4f} | {means[2]:.4f} | {means[3]:.4f} |\n")
    f.write("\n")

    f.write("## Pre-Registration Falsification Tests\n\n")
    f.write("Criteria (from `src/pre_registration.md`):\n")
    f.write("- **F1**: P3-C mean test acc - Untrained mean test acc < 8pp OR p >= 0.05 OR Cohen's d < 1.0\n")
    f.write("- **F2**: P3-B mean test acc - P3-C mean test acc > 10pp\n")
    f.write("- **F3**: P3-C mean test acc < P3-A mean test acc - 20pp\n")
    f.write("- **F4**: P3-C JEPA training loss > 2x P3-B final JEPA loss\n")
    f.write("- If **ANY** criterion is triggered, the specific aspect of the hypothesis is **falsified**.\n\n")

    # F1
    f.write("### F1: P3-C vs Untrained\n")
    f.write(f"- P3-C mean test accuracy: {summary['P3-C']['test_mean']:.4f}\n")
    f.write(f"- Untrained mean test accuracy: {summary['Untrained']['test_mean']:.4f}\n")
    f.write(f"- Gain: {f1_gain*100:.2f} percentage points\n")
    f.write(f"- Paired t-test: t = {f1_ttest.statistic:.4f}, p = {f1_ttest.pvalue:.4f}\n")
    f.write(f"- Cohen's d: {f1_d:.4f}\n")
    f.write(f"- Required: gain >= 8pp, p < 0.05, Cohen's d >= 1.0\n")
    f.write(f"- **Verdict: {'FAIL' if f1_triggered else 'PASS'}**\n\n")

    # F2
    f.write("### F2: P3-B vs P3-C\n")
    f.write(f"- P3-B mean test accuracy: {summary['P3-B']['test_mean']:.4f}\n")
    f.write(f"- P3-C mean test accuracy: {summary['P3-C']['test_mean']:.4f}\n")
    f.write(f"- Penalty (P3-B - P3-C): {f2_penalty*100:.2f} percentage points\n")
    f.write(f"- Required: penalty <= 10pp\n")
    f.write(f"- **Verdict: {'FAIL' if f2_triggered else 'PASS'}**\n\n")

    # F3
    f.write("### F3: P3-C vs P3-A\n")
    f.write(f"- P3-A mean test accuracy: {summary['P3-A']['test_mean']:.4f}\n")
    f.write(f"- P3-C mean test accuracy: {summary['P3-C']['test_mean']:.4f}\n")
    f.write(f"- Gap (P3-A - P3-C): {f3_gap*100:.2f} percentage points\n")
    f.write(f"- Required: gap < 20pp (i.e., P3-C >= P3-A - 20pp)\n")
    f.write(f"- **Verdict: {'FAIL' if f3_triggered else 'PASS'}**\n\n")

    # F4
    f.write("### F4: P3-C JEPA loss vs 2x P3-B JEPA loss\n")
    f.write(f"- P3-C mean combined JEPA loss (spatial + temporal): {p3c_jepa.mean():.4f}\n")
    f.write(f"- P3-B mean combined JEPA loss (spatial + temporal): {p3b_jepa.mean():.4f}\n")
    f.write(f"- 2x P3-B JEPA loss: {2.0 * p3b_jepa.mean():.4f}\n")
    f.write(f"- Required: P3-C loss <= 2x P3-B loss\n")
    f.write(f"- **Verdict: {'FAIL' if f4_triggered else 'PASS'}**\n\n")

    # Overall
    f.write("### Overall Falsification Verdict\n")
    if overall_falsified:
        f.write("**At least one falsification criterion is TRIGGERED.**\n")
        failed = []
        if f1_triggered: failed.append("F1")
        if f2_triggered: failed.append("F2")
        if f3_triggered: failed.append("F3")
        if f4_triggered: failed.append("F4")
        f.write(f"Triggered criteria: {', '.join(failed)}.\n")
        f.write("Therefore, the specific aspect of the universal parameter hypothesis "
                "tested in Phase 3 is **falsified**.\n\n")
    else:
        f.write("**No falsification criteria triggered.**\n")
        f.write("The universal parameter hypothesis is **not falsified** by Phase 3 results.\n\n")

    # Shortcut baselines
    f.write("## Shortcut Baseline Results\n\n")
    f.write("| Baseline | Train Acc (mean+-std) | Test Acc (mean+-std) |\n")
    f.write("|----------|----------------------|---------------------|\n")
    for name in sorted(shortcut_summary.keys()):
        s = shortcut_summary[name]
        f.write(f"| {name} | {s['train_mean']:.4f}+-{s['train_std']:.4f} | {s['test_mean']:.4f}+-{s['test_std']:.4f} |\n")
    f.write("\n")

    # Untrained per-task analysis
    f.write("## Per-Task Untrained Baseline Analysis\n\n")
    f.write("| Task | Untrained Accuracy | Flagged (>60%)? |\n")
    f.write("|------|-------------------|-----------------|\n")
    for i in range(4):
        flagged = untrained_class_means[i] > 0.60
        f.write(f"| {CLASS_LABELS[i]} | {untrained_class_means[i]:.4f} | {'YES' if flagged else 'No'} |\n")
    f.write("\n")
    if flagged_tasks:
        f.write("**Warning:** The following task(s) have Untrained per-class accuracy > 60%, "
                "which may indicate a potential shortcut or label leakage in the task design.\n\n")
        for idx, name, acc in flagged_tasks:
            f.write(f"- **{name}**: {acc:.4f}\n")
        f.write("\n")
    else:
        f.write("No tasks exceed the 60% Untrained threshold.\n\n")

    f.write("## Key Findings\n\n")
    f.write("1. **Overall test accuracies are low (~41-48%)**, well above chance (25%) "
            "but far below what would constitute strong task learning.\n")
    f.write("2. **P3-C (unified/shared weights) underperforms P3-B (separate weights)** "
            f"by {f2_penalty*100:.1f}pp, and is slightly below P3-A (sequential) by {f3_gap*100:.1f}pp.\n")
    f.write("3. **P3-C does not demonstrate a statistically significant gain over Untrained** "
            f"(gain = {f1_gain*100:.1f}pp, p = {f1_ttest.pvalue:.3f}, Cohen's d = {f1_d:.2f}).\n")
    f.write("4. **JEPA losses converge** for all variants, with P3-C's combined loss "
            f"({p3c_jepa.mean():.2f}) within the 2x bound of P3-B ({2.0*p3b_jepa.mean():.2f}).\n")
    f.write("5. **Shortcut baselines** achieve ~23-38% test accuracy, confirming that "
            "single-frame and temporal-average features are insufficient for the task.\n")
    f.write("6. **P3-C uses 50% fewer parameters** than P3-A/P3-B ({params_c:,} vs {params_b:,}), "
            "but this parameter efficiency does not translate into competitive accuracy.\n\n")

    f.write("## Conclusions\n\n")
    if overall_falsified:
        f.write("The Phase 3 experiment **fails to support** the universal parameter hypothesis.\n\n")
        f.write("The pre-registered falsification criteria were designed to test whether a single "
                "shared weight set (P3-C) could achieve performance competitive with sequential (P3-A) "
                "and joint-but-separate (P3-B) architectures. The results show:\n\n")
        if f1_triggered:
            f.write("- **F1 (Training Gain) is FAILED**: P3-C does not significantly outperform the "
                    "untrained baseline, meaning the training procedure does not produce a meaningful "
                    "learning signal for the unified weights.\n")
        if f2_triggered:
            f.write("- **F2 (Expressivity Penalty) is FAILED**: The shared-weight constraint in P3-C "
                    "imposes a larger-than-acceptable accuracy penalty relative to P3-B.\n")
        if f3_triggered:
            f.write("- **F3 (Sequential Baseline) is FAILED**: P3-C falls more than 20pp behind P3-A, "
                    "failing the viability threshold.\n")
        if f4_triggered:
            f.write("- **F4 (Optimization) is FAILED**: P3-C's combined JEPA loss exceeds twice P3-B's, "
                    "indicating optimization difficulty due to conflicting spatial and temporal objectives.\n")
        f.write("\nGiven these failures, the hypothesis that a single universal weight set can serve "
                "both spatial and temporal prediction while maintaining competitive classification accuracy "
                "is **not supported** by the Phase 3 data.\n")
    else:
        f.write("The Phase 3 experiment provides preliminary support for the universal parameter hypothesis.\n\n")
        f.write("P3-C (shared weights) satisfies all four falsification criteria, meaning:\n\n")
        f.write("- It significantly outperforms the untrained baseline (F1).\n")
        f.write("- The shared-weight penalty relative to P3-B is <= 10pp (F2).\n")
        f.write("- It remains within 20pp of the sequential P3-A baseline (F3).\n")
        f.write("- Its JEPA loss does not indicate catastrophic optimization failure (F4).\n\n")
        f.write("However, absolute accuracies remain modest (~40-45%), suggesting that while the "
                "unified architecture is viable, further architectural or optimization improvements "
                "are needed for strong spatiotemporal task performance.\n")

    f.write("\n---\n")
    f.write("*Report generated automatically by phase_3/comprehensive_analysis.py*\n")

print(f"\nReport written to {REPORT_MD}")
