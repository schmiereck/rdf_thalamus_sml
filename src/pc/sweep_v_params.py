"""
sweep_v_params.py — Sweep über V-Forward-Modell-Hyperparameter des PCNode.

Getestete Achsen
----------------
  eta_temporal  : Lernrate für V  [0.001 … 0.05]
  w_clip_V      : Gewichts-Clipping für V  [1.0 … 10.0, None=kein Clip]
  forward_mode  : "double" = f(V·f(μ))  (Standard, doppeltes tanh)
                  "single" = V·f(μ)     (kein äußeres f, μ nicht squasht)

Metriken
--------
  anticipation  : Ratio scrambled/ordered initiale Überraschung auf dem
                  3-Pixel-Wanderpuls (>1 = V lernt Dynamik, je höher desto besser)
  sensor_err    : mittlerer Sensor-Rekonstruktionsfehler auf test_pc2-Patterns
  state_err     : mittlerer Hidden-State-Fehler auf test_pc2-Patterns
  score         : kombinierter Rang (höchste anticipation UND niedrigster Fehler)

Ausführung:  python src/pc/sweep_v_params.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from dataclasses import dataclass

from pc import PCNode, SensorNode, PCNetwork
from pc.connection import ConnType

# ---------------------------------------------------------------------------
# Patch PCNode's forward_mode at runtime without subclassing
# ---------------------------------------------------------------------------
# We monkey-patch commit_step and learn_temporal per-instance so we can
# test "single" mode (no outer activation) without touching node.py.

def _commit_step_single(self) -> None:
    """Variant: predicted_next_mu = V @ f(μ)  (no outer activation)."""
    if self._clamped:
        self._prev_mu = self.mu.copy()
        return
    self._prev_f_mu = self._act(self.mu).copy()
    self._prev_mu   = self.mu.copy()
    pre = self.V @ self._prev_f_mu
    self._predicted_next_mu = pre                  # <- no f(pre)


def _learn_temporal_single(self) -> None:
    """Matching gradient for single mode: dV = η · δ ⊗ f(μ_prev)."""
    if self._clamped:
        return
    delta = self.mu - self._predicted_next_mu      # shape [dim]
    # no activation inside the forward model: grad_act = 1
    dV = np.outer(delta, self._prev_f_mu)
    if np.all(np.isfinite(dV)):
        self.V += self.eta_temporal * dV
    if self.w_clip_V > 0.0:
        np.clip(self.V, -self.w_clip_V, self.w_clip_V, out=self.V)


import types as _types

def _apply_forward_mode(node: PCNode, mode: str) -> None:
    if mode == "single":
        node.commit_step    = _types.MethodType(_commit_step_single,    node)
        node.learn_temporal = _types.MethodType(_learn_temporal_single, node)
    # "double" is the default — nothing to patch


# ---------------------------------------------------------------------------
# Tiny 3-pixel anticipation test (from test_pc_forward.py)
# ---------------------------------------------------------------------------

def _initial_surprise(net: PCNetwork, sensor: SensorNode, frame: np.ndarray) -> float:
    sensor.set_input(frame)
    net.phase_predict()
    net.phase_error()
    surprise = float(np.sum(sensor.epsilon ** 2))
    net.phase_relax()
    net.phase_learn()
    net.commit_step()
    return surprise


def anticipation_score(
    eta_temporal: float,
    w_clip_V: float,
    forward_mode: str,
    seed: int = 0,
    n_train_cycles: int = 400,
    n_eval_laps: int = 20,
) -> float:
    """Train on a 3-pixel travelling pulse; return scrambled/ordered surprise ratio."""
    rng = np.random.default_rng(seed)
    net = PCNetwork(
        eta_inf=0.1, n_relax=30, eps_tol=1e-6,
        alpha=1.0, beta=1.0, gamma=1.0,
        eta_learn=0.01,
        eta_temporal=eta_temporal,
        lambda_decay=0.0, w_clip=5.0, rng=rng,
    )
    sensor = net.add(SensorNode("i1", dim=3))
    h = net.add(PCNode("a1", dim=6, activation="tanh", rng=rng))
    h.w_clip_V = w_clip_V
    _apply_forward_mode(h, forward_mode)
    net.connect("a1", "i1", ConnType.UP)

    frames = [np.array([1., 0, 0]), np.array([0, 1., 0]), np.array([0, 0, 1.])]

    for _ in range(n_train_cycles):
        for f in frames:
            sensor.set_input(f)
            net.step(learn=True)
            net.commit_step()

    ordered = [_initial_surprise(net, sensor, f) for _ in range(n_eval_laps) for f in frames]
    scrambled = [_initial_surprise(net, sensor, frames[i])
                 for i in rng.integers(0, 3, size=n_eval_laps * 3)]

    mo, ms = float(np.mean(ordered)), float(np.mean(scrambled))
    return ms / mo if mo > 0 else 1.0


# ---------------------------------------------------------------------------
# test_pc2-style reconstruction benchmark
# ---------------------------------------------------------------------------

# Movement patterns from test_pc2 (reduced to 4 essential ones for speed)
TRAIN_PATTERNS = {
    "one-dot L→R": [[1,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0],[0,0,1,0,0,0,0,0],
                    [0,0,0,1,0,0,0,0],[0,0,0,0,1,0,0,0],[0,0,0,0,0,1,0,0],
                    [0,0,0,0,0,0,1,0],[0,0,0,0,0,0,0,1]],
    "one-dot R→L": [[0,0,0,0,0,0,0,1],[0,0,0,0,0,0,1,0],[0,0,0,0,0,1,0,0],
                    [0,0,0,0,1,0,0,0],[0,0,0,1,0,0,0,0],[0,0,1,0,0,0,0,0],
                    [0,1,0,0,0,0,0,0],[1,0,0,0,0,0,0,0]],
    "bounce L→mid": [[1,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0],[0,0,1,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0],[0,0,0,0,1,0,0,0],[0,0,0,1,0,0,0,0],
                     [0,0,1,0,0,0,0,0],[0,1,0,0,0,0,0,0]],
    "two-dots L→R": [[1,0,0,0,1,0,0,0],[0,1,0,0,0,1,0,0],[0,0,1,0,0,0,1,0],
                     [0,0,0,1,0,0,0,1],[1,0,0,0,1,0,0,0],[0,1,0,0,0,1,0,0],
                     [0,0,1,0,0,0,1,0],[0,0,0,1,0,0,0,1]],
}
NOVEL_PATTERNS = {
    "slow L→R [NEW]":        [[1,0,0,0,0,0,0,0],[1,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0],
                               [0,1,0,0,0,0,0,0],[0,0,1,0,0,0,0,0],[0,0,1,0,0,0,0,0],
                               [0,0,0,1,0,0,0,0],[0,0,0,1,0,0,0,0]],
    "three-dots L→R [NEW]":  [[1,0,0,1,0,0,1,0],[0,1,0,0,1,0,0,1],[1,0,1,0,0,1,0,0],
                               [0,1,0,1,0,0,1,0],[1,0,1,0,1,0,0,1],[0,1,0,1,0,1,0,0],
                               [1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1]],
}
POSITIONS = [round(0.1 * (i + 1), 1) for i in range(8)]


def _set_frame(sensors: list[SensorNode], frame: list[float]) -> None:
    for i, (s, v) in enumerate(zip(sensors, frame)):
        s.set_input(np.array([POSITIONS[i], float(v)]))


def _eval_patterns(
    net: PCNetwork,
    sensors: list[SensorNode],
    patterns: dict,
    n_passes: int = 3,
) -> tuple[float, float]:
    s_errs, h_errs = [], []
    for frames in patterns.values():
        for _ in range(n_passes):
            for row in frames:
                _set_frame(sensors, row)
                net.step(learn=False)
                net.commit_step()
                s_errs.append(float(np.mean([
                    np.sum(net.node(f"s{i}").epsilon ** 2) for i in range(8)
                ])))
                h_errs.append(float(np.mean([
                    np.sum(net.node(f"h{i}").epsilon ** 2) for i in range(8)
                ])))
    return float(np.mean(s_errs)), float(np.mean(h_errs))


def reconstruction_score(
    eta_temporal: float,
    w_clip_V: float,
    forward_mode: str,
    seed: int = 0,
    n_epochs: int = 8,
    n_repeats: int = 3,
) -> tuple[float, float]:
    """Train on test_pc2 patterns; return (sensor_err, state_err) on novel patterns."""
    rng = np.random.default_rng(seed)
    net = PCNetwork(
        eta_inf=0.02, n_relax=80, eps_tol=1e-5,
        alpha=1.0, beta=1.0, gamma=0.3,
        eta_learn=0.002,
        eta_temporal=eta_temporal,
        lambda_decay=0.0, w_clip=3.0, rng=rng,
    )
    sensors: list[SensorNode] = []
    for i in range(8):
        sensors.append(net.add(SensorNode(f"s{i}", dim=2)))
    for i in range(8):
        h = net.add(PCNode(f"h{i}", dim=8, activation="tanh", rng=rng))
        h.w_clip_V = w_clip_V
        _apply_forward_mode(h, forward_mode)
    top = net.add(PCNode("top", dim=16, activation="tanh", rng=rng))
    top.w_clip_V = w_clip_V
    _apply_forward_mode(top, forward_mode)

    for i in range(8):
        net.connect(f"h{i}", f"s{i}", ConnType.UP)
        if i > 0:
            net.connect(f"h{i-1}", f"h{i}", ConnType.LATERAL)
            net.connect(f"h{i}",   f"h{i-1}", ConnType.LATERAL)
    for i in range(8):
        net.connect("top", f"h{i}", ConnType.UP)

    pattern_list = list(TRAIN_PATTERNS.values())
    for _ in range(n_epochs):
        for frames in pattern_list:
            for _ in range(n_repeats):
                for row in frames:
                    _set_frame(sensors, row)
                    net.step(learn=True)
                    net.commit_step()

    return _eval_patterns(net, sensors, NOVEL_PATTERNS)


# ---------------------------------------------------------------------------
# Sweep grid
# ---------------------------------------------------------------------------

@dataclass
class SweepResult:
    eta_temporal: float
    w_clip_V: float
    forward_mode: str
    anticipation: float   # higher = better (V learned dynamics)
    sensor_err: float     # lower = better
    state_err: float      # lower = better
    seconds: float


def run_sweep(seeds: list[int] = (0, 1, 2)) -> list[SweepResult]:
    eta_vals   = [0.001, 0.005, 0.01, 0.02, 0.05]
    clip_vals  = [1.0, 3.0, 5.0, 10.0]
    modes      = ["double", "single"]

    results = []
    total = len(eta_vals) * len(clip_vals) * len(modes)
    idx = 0
    for mode in modes:
        for eta in eta_vals:
            for clip in clip_vals:
                idx += 1
                t0 = time.time()
                ants, serrs, herrs = [], [], []
                for seed in seeds:
                    ants.append(anticipation_score(eta, clip, mode, seed=seed))
                    s, h = reconstruction_score(eta, clip, mode, seed=seed)
                    serrs.append(s); herrs.append(h)
                r = SweepResult(
                    eta_temporal=eta,
                    w_clip_V=clip,
                    forward_mode=mode,
                    anticipation=float(np.mean(ants)),
                    sensor_err=float(np.mean(serrs)),
                    state_err=float(np.mean(herrs)),
                    seconds=time.time() - t0,
                )
                elapsed = r.seconds
                print(f"  [{idx:2d}/{total}] {mode:6s} eta={eta:.3f} clip={clip:5.1f}"
                      f"  ant={r.anticipation:.2f}  sensor={r.sensor_err:.4f}"
                      f"  state={r.state_err:.4f}  ({elapsed:.0f}s)")
                results.append(r)
    return results


def print_table(results: list[SweepResult]) -> None:
    # Normalise metrics → rank-score: higher anticipation better, lower errors better.
    ants   = [r.anticipation for r in results]
    serrs  = [r.sensor_err   for r in results]
    herrs  = [r.state_err    for r in results]
    a_max, a_min = max(ants), min(ants)
    s_max, s_min = max(serrs), min(serrs)
    h_max, h_min = max(herrs), min(herrs)

    def norm_score(r: SweepResult) -> float:
        a_s = (r.anticipation - a_min) / (a_max - a_min + 1e-9)
        s_s = (s_max - r.sensor_err)   / (s_max - s_min + 1e-9)
        h_s = (h_max - r.state_err)    / (h_max - h_min + 1e-9)
        return (a_s + s_s + h_s) / 3.0

    ranked = sorted(results, key=norm_score, reverse=True)

    W = 80
    print()
    print("=" * W)
    print("  Sweep: V-Forward-Modell-Parameter (eta_temporal × w_clip_V × forward_mode)")
    print("  Metriken: anticipation↑ (V lernt Dynamik)  sensor_err↓  state_err↓")
    print("=" * W)
    print(f"  {'config':<35s} {'ant↑':>6s} {'sensor↓':>8s} {'state↓':>8s} {'score':>7s}")
    print("-" * W)
    for r in ranked:
        sc = norm_score(r)
        label = f"{r.forward_mode:6s} eta={r.eta_temporal:.3f} clip={r.w_clip_V:5.1f}"
        print(f"  {label:<35s} {r.anticipation:6.2f}   {r.sensor_err:7.4f}   {r.state_err:7.4f}   {sc:6.3f}")
    print("=" * W)
    best = ranked[0]
    print(f"  Beste Konfiguration: {best.forward_mode}, eta_temporal={best.eta_temporal},"
          f" w_clip_V={best.w_clip_V}")
    print(f"    anticipation={best.anticipation:.2f}x,"
          f" sensor_err={best.sensor_err:.4f}, state_err={best.state_err:.4f}")
    print("=" * W)


if __name__ == "__main__":
    from dataclasses import dataclass  # re-import for __main__ scope guard
    print(f"Starte V-Parameter-Sweep ({5 * 4 * 2} Konfigurationen, 3 Seeds je)...")
    results = run_sweep(seeds=[0, 1, 2])
    print_table(results)
