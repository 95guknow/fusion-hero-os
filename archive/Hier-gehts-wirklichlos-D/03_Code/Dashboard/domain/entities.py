# -*- coding: utf-8 -*-
"""Domain entities for QUBO solver pipeline."""
from __future__ import annotations

import numpy as np


class QUBOProblem:
    def __init__(self, Q: np.ndarray):
        self.Q = np.asarray(Q, dtype=np.float64)


class SolverResult:
    def __init__(self, solution: np.ndarray, energy: float, backend: str, runtime_seconds: float):
        self.solution = solution
        self.energy = energy
        self.backend = backend
        self.runtime_seconds = runtime_seconds


class QUBOSolverConfig:
    def __init__(self, backend: str = "simulated_annealing", steps: int = 4000, T0: float = 2.0):
        self.backend = backend
        self.steps = steps
        self.T0 = T0