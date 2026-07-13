"""
HeroGuideCore v7.12 - Unified Layer
Vereinheitlichte HERO-GUIDE Schicht für den ALTE_Frau_95g Heroic Core.

Dieses Modul dient als zentrale Abstraktionsschicht zwischen Core und Präsentation (z.B. NiceGUI).
"""

from typing import Dict, Any, Optional
from enum import Enum


class GuideMode(Enum):
    DASHBOARD = "dashboard"
    BOOK = "book"
    THEORY = "theory"
    SYSTEM = "system"


class HeroGuideCore:
    """
    Vereinheitlichter HERO-GUIDE Layer.
    NiceGUI ist nur eine mögliche Präsentationsschicht darüber.
    """

    def __init__(self):
        self.current_mode: GuideMode = GuideMode.DASHBOARD
        self.registered_views: Dict[str, Any] = {}
        self.core_connection_active: bool = True

    def set_mode(self, mode: GuideMode):
        """Wechselt den aktuellen Guide-Modus."""
        self.current_mode = mode

    def register_view(self, name: str, handler: Any):
        """Registriert eine View (z.B. NiceGUI Seite)."""
        self.registered_views[name] = handler

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_mode": self.current_mode.value,
            "registered_views": list(self.registered_views.keys()),
            "core_connected": self.core_connection_active,
            "description": "Unified HeroGuide Layer - NiceGUI is one presentation layer only"
        }

    def route_request(self, view_name: str, data: Optional[Dict] = None) -> Any:
        """Einfaches Routing zu registrierten Views."""
        if view_name in self.registered_views:
            return self.registered_views[view_name](data)
        return {"error": f"View '{view_name}' not found"}


# Globale Instanz
hero_guide = HeroGuideCore()