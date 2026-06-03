"""
diag_pc_act3.py — Diagnose: folgt der Pointer dem Objekt oder nur der Feder?

Trainiert das Netz wie test_pc_act3 und misst dann drei Bedingungen in der
Evaluationsphase (kein Lernen):

  FULL    : Fovea-Action + Pointer-Action (volle Netz-Steuerung)
  SPRING  : Fovea-Action + Pointer nur Feder (POINTER_ACTION_GAIN=0)
  STILL   : Fovea-Action + Pointer fest in der Mitte (p=centre)

Metriken pro Bedingung:
  pointer_eff  = 1 − mean|Δ(p−com)| / mean|Δcom|   (wie tracking_eff der Fovea)
  mean_dist    = mean|p − com|                       (mittlerer Abstand Pointer↔Objekt)
  centre_dist  = mean|p − N/2|                       (wie weit weg von Mitte?)
  corr(p,com)  = Pearson-Korrelation zw. Pointer-Pos. und Objekt-COM

Eine positive pointer_eff und hohe corr(p,com) beweisen echtes Folge-Verhalten.
Wenn FULL ≈ SPRING bei pointer_eff: das Netz trägt nichts bei — nur die Feder.

Run:  python src/pc/diag_pc_act3.py          # quick budget (~5 min)
      python src/pc/diag_pc_act3.py --full   # full budget matching test_pc_act3
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--full", action="store_true")
_args, _ = _parser.parse_known_args()

import numpy as np
from pc.test_pc_act3 import (
    build_network,
    apply_fovea_shift,
    render_pointer_row,
    set_frame,
    compute_action_gradient,
    sample_bounce_patterns,
    world_com,
)

# ---- Training config ----
N_INPUTS          = 16
N_LAYERS          = 3
BASE_DIM          = 4
DIM_GROWTH        = 2
LATERAL_STEPS     = 0
ETA_LEARN         = 0.004

if _args.full:
    # Full budget — matches test_pc_act3.py defaults exactly
    N_TRAIN_PATTERNS  = 10
    REPEATS_PER_SEQ   = 3
    N_EPOCHS_PASSIVE  = 8
    N_EPOCHS_ORACLE   = 8
    N_EPOCHS_ACTIVE   = 34
    N_RELAX           = 40
else:
    # Quick budget — finishes in ~5 min, directional answer
    N_TRAIN_PATTERNS  = 6
    REPEATS_PER_SEQ   = 2
    N_EPOCHS_PASSIVE  = 3
    N_EPOCHS_ORACLE   = 4
    N_EPOCHS_ACTIVE   = 12
    N_RELAX           = 25
ORACLE_TARGET     = 0.35
MAX_V             = 2.0
MAX_VP            = 2.0
ACTION_GAIN       = 1.5
ACTION_SMOOTH     = 0.2
SPRING_K          = 0.05
PASSIVE_DRIFT     = 0.3
PASSIVE_SPRING_K  = 0.30
POINTER_WIDTH     = 2
POINTER_MASS      = 1.0
POINTER_DAMPING   = 0.15
POINTER_ACTION_GAIN = 1.5
POINTER_SPRING_K  = 0.04
POINTER_DRIFT     = 0.3
PHI_MIN = float(-N_INPUTS)
PHI_MAX = float(N_INPUTS)
P_MIN   = 0.0
P_MAX   = float(N_INPUTS - 1)


def _pointer_step(p: float, vp: float, phi: float, force: float) -> tuple[float, float]:
    """Advance pointer one step with given force."""
    gc = phi + N_INPUTS / 2.0
    f_spring = -POINTER_SPRING_K * (p - gc)
    accel = (force + f_spring) / POINTER_MASS
    vp = float(np.clip((vp + accel) * (1.0 - POINTER_DAMPING), -MAX_VP, MAX_VP))
    p  = float(np.clip(p + vp, P_MIN, P_MAX))
    return p, vp


def train(rng: np.random.Generator, train_patterns: list):
    """Full training run. Returns (net, object_sensors, pointer_sensors, motor_sensor)."""
    net, obj, ptr, motor = build_network(
        rng, n_inputs=N_INPUTS, n_layers=N_LAYERS, base_dim=BASE_DIM,
        dim_growth=DIM_GROWTH, lateral_steps=LATERAL_STEPS, eta_learn=ETA_LEARN,
        n_relax=N_RELAX,
    )
    phi, v, p, vp = 0.0, 0.0, (N_INPUTS - 1) / 2.0, 0.0
    prev_rcom = None
    oracle_start = N_EPOCHS_PASSIVE
    active_start = N_EPOCHS_PASSIVE + N_EPOCHS_ORACLE
    total_epochs = active_start + N_EPOCHS_ACTIVE

    for epoch in range(total_epochs):
        oracle_en = oracle_start <= epoch < active_start
        action_en = epoch >= active_start
        phi, v, p, vp = 0.0, 0.0, (N_INPUTS - 1) / 2.0, 0.0
        prev_rcom = None
        for _name, frames in train_patterns:
            for _ in range(REPEATS_PER_SEQ):
                for world_frame in frames:
                    shifted     = apply_fovea_shift(world_frame, phi, N_INPUTS)
                    ptr_world   = render_pointer_row(p, N_INPUTS, POINTER_WIDTH)
                    ptr_shifted = apply_fovea_shift(ptr_world, phi, N_INPUTS)
                    set_frame(obj,   shifted)
                    set_frame(ptr,   ptr_shifted)
                    motor.set_input(np.array([v / MAX_V, vp / MAX_VP]))

                    _disp, _pdisp = 0.0, 0.0
                    if action_en:
                        net.phase_predict(); net.phase_error()
                        _disp  = -compute_action_gradient(obj, shifted)
                        _pdisp = -compute_action_gradient(ptr, ptr_shifted, anticipatory=False)

                    net.step(learn=True); net.commit_step()

                    # Fovea update
                    if action_en:
                        vt = _disp * ACTION_GAIN - SPRING_K * phi
                        v  = float(np.clip((1-ACTION_SMOOTH)*vt + ACTION_SMOOTH*v, -MAX_V, MAX_V))
                    elif oracle_en:
                        com = world_com(world_frame)
                        v = float(np.clip((com - ORACLE_TARGET*N_INPUTS) - phi, -MAX_V, MAX_V)) \
                            if com is not None else 0.0
                    else:
                        v = float(np.clip(rng.normal(0, PASSIVE_DRIFT) - PASSIVE_SPRING_K*phi,
                                          -MAX_V, MAX_V))
                    phi = float(np.clip(phi + v, PHI_MIN, PHI_MAX))

                    # Pointer update
                    ptr_force = POINTER_ACTION_GAIN * _pdisp if action_en \
                                else rng.normal(0, POINTER_DRIFT)
                    p, vp = _pointer_step(p, vp, phi, ptr_force)

        done = epoch + 1
        if done % 10 == 0 or done == total_epochs:
            print(f"  epoch {done}/{total_epochs}", flush=True)
    return net, obj, ptr, motor


def evaluate(
    net, obj_sensors, ptr_sensors, motor_sensor,
    eval_patterns: list,
    pointer_gain: float,        # POINTER_ACTION_GAIN to use (0 = spring only)
    fixed_ptr: bool = False,    # True = pointer frozen at centre each frame
    label: str = "",
) -> dict:
    """
    Evaluate one condition.  Returns dict with pointer_eff, mean_dist,
    centre_dist, and correlation(p, com).
    """
    p_hist, com_hist = [], []
    slip_tracked, slip_frozen = [], []
    prev_p_minus_com = None
    prev_com = None

    for _name, frames in eval_patterns:
        phi, v, p, vp = 0.0, 0.0, (N_INPUTS - 1) / 2.0, 0.0
        for world_frame in frames:
            shifted     = apply_fovea_shift(world_frame, phi, N_INPUTS)
            ptr_world   = render_pointer_row(p, N_INPUTS, POINTER_WIDTH)
            ptr_shifted = apply_fovea_shift(ptr_world, phi, N_INPUTS)
            set_frame(obj_sensors,   shifted)
            set_frame(ptr_sensors,   ptr_shifted)
            motor_sensor.set_input(np.array([v / MAX_V, vp / MAX_VP]))

            net.phase_predict(); net.phase_error()
            _disp  = -compute_action_gradient(obj_sensors, shifted)
            _pdisp = -compute_action_gradient(ptr_sensors, ptr_shifted, anticipatory=False)
            net.step(learn=False); net.commit_step()

            # Fovea velocity (always full action during eval)
            vt = _disp * ACTION_GAIN - SPRING_K * phi
            v  = float(np.clip((1-ACTION_SMOOTH)*vt + ACTION_SMOOTH*v, -MAX_V, MAX_V))
            phi = float(np.clip(phi + v, PHI_MIN, PHI_MAX))

            # Pointer update according to condition
            if fixed_ptr:
                p  = (N_INPUTS - 1) / 2.0   # always centred
                vp = 0.0
            else:
                ptr_force = pointer_gain * _pdisp
                p, vp = _pointer_step(p, vp, phi, ptr_force)

            com = world_com(world_frame)
            if com is not None:
                p_hist.append(p)
                com_hist.append(com)
                pmc = p - com
                if prev_p_minus_com is not None and prev_com is not None:
                    slip_tracked.append(abs(pmc - prev_p_minus_com))
                    slip_frozen.append(abs(com - prev_com))
                prev_p_minus_com = pmc
                prev_com = com
            else:
                prev_p_minus_com = None
                prev_com = None

    p_arr   = np.array(p_hist)
    com_arr = np.array(com_hist)
    centre  = (N_INPUTS - 1) / 2.0

    mean_slip_t = float(np.mean(slip_tracked)) if slip_tracked else float("nan")
    mean_slip_f = float(np.mean(slip_frozen))  if slip_frozen  else float("nan")
    if np.isfinite(mean_slip_f) and mean_slip_f > 1e-6:
        ptr_eff = 1.0 - mean_slip_t / mean_slip_f
    else:
        ptr_eff = float("nan")

    mean_dist    = float(np.mean(np.abs(p_arr - com_arr))) if len(p_arr) else float("nan")
    centre_dist  = float(np.mean(np.abs(p_arr - centre)))  if len(p_arr) else float("nan")

    if len(p_arr) > 2 and np.std(p_arr) > 1e-6 and np.std(com_arr) > 1e-6:
        corr = float(np.corrcoef(p_arr, com_arr)[0, 1])
    else:
        corr = float("nan")

    print(f"  {label:<12s}  ptr_eff={ptr_eff:+.3f}  "
          f"mean|p-com|={mean_dist:.2f}px  "
          f"mean|p-N/2|={centre_dist:.2f}px  "
          f"corr(p,com)={corr:+.3f}")
    return dict(ptr_eff=ptr_eff, mean_dist=mean_dist,
                centre_dist=centre_dist, corr=corr, label=label)


def main() -> None:
    rng = np.random.default_rng(42)
    train_patterns = sample_bounce_patterns(N_INPUTS, seed=0,    n_sequences=N_TRAIN_PATTERNS)
    eval_patterns  = sample_bounce_patterns(N_INPUTS, seed=9999, n_sequences=10)

    print("Training …")
    net, obj, ptr, motor = train(rng, train_patterns)

    print("\nEvaluation (learn=False, 10 eval patterns):")
    print(f"  {'condition':<12s}  {'ptr_eff':>8s}  {'|p-com|':>10s}  "
          f"{'|p-N/2|':>10s}  {'corr(p,com)':>12s}")
    print("  " + "-" * 62)

    r_full   = evaluate(net, obj, ptr, motor, eval_patterns,
                        pointer_gain=POINTER_ACTION_GAIN, label="FULL")
    r_spring = evaluate(net, obj, ptr, motor, eval_patterns,
                        pointer_gain=0.0, label="SPRING-ONLY")
    r_still  = evaluate(net, obj, ptr, motor, eval_patterns,
                        pointer_gain=0.0, fixed_ptr=True, label="STILL")

    print()
    print("  Interpretation:")

    # Is the network doing something?
    net_contrib = r_full["ptr_eff"] - r_spring["ptr_eff"]
    print(f"  Network contribution to ptr_eff: {net_contrib:+.3f}  "
          f"({'yes, positive' if net_contrib > 0.02 else 'negligible or negative'})")

    # Is pointer near object or just near centre?
    if np.isfinite(r_full["mean_dist"]) and np.isfinite(r_full["centre_dist"]):
        closer = "OBJECT" if r_full["mean_dist"] < r_full["centre_dist"] else "CENTRE"
        print(f"  Pointer is closer to: {closer}  "
              f"(|p-com|={r_full['mean_dist']:.2f}  vs  |p-N/2|={r_full['centre_dist']:.2f})")

    if np.isfinite(r_full["corr"]):
        print(f"  corr(p, com) = {r_full['corr']:+.3f}  "
              f"({'positive spatial correlation' if r_full['corr'] > 0.3 else 'weak'})")

    print()


if __name__ == "__main__":
    main()
