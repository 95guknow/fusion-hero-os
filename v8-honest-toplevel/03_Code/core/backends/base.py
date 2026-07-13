"""Abstract base for QUBO solver backends."""

from abc import ABC, abstractmethod

from domain.config import QUBOSolverConfig
from domain.qubo_problem import QUBOProblem
from domain.solver_result import SolverResult


class SolverBackend(ABC):
    @abstractmethod
    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        pass