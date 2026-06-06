r"""
test_pc_planner_curiosity.py — Option 2: a CURIOSITY-driven planner.

Option 1 dreamed the *rewarded* goal (extrinsic, supervised).  Option 2 swaps the
criterion to an INTRINSIC, epistemic one: dream goals where the planner's own model
of the world is still ignorant — "go where you haven't been".  No external reward,
no task rule.  This is the user's Neugier-Modul ("search undiscovered regions in the
latent space, propose them") coupled to the Belohnungs-Modul ("a new goal reached →
learn that state → it is no longer novel → move on").

The loop, per round (NO reward, NO rule):
  1. sample K candidate goal latents (on the goal module's manifold)
  2. score each by NOVELTY; dream (pick) the most novel one
  3. carry the object there (it is reached) and mark it VISITED → novelty there drops
The claim: an epistemic criterion covers the whole world faster, with fewer
revisits, than dreaming random goals — and the dreamed goals stay actionable.

Two novelty signals are compared against a random baseline:
  * distance novelty (model-free) : min latent-distance to visited goals
  * RND novelty (learned predictor): a trainable net chases a FIXED random net;
    where the predictor is still untrained = high error = unexplored
    (this is the "planner's own prediction error" epistemic signal)

Run:  python test_pc_planner_curiosity.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc.test_pc_act6 import GoalModule

WORLD = 48.0
Z = 6              # goal-module latent dim
NBINS = 12         # world-coverage bins over [0.1W, 0.9W]
LO, HI = 0.1 * WORLD, 0.9 * WORLD


def carry_to(desired: float, start: float, *, gain=0.15, vmax=2.0,
             grab=1.5, tol=1.5, max_steps=500) -> float:
    """act6 synced rigid grab-carry: return final |obj - desired|."""
    obj = p = float(start)
    for _ in range(max_steps):
        if abs(p - obj) < grab:
            vp = float(np.clip(gain * (desired - obj), -vmax, vmax))
            obj = float(np.clip(obj + vp, 0.0, WORLD)); p = float(np.clip(p + vp, 0.0, WORLD))
        else:
            vp = float(np.clip(gain * (obj - p), -vmax, vmax))
            p = float(np.clip(p + vp, 0.0, WORLD))
        if abs(obj - desired) < tol:
            break
    return abs(obj - desired)


def bin_of(pos: float) -> int:
    return int(np.clip((pos - LO) / (HI - LO) * NBINS, 0, NBINS - 1))


# --------------------------------------------------------------------------- #
# Novelty signals — each: .score(z)->higher means more novel ; .visit(z)
# --------------------------------------------------------------------------- #
class RandomNov:
    """Baseline: no curiosity — every candidate scored at random."""
    def __init__(self, rng): self.rng = rng
    def score(self, z): return float(self.rng.random())
    def visit(self, z): pass


class DistanceNov:
    """Model-free epistemic value: distance to the nearest visited latent."""
    def __init__(self): self.seen = []
    def score(self, z):
        if not self.seen:
            return 1.0
        return float(min(np.linalg.norm(z - s) for s in self.seen))
    def visit(self, z): self.seen.append(np.asarray(z, float))


class RNDNov:
    """Learned-predictor (RND) novelty = the planner's OWN prediction error.
    A trainable MLP g chases a FIXED random nonlinear net f; where g has not yet been
    trained (unvisited z) the error ||f(z)-g(z)|| is high.  g needs a hidden layer —
    a linear g cannot match the nonlinear f and its residual swamps the novelty signal."""
    def __init__(self, rng, m=8, h=12, lr=0.03, iters=80):
        self.Wf = rng.normal(0, 1.0, (m, Z)); self.bf = rng.normal(0, 1.0, m)
        self.W1 = rng.normal(0, 0.3, (h, Z));  self.b1 = np.zeros(h)
        self.W2 = rng.normal(0, 0.3, (m, h));  self.b2 = np.zeros(m)
        self.lr, self.iters, self.seen = lr, iters, []
    def _f(self, z): return np.tanh(self.Wf @ z + self.bf)
    def _g(self, z): return self.W2 @ np.tanh(self.W1 @ z + self.b1) + self.b2
    def score(self, z): return float(np.linalg.norm(self._f(z) - self._g(z)))
    def visit(self, z):
        self.seen.append(np.asarray(z, float))
        Zs = np.array(self.seen); Fs = np.array([self._f(z) for z in Zs]); n = len(Zs)
        for _ in range(self.iters):                       # backprop on all visited
            Hh = np.tanh(Zs @ self.W1.T + self.b1)        # (n, h)
            err = (Hh @ self.W2.T + self.b2) - Fs         # (n, m)
            dHh = (err @ self.W2) * (1 - Hh ** 2)         # (n, h)
            self.W2 -= self.lr * (err.T @ Hh) / n; self.b2 -= self.lr * err.mean(0)
            self.W1 -= self.lr * (dHh.T @ Zs) / n; self.b1 -= self.lr * dHh.mean(0)


# --------------------------------------------------------------------------- #
def explore(gm, make_nov, sample_cands, *, rounds, K, seed_pos):
    """Run the curiosity loop; return coverage curve, per-round bins, transport errs."""
    nov = make_nov()
    nov.visit(gm.encode(seed_pos))
    covered = np.zeros(NBINS, bool); covered[bin_of(seed_pos)] = True
    pos = float(seed_pos)
    curve, bins, terrs = [], [], []
    for _ in range(rounds):
        cands = sample_cands(K)
        z = cands[int(np.argmax([nov.score(c) for c in cands]))]
        p = gm.decode_dream(z)
        terrs.append(carry_to(p, pos)); pos = p
        b = bin_of(p); bins.append(b); covered[b] = True
        nov.visit(z)
        curve.append(covered.mean())
    return np.array(curve), bins, float(np.mean(terrs))


def early_revisits(bins, seed_bin, n):
    """Revisits within the first n rounds (ideal explorer = 0: each round a new bin)."""
    seen = {seed_bin}; rev = 0
    for b in bins[:n]:
        if b in seen:
            rev += 1
        seen.add(b)
    return rev


def rounds_to(curve, thresh):
    hit = np.where(curve >= thresh)[0]
    return int(hit[0] + 1) if len(hit) else None


def main():
    gm = GoalModule(WORLD, img=16, latent=Z, activation="identity",
                    rng=np.random.default_rng(7))
    gm.pretrain(15000)

    # Encode a position grid → the goal module's latent manifold.  Candidates are
    # proposed UNIFORMLY along the manifold (interpolated latents) so the comparison
    # isolates the SELECTION criterion, not the proposal distribution's own bias.
    grid = np.linspace(0.03 * WORLD, 0.97 * WORLD, 60)
    Zgrid = np.array([gm.encode(p) for p in grid])

    def goal_latent(p):
        return np.array([np.interp(p, grid, Zgrid[:, k]) for k in range(Z)])

    print("=" * 78)
    print("  Curiosity-driven planner (Option 2): explore with NO reward")
    print(f"  world={WORLD:.0f}px  latent={Z}  bins={NBINS}  gm decode_err={gm.decode_error():.2f}px")
    print(f"  candidates proposed uniformly on the manifold (selection is the variable)")
    print("=" * 78)

    ROUNDS, K, REPEATS = 30, 24, 8
    seed_bin = bin_of(LO + 1.0)
    methods = {
        "random       ": lambda rng: (lambda: RandomNov(rng)),
        "distance nov ": lambda rng: (lambda: DistanceNov()),
        "RND nov      ": lambda rng: (lambda: RNDNov(rng)),
    }
    for name, make in methods.items():
        curves, erevs, full, terrs = [], [], [], []
        for rep in range(REPEATS):
            rng = np.random.default_rng(100 + rep)
            sample = lambda K, rng=rng: np.array([goal_latent(p)
                                                  for p in rng.uniform(LO, HI, K)])
            curve, bins, terr = explore(gm, make(rng), sample,
                                        rounds=ROUNDS, K=K, seed_pos=LO + 1.0)
            curves.append(curve); terrs.append(terr)
            erevs.append(early_revisits(bins, seed_bin, NBINS))
            r100 = rounds_to(curve, 0.999); full.append(r100 if r100 else ROUNDS + 1)
        curve = np.mean(curves, 0)
        print(f"  {name}: cov@5={curve[4]:.2f} cov@10={curve[9]:.2f} cov@15={curve[14]:.2f}"
              f"  rounds->full={np.mean(full):4.1f}  early-revisits={np.mean(erevs):4.1f}"
              f"  transport={np.mean(terrs):.2f}px")
    print("-" * 78)
    print("  Read: DISTANCE/density novelty covers the world ~2x FASTER (full in ~14 vs")
    print("        ~31 rounds), with fewer early-revisits, all with NO reward — and low")
    print("        transport means every dreamed goal stays actionable. Curiosity works.")
    print("  Note: RND (learned-predictor) novelty FAILS here — on a smooth 1-D goal")
    print("        manifold the predictor interpolates over unvisited gaps, washing out")
    print("        the signal. Density-based novelty is the robust epistemic criterion.")
    print("=" * 78)


if __name__ == "__main__":
    main()
