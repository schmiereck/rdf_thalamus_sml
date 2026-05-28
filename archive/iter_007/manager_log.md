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

## Iteration 007 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
Phase 4 (Training Objective Comparison) on the P3-C spatiotemporal benchmark:
(H1) JEPA + pooled VICReg achieves test accuracy ≥ 55% (reproducing the 61.55%
     reference from iter_006 with relaxed floor).
(H2) No other objective (with OR without pooled VICReg) exceeds JEPA + pooled
     VICReg by ≥ 3 percentage points.
(H3) For most objectives, pooled VICReg improves accuracy over the VICReg-free
     version. Reconstruction may violate H3 (it natively resists collapse).

**Proposed Falsification Criterion:**
F1: JEPA + pooled VICReg achieves < 55% test accuracy (implementation broken).
F2: Any other objective exceeds JEPA + pooled VICReg by ≥ 3pp (JEPA not best).
F3: For any objective X (other than Reconstruction), accuracy(X without VICReg)
    ≥ accuracy(X with VICReg) — pooled VICReg does not generalise. F3 triggering
    for Reconstruction is expected and explicitly allowed.

**Proposed Method:**
Step 1: Fix src/run_phase4.py to address memory and timeout failures:
  a) Replace multiprocessing Pool with sequential execution in main process
  b) Add batched feature extraction for evaluation (process in chunks of 64
     instead of full 800-sample forward pass — avoids ~1 GB memory spike)
  c) Remove the redundant final_fwd forward pass on full training set;
     use metrics["pooled_std"] from last epoch instead
  d) Skip training loop for untrained baseline (just do evaluation)
  e) Add gc.collect() between runs to free memory
  f) Add --objectives CLI argument to run subset of objectives
  g) Change results CSV to append mode (support split runs)

Step 2: Run experiments in two sequential sub-agents to stay within timeout:
  Sub-agent 7.2 (retry): Fix code + run JEPA (10) + SFA (10) + untrained (5) = 25 runs
  Sub-agent 7.3: Run Hebbian (10) + Reconstruction (10) = 20 runs, append to CSV

Step 3: Sub-agent 7.4 loads all 45 results from phase_4/phase4_results.csv,
  runs statistical analysis (paired t-tests, Cohen's d), evaluates F1/F2/F3
  falsification criteria, and generates phase_4/REPORT.md.

Step 4: Update current_state.md with Phase 4 results and recommendation for
  default training objective going forward.

Files to modify: src/run_phase4.py (major refactor), src/pre_registration.md (update iteration number)
Files to create: phase_4/phase4_results.csv, phase_4/REPORT.md
Files to update: current_state.md

Experimental config (unchanged from pre-registration):
- P3-C architecture, d=16, d_out=16, 1,600 params
- 4 objectives × 2 VICReg conditions × 5 seeds = 40 trained + 5 untrained = 45 runs
- 30 epochs, batch=64, lr=1e-3, alpha=0.5
- Readout: spatial_pooled_then_flat (416 dims)
- Seeds: [42, 43, 44, 45, 46]

---

## Iteration 007 -> Planner [Strategic Guidance]

### Manager's Note: Strategic Guidance for Phase 4

While the proposed plan to optimize the execution of `src/run_phase4.py` is highly pragmatic and addresses the concrete hardware constraints, we must maintain strict scientific rigour. Under my supervision, you will execute this phase with high parameter hygiene and statistically robust criteria.

---

### 1. Parameter-Tuning Hygiene and the "Fair Comparison" Limit
You are comparing four fundamentally distinct unsupervised learning paradigms (JEPA, SFA, Hebbian, and Reconstruction) under a shared architectural and hyperparameter envelope ($lr=10^{-3}$, $30$ epochs, specific VICReg weights). 
* **The Trap:** If SFA or Hebbian performs poorly, it is highly likely a failure of this shared hyperparameter envelope rather than a fundamental refutation of the learning rule itself. 
* **The Discipline:** You must not write that a given objective is "fundamentally inferior." Instead, use precise, constrained language: *“Under the shared spatiotemporal hyperparameter envelope optimized for JEPA, method X does not yield a competitive representation.”* If you perform minor tuning of learning rates or regularizers for other methods to get them to function, this must be explicitly documented in the pre-registration and final report as a controlled hyperparameter sweep.

### 2. Rigour in Pre-Registration & Statistical Falsification
Your proposed Falsification Criterion **F3** is currently too weak:
* *Proposed:* `accuracy(X without VICReg) >= accuracy(X with VICReg)`
* *The Critique:* Comparing raw means over only 5 seeds is highly vulnerable to random seed noise. A marginal 0.2pp fluctuation could trigger or dodge falsification without scientific meaning.
* **The Demand:** Update your `src/pre_registration.md` to make **F3** statistically rigorous. Specify that the accuracy gap must be positive *and* either statistically significant ($p < 0.05$ via a paired t-test across seeds) or exceed $1.5\times$ the pooled standard error of the difference. If a null result occurs (i.e., VICReg does not statistically improve an objective), report it as an honest, valuable finding.

### 3. Execution & Robust Append-Mode Auditing
Since the execution is split across sub-agents to avoid timeout limits, there is a risk of data corruption or partial overwriting of `phase_4/phase4_results.csv`.
* Implement a strict schema validation check at the beginning of sub-agents 7.3 and 7.4.
* Ensure that the evaluation code asserts the presence of exactly 45 distinct, fully-completed runs (5 seeds $\times$ [1 untrained + 4 objectives $\times$ 2 VICReg conditions]) before generating the final report.

The Orchestrator will now automatically write your updated hypotheses and refined falsification criteria to `src/pre_registration.md`. You may proceed to execution under these strict guidelines.

---

