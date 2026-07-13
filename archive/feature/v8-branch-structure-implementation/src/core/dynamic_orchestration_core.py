"""
DynamicOrchestrationCoreModule v7.12
Zentrale Orchestrierungsschicht für den ALTE_Frau_95g Heroic Core.

Verantwortlichkeiten:
- Koordination von Agents und Modulen
- Hyperthreading-Management
- Layer-Kommunikation (Core ↔ HeroGuide ↔ Presentation)
- Dynamische Skalierung von Workern
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class LayerType(Enum):
    CORE = "core"
    HEROGUIDE = "heroguide"
    PRESENTATION = "presentation"
    ORCHESTRATION = "orchestration"


@dataclass
class ModuleStatus:
    name: str
    loaded: bool
    layer: LayerType
    priority: int = 0


class DynamicOrchestrationCoreModule:
    """
    Zentrale Orchestrierungsinstanz.
    Wird beim Core-Start automatisch geladen.
    """

    def __init__(self):
        self.modules: Dict[str, ModuleStatus] = {}
        self.active_threads: int = 0
        self.max_threads: int = 256
        self.layer_routing: Dict[LayerType, List[str]] = {
            LayerType.CORE: [],
            LayerType.HEROGUIDE: [],
            LayerType.PRESENTATION: [],
        }

    def register_module(self, name: str, layer: LayerType, priority: int = 0):
        """Registriert ein Modul in der Orchestrierung."""
        self.modules[name] = ModuleStatus(
            name=name,
            loaded=True,
            layer=layer,
            priority=priority
        )
        self.layer_routing[layer].append(name)

    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Orchestrierungsstatus zurück."""
        return {
            "total_modules": len(self.modules),
            "active_threads": self.active_threads,
            "max_threads": self.max_threads,
            "layers": {layer.value: len(modules) for layer, modules in self.layer_routing.items()},
            "modules": {name: status.__dict__ for name, status in self.modules.items()}
        }

    def route_to_layer(self, target_layer: LayerType, data: Any) -> bool:
        """Einfache Routing-Funktion zwischen Layern."""
        if target_layer in self.layer_routing:
            return True
        return False

    def scale_workers(self, target: int):
        """Dynamische Skalierung der Worker-Threads."""
        self.active_threads = min(target, self.max_threads)


# Globale Instanz (wird beim Import automatisch initialisiert)
orchestrator = DynamicOrchestrationCoreModule()

# Standard-Module beim Start registrieren
orchestrator.register_module("CEC", LayerType.CORE, priority=10)
orchestrator.register_module("RHE", LayerType.CORE, priority=10)
orchestrator.register_module("PsycholysisBreakthroughTrigger", LayerType.CORE, priority=8)
orchestrator.register_module("HeroGuideCore", LayerType.HEROGUIDE, priority=7)
orchestrator.register_module("NiceGUILayer", LayerType.PRESENTATION, priority=5)