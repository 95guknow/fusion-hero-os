"""HeroicLLM-EA Orchestrator — Proposal Engine + Evolutionary Selector."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fusion_hero_os.core.base_module import BaseModule, ReviewCriterion, ReviewResult
from fusion_hero_os.modules.heroic_llm_ea.evolution import EvolutionConfig, EvolutionarySelector
from fusion_hero_os.modules.heroic_llm_ea.fitness import score_with_peer_review
from fusion_hero_os.modules.heroic_llm_ea.memory import MutationMemory, ProposalRecord
from fusion_hero_os.modules.heroic_llm_ea.providers import (
    CampfireTemplateProvider,
    CallableLLMProvider,
    LLMProvider,
    StubLLMProvider,
)


class HeroicLLMEAOrchestrator(BaseModule):
    """
    LLM Proposal Engine + (μ+λ) Evolutionary Selector.

    Actions (payload.action):
      - propose: einzelne Generation
      - evolve: mehrere Generationen
      - status: Memory-Snapshot
    """

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        super().__init__()
        self.llm: LLMProvider = llm or StubLLMProvider()
        self.selector = EvolutionarySelector()
        self.generation = 0

    @classmethod
    def with_campfire_templates(cls) -> "HeroicLLMEAOrchestrator":
        return cls(llm=CampfireTemplateProvider())

    def _score_proposal(self, text: str, context: Dict[str, Any]) -> ProposalRecord:
        scores = score_with_peer_review(text, context)
        return ProposalRecord(
            text=text,
            generation=self.generation,
            fitness=scores["fitness"],
            peer_review_score=scores["peer_review_score"],
            performance_score=scores["performance_score"],
            consistency_score=scores["consistency_score"],
        )

    def _propose_once(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(payload.get("prompt", ""))
        n_proposals = int(payload.get("n_proposals", 3))
        context = {k: v for k, v in payload.items() if k not in ("action",)}
        proposals = self.llm.propose(prompt, n=n_proposals, context=context)
        result = self.selector.run_generation(proposals, self.generation, context)
        self.generation += 1
        result["status"] = self._provider_status()
        return result

    def _evolve_many(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        n_generations = int(payload.get("n_generations", 3))
        history: List[Dict[str, Any]] = []
        for _ in range(n_generations):
            history.append(self._propose_once(payload))
        return {
            "action": "evolve",
            "generations_run": n_generations,
            "history": history,
            "final_best": history[-1]["best"] if history else None,
            "status": self._provider_status(),
        }

    def _provider_status(self) -> str:
        if isinstance(self.llm, StubLLMProvider):
            return "stub_llm"
        if isinstance(self.llm, CampfireTemplateProvider):
            return "campfire_templates"
        if isinstance(self.llm, CallableLLMProvider):
            return "callable_llm"
        return "external_llm"

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        action = payload.get("action", "propose")
        if action == "evolve":
            return self._evolve_many(payload)
        if action == "status":
            return {
                "action": "status",
                "generation": self.generation,
                "memory": self.selector.memory.snapshot(),
                "status": self._provider_status(),
            }
        if payload.get("init"):
            init = payload["init"]
            self.selector = EvolutionarySelector(
                EvolutionConfig(
                    mu=int(init.get("mu", 2)),
                    lam=int(init.get("lam", 4)),
                )
            )
        return self._propose_once(payload)

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        has_real_llm = self._provider_status() == "external_llm"
        criteria = [
            ReviewCriterion("LLM-Interface austauschbar", True),
            ReviewCriterion("(μ+λ)-Evolution", True, f"mu={self.selector.config.mu} lam={self.selector.config.lam}"),
            ReviewCriterion("5-Dim PeerReview in Fitness", True, "methodology.core_modules"),
            ReviewCriterion("Campfire-Templates", isinstance(self.llm, CampfireTemplateProvider)),
            ReviewCriterion("Echter LLM-Provider", has_real_llm, "Default: Stub oder Templates"),
            ReviewCriterion("Hierarchisches Mutations-Gedächtnis", True),
        ]
        return ReviewResult(module=self.name, criteria=criteria)