"""Typed, versioned multidimensional property graph — the 'meta-neural network'.

"Meta-neural" is a *graph architecture metaphor*, not a claim of cognition. The
structure is a plain typed property graph:

* **Typed nodes/edges** — every node and edge carries a ``type`` drawn from a
  registered :class:`GraphSchema`.
* **Dimensions** — nodes live in a set of named scalar *dimensions* (a sparse
  coordinate in a labelled space), enabling the coupling/QUBO layers to treat
  the graph as a numeric system.
* **Provenance** — every node/edge records who/what created it, when, and under
  which consent grant/purpose.
* **Immutable snapshots** — a :class:`GraphSnapshot` is frozen and content
  addressed (sha256 of its canonical serialisation).
* **Schema versioning + validation** — snapshots embed a schema version and are
  validated against the schema on build.
* **Deterministic serialisation** — canonical JSON (sorted keys, fixed float
  formatting) so equal graphs hash equally across runs/machines.

Privacy: nodes store opaque subject ids and numeric dimensions only. Raw vault
attributes never enter a snapshot.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, UTC
from collections.abc import Mapping

SCHEMA_VERSION = "1.0.0"


class GraphError(ValueError):
    """Raised on schema/validation violations."""


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_number(x: float) -> float:
    # Normalise -0.0 to 0.0 and round to a stable precision for hashing.
    v = round(float(x), 12)
    return 0.0 if v == 0.0 else v


@dataclass(frozen=True)
class Provenance:
    """Where a graph element came from."""

    created_by: str
    created_at: str
    purpose: str | None = None
    grant_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "created_by": self.created_by,
            "created_at": self.created_at,
            "purpose": self.purpose,
            "grant_id": self.grant_id,
        }

    @staticmethod
    def now(created_by: str, *, purpose: str | None = None,
            grant_id: str | None = None) -> Provenance:
        return Provenance(created_by=created_by, created_at=_utcnow_iso(),
                          purpose=purpose, grant_id=grant_id)


@dataclass(frozen=True)
class GraphSchema:
    """Registered node/edge types and the allowed dimension names."""

    version: str
    node_types: frozenset[str]
    edge_types: frozenset[str]
    dimensions: frozenset[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "node_types": sorted(self.node_types),
            "edge_types": sorted(self.edge_types),
            "dimensions": sorted(self.dimensions),
        }


@dataclass(frozen=True)
class Node:
    node_id: str
    type: str
    dimensions: Mapping[str, float]
    attributes: Mapping[str, object]
    provenance: Provenance

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "type": self.type,
            "dimensions": {k: _canonical_number(v) for k, v in self.dimensions.items()},
            "attributes": dict(self.attributes),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class Edge:
    edge_id: str
    type: str
    source: str
    target: str
    weight: float
    attributes: Mapping[str, object]
    provenance: Provenance

    def to_dict(self) -> dict[str, object]:
        return {
            "edge_id": self.edge_id,
            "type": self.type,
            "source": self.source,
            "target": self.target,
            "weight": _canonical_number(self.weight),
            "attributes": dict(self.attributes),
            "provenance": self.provenance.to_dict(),
        }


class PropertyGraph:
    """Mutable builder for a typed property graph.

    Mutations are validated against the schema immediately. Call
    :meth:`snapshot` to produce an immutable, content-addressed
    :class:`GraphSnapshot`.
    """

    def __init__(self, schema: GraphSchema) -> None:
        self.schema = schema
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}

    # -- nodes -----------------------------------------------------------
    def add_node(
        self,
        node_id: str,
        type: str,
        *,
        dimensions: Mapping[str, float] | None = None,
        attributes: Mapping[str, object] | None = None,
        provenance: Provenance,
    ) -> Node:
        if type not in self.schema.node_types:
            raise GraphError(f"unknown node type {type!r}")
        dims = dict(dimensions or {})
        for dim in dims:
            if dim not in self.schema.dimensions:
                raise GraphError(f"unknown dimension {dim!r}")
        if node_id in self._nodes:
            raise GraphError(f"duplicate node_id {node_id!r}")
        node = Node(
            node_id=node_id,
            type=type,
            dimensions={k: float(v) for k, v in dims.items()},
            attributes=dict(attributes or {}),
            provenance=provenance,
        )
        self._nodes[node_id] = node
        return node

    # -- edges -----------------------------------------------------------
    def add_edge(
        self,
        edge_id: str,
        type: str,
        source: str,
        target: str,
        *,
        weight: float = 1.0,
        attributes: Mapping[str, object] | None = None,
        provenance: Provenance,
    ) -> Edge:
        if type not in self.schema.edge_types:
            raise GraphError(f"unknown edge type {type!r}")
        if source not in self._nodes:
            raise GraphError(f"edge source {source!r} is not a node")
        if target not in self._nodes:
            raise GraphError(f"edge target {target!r} is not a node")
        if edge_id in self._edges:
            raise GraphError(f"duplicate edge_id {edge_id!r}")
        edge = Edge(
            edge_id=edge_id,
            type=type,
            source=source,
            target=target,
            weight=float(weight),
            attributes=dict(attributes or {}),
            provenance=provenance,
        )
        self._edges[edge_id] = edge
        return edge

    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def edges(self) -> list[Edge]:
        return list(self._edges.values())

    def snapshot(self, *, snapshot_id: str | None = None) -> GraphSnapshot:
        return GraphSnapshot.build(
            schema=self.schema,
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            snapshot_id=snapshot_id,
        )


class GraphSnapshot:
    """An immutable, content-addressed view of a graph at a point in time."""

    def __init__(
        self,
        schema: GraphSchema,
        nodes: tuple[Node, ...],
        edges: tuple[Edge, ...],
        content_hash: str,
        snapshot_id: str | None = None,
    ) -> None:
        self._schema = schema
        self._nodes = nodes
        self._edges = edges
        self._content_hash = content_hash
        self._snapshot_id = snapshot_id or content_hash

    @property
    def schema(self) -> GraphSchema:
        return self._schema

    @property
    def nodes(self) -> tuple[Node, ...]:
        return self._nodes

    @property
    def edges(self) -> tuple[Edge, ...]:
        return self._edges

    @property
    def content_hash(self) -> str:
        return self._content_hash

    @property
    def snapshot_id(self) -> str:
        return self._snapshot_id

    @classmethod
    def build(
        cls,
        *,
        schema: GraphSchema,
        nodes: list[Node],
        edges: list[Edge],
        snapshot_id: str | None = None,
    ) -> GraphSnapshot:
        cls._validate(schema, nodes, edges)
        ordered_nodes = tuple(sorted(nodes, key=lambda n: n.node_id))
        ordered_edges = tuple(sorted(edges, key=lambda e: e.edge_id))
        content_hash = cls._hash(schema, ordered_nodes, ordered_edges)
        return cls(schema, ordered_nodes, ordered_edges, content_hash, snapshot_id)

    @staticmethod
    def _validate(schema: GraphSchema, nodes: list[Node], edges: list[Edge]) -> None:
        node_ids = set()
        for n in nodes:
            if n.type not in schema.node_types:
                raise GraphError(f"node {n.node_id!r} has unknown type {n.type!r}")
            for dim in n.dimensions:
                if dim not in schema.dimensions:
                    raise GraphError(f"node {n.node_id!r} has unknown dimension {dim!r}")
            if n.node_id in node_ids:
                raise GraphError(f"duplicate node_id {n.node_id!r}")
            node_ids.add(n.node_id)
        edge_ids = set()
        for e in edges:
            if e.type not in schema.edge_types:
                raise GraphError(f"edge {e.edge_id!r} has unknown type {e.type!r}")
            if e.source not in node_ids or e.target not in node_ids:
                raise GraphError(f"edge {e.edge_id!r} references missing node")
            if e.edge_id in edge_ids:
                raise GraphError(f"duplicate edge_id {e.edge_id!r}")
            edge_ids.add(e.edge_id)

    @staticmethod
    def _canonical_payload(
        schema: GraphSchema, nodes: tuple[Node, ...], edges: tuple[Edge, ...]
    ) -> dict[str, object]:
        return {
            "schema": schema.to_dict(),
            "schema_version": schema.version,
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }

    @classmethod
    def _hash(
        cls, schema: GraphSchema, nodes: tuple[Node, ...], edges: tuple[Edge, ...]
    ) -> str:
        payload = cls._canonical_payload(schema, nodes, edges)
        # Exclude provenance timestamps from the identity hash so that two
        # structurally identical graphs are equal regardless of creation time,
        # but keep provenance in the serialised form.
        for coll in ("nodes", "edges"):
            for item in payload[coll]:
                item["provenance"] = {
                    k: v for k, v in item["provenance"].items() if k != "created_at"
                }
        blob = cls.to_canonical_json_static(payload)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    @staticmethod
    def to_canonical_json_static(payload: Mapping[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def to_canonical_json(self) -> str:
        payload = self._canonical_payload(self._schema, self._nodes, self._edges)
        payload["snapshot_id"] = self._snapshot_id
        payload["content_hash"] = self._content_hash
        return self.to_canonical_json_static(payload)

    def to_dict(self) -> dict[str, object]:
        return json.loads(self.to_canonical_json())

    def node_matrix(self, dimensions: list[str] | None = None) -> tuple[list[str], list[list[float]]]:
        """Return (node_ids, matrix) with one row per node over ``dimensions``.

        Deterministic node order (sorted by node_id) and dimension order.
        """
        dims = sorted(dimensions) if dimensions else sorted(self._schema.dimensions)
        ids = [n.node_id for n in self._nodes]
        matrix = [[float(n.dimensions.get(d, 0.0)) for d in dims] for n in self._nodes]
        return ids, matrix

    def adjacency(self) -> tuple[list[str], list[list[float]]]:
        """Symmetric weighted adjacency matrix over sorted node ids."""
        ids = [n.node_id for n in self._nodes]
        index = {nid: i for i, nid in enumerate(ids)}
        n = len(ids)
        adj = [[0.0] * n for _ in range(n)]
        for e in self._edges:
            i, j = index[e.source], index[e.target]
            adj[i][j] += e.weight
            if i != j:
                # Self-loops touch a single diagonal cell; adding twice would
                # double-count the weight.
                adj[j][i] += e.weight
        return ids, adj
