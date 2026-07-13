"""Banach-Rückkopplung → Faden-Speicher Automatik."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

_CORE = Path(__file__).resolve().parents[1] / "03_Code" / "core"
_DASH = Path(__file__).resolve().parents[1] / "03_Code" / "Dashboard"
for p in (_CORE, _DASH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture
def ctx_env(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("FUSION_FADEN_AUTO_SAVE", "1")
    monkeypatch.setenv("FUSION_BANACH_LAMBDA", "0.74")
    monkeypatch.setattr("conversation_context_core._STORE", tmp_path / "conversation_context.json")
    monkeypatch.setattr("conversation_context_core._CTX", None)
    monkeypatch.setattr("faden_store._store", None)

    import conversation_context_core as ccc

    return ccc


def test_feedback_persists_banach_faden_thread(ctx_env):
    core = ctx_env.ConversationContextCore()
    root = core.init_root("Start-Anker für Session", {"layer": 1})
    root_id = root["root"]["window_id"]

    sub = core.allocate_subagent("worker-a", "medium")
    sub_id = sub["subagent_window"]["window_id"]

    result = core.feedback(sub_id, "Erkenntnis: Modul geladen und getestet.", {"task_id": "t1"})

    assert result["ok"] is True
    assert "faden" in result
    assert result["faden"]["strength"] == "mittel"

    expected_tid = hashlib.sha256(f"banach:{root_id}:{sub_id}".encode()).hexdigest()[:12]
    assert result["faden"]["thread_id"] == expected_tid

    from faden_store import get_faden_store

    stored = get_faden_store().get(expected_tid)
    assert stored is not None
    assert stored["source"] == "conversation_context_core"
    assert stored["fixpoint_id"] == root_id
    assert stored["state"]["subagent_name"] == "worker-a"
    assert stored["state"]["revision"] == 1


def test_feedback_skips_faden_when_disabled(ctx_env, monkeypatch):
    monkeypatch.setenv("FUSION_FADEN_AUTO_SAVE", "0")
    core = ctx_env.ConversationContextCore()
    core.init_root("Anker")
    sub = core.allocate_subagent("worker-b")
    sub_id = sub["subagent_window"]["window_id"]

    result = core.feedback(sub_id, "Kurzes Ergebnis")
    assert result["ok"] is True
    assert "faden" not in result