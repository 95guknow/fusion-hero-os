"""
Nibelungen-Saga + Grimm KHM + Siegfried-Moment — narrative mythos organ.

Additive to Fable5/Mythos5 · public-safe · labor only.
Does NOT claim saga = code proof. Does NOT ship exploit payloads.

Geltung: Spezifikation (file presence, YAML load) · MODELL (narrative maps)
Policy: dry_run_default · sandbox_only · no_external_targets · public_safe_output
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
MYTHOS_DIR = ROOT / "docs" / "mythos"

DOC_RELPATHS: tuple[str, ...] = (
    "docs/mythos/README.md",
    "docs/mythos/SIEGFRIED_MOMENT.md",
    "docs/mythos/NIBELUNGEN_SAGA.md",
    "docs/mythos/GRIMM_MAERCHEN_VOLLAUSGABE.md",
    "docs/mythos/nibelungen_grimm_map.yaml",
    "docs/mythos/KHM_INDEX.yaml",
)

__all__ = [
    "MythosConfig",
    "siegfried_moment_status",
    "grimm_lookup",
    "list_grimm_by_tag",
    "load_map",
    "run_self_check",
]


@dataclass
class MythosConfig:
    """Labor defaults — narrative organ only."""

    dry_run: bool = True
    sandbox_only: bool = True
    public_safe: bool = True
    platform: str = "13.0.0"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _try_yaml_load(path: Path) -> Any:
    """Load YAML if PyYAML available; else minimal line fallback for KHM index."""
    text = _read_text(path)
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        return {"_raw_path": str(path), "_yaml_fallback": True, "_chars": len(text)}


def load_map() -> dict[str, Any]:
    path = MYTHOS_DIR / "nibelungen_grimm_map.yaml"
    if not path.is_file():
        return {"ok": False, "error": "map_missing", "path": str(path)}
    data = _try_yaml_load(path)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "data": data}


def _load_khm_index() -> list[dict[str, Any]]:
    path = MYTHOS_DIR / "KHM_INDEX.yaml"
    if not path.is_file():
        return []
    data = _try_yaml_load(path)
    if isinstance(data, dict) and isinstance(data.get("tales"), list):
        return list(data["tales"])
    # Fallback: parse simple "- { khm: N, title_de: \"...\" }" lines
    tales: list[dict[str, Any]] = []
    for line in _read_text(path).splitlines():
        line = line.strip()
        if "khm:" not in line or "title_de:" not in line:
            continue
        try:
            # very small parser for flow-style mapping lines
            import re

            m = re.search(r"khm:\s*(\d+).*title_de:\s*\"([^\"]+)\"", line)
            if not m:
                continue
            entry: dict[str, Any] = {"khm": int(m.group(1)), "title_de": m.group(2)}
            tm = re.search(r"tags:\s*\[([^\]]*)\]", line)
            if tm:
                tags = [t.strip() for t in tm.group(1).split(",") if t.strip()]
                entry["tags"] = tags
            tales.append(entry)
        except Exception:
            continue
    return tales


def grimm_lookup(khm: int) -> dict[str, Any]:
    """Return KHM entry by number or not_found."""
    for tale in _load_khm_index():
        if int(tale.get("khm", -1)) == int(khm):
            return {"ok": True, "tale": tale, "geltung": "Modell"}
    return {"ok": False, "error": "not_found", "khm": khm}


def list_grimm_by_tag(tag: str) -> dict[str, Any]:
    tag_l = tag.strip().lower()
    hits = []
    for tale in _load_khm_index():
        tags = [str(t).lower() for t in tale.get("tags") or []]
        if tag_l in tags:
            hits.append(tale)
    return {
        "ok": True,
        "tag": tag,
        "count": len(hits),
        "tales": hits,
        "geltung": "Modell",
    }


def siegfried_moment_status(cfg: MythosConfig | None = None) -> dict[str, Any]:
    """
    Labor status of the Siegfried-Moment layer (docs + map presence).
    Does not claim realraum invulnerability.
    """
    cfg = cfg or MythosConfig()
    if not cfg.sandbox_only:
        raise RuntimeError("nibelungen_mythos requires sandbox_only=True")

    docs: list[dict[str, Any]] = []
    all_present = True
    for rel in DOC_RELPATHS:
        p = ROOT / rel
        present = p.is_file()
        all_present = all_present and present
        docs.append(
            {
                "path": rel,
                "present": present,
                "bytes": p.stat().st_size if present else 0,
            }
        )

    tales = _load_khm_index()
    mmap = load_map()

    return {
        "organ": "siegfried_moment",
        "platform": cfg.platform,
        "timestamp": datetime.now(UTC).isoformat(),
        "dry_run": cfg.dry_run,
        "sandbox_only": cfg.sandbox_only,
        "public_safe": cfg.public_safe,
        "definition": (
            "Harter Speer der Hypertarnkappe durchbricht Drachenhaut "
            "(public-safe expression; vault sealed)"
        ),
        "public_pole": "https://95guknow.github.io",
        "docs": docs,
        "docs_all_present": all_present,
        "khm_catalog_count": len(tales),
        "khm_expected_min": 200,
        "khm_catalog_ok": len(tales) >= 200,
        "map_ok": bool(mmap.get("ok")),
        "lindenblatt": [
            "code_honesty",
            "consent_fail_closed",
            "human_confirm_gate",
        ],
        "not_claimed": [
            "realraum_invulnerability",
            "saga_as_mathematical_satz",
            "exploit_as_dragon_slaying",
        ],
        "geltung": "Spezifikation (file checks) · Modell (narrative frame)",
        "status": "PASS" if all_present and len(tales) >= 200 else "PARTIAL",
    }


def run_self_check(cfg: MythosConfig | None = None) -> dict[str, Any]:
    """Aggregate self-check for registry / CLI."""
    cfg = cfg or MythosConfig()
    status = siegfried_moment_status(cfg)
    sample = grimm_lookup(50)
    tagged = list_grimm_by_tag("drachenkampf_volksform")
    return {
        "module": "core.nibelungen_mythos",
        "siegfried_moment": status,
        "sample_khm_50": sample,
        "tag_drachenkampf_volksform": {
            "count": tagged.get("count"),
            "titles": [t.get("title_de") for t in tagged.get("tales") or []],
        },
        "config": asdict(cfg),
    }


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2, ensure_ascii=False))
