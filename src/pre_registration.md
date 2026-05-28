# RDF Scientific Pre-Registration

*   **Iteration:** 007
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
On the Phase 3 spatiotemporal benchmark (P3-C architecture, 1,600 params,
spatial_pooled_then_flat readout, pooled VICReg applied to all objectives),
JEPA + pooled VICReg is the best training objective. Specifically:
(H1) JEPA + pooled VICReg achieves test accuracy ≥ 58% (within 4pp of the
     61.55% reference from iter_006).
(H2) No other objective (SFA, Hebbian, Contrastive, Reconstruction) with
     pooled VICReg exceeds JEPA + pooled VICReg by more than 2pp.
(H3) All objectives with pooled VICReg outperform their counterparts without
     pooled VICReg (confirming the pooled VICReg fix generalises).

## 2. Falsification Criterion
The hypothesis is falsified if ANY of the following hold:
F1: JEPA + pooled VICReg achieves < 55% test accuracy (indicating the
    result is not reproducible or the implementation is broken).
F2: Any other objective with pooled VICReg exceeds JEPA + pooled VICReg
    by ≥ 3pp (JEPA is NOT the best objective).
F3: For any objective, the version WITHOUT pooled VICReg achieves equal or
    higher accuracy than the version WITH pooled VICReg (pooled VICReg fix
    does not generalise).

## 3. Proposed Method
Step 1: Create src/run_phase4.py — the unified Phase 4 experiment runner.

Step 2: Implement 5 training objectives adapted for SpatiotemporalEncoder:
  - P4-A: JEPA + pooled VICReg (reference, from run_phase3_vicreg_fix.py)
  - P4-B: Local JEPA (prediction only, no pooled VICReg — control)
  - P4-C: SFA + pooled VICReg (slowness on temporal axis + variance penalty)
  - P4-D: Hebbian + pooled VICReg (Oja's rule on encoder weights + VICReg)
  - P4-E: Reconstruction (sparse AE) + pooled VICReg (local reconstruction + VICReg)

For each objective, the training loop follows the same pattern:
1. Forward pass through SpatiotemporalEncoder
2. Compute objective-specific loss and code gradients
3. If pooled VICReg is enabled, compute pooled VICReg gradient and inject
   into the last temporal code gradient (same mechanism as iter_006)
4. Backward pass through encoder
5. Adam update on encoder parameters
6. Evaluate with spatial_pooled_then_flat readout

Step 3: Run 5 objectives × 2 VICReg conditions (with/without) × 5 seeds
= 50 experiments. Plus 5 untrained baselines × 5 seeds = 25 additional.
Total: 55 runs. Each run: 30 epochs, batch=64, lr=1e-3.

Step 4: Save results to phase_4/phase4_results.csv with columns:
objective, seed, use_pooled_vicreg, train_acc, test_acc, per-class accs,
final_loss, pooled_std, training_time_sec.

Step 5: Statistical analysis and report generation:
- Paired t-tests between each objective and untrained baseline
- Effect sizes (Cohen's d)
- Comparison table with mean ± std for all 10+ conditions
- VICReg ablation analysis (with vs without for each objective)
- Recommendation for default objective

Step 6: Write phase_4/REPORT.md with:
- Clean comparison table (all objectives, both VICReg conditions)
- Statistical significance markers
- Training stability observations
- Compute cost comparison
- Formal recommendation

Files to create/modify:
- src/run_phase4.py (NEW — unified experiment runner)
- src/pre_registration.md (UPDATE)
- phase_4/phase4_results.csv (NEW — results)
- phase_4/REPORT.md (NEW — final comparison report)

---
*Created automatically by the RDF Orchestrator prior to iteration execution.*
