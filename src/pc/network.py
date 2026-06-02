"""PCNetwork — assembles PCNodes and PCConnections into a runnable graph."""

from __future__ import annotations

import numpy as np

from .node import PCNode, SensorNode
from .connection import PCConnection, ConnType


class PCNetwork:
    """
    Container and orchestrator for a Predictive Coding graph.

    Each hidden PCNode now carries an internal temporal forward model (V matrix)
    that predicts its own next state.  The temporal lifecycle is:

        Phase 1  load_predicted_state()  <- warm-start mu from V's prediction
                 hierarchical predict (top-down connections push pi)
        Phase 2  compute errors epsilon = mu - pi
        Phase 3  relax  (n_relax iterations)
        Phase 4  learn hierarchical W  (PCConnection.learn)
                 learn temporal V      (PCNode.learn_temporal)
        commit_step()  snapshot mu, run V forward to prepare next prediction

    Usage
    -----
    net = PCNetwork(eta_inf=0.1, n_relax=20)
    sensor = net.add(SensorNode("i1", dim=8))
    hidden = net.add(PCNode("a1", dim=16))
    top    = net.add(PCNode("b1", dim=4))
    net.connect("b1", "a1", ConnType.UP)
    net.connect("a1", "i1", ConnType.UP)
    sensor.set_input(x)
    net.step()
    net.commit_step()
    """

    def __init__(
        self,
        eta_inf: float = 0.05,
        n_relax: int = 20,
        eps_tol: float = 1e-4,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
        eta_learn: float = 0.001,
        eta_temporal: float | None = None,  # defaults to eta_learn if None
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
        self.eta_temporal = eta_temporal if eta_temporal is not None else eta_learn
        self.lambda_decay = lambda_decay
        self.w_clip = w_clip
        self._rng = rng or np.random.default_rng()

        self._nodes: dict[str, PCNode] = {}
        self._connections: list[PCConnection] = []

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add(self, node: PCNode) -> PCNode:
        """Register a node.  Returns the node for inline use."""
        if node.id in self._nodes:
            raise ValueError(f"Node id '{node.id}' already exists.")
        # Inject network-level temporal learning rate into newly added nodes
        if not node.is_clamped:
            node.eta_temporal = self.eta_temporal
            node.w_clip_V = self.w_clip
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
        Create a directed connection source -> target.

        Note: RECURRENT connections and the old tau/use_prev parameters are no
        longer needed -- the temporal forward model V inside each PCNode handles
        cross-frame prediction internally.  ConnType.RECURRENT is still accepted
        for backwards compatibility.
        """
        src = self._nodes[source_id]
        tgt = self._nodes[target_id]
        cid = conn_id or f"{source_id}->{target_id}"
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
        return self._nodes[node_id]

    # ------------------------------------------------------------------
    # Full time step
    # ------------------------------------------------------------------

    def step(self, learn: bool = True) -> dict:
        """
        Execute one full PC cycle:
            Phase 1 -- load forward-model prediction, then hierarchical predict
            Phase 2 -- compute errors
            Phase 3 -- relax (n_relax iterations or until eps_tol)
            Phase 4 -- learn  (hierarchical W + temporal V, skipped if learn=False)

        Returns diagnostics dict with 'relax_steps', 'sensor_error',
        'state_error', 'total_error'.
        """
        self._phase_predict()
        self._phase_error()
        relax_steps = self._phase_relax()
        if learn:
            self._phase_learn()

        sensor_error = sum(
            float(np.sum(n.epsilon ** 2))
            for n in self._nodes.values()
            if n.is_clamped
        )
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
    # Individual phases (public for experiments)
    # ------------------------------------------------------------------

    def phase_predict(self) -> None:
        self._phase_predict()

    def phase_error(self) -> None:
        self._phase_error()

    def phase_relax(self) -> int:
        return self._phase_relax()

    def phase_learn(self) -> None:
        self._phase_learn()

    def commit_step(self) -> None:
        """
        End-of-frame bookkeeping: snapshot each node's relaxed state, then run
        the temporal forward model V to produce predicted_next_mu for the NEXT
        frame's Phase-1 warm-start.
        """
        for node in self._nodes.values():
            node.commit_step()

    # ------------------------------------------------------------------
    # Internal phase implementations
    # ------------------------------------------------------------------

    def _phase_predict(self) -> None:
        """
        Phase 1:
          (a) Each hidden node warm-starts mu from its own forward-model prediction.
          (b) Every connection pushes a top-down prediction to its target.
          (c) Each node finalises its pi.
        """
        for node in self._nodes.values():
            node.load_predicted_state()
        for conn in self._connections:
            conn.predict()
        for node in self._nodes.values():
            node.finalize_prediction()

    def _phase_error(self) -> None:
        """Phase 2: epsilon = mu - pi for every node."""
        for node in self._nodes.values():
            node.compute_error()

    def _phase_relax(self) -> int:
        """Phase 3: iterative state update until convergence or n_relax steps."""
        for step in range(self.n_relax):
            for conn in self._connections:
                conn.propagate_error(beta=self.beta, gamma=self.gamma)
            max_delta = 0.0
            for node in self._nodes.values():
                mu_before = node.mu.copy()
                node.update_state(self.eta_inf, self.alpha)
                max_delta = max(max_delta, float(np.max(np.abs(node.mu - mu_before))))
            for conn in self._connections:
                conn.predict()
            for node in self._nodes.values():
                node.finalize_prediction()
                node.compute_error()
            if max_delta < self.eps_tol:
                return step + 1
        return self.n_relax

    def _phase_learn(self) -> None:
        """Phase 4: hierarchical W update + temporal V update."""
        for conn in self._connections:
            conn.learn()
        for node in self._nodes.values():
            node.learn_temporal()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def reset_states(self, rng: np.random.Generator | None = None) -> None:
        for node in self._nodes.values():
            if not node.is_clamped:
                node.reset(rng)

    def total_parameters(self) -> int:
        """Count all learnable parameters: W matrices (connections) + V matrices (nodes)."""
        w_params = sum(c.W.size for c in self._connections)
        v_params = sum(n.V.size for n in self._nodes.values() if not n.is_clamped)
        return w_params + v_params

    def summary(self) -> str:
        lines = ["PCNetwork"]
        lines.append(f"  nodes      : {len(self._nodes)}")
        lines.append(f"  connections: {len(self._connections)}")
        w_p = sum(c.W.size for c in self._connections)
        v_p = sum(n.V.size for n in self._nodes.values() if not n.is_clamped)
        lines.append(f"  parameters : {w_p + v_p}  (W={w_p}, V={v_p})")
        lines.append(f"  eta_inf={self.eta_inf}, n_relax={self.n_relax}, "
                     f"alpha={self.alpha}, beta={self.beta}, gamma={self.gamma}")
        lines.append(f"  eta_learn={self.eta_learn}, eta_temporal={self.eta_temporal}")
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
