# Phase 3: Final Cleanup, Shortcut Baselines, and Statistical Analysis

Working directory: `C:\Users\thomas\Projekte\rdf_thalamus_sml`

All 20 experiment runs (4 variants × 5 seeds) have been completed. The results are in `phase_3/phase3_full_results.csv` but have many duplicate rows from multiple background processes. You need to:

## Step 1: Clean Up CSV (deduplicate)

Write and run a script to deduplicate the CSV, keeping only the FIRST occurrence of each (variant, seed) pair:

```python
import csv

INPUT = "phase_3/phase3_full_results.csv"
rows = []
seen = set()
with open(INPUT) as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        key = (row['variant'], row['seed'])
        if key not in seen:
            seen.add(key)
            rows.append(row)

with open(INPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
print(f"Cleaned: {len(rows)} unique rows")
```

## Step 2: Run Shortcut Baselines

Create and run a script to compute shortcut baselines:

```python
import sys, os, csv
sys.path.insert(0, 'src')
from spatiotemporal_dataset import generate_spatiotemporal_dataset, evaluate_all_shortcut_baselines

SEEDS = [42, 43, 44, 45, 46]
shortcut_rows = []
for seed in SEEDS:
    ds = generate_spatiotemporal_dataset(
        n_train_per_class=200,
        n_test_per_class=100,
        noise_flip_prob=0.10,
        seed=seed,
    )
    results = evaluate_all_shortcut_baselines(
        ds["train_x"], ds["train_y"], ds["test_x"], ds["test_y"],
        frames_to_test=[0, 8, 16, 24, 31],
    )
    for name, res in results.items():
        shortcut_rows.append({
            "seed": seed,
            "baseline_name": name,
            "train_acc": res["train_acc"],
            "test_acc": res["test_acc"],
        })

with open("phase_3/shortcut_baselines.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)
print(f"Shortcut baselines: {len(shortcut_rows)} rows")
for row in shortcut_rows:
    print(f"  {row['seed']}/{row['baseline_name']}: train={row['train_acc']:.4f} test={row['test_acc']:.4f}")
```

## Step 3: Comprehensive Statistical Analysis

Create and run a comprehensive analysis script. Read the pre-registration file at `src/pre_registration.md` for the exact falsification criteria.

The analysis should:
1. Load the cleaned CSV
2. Compute mean ± std test accuracy for each variant
3. Compute per-class accuracy for each variant (mean across seeds)
4. Test the pre-registered falsification criteria:
   - F1: P3-C vs Untrained (paired t-test, Cohen's d, gain >= 8pp)
   - F2: P3-B vs P3-C (penalty <= 10pp)
   - F3: P3-C vs P3-A (within 20pp)
   - F4: P3-C JEPA loss <= 2× P3-B JEPA loss
5. Check if any task has Untrained per-class accuracy > 60% (Research Manager mandate)
6. Compare with shortcut baselines
7. Parameter count comparison

Write the results to `phase_3/REPORT.md`.

## Step 4: Write Phase 3 Report

Write `phase_3/REPORT.md` with the following structure:

```markdown
# Phase 3: Unified Spatiotemporal Grid — Results Report

## Experiment Configuration
- Epochs: 30
- Train per class: 200
- Test per class: 100
- Batch size: 64
- Learning rate: 1e-3
- Seeds: 42-46

## Architecture Summary
| Variant | Description | Weight Sets | Params |
|---------|-------------|-------------|--------|
| P3-A    | Sequential spatial→temporal | 2 (W_spatial, W_temporal) | ? |
| P3-B    | Joint training, separate weights | 2 (W_spatial, W_temporal) | ? |
| P3-C    | Unified, shared weights | 1 (W_shared) | ? |
| Untrained | P3-B architecture, frozen weights | 2 (random, frozen) | ? |

## Main Results

| Variant | Test Acc (mean±std) | Spatial Loss | Temporal Loss |
|---------|---------------------|--------------|---------------|
| P3-A    | ?±?                 | ?            | ?             |
| P3-B    | ?±?                 | ?            | ?             |
| P3-C    | ?±?                 | ?            | ?             |
| Untrained | ?±?               | ?            | ?             |

## Per-Class (Per-Task) Accuracies
[Table showing per-class accuracy for each variant]

## Pre-Registration Falsification Tests

### F1: P3-C vs Untrained
- Gain: ?pp
- Paired t-test: t=?, p=?
- Cohen's d: ?
- Verdict: PASS/FAIL

[Similar for F2, F3, F4]

## Shortcut Baseline Results
[Table]

## Per-Task Untrained Baseline Analysis
[Flag any task where Untrained > 60%]

## Key Findings
[Summarize]

## Conclusions
[Clear statement about whether the universal parameter hypothesis is supported]
```

IMPORTANT: The report must be factual and avoid speculative language. If P3-C fails to outperform untrained, state this clearly.

## Pre-Registration Falsification Criteria (from src/pre_registration.md)

- F1: P3-C mean test accuracy - Untrained mean test accuracy < 8pp OR p >= 0.05 OR Cohen's d < 1.0
- F2: P3-B mean test accuracy - P3-C mean test accuracy > 10pp
- F3: P3-C mean test accuracy < P3-A mean test accuracy - 20pp
- F4: P3-C JEPA training loss > 2× P3-B final JEPA loss

If ANY of F1, F2, F3, F4 is triggered, the specific aspect of the hypothesis is falsified.
