# -*- coding: utf-8 -*-
"""Import-Sicherheit: die Bibliotheks-Module müssen ohne Seiteneffekte
importierbar sein (kein Netzwerk, kein ui.run(), keine Exceptions beim Import).

app.py ist bewusst NICHT dabei — es ist der GUI-Einstiegspunkt (NiceGUI).
"""
import importlib

import pytest

LIBRARY_MODULES = [
    "engine.mainframe",
    "engine.mining_qubo",
    "methodology.connectors",
    "methodology.core_modules",
    "methodology.knowledge",
    "orchestration.agents",
]


@pytest.mark.parametrize("module_name", LIBRARY_MODULES)
def test_module_imports_without_side_effects(module_name):
    mod = importlib.import_module(module_name)
    assert mod is not None
