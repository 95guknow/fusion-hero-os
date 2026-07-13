"""Hierarchisches Mutations-Gedächtnis für HeroicLLM-EA."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProposalRecord:
    text: str
    generation: int
    fitness: float
    peer_review_score: float
    performance_score: float
    consistency_score: float
    parent_id: Optional[str] = None
    mutation_op: str = "propose"
    created_at: float = field(default_factory=time.time)

    @property
    def proposal_id(self) -> str:
        return hashlib.sha256(f"{self.text}:{self.generation}".encode()).hexdigest()[:12]


class MutationMemory:
    """Generation → Elite-Proposals + Lineage (parent_id)."""

    def __init__(self, max_per_generation: int = 20) -> None:
        self._store: Dict[int, List[ProposalRecord]] = {}
        self.max_per_generation = max_per_generation
        self._lineage: Dict[str, str] = {}

    def remember(self, record: ProposalRecord) -> None:
        bucket = self._store.setdefault(record.generation, [])
        bucket.append(record)
        if record.parent_id:
            self._lineage[record.proposal_id] = record.parent_id
        bucket.sort(key=lambda r: r.fitness, reverse=True)
        if len(bucket) > self.max_per_generation:
            del bucket[self.max_per_generation:]

    def elites(self, generation: int, k: int = 1) -> List[ProposalRecord]:
        items = self._store.get(generation, [])
        return items[:k]

    def best(self, generation: Optional[int] = None) -> Optional[ProposalRecord]:
        if generation is not None:
            items = self._store.get(generation, [])
            return items[0] if items else None
        all_items = [r for gen in sorted(self._store) for r in self._store[gen]]
        return max(all_items, key=lambda r: r.fitness, default=None)

    def mutate_from_elite(self, elite: ProposalRecord, op: str = "suffix") -> str:
        if op == "suffix":
            return f"{elite.text} [mut:{elite.generation}:{op}]"
        if op == "prefix":
            return f"[mut:{op}] {elite.text}"
        return elite.text + " → alternative jedoch komprimiert"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generations": len(self._store),
            "total": sum(len(v) for v in self._store.values()),
            "best_fitness": (self.best().fitness if self.best() else None),
            "lineage_edges": len(self._lineage),
        }