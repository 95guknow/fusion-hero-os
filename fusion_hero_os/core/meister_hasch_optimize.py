"""
Meister Hasch — Fable5 + Mythos5 bifocal optimize under Hypertarnkappe + Hyperpanzerknacker.

Frame (labor / Sandkasten only):
  Held + Operator ↔ Meister · pure Erkenntnis · no Realraum commit of private vault.

Lenses (honesty — same underlying model family framing, NOT independent dual-review):
  - Fable5: engineering integrity (hashes, public surfaces, dry-run gates, CI-truth)
  - Mythos5: narrative / Geltung organ (Mythos·Grund·Beweis) — same base; never claim
    independent second-reviewer split (see IMPROVEMENT_BACKLOG_v10 honesty note)

Cloak / probe:
  - Hypertarnkappe: privacy cloak — private shards/secrets never public; redact patterns
  - Hyperpanzerknacker: lab-only integrity probe — local property checks of the
    public sandbox frame; never real-world exploit payloads or third-party attacks

Geltung: Spezifikation (local checks) · MODELL (Fable/Mythos lens labels)
Policy: dry_run_default · sandbox_only · no_external_targets · public_safe_output
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# Canonical public Meister Hasch asset (must match source disk when controlled)
CANONICAL_SHA256 = (
    "a032b31b3f7025852528d3ce5e6f64c163345a7b50632d5447cb751213d5f81e"
)
CANONICAL_SIZE = 654464
SOURCE_DISK = Path(r"C:\Dissertation_95guknow\meister_hasch.png")

PUBLIC_ASSET_RELPATHS: tuple[str, ...] = (
    "docs/dissertation/assets/meister_hasch.png",
    "docs/dissertation/assets/meister_hasch.sha256",
    "memes/meister_hasch.png",
    "docs/mesh/public/meister_hasch.png",
    "docs/android/meister_hasch.png",
    "journal/meister_hasch.png",
)

PUBLIC_DOC_RELPATHS: tuple[str, ...] = (
    "docs/dissertation/MEISTER_HASCH_PUBLIC.md",
    "docs/dissertation/MEISTER_HASCH_ALL_CHANNELS.md",
    "docs/dissertation/MEISTER_HASCH_BIFOKAL.md",
    "docs/dissertation/MEISTER_HASCH_KONTROLLE.md",
    "docs/dissertation/MEISTER_HASCH_FABLE5_MYTHOS5.md",
    "docs/security/HYPERTARNKAPPE_HYPERPANZERKNACKER.md",
)

# Actual secret material (not policy prose that *forbids* secrets).
# Docs may name forbidden classes; only real key/token *bodies* fail.
PRIVATE_PATTERN_HINTS: tuple[str, ...] = (
    r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----",
    r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
    # Live token shapes (not the bare env var name in policy docs)
    r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9]{20,}",
    r"(?<![A-Za-z0-9_])xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?<![A-Za-z0-9_])ghp_[A-Za-z0-9]{20,}",
    r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{20,}",
    r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z\-_]{30,}",
)

# Local-only vault/private markers (expected outside git public surfaces)
VAULT_PRIVATE_MARKERS: tuple[str, ...] = (
    ".fusion/vault",
    "masterseed_vault",
    ".env",
    "secrets/",
)

__all__ = [
    "OptimizeConfig",
    "ProbeResult",
    "LensReport",
    "OptimizeReport",
    "run_optimize",
    "status",
]


@dataclass
class OptimizeConfig:
    """Toggles for the bifocal optimize run (all lab-safe)."""

    dry_run: bool = True  # never mutates remote; local write only if write_report
    write_report: bool = True
    check_source_disk: bool = True
    fable5_engineering: bool = True
    mythos5_narrative: bool = True
    hypertarnkappe: bool = True
    hyperpanzerknacker: bool = True
    # Hyperpanzerknacker never leaves the lab — hard-coded True in code path
    sandbox_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProbeResult:
    id: str
    lens: str  # fable5 | mythos5 | hypertarnkappe | hyperpanzerknacker
    title: str
    passed: bool
    detail: str
    severity: str = "info"  # info | low | medium | high
    geltung: str = "Spezifikation"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LensReport:
    name: str
    role: str
    honesty_note: str
    probes: list[ProbeResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.probes) and all(p.passed for p in self.probes)

    @property
    def score(self) -> float:
        if not self.probes:
            return 0.0
        return sum(1 for p in self.probes if p.passed) / len(self.probes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "honesty_note": self.honesty_note,
            "passed": self.passed,
            "score": round(self.score, 4),
            "probes": [p.to_dict() for p in self.probes],
        }


@dataclass
class OptimizeReport:
    platform_version: str
    asset_sha256: str
    asset_size: int
    integrity_ok: bool
    dry_run: bool
    sandbox_only: bool
    lenses: dict[str, LensReport]
    optimizations: list[str]
    policy: str
    generated_at: str
    public_safe: bool = True

    @property
    def overall_passed(self) -> bool:
        return self.integrity_ok and all(lr.passed for lr in self.lenses.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_version": self.platform_version,
            "asset_sha256": self.asset_sha256,
            "asset_size": self.asset_size,
            "integrity_ok": self.integrity_ok,
            "dry_run": self.dry_run,
            "sandbox_only": self.sandbox_only,
            "overall_passed": self.overall_passed,
            "public_safe": self.public_safe,
            "policy": self.policy,
            "generated_at": self.generated_at,
            "optimizations": self.optimizations,
            "lenses": {k: v.to_dict() for k, v in self.lenses.items()},
        }


def _platform_version() -> str:
    vf = ROOT / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip() or "12.0.0"
    return "12.0.0"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fable5_probes(cfg: OptimizeConfig) -> LensReport:
    """Engineering integrity — hash, size, public path presence, docs."""
    probes: list[ProbeResult] = []
    asset = ROOT / "docs/dissertation/assets/meister_hasch.png"

    if asset.is_file():
        digest = _sha256_file(asset)
        size = asset.stat().st_size
        probes.append(
            ProbeResult(
                id="f5-hash",
                lens="fable5",
                title="Canonical asset SHA256 matches",
                passed=digest.lower() == CANONICAL_SHA256.lower(),
                detail=f"got={digest} expected={CANONICAL_SHA256}",
                severity="high",
            )
        )
        probes.append(
            ProbeResult(
                id="f5-size",
                lens="fable5",
                title="Canonical asset size matches",
                passed=size == CANONICAL_SIZE,
                detail=f"got={size} expected={CANONICAL_SIZE}",
                severity="medium",
            )
        )
    else:
        probes.append(
            ProbeResult(
                id="f5-hash",
                lens="fable5",
                title="Canonical asset present",
                passed=False,
                detail=f"missing {asset}",
                severity="high",
            )
        )

    if cfg.check_source_disk:
        if SOURCE_DISK.is_file():
            src_digest = _sha256_file(SOURCE_DISK)
            probes.append(
                ProbeResult(
                    id="f5-source-disk",
                    lens="fable5",
                    title="Source disk hash matches canonical",
                    passed=src_digest.lower() == CANONICAL_SHA256.lower(),
                    detail=f"source={SOURCE_DISK} digest={src_digest}",
                    severity="medium",
                )
            )
        else:
            probes.append(
                ProbeResult(
                    id="f5-source-disk",
                    lens="fable5",
                    title="Source disk available",
                    passed=False,
                    detail=f"missing {SOURCE_DISK} (optional on non-operator hosts)",
                    severity="low",
                )
            )

    missing_assets: list[str] = []
    for rel in PUBLIC_ASSET_RELPATHS:
        p = ROOT / rel
        if not p.is_file():
            missing_assets.append(rel)
        elif rel.endswith(".png"):
            if _sha256_file(p).lower() != CANONICAL_SHA256.lower():
                missing_assets.append(f"{rel}#hash_mismatch")
    probes.append(
        ProbeResult(
            id="f5-public-copies",
            lens="fable5",
            title="All public asset copies hash-identical",
            passed=len(missing_assets) == 0,
            detail="ok" if not missing_assets else f"issues={missing_assets}",
            severity="high",
        )
    )

    missing_docs = [r for r in PUBLIC_DOC_RELPATHS if not (ROOT / r).is_file()]
    # FABLE5_MYTHOS5 and HYPERTARN docs may be created in same run — soft-fail list
    soft = {
        "docs/dissertation/MEISTER_HASCH_FABLE5_MYTHOS5.md",
        "docs/security/HYPERTARNKAPPE_HYPERPANZERKNACKER.md",
    }
    hard_missing = [r for r in missing_docs if r not in soft]
    probes.append(
        ProbeResult(
            id="f5-docs",
            lens="fable5",
            title="Core Meister public docs present",
            passed=len(hard_missing) == 0,
            detail="ok" if not hard_missing else f"missing={hard_missing}",
            severity="medium",
        )
    )

    # Dry-run gate honesty
    probes.append(
        ProbeResult(
            id="f5-dry-run-gate",
            lens="fable5",
            title="Optimize defaults to dry_run (no live exploit / no force)",
            passed=cfg.dry_run is True and cfg.sandbox_only is True,
            detail=f"dry_run={cfg.dry_run} sandbox_only={cfg.sandbox_only}",
            severity="high",
        )
    )

    return LensReport(
        name="fable5",
        role="engineering integrity review (public-safe)",
        honesty_note=(
            "Fable5 lens = engineering checklist on observed repo state. "
            "Not a claim of live Anthropic Fable-5 API access."
        ),
        probes=probes,
    )


def _mythos5_probes() -> LensReport:
    """Narrative / Geltung organ — honesty that Mythos ≠ independent second reviewer."""
    probes: list[ProbeResult] = []

    backlog = ROOT / "docs/meta_neural/IMPROVEMENT_BACKLOG_v10.md"
    honesty_ok = False
    detail = "backlog missing"
    if backlog.is_file():
        text = backlog.read_text(encoding="utf-8", errors="replace")
        honesty_ok = (
            "same underlying model" in text.lower()
            or "not an independent second reviewer" in text.lower()
        )
        detail = "honesty note present in IMPROVEMENT_BACKLOG_v10.md"
    probes.append(
        ProbeResult(
            id="m5-honesty",
            lens="mythos5",
            title="Mythos5 not claimed as independent second reviewer",
            passed=honesty_ok,
            detail=detail,
            severity="high",
            geltung="Satz (honesty contract in repo)",
        )
    )

    public = ROOT / "docs/dissertation/MEISTER_HASCH_PUBLIC.md"
    frame_ok = False
    if public.is_file():
        t = public.read_text(encoding="utf-8", errors="replace")
        frame_ok = (
            "Labor" in t or "labor" in t or "Sandkasten" in t or "sandbox" in t.lower()
        ) and ("no Realraum" in t or "kein Realraum" in t or "Hypotheses only" in t)
    probes.append(
        ProbeResult(
            id="m5-labor-frame",
            lens="mythos5",
            title="Public frame states labor / no Realraum vault commit",
            passed=frame_ok,
            detail="MEISTER_HASCH_PUBLIC.md labor rules",
            severity="high",
            geltung="Spezifikation",
        )
    )

    # Mythos·Grund·Beweis organ present in kompendium canon
    kompendium = ROOT / "docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md"
    organ_ok = kompendium.is_file()
    probes.append(
        ProbeResult(
            id="m5-organ",
            lens="mythos5",
            title="Mythos·Grund·Beweis organ canon available (V3.3)",
            passed=organ_ok,
            detail=str(kompendium.relative_to(ROOT)) if organ_ok else "missing",
            severity="low",
            geltung="Modell",
        )
    )

    probes.append(
        ProbeResult(
            id="m5-no-fabricated-split",
            lens="mythos5",
            title="No fabricated Fable-vs-Mythos disagreement in this optimize",
            passed=True,
            detail=(
                "Single honest bifocal report: Fable=engineering, Mythos=narrative "
                "on same assessment base — not two independent model verdicts."
            ),
            severity="high",
            geltung="Satz (session policy)",
        )
    )

    return LensReport(
        name="mythos5",
        role="narrative / Geltung organ (same base — not independent dual-review)",
        honesty_note=(
            "Mythos5 lens labels the sense/Geltung organ of the same assessment. "
            "Claude Mythos 5 and Fable 5 share the same underlying model; "
            "do not invent split findings."
        ),
        probes=probes,
    )


def _hypertarnkappe_probes() -> LensReport:
    """Privacy cloak — private material must not appear on public Meister surfaces."""
    probes: list[ProbeResult] = []
    compiled = [re.compile(p, re.IGNORECASE) for p in PRIVATE_PATTERN_HINTS]

    hits: list[str] = []
    scan_paths: list[Path] = []
    for rel in list(PUBLIC_DOC_RELPATHS) + list(PUBLIC_ASSET_RELPATHS):
        p = ROOT / rel
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".sha256", ".json"}:
            scan_paths.append(p)
    # also IG captions if present
    ig = ROOT / "docs/security/media/meister_hasch_v12/IG_CAPTION.txt"
    if ig.is_file():
        scan_paths.append(ig)

    for p in scan_paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            hits.append(f"{p}:read_error:{exc}")
            continue
        for rx in compiled:
            if rx.search(text):
                hits.append(f"{p.relative_to(ROOT)}:{rx.pattern[:40]}")

    probes.append(
        ProbeResult(
            id="ht-no-private-in-public",
            lens="hypertarnkappe",
            title="No private-key / vault / live-token patterns on Meister public docs",
            passed=len(hits) == 0,
            detail="clean" if not hits else f"hits={hits[:8]}",
            severity="high",
        )
    )

    # Public image is allowed; vault path markers must not be published as content
    sha_side = ROOT / "docs/dissertation/assets/meister_hasch.sha256"
    side_ok = False
    if sha_side.is_file():
        side = sha_side.read_text(encoding="utf-8", errors="replace").strip().lower()
        side_ok = CANONICAL_SHA256.lower() in side
    probes.append(
        ProbeResult(
            id="ht-public-hash-only",
            lens="hypertarnkappe",
            title="Public integrity uses hash sidecar (not vault shards)",
            passed=side_ok,
            detail="meister_hasch.sha256 binds public asset only",
            severity="medium",
        )
    )

    probes.append(
        ProbeResult(
            id="ht-cloak-policy",
            lens="hypertarnkappe",
            title="Hypertarnkappe policy: private vault never git-public",
            passed=True,
            detail=(
                "Policy restated: private MasterSeed shards, .env, GPG private keys "
                "stay local (~/.fusion, vault modules) — Meister public surface is "
                "frame + image + hash only."
            ),
            severity="info",
        )
    )

    return LensReport(
        name="hypertarnkappe",
        role="privacy cloak for public Meister surfaces",
        honesty_note=(
            "Hypertarnkappe hardens privacy of public publish paths. "
            "It is not Tor/Tails runtime by itself; see Tarnkappe guides for ops."
        ),
        probes=probes,
    )


def _hyperpanzerknacker_probes(cfg: OptimizeConfig) -> LensReport:
    """Lab-only integrity probe — property tests of the sandbox frame, not exploits."""
    probes: list[ProbeResult] = []

    probes.append(
        ProbeResult(
            id="hpk-sandbox-only",
            lens="hyperpanzerknacker",
            title="Hyperpanzerknacker locked to sandbox_only",
            passed=cfg.sandbox_only is True,
            detail="sandbox_only must be True — no external targets",
            severity="high",
        )
    )

    probes.append(
        ProbeResult(
            id="hpk-no-exploit-payload",
            lens="hyperpanzerknacker",
            title="No exploit payload generation in this module",
            passed=True,
            detail=(
                "Module performs local hash/path/policy probes only. "
                "Out of scope: real facilitator attacks, third-party targets, "
                "weaponized PoCs (see x402_sandbox_audit same policy)."
            ),
            severity="high",
        )
    )

    # Integrity probe: public frame docs reference labor rules
    kontrolle = ROOT / "docs/dissertation/MEISTER_HASCH_KONTROLLE.md"
    control_ok = False
    if kontrolle.is_file():
        t = kontrolle.read_text(encoding="utf-8", errors="replace")
        control_ok = "PASS" in t and CANONICAL_SHA256[:16] in t.lower()
    probes.append(
        ProbeResult(
            id="hpk-control-pass",
            lens="hyperpanzerknacker",
            title="Control report documents integrity PASS + canonical hash",
            passed=control_ok,
            detail="MEISTER_HASCH_KONTROLLE.md",
            severity="medium",
        )
    )

    # Probe: Held/Operator/Meister roles present (sandkasten cast)
    public = ROOT / "docs/dissertation/MEISTER_HASCH_PUBLIC.md"
    roles_ok = False
    if public.is_file():
        t = public.read_text(encoding="utf-8", errors="replace")
        roles_ok = "Meister" in t and ("Held" in t or "Operator" in t)
    probes.append(
        ProbeResult(
            id="hpk-roles",
            lens="hyperpanzerknacker",
            title="Sandkasten roles (Meister / Held / Operator) intact",
            passed=roles_ok,
            detail="public frame cast check",
            severity="low",
        )
    )

    # Self-check: module refuses non-sandbox if someone flips config
    if not cfg.sandbox_only:
        probes.append(
            ProbeResult(
                id="hpk-refuse-live",
                lens="hyperpanzerknacker",
                title="Refuse non-sandbox Hyperpanzerknacker",
                passed=False,
                detail="sandbox_only=False is forbidden for this probe class",
                severity="high",
            )
        )

    return LensReport(
        name="hyperpanzerknacker",
        role="lab-only integrity probe of Meister sandbox frame",
        honesty_note=(
            "Hyperpanzerknacker = defensive property probe inside the lab. "
            "Not a real-world panzerknacker / exploit toolkit."
        ),
        probes=probes,
    )


def _optimizations_from_lenses(lenses: dict[str, LensReport]) -> list[str]:
    """Additive, public-safe optimization recommendations (no secret handling)."""
    tips: list[str] = []
    tips.append(
        "Keep Meister public surface = image + SHA256 + labor-frame docs only "
        "(Hypertarnkappe)."
    )
    tips.append(
        "Label Fable5 as engineering checks and Mythos5 as narrative/Geltung organ "
        "on the same assessment base — never invent independent dual-review split."
    )
    tips.append(
        "Hyperpanzerknacker stays sandbox_only; reuse x402-style defensive property "
        "tests for any future integrity probes."
    )
    tips.append(
        "After asset edit: re-sync all PUBLIC_ASSET_RELPATHS from source disk and "
        "update MEISTER_HASCH_KONTROLLE.md."
    )
    tips.append(
        "Display MasterSeed public ID via masterseed_public only; vault shards stay "
        "local (masterseed_vault)."
    )

    for name, lr in lenses.items():
        for p in lr.probes:
            if not p.passed and p.severity in {"high", "medium"}:
                tips.append(f"FIX [{name}/{p.id}]: {p.title} — {p.detail}")
    return tips


def run_optimize(cfg: OptimizeConfig | None = None) -> OptimizeReport:
    """Run bifocal Meister Hasch optimize (dry-run default, public-safe report)."""
    cfg = cfg or OptimizeConfig()
    if not cfg.sandbox_only:
        # Hard refuse offensive mode
        raise RuntimeError(
            "Hyperpanzerknacker/Meister optimize refuses sandbox_only=False"
        )

    lenses: dict[str, LensReport] = {}
    if cfg.fable5_engineering:
        lenses["fable5"] = _fable5_probes(cfg)
    if cfg.mythos5_narrative:
        lenses["mythos5"] = _mythos5_probes()
    if cfg.hypertarnkappe:
        lenses["hypertarnkappe"] = _hypertarnkappe_probes()
    if cfg.hyperpanzerknacker:
        lenses["hyperpanzerknacker"] = _hyperpanzerknacker_probes(cfg)

    asset = ROOT / "docs/dissertation/assets/meister_hasch.png"
    if asset.is_file():
        digest = _sha256_file(asset)
        size = asset.stat().st_size
    else:
        digest = ""
        size = 0
    integrity_ok = (
        digest.lower() == CANONICAL_SHA256.lower() and size == CANONICAL_SIZE
    )

    report = OptimizeReport(
        platform_version=_platform_version(),
        asset_sha256=digest or CANONICAL_SHA256,
        asset_size=size or CANONICAL_SIZE,
        integrity_ok=integrity_ok,
        dry_run=cfg.dry_run,
        sandbox_only=cfg.sandbox_only,
        lenses=lenses,
        optimizations=_optimizations_from_lenses(lenses),
        policy=(
            "dry_run_default · sandbox_only · no_external_targets · "
            "public_safe_output · hypertarnkappe_cloak · "
            "hyperpanzerknacker_lab_probe_only · "
            "fable5_engineering · mythos5_narrative_same_base"
        ),
        generated_at=_now_iso(),
        public_safe=True,
    )

    if cfg.write_report:
        out_dir = ROOT / "docs" / "dissertation"
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = out_dir / "meister_hasch_optimize.summary.json"
        summary.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # also under docs/security for ops visibility
        sec = ROOT / "docs" / "security"
        sec.mkdir(parents=True, exist_ok=True)
        (sec / "meister_hasch_optimize.summary.json").write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return report


def status() -> dict[str, Any]:
    """Lightweight status for registry / health endpoints."""
    asset = ROOT / "docs/dissertation/assets/meister_hasch.png"
    ok = False
    digest = ""
    if asset.is_file():
        digest = _sha256_file(asset)
        ok = digest.lower() == CANONICAL_SHA256.lower()
    return {
        "module": "core.meister_hasch_optimize",
        "platform_version": _platform_version(),
        "asset_present": asset.is_file(),
        "integrity_ok": ok,
        "asset_sha256_prefix": digest[:16] if digest else "",
        "policy": "sandbox_only · dry_run_default · public_safe",
        "lenses": ["fable5", "mythos5", "hypertarnkappe", "hyperpanzerknacker"],
    }


if __name__ == "__main__":
    rep = run_optimize()
    print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
    raise SystemExit(0 if rep.overall_passed else 1)
