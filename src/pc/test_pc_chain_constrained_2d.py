r"""test_pc_chain_constrained_2d.py — the constrained chain in 2D (port of the 1D PoC).

The 1D PoC (test_pc_chain_constrained.py) learned a position-dependent SPEED CAP (a "mud" band) and the
chained forward-model rollout RESPECTED it (it slowed down in the mud where naive interpolation stayed
uniform).  The decisive lever was the world-model REPRESENTATION: scaled LOCALIZED (blob/RBF) position
features + a DISPLACEMENT target + mud oversampling (Hebel 1).

This is the 2D port.  Now the mud is a localized DISK in the plane, so the interesting behaviour is no
longer just slowing down -- the planner can ROUTE AROUND the slow zone.  The pipeline:

  1.  a tiny NONLINEAR forward world model  delta = f(pos_features, u)  with the SAME representation that
      worked in 1D, lifted to 2D: position as a 2D RBF/blob code (outer product of the per-axis blobs,
      scaled to ~unit magnitude) + a 2D action; trained on random moves with the mud DISK OVERSAMPLED.
  2.  from the LEARNED model we read a SPEED FIELD (how far one action carries you at each point) -- this
      is the model's own picture of the constraint (fast open, slow mud).
  3.  the PLANNER optimises interior waypoints to minimise TRAVERSAL TIME through that learned field
      (endpoints clamped).  Min-time naturally curves AROUND the slow mud, where the naive straight line
      ploughs through it.

Honest framing: this shows the LEARNED constraint shaping a 2D plan.  The model is still tiny; the point is
that the representation that fixed 1D ports to 2D, and the chained/forward model earns its keep (a straight
interpolation cannot route around a localized constraint).

Env: CON2D_STEPS  CON2D_HID  CON2D_MUDCAP  CON2D_RADIUS  CON2D_ITERS  CON2D_NOVIZ
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

G = 13                                                       # grid 0..G-1 in each axis (continuous coords)
MUD_CX, MUD_CY = 6.0, 6.0                                    # mud disk centre
MUD_R = float(os.environ.get("CON2D_RADIUS", "2.6"))        # mud disk radius
MUD_CAP = float(os.environ.get("CON2D_MUDCAP", "0.3"))     # speed limit inside the mud
OPEN_CAP = 1.5                                               # speed limit in the open
UMAX = 1.8                                                   # action magnitude range


def blob1d(pos, sigma=0.8):
    x = np.arange(G)
    b = np.exp(-0.5 * ((x - pos) / sigma) ** 2)
    return b / (b.sum() + 1e-9)


def feat(pos):
    """2D position as a LOCALIZED RBF code: outer product of the per-axis blobs (encodes the JOINT
    position, so the disk -- which couples x and y -- is linearly separable from open space).  Scaled to
    UNIT L2 NORM so the whole 169-dim position code carries about the SAME energy as the 2-dim action;
    otherwise position drowns the action and the net cannot read the action's magnitude or the cap.  (In
    1D the energy ratio was ~2:1 and it worked; the raw 2D outer product was ~85:1 and the model collapsed
    every displacement magnitude to the dataset mean.)"""
    bx, by = blob1d(pos[0]), blob1d(pos[1])
    f = np.outer(bx, by).ravel()
    return f / (np.linalg.norm(f) + 1e-9)


def in_mud(pos):
    return (pos[0] - MUD_CX) ** 2 + (pos[1] - MUD_CY) ** 2 <= MUD_R ** 2


def cap_at(pos):
    return MUD_CAP if in_mud(pos) else OPEN_CAP


def true_step(pos, u):
    """Apply the action capped to the LOCAL speed limit (norm-capped), clipped to the grid."""
    cap = cap_at(pos)
    n = np.linalg.norm(u)
    if n > cap:
        u = u / (n + 1e-9) * cap
    return np.clip(np.asarray(pos, float) + u, 0.0, G - 1.0)


class Forward2D:
    """Tiny NONLINEAR MLP world model:  delta = MLP([RBF(pos), u]) * UMAX  (predicts the DISPLACEMENT, the
    representation that worked in 1D).  TWO hidden layers: the dynamics are a GATE x MAGNITUDE product (in
    the mud cap |u| to 0.3; in the open pass |u| through), and a single tanh layer cannot represent that
    spatial gating -- a one-layer net learns magnitude fine with NO mud but blends mud and open together
    once the disk is added.  Depth gives the multiplicative gate.  Backprop over a fixed dataset with the
    mud disk oversampled."""

    def __init__(self, hid=None, lr=0.002, rng=None):
        rng = rng or np.random.default_rng(0)
        hid = hid or int(os.environ.get("CON2D_HID", "256"))
        din = G * G + 2
        self.W1 = rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 1 / np.sqrt(hid), (hid, hid)); self.b2 = np.zeros(hid)
        self.W3 = rng.normal(0, 1 / np.sqrt(hid), (2, hid)); self.b3 = np.zeros(2)
        self.lr = lr

    def _x(self, pos, u):
        return np.concatenate([feat(pos), np.asarray(u, float) / UMAX])

    def train(self, steps=400000, rng=None):
        rng = rng or np.random.default_rng(1)
        n = 30000; bs = 256; epochs = max(1, steps // n)
        # OVERSAMPLE the mud disk (~13% of the area) so the net LEARNS the low cap instead of averaging it.
        nm = int(0.45 * n)
        ang = rng.uniform(0, 2 * np.pi, nm); rad = MUD_R * np.sqrt(rng.uniform(0, 1, nm))
        Pm = np.stack([MUD_CX + rad * np.cos(ang), MUD_CY + rad * np.sin(ang)], 1)
        Po = rng.uniform(0.5, G - 1.5, (n - nm, 2))
        P = np.concatenate([Pm, Po], 0)
        # RADIAL action sampling (angle uniform, magnitude uniform up to UMAX) so the CAP is exercised at
        # full push in EVERY direction -- a box under-covers the large magnitudes that reveal the limit.
        aa = rng.uniform(0, 2 * np.pi, n); mm = rng.uniform(0, UMAX, n)
        U = np.stack([mm * np.cos(aa), mm * np.sin(aa)], 1)
        X = np.array([self._x(p, u) for p, u in zip(P, U)])
        T = np.array([(true_step(p, u) - p) / UMAX for p, u in zip(P, U)])      # 2D displacement target
        self.fit_arrays(X, T, epochs, bs=bs, rng=rng)

    def fit_arrays(self, X, T, epochs, bs=256, rng=None):
        """ADAM training on a pre-built (feature, displacement-target) dataset.  Shared by the synthetic
        1D-style task and the ARM lift (which supplies its own babbled data).  ADAM is essential: plain
        SGD parks in a 'predict the mean magnitude in the action direction' plateau and never learns to
        GATE the magnitude by position (the spatial speed cap) -- the optimizer was the lever, not just
        depth."""
        rng = rng or np.random.default_rng(1)
        X = np.asarray(X, float); T = np.asarray(T, float); n = len(X)
        params = ["W1", "b1", "W2", "b2", "W3", "b3"]
        mom = {p: np.zeros_like(getattr(self, p)) for p in params}
        vel = {p: np.zeros_like(getattr(self, p)) for p in params}
        b1a, b2a, eps, t = 0.9, 0.999, 1e-8, 0
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb, tb = X[b], T[b]
                h1 = np.tanh(xb @ self.W1.T + self.b1)             # (B,hid)
                h2 = np.tanh(h1 @ self.W2.T + self.b2)             # (B,hid)
                y = h2 @ self.W3.T + self.b3                       # (B,2)
                e = (y - tb) / len(b)
                grad = {}
                grad["W3"] = e.T @ h2; grad["b3"] = e.sum(0)
                dh2 = (e @ self.W3) * (1 - h2 ** 2)
                grad["W2"] = dh2.T @ h1; grad["b2"] = dh2.sum(0)
                dh1 = (dh2 @ self.W2) * (1 - h1 ** 2)
                grad["W1"] = dh1.T @ xb; grad["b1"] = dh1.sum(0)
                t += 1
                for p in params:
                    g = grad[p]
                    mom[p] = b1a * mom[p] + (1 - b1a) * g
                    vel[p] = b2a * vel[p] + (1 - b2a) * g * g
                    mh = mom[p] / (1 - b1a ** t); vh = vel[p] / (1 - b2a ** t)
                    setattr(self, p, getattr(self, p) - self.lr * mh / (np.sqrt(vh) + eps))

    def delta(self, pos, u):
        u = np.asarray(u, float)
        n = np.linalg.norm(u)
        if n > UMAX:
            u = u / n * UMAX
        h1 = np.tanh(self.W1 @ self._x(pos, u) + self.b1)
        h2 = np.tanh(self.W2 @ h1 + self.b2)
        return (self.W3 @ h2 + self.b3) * UMAX

    def speed(self, pos, ndir=8):
        """The LEARNED speed at a point: mean displacement magnitude over action directions at full push.
        Open ~ OPEN_CAP, mud ~ MUD_CAP -- the model's own picture of the constraint."""
        mags = []
        for a in np.linspace(0, 2 * np.pi, ndir, endpoint=False):
            u = UMAX * np.array([np.cos(a), np.sin(a)])
            mags.append(np.linalg.norm(self.delta(pos, u)))
        return float(np.mean(mags))


