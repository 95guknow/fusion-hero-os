"""Zentrale Konfiguration für Dispatcher und Core-Module.

Eine einzelne, dokumentierte Stelle für Laufzeit-Einstellungen statt
verstreuter ``os.getenv(...)``-Aufrufe in einzelnen Modulen.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Set


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_set(name: str) -> Set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


@dataclass(frozen=True)
class DispatcherConfig:
    """Laufzeit-Konfiguration für :mod:`fusion_hero_os.core.dispatcher`.

    - ``FUSION_DISPATCHER_MAX_WORKERS``: Obergrenze für parallele
      ``dispatch_many``-Ausführung (Default: ``None`` -> Python-Default,
      i.d.R. ``min(32, os.cpu_count() + 4)``).
    - ``FUSION_DISABLED_MODULES``: kommagetrennte Liste von Modulnamen, die
      ``build_default_dispatcher()`` NICHT registrieren soll (z.B. für
      Umgebungen ohne die für ein Modul nötigen optionalen Abhängigkeiten).
    """

    max_workers: int | None = field(default_factory=lambda: _max_workers_or_none())
    disabled_modules: Set[str] = field(default_factory=lambda: _env_set("FUSION_DISABLED_MODULES"))


def _max_workers_or_none() -> int | None:
    raw = os.getenv("FUSION_DISPATCHER_MAX_WORKERS")
    return int(raw) if raw and raw.isdigit() else None


_default_config: DispatcherConfig | None = None


def get_config() -> DispatcherConfig:
    global _default_config
    if _default_config is None:
        _default_config = DispatcherConfig()
    return _default_config
