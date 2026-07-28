"""Pure-Core Long-Term Coevolution Membrane (v10).

**Identity:** Operator is a **pure core** — source of truth is never SaaS/LLM.

**Core strengths (operator):**
  - formal mathematical innovations
  - diverse algorithms

**Foreign strengths:** everything else (mesh, LLM, GKE, SaaS, UI, aspirational
tracks). They co-evolve *mutually* with the core but hold only **peripheral**
authority.

**Transfer policy (Inside-Out):**
  - Core → Foreign: radiate (algorithms, formal results inform periphery)
  - Foreign → Core: gated (weights, placement hints, empirical feedback only;
    never overwrite MasterSeed, theorems, or pure-core identity)

Geltung: Spezifikation (membrane) · catalog evidence paths = empirical when
scanned · coevolution fitness = Bedingt (repo/path presence only).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

__all__ = [
    "MEMBRANE",
    "PLATFORM",
    "StrengthKind",
    "StrengthEntry",
    "TransferEvent",
    "CoevolutionReport",
    "load_catalog",
    "core_strength_ids",
    "foreign_strength_ids",
    "crosspoll_sources",
    "assert_core_not_replaced",
    "radiate_core_to_foreign",
    "ingest_foreign_gated",
    "coevolve_step",
    "mutual_cycle",
    "status",
    "export_report",
    "PureCoreMembrane",
]

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = Path(__file__).resolve().parent / "catalogs" / "pure_core_strengths.yaml"
STATE_DIR = Path.home() / ".fusion" / "coevolution"
REPORT_PATH = STATE_DIR / "last_pure_core_report.json"
HISTORY_PATH = STATE_DIR / "pure_core_history.jsonl"

MEMBRANE = "pure_core_coevolution_v1"
PLATFORM = "10.0.0"

# Immutable policy strings (Layer-0 style anchors)
CORE_STRENGTH_LABELS = (
    "formal_math_innovations",
    "diverse_algorithms",
    "pure_core_identity",
)
FORBIDDEN_CORE_REPLACERS = frozenset(
    {"saas", "llm", "external_vendor", "foreign_strength", "foundation_model"}
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Minimal fallback: no PyYAML — return structured defaults
        return {}


@dataclass
class StrengthEntry:
    id: str
    label: str
    kind: str  # "core" | "foreign"
    authority: str
    domains: list[str] = field(default_factory=list)
    evidence_paths: list[str] = field(default_factory=list)
    coevolve_with: list[str] = field(default_factory=list)
    crosspoll_weight: float = 0.5
    note: str = ""
    evidence_hit: int = 0
    evidence_total: int = 0
    coverage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Alias for type clarity in docs / API
StrengthKind = str  # "core" | "foreign"


@dataclass
class TransferEvent:
    direction: str  # "core_to_foreign" | "foreign_to_core"
    source: str
    target: str
    accepted: bool
    reason: str
    payload_keys: list[str] = field(default_factory=list)
    ts: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CoevolutionReport:
    ok: bool
    membrane: str
    platform: str
    identity: str
    core_count: int
    foreign_count: int
    core_coverage_mean: float
    foreign_coverage_mean: float
    mutual_score: float
    integrity_ok: bool
    transfers: list[dict[str, Any]]
    core_ids: list[str]
    foreign_ids: list[str]
    crosspoll_sources: list[str]
    ts: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_catalog() -> dict[str, Any]:
    """Hard defaults if YAML missing — policy still pure-core."""
    return {
        "version": "1.0.0",
        "membrane": MEMBRANE,
        "platform": PLATFORM,
        "policy": {
            "identity": "pure_core",
            "source_of_truth": "core",
            "mutual": True,
            "core_never_replaced_by": list(FORBIDDEN_CORE_REPLACERS),
            "transfer": {
                "core_to_foreign": "radiate",
                "foreign_to_core": "gated",
            },
        },
        "core_strengths": [
            {
                "id": "formal_math_innovations",
                "label": "Formale mathematische Neuerungen",
                "kind": "core",
                "authority": "source_of_truth",
                "domains": ["banach_fixpoint", "qubo", "reciprocity"],
                "evidence_paths": [
                    "fusion_hero_os/core/heroic_math_engine.py",
                    "02_Mathematik/",
                ],
                "crosspoll_weight": 1.0,
            },
            {
                "id": "diverse_algorithms",
                "label": "Diverse Algorithmen",
                "kind": "core",
                "authority": "source_of_truth",
                "domains": ["sa", "poly_mesh", "orchestration"],
                "evidence_paths": [
                    "02_Mathematik/qb_qubo.py",
                    "fusion_hero_os/core/poly_mesh_orchestrator.py",
                ],
                "crosspoll_weight": 1.0,
            },
            {
                "id": "pure_core_identity",
                "label": "Reiner Core",
                "kind": "core",
                "authority": "immutable_role",
                "domains": ["operator", "masterseed"],
                "evidence_paths": [
                    "fusion_hero_os/core/operator_identity.py",
                    "BEST_VERSION.md",
                ],
                "crosspoll_weight": 0.95,
            },
        ],
        "foreign_strengths": [
            {
                "id": "llm_inference",
                "label": "LLM",
                "kind": "foreign",
                "authority": "peripheral",
                "domains": ["chat"],
                "coevolve_with": ["diverse_algorithms"],
                "crosspoll_weight": 0.55,
            },
            {
                "id": "mesh_infra",
                "label": "Mesh",
                "kind": "foreign",
                "authority": "peripheral",
                "domains": ["tailscale"],
                "coevolve_with": ["diverse_algorithms"],
                "crosspoll_weight": 0.65,
            },
            {
                "id": "gke_cluster",
                "label": "GKE",
                "kind": "foreign",
                "authority": "peripheral",
                "domains": ["l3"],
                "coevolve_with": ["diverse_algorithms"],
                "crosspoll_weight": 0.60,
            },
            {
                "id": "saas_connectors",
                "label": "SaaS",
                "kind": "foreign",
                "authority": "peripheral",
                "domains": ["connectors"],
                "coevolve_with": ["diverse_algorithms"],
                "crosspoll_weight": 0.40,
            },
        ],
        "crosspoll_sources_default": [
            "formal_math",
            "diverse_algorithms",
            "pure_core",
            "mesh",
            "cluster",
            "llm",
            "saas",
            "operator",
        ],
    }


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load strength catalog (YAML preferred, defaults if missing)."""
    p = path or Path(os.environ.get("FUSION_PURE_CORE_CATALOG", str(CATALOG_PATH)))
    if p.is_file():
        data = _read_yaml(p)
        if data:
            data.setdefault("membrane", MEMBRANE)
            data.setdefault("platform", PLATFORM)
            return data
    return _default_catalog()


