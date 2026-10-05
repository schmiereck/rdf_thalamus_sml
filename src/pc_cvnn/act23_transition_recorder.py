"""Passive encoder/command transitions around native ACT23 sim.step calls.

Does not drive the robot or query pressure, contacts, object poses or FK.
"""
import json
import numpy as np
from .measured_servo import JOINTS, POSITION_SCHEMA, LOW, HIGH, encode, decode


class TransitionRecorder:
    def __init__(self, output, split):
        if split not in ('train', 'test'):
            raise ValueError('Explicit whole-run train/test split required')
        self.output, self.split = output, split
        self.handle = (output/'transitions.jsonl').open('x', encoding='utf-8')
        self.count = 0
        self.images, self.image_rows, self.image_side = [], [], []

    @staticmethod
    def sensors(sim):
        q = np.array([sim.d.qpos[sim.jqadr[j]] for j in JOINTS])
        v = np.array([sim.d.qvel[sim.m.jnt_dofadr[sim._jid(j)]] for j in JOINTS])
        ctrl = np.array([sim.d.ctrl[sim.act[j]] for j in JOINTS])
        return q, v, ctrl

    def step(self, sim, original, n, episode, phase, camera):
        q, v, ctrl = self.sensors(sim)
        timestamp = float(sim.d.time)
        photograph = self.count % 25 == 0
        if photograph:
            self.images.append(sim.render(camera).copy())
            self.image_rows.append(self.count); self.image_side.append(0)
        returned = original(n)  # exactly the original n; no resampling of the physics
        nq, nv, next_ctrl = self.sensors(sim)
        end = float(sim.d.time)
        assert np.array_equal(ctrl, next_ctrl), 'Control changed inside constant-command interval'
        assert np.isclose(end-timestamp, int(n)*sim.m.opt.timestep, rtol=0, atol=1e-9)
        valid = bool(all(np.isfinite(a).all() for a in (q,v,ctrl,nq,nv)) and
                     np.all((q>=LOW)&(q<=HIGH)) and np.all((nq>=LOW)&(nq<=HIGH)))
        latent, next_latent = (encode(q), encode(nq)) if valid else (None, None)
        if valid:
            assert np.max(np.abs(decode(latent)-q)) < 1e-12
            assert np.max(np.abs(decode(next_latent)-nq)) < 1e-12
        row = dict(schema='act23-native-transition-v1', position_schema=POSITION_SCHEMA,
                   row_id=self.count, episode=episode, phase=phase, split=self.split,
                   time=timestamp, next_time=end, physics_steps=int(n), timestep_seconds=float(sim.m.opt.timestep),
                   q_rad=q.tolist(), qvel_rad_s=v.tolist(), command_rad=ctrl.tolist(),
                   q_next_rad=nq.tolist(), qvel_next_rad_s=nv.tolist(), position_valid=valid,
                   position_latent=None if latent is None else latent.tolist(),
                   next_position_latent=None if next_latent is None else next_latent.tolist(),
                   has_camera_pair=photograph)
        self.handle.write(json.dumps(row, allow_nan=False)+'\n')
        self.handle.flush()
        if photograph:
            self.images.append(sim.render(camera).copy())
            self.image_rows.append(self.count); self.image_side.append(1)
        self.count += 1
        return returned

    def close(self):
        self.handle.close()
        np.savez_compressed(self.output/'transition-camera.npz', rgb=np.asarray(self.images),
                            row_id=self.image_rows, side=self.image_side)


def audit(output):
    rows = [json.loads(line) for line in (output/'transitions.jsonl').read_text().splitlines()]
    if not rows:
        raise ValueError('No native transitions recorded')
    discontinuities = []
    for i, row in enumerate(rows):
        assert row['row_id']==i and len(row['q_rad'])==6
        assert abs(row['next_time']-row['time']-row['physics_steps']*row['timestep_seconds'])<1e-9
        if row['position_valid']:
            assert np.max(np.abs(decode(row['position_latent'])-row['q_rad']))<1e-12
            assert np.max(np.abs(decode(row['next_position_latent'])-row['q_next_rad']))<1e-12
        if i and row['episode']==rows[i-1]['episode']:
            prev = rows[i-1]
            if (row['time']!=prev['next_time'] or row['q_rad']!=prev['q_next_rad'] or
                    row['qvel_rad_s']!=prev['qvel_next_rad_s']):
                discontinuities.append(i)  # Do not invent a cross-reset transition.
    with np.load(output/'transition-camera.npz', allow_pickle=False) as saved:
        pairs = sum(row['has_camera_pair'] for row in rows)
        assert saved['rgb'].shape==(2*pairs,240,240,3)
        assert np.array_equal(saved['row_id'], np.repeat([r['row_id'] for r in rows if r['has_camera_pair']],2))
        assert np.array_equal(saved['side'], np.tile([0,1], pairs))
    counts, baseline = {}, {}
    for n in sorted({r['physics_steps'] for r in rows}):
        selected = [r for r in rows if r['physics_steps']==n]
        delta = np.array([np.array(r['q_next_rad'])-r['q_rad'] for r in selected])
        counts[str(n)] = len(selected)
        baseline[str(n)] = np.mean(delta**2,axis=0).tolist()
    return dict(rows=len(rows), episodes=sorted({r['episode'] for r in rows}),
                split=sorted({r['split'] for r in rows}), physics_step_counts=counts,
                persistence_mse_by_steps_and_joint=baseline, camera_pairs=pairs,
                invalid_positions=sum(not r['position_valid'] for r in rows),
                discontinuities=discontinuities, position_schema=POSITION_SCHEMA,
                passed=not discontinuities and all(r['position_valid'] for r in rows))
