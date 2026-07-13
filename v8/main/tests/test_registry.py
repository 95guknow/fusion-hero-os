# -*- coding: utf-8 -*-
"""Gates für die zentrale Modul-Registry (fusion_hero_os/registry.py).

Stellt sicher, dass required-Module wirklich geladen werden, Stub-Module
ehrlich als Stub markiert bleiben und ``get()`` bei nicht verfügbaren
Modulen einen sprechenden Fehler wirft statt still ``None`` zurückzugeben.
"""
import pytest

from fusion_hero_os.registry import (
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


def test_stub_modules_are_marked_as_stub_not_loaded():
    registry = get_registry()
    for name in ("modules.alte_frau_95g", "modules.mainframe_laden", "modules.skill_creator"):
        spec = registry.load(name)
        assert spec.status is ModuleStatus.STUB


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
