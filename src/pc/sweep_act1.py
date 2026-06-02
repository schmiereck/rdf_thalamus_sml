"""
sweep_act1.py — Architecture / hyperparameter sweep for the active-inference fovea.

Trains many network configurations headless (no terminal animation) and ranks
them by how well the eye learns to TRACK a moving object — the strongest
behavioural signal we have — alongside the raw prediction errors.

Tracking metric (efficiency)
----------------------------
For each frame we compute the object's centre of mass in world coordinates
(com).  Its retinal position is  com - phi.  Perfect tracking keeps the object
at a fixed retinal location, i.e.  Δ(com - phi) ≈ 0.  With a frozen eye the
retinal slip would equal the object's own world velocity Δcom.  Hence

    tracking_efficiency = 1 - mean|Δ(com - phi)| / mean|Δcom|

      1.0  perfect pursuit (object pinned on the retina)
      0.0  eye stationary (no better than staring straight ahead)
     <0    eye actively makes things worse

Only frames where the object is visible *and* moving contribute, and the
metric is measured in a dedicated evaluation pass (action on, learning off).

Usage
-----
    python sweep_act1.py                 # run the default sweep
    python sweep_act1.py --quick         # smaller/faster sweep
    python sweep_act1.py --jobs 4        # parallel workers
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pc.pattern_generator import PatternGenerator
from pc.test_pc_act1 import (
    build_network,
    apply_fovea_shift,
    compute_action_gradient,
    set_frame,
)


# ---------------------------------------------------------------------------
# Configuration of a single run
# ---------------------------------------------------------------------------

@dataclass
class RunConfig:
    name: str
    # architecture
    n_inputs: int = 16
    n_layers: int = 3
    base_dim: int = 4
    dim_growth: int = 2
    lateral_steps: int = 1
    recurrent: bool = False
    tau_base: float = 0.0
    # network dynamics
    eta_inf: float = 0.05
    n_relax: int = 40
    eta_learn: float = 0.002
    gamma: float = 0.3
    # action / fovea
    max_v: float = 2.0
    action_gain: float = 0.7
    action_smooth: float = 0.2
    spring_k: float = 0.05
    passive_drift: float = 0.3
    # training budget
    n_train_patterns: int = 8
    repeats_per_seq: int = 2
    n_epochs_passive: int = 5
    n_epochs_active: int = 12
    # reproducibility
    seed: int = 42


# ---------------------------------------------------------------------------
# Tracking helpers
# ---------------------------------------------------------------------------

def world_com(frame: list[float]) -> float | None:
    """Intensity-weighted centre of mass of a world frame, or None if empty."""
    arr = np.asarray(frame, dtype=float)
    total = arr.sum()
    if total < 1e-6:
        return None
    return float((np.arange(arr.size) * arr).sum() / total)


# ---------------------------------------------------------------------------
# One headless train + eval run
# ---------------------------------------------------------------------------

def run_one(cfg: RunConfig) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(cfg.seed)

    net, visual_sensors, motor_sensor = build_network(
        rng,
        n_inputs=cfg.n_inputs,
        n_layers=cfg.n_layers,
        base_dim=cfg.base_dim,
        dim_growth=cfg.dim_growth,
        lateral_steps=cfg.lateral_steps,
        eta_inf=cfg.eta_inf,
        n_relax=cfg.n_relax,
        eta_learn=cfg.eta_learn,
        gamma=cfg.gamma,
        recurrent=cfg.recurrent,
        tau_base=cfg.tau_base,
    )

    phi_min, phi_max = -float(cfg.n_inputs), float(cfg.n_inputs)
    n = cfg.n_inputs

    # Fixed pattern sets (train uses simple bias; eval is a separate, moving set)
    train_patterns = [
        (str(spec), frames)
        for frames, spec in PatternGenerator(
            n_inputs=n, seed=cfg.seed, bias_simple=True
        ).stream(max_sequences=cfg.n_train_patterns)
    ]
    eval_patterns = [
        (str(spec), frames)
        for frames, spec in PatternGenerator(
            n_inputs=n, seed=cfg.seed + 7777
        ).stream(max_sequences=6)
    ]

    # ---- Training ----
    phi = 0.0
    v = 0.0
    diverged = False
    for epoch in range(cfg.n_epochs_passive + cfg.n_epochs_active):
        action_enabled = epoch >= cfg.n_epochs_passive
        phi = 0.0
        v = 0.0
        for _name, world_frames in train_patterns:
            for _ in range(cfg.repeats_per_seq):
                for world_frame in world_frames:
                    shifted = apply_fovea_shift(world_frame, phi, n)
                    set_frame(visual_sensors, shifted)
                    motor_sensor.set_input(np.array([v / cfg.max_v]))

                    action_grad = 0.0
                    if action_enabled:
                        net.phase_predict()
                        net.phase_error()
                        action_grad = compute_action_gradient(visual_sensors, shifted)

                    net.step(learn=True)
                    net.commit_step()

                    if action_enabled:
                        v_target = -cfg.action_gain * action_grad - cfg.spring_k * phi
                        v = float(np.clip(
                            (1.0 - cfg.action_smooth) * v_target + cfg.action_smooth * v,
                            -cfg.max_v, cfg.max_v,
                        ))
                    else:
                        v = float(np.clip(
                            rng.normal(0.0, cfg.passive_drift), -cfg.max_v, cfg.max_v
                        ))
                    phi = float(np.clip(phi + v, phi_min, phi_max))

    # ---- Evaluation (action on, learning off): tracking + errors ----
    s_errs, st_errs, m_errs = [], [], []
    slip_tracked, slip_frozen = [], []

    for _name, world_frames in eval_patterns:
        phi = 0.0
        v = 0.0
        prev_retinal = None
        prev_com = None
        for world_frame in world_frames:
            shifted = apply_fovea_shift(world_frame, phi, n)
            set_frame(visual_sensors, shifted)
            motor_sensor.set_input(np.array([v / cfg.max_v]))

            net.phase_predict()
            net.phase_error()
            action_grad = compute_action_gradient(visual_sensors, shifted)

            info = net.step(learn=False)
            net.commit_step()
            m_err = float(np.sum(net.node("motor").epsilon ** 2))
            s_errs.append(info["sensor_error"] - m_err)
            st_errs.append(info["state_error"])
            m_errs.append(m_err)

            # tracking bookkeeping (object centre of mass in the world)
            com = world_com(world_frame)
            if com is not None:
                retinal = com - phi
                if prev_retinal is not None and prev_com is not None:
                    slip_tracked.append(abs(retinal - prev_retinal))
                    slip_frozen.append(abs(com - prev_com))
                prev_retinal = retinal
                prev_com = com
            else:
                prev_retinal = None
                prev_com = None

            # apply action
            v_target = -cfg.action_gain * action_grad - cfg.spring_k * phi
            v = float(np.clip(
                (1.0 - cfg.action_smooth) * v_target + cfg.action_smooth * v,
                -cfg.max_v, cfg.max_v,
            ))
            phi = float(np.clip(phi + v, phi_min, phi_max))

    def _safe_mean(xs):
        xs = [x for x in xs if np.isfinite(x)]
        return float(np.mean(xs)) if xs else float("nan")

    mean_slip_tracked = _safe_mean(slip_tracked)
    mean_slip_frozen = _safe_mean(slip_frozen)
    if mean_slip_frozen and mean_slip_frozen > 1e-6 and np.isfinite(mean_slip_tracked):
        tracking_eff = 1.0 - mean_slip_tracked / mean_slip_frozen
    else:
        tracking_eff = float("nan")

    sensor_err = _safe_mean(s_errs)
    state_err = _safe_mean(st_errs)
    if (not np.isfinite(sensor_err) or sensor_err > 1e6
            or not np.isfinite(state_err) or state_err > 1e6):
        diverged = True

    return {
        "name": cfg.name,
        "tracking_eff": tracking_eff,
        "slip_tracked": mean_slip_tracked,
        "slip_frozen": mean_slip_frozen,
        "sensor_err": sensor_err,
        "state_err": state_err,
        "motor_err": _safe_mean(m_errs),
        "n_params": net.total_parameters(),
        "diverged": diverged,
        "seconds": time.time() - t0,
        "config": asdict(cfg),
    }


# ---------------------------------------------------------------------------
# Sweep definitions
# ---------------------------------------------------------------------------

def build_focused_sweep() -> list[RunConfig]:
    """
    Targeted follow-up sweep based on sweep 1 findings:
      - base_dim=8 and lateral=0 were the strongest 'real' improvements
      - action_gain=1.0 was the single biggest tracking lever
    We now cross these factors and probe action_gain further (1.0–1.6),
    averaging each config over 3 different random seeds to reduce noise.
    """
    seeds = [42, 123, 777]
    base = dict(n_epochs_passive=5, n_epochs_active=12,
                n_train_patterns=8, repeats_per_seq=2)

    combos = [
        # name-suffix          kwargs
        ("baseline L3",        dict()),
        ("d8 lat0",            dict(base_dim=8, lateral_steps=0)),
        ("d8 lat0 g1.0",       dict(base_dim=8, lateral_steps=0, action_gain=1.0)),
        ("d8 lat0 g1.3",       dict(base_dim=8, lateral_steps=0, action_gain=1.3)),
        ("d8 lat0 g1.6",       dict(base_dim=8, lateral_steps=0, action_gain=1.6)),
        ("d8 lat0 g1.0 L2",    dict(base_dim=8, lateral_steps=0, action_gain=1.0, n_layers=2)),
        ("d8 lat0 g1.0 L4",    dict(base_dim=8, lateral_steps=0, action_gain=1.0, n_layers=4)),
        ("d6 lat0 g1.0",       dict(base_dim=6, lateral_steps=0, action_gain=1.0)),
        ("d8 lat0 g1.0 sp.02", dict(base_dim=8, lateral_steps=0, action_gain=1.0, spring_k=0.02)),
        ("d8 lat0 g1.0 sp.10", dict(base_dim=8, lateral_steps=0, action_gain=1.0, spring_k=0.10)),
    ]

    configs: list[RunConfig] = []
    for label, kw in combos:
        for seed in seeds:
            configs.append(RunConfig(
                name=f"{label} s{seed}",
                seed=seed,
                **kw,
                **base,
            ))
    return configs


def aggregate_focused(results: list[dict]) -> list[dict]:
    """Average metrics across seeds for configs sharing the same base name."""
    from collections import defaultdict
    import re
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        # strip trailing " sNNN"
        base_name = re.sub(r" s\d+$", "", r["name"])
        groups[base_name].append(r)

    aggregated = []
    for base_name, rs in groups.items():
        valid = [r for r in rs if not r["diverged"] and np.isfinite(r["tracking_eff"])]
        if not valid:
            valid = rs  # keep diverged entries so table isn't empty
        def _m(key):
            vals = [r[key] for r in valid if np.isfinite(r[key])]
            return float(np.mean(vals)) if vals else float("nan")
        def _s(key):
            vals = [r[key] for r in valid if np.isfinite(r[key])]
            return float(np.std(vals)) if len(vals) > 1 else 0.0
        aggregated.append({
            "name": base_name,
            "tracking_eff": _m("tracking_eff"),
            "tracking_std": _s("tracking_eff"),
            "slip_tracked": _m("slip_tracked"),
            "slip_frozen":  _m("slip_frozen"),
            "sensor_err":   _m("sensor_err"),
            "state_err":    _m("state_err"),
            "motor_err":    _m("motor_err"),
            "n_params":     int(np.mean([r["n_params"] for r in rs])),
            "diverged":     any(r["diverged"] for r in rs),
            "seconds":      sum(r["seconds"] for r in rs),
            "n_seeds":      len(rs),
        })
    return sorted(aggregated,
                  key=lambda r: (r["diverged"],
                                 -(r["tracking_eff"] if np.isfinite(r["tracking_eff"]) else -9)))


def print_focused_table(results: list[dict]) -> None:
    agg = aggregate_focused(results)
    print(f"\n{'='*102}")
    print("  Focused sweep — averaged over 3 seeds, ranked by tracking efficiency")
    print(f"{'='*102}")
    print(f"  {'config':<26s} {'track_eff':>9s} {'±std':>5s} {'slip↓':>7s} "
          f"{'sensor':>8s} {'state':>8s} {'params':>7s} {'total_s':>7s}")
    print(f"  {'-'*96}")

    def _fmt(x, w=8):
        if not np.isfinite(x):   return f"{'nan':>{w}s}"
        if abs(x) >= 1e4:        return f"{'OVF':>{w}s}"
        return f"{x:{w}.3f}"

    for r in agg:
        flag = "  ⚠DIV" if r["diverged"] else ""
        te = r["tracking_eff"]
        te_s = f"{te:9.3f}" if np.isfinite(te) else f"{'n/a':>9s}"
        std_s = f"{r['tracking_std']:5.3f}"
        print(f"  {r['name']:<26s} {te_s} {std_s} {_fmt(r['slip_tracked'],7)} "
              f"{_fmt(r['sensor_err'])} {_fmt(r['state_err'])} "
              f"{r['n_params']:7d} {r['seconds']:7.0f}{flag}")
    print(f"{'='*102}")

    valid = [r for r in agg if not r["diverged"] and np.isfinite(r["tracking_eff"])]
    if valid:
        best = valid[0]
        print(f"\n  Best: {best['name']}  "
              f"efficiency={best['tracking_eff']:.3f} ±{best['tracking_std']:.3f}, "
              f"sensor_err={best['sensor_err']:.3f}")
    print()


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def build_sweep(quick: bool) -> list[RunConfig]:
    """One-factor-at-a-time sweep around a sensible baseline."""
    base = dict(
        n_epochs_passive=3 if quick else 5,
        n_epochs_active=6 if quick else 12,
        n_train_patterns=6 if quick else 8,
        repeats_per_seq=2,
    )
    configs: list[RunConfig] = []

    configs.append(RunConfig(name="baseline (L3 d4+2 lat1)", **base))

    configs.append(RunConfig(name="depth: L2",  n_layers=2, **base))
    configs.append(RunConfig(name="depth: L4",  n_layers=4, **base))

    configs.append(RunConfig(name="dim: base6",   base_dim=6,   **base))
    configs.append(RunConfig(name="dim: base8",   base_dim=8,   **base))
    configs.append(RunConfig(name="dim: growth0", dim_growth=0, **base))
    configs.append(RunConfig(name="dim: growth4", dim_growth=4, **base))

    configs.append(RunConfig(name="lateral: 0", lateral_steps=0, **base))
    configs.append(RunConfig(name="lateral: 2", lateral_steps=2, **base))

    if not quick:
        configs.append(RunConfig(name="relax: 20",      n_relax=20,      **base))
        configs.append(RunConfig(name="relax: 80",      n_relax=80,      **base))
        configs.append(RunConfig(name="eta_learn:.004", eta_learn=0.004, **base))
        configs.append(RunConfig(name="eta_inf:.10",    eta_inf=0.10,    **base))
        configs.append(RunConfig(name="gain: 1.0",      action_gain=1.0, **base))
        configs.append(RunConfig(name="spring: 0.10",   spring_k=0.10,   **base))
        configs.append(RunConfig(name="spring: 0.02",   spring_k=0.02,   **base))
        configs.append(RunConfig(name="combo L4 d6 lat2",
                                 n_layers=4, base_dim=6, lateral_steps=2, **base))
    return configs


def print_table(results: list[dict]) -> None:
    results = sorted(
        results,
        key=lambda r: (r["diverged"], -(r["tracking_eff"] if np.isfinite(r["tracking_eff"]) else -9)),
    )
    print(f"\n{'='*92}")
    print("  Sweep results — ranked by tracking efficiency (higher = eye follows object better)")
    print(f"{'='*92}")
    print(f"  {'config':<26s} {'track_eff':>9s} {'slip↓':>7s} {'sensor':>8s} "
          f"{'state':>8s} {'motor':>8s} {'params':>7s} {'sec':>5s}")
    print(f"  {'-'*88}")
    def _fmt(x: float, w: int = 8) -> str:
        if not np.isfinite(x):
            return f"{'nan':>{w}s}"
        if abs(x) >= 1e4:
            return f"{'OVF':>{w}s}"
        return f"{x:{w}.3f}"

    for r in results:
        flag = "  ⚠DIV" if r["diverged"] else ""
        te = r["tracking_eff"]
        te_s = f"{te:9.3f}" if np.isfinite(te) else f"{'n/a':>9s}"
        print(f"  {r['name']:<26s} {te_s} {_fmt(r['slip_tracked'], 7)} "
              f"{_fmt(r['sensor_err'])} {_fmt(r['state_err'])} {_fmt(r['motor_err'])} "
              f"{r['n_params']:7d} {r['seconds']:5.0f}{flag}")
    print(f"{'='*92}")

    finite = [r for r in results if np.isfinite(r["tracking_eff"]) and not r["diverged"]]
    if finite:
        best = finite[0]
        print(f"\n  Best tracking: {best['name']}  "
              f"(efficiency={best['tracking_eff']:.3f}, "
              f"slip={best['slip_tracked']:.3f} vs frozen {best['slip_frozen']:.3f})")
        c = best["config"]
        print(f"    L{c['n_layers']}  base_dim={c['base_dim']}  growth={c['dim_growth']}  "
              f"lateral={c['lateral_steps']}  relax={c['n_relax']}  "
              f"eta_inf={c['eta_inf']}  eta_learn={c['eta_learn']}  "
              f"gain={c['action_gain']}  spring={c['spring_k']}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick",   action="store_true", help="smaller/faster sweep")
    ap.add_argument("--focused", action="store_true", help="targeted follow-up sweep (3-seed average)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                    help="parallel worker processes")
    args = ap.parse_args()

    if args.focused:
        configs = build_focused_sweep()
        mode = "focused"
    else:
        configs = build_sweep(args.quick)
        mode = "quick" if args.quick else "full"
    print(f"Running {len(configs)} configurations on {args.jobs} worker(s) [{mode}] ...\n")

    results: list[dict] = []
    if args.jobs <= 1:
        for cfg in configs:
            r = run_one(cfg)
            results.append(r)
            _progress(r, len(results), len(configs))
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(run_one, cfg): cfg for cfg in configs}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                _progress(r, len(results), len(configs))

    if args.focused:
        print_focused_table(results)
    else:
        print_table(results)


def _progress(r: dict, done: int, total: int) -> None:
    te = r["tracking_eff"]
    te_s = f"{te:.3f}" if np.isfinite(te) else "n/a"
    print(f"  [{done:2d}/{total}] {r['name']:<26s} "
          f"track_eff={te_s:>7s}  sensor={r['sensor_err']:7.3f}  ({r['seconds']:.0f}s)")


if __name__ == "__main__":
    main()
