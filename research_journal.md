# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Transitioning from Phase 4 (Training Objective Comparison) to Phase 5 (Vector Semantics Investigation).
*   **Active Direction:** Phase 4 has been completed, resulting in a crucial paradigm shift. While JEPA was hypothesized to be the optimal local learning objective, it was significantly outperformed by Reconstruction + pooled VICReg (83.00%) and Slow Feature Analysis (SFA) + pooled VICReg (82.15%). The pre-registered falsification criterion (F2) was triggered, refuting the hypothesis that JEPA is the superior objective. The project now advances to Phase 5 to investigate if the dimensions of these high-performing representations (Reconstruction and SFA) carry consistent physical semantics across spatial positions and hierarchical layers.
*   **Confidence Score:** 90% (High confidence, established by rigorous 5-seed cross-validation and explicit control groups).

## 2. Strategic Insights & Lessons Learned
*   **Objective Hierarchy:** The choice of local objective matters less than the prevention of representation collapse. Without pooled VICReg, all objectives collapse to random-level performance.
*   **Information Preservation vs. Prediction:** Reconstruction forces the node to act as a high-fidelity bottleneck, retaining static discriminative features that are discarded by predictive objectives (like JEPA) which prioritize future state transitions.
*   **Temporal Slowness Prior:** Enforcing temporal slowness via SFA serves as an exceptionally strong regularizer for sequence classification, matching reconstruction performance without requiring an explicit decoding/reconstruction step.
*   **Hebbian Insufficiency:** Simple Hebbian learning rules failed to establish discriminative spatiotemporal representations, showing no statistically significant improvement even when regularized with VICReg.

## 3. Loop & Bottleneck Detection
*   **The Representation Collapse Loop:** Fully resolved via the pooled VICReg loss constraint.
*   **The Readout Bottleneck:** Bypassed using `spatial_pooled_then_flat` readout, which successfully preserves high-frequency temporal sequence information.
*   **Next Potential Bottleneck (Phase 5):** High classification accuracy does not guarantee semantic consistency or disentanglement. A highly accurate reconstruction-based node might achieve its score through high-entropy random coordinate mappings (acting as a random projection hash). Phase 5 must rigorously test whether individual dimensions correlate consistently with physical semantic axes (gradients, activity, variance) across layers and positions.

## 4. Alternate Research Paths
*   **Reconstruction-SFA Hybrid:** Test whether a joint loss minimizing reconstruction error and temporal slowness produces representations that are both highly discriminative and temporally coherent.
*   **Purely Local Slowness with Gradient Scaling:** Explore if scaling the local SFA gradient can achieve stable, uncollapsed training without relying on any pooled global loss terms.