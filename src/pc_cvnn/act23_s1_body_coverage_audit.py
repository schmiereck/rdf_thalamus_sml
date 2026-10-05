"""B1 coverage diagnosis only. Privileged masks never become training labels."""
from __future__ import annotations

import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.act23_s1_visual_body import load_samples, write_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    values = np.asarray(values, dtype=float)
    return dict(min=float(values.min()), median=float(np.median(values)),
                max=float(values.max()), mean=float(values.mean()))


def pose_coverage(training, testing, result):
    from scipy.spatial import ConvexHull
    from scipy.spatial.distance import cdist
    from scipy.stats import spearmanr
    from pc_cvnn.act23_s1_transition_collector import CTRL_LOW, CTRL_HIGH
    x = (training['q_rad'] - CTRL_LOW) / (CTRL_HIGH - CTRL_LOW)
    tx = (testing['q_rad'] - CTRL_LOW) / (CTRL_HIGH - CTRL_LOW)
    distances = cdist(tx, x)
    nearest = distances.min(axis=1)
    own = cdist(x, x)
    np.fill_diagonal(own, np.inf)
    hull = ConvexHull(x)
    inside = np.all(tx @ hull.equations[:, :-1].T + hull.equations[:, -1] <= 1e-10, axis=1)
    error = np.asarray(result['metrics']['model']['per_pose_mse'])
    baseline = np.asarray(result['metrics']['mean']['per_pose_mse'])
    order = np.argsort(nearest)
    groups = dict(near_half=order[:len(order)//2], far_half=order[len(order)//2:],
                  inside_hull=np.flatnonzero(inside), outside_hull=np.flatnonzero(~inside))
    grouped = {}
    for name, ids in groups.items():
        grouped[name] = dict(n=len(ids), model_mse=float(error[ids].mean()) if len(ids) else None,
                            ratio_mean=float(error[ids].mean()/baseline[ids].mean()) if len(ids) else None)
    return dict(train_nearest_other=stats(own.min(axis=1)), test_nearest_train=stats(nearest),
                test_outside_train_axis_box=int(np.any((tx<x.min(axis=0)) | (tx>x.max(axis=0)), axis=1).sum()),
                test_inside_train_convex_hull=int(inside.sum()),
                train_q_min=training['q_rad'].min(axis=0).tolist(), train_q_max=training['q_rad'].max(axis=0).tolist(),
                spearman_distance_error=float(spearmanr(nearest, error).statistic), groups=grouped,
                test_nearest_distances=nearest.tolist(), test_nearest_train_ids=distances.argmin(axis=1).tolist(),
                test_inside_hull=inside.tolist())


def project(points, position, rotation, fovy, size=96):
    camera = (np.asarray(points) - position) @ rotation.reshape(3, 3)
    depth = -camera[:, 2]
    focal = .5 * size / np.tan(np.deg2rad(fovy) / 2)
    uv = np.column_stack([size/2 + focal*camera[:, 0]/depth,
                          size/2 - focal*camera[:, 1]/depth])
    return uv, depth


def claw_projection(sim, geom_id, cam_id):
    corners = np.array(list(product((-1, 1), repeat=3))) * sim.m.geom_size[geom_id]
    points = corners @ sim.d.geom_xmat[geom_id].reshape(3, 3).T + sim.d.geom_xpos[geom_id]
    points = np.vstack([sim.d.geom_xpos[geom_id], points])
    uv, depth = project(points, sim.d.cam_xpos[cam_id], sim.d.cam_xmat[cam_id], sim.m.cam_fovy[cam_id])
    outside = bool(np.all(depth > 0) and (
        np.all(uv[1:, 0] < 0) or np.all(uv[1:, 0] >= 96) or
        np.all(uv[1:, 1] < 0) or np.all(uv[1:, 1] >= 96)))
    return dict(center_uv=uv[0].tolist(), center_depth=float(depth[0]),
                center_in_frame=bool(depth[0] > 0 and np.all((uv[0]>=0) & (uv[0]<96))),
                box_definitely_outside=outside)


def replay(data, output, name):
    import mujoco
    from pc_cvnn.act23_s1_transition_collector import BracketArmSim, HOME, _park_objects, _direct, _q, _qvel
    sim = BracketArmSim(render_wh=(96, 96))
    rows, arm_masks, claw_masks = [], [], []
    try:
        _park_objects(sim)
        base = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, 'base_link')
        arm_bodies = {base}
        for body in range(1, sim.m.nbody):
            if sim.m.body_parentid[body] in arm_bodies:
                arm_bodies.add(body)
        arm_geoms = np.flatnonzero(np.isin(sim.m.geom_bodyid, list(arm_bodies)))
        claws = [mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_GEOM, n)
                 for n in ('claw_left', 'claw_right')]
        cam = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_CAMERA, 'overview')
        assert base >= 0 and min(claws) >= 0 and cam >= 0
        assert all(sim.m.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX for g in claws)
        for i, command in enumerate(data['command_rad']):
            _direct(sim, command)
            sim.target('joint_5', HOME['joint_5'])
            sim.step(400)
            assert np.array_equal(_q(sim), data['q_rad'][i]), f'{name} {i}: q mismatch'
            assert np.array_equal(_qvel(sim), data['qvel_rad_s'][i]), f'{name} {i}: velocity mismatch'
            assert sim.d.time == data['sim_time'][i], f'{name} {i}: time mismatch'
            assert sim.d.qpos[sim.jqadr['joint_5']] == data['gripper'][i, 0]
            assert np.array_equal(sim.render('overview'), data['rgb'][i]), f'{name} {i}: RGB mismatch'
            sim._renderer.enable_segmentation_rendering()
            try:
                segmented = sim.render('overview')
            finally:
                sim._renderer.disable_segmentation_rendering()
            geom_pixel = segmented[:, :, 1] == mujoco.mjtObj.mjOBJ_GEOM
            arm = geom_pixel & np.isin(segmented[:, :, 0], arm_geoms)
            claw = geom_pixel & np.isin(segmented[:, :, 0], claws)
            assert np.all(~claw | arm), 'Claw is not a subset of arm'
            projections = [claw_projection(sim, g, cam) for g in claws]
            counts = [int((geom_pixel & (segmented[:, :, 0] == g)).sum()) for g in claws]
            # If an entire convex box projects outside the image, it cannot have visible pixels.
            for count, projected in zip(counts, projections):
                assert not (count and projected['box_definitely_outside']), 'Projection/renderer disagreement'
            pooled = claw.reshape(24, 4, 24, 4).mean(axis=(1, 3))
            row = dict(sample_id=i, arm_pixels=int(arm.sum()), claw_pixels=int(claw.sum()),
                       claw_pixels_each=counts, claw_equivalent_pixels_24=float(pooled.sum()),
                       claw_half_occupied_cells_24=int((pooled>=.5).sum()),
                       projections=projections)
            rows.append(row); arm_masks.append(arm); claw_masks.append(claw)
            if (i+1) % 32 == 0:
                print(f'{name}: {i+1}/{len(data["q_rad"])} exact replay', flush=True)
        np.savez_compressed(output / f'{name}-evaluation-masks.npz', arm=arm_masks, claw=claw_masks)
        write_json(output / f'{name}-evaluation.json', rows)
        return rows, np.asarray(arm_masks)
    finally:
        sim._renderer.close()


