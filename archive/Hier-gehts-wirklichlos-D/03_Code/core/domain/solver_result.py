"""Solver result container."""

from __future__ import annotations

import numpy as np


class SolverResult:
    def __init__(
        self,
        solution: np.ndarray,
        energy: float,
        backend: str,
        runtime_seconds: float,
    ):
        self.solution = solution
        self.energy = energy
        self.backend = backend
        self.runtime_seconds = runtime_seconds