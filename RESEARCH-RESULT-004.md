# RDF Milestone Review — Iteration 004 — Phase 2: Temporal Integration and the Spatial-to-Temporal Weight Transfer Audit

## 1. Pre-Declared Hypothesis and Falsification Criterion
We investigated two primary hypotheses in Phase 2:
1. **Hypothesis H1 (Zero-Shot Transfer):** A universal node encoder trained to predict local spatial structures (Phase 1 spatial JEPA) can be deployed zero-shot along the temporal axis (Phase 2) to capture temporal transitions without parameter retraining, achieving a temporal JEPA loss significantly lower than a random initialization ($L_{\text{trans}} / L_{\text{rand}} < 0.85$).
   - **Falsification Criterion F0/F1:** If the loss ratio $L_{\text{trans}} / L_{\text{rand}} \ge 0.95$ and downstream temporal classification accuracy shows no statistically significant improvement over random initialization, H1 is refuted.
2. **Hypothesis H2 (P2-D Temporal Viability):** A symmetric kernel-3 temporal node (P2-D: receiving $x_{t-2}, x_{t-1}, x_t$) trained from scratch with local JEPA is competitive with or superior to dedicated recurrent/feedback mechanisms (P2-B RNN, P2-C Feedback loop), while preserving the single-node architecture.
   - **Validation Criterion F2/F3:** P2-D temporal JEPA must achieve downstream classification accuracy statistically greater than the untrained baseline (confidence interval clears the baseline) and within 3 percentage points of the best dedicated temporal mechanism.

## 2. Experimental Protocol
- **Grid / Architecture:** Single spatial position, temporal sequences of length 32. Encoder dimension $d=16$, inputs are sequences of single-state vectors (periodic, irregular, random walk, long-range periodic).
- **Node Configurations:**
  - **P2-A:** Different tick rates per layer (pooling baseline).
  - **P2-B:** Internal recurrent state (locally trained GRU-like).
  - **P2-C:** Feedback loop (output at $t-1$ fed back).
  - **P2-D:** Three-temporal-slot node (kernel-3 spatial-temporal symmetry).
- **Optimization:** JEPA objective with VICReg regularization (variance, covariance constraints held constant). Trained for 100 epochs, Adam optimizer, 5 random seeds.
- **Control Group:** Untrained random-projection encoder (initialized with same distribution).

## 3. Observed Quantities
- **Zero-Shot Transfer Audit (H1):**
  - Spatial-to-Temporal Transferred Weight Loss: JEPA loss = 4.21 ± 0.12.
  - Random Initialization Weight Loss: JEPA loss = 4.25 ± 0.09.
  - Loss Ratio ($L_{\text{trans}} / L_{\text{rand}}$): 0.99 (fails the <0.85 threshold; triggers F0).
  - Downstream Classification Accuracy (Transferred): 57.2% ± 2.1%.
  - Downstream Classification Accuracy (Random Init): 58.0% ± 1.8%.
  - Accuracy Gap: -0.8 percentage points (statistically insignificant, $p > 0.5$; triggers F1).
- **Temporal JEPA on P2-D (H2):**
  - P2-D (Trained from scratch): Downstream classification accuracy = 65.33% ± 1.2%.
  - Untrained Baseline Accuracy: 58.0% ± 1.8%.
  - Performance Gap over Baseline: +7.33 percentage points (statistically significant, $p=0.012$; satisfies F2).
  - Comparison to Best Dedicated Mechanism (P2-A pooling): 67.0% ± 1.5%.
  - Gap to Best Mechanism: 1.67 percentage points (within the pre-registered 3.0pp threshold; satisfies F3).
  - P2-B (RNN) Accuracy: 61.2% ± 2.4%.
  - P2-C (Feedback) Accuracy: 62.1% ± 2.0%.

## 4. Verdict
- **Hypothesis H1 (Zero-Shot Transfer): REFUTED.** The experimental evidence demonstrates that spatially-trained weights provide no zero-shot advantage when applied to temporal sequences under our local JEPA objective.
- **Hypothesis H2 (P2-D Viability): CONSISTENT.** The symmetric 3-temporal-slot node, when trained with local temporal JEPA, successfully learns temporal sequence representations, outperforming more complex local recurrent (P2-B) and feedback (P2-C) mechanisms.

## 5. Construction-vs-Empirical Note
The failure of zero-shot weight transfer is an empirical finding. Because the temporal and spatial data distributions differ in their transitional dynamics (spatial structures represent static blob boundaries, whereas temporal sequences represent transitions and walks), the learned projection matrices do not align.
The success of P2-D is also empirical: it demonstrates that the same mathematical node construction (kernel-3, JEPA objective) can capture temporal features without requiring explicit recurrent memory cells or feedback paths, validating the structural flexibility of the universal node design.

## 6. Limitations
- This result does not show that spatial and temporal weights can never be shared if trained jointly (simultaneous spatial-temporal training was not tested).
- The evaluation is limited to low-dimensional sequences ($d=16$) and synthetic transition rules. The scalability of P2-D to complex natural temporal transitions remains untested.