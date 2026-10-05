"""Observe native ACT23 work poses with the unchanged physical-rig camera.

Frozen FSM diagnostic, not training or a new controller. Geometry is evaluator-only.
"""
import argparse
from collections import defaultdict
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    def scalar(item):
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f'Unsupported audit value: {type(item).__name__}')
    path.write_text(json.dumps(value, indent=2, default=scalar)+'\n', encoding='utf-8')


def run(source, output, *, seed=421, episodes=4, split=None):
    source, output = source.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source_hash = sha(source)
    copied = output/'state-input.pkl'
    shutil.copy2(source, copied)
    settings = dict(ACT23_STATE_PATH=str(copied), ACT23_NO_PERSIST='1', ACT23_D0_FREEZE='1',
                    ACT23_STATE_HEADLESS='1', ACT23_VIZ_HEADLESS='1', ACT23_AUTO_N=str(episodes),
                    ACT23_AUTO_CURIOUS='0', ACT23_AUTO_OBJ='', ACT23_CHOREO='fsm',
                    ACT23_SCENE_N='4', ACT23_SCENE_EVERY='1', ACT23_SEED=str(seed),
                    ACT23_RES='240', ACT23_WM_EVAL='0', ACT21_HEADLESS='1',
                    ACT23_D0_MANIFEST_DIR=str(output/'manifests'),
                    ACT23_D0_EPISODE_JSONL=str(output/'episodes.jsonl'),
                    ACT23_D0_CREDIT_JSONL=str(output/'credit.jsonl'))
    os.environ.update(settings)
    import mujoco
    import pc_cvnn.pc_act23 as act23  # ACT23 sets reach and DOF defaults BEFORE simulator import
    from pc_cvnn.act23_s1_transition_collector import OBS_LOW, OBS_HIGH, _q
    from pc_cvnn.arm_modules.d0_integrity import changed_components
    from pc_cvnn.act23_transition_recorder import TransitionRecorder, audit as audit_transitions
    recorder = None if split is None else TransitionRecorder(output, split)
    original = act23.act16.run_combined
    records, images, masks, scene_records = [], [], [], []
    episode_number = [0]

    def observed(sim, *args, **kwargs):
        episode = episode_number[0]
        episode_number[0] += 1
        command = kwargs.get('cmd_fixed')
        if callable(command):
            command = command(0)  # ACT23 supplies CommandState23.cmd_fn, not a body-name string.
        prior_hook = kwargs.get('macro_log_fn')
        phase_counts = defaultdict(int)
        current_phase = ['setup']
        claw_ids = [mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_GEOM, n)
                    for n in ('claw_left', 'claw_right')]
        camera_id = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_CAMERA, act23.CAM)
        camera_config = np.r_[sim.m.cam_pos[camera_id], sim.m.cam_quat[camera_id], sim.m.cam_fovy[camera_id]].copy()

        def capture(phase):
            q = _q(sim)
            before_qpos, before_time = sim.d.qpos.copy(), float(sim.d.time)
            rgb = sim.render(act23.CAM).copy()
            assert rgb.shape == (240,240,3)
            sim._renderer.enable_segmentation_rendering()
            try:
                seg = sim.render(act23.CAM)
            finally:
                sim._renderer.disable_segmentation_rendering()
            geom = seg[:,:,1] == mujoco.mjtObj.mjOBJ_GEOM
            claw = geom & np.isin(seg[:,:,0], claw_ids)
            assert np.array_equal(before_qpos, sim.d.qpos) and before_time == sim.d.time
            assert np.array_equal(rgb, sim.render(act23.CAM)), 'Evaluator altered subsequent RGB'
            assert np.array_equal(camera_config, np.r_[sim.m.cam_pos[camera_id], sim.m.cam_quat[camera_id], sim.m.cam_fovy[camera_id]])
            individual = [int((geom & (seg[:,:,0]==g)).sum()) for g in claw_ids]
            records.append(dict(sample_id=len(records), episode=episode, command=command, phase=phase,
                                time=before_time, q_rad=q.tolist(),
                                outside_s1_box=bool(np.any((q<OBS_LOW)|(q>OBS_HIGH))),
                                gripper_rad=float(sim.d.qpos[sim.jqadr['joint_5']]),
                                claw_pixels=int(claw.sum()), claw_pixels_each=individual))
            images.append(rgb); masks.append(claw)
            return seg

        seg = capture('before')
        objects = []
        for name in act23.act16.OBJS:
            bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, name)
            gids = np.flatnonzero(sim.m.geom_bodyid==bid)
            visible = (seg[:,:,1]==mujoco.mjtObj.mjOBJ_GEOM) & np.isin(seg[:,:,0], gids)
            objects.append(dict(name=name, xyz=sim.obj_pos(name).tolist(), visible_pixels=int(visible.sum())))
        scene_records.append(dict(episode=episode, command=command, objects=objects,
                                  camera_position=sim.m.cam_pos[camera_id].tolist(),
                                  camera_fovy=float(sim.m.cam_fovy[camera_id])))

        def hook(state, aim, j5, phase):
            current_phase[0] = phase
            if prior_hook is not None:
                prior_hook(state, aim, j5, phase)
            phase_counts[phase] += 1
            if phase_counts[phase] == 1 or phase_counts[phase] % 15 == 0:
                capture(phase)
        kwargs['macro_log_fn'] = hook
        native_step = sim.step
        if recorder is not None:
            def observed_step(n=1):
                return recorder.step(sim, native_step, n, episode, current_phase[0], act23.CAM)
            sim.step = observed_step
        try:
            result = original(sim, *args, **kwargs)
        finally:
            sim.step = native_step
        capture('after')
        scene_records[-1]['phase_steps'] = dict(phase_counts)
        scene_records[-1]['return'] = list(result)
        print(f'[WorkposeAudit] episode={episode} samples={len(records)}', flush=True)
        return result

    # Keep any diagnostics initially attached to the function. During execution, ACT16 writes
    # its function attributes onto this same wrapper via its module-global name.
    observed.__dict__.update(original.__dict__)
    act23.act16.run_combined = observed
    try:
        with (output/'act23.log').open('w', encoding='utf-8') as log:
            with redirect_stdout(log), redirect_stderr(log):
                act23.run_self_learning_steering(headless=True)
    finally:
        act23.act16.run_combined = original
        if recorder is not None:
            recorder.close()
        np.savez_compressed(output/'camera-observations.npz', rgb=np.asarray(images),
                            q_rad=np.asarray([r['q_rad'] for r in records]),
                            gripper_rad=np.asarray([r['gripper_rad'] for r in records]))
        np.savez_compressed(output/'claw-evaluation.npz', mask=np.asarray(masks))
        write_json(output/'observations.json', records)
        write_json(output/'scenes-evaluation.json', scene_records)
    before = json.loads((output/'manifests/before.json').read_text())
    after = json.loads((output/'manifests/after.json').read_text())
    changes = changed_components(before, after, learning_only=True)
    groups = {}
    for phase in sorted({r['phase'] for r in records}):
        rows = [r for r in records if r['phase']==phase]
        groups[phase] = dict(n=len(rows), any_claw_visible=sum(r['claw_pixels']>0 for r in rows),
                            both_claws_visible=sum(all(r['claw_pixels_each']) for r in rows),
                            median_claw_pixels=float(np.median([r['claw_pixels'] for r in rows])),
                            outside_s1_box=sum(r['outside_s1_box'] for r in rows))
    result = dict(episodes=episode_number[0], samples=len(records), phases=groups,
                  changed_learning_components=changes, settings=settings, source_state=str(source),
                  source_hash=source_hash, source_unchanged=sha(source)==source_hash,
                  copy_unchanged=sha(copied)==source_hash,
                  act23_source_sha256=sha(Path(act23.__file__)), camera='overview', resolution=[240,240])
    if recorder is not None:
        result['transitions'] = audit_transitions(output)
        result['transitions_sha256'] = sha(output/'transitions.jsonl')
        result['transition_camera_sha256'] = sha(output/'transition-camera.npz')
    write_json(output/'result.json', result)
    assert result['episodes']==episodes and not changes and result['source_unchanged'] and result['copy_unchanged']
    if recorder is not None:
        assert result['transitions']['passed'], 'Native transition integrity failed; retain all rows for audit'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=421)
    parser.add_argument('--episodes', type=int, default=4)
    parser.add_argument('--split', choices=('train','test'), help='Record native transitions for this whole-run split')
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error('episodes must be positive')
    run(args.state, args.output, seed=args.seed, episodes=args.episodes, split=args.split)
