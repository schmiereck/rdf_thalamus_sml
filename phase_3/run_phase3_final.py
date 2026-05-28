"""
Phase 3 Final Run Script:
1. Deduplicate phase_3/phase3_full_results.csv (keep first occurrence)
2. Run P3-A experiments for seeds 42-46
3. Run shortcut baselines
4. Verify final results
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, 'src')

RESULTS_CSV = 'phase_3/phase3_full_results.csv'
SHORTCUT_CSV = 'phase_3/shortcut_baselines.csv'
SEEDS = [42, 43, 44, 45, 46]

# -----------------------------------------------------------
# Task 1: Deduplicate
# -----------------------------------------------------------
print("=" * 70)
print("  Task 1: Deduplicate Results CSV")
print("=" * 70)

with open(RESULTS_CSV, 'r', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f"  Total rows before dedup: {len(rows)}")

seen = set()
unique_rows = []
for row in rows:
    key = (row['variant'], row['seed'])
    if key not in seen:
        seen.add(key)
        unique_rows.append(row)

print(f"  Total rows after dedup:  {len(unique_rows)}")

# Write back clean version
with open(RESULTS_CSV, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_rows)

print(f"  -> Clean CSV saved to {RESULTS_CSV}")

# Which P3-A seeds are missing?
present = set((r['variant'], r['seed']) for r in unique_rows)
missing_seeds = [s for s in SEEDS if ('P3-A', str(s)) not in present]
print(f"  Missing P3-A seeds: {missing_seeds}")
print()

# -----------------------------------------------------------
# Task 2: Run missing P3-A experiments
# -----------------------------------------------------------
if missing_seeds:
    print("=" * 70)
    print("  Task 2: Run P3-A Experiments")
    print("=" * 70)

    from run_phase3_optimized import (
        run_single_experiment_opt,
        save_result_incrementally,
        EPOCHS,
        BATCH_SIZE,
        LR,
        N_TRAIN_PER_CLASS,
        N_TEST_PER_CLASS,
    )

    for seed in missing_seeds:
        print(f"\n--- P3-A, seed={seed} ---")
        t0 = time.time()
        result = run_single_experiment_opt(
            variant='P3-A',
            seed=seed,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            lr=LR,
            update_encoder=True,
            n_train_per_class=N_TRAIN_PER_CLASS,
            n_test_per_class=N_TEST_PER_CLASS,
        )
        elapsed = time.time() - t0
        save_result_incrementally(result, RESULTS_CSV)
        print(f"  -> Saved (took {elapsed:.1f}s)")

    print("\n  All P3-A experiments complete.")
else:
    print("=" * 70)
    print("  Task 2: All P3-A experiments already present, skipping.")
    print("=" * 70)

print()

# -----------------------------------------------------------
# Task 3: Run Shortcut Baselines
# -----------------------------------------------------------
print("=" * 70)
print("  Task 3: Run Shortcut Baselines")
print("=" * 70)

from run_phase3_optimized import run_shortcut_baselines

shortcut_rows = []
for seed in SEEDS:
    print(f"\n  Seed {seed}...")
    rows = run_shortcut_baselines(seed, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS)
    shortcut_rows.extend(rows)
    for row in rows:
        print(f"    {row['baseline_name']:30s}  test_acc={row['test_acc']:.4f}")

with open(SHORTCUT_CSV, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "baseline_name", "train_acc", "test_acc"])
    writer.writeheader()
    writer.writerows(shortcut_rows)

print(f"\n  -> Shortcut baselines saved to {SHORTCUT_CSV}")
print()

# -----------------------------------------------------------
# Task 4: Verify Final Results
# -----------------------------------------------------------
print("=" * 70)
print("  Task 4: Verify Final Results")
print("=" * 70)

with open(RESULTS_CSV, 'r', newline='') as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

print(f"  Total rows: {len(all_rows)}")
pairs = [(r['variant'], r['seed']) for r in all_rows]
unique_pairs = set(pairs)
print(f"  Unique (variant, seed) pairs: {len(unique_pairs)}")

# Check: exactly 20 unique pairs
n_variants = len(set(p[0] for p in unique_pairs))
print(f"  Distinct variants: {n_variants}")
for v in sorted(set(p[0] for p in unique_pairs)):
    seeds_for_v = [p[1] for p in unique_pairs if p[0] == v]
    print(f"    {v}: {len(seeds_for_v)} seeds ({sorted([int(s) for s in seeds_for_v])})")

# Check no duplicates
duplicates = False
from collections import Counter
counts = Counter(pairs)
for (v, s), c in counts.items():
    if c > 1:
        print(f"  DUPLICATE: {v}, seed {s} appears {c} times")
        duplicates = True
if not duplicates:
    print("  No duplicate rows: PASS")

# Check: reasonable accuracy values (all between 0 and 1)
bad_acc = False
for r in all_rows:
    for key in ['train_acc', 'test_acc', 'class_0_acc', 'class_1_acc', 'class_2_acc', 'class_3_acc']:
        val = float(r[key])
        if not (0.0 <= val <= 1.0):
            print(f"  BAD VALUE: {r['variant']}, seed {r['seed']}, {key}={val}")
            bad_acc = True
if not bad_acc:
    print("  All accuracy values in [0, 1]: PASS")

# Expect exactly 20 rows
if len(all_rows) == 20:
    print("  Exactly 20 rows: PASS")
else:
    print(f"  Exactly 20 rows: FAIL (got {len(all_rows)})")

# Expect 4 variants
variants_expected = {'Untrained', 'P3-A', 'P3-B', 'P3-C'}
if set(p[0] for p in unique_pairs) == variants_expected:
    print("  All 4 variants present: PASS")
else:
    print(f"  All 4 variants present: FAIL")

print("\n" + "=" * 70)
print("  Verification Complete")
print("=" * 70)
