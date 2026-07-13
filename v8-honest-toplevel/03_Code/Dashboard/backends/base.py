# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

from domain.entities import QUBOProblem, QUBOSolverConfig, SolverResult


class SolverBackend(ABC):
    @abstractmethod
    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        pass