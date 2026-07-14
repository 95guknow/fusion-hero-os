"""
integration/mesh_connectors.py — Mesh Connector Registry

Ehrlicher Status: PLATZHALTER. orchestrator.py referenziert
MeshConnectorRegistry hinter dem Feature-Flag `config.mesh_connectors.enabled`
(siehe mesh_connectors.yaml fuer die deklarierte Konfiguration), aber es gibt
noch keine echte Implementierung, die Mesh-Connectoren tatsaechlich verbindet.
Diese Klasse existiert nur, damit der Import aufloest und initialize_integration_hub()
nicht mit einem ImportError abbricht, falls das Flag aktiviert wird - jeder
echte Aufruf ist noch nicht implementiert und sagt das auch so.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MeshConnectorRegistry:
    """PLATZHALTER-STUB - noch NICHT implementiert. Siehe Modul-Docstring."""

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.connectors: Dict[str, Any] = {}

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": False,
            "reason": "noch nicht implementiert (PLATZHALTER-STUB)",
            "connectors": list(self.connectors.keys()),
        }

    def connect(self, name: str) -> None:
        raise NotImplementedError(
            f"MeshConnectorRegistry.connect({name!r}) ist noch nicht implementiert."
        )
