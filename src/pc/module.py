"""PCModule — a named group of PCNodes with declared input/output ports.

A module is a purely organisational concept: it wraps a subset of nodes
inside a PCNetwork and declares which nodes form its interface.  The
underlying mechanics (connections, learning, relaxation) are completely
unchanged — modules add *naming and routing* on top.

Port model
----------
Each port is a named, ordered list of node IDs.  A single node may appear
on both an in-port and an out-port of the same module (e.g. a sensor node
that receives external input AND broadcasts its activation outward).

Typical usage
-------------
    # 1. Build the network as usual, get back node IDs.
    # 2. Wrap groups of nodes into modules:
    vis = PCModule("VisualCortex")
    vis.add_in_port("obj_input",  obj_ids)
    vis.add_out_port("obj_row",   obj_ids)
    vis.add_in_port("ptr_input",  ptr_ids)
    vis.add_out_port("ptr_row",   ptr_ids)

    hid = PCModule("HiddenHierarchy")
    hid.add_in_port("visual",   h1_ids)
    hid.add_out_port("abstract", top_ids)

    # 3. Register modules with the network (optional, for summary):
    net.add_module(vis)
    net.add_module(hid)

    # 4. Wire modules with existing connect() calls OR the helper:
    #    net.wire_modules(vis, "obj_row", hid, "visual", ConnType.UP)
    #    (helper creates one connection per node pair in order)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .network import PCNetwork
    from .node import PCNode


class PCModule:
    """A named group of PCNodes with declared input/output ports."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._node_ids: list[str] = []
        self.in_ports:  dict[str, list[str]] = {}
        self.out_ports: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def register(self, *node_ids: str) -> "PCModule":
        """Mark node IDs as belonging to this module (no duplicate check needed)."""
        for nid in node_ids:
            if nid not in self._node_ids:
                self._node_ids.append(nid)
        return self

    def add_in_port(self, port_name: str, node_ids: list[str]) -> "PCModule":
        """Declare an input port (list of node IDs, in order)."""
        self.in_ports[port_name] = list(node_ids)
        self.register(*node_ids)
        return self

    def add_out_port(self, port_name: str, node_ids: list[str]) -> "PCModule":
        """Declare an output port (list of node IDs, in order)."""
        self.out_ports[port_name] = list(node_ids)
        self.register(*node_ids)
        return self

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    @property
    def node_ids(self) -> list[str]:
        return list(self._node_ids)

    def port_in(self, port_name: str) -> list[str]:
        """Return the node-ID list for a named input port."""
        return self.in_ports[port_name]

    def port_out(self, port_name: str) -> list[str]:
        """Return the node-ID list for a named output port."""
        return self.out_ports[port_name]

    def nodes(self, net: "PCNetwork", port_name: str | None = None) -> list["PCNode"]:
        """Return PCNode objects, either for a named port or for all module nodes.

        net.node(id) is used, so the nodes must already be registered with net.
        """
        ids = (
            self.in_ports.get(port_name) or self.out_ports.get(port_name)
            if port_name is not None
            else self._node_ids
        )
        if ids is None:
            raise KeyError(f"Port {port_name!r} not found in module {self.name!r}")
        return [net.node(nid) for nid in ids]

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"PCModule({self.name!r}, "
            f"nodes={len(self._node_ids)}, "
            f"in_ports={list(self.in_ports)}, "
            f"out_ports={list(self.out_ports)})"
        )
