# RDF Scientific Pre-Registration

*   **Iteration:** 007
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
Phase 4 (Training Objective Comparison) on the P3-C spatiotemporal benchmark:
(H1) JEPA + pooled VICReg achieves test accuracy ≥ 55% (reproducing the 61.55%
     reference from iter_006 with relaxed floor).
(H2) No other objective (with OR without pooled VICReg) exceeds JEPA + pooled
     VICReg by ≥ 3 percentage points.
(H3) For most objectives, pooled VICReg improves accuracy over the VICReg-free
     version. Reconstruction may violate H3 (it natively resists collapse).

## 2. Falsification Criterion
F1: JEPA + pooled VICReg achieves < 55% test accuracy (implementation broken).
F2: Any other objective exceeds JEPA + pooled VICReg by ≥ 3pp (JEPA not best).
F3: For any objective X (other than Reconstruction), accuracy(X without VICReg)
    ≥ accuracy(X with VICReg) — pooled VICReg does not generalise. F3 triggering
    for Reconstruction is expected and explicitly allowed.

## 3. Proposed Method
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
*Created automatically by the RDF Orchestrator prior to iteration execution.*
