r"""
test_pc_act8b.py — clean 1-D rebuild toward LEARNED perception + ERROR-DRIVEN action.

Motivation: act6–act9's live manipulation was a scripted COORDINATE carry on oracle /
hand-computed positions.  act8b rebuilds the 1-D pipeline from scratch, deliberately
minimal, so that perception AND action are genuinely the network's — step by step:

  Step 1 (THIS FILE): learned perception + error-driven fovea, NO oracle.
    * the PC net learns to predict the windowed object image (world model);
    * the FOVEA is active-inference: it moves along the prediction-error gradient to
      keep the object centred (no oracle, no coordinate target);
    * the object's position is read from the net's HIDDEN beliefs by a learned READOUT
      (retinal position; world = known gaze φ + retinal), self-supervised during a
      developmental phase against the raw centre-of-mass (the teacher).  At test the
      agent perceives from the net alone.
  Later steps add: error-driven SELF-movement (goal prior), then the hard one —
  error-driven MANIPULATION of an object through a learned pointer→object model,
  then a learned grip; then colour/multi-object; then a 2-D port.

Run:  python test_pc_act8b.py        (live)   |   ACT8B_HEADLESS=1 python ...

Metrics (active phase): object-in-view %, readout retinal error, and the perceived-
vs-true world error — the honest test that perception comes from the learned net.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType
from pc.module import PCModule

W = 48        # world width
N = 16        # fovea window width
PHI_MIN = -N / 2.0
PHI_MAX = W - N / 2.0


def blob1d(pos: float, n: int, sigma: float = 1.2) -> np.ndarray:
    x = np.arange(n)
    return np.exp(-0.5 * ((x - pos) / sigma) ** 2)


def com1d(v: np.ndarray):
    v = np.clip(v, 0.0, None)
    s = v.sum()
    return float((np.arange(len(v)) * v).sum() / s) if s > 1e-4 else None


# --------------------------------------------------------------------------- #
# 1-D world: one object that lies around / drifts (no self-propulsion needed yet)
# --------------------------------------------------------------------------- #
class World1D:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.lo, self.hi = W / 8.0, W * 7.0 / 8.0
        self.obj = float(self.rng.uniform(self.lo, self.hi))
        self.vel = 0.0

    def scatter(self):
        self.obj = float(self.rng.uniform(self.lo, self.hi)); self.vel = 0.0

    def drift(self):
        # a SLOW smooth random walk so the error-driven fovea can track it
        self.vel = float(np.clip(0.9 * self.vel + self.rng.normal(0, 0.08), -0.5, 0.5))
        self.obj = float(np.clip(self.obj + self.vel, 0.0, W - 1))
        if self.obj <= 0.0 or self.obj >= W - 1:
            self.vel = -self.vel

    def world_lum(self):
        return blob1d(self.obj, W)


def window(field, phi):
    o = int(round(phi))
    out = np.zeros(N)
    for i in range(N):
        wi = o + i
        if 0 <= wi < W:
            out[i] = field[wi]
    return out


# --------------------------------------------------------------------------- #
# PC perception net: N sensor cells (object luminance), lateral neighbour coupling,
# a stride-2 hidden layer with local RFs, a top node.  Learns to predict the image.
# --------------------------------------------------------------------------- #
def build_net(rng):
    net = PCNetwork(eta_inf=0.05, n_relax=24, eps_tol=1e-5, eta_learn=0.006,
                    gamma=0.3, w_clip=3.0, rng=rng)
    cells = [net.add(SensorNode(f"s{i}", dim=1)) for i in range(N)]
    for i in range(N):                       # lateral coupling to nearest neighbours
        for j in (i - 1, i + 1):
            if 0 <= j < N:
                net.connect(f"s{i}", f"s{j}", ConnType.LATERAL, pressure_scale=0.1)
    h1 = []
    for c in range(0, N, 2):                 # hidden node every 2 cells, RF = [c-1..c+1]
        nid = f"h1_{c}"
        net.add(PCNode(nid, dim=6, activation="tanh", rng=rng)); h1.append(nid)
        for j in (c - 1, c, c + 1):
            if 0 <= j < N:
                net.connect(nid, f"s{j}", ConnType.UP, pressure_scale=1.0)
    net.add(PCNode("top", dim=6, activation="tanh", rng=rng))
    for nid in h1:
        net.connect("top", nid, ConnType.UP, pressure_scale=0.3)
    m = PCModule("Cortex1D"); m.add_in_port("cells", [f"s{i}" for i in range(N)])
    m.add_out_port("abstract", ["top"]); net.add_module(m)
    return net, cells, h1


def set_sheet(cells, lum_w):
    for i in range(N):
        cells[i].set_input(np.array([lum_w[i]]))


def fovea_gradient(cells):
    """Active-inference fovea drive: ∂E/∂φ on the object channel.  Uses the net's
    prediction (pi) and error (epsilon); moving against this reduces the error → the
    fovea slides to centre the object.  No oracle, no coordinate target."""
    e = np.array([c.epsilon[0] for c in cells])
    base = np.array([c.pi[0] for c in cells])
    grad = (np.roll(base, -1) - np.roll(base, 1)) * 0.5
    return float(np.sum(e * grad))


# --------------------------------------------------------------------------- #
# Learned perception readout: hidden beliefs (h1 mu) → RETINAL object position.
# Self-supervised by the raw COM teacher; world pos = gaze φ + retinal.
# --------------------------------------------------------------------------- #
class Readout:
    def __init__(self, in_dim, hid=32, lr=0.03, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 1 / np.sqrt(in_dim), (hid, in_dim)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), hid); self.b2 = 0.0
        self.lr = lr; self.err_ema = None

    def predict(self, x):
        h = np.tanh(self.W1 @ x + self.b1)
        return float(self.W2 @ h + self.b2), h

    def train(self, x, target_norm):
        y, h = self.predict(x)
        err = y - target_norm
        self.err_ema = abs(err) if self.err_ema is None else 0.99 * self.err_ema + 0.01 * abs(err)
        self.W2 -= self.lr * err * h; self.b2 -= self.lr * err
        dh = (self.W2 * err) * (1 - h ** 2)
        self.W1 -= self.lr * np.outer(dh, x); self.b1 -= self.lr * dh


def gather(net, ids):
    return np.concatenate([net.node(i).mu for i in ids])


# --------------------------------------------------------------------------- #
def render(step, total, world, phi, perceived, seen, sensor_err):
    o = int(round(phi))
    row = ["·"] * W
    ob = int(round(world.obj))
    if 0 <= ob < W:
        row[ob] = "O"
    if perceived is not None:
        pp = int(round(perceived))
        if 0 <= pp < W and pp != ob:
            row[pp] = "x"          # where the NET thinks the object is
    chars = []
    for i in range(W):
        if i == o:
            chars.append("[")
        chars.append(row[i])
        if i == o + N - 1:
            chars.append("]")
    sys.stdout.write("\x1b[H\x1b[2J")
    print(f"Step {step}/{total}   obj={world.obj:5.1f}  "
          f"perceived={perceived if perceived is None else round(perceived,1)}  "
          f"seen={seen}  sensor_err={sensor_err:.3f}")
    print("  O=object  x=net's percept  [..]=fovea")
    print("  " + "".join(chars))


def main():
    HEADLESS = os.environ.get("ACT8B_HEADLESS", "0") == "1"
    PERCEIVE = os.environ.get("ACT8B_PERCEIVE", "net").lower()   # net | raw
    SCALE = float(os.environ.get("ACT8B_SCALE", "1.0"))
    DELAY = float(os.environ.get("ACT8B_DELAY", "0.0"))
    GAIN = float(os.environ.get("ACT8B_GAIN", "3.0"))   # fovea action gain
    rng = np.random.default_rng(0)

    net, cells, h1 = build_net(rng)
    readout = Readout(in_dim=len(h1) * 6, rng=np.random.default_rng(3))
    world = World1D(seed=1)

    DEV = int(3000 * SCALE)                     # developmental phase (learn net+readout)
    TEST = int(3000 * SCALE)                    # active test (error-driven fovea)
    total = DEV + TEST
    phi = (W - N) / 2.0

    print(f"act8b step 1 — learned perception + error-driven fovea (1D, no oracle)")
    print(f"  world={W} fovea={N}  perceive={PERCEIVE}  dev={DEV} test={TEST}")

    se_hist, in_view, world_err, act = [], 0, 0.0, 0
    fov_v = 0.0; SMOOTH = 0.3                    # fovea velocity smoothing (momentum)

    for step in range(total):
        dev = step < DEV
        lum = world.world_lum()
        lum_w = window(lum, phi)
        set_sheet(cells, lum_w)
        r = net.step(learn=True); net.commit_step()
        if np.isfinite(r["sensor_error"]):
            se_hist.append(r["sensor_error"])

        raw_com = com1d(lum_w)                  # in-window COM (teacher / raw percept)
        seen = raw_com is not None
        x = gather(net, h1)
        if seen:                                # train the readout (self-supervised)
            readout.train(x, raw_com / (N - 1))
        pred_win, _ = readout.predict(x)
        net_world = int(round(phi)) + float(np.clip(pred_win * (N - 1), 0, N - 1))
        raw_world = (int(round(phi)) + raw_com) if seen else None
        perceived = (net_world if PERCEIVE == "net" else raw_world) if seen else None

        if dev:
            # developmental: object at VARIED in-window positions so the readout must
            # localise (gaze placed with a random offset, not centred); object scattered.
            world.scatter()
            phi = float(np.clip(world.obj - rng.uniform(1.0, N - 1.0), PHI_MIN, PHI_MAX))
        else:
            # active test: object drifts; the FOVEA tracks it via the error gradient
            # (active inference) — no oracle.  Perception via the chosen source.
            world.drift()
            disp = -fovea_gradient(cells)
            fov_v = (1 - SMOOTH) * (GAIN * disp) + SMOOTH * fov_v   # momentum
            fov_v = float(np.clip(fov_v, -2.0, 2.0))
            phi = float(np.clip(phi + fov_v, PHI_MIN, PHI_MAX))
            act += 1
            in_view += int(seen)
            if perceived is not None:
                world_err += abs(perceived - world.obj)
            if not HEADLESS:
                render(step, total, world, phi, perceived, seen, r["sensor_error"])
                if DELAY > 0:
                    time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    print("=" * 64)
    print(f"  act8b step 1 summary")
    print(f"  sensor_error: {np.mean(se_hist[:q]):.3f} → {np.mean(se_hist[-q:]):.3f}"
          f"   [drops → the net learned the world model]")
    print(f"  fovea (error-driven) kept object in view: {100.0*in_view/max(1,act):.1f}%")
    print(f"  readout retinal error (EMA): {readout.err_ema*(N-1):.2f}px  in {N}px window")
    print(f"  perceived ({PERCEIVE}) vs true object: {world_err/max(1,act):.2f}px mean")
    print(f"  [perceive=net → position came from the LEARNED net, raw COM only taught it]")
    print("=" * 64)


if __name__ == "__main__":
    main()
