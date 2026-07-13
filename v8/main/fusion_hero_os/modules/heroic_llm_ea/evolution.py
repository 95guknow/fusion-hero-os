"""Evolutionary Selector (μ+λ) für Prompt-Populationen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fusion_hero_os.modules.heroic_llm_ea.fitness import score_with_peer_review
from fusion_hero_os.modules.heroic_llm_ea.memory import MutationMemory, ProposalRecord


@dataclass
class EvolutionConfig:
    mu: int = 2
    lam: int = 4
    mutation_ops: tuple = ("suffix", "prefix", "compress")


class EvolutionarySelector:
    """(μ+λ)-Selektion über Proposal-Texte mit Mutations-Gedächtnis."""

    def __init__(self, config: Optional[EvolutionConfig] = None) -> None:
        self.config = config or EvolutionConfig()
        self.memory = MutationMemory()

    def run_generation(
        self,
        proposals: List[str],
        generation: int,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        scored: List[ProposalRecord] = []
        for text in proposals:
            scores = score_with_peer_review(text, context)
            scored.append(
                ProposalRecord(
                    text=text,
                    generation=generation,
                    fitness=scores["fitness"],
                    peer_review_score=scores["peer_review_score"],
                    performance_score=scores["performance_score"],
                    consistency_score=scores["consistency_score"],
                )
            )
        scored.sort(key=lambda r: r.fitness, reverse=True)
        elites = scored[: self.config.mu]

        offspring: List[str] = []
        parent_ids: List[Optional[str]] = []
        for i, elite in enumerate(elites):
            for j in range(max(1, self.config.lam // max(1, len(elites)))):
                op = self.config.mutation_ops[(i + j) % len(self.config.mutation_ops)]
                child = self.memory.mutate_from_elite(elite, op=op)
                offspring.append(child)
                parent_ids.append(elite.proposal_id)

        child_records: List[ProposalRecord] = []
        for text, pid in zip(offspring, parent_ids):
            scores = score_with_peer_review(text, context)
            rec = ProposalRecord(
                text=text,
                generation=generation,
                fitness=scores["fitness"],
                peer_review_score=scores["peer_review_score"],
                performance_score=scores["performance_score"],
                consistency_score=scores["consistency_score"],
                parent_id=pid,
                mutation_op="mutate",
            )
            child_records.append(rec)

        pool = scored + child_records
        pool.sort(key=lambda r: r.fitness, reverse=True)
        next_elites = pool[: self.config.mu]

        for rec in pool:
            self.memory.remember(rec)

        best = next_elites[0]
        return {
            "generation": generation,
            "best": {
                "id": best.proposal_id,
                "text": best.text,
                "fitness": best.fitness,
                "peer_review_score": best.peer_review_score,
            },
            "elites": [
                {"id": e.proposal_id, "fitness": e.fitness, "text": e.text[:160]}
                for e in next_elites
            ],
            "offspring_count": len(offspring),
            "memory": self.memory.snapshot(),
        }