# Current Research State — HSUN Project
**Last updated:** After Phase 1 completion (iter_2, sub-agents 2.1–2.3)

## Goal
Investigate an architecture for unsupervised representation learning built from
a single, universal node type. Phase 1 (Spatial Hierarchy) is now complete.

## Confirmed (with iter/sub-agent references)

1. **Weight sharing has ZERO expressivity penalty** (iter_2, 2.2):
   - P1-B (cross-layer sharing, d=8): 33.52% ± 3.05%
   - P1-C (independent weights, d=8): 33.24% ± 2.51%
   - Gap: −0.28pp (well within 15pp threshold)
   - This is the most POSITIVE finding for the universal-node hypothesis

2. **Reconstruction training is misaligned with classification** (iter_2, 2.2, 2.3):
   - ALL trained configs (P1-A through P1-E, k-WTA, predictive coding, strong L1)
     achieve 33–42% accuracy, below the untrained baseline at ~48–51%
   - The autoencoder optimizes for pixel-level reconstruction, not category structure
   - Simultaneous training (41.5%) outperforms progressive training (33.5%)

3. **d_out = 3*d creates no bottleneck (BUG, now fixed)** (iter_2, 2.1→2.2):
   - Original: Encoder 24→24, Decoder 24→24 (identity-like, no compression)
   - Corrected: Encoder 24→8, Decoder 8→24 (true 3:1 bottleneck)
   - Original + tiny embeddings → representation collapse (all weights → 0)
   - Corrected + Normal(0,1) embeddings → no collapse but accuracy still low

4. **L1 sparsity is incompatible with discriminative representations** (iter_2, 2.2):
   - L1 λ=0.002 with Normal(0,1) embeddings → sparsity = 0.03% (ineffective)
   - Stronger L1 doesn't help accuracy (diagnostic Exp5: 37.1%)
   - Hyperparameter search: accuracy-sparsity trade-off is fundamental

5. **k-WTA successfully enforces structural sparsity** (iter_2, 2.2):
   - P1-B-kwta with k=4/8: sparsity = 50.0% (exactly), accuracy = 35.7%
   - Sparsity is guaranteed by construction, independent of training dynamics
   - Does NOT solve the accuracy problem (still below untrained baseline)

6. **Predictive coding with lateral inhibition creates sparsity but unstable** (iter_2, 2.3):
   - Mean accuracy: 38.2%, sparsity: 72.5%
   - High variance across seeds: 20%–53% accuracy
   - Lateral inhibition suppresses weakly-activated neurons, creating sparsity
   - But also suppresses useful discriminative information

7. **The untrained baseline is a strong reference** (iter_2, 2.2, 2.3):
   - Original architecture (tiny embeddings): ~30% accuracy
   - Corrected architecture (Normal embeddings): ~48% accuracy
   - Random flat embedding (16×8=128 features): ~43% accuracy
   - Random 3-layer hierarchy: ~51% accuracy (best non-trained result)
   - This means 51% is achievable with zero training — any useful training
     should IMPROVE on this, not degrade it

8. **P1-D (d=4) is too small** (iter_2, 2.2):
   - Accuracy: 23.9% (near chance), confirms d=4 bottleneck is too aggressive
   - Supports d=8 as minimum viable per-slot dimension

9. **P1-E (d_out=16, wider) slightly outperforms P1-B (d_out=8, recursive)** (iter_2, 2.2):
   - P1-E: 35.2% vs P1-B: 33.5% (+1.7pp)
   - Wider code dimension provides slightly more capacity
   - But still below untrained baseline

## Refuted Hypotheses
- Phase 1 pre-registered hypothesis FALSIFIED on multiple counts:
  (1) P1-B accuracy < 80% (observed: 33.5%)
  (2) Trained P1-B − untrained < 15pp (observed: −14.9pp)
  (3) P1-B sparsity < 50% with L1 (observed: 0.03%)
- The reconstruction + L1 training objective cannot produce discriminative
  sparse codes in a hierarchical autoencoder with 3:1 bottleneck compression

## Current Best Result
- **Untrained hierarchical encoder** (Normal(0,1) embeddings, d=8, d_out=8):
  48.4% accuracy, but no sparsity (0.04%)
- **P1-B-kwta** (cross-layer sharing, k-WTA k=4):
  35.7% accuracy, 50.0% sparsity — the only config meeting sparsity criterion
- **Simultaneous training** (diagnostic):
  41.5% accuracy — best trained result, but still below untrained

## In Progress
- Phase 4 training objectives should be tested NEXT (moved earlier from plan)
- Need a training objective that PRESERVES discriminative information
  while enforcing sparsity

## Open Questions (ordered by expected value)
1. **Can any non-reconstruction local objective reach ≥60%?** This is the
   most critical question. If no local objective can beat random projections,
   the HSUN architecture requires a fundamentally different approach.
2. **Is 80% accuracy achievable with any local training?** The untrained
   baseline at 51% sets an upper bound for random projections. We need to
   determine if supervised or semi-supervised signals are necessary.
3. **Can simultaneous training + better objective close the gap?**
   Simultaneous training (41.5%) significantly outperforms progressive (33.5%).
   Combined with a contrastive or Hebbian objective, could we reach ≥60%?
4. **Does increasing d improve accuracy?** d=8 gives 80 top-layer features.
   d=16 would give 160 features — does the wider bottleneck help?
5. **Can lateral inhibition + simultaneous training work together?**
   Predictive coding achieved 72% sparsity but unstable. Simultaneous training
   gave best accuracy. Can they be combined?
6. **Is tanh the right activation for the bottleneck?** ReLU might allow
   more expressive sparse codes (natural sparsity from ReLU dead neurons).
7. **Spatial-temporal symmetry (Phase 2):** Can a kernel-3 node trained
   spatially be applied temporally without retraining? This remains untested.

## Critical Design Decisions Made This Phase
- **d_out = d (recursive form):** Confirmed as correct (not 3*d)
- **Embedding: Normal(0,1):** Confirmed as necessary (not Uniform[-0.01,0.01])
- **Simultaneous training > progressive training:** For this task/architecture
- **k-WTA > L1 for sparsity:** Structural sparsity is more reliable than L1

## Files Created This Phase
- src/node.py — UniversalNode with encoder/decoder, L1, k-WTA, gradient check
- src/hierarchical_encoder.py — 3-layer hierarchical encoder with weight sharing
- src/dataset_phase1.py — 5 structured 16-bit datasets
- src/eval_phase1.py — Linear probe evaluation module
- src/run_phase1.py — Experiment runner (7 configs × 5 seeds)
- src/diagnostic_phase1.py — 5 diagnostic experiments
- src/pre_registration.md — Updated with Phase 1 hypothesis + Manager's criteria
- phase_1/results.csv — Raw experimental results
- phase_1/diagnostic_results.csv — Diagnostic experiment results
- phase_1/REPORT.md — Full comparison report
