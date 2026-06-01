"""PCNetwork — assembles PCNodes and PCConnections into a runnable graph."""

from __future__ import annotations

import numpy as np

from .node import PCNode, SensorNode
from .connection import PCConnection, ConnType


class PCNetwork:
    """
    Container and orchestrator for a Predictive Coding graph.

    Usage
    -----
    net = PCNetwork(eta_inf=0.1, n_relax=20)

    # Build graph
    sensor = net.add(SensorNode("i1", dim=8))
    hidden = net.add(PCNode("a1", dim=16))
    top    = net.add(PCNode("b1", dim=4))
    net.connect("i1", "a1", ConnType.UP)
    net.connect("a1", "b1", ConnType.UP)

    # Run one time step
    sensor.set_input(x)
    net.step()

    # Inspect
    print(top.mu)      # top-level representation
    print(hidden.epsilon)  # prediction error at hidden layer
    """

    def __init__(
        self,
        eta_inf: float = 0.05,
        n_relax: int = 20,
        eps_tol: float = 1e-4,
        alpha: float = 1.0,   # weight on own-error pressure
        beta: float = 1.0,    # weight on UP back-pressure
        gamma: float = 1.0,   # weight on LATERAL back-pressure
        eta_learn: float = 0.001,
        lambda_decay: float = 0.0,
        w_clip: float = 5.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.eta_inf = eta_inf
        self.n_relax = n_relax
        self.eps_tol = eps_tol
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.eta_learn = eta_learn
        self.lambda_decay = lambda_decay
        self.w_clip = w_clip
        self._rng = rng or np.random.default_rng()

        self._nodes: dict[str, PCNode] = {}
        self._connections: list[PCConnection] = []

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add(self, node: PCNode) -> PCNode:
        """Register a node. Returns the node for inline use."""
        if node.id in self._nodes:
            raise ValueError(f"Node id '{node.id}' already exists.")
        self._nodes[node.id] = node
        return node

    def connect(
        self,
        source_id: str,
        target_id: str,
        conn_type: ConnType = ConnType.UP,
        eta_learn: float | None = None,
        lambda_decay: float | None = None,
        pressure_scale: float = 1.0,
        conn_id: str | None = None,
    ) -> PCConnection:
        """
        Create a connection source → target and register it.

        source and target must already be added via add().
        Returns the PCConnection for optional inspection.
        """
        src = self._nodes[source_id]
        tgt = self._nodes[target_id]
        cid = conn_id or f"{source_id}→{target_id}"
        conn = PCConnection(
            conn_id=cid,
            source=src,
            target=tgt,
            conn_type=conn_type,
            eta_learn=eta_learn if eta_learn is not None else self.eta_learn,
            lambda_decay=lambda_decay if lambda_decay is not None else self.lambda_decay,
            w_clip=self.w_clip,
            pressure_scale=pressure_scale,
            rng=self._rng,
        )
        self._connections.append(conn)
        return conn

    def node(self, node_id: str) -> PCNode:
        """Look up a node by id."""
        return self._nodes[node_id]

    # ------------------------------------------------------------------
    # Full time step
    # ------------------------------------------------------------------

    def step(self, learn: bool = True) -> dict:
        """
        Execute one full PC cycle:
            Phase 1 — predict
            Phase 2 — compute errors
            Phase 3 — relax (n_relax iterations or until eps_tol)
            Phase 4 — learn  (skipped if learn=False)

        Returns a dict with diagnostics:
            'relax_steps'  : actual iterations used
            'total_error'  : sum of ||ε||² across all non-sensor nodes
        """
        self._phase_predict()
        self._phase_error()
        relax_steps = self._phase_relax()
        if learn:
            self._phase_learn()

        # Sensor error = how well the network predicts the input (the real signal)
        sensor_error = sum(
            float(np.sum(n.epsilon ** 2))
            for n in self._nodes.values()
            if n.is_clamped
        )
        # State error = mismatch between hidden states and predictions from above
        state_error = sum(
            float(np.sum(n.epsilon ** 2))
            for n in self._nodes.values()
            if not n.is_clamped
        )
        return {
            "relax_steps": relax_steps,
            "sensor_error": sensor_error,
            "state_error": state_error,
            "total_error": sensor_error + state_error,
        }

    # ------------------------------------------------------------------
    # Individual phases (public so experiments can call them selectively)
    # ------------------------------------------------------------------

    def phase_predict(self) -> None:
        self._phase_predict()

    def phase_error(self) -> None:
        self._phase_error()

    def phase_relax(self) -> int:
        return self._phase_relax()

    def phase_learn(self) -> None:
        self._phase_learn()

    # ------------------------------------------------------------------
    # Internal phase implementations
    # ------------------------------------------------------------------

    def _phase_predict(self) -> None:
        """Phase 1: every connection pushes a prediction to its target."""
        for conn in self._connections:
            conn.predict()
        for node in self._nodes.values():
            node.finalize_prediction()

    def _phase_error(self) -> None:
        """Phase 2: every node computes ε = μ - π."""
        for node in self._nodes.values():
            node.compute_error()

    def _phase_relax(self) -> int:
        """
        Phase 3: iterative state update until convergence or n_relax steps.

        After each state update, predictions and errors are recomputed so that
        the relaxation gradient is always consistent with the current states.
        """
        for step in range(self.n_relax):
            # Collect error back-pressure from all connections
            for conn in self._connections:
                conn.propagate_error(beta=self.beta, gamma=self.gamma)

            # Update states, track max change for convergence check
            max_delta = 0.0
            for node in self._nodes.values():
                mu_before = node.mu.copy()
                node.update_state(self.eta_inf, self.alpha)
                max_delta = max(max_delta, float(np.max(np.abs(node.mu - mu_before))))

            # Recompute predictions and errors with updated states
            for conn in self._connections:
                conn.predict()
            for node in self._nodes.values():
                node.finalize_prediction()
                node.compute_error()

            if max_delta < self.eps_tol:
                return step + 1

        return self.n_relax

    def _phase_learn(self) -> None:
        """Phase 4: every connection applies its local Hebbian update."""
        for conn in self._connections:
            conn.learn()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def reset_states(self, rng: np.random.Generator | None = None) -> None:
        """Reset all node states (not weights) — useful between sequences."""
        for node in self._nodes.values():
            if not node.is_clamped:
                node.reset(rng)

    def total_parameters(self) -> int:
        """Count total learnable parameters (weight matrix elements)."""
        return sum(c.W.size for c in self._connections)

    def summary(self) -> str:
        lines = ["PCNetwork"]
        lines.append(f"  nodes      : {len(self._nodes)}")
        lines.append(f"  connections: {len(self._connections)}")
        lines.append(f"  parameters : {self.total_parameters()}")
        lines.append(f"  eta_inf={self.eta_inf}, n_relax={self.n_relax}, "
                     f"alpha={self.alpha}, beta={self.beta}, gamma={self.gamma}")
        lines.append("")
        lines.append("  Nodes:")
        for n in self._nodes.values():
            lines.append(f"    {n}")
        lines.append("  Connections:")
        for c in self._connections:
            lines.append(f"    {c}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"PCNetwork(nodes={len(self._nodes)}, "
            f"connections={len(self._connections)}, "
            f"params={self.total_parameters()})"
        )
