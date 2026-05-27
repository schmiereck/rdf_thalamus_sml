# RDF Project: Hierarchical Sparse Universal Nodes (HSUN)

## Vision

Investigate an architecture for unsupervised representation learning built from a **single, universal node type** that satisfies the following properties:

1. Maps a small fixed-arity input (target: 3 slots, each a vector of dimension `d`) to a single output vector of dimension `d`.
2. Can be stacked hierarchically by feeding triplets of node outputs into nodes of the next layer (shared weights, kernel-3 1D convolution semantics, stride 1 — overlap of 2).
3. Can be applied along the time axis identically — three temporally consecutive outputs of one position feeding a temporal node.
4. Is trained via a **local, label-free objective** such that the same trained node works at every spatial position and every hierarchical level.

The architecture should yield representations where similar inputs produce similar codes (similarity-preserving encoding) and the dimensions of those codes carry **consistent semantics across positions and layers**.

## Non-Goals (for this project)

- 2D or higher-dimensional sensory data
- End-to-end backpropagation across the full hierarchy
- Real-world sensor integration
- Motor / action loops (deferred — see `rdf_thalamus` project)

## Design Constraints

- Python 3.10 / 3.11
- **No SaaS dependencies, no global ML library installations.** Isolated environments per phase.
- All training and evaluation runs locally (CPU acceptable for early phases)
- File naming: `snake_case` for modules, `PascalCase` for classes
- Each component must be swappable behind a small, explicit interface
- Each phase produces a numerical comparison report committed to the repo

## How to Read This Document

This document defines a **gated phase plan**. The implementing agent should not advance to the next phase until the current phase's success criteria are met, OR a rigorous justification for skipping is documented in `current_state.md`. The strategist may reorder alternatives within a phase but must not skip phases without justification.

Each phase specifies:
- **Setup** — the experimental configuration
- **Alternatives** — concrete variants to implement and compare
- **Success criteria** — quantitative bar to clear before advancing
- **Expected insight** — what the phase is supposed to teach us

---

## Phase 0 — Harness & Smoke Test

**Purpose:** Verify the experimental pipeline end-to-end. Establish a similarity metric and a baseline. **This is a smoke test, not a research result.**

**Setup:**
- Input: 3 binary pixels (8 possible states)
- Single encoder, no hierarchy, no time
- Synthetic dataset enumerating all 8 states with controlled noise variants

**Alternatives to implement and compare:**

| ID    | Name                      | Description                                                      |
|-------|---------------------------|------------------------------------------------------------------|
| P0-A  | Lookup table              | One-hot embedding, trivial lower bound                           |
| P0-B  | SDR / Spatial Pooler      | HTM-style sparse distributed representation, k-WTA               |
| P0-C  | Self-Organizing Map       | Kohonen SOM on a small grid                                      |
| P0-D  | Sparse Autoencoder        | Reconstruction + L1 sparsity penalty                             |
| P0-E  | Predictive Coding node    | Local-error node in the spirit of ngclearn                       |

**Success criteria:**
- All five implementations run end-to-end
- Similarity metric: cosine similarity of codes correlates with inverse Hamming distance of inputs (Spearman ρ ≥ 0.6 for non-trivial methods)
- A comparison report is produced (`phase_0/REPORT.md`)

**Expected insight:** With only 8 input states, every reasonable method succeeds. The deliverable is a working harness, a fixed similarity metric, and confidence that all five candidate encoders are correctly implemented. **Do not draw architectural conclusions from this phase.**

---

## Phase 1 — Spatial Hierarchy without Time

**Purpose:** Test the shared-weight stacked architecture on a non-trivial input space.

**Setup:**
- Input: 16 binary pixels in a 1D array
- Architecture: kernel-3 nodes with stride 1, 2–3 stacked layers
- Output dimension `d` chosen such that input slot dim = output slot dim (recursability)
- Structured datasets, not exhaustive enumeration of 2^16:
  - Uniform random bits
  - Single-blob inputs (one contiguous run of 1s)
  - Two-blob inputs
  - Periodic patterns (periods 2, 3, 4)
  - Mixed noise overlays

