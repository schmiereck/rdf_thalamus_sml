# Phase 3: Complete Spatiotemporal Grid Experiments

You are continuing the HSUN Phase 3 experiments. The code infrastructure exists but only seed 42 has been run. You need to complete all experiments and produce a comprehensive results file.

## Current State

The following files exist and are ready to use:
- `src/spatiotemporal_encoder.py` — P3-A, P3-B, P3-C architectures (3 bugs fixed)
- `src/spatiotemporal_dataset.py` — 4-class spatiotemporal dataset generator
- `src/run_phase3.py` — Full experiment runner (200 epochs, 500 train/class, 5 seeds)
- `src/run_phase3_fast.py` — Fast experiment runner (50 epochs, 200 train/class, 4 seeds)
- `src/training_objectives.py` — JEPALoss, _Adam optimizer
- `src/node.py` — UniversalNode
- `src/harness.py` — SimpleLogisticRegression
- `src/pre_registration.md` — Pre-registration file (needs update per Research Manager)
- `phase_3/phase3_results.csv` — Only seed 42 results exist (may be from pre-fix code)

## Your Tasks

### Step 1: Update Pre-Registration

Update `src/pre_registration.md` with the revised F2 criterion from the Research Manager:
- Original F2: "P3-C mean accuracy is within 5pp of untrained-baseline accuracy"
- Revised F2: "P3-C fails to outperform the Untrained baseline with statistical significance (p < 0.05 via paired t-test across 5 seeds) and strong effect size (Cohen's d ≥ 1.0), with absolute mean accuracy gain over untrained of at least 8pp. If P3-C fails this test, the unified weight hypothesis is falsified."

Also add the full pre-registered falsification criteria as follows:
- F1: P3-C mean test accuracy - Untrained mean test accuracy < 8pp OR p >= 0.05 OR Cohen's d < 1.0 (training gain insufficient)
- F2: P3-B mean test accuracy - P3-C mean test accuracy > 10pp (shared-weight expressivity penalty too large)
- F3: P3-C mean test accuracy < P3-A mean test accuracy - 20pp (not viable vs sequential baseline)
- F4: P3-C JEPA training loss > 2x P3-B final JEPA loss (optimization failure)

### Step 2: Profile Training Speed

Before running all experiments, profile a single training run to determine actual speed:
```bash
cd C:\Users\thomas\Projekte\rdf_thalamus_sml
python -c "
import sys, os, time
sys.path.insert(0, 'src')
from run_phase3 import run_single_experiment
t0 = time.time()
result = run_single_experiment('P3-B', 42, epochs=10, batch_size=32, lr=1e-3, update_encoder=True)
t1 = time.time()
print(f'10-epoch P3-B run: {t1-t0:.1f}s')
print(f'Estimated 200-epoch: {(t1-t0)*20:.1f}s')
"
```

If 200-epoch × 20 runs would exceed 30 minutes total, use reduced settings:
- Try 100 epochs first (should be sufficient for JEPA convergence)
- If still too slow, use 50 epochs with 200 train/class (the fast runner settings)
- Document what settings you use and why

### Step 3: Run All Experiments

Run 4 variants × 5 seeds = 20 experiments:
- Variants: P3-A, P3-B, P3-C, Untrained
- Seeds: 42, 43, 44, 45, 46
- Use the run_phase3.py infrastructure (modify settings as needed based on profiling)
- Save results to `phase_3/phase3_full_results.csv`

IMPORTANT: Save results incrementally (after each seed completes) so we don't lose data if interrupted. Write a custom runner script that appends to CSV after each run.

### Step 4: Run Shortcut Baselines

Run shortcut baselines (single-frame, temporal-average) for each seed:
- Use `evaluate_all_shortcut_baselines` from `src/spatiotemporal_dataset.py`
- Save to `phase_3/shortcut_baselines.csv`
- These are CRITICAL for the Research Manager's mandate to flag tasks with untrained > 60%

### Step 5: Run Per-Task Analysis

For each of the 4 classes/tasks, compute the untrained baseline accuracy separately. The dataset has 4 classes:
- Class 0: moving_blob
- Class 1: expanding_blob
- Class 2: periodic_st
- Class 3: object_permanence

The existing phase3_results.csv already has per-class accuracies (class_0_acc, class_1_acc, class_2_acc, class_3_acc). Use these to identify if any task has untrained accuracy > 60%.

### Step 6: Verify Data Integrity

After all runs complete, verify:
- All 20 rows exist in the results CSV
- No NaN or infinite values
- Per-class accuracies sum to reasonable values
- Training times are consistent

## Output Files

Create/overwrite:
- `src/pre_registration.md` — Updated with revised F2 criterion
- `phase_3/phase3_full_results.csv` — All 20 experiment results
- `phase_3/shortcut_baselines.csv` — Shortcut baseline results
- `phase_3/experiment_config.txt` — Document the actual settings used (epochs, train_size, batch_size, lr)

## Important Notes

- Working directory: C:\Users\thomas\Projekte\rdf_thalamus_sml
- Python is available on the system PATH
- All src/ files are importable via sys.path.insert(0, 'src')
- The spatiotemporal_dataset uses N_CLASSES=4, N_SPATIAL=16, N_TIMESTEPS=32
- For P3-A: sequential training (spatial first then temporal) — this takes 2x the time
- For P3-B, P3-C: joint training alpha=0.5
- For Untrained: same as P3-B architecture but encoder weights frozen (only JEPA predictors trained)
