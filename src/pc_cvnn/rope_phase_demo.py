r"""rope_phase_demo.py — proves WHY the complex engine currently looks identical to
the real one, and HOW a RoPE-style PHASE encoding makes the phase channel carry
information (position), so the network "feels" relative distance via interference.

Diagnosis (run it):
  * The current sensor boundary lifts a REAL value into the complex plane with
    ZERO imaginary part (phase ≡ 0).  GoalModule2D even encodes position as a real
    spatial blob and discards the latent's imaginary part on decode.  => the phase
    channel only ever holds weight-init noise => no observable difference vs real.

  * RoPE fix:  z_k = A_k · exp(i · p · θ_k)
        amplitude A_k  = the "meaning" (here: constant 1 = "a position token")
        phase     p·θ_k = the POSITION, via per-channel frequencies θ_k
    Shifting position by m is a pure rotation (no new weights).  The inner product
    of two codes depends only on the RELATIVE displacement (p_i − p_j):
        <z(p_i), z(p_j)> = Σ_k exp(i (p_i − p_j) θ_k)   -> a distance kernel.

Run:  python src/pc_cvnn/rope_phase_demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc_cvnn.node import SensorNode, PCNode
from pc_cvnn.connection import ConnType
from pc_cvnn.network import PCNetwork
from pc_cvnn.rope import (rope_freqs, rope_encode_1d, rope_decode_1d,
                          rope_encode_2d, rope_decode_2d)


def banner(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ----------------------------------------------------------------------
# 1) The current boundary: a real value lifted to complex has ZERO phase
# ----------------------------------------------------------------------

def demo_zero_phase():
    banner("1) WHY no difference: the current sensor boundary kills the phase")
    net = PCNetwork(n_relax=5, rng=np.random.default_rng(0))
    s = net.add(SensorNode("s", dim=4))
    # The way GoalModule2D / the fovea feed data today: a REAL vector.
    s.set_input(np.array([0.5, -0.2, 0.1, 0.8]))
    ph = np.angle(s.mu)
    print(f"  real input -> sensor μ phase = {np.round(ph, 3)}")
    print("  phase is 0 (or ±π for negatives) -> the phase channel carries NO info.")
    print("  => downstream interference has nothing to interfere with -> behaves real.")


# ----------------------------------------------------------------------
# 2) RoPE: phase carries position, relative distance via interference
# ----------------------------------------------------------------------

def demo_rope_property():
    banner("2) RoPE phase code: encode position in phase, recover it, feel distance")
    th = rope_freqs(8, span=7.5)
    for p in (0.0, 1.0, 3.5, 7.0):
        z = rope_encode_1d(p, th)
        rec = rope_decode_1d(z, th)
        print(f"  p={p:4.1f}  |z|={np.abs(z).mean():.3f} (amplitude=meaning, constant)"
              f"   decoded={rec:5.2f}   err={abs(rec - p):.2e}")

    print("\n  relative-distance kernel  K(Δ) = (1/K)·Σ_k cos((p_i−p_j)·θ_k):")
    anchor = 3.0
    for q in (3.0, 3.5, 4.0, 5.0, 7.0):
        zi, zj = rope_encode_1d(anchor, th), rope_encode_1d(q, th)
        kern = float(np.real(np.vdot(zj, zi)) / len(th))   # <z_j, z_i> real part, normalised
        print(f"    p_i={anchor}  p_j={q:4.1f}  Δ={q-anchor:+4.1f}   K={kern:+.3f}")
    print("  K peaks at Δ=0 and falls off with |Δ| — the net FEELS relative position,")
    print("  exactly the RoPE / attention phase-subtraction property.")


# ----------------------------------------------------------------------
# 3) The complex PC engine TRANSPORTS the phase code end to end
# ----------------------------------------------------------------------

def demo_engine_transport():
    banner("3) The complex PC engine carries phase-encoded position through clamp+relax")
    NF = 8
    th = rope_freqs(NF // 2, span=6.0)
    net = PCNetwork(eta_inf=0.1, n_relax=60, eps_tol=1e-7, eta_learn=0.02,
                    gamma=0.3, w_clip=3.0, rng=np.random.default_rng(1))
    img = net.add(SensorNode("img", dim=NF))                 # complex sensor (rope code)
    z = net.add(PCNode("z", dim=NF, activation="identity", eta_temporal=0.0,
                       rng=np.random.default_rng(2)))
    net.connect("z", "img", ConnType.UP, pressure_scale=1.0)

    rng = np.random.default_rng(3)
    # "pretrain": let the top-down W learn to reconstruct rope codes of random positions
    for _ in range(4000):
        p = rng.uniform(0, 6, 2)
        img.set_input(rope_encode_2d(p, NF))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        net.phase_learn(); net.commit_step()

    # encode/decode round trip THROUGH the latent (latent kept COMPLEX, phase intact)
    errs = []
    for _ in range(200):
        p = rng.uniform(0.5, 5.5, 2)
        z.unclamp(); img.set_input(rope_encode_2d(p, NF))
        net.phase_predict(); net.phase_error(); net.phase_relax()
        recon = net.node("img").pi                            # complex reconstruction
        p_hat = rope_decode_2d(recon, NF)
        errs.append(np.linalg.norm(p_hat - p))
    print(f"  latent dtype = {z.mu.dtype} (kept complex, NOT cast to float)")
    print(f"  position recovered from the reconstructed PHASE: mean err = {np.mean(errs):.3f}")
    print(f"  (input was {NF} complex cells = {NF} numbers, vs a 12x12=144-cell real blob")
    print("   -> higher representational density, position lives in the phase.)")


if __name__ == "__main__":
    demo_zero_phase()
    demo_rope_property()
    demo_engine_transport()
    print("\nTakeaway: the engine is ready; to SEE a difference, feed position as PHASE")
    print("(RoPE) at the sensor boundary and keep the latent complex on decode.")
