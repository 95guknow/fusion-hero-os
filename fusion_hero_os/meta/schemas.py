# -*- coding: utf-8 -*-
"""Typed API contract models for the meta-neural vertical slice.

These pydantic models are the single source of truth for the request/response
contract. The TypeScript types in ``src/lib/meta/contracts.ts`` mirror them.
No field here carries personal data — subjects are opaque ids only.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ConsentGrantRequest(BaseModel):
    subject_id: str = Field(..., description="Opaque subject id (no PII).")
    purpose: str = Field(..., description="One of the Purpose enum values.")
    retention_days: int = Field(30, ge=1, le=3650)


class ConsentGrantResponse(BaseModel):
    grant_id: str
    subject_id: str
    purpose: str
    granted_at: str
    expires_at: str
    revoked_at: Optional[str] = None
    active: bool


class NodeFixture(BaseModel):
    node_id: str
    type: str
    dimensions: Dict[str, float] = Field(default_factory=dict, max_length=256)
    attributes: Dict[str, object] = Field(default_factory=dict, max_length=256)


class EdgeFixture(BaseModel):
    edge_id: str
    type: str
    source: str
    target: str
    weight: float = 1.0


# Bounds below guard against a single request driving an unbounded, synchronous
# O(n^2)-ish QUBO build/solve (see pipeline.optimize / qubo_bridge.build_qubo).
# Not a product limit — a resource-exhaustion backstop for this local slice.
class IngestRequest(BaseModel):
    subject_id: str
    grant_id: str
    nodes: List[NodeFixture] = Field(default_factory=list, max_length=2000)
    edges: List[EdgeFixture] = Field(default_factory=list, max_length=4000)


class SnapshotResponse(BaseModel):
    snapshot_id: str
    content_hash: str
    schema_version: str
    node_count: int
    edge_count: int


class ActivateRequest(BaseModel):
    subject_id: str
    grant_id: str
    activations: Dict[str, float] = Field(default_factory=dict, max_length=2000)
    steps: int = Field(1, ge=0, le=1000)


class ActivationReportResponse(BaseModel):
    step_index: int
    capacity: float
    decay: float
    active: List[Dict[str, object]]


class AssociateRequest(BaseModel):
    subject_id: str
    grant_id: str


class ConvergenceResponse(BaseModel):
    is_contraction: bool
    lipschitz_bound: float
    spectral_radius: float
    norm_order: str
    note: str


class OptimizeRequest(BaseModel):
    subject_id: str
    grant_id: str
    selection_dimension: str = "salience"
    cardinality: Optional[int] = None
    backend: str = "numpy"
    seed: int = 7
    steps: int = Field(2000, ge=1, le=200000)


class OptimizeResponse(BaseModel):
    objective: float
    assignment: Dict[str, int]
    backend: str
    seed: int
    steps: int
    constraints: Dict[str, object]
    source_snapshot: str
    note: str


class AuditEventResponse(BaseModel):
    seq: int
    event_id: str
    timestamp: str
    action: str
    subject_id: Optional[str]
    purpose: Optional[str]
    decision: str
    detail: Dict[str, object]


class AuditTrailResponse(BaseModel):
    chain_valid: bool
    events: List[AuditEventResponse]
