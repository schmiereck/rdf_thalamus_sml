# Research Manager Journal & Strategic State

## 1. High-Level Strategy & Trajectory
*   **Current Phase:** Phase 5 (Vector Semantics Investigation) is now RESOLVED. This concludes the primary gated phase plan of the HSUN research project.
*   **Active Direction:** With the completion of Phase 5, we have mapped the entire trajectory of the Hierarchical Sparse Universal Node (HSUN) architecture. The project has moved from the initial smoke tests (Phase 0) to establishing spatial/temporal properties (Phases 1–3), optimizing the local learning objective (Phase 4), and finally probing the internal semantic structure of the codes (Phase 5). The final phase has revealed that the high semantic consistency across spatial positions is an inherent structural prior of the shared-weight architecture rather than an emergent property of unsupervised training.
*   **Confidence Score:** 95% (Extremely high confidence, supported by rigorous control runs, cross-validation, and triggered pre-registered falsification criteria).

## 2. Strategic Insights & Lessons Learned
*   **Structural Inductive Bias Dominates Training:** A critical architectural finding is that weight-sharing combined with tanh bottlenecks and structured binary inputs natively partitions the representation space into consistent physical semantic dimensions (primarily magnitude and gradient). Unsupervised training (Reconstruction + VICReg) refines these boundaries but only contributes a marginal (+0.039) gain to cross-layer consistency.
*   **Failure of Explicit Anchoring:** Forcing specific dimensions to align with hand-designed semantic axes via auxiliary loss terms (anchoring) degrades representation consistency and interferes with the natural coordinate structure discovered by the network's projection geometry.
*   **Universal Node Viability:** The core vision of a single, universal node type is highly viable. Weight sharing across positions imposes zero expressivity penalty while guaranteeing spatial semantic uniformity. However, weights must remain axis-specific (spatial vs. temporal), as zero-shot spatial-to-temporal transfer was previously falsified (Phase 2).
*   **Anti-Collapse is the True Objective Gate:** As established in Phase 4, the choice of local predictive loss is secondary to the presence of a robust anti-collapse constraint (such as pooled VICReg), which is the dominant factor enabling discriminative representation transfer.

## 3. Loop & Bottleneck Detection
*   **Non-Local Loss Bottleneck:** Although the node architecture is strictly local, the best-performing anti-collapse mechanism (pooled VICReg) relies on batch-level statistics, which violates strict biological locality. Replacing this with a genuinely local anti-collapse mechanism (e.g., local lateral inhibition or running trace variance normalization) remains an unresolved bottleneck for fully decentralized hardware implementations.
*   **Semantic Saturation:** We observed that spatial layers are heavily dominated by low-level geometric statistics (magnitude and gradient). Higher-level concepts (periodicity, novelty) fail to register significantly until the deepest temporal layers, indicating that semantic depth is strictly bound to hierarchical depth.

## 4. Alternate Research Paths
*   **Decentralized Anti-Collapse:** Investigate Oja-like or Hebbian-style local variance stabilization rules that match VICReg performance without requiring batch-level covariance tracking.
*   **Continuous Physics Scaling:** Port the universal node architecture to a 1D physics engine to evaluate if the structural magnitude/gradient priors generalize when processing continuous, multi-object dynamics.