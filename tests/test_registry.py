# -*- coding: utf-8 -*-
"""Gates für die zentrale Modul-Registry (fusion_hero_os/registry.py).

Stellt sicher, dass required-Module wirklich geladen werden, dass **kein**
Spec mehr als Stub deklariert ist (Stand 2026-07-24: alle vormaligen Stubs
sind verdrahtet) und ``get()`` bei nicht verfügbaren Modulen einen
sprechenden Fehler wirft statt still ``None`` zurückzugeben.

Proof-Registry-Anker: REGISTRY-NO-STUBS.
"""
import pytest

from fusion_hero_os.registry import (
    DEFAULT_MODULES,
    ModuleSpec,
    ModuleStatus,
    ModuleUnavailableError,
    Registry,
    get_registry,
)


def test_required_modules_load_successfully():
    registry = get_registry()
    registry.load_all()
    for name in ("engine.mainframe", "orchestration.agents"):
        spec = registry.load(name)
        assert spec.status is ModuleStatus.LOADED, f"{name}: {spec.error}"
        assert spec.module is not None


def test_former_stub_modules_are_now_wired_and_loaded():
    """Historie: builder_profile/mainframe_laden/skill_creator waren Registry-Stubs
    (Legacy Ghost Hunt 2026-07-16, Recovery-Punkt 6). Sie wurden als echte Pakete
    verdrahtet (stub=False, 'wired P1'); dieser Test hielt den alten Zustand fest
    und wurde 2026-07-24 auf den realen Stand nachgezogen."""
    registry = get_registry()
    for name in ("modules.builder_profile", "modules.mainframe_laden", "modules.skill_creator"):
        spec = registry.load(name)
        assert spec.status is ModuleStatus.LOADED, f"{name}: {spec.error}"
        assert spec.module is not None
        assert spec.stub is False


def test_no_registry_spec_is_declared_stub_anymore():
    """'Alle Stubs befuellt' als maschineller Guard statt Prosa-Behauptung:
    kein DEFAULT_MODULES-Spec traegt stub=True. Verhindert, dass ein neuer
    Stub still zurueckkehrt und die Aussage unbemerkt falsch wird."""
    stubs = [s.name for s in DEFAULT_MODULES if s.stub]
    assert stubs == [], f"Registry-Stubs zurueckgekehrt: {stubs}"


def test_get_raises_clear_error_for_unavailable_module():
    registry = Registry(specs=[
        ModuleSpec("does.not.exist", "fusion_hero_os.nonexistent_module", "test fixture")
    ])
    with pytest.raises(ModuleUnavailableError):
        registry.get("does.not.exist")


def test_status_report_lists_every_registered_module():
    registry = get_registry()
    registry.load_all()
    names = {row["name"] for row in registry.status_report()}
    assert "engine.mainframe" in names
    assert "orchestration.agents" in names
    assert "modules.skill_creator" in names
