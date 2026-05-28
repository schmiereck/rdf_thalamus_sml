# Current Research State — HSUN Project
**Last updated:** After Phase 5 (iter_008, sub-agents 8.1–8.3)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. All five gated phases are now COMPLETE.

## Confirmed (with iter/sub-agent references)

### Phase 5 Resolution (iter_008)
1. **Within-layer semantic consistency is near-perfect (0.974)** for P5-A
   (Reconstruction + pooled VICReg), confirming shared W_enc produces
   position-consistent code semantics (iter_008, 8.3). F3 NOT triggered.

2. **Overall semantic consistency is 0.714** for P5-A, but untrained baseline
   is already 0.675. **Training gain = +0.039** (F2 TRIGGERED: gain ≤ 0.05).
   The consistency is predominantly structural (shared weights + tanh on binary
   inputs), not training-induced (iter_008, 8.3).

3. **Two dominant semantic axes**: Magnitude (R² up to 0.84 at temporal_0) and
   Gradient (R² up to 0.59). Variance, periodicity, and novelty are weakly
   represented only at the deepest temporal layer (iter_008, 8.3).

4. **Anchor regularization (P5-B) is counterproductive**: Anchored dims (0-4)
   consistency = 0.700 < P5-A overall (0.714). Free dims (5-15) = 0.738.
   F5 TRIGGERED (improvement = -0.014). The hand-designed probes conflict
   with the natural code structure (iter_008, 8.3).

5. **Disentanglement penalty (P5-C) has negligible effect**: Overall = 0.712
   vs P5-A 0.714. β=0.01 is too small to matter (iter_008, 8.3).

6. **Classification accuracy maintained**: P5-A=83.0%, P5-B=82.0%, P5-C=82.6%.
   F4 NOT triggered (P5-B ≥ 75%) (iter_008, 8.3).

7. **Cross-layer consistency**: P5-A=0.580, untrained=0.447. Training improves
   cross-layer alignment by +0.133 — the largest training effect on consistency
   (iter_008, 8.3).

8. **Untrained high-consistency paradox**: Xavier-initialized W_enc with tanh
   on binary inputs naturally produces outputs correlated with magnitude and
   gradient. This structural prior creates 0.944 within-layer consistency
   without training, but only 52.1% classification accuracy. Training sharpens
   discriminative power (→83%) with minimal consistency gain (iter_008, 8.3).

### Phase 4 Carry-Forward (iter_007)
- Reconstruction + pooled VICReg is the best training objective (83.00%)
- Pooled VICReg is the dominant anti-collapse factor across all objectives
- JEPA refuted as best objective (F2 triggered in Phase 4)

### Phase 3 Carry-Forward (iter_006)
- P3-C (universal weights) + pooled VICReg + spatial_pooled readout = 61.55%
- Universal parameter hypothesis SUPPORTED

### Phase 1-2 Carry-Forward (iter_002–004)
- JEPA local objective works spatially: 62.12% (d=8), 65.20% (d=16)
- P2-D temporal JEPA: 65.33% ± 2.74%
- Weight sharing has zero expressivity penalty
- Zero-shot spatial→temporal transfer is falsified; node type is universal, weights are axis-specific

## Refuted Hypotheses
- "Training produces significant semantic consistency gains over untrained baseline": REFUTED (F2, iter_008)
- "Anchor regularization improves consistency": REFUTED (F5, iter_008)
- "JEPA + pooled VICReg is the best training objective": REFUTED (iter_007)
- "Reconstruction natively resists collapse": REFUTED (iter_007)
- "Zero-shot spatial→temporal weight transfer works": REFUTED (iter_004)

## Current Best Results
- **Best classification**: Reconstruction + pooled VICReg, 83.00% ± 2.27%, 1,600 params (iter_007)
- **Within-layer consistency**: 0.974 (P5-A, iter_008)
- **Cross-layer consistency**: 0.580 (P5-A, iter_008)
- **Overall consistency**: 0.714 (P5-A, iter_008)
- **Dominant semantic axes**: Magnitude (R² up to 0.84), Gradient (R² up to 0.59)

## Files Created This Phase
- src/semantic_probes.py — 5 semantic probe computation + downsampling
- src/run_phase5.py — Phase 5 experiment runner
- src/phase_5/phase5_results.csv — 20 experiment results
- src/phase_5/REPORT.md — Comprehensive analysis report

## Open Questions (ordered by expected value)
1. **Does the structural prior (shared weights + tanh + binary inputs) generalize
   to continuous, higher-dimensional inputs?** The high untrained consistency
   may be specific to binary inputs where tanh saturation creates natural
   magnitude/gradient tuning.
2. **Can the architecture maintain 80%+ accuracy on richer input spaces (e.g.,
   1D physics sandbox with 128 RGB pixels, 3 objects)?** This is the stated
   long-term target.
3. **Would alternative activation functions (ReLU, GELU) change the balance
   between structural and training-induced consistency?**
4. **Is the two-axis dominance (magnitude, gradient) a feature or a limitation?**
   It may mean the architecture is limited to spatial-structural representations
   and cannot learn temporal-semantic features without deeper temporal processing.
5. **What would a Phase 6 (convergence) synthesis conclude about the overall
   viability of the universal node architecture?** All five gated phases are
   now complete.

## Project Status
All five gated phases (0–4) are COMPLETE. The project is ready for a
convergence phase that synthesizes findings across all phases and determines
whether the HSUN architecture is viable for its stated long-term goals.
