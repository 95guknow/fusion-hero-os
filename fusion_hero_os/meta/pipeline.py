"""End-to-end orchestration of the meta-neural vertical slice.

Flow (each step fails closed on missing consent):

    consent grant -> ingest neutral fixture -> activate working memory
    -> update associations -> analyze coupling/convergence -> optimize
    -> retrieve audit trail

The :class:`MetaNeuralService` ties together consent, the property graph,
working memory, Hebbian memory, coupling analysis and the QUBO bridge. It is
local-only and holds all state in memory. Persistence hooks are explicit and
also consent-gated.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)

import numpy as np

from .consent import ConsentError, ConsentStore, Purpose
from .coupling import ContractionResult, is_contraction
from .graph import GraphSchema, GraphSnapshot, PropertyGraph, Provenance
from .hebbian import HebbianAssociationMemory, HebbianConfig
from .qubo_bridge import QUBOResult, build_qubo, solve_qubo
from .working_memory import ActivationReport, WorkingMemorySpace

DEFAULT_SCHEMA = GraphSchema(
    version="1.0.0",
    node_types=frozenset({"concept", "subject", "artifact"}),
    edge_types=frozenset({"relates_to", "derived_from", "associates"}),
    dimensions=frozenset({"salience", "valence", "recency"}),
)


class MetaNeuralService:
    """In-memory, consent-scoped orchestration of the slice."""

    def __init__(
        self,
        *,
        schema: GraphSchema = DEFAULT_SCHEMA,
        consent_store: ConsentStore | None = None,
        wm_capacity: float = 1.0,
        wm_decay: float = 0.9,
        admin_token: str | None = None,
    ) -> None:
        self.schema = schema
        self.consent = consent_store or ConsentStore()
        self._graphs: dict[str, PropertyGraph] = {}
        self._snapshots: dict[str, GraphSnapshot] = {}
        self._wm: dict[str, WorkingMemorySpace] = {}
        self._hebbian: dict[str, HebbianAssociationMemory] = {}
        self._wm_capacity = wm_capacity
        self._wm_decay = wm_decay
        # Cross-subject audit reads require this explicit admin capability.
        # Disabled (None) by default and never exposed over the HTTP API.
        self._admin_token = admin_token
        # Guards the per-subject state maps against concurrent mutation from
        # the process-wide service singleton.
        self._lock = threading.RLock()

    # -- consent ---------------------------------------------------------
    def grant_consent(self, subject_id: str, purpose: Purpose,
                      retention_days: int = 30):
        return self.consent.grant(
            subject_id, Purpose(purpose), retention=timedelta(days=retention_days)
        )

    def _require(self, subject_id: str, grant_id: str, purpose: Purpose, action: str):
        # Single audit decision (granted XOR denied); a grant_id mismatch is a
        # single ``denied`` event rather than a misleading granted->denied pair.
        return self.consent.authorize(
            subject_id, Purpose(purpose), action=action, expected_grant_id=grant_id
        )

    # -- erasure / retention --------------------------------------------
    def _purge_subject_state(
        self, subject_id: str, *, reason: str, at: datetime | None = None
    ) -> dict[str, int]:
        """Deterministically remove all in-memory state for ``subject_id``.

        Drops the property graph, the cached snapshot, the working-memory space
        and the Hebbian association memory (the secondary indexes/caches). A
        minimal, non-PII deletion tombstone is appended to the audit log as
        lawful evidence that erasure occurred; no subject content is retained.
        """
        with self._lock:
            counts = {
                "graph": 1 if self._graphs.pop(subject_id, None) is not None else 0,
                "snapshot": 1 if self._snapshots.pop(subject_id, None) is not None else 0,
                "working_memory": 1 if self._wm.pop(subject_id, None) is not None else 0,
                "hebbian": 1 if self._hebbian.pop(subject_id, None) is not None else 0,
            }
        self.consent.audit.append(
            "subject.purge", decision="n/a", subject_id=subject_id,
            purpose=None, detail={"reason": reason, "removed": counts}, at=at,
        )
        return counts

    def revoke_consent(
        self, subject_id: str, grant_id: str, *, at: datetime | None = None
    ) -> dict[str, int]:
        """Revoke a grant and immediately purge the subject's derived state."""
        self.consent.revoke(grant_id, at=at)
        return self._purge_subject_state(subject_id, reason="revocation", at=at)

    def _purge_if_expired(
        self, subject_id: str, *, at: datetime | None = None
    ) -> dict[str, int]:
        """Purge a subject's state if no consent grant remains active.

        Called before privileged reads/writes so expiry (not just explicit
        revocation) deterministically triggers erasure of derived state.
        """
        at = at or datetime.now(tz=UTC)
        with self._lock:
            has_state = subject_id in self._graphs or subject_id in self._wm
        if not has_state:
            return {}
        active = any(
            self.consent.find_active(subject_id, p, at=at) is not None
            for p in Purpose
        )
        if active:
            return {}
        return self._purge_subject_state(subject_id, reason="expiry", at=at)

    def sweep_expired(self, *, at: datetime | None = None) -> dict[str, dict[str, int]]:
        """Purge every subject whose consent has fully expired/been revoked."""
        with self._lock:
            subjects = set(self._graphs) | set(self._wm) | set(self._hebbian)
        removed: dict[str, dict[str, int]] = {}
        for sid in subjects:
            counts = self._purge_if_expired(sid, at=at)
            if counts:
                removed[sid] = counts
        return removed

    # -- ingest ----------------------------------------------------------
    def ingest(
        self,
        subject_id: str,
        grant_id: str,
        nodes: list[dict],
        edges: list[dict],
    ) -> GraphSnapshot:
        self._purge_if_expired(subject_id)
        grant = self._require(subject_id, grant_id, Purpose.INGEST, "graph.ingest")
        graph = PropertyGraph(self.schema)
        prov = Provenance.now("meta.pipeline", purpose=Purpose.INGEST.value,
                              grant_id=grant.grant_id)
        for nd in nodes:
            graph.add_node(
                nd["node_id"], nd["type"],
                dimensions=nd.get("dimensions"),
                attributes=nd.get("attributes"),
                provenance=prov,
            )
        for ed in edges:
            graph.add_edge(
                ed["edge_id"], ed["type"], ed["source"], ed["target"],
                weight=ed.get("weight", 1.0),
                attributes=ed.get("attributes"),
                provenance=prov,
            )
        snapshot = graph.snapshot()
        # working memory slots = node ids (opaque)
        node_ids = [n.node_id for n in graph.nodes()]
        with self._lock:
            self._graphs[subject_id] = graph
            self._snapshots[subject_id] = snapshot
            self._wm[subject_id] = WorkingMemorySpace(
                node_ids, capacity=self._wm_capacity, decay=self._wm_decay
            )
            self._hebbian[subject_id] = HebbianAssociationMemory(HebbianConfig())
        self.consent.audit.append(
            "graph.snapshot", decision="granted", subject_id=subject_id,
            purpose=Purpose.INGEST.value,
            detail={"snapshot": snapshot.content_hash,
                    "nodes": len(node_ids), "edges": len(graph.edges())},
        )
        return snapshot

    def snapshot_for(self, subject_id: str) -> GraphSnapshot:
        if subject_id not in self._snapshots:
            raise KeyError(f"no snapshot for subject {subject_id!r}")
        return self._snapshots[subject_id]

    # -- working memory --------------------------------------------------
    def activate(
        self,
        subject_id: str,
        grant_id: str,
        activations: dict[str, float],
        steps: int = 1,
    ) -> ActivationReport:
        self._purge_if_expired(subject_id)
        self._require(subject_id, grant_id, Purpose.WORKING_MEMORY, "wm.activate")
        with self._lock:
            wm = self._wm[subject_id]
            for slot, amount in activations.items():
                wm.activate(slot, amount)
            for _ in range(steps):
                wm.step()
            report = wm.report()
        self.consent.audit.append(
            "wm.report", decision="granted", subject_id=subject_id,
            purpose=Purpose.WORKING_MEMORY.value,
            detail={"active_count": len(report.active), "step_index": report.step_index},
        )
        return report

    # -- associations ----------------------------------------------------
    def associate(self, subject_id: str, grant_id: str) -> HebbianAssociationMemory:
        """Update Hebbian weights from current working-memory co-activations."""
        self._purge_if_expired(subject_id)
        self._require(subject_id, grant_id, Purpose.ASSOCIATION, "assoc.update")
        with self._lock:
            wm = self._wm[subject_id]
            heb = self._hebbian[subject_id]
            slots = wm.slots
            acts = wm.vector()
            for i in range(len(slots)):
                for j in range(i + 1, len(slots)):
                    if acts[i] != 0.0 and acts[j] != 0.0:
                        heb.update(slots[i], slots[j], acts[i], acts[j])
        self.consent.audit.append(
            "assoc.update", decision="granted", subject_id=subject_id,
            purpose=Purpose.ASSOCIATION.value,
            detail={"pairs": len(heb)},
        )
        return heb

    # -- coupling / convergence -----------------------------------------
    def analyze_convergence(
        self, subject_id: str, grant_id: str
    ) -> ContractionResult:
        """Treat association-weighted decay dynamics as a linear map and test it.

        Dynamics: ``x_{k+1} = decay * (I + A) x`` where ``A`` is the (scaled)
        association matrix. The Jacobian is constant (linear), so the
        contractivity test is exact for this map.
        """
        self._purge_if_expired(subject_id)
        self._require(subject_id, grant_id, Purpose.ASSOCIATION, "coupling.analyze")
        with self._lock:
            wm = self._wm[subject_id]
            heb = self._hebbian[subject_id]
            slots = wm.slots
        _, A = heb.to_matrix(slots)
        A = np.asarray(A, dtype=np.float64)
        n = A.shape[0]
        J = wm.decay * (np.eye(n) + A)
        result = is_contraction(J, norm_order="inf")
        self.consent.audit.append(
            "coupling.analyze", decision="granted", subject_id=subject_id,
            purpose=Purpose.ASSOCIATION.value,
            detail=result.to_dict(),
        )
        return result

    # -- optimize --------------------------------------------------------
    def optimize(
        self,
        subject_id: str,
        grant_id: str,
        *,
        selection_dimension: str = "salience",
        cardinality: int | None = None,
        backend: str = "numpy",
        seed: int = 7,
        steps: int = 2000,
    ) -> QUBOResult:
        self._purge_if_expired(subject_id)
        self._require(subject_id, grant_id, Purpose.OPTIMIZATION, "qubo.optimize")
        with self._lock:
            snapshot = self.snapshot_for(subject_id)
            heb = self._hebbian.get(subject_id)
        assoc = heb.to_matrix([n.node_id for n in snapshot.nodes]) if heb else None
        problem = build_qubo(
            snapshot,
            selection_dimension=selection_dimension,
            association=assoc,
            cardinality=cardinality,
        )
        result = solve_qubo(problem, backend=backend, seed=seed, steps=steps)
        self.consent.audit.append(
            "qubo.optimize", decision="granted", subject_id=subject_id,
            purpose=Purpose.OPTIMIZATION.value,
            detail={
                "objective": round(result.objective, 12),
                "backend": result.backend,
                "seed": result.seed,
                "source_snapshot": result.source_snapshot,
            },
        )
        return result

    # -- audit -----------------------------------------------------------
    def audit_trail(
        self,
        subject_id: str,
        grant_id: str,
        *,
        include_all: bool = False,
        admin_token: str | None = None,
    ) -> tuple[bool, list]:
        """Return ``(chain_intact, events)`` scoped to ``subject_id``.

        By default a subject with AUDIT_READ sees only its own records. A
        cross-subject (global) read is a distinct administrative capability: it
        requires ``include_all=True`` *and* a matching ``admin_token`` that was
        configured out-of-band at construction. The capability is disabled when
        no admin token is set and is never plumbed through the HTTP API.
        """
        self._require(subject_id, grant_id, Purpose.AUDIT_READ, "audit.read")
        intact = self.consent.audit.verify()
        if include_all:
            if self._admin_token is None or admin_token != self._admin_token:
                self.consent.audit.append(
                    "audit.read_all", decision="denied", subject_id=subject_id,
                    purpose=Purpose.AUDIT_READ.value,
                    detail={"reason": "admin capability required for cross-subject read"},
                )
                raise ConsentError("cross-subject audit read requires the admin capability")
            self.consent.audit.append(
                "audit.read_all", decision="granted", subject_id=subject_id,
                purpose=Purpose.AUDIT_READ.value, detail={"scope": "all"},
            )
            return intact, self.consent.audit.events()
        return intact, self.consent.audit.events_for(subject_id)