**Alternatives to compare:**

| ID    | Name                                                 | Description                                              |
|-------|------------------------------------------------------|----------------------------------------------------------|
| P1-A  | Best Phase-0 method, stacked, shared within layer    | Baseline stacking                                        |
| P1-B  | Same, but weights shared across layers too           | Test the strict universal-node hypothesis                |
| P1-C  | Per-layer learned weights (no cross-layer sharing)   | Upper-bound reference: what does sharing cost?           |
| P1-D  | Output dim = input dim, fully recursive form         | Strict universal-node form                               |
| P1-E  | Output dim ≠ input dim (e.g., wider)                 | Test if shape-matching is too restrictive                |

**Success criteria:**
- Top-layer codes separate the five structured input categories with ≥80% linear-probe accuracy
- Per-layer-vs-shared comparison quantified
- The strict universal form (P1-B with P1-D) reaches within 15% of upper-bound (P1-C)

**Expected insight:** Does forcing `dim_out = dim_in` and cross-layer weight sharing sacrifice too much expressivity? This phase decides whether the universal-node ambition is viable in the spatial-only setting.

---

## Phase 2 — Temporal Integration at a Single Node

**Purpose:** Test mechanisms for letting representations integrate over time, isolated from spatial hierarchy.

**Setup:**
- Single spatial position
- Input: sequence of single-state vectors over time (A/B/C: single Input 1.0,, AB/ABC/...: inputs 1.0,  '-': all Inputs 0.0)
- Example Test sequences:
  - Periodic: `A,B,C,A,B,C,…`, `AB,C,AB,C,…`, `A,B,-,A,B,-,…`, ...
  - Irregular: `A,B,A,B,C,B,A,B,…`, `A,AB,B,BC,A,B,AC,C,ABC,…`, ...
  - Random walks over a small state set
  - Long-range periodic patterns (period 7, 11)

**Alternatives to compare:**

| ID    | Name                            | Description                                                                     |
|-------|---------------------------------|---------------------------------------------------------------------------------|
| P2-A  | Different tick rates per layer  | Higher-level node updates every N steps, pools lower outputs                    |
| P2-B  | Internal recurrent state        | Node has a hidden state, mixes with current input (GRU-like, locally trained)   |
| P2-C  | Output-as-input loop            | Output at t-1 fed as an additional input slot at t (thalamus-style)             |
| P2-D  | Three-temporal-slot node        | Same kernel-3 node, inputs are `(state_{t-2}, state_{t-1}, state_t)` — full spatial-temporal symmetry |

**Success criteria:**
- Each method evaluated on (a) next-step prediction accuracy and (b) periodic-vs-random classification
- For P2-D specifically: can the same node trained spatially be applied temporally **without retraining**? If yes, this is the strongest evidence for unification.

**Expected insight:** P2-D is architecturally the cleanest. This phase decides whether the unified spatial-temporal grid is viable.

---

## Phase 3 — Unified Spatiotemporal Grid

**Purpose:** Combine spatial hierarchy and temporal integration into one architecture using a single universal node type.

**Setup:**
- 16 binary pixels, sequences of length 32
- 2D grid of nodes: spatial axis × temporal axis
- Single node type applied at every `(space, time)` position with kernel-3 receptive field in both axes

**Alternatives to compare:**

| ID    | Name                                                       | Description                                       |
|-------|------------------------------------------------------------|---------------------------------------------------|
| P3-A  | Separate spatial then temporal stages                       | Sequential: spatial encoder → temporal encoder    |
| P3-B  | Unified grid, anisotropic (different params space/time)     | Slight relaxation of the universal hypothesis     |
| P3-C  | Fully unified grid, single node type                        | The strong universal hypothesis                   |

**Test patterns:**
- Moving blob (translation in time)
- Expanding/contracting blob
- Periodic spatial-temporal patterns
- Object permanence: blob disappears for k steps then reappears

