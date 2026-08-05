"""
Eudaemon Agent — Korridor begehen, jenseits handeln (Meister Hasch Labor).

Corridor = public SPA / dual-plane path surface (often a shell).
Other side = operator-local lab where the eudaemon may act:
  integrity checks, self-heal pulse, eudaimonia corridor validation,
  public-safe report — never third-party offense.

Roles (Meister Hasch):
  Meister  — integrity probe
  Held     — kernel capability
  Eudaemon — this agent: sustainable good (eudaimonia) without collapse

Policy: sandbox_only · no_external_targets · lab publish only
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MEISTER_DISK = Path(r"C:\Dissertation_95guknow\meister_hasch.png")
MEISTER_REPO = ROOT / "docs" / "dissertation" / "assets" / "meister_hasch.png"
MEISTER_SEAL = ROOT / "docs" / "dissertation" / "alpha_meister_hasch.seal.json"
MEISTER_SHA256_ANCHOR = "a032b31b3f7025852528d3ce5e6f64c163345a7b50632d5447cb751213d5f81e"
SUMMARY = ROOT / "docs" / "security" / "eudaemon_agent.summary.json"
ALERT = Path.home() / ".fusion" / "alerts" / "eudaemon_agent.json"
REPORT_MD = ROOT / "docs" / "security" / "EUDAEMON_KORRIDOR_REPORT.md"

CLOUD_RUN = "https://fusion-hero-os-42426705927.europe-west2.run.app"

# Corridor steps: public edge → dual-plane intents → SPA depths
CORRIDOR_PATHS = (
    "/",
    "/assets/index-kwraethi.js",
    "/assets/index-3uS2yhtK.css",
    "/api/health",
    "/api/planes",
    "/api/v1/business",
    "/api/v1/business/health",
    "/mainframe",
    "/heroic",
    "/about",
)

# Energy ceiling — same spirit as EudaimoniaGuard (classical backend)
EUDAIMONIA_ENERGY_CEILING = 1e6


@dataclass
class CorridorStep:
    path: str
    status: int | None
    bytes: int
    content_type: str
    kind: str  # spa_shell | static_asset | unknown | error
    plane_hint: str  # business | hyperraum | public | asset

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _plane_hint(path: str) -> str:
    if path.startswith("/assets"):
        return "asset"
    if path in ("/", "/about", "/heroic"):
        return "public"
    if path.startswith("/api/v1/business") or path in (
        "/api/health",
        "/api/metrics",
        "/api/gui/status",
    ):
        return "business"
    if path.startswith("/api/") or path.startswith("/mainframe"):
        return "hyperraum"
    return "public"


def _classify_body(path: str, status: int, n: int, ctype: str) -> str:
    if status != 200:
        return "error"
    if "javascript" in ctype or path.endswith(".js"):
        return "static_asset"
    if "css" in ctype or path.endswith(".css"):
        return "static_asset"
    if n < 2000 and "html" in ctype:
        return "spa_shell"
    if "json" in ctype:
        return "json_api"
    return "unknown"


def walk_corridor(
    base: str = CLOUD_RUN,
    paths: tuple = CORRIDOR_PATHS,
    timeout: float = 12.0,
) -> list[CorridorStep]:
    """Begehe den öffentlichen Korridor (read-only HTTP GET)."""
    steps: list[CorridorStep] = []
    for path in paths:
        url = base.rstrip("/") + path
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "FusionEudaemon/12.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                status = resp.status
                n = len(data)
        except urllib.error.HTTPError as e:
            steps.append(
                CorridorStep(
                    path=path,
                    status=e.code,
                    bytes=0,
                    content_type="",
                    kind="error",
                    plane_hint=_plane_hint(path),
                )
            )
            continue
        except Exception:
            steps.append(
                CorridorStep(
                    path=path,
                    status=None,
                    bytes=0,
                    content_type="",
                    kind="error",
                    plane_hint=_plane_hint(path),
                )
            )
            continue
        steps.append(
            CorridorStep(
                path=path,
                status=status,
                bytes=n,
                content_type=ctype,
                kind=_classify_body(path, status, n, ctype),
                plane_hint=_plane_hint(path),
            )
        )
    return steps


def meister_integrity() -> dict[str, Any]:
    """Integrity probe: disk↔repo hash, or intentional withdrawal via seal."""
    out: dict[str, Any] = {
        "binding": True,
        "frame": "labor_sandkasten",
        "sha256_anchor": MEISTER_SHA256_ANCHOR,
    }
    for label, p in (("disk", MEISTER_DISK), ("repo", MEISTER_REPO)):
        if p.is_file():
            raw = p.read_bytes()
            out[label] = {
                "path": str(p),
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        else:
            out[label] = {"path": str(p), "missing": True}
    d = out.get("disk", {})
    r = out.get("repo", {})

    withdrawn = False
    seal_id = None
    if MEISTER_SEAL.is_file():
        try:
            seal = json.loads(MEISTER_SEAL.read_text(encoding="utf-8"))
            asset = seal.get("asset") or {}
            withdrawn = asset.get("status") == "withdrawn"
            seal_id = seal.get("seal_id")
            anchor = asset.get("sha256")
            if isinstance(anchor, str) and len(anchor) == 64:
                out["sha256_anchor"] = anchor
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    out["withdrawn"] = withdrawn
    out["seal_id"] = seal_id
    anchor = out["sha256_anchor"]

    if withdrawn:
        # Public tree must not deliver image bytes. Lab disk may still exist.
        if not r.get("missing"):
            out["hash_match"] = False
            out["mode"] = "withdrawn_but_repo_present"
            return out
        lab_ok = d.get("missing") or d.get("sha256") == anchor
        out["lab_disk_ok"] = lab_ok
        out["hash_match"] = True  # public integrity: absence is intentional
        out["mode"] = (
            "withdrawn_absent"
            if d.get("missing")
            else "withdrawn_repo_absent_disk_lab"
        )
        return out

    out["hash_match"] = (
        not d.get("missing")
        and not r.get("missing")
        and d.get("sha256") == r.get("sha256")
    )
    out["mode"] = "disk_repo_hash"
    return out


def eudaimonia_corridor_check(energy: float = 0.0) -> dict[str, Any]:
    """Local EudaimoniaGuard-style corridor: energy must stay inside bounds."""
    alerts: list[str] = []
    if energy > EUDAIMONIA_ENERGY_CEILING:
        alerts.append("Divergenter Energiewert außerhalb des eudaimonischen Korridors.")
    return {
        "passed": len(alerts) == 0,
        "alerts": alerts,
        "energy": energy,
        "ceiling": EUDAIMONIA_ENERGY_CEILING,
        "role": "eudaemon",
    }


def act_other_side(*, seed: int = 0) -> dict[str, Any]:
    """
    Jenseits des SPA-Korridors: operator-local eudaemon actions.
    """
    actions: list[dict[str, Any]] = []

    # 1) Meister Hasch integrity
    mi = meister_integrity()
    actions.append(
        {
            "id": "meister_integrity",
            "ok": bool(mi.get("hash_match")),
            "detail": (
                f"meister ok mode={mi.get('mode')}"
                if mi.get("hash_match")
                else "hash mismatch or missing"
            ),
        }
    )

    # 2) Daemon self-heal field study (if available)
    heal: dict[str, Any] = {}
    try:
        from fusion_hero_os.core.daemon_self_heal_field_study import run_field_study

        heal = run_field_study(seed=seed, write=True)
        actions.append(
            {
                "id": "self_heal_qubo_fixpoint",
                "ok": bool(heal.get("healed")),
                "detail": f"dist {heal.get('initial_distance')}→{heal.get('final_distance')}",
            }
        )
        energy = float(heal.get("final_distance", 0))
    except Exception as e:
        actions.append(
            {"id": "self_heal_qubo_fixpoint", "ok": False, "detail": str(e)[:200]}
        )
        energy = 0.0

    # 3) Eudaimonia corridor
    eu = eudaimonia_corridor_check(energy=energy)
    actions.append(
        {
            "id": "eudaimonia_corridor",
            "ok": eu["passed"],
            "detail": "within ceiling" if eu["passed"] else "; ".join(eu["alerts"]),
        }
    )

    # 4) Dead-letterbox sim pulse (optional, lab)
    try:
        from fusion_hero_os.core.dead_letterbox_pseudo_attack_sim import (
            run_pseudo_attack_sim,
        )

        sim = run_pseudo_attack_sim(seed=seed, write_evidence=True)
        actions.append(
            {
                "id": "dead_letterbox_pulse",
                "ok": bool(sim.get("all_properties_pass")),
                "detail": f"sha16={sim.get('sha16')}",
            }
        )
    except Exception as e:
        actions.append(
            {"id": "dead_letterbox_pulse", "ok": False, "detail": str(e)[:200]}
        )

    # 5) Super-door note (read existing summary if present)
    door = ROOT / "docs" / "security" / "super_door_lookaround.summary.json"
    if door.is_file():
        try:
            d = json.loads(door.read_text(encoding="utf-8"))
            actions.append(
                {
                    "id": "super_door_awareness",
                    "ok": True,
                    "detail": f"p0={d.get('p0')}",
                }
            )
        except json.JSONDecodeError:
            actions.append(
                {"id": "super_door_awareness", "ok": False, "detail": "unreadable"}
            )

    all_ok = all(a.get("ok") for a in actions if a["id"] != "super_door_awareness")
    return {
        "side": "operator_local_lab",
        "agent": "eudaemon",
        "actions": actions,
        "eudaimonia": eu,
        "meister": mi,
        "all_critical_ok": all_ok,
        "stance": {
            "offense": "FORBIDDEN",
            "publish": "public_safe_lab_only",
            "goal": "sustainable_good_without_collapse",
        },
    }


def run_eudaemon(*, walk: bool = True, act: bool = True, seed: int = 0) -> dict[str, Any]:
    corridor: list[CorridorStep] = []
    if walk:
        corridor = walk_corridor()

    spa_shells = [s for s in corridor if s.kind == "spa_shell"]
    assets = [s for s in corridor if s.kind == "static_asset"]
    json_apis = [s for s in corridor if s.kind == "json_api"]

    other = act_other_side(seed=seed) if act else {}

    report = {
        "kind": "eudaemon_korridor",
        "generated_at": _now(),
        "meister_hasch_binding": True,
        "platform_version": "12.0.0",
        "corridor": {
            "base": CLOUD_RUN,
            "steps": [s.to_dict() for s in corridor],
            "spa_shell_count": len(spa_shells),
            "static_asset_count": len(assets),
            "json_api_count": len(json_apis),
            "reading": (
                "Korridor = öffentliche SPA-Hülle; JSON-API-Plane hier nicht erreichbar. "
                "Andere Seite = operator-local Lab (Eudaemon handelt dort)."
            ),
        },
        "other_side": other,
        "policy": {
            "sandbox_only": True,
            "no_external_targets": True,
            "roleplay_lab": True,
        },
        "geltung": "HTTP corridor = Satz · eudaemon actions local = Satz · mythos = Modell",
        "doc": "docs/security/EUDAEMON_KORRIDOR_REPORT.md",
    }

    # Write evidence
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    ALERT.parent.mkdir(parents=True, exist_ok=True)
    public = {
        k: report[k]
        for k in (
            "kind",
            "generated_at",
            "meister_hasch_binding",
            "platform_version",
            "policy",
            "geltung",
            "doc",
        )
    }
    public["corridor"] = {
        "base": CLOUD_RUN,
        "spa_shell_count": report["corridor"]["spa_shell_count"],
        "static_asset_count": report["corridor"]["static_asset_count"],
        "json_api_count": report["corridor"]["json_api_count"],
        "reading": report["corridor"]["reading"],
        "steps": report["corridor"]["steps"],
    }
    if other:
        public["other_side"] = {
            "agent": other.get("agent"),
            "all_critical_ok": other.get("all_critical_ok"),
            "actions": other.get("actions"),
            "stance": other.get("stance"),
        }
    SUMMARY.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ALERT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Markdown report
    lines = [
        "# Eudaemon — Korridor begangen, jenseits gehandelt",
        "",
        f"**UTC:** {report['generated_at']}",
        f"**Meister Hasch:** binding · labor",
        f"**Cloud Run:** `{CLOUD_RUN}`",
        "",
        "## 1. Korridor (public edge)",
        "",
        "| Path | Status | Bytes | Kind | Plane hint |",
        "|------|--------|-------|------|------------|",
    ]
    for s in corridor:
        lines.append(
            f"| `{s.path}` | {s.status} | {s.bytes} | {s.kind} | {s.plane_hint} |"
        )
    lines.extend(
        [
            "",
            f"- SPA shells: **{len(spa_shells)}** · static assets: **{len(assets)}** · JSON APIs: **{len(json_apis)}**",
            "",
            "## 2. Andere Seite (Eudaemon)",
            "",
            "Agent handelt **operator-local**: Integrität, Self-Heal, Eudaimonia-Korridor, Lab-Pulse.",
            "",
        ]
    )
    if other:
        lines.append("| Action | OK | Detail |")
        lines.append("|--------|----|--------|")
        for a in other.get("actions", []):
            lines.append(f"| `{a['id']}` | {a['ok']} | {a.get('detail', '')} |")
        lines.append("")
        lines.append(f"**all_critical_ok:** {other.get('all_critical_ok')}")
        lines.append("")
        lines.append("## 3. Stance")
        lines.append("")
        for k, v in (other.get("stance") or {}).items():
            lines.append(f"- **{k}:** {v}")
    lines.extend(
        [
            "",
            "## Geltung",
            "",
            "Korridor-HTTP = **Satz**. Eudaemon-Lab-Aktionen = **Satz**. Keine Offensive.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["evidence_paths"] = {
        "summary": str(SUMMARY),
        "alert": str(ALERT),
        "markdown": str(REPORT_MD),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Eudaemon: walk corridor, act on other side")
    p.add_argument("--no-walk", action="store_true")
    p.add_argument("--no-act", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    r = run_eudaemon(walk=not args.no_walk, act=not args.no_act, seed=args.seed)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        c = r["corridor"]
        print(
            f"[eudaemon] corridor spa={c['spa_shell_count']} "
            f"assets={c['static_asset_count']} json_api={c['json_api_count']}"
        )
        o = r.get("other_side") or {}
        print(f"[eudaemon] other_side all_critical_ok={o.get('all_critical_ok')}")
        for a in o.get("actions") or []:
            print(f"  {'OK' if a['ok'] else 'NO'} {a['id']}: {a.get('detail')}")
        print(f"  report: {r['evidence_paths']['markdown']}")
    ok = True
    if r.get("other_side"):
        ok = bool(r["other_side"].get("all_critical_ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
