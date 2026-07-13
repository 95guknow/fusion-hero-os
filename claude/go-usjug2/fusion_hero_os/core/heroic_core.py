# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.8 — HeroicCore (zentraler Aggregator)

Dies ist der eine Ort, an dem **alle** epistemischen und operationalen
Konzepte des Heroic Core zusammenkommen und für den Rest des Repos
verfügbar gemacht werden.

Enthält:
- MasterSeed (Integrity + Contraction)
- SisyphosCycle (Eudaimonia-Gerüst)
- FailClosed Enforcement
- PsycholysisTrigger (mit somatischer Pflicht)
- UnifiedHeroicLLMCore (LLM/Agenten-Brain)

Andere Module (QUBOIntegration, Agents, SelfModify, heroic_llm_ea, Dispatcher, etc.)
können sich hier registrieren oder die Methoden nutzen, um "heroic" zu werden.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from .heroic_core_orchestrator import MasterSeed, QuadCoreBridge
    from .universal_llm_router import get_unified_llm_core, UnifiedHeroicLLMCore
    from .psycholysis_trigger import PsycholysisTrigger
    from .universal_llm_router import SisyphosCycle, FailClosed   # aus v8.7
except Exception:
    MasterSeed = None
    QuadCoreBridge = None
    UnifiedHeroicLLMCore = None
    PsycholysisTrigger = None
    SisyphosCycle = None
    FailClosed = None


class HeroicCore:
    """
    Der ultimative zentrale Heroic Core Aggregator v8.8.

    Alle anderen Funktionen, Module und Agenten im Repo sollten idealerweise
    über dieses Objekt oder dessen Interfaces mit dem philosophischen
    Fundament interagieren.
    """

    def __init__(self, quad_core: Optional[QuadCoreBridge] = None):
        self.quad_core = quad_core
        self.masterseed: Optional[MasterSeed] = getattr(quad_core, "seed", None) if quad_core else None
        self.llm: Optional[UnifiedHeroicLLMCore] = get_unified_llm_core(heroic_core=quad_core) if quad_core else None
        self.sisyphos: Optional[SisyphosCycle] = getattr(self.llm, "sisyphos", None) if self.llm else None
        self.psycholysis: Optional[PsycholysisTrigger] = getattr(self.llm, "psycholysis", None) if self.llm else None
        self.fail_closed = FailClosed if FailClosed else None

        self.registered_modules: Dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        """Registriert ein beliebiges Modul (QUBO, Agent, SelfModify, ...), damit es
        später heroic-Verhalten nutzen oder triggern kann."""
        self.registered_modules[name] = module

    def get_llm(self) -> Optional[UnifiedHeroicLLMCore]:
        return self.llm

    def get_sisyphos_state(self) -> Dict[str, Any]:
        if self.sisyphos:
            return self.sisyphos.get_state()
        return {}

    def enforce_fail_closed(self, operation: str = "module_operation"):
        """Gibt den FailClosed-Kontextmanager zurück, den andere Module nutzen können."""
        if self.fail_closed:
            return self.fail_closed.enforce(core=self, operation=operation)
        return self._dummy_context()

    @staticmethod
    def _dummy_context():
        import contextlib
        @contextlib.contextmanager
        def _dummy():
            yield
        return _dummy()

    def trigger_psycholysis_if_needed(self, load: float = 0.8) -> Optional[Dict[str, Any]]:
        if self.psycholysis and self.sisyphos and self.sisyphos.load > load:
            return self.psycholysis.trigger({"source": "heroic_core", "load": load})
        return None

    def status(self) -> Dict[str, Any]:
        return {
            "version": "v8.8-heroic-core-aggregator",
            "masterseed_integrity": self.masterseed.verify_integrity(self.masterseed.state_hash()) if self.masterseed else None,
            "sisyphos": self.get_sisyphos_state(),
            "llm_version": self.llm._version if self.llm else None,
            "registered_modules": list(self.registered_modules.keys()),
            "psycholysis_available": self.psycholysis is not None,
        }


_heroic_core_instance: Optional[HeroicCore] = None

def get_heroic_core(quad_core: Optional[QuadCoreBridge] = None) -> HeroicCore:
    global _heroic_core_instance
    if _heroic_core_instance is None:
        _heroic_core_instance = HeroicCore(quad_core=quad_core)
    return _heroic_core_instance
