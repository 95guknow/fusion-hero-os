"""QUBO solver configuration."""

from __future__ import annotations


class QUBOSolverConfig:
    def __init__(
        self,
        backend: str = "simulated_annealing",
        steps: int = 4000,
        T0: float = 2.0,
    ):
        self.backend = backend
        self.steps = steps
        self.T0 = T0