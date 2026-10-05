"""Versioned six-servo sensor code for the ACT23 working range; no learned forecast."""
import numpy as np

JOINTS = tuple(f'joint_{i}' for i in range(6))
POSITION_SCHEMA = 'joint-phase-v2/6/ReIm-interleaved/rad/[-0.1,pi+0.1]'
LOW, HIGH = -.1, np.pi + .1  # Representation domain, NOT actuator safety limits.


def vector(value):
    q = np.asarray(value, dtype=float)
    if q.shape != (6,) or not np.isfinite(q).all():
        raise ValueError('Expected six finite measured servo values')
    return q


def encode(q):
    q = vector(q)
    if np.any((q < LOW) | (q > HIGH)):
        raise ValueError('Position outside declared v2 sensor domain; no clipping')
    return np.column_stack([np.cos(q), np.sin(q)]).reshape(12)


def decode(value):
    packed = np.asarray(value, dtype=float)
    if packed.shape != (12,) or not np.isfinite(packed).all():
        raise ValueError('Expected twelve finite interleaved components')
    z = packed[::2] + 1j * packed[1::2]
    if not np.allclose(abs(z), 1., rtol=0, atol=1e-10):
        raise ValueError('Expected unit position phases')
    # Branch centred on pi/2, safely away from both ends of the declared domain.
    q = np.angle(z * -1j) + np.pi/2
    if np.any((q < LOW-1e-12) | (q > HIGH+1e-12)):
        raise ValueError('Decoded phase outside v2 domain')
    return q
