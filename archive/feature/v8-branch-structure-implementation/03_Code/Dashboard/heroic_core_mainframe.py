# -*- coding: utf-8 -*-
"""
HEROIC CORE MAINFRAME — INTEGRAL VERSION (v5.25)
================================================
  1. High-Performance Engine     → qb_qubo.py (Numba-JIT, O(n) Delta)
  2. Epistemisches Gateway       → backends/classical.py
  3. Core-Sicherheitslayer       → SelfModify, Evolution, MetaAnalysis
  4. Immutable Foundations       → AuditAgent + EudaimoniaGuard
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_DASH = Path(__file__).resolve().parent
for p in (_ROOT, _DASH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hyperthreading_config import parallel_workers
from domain.entities import QUBOProblem, QUBOSolverConfig, SolverResult
from backends.classical import ClassicalBackend, EudaimoniaGuard
import qb_qubo

make_Q = qb_qubo.make_Q
simulated_annealing = qb_qubo.simulated_annealing
local_search = qb_qubo.local_search
parallel_anneal = qb_qubo.parallel_anneal
warmup_kernels = qb_qubo.warmup_kernels


def parallel_worker_count(override=None):
    return parallel_workers(override)


# Re-exports für Abwärtskompatibilität
__all__ = [
    "QUBOProblem", "QUBOSolverConfig", "SolverResult", "ClassicalBackend",
    "EudaimoniaGuard", "SelfModifyCoreModule", "GenerationalEvolutionProtocolCoreModule",
    "CriticalMetaAnalysisCoreModule", "ExecutableAuditAgent",
    "QUBOIntegrationCoreModule", "make_Q", "simulated_annealing",
    "local_search", "parallel_anneal", "warmup_kernels", "parallel_worker_count",
]


class SelfModifyCoreModule:
    def __init__(self):
        self.modification_history = []
        self.audit_hooks = {}

    def register_audit_hook(self, name: str, func):
        self.audit_hooks[name] = func


class GenerationalEvolutionProtocolCoreModule:
    def __init__(self):
        self.generation = 0

    def run_generation(self):
        self.generation += 1
        return {"generation": self.generation, "status": "active"}


class CriticalMetaAnalysisCoreModule:
    def analyze(self, text: str) -> list:
        issues = []
        if "immer" in text.lower() or "nie" in text.lower():
            issues.append("Mögliche epistemische Inflation erkannt")
        return issues


class ExecutableAuditAgent:
    def __init__(self):
        self.execute_hook = None


class QUBOIntegrationCoreModule:
    """Zentrales Integrationsmodul — Dependency Injection + Hook-Interlocking."""

    def __init__(self):
        self.self_modify = SelfModifyCoreModule()
        self.evolution = GenerationalEvolutionProtocolCoreModule()
        self.meta_analyzer = CriticalMetaAnalysisCoreModule()
        self.audit_agent = ExecutableAuditAgent()
        self.backend = ClassicalBackend(
            audit_agent=self.audit_agent,
            meta_analyzer=self.meta_analyzer,
        )
        self._interlock_core_hooks()

    def _interlock_core_hooks(self):
        def pre_solve_audit_hook(payload):
            Q = payload.get("matrix_Q")
            if np.any(np.isnan(Q)) or np.any(np.isinf(Q)):
                raise ValueError(
                    "[CRITICAL] Epistemischer Kollaps: Ungültige Matrixzustände detektiert."
                )
            max_val = np.max(np.abs(Q))
            if max_val > 1e5:
                print("[AUDIT] Warnung: Hohe Penalty-Werte — Risiko Modal-Kollaps.")
            print("[AUDIT] Layer 1 (Pre-Solve): Strukturüberprüfung passed.")
            return True

        def post_solve_audit_hook(payload):
            result = payload.get("result")
            eudaimonia = payload.get("eudaimonia") or EudaimoniaGuard.validate_result(result)
            for alert in eudaimonia.get("alerts", []):
                print(f"[ALERT] {alert}")
            print(
                f"[AUDIT] Layer 3 (Post-Solve): Energie {result.energy:.4f} "
                f"({'OK' if eudaimonia.get('passed') else 'OFFEN'})"
            )
            return True

        self.self_modify.register_audit_hook("before_solve", pre_solve_audit_hook)
        self.self_modify.register_audit_hook("after_solve", post_solve_audit_hook)
        self.audit_agent.execute_hook = lambda name, data: self.self_modify.audit_hooks[name](data)

    def execute_secure_run(self, problem_matrix, config=None):
        gen_status = self.evolution.run_generation()
        print(f"\n[CORE MAINFRAME] Generation {gen_status['generation']}...")
        if config is None:
            config = QUBOSolverConfig(backend="simulated_annealing", steps=5000)
        return self.backend.solve(QUBOProblem(Q=problem_matrix), config)

    def execute_parallel_run(self, problem_matrix, steps=8000, T0=2.0,
                             n_restarts=None, n_samples=60):
        gen_status = self.evolution.run_generation()
        n_eff = n_restarts or parallel_worker_count()
        print(
            f"\n[CORE MAINFRAME] Parallele Generation {gen_status['generation']} "
            f"({n_eff} Restarts / {os.cpu_count()} Kerne)..."
        )
        Q = np.asarray(problem_matrix, dtype=np.float64)
        self.audit_agent.execute_hook("before_solve", {"matrix_Q": Q, "timestamp": time.time()})
        out = parallel_anneal(Q, steps=steps, T0=T0, n_restarts=n_restarts, n_samples=n_samples)
        audit_result = SolverResult(
            solution=out["solution"], energy=out["energy"],
            backend="parallel_annealing", runtime_seconds=out["runtime_seconds"],
        )
        eudaimonia = EudaimoniaGuard.validate_result(audit_result)
        self.audit_agent.execute_hook("after_solve", {"result": audit_result, "eudaimonia": eudaimonia})
        return out


if __name__ == "__main__":
    print("=" * 80)
    print("HEROIC CORE MAINFRAME (ALTE_FRAU_95g) — qb_qubo + classical.py")
    print("=" * 80)
    warmup_kernels()
    mainframe = QUBOIntegrationCoreModule()
    target_matrix = make_Q(12, submodular=False, scale=2.5)
    cfg = QUBOSolverConfig(backend="simulated_annealing", steps=8000, T0=2.5)
    result = mainframe.execute_secure_run(target_matrix, config=cfg)
    print("-" * 80)
    print("CORE-STATUS: STABIL // PRODUKTIONSBEREIT")
    print(f"Zustand x: {result.solution}")
    print(f"Energie E: {result.energy:.6f}")
    print(f"Laufzeit:  {result.runtime_seconds * 1000:.2f} ms")
    print("=" * 80)