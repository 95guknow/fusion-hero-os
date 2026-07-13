# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.7 — Unified Heroic LLM Core

**Epistemische Begriffe jetzt mit executable Code belegt.**

Ausgehend vom besten aktuellen Stand (v8.6 Unified) wurde alles zu einem zusammengeführt
und die zentralen philosophischen/epistemischen Konzepte des Rekonstruktivistischen
Eudaimonismus / Heroic Core mit konkretem, lauffähigem Code versehen:

- MasterSeed (aktiv mit Integrity + Contraction Enforcement)
- Sisyphos-Zyklus (operationaler Zustandsautomat für dauerhafte Eudaimonia)
- Fail-Closed (erzwingbarer Kontext + Recovery)
- Psycholyse (integriert via PsycholysisTrigger mit somatischer Pflichtphase)

Python als primäre, sinnvolle Sprache für die High-Level-Orchestrierung
(mit Erweiterbarkeit auf Rust für schwere Verifikations-Tasks via bestehendes PMS-Kernel).

Dies ist der eine, kohärente Ort für alle LLM/Agenten-Interaktionen im gesamten Repo.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .heroic_core_orchestrator import QuadCoreBridge, MasterSeed

try:
    from ..providers.base import LLMResult, BaseLLMProvider
    from ..providers.claude_provider import ClaudeProvider
    from ..providers.grok_provider import GrokProvider
    from ..providers.everyapi_provider import EveryAPIProvider
    from ..providers.internal_provider import InternalFallbackProvider
    from .psycholysis_trigger import PsycholysisTrigger
except Exception:
    LLMResult = None
    BaseLLMProvider = object
    ClaudeProvider = GrokProvider = EveryAPIProvider = InternalFallbackProvider = None
    PsycholysisTrigger = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ======================================================================
# EPISDEMISCHE BEGRIFFE MIT CODE BELEGT (v8.7)
# ======================================================================

@dataclass
class SisyphosCycle:
    """
    Operationaler Sisyphos-Zyklus als tragfähiges Gerüst für verkörperte Eudaimonia.

    Der Zyklus oszilliert zwischen Last (load) und Zufriedenheit (satisfaction).
    Jeder Step erhöht die Zyklus-Zählung und berechnet die aktuelle Zufriedenheit.
    Dies ist die Code-Umsetzung des philosophischen Kerns: zufriedener Sisyphos.
    """
    load: float = 0.0
    satisfaction: float = 0.0
    cycles_completed: int = 0
    history: List[Dict[str, float]] = field(default_factory=list)

    def step(self, new_load: float) -> float:
        self.load = max(0.0, min(1.0, new_load))
        self.satisfaction = max(0.0, 1.0 - self.load * 0.7)  # vereinfachtes, stabiles Modell
        self.cycles_completed += 1
        self.history.append({"load": self.load, "satisfaction": self.satisfaction, "cycle": self.cycles_completed})
        if len(self.history) > 50:
            self.history.pop(0)
        return self.satisfaction

    def get_state(self) -> Dict[str, Any]:
        return {
            "load": self.load,
            "satisfaction": self.satisfaction,
            "cycles_completed": self.cycles_completed,
            "is_sustainable": self.satisfaction > 0.4 and self.load < 0.85,
        }


class FailClosed:
    """
    Fail-Closed Enforcement.

    Jede kritische Operation im Heroic Core muss in diesem Kontext laufen.
    Bei Verletzung wird Recovery (z.B. Phoenix-Mode) ausgelöst.
    Dies ist die Code-Umsetzung des zentralen Sicherheits- und Integritätsprinzips.
    """

    @staticmethod
    @contextlib.contextmanager
    def enforce(core: Optional[Any] = None, operation: str = "unknown"):
        try:
            yield
        except Exception as exc:
            if core and hasattr(core, "initiate_recovery"):
                core.initiate_recovery(reason=f"Fail-Closed breach in {operation}", error=str(exc))
            else:
                print(f"[FAIL-CLOSED v8.7] Breach in {operation}: {exc}")
            raise  # oder graceful degrade in Produktion


# ======================================================================
# UNIFIED HEROIC LLM CORE v8.7 (mit allen Begriffen operational)
# ======================================================================

