"""Tests für zentrale Fusion-Einstellungen."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_DASHBOARD = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

from fusion_settings import (
    SETTINGS_SCHEMA,
    apply_settings,
    boot_load,
    get_schema,
    get_values,
    reset_defaults,
)


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    path = tmp_path / "fusion_settings.json"
    monkeypatch.setattr("fusion_settings.SETTINGS_FILE", path)
    monkeypatch.setattr("fusion_settings.STATE_DIR", tmp_path)
    yield


def test_schema_has_bool_and_enum():
    schema = get_schema()
    types = {s["type"] for s in schema["settings"]}
    assert "bool" in types
    assert "enum" in types
    assert len(schema["groups"]) >= 5


def test_apply_and_read_bool():
    result = apply_settings({"FUSION_HYPERTHREADING": False, "ui.bridge_panel": True})
    assert result["status"] == "ok"
    assert os.getenv("FUSION_HYPERTHREADING") == "0"
    values = get_values()
    assert values["env"]["FUSION_HYPERTHREADING"] is False
    assert values["ui"]["bridge_panel"] is True


def test_apply_enum_profile():
    apply_settings({"FUSION_PROFILE": "eco"})
    values = get_values()
    assert values["env"]["FUSION_PROFILE"] == "eco"


def test_multi_enum_disabled_modules():
    apply_settings({"FUSION_DISABLED_MODULES": ["SelfModifyCoreModule", "MERModule"]})
    values = get_values()
    assert "SelfModifyCoreModule" in values["env"]["FUSION_DISABLED_MODULES"]


def test_boot_load_from_file(isolated_settings, tmp_path):
    path = tmp_path / "fusion_settings.json"
    path.write_text(
        json.dumps({"env": {"FUSION_LLM_BACKEND": "llama-local", "FUSION_CONTEXT_WINDOW": "0"}}),
        encoding="utf-8",
    )
    boot_load()
    assert os.getenv("FUSION_LLM_BACKEND") == "llama-local"
    assert os.getenv("FUSION_CONTEXT_WINDOW") == "0"


def test_reset_defaults():
    apply_settings({"FUSION_PROFILE": "eco", "FUSION_HYPERTHREADING": False})
    reset_defaults()
    values = get_values()
    spec = {s["key"]: s["default"] for s in SETTINGS_SCHEMA}
    assert values["env"]["FUSION_PROFILE"] == spec["FUSION_PROFILE"]