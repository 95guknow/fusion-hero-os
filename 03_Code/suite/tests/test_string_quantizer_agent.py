"""Tests: String-Quantisierer (3. Agent) — whole-string emit + Phrase-Quantisierung."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_CORE = Path(__file__).resolve().parents[2] / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from string_quantizer_agent import (  # noqa: E402
    StringQuantizer,
    accompany,
    emit_logical,
    emit_whole_strings,
    get_quantizer,
    split_logical_strings,
)


def test_split_logical_never_chars():
    text = "Alpha Beta. Gamma Delta. Alpha Beta."
    units = split_logical_strings(text)
    assert len(units) >= 2
    assert all(len(u) > 1 for u in units)


def test_emit_whole_strings_bundles_single_letters():
    # Einzelbuchstaben werden gebündelt, nie solo als Stream-Policy
    out = emit_whole_strings(["H", "e", "l", "l", "o", " ", "W", "o", "r", "l", "d"])
    assert out == "Hello World"
    assert " " in out


def test_quantize_repeating_phrases():
    q = StringQuantizer()
    text = (
        "Fusion Hero OS Fusion Hero OS — "
        "MasterSeed MasterSeed MasterSeed. "
        "Fusion Hero OS hält den Fixpunkt."
    )
    payload = q.quantize(text)
    assert payload.stats.get("table_size", 0) >= 1
    assert any(t.startswith("Q#") for t in payload.sequence)
    expanded = payload.expand()
    assert "Fusion Hero OS" in expanded or "MasterSeed" in expanded


def test_emit_logical_whole_strings():
    text = "Eins. Zwei. Eins. Zwei."
    out = emit_logical(text)
    assert isinstance(out, str)
    assert len(out) > 0
    # keine Char-für-Char-Repräsentation (z.B. "E i n s")
    assert "E i n s" not in out


def test_accompany_negotiation_triad():
    os.environ["FUSION_QUANTIZER_AGENT"] = "1"
    get_quantizer().reset()
    agent = "Die Antwort nutzt MasterSeed und MasterSeed erneut im Heroic Core."
    anti = "Kritik: MasterSeed wird wiederholt ohne neuen Beweis."
    out = accompany("Erkläre MasterSeed", agent, anti)
    assert out["ok"] is True
    assert out["role"] == "quantizer"
    assert out["never_char_by_char"] is True
    assert out["ordered_unit_count"] >= 1
    assert "quantized" in out
    assert out["quantized"]["mode"] == "adaptive_substring_logical"


def test_adaptive_substrings_not_full_doc_only():
    q = StringQuantizer()
    text = "Liebe und Vertrauen. Liebe und Nähe. Zufrieden und ruhig. Sinn und MasterSeed."
    subs = q.adaptive_substrings(text)
    assert any("liebe" in s for s in subs)
    # sub strings should exist shorter than full document
    assert any(len(s) < len(text) for s in subs)


def test_sinn_quanten_mapping():
    from sinn_quanten_registry import score_text, status
    sc = score_text("Echte Nähe und Vertrauen — Liebesquant. Ich bin zufrieden und ruhig.")
    assert "liebesquant" in sc.get("scores", {}) or "zufriedenheitsquant" in sc.get("scores", {})
    st = status()
    assert "liebesquant" in st["ids"]
    assert "zufriedenheitsquant" in st["ids"]


def test_router_dual_run_includes_quantizer(monkeypatch):
    os.environ["FUSION_QUANTIZER_AGENT"] = "1"
    os.environ["FUSION_DUAL_AGENT"] = "1"

    import agent_backend_router as abr

    def fake_invoke(role, query, context=None, agent_response=None, anti_response=None):
        if role == "agent":
            return {
                "ok": True,
                "backend": "stub",
                "role": "agent",
                "response": "MasterSeed MasterSeed — heroische Antwort MasterSeed.",
            }
        if role == "anti_agent":
            return {
                "ok": True,
                "backend": "stub",
                "role": "anti_agent",
                "response": "Anti: MasterSeed fehlt Beweis.",
            }
        if role == "quantizer":
            from string_quantizer_agent import accompany

            return accompany(
                query,
                agent_response or "",
                anti_response or "",
                context,
            )
        return {"ok": False, "role": role, "error": "unknown"}

    monkeypatch.setattr(abr, "invoke", fake_invoke)
    result = abr.dual_run("Was ist MasterSeed?")
    assert result["ok"] is True
    assert result.get("triad") is True
    assert result.get("quantizer") is not None
    assert result["quantizer"].get("ok") is True
    assert "Quantisierer" in result.get("synthesis", "") or result["quantizer"].get("compact")


def test_policy_lists_quantizer():
    import agent_backend_router as abr

    pol = abr.policy()
    assert pol["quantizer_agent_enabled"] in (True, False)
    assert "quantizer" in pol["triad"]
    assert pol["emit_policy"] == "whole_string_logical_never_char_stream"