class UnifiedHeroicLLMCore:
    """
    Der eine, wahre, zentrale LLM/Agenten-Orchestrator von Fusion Hero OS v8.7.

    Alle epistemischen Kernbegriffe sind hier mit lauffähigem Code belegt und
    in die dynamische Zuweisung + Heroic Context Injection integriert.
    """

    def __init__(self, heroic_core: Optional["QuadCoreBridge"] = None) -> None:
        self.heroic_core = heroic_core
        self._providers: Dict[str, BaseLLMProvider] = {}

        for Prov in (ClaudeProvider, GrokProvider, EveryAPIProvider):
            if Prov:
                p = Prov()
                if p.is_available():
                    self._providers[p.name] = p

        internal = InternalFallbackProvider(heroic_core=heroic_core)
        self._providers[internal.name] = internal

        # Epistemische Begriffe als first-class Members
        self.sisyphos = SisyphosCycle()
        self.psycholysis = PsycholysisTrigger() if PsycholysisTrigger else None
        self.fail_closed = FailClosed

        # MasterSeed wird vom heroic_core übernommen oder neu instanziiert
        self.masterseed: Optional[MasterSeed] = getattr(heroic_core, "seed", None) if heroic_core else None

        self._version = "v8.7-epistemic-grounded"

    def _build_heroic_context(self) -> str:
        sisy = self.sisyphos.get_state() if hasattr(self, "sisyphos") else {}
        base = "Fusion Hero OS v8.7 | Unified Heroic LLM Core | Sisyphos-Zyklus aktiv"
        if self.masterseed:
            verified = self.masterseed.verify_integrity(self.masterseed.state_hash())
            base += f" | MasterSeed: {'VERIFIZIERT' if verified else 'CHECK NEEDED'}"
        base += f" | Fail-Closed enforced | Psycholyse verfügbar: {self.psycholysis is not None}"
        base += f" | Aktueller Sisyphos: satisfaction={sisy.get('satisfaction', 0):.2f}"
        return base

    def _classify(self, prompt: str) -> str:
        p = prompt.lower()
        if any(kw in p for kw in ["code", "programmier", "script", "debug", "qubo"]):
            return "code"
        if any(kw in p for kw in ["heute", "aktuell", "news"]):
            return "current_events"
        if any(kw in p for kw in ["was ist", "definition"]):
            return "simple_fact"
        if any(kw in p for kw in ["schreib", "erzähl", "vision"]):
            return "creative"
        if any(kw in p for kw in ["masterseed", "sisyphos", "fail-closed", "psycholyse", "heroic"]):
            return "heroic_core"
        return "default"

    def _score(self, name: str, category: str) -> float:
        prov = self._providers.get(name)
        if not prov:
            return 0.0
        cap = prov.capabilities.get(category, prov.capabilities.get("default", 0.55))
        h = prov.health()
        lat_pen = min(h.get("last_latency_ms", 900) / 2800, 0.75)
        fail_pen = min(h.get("failure_count", 0) / 9, 0.65)
        heroic_boost = 0.18 if (name == "fusion-hero" and category == "heroic_core") else 0.0
        return max(0.08, min(0.97, cap * 0.62 - lat_pen * 0.22 - fail_pen * 0.16 + heroic_boost))

    def get_best_assignment(self, prompt: str) -> Dict[str, Any]:
        category = self._classify(prompt)
        scored = [(name, self._score(name, category)) for name in self._providers]
        scored.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = scored[0]
        return {
            "provider": best_name,
            "score": round(best_score, 4),
            "category": category,
            "reason": f"{category} | sisyphos_satisfaction={self.sisyphos.satisfaction:.2f}",
            "alternatives": scored[1:3],
        }

    def ask(self, prompt: str, system_prompt: Optional[str] = None,
            force_provider: Optional[str] = None, context: str = "heroic") -> LLMResult:
        assignment = self.get_best_assignment(prompt)
        chosen = force_provider if force_provider in self._providers else assignment["provider"]
        provider = self._providers[chosen]

        sys = system_prompt
        if context == "heroic" and not system_prompt:
            sys = self._build_heroic_context()

        # Fail-Closed Enforcement um die kritische Operation
        with self.fail_closed.enforce(core=self, operation="llm.ask"):
            start = time.time()
            try:
                result = provider.generate(prompt, system_prompt=sys, category=assignment["category"])
                result.fallback_chain = [chosen]
                result.meta.update({
                    "assignment": assignment,
                    "unified_core_version": self._version,
                    "sisyphos_state": self.sisyphos.get_state(),
                    "heroic_context_injected": context == "heroic",
                })
                # Sisyphos-Cycle updaten (Last als Proxy für Prompt-Komplexität)
                complexity = min(1.0, len(prompt) / 800)
                self.sisyphos.step(complexity)
                return result
            except Exception as e:
                # Psycholyse-Trigger bei hoher Last
                if self.psycholysis and self.sisyphos.load > 0.75:
                    try:
                        session = self.psycholysis.trigger({"prompt": prompt[:100], "reason": "high_load"})
                        result.meta["psycholysis_triggered"] = session
                    except Exception:
                        pass
                raise

    async def aask(self, prompt: str, system_prompt: Optional[str] = None, context: str = "heroic") -> LLMResult:
        return await asyncio.to_thread(self.ask, prompt, system_prompt, None, context)

    def initiate_recovery(self, reason: str = "", error: str = ""):
        """Wird von FailClosed aufgerufen. Kann später Phoenix-Mode triggern."""
        print(f"[v8.7 RECOVERY] {reason} | {error}")
        if self.heroic_core and hasattr(self.heroic_core, "invoke_phoenix_mode"):
            self.heroic_core.invoke_phoenix_mode()

    def status(self) -> Dict[str, Any]:
        return {
            "version": self._version,
            "providers": list(self._providers.keys()),
            "sisyphos": self.sisyphos.get_state(),
            "fail_closed_active": True,
            "psycholysis_available": self.psycholysis is not None,
            "masterseed_integrity": self.masterseed.verify_integrity(self.masterseed.state_hash()) if self.masterseed else None,
            "heroic_core_connected": self.heroic_core is not None,
        }


_unified_instance: Optional[UnifiedHeroicLLMCore] = None

def get_unified_llm_core(heroic_core: Optional["QuadCoreBridge"] = None) -> UnifiedHeroicLLMCore:
    global _unified_instance
    if _unified_instance is None:
        _unified_instance = UnifiedHeroicLLMCore(heroic_core=heroic_core)
    elif heroic_core and not _unified_instance.heroic_core:
        _unified_instance.heroic_core = heroic_core
    return _unified_instance


get_universal_llm_router = get_unified_llm_core
UniversalLLMRouter = UnifiedHeroicLLMCore


if __name__ == "__main__":
    core = get_unified_llm_core()
    print("v8.7 Status:", core.status())
    res = core.ask("Wie fühlt sich der Sisyphos-Zyklus in Code an?")
    print(f"Provider: {res.provider} | Sisyphos satisfaction: {res.meta.get('sisyphos_state', {}).get('satisfaction')}")
