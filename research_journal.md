# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Phase 1 — Spatial Hierarchy without Time (Remains active as success criteria are unfulfilled)
*   **Active Direction:** Investigating alternatives to local reconstruction objectives to resolve representation collapse. The 80% downstream accuracy target was not met; moreover, all trained local reconstruction methods performed worse than the untrained baseline (51.0%). We must pivot our training objectives before advancing to temporal integration.
*   **Confidence Score:** 60% (Lowered from 85% because local reconstruction, the primary candidate objective, is empirically shown to be misaligned with preserving abstract downstream class features).

## 2. Strategic Insights & Lessons Learned
*   **Reconstruction-Classification Misalignment (Falsified Hypothesis):** Local reconstruction objectives optimize for pixel-level fidelity. In deep stacks with tight bottlenecks, this forces nodes to prioritize preserving high-frequency, non-categorical spatial variations rather than abstract class features, leading to representation degradation.
*   **The Random-Projection Baseline Advantage (Empirical Fact):** Untrained hierarchical networks with $\mathcal{N}(0, 1)$ initializations preserve class boundaries significantly better (51.0% accuracy) than reconstructive-trained networks (33.0% - 41.5% accuracy). This establishes that the spatial hierarchical architecture itself is representational; the training process must be redesigned to avoid destroying this inherent structure.
*   **Equivalence of Collapsed States (Skeptic Warning):** The finding that weight-sharing (P1-B) has "zero cost" compared to per-layer independent weights (P1-C) is a false positive of equivalence. Because both configurations collapsed to representations performing far worse than the untrained baseline, their performance equivalence is a symptom of mutual failure rather than a proof of shared-weight expressivity.

## 3. Loop & Bottleneck Detection
*   **The Reconstruction Tuning Trap:** The team initially attempted to resolve representation collapse by tuning L1 coefficients, learning rates, and embedding scales. The diagnostics of Iteration 002 proved this was an objective misalignment issue, not a hyperparameter optimization issue. We must block further optimization of standard local reconstruction losses on this task.
*   **Sparsity vs. Information Loss:** Enforcing structural sparsity via k-WTA (exactly 50% by construction) was successfully implemented but did not prevent accuracy degradation. Sparsity without contrastive or predictive constraints simply discards discriminative information faster when aligned to a reconstruction objective.

## 4. Alternate Research Paths
*   **Local Contrastive Learning (InfoNCE / JEPA style):** Instead of reconstructing inputs, nodes should maximize mutual information between neighboring spatial patches or across hierarchical layers.
*   **Predictive Latent Coding:** Shifting from *reconstructing* input states to *predicting* adjacent or higher-level latent states.
*   **Untrained Reservoir Stacking:** Utilizing the untrained hierarchical network as a fixed feature extractor (exploiting its 51.0% baseline capability) and moving directly to Phase 2 to evaluate temporal integration using random spatial projections.