"""D0b-F1b: isolated temporal Fovea-crop head, evaluated by whole positions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.pc_act18 import hex_sample
from pc_cvnn.act23_d0b_fovea_crop_head_audit import GRID, _mass_at, _score, _train, _truth


def _features(open_rgb, closed_rgb):
    # The temporal image is observable only after the agent's own pulse.  No simulator channel enters.
    delta = np.abs(open_rgb.astype(np.int16) - closed_rgb.astype(np.int16)).astype(np.uint8)
    rows = []
    for image in delta:
        per_pose = []
        for gaze in GRID:
            crop = hex_sample(image, gaze, 4.0)[:, :, 1:] / 255.0
            per_pose.append(crop.reshape(8, 2, 8, 2, 3).mean(axis=(1, 3)).reshape(-1))
        rows.append(per_pose)
    return np.asarray(rows)


def run(frames: Path, evaluation: Path, output: Path, seeds=(11, 17, 23)):
    data = np.load(frames); ids = data["pose_id"].astype(int); motion = data["motion_rgb_l1"]
    features = _features(data["open_rgb"], data["closed_rgb"])
    mass = np.asarray([[_mass_at(item, gaze) for gaze in GRID] for item in motion]); labels = (mass >= .10).astype(float)
    test = ids % 3 == 0; truth = _truth(evaluation); output.mkdir(parents=True, exist_ok=True); summaries=[]
    for seed in seeds:
        model = _train(features[~test].reshape(-1, features.shape[-1]), labels[~test].reshape(-1), seed)
        scores = _score(features.reshape(-1, features.shape[-1]), model).reshape(len(ids), len(GRID)); rows=[]; errors=[]
        for i,pid in enumerate(ids):
            if not test[i]: continue
            choice=int(np.argmax(scores[i])); expected=truth.get(int(pid)); selected=GRID[choice].tolist()
            error=None if expected is None else float(np.linalg.norm(np.subtract(selected,expected)))
            if error is not None: errors.append(error)
            rows.append({"schema":"act23-d0b-f1b-prediction-v1","seed":seed,"pose_id":int(pid),"selected_gaze_px":selected,"truth_claw_px":expected,"error_px":error,"scores":[float(x) for x in scores[i]]})
        with (output/f"predictions-seed{seed}.jsonl").open("w",encoding="utf-8") as h:
            for row in rows: h.write(json.dumps(row,sort_keys=True)+"\n")
        summaries.append({"seed":seed,"paired_test_poses":len(errors),"median_error_px":None if not errors else float(np.median(errors)),"within_24px":int(sum(e<=24 for e in errors))})
    passed=[x for x in summaries if x["median_error_px"] is not None and x["median_error_px"]<=24 and x["within_24px"]>=12]
    result={"schema":"act23-d0b-f1b-result-v1","train_poses":int((~test).sum()),"test_poses":int(test.sum()),"seeds":summaries,"contract_passes":len(passed),"contract_pass":len(passed)>=2,"frames":str(frames),"evaluation":str(evaluation)}
    (output/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return result


def main():
    p=argparse.ArgumentParser();p.add_argument("--frames",type=Path,required=True);p.add_argument("--evaluation",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.frames,a.evaluation,a.output),indent=2,sort_keys=True))
if __name__ == "__main__": main()
