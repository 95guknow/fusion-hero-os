# -*- coding: utf-8 -*-
"""
AscensionOS v9.0 - Inside-Out Generational Evolution Engine (Fixed)

Korrigierte Version:
- Bessere Kompatibilität mit realen State-Daten (SisyphosCycle.get_state())
- Robustere Fitness-Bewertung
- Bessere Simulation von Generationen
- Package-Struktur korrigiert
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Generation:
    number: int
    timestamp: str
    core_state: Dict[str, Any]
    improvements: List[str] = field(default_factory=list)
    fitness_score: float = 0.0
    notes: str = ""


class GenerationalEvolutionEngine:
    """
    Inside-Out Generational Evolution Engine für AscensionOS.

    Jede Generation beginnt im Kern und arbeitet nach außen.
    """

    def __init__(self, ascension_core: Any = None):
        self.ascension_core = ascension_core
        self.generations: List[Generation] = []
        self.current_generation = 0

    def evaluate_fitness(self, core_state: Dict[str, Any]) -> float:
        """
        Bewertet Fitness basierend auf tatsächlich vorhandenen Keys
        aus SisyphosCycle.get_state() und anderen Komponenten.
        """
        score = 50.0  # Basiswert

        # SisyphosCycle State (realistische Keys)
        if "is_sustainable" in core_state:
            if core_state.get("is_sustainable"):
                score += 20
            else:
                score -= 10

        if "satisfaction" in core_state:
            satisfaction = core_state["satisfaction"]
            score += (satisfaction - 0.5) * 30  # -15 bis +15

        if "load" in core_state:
            load = core_state["load"]
            if load > 0.85:
                score -= 15
            elif load < 0.4:
                score += 5

        # Weitere Ascension-Eigenschaften (falls vorhanden)
        if core_state.get("fail_closed_active"):
            score += 10
        if core_state.get("masterseed_integrity"):
            score += 10
        if core_state.get("ascension_mode_active"):
            score += 15

        return max(0.0, min(100.0, score))

    def propose_improvements(self, current_state: Dict[str, Any]) -> List[str]:
        improvements = []

        if current_state.get("is_sustainable") is False:
            improvements.append("Improve SisyphosCycle sustainability (core layer)")

        if current_state.get("satisfaction", 0.5) < 0.6:
            improvements.append("Increase overall system satisfaction / reduce load")

        if current_state.get("load", 0.5) > 0.8:
            improvements.append("Reduce system load through better task distribution")

        if not current_state.get("fail_closed_active"):
            improvements.append("Activate/strengthen FailClosed across layers")

        if not current_state.get("ascension_mode_active"):
            improvements.append("Enable full Ascension mode in QuadCoreBridge")

        if not improvements:
            improvements.append("Fine-tune cross-layer integration and self-reflection")

        return improvements

    def run_generation(self, current_state: Dict[str, Any]) -> Generation:
        self.current_generation += 1

        improvements = self.propose_improvements(current_state)
        fitness = self.evaluate_fitness(current_state)

        new_gen = Generation(
            number=self.current_generation,
            timestamp=datetime.now().isoformat(),
            core_state=current_state.copy(),
            improvements=improvements,
            fitness_score=fitness,
        )

        self.generations.append(new_gen)
        return new_gen

    def run_generations(self, initial_state: Dict[str, Any], generations: int = 10) -> List[Generation]:
        results = []
        state = initial_state.copy()

        for _ in range(generations):
            gen = self.run_generation(state)
            results.append(gen)

            # Realistischere State-Transition
            if "satisfaction" in state:
                state["satisfaction"] = min(1.0, state["satisfaction"] + 0.03)
            if "load" in state:
                state["load"] = max(0.0, state["load"] - 0.02)
            if "is_sustainable" in state:
                state["is_sustainable"] = state.get("satisfaction", 0) > 0.55 and state.get("load", 1) < 0.75

            state["ascension_mode_active"] = True
            state["fail_closed_active"] = True

        return results

    def get_evolution_summary(self) -> Dict[str, Any]:
        if not self.generations:
            return {"status": "No generations run yet"}

        return {
            "total_generations": len(self.generations),
            "final_fitness": round(self.generations[-1].fitness_score, 2),
            "average_fitness": round(sum(g.fitness_score for g in self.generations) / len(self.generations), 2),
            "latest_improvements": self.generations[-1].improvements,
            "fitness_trend": [round(g.fitness_score, 1) for g in self.generations[-5:]],
        }
