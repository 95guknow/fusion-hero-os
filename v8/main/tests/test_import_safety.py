# -*- coding: utf-8 -*-
"""Import-Sicherheit: die Bibliotheks-Module müssen ohne Seiteneffekte
importierbar sein (kein Netzwerk, kein ui.run(), keine Exceptions beim Import).

app.py ist bewusst NICHT dabei — es ist der GUI-Einstiegspunkt (NiceGUI).
"""
import importlib

import pytest

LIBRARY_MODULES = [
    "fusion_hero_os.engine.mainframe",
    "fusion_hero_os.engine.mining_qubo",
    "fusion_hero_os.methodology.connectors",
    "fusion_hero_os.methodology.core_modules",
    "fusion_hero_os.methodology.knowledge",
    "fusion_hero_os.orchestration.agents",
]


@pytest.mark.parametrize("module_name", LIBRARY_MODULES)
def test_module_imports_without_side_effects(module_name):
    mod = importlib.import_module(module_name)
    assert mod is not None
