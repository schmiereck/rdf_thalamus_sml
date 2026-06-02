# Temporal Hierarchy Design

## Motivation

The current network has no internal representation of *motion direction*.  
It only reacts to the instantaneous retinal slip (∂E/∂φ).  
A deeper layer that integrates over time could predict *where an object will be*  
rather than just *where it currently is*, enabling anticipatory gaze control.

Your diagram describes exactly this:

```
time →       1     2     3     4     5     6
─────────────────────────────────────────────
Layer 1       1     2     3     4     5     6      (single frames)
Layer 2       ·     12    23    34    45    56      (pairs, lag-1 integration)
Layer 3       ·     ·     ·     1234  2345  3456    (quadruplets, lag-3)
```

Each layer doubles the integration window and halves temporal resolution.
Deeper = slower = more history = can encode velocity/direction.

---

## Common element: recurrent self-connection (both designs)

Both designs need each hidden node to combine its own previous state with new
bottom-up input.  You chose **learned weights** for this.

In PC terms, a recurrent self-connection is just a LATERAL connection from a
node back to itself with a one-step delay:

```
  h_k(t) acts as both SOURCE and TARGET of a PCConnection
  W_self shape: [dim_k × dim_k]
  ΔW_self = η · f(μ_k(t-1)) ⊗ ε_k(t)      (Hebbian, same as other connections)
```

Implementation: at the start of each frame, before `phase_predict()`, each
hidden node copies its current activation into a "prev" buffer.  The
self-connection then uses this buffer as its source activation.

```python
# In network step, before phase_predict:
for node in hidden_nodes:
    node.prev_activation = node.activation.copy()   # f(μ(t-1))

# The self-connection PCConnection uses node.prev_activation as source
# instead of the live node.activation.
```

This requires a small addition to `PCConnection`: a flag
`use_prev_activation=True` that reads `source.prev_activation` instead of
`source.activation`.

---

## Design A — Clocked layers (literal to your diagram)

### Concept

Layer k updates only once every 2^(k-1) steps.  Between updates it holds its
state frozen.  When it does update, it pools (averages) the last 2^(k-1)
states of layer k-1.

```
Step:   1    2    3    4    5    6    7    8
L1:     ↑    ↑    ↑    ↑    ↑    ↑    ↑    ↑     (every step)
L2:     -    ↑    -    ↑    -    ↑    -    ↑     (every 2 steps, pools L1)
L3:     -    -    -    ↑    -    -    -    ↑     (every 4 steps, pools L2)
```

### Pros
- Exactly matches your diagram: "12" → "1234" doubling is literal.
- Deep layers genuinely integrate over long intervals.
- Clear separation of timescales.

### Cons
- Requires a clock/tick counter per layer in the training loop.
- During a clocked cycle the upper layers emit *stale* predictions to the
  lower layers — creates a systematic prediction lag.
- Backpressure (error signals flowing upward) is also clocked, so lower layers
  receive guidance only every 2^(k-1) steps.  Learning in lower layers becomes
  decoupled from upper layers for long stretches.
- Non-trivial to wire into the existing `net.step()` API without restructuring.

### Code changes needed
```
PCNetwork:
  + step_clocked(layer_clocks)  — runs per-layer sub-cycles
  + layer_tick_counter[]

PCNode:
  + pool_buffer: list of recent activations (for pooling)
  + is_frozen: bool (upper layers skip update when not their tick)

Training loop:
  + tick counter per epoch
  + conditional clamp / relax per layer
```

**Estimated complexity: large** — touches network core, node, training loop.
Risk of subtle synchronisation bugs.

---

## Design B — Leaky time constants (continuous, per-layer τ)

### Concept

Every layer updates every step, but with a layer-specific decay τ_k ∈ [0, 1):

```
μ_k(t) ← (1 − τ_k) · [relaxed state] + τ_k · μ_k(t-1)
```

- τ_1 = 0.0 → fully replaces state each step (current behaviour, fast)
- τ_2 = 0.5 → exponential moving average, half-life ≈ 1.4 steps
- τ_3 = 0.8 → half-life ≈ 3 steps
- τ_k = 1 − 2^(1−k)  is a natural schedule (each layer twice as slow)

The recurrent self-connection (learned W_self) provides the associative memory
on top of this exponential decay.  The decay alone gives the *timescale*; the
learned weights give the *content*.

### What this encodes

After training on leftward motion patterns, a deep node with τ=0.8 will carry
a "leftward" activation signature for ~3 steps after the object disappears —
enough for the action gradient to continue driving the eye in the right
direction even in the absence of immediate visual error.

### Pros
- Minimal API change: one extra parameter `tau` per node/layer.
- Every layer still participates every step → no synchronisation issues.
- Recurrent + leaky naturally approximates your diagram:
  - L1 (τ=0.0): reacts to current frame only
  - L2 (τ=0.5): effectively averages ~2 recent frames
  - L3 (τ=0.8): effectively averages ~5 recent frames
- Easy to sweep τ values to find the optimal timescale.

### Cons
- Softer timescale separation than Design A (exponential decay, not hard window).
- The "12", "1234" blocks in your diagram are approximated, not exact.

### Code changes needed

```python
# PCNode: add tau parameter and apply after update_state
def update_state(self, eta_inf, alpha):
    ...
    self.mu = (1.0 - self.tau) * new_mu + self.tau * prev_mu   # leaky blend

# build_network: assign tau per layer
tau_schedule = [1.0 - 2.0**(1.0 - k) for k in range(1, n_layers+1)]
# k=1: 0.0, k=2: 0.5, k=3: 0.75, k=4: 0.875 ...

# PCConnection: add ConnType.RECURRENT (or use_prev=True flag)
# recurrent self-connection per hidden node, W shape [dim×dim]
```

**Estimated complexity: small/medium** — clean addition to existing API.
Can ship in one session.

---

## Comparison table

| | Design A (clocked) | Design B (leaky) |
|---|---|---|
| Faithfulness to diagram | exact | approximate |
| Code complexity | large | small |
| Learning stability | risk of decoupling | continuous gradients |
| Timescale control | discrete, hard | continuous τ, sweepable |
| Risk of new bugs | high | low |
| Estimated build time | 2–3 sessions | 1 session |
| Recommended order | second | **first** |

---

## Recommendation

Start with **Design B** (leaky + learned self-connection).  It is:
- implementable in one session
- immediately testable in the sweep
- a strict generalization of the current network (τ=0 everywhere = current behaviour)

If results plateau and you want the exact clocked structure from your diagram,
Design A can be built on top as a follow-up.  The two designs are not
mutually exclusive: Design A is essentially Design B with τ=1.0 between clock
ticks and a hard reset at the tick boundary.

---

## Concrete next step (Design B)

1. `PCNode.__init__`: add `tau: float = 0.0` and `prev_mu` buffer
2. `PCNode.update_state`: apply leaky blend after relaxation update
3. `PCConnection`: add `ConnType.RECURRENT` that reads `source.prev_activation`
4. `build_network` in `test_pc_act1.py`: assign tau schedule + add recurrent
   self-connections to each hidden node
5. Sweep: add `tau_schedule` as a sweepable parameter

The recurrent weight matrix W_self [dim×dim] starts near zero (small random
init) so the network begins like the current architecture and learns to use
memory only where it helps.
