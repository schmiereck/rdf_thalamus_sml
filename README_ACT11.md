# act11 — goal-directed manipulation of a *commanded* coloured object in 2-D

`src/pc/test_pc_act11.py` is the current head of a line of experiments that build a
**Predictive-Coding + active-inference** agent which manipulates objects toward a goal,
as an architecture benchmark. act11 is the richest stage so far: a 2-D top-down world with
**multiple coloured objects**, a **digital colour command** that selects which one to act on,
**target search**, a **proprioceptive body model**, and two manipulation modes — **carry**
(learned contact coupling) and genuine **push** (learned 2-D push-side policy via MPC).

Everything the agent does is **learned and coordinate-free** in spirit: it perceives a learned
scene, acts by reducing prediction errors / planning through learned models, and never reads
world coordinates out of an oracle for its control law.

---

## Run

```powershell
# live coloured top-down render
python src/pc/test_pc_act11.py

# push the COMMANDED object (learned 2-D push-side policy)
$env:ACT11_MANIP="push"; $env:ACT11_DELAY="0.05"; python src/pc/test_pc_act11.py

# headless metrics only
$env:ACT11_HEADLESS="1"; python src/pc/test_pc_act11.py
```

Environment knobs:

| var | default | meaning |
|---|---|---|
| `ACT11_MANIP` | `carry` | `carry` (learned coupling) or `push` (learned 2-D push-side MPC) |
| `ACT11_GOAL` | `obj` | `obj` = real goal; `none` / `scramble` = controls (must stay 0 %) |
| `ACT11_NOBJ` | `3` | number of coloured objects (1 commanded + N-1 distractors) |
| `ACT11_HEADLESS` | `0` | `1` = print summary only, no render |
| `ACT11_SCALE` | `1.0` | scales babble + dev + active steps (use `0.3` for a quick run) |
| `ACT11_LIFELONG` | `1` | keep learning the motor/dynamics models from real experience |
| `ACT11_DELAY` | `0.0` | seconds per frame in the live render |

---

## Architecture

The world (`WorldColor`) holds N coloured objects (distinct palette hues R/G/B/Y/M/C), a
target, a hand/pointer, and a **colour command** = "transport the object of THIS colour".
The scene is presented as a **3-channel RGB hex sensor sheet** `[R, G, B, pointer, target]`.

The agent is a set of cooperating modules, each a small PC network or a learned model:

* **VisualCortex** — a hex-lattice PC network (`build_hexnet`): an 8×8 retinal fovea of
  5-D sensor nodes (lateral 6-neighbour hex coupling) → `h1` hidden layer → `top`. It learns
  to reconstruct the coloured scene; its latent activations `x` are the substrate everything
  else reads from.
* **Colour-cued SELECTION** — `selected_lum` keeps per-cell luminance only where the perceived
  colour matches the command (cosine > `MATCH_TH=0.9`); the object's position is the centre of
  mass of that. This is the **conditioning** at work: the command picks the right object out of
  the distractors.
* **Target search** — saccadic: the fovea scans, foveates the commanded object and the target,
  and **remembers** both (sub-pixel) before manipulating. No oracle tells the agent where things are.
* **BodyModel** — a proprioceptive PC module (belief→observation per body part). The hand is
  moved **blind by efference**; vision corrects the felt position, **precision-weighted** by how
  central the hand is in the fovea (reliable at the centre, weakly trusted at the periphery).
  The agent always acts on its **felt** hand, even when the hand is out of view.
* **Manipulation**
  * *carry* — once in contact, a learned `Coupling` model + a learned `GoalPrior` (signed
    object→target error) drive the object to the target.
  * *push* — a learned 2-D push-dynamics model (`PushModel2D`) + short-horizon **MPC**: the
    push side (which way to go around the object) falls out of the learned dynamics. An
    **approach leash** walks the hand to the object first so the model stays in its valid range.
* **Lifelong learning** — the motor/dynamics models keep updating from real contact events.

The control loop each step: perceive → (search | select object) → keep gaze on object, lead the
hand there blind → carry or MPC-push → correct the felt hand by vision when it arrives → learn.

### Surprise readout (predicted vs actual)

Every PC module exposes its prediction error ("surprise") live in the render header and in the
headless summary:

* **VisualCortex** — `vis-sens` (input reconstruction) + `vis-LATENT` (`h1`/`top` `μ−π`, the
  latent-space surprise), per-dimension RMS.
