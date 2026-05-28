# RDF Milestone Review — Iteration 006 — Resolution of Phase 3 (Unified Spatiotemporal Grid)

## 1. Pre-Declared Hypothesis and Falsification Criterion
The hypothesis formulated for Phase 3 was that a single, universal node type with fully shared weights across both spatial and temporal axes (P3-C) can learn representation features that improve downstream spatiotemporal classification.
The pre-declared falsification criteria (revised in Iteration 6 pre-registration to account for readout modifications) were:
1. Downstream classification accuracy gain of trained P3-C over untrained P3-C under the identical readout mechanism must be >= 8.0 percentage points (pp).
2. The classification improvement must be statistically significant (p < 0.05 under a two-tailed t-test over 5 seeds).
3. Effect size Cohen's d >= 1.0.

## 2. Experimental Protocol
- **Architecture:** P3-C (Unified spatiotemporal grid, 1,600 parameters, weight sharing across space, time, and layers).
- **Dataset:** 4-class spatiotemporal dataset (moving_blob, expanding_blob, periodic_st, object_permanence). 16 spatial inputs, 32 time steps. Train set: 200 sequences per class (800 total). Test set: 100 sequences per class (400 total).
- **Training Parameters:** 30 epochs, batch size 64, Adam optimizer, learning rate 1e-3.
- **Loss Formulation (Condition D):** Joint Embedding Predictive Architecture (JEPA) loss combined with a Pooled VICReg loss (variance weight lambda_var=25, covariance weight lambda_cov=25) applied directly to the pooled representation.
- **Control Run (Untrained):** Network weights initialized randomly and kept frozen; the same feature extraction and downstream classification pipeline were applied.
- **Readout:** Both trained and control runs used the `spatial_pooled_then_flat` readout mechanism (averaging over space but retaining the temporal sequence dimension) to prevent the loss of high-frequency temporal dynamics.
- **Evaluation:** A linear probe (Logistic Regression) trained on the extracted representation to classify the 4 spatiotemporal patterns. Averaged over 5 independent random seeds (42–46).

## 3. Observed Quantities
- **Downstream Classification Accuracy:**
  - Trained P3-C (Condition D): 61.55% +/- 1.48%
  - Untrained P3-C baseline: 52.10% +/- 2.37%
  - **Absolute Accuracy Gain:** +9.45 percentage points
- **Statistical Significance:**
  - p-value: 0.013
  - Cohen's d: 1.91
- **Representation Variance:**
  - Average per-dimension standard deviation of pooled representation: 0.072 (Untrained) -> 0.130 (Condition D) (an increase of +80.3%).
  - Mean-squared VICReg variance loss: decreased to active range (from 0.00 to 0.87).

## 4. Verdict
**Consistent** with the hypothesis. 
The universal parameter hypothesis (P3-C) is supported. The network successfully learned spatiotemporal representations that provide a +9.45pp classification benefit over its untrained counterpart, clearing all pre-registered quantitative thresholds (gain >= 8pp, p < 0.05, d >= 1.0).

## 5. Construction-vs-Empirical Note
The increase in per-dimension standard deviation is partly driven by the construction of the Pooled VICReg loss, which explicitly penalizes low-variance representations. However, the downstream classification accuracy of 61.55% (compared to 52.10% untrained) is an empirical result. This shows that preventing variance collapse at the representation level preserves discriminative features that are highly useful for linear classification of physical spatiotemporal behaviors.

## 6. Limitations
1. This result does not demonstrate that local VICReg alone can prevent collapse when applied globally without pooling adjustments; the gradient dilution effect (1/28672 scaling factor for intermediate steps vs. 1/64 at pooled level) remains an intrinsic limitation of training deep/unfolded architectures using uniform local losses without normalization.
2. The classification performance of 61.55% is still far from perfect classification (100%). In particular, high-frequency temporal patterns like `periodic_st` remain difficult to resolve with a linear probe.
3. The feature extraction relies on preserving temporal resolution in the readout (`spatial_pooled_then_flat`). If representations are fully collapsed temporally (global average pooling), accuracy degrades significantly.