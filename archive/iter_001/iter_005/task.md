## Task: Tune Encoders, Create Experiment Runner, Run Full Experiment, Generate Report

This is the final sub-task for Phase 0 of the HSUN project. You must:
1. Update P0-D defaults to match best-found hyperparameters
2. Test and tune all encoders
3. Create the experiment runner
4. Run the full experiment across 5 seeds
5. Generate the comparison report

### Step 1: Update P0-D SparseAutoencoder defaults

Edit `src/encoders/sparse_autoencoder.py`: Change the default parameters to the best-found values:
- `lr=0.15` (was 0.05)
- `l1_lambda=0.002` (was 0.005)
- `epochs=200` in train() default (already there)

Also verify the backprop implementation is correct (the agent in 1.4 mentioned a bug fix for bias gradients using np.sum instead of np.mean — check that the current code uses np.sum for d_b2 and d_b1).

### Step 2: Test all encoders individually

Run each encoder's standalone test to verify they work and get preliminary rho values:

```bash
cd /to/project/root
python -c "import sys; sys.path.insert(0,'src'); from encoders.lookup_table import LookupTableEncoder; from harness import DatasetGenerator, SimilarityEvaluator; import numpy as np; ds=DatasetGenerator(seed=42); base=ds.get_base_states(); all_s=ds.get_all_samples(); e=LookupTableEncoder(seed=42); e.train(all_s); c=e.encode(base); rho,p,_,_,_,_=SimilarityEvaluator.evaluate(base,c); print(f'P0-A rho={rho}, codes shape={c.shape}')"

python src/encoders/spatial_pooler.py
python src/encoders/som.py  
python src/encoders/sparse_autoencoder.py
python src/encoders/predictive_coding.py
```

### Step 3: Tune encoders that don't meet rho >= 0.6

For each encoder that doesn't achieve rho >= 0.6, try tuning:

**P0-B SpatialPooler:** The current implementation achieved rho=0.16 which is very low. The problem is likely that the HTM-style permanence update doesn't produce similarity-preserving codes well for this tiny problem. Try these modifications:
- Increase training epochs (200 instead of 50)
- Reduce k from 5 to 3 (fewer winners = sparser but potentially more structured)
- Add a boost mechanism: under-utilized columns get boosted
- IMPORTANT: If after reasonable tuning P0-B still can't reach 0.6, that's a valid scientific finding — document it honestly

**P0-C SOM:** Achieved rho=0.44. Try:
- More training epochs (200)
- Better neighborhood decay schedule
- Use Euclidean distance in weight space directly as the code (instead of Gaussian activation) — this preserves topology better. The code could be: for each input, compute distance to ALL 16 SOM units. Normalize these distances to create a code vector where similar inputs produce similar distance patterns.

**P0-E PredictiveCodingEncoder:** Untested. Run it and see. If rho is low:
- Adjust learning rate
- Try different sparsity thresholds
- If the local error learning doesn't produce good codes, that's a valid finding

**IMPORTANT about the rho >= 0.6 criterion:** According to the pre-registration (`src/pre_registration.md`), only P0-B through P0-E need rho >= 0.6. If one of them genuinely cannot reach 0.6 after reasonable tuning, that is a NEGATIVE RESULT, not a bug. Report it honestly. Phase 0 is a smoke test; the key question is whether the harness works, not whether every method is great.

### Step 4: Create `src/run_phase0.py`

The main experiment runner:

```python
"""
HSUN Phase 0 — Full Experiment Runner

Runs all 5 encoders × 5 seeds, collects metrics, generates report.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import time
import numpy as np
from harness import DatasetGenerator, SimilarityEvaluator, compute_sparsity
from encoders import ENCODER_REGISTRY

SEEDS = [42, 43, 44, 45, 46]
EPOCHS = 200  # Training epochs for iterative methods

def run_single(encoder_id, encoder_class, seed):
    """Run one encoder with one seed. Return dict of metrics."""
    ds = DatasetGenerator(seed=seed)
    base = ds.get_base_states()
    all_samples = ds.get_all_samples()
    
    # Instantiate encoder
    if encoder_id == "p0-a":
        encoder = encoder_class(seed=seed)
    else:
        encoder = encoder_class(seed=seed)
    
    # Train
    t0 = time.time()
    train_metrics = encoder.train(all_samples, epochs=EPOCHS)
    train_time = time.time() - t0
    
    # Encode base states
    codes = encoder.encode(base)
    
    # Evaluate similarity
    rho, p_val, inv_h, cos_s, _, _ = SimilarityEvaluator.evaluate(base, codes)
    
    # Compute sparsity
    sparsity = compute_sparsity(codes)
    
    return {
        "encoder_id": encoder_id,
        "seed": seed,
        "spearman_rho": rho,
        "p_value": p_val,
        "sparsity": sparsity,
        "train_time_sec": train_time,
        "final_loss": train_metrics.get("final_loss", float("nan")),
        "n_codes": codes.shape[0],
        "dim_out": encoder.dim_out,
    }

def main():
    results = []
    for encoder_id, encoder_class in sorted(ENCODER_REGISTRY.items()):
        for seed in SEEDS:
            try:
                result = run_single(encoder_id, encoder_class, seed)
                result["status"] = "ok"
                print(f"  {encoder_id} seed={seed}: rho={result['spearman_rho']:.4f}, sparsity={result['sparsity']:.4f}")
            except Exception as e:
                result = {"encoder_id": encoder_id, "seed": seed, "status": f"error: {e}"}
                print(f"  {encoder_id} seed={seed}: ERROR: {e}")
            results.append(result)
    
    # Save raw results as CSV
    # ... (implement CSV writing)
    
    # Generate report
    # ... (implement report generation)

if __name__ == "__main__":
    main()
```

Complete the implementation with:
- CSV output to `phase_0/results.csv`
- Full report generation to `phase_0/REPORT.md`

### Step 5: Generate `phase_0/REPORT.md`

The report must contain:

1. **Summary Table** with columns: Encoder | rho (mean±std) | Sparsity | Final Loss | Train Time | Pass/Fail
   - P0-A is EXEMPT from the rho >= 0.6 criterion
   - For P0-A, show "Exempt (negative control)" in the Pass/Fail column

2. **Success Criteria Evaluation**:
   - Criterion 1: All five implementations run end-to-end → YES/NO
   - Criterion 2: Non-trivial encoders achieve rho >= 0.6 → per-encoder status
   - Criterion 3: Local methods within 0.15 of P0-D baseline → per-method comparison

3. **Key Findings**:
   - Which methods pass/fail and why
   - Comparison of local vs global training
   - Recommendation for Phase 1 baseline

4. **Data**: Reference `phase_0/results.csv` for raw data

### Critical Instructions:
- READ `src/pre_registration.md` first and follow its criteria strictly
- Do NOT alter the rho >= 0.6 threshold post-hoc if methods fail
- Report honest results, including negative findings
- All files in `src/`, report in `phase_0/`
- Create `phase_0/` directory if it doesn't exist
- Make sure the experiment runs completely (all 25 runs: 5 encoders × 5 seeds)
