"""
matverse.atlas
==============

Atlas — the live cartographic projection of the MatVerse organism.

Atlas is NOT the organism, NOT the memory. It is a navigable map
derived from the Registry, the receipts, the SVCAs, and the MMNB lineage.

What Atlas answers:
  - what exists?
  - where is it?
  - how does it relate?
  - where did it come from?
  - what function does it serve?
  - in what state is it?
  - what can transform it?

Atlas is regenerated from the underlying sources of truth. It is not
maintained as a parallel narrative.

The Atlas data model is a small graph:

  Node  = a named entity (organ, organ version, capability, hypothesis,
          experiment, SVCA, closure, MMNB seed, ...)
  Edge  = a typed relation (depends_on, instance_of, derived_from,
          registered_in, ...)

A snapshot is the dict serialization of that graph.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Node & Edge
# ---------------------------------------------------------------------------

@dataclass
class AtlasNode:
    id: str
    kind: str                            # organ | capability | hypothesis | svca | closure | mmnb_seed | ...
    name: str = ""
    state: str = "ACTIVE"                # ACTIVE | DEGRADED | QUARANTINED | SUPERSEDED | REVOKED | ARCHIVED
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen_ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "state": self.state,
            "metadata": self.metadata,
            "last_seen_ts": self.last_seen_ts,
        }


@dataclass
class AtlasEdge:
    src: str
    dst: str
    relation: str                        # depends_on | instance_of | derived_from | registered_in | ...
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"src": self.src, "dst": self.dst,
                "relation": self.relation, "metadata": self.metadata}


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------

class Atlas:
    """The live projection of the organism's anatomy and lineage."""

    def __init__(self) -> None:
        self._nodes: Dict[str, AtlasNode] = {}
        self._edges: List[AtlasEdge] = []
        self._index: Dict[str, Set[str]] = {}     # kind -> set of ids

    # ----------------- ingestion -----------------

    def upsert_node(self, node: AtlasNode) -> None:
        node.last_seen_ts = int(time.time())
        self._nodes[node.id] = node
        self._index.setdefault(node.kind, set()).add(node.id)

    def add_edge(self, edge: AtlasEdge) -> None:
        self._edges.append(edge)
        # Ensure both endpoints exist as nodes (as instances of nothing)
        if edge.src not in self._nodes:
            self.upsert_node(AtlasNode(id=edge.src, kind="unknown"))
        if edge.dst not in self._nodes:
            self.upsert_node(AtlasNode(id=edge.dst, kind="unknown"))

    # ----------------- bulk update from canonical sources -----------------

    def register_organ(self, organ_id: str, name: str,
                       state: str = "ACTIVE",
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        self.upsert_node(AtlasNode(
            id=organ_id, kind="organ", name=name, state=state,
            metadata=metadata or {},
        ))

    def register_capability(self, capability_id: str, organ_id: str,
                            state: str = "ACTIVE",
                            metadata: Optional[Dict[str, Any]] = None) -> None:
        self.upsert_node(AtlasNode(
            id=capability_id, kind="capability",
            name=capability_id, state=state,
            metadata=metadata or {},
        ))
        self.add_edge(AtlasEdge(src=capability_id, dst=organ_id,
                                relation="registered_in"))

    def record_svca(self, svca_id: str, capability_id: str,
                    problem_id: str, status: str = "PASS",
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        self.upsert_node(AtlasNode(
            id=svca_id, kind="svca", name=svca_id, state=status,
            metadata=metadata or {},
        ))
        self.add_edge(AtlasEdge(src=svca_id, dst=capability_id,
                                relation="produced_by"))
        self.add_edge(AtlasEdge(src=svca_id, dst=problem_id,
                                relation="evidence_for"))

    def record_closure(self, closure_id: str, parent_closure_id: Optional[str],
                       svca_ids: List[str], state: str = "CLOSED") -> None:
        self.upsert_node(AtlasNode(
            id=closure_id, kind="closure", name=closure_id, state=state,
        ))
        for s in svca_ids:
            self.add_edge(AtlasEdge(src=closure_id, dst=s, relation="incorporates"))
        if parent_closure_id:
            self.add_edge(AtlasEdge(src=closure_id, dst=parent_closure_id,
                                    relation="derived_from"))

    def record_mmnb_seed(self, seed_id: str, parent_seed: Optional[str],
                         closure_id: Optional[str] = None) -> None:
        self.upsert_node(AtlasNode(id=seed_id, kind="mmnb_seed",
                                   name=seed_id, state="ACTIVE"))
        if parent_seed:
            self.add_edge(AtlasEdge(src=seed_id, dst=parent_seed,
                                    relation="evolved_from"))
        if closure_id:
            self.add_edge(AtlasEdge(src=seed_id, dst=closure_id,
                                    relation="produced_by"))

    def set_node_state(self, node_id: str, state: str) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].state = state
            self._nodes[node_id].last_seen_ts = int(time.time())

    # ----------------- queries -----------------

    def nodes(self, kind: Optional[str] = None) -> List[AtlasNode]:
        if kind is None:
            return list(self._nodes.values())
        return [n for n in self._nodes.values() if n.kind == kind]

    def edges(self) -> List[AtlasEdge]:
        return list(self._edges)

    def neighbours(self, node_id: str) -> List[AtlasEdge]:
        return [e for e in self._edges
                if e.src == node_id or e.dst == node_id]

    def health(self) -> Dict[str, Any]:
        states: Dict[str, int] = {}
        for n in self._nodes.values():
            states[n.state] = states.get(n.state, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "states": states,
            "kinds": {k: len(v) for k, v in self._index.items()},
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "ts": int(time.time()),
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
            "health": self.health(),
        }
