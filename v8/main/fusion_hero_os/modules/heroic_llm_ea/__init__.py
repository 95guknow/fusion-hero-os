"""HeroicLLM-EA Orchestrator — LLM-Vorschläge + evolutionäre Auswahl."""

from fusion_hero_os.modules.heroic_llm_ea.orchestrator import HeroicLLMEAOrchestrator
from fusion_hero_os.modules.heroic_llm_ea.providers import (
    CallableLLMProvider,
    CampfireTemplateProvider,
    StubLLMProvider,
)

__all__ = [
    "HeroicLLMEAOrchestrator",
    "CallableLLMProvider",
    "CampfireTemplateProvider",
    "StubLLMProvider",
]