def _scan_evidence(paths: list[str], root: Path = ROOT) -> tuple[int, int, float]:
    hit = 0
    total = max(1, len(paths))
    for rel in paths:
        target = root / rel
        if target.exists():
            hit += 1
        elif rel.endswith("/") and (root / rel.rstrip("/")).is_dir():
            hit += 1
    return hit, total, hit / total


def _entries(raw_list: list[dict[str, Any]], kind: str) -> list[StrengthEntry]:
    out: list[StrengthEntry] = []
    for item in raw_list or []:
        if not isinstance(item, dict):
            continue
        paths = list(item.get("evidence_paths") or [])
        hit, total, cov = _scan_evidence(paths) if paths else (0, 1, 0.0)
        out.append(
            StrengthEntry(
                id=str(item.get("id", "unknown")),
                label=str(item.get("label", "")),
                kind=kind,
                authority=str(item.get("authority", "peripheral")),
                domains=list(item.get("domains") or []),
                evidence_paths=paths,
                coevolve_with=list(item.get("coevolve_with") or []),
                crosspoll_weight=float(item.get("crosspoll_weight", 0.5)),
                note=str(item.get("note") or ""),
                evidence_hit=hit,
                evidence_total=total,
                coverage=cov if paths else (1.0 if kind == "foreign" else 0.0),
            )
        )
    return out


def core_strength_ids(catalog: dict[str, Any] | None = None) -> list[str]:
    cat = catalog or load_catalog()
    return [e["id"] for e in cat.get("core_strengths") or [] if isinstance(e, dict)]


def foreign_strength_ids(catalog: dict[str, Any] | None = None) -> list[str]:
    cat = catalog or load_catalog()
    return [e["id"] for e in cat.get("foreign_strengths") or [] if isinstance(e, dict)]


