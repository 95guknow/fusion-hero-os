# -*- coding: utf-8 -*-
"""
ClassicalBackend — epistemisches Gateway für qb_qubo.py.

Dreistufige Kontrollkaskade:
  1. Pre-Solve-Audit  (Struktur-Hygiene, Modal-Kollaps-Schutz)
  2. Execution-Layer  (Numba-JIT Engine)
  3. Post-Solve-Audit (Eudaimonia-Validierung)
"""
from __future__ import annotations

import time
from typing import Optional

from backends.base import SolverBackend
from domain.entities import QUBOProblem, QUBOSolverConfig, SolverResult


class EudaimoniaGuard:
    """Layer-0 Grenzwertüberwachung nach ALTE_FRAU_95g."""

    ENERGY_CEILING = 1e6

    @classmethod
    def validate_result(cls, result: SolverResult) -> dict:
        alerts = []
        if result.energy > cls.ENERGY_CEILING:
            alerts.append("Divergenter Energiewert außerhalb des eudaimonischen Korridors.")
        try:
            from foundation import check_foundation_gate
            report = check_foundation_gate(
                f"QUBO energy={result.energy:.6f} backend={result.backend}",
                require_explicit=False,
            )
            if not report.passed:
                alerts.append("Foundation gate: epistemische Hygiene offen")
        except Exception:
            pass
        return {"passed": len(alerts) == 0, "alerts": alerts}


class ClassicalBackend(SolverBackend):
    """Klassischer QUBO-Solver-Backend mit qb_qubo-Engine und Audit-Kaskade."""

    def __init__(self, audit_agent=None, meta_analyzer=None):
        self.audit_agent = audit_agent
        self.meta_analyzer = meta_analyzer
        from qb_qubo import simulated_annealing, local_search
        self.solvers = {
            "simulated_annealing": simulated_annealing,
            "local_search": local_search,
        }

    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        if self.audit_agent:
            self.audit_agent.execute_hook("before_solve", {
                "matrix_Q": problem.Q, "timestamp": time.time(),
            })
            if self.meta_analyzer:
                issues = self.meta_analyzer.analyze(f"QUBO Dimension: {problem.Q.shape[0]}")
                if issues:
                    print(f"[WARN] Meta-Analyse Trigger: {issues}")

        start_time = time.time()
        solver_func = self.solvers.get(config.backend, self.solvers["simulated_annealing"])
        if config.backend == "simulated_annealing":
            x, energy = solver_func(problem.Q, steps=config.steps, T0=config.T0)
        elif config.backend == "local_search":
            x, energy = solver_func(problem.Q, iters=config.steps)
        else:
            x, energy = solver_func(problem.Q)

        result = SolverResult(
            solution=x,
            energy=energy,
            backend=config.backend,
            runtime_seconds=time.time() - start_time,
        )

        if self.audit_agent:
            eudaimonia = EudaimoniaGuard.validate_result(result)
            self.audit_agent.execute_hook("after_solve", {
                "result": result, "eudaimonia": eudaimonia,
            })
        return result