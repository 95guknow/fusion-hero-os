# core/GenerationalEvolutionProtocolCoreModule.py
# Version: v5.22

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class GenerationalEvolutionProtocolCoreModule:
    """Generational Evolution: Fitness aus Modul-Gesundheit, Selektion über Schwellwert."""

    def __init__(self, fitness_threshold: float = 0.72):
        self.generation = 0
        self.fitness_history: List[Dict[str, Any]] = []
        self.fitness_threshold = fitness_threshold
        self._last_selected: List[str] = []

    def _measure_fitness(self) -> Dict[str, Any]:
        try:
            from module_registry import signal_health, list_modules

            health = signal_health("delta")
            modules = list_modules()
            loaded = sum(1 for m in modules if m.get("loaded"))
            total = max(len(modules), 1)
            load_ratio = loaded / total
            ram = health.get("delta", {}).get("ram", 50.0)
            ram_penalty = max(0.0, (ram - 85.0) / 15.0)
            fitness = max(0.0, min(1.0, load_ratio * 0.6 + (1.0 - ram_penalty) * 0.4))
            return {
                "fitness": round(fitness, 4),
                "load_ratio": round(load_ratio, 4),
                "modules_loaded": loaded,
                "modules_total": total,
                "ram_pct": ram,
            }
        except Exception as exc:
            return {"fitness": 0.5, "error": str(exc)}

    def run_generation(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.generation += 1
        metrics = self._measure_fitness()
        fitness = metrics.get("fitness", 0.5)
        selected = []
        if fitness >= self.fitness_threshold:
            try:
                from module_registry import list_modules

                selected = [
                    m["name"] for m in list_modules()
                    if m.get("loaded") and m.get("enabled")
                ][:12]
            except Exception:
                selected = ["heroic_orchestration", "agent_control"]
        self._last_selected = selected

        record = {
            "generation": self.generation,
            "fitness": fitness,
            "selected_modules": selected,
            "survived": fitness >= self.fitness_threshold,
            "ts": time.time(),
            **metrics,
        }
        self.fitness_history.append(record)
        return {
            "generation": self.generation,
            "status": "completed",
            "fitness": fitness,
            "threshold": self.fitness_threshold,
            "survived": record["survived"],
            "selected_modules": selected,
        }

    def get_current_generation(self) -> int:
        return self.generation

    def status(self) -> Dict[str, Any]:
        last = self.fitness_history[-1] if self.fitness_history else None
        return {
            "generation": self.generation,
            "fitness_threshold": self.fitness_threshold,
            "history_len": len(self.fitness_history),
            "last_fitness": last.get("fitness") if last else None,
            "last_selected": self._last_selected,
        }