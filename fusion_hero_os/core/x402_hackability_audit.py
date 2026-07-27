"""
x402 Foundation protocol — defensive hackability audit via Heroic Mathematics.

Maps public x402 threat model (HTTP 402 payment handshake) onto:
  - Orthogonal projectors (idempotent single-use grant)
  - Banach contraction / finality (grant only after settlement fixed-point)
  - Binding / commutator non-zero (amount-resource-payee mismatch)
  - Boundary leak (HTTP vs chain)

Emergency warning when risk score exceeds threshold.
NO exploit code, NO PoC payloads — warn path only.

Geltung: MODELL (threat) · Spezifikation (audit/warn pipeline)
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "load_config",
    "audit",
    "risk_score",
    "emit_warning",
    "status",
    "heroic_math_checks",
]


def load_config() -> dict[str, Any]:
    path = ROOT / "x402_hackability.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


@dataclass
class GateResult:
    id: str
    ok: bool
    attack: str
    description: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MathCheck:
    id: str
    property: str
    ok: bool
    detail: str
    geltung: str = "MODELL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    ok: bool
    protocol: str
    risk_score: float
    level: str  # ok | warn | critical
    warn: bool
    gates: list[GateResult]
    math_checks: list[MathCheck]
    open_attacks: list[dict[str, Any]]
    controls_ok: int
    controls_total: int
    generated_at: str
    emergency_paths: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["gates"] = [g.to_dict() if hasattr(g, "to_dict") else g for g in self.gates]
        d["math_checks"] = [
            m.to_dict() if hasattr(m, "to_dict") else m for m in self.math_checks
        ]
        return d


def heroic_math_checks(seed: int = 402) -> list[MathCheck]:
    """Formal properties used as *analogues* for x402 safety (MODELL, not HTTP proof)."""
    from fusion_hero_os.core.heroic_math_engine import (
        OrthogonalProjector,
        BanachContractionSeed,
        HeroicMatrixEngine,
    )

    rng = np.random.default_rng(seed)
    out: list[MathCheck] = []

    # --- Projector: single-use grant analogue (idempotent apply) ---
    try:
        n, k = 5, 2
        proj = OrthogonalProjector(rng.normal(size=(n, k)))
        v = rng.normal(size=n)
        idem = proj.is_idempotent()
        nonexp = proj.is_nonexpansive_for(v)
        # double-apply equals single apply
        p1 = proj.project(v)
        p2 = proj.project(p1)
        double_eq = bool(np.allclose(p1, p2))
        ok = idem and nonexp and double_eq
        out.append(
            MathCheck(
                id="M_projector_idempotent_grant",
                property="OrthogonalProjector P²=P → grant projector must be single-use/idempotent",
                ok=ok,
                detail=f"idempotent={idem} nonexpansive={nonexp} double_eq={double_eq}",
                geltung="MODELL",
            )
        )
    except Exception as e:  # noqa: BLE001
        out.append(
            MathCheck(
                "M_projector_idempotent_grant",
                "projector",
                False,
                f"error:{e}",
            )
        )

    # --- Banach: settlement finality before grant ---
    try:
        A = rng.normal(size=(3, 3)) * 0.15  # ||A||_2 << 1
        c = rng.normal(size=3)
        banach = BanachContractionSeed(A, c)
        x0 = rng.normal(size=3)
        bound_ok = banach.verify_contraction_bound(x0, n_steps=40)
        # "grant before fixed point" = early iterate far from fixpoint
        x_star = banach.fixpoint()
        x_early = banach.apply(x0)
        early_gap = float(np.linalg.norm(x_early - x_star))
        final_x, _ = banach.iterate(x0, tol=1e-12, max_steps=10_000)
        final_gap = float(np.linalg.norm(final_x - x_star))
        out.append(
            MathCheck(
                id="M_banach_finality_before_grant",
                property="Banach fixpoint: grant only after contraction residual small (finality)",
                ok=bound_ok and final_gap < early_gap,
                detail=f"bound_ok={bound_ok} early_gap={early_gap:.4e} final_gap={final_gap:.4e}",
                geltung="MODELL",
            )
        )
    except Exception as e:  # noqa: BLE001
        out.append(
            MathCheck("M_banach_finality_before_grant", "banach", False, f"error:{e}")
        )

    # --- Binding: transpose reciprocity / order sensitivity ---
    try:
        eng = HeroicMatrixEngine()
        q1, b1 = rng.normal(size=(3, 3)), rng.normal(size=(3, 3))
        q2, b2 = rng.normal(size=(3, 3)), rng.normal(size=(3, 3))
        naive = eng.check_reciprocity_condition(q1, b1, q2, b2)
        true_rec = eng.check_transpose_reciprocity(q1, b1, q2, b2)
        # Security lesson: naive equality fails; binding must use correct law
        out.append(
            MathCheck(
                id="M_binding_not_naive_equality",
                property="Binding amount/resource/payee: naive swap-equality fails; need strict binding law",
                ok=(not naive) and true_rec,
                detail=f"naive_holds={naive} transpose_reciprocity={true_rec}",
                geltung="MODELL",
            )
        )
    except Exception as e:  # noqa: BLE001
        out.append(
            MathCheck("M_binding_not_naive_equality", "binding", False, f"error:{e}")
        )

    # --- Commutator: order of pay-vs-grant matters ---
    try:
        eng = HeroicMatrixEngine()
        q, b = eng.q_default, eng.b_default
        comm = eng.compute_commutator(q, b)
        nonzero = float(np.linalg.norm(comm)) > 1e-12
        out.append(
            MathCheck(
                id="M_commutator_order_matters",
                property="[pay, grant] order: non-commuting stages → reorder attacks exist if unbound",
                ok=nonzero,
                detail=f"||[Q,B]||={float(np.linalg.norm(comm)):.6f}",
                geltung="MODELL",
            )
        )
    except Exception as e:  # noqa: BLE001
        out.append(
            MathCheck("M_commutator_order_matters", "commutator", False, f"error:{e}")
        )

    return out


def _default_gate_answers(cfg: dict[str, Any]) -> dict[str, bool]:
    """
    Default: assume gates NOT implemented in Fusion (honest).
    Override via env FUSION_X402_GATES=json or config fusion_gates.
    """
    env = os.environ.get("FUSION_X402_GATES", "").strip()
    if env:
        try:
            return {str(k): bool(v) for k, v in json.loads(env).items()}
        except Exception:
            pass
    custom = cfg.get("fusion_gates") or {}
    if custom:
        return {str(k): bool(v) for k, v in custom.items()}
    # Honest defaults: we do not claim x402 production hardening yet
    return {g["id"]: False for g in (cfg.get("control_gates") or [])}


def audit(
    *,
    gate_answers: dict[str, bool] | None = None,
    emit: bool = True,
) -> AuditReport:
    cfg = load_config()
    gates_cfg = list(cfg.get("control_gates") or [])
    answers = gate_answers if gate_answers is not None else _default_gate_answers(cfg)

    gate_results: list[GateResult] = []
    for g in gates_cfg:
        gid = str(g.get("id"))
        ok = bool(answers.get(gid, False))
        gate_results.append(
            GateResult(
                id=gid,
                ok=ok,
                attack=str(g.get("attack") or ""),
                description=str(g.get("description") or ""),
                note="implemented" if ok else "MISSING — risk remains open",
            )
        )

    math_checks = heroic_math_checks()
    score, open_attacks = risk_score(cfg, gate_results, math_checks)

    scoring = cfg.get("scoring") or {}
    warn_th = float(scoring.get("warn_threshold", 45))
    crit_th = float(scoring.get("critical_threshold", 70))
    if score >= crit_th:
        level = "critical"
    elif score >= warn_th:
        level = "warn"
    else:
        level = "ok"
    warn = level in ("warn", "critical")

    controls_ok = sum(1 for g in gate_results if g.ok)
    summary = (
        f"x402 hackability audit: score={score:.1f}/100 level={level} "
        f"gates={controls_ok}/{len(gate_results)} open_attacks={len(open_attacks)}"
    )

    report = AuditReport(
        ok=not warn,  # ok means no emergency
        protocol="x402",
        risk_score=score,
        level=level,
        warn=warn,
        gates=gate_results,
        math_checks=math_checks,
        open_attacks=open_attacks,
        controls_ok=controls_ok,
        controls_total=len(gate_results),
        generated_at=datetime.now(UTC).isoformat(),
        summary=summary,
    )

    if emit:
        paths = emit_warning(report, cfg) if warn else _persist_report(report, cfg, emergency=False)
        report.emergency_paths = paths

    return report


def risk_score(
    cfg: dict[str, Any],
    gates: list[GateResult],
    math_checks: list[MathCheck],
) -> tuple[float, list[dict[str, Any]]]:
    """Score 0..100 from open attacks (failed gates) + math model failures."""
    scoring = cfg.get("scoring") or {}
    weights = scoring.get("weights") or {
        "critical": 22,
        "high": 14,
        "medium": 8,
        "low": 3,
    }
    attacks = {a["id"]: a for a in (cfg.get("attack_classes") or [])}
    open_ids = set()
    for g in gates:
        if not g.ok and g.attack:
            open_ids.add(g.attack)

    open_list: list[dict[str, Any]] = []
    score = 0.0
    for aid in open_ids:
        a = attacks.get(aid) or {"id": aid, "severity": "high", "name": aid}
        sev = str(a.get("severity") or "high").lower()
        w = float(weights.get(sev, 10))
        score += w
        open_list.append(
            {
                "id": aid,
                "name": a.get("name"),
                "severity": sev,
                "weight": w,
                "heroic_math": a.get("heroic_math"),
            }
        )

    # Math check failures add model uncertainty (capped)
    math_fail = sum(1 for m in math_checks if not m.ok)
    score += math_fail * 5.0

    # Baseline residual risk for agentic payment protocol even if all gates pass
    residual = 8.0 if not open_ids else 0.0
    score += residual

    max_score = float(scoring.get("max_score", 100))
    score = min(max_score, score)
    return round(score, 2), open_list


def _persist_report(
    report: AuditReport, cfg: dict[str, Any], *, emergency: bool
) -> list[str]:
    paths: list[str] = []
    alert_dir = Path.home() / ".fusion" / "alerts"
    alert_dir.mkdir(parents=True, exist_ok=True)
    name = "x402_emergency.json" if emergency else "x402_audit_latest.json"
    p = alert_dir / name
    payload = report.to_dict()
    payload["sha16"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    paths.append(str(p))

    docs = ROOT / "docs" / "security"
    docs.mkdir(parents=True, exist_ok=True)
    pub = {
        "generated_at": report.generated_at,
        "protocol": report.protocol,
        "risk_score": report.risk_score,
        "level": report.level,
        "warn": report.warn,
        "controls_ok": report.controls_ok,
        "controls_total": report.controls_total,
        "open_attack_ids": [a.get("id") for a in report.open_attacks],
        "math_ok": sum(1 for m in report.math_checks if m.ok),
        "math_total": len(report.math_checks),
        "summary": report.summary,
        "geltung": "MODELL+Spezifikation",
        "no_exploit_poc": True,
    }
    pub_path = docs / "x402_hackability.summary.json"
    pub_path.write_text(json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8")
    paths.append(str(pub_path))
    return paths


def emit_warning(report: AuditReport, cfg: dict[str, Any] | None = None) -> list[str]:
    """Emergency warning path — files + optional print (no external send without keys)."""
    cfg = cfg or load_config()
    paths = _persist_report(report, cfg, emergency=True)

    # Human-readable alert
    alert_md = Path.home() / ".fusion" / "alerts" / "X402_EMERGENCY_WARNING.md"
    lines = [
        "# X402 EMERGENCY WARNING",
        "",
        f"**Level:** `{report.level}` · **Score:** {report.risk_score}/100",
        f"**Time:** {report.generated_at}",
        "",
        report.summary,
        "",
        "## Open attack classes (gates missing)",
    ]
    for a in report.open_attacks:
        lines.append(
            f"- **{a.get('id')}** ({a.get('severity')}): {a.get('name')} · math={a.get('heroic_math')}"
        )
    lines.extend(
        [
            "",
            "## Heroic-math model checks",
        ]
    )
    for m in report.math_checks:
        mark = "OK" if m.ok else "FAIL"
        lines.append(f"- [{mark}] `{m.id}` — {m.property} ({m.detail})")
    lines.extend(
        [
            "",
            "## Fusion policy",
            "- Do **not** treat x402 as source-of-truth for MasterSeed/secrets",
            "- Payments integration: **warn-only** until gates green",
            "- No exploit PoCs in this tree",
            "",
            f"Full JSON: `{Path.home() / '.fusion' / 'alerts' / 'x402_emergency.json'}`",
            "",
        ]
    )
    alert_md.write_text("\n".join(lines), encoding="utf-8")
    paths.append(str(alert_md))

    # docs security note
    docs_md = ROOT / "docs" / "security" / "X402_HACKABILITY_AUDIT.md"
    docs_md.parent.mkdir(parents=True, exist_ok=True)
    docs_md.write_text(
        "\n".join(
            [
                "# x402 Foundation — Hackability Audit (Heroic Math)",
                "",
                f"**Last run:** {report.generated_at}",
                f"**Risk score:** {report.risk_score}/100 · **Level:** {report.level}",
                f"**Warn:** {report.warn}",
                "",
                "## Protocol",
                "",
                "x402 (x402 Foundation / Linux Foundation) reactivates **HTTP 402 Payment Required**",
                "as an open internet-native payment handshake for agents and APIs.",
                "",
                "## Public research (defensive)",
                "",
                "- Five Attacks paper (2026): settlement optimistic grant, preemption, replay,",
                "  header/proxy cache, agent server selection",
                "- Facilitator trust monoculture; prompt-injection → wrong wallet",
                "",
                "## Heroic mathematics mapping (MODELL)",
                "",
                "| Math object | x402 safety analogue |",
                "|-------------|----------------------|",
                "| Orthogonal projector P²=P | Single-use payment→grant (idempotent) |",
                "| Banach contraction finality | Grant only after settlement fixed-point |",
                "| Transpose reciprocity vs naive equality | Strict amount/resource/payee binding |",
                "| Commutator [Q,B]≠0 | Pay/grant order attacks if unbound |",
                "",
                "## Result",
                "",
                f"- Gates: **{report.controls_ok}/{report.controls_total}**",
                f"- Open attacks: {', '.join(a.get('id','') for a in report.open_attacks) or '(none)'}",
                f"- Summary: {report.summary}",
                "",
                "## Emergency",
                "",
                "If `level` is `warn` or `critical`, see:",
                "",
                "- `~/.fusion/alerts/x402_emergency.json`",
                "- `~/.fusion/alerts/X402_EMERGENCY_WARNING.md`",
                "",
                "**Geltung:** MODELL (threat) · Spezifikation (this audit tool). No exploit payloads.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    paths.append(str(docs_md))
    return paths


def status() -> dict[str, Any]:
    cfg = load_config()
    alert = Path.home() / ".fusion" / "alerts" / "x402_emergency.json"
    latest = None
    if alert.is_file():
        try:
            latest = json.loads(alert.read_text(encoding="utf-8"))
        except Exception:
            latest = {"raw": True}
    return {
        "ok": True,
        "protocol": "x402",
        "config_version": cfg.get("version"),
        "warn_threshold": (cfg.get("scoring") or {}).get("warn_threshold"),
        "critical_threshold": (cfg.get("scoring") or {}).get("critical_threshold"),
        "attack_classes": len(cfg.get("attack_classes") or []),
        "control_gates": len(cfg.get("control_gates") or []),
        "last_emergency": latest,
        "policy": cfg.get("fusion_policy"),
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="x402 hackability audit + emergency warn")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--audit", action="store_true", help="run full audit (default)")
    ap.add_argument("--assume-all-gates", action="store_true", help="simulate all controls OK")
    ap.add_argument("--no-emit", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0

    gate_answers = None
    if args.assume_all_gates:
        cfg = load_config()
        gate_answers = {g["id"]: True for g in (cfg.get("control_gates") or [])}

    report = audit(gate_answers=gate_answers, emit=not args.no_emit)
    print(
        json.dumps(
            {
                "ok": report.ok,
                "level": report.level,
                "risk_score": report.risk_score,
                "warn": report.warn,
                "controls": f"{report.controls_ok}/{report.controls_total}",
                "open_attacks": [a.get("id") for a in report.open_attacks],
                "math": [
                    {"id": m.id, "ok": m.ok, "detail": m.detail} for m in report.math_checks
                ],
                "summary": report.summary,
                "emergency_paths": report.emergency_paths,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if report.level == "critical":
        return 3
    if report.warn:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
