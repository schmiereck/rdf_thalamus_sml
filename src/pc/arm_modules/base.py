"""A small, pluggable MODULE FRAMEWORK for the arm agent — the act14-19 port of the
1D PCModule architecture.

In the 1D line (act5-act11) the agent was split into PCModules (VisualCortex, BodyModel,
Premotor/Motor) with declared, named PORTS, plus separate PC-net modules (GoalModule,
Planner) coupled over clean interfaces.  That "pluggable, talks-only-over-ports" structure
is what this module restores for the MuJoCo arm.

Design: every component is its own `ArmModule` with declared, typed in/out `Port`s; an
`ArmAgent` wires ports together ("zusammengesteckt") and can step the modules.  The
internals are heterogeneous — a `PCNetwork`, an analytic linear FK, an MLP — but they all
implement the SAME port interface, so they plug in identically.  PC-net-backed modules
additionally expose their `PCModule` node-port grouping via `pc_module()`: the literal 1D
PCModule lives INSIDE them.  New interfaces are just new ports.
"""
from __future__ import annotations

import numpy as np


class Port:
    """A named, typed data channel on a module; holds the most recent value (or None)."""

    def __init__(self, name: str, dim: int, desc: str = "") -> None:
        self.name = name
        self.dim = dim
        self.desc = desc
        self.value = None

    def set(self, v):
        self.value = None if v is None else np.asarray(v, float)
        return self.value

    def __repr__(self) -> str:
        return f"Port({self.name!r}, dim={self.dim})"


class ArmModule:
    """Base class: declares named in/out ports and a `step()`.  A subclass reads its
    in-ports, computes, and writes its out-ports inside `step()`."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.in_ports: dict[str, Port] = {}
        self.out_ports: dict[str, Port] = {}

    # -- port declaration (chainable) --
    def add_in(self, name: str, dim: int, desc: str = "") -> "ArmModule":
        self.in_ports[name] = Port(name, dim, desc); return self

    def add_out(self, name: str, dim: int, desc: str = "") -> "ArmModule":
        self.out_ports[name] = Port(name, dim, desc); return self

    # -- value accessors --
    def get_in(self, name: str):
        return self.in_ports[name].value

    def set_in(self, name: str, v):
        return self.in_ports[name].set(v)

    def get_out(self, name: str):
        return self.out_ports[name].value

    def set_out(self, name: str, v):
        return self.out_ports[name].set(v)

    # -- overridables --
    def step(self) -> None:
        """Read in-ports, compute, write out-ports.  Override in subclasses."""
        raise NotImplementedError

    def surprise(self) -> dict | None:
        """Optional: the module's current surprise / diagnostics (for SurpriseViz), or None."""
        return None

    def pc_module(self):
        """Optional: the underlying PCModule node-port grouping (PC-net modules only)."""
        return None

    def __repr__(self) -> str:
        return (f"{type(self).__name__}({self.name!r}, "
                f"in={list(self.in_ports)}, out={list(self.out_ports)})")


class ArmAgent:
    """Holds module instances + the wiring between their ports, and runs them.

    `wire(src, 'out_port', dst, 'in_port')` connects an out-port to an in-port (dims must
    match).  `step(order)` propagates wired values then steps each module in `order`, so a
    downstream module sees the upstream module's fresh outputs.  `surprises()` collects the
    per-module surprise for the live viz; `summary()` prints the plugged-together wiring."""

    def __init__(self, name: str = "ArmAgent") -> None:
        self.name = name
        self.modules: dict[str, ArmModule] = {}
        self.edges: list[tuple[str, str, str, str]] = []   # (src_mod, src_port, dst_mod, dst_port)

    def add(self, module: ArmModule) -> ArmModule:
        if module.name in self.modules:
            raise ValueError(f"module {module.name!r} already added")
        self.modules[module.name] = module
        return module

    def wire(self, src, src_port: str, dst, dst_port: str) -> "ArmAgent":
        sm = self.modules[src] if isinstance(src, str) else src
        dm = self.modules[dst] if isinstance(dst, str) else dst
        sp, dp = sm.out_ports[src_port], dm.in_ports[dst_port]
        if sp.dim != dp.dim:
            raise ValueError(f"port dim mismatch: {sm.name}.{src_port}({sp.dim}) -> "
                             f"{dm.name}.{dst_port}({dp.dim})")
        self.edges.append((sm.name, src_port, dm.name, dst_port))
        return self

    def _propagate(self) -> None:
        for (sm, sp, dm, dp) in self.edges:
            self.modules[dm].in_ports[dp].set(self.modules[sm].out_ports[sp].value)

    def step(self, order: list[str]) -> None:
        """Step the modules named in `order`, propagating wired port values before each."""
        for nm in order:
            self._propagate()
            self.modules[nm].step()
        self._propagate()

    def surprises(self) -> dict:
        return {nm: m.surprise() for nm, m in self.modules.items()}

    def summary(self) -> str:
        lines = [f"ArmAgent {self.name!r} — {len(self.modules)} modules, {len(self.edges)} wires"]
        for nm, m in self.modules.items():
            tag = "  (PC-net)" if m.pc_module() is not None else ""
            lines.append(f"  [{nm}]{tag}  in={list(m.in_ports)}  out={list(m.out_ports)}")
        lines.append("  wiring (plugged together):")
        for (sm, sp, dm, dp) in self.edges:
            lines.append(f"    {sm}.{sp}  ->  {dm}.{dp}")
        return "\n".join(lines)
