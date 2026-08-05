"""FastAPI router exposing the meta-neural vertical slice (local-only).

Mounts under ``/meta``. The endpoints mirror the pipeline steps. Every
privileged step is consent-gated inside :class:`MetaNeuralService`; unsafe paths
(missing/mismatched/absent consent) return HTTP 403.

This router is intentionally not auto-mounted anywhere with network exposure.
:func:`create_app` builds a standalone local app for development and tests.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException

from .consent import ConsentError, Purpose
from .pipeline import MetaNeuralService
from .schemas import (
    ActivateRequest,
    ActivationReportResponse,
    AssociateRequest,
    AuditEventResponse,
    AuditTrailResponse,
    ConsentGrantRequest,
    ConsentGrantResponse,
    ConvergenceResponse,
    IngestRequest,
    OptimizeRequest,
    OptimizeResponse,
    SnapshotResponse,
)

router = APIRouter(prefix="/meta", tags=["meta-neural"])

# A single local service instance backs the router (local-only, in-memory).
_service = MetaNeuralService()


def get_service() -> MetaNeuralService:
    return _service


@router.post("/consent", response_model=ConsentGrantResponse)
def grant_consent(req: ConsentGrantRequest) -> ConsentGrantResponse:
    try:
        grant = get_service().grant_consent(
            req.subject_id, Purpose(req.purpose), retention_days=req.retention_days
        )
    except (ConsentError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ConsentGrantResponse(**grant.to_public_dict())


@router.post("/ingest", response_model=SnapshotResponse)
def ingest(req: IngestRequest) -> SnapshotResponse:
    svc = get_service()
    try:
        snapshot = svc.ingest(
            req.subject_id,
            req.grant_id,
            [n.model_dump() for n in req.nodes],
            [e.model_dump() for e in req.edges],
        )
    except ConsentError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:  # graph validation errors
        raise HTTPException(status_code=400, detail=str(exc))
    return SnapshotResponse(
        snapshot_id=snapshot.snapshot_id,
        content_hash=snapshot.content_hash,
        schema_version=snapshot.schema.version,
        node_count=len(snapshot.nodes),
        edge_count=len(snapshot.edges),
    )


@router.post("/activate", response_model=ActivationReportResponse)
def activate(req: ActivateRequest) -> ActivationReportResponse:
    try:
        report = get_service().activate(
            req.subject_id, req.grant_id, req.activations, steps=req.steps
        )
    except ConsentError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ActivationReportResponse(**report.to_dict())


@router.post("/associate", response_model=ConvergenceResponse)
def associate(req: AssociateRequest) -> ConvergenceResponse:
    svc = get_service()
    try:
        svc.associate(req.subject_id, req.grant_id)
        result = svc.analyze_convergence(req.subject_id, req.grant_id)
    except ConsentError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ConvergenceResponse(**result.to_dict())


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest) -> OptimizeResponse:
    try:
        result = get_service().optimize(
            req.subject_id,
            req.grant_id,
            selection_dimension=req.selection_dimension,
            cardinality=req.cardinality,
            backend=req.backend,
            seed=req.seed,
            steps=req.steps,
        )
    except ConsentError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    d = result.to_dict()
    return OptimizeResponse(
        objective=d["objective"],
        assignment=d["assignment"],
        backend=d["backend"],
        seed=d["seed"],
        steps=d["steps"],
        constraints=d["constraints"],
        source_snapshot=d["source_snapshot"],
        note=d["note"],
    )


@router.get("/audit/{subject_id}", response_model=AuditTrailResponse)
def audit_trail(subject_id: str, grant_id: str) -> AuditTrailResponse:
    try:
        valid, events = get_service().audit_trail(subject_id, grant_id)
    except ConsentError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return AuditTrailResponse(
        chain_valid=valid,
        events=[AuditEventResponse(**{k: v for k, v in e.to_dict().items()
                                      if k not in ("prev_hash", "event_hash")})
                for e in events],
    )


def create_app() -> FastAPI:
    """Build a standalone local-only FastAPI app mounting the meta router."""
    app = FastAPI(title="Fusion Hero OS — Meta-Neural Slice (local-only)")
    app.include_router(router)
    return app
