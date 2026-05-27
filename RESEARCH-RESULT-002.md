# RDF Milestone Review — Iteration 002 — Null Result on Local Reconstruction for Spatial Hierarchy

## 1. Pre-Declared Hypothesis and Falsification Criterion
- **Hypothesis:** A hierarchical, stacked universal node architecture (kernel-3, stride-1) trained via unsupervised local reconstruction objectives (e.g., Sparse Autoencoders, local Predictive Coding) can construct representations that capture spatial category structures, achieving $\ge 80\%$ linear-probe accuracy on five structured input classes.
- **Falsification Criterion:** The hypothesis is refuted if trained models do not exceed the classification performance of an untrained (randomly initialized) baseline network, or if no tested local reconstruction objective exceeds $60\%$ accuracy.

## 2. Experimental Protocol
- **Input Data:** 16-bit binary 1D patterns belonging to 5 structured classes: (1) uniform random, (2) single-blob, (3) two-blob, (4) periodic patterns (periods 2, 3, 4), (5) mixed noise overlays.
- **Architecture:** 3-layer hierarchical 1D network. Universal nodes of kernel-3, stride-1. 
  - Input layer 1: 16 pixels. Layer 1 outputs: 14 nodes.
  - Layer 2 outputs: 12 nodes.
  - Layer 3 outputs: 10 nodes.
  - Dimension $d=8$ for all node outputs. Nodes in layers 2 and 3 map a $3 \times 8 = 24$-dimensional input triplet to an $8$-dimensional output vector.
- **Parameters & Variations:**
  - P1-B (Strict weight sharing across all layers and positions).
  - P1-C (Per-layer independent weights, serves as upper-bound comparison).
  - Training regimes: Progressive (layer-by-layer) vs. Simultaneous (all layers trained together).
  - Objectives: L1-regularized Sparse Autoencoder, k-WTA structural sparse autoencoder, local Predictive Coding with lateral inhibition.
  - Optimization: Adam or SGD, weights initialized with $\mathcal{N}(0, 1)$, evaluated over 5 random seeds.
- **Control Run:** An untrained hierarchical network with identical architecture, initialized with random weights $\mathcal{N}(0, 1)$, evaluated using the same downstream linear probe.

## 3. Observed Quantities
- **Untrained Baseline (Control):** $51.0\% \pm 0.0\%$ linear-probe accuracy.
- **Progressive Reconstruction (P1-B):** $33.5\% \pm 1.2\%$ accuracy.
- **Simultaneous Reconstruction:** $41.5\% \pm 0.8\%$ accuracy.
- **Predictive Coding with Lateral Inhibition:** $38.2\% \pm 1.5\%$ accuracy.
- **Weight-Sharing Penalty Comparison:** P1-B (shared: $33.5\%$) vs. P1-C (independent: $33.2\%$). Difference: $+0.3\%$ (within statistical margin).
- **Sparsity:** k-WTA variants successfully enforced exactly $50\%$ structural sparsity (enforced by construction of the selection rule), but downstream accuracy remained low ($31.8\%$).

## 4. Verdict
**Refuted.** Unsupervised training via local reconstruction objectives actively degrades representational quality compared to a random initialization control. None of the local reconstruction or predictive coding variants exceeded the $60\%$ threshold, and all performed significantly worse than the $51.0\%$ untrained baseline.

## 5. Construction-vs-Empirical Note
- The equivalence of weight-shared (P1-B) and independent (P1-C) model performance ($33.5\%$ vs $33.2\%$) is not an empirical proof of the "zero cost" of universal-node constraints. Because both configurations collapsed to representations that perform far worse than the untrained baseline, this equivalence is an artifact of training failure rather than a demonstration of shared-weight expressivity.
- The $51.0\%$ accuracy of the untrained model is a genuine empirical finding, showing that random hierarchical convolutions act as a decent random-projection reservoir that retains class separation before any training-induced collapse.

## 6. Limitations
- This finding is limited to local *reconstruction-based* objectives (predictive coding and autoencoders trying to reconstruct their inputs). It does not rule out local *contrastive* (e.g., InfoNCE), *predictive* (predicting adjacent patches or future states), or *slow feature analysis* objectives.
- The investigation used a small node dimension ($d=8$). It remains unknown if scaling $d$ prevents representation collapse under reconstruction objectives.