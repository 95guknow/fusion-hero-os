"""skill_creator — Dynamic skill scaffold proposals (P1 wiring, no longer a stub).

Produces *declarative* skill skeletons for human/CI review — does not auto-write
into live skill trees without explicit apply.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

MODULE_ID = "skill_creator"
PLATFORM = "10.0.0"


def status() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    skill_dirs = [
        root / "01_Framework" / "skills",
        root / ".grok" / "skills",
    ]
    found: list[str] = []
    for d in skill_dirs:
        if d.is_dir():
            found.extend(sorted(p.name for p in d.iterdir() if p.is_dir()))
    return {
        "module": MODULE_ID,
        "stub": False,
        "platform_version": PLATFORM,
        "existing_skills": found[:40],
        "skill_count": len(found),
        "ok": True,
    }


def propose_skill(
    name: str,
    purpose: str = "",
    triggers: list[str] | None = None,
) -> dict[str, Any]:
    """Build a SKILL.md skeleton (declarative only)."""
    slug = re.sub(r"[^a-z0-9_-]+", "-", name.strip().lower()).strip("-") or "new-skill"
    triggers = triggers or [slug.replace("-", " ")]
    body = f"""# {name.strip() or slug}

**Platform:** Fusion Hero OS v{PLATFORM}  
**Status:** proposed (not applied)

## Purpose

{purpose.strip() or "Describe the skill purpose."}

## Triggers

{chr(10).join(f"- {t}" for t in triggers)}

## Behaviour

1. Load mainframe / heroic core context when relevant.
2. Prefer mesh-only paths for audio (100.x).
3. Never auto-commit secrets; route pushes through push_layer_guard.

## Evolution

Proposals via SelfModify / peer review before core integration.
"""
    return {
        "module": MODULE_ID,
        "stub": False,
        "slug": slug,
        "skill_md": body,
        "applied": False,
        "note": "Declarative only — write path left to operator/CI",
        "ok": True,
    }


class SkillCreatorModule:
    name = MODULE_ID

    def process(self, payload: Any = None) -> dict[str, Any]:
        if not payload:
            return status()
        if isinstance(payload, dict):
            if payload.get("action") in (None, "status"):
                return status()
            return propose_skill(
                str(payload.get("name") or "new-skill"),
                str(payload.get("purpose") or ""),
                payload.get("triggers"),
            )
        return status()

    def propose_evolution(self, context: Any = None) -> None:
        return None
