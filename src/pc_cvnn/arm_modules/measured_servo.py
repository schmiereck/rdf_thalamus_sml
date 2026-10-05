"""Optional measured six-servo port; deliberately no unvalidated S1 prediction."""
import numpy as np
from .base import ArmModule
from ..measured_servo import JOINTS, POSITION_SCHEMA, encode, vector


class MeasuredServoModule(ArmModule):
    def __init__(self, name='MeasuredServo'):
        super().__init__(name)
        self.joints, self.position_schema = JOINTS, POSITION_SCHEMA
        self.add_in('q_rad', 6); self.add_in('qvel_rad_s', 6)
        self.add_out('position_latent', 12); self.add_out('velocity_rad_s', 6)

    def step(self):
        # Validate all present inputs before publishing a partial observation.
        q, v = self.get_in('q_rad'), self.get_in('qvel_rad_s')
        values = [None if q is None else encode(q), None if v is None else vector(v).copy()]
        for key, source, value in zip(('position_latent','velocity_rad_s'), ('q_rad','qvel_rad_s'), values):
            port, seq = self.out_ports[key], self.in_ports[source].seq
            same = ((value is None and port.value is None) or
                    (value is not None and port.value is not None and np.array_equal(value, port.value)))
            if not same or port.src_seq != seq:
                port.set(value, src_seq=seq)
