"""Isolated B1: learn an observed camera view directly from measured joint phases.

No FK, IK, hand labels, pressure, PC-state PKLs, or production integration.
See wiki/messungen/s1-visuelles-koerpermodell.md for the fixed preregistration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.servo_latent import POSITION_SCHEMA, position_latent


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def collect(output, seed, count):
    from pc_cvnn.act23_s1_transition_collector import (
        BracketArmSim, HOME, CTRL_LOW, CTRL_HIGH, OBS_LOW, OBS_HIGH,
        _direct, _park_objects, _q, _qvel,
    )
    output.mkdir(parents=True, exist_ok=False)
    sim = BracketArmSim(render_wh=(96, 96))
    rng = np.random.default_rng(seed)
    images, positions, velocities, phases, grip, times, commands = [], [], [], [], [], [], []
    try:
        _park_objects(sim)
        for sample_id in range(count):
            command = rng.uniform(CTRL_LOW, CTRL_HIGH)
            _direct(sim, command)
            sim.target('joint_5', HOME['joint_5'])
            sim.step(400)
            timestamp = float(sim.d.time)
            q, qvel = _q(sim), _qvel(sim)
            frame = sim.render('overview').copy()
            assert sim.d.time == timestamp, 'Camera/encoder pairing advanced physics'
            positions.append(q); velocities.append(qvel); phases.append(position_latent(q))
            images.append(frame); times.append(timestamp); commands.append(command)
            grip.append([sim.d.qpos[sim.jqadr['joint_5']],
                         sim.d.qvel[sim.m.jnt_dofadr[sim._jid('joint_5')]]])
            if (sample_id + 1) % 32 == 0:
                print(f'collected seed={seed} {sample_id + 1}/{count}', flush=True)
    finally:
        sim._renderer.close()
    positions, velocities = np.asarray(positions), np.asarray(velocities)
    images = np.asarray(images, dtype=np.uint8)
    target = images.astype(float).reshape(count, 24, 4, 24, 4, 3).mean(axis=(2, 4)) / 255.
    np.savez_compressed(output / 'samples.npz', position_latent=phases, q_rad=positions,
                        qvel_rad_s=velocities, gripper=grip, sim_time=times, command_rad=commands,
                        sample_id=np.arange(count), rgb=images, target_rgb=target)
    finite = bool(np.isfinite(positions).all() and np.isfinite(velocities).all()
                  and np.isfinite(grip).all())
    violations = np.any((positions < OBS_LOW) | (positions > OBS_HIGH), axis=1)
    speed = float(np.max(np.abs(velocities)))
    manifest = dict(schema='s1-visual-body-v1', position_schema=POSITION_SCHEMA, seed=seed,
                    samples=count, camera='overview', image_size=[96, 96], target_size=[24, 24],
                    settle_steps=400, timestep_seconds=float(sim.m.opt.timestep),
                    max_arm_speed_rad_s=speed, bounds_violation_samples=int(violations.sum()),
                    finite=finite, collection_pass=finite and speed <= .05 and not violations.any(),
                    samples_sha256=hashlib.sha256((output / 'samples.npz').read_bytes()).hexdigest(),
                    pressure_used=False, hand_position_labels=False, teacher_ik_used=False)
    manifest['collection_pass'] = bool(manifest['collection_pass'])
    write_json(output / 'manifest.json', manifest)
    return manifest


def phase_array(value):
    x = np.asarray(value, dtype=float)
    if x.ndim != 2 or x.shape[1] != 10 or not np.isfinite(x).all():
        raise ValueError('Expected finite N x 10 position phases')
    if not np.allclose(x[:, 0::2] ** 2 + x[:, 1::2] ** 2, 1., atol=1e-10, rtol=0):
        raise ValueError('Expected unit position phases')
    return x


class VisualBody:
    """Camera decoder consuming position_latent directly; no angle reconstruction."""
    def __init__(self, x, y, seed=17):
        x = phase_array(x)
        y = np.asarray(y, dtype=float)
        if y.ndim != 2 or len(y) != len(x) or not np.isfinite(y).all():
            raise ValueError('Expected aligned finite image targets')
        self.mean = x.mean(axis=0)
        std = x.std(axis=0)
        self.active = std > 1e-8
        self.scale = np.where(self.active, np.maximum(std, 1e-3), 1.)
        self.target_mean = y.mean(axis=0)
        rng = np.random.default_rng(seed)
        self.params = [rng.normal(0, 1 / np.sqrt(10), (10, 64)), np.zeros(64),
                       rng.normal(0, .01, (64, y.shape[1])), np.zeros(y.shape[1])]

    def features(self, x):
        return (phase_array(x) - self.mean) / self.scale * self.active

    def predict(self, x):
        w1, b1, w2, b2 = self.params
        return np.tanh(self.features(x) @ w1 + b1) @ w2 + b2 + self.target_mean

    def loss_grad(self, x, y):
        v = self.features(x)
        w1, b1, w2, b2 = self.params
        hidden = np.tanh(v @ w1 + b1)
        error = hidden @ w2 + b2 + self.target_mean - y
        grad_output = 2 * error / error.size
        grad_hidden = (grad_output @ w2.T) * (1 - hidden ** 2)
        return float(np.mean(error ** 2)), [v.T @ grad_hidden, grad_hidden.sum(axis=0),
                                             hidden.T @ grad_output, grad_output.sum(axis=0)]

    def fit(self, x, y, steps=400, rate=.003):
        first = [np.zeros_like(p) for p in self.params]
        second = [np.zeros_like(p) for p in self.params]
        history = []
        for step in range(1, steps + 1):
            loss, grads = self.loss_grad(x, y)
            if not np.isfinite(loss) or not all(np.isfinite(g).all() for g in grads):
                raise FloatingPointError('Nonfinite training')
            for p, g, m, v in zip(self.params, grads, first, second):
                m *= .9; m += .1 * g
                v *= .999; v += .001 * g ** 2
                p -= rate * (m / (1 - .9 ** step)) / (np.sqrt(v / (1 - .999 ** step)) + 1e-8)
            if step == 1 or step % 100 == 0:
                history.append(dict(step=step, preupdate_mse=loss))
        return history

    def save(self, path):
        np.savez_compressed(path, mean=self.mean, scale=self.scale, active=self.active,
                            target_mean=self.target_mean, position_schema=POSITION_SCHEMA,
                            **{f'p{i}': p for i, p in enumerate(self.params)})

    @classmethod
    def load(cls, path):
        model = cls.__new__(cls)
        with np.load(path, allow_pickle=False) as saved:
            if str(saved['position_schema']) != POSITION_SCHEMA:
                raise ValueError('Incompatible position schema')
            for name in ('mean', 'scale', 'active', 'target_mean'):
                setattr(model, name, saved[name].copy())
            model.params = [saved[f'p{i}'].copy() for i in range(4)]
        arrays = [model.mean, model.scale, model.target_mean, *model.params]
        if not all(np.isfinite(a).all() for a in arrays) or np.any(model.scale <= 0):
            raise ValueError('Invalid saved model')
        return model


def load_samples(path, seed, count):
    meta = json.loads((path / 'manifest.json').read_text(encoding='utf-8'))
    assert meta['seed'] == seed and meta['samples'] == count and meta['collection_pass']
    assert meta['position_schema'] == POSITION_SCHEMA
    assert meta['samples_sha256'] == hashlib.sha256((path / 'samples.npz').read_bytes()).hexdigest()
    with np.load(path / 'samples.npz', allow_pickle=False) as data:
        arrays = {k: data[k].copy() for k in data.files}
    assert np.array_equal(arrays['sample_id'], np.arange(count))
    assert np.all(np.diff(arrays['sim_time']) > 0)
    assert np.allclose(arrays['position_latent'], [position_latent(q) for q in arrays['q_rad']],
                       rtol=0, atol=1e-12)
    target = arrays['rgb'].astype(float).reshape(count, 24, 4, 24, 4, 3).mean(axis=(2, 4)) / 255.
    assert np.array_equal(arrays['target_rgb'], target)
    return arrays, meta


def train(output, train_path, test_path):
    output.mkdir(parents=True, exist_ok=False)
    training, train_meta = load_samples(train_path, 401, 160)
    testing, test_meta = load_samples(test_path, 409, 64)
    grip_span = float(np.ptp(np.concatenate([training['gripper'][:, 0], testing['gripper'][:, 0]])))
    if grip_span > .01:
        raise ValueError(f'Unmodelled gripper variation: {grip_span}')
    x, y = training['position_latent'], training['target_rgb'].reshape(160, -1)
    tx, ty = testing['position_latent'], testing['target_rgb'].reshape(64, -1)
    variable = y.reshape(160, 24, 24, 3).var(axis=0).mean(axis=2) > 1e-4
    if variable.sum() < 16:
        raise ValueError('Insufficient camera variation; no model training')
    mask = np.repeat(variable.reshape(-1), 3)
    model = VisualBody(x, y)
    history = model.fit(x, y)
    model.save(output / 'model.npz')
    restored = VisualBody.load(output / 'model.npz')
    if not np.array_equal(model.predict(tx), restored.predict(tx)):
        raise AssertionError('Checkpoint replay changed predictions')
    shuffled_y = y[np.random.default_rng(918).permutation(len(y))]
    control = VisualBody(x, shuffled_y)
    control_history = control.fit(x, shuffled_y)
    control.save(output / 'shuffled-model.npz')
    predictions = dict(model=model.predict(tx), mean=np.broadcast_to(y.mean(axis=0), ty.shape),
                       shuffled=control.predict(tx))
    metrics = {}
    for name, prediction in predictions.items():
        squared = (prediction - ty) ** 2
        metrics[name] = dict(mse=float(squared.mean()), variable_mse=float(squared[:, mask].mean()),
                             per_pose_mse=squared.mean(axis=1).tolist(),
                             per_pose_variable_mse=squared[:, mask].mean(axis=1).tolist())
    ratio = metrics['model']['mse'] / metrics['mean']['mse']
    variable_ratio = metrics['model']['variable_mse'] / metrics['mean']['variable_mse']
    shuffle_ratio = metrics['model']['variable_mse'] / metrics['shuffled']['variable_mse']
    np.savez_compressed(output / 'predictions.npz', **predictions, target=ty, variable_mask=variable)
    result = dict(schema='s1-visual-body-result-v1', train_manifest=train_meta, test_manifest=test_meta,
                  variable_pixels=int(variable.sum()), gripper_span_rad=grip_span,
                  history=history, shuffled_history=control_history, metrics=metrics,
                  ratio_mean=ratio, variable_ratio_mean=variable_ratio, variable_ratio_shuffled=shuffle_ratio,
                  gate_pass=bool(ratio <= .9 and variable_ratio <= .9 and shuffle_ratio <= .9),
                  model_sha256=hashlib.sha256((output / 'model.npz').read_bytes()).hexdigest())
    write_json(output / 'result.json', result)
    return {k: v for k, v in result.items() if k not in ('metrics', 'train_manifest', 'test_manifest')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    collection = sub.add_parser('collect')
    collection.add_argument('--output', type=Path, required=True)
    collection.add_argument('--seed', type=int, required=True)
    collection.add_argument('--count', type=int, required=True)
    learning = sub.add_parser('train')
    learning.add_argument('--output', type=Path, required=True)
    learning.add_argument('--train-data', type=Path, required=True)
    learning.add_argument('--test-data', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'collect':
        if args.count < 2:
            parser.error('count >= 2 required')
        result = collect(args.output, args.seed, args.count)
    else:
        result = train(args.output, args.train_data, args.test_data)
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
