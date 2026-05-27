# RDF Scientific Pre-Registration

*   **Iteration:** 004
*   **Pre-Registration File:** src/pre_registration.md

## 1. Hypothesis
A UniversalNode (kernel-3, d=16) trained with JEPA on spatial data produces weights
that transfer to the temporal axis without retraining: when applied to temporal
triplets (state_{t-2}, state_{t-1}, state_t), the spatially-trained node yields
periodic-vs-random classification accuracy ≥10pp above an untrained-weight baseline.

Additionally, a P2-D node trained from scratch on temporal data with JEPA achieves
≥60% periodic-vs-random classification accuracy and ≥55% next-step prediction accuracy,
confirming the JEPA objective works along the temporal axis.

The P2-D approach (three-temporal-slot node) is architecturally identical to the
spatial node, differing only in which axis provides the three inputs. Success here
would validate the core universal-node claim: one node type, one set of weights,
applicable along any axis.

## 2. Falsification Criterion
The hypothesis is falsified if ANY of the following hold:

F0 (Zero-Shot Transfer JEPA Loss): If Loss_spatial_trained / Loss_untrained >= 0.85 on temporal JEPA loss, the spatial -> temporal transfer has FAILED. This is the most rigorous test of whether spatially-trained weights encode general local-pattern structure vs. axis-specific structure.

F1 (Transfer failure): Spatially-trained weights applied temporally yield
periodic-vs-random classification accuracy ≤5pp above the untrained-weight
temporal baseline. This would mean the node learns axis-specific (spatial)
structure, not a general local-pattern operation.

F2 (Temporal JEPA failure): P2-D trained from scratch on temporal data with
JEPA fails to reach ≥60% periodic-vs-random classification. This would mean
the JEPA objective does not generalize to temporal structure.

F3 (P2-D non-competitiveness): P2-D (temporal training) performs ≥20pp worse
than the best alternative (P2-A/B/C) on the classification task. This would
mean the kernel-3 temporal node is fundamentally inferior to dedicated temporal
mechanisms, undermining the universal-node architecture.

## 3. Proposed Method
## Phase 2: Temporal Integration at a Single Node

### Step 1: Temporal Dataset & Infrastructure (planner sub-agent)
Create the temporal experiment infrastructure:
- **src/temporal_dataset.py**: Generate temporal sequences of d=16 vectors
  - Periodic sequences (periods 3, 4, 7, 11) — labeled "periodic"
  - Random walk sequences over a small state set — labeled "random"
  - Irregular/semi-random sequences (Markov with varying transition probs)
  - Each discrete state (A, B, C, D, ...) mapped to a fixed d=16 random embedding
  - Sequences of length 32, with stride-1 sliding window for temporal triplets
- **src/temporal_encoder.py**: Implement the four temporal integration mechanisms:
  - P2-D: Three-temporal-slot node (reuse UniversalNode, inputs = state_{t-2}, state_{t-1}, state_t)
  - P2-A: Multi-tick-rate node (updates every N steps, pools lower outputs)
  - P2-B: Recurrent state node (hidden state + GRU-like gating)
  - P2-C: Output-as-input loop (output at t-1 fed as additional input at t)
- Evaluation: next-step prediction accuracy + periodic-vs-random linear-probe classification

### Step 2: P2-D Zero-Shot Transfer Test (medium sub-agent)
Load Phase 1 JEPA-d16 trained weights, apply UniversalNode to temporal triplets.
- Run on all sequence types with 5 seeds (different random embeddings)
- Evaluate: (a) periodic-vs-random classification, (b) next-step prediction
- Compare against untrained-weight baseline (same architecture, random weights)
- This is the CRITICAL test: does spatial → temporal transfer work?

### Step 3: P2-D Temporal Training (medium sub-agent)
Train P2-D from scratch on temporal data with JEPA objective.
- Use the same JEPALoss from src/training_objectives.py
- Temporal JEPA: predict neighbor codes in the time dimension
- Train for 200 epochs, 5 seeds, d=16
- Evaluate on same tasks as Step 2

### Step 4: P2-A/B/C Baselines (medium sub-agent)
Implement and train P2-A, P2-B, P2-C with same compute budget.
- Each trained with appropriate local objectives
- 5 seeds each
- Same evaluation tasks

### Step 5: Analysis & Report (high sub-agent)
- Statistical comparison across all methods
- Test falsification criteria F0, F1, F2, F3
- If F1 is NOT triggered (transfer works): document as strongest evidence for
  universal node hypothesis
- If F1 IS triggered (transfer fails): analyze WHY spatial weights don't transfer
  — is it the weight structure, the input distribution shift, or fundamental
  axis-specificity?
- Produce phase_2/REPORT.md

### Files to create/modify:
- NEW: src/temporal_dataset.py
- NEW: src/temporal_encoder.py
- NEW: src/run_phase2.py
- NEW: src/test_temporal.py
- NEW: phase_2/REPORT.md
- MODIFY: src/pre_registration.md (update with Phase 2 plan and criteria)

---
*Created automatically by the RDF Orchestrator prior to iteration execution.*