* **BodyModel** — proprioceptive prediction vs seen hand.
* **Coupling / PushModel2D** — predicted vs actually-experienced object displacement.

This is diagnostic, not just decorative: the **dynamics surprise directly explained the
carry/push gap** (a well-modelled carry is barely surprised; a hard push is).

---

## Current results (headless)

| mode | commanded object delivered | notes |
|---|---|---|
| carry, `goal=obj` | **100 %** | learned coupling; felt-hand in 0.6 px / out 0.0 px |
| push, `goal=obj` | **100 %** | learned 2-D push-side MPC + approach leash |
| controls `none` / `scramble` | **0 % / 0 %** | scramble breaks the learned models → no delivery |

* **Selection** (attended vs commanded object): ~0.1–0.2 px among distractors.
* **Body model** felt-hand vs true: in **0.95 px**, out-of-view **1.61 px** (precision-weighted).

---

## Considerations & limits (honest)

* **Selection is direct colour-match attention**, not a net-learned classifier. It works
  perfectly here but is the most "hand-wired" part; making the selection itself net-learned /
  conditioned is the obvious next step.
* **Push is the hard mode.** It reaches 100 % only with the approach leash (keeping the learned
  push model in-distribution) + a stall-escape. The MPC is a short-horizon greedy planner; a
  value function / RL planner would be needed for genuinely cluttered pushing. Without the leash,
  a far hand drives the model out of distribution and the hand wanders to the edge.
* **Body model out-of-view drift** is bounded but not zero (~1.6 px). The felt hand dead-reckons
  from efference; it is only re-anchored by vision near the fovea centre. A fixed-gain correction
  trusting peripheral vision was the bug that caused ~5 px drift — fixed by precision weighting.
  An *active* look-at-the-hand glance was tried and made it worse (you need a good felt estimate
  to aim the glance), so it was reverted.
* The world is a clean simulation (no occlusion, simple shove physics, one mobile hand).

---

## Lineage — the steps that got here

Each big step is a separate `src/pc/test_pc_*.py` (copy-for-big-steps), so earlier stages stay
runnable. The two threads are the **environment line** (act5 → act11) and **de-risk
experiments** that validated a mechanism before it went live.

| file | what it added |
|---|---|
| `test_pc_act5.py` | tap/reach in a 1-D world; exposed that a pre-relax read + no exploration can't be goal-directed |
| `test_pc_goal_reach.py` | **goal-as-prior** validated (the dark-room fix: a goal injected as a top-down prior drives reaching) |
| `test_pc_act6.py` | closed the perception loop (measured the real cost of perceptual, non-oracle carry) |
| `test_pc_act7.py` | object **RGB colour** as a perception channel |
| `test_pc_act8.py` | **multi-object + colour-command conditioning** (1-D): a command selects which object to transport |
| `test_pc_act8b.py` | clean 1-D rebuild: genuinely **learned perception**, **error-driven coordinate-free action**, the **BodyModel** PC module, first genuine push |
| `test_pc_push_policy.py` | **1-D push de-risk**: MPC through a learned push model discovers reposition-then-push (cumulative discounted cost is the key; 100 %) |
| `test_pc_act9.py` | first **2-D top-down hex** world (colour + multi-object), but with a *scripted* coordinate carry |
| `test_pc_act10.py` | **2-D port of the learned/error-driven/coordinate-free line** (monochrome): learned 2-D perception, error-driven fovea, body model, learned-coupling carry, genuine 2-D push |
| `test_pc_push_policy_2d.py` | **2-D push de-risk**: 8 push dirs + fine + reposition actions, horizon-3 MPC; the 2-D push side emerges |
| **`test_pc_act11.py`** | **act10 + colour + multi-object + colour-command conditioning**, both carry and genuine push of the *commanded* object, surprise readout, precision-weighted body vision |

(Other `test_pc_planner*.py`, `test_pc_dream_goal.py`, `test_pc_goal_module.py` explored a
higher "dreaming/curiosity" planner above the goal module — a parallel thread, not on the act11
manipulation path.)

The reusable PC primitives live in `src/pc/` (`PCNode`, `SensorNode`, `PCNetwork`, `PCModule`,
`PCConnection`). act11 imports its proven 2-D parts (`Readout`, `BodyModel`, `Coupling`,
`GoalPrior`, hex helpers) straight from `test_pc_act10.py`, and the push model from
`test_pc_push_policy_2d.py`.