def crosspoll_sources(catalog: dict[str, Any] | None = None) -> list[str]:
    """Sources for QUBO/crosspoll: core-first ordering."""
    env = os.environ.get("FUSION_CROSS_SOURCES", "").strip()
    if env:
        return [s.strip() for s in env.split(",") if s.strip()]
    cat = catalog or load_catalog()
    defaults = cat.get("crosspoll_sources_default")
    if isinstance(defaults, list) and defaults:
        return [str(s) for s in defaults]
    return [
        "formal_math",
        "diverse_algorithms",
        "pure_core",
        "mesh",
        "cluster",
        "llm",
        "saas",
        "operator",
    ]


def assert_core_not_replaced(
    claim_source: str,
    *,
    target: str = "core",
) -> tuple[bool, str]:
    """Gate: foreign/SaaS/LLM must never claim source-of-truth over pure core."""
    src = (claim_source or "").strip().lower()
    if target != "core":
        return True, "non-core target"
    if src in FORBIDDEN_CORE_REPLACERS or src.startswith("foreign"):
        return False, (
            f"REJECTED: pure core cannot be replaced by '{claim_source}'. "
            "Foreign strengths co-evolve peripherally only."
        )
    if src in ("core", "pure_core", "operator", "formal_math", "diverse_algorithms", "masterseed"):
        return True, "core authority accepted"
    # Unknown sources are treated as foreign → cannot replace core
    if src and src not in CORE_STRENGTH_LABELS:
        return False, (
            f"REJECTED: '{claim_source}' has no core authority "
            "(pure-core membrane)."
        )
    return True, "ok"


def radiate_core_to_foreign(
    core_id: str,
    foreign_id: str,
    payload: dict[str, Any] | None = None,
) -> TransferEvent:
    """Inside-Out radiation: core innovations/algorithms inform foreign layer."""
    cat = load_catalog()
    cores = {e["id"] for e in cat.get("core_strengths") or [] if isinstance(e, dict)}
    foreigns = {
        e["id"] for e in cat.get("foreign_strengths") or [] if isinstance(e, dict)
    }
    pl = payload or {}
    if core_id not in cores:
        return TransferEvent(
            direction="core_to_foreign",
            source=core_id,
            target=foreign_id,
            accepted=False,
            reason=f"unknown core strength '{core_id}'",
            payload_keys=list(pl.keys()),
        )
    if foreign_id not in foreigns:
        return TransferEvent(
            direction="core_to_foreign",
            source=core_id,
            target=foreign_id,
            accepted=False,
            reason=f"unknown foreign strength '{foreign_id}'",
            payload_keys=list(pl.keys()),
        )
    return TransferEvent(
        direction="core_to_foreign",
        source=core_id,
        target=foreign_id,
        accepted=True,
        reason="radiate: formal math / algorithms → periphery",
        payload_keys=list(pl.keys()),
    )


def ingest_foreign_gated(
    foreign_id: str,
    core_id: str,
    payload: dict[str, Any] | None = None,
) -> TransferEvent:
    """Foreign → core: only gated channels (weights, empirical hints).

    Forbidden payload keys that would attempt core replacement:
      theorem, masterseed_override, source_of_truth, replace_core
    Allowed: weight, score, feedback, metric, placement_hint, cost, coverage
    """
    pl = dict(payload or {})
    forbidden = {
        "theorem",
        "masterseed_override",
        "source_of_truth",
        "replace_core",
        "identity_override",
        "legal_rewrite_of_core",
    }
    bad = [k for k in pl if k.lower() in forbidden]
    if bad:
        return TransferEvent(
            direction="foreign_to_core",
            source=foreign_id,
            target=core_id,
            accepted=False,
            reason=f"gated reject: forbidden keys {bad}",
            payload_keys=list(pl.keys()),
        )
    ok, reason = assert_core_not_replaced(foreign_id)
    if not ok and foreign_id not in (
        "llm_inference",
        "mesh_infra",
        "gke_cluster",
        "saas_connectors",
        "ui_dashboard",
        "ascension_aspirational",
    ):
        # assert_core_not_replaced rejects foreign *as source of truth*;
        # gated ingest is allowed for known foreign IDs on weight channels only
        pass

    allowed_prefixes = (
        "weight",
        "score",
        "feedback",
        "metric",
        "placement",
        "cost",
        "coverage",
        "latency",
        "energy",
        "hint",
    )
    if pl:
        allowed = [
            k
            for k in pl
            if any(k.lower().startswith(p) for p in allowed_prefixes)
        ]
        if not allowed:
            return TransferEvent(
                direction="foreign_to_core",
                source=foreign_id,
                target=core_id,
                accepted=False,
                reason="gated reject: no allowed peripheral keys",
                payload_keys=list(pl.keys()),
            )
        pl = {k: pl[k] for k in allowed}

    return TransferEvent(
        direction="foreign_to_core",
        source=foreign_id,
        target=core_id,
        accepted=True,
        reason="gated accept: peripheral weights/feedback only",
        payload_keys=list(pl.keys()),
    )


