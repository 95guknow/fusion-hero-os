"""QUBOIntegrationCoreModule (BaseModule-Adapter).

Wrapt :class:`fusion_hero_os.engine.mainframe.QUBOIntegrationCoreModule`,
das den QUBO-Solver (``ClassicalBackend``) inklusive Pre-/Post-Solve-Audit-
Hooks kapselt. Andere Solver-Backends (z.B. Quantenhardware-Anbindung) sind
noch nicht implementiert — dieser Adapter ist bewusst so geschrieben, dass
ein zusätzliches Backend später ergänzt werden kann, ohne den Dispatcher-
Vertrag zu ändern.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.engine.mainframe import QUBOIntegrationCoreModule as _QUBOIntegrationImpl


class QUBOIntegrationCoreModule(BaseModule):
    """``process(payload)`` erwartet ``{"problem_matrix": array-like,
    "mode": "secure" | "parallel", ...}`` und routet an den entsprechenden
    gesicherten Solver-Lauf.
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl = _QUBOIntegrationImpl()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Any:
        payload = payload or {}
        problem_matrix = payload["problem_matrix"]
        mode = payload.get("mode", "secure")
        if mode == "parallel":
            return self._impl.execute_parallel_run(
                problem_matrix,
                steps=payload.get("steps", 8000),
                T0=payload.get("T0", 2.0),
                n_restarts=payload.get("n_restarts"),
                n_samples=payload.get("n_samples", 60),
            )
        return self._impl.execute_secure_run(problem_matrix, config=payload.get("config"))
