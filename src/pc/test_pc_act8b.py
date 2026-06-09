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
CONTACT_R = 1.5      # pointer pushes the object when within this distance

class World1D:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.lo, self.hi = W / 8.0, W * 7.0 / 8.0
        self.obj = float(self.rng.uniform(self.lo, self.hi))
        self.target = float(self.rng.uniform(self.lo, self.hi))
        self.vel = 0.0

    def scatter(self, with_target=False):
        self.obj = float(self.rng.uniform(self.lo, self.hi)); self.vel = 0.0
        if with_target:
            self.target = float(self.rng.uniform(self.lo, self.hi))

    def push(self, pointer, pointer_vel, finger=1.0):
        """Move the object.  The object couples to the pointer's velocity GRADED by the
        finger extension (finger∈[0,1]) and only within contact range.  finger=1 →
        full carry (step 3 default); finger=0 → no transfer even on touch (step 4 must
        LEARN to extend the finger).  No impulse."""
        if abs(pointer - self.obj) < CONTACT_R:
            self.obj = float(np.clip(self.obj + finger * pointer_vel, 0.0, W - 1))
            return finger > 0.05
        return False

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
# Step 3: learned pointer→object COUPLING model J(p−obj).  Babble: jiggle the pointer
# at random offsets from the object, observe how much the object moves (Δobj/a), and
# learn J(d) — the Jacobian "does my motion move the object?" (≈1 in contact, ≈0 out).
# The manipulation action sends the OBJECT-goal error through this learned J.
# --------------------------------------------------------------------------- #
class Coupling:
    def __init__(self, hid=24, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 0.6, (hid, 1)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 0.3, hid); self.b2 = 0.0
        self.lr = lr; self.rng = rng

    def _scale(self, d):
        return np.array([d / CONTACT_R])              # normalise the offset

    def predict(self, d):
        h = np.tanh(self.W1 @ self._scale(d) + self.b1)
        return float(self.W2 @ h + self.b2), h

    def babble(self, world, steps):
        for _ in range(steps):
            obj = float(self.rng.uniform(world.lo, world.hi))
            d = float(self.rng.uniform(-(CONTACT_R + 2), CONTACT_R + 2))
            a = float(self.rng.uniform(-1.0, 1.0))
            world.obj = obj
            moved = world.push(obj + d, a)            # observe Δobj for this (d, a)
            dobj = world.obj - obj
            target = dobj / a if abs(a) > 1e-3 else 0.0   # observed coupling J
            y, h = self.predict(d)
            err = y - target
            self.W2 -= self.lr * err * h; self.b2 -= self.lr * err
            dh = (self.W2 * err) * (1 - h ** 2)
            self.W1 -= self.lr * np.outer(dh, self._scale(d)); self.b1 -= self.lr * dh

    def scramble(self):
        self.W1 = self.rng.normal(0, 0.6, self.W1.shape)
        self.W2 = self.rng.normal(0, 0.6, self.W2.shape)


class CouplingF:
    """Step 4: coupling that also depends on the FINGER — J(d, f) ≈ f when in contact,
    ≈0 out of contact.  Babble random (d, f, a), observe Δobj/a (= the finger-graded
    contact coupling) and learn it.  Lets the agent discover that extending the finger
    in contact is what makes the object follow — the grip is LEARNED, not wired."""
    def __init__(self, hid=32, lr=0.02, rng=None):
        rng = rng or np.random.default_rng()
        self.W1 = rng.normal(0, 0.6, (hid, 2)); self.b1 = np.zeros(hid)
        self.W2 = rng.normal(0, 0.3, hid); self.b2 = 0.0
        self.lr = lr; self.rng = rng

    def _x(self, d, f):
        return np.array([d / CONTACT_R, f])

    def predict(self, d, f):
        h = np.tanh(self.W1 @ self._x(d, f) + self.b1)
        return float(self.W2 @ h + self.b2), h

    def babble(self, world, steps):
        for _ in range(steps):
            obj = float(self.rng.uniform(world.lo, world.hi))
            d = float(self.rng.uniform(-(CONTACT_R + 2), CONTACT_R + 2))
            a = float(self.rng.uniform(-1.0, 1.0))
            f = float(self.rng.uniform(0.0, 1.0))
            world.obj = obj
            world.push(obj + d, a, finger=f)
            target = (world.obj - obj) / a if abs(a) > 1e-3 else 0.0
            y, h = self.predict(d, f)
            err = y - target
            self.W2 -= self.lr * err * h; self.b2 -= self.lr * err
            dh = (self.W2 * err) * (1 - h ** 2)
            self.W1 -= self.lr * np.outer(dh, self._x(d, f)); self.b1 -= self.lr * dh

    def scramble(self):
        self.W1 = self.rng.normal(0, 0.6, self.W1.shape)
        self.W2 = self.rng.normal(0, 0.6, self.W2.shape)


