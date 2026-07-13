from backends.base import SolverBackend
from domain.qubo_problem import QUBOProblem
from domain.solver_result import SolverResult
from domain.config import QUBOSolverConfig
import time

class ClassicalBackend(SolverBackend):
    """Classical QUBO solver backend using qb_qubo.py functions."""

    def __init__(self):
        try:
            from qb_qubo import simulated_annealing, local_search
            self.solvers = {
                "simulated_annealing": simulated_annealing,
                "local_search": local_search
            }
            self.available = True
        except ImportError:
            self.available = False

    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        if not self.available:
            raise RuntimeError("qb_qubo module not available.")

        start = time.time()
        solver_func = self.solvers.get(config.backend, self.solvers["simulated_annealing"])
        x, energy = solver_func(problem.Q)
        runtime = time.time() - start

        return SolverResult(
            solution=x,
            energy=energy,
            backend=config.backend,
            runtime_seconds=runtime
        )