def summary(rows):
    return dict(n=len(rows), arm_visible=sum(r['arm_pixels']>0 for r in rows),
                claw_visible=sum(r['claw_pixels']>0 for r in rows),
                both_claws_visible=sum(all(r['claw_pixels_each']) for r in rows),
                both_claw_boxes_definitely_outside=sum(all(p['box_definitely_outside'] for p in r['projections']) for r in rows),
                any_claw_center_in_frame=sum(any(p['center_in_frame'] for p in r['projections']) for r in rows),
                arm_pixels=stats([r['arm_pixels'] for r in rows]),
                claw_pixels=stats([r['claw_pixels'] for r in rows]),
                claw_equivalent_pixels_24=stats([r['claw_equivalent_pixels_24'] for r in rows]),
                any_half_claw_cell_24=sum(r['claw_half_occupied_cells_24']>0 for r in rows))


def plot(root, output):
    """Scientific audit figure from saved observations/results; no model or simulator."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report = json.loads((output/'result.json').read_text())
    old = json.loads((root/'fit/result.json').read_text())
    with np.load(root/'test409/samples.npz', allow_pickle=False) as data:
        rgb = data['rgb'].copy()
    with np.load(output/'test409-evaluation-masks.npz', allow_pickle=False) as data:
        arm, claw = data['arm'].copy(), data['claw'].copy()
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for offset, split in [(0, 'train'), (.35, 'test')]:
        group = report[split]
        values = [group['claw_visible'], group['both_claws_visible'], group['both_claw_boxes_definitely_outside']]
        axes[0,0].bar(np.arange(3)+offset, np.array(values)/group['n']*100, width=.35, label=split)
    axes[0,0].set_xticks(np.arange(3)+.175, ['Any claw visible', 'Both visible', 'Both off-frame'])
    axes[0,0].set_ylabel('Poses (%)'); axes[0,0].set_ylim(0,100); axes[0,0].legend()
    axes[0,0].set_title('Original camera, 224 exactly replayed poses')
    distances = report['pose_coverage']['test_nearest_distances']
    inside = np.asarray(report['pose_coverage']['test_inside_hull'])
    errors = np.asarray(old['metrics']['model']['per_pose_mse'])
    for selection, label in [(inside, 'Inside train hull'), (~inside, 'Outside train hull')]:
        axes[0,1].scatter(np.asarray(distances)[selection], errors[selection], label=label, s=25)
    axes[0,1].set_xlabel('Nearest train pose, range-scaled joint distance')
    axes[0,1].set_ylabel('Frozen decoder test MSE'); axes[0,1].legend()
    axes[0,1].set_title('Descriptive diagnosis, no retraining')
    for ax, i in zip(axes[1], [0, 1]):
        ax.imshow(rgb[i])
        overlay = np.zeros((96,96,4))
        overlay[arm[i]] = [0,1,0,.25]
        overlay[claw[i]] = [1,0,0,.8]
        ax.imshow(overlay); ax.axis('off')
        ax.set_title(f'Test pose {i}: {claw[i].sum()} claw pixels\nGreen: arm incl. base; red: claw (evaluator only)')
    fig.tight_layout(); fig.savefig(output/'coverage.png', dpi=140); plt.close(fig)


def run(root, output):
    output.mkdir(parents=True, exist_ok=False)
    source_paths = [root/p for p in ['train401/samples.npz', 'test409/samples.npz', 'fit/model.npz',
                                    'fit/result.json', 'fit/predictions.npz']]
    before = {str(p): sha(p) for p in source_paths}
    a, _ = load_samples(root/'train401', 401, 160)
    b, _ = load_samples(root/'test409', 409, 64)
    result = json.loads((root/'fit/result.json').read_text())
    assert sha(root/'fit/model.npz') == result['model_sha256']
    coverage = pose_coverage(a, b, result)
    write_json(output/'pose-coverage.json', coverage)
    # Projection convention controls: identity camera looks along -Z, +Y goes up.
    uv, depth = project(np.array([[0,0,-1], [.5,0,-1], [0,.5,-1]]), np.zeros(3), np.eye(3), 90)
    assert np.allclose(uv, [[48,48], [72,48], [48,24]]) and np.all(depth==1)
    train_rows, train_masks = replay(a, output, 'train401')
    test_rows, _ = replay(b, output, 'test409')
    union = train_masks.any(axis=0).reshape(24,4,24,4).any(axis=(1,3))
    variance = a['target_rgb'].var(axis=0).sum(axis=2)
    report = dict(pose_coverage=coverage, train=summary(train_rows), test=summary(test_rows),
                  train_variance_fraction_in_ever_arm_cells=float(variance[union].sum()/variance.sum()),
                  original_rgb_and_encoders_exact=True, privileged_evaluator_only=True,
                  source_hashes=before, source_unchanged=all(sha(p)==before[str(p)] for p in source_paths))
    assert report['source_unchanged']
    write_json(output/'result.json', report)
    plot(root, output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('pose_coverage','source_hashes')}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
