"""Image-Provider-Protokoll — Dry-Run default (connectors-Pattern)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol


class ImageProvider(Protocol):
    def render(self, built_prompt: str, *, metadata: Optional[dict] = None) -> Dict[str, Any]: ...


class DryRunImageProvider:
    """Kein echter API-Call — liefert Plan-Dict."""

    def render(self, built_prompt: str, *, metadata: Optional[dict] = None) -> Dict[str, Any]:
        return {
            "would_execute": False,
            "mode": "dry_run",
            "built_prompt": built_prompt,
            "artifact": None,
            "note": "Explizites User-Opt-in nötig für echten Provider",
            "metadata": metadata or {},
        }


class CallableImageProvider:
    """Injection für echte Provider (z. B. nach Opt-in)."""

    def __init__(self, fn) -> None:
        self._fn = fn

    def render(self, built_prompt: str, *, metadata: Optional[dict] = None) -> Dict[str, Any]:
        return self._fn(built_prompt, metadata=metadata)