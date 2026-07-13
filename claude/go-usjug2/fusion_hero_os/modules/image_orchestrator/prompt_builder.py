"""Prompt-Builder aus Visual-Identity-Daten (YAML)."""

from __future__ import annotations

from typing import Any, Dict, List


def build_prompt(user_prompt: str, identity: Dict[str, Any]) -> str:
    """Kombiniert User-Prompt mit Character-Bible / Style-Tags."""
    name = identity.get("name", "ALTE_Frau_95g")
    tags: List[str] = list(identity.get("style_tags", []))
    palette = identity.get("palette", {})
    seed = identity.get("primary_seed", "")
    tag_str = ", ".join(tags) if tags else "heroic"
    colors = ", ".join(f"{k}={v}" for k, v in palette.items()) if palette else ""
    parts = [
        f"[{name}]",
        f"style: {tag_str}",
        user_prompt.strip(),
    ]
    if seed:
        parts.append(f"seed: {seed}")
    if colors:
        parts.append(f"palette: {colors}")
    return " | ".join(p for p in parts if p)


def validate_identity(identity: Dict[str, Any]) -> Dict[str, Any]:
    """Prüft Mindestfelder der Character Bible."""
    required = ["name", "style_tags"]
    missing = [k for k in required if not identity.get(k)]
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "tag_count": len(identity.get("style_tags", [])),
    }