**Success criteria:**
- Pattern recognition accuracy on the four spatiotemporal benchmarks
- P3-C within 20% accuracy of P3-A
- Parameter count comparison: P3-C should be dramatically smaller

---

## Phase 4 — Training Objective Comparison

**Purpose:** With the architecture fixed (best variant from Phase 3), compare self-supervised training objectives on identical conditions.

**Setup:**
- Architecture frozen to the Phase-3 winner
- Dataset and evaluation held constant
- Train from scratch with each objective; equal compute budget

**Alternatives to compare:**

| ID    | Name                            | Description                                                          |
|-------|---------------------------------|----------------------------------------------------------------------|
| P4-A  | Predictive Coding (local)       | ngclearn-style local error propagation                               |
| P4-B  | Local JEPA                      | Predict own future latent from neighbors + own past                  |
| P4-C  | Slow Feature Analysis           | Minimize temporal change subject to variance constraint              |
| P4-D  | Hebbian + sparsity              | Pure local correlation learning with sparsity penalty                |
| P4-E  | Reconstruction (sparse AE)      | Reference point                                                      |

**Downstream evaluation tasks (held out from training):**
1. Anomaly detection (inject novel patterns)
2. Sequence classification
3. Next-step prediction

**Success criteria:**
- Ranked comparison across the three downstream tasks
- Training stability and per-method compute cost documented
- Recommendation issued for the default objective going forward

---

## Phase 5 — Vector Semantics Investigation

**Purpose:** Investigate whether code dimensions carry consistent semantics across positions and layers.

**Setup:**
- Take best model from Phase 4
- Probe each dimension of the code vector for correlations with hand-designed semantic axes:
  - Local magnitude / activity level
  - Local gradient (left-right asymmetry)
  - Local variance / "chaos"
  - Periodicity / repetition
  - Novelty / surprise (deviation from local prediction)

**Alternatives to compare:**

| ID    | Name                       | Description                                                            |
|-------|----------------------------|------------------------------------------------------------------------|
| P5-A  | Pure emergence             | No constraints on dimensions during training                           |
| P5-B  | Anchor features            | First k dimensions regularized toward hand-designed semantic features  |
| P5-C  | Disentanglement penalty    | Information-bottleneck or β-VAE-like loss term added                   |

**Success criteria:**
- For each dimension at each (layer, position): variance explained by each semantic axis
- Consistency score: how stable is the dimension-to-semantics mapping across positions and layers?
- Document which approach yields the most consistent and most interpretable semantics

---

## Open Question Resolved in Phase 0

> *Is it meaningful to begin with only 3 b/w inputs and no temporal component, or does that strip out all the interesting properties?*

**Answer:** Phase 0 with 3 inputs is a smoke test for the harness only. The architecture's interesting properties — hierarchy, time, recursion, universal node — cannot be evaluated at that scale (only 8 possible input states; every reasonable method succeeds trivially). Phase 1 (16 inputs, spatial hierarchy) is the first phase where method comparisons carry research weight. Phase 2 is where the architecture's distinctive value proposition begins to be tested. **Do not draw architectural conclusions from Phase 0.**

## Relationship to Existing Projects

- Findings from this project may feed back into `rdf_thalamus` if a viable universal-node design emerges. Specifically, the output-as-input loop tested in Phase 2 (P2-C) is structurally identical to the thalamus output loop.
- The architecture is intended to be eventually testable as a perception encoder in the 1D physics sandbox (128 RGB pixels, 3 objects). That integration is **out of scope** for this project but should be kept in mind as the long-term target.

## References for the Implementing Agent

- **HTM Spatial Pooler & Temporal Memory** — Numenta literature (Hawkins et al.)
- **ngclearn** — predictive coding library, biologically plausible local learning
- **JEPA family** — LeCun et al., joint embedding predictive architectures
- **Slow Feature Analysis** — Wiskott & Sejnowski, 2002
- **Hebbian / Oja learning rules** — classical references
- **Sparse coding** — Olshausen & Field, 1996
