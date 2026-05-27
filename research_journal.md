# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Phase 2 — Temporal Integration at a Single Node (Completed) → Transitioning to Phase 3 — Unified Spatiotemporal Grid.
*   **Active Direction:** Based on Phase 2 results, we are transitioning to Phase 3. The strict hypothesis of zero-shot spatial-to-temporal weight transfer has been refuted. However, the viability of the universal node *type* has been validated: the symmetric 3-slot node (P2-D) trained from scratch with temporal JEPA is highly competitive, outperforming recurrent and feedback baselines. Therefore, in Phase 3, we will construct a unified spatiotemporal grid using identical P2-D style kernel-3 nodes, but we will allow weights to be learned axis-specifically (spatial vs. temporal axes) using local JEPA.
*   **Confidence Score:** 88% (Increased due to resolving the temporal integration architecture and establishing that explicit recurrent state cells are unnecessary for temporal sequence modeling within the HSUN framework).

## 2. Strategic Insights & Lessons Learned
*   **Axis-Specific Weight Requirements (Refuted Transfer Hypothesis):** Even though the mathematical node structure is fully universal (kernel-3 input slots mapped to dimension $d$), the optimal weights are highly axis-specific. Zero-shot deploying spatially-trained projection matrices onto temporal sequences yields a loss ratio of 0.99 compared to random initialization, proving that spatial and temporal patterns in our setup do not share isomorphic geometric structures.
*   **Symmetric Context is Superior to Recurrence:** P2-D (three-temporal-slot sliding window) outclassed both P2-B (local RNN) and P2-C (feedback loop) by +4.13pp and +3.23pp respectively. This indicates that local recurrence is prone to instability and optimization bottlenecks under self-supervised objectives, whereas feedforward temporal windows trained via JEPA exhibit stable convergence and superior category representation.
*   **The Next-Step Similarity Paradox:** Encoders trained via temporal JEPA showed lower next-step cosine similarity but higher classification accuracy than untrained baselines. This proves that JEPA does not simply act as a temporal low-pass filter (smoothing sequential states); rather, it actively partitions the latent space into predictive, structurally distinct categories.

## 3. Loop & Bottleneck Detection
*   **The Weight Transfer Blindspot:** We must avoid trying to force a single, globally shared weight matrix across both spatial and temporal axes in Phase 3. Expecting one weight set to handle both spatial relationships and temporal transition dynamics without axis specialization is a proven bottleneck. The "universal node" concept refers to structural and objective uniformity, not parameter identity across axes.
*   **Mitigation Strategy for Phase 3:** We will design the spatiotemporal grid to employ identical node types (kernel-3) and training losses (JEPA + VICReg), but with independent parameter sets for the spatial layers and temporal layers (P3-B anisotropic grid style).

## 4. Alternate Research Paths
*   **Joint Spatiotemporal Optimization:** Investigating if training a single node simultaneously on both spatial and temporal sequence streams (mixed batches) forces the discovery of a unified weight set that survives cross-axis deployment.
*   **Temporal VICReg Calibration:** Fine-tuning the covariance regularization strength specifically on temporal transitions to prevent representation collapse in deeper temporal hierarchies.