# --------------------------------------------------------------------------- #
# Step 2: error-driven SELF-movement to a GOAL PRIOR (proprioceptive goal-reach).
# A tiny PC net: goal(prior) → belief → pos(proprioception).  The forward model
# belief→pos is LEARNED by babble (goal == current).  At run time the goal is clamped
# (= the LEARNED-perceived object), and the action moves the pointer to REDUCE the
# proprioceptive prediction error: p -= gain · pos.epsilon.  The agent never computes
# (goal − p); the move emerges from error-minimisation on the learned model — scramble
# the weights and it fails (proof it is learned, not a wired coordinate controller).
# --------------------------------------------------------------------------- #
class ProprioReach:
    def __init__(self, rng):
        net = PCNetwork(eta_inf=0.1, n_relax=40, eps_tol=1e-6, eta_learn=0.02,
                        gamma=0.3, w_clip=3.0, rng=rng)
        self.goal = net.add(SensorNode("goal", dim=1))
        self.belief = net.add(PCNode("belief", dim=4, activation="identity",
                                     eta_temporal=0.0, rng=rng))
        self.pos = net.add(SensorNode("pos", dim=1))
        net.connect("goal", "belief", ConnType.UP, pressure_scale=1.0)
        net.connect("belief", "pos", ConnType.UP, pressure_scale=1.0)
        self.net = net; self.rng = rng

    def babble(self, steps):
        for _ in range(steps):
            v = float(self.rng.uniform(0, 1))      # goal == current → learn fwd model
            self.goal.set_input(np.array([v])); self.pos.set_input(np.array([v]))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()

    def scramble(self):
        conns = self.net._connections
        conns = conns.values() if hasattr(conns, "values") else conns
        for conn in conns:
            conn.W = self.rng.normal(0, 0.5, conn.W.shape)

    def error(self, p_norm, goal_norm):
        self.goal.set_input(np.array([goal_norm])); self.pos.set_input(np.array([p_norm]))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return float(self.net.node("pos").epsilon[0])


