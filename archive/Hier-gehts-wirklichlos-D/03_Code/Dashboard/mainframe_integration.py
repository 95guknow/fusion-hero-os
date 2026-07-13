# -*- coding: utf-8 -*-
"""Entry-point alias — qb_qubo + classical + mainframe v5.25."""
from heroic_core_mainframe import (
    ClassicalBackend,
    CriticalMetaAnalysisCoreModule,
    EudaimoniaGuard,
    ExecutableAuditAgent,
    GenerationalEvolutionProtocolCoreModule,
    QUBOIntegrationCoreModule,
    QUBOProblem,
    QUBOSolverConfig,
    SelfModifyCoreModule,
    SolverResult,
    make_Q,
    local_search,
    parallel_anneal,
    simulated_annealing,
    warmup_kernels,
)

__all__ = [
    "ClassicalBackend", "CriticalMetaAnalysisCoreModule", "EudaimoniaGuard",
    "ExecutableAuditAgent", "GenerationalEvolutionProtocolCoreModule",
    "QUBOIntegrationCoreModule", "QUBOProblem", "QUBOSolverConfig",
    "SelfModifyCoreModule", "SolverResult", "make_Q", "local_search",
    "parallel_anneal", "simulated_annealing", "warmup_kernels",
]

if __name__ == "__main__":
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).parent / "heroic_core_mainframe.py"), run_name="__main__")