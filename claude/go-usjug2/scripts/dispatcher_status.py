#!/usr/bin/env python3
"""Entwickler-Utility: baut den Standard-Dispatcher auf und zeigt, welche
Core-Module registriert sind. Praktisch für einen schnellen manuellen Check
("ist die Verdrahtung intakt?"), ohne extra Testcode zu schreiben.

Nutzung:
    python scripts/dispatcher_status.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Erlaubt den Aufruf direkt aus scripts/ ohne vorheriges `pip install -e .`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fusion_hero_os.core.dispatcher import build_default_dispatcher  # noqa: E402


def main() -> None:
    dispatcher = build_default_dispatcher()
    modules = dispatcher.list_modules()
    print(f"Dispatcher aktiv mit {len(modules)} registrierten Core-Modulen:")
    for name in modules:
        print(f"  - {name}")

    proposals = dispatcher.collect_evolution_proposals()
    print(f"\nOffene Evolution-Vorschläge (ohne Kontext angefragt): {len(proposals)}")
    print("(Vorschläge entstehen nur, wenn ein Modul explizit mit Kontext "
          "aufgerufen wird -- siehe propose_evolution() je Modul.)")


if __name__ == "__main__":
    main()
