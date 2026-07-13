"""GenerationalEvolutionProtocolCoreModule (BaseModule-Adapter).

Wrapt :class:`fusion_hero_os.engine.mainframe.GenerationalEvolutionProtocolCoreModule`
— eine echte (μ+λ)-Evolutionsstrategie über die Solver-Hyperparameter
(steps, T0, n_restarts) von ``parallel_anneal``. Das ist kein Stub: die
Fitness jeder Generation wird tatsächlich über den QUBO-Solver berechnet,
und die Elite-Fitness ist über die Generationen monoton nicht-fallend.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.engine.mainframe import (
    GenerationalEvolutionProtocolCoreModule as _EvolutionImpl,
)


class GenerationalEvolutionProtocolCoreModule(BaseModule):
    """``process(payload)`` erwartet optional ``{"n_generations": int}``
    (Default 1) und führt entsprechend viele echte (μ+λ)-Generationen aus.
    Konstruktor-Parameter (``n``, ``mu``, ``lam``, ``seed``, ``target_Q``)
    können über ``payload["init"]`` beim ersten Aufruf gesetzt werden.
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl: Optional[_EvolutionImpl] = None

    def _ensure_impl(self, init: Optional[Dict[str, Any]]) -> _EvolutionImpl:
        if self._impl is None:
            self._impl = _EvolutionImpl(**(init or {}))
        return self._impl

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        impl = self._ensure_impl(payload.get("init"))
        n_generations = int(payload.get("n_generations", 1))
        return impl.evolve(n_generations=n_generations)

    def status(self) -> Dict[str, Any]:
        """Aktueller Stand ohne eine neue Generation auszulösen."""
        if self._impl is None:
            return {"generation": 0, "best_fitness": None}
        return {
            "generation": self._impl.generation,
            "best_fitness": self._impl.best_fitness,
            "best_genome": dict(self._impl.best_genome) if self._impl.best_genome else None,
        }
