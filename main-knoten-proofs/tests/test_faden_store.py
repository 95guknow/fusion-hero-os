"""Tests für Faden-Speicher (Stärke-Stufen Fein → Fixpunkt)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

_DASHBOARD = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

from faden_store import (
    FadenStore,
    STRENGTH_TIERS,
    strength_from_lambda,
)


@pytest.fixture(autouse=True)
def isolated_faden_store(tmp_path, monkeypatch):
    index = tmp_path / "faden_threads" / "index.json"
    monkeypatch.setenv("FUSION_STATE_DIR", str(tmp_path))
    monkeypatch.setattr("faden_store._store", None)
    yield index


def test_strength_from_lambda_tiers():
    assert strength_from_lambda(0.95) == "fein"
    assert strength_from_lambda(0.70) == "mittel"
    assert strength_from_lambda(0.40) == "stark"
    assert strength_from_lambda(0.10) == "fixpunkt"


def test_upsert_and_list_by_strength(isolated_faden_store):
    store = FadenStore(path=isolated_faden_store)
    r1 = store.upsert({"label": "Echo-A", "lambda_contract": 0.92})
    r2 = store.upsert({"label": "Anker-Z", "lambda_contract": 0.15, "fixpoint_id": "Z*"})

    assert r1["ok"] is True
    assert r1["thread"]["strength"] == "fein"
    assert r2["thread"]["strength"] == "fixpunkt"

    fein = store.list_threads(strength="fein")
    fix = store.list_threads(fixpoint_id="Z*")
    assert len(fein) == 1
    assert len(fix) == 1
    assert fein[0]["label"] == "Echo-A"
    assert fix[0]["label"] == "Anker-Z"


def test_prune_expired_fine_threads(isolated_faden_store):
    store = FadenStore(path=isolated_faden_store)
    store.upsert({"label": "alt", "strength": "fein"})
    tid = list(store._threads.keys())[0]
    store._threads[tid].expires_at = time.time() - 10
    store._save()

    result = store.prune()
    assert result["expired"] == 1
    assert result["remaining"] == 0


def test_delete_thread(isolated_faden_store):
    store = FadenStore(path=isolated_faden_store)
    created = store.upsert({"label": "temp", "strength": "mittel"})
    tid = created["thread"]["thread_id"]
    assert store.delete(tid)["ok"] is True
    assert store.get(tid) is None


def test_status_counts_by_strength(isolated_faden_store):
    store = FadenStore(path=isolated_faden_store)
    store.upsert({"strength": "fein", "label": "a"})
    store.upsert({"strength": "mittel", "label": "b"})
    store.upsert({"strength": "stark", "label": "c"})

    st = store.status()
    assert st["total"] == 3
    assert st["by_strength"]["fein"] == 1
    assert st["by_strength"]["mittel"] == 1
    assert st["by_strength"]["stark"] == 1
    assert "fixpunkt" in st["tiers"]
    assert STRENGTH_TIERS["fixpunkt"]["ttl_sec"] is None