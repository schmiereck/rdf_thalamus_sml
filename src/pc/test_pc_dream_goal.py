r"""
test_pc_dream_goal.py — Can the goal module DREAM novel, actionable goals?

In act6 a goal is shown as an image (or its encoded latent is re-decoded — a faithful
round-trip).  The real question for "the network invents its own goals" is whether a
latent SAMPLED in the goal module's latent space — never derived from any image —
decodes to a VALID, DIVERSE world-position, and whether the object can be
transported to it.  This is the basis for a future Planner that dreams goals.

Uses the act6 GoalModule (PC autoencoder over object world-positions).  Two ways to
dream a latent:
  (A) interpolation : z = (1-t)·encode(p_i) + t·encode(p_j)   — between known goals
  (B) latent prior  : fit a Gaussian to the encoded-latent distribution and sample z

For each dreamed z:  pos = decode_dream(z); is pos valid/in-range? do dreamed
positions SPAN the world (diverse)?  Then a synced grab-carry (the act6 controller)
transports the object to pos — does it arrive?

Run:  python test_pc_dream_goal.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc.test_pc_act6 import GoalModule

WORLD = 48.0


def carry_to(desired: float, start: float, *, gain=0.15, vmax=2.0,
             grab=1.5, tol=1.5, max_steps=500) -> float:
    """act6 synced rigid grab-carry: return final |obj - desired|."""
    obj = p = float(start)
    for _ in range(max_steps):
        grabbed = abs(p - obj) < grab
        if grabbed:
            vp = float(np.clip(gain * (desired - obj), -vmax, vmax))
            obj = float(np.clip(obj + vp, 0.0, WORLD)); p = float(np.clip(p + vp, 0.0, WORLD))
        else:
            vp = float(np.clip(gain * (obj - p), -vmax, vmax))
            p = float(np.clip(p + vp, 0.0, WORLD))
        if abs(obj - desired) < tol:
            break
    return abs(obj - desired)


def main() -> None:
    rng = np.random.default_rng(0)
    gm = GoalModule(WORLD, img=16, latent=6, activation="identity",
                    rng=np.random.default_rng(7))
    gm.pretrain(15000)
    print("=" * 76)
    print("  Dreaming novel goals in the goal module's latent space")
    print(f"  world={WORLD:.0f}px  latent=6   decode_err={gm.decode_error():.2f}px")
    print("=" * 76)

    # Learned latent manifold: encode a grid of real positions.
    grid = np.linspace(0.05 * WORLD, 0.95 * WORLD, 40)
    Zd = np.array([gm.encode(p) for p in grid])

    # ---- (A) interpolation dreams (between two known goals) ----
    n, valid, monotone, reach = 300, 0, 0, []
    for _ in range(n):
        i, j = rng.integers(0, len(grid), 2)
        t = float(rng.uniform())
        z = (1 - t) * Zd[i] + t * Zd[j]
        pos = gm.decode_dream(z)
        lo, hi = sorted((grid[i], grid[j]))
        if 0.0 <= pos <= WORLD:
            valid += 1
        if lo - 2 <= pos <= hi + 2:        # decoded between the two endpoints?
            monotone += 1
        reach.append(carry_to(pos, float(rng.uniform(0.1 * WORLD, 0.9 * WORLD))))
    print(f"  (A) interpolation : valid={100*valid/n:5.1f}%  between-endpoints="
          f"{100*monotone/n:5.1f}%  transport_err={np.mean(reach):.2f}px")

    # ---- (B) latent-prior dreams (sample the network's own latent distribution) ----
    mean, cov = Zd.mean(0), np.cov(Zd.T)
    n, valid, poss, reach = 300, 0, [], []
    for _ in range(n):
        z = rng.multivariate_normal(mean, cov)
        pos = gm.decode_dream(z)
        if 0.0 <= pos <= WORLD:
            valid += 1; poss.append(pos)
            reach.append(carry_to(pos, float(rng.uniform(0.1 * WORLD, 0.9 * WORLD))))
    poss = np.array(poss)
    cover = f"min={poss.min():.0f} max={poss.max():.0f} std={poss.std():.0f}" if len(poss) else "n/a"
    print(f"  (B) latent prior  : valid={100*valid/n:5.1f}%  coverage[{cover}]"
          f"  transport_err={np.mean(reach):.2f}px")

    # A few concrete dreamed goals (latent prior) and where they land.
    print("-" * 76)
    print("  sample dreamed goals (sampled latent → decoded position → transported):")
    for _ in range(6):
        z = rng.multivariate_normal(mean, cov)
        pos = gm.decode_dream(z)
        err = carry_to(pos, float(rng.uniform(0.1 * WORLD, 0.9 * WORLD)))
        print(f"    z=[{' '.join(f'{v:+.2f}' for v in z)}] → pos={pos:5.1f}px  "
              f"reached(|obj-pos|={err:.2f}px)")
    print("-" * 76)
    print("  Read: high valid% + wide coverage → dreamed latents are real, diverse")
    print("        goals; low transport_err → the object can be sent to a dreamed goal.")
    print("=" * 76)


if __name__ == "__main__":
    main()
