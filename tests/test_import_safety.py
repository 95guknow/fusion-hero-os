# -*- coding: utf-8 -*-
"""Import-Sicherheit: die Bibliotheks-Module müssen ohne Seiteneffekte
importierbar sein (kein Netzwerk, kein ui.run(), keine Exceptions beim Import).

app.py ist bewusst NICHT dabei — es ist der GUI-Einstiegspunkt (NiceGUI).
"""
import ast
import importlib
from pathlib import Path

import pytest

LIBRARY_MODULES = [
    "fusion_hero_os.engine.mainframe",
    "fusion_hero_os.engine.mining_qubo",
    "fusion_hero_os.methodology.connectors",
    "fusion_hero_os.methodology.core_modules",
    "fusion_hero_os.methodology.knowledge",
    "fusion_hero_os.orchestration.agents",
]

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "fusion_hero_os"


@pytest.mark.parametrize("module_name", LIBRARY_MODULES)
def test_module_imports_without_side_effects(module_name):
    mod = importlib.import_module(module_name)
    assert mod is not None


def _package_python_files():
    return sorted(
        p for p in _PACKAGE_ROOT.rglob("*.py")
        if "__pycache__" not in p.parts
    )


def test_no_uncompilable_placeholder_modules():
    """Jede .py-Datei im Paket muss echter, parsebarer Python-Code sein.

    Regression zu PR #62/#64: der Owner-Follow-up hatte Prosa-Platzhalter
    (``THE FULL CONTENT OF ...``) als .py-Dateien eingecheckt. Die sind kein
    Code, brechen ``ast.parse`` und tauchen im Dependency Atlas als
    ``syntax-error``-Unresolved auf. Dieser Test faengt solche Artefakte am
    Ort ihrer Entstehung ab, unabhaengig vom Atlas-Scan.
    """
    broken = []
    for py in _package_python_files():
        try:
            ast.parse(py.read_text(encoding="utf-8-sig"), filename=str(py))
        except SyntaxError as exc:
            rel = py.relative_to(_PACKAGE_ROOT.parent)
            broken.append(f"{rel}: {exc.msg} (Zeile {exc.lineno})")
    assert broken == [], (
        "Nicht-kompilierbare Platzhalter-Module im Paket gefunden: " + "; ".join(broken)
    )


def test_no_stray_versioned_module_variants():
    """Kanonische Module leben an ihrem Pfad, nicht als ``*_v9``/``__init___*``-Kopien.

    Verhindert wiederkehrende 'Update per Datei-Duplikat'-Artefakte: die
    echte Timespace-Funktionalitaet liegt in
    ``fusion_hero_os/modules/timespace_token/`` — parallele Root-Kopien wie
    ``timespace_token_v9.py`` oder ``__init___v9_update.py`` sind Platzhalter.
    """
    stray = [
        str(p.relative_to(_PACKAGE_ROOT.parent))
        for p in _package_python_files()
        if p.stem.startswith("__init___") or "_v9" in p.stem
    ]
    assert stray == [], f"Verdaechtige Platzhalter-/Duplikat-Module: {stray}"