def speed_grid(fm, res=40):
    """Precompute the model's speed field on a fine grid for fast bilinear lookup in the planner."""
    xs = np.linspace(0, G - 1, res)
    S = np.array([[fm.speed((x, y)) for x in xs] for y in xs])   # S[iy, ix]
    return xs, S


def speed_at(xs, S, pos):
    res = len(xs); step = xs[1] - xs[0]
    fx = np.clip((pos[0] - xs[0]) / step, 0, res - 1.001)
    fy = np.clip((pos[1] - xs[0]) / step, 0, res - 1.001)
    ix, iy = int(fx), int(fy); dx, dy = fx - ix, fy - iy
    s00, s10 = S[iy, ix], S[iy, ix + 1]; s01, s11 = S[iy + 1, ix], S[iy + 1, ix + 1]
    return (s00 * (1 - dx) + s10 * dx) * (1 - dy) + (s01 * (1 - dx) + s11 * dx) * dy


def path_time(xs, S, pts):
    """Traversal TIME of a polyline through the learned speed field: each segment costs length / speed."""
    t = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        mid = 0.5 * (a + b)
        s = max(speed_at(xs, S, mid), 1e-3)
        t += np.linalg.norm(b - a) / s
    return t


def _descend(xs, S, W, K, iters, lr=0.08, eps=0.12):
    """Numerical-gradient descent on traversal time, interior points only, with a NORMALISED step (the
    speed field is sharp at the mud boundary, so a raw gradient step is unstable)."""
    W = W.copy()
    for _ in range(iters):
        g = np.zeros_like(W)
        for i in range(1, K):
            for d in range(2):
                Wp = W.copy(); Wp[i, d] += eps; tp = path_time(xs, S, Wp)
                Wm = W.copy(); Wm[i, d] -= eps; tm = path_time(xs, S, Wm)
                g[i, d] = (tp - tm) / (2 * eps)
        gn = np.linalg.norm(g)
        if gn > 1e-9:
            g = g / gn * min(gn, 2.0)                           # cap the step magnitude (stability)
        W[1:K] -= lr * g[1:K]
        W = np.clip(W, 0.0, G - 1.0)
    return W


