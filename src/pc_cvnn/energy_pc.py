"""Isolated, non-temporal complex PC reference implementation (not an ACT23 backend).

E = 1/2 sum_j ||mu_j - mean_i(W_ij.T f(mu_i))||^2.
Nodes without parents have prediction zero, hence a unit quadratic prior.
All derivatives use real coordinates (Re, Im). No decay, clipping, gain heuristics,
temporal warm starts, silent recovery or production-engine monkeypatches.
"""
from dataclasses import dataclass

import numpy as np


def activation(z, name):
    if name == 'tanh':
        r = np.abs(z)
        return z * np.divide(np.tanh(r), r, out=np.ones_like(r), where=r > 0)
    if name in ('identity', 'relu'):
        return z.copy()  # unshifted modulus ReLU is identity, including at zero
    raise ValueError(f'Unsupported activation: {name}')


def pullback(z, g, name):
    if name in ('identity', 'relu'):
        return g.copy()
    if name != 'tanh':
        raise ValueError(name)
    r = np.abs(z)
    tangent = np.divide(np.tanh(r), r, out=np.ones_like(r), where=r > 0)
    radial_projection = np.divide(np.real(z.conj()*g), r*r,
                                  out=np.zeros_like(r), where=r > 0)
    return tangent*g + (1-np.tanh(r)**2-tangent)*z*radial_projection


@dataclass
class Edge:
    source: str
    target: str
    weight: np.ndarray


class EnergyPC:
    """Small explicit graph. Topology is fixed at construction; all arrays are owned.

    infer() holds clamps and W fixed; learn() holds mu fixed and updates W once.
    reset() clears states and clamps, never parameters. Each sample must install its
    clamps explicitly. Temporal modes other than 'off' are deliberately unsupported.
    """

    def __init__(self, nodes, edges, *, temporal_mode='off'):
        if temporal_mode != 'off':
            raise ValueError('Only explicit temporal_mode="off" is supported')
        self.spec = dict(nodes)  # id -> (dimension, activation)
        self.mu = {k: np.zeros(d, complex) for k, (d, _) in self.spec.items()}
        for _, name in self.spec.values():
            activation(np.zeros(1, complex), name)
        self.edges = []
        self.degree = dict.fromkeys(self.spec, 0)
        for source, target, weight in edges:
            w = np.array(weight, dtype=complex, copy=True)
            if w.shape != (self.spec[source][0], self.spec[target][0]):
                raise ValueError('Invalid weight dimensions')
            self.edges.append(Edge(source, target, w))
            self.degree[target] += 1
        self.clamped = set()
        self._check()

    def _check(self):
        if not all(np.isfinite(a).all() for a in [*self.mu.values(),
                                                  *(e.weight for e in self.edges)]):
            raise FloatingPointError('Nonfinite PC state or parameter; no silent reset')

    def reset(self):
        for state in self.mu.values():
            state.fill(0)
        self.clamped.clear()

    def clamp(self, key, value):
        value = np.asarray(value, dtype=complex)
        if value.shape != self.mu[key].shape or not np.isfinite(value).all():
            raise ValueError(f'Invalid clamp for {key}')
        self.mu[key] = value.copy()
        self.clamped.add(key)

    def unclamp(self, key):
        self.clamped.discard(key)

    def commit_step(self):
        """Intentional no-op: temporal off is not a frozen random V."""

    def terms(self):
        self._check()
        acts = {k: activation(z, self.spec[k][1]) for k, z in self.mu.items()}
        pred = {k: np.zeros_like(z) for k, z in self.mu.items()}
        for edge in self.edges:
            pred[edge.target] += edge.weight.T @ acts[edge.source] / self.degree[edge.target]
        errors = {k: self.mu[k] - pred[k] for k in self.mu}
        energy = .5*sum(float(np.vdot(v, v).real) for v in errors.values())
        if not np.isfinite(energy):
            raise FloatingPointError('Nonfinite PC energy')
        return energy, errors, acts

    def directions(self):
        """Negative real-coordinate gradients, including clamped coordinates for audits."""
        energy, errors, acts = self.terms()
        pressure = {k: np.zeros_like(z) for k, z in self.mu.items()}
        dw = []
        for edge in self.edges:
            error = errors[edge.target] / self.degree[edge.target]
            pressure[edge.source] += edge.weight.conj() @ error
            dw.append(np.outer(acts[edge.source].conj(), error))
        dz = {k: -errors[k] + pullback(self.mu[k], pressure[k], self.spec[k][1])
              for k in self.mu}
        return energy, dz, dw

    def infer(self, *, max_steps=128, step_size=.08, tolerance=1e-5):
        """Simultaneous state descent with Armijo backtracking and convergence report.

        No claim of a global optimum for nonlinear graphs. Learning is separate, so
        energy monotonicity refers strictly to fixed-parameter inference.
        """
        if max_steps < 0 or step_size <= 0 or tolerance <= 0:
            raise ValueError('Invalid inference settings')
        free = [k for k in self.mu if k not in self.clamped]
        history = [self.terms()[0]]
        backtracks = 0
        for _ in range(max_steps):
            energy, dz, _ = self.directions()
            norm = max((float(np.max(np.abs(dz[k]))) for k in free), default=0.)
            if norm <= tolerance:
                break
            squared = sum(float(np.vdot(dz[k], dz[k]).real) for k in free)
            old = {k: self.mu[k].copy() for k in free}
            rate = step_size
            for attempt in range(40):
                for k in free:
                    self.mu[k] = old[k] + rate*dz[k]
                try:
                    candidate = self.terms()[0]
                except FloatingPointError:
                    candidate = np.inf
                if candidate <= energy - 1e-4*rate*squared + 1e-14*max(1., energy):
                    break
                rate *= .5
                backtracks += 1
            else:
                self.mu.update(old)
                raise RuntimeError('Inference line search failed; state restored')
            history.append(candidate)
        _, dz, _ = self.directions()
        norm = max((float(np.max(np.abs(dz[k]))) for k in free), default=0.)
        return dict(steps=len(history)-1, converged=norm <= tolerance,
                    gradient_max=norm, energies=history, backtracks=backtracks)

    def learn(self, rate=.004):
        if not np.isfinite(rate) or rate < 0:
            raise ValueError('Invalid learning rate')
        if rate == 0:
            return  # strict freeze, including no clipping/decay
        _, _, dw = self.directions()
        candidates = [edge.weight + rate*delta for edge, delta in zip(self.edges, dw)]
        if not all(np.isfinite(w).all() for w in candidates):
            raise FloatingPointError('Nonfinite update; parameters unchanged')
        for edge, weight in zip(self.edges, candidates):
            edge.weight = weight
