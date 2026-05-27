Generate the scientific report in `phase_1/REPORT.md`.

It must include:
1. **Title**: HSUN Phase 1 — Spatial Hierarchy without Time: Full Experimental Report
2. **Summary Table**:
   - Show columns: Configuration, Description, n_params, Test Accuracy (mean ± std), Sparsity (mean ± std), Layer 0 Recon MSE (mean), Pass/Fail on Success Criteria.
   - Include rows: P1-A, P1-B, P1-C, P1-D, P1-E, Untrained-P1-B.
3. **Primary Hypothesis Evaluation**:
   - Assess whether P1-B achieved accuracy >= 80%. (It failed, performing at chance level).
   - Assess the P1-B vs P1-C gap (which is very small, ~0.68pp, but both are at chance level).
4. **Untrained Baseline Comparison**:
   - Assess whether trained P1-B outperformed the untrained baseline by >= 15pp. (It failed, trained P1-B is actually ~11.4pp worse than untrained!).
5. **Code Sparsity Evaluation**:
   - Assess whether P1-B code sparsity was >= 50%. (It passed, mean was 70.0%).
6. **Detailed Gap & Dimension Analysis**:
   - Compare P1-D (smaller d=4) vs P1-B (d=8).
   - Compare P1-E (wider output d_out=16) vs P1-B.
   - Compare P1-A (within-layer sharing) vs P1-B (cross-layer sharing).
7. **Rigorously explain the representation collapse phenomenon**:
   - Explain why the default embedding initialization scale `Uniform[-0.01, 0.01]` led to the failure.
   - Detail how the tiny input magnitude led to tiny reconstruction loss, which was completely dominated by the L1 sparsity penalty (`l1_lambda = 0.002`), driving all parameters and activations to zero.
   - Contrast this with the Untrained baseline which avoids training, retains its random initialization, and thus preserves informative random projections achieving ~30% accuracy.
   - Reference the hyperparameter search we conducted, where increasing the embedding scale to `Normal(0, 2.0)` prevented collapse and boosted accuracy to ~53.8%, but showed a stark trade-off where high-accuracy configurations had near-zero sparsity.
8. **Final Conclusion**:
   - Explicitly declare whether the Phase 1 hypothesis was supported or FALSIFIED (it was FALSIFIED on multiple counts).
   - Discuss the implications for Phase 2 (Temporal Hierarchy) and how we must design the scaling of input embeddings and sparsification dynamics to make local hierarchical learning viable.

Save the file and verify its contents.