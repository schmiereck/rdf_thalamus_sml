"""Frozen S1 predictor and explicit proprioceptive latent interface.

Position phases are reversible sensor coding, NOT a learned body model or FK.
The learned 24-complex transition features depend on the candidate servo command.
Only joint_0..joint_4 and the trained 20ms S1 horizon are supported here.
"""
from pathlib import Path
import hashlib

import numpy as np
from scipy.optimize import minimize

from .energy_pc import activation, pullback

JOINTS=tuple(f'joint_{i}' for i in range(5))
POSITION_SCHEMA='joint-phase-v1/ReIm-interleaved/rad/principal-interval'
HORIZON_SECONDS=.02


def pack_complex(z):
    z=np.asarray(z,dtype=complex)
    if z.ndim!=1 or not np.isfinite(z).all():
        raise ValueError('Expected finite complex vector')
    return np.column_stack([z.real,z.imag]).reshape(-1)


def unpack_complex(value):
    value=np.asarray(value,dtype=float)
    if value.ndim!=1 or value.size%2 or not np.isfinite(value).all():
        raise ValueError('Expected finite interleaved Re/Im vector')
    return value[::2]+1j*value[1::2]


def joint_vector(value):
    value=np.asarray(value,dtype=float)
    if value.shape!=(5,) or not np.isfinite(value).all():
        raise ValueError('Expected five finite joint values')
    return value


def position_latent(q):
    q=joint_vector(q)
    if np.any(q < -np.pi) or np.any(q >= np.pi):
        raise ValueError('Position phase v1 requires -pi <= q < pi; no multi-turn aliasing')
    return pack_complex(np.exp(1j*q))


def position_from_latent(packed):
    phase=unpack_complex(packed)
    if phase.shape!=(5,) or not np.allclose(np.abs(phase),1.,rtol=0,atol=1e-10):
        raise ValueError('Expected five unit position phases')
    # Canonicalize the signed pi boundary consistently with the supported interval.
    return (np.angle(phase)+np.pi)%(2*np.pi)-np.pi


class FrozenServoPredictor:
    """Read-only learned arrays, stable coordinate identifiers, no training API."""
    def __init__(self,checkpoint):
        path=Path(checkpoint)
        self.model_id=hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path,allow_pickle=False) as saved:
            for key,shape in [('encoder',(24,15)),('online_head',(24,5)),
                              ('input_mean',(15,)),('input_std',(15,)),
                              ('output_mean',(5,)),('output_std',(5,))]:
                array=np.array(saved[key],copy=True)
                if array.shape!=shape or not np.isfinite(array).all():
                    raise ValueError(f'Invalid {key}')
                array.setflags(write=False)
                setattr(self,key,array)
        if np.any(self.input_std<=0) or np.any(self.output_std<=0):
            raise ValueError('Invalid normalization')
        self.encoder_id=hashlib.sha256(b''.join(a.tobytes() for a in
                         (self.encoder,self.input_mean,self.input_std))).hexdigest()

    def fingerprint(self):
        return hashlib.sha256(b''.join(getattr(self,k).tobytes() for k in
            ('encoder','online_head','input_mean','input_std','output_mean','output_std'))).hexdigest()

    def infer(self,q,qvel,command):
        q,qvel,command=map(joint_vector,(q,qvel,command))
        measured=position_latent(q)
        x=(np.concatenate([q,qvel,command])-self.input_mean)/self.input_std
        def objective(v):
            z=v[:24]+1j*v[24:]
            error=self.encoder.T@activation(z,'tanh')-x
            value=.5*float(np.vdot(z,z).real+np.vdot(error,error).real)
            gradient=z+pullback(z,self.encoder.conj()@error,'tanh')
            return value,np.concatenate([gradient.real,gradient.imag])
        result=minimize(objective,np.zeros(48),jac=True,method='L-BFGS-B',
                        options=dict(maxiter=2048,gtol=1e-9,ftol=1e-15,maxls=40))
        _,gradient=objective(result.x)
        residual=float(np.max(np.abs(gradient[:24]+1j*gradient[24:])))
        if residual>=1e-5 or not np.isfinite(residual):
            raise RuntimeError(f'Unconverged servo inference: {residual}')
        z=result.x[:24]+1j*result.x[24:]
        features=activation(z,'tanh')
        prediction=(self.online_head.T@features).real*self.output_std+self.output_mean
        return dict(position_latent=measured,velocity_rad_s=qvel.copy(),
                    transition_latent=pack_complex(features),latent_state=pack_complex(z),
                    predicted_position_latent=position_latent(prediction),predicted_q_rad=prediction,
                    gradient_max=residual)