def plan_mintime(xs, S, start, goal, K=14, iters=None):
    """Optimise interior waypoints to MINIMISE traversal time through the learned speed field (endpoints
    clamped).  Min-time routes AROUND the slow mud; a straight line ploughs through it.

    The straight-line init sits on a SYMMETRY SADDLE (going over or under the disk is equally good, so the
    gradient there is ~0).  We break the symmetry with several ARC initialisations (a sine bulge to each
    side, a few amplitudes), descend each, and keep the lowest-time plan."""
    iters = iters or int(os.environ.get("CON2D_ITERS", "200"))
    straight = np.array([start + (goal - start) * k / K for k in range(K + 1)], float)
    d = goal - start; perp = np.array([-d[1], d[0]]); perp = perp / (np.linalg.norm(perp) + 1e-9)
    arch = np.sin(np.linspace(0, np.pi, K + 1))                # 0 at the ends, 1 in the middle
    best, best_t = straight, path_time(xs, S, straight)
    for side in (+1.0, -1.0):
        for amp in (2.0, 4.0):
            W0 = straight + side * amp * arch[:, None] * perp[None, :]
            W0 = np.clip(W0, 0.0, G - 1.0)
            W = _descend(xs, S, W0, K, iters)
            t = path_time(xs, S, W)
            if t < best_t:
                best, best_t = W, t
    return best


def mud_fraction(pts, samples=200):
    """Fraction of the path length spent inside the mud disk (lower = better routing)."""
    tot = mud = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, samples):
            p = a + (b - a) * t; w = np.linalg.norm(b - a) / samples
            tot += w; mud += w * in_mud(p)
    return mud / max(tot, 1e-9)


