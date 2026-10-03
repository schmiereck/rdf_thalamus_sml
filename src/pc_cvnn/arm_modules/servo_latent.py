"""Optional isolated module exposing measured and predicted servo latents.

Not wired into ACT23. Complex channels use explicit interleaved Re/Im because
base.Port stores real arrays. Positional coding is independent of the action.
"""
import numpy as np

from .base import ArmModule
from ..servo_latent import FrozenServoPredictor, POSITION_SCHEMA, JOINTS, HORIZON_SECONDS, position_latent, joint_vector


class ServoLatentModule(ArmModule):
    def __init__(self,checkpoint,name='ServoLatent'):
        super().__init__(name)
        self.predictor=FrozenServoPredictor(checkpoint)
        self.position_schema=POSITION_SCHEMA
        self.encoder_id=self.predictor.encoder_id
        self.model_id=self.predictor.model_id
        self.joints=JOINTS
        self.horizon_seconds=HORIZON_SECONDS
        for key in ('q_rad','qvel_rad_s','command_rad'):
            self.add_in(key,5)
        for key,dim in [('position_latent',10),('velocity_rad_s',5),
                        ('transition_latent',48),('predicted_position_latent',10),
                        ('predicted_q_rad',5)]:
            self.add_out(key,dim)

    def _publish(self,key,value,source):
        port=self.out_ports[key]
        same=(value is None and port.value is None) or (
            value is not None and port.value is not None and np.array_equal(value,port.value))
        if not same or port.src_seq!=source:
            port.set(value,src_seq=source)

    def step(self):
        keys=('q_rad','qvel_rad_s','command_rad')
        values=[self.get_in(key) for key in keys]
        self._publish('position_latent',None if values[0] is None else position_latent(values[0]),
                      self.in_ports['q_rad'].seq)
        self._publish('velocity_rad_s',None if values[1] is None else joint_vector(values[1]).copy(),
                      self.in_ports['qvel_rad_s'].seq)
        context_sources=tuple(self.in_ports[k].seq for k in keys)
        if any(value is None for value in values):
            # Explicit invalidation instead of publishing stale values as a fresh observation.
            for key in ('transition_latent','predicted_position_latent','predicted_q_rad'):
                self._publish(key,None,context_sources)
            return
        result=self.predictor.infer(*values)
        for key in self.out_ports:
            if key in ('position_latent','velocity_rad_s'):
                continue
            self._publish(key,result[key],context_sources)
