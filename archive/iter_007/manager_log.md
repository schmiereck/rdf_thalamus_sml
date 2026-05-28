# Research Manager Log - Iteration 007

## Iteration 007 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
On the Phase 3 spatiotemporal benchmark (P3-C architecture, 1,600 params,
spatial_pooled_then_flat readout, pooled VICReg applied to all objectives),
JEPA + pooled VICReg is the best training objective. Specifically:
(H1) JEPA + pooled VICReg achieves test accuracy ≥ 58% (within 4pp of the
     61.55% reference from iter_006).
(H2) No other objective (SFA, Hebbian, Contrastive, Reconstruction) with
     pooled VICReg exceeds JEPA + pooled VICReg by more than 2pp.
(H3) All objectives with pooled VICReg outperform their counterparts without
     pooled VICReg (confirming the pooled VICReg fix generalises).

**Proposed Falsification Criterion:**
The hypothesis is falsified if ANY of the following hold:
F1: JEPA + pooled VICReg achieves < 55% test accuracy (indicating the
    result is not reproducible or the implementation is broken).
F2: Any other objective with pooled VICReg exceeds JEPA + pooled VICReg
    by ≥ 3pp (JEPA is NOT the best objective).
F3: For any objective, the version WITHOUT pooled VICReg achieves equal or
    higher accuracy than the version WITH pooled VICReg (pooled VICReg fix
    does not generalise).

**Proposed Method:**
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

## Iteration 007 -> Planner [Strategic Guidance]

### Strategic Guidance: Manager's Note

To: The Planner Agent
From: Research Manager
Subject: Phase 4 Methodological Rigour — Objective Formulation & Collapse Baselines

We are transitioning into **Phase 4 (Training Objective Comparison)**. While the resolution of Phase 3 was a significant success, we must approach the comparative phase with high skepticism and formal mathematical discipline. 

I have reviewed your draft plan and have detected several conceptual ambiguities regarding how these training objectives are formulated, particularly around the mechanics of representation collapse and the role of VICReg.

Please address the following **three strategic directives** in your final pre-registration and implementation:

---

### 1. The Reconstruction Baseline: Native vs. Regularized
Your plan proposes running "Reconstruction + pooled VICReg". 
* **The Construction-vs-Empirical Test:** A reconstruction objective (e.g., minimizing $\|x - \hat{x}\|_2^2$ via a local decoder) is mathematically incapable of collapsing to a constant vector under non-constant inputs, because a constant representation contains zero mutual information about the target. Thus, **pure reconstruction natively resists representation collapse**.
* **Action:** You must evaluate a **pure Reconstruction (Sparse/Standard AE) control without VICReg**. If Reconstruction *without* VICReg outperforms JEPA + VICReg, or if adding VICReg to Reconstruction degrades its performance, this is a major empirical finding that we must report honestly. Do not default to grafting VICReg onto objectives that do not require it.

### 2. Formulating SFA and Hebbian Objectives Mathematically
To avoid vague implementations, you must pre-register the exact mathematical loss functions or update rules for SFA and Hebbian learning:
* **Slow Feature Analysis (SFA):** Classic SFA minimizes temporal variance of the first derivative: $\mathcal{L}_{\text{slow}} = \mathbb{E}_t[\|h_t - h_{t-1}\|_2^2]$ subject to $\text{Var}(h) = I$. In a gradient-descent framework, the VICReg variance and covariance terms are precisely the lagrangian relaxations of these SFA constraints. Therefore, **SFA + VICReg is the standard gradient-based formulation of SFA**. Frame and document it as such, rather than as an ad-hoc hybrid.
* **Hebbian Learning:** Classical Hebbian rules (like Oja's rule) are direct, non-gradient weight updates ($\Delta W = \eta (y x^T - y^2 W)$). If you implement Oja's rule, it must bypass Adam and update weights directly after the forward pass. If you instead write a "Hebbian loss" to be optimized via backpropagation and Adam, you must define it. Note that maximizing representation variance ($\mathcal{L} = -\sum \text{Var}(h_i)$) is mathematically equivalent to the Hebbian objective. If you use a gradient loss, clarify why it is distinct from VICReg's variance term, or explicitly implement true local Oja updates.

### 3. Refined Falsification and Pre-Registration
Your pre-registration file (`src/pre_registration.md`) must be written and committed before running the simulations. Refine your falsification criteria to make room for honest nulls or alternative winners:
* **F1 (Fidelity Check):** JEPA + pooled VICReg fails to achieve $\ge 55\%$ test accuracy (verifying code/pipeline regression).
* **F2 (Superiority Falsification):** Any other objective (with or without VICReg) outperforms JEPA + pooled VICReg by $\ge 3\text{ pp}$. (If Reconstruction or SFA wins natively, we celebrate the result and pivot).
* **F3 (Ablation Rigour):** If VICReg is claimed to be universally necessary, but any objective $X$ performs equal to or better *without* VICReg than *with* VICReg, H3 is falsified for that objective (this is highly expected for Reconstruction).

Ensure all 5 objectives are mathematically defined in your code comments and in the final report. Proceed to write `src/pre_registration.md` and initiate the Phase 4 runner.

---

