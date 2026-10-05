"""Port contract, reversible coding, frozen inference and action-separation checks."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pc_cvnn.servo_latent import FrozenServoPredictor, position_latent, position_from_latent, pack_complex, unpack_complex
from pc_cvnn.arm_modules.servo_latent import ServoLatentModule
from pc_cvnn.arm_modules.base import ArmModule, ArmAgent
from act23_s1_objective_audit import solve
from energy_pc import activation


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,default=Path('log/s1-online-readout-20261003/model.npz'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    q=np.array([1.4,.4,.4,2.8,1.5]); velocity=np.array([.1,-.2,.3,0,.1]); command=q+.01
    model=FrozenServoPredictor(args.checkpoint); before=model.fingerprint()
    first=model.infer(q,velocity,command); changed=model.infer(q,velocity,command+.01)
    assert np.array_equal(first['position_latent'],changed['position_latent'])
    latent_change=float(np.linalg.norm(first['transition_latent']-changed['transition_latent']))
    assert latent_change>1e-8
    x=(np.concatenate([q,velocity,command])-model.input_mean)/model.input_std
    z,_,_=solve(model.encoder,x,'tanh',1.)
    reference=(model.online_head.T@activation(z,'tanh')).real*model.output_std+model.output_mean
    prediction_error=float(np.max(np.abs(reference-first['predicted_q_rad'])))
    assert prediction_error<1e-12
    assert model.fingerprint()==before
    assert not model.encoder.flags.writeable and not model.online_head.flags.writeable
    edge_q=np.array([-np.pi,-1.,0,1.,np.pi-1e-8])
    roundtrip=float(np.max(np.abs(position_from_latent(position_latent(edge_q))-edge_q)))
    assert roundtrip<1e-12
    value=np.array([1+2j,3-4j,5j]); assert np.array_equal(unpack_complex(pack_complex(value)),value)
    for invalid in ([0]*4,[np.pi]*5,[np.nan]*5):
        try:
            position_latent(invalid)
            raise AssertionError('Invalid phase input accepted')
        except ValueError:
            pass
    class Consumer(ArmModule):
        def __init__(self):
            super().__init__('TestConsumer'); self.add_in('position',10); self.received=None
        def step(self):
            packed=self.get_in('position')
            self.received=None if packed is None else position_from_latent(packed)
    module=ServoLatentModule(args.checkpoint); sink=Consumer(); agent=ArmAgent()
    agent.add(module); agent.add(sink); agent.wire(module,'position_latent',sink,'position')
    # Measured position must be usable even without an action or velocity.
    module.in_ports['q_rad'].set(q,seq=41)
    agent.step([module.name,sink.name])
    assert np.max(np.abs(sink.received-q))<1e-12
    assert module.get_out('transition_latent') is None
    assert module.out_ports['position_latent'].src_seq==41
    observed_generation=module.out_ports['position_latent'].seq
    module.in_ports['qvel_rad_s'].set(velocity,seq=41)
    module.in_ports['command_rad'].set(command,seq=42)
    agent.step([module.name,sink.name])
    assert module.get_out('transition_latent').shape==(48,)
    assert module.out_ports['transition_latent'].src_seq==(41,41,42)
    assert module.out_ports['position_latent'].seq==observed_generation
    assert module.out_ports['position_latent'].value.dtype.kind=='f'
    assert np.max(np.abs(sink.received-q))<1e-12
    assert sink.in_ports['position'].src_seq==module.out_ports['position_latent'].seq
    generations={key:port.seq for key,port in module.out_ports.items()}
    agent.step([module.name,sink.name])
    assert generations=={key:port.seq for key,port in module.out_ports.items()}
    module.in_ports['q_rad'].set(q,seq=42)  # new measurement can have the same numeric value
    agent.step([module.name,sink.name])
    assert module.out_ports['position_latent'].seq>observed_generation
    module.in_ports['command_rad'].set(None,seq=43)
    agent.step([module.name,sink.name])
    assert module.get_out('predicted_position_latent') is None
    assert np.max(np.abs(sink.received-q))<1e-12
    module.in_ports['q_rad'].set(None,seq=44)
    agent.step([module.name,sink.name])
    assert sink.received is None
    result=dict(passed=True,position_phase_roundtrip_max_rad=roundtrip,
                complex_pack_lossless=True,position_independent_of_command=True,
                transition_latent_change=latent_change,prediction_reference_max_error_rad=prediction_error,
                position_available_without_action=True,missing_input_invalidates_prediction=True,
                missing_position_invalidates_measured_port=True,port_provenance_preserved=True,
                held_inputs_keep_port_generation=True,new_measurement_advances_generation=True,
                parameter_freeze=True,body_consumer_is_test_double=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
