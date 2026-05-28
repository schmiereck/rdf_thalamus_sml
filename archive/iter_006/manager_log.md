# Research Manager Log - Iteration 006

## Iteration 006 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
The Phase 3 failure (P3-C gain of only 1.15pp over untrained, p=0.648, Cohen's d=0.22)
was caused by omission of VICReg collapse-prevention constraints from the training
objective. In iter_003, JEPA was trained WITH VICReg (variance: std ≥ 1 per dimension;
covariance: off-diagonal penalty), achieving +16pp over untrained. In iter_005,
JEPA was trained WITHOUT VICReg, causing representation collapse (loss decreases
but codes become invariant). Adding VICReg back to P3-C's JEPA training will
restore discriminative representations, achieving ≥8pp gain over untrained
baseline on spatiotemporal 4-class classification, with p < 0.05 and
Cohen's d ≥ 0.8.

**Proposed Falsification Criterion:**
If P3-C with VICReg fails to achieve ≥8pp gain over untrained baseline
(i.e., test accuracy < 50.85%, given untrained ≈ 42.85%), OR the gain is
not statistically significant (p ≥ 0.05), OR the effect size is small
(Cohen's d < 0.8), then the problem is genuinely architectural — joint
spatial-temporal optimization fundamentally prevents JEPA from producing
discriminative representations, even with collapse prevention. This would
mean Phase 3's failure is NOT merely a training regression.

**Proposed Method:**
MINIMAL BUG-FIX ITERATION — same architecture, same protocol, add VICReg back.

Step 1: Examine iter_003's JEPA+VICReg implementation (src/ files from
archive/iter_003/) and iter_005's JEPA-only implementation to confirm
the VICReg omission. Document the diff.

Step 2: Implement VICReg loss module (src/vicreg_loss.py) with:
  - Variance term: max(0, 1 - std(z_dim)) per dimension, averaged
  - Covariance term: off-diagonal elements of cov(z) squared, averaged
  - Weight coefficients λ_var=25, λ_cov=1 (matching iter_003 settings
    or standard VICReg defaults)

Step 3: Modify the training loop (src/run_phase3_vicreg.py or
src/run_phase3_optimized.py) to add VICReg loss to the JEPA objective:
  total_loss = jepa_loss + λ_var * var_loss + λ_cov * cov_loss
  Applied to the final pooled representation (same as iter_003).

Step 4: Run experiments with IDENTICAL protocol to iter_005:
  - P3-C (shared weights, unified node): 5 seeds × 30 epochs
  - P3-A (separate spatial+temporal) with VICReg: 5 seeds × 30 epochs
    (control: does VICReg fix all variants or only P3-C?)
  - Untrained baseline: 5 seeds (or reuse iter_005 baseline: 42.85%)
  - Config: 200 train/class, 100 test/class, batch=64, lr=1e-3

Step 5: Compute metrics:
  - Mean test accuracy ± std for P3-C+VICReg and P3-A+VICReg
  - Gain over untrained (pp)
  - Two-sample t-test p-value
  - Cohen's d effect size
  - Per-dimension variance diagnostic (confirm VICReg is active: 
    std per dim should be ≥ 1.0 after training)

Step 6: Falsification decision:
  - If P3-C+VICReg gain ≥ 8pp, p < 0.05, d ≥ 0.8 → regression confirmed,
    Phase 3 result is revised upward, proceed to Phase 4
  - If P3-C+VICReg gain < 8pp → genuine architectural problem,
    need to investigate joint spatiotemporal optimization fundamentally

Files to create/modify:
  - src/vicreg_loss.py (NEW — VICReg loss implementation)
  - src/run_phase3_vicreg.py (NEW — runner with VICReg, based on run_phase3_optimized.py)
  - src/pre_registration.md (UPDATE — with this iteration's hypothesis)
  - phase_3/REPORT_vicreg.md (NEW — results and analysis)

---

## Iteration 006 -> Planner [Strategic Guidance]

# Manager's Note: Strategic Guidance for Iteration 6

To maintain scientific rigour and systematically address the performance regression observed in Phase 3, you are authorized to proceed with this **minimal bug-fix iteration** to validate the collapse-prevention hypothesis. 

Apply the following constraints to ensure empirical validity:

### 1. Strict Parameter-Tuning Hygiene & Reference Preservation
You suspect that the omission of the variance/covariance constraint (VICReg) caused representation collapse. To prove this empirically, you must not "tune" the VICReg hyperparameters to fit the classification scores:
*   **Retrieve and replicate:** Search the codebase/history of Iteration 3 (Phase 1) and extract the exact hyperparameters ($\lambda_{\text{var}}$, $\lambda_{\text{cov}}$, $\mu_{\text{sim}}$ or equivalent weights) used there. 
*   **No Post-Hoc Sweeps:** You must run the experiments with these historically validated hyperparameters. If you must adjust them, you must state the physical/mathematical reason *before* observing the downstream classification accuracy. Treating a hyperparameter sweep as a "success" when only one specific seed/ratio works is a violation of our tuning hygiene.

### 2. Mechanistic Verification of Collapse (The Diagnostic Test)
Do not rely solely on the final classification accuracy to declare success. You must prove the *mechanism* of the failure and the fix:
*   **Measure Code Variance:** For both the baseline (Iter 5 checkpoint, if available, or a reconstructed no-VICReg run) and the new VICReg run, calculate and report the average standard deviation per dimension of the final pooled representations across the test set.
*   **Falsification of the Collapse Hypothesis:** If the representation variance in Iteration 5 was already high ($\text{std} \gg 10^{-3}$ per dimension) and not collapsed, then the "invariance collapse" hypothesis is false, even if adding VICReg happens to nudge the accuracy. We require proof that VICReg actually prevents a demonstrated collapse.

### 3. Pre-Registration Mandate
Before running the pipeline, ensure that your exact hypothesis, the specific mathematical formulations of the variance/covariance losses, the expected baseline, and the $\ge 8\text{pp}$ gain target (yielding a threshold of $\ge 50.85\%$ accuracy) are written to `src/pre_registration.md`. The sub-agents must read and strictly adhere to this file during execution. 

Keep your language disciplined: do not report a successful classification run as a "monumental breakthrough"—it is a verification of a definitional collapse-prevention constraint in joint spatiotemporal optimization.

---

