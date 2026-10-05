"""Six-servo phase boundary, real ACT23 replay and port lifecycle checks."""
import json
from pathlib import Path
import sys
import io
from types import SimpleNamespace
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc_cvnn.measured_servo import LOW, HIGH, encode, decode
from pc_cvnn.arm_modules.measured_servo import MeasuredServoModule
from pc_cvnn.act23_transition_recorder import TransitionRecorder


def run():
    rng = np.random.default_rng(67)
    rows = rng.uniform(LOW,HIGH,(1000,6))
    rows = np.vstack([rows, [LOW, HIGH, np.pi, np.pi+.0002, -.0024, 0]])
    error = max(float(np.max(abs(decode(encode(q))-q))) for q in rows)
    assert error<1e-12
    for q in [np.zeros(5), np.full(6,np.nan), np.full(6,HIGH+1e-5), np.full(6,LOW-1e-5), np.ones(6)*2*np.pi]:
        try:
            encode(q)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid/aliased input accepted')
    m = MeasuredServoModule()
    q = rows[-1]
    m.in_ports['q_rad'].set(q,seq=1)
    m.step()
    assert np.max(abs(decode(m.get_out('position_latent'))-q))<1e-12
    assert m.get_out('velocity_rad_s') is None
    port=m.out_ports['position_latent']
    port._geschrieben=False
    m.step(); assert not port._geschrieben, 'Held measurement republished'
    m.in_ports['q_rad'].set(q,seq=2)
    m.step(); assert port._geschrieben and port.src_seq==2
    m.in_ports['q_rad'].set(None,seq=3)
    m.step(); assert m.get_out('position_latent') is None
    artifact=Path('log/act23-workpose-20261004-r3/observations.json')
    replay_error=None
    if artifact.exists():
        observations=json.loads(artifact.read_text())
        replay_error=max(float(np.max(abs(decode(encode(np.r_[r['q_rad'],r['gripper_rad']]))-
                                       np.r_[r['q_rad'],r['gripper_rad']]))) for r in observations)
        assert replay_error<1e-12
    # Check the causal step boundary without a physics model: original called once with n,
    # output preserved, no extra step, before/after observations correctly paired.
    rec=TransitionRecorder.__new__(TransitionRecorder)
    rec.handle=io.StringIO(); rec.count=0; rec.split='train'
    rec.images=[]; rec.image_rows=[]; rec.image_side=[]
    sim=SimpleNamespace(d=SimpleNamespace(time=0.),m=SimpleNamespace(opt=SimpleNamespace(timestep=.002)))
    sim.q=np.full(6,.2)
    sim.render=lambda camera: np.full((240,240,3),int(round(sim.q[0]*100)),dtype=np.uint8)
    rec.sensors=lambda instance:(instance.q.copy(),np.ones(6),np.full(6,.3))
    calls=[]
    def original(n):
        calls.append(n); sim.q+=n*.002; sim.d.time+=n*.002
        return 'original-result'
    assert rec.step(sim,original,2,0,'over','overview')=='original-result'
    row=json.loads(rec.handle.getvalue())
    assert calls==[2] and row['physics_steps']==2 and row['next_time']==.004
    assert np.allclose(row['q_rad'],.2) and np.allclose(row['q_next_rad'],.204)
    assert rec.image_rows==[0,0] and rec.image_side==[0,1]
    assert row['has_camera_pair'] and row['position_valid']
    return dict(max_roundtrip_rad=error, real_act23_roundtrip_rad=replay_error,
                invalid_inputs_rejected=True, held_fresh_missing_controls=True,
                native_step_called_once_and_time_pairing=True)


if __name__=='__main__':
    print(json.dumps(run(),indent=2))