# --------------------------------------------------------------------------- #
def render(step, total, world, phi, perceived, seen, sensor_err, pointer=None, target=None):
    o = int(round(phi))
    row = ["·"] * W
    if target is not None:
        tt = int(round(target))
        if 0 <= tt < W:
            row[tt] = "+"          # the object's goal (step 3)
    ob = int(round(world.obj))
    if 0 <= ob < W:
        row[ob] = "O"
    if perceived is not None:
        pp = int(round(perceived))
        if 0 <= pp < W and pp != ob:
            row[pp] = "x"          # where the NET thinks the object is
    if pointer is not None:
        pt = int(round(pointer))
        if 0 <= pt < W and row[pt] == "·":
            row[pt] = "P"          # the agent's effector (reaches the perceived object)
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
    GOALMODE = os.environ.get("ACT8B_GOAL", "obj").lower()       # obj | none | scramble
    SCALE = float(os.environ.get("ACT8B_SCALE", "1.0"))
    DELAY = float(os.environ.get("ACT8B_DELAY", "0.0"))
    GAIN = float(os.environ.get("ACT8B_GAIN", "3.0"))   # fovea action gain
    REACH_GAIN = 2.0                                     # pointer error-driven gain
    rng = np.random.default_rng(0)

    STEP = int(os.environ.get("ACT8B_STEP", "3"))        # 2 = reach demo, 3 = manipulate
    net, cells, h1 = build_net(rng)
    readout = Readout(in_dim=len(h1) * 6, rng=np.random.default_rng(3))
    reach = ProprioReach(np.random.default_rng(4))      # step 2: pointer-reach subnet
    objgoal = ProprioReach(np.random.default_rng(6))    # step 3: OBJECT-goal prior (ε_obj)
    coupling = Coupling(rng=np.random.default_rng(7))   # step 3: learned pointer→object J
    couplingF = CouplingF(rng=np.random.default_rng(8)) # step 4: J(d, finger)
    world = World1D(seed=1)
    pointer = (W - N) / 2.0 + N / 2.0                    # the agent's effector

    DEV = int(3000 * SCALE)                     # developmental phase (learn net+readout)
    TEST = int(3000 * SCALE)                    # active test (error-driven fovea)
    total = DEV + TEST
    phi = (W - N) / 2.0

    print(f"act8b step 1+2 — learned perception + error-driven fovea AND pointer reach")
    print(f"  world={W} fovea={N}  perceive={PERCEIVE}  goal={GOALMODE}  dev={DEV} test={TEST}")

    se_hist, in_view, world_err, act = [], 0, 0.0, 0
    fov_v = 0.0; SMOOTH = 0.3                    # fovea velocity smoothing (momentum)
    reach.babble(int(4000 * SCALE))             # learn pointer proprioceptive fwd model
    objgoal.babble(int(9000 * SCALE))           # learn object proprioceptive fwd model
    coupling.babble(world, int(6000 * SCALE))   # learn pointer→object coupling J(p−obj)
    if STEP >= 4:
        couplingF.babble(world, int(8000 * SCALE))   # learn J(d, finger) for the grip
    if GOALMODE == "scramble":
        coupling.scramble(); couplingF.scramble()    # control: break the learned coupling
    reach_d = []                                # |pointer - object| over the test
    manip_d = []                                # |object - target| over the test (step 3)
    deliveries = 0                              # step 3: object delivered to target count
    fing_contact, fing_far = [], []             # step 4: finger extension in/out of contact
    REACH_GAIN_P = 1.2; PUSH_GAIN = 2.5         # step-3 reach / push gains

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
            # active test.  STEP 2: object drifts, pointer reaches it.  STEP 3: object
            # lies still, the pointer reaches it AND pushes it to the target — both via
            # error-driven action.  The FOVEA tracks the object by its error gradient.
            if STEP == 2:
                world.drift()
            elif step == DEV or abs(world.obj - world.target) < 2.5:   # learned-model precision
                # episode (re)start: fresh object+target; put the gaze on the object and
                # the hand on it (isolates the new PUSH mechanism; reach is step-2-proven).
                if step > DEV:
                    deliveries += 1                    # object reached target → delivered
                world.scatter(with_target=True)
                phi = float(np.clip(world.obj - N / 2.0, PHI_MIN, PHI_MAX))
                pointer = float(world.obj)
            disp = -fovea_gradient(cells)
            fov_v = (1 - SMOOTH) * (GAIN * disp) + SMOOTH * fov_v   # momentum
            fov_v = float(np.clip(fov_v, -2.0, 2.0))
            phi = float(np.clip(phi + fov_v, PHI_MIN, PHI_MAX))
            act += 1
            in_view += int(seen)
            if perceived is not None:
                world_err += abs(perceived - world.obj)

            obj_before = world.obj
            if perceived is not None:
                pn = pointer / (W - 1)
                # (a) REACH: keep the hand on the perceived object (step-2 mechanism).
                goal_reach = perceived if (STEP == 2 and GOALMODE == "none") else perceived
                eps_p = reach.error(pn, float(np.clip(goal_reach, 0, W - 1)) / (W - 1))
                a_reach = -(REACH_GAIN_P if STEP == 3 else REACH_GAIN) * (W - 1) * eps_p
                a = a_reach
                finger = 1.0                           # step 3: always-on coupling
                if STEP >= 3 and GOALMODE != "none":
                    # (b) PUSH: send the OBJECT-goal error ε_obj through the LEARNED
                    # coupling.  a_push = −gain·J·ε_obj — error-driven, no (goal−obj).
                    eps_obj = objgoal.error(perceived / (W - 1),
                                            float(np.clip(world.target, 0, W - 1)) / (W - 1))
                    d = pointer - perceived
                    if STEP >= 4:
                        # (c) LEARNED GRIP: extend the finger when there is an object-goal
                        # error to fix AND the learned model says gripping HERE couples
                        # (J(d, f=1) high → in contact).  Out of contact → finger stays
                        # retracted.  The grip is driven by error × the learned coupling.
                        J1, _ = couplingF.predict(d, 1.0)
                        drive = 6.0 * abs(eps_obj) * (W - 1) * float(np.clip(J1, 0, 1))
                        finger = float(1.0 / (1.0 + np.exp(-(drive - 2.0))))
                        J, _ = couplingF.predict(d, finger)
                    else:
                        J, _ = coupling.predict(d)
                    a += -PUSH_GAIN * (W - 1) * J * eps_obj
                # cap the step BELOW the contact radius so the hand stays on the object
                # while pushing (same lesson as the 2D grip: move < contact each step).
                a = float(np.clip(a, -1.3, 1.3))
                in_contact = abs(pointer - world.obj) < CONTACT_R     # before moving
                if STEP >= 4:
                    # A committed GRIP (finger>0.5) holds the hand RIGIDLY on the object:
                    # hand and object move together by a (no slip → no desync).  Out of
                    # grip the object stays.  The LEARNED parts are perception, the grip
                    # DECISION (finger via the learned coupling), and the push (eps_obj).
                    if finger > 0.5 and in_contact:
                        world.obj = float(np.clip(world.obj + a, 0.0, W - 1))
                    pointer = float(np.clip(pointer + a, 0.0, W - 1))
                else:
                    pointer = float(np.clip(pointer + a, 0.0, W - 1))
                    if STEP == 3:
                        world.push(pointer, a)         # step-3 push-on-touch (finger=1)
            # Efference-copy gaze pursuit: the agent moved the object by a known amount,
            # so slide the fovea along with it.  Keeps the manipulated object centred
            # even when the net predicts it so well there is no error gradient to follow
            # (the fovea-freezes-during-manipulation bug).  No oracle — it's our own act.
            if STEP >= 3:
                phi = float(np.clip(phi + (world.obj - obj_before), PHI_MIN, PHI_MAX))
                if os.environ.get("ACT8B_DEBUG") == "1" and STEP >= 4 and (step - DEV) % 80 == 0:
                    print(f"[dbg {step-DEV}] phi={phi:5.1f} obj={world.obj:5.1f} "
                          f"perc={perceived if perceived is None else round(perceived,1)} "
                          f"tgt={world.target:5.1f} p={pointer:5.1f} "
                          f"fovgrad={disp:+.2f} fing={finger:.2f} a={a:+.2f}", flush=True)
            reach_d.append(abs(pointer - world.obj))
            manip_d.append(abs(world.obj - world.target))
            if STEP >= 4 and perceived is not None:
                (fing_contact if abs(pointer - world.obj) < CONTACT_R
                 else fing_far).append(finger)

            if not HEADLESS:
                render(step, total, world, phi, perceived, seen, r["sensor_error"],
                       pointer, world.target if STEP == 3 else None)
                if DELAY > 0:
                    time.sleep(DELAY)

    q = max(1, len(se_hist) // 10)
    rq = max(1, len(reach_d) // 10)
    print("=" * 64)
    print(f"  act8b step 1+2 summary   (perceive={PERCEIVE}  goal={GOALMODE})")
    print(f"  sensor_error: {np.mean(se_hist[:q]):.3f} → {np.mean(se_hist[-q:]):.3f}"
          f"   [drops → the net learned the world model]")
    print(f"  STEP1  fovea (error-driven) kept object in view: {100.0*in_view/max(1,act):.1f}%")
    print(f"  STEP1  readout retinal error (EMA): {readout.err_ema*(N-1):.2f}px in {N}px window")
    print(f"  STEP1  perceived ({PERCEIVE}) vs true object: {world_err/max(1,act):.2f}px mean")
    if reach_d:
        print(f"  STEP2  pointer→object |p-obj|: start {np.mean(reach_d[:rq]):.1f}px → "
              f"end {np.mean(reach_d[-rq:]):.1f}px   [error-driven reach to perceived obj]")
    if STEP >= 3 and manip_d:
        lbl = "STEP4" if STEP >= 4 else "STEP3"
        extra = ""
        if STEP >= 4 and fing_contact:
            extra = (f"   finger: in-contact {np.mean(fing_contact):.2f} vs "
                     f"out {np.mean(fing_far) if fing_far else 0:.2f}"
                     f" [LEARNED grip: extends only in contact]")
        print(f"  {lbl}  object DELIVERED to target: {deliveries}×   (mean |obj-tgt| "
              f"{np.mean(manip_d):.1f}px){extra}   [goal={GOALMODE}]")
    print(f"  [net perception + error-driven action; scramble coupling → manipulation fails]")
    print("=" * 64)


if __name__ == "__main__":
    main()
