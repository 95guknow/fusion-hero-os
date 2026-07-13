"""Dispatcher — zentraler Orchestrator für Core-Module.

Ersetzt lose, verstreute Direktaufrufe einzelner Module durch einen
Registrierungs-/Routing-Mechanismus: Module werden einmal unter einem Namen
registriert (:meth:`Dispatcher.register`) und danach ausschließlich über
diesen Namen angesprochen (:meth:`Dispatcher.dispatch`). Für mehrere
unabhängige Anfragen unterstützt :meth:`Dispatcher.dispatch_many` parallele
Ausführung über ``concurrent.futures.ThreadPoolExecutor`` (im Projekt als
"Hyperthreading" bezeichnet, siehe ``engine/mainframe.py``).

Kein Modul wird hier automatisch verändert oder ausgeführt, ohne dass der
Aufrufer das explizit anstößt — der Dispatcher ist reine Verdrahtung, keine
Automation, die von sich aus tätig wird.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fusion_hero_os.config import get_config
from fusion_hero_os.core.base_module import BaseModule, EvolutionProposal, ReviewResult

logger = logging.getLogger("fusion_hero_os.dispatcher")


class ModuleNotRegisteredError(KeyError):
    """Wird geworfen, wenn ein unbekannter Modulname angefragt wird."""


class Dispatcher:
    """Registriert :class:`BaseModule`-Instanzen und routet Anfragen an sie."""

    def __init__(self, max_workers: Optional[int] = None) -> None:
        self._modules: Dict[str, BaseModule] = {}
        self._max_workers = max_workers if max_workers is not None else get_config().max_workers

    def register(self, module: BaseModule, name: Optional[str] = None) -> None:
        """Registriert ``module`` unter ``name`` (Default: ``module.name``).

        Eine erneute Registrierung unter demselben Namen überschreibt bewusst
        die vorherige (z.B. um in Tests ein Modul durch ein Fake zu ersetzen).
        """
        key = name or module.name
        if not key:
            raise ValueError("Modul benötigt einen Namen (module.name oder name=...).")
        self._modules[key] = module
        logger.debug("Modul registriert: %s (%s)", key, type(module).__name__)

    def unregister(self, name: str) -> None:
        self._modules.pop(name, None)

    def list_modules(self) -> List[str]:
        return sorted(self._modules)

    def _get(self, name: str) -> BaseModule:
        try:
            return self._modules[name]
        except KeyError as exc:
            raise ModuleNotRegisteredError(
                f"Kein Modul unter {name!r} registriert. Verfügbar: {self.list_modules()}"
            ) from exc

    def dispatch(self, name: str, payload: Any = None) -> Any:
        """Routet ``payload`` an ``module.process()`` des registrierten Moduls."""
        module = self._get(name)
        return module.process(payload)

    def dispatch_many(
        self, requests: Sequence[Tuple[str, Any]], parallel: bool = True
    ) -> List[Any]:
        """Führt mehrere ``(modulname, payload)``-Anfragen aus.

        Bei ``parallel=True`` (Default) laufen sie über einen
        ``ThreadPoolExecutor`` gleichzeitig — sinnvoll, wenn die Module
        unabhängig sind und mindestens teilweise auf I/O bzw. numba-
        Kernels warten (GIL wird dort freigegeben, siehe ``engine/mainframe.py``).
        Ergebnisse werden in der Reihenfolge der Anfragen zurückgegeben,
        auch wenn sie nicht in dieser Reihenfolge fertig werden.
        """
        if not requests:
            return []
        if not parallel or len(requests) == 1:
            return [self.dispatch(name, payload) for name, payload in requests]

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = [pool.submit(self.dispatch, name, payload) for name, payload in requests]
            return [f.result() for f in futures]

    def propose_evolution(self, name: str, context: Any = None) -> Optional[EvolutionProposal]:
        return self._get(name).propose_evolution(context)

    def collect_evolution_proposals(self, context: Any = None) -> List[EvolutionProposal]:
        """Fragt alle registrierten Module nach Verbesserungsvorschlägen.

        Liefert nur die Vorschläge, die tatsächlich einen zurückgeben (die
        Default-Implementierung in ``BaseModule`` liefert ``None``).
        """
        proposals = []
        for module in self._modules.values():
            proposal = module.propose_evolution(context)
            if proposal is not None:
                proposals.append(proposal)
        return proposals

    def peer_review(self, name: str, target: Any = None) -> ReviewResult:
        return self._get(name).peer_review(target)


_default_dispatcher: Optional[Dispatcher] = None


def build_default_dispatcher() -> Dispatcher:
    """Baut einen neuen Dispatcher mit allen Standard-Core-Modulen registriert.

    Import von ``fusion_hero_os.modules`` erfolgt hier lokal (nicht auf
    Modulebene), damit ``core.dispatcher`` unabhängig von ``modules``
    importierbar bleibt und keine Zyklen entstehen können.
    """
    from fusion_hero_os.modules import ALL_CORE_MODULES

    disabled = get_config().disabled_modules
    dispatcher = Dispatcher()
    for module_cls in ALL_CORE_MODULES:
        instance = module_cls()
        if instance.name in disabled:
            logger.info("Modul %r via FUSION_DISABLED_MODULES deaktiviert.", instance.name)
            continue
        dispatcher.register(instance)
    return dispatcher


def get_default_dispatcher() -> Dispatcher:
    """Geteilte Standard-Dispatcher-Instanz (Singleton je Prozess)."""
    global _default_dispatcher
    if _default_dispatcher is None:
        _default_dispatcher = build_default_dispatcher()
    return _default_dispatcher
