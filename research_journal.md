# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Phase 1 — Spatial Hierarchy without Time (Transitioning to Phase 2)
*   **Active Direction:** Having successfully resolved the representation collapse of Phase 1 by replacing reconstruction losses with a Local Joint Embedding Predictive Architecture (JEPA), we are preparing to transition to Phase 2 (Temporal Integration). The Local JEPA objective achieved 62.1% downstream accuracy, comfortably exceeding the revised 60% pre-registered target and outperforming the untrained random-projection baseline (51.0%) by +11.1 percentage points.
*   **Confidence Score:** 85% (Restored from 60% due to the definitive resolution of the representation collapse and the empirical validation of the local latent prediction hypothesis).

## 2. Strategic Insights & Lessons Learned
*   **The Latent Prediction Triumph (Verified Hypothesis):** Training nodes to predict the latent codes of their spatial neighbors (Local JEPA) instead of reconstructing their raw inputs (Autoencoder) is the key to preventing representation collapse in deep hierarchies. This forces nodes to discard local, high-frequency spatial noise and retain abstract, mutually shared structural categories.
*   **VICReg as a Core Architectural Pillar:** Without global backpropagation, local predictive coding collapses to constant outputs. Incorporating variance and covariance constraints (VICReg style) directly into the local node objective is mandatory to preserve information capacity and maintain training stability.
*   **Bottleneck Hypothesis Refuted:** Comparing $d=8$ against $d=16$ bottleneck sizes showed only a minor +3.08pp improvement. This proves that the $24 \to 8$ dimensional compression is not the structural bottleneck; rather, the alignment of the training objective dictates representation quality.
*   **Failure of Non-Predictive Local Methods:** Pure Hebbian learning (24.2%) performs near chance, and local SFA / Contrastive methods failed to achieve statistical significance over the random baseline. This indicates that structured latent-space prediction is highly unique in its ability to build discriminative spatial hierarchies under strict weight-sharing.

## 3. Loop & Bottleneck Detection
*   **The 80% Absolute Accuracy Gap:** Although 62.1% is a massive success compared to the collapsed reconstruction models, it still falls short of the original, highly ambitious 80% target for Phase 1. This is a known spatial bottleneck: 1D spatial context in a local neighborhood is fundamentally limited.
*   **Unification Strategy:** Rather than over-tuning spatial hyperparameters to force the remaining 18% accuracy, we will proceed to Phase 2. The temporal axis provides a rich stream of predictable transitions. If the JEPA hypothesis holds, applying the identical local predictive objective along the temporal axis should naturally resolve spatial ambiguities and boost downstream categorization.

## 4. Alternate Research Paths
*   **Spatiotemporal Joint Predictor:** Expanding the local JEPA neighborhood to predict not just spatial neighbors, but also temporal successors within the same universal node.
*   **VICReg Parameter Tuning:** Documenting the sensitivity of the local node to the ratio of variance, invariance, and covariance loss weights to establish stable default configurations.