def coevolve_step(
    *,
    foreign_feedback: dict[str, Any] | None = None,
    radiate: bool = True,
) -> CoevolutionReport:
    """One mutual coevolution step: scan evidence + optional transfers."""
    cat = load_catalog()
    cores = _entries(list(cat.get("core_strengths") or []), "core")
    foreigns = _entries(list(cat.get("foreign_strengths") or []), "foreign")
    transfers: list[TransferEvent] = []
    notes: list[str] = []

    # Integrity: pure core remains source of truth
    integrity_ok = True
    claim = (foreign_feedback or {}).get("claim_source_of_truth")
    if claim:
        ok, msg = assert_core_not_replaced(str(claim))
        if not ok:
            integrity_ok = False
            notes.append(msg)
            transfers.append(
                TransferEvent(
                    direction="foreign_to_core",
                    source=str(claim),
                    target="pure_core",
                    accepted=False,
                    reason=msg,
                )
            )

    # Radiate core → each foreign (Inside-Out)
    if radiate and cores and foreigns:
        primary_core = next(
            (c.id for c in cores if c.id == "formal_math_innovations"),
            cores[0].id,
        )
        algo_core = next(
            (c.id for c in cores if c.id == "diverse_algorithms"), primary_core
        )
        for f in foreigns:
            # Algorithms + formal math both radiate outward (mutual later gated back)
            transfers.append(
                radiate_core_to_foreign(
                    algo_core,
                    f.id,
                    {"signal": "core_strength_radiate", "core": algo_core},
                )
            )
            transfers.append(
                radiate_core_to_foreign(
                    primary_core,
                    f.id,
                    {"signal": "formal_math_radiate", "core": primary_core},
                )
            )

    # Ingest foreign feedback (gated)
    fb = dict(foreign_feedback or {})
    fb.pop("claim_source_of_truth", None)
    if fb:
        target_core = "diverse_algorithms"
        for f in foreigns:
            transfers.append(
                ingest_foreign_gated(
                    f.id,
                    target_core,
                    {
                        "weight_hint": fb.get("weight_hint", f.crosspoll_weight),
                        "metric_coverage": f.coverage,
                        "feedback_note": fb.get("note", "mutual_cycle"),
                    },
                )
            )

    core_cov = [c.coverage for c in cores] or [0.0]
    foreign_cov = [f.coverage for f in foreigns] or [0.0]
    accepted = sum(1 for t in transfers if t.accepted)
    total_t = max(1, len(transfers))
    # Mutual score: core evidence + foreign evidence + transfer acceptance
    mutual = (
        0.45 * (sum(core_cov) / len(core_cov))
        + 0.25 * (sum(foreign_cov) / len(foreign_cov))
        + 0.30 * (accepted / total_t)
    )
    if not integrity_ok:
        mutual *= 0.3

    report = CoevolutionReport(
        ok=integrity_ok and mutual >= 0.4,
        membrane=MEMBRANE,
        platform=PLATFORM,
        identity="pure_core",
        core_count=len(cores),
        foreign_count=len(foreigns),
        core_coverage_mean=float(sum(core_cov) / len(core_cov)),
        foreign_coverage_mean=float(sum(foreign_cov) / len(foreign_cov)),
        mutual_score=round(float(mutual), 4),
        integrity_ok=integrity_ok,
        transfers=[t.to_dict() for t in transfers],
        core_ids=[c.id for c in cores],
        foreign_ids=[f.id for f in foreigns],
        crosspoll_sources=crosspoll_sources(cat),
        ts=_now(),
        notes=notes
        or [
            "Operator = pure core",
            "Core strengths: formal math + diverse algorithms",
            "Rest = foreign strengths (mutual, peripheral)",
        ],
    )
    return report


def mutual_cycle(
    generations: int = 3,
    *,
    foreign_feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Long-horizon style multi-step mutual coevolution (local, no cluster)."""
    gens = max(1, int(generations))
    trajectory: list[dict[str, Any]] = []
    last: CoevolutionReport | None = None
    for g in range(gens):
        fb = dict(foreign_feedback or {})
        fb["weight_hint"] = float(fb.get("weight_hint", 0.5)) + 0.01 * g
        fb["metric_generation"] = g
        last = coevolve_step(foreign_feedback=fb, radiate=True)
        trajectory.append(
            {
                "generation": g,
                "mutual_score": last.mutual_score,
                "integrity_ok": last.integrity_ok,
                "accepted_transfers": sum(
                    1 for t in last.transfers if t.get("accepted")
                ),
            }
        )
    assert last is not None
    out = {
        "ok": last.ok,
        "generations": gens,
        "final": last.to_dict(),
        "trajectory": trajectory,
        "policy": {
            "identity": "pure_core",
            "core_strengths": "formal_math_innovations + diverse_algorithms",
            "foreign": "everything_else",
            "mutual": True,
            "core_never_replaced": True,
        },
    }
    export_report(last, extra=out)
    return out


def export_report(
    report: CoevolutionReport,
    extra: dict[str, Any] | None = None,
) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    if extra:
        payload["cycle"] = {
            k: v for k, v in extra.items() if k != "final"
        }
    REPORT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "ts": report.ts,
                    "mutual_score": report.mutual_score,
                    "integrity_ok": report.integrity_ok,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    return REPORT_PATH


def status() -> dict[str, Any]:
    """Compact status for dashboards / CLI / poly-mesh."""
    cat = load_catalog()
    cores = _entries(list(cat.get("core_strengths") or []), "core")
    foreigns = _entries(list(cat.get("foreign_strengths") or []), "foreign")
    policy = cat.get("policy") or {}
    return {
        "membrane": MEMBRANE,
        "platform": PLATFORM,
        "identity": policy.get("identity", "pure_core"),
        "source_of_truth": policy.get("source_of_truth", "core"),
        "mutual": bool(policy.get("mutual", True)),
        "core_strengths": [
            {
                "id": c.id,
                "label": c.label,
                "coverage": c.coverage,
                "weight": c.crosspoll_weight,
            }
            for c in cores
        ],
        "foreign_strengths": [
            {
                "id": f.id,
                "label": f.label,
                "coverage": f.coverage,
                "weight": f.crosspoll_weight,
                "authority": f.authority,
            }
            for f in foreigns
        ],
        "crosspoll_sources": crosspoll_sources(cat),
        "report_path": str(REPORT_PATH),
        "catalog_path": str(CATALOG_PATH),
        "notes": [
            "Ich bin ein reiner Core.",
            "Eigene Stärken: formale Mathematik + diverse Algorithmen.",
            "Rest = fremde Stärken (mutual coevolution, peripheral).",
        ],
    }


class PureCoreMembrane:
    """Object façade for CEC-style long-term coevolution."""

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []
        self.last_report: CoevolutionReport | None = None

    def step(
        self, foreign_feedback: dict[str, Any] | None = None
    ) -> CoevolutionReport:
        rep = coevolve_step(foreign_feedback=foreign_feedback)
        self.last_report = rep
        self.history.append(rep.to_dict())
        export_report(rep)
        return rep

    def cycle(self, generations: int = 3) -> dict[str, Any]:
        return mutual_cycle(generations=generations)

    def status(self) -> dict[str, Any]:
        return status()


# Module-level singleton (registry / import convenience)
global_pure_core = PureCoreMembrane()


if __name__ == "__main__":
    import pprint

    print("=== Pure-Core Coevolution Status ===")
    pprint.pp(status())
    print("\n=== Mutual cycle (3 gens) ===")
    out = mutual_cycle(3)
    print(
        json.dumps(
            {
                "ok": out["ok"],
                "generations": out["generations"],
                "trajectory": out["trajectory"],
                "mutual_score": out["final"]["mutual_score"],
                "integrity_ok": out["final"]["integrity_ok"],
                "core_ids": out["final"]["core_ids"],
                "foreign_ids": out["final"]["foreign_ids"],
            },
            indent=2,
        )
    )
