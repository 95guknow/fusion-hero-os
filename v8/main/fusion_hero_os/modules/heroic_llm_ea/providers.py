"""LLM-Provider für HeroicLLM-EA — austauschbar, kein hartkodierter Dienst."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Protocol

import yaml

_TEMPLATES_PATH = Path(__file__).parent / "config" / "campfire_templates.yaml"


class LLMProvider(Protocol):
    def propose(self, prompt: str, n: int = 1, *, context: Optional[dict] = None) -> List[str]: ...


class StubLLMProvider:
    """Deterministischer Stub — kein Netzwerk."""

    def propose(self, prompt: str, n: int = 1, *, context: Optional[dict] = None) -> List[str]:
        base = prompt.strip() or "empty-prompt"
        return [f"{base}::variant-{i}" for i in range(max(1, n))]


class CallableLLMProvider:
    """Wraps eine Callable — für echte Provider-Injection."""

    def __init__(self, fn: Callable[[str, int], List[str]]) -> None:
        self._fn = fn

    def propose(self, prompt: str, n: int = 1, *, context: Optional[dict] = None) -> List[str]:
        return self._fn(prompt, n)


class CampfireTemplateProvider:
    """
    Campfire-Pilot: variiert Prompts aus YAML-Templates (kein echter Bild-/LLM-API-Call).
    """

    def __init__(self, templates_path: Optional[Path] = None) -> None:
        self.templates_path = templates_path or _TEMPLATES_PATH
        self._templates = self._load()

    def _load(self) -> List[str]:
        if not self.templates_path.exists():
            return [
                "cyberpunk campfire: {prompt} — therefore alternative next step",
                "meme theory: {prompt} — quelle: heroic core — risiko: offen",
            ]
        with open(self.templates_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return list(data.get("templates", []))

    def propose(self, prompt: str, n: int = 1, *, context: Optional[dict] = None) -> List[str]:
        theme = (context or {}).get("theme", "campfire")
        out: List[str] = []
        for i, tmpl in enumerate(self._templates[: max(n, 1)]):
            out.append(tmpl.format(prompt=prompt, theme=theme, variant=i))
        while len(out) < n:
            out.append(f"{prompt}::campfire-extra-{len(out)}")
        return out[:n]