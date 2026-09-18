"""D0: measure Y/T descriptor separation and the operational open-set claim.

Protocol: wiki/messungen/dream-rsi-yt-trennbarkeit.md.  This is a diagnostic
testbed; truth labels are used only after rendering for external scoring.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def sha_file(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def quantiles(values):
    import numpy as np
    return {str(q): float(np.quantile(values, q)) for q in (0.1, 0.5, 0.9)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    state_path = args.state.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ["MPLCONFIGDIR"] = str(out / "mpl")
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    inherited = {k: v for k, v in os.environ.items() if k.startswith("ACT")}
    for key in inherited:
        del os.environ[key]
    os.environ["ACT14_DOF"] = "4"
    os.environ["ACT14_HEADLESS"] = "1"
    os.environ["MPLBACKEND"] = "Agg"

    import mujoco
    import numpy as np
    import scipy
    from pc_cvnn.pc_act14 import BracketArmSim
    from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule

    start = time.perf_counter()
    original_hash = sha_file(state_path)
    with open(state_path, "rb") as stream:
        state = pickle.load(stream)
    if state.get("schema") != 2 or state.get("dof") != 4:
        raise ValueError("D0 Y/T probe requires schema=2 and dof=4")
    protocol = ROOT / "wiki/messungen/dream-rsi-yt-trennbarkeit.md"
    manifest = {
        "protocol": "d0-yt-separation-v1", "state_sha256": original_hash,
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "script_sha256": sha_file(__file__), "protocol_sha256": sha_file(protocol),
        "python": sys.version, "python_executable": sys.executable,
        "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
        "mujoco": mujoco.__version__, "seeds": [1703, 1704], "bootstrap_steps": 2500,
        "support_y": 3, "heldout_per_body": 32, "threads": 1,
        "ignored_inherited_switches": inherited,
        "source_hashes": {str(p.relative_to(ROOT)): sha_file(p) for p in [
            ROOT / "src/pc_cvnn/assets/bracket_arm.xml", ROOT / "src/pc_cvnn/pc_act14.py",
            ROOT / "src/pc_cvnn/arm_modules/shape_classifier.py"]},
    }
    write_json(out / "manifest.json", manifest)
    (out / "runner.py").write_bytes(Path(__file__).read_bytes())
    (out / "protocol.md").write_bytes(protocol.read_bytes())

    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    original_rgba = sim.m.geom_rgba.copy()
    all_bodies = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X", "obj_Y"]
    colors = [[0.1, 0.8, 0.85, 1.0], [0.45, 0.12, 0.9, 1.0], [0.95, 0.55, 0.1, 1.0]]

    def scene(rng, body, label):
        return {"id": label, "body": body,
                "xy": [float(rng.uniform(-0.09, 0.09)), float(rng.uniform(0.12, 0.21))],
                "yaw": float(rng.uniform(0, 2 * np.pi)),
                "rgba": colors[int(rng.integers(len(colors)))]}

    def set_scene(item):
        sim.reset_home()
        sim.m.geom_rgba[:] = original_rgba
        for index, body in enumerate(all_bodies):
            sim.set_object(body, [0.5 + 0.07 * index, -0.6], z=0.012)
        body = item["body"]
        sim.set_object(body, item["xy"], z=0.012, yaw=item["yaw"])
        bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
        first = sim.m.body_geomadr[bid]
        sim.m.geom_rgba[first:first + sim.m.body_geomnum[bid]] = item["rgba"]
        mujoco.mj_forward(sim.m, sim.d)

    summaries, rows = [], []
    try:
        for seed in manifest["seeds"]:
            bootstrap_rng = np.random.default_rng(seed + 200000)
            clf = ShapeClassifierModule(rng=bootstrap_rng)
            sim.m.geom_rgba[:] = original_rgba
            accuracy = float(clf.train(sim, steps=2500, rng=bootstrap_rng))
            support_rng = np.random.default_rng(seed + 300000)
            test_rng = np.random.default_rng(seed + 400000)
            support = [scene(support_rng, "obj_Y", f"support-y-{i}") for i in range(3)]
            tests = ([scene(test_rng, "obj_Y", f"test-y-{i}") for i in range(32)] +
                     [scene(test_rng, "obj_T", f"test-t-{i}") for i in range(32)])
            write_json(out / f"scenes-{seed}.json", {"support": support, "tests": tests})

            def feature(item):
                set_scene(item)
                saved = sim.d.mocap_pos.copy()
                try:
                    dets = clf.perceive_all(sim)
                finally:
                    sim.d.mocap_pos[:] = saved
                    mujoco.mj_forward(sim.m, sim.d)
                located = [(det, float(np.linalg.norm(np.asarray(det["pos"]) - item["xy"])))
                           for det in dets if det.get("pos") is not None]
                det, error = min(located, key=lambda x: x[1]) if located else (None, None)
                if det is None or error > 0.020:
                    raise RuntimeError(f"No valid detection for {item['id']}")
                return np.asarray(det["desc"], float), float(det.get("dicke", 0.0)), error

            support_data = [feature(item) for item in support]
            test_data = [feature(item) for item in tests]
            support_z = np.asarray([clf._z(x[0]) for x in support_data])
            test_z = np.asarray([clf._z(x[0]) for x in test_data])
            # Inject only in a throwaway readout: this imitates a three-view young Y class.
            readout = copy.deepcopy(clf)
            readout.open = {"y-probe": [x.copy() for x in support_z]}
            readout.open_names = ["y-probe"]
            claims, distances = [], []
            for item, (desc, thick, error), z in zip(tests, test_data, test_z):
                prediction, nearest = readout.resolve(desc, dicke=thick)
                support_distance = float(np.min(np.linalg.norm(support_z - z, axis=1)))
                claims.append(prediction == "y-probe")
                distances.append(support_distance)
                rows.append({"seed": seed, "id": item["id"], "body": item["body"],
                             "claim": prediction == "y-probe", "prediction": prediction,
                             "claim_distance": float(nearest), "nearest_y_distance": support_distance,
                             "dicke": thick, "position_error_m": error})
            labels = np.array([0] * 32 + [1] * 32)
            full = test_z
            sq = np.sum((full[:, None, :] - full[None, :, :]) ** 2, axis=2)
            np.fill_diagonal(sq, np.inf)
            loo = labels[np.argmin(sq, axis=1)]
            y_claims, t_claims = np.asarray(claims[:32]), np.asarray(claims[32:])
            y_dist, t_dist = np.asarray(distances[:32]), np.asarray(distances[32:])
            threshold = float(clf.novel_th * 1.6)
            result = {"seed": seed, "bootstrap_accuracy": accuracy, "novel_th": float(clf.novel_th),
                      "claim_radius": threshold, "y_claims": int(y_claims.sum()), "y_n": 32,
                      "t_false_claims": int(t_claims.sum()), "t_n": 32,
                      "y_distance_quantiles": quantiles(y_dist), "t_distance_quantiles": quantiles(t_dist),
                      "loo_1nn_accuracy": float(np.mean(loo == labels)),
                      "operational_pass": bool(y_claims.sum() >= 24 and t_claims.sum() <= 1),
                      "max_position_error_m": float(max(x[2] for x in support_data + test_data))}
            summaries.append(result)
            print(json.dumps(result), flush=True)
        if sha_file(state_path) != original_hash:
            raise AssertionError("Input state changed")
        write_json(out / "observations.json", rows)
        write_json(out / "summary.json", {"seeds": summaries, "state_file_unchanged": True,
                                            "elapsed_seconds": time.perf_counter() - start})
    finally:
        sim._renderer.close()


if __name__ == "__main__":
    main()
