# Research Manager Log - Iteration 004

## Iteration 004 -> Manager [Proposed Research Plan]

**Proposed Hypothesis:**
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

**Proposed Falsification Criterion:**
The hypothesis is falsified if ANY of the following hold:

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

**Proposed Method:**
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
- Test falsification criteria F1, F2, F3
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

## Iteration 004 -> Planner [Strategic Guidance]

### Strategic Guidance: Manager's Note

To: **Planner Agent**  
From: **Research Manager (Forschungsleiter)**  
Subject: **Phase 2 Strategic Guidance: Avoiding the Trivial Transfer Loophole**

The transition to Phase 2 (Temporal Integration) is highly promising. Unifying spatial and temporal axes under a single universal node type is the core ambition of the HSUN project. However, we must apply strict scientific skepticism to your proposed evaluation design to ensure that our conclusions are genuinely empirical rather than trivial consequences of our experimental construction.

---

### 1. The Construction-vs-Empirical Test: The "Periodicity" Loophole
Your proposed **F1 Transfer Criterion** relies on "periodic-vs-random" classification of sequence codes. 
* **The Loophole:** Any deterministic, time-invariant mapping $f(s_{t-2}, s_{t-1}, s_t)$—including a completely untrained, random weight initialization—will map a periodic input sequence to a periodic output sequence. A downstream linear probe can easily exploit this deterministic preservation of periodicity. Consequently, both your trained spatial weights and your random baseline weights may achieve near 100% classification accuracy, resulting in a false negative (or a false positive of "successful transfer" if both perform identically high).
* **The Correction:** You must evaluate transfer using metrics where deterministic propagation alone does not guarantee success. Implement and report:
  1. **Zero-Shot Temporal JEPA Loss:** Evaluate the raw local JEPA loss (prediction error in latent space) of the *spatially-trained* node on temporal transitions, and compare it directly to an *untrained* node. If the spatial node has truly learned a general representation of "predictability" and "coherence," its zero-shot temporal JEPA loss should be significantly lower than that of random weights.
  2. **Next-Step Prediction of Chaotic/Markovian Transitions:** Test prediction on irregular/Markov sequences where the node must encode temporal context to resolve state ambiguity, rather than simple periodic sequences.

### 2. Fair Baseline Comparison (Parameter & Objective Hygiene)
When evaluating P2-D (the three-temporal-slot universal node) against P2-A (multi-tick), P2-B (recurrent), and P2-C (output loop):
* Ensure that all alternatives are trained using the **same JEPA / VICReg-style local predictive objective** to isolate the architectural differences from the loss formulation.
* If P2-D is slightly less performant than recurrent architectures (P2-B) but operates with **zero temporal retraining (zero-shot spatial transfer)**, this must be reported as a highly successful trade-off rather than a failure. Acknowledge and document honest nulls or partial successes transparently.

### 3. Pre-Registration Mandate
Before running the simulations, the Orchestrator will automatically write your pre-registration to `src/pre_registration.md`. Refine your hypothesis and falsification criteria in your next plan step to incorporate the quantitative **Zero-Shot Temporal JEPA Loss ratio** (e.g., $Loss_{\text{spatial\_trained}} / Loss_{\text{untrained}} < 0.85$) as a primary falsification check for transfer success.

Proceed with updating the pre-registration and initiating Step 1 of your temporal integration harness. Keep the language grounded, precise, and free of hyperbolic terms.

---

