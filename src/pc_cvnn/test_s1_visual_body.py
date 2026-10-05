"""Gradient, phase handling and serialization controls for isolated B1."""
import json
from pathlib import Path
import sys
import io

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.act23_s1_visual_body import VisualBody
from pc_cvnn.servo_latent import position_latent


def run():
    rng = np.random.default_rng(62)
    q = rng.uniform(-1, 1, (12, 5))
    q[:, 4] = .4  # both components of one joint are constant during training
    x = np.array([position_latent(row) for row in q])
    y = rng.normal(size=(12, 9))
    model = VisualBody(x, y)
    loss, grads = model.loss_grad(x, y)
    max_error = 0.
    for parameter, gradient in zip(model.params, grads):
        for flat_index in [0, parameter.size // 2, parameter.size - 1]:
            original = parameter.flat[flat_index]
            parameter.flat[flat_index] = original + 1e-6
            positive = model.loss_grad(x, y)[0]
            parameter.flat[flat_index] = original - 1e-6
            negative = model.loss_grad(x, y)[0]
            parameter.flat[flat_index] = original
            max_error = max(max_error, abs((positive - negative) / 2e-6 - gradient.flat[flat_index]))
    assert max_error < 1e-8
    assert not model.active[-2:].any()
    changed = q.copy(); changed[:, 4] = 1.2
    changed_x = np.array([position_latent(row) for row in changed])
    assert np.array_equal(model.predict(x), model.predict(changed_x)), 'Untrained columns leaked'
    model.fit(x, y, steps=100)
    final = model.loss_grad(x, y)[0]
    assert final < loss
    before = [p.copy() for p in model.params]
    checkpoint = io.BytesIO()
    model.save(checkpoint)
    checkpoint.seek(0)
    restored = VisualBody.load(checkpoint)
    assert np.array_equal(model.predict(x), restored.predict(x))
    assert all(np.array_equal(p, old) for p, old in zip(model.params, before))
    for bad in (np.zeros((1, 10)), np.full((1, 10), np.nan), np.ones((1, 5))):
        try:
            model.predict(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid phases accepted')
    return dict(gradient_max_error=max_error, initial_loss=loss, final_loss=final,
                checkpoint_replay_exact=True, constant_columns_ignored=True,
                inference_frozen=True, invalid_phases_rejected=True)


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
