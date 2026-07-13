"""Re-export qb_qubo from 03_Code/tools (avoids name collision via importlib)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_TOOLS_FILE = Path(__file__).resolve().parent.parent / "tools" / "qb_qubo.py"


def _load_tools_qubo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_fusion_qb_tools", _TOOLS_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load qb_qubo from {_TOOLS_FILE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_qb = _load_tools_qubo()

energy = _qb.energy
springloop_energy = _qb.springloop_energy
brute_force_min = _qb.brute_force_min
simulated_annealing = _qb.simulated_annealing
make_Q = _qb.make_Q
local_search = _qb.local_search
qubo_to_ising = _qb.qubo_to_ising
parallel_anneal = getattr(_qb, "parallel_anneal", None)