def main():
    rng = np.random.default_rng(42)
    print("=" * 80)
    print(f"  CONSTRAINED chained planning in 2D  (mud DISK centre ({MUD_CX:.0f},{MUD_CY:.0f}) r {MUD_R}"
          f"  cap {MUD_CAP} vs open {OPEN_CAP})")
    print("  training the tiny 2D NONLINEAR forward world model (same representation as the 1D fix) ...")
    fm = Forward2D(rng=rng)
    fm.train(int(os.environ.get("CON2D_STEPS", "1500000")))

    # cap fidelity: learned speed at open points vs inside the mud (true: ~1.5 vs ~0.3)
    probes = [(2, 2), (2, 6), (6, 6), (6.0, 5.5), (11, 6), (11, 11)]
    print("  learned speed  " + "  ".join(
        f"({p[0]:.0f},{p[1]:.0f}){'M' if in_mud(p) else ' '}:{fm.speed(p):.2f}" for p in probes)
          + f"   (true open {OPEN_CAP}, mud {MUD_CAP})")

    xs, S = speed_grid(fm)
    start = np.array([1.0, 6.0]); goal = np.array([11.0, 6.0])     # straight line crosses the mud centre
    K = 14
    planned = plan_mintime(xs, S, start, goal, K=K)
    straight = np.array([start + (goal - start) * k / K for k in range(K + 1)])

    print("=" * 80)
    print(f"  start ({start[0]:.0f},{start[1]:.0f}) -> goal ({goal[0]:.0f},{goal[1]:.0f})"
          f"   (the straight line passes through the mud disk)")
    print(f"  straight (naive)  mud-fraction {mud_fraction(straight):.2f}   "
          f"traversal-time {path_time(xs, S, straight):.1f}")
    print(f"  planned  (chain)  mud-fraction {mud_fraction(planned):.2f}   "
          f"traversal-time {path_time(xs, S, planned):.1f}   end ({planned[-1][0]:.1f},{planned[-1][1]:.1f})")
    routed = mud_fraction(planned) < 0.5 * mud_fraction(straight) + 1e-6
    print("-" * 80)
    print(f"  Read: the planner {'ROUTES AROUND' if routed else 'does NOT route around'} the learned mud zone"
          " -- it trades a longer path for a faster one,")
    print("  cutting the time through the slow mud, where the naive straight interpolation ploughs through.")
    print("  The constraint comes ENTIRELY from the learned world model (the speed field), not from a hand-")
    print("  coded obstacle.  Same representation (scaled RBF features + displacement target + mud oversample)")
    print("  that fixed the 1D case -- it ports to 2D.  Next step: lift this onto the arm's reachable plane.")
    print("=" * 80)

    if os.environ.get("CON2D_NOVIZ", "0") != "1":
        try:
            _plot(fm, xs, S, start, goal, straight, planned,
                  os.path.join(os.path.dirname(__file__), "chain_constrained_2d.png"))
        except Exception as e:
            print(f"  [viz] could not save the plot: {e}")


def _plot(fm, xs, S, start, goal, straight, planned, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    fig.patch.set_facecolor("#0e0e12"); ax.set_facecolor("#0e0e12")
    # the LEARNED speed field as the background (the model's own picture of the constraint)
    im = ax.imshow(S, origin="lower", extent=(0, G - 1, 0, G - 1), cmap="magma",
                   aspect="equal", alpha=0.95)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.set_label("learned speed", color="w")
    cb.ax.yaxis.set_tick_params(color="w"); plt.setp(cb.ax.get_yticklabels(), color="w")
    # the TRUE mud disk outline (ground truth) for reference
    th = np.linspace(0, 2 * np.pi, 100)
    ax.plot(MUD_CX + MUD_R * np.cos(th), MUD_CY + MUD_R * np.sin(th), "--", color="#66ddff", lw=1.2,
            label="true mud (cap %.1f)" % MUD_CAP)
    ax.plot(straight[:, 0], straight[:, 1], "o-", color="#ff5566", lw=1.6, ms=4,
            label="naive straight (through mud)")
    ax.plot(planned[:, 0], planned[:, 1], "o-", color="#66ff88", lw=1.8, ms=4,
            label="planned (routes around)")
    ax.scatter([start[0]], [start[1]], c="#ffffff", s=80, marker="s", zorder=5, label="start")
    ax.scatter([goal[0]], [goal[1]], c="#ffdd33", s=120, marker="*", zorder=5, label="goal")
    ax.set_title("2D constrained chain: learned speed field + min-time plan", color="w")
    ax.tick_params(colors="w"); [s.set_color("#555") for s in ax.spines.values()]
    ax.set_xlim(0, G - 1); ax.set_ylim(0, G - 1)
    ax.legend(facecolor="#1a1a22", edgecolor="#444", labelcolor="w", fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(path, dpi=120, facecolor=fig.get_facecolor())
    print(f"  [viz] plot saved -> {path}")


if __name__ == "__main__":
    main()
