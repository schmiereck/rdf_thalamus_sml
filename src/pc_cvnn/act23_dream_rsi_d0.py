"""D0: headless learning/frozen comparison on held-out views of the Y shape.

Protocol: wiki/messungen/dream-rsi-d0-pilot.md. This measures open-set memory
learning, not arm learning or a Dream-RSI scheduler. Never writes the input state.
Each output directory is immutable; use a new directory for another invocation.
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


def sha_object(value):
    return hashlib.sha256(pickle.dumps(value, protocol=5)).hexdigest()


def write_json(path, value):
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true", help="Seed 1700 only; technical check")
    parser.add_argument("--fresh-shape", action="store_true", help="Separate v2: bootstrap cube/L/U from scratch")
    args = parser.parse_args()
    state_path = args.state.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ["MPLCONFIGDIR"] = str(out / "mpl")
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    # The process has a fixed protocol; inherited experimental switches would confound it.
    inherited = {k: v for k, v in os.environ.items() if k.startswith("ACT")}
    for key in inherited:
        del os.environ[key]
    os.environ["ACT14_DOF"] = "4"
    os.environ["ACT14_HEADLESS"] = "1"
    os.environ["MPLBACKEND"] = "Agg"

    import mujoco
    import numpy as np
    import scipy
    from scipy.stats import fisher_exact
    from pc_cvnn.pc_act14 import BracketArmSim
    from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule

    started = time.perf_counter()
    original_hash = sha_file(state_path)
    with open(state_path, "rb") as stream:
        state = pickle.load(stream)
    if state.get("schema") != 2 or state.get("dof") != 4:
        raise ValueError("D0 protocol requires schema=2 and dof=4")
    shape = state["shape_clf"]
    if "obj_Y" in state.get("shape_key", {}):
        raise ValueError("Y is already bound in the start state")
    weights = lambda sc: sha_object((sc.W1, sc.b1, sc.W2, sc.b2, sc.head,
                                     sc.fmu, sc.fsd, sc._ZX))
    known = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]
    expected = dict(zip(known[:5], ["cube", "cube", "cube", "L", "U"]))
    expected.update(state["shape_key"])
    if args.fresh_shape:
        expected.update({"obj_T": None, "obj_X": None})  # unknown negative controls, not trained classes
    maintenance_bodies = known[:5] if args.fresh_shape else known
    train_colors = [[0.9, 0.1, 0.1, 1.0], [0.1, 0.8, 0.2, 1.0], [0.85, 0.1, 0.45, 1.0]]
    test_colors = [[0.1, 0.8, 0.85, 1.0], [0.45, 0.12, 0.9, 1.0], [0.95, 0.55, 0.1, 1.0]]
    seeds = [1700] if args.smoke else [1701, 1702]
    n_train, n_y, n_known = (3, 6, 1) if args.smoke else (24, 24, 4)
    checkpoints = [0, 3] if args.smoke else [0, 3, 6, 12, 24]
    manifest = {
        "protocol": "d0-shape-v2-fresh" if args.fresh_shape else "d0-shape-v1",
        "scope": "component-testbed", "smoke": args.smoke, "fresh_shape": args.fresh_shape,
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "script_sha256": sha_file(__file__), "state_sha256": original_hash,
        "protocol_sha256": sha_file(ROOT / "wiki/messungen/dream-rsi-d0-pilot.md"),
        "state_path": str(state_path), "schema": state["schema"], "dof": state["dof"],
        "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__, "mujoco": mujoco.__version__,
        "threads": 1, "seeds": seeds, "train_y_views": n_train, "test_y_views": n_y,
        "test_views_per_known_body": n_known, "checkpoints": checkpoints,
        "ignored_inherited_switches": inherited, "shape_engine": shape.engine,
        "start_open_names": shape.open_names, "start_shape_key": state.get("shape_key"),
        "source_hashes": {str(p.relative_to(ROOT)): sha_file(p) for p in [
            ROOT / "src/pc_cvnn/assets/bracket_arm.xml", ROOT / "src/pc_cvnn/pc_act14.py",
            ROOT / "src/pc_cvnn/pc_act23.py", ROOT / "src/pc_cvnn/arm_modules/shape_classifier.py"]},
    }
    write_json(out / "manifest.json", manifest)
    (out / "runner.py").write_bytes(Path(__file__).read_bytes())
    (out / "protocol.md").write_bytes((ROOT / "wiki/messungen/dream-rsi-d0-pilot.md").read_bytes())
    sim = BracketArmSim(render_wh=(240, 240))
    sim.set_reach_site("contact")
    original_rgba = sim.m.geom_rgba.copy()
    try:
        if shape.needs_recal(sim):
            raise ValueError("Start state calibration does not match 240px; do not silently retrain")
        free_bodies = []
        for body in range(sim.m.nbody):
            if sim.m.body_jntnum[body] and sim.m.jnt_type[sim.m.body_jntadr[body]] == mujoco.mjtJoint.mjJNT_FREE:
                free_bodies.append(mujoco.mj_id2name(sim.m, mujoco.mjtObj.mjOBJ_BODY, body))

        def set_scene(scene):
            sim.reset_home()
            for i, body in enumerate(free_bodies):
                sim.set_object(body, [0.5 + 0.07 * i, -0.6], z=0.012)
            body = scene["body"]
            sim.set_object(body, scene["xy"], z=0.012, yaw=scene["yaw"])
            bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
            start = sim.m.body_geomadr[bid]
            sim.m.geom_rgba[start:start + sim.m.body_geomnum[bid]] = scene["rgba"]
            mujoco.mj_forward(sim.m, sim.d)

        def perceive(sc):
            saved = sim.d.mocap_pos.copy()
            try:
                return sc.perceive_all(sim)
            finally:
                sim.d.mocap_pos[:] = saved
                mujoco.mj_forward(sim.m, sim.d)

        def sample_scene(rng, body, colors, train, scene_id):
            return {"id": scene_id, "body": body,
                    "xy": [float(rng.uniform(-0.05, 0.05) if train else rng.uniform(-0.09, 0.09)),
                           float(rng.uniform(0.14, 0.19) if train else rng.uniform(0.12, 0.21))],
                    "yaw": float(rng.uniform(0, 2 * np.pi)),
                    "rgba": colors[int(rng.integers(len(colors)))]}

        summaries = []
        with open(out / "observations.jsonl", "x", encoding="utf-8") as events:
            def event(row):
                events.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                events.flush()

            for seed in seeds:
                if args.fresh_shape:
                    bootstrap_start = time.perf_counter()
                    print(f"bootstrap seed={seed}: 2500 labelled base-shape views", flush=True)
                    sim.m.geom_rgba[:] = original_rgba
                    shape = ShapeClassifierModule(rng=np.random.default_rng(seed + 200000))
                    accuracy = shape.train(sim, steps=2500, rng=shape.rng)
                    with open(out / f"bootstrap-{seed}.pkl", "xb") as stream:
                        pickle.dump(shape, stream, protocol=5)
                    event({"kind": "bootstrap", "seed": seed, "labelled_samples": len(shape._ZX),
                           "training_accuracy": float(accuracy), "novel_th": float(shape.novel_th),
                           "elapsed_seconds": time.perf_counter() - bootstrap_start,
                           "state_hash": sha_object(shape), "open_names": list(shape.open_names)})
                    print(f"bootstrap seed={seed}: done, accuracy={accuracy:.3f}, novel_th={shape.novel_th:.3f}", flush=True)
                train_rng = np.random.default_rng(seed)
                test_rng = np.random.default_rng(seed + 100000)
                train = []
                for step in range(1, n_train + 1):
                    train.append(sample_scene(train_rng, "obj_Y", train_colors, True, f"train-y-{step}"))
                    if step % 3 == 0:
                        train.append(sample_scene(train_rng, maintenance_bodies[(step // 3 - 1) % len(maintenance_bodies)],
                                                  train_colors, True, f"train-maintenance-{step}"))
                tests = [sample_scene(test_rng, "obj_Y", test_colors, False, f"test-y-{i}") for i in range(n_y)]
                tests += [sample_scene(test_rng, b, test_colors, False, f"test-{b}-{i}")
                          for b in known for i in range(n_known)]
                write_json(out / f"scenes-{seed}.json", {"train": train, "evaluation": tests})
                frozen = copy.deepcopy(shape)
                learning = copy.deepcopy(shape)
                frozen_hash, start_weights = sha_object(frozen), weights(frozen)
                anchor = None
                seen_y = 0
                start_names = set(shape.open_names)
                baseline_predictions = {}

                def evaluate(sc, arm, step):
                    before = sha_object(sc)
                    # Inference caches and readout counters cannot contaminate the training object.
                    readout = copy.deepcopy(sc)
                    counts = {"y_hits": 0, "y_n": n_y, "y_initially_novel": 0,
                              "false_y_claims": 0, "known_correct": 0, "known_n": len(known) * n_known,
                              "known_changed": 0, "missing": 0}
                    for scene in tests:
                        set_scene(scene)
                        detections = perceive(readout)
                        located = [(d, float(np.linalg.norm(np.asarray(d["pos"]) - scene["xy"])))
                                   for d in detections if d.get("pos") is not None]
                        det, distance = min(located, key=lambda pair: pair[1]) if located else (None, None)
                        valid = det is not None and distance <= 0.020
                        prediction = det.get("shape") if valid else None
                        if not valid:
                            counts["missing"] += 1
                        if scene["body"] == "obj_Y":
                            counts["y_hits"] += int(valid and anchor is not None and prediction == anchor)
                            counts["y_initially_novel"] += int(valid and prediction is None)
                        else:
                            counts["false_y_claims"] += int(valid and anchor is not None and prediction == anchor)
                            counts["known_correct"] += int(valid and prediction == expected[scene["body"]])
                            if arm == "frozen" and step == 0:
                                baseline_predictions[scene["id"]] = prediction
                            counts["known_changed"] += int(prediction != baseline_predictions[scene["id"]])
                        event({"kind": "evaluation", "seed": seed, "arm": arm, "y_views": step,
                               "scene": scene["id"], "body": scene["body"], "prediction": prediction,
                               "expected_control_class": expected.get(scene["body"]),
                               "anchor": anchor, "located": valid, "distance_m": distance,
                               "detection_count": len(detections)})
                    if sha_object(sc) != before:
                        raise AssertionError("Evaluation changed training state")
                    result = {"seed": seed, "arm": arm, "y_views": step, "anchor": anchor, **counts,
                              "open_names": list(sc.open_names), "state_hash": before,
                              "weights_unchanged": weights(sc) == start_weights}
                    summaries.append(result)
                    print(json.dumps({k: result[k] for k in ("seed", "arm", "y_views", "anchor", "y_hits",
                                                           "false_y_claims", "known_correct", "missing")}), flush=True)

                evaluate(frozen, "frozen", 0)
                evaluate(learning, "learning", 0)
                for idx, scene in enumerate(train):
                    set_scene(scene)
                    saved = sim.d.mocap_pos.copy()
                    try:
                        born = learning.observe_scene(sim)
                    finally:
                        sim.d.mocap_pos[:] = saved
                        mujoco.mj_forward(sim.m, sim.d)
                    if scene["body"] == "obj_Y":
                        seen_y += 1
                        if anchor is None:
                            anchor = next((name for name in born if name not in start_names), None)
                    event({"kind": "training", "seed": seed, "scene": scene["id"], "body": scene["body"],
                           "y_views": seen_y, "born": born, "anchor": anchor,
                           "events": getattr(learning, "last_events", []),
                           "open_counts": {name: len(ex) for name, ex in learning.open.items()}})
                    # Evaluate after maintenance, so all checkpoints include the same protocol.
                    end_block = idx + 1 == len(train) or train[idx + 1]["body"] == "obj_Y"
                    if seen_y in checkpoints and end_block:
                        evaluate(frozen, "frozen", seen_y)
                        evaluate(learning, "learning", seen_y)
                if sha_object(frozen) != frozen_hash:
                    raise AssertionError("Frozen control changed")
                event({"kind": "integrity", "seed": seed, "frozen_unchanged": True,
                       "learning_state_changed": sha_object(learning) != frozen_hash,
                       "neural_weights_unchanged": weights(learning) == start_weights})

        endpoints = []
        for seed in seeds:
            before = next(r for r in summaries if r["seed"] == seed and r["arm"] == "learning" and r["y_views"] == 0)
            end = next(r for r in summaries if r["seed"] == seed and r["arm"] == "learning" and r["y_views"] == n_train)
            control = next(r for r in summaries if r["seed"] == seed and r["arm"] == "frozen" and r["y_views"] == n_train)
            table = [[end["y_hits"], n_y - end["y_hits"]], [control["y_hits"], n_y - control["y_hits"]]]
            passed = (end["y_hits"] / n_y >= 0.5 and (end["y_hits"] - control["y_hits"]) / n_y >= 0.2
                      and end["false_y_claims"] <= 1 and end["known_correct"] >= before["known_correct"] - 1)
            endpoints.append({"seed": seed, "screening_pass": passed,
                              "fisher_p_descriptive_only": float(fisher_exact(table).pvalue),
                              "learning": end, "frozen": control})
        if sha_file(state_path) != original_hash:
            raise AssertionError("Input state file changed")
        result = {"scope": "component-testbed", "smoke": args.smoke, "checkpoints": summaries,
                  "endpoints": endpoints, "state_file_unchanged": True,
                  "elapsed_seconds": time.perf_counter() - started}
        write_json(out / "summary.json", result)
        print(json.dumps({"completed": True, "out": str(out), "elapsed_seconds": result["elapsed_seconds"],
                          "screening_pass": [r["screening_pass"] for r in endpoints]}), flush=True)
    finally:
        sim._renderer.close()


if __name__ == "__main__":
    main()
