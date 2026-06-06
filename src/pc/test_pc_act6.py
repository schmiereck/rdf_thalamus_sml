r"""
test_pc_act5.py — Phase 2 active inference: push object to target.

Upgrades from test_pc_act4:
  physics      : 1-D physics world with mass, friction, wall bounce
  tap action   : PremotorModule issues tap commands driven by HiddenHierarchy
  task         : push the single object to a fixed target; hold it there
  RGB sensors  : object row carries 3 channels [pos, object_val, target_val]
  flash sensor : 1 dedicated sensor node (1.0 = success, else 0.0)
  motor dim=3  : [v_fovea/MAX_V, v_ptr/MAX_VP, tap_gate]
  reward       : RPE = normalised proximity to target − EMA baseline

Architecture additions over act4:
  PremotorModule — one PCNode "pm_0" connected from HiddenHierarchy abstract
                   output via UP connections.  After phase_predict, pm_0.pi[0]
                   encodes the hierarchy's intended tap command; the tap gate is
                   derived from it.  PremotorModule sits between the abstract
                   hierarchy and the motor sensor — it never connects directly to
                   the raw visual sensors.

  Flash sensor   — connected from the top hidden layer (hierarchy predicts success).

World schematic
---------------
  Object row  [pos, obj, tgt]  ← 3-channel, dim=3 each pixel
  Pointer row [pos, ptr]       ← 2-channel, dim=2 each pixel
  Flash sensor[flash]          ← 1-channel, 1.0 when success

  The physical world is WORLD_W = 3*N_INPUTS pixels wide; the N_INPUTS-wide
  visual/fovea window slides over it (phi = window left-edge offset).  Object
  and pointer both live in world coords and may roam the whole world.
  Target is fixed at 3/4 of the world (world pixel 35 for WORLD_W=48).
  Object starts near left edge, bounces with light friction.
  Pointer (force-controlled) can TAP the object: if tap_gate > TAP_THRESHOLD
  and the pointer is within TAP_RANGE of the object, the object receives an
  impulse that pushes it away from the pointer (billiard-ball model).
  Success = object at rest within 1.5 px of target → flash + reward bonus.
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


# ---------------------------------------------------------------------------
# Goal module — standalone PC autoencoder with a learned latent "language".
# ---------------------------------------------------------------------------
# Encodes a desired object WORLD-position (shown as a coarse blob image) into a
# small latent code, and decodes it back to a position.  Used as the goal prior:
# the active phase decodes the "desired object position" from the shown target
# (or from a DREAMED latent) and the finger transports the object there — the
# dark-room antidote validated in test_pc_goal_module / test_pc_push_goal.
# It is its OWN module (own net) so goals can later be dreamed in its latent space.
class GoalModule:
    def __init__(self, world_w: float, img: int = 16, latent: int = 3,
                 activation: str = "identity",
                 rng: np.random.Generator | None = None) -> None:
        self.world_w = float(world_w)
        self.G = img
        self.rng = rng or np.random.default_rng()
        net = PCNetwork(eta_inf=0.1, n_relax=60, eps_tol=1e-6, alpha=1.0,
                        beta=1.0, gamma=0.3, eta_learn=0.01, lambda_decay=0.0,
                        w_clip=3.0, rng=self.rng)
        self.img_node = net.add(SensorNode("g_img", dim=img))
        self.z_node   = net.add(PCNode("g_z", dim=latent, activation=activation,
                                       eta_temporal=0.0, rng=self.rng))
        net.connect("g_z", "g_img", ConnType.UP, pressure_scale=1.0)  # decoder
        self.net = net

    def _blob(self, world_pos: float) -> np.ndarray:
        c = world_pos / self.world_w * (self.G - 1)
        x = np.arange(self.G)
        return np.exp(-0.5 * ((x - c) / 1.0) ** 2)

    def _com(self, img: np.ndarray) -> float:
        img = np.clip(img, 0.0, None)
        s = img.sum()
        if s < 1e-6:
            return self.world_w / 2.0
        return float((np.arange(self.G) * img).sum() / s / (self.G - 1) * self.world_w)

    def pretrain(self, steps: int = 5000) -> None:
        """Babble across the world: learn the position↔latent autoencoder."""
        pos = float(self.rng.uniform(0.0, self.world_w))
        for _ in range(steps):
            pos = float(np.clip(pos + self.rng.normal(0.0, self.world_w * 0.05),
                                0.0, self.world_w))
            self.img_node.set_input(self._blob(pos))
            self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
            self.net.phase_learn(); self.net.commit_step()

    def decode_target(self, target_world: float) -> float:
        """Show a target image, return the decoded desired world-position."""
        self.z_node.unclamp()
        self.img_node.set_input(self._blob(target_world))
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        return self._com(self.img_node.pi)

    def encode(self, target_world: float) -> np.ndarray:
        self.decode_target(target_world)
        return self.z_node.mu.copy()

    def decode_dream(self, z: np.ndarray) -> float:
        """Decode a goal specified purely in latent space (no image)."""
        self.img_node.unclamp()
        self.z_node.clamp(z)
        self.net.phase_predict(); self.net.phase_error(); self.net.phase_relax()
        d = self._com(self.img_node.pi)
        self.z_node.unclamp()
        self.img_node.clamp(self._blob(self.world_w / 2.0))
        return d

    def decode_error(self, n: int = 15) -> float:
        """Mean |decoded - target| across the world (sanity check)."""
        errs = [abs(self.decode_target(t) - t)
                for t in np.linspace(0.1 * self.world_w, 0.9 * self.world_w, n)]
        return float(np.mean(errs))


# ---------------------------------------------------------------------------
# Curiosity planner — the agent DREAMS its own next goal.
# ---------------------------------------------------------------------------
# The next PC layer above the goal module: instead of an externally-shown target,
# the planner proposes the next goal purely in the goal module's latent space,
# preferring NOVEL (recently-unvisited) regions — self-directed exploration.  It
# replaces act6's random target relocation, so the agent sets its OWN goals and the
# validated goal-prior + finger machinery transports the object to each.  Distance/
# density novelty (validated in test_pc_planner_curiosity.py); a short visited-memory
# keeps it exploring indefinitely ("go where you haven't been recently").
class CuriosityPlanner:
    def __init__(self, goal_mod: "GoalModule", lo: float, hi: float, *,
                 k: int = 24, memory: int = 20,
                 rng: np.random.Generator | None = None) -> None:
        self.gm = goal_mod
        self.lo, self.hi = float(lo), float(hi)
        self.k, self.memory = k, memory
        self.rng = rng or np.random.default_rng()
        # Encode a position grid → the goal module's latent manifold (for fast
        # on-manifold candidate proposal by interpolation).
        self._grid  = np.linspace(0.03 * goal_mod.world_w, 0.97 * goal_mod.world_w, 60)
        self._zgrid = np.array([goal_mod.encode(p) for p in self._grid])
        self._visited: list[np.ndarray] = []   # recent dreamed latents

    def _latent(self, pos: float) -> np.ndarray:
        return np.array([np.interp(pos, self._grid, self._zgrid[:, k])
                         for k in range(self._zgrid.shape[1])])

    def _novelty(self, z: np.ndarray) -> float:
        if not self._visited:
            return 1.0
        return float(min(np.linalg.norm(z - s) for s in self._visited))

    def next_goal(self, current_pos: float | None = None) -> float:
        """Dream the next goal: most-novel of K on-manifold candidates → decode."""
        cands_pos = self.rng.uniform(self.lo, self.hi, self.k)
        cands_z   = [self._latent(p) for p in cands_pos]
        z = cands_z[int(np.argmax([self._novelty(c) for c in cands_z]))]
        self._visited.append(z)
        if len(self._visited) > self.memory:
            self._visited.pop(0)
        return float(np.clip(self.gm.decode_dream(z), self.lo, self.hi))


# ---------------------------------------------------------------------------
# 1-D Physics World
# ---------------------------------------------------------------------------

TAP_THRESHOLD = 0.4   # (legacy) minimum tap_gate to apply impulse
FINGER_DOWN   = 0.5   # finger extension above which it contacts the surface


class PhysicsWorld1D:
    """
    1-D physics world: one moving object, one fixed target, tap interaction.

    Object dynamics: velocity integration with friction; elastic wall bounce
    (with a little energy loss so the object eventually settles).

    Tap: if tap_gate > TAP_THRESHOLD and pointer within TAP_RANGE of object,
    the object receives an impulse that pushes it away from the pointer.
    """

    def __init__(
        self,
        n: int,
        obj_friction:    float = 0.025,
        tap_impulse:     float = 2.5,
        tap_range:       float = 2.5,
        finger_radius:   float = 1.5,   # reach within which the finger grips the object
        drag_slip:       float = 0.0,   # 0 = rigid carry; 1 = no coupling
        flash_duration:  int   = 8,
        dwell_steps:     int   = 12,
        target_frac:     float = 0.75,
        kick_after:      int   = 60,    # steps without net progress before a kick
        kick_idle_thr:   float = 1.5,   # net displacement below this = "stuck"
        kick_margin:     float = 1.0,   # keep kick destinations off the walls
        kick_gain:       float = 1.2,   # impulse strength toward the random dest
        kick_min_dist:   float = None,  # min destination distance (default n*0.4)
        seed:            int   = 0,
    ) -> None:
        self.n             = n
        self.obj_friction  = obj_friction
        self.tap_impulse   = tap_impulse
        self.tap_range     = tap_range
        self.finger_radius = finger_radius
        self.drag_slip     = drag_slip
        self.kick_after    = kick_after
        self.kick_idle_thr = kick_idle_thr
        self.kick_margin   = kick_margin
        self.kick_gain     = kick_gain
        self.kick_min_dist = kick_min_dist if kick_min_dist is not None else n * 0.4
        self.flash_duration = flash_duration
        self.dwell_steps    = dwell_steps
        # Centered 3/4 band of the world: 1/8 .. 7/8 (width = 3/4, centered).
        # Object spawns, kick destinations and post-flash target positions are
        # all drawn from this band so the action stays in the central 3/4.
        self.range_lo      = n / 8.0
        self.range_hi      = n * 7.0 / 8.0
        self.target_pos    = float(round(target_frac * (n - 1)))
        # Optional callable () -> next target world-position.  When set (e.g. by a
        # CuriosityPlanner) it REPLACES random relocation so goals are self-dreamed.
        self.target_provider = None
        self._rng          = np.random.default_rng(seed)

        self.obj_pos:    float = 0.0
        self.obj_vel:    float = 0.0
        self.flash_timer: int  = 0
        self.dwell_timer: int  = 0     # >0 = object resting quietly on the target
        self._t:         int   = 0     # global step counter (never reset)
        self._kick_ref_pos:  float = 0.0  # last position where real progress seen
        self._kick_ref_step: int   = 0    # _t at that moment
        self.reset()

    def reset(self, fixed: bool = False, static: bool = False,
              reposition: bool = True) -> None:
        """Reset the object.

        fixed      — deterministic start (left quarter, vel=0.8) for diagnostics.
        static     — zero initial velocity (object only moves via tap/kick).
        reposition — if False, keep the current obj_pos (object persists across
                     episodes; motion comes only from taps and auto-kicks).

        When repositioning, the object is placed uniformly across the FULL world
        width (minus a small margin), not just the left third — so training
        covers the whole world instead of a narrow band.
        """
        lo, hi = self.range_lo, self.range_hi
        if fixed:
            self.obj_pos = float(self.n // 4)
            self.obj_vel = 0.8
        else:
            if reposition:
                self.obj_pos = float(self._rng.uniform(lo, hi))
            if static:
                self.obj_vel = 0.0
            else:
                # Use _do_kick so every episode start sends the object toward a
                # fresh random world-spanning destination — guarantees coverage
                # in every phase including passive, not just when the idle timer
                # fires.
                self._do_kick()
        self.flash_timer    = 0
        self.dwell_timer    = 0
        self._kick_ref_pos  = self.obj_pos
        self._kick_ref_step = self._t

    def _do_kick(self) -> None:
        """Send the object toward a random destination across the world.

        The impulse magnitude is tuned to the friction so the object roughly
        coasts to the chosen destination (travel ≈ v0 / friction), giving
        varied, world-spanning trajectories rather than a fixed shove.
        """
        lo, hi = self.range_lo, self.range_hi
        dest = float(self._rng.uniform(lo, hi))
        # Ensure the destination is a meaningful distance away.
        if abs(dest - self.obj_pos) < self.kick_min_dist:
            direction = 1.0 if self.obj_pos < self.n / 2.0 else -1.0
            dest = float(np.clip(self.obj_pos + direction * self.kick_min_dist, lo, hi))
        self.obj_vel = (dest - self.obj_pos) * self.obj_friction * self.kick_gain

    def step(self, finger_y: float, pointer_pos: float,
             pointer_vel: float = 0.0) -> dict:
        """Advance physics one frame.

        The actuator is a FINGER that extends (finger_y → contact) and, while
        touching the object, drags it along with the pointer's sideways motion —
        graded velocity control, not an impulse.  Returns
        {contact, dragged, success, flash, kicked}.
        """
        contact = False
        dragged = False
        kicked = False

        # ---- Dwell: quiet rest on the target after a hit ----
        # Instead of scrambling the world the instant the object reaches the
        # target, the object is pinned ON the target for `dwell_steps` frames:
        # zero velocity, taps ignored, the scene perfectly steady.  This is a
        # genuine low-surprise rest that the reward keeps reinforcing — the
        # achieved goal-state becomes attractive instead of being destroyed on
        # contact.  Only when the dwell ends is the object sent off and the
        # target relocated.
        if self.dwell_timer > 0:
            self.dwell_timer -= 1
            self.obj_pos = self.target_pos
            self.obj_vel = 0.0
            if self.flash_timer > 0:
                self.flash_timer -= 1
            self._t += 1
            if self.dwell_timer == 0:
                # Dwell over: send the object off and move the target to a fresh
                # random spot, so success must be re-earned at a new location.
                self._do_kick()
                self.relocate_target()
                self._kick_ref_pos  = self.obj_pos
                self._kick_ref_step = self._t
                kicked = True
            return {"contact": False, "dragged": False, "success": True,
                    "flash": self.flash_timer > 0, "kicked": kicked}

        # ---- Finger contact + drag ----
        # When the finger is extended (finger_y > FINGER_DOWN) and within reach of
        # the object, the object's velocity is coupled toward the pointer's
        # sideways velocity (graded carry; drag_slip=0 → rigid).  No impulse:
        # extending onto a still pointer (pointer_vel≈0) just holds the object in
        # place — your "direct hit ⇒ do nothing".  While held the object does not
        # feel friction; on release it keeps the finger's velocity and coasts.
        contact = (finger_y > FINGER_DOWN
                   and abs(pointer_pos - self.obj_pos) < self.finger_radius)
        if contact:
            self.obj_vel = ((1.0 - self.drag_slip) * pointer_vel
                            + self.drag_slip * self.obj_vel)
            dragged = abs(self.obj_vel) > 1e-6
            self.obj_pos += self.obj_vel
        else:
            self.obj_vel *= (1.0 - self.obj_friction)
            self.obj_pos += self.obj_vel

        # Elastic wall bounce with slight energy loss
        if self.obj_pos <= 0.0:
            self.obj_pos = 0.0
            self.obj_vel = abs(self.obj_vel) * 0.85
        elif self.obj_pos >= self.n - 1:
            self.obj_pos = float(self.n - 1)
            self.obj_vel = -abs(self.obj_vel) * 0.85

        at_target = abs(self.obj_pos - self.target_pos) < 1.5
        at_rest   = abs(self.obj_vel) < 0.3
        success   = at_target and at_rest
        if success and self.flash_timer == 0:
            # Begin the quiet dwell (handled at the top of the next step) instead
            # of an immediate kick + target relocation.
            self.flash_timer = self.flash_duration
            self.dwell_timer = self.dwell_steps
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Auto-kick (recurring): track NET progress, not displacement from a
        # fixed start.  Whenever the object actually moves more than
        # kick_idle_thr we refresh the reference; if it fails to make that much
        # progress within kick_after steps (e.g. it only jitters in place, or a
        # tap keeps pinning it), we kick it toward a fresh random destination.
        # This fires as often as needed and is immune to the small back-and-forth
        # wandering that previously masked "stuck" states.
        self._t += 1
        if kicked:
            # A flash-kick already happened this step; refresh the progress
            # reference so the idle counter starts fresh from the new motion.
            self._kick_ref_pos  = self.obj_pos
            self._kick_ref_step = self._t
        elif abs(self.obj_pos - self._kick_ref_pos) > self.kick_idle_thr:
            self._kick_ref_pos  = self.obj_pos
            self._kick_ref_step = self._t
        elif self._t - self._kick_ref_step >= self.kick_after:
            self._do_kick()
            self._kick_ref_pos  = self.obj_pos
            self._kick_ref_step = self._t
            kicked = True

        return {"contact": contact, "dragged": dragged, "success": success,
                "flash": self.flash_timer > 0, "kicked": kicked}

    # ------------------------------------------------------------------

    def render_obj_channel(self) -> list[float]:
        """2-pixel blob at object position (best-behaving width in act4)."""
        return _flat_blob(self.obj_pos, self.n, width=2)

    def render_target_channel(self) -> list[float]:
        """2-pixel marker at target position (always visible)."""
        return _flat_blob(self.target_pos, self.n, width=2)

    def world_com(self) -> float:
        """Centre-of-mass of the object in world coords."""
        return self.obj_pos

    def relocate_target(self) -> None:
        """Move the target to a fresh spot in the centered 3/4 band.  If a
        target_provider is set (the planner), the next goal is DREAMED, not random."""
        if self.target_provider is not None:
            self.target_pos = float(round(np.clip(
                self.target_provider(), self.range_lo, self.range_hi)))
        else:
            self.target_pos = float(round(
                self._rng.uniform(self.range_lo, self.range_hi)))


def _flat_blob(center: float, n: int, width: int = 1) -> list[float]:
    """Anti-aliased flat blob of given width in a world of n pixels."""
    frame = np.zeros(n)
    half = (width - 1) / 2.0
    lo, hi = center - half, center + half
    for i in range(n):
        if lo <= i <= hi:
            frame[i] = 1.0
        elif lo - 1 < i < lo:
            frame[i] = i - (lo - 1)
        elif hi < i < hi + 1:
            frame[i] = (hi + 1) - i
    return frame.tolist()


# ---------------------------------------------------------------------------
# Network construction
# ---------------------------------------------------------------------------

def build_network(
    rng: np.random.Generator,
    n_inputs:      int   = 16,
    n_layers:      int   = 3,
    base_dim:      int   = 4,
    dim_growth:    int   = 2,
    lateral_steps: int   = 0,
    eta_inf:       float = 0.05,
    n_relax:       int   = 40,
    eta_learn:     float = 0.002,
    gamma:         float = 0.3,
) -> tuple[PCNetwork, list[SensorNode], list[SensorNode],
           SensorNode, SensorNode]:
    """
    Build the act5 network with four PCModules:

      VisualCortex    — 3-channel obj sensors + 2-channel ptr sensors, hexagonally
                        coupled; plus flash (dim=1) and motor (dim=3) sensors.
                        in-ports : obj_input [dim=3], ptr_input [dim=2], flash_in, motor_in
                        out-ports: obj_row, ptr_row

      HiddenHierarchy — pyramidal hidden layers receiving from VisualCortex.
                        in-ports : visual_in (layer-1 nodes)
                        out-ports: abstract_out (top layer)

      PremotorModule  — one PCNode "pm_0" (dim=2, tanh) receiving from the top
                        of HiddenHierarchy.  pm_0.pi[0] drives the tap gate.
                        in-ports : abstract_in (top hidden IDs)
                        out-ports: tap_out (["pm_0"])

      MotorModule     — 1 SensorNode, dim=3: [v_fovea, v_ptr, tap_gate].
                        in-ports : efference_in

    Returns (net, object_sensors, pointer_sensors, flash_sensor, motor_sensor).
    """
    net = PCNetwork(
        eta_inf=eta_inf,
        n_relax=n_relax,
        eps_tol=1e-5,
        alpha=1.0,
        beta=1.0,
        gamma=gamma,
        eta_learn=eta_learn,
        lambda_decay=0.0,
        w_clip=3.0,
        rng=rng,
    )

    # ------------------------------------------------------------------
    # VisualCortex
    # ------------------------------------------------------------------
    visual_cortex = PCModule("VisualCortex")

    # Object sensors: dim=3 = [retinal_pos, object_val, target_val]
    object_sensors: list[SensorNode] = [
        net.add(SensorNode(f"so{i}", dim=3)) for i in range(n_inputs)
    ]
    # Pointer sensors: dim=2 = [retinal_pos, pointer_val]
    pointer_sensors: list[SensorNode] = [
        net.add(SensorNode(f"sp{i}", dim=2)) for i in range(n_inputs)
    ]
    obj_ids = [f"so{i}" for i in range(n_inputs)]
    ptr_ids = [f"sp{i}" for i in range(n_inputs)]

    # Hexagonal coupling inside VisualCortex
    HEX_PS = 0.1
    for j in range(n_inputs):
        for jp in (j, j + 1):
            if 0 <= jp < n_inputs:
                net.connect(f"so{j}", f"sp{jp}", ConnType.LATERAL, pressure_scale=HEX_PS)
                net.connect(f"sp{jp}", f"so{j}", ConnType.LATERAL, pressure_scale=HEX_PS)

    # Flash sensor (dim=1) and motor sensor (dim=3)
    flash_sensor = net.add(SensorNode("flash", dim=1))
    motor_sensor = net.add(SensorNode("motor", dim=3))

    (visual_cortex
        .add_in_port("obj_input",  obj_ids)
        .add_out_port("obj_row",   obj_ids)
        .add_in_port("ptr_input",  ptr_ids)
        .add_out_port("ptr_row",   ptr_ids)
        .add_in_port("flash_in",   ["flash"])
        .add_in_port("motor_in",   ["motor"])
    )
    net.add_module(visual_cortex)

    # ------------------------------------------------------------------
    # HiddenHierarchy
    # ------------------------------------------------------------------
    hidden = PCModule("HiddenHierarchy")

    layer_widths = [max(1, n_inputs // (2 ** k)) for k in range(1, n_layers + 1)]
    layer_dims   = [base_dim + (k - 1) * dim_growth for k in range(1, n_layers + 1)]

    for k, (width, dim) in enumerate(zip(layer_widths, layer_dims), start=1):
        for j in range(width):
            net.add(PCNode(f"h{k}_{j}", dim=dim, activation="tanh", rng=rng))

    h1_ids  = [f"h1_{j}"          for j in range(layer_widths[0])]
    top_ids = [f"h{n_layers}_{j}" for j in range(layer_widths[-1])]

    hidden.add_in_port("visual_in",     h1_ids)
    hidden.add_out_port("abstract_out", top_ids)

    # VisualCortex → HiddenHierarchy: joint receptive field (obj + ptr)
    for j in range(layer_widths[0]):
        ps = 1.0
        net.connect(f"h1_{j}", f"so{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"so{2*j+1}", ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j}",   ConnType.UP, pressure_scale=ps)
        net.connect(f"h1_{j}", f"sp{2*j+1}", ConnType.UP, pressure_scale=ps)

    # Layer k+1 ← layer k (within HiddenHierarchy)
    for k in range(1, n_layers):
        width_above = layer_widths[k]
        ps = 0.1 if k == n_layers - 1 else 1.0
        for j in range(width_above):
            net.connect(f"h{k+1}_{j}", f"h{k}_{2*j}",   ConnType.UP, pressure_scale=ps)
            net.connect(f"h{k+1}_{j}", f"h{k}_{2*j+1}", ConnType.UP, pressure_scale=ps)

    # Lateral connections within each hidden layer
    for k in range(1, n_layers + 1):
        width = layer_widths[k - 1]
        for j in range(width):
            for d in range(1, lateral_steps + 1):
                if j + d < width:
                    net.connect(f"h{k}_{j}",   f"h{k}_{j+d}", ConnType.LATERAL)
                    net.connect(f"h{k}_{j+d}", f"h{k}_{j}",   ConnType.LATERAL)

    # Flash visible to top of hierarchy (hierarchy learns to predict success)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "flash", ConnType.UP, pressure_scale=0.3)

    net.add_module(hidden)

    # ------------------------------------------------------------------
    # PremotorModule
    # ------------------------------------------------------------------
    premotor_mod = PCModule("PremotorModule")
    net.add(PCNode("pm_0", dim=2, activation="tanh", rng=rng))

    premotor_mod.add_in_port("abstract_in", top_ids)
    premotor_mod.add_out_port("tap_out",    ["pm_0"])
    net.add_module(premotor_mod)

    # HiddenHierarchy → PremotorModule (top-down: hierarchy predicts premotor state)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "pm_0", ConnType.UP, pressure_scale=0.1)

    # PremotorModule → MotorModule (efference copy of tap command)
    net.connect("pm_0", "motor", ConnType.UP, pressure_scale=0.05)

    # ------------------------------------------------------------------
    # MotorModule
    # ------------------------------------------------------------------
    motor_mod = PCModule("MotorModule")
    motor_mod.add_in_port("efference_in", ["motor"])
    net.add_module(motor_mod)

    # HiddenHierarchy → MotorModule (efference copy of fovea/pointer commands)
    for j in range(layer_widths[-1]):
        net.connect(f"h{n_layers}_{j}", "motor", ConnType.UP, pressure_scale=0.05)

    return net, object_sensors, pointer_sensors, flash_sensor, motor_sensor


# ---------------------------------------------------------------------------
# Fovea helpers  (unchanged from act4)
# ---------------------------------------------------------------------------

def apply_fovea_shift(world_frame: list[float], phi: float, n_inputs: int) -> list[float]:
    """Extract n_inputs-wide window from world_frame at offset round(phi)."""
    offset = round(phi)
    world_len = len(world_frame)
    result = []
    for i in range(n_inputs):
        wi = offset + i
        result.append(float(world_frame[wi]) if 0 <= wi < world_len else 0.0)
    return result


def retinal_com(values: list[float] | np.ndarray) -> float | None:
    """Intensity-weighted centre of mass of a retinal image."""
    arr = np.asarray(values, dtype=float)
    arr = np.clip(arr, 0.0, None)
    total = arr.sum()
    if total < 1e-4:
        return None
    return float((np.arange(arr.size) * arr).sum() / total)


def compute_action_gradient(
    visual_sensors: list[SensorNode],
    image: list[float],
    anticipatory: bool = True,
    channel: int = 1,
) -> float:
    """
    Active-inference action signal: ∂E/∂φ.

    `channel` selects which sensor dimension to use for the gradient
    (default 1 = the object/value channel, valid for both dim=2 and dim=3 sensors).
    """
    e    = np.array([s.epsilon[channel] for s in visual_sensors])
    base = (np.array([s.pi[channel] for s in visual_sensors]) if anticipatory
            else np.array(image))
    grad = (np.roll(base, -1) - np.roll(base, 1)) * 0.5
    return float(np.sum(e * grad))


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _positions(n: int) -> list[float]:
    """Evenly-spaced retinal positions in (0, 1], length n."""
    step = 1.0 / n
    return [round(step * (i + 1), 4) for i in range(n)]


def set_frame_obj(
    object_sensors: list[SensorNode],
    obj_vals:    list[float],
    target_vals: list[float],
) -> None:
    """Push [retinal_pos, object_value, target_value] into dim=3 object sensor nodes."""
    pos = _positions(len(object_sensors))
    for i, s in enumerate(object_sensors):
        s.set_input(np.array([pos[i], float(obj_vals[i]), float(target_vals[i])]))


def set_frame_ptr(
    pointer_sensors: list[SensorNode],
    values: list[float],
) -> None:
    """Push [retinal_pos, pointer_value] into dim=2 pointer sensor nodes."""
    pos = _positions(len(pointer_sensors))
    for i, (s, v) in enumerate(zip(pointer_sensors, values)):
        s.set_input(np.array([pos[i], float(v)]))


def render_pointer_row(p: float, world_len: int, width: int = 2) -> list[float]:
    """Anti-aliased pointer blob (world frame)."""
    return _flat_blob(p, world_len, width=width)


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

BAR_WIDTH      = 28
HISTORY_LEN    = 60
SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"


def _bar(value: float, max_val: float, width: int = BAR_WIDTH) -> str:
    if not np.isfinite(value):
        return "N" * width
    filled = int(min(value / max(max_val, 1e-6), 1.0) * width)
    return "█" * filled + "░" * (width - filled)


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return "?" * len(values)
    lo, hi = min(finite), max(finite)
    span = hi - lo or 1e-6
    chars = []
    for v in values:
        if not np.isfinite(v):
            chars.append("?")
        else:
            idx = int((v - lo) / span * (len(SPARKLINE_CHARS) - 1))
            chars.append(SPARKLINE_CHARS[idx])
    return "".join(chars)


def _clear_lines(n: int) -> None:
    for _ in range(n):
        sys.stdout.write("\x1b[1A\x1b[2K")


def _ch(val: float) -> str:
    return "█" if val >= 0.9 else ("▓" if val >= 0.6 else ("░" if val >= 0.2 else "·"))


def render(
    step: int,
    total_steps: int,
    episode: int,
    world: PhysicsWorld1D,
    phi: float,
    v: float,
    p: float,
    vp: float,
    tap_gate: float,
    tapped: bool,
    kicked: bool,
    n_inputs: int,
    action_enabled: bool,
    oracle_enabled: bool,
    pursuit_enabled: bool,
    sensor_err: float,
    state_err: float,
    motor_err: float,
    sensor_history: list[float],
    state_history: list[float],
    max_err: float,
    prev_lines: int,
    f_action: float = 0.0,
    f_spring: float = 0.0,
) -> int:
    if prev_lines > 0:
        _clear_lines(prev_lines)

    phase_str = ("Phase 2 [ACTIVE]" if action_enabled
                 else "Phase 1.75 [PURSUIT]" if pursuit_enabled
                 else "Phase 1.5 [ORACLE]" if oracle_enabled
                 else "Phase 1 [passive]")
    flash_str = " [FLASH!]" if world.flash_timer > 0 else ""
    kick_str  = " [KICK]"  if kicked else ""

    obj_world    = world.render_obj_channel()
    target_world = world.render_target_channel()
    world_w      = len(obj_world)
    ptr_world    = render_pointer_row(p, world_w)
    # Padding on each side of the world so the fovea window can be drawn even
    # when it overshoots a world edge (phi may run slightly past 0 / WORLD_W).
    pad = n_inputs // 2

    # Padded display [pad zeros][world][pad zeros]
    def _pad_display(frame: list[float], bracket_at: int) -> str:
        padded = [0.0] * pad + list(frame) + [0.0] * pad
        win_s  = pad + bracket_at
        win_e  = win_s + n_inputs - 1
        out = []
        for i, val in enumerate(padded):
            if i == win_s:
                out.append("[")
            out.append(_ch(val))
            if i == win_e:
                out.append("]")
        return "".join(out)

    phi_r = round(phi)

    # Object world: object as block chars, with the fixed target overlaid as a
    # caret "‸" wherever there is no object pixel.  When the pointer TAPS, its
    # contact pixel is flashed into this row as "✸" so the interaction is visible.
    tap_world = render_pointer_row(p, world_w) if tapped else [0.0] * world_w

    def _pad_obj_display(obj_f: list[float], tgt_f: list[float],
                         tap_f: list[float], bracket_at: int) -> str:
        obj_p = [0.0] * pad + list(obj_f) + [0.0] * pad
        tgt_p = [0.0] * pad + list(tgt_f) + [0.0] * pad
        tap_p = [0.0] * pad + list(tap_f) + [0.0] * pad
        win_s = pad + bracket_at
        win_e = win_s + n_inputs - 1
        out = []
        for i, ov in enumerate(obj_p):
            if i == win_s:
                out.append("[")
            ch = _ch(ov)
            if tap_p[i] >= 0.5:
                ch = "✸"            # pointer tap contact flash (overlays everything)
            elif ch == "·" and tgt_p[i] >= 0.5:
                ch = "‸"            # target marker shows through empty pixels
            out.append(ch)
            if i == win_e:
                out.append("]")
        return "".join(out)

    obj_disp = _pad_obj_display(obj_world, target_world, tap_world, phi_r)
    ptr_disp = _pad_display(ptr_world, phi_r)

    # Sensor window string (object channel + target overlaid as "‸")
    def _obj_sensor_str() -> str:
        obj_sh = apply_fovea_shift(obj_world,    phi, n_inputs)
        tgt_sh = apply_fovea_shift(target_world, phi, n_inputs)
        chars = []
        for ov, tv in zip(obj_sh, tgt_sh):
            ch = _ch(ov)
            if ch == "·" and tv >= 0.5:
                ch = "‸"
            chars.append(ch)
        return "".join(chars)

    win_start_disp = pad + phi_r
    arrow = "→net   " if abs(f_action) > abs(f_spring) else "→spring"
    tap_str = f"  GRAB!" if tapped else ""

    lines = []
    lines.append(
        f"Step {step:5d}/{total_steps}  {phase_str}  "
        f"ep={episode}  obj={world.obj_pos:+.1f}  vel={world.obj_vel:+.2f}"
        f"  tgt={world.target_pos:.0f}{flash_str}{kick_str}"
    )
    lines.append(f"  Obj world:  {obj_disp}   (φ={phi:+.1f}  v={v:+.2f})  ‸=target")
    lines.append(f"  Obj sensor: {' ' * win_start_disp}[{_obj_sensor_str()}]")
    lines.append(f"  Ptr world:  {ptr_disp}   (p={p:+.1f}  vp={vp:+.2f})")
    lines.append(
        f"  Ptr force:  f_act={f_action:+.3f}  f_spr={f_spring:+.3f}  [{arrow}]"
        f"  finger={tap_gate:.2f}{tap_str}"
    )
    lines.append("")
    lines.append(f"  sensor_error  {_bar(sensor_err, max_err)}  {sensor_err:7.4f}")
    lines.append(f"  state_error   {_bar(state_err,  max_err)}  {state_err:7.4f}")
    lines.append(f"  motor_error   {_bar(motor_err,  max_err)}  {motor_err:7.4f}")
    lines.append("")
    h_sensor = sensor_history[-HISTORY_LEN:]
    h_state  = state_history[-HISTORY_LEN:]
    lines.append(f"  History (last {HISTORY_LEN} steps):")
    lines.append(f"    sensor █ {_sparkline(h_sensor)}")
    lines.append(f"    state  █ {_sparkline(h_state)}")
    lines.append("")

    print("\n".join(lines), end="", flush=True)
    return len(lines)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    step: int,
    sensor_history: list[float],
    state_history: list[float],
    motor_history: list[float],
    passive_steps: int,
    success_count: int,
    total_active_steps: int,
    tap_count: int,
    reward_sum: float,
    reward_steps: int,
    reward_pos: int,
    reward_neg: int,
    ptr_toward_obj: int,
    ptr_total_steps: int,
    ptr_descent_ok: int,
    pursuit_toward_obj: int = 0,
    pursuit_total_steps: int = 0,
    push_side_ok: int = 0,
    push_side_total: int = 0,
    tap_toward_target: int = 0,
    tap_total: int = 0,
) -> None:
    n = len(sensor_history)
    q = max(1, n // 10)
    first_s,  last_s  = sensor_history[:q], sensor_history[-q:]
    first_st, last_st = state_history[:q],  state_history[-q:]
    first_m,  last_m  = motor_history[:q],  motor_history[-q:]

    print(f"\n{'='*64}")
    print(f"  Training summary — act5 (push-to-target)")
    print(f"{'='*64}")
    print(f"  Steps completed    : {step}  (active started at step {passive_steps})")
    print(f"  {'':20s}  {'start':>8s}  {'end':>8s}  {'Δ':>8s}")
    for label, first, last in [
        ("sensor_error", first_s, last_s),
        ("state_error",  first_st, last_st),
        ("motor_error",  first_m,  last_m),
    ]:
        if first and last:
            print(f"  {label:20s}  {np.mean(first):8.4f}  {np.mean(last):8.4f}"
                  f"  {np.mean(first)-np.mean(last):+8.4f}")

    if pursuit_total_steps > 0:
        pursuit_pct = 100.0 * pursuit_toward_obj / pursuit_total_steps
        print(f"\n{'='*64}")
        print(f"  Pursuit-phase (object-following) statistics")
        print(f"{'='*64}")
        print(
            f"  ptr-action→object  : {pursuit_toward_obj}/{pursuit_total_steps}"
            f"  ({pursuit_pct:.1f}%)"
            f"   [>50% = following re-learned]"
        )

    if total_active_steps > 0:
        print(f"\n{'='*64}")
        print(f"  Active-phase statistics")
        print(f"{'='*64}")
        print(f"  Task successes     : {success_count}"
              f"   ({100.0 * success_count / max(1, total_active_steps):.2f}% of active steps in flash)")
        tap_pct = 100.0 * tap_count / total_active_steps
        print(f"  Finger contact     : {tap_count}/{total_active_steps}"
              f"  ({tap_pct:.1f}% of steps)   [finger touching the object]")

    if ptr_total_steps > 0:
        toward_pct  = 100.0 * ptr_toward_obj / ptr_total_steps
        descent_pct = 100.0 * ptr_descent_ok / ptr_total_steps
        print(
            f"  f_act→object       : {ptr_toward_obj}/{ptr_total_steps}"
            f"  ({toward_pct:.1f}%)"
            f"   [>50% = object-following]"
        )
        print(
            f"  (a) ptr-error ↓    : {ptr_descent_ok}/{ptr_total_steps}"
            f"  ({descent_pct:.1f}%)"
            f"   [>50% = active inference OK]"
        )

    if push_side_total > 0:
        side_pct = 100.0 * push_side_ok / push_side_total
        print(
            f"  ptr on PUSH side   : {push_side_ok}/{push_side_total}"
            f"  ({side_pct:.1f}%)"
            f"   [>50% = positioned to push object toward target]"
        )
    if tap_total > 0:
        tt_pct = 100.0 * tap_toward_target / tap_total
        print(
            f"  drag toward target : {tap_toward_target}/{tap_total}"
            f"  ({tt_pct:.1f}%)"
            f"   [>50% = drags move the object the right way]"
        )

    if reward_steps > 0:
        mean_r   = reward_sum / reward_steps
        pos_pct  = 100.0 * reward_pos / reward_steps
        neg_pct  = 100.0 * reward_neg / reward_steps
        print(f"\n  Reward stats (RPE):")
        print(f"    mean raw reward  : {mean_r:+.3f} over {reward_steps} steps")
        print(
            f"    modulator sign   : reinforce {pos_pct:.1f}%  |  punish {neg_pct:.1f}%"
            f"   [near 50/50 = discriminative]"
        )

    print(f"{'='*64}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------
    N_INPUTS       = 16   # visual sensor / fovea WINDOW width (pixels)
    WORLD_W        = 3 * N_INPUTS  # physical world width: fovea slides over it
    N_LAYERS       = 3    # hidden pyramid layers
    BASE_DIM       = 4    # state dim at layer 1
    DIM_GROWTH     = 2    # dim increment per layer
    LATERAL_STEPS  = 0    # lateral neighbours per side

    # ---- Training schedule ------------------------------------------------
    EPISODE_LEN          = 80    # steps per episode (world resets each episode)
    N_EPISODES_PASSIVE   = 120   # Phase 1:    passive learning (no action)
    N_EPISODES_ORACLE    = 60    # Phase 1.5:  oracle fovea tracking
    N_EPISODES_PURSUIT   = 200   # Phase 1.75: pointer learns to FOLLOW the object
                                 #   (reward = pointer-near-object, no tap). This
                                 #   re-establishes the act4 object-following basis
                                 #   before the harder push-to-target task.
    N_EPISODES_ACTIVE    = 250   # Phase 2:    full active control + push-to-target

    # ---- Fovea ------------------------------------------------------------
    ACTION_MODE       = "gradient"
    ACTION_GAIN       = 1.5
    ACTION_SMOOTH     = 0.2
    MAX_V             = 2.0
    SPRING_K          = 0.05
    PASSIVE_DRIFT     = 0.8    # wider drift so the fovea wanders across the world
    PASSIVE_SPRING_K  = 0.01   # weak centering toward PHI_MID
    PASSIVE_TRACK_K   = 0.10   # weak pull of fovea toward object (passive tracking)
    ORACLE_TARGET     = 0.5   # place object at fovea CENTRE so pointer spring aligns
    # Fovea window (N_INPUTS wide) slides over the WORLD_W-wide world.  phi is the
    # window's left-edge offset in world coords; allow the window CENTRE
    # (phi + N_INPUTS/2) to reach either world edge.
    PHI_MIN           = float(-N_INPUTS // 2)
    PHI_MAX           = float(WORLD_W - N_INPUTS // 2)
    PHI_MID           = float((WORLD_W - N_INPUTS) / 2.0)  # window centred in world

    # ---- Pointer ----------------------------------------------------------
    POINTER_WIDTH        = 2
    POINTER_MASS         = 1.0
    POINTER_DAMPING      = 0.05
    POINTER_ACTION_GAIN  = 1.5
    POINTER_SPRING_K     = 0.02
    POINTER_DRIFT        = 0.3
    MAX_VP               = 2.0
    P_MIN                = 0.0
    P_MAX                = float(WORLD_W - 1)
    POINTER_DRIVE        = "self"
    # PURSUIT-phase follow stiffness.  The pointer is a spring-damper anchored
    # directly on the OBJECT: its only fixed point is the object position, so
    # there is no steady-state offset (and none can be learned), while mass +
    # damping make it lag during motion — the desired loose coupling.  Lower K =
    # looser / more lag; raise K (or POINTER_DAMPING) if it overshoots/oscillates.
    POINTER_PURSUIT_K    = 0.10
    # Soft push-positioning bias (ACTIVE phase only).  Gently nudges the pointer
    # toward the side of the object AWAY from the target, so that a tap would push
    # the object TOWARD the target.  Deliberately weak: a *tendency* that creates
    # opportunities for good pushes — which the reward then reinforces — not a
    # command that solves the task mechanically.  The network still drives the
    # pointer (f_action) and decides WHEN to tap; this only tilts the resting
    # position to the helpful side.  POINTER_PUSH_K=0 disables it (env ACT5_PUSH_K).
    # NOTE: tried at 0.04 — made things clearly WORSE (object ratcheted to the
    # wall, following collapsed 48%→16%, push-side 24%→5.5%).  A weak oracle bias
    # fights the learned f_action and destabilises the dynamics.  Default 0.
    POINTER_PUSH_K       = 0.0    # strength of the push-side bias
    POINTER_PUSH_OFFSET  = 1.8    # how far past the object to aim (< tap_range=2.5)
    # PHASE-A goal-directed pointer scaffold (diagnostic).  When GOAL_DRIVE is on,
    # the active-phase pointer is sprung to the push-side of the object instead of
    # following it, with strength ∝ object→target distance (self-limiting).  This
    # REPLACES the self-gradient drive (no fighting) to test whether forcing good
    # positioning is sufficient to solve the push task.  env: ACT5_GOAL_DRIVE (0/1).
    # Default OFF: the Phase-A scaffold was a diagnostic (it confirmed positioning
    # is NOT the final blocker — see findings).  Enable via ACT5_GOAL_DRIVE=1.
    GOAL_DRIVE           = False
    GOAL_K               = 0.40   # spring gain toward the push position
    GOAL_OFFSET          = 1.8    # push-position offset past the object (< tap_range)
    GOAL_DIST_SCALE      = 6.0    # distance (px) over which drive strength saturates
    # ---- act6: goal-MODULE driven manipulation (the real integration) --------
    # The GoalModule decodes the desired object world-position from the shown
    # target (GOAL6_DREAM=False) or from a dreamed latent (True).  In the active
    # phase the finger auto-grabs the object and the pointer carries it to that
    # decoded desired — the validated goal-prior antidote to the dark room,
    # REPLACING the reward-modulated premotor finger.  env ACT6_GOAL (0/1).
    GOAL6_DRIVE          = True
    GOAL6_K              = 0.15   # pointer spring gain toward grab/carry target
    GOAL6_DREAM          = False  # True = specify the goal purely in latent space
    # Cap the CARRY velocity (object held) below the fovea's max tracking speed
    # (MAX_V=2.0) so the gaze keeps the carried object in view instead of being
    # outrun — the object/pointer otherwise jump faster than the fovea can follow.
    # Only the carry is limited; the (object-less) grab approach may stay fast.
    GOAL6_VMAX           = 1.2    # max |goal_vp| while carrying  (env ACT6_VMAX)

    # ---- Tap --------------------------------------------------------------
    # In active phase, the tap gate is derived from the PremotorModule:
    #   tap_gate = clip( (tanh(pm_node.pi[0]) + 1) / 2 + noise , 0, 1 )
    # read AFTER a relax (see "Ingredient 1" in the loop).
    # In passive/oracle phases the pointer does not tap (tap_gate = 0).
    TAP_PASSIVE = False   # allow tap in passive / oracle phases
    # Exploration noise on the tap gate (active phase), annealed linearly to 0
    # across the active phase.  Without it the reward modulator has nothing to
    # reinforce (the diagnostic test_pc_tap_diag.py needed expl>0 to learn at
    # all).  env override: ACT5_TAP_EXPL.
    TAP_EXPL_SIGMA = 0.3
    # PHASE-A.2 diagnostic: suppress the tap when |obj-target| < this, so the
    # object can coast to rest at the target (success needs at-rest).  0 = off.
    TAP_SETTLE_GATE = 0.0

    # ---- Active-phase object behaviour ------------------------------------
    # True  = object starts STATIONARY each active episode; only the pointer
    #         tap can set it in motion.  Isolates intentional pushing from
    #         opportunistic bounce-exploitation.
    # False = object starts with a random velocity (same as pursuit phase),
    #         allowing the network to also exploit natural bounce dynamics.
    ACTIVE_STATIC_OBJ = True
    # Fraction of PURSUIT episodes that also start the object stationary, so the
    # pointer practices APPROACHING a still object (not just chasing a moving
    # one).  0.0 = always moving (old behaviour), 1.0 = always static.
    PURSUIT_STATIC_FRAC = 0.5
    # Object persistence: when True the object is NOT repositioned at episode
    # boundaries — it keeps its position and is moved only by taps and recurring
    # auto-kicks toward random, world-spanning destinations.  This breaks the
    # narrow "object always starts left, pointer guards the gap" regime by
    # forcing the object across the whole world over time.
    PERSIST_OBJ = True
    # Active-phase target timeout: if the object fails to reach the target
    # within this many active steps, the target is moved to a fresh random
    # location.  Stops the network from settling into a stable "guard one spot,
    # never score" regime — keeps the goal fresh so that actually scoring stays
    # the only route to the quiet dwell.
    ACTIVE_TARGET_TIMEOUT = 200

    # ---- Reward -----------------------------------------------------------
    # (Experiment 1 — REWARD_GAIN>1 + high SHAPING_GAIN for genuine un-learning —
    # produced no behavioural change vs 1.0/8.0, so reverted.  The real blocker is
    # structural: the pointer almost never reaches the push side.  Both still
    # overridable via ACT5_REWARD_GAIN / ACT5_SHAPING_GAIN for future sweeps.)
    REWARD_GAIN       = 1.0
    REWARD_STRENGTH   = 1.0
    # PURSUIT phase keeps the EMA-baselined proximity reward (pointer-near-object).
    REWARD_BASELINE   = "ema"     # "none" or "ema" (RPE = reward - running mean)
    REWARD_BASE_DECAY = 0.99
    SUCCESS_BONUS     = 1.5       # (legacy, unused) replaced by REWARD_DWELL below
    # --- Active-phase reward: potential-based shaping + goal term ----------
    # Instead of absolute proximity minus a slow EMA, the active phase rewards
    # the CHANGE in object→target closeness each step (Ng-style potential-based
    # shaping):  pushing the object toward the target is promptly positive,
    # pushing it away promptly negative — without hard-coding which side to tap
    # from.  A separate goal term rewards RESTING on the target (the dwell), so
    # both the approach and the achieved state are reinforced.
    #   Φ      = 1 - |obj - target| / (WORLD_W/2)        (closeness potential)
    #   signal = clip(SHAPING_GAIN·(Φ_now - Φ_prev) + goal, -1, 1)
    #   goal   = REWARD_DWELL  while the object rests on the target, else 0
    SHAPING_GAIN      = 8.0       # amplifies per-step closeness change → modulator
    REWARD_DWELL      = 0.5       # reward per step while the object rests on target
    DWELL_STEPS       = 12        # frames the object dwells quietly on the target
    # The post-success freeze (inputs blanked to 0) is REPLACED by the quiet
    # dwell above: the object now rests *visibly* on the target instead of the
    # inputs being zeroed — zeroing was itself a surprise spike, not calm.
    # Kept at 0; set >0 to re-enable the old freeze behaviour.
    SUCCESS_FREEZE    = 0

    # ---- Learning ---------------------------------------------------------
    ETA_LEARN = 0.004

    DELAY = 0.0   # seconds between steps (0 = as fast as possible)
    # -----------------------------------------------------------------------

    # ---- Environment overrides (headless evaluation / A-B experiments) ----
    #   ACT5_HEADLESS=1        : no terminal animation; print periodic windowed
    #                            active-phase metrics + the final summary instead.
    #   ACT5_SHAPING_GAIN=<f>  : override SHAPING_GAIN (per-step closeness reward).
    #   ACT5_REWARD_GAIN=<f>   : override REWARD_GAIN  (>1 enables un-learning).
    #   ACT5_LOG_EVERY=<int>   : active-step window size for the headless metrics.
    #   ACT5_EPISODES_SCALE=<f>: scale every phase's episode count (quick smoke).
    HEADLESS   = os.environ.get("ACT5_HEADLESS", "0") == "1"
    LIVE       = not HEADLESS
    LOG_EVERY  = int(os.environ.get("ACT5_LOG_EVERY", "2000"))
    SHAPING_GAIN = float(os.environ.get("ACT5_SHAPING_GAIN", SHAPING_GAIN))
    REWARD_GAIN  = float(os.environ.get("ACT5_REWARD_GAIN",  REWARD_GAIN))
    POINTER_PUSH_K = float(os.environ.get("ACT5_PUSH_K", POINTER_PUSH_K))
    TAP_EXPL_SIGMA = float(os.environ.get("ACT5_TAP_EXPL", TAP_EXPL_SIGMA))
    GOAL_DRIVE     = os.environ.get("ACT5_GOAL_DRIVE", "1" if GOAL_DRIVE else "0") == "1"
    GOAL_K         = float(os.environ.get("ACT5_GOAL_K", GOAL_K))
    GOAL6_DRIVE    = os.environ.get("ACT6_GOAL", "1" if GOAL6_DRIVE else "0") == "1"
    GOAL6_DREAM    = os.environ.get("ACT6_DREAM", "1" if GOAL6_DREAM else "0") == "1"
    GOAL6_VMAX     = float(os.environ.get("ACT6_VMAX", GOAL6_VMAX))
    # Option-3 MEASUREMENT: drive the carry controller from PERCEIVED positions
    # (retinal centre-of-mass + fovea offset) instead of oracle world positions, to
    # quantify the cost of closing the perception loop.  No memory/active-looking yet:
    # when a needed thing is out of the fovea window the controller cannot act.
    #   off  : oracle (current behaviour)
    #   obj  : object perceived, target still oracle
    #   both : object AND target perceived (full perception loop)
    PERCEIVE       = os.environ.get("ACT6_PERCEIVE", "off").lower()
    # act6 Planner: the agent DREAMS its own next goal (curiosity-driven) instead of
    # a random/shown target.  Requires GOAL6_DRIVE (reuses the pretrained goal mod).
    PLANNER        = os.environ.get("ACT6_PLANNER", "0") == "1"
    TAP_SETTLE_GATE = float(os.environ.get("ACT5_SETTLE_GATE", TAP_SETTLE_GATE))
    _ep_scale  = float(os.environ.get("ACT5_EPISODES_SCALE", "1.0"))
    if _ep_scale != 1.0:
        N_EPISODES_PASSIVE = max(1, round(N_EPISODES_PASSIVE * _ep_scale))
        N_EPISODES_ORACLE  = max(1, round(N_EPISODES_ORACLE  * _ep_scale))
        N_EPISODES_PURSUIT = max(1, round(N_EPISODES_PURSUIT * _ep_scale))
        N_EPISODES_ACTIVE  = max(1, round(N_EPISODES_ACTIVE  * _ep_scale))

    rng = np.random.default_rng(42)
    net, object_sensors, pointer_sensors, flash_sensor, motor_sensor = build_network(
        rng,
        n_inputs=N_INPUTS,
        n_layers=N_LAYERS,
        base_dim=BASE_DIM,
        dim_growth=DIM_GROWTH,
        lateral_steps=LATERAL_STEPS,
        eta_learn=ETA_LEARN,
    )
    net.reward_gain = REWARD_GAIN

    world = PhysicsWorld1D(n=WORLD_W, dwell_steps=DWELL_STEPS, seed=0)

    # Goal module: its own PC autoencoder over object world-positions.  Pre-train
    # it so it can decode a desired object position from a shown target (or a
    # dreamed latent).  In the active phase this decoded desired drives the
    # finger to transport the object there (goal-prior antidote to the dark room).
    goal_mod = GoalModule(WORLD_W, img=16, latent=6, activation="identity",
                          rng=np.random.default_rng(7))
    if GOAL6_DRIVE:
        goal_mod.pretrain(steps=15000)

    # Curiosity planner: when enabled, the agent dreams its own next goal (replacing
    # random target relocation) — a self-directed, autonomous goal-setting loop.
    planner = None
    if GOAL6_DRIVE and PLANNER:
        planner = CuriosityPlanner(goal_mod, world.range_lo, world.range_hi,
                                   rng=np.random.default_rng(11))
        world.target_provider = lambda: planner.next_goal(world.obj_pos)

    total_episodes = (N_EPISODES_PASSIVE + N_EPISODES_ORACLE
                      + N_EPISODES_PURSUIT + N_EPISODES_ACTIVE)
    total_steps    = total_episodes * EPISODE_LEN
    planned_active_steps = N_EPISODES_ACTIVE * EPISODE_LEN  # for tap-exploration anneal

    sensor_history: list[float] = []
    state_history:  list[float] = []
    motor_history:  list[float] = []
    max_err = 5.0

    print(net.summary())
    print(f"\nAct5 — Push-to-target")
    print(f"World:    {WORLD_W}px  |  fovea window {N_INPUTS}px"
          f"  |  target at pixel {world.target_pos:.0f}")
    print(f"Physics:  friction={world.obj_friction}"
          f"  finger_radius={world.finger_radius}  drag_slip={world.drag_slip}")
    print(f"Phase 1:   {N_EPISODES_PASSIVE} episodes × {EPISODE_LEN} steps (passive)")
    print(f"Phase 1.5: {N_EPISODES_ORACLE} episodes × {EPISODE_LEN} steps (oracle fovea)")
    print(f"Phase 1.75:{N_EPISODES_PURSUIT} episodes × {EPISODE_LEN} steps (pursuit: pointer follows object)")
    print(f"Phase 2:   {N_EPISODES_ACTIVE} episodes × {EPISODE_LEN} steps (active push-to-target)")
    print(f"Total:    ≈{total_steps} steps\n")
    print(f"Reward:   SHAPING_GAIN={SHAPING_GAIN}  REWARD_GAIN={REWARD_GAIN}"
          f"  REWARD_DWELL={REWARD_DWELL}  DWELL_STEPS={DWELL_STEPS}"
          f"  ACTIVE_TARGET_TIMEOUT={ACTIVE_TARGET_TIMEOUT}")
    print(f"Finger:   FINGER_EXPL_SIGMA={TAP_EXPL_SIGMA} (post-relax read, annealed)"
          f"  drag actuator (no impulse)")
    print(f"Goal:     GOAL_DRIVE={GOAL_DRIVE}  GOAL_K={GOAL_K}  GOAL_OFFSET={GOAL_OFFSET}"
          f"  GOAL_DIST_SCALE={GOAL_DIST_SCALE}  [PHASE-A scaffold]")
    if GOAL6_DRIVE:
        print(f"act6 Goal-MODULE: ON  GOAL6_K={GOAL6_K}  dream={GOAL6_DREAM}"
              f"  decode_err={goal_mod.decode_error():.2f}px (world {WORLD_W}px)"
              f"  [finger auto-grabs, carries object to decoded target]")
    if planner is not None:
        print(f"act6 PLANNER:     ON  curiosity-driven  k={planner.k}"
              f"  memory={planner.memory}  carry_vmax={GOAL6_VMAX}"
              f"  [agent DREAMS its own next goal; desired=dreamed goal directly]")
    if PERCEIVE != "off":
        print(f"act6 PERCEIVE:    {PERCEIVE.upper()}  [carry driven by retinal COM + "
              f"fovea offset; NO memory — out-of-view = cannot act this step]")
    if HEADLESS:
        print(f"[headless] windowed active metrics every {LOG_EVERY} active steps:")
        print(f"[headless]   meanDist = mean |obj-target|  (lower = closer; "
              f"WORLD_W/2={WORLD_W/2:.0f} = chance)")
        print(f"[headless]   meanObj  = mean object world-pos (24=centre, "
              f"~47=right wall, ~0=left wall)")
        print(f"[headless]   →tgt(cum)= cumulative % of taps pushing toward target")
        print(f"[headless]   neg-mod  = % steps with neuromod<0 (genuine un-learning)\n")
    else:
        print("Press Ctrl+C to stop early.\n")

    oracle_start_ep  = N_EPISODES_PASSIVE
    pursuit_start_ep = N_EPISODES_PASSIVE + N_EPISODES_ORACLE
    active_start_ep  = N_EPISODES_PASSIVE + N_EPISODES_ORACLE + N_EPISODES_PURSUIT

    prev_lines    = 0
    step          = 0
    passive_steps = 0
    phi = PHI_MID
    v   = 0.0
    p   = float(WORLD_W // 2)
    vp  = 0.0
    finger_y      = 0.0
    ptr_f_action  = 0.0
    ptr_f_spring  = 0.0

    # Statistics
    success_count       = 0
    freeze_countdown    = 0   # steps remaining in post-success silence
    total_active_steps  = 0
    pursuit_toward_obj  = 0   # pursuit phase: pointer-action points at object
    pursuit_total_steps = 0
    tap_count           = 0
    reward_sum          = 0.0
    reward_steps        = 0
    reward_baseline     = 0.0
    phi_prev            = None   # previous closeness potential (shaping reward)
    target_idle         = 0      # active steps since the object last reached target
    reward_pos          = 0
    reward_neg          = 0
    ptr_toward_obj      = 0
    ptr_total_steps     = 0
    ptr_descent_ok      = 0
    # Push-side diagnostics (active phase): is the pointer on the side of the
    # object AWAY from the target, i.e. positioned so a tap would push the
    # object TOWARD the target?
    push_side_ok        = 0   # pointer on the correct (away-from-target) side
    push_side_total     = 0   # steps where object is off-target and pointer is off-object
    tap_toward_target   = 0   # taps whose impulse pushed the object toward target
    tap_total           = 0   # taps that actually landed (active phase)
    # Headless windowed active-phase metrics (reset every LOG_EVERY active steps).
    eval_win = dict(steps=0, dist=0.0, objpos=0.0, succ=0, taps=0, negmod=0)
    # Option-3 perception-loop visibility stats (PERCEIVE != off): how often the
    # object / target are actually in the fovea window when the controller needs them.
    perceive_steps = 0
    obj_seen_count = 0
    tgt_seen_count = 0

    try:
        for ep in range(total_episodes):
            oracle_enabled  = oracle_start_ep <= ep < pursuit_start_ep
            pursuit_enabled = pursuit_start_ep <= ep < active_start_ep
            action_enabled  = ep >= active_start_ep
            # In both pursuit and active phases the NETWORK drives fovea+pointer.
            control_enabled = pursuit_enabled or action_enabled

            if ep == active_start_ep:
                passive_steps = step
                reward_baseline = 0.0   # reset RPE baseline: reward target changed
                phi_prev = None         # no stale potential into the active phase
                target_idle = 0         # start the target-timeout clock fresh
                if planner is not None:
                    world.relocate_target()   # dream the FIRST self-set goal

            # Reset world and effectors at episode start.
            # Active phase: object can start stationary so only a tap moves it.
            # Pursuit phase: a fraction of episodes also start static so the
            # pointer practices approaching a still object.
            ep_static = (action_enabled and ACTIVE_STATIC_OBJ) or (
                pursuit_enabled and rng.random() < PURSUIT_STATIC_FRAC)
            # With PERSIST_OBJ the object keeps its position across episodes and
            # is moved only by taps + auto-kicks (full-world coverage over time).
            world.reset(static=ep_static, reposition=not PERSIST_OBJ)
            # Fovea (phi), pointer (p) and their velocities PERSIST across
            # episode boundaries — like the object — so the scene flows
            # continuously instead of snapping back to the world centre every
            # episode (which created an artificial recurring "reset to middle").
            finger_y = 0.0

            for frame_idx in range(EPISODE_LEN):
                # ---- Post-success freeze ----
                # After a hit the network sits in silence for SUCCESS_FREEZE
                # steps: ALL sensor inputs are set to zero, no action, no
                # reward.  This prevents the FLASH prediction-error spike from
                # being experienced as aversive — the network simply rests.
                frozen = freeze_countdown > 0
                if frozen:
                    freeze_countdown -= 1
                    for s in object_sensors:
                        s.set_input(np.zeros(s.dim))
                    for s in pointer_sensors:
                        s.set_input(np.zeros(s.dim))
                    flash_sensor.set_input(np.zeros(flash_sensor.dim))
                    motor_sensor.set_input(np.zeros(motor_sensor.dim))
                    net.step(learn=True)
                    net.commit_step()
                    # Physics and display keep running so the world moves on.
                    phys = world.step(0.0, p, 0.0)
                    step += 1
                    if action_enabled:
                        total_active_steps += 1
                    if LIVE:
                        prev_lines = render(
                            step, total_steps, ep, world,
                            phi, v, p, vp, 0.0, False, phys["kicked"],
                            N_INPUTS, action_enabled, oracle_enabled, pursuit_enabled,
                            0.0, 0.0, 0.0,
                            sensor_history, state_history, max_err,
                            prev_lines,
                            f_action=0.0, f_spring=0.0,
                        )
                    continue

                # ---- Build world frames ----
                obj_world    = world.render_obj_channel()
                target_world = world.render_target_channel()
                ptr_world    = render_pointer_row(p, WORLD_W, POINTER_WIDTH)

                obj_shifted  = apply_fovea_shift(obj_world,    phi, N_INPUTS)
                tgt_shifted  = apply_fovea_shift(target_world, phi, N_INPUTS)
                ptr_shifted  = apply_fovea_shift(ptr_world,    phi, N_INPUTS)
                flash_val    = 1.0 if world.flash_timer > 0 else 0.0

                # ---- Clamp sensors ----
                set_frame_obj(object_sensors, obj_shifted, tgt_shifted)
                set_frame_ptr(pointer_sensors, ptr_shifted)
                flash_sensor.set_input(np.array([flash_val]))
                motor_sensor.set_input(np.array([v / MAX_V, vp / MAX_VP, finger_y]))

                # ---- Action signals (require phase_predict + phase_error first) ----
                _disp  = 0.0
                _pdisp = 0.0
                goal_vp = 0.0   # act6: synced goal-carry pointer velocity (GOAL6_DRIVE)
                if control_enabled:
                    net.phase_predict()
                    net.phase_error()

                    # Fovea: gradient on object channel (index 1 of dim=3 sensors)
                    _disp = -compute_action_gradient(object_sensors, obj_shifted, channel=1)

                    # Pointer: gradient on value channel (index 1 of dim=2 sensors)
                    if POINTER_DRIVE == "self":
                        _pdisp = +compute_action_gradient(
                            pointer_sensors, ptr_shifted, anticipatory=False, channel=1
                        )
                    else:
                        _pdisp = -compute_action_gradient(
                            object_sensors, obj_shifted, anticipatory=True, channel=1
                        )

                    # Tap gate from PremotorModule — only in the active push-to-target
                    # phase.  During pursuit the pointer just learns to follow, no tap.
                    if action_enabled:
                        # Ingredient 1: read the tap AFTER a relax, so pm_0 reflects
                        # the CURRENT frame's evidence (not just the temporal warm-
                        # start prediction).  The diagnostic (test_pc_tap_diag.py)
                        # showed the conditional tap only becomes learnable post-relax.
                        # This relax is discarded by net.step()'s own predict/relax
                        # below (warm-start is reloaded), so learning is unchanged.
                        net.phase_relax()
                        pm_node    = net.node("pm_0")
                        finger_raw = float(np.clip(
                            (np.tanh(pm_node.pi[0]) + 1.0) / 2.0, 0.0, 1.0))
                        # Ingredient 2: exploration noise on the finger extension,
                        # annealed to 0 across the active phase, so reward has
                        # something to reinforce.  The noisy value is executed AND
                        # fed back as the efference copy next frame.
                        finger_sigma = TAP_EXPL_SIGMA * max(
                            0.0, 1.0 - total_active_steps / max(1, planned_active_steps))
                        finger_y = float(np.clip(
                            finger_raw + rng.normal(0.0, finger_sigma), 0.0, 1.0))
                        # (diagnostic) optionally RETRACT the finger near the target
                        # so the object coasts to rest.  env ACT5_SETTLE_GATE; 0=off.
                        if (TAP_SETTLE_GATE > 0.0
                                and abs(world.obj_pos - world.target_pos) < TAP_SETTLE_GATE):
                            finger_y = 0.0
                        if GOAL6_DRIVE:
                            # act6: decode the desired object position from the goal
                            # module, auto-grab, and compute a SYNCED carry velocity.
                            # When grabbed, goal_vp drives the OBJECT toward desired;
                            # object and pointer then move by the SAME goal_vp below
                            # → rigid grasp (no drift).  When not grabbed, approach
                            # the object to grab it.  (Replaces the premotor finger.)
                            # Positions the carry controller acts on: oracle, or
                            # PERCEIVED from the retina (COM in the window + offset).
                            # round(phi) matches apply_fovea_shift's window offset.
                            if PERCEIVE == "off":
                                obj_ctrl = world.obj_pos
                                tgt_ctrl = world.target_pos
                            else:
                                _oc = retinal_com(obj_shifted)
                                obj_ctrl = (round(phi) + _oc) if _oc is not None else None
                                if PERCEIVE == "both":
                                    _tc = retinal_com(tgt_shifted)
                                    tgt_ctrl = (round(phi) + _tc) if _tc is not None else None
                                else:
                                    tgt_ctrl = world.target_pos
                                perceive_steps += 1
                                if obj_ctrl is not None:
                                    obj_seen_count += 1
                                if tgt_ctrl is not None:
                                    tgt_seen_count += 1

                            # The goal position the object is carried to.
                            if planner is not None:
                                # The planner already decoded its dreamed latent to
                                # target_pos — use it directly (no second decode), so
                                # "carry destination" == "success criterion" and the
                                # object reaches its own goal instead of resting at a
                                # re-decoded point short of it (the freeze cause).
                                desired = tgt_ctrl
                            elif GOAL6_DREAM:
                                desired = (goal_mod.decode_dream(
                                    goal_mod.encode(world.target_pos))
                                    if tgt_ctrl is not None else None)
                            else:
                                desired = (goal_mod.decode_target(world.target_pos)
                                           if tgt_ctrl is not None else None)

                            if obj_ctrl is None or desired is None:
                                # Needed perception missing (out of view) and no
                                # memory yet → the controller cannot act this step.
                                finger_y = 0.0
                                goal_vp = 0.0
                            else:
                                grabbed = abs(p - obj_ctrl) < world.finger_radius
                                finger_y = 1.0 if grabbed else 0.0
                                if grabbed:
                                    # Carry capped at GOAL6_VMAX so the fovea keeps up.
                                    goal_vp = float(np.clip(
                                        GOAL6_K * (desired - obj_ctrl),
                                        -GOAL6_VMAX, GOAL6_VMAX))
                                else:
                                    goal_vp = float(np.clip(
                                        GOAL6_K * (obj_ctrl - p), -MAX_VP, MAX_VP))
                    else:
                        finger_y = 0.0

                    # (a) test: does pointer action direction reduce pointer-row error?
                    pi_val = np.array([s.pi[1] for s in pointer_sensors])
                    e_cur  = float(np.sum((np.array(ptr_shifted) - pi_val) ** 2))
                    p_pert = float(np.clip(p + 0.5 * np.sign(_pdisp), P_MIN, P_MAX))
                    pert_w = render_pointer_row(p_pert, WORLD_W, POINTER_WIDTH)
                    pert_s = apply_fovea_shift(pert_w, phi, N_INPUTS)
                    e_new  = float(np.sum((np.array(pert_s) - pi_val) ** 2))
                    if e_new < e_cur:
                        ptr_descent_ok += 1
                    ptr_total_steps += 1

                    # Does the pointer action point toward the object?
                    obj_com = world.world_com()
                    if abs(obj_com - p) > 0.3:
                        if np.sign(_pdisp) == np.sign(obj_com - p):
                            ptr_toward_obj += 1
                            if pursuit_enabled:
                                pursuit_toward_obj += 1
                        if pursuit_enabled:
                            pursuit_total_steps += 1
                else:
                    finger_y = 0.0

                # ---- Physics step (finger drags the object via pointer motion) ----
                # Stat slots are reused for the finger actuator:
                #   tap_count         := steps the finger is in CONTACT
                #   tap_total         := drag steps with the target off-object
                #   tap_toward_target := of those, drags that moved the object
                #                        TOWARD the target (sign(obj_vel)==sign(to_tgt))
                obj_pre    = world.obj_pos
                to_tgt_pre = world.target_pos - obj_pre
                phys = world.step(finger_y, p,
                                  goal_vp if (GOAL6_DRIVE and action_enabled) else vp)
                if phys["contact"]:
                    tap_count += 1
                if action_enabled and phys["dragged"] and abs(to_tgt_pre) > 0.5:
                    tap_total += 1
                    if np.sign(world.obj_vel) == np.sign(to_tgt_pre):
                        tap_toward_target += 1
                if action_enabled and phys["success"]:
                    success_count += 1
                    if SUCCESS_FREEZE > 0:
                        freeze_countdown = SUCCESS_FREEZE

                # ---- Reward ----
                # Pursuit phase: reward = pointer-near-object (re-learn following).
                # Active phase : reward = object-near-target  (+ success bonus).
                if control_enabled:
                    if pursuit_enabled:
                        # Pursuit: reward pointer-near-object (EMA-baselined RPE).
                        raw_reward = float(np.clip(
                            (1.0 - abs(p - world.obj_pos) / (N_INPUTS / 2))
                            * REWARD_STRENGTH,
                            -1.0, 1.0,
                        ))
                        signal = raw_reward - reward_baseline
                        reward_baseline = (REWARD_BASE_DECAY * reward_baseline
                                           + (1.0 - REWARD_BASE_DECAY) * raw_reward)
                    else:
                        # Active: potential-based shaping + goal term (see config).
                        #   shaping = Φ_now - Φ_prev   (motivate moving toward target)
                        #   goal    = REWARD_DWELL     (reinforce resting on target)
                        # Shaping is skipped on the first step and across a target
                        # relocation (phys["kicked"]), where Φ_prev is stale and the
                        # potential jump is not the action's doing.
                        phi_now = float(np.clip(
                            1.0 - abs(world.obj_pos - world.target_pos) / (WORLD_W / 2),
                            -1.0, 1.0,
                        ))
                        if phi_prev is None or phys["kicked"]:
                            shaping = 0.0
                        else:
                            shaping = phi_now - phi_prev
                        phi_prev = phi_now
                        goal   = REWARD_DWELL if phys["success"] else 0.0
                        signal = float(np.clip(
                            SHAPING_GAIN * shaping + goal, -1.0, 1.0))
                        raw_reward = signal

                    net.set_reward(signal)
                    reward_sum   += raw_reward
                    reward_steps += 1
                    if signal > 0:
                        reward_pos += 1
                    elif signal < 0:
                        reward_neg += 1

                # ---- PC step ----
                info = net.step(learn=True)
                net.commit_step()

                m_err  = float(np.sum(net.node("motor").epsilon ** 2))
                s_err  = (info["sensor_error"] - m_err)
                st_err = info["state_error"]
                s_err  = s_err  if np.isfinite(s_err)  else max_err
                st_err = st_err if np.isfinite(st_err) else max_err
                m_err  = m_err  if np.isfinite(m_err)  else max_err

                sensor_history.append(s_err)
                state_history.append(st_err)
                motor_history.append(m_err)
                max_err = max(max_err * 0.99, s_err, st_err, 0.1)

                if LIVE:
                    prev_lines = render(
                        step + 1, total_steps, ep, world,
                        phi, v, p, vp, finger_y, phys["contact"], phys["kicked"],
                        N_INPUTS, action_enabled, oracle_enabled, pursuit_enabled,
                        s_err, st_err, m_err,
                        sensor_history, state_history, max_err,
                        prev_lines,
                        f_action=ptr_f_action, f_spring=ptr_f_spring,
                    )
                step += 1
                if action_enabled:
                    total_active_steps += 1

                # ---- Headless windowed active-phase metrics ----
                if HEADLESS and action_enabled:
                    ew = eval_win
                    ew["steps"]    += 1
                    ew["dist"]     += abs(world.obj_pos - world.target_pos)
                    ew["objpos"]   += world.obj_pos
                    if phys["success"]:
                        ew["succ"] += 1
                    if phys["contact"]:
                        ew["taps"] += 1
                    # signal is the modulator input this step; neuromod = 1+gain·signal
                    if 1.0 + REWARD_GAIN * signal < 0.0:
                        ew["negmod"] += 1
                    if ew["steps"] >= LOG_EVERY:
                        n   = ew["steps"]
                        tt  = (100.0 * tap_toward_target / tap_total) if tap_total else 0.0
                        print(
                            f"[active {total_active_steps:6d}]  "
                            f"meanDist={ew['dist']/n:5.1f}  "
                            f"meanObj={ew['objpos']/n:5.1f}  "
                            f"succ={ew['succ']:4d}  contact={ew['taps']:4d}  "
                            f"drag→tgt(cum)={tt:4.1f}%  neg-mod={100.0*ew['negmod']/n:4.1f}%",
                            flush=True,
                        )
                        eval_win = dict(steps=0, dist=0.0, objpos=0.0,
                                        succ=0, taps=0, negmod=0)

                # ---- Fovea update ----
                # The fovea always keeps the OBJECT in view (consistent across
                # passive, oracle and pursuit) — the only thing that differs
                # between training phases is how the POINTER is driven.  Only in
                # the final ACTIVE phase is the fovea self-driven by the
                # prediction-error gradient (true active inference).
                if action_enabled:
                    # Active inference: fovea driven by its own error gradient,
                    # softly centred on the world middle (PHI_MID, not 0).
                    v_target = _disp * ACTION_GAIN - SPRING_K * (phi - PHI_MID)
                    v = float(np.clip(
                        (1.0 - ACTION_SMOOTH) * v_target + ACTION_SMOOTH * v,
                        -MAX_V, MAX_V,
                    ))
                elif oracle_enabled or pursuit_enabled:
                    # Reliable object tracking — same goal as the passive fovea,
                    # so PURSUIT trains the pointer-follows-object mapping with
                    # the object centred, NOT the opposite (fovea-on-pointer).
                    # Velocity feed-forward (+ obj_vel) anticipates the object's
                    # motion so a constantly-moving object stays centred instead
                    # of lagging to the leading edge (smooth-pursuit tracking).
                    com = world.world_com() + world.obj_vel
                    # Centre on the TRUE geometric middle of the window:
                    # indices 0..N_INPUTS-1 → centre = (N_INPUTS-1)/2 = 7.5 for
                    # N_INPUTS=16.  Using N_INPUTS (=8) would put the object half
                    # a pixel right of centre.
                    target_phi = com - ORACLE_TARGET * (N_INPUTS - 1)
                    v = float(np.clip(target_phi - phi, -MAX_V, MAX_V))
                else:
                    # Passive fovea: random drift + weak centering + weak pull
                    # toward the object so the network reliably sees it while
                    # still exploring the full world width.
                    obj_phi = world.world_com() - (N_INPUTS - 1) / 2.0  # ideal phi to centre object
                    v = float(np.clip(
                        rng.normal(0.0, PASSIVE_DRIFT)
                        - PASSIVE_SPRING_K * (phi - PHI_MID)
                        + PASSIVE_TRACK_K * (obj_phi - phi),
                        -MAX_V, MAX_V,
                    ))
                phi = float(np.clip(phi + v, PHI_MIN, PHI_MAX))

                # ---- Pointer physics ----
                f_push = 0.0
                if pursuit_enabled:
                    # Loose object-following: spring-damper anchored DIRECTLY on
                    # the object.  The spring's only fixed point is the object,
                    # so the pointer's steady-state target IS the object (no
                    # offset, and none can be learned); mass + damping produce the
                    # lag during motion.  The network's own pointer gradient is
                    # NOT fed back as a force here — a self-driven pointer
                    # (POINTER_DRIVE="self") forms a self-fulfilling loop that can
                    # settle at an arbitrary offset from the object.  _pdisp is
                    # still computed above, but only for the following-statistic.
                    f_action = 0.0
                    f_spring = -POINTER_PURSUIT_K * (p - world.world_com())
                elif action_enabled:
                    gaze_centre = phi + (N_INPUTS - 1) / 2.0
                    f_spring = -POINTER_SPRING_K * (p - gaze_centre)
                    if GOAL6_DRIVE:
                        # act6: pointer is updated kinematically below using goal_vp
                        # (computed in the control block for a synced rigid grasp).
                        f_action = 0.0
                        f_spring = 0.0
                    elif GOAL_DRIVE:
                        # PHASE-A diagnostic scaffold: REPLACE the self-following
                        # drive with a goal-directed one.  The pointer is sprung to
                        # a point just past the object on the side AWAY from the
                        # target (so a tap pushes the object toward the target).
                        # The drive is SELF-LIMITING: its strength ∝ object→target
                        # distance and →0 near the target, so the pointer stops
                        # shoving once the object arrives (the suspected ratchet
                        # cause of the old additive POINTER_PUSH_K bias).  This
                        # forces good positioning to TEST whether positioning is the
                        # binding constraint; it is NOT the final mechanism.
                        d = world.target_pos - world.obj_pos
                        if abs(d) > 0.5:
                            strength = min(1.0, abs(d) / GOAL_DIST_SCALE)
                            push_pos = (world.obj_pos
                                        + np.sign(world.obj_pos - world.target_pos)
                                        * GOAL_OFFSET)
                            f_action = GOAL_K * strength * (push_pos - p)
                        else:
                            f_action = 0.0   # at target: let the pointer settle
                    else:
                        # Active inference: pointer driven by its own error gradient.
                        f_action = POINTER_ACTION_GAIN * _pdisp
                        # (legacy) optional weak additive push bias.
                        if POINTER_PUSH_K > 0.0 and abs(world.obj_pos - world.target_pos) > 0.5:
                            push_pos = (world.obj_pos
                                        + np.sign(world.obj_pos - world.target_pos)
                                        * POINTER_PUSH_OFFSET)
                            f_push = POINTER_PUSH_K * (push_pos - p)
                else:
                    # Passive: random drift, weak centring on the gaze centre.
                    gaze_centre = phi + (N_INPUTS - 1) / 2.0
                    f_spring = -POINTER_SPRING_K * (p - gaze_centre)
                    f_action = rng.normal(0.0, POINTER_DRIFT)
                if GOAL6_DRIVE and action_enabled:
                    # Kinematic: pointer moves by the SAME goal_vp the object was
                    # dragged with → rigid grasp, no drift.
                    vp = goal_vp
                    p  = float(np.clip(p + vp, P_MIN, P_MAX))
                    ptr_f_action = goal_vp
                    ptr_f_spring = 0.0
                else:
                    accel = (f_action + f_spring + f_push) / POINTER_MASS
                    ptr_f_action = f_action
                    ptr_f_spring = f_spring
                    vp = float(np.clip((vp + accel) * (1.0 - POINTER_DAMPING), -MAX_VP, MAX_VP))
                    p  = float(np.clip(p + vp, P_MIN, P_MAX))

                # ---- Active-phase target timeout ----
                # Reset the clock whenever the object is on the target; otherwise
                # count up and, after ACTIVE_TARGET_TIMEOUT idle steps, move the
                # target so the network cannot settle into "guard one spot".
                if action_enabled:
                    if phys["success"]:
                        target_idle = 0
                    else:
                        target_idle += 1
                        if target_idle >= ACTIVE_TARGET_TIMEOUT:
                            world.relocate_target()
                            target_idle = 0
                            phi_prev = None   # target jumped: skip shaping next step

                if DELAY > 0:
                    time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n\nStopped early.")

    if PERCEIVE != "off" and perceive_steps > 0:
        print(f"\n[perceive {PERCEIVE}]  control steps={perceive_steps}"
              f"  object-in-view={100.0*obj_seen_count/perceive_steps:.1f}%"
              f"  target-in-view={100.0*tgt_seen_count/perceive_steps:.1f}%"
              f"   [out-of-view = could not act; motivates memory/active-looking]")

    print_summary(
        step, sensor_history, state_history, motor_history,
        passive_steps, success_count, total_active_steps,
        tap_count, reward_sum, reward_steps,
        reward_pos, reward_neg,
        ptr_toward_obj, ptr_total_steps, ptr_descent_ok,
        pursuit_toward_obj, pursuit_total_steps,
        push_side_ok, push_side_total,
        tap_toward_target, tap_total,
    )


if __name__ == "__main__":
    main()
