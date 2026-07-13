#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests für structured_output und den claude_science Tool-Use-Loop (offline)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

import structured_output as so  # noqa: E402

SCHEMA = {
    "type": "object",
    "required": ["idee", "risiko"],
    "properties": {
        "idee": {"type": "string", "minLength": 5},
        "risiko": {"type": "string", "enum": ["niedrig", "mittel", "hoch"]},
        "prio": {"type": "integer", "minimum": 1, "maximum": 5},
    },
}


def test_extract_json_from_fence():
    text = 'Vorwort... ```json\n{"a": [1, 2], "b": "x"}\n``` Nachwort'
    assert so.extract_json(text) == {"a": [1, 2], "b": "x"}
    print("test_extract_json_from_fence: PASS")


def test_extract_json_inline_and_nested():
    text = 'Antwort: {"outer": {"inner": "wert mit } klammer im string"}} rest'
    data = so.extract_json(text)
    assert data == {"outer": {"inner": "wert mit } klammer im string"}}
    assert so.extract_json("gar kein json hier") is None
    assert so.extract_json("") is None
    print("test_extract_json_inline_and_nested: PASS")


def test_validate_ok():
    inst = {"idee": "Kontext-Anker pro Schritt", "risiko": "niedrig", "prio": 2}
    assert so.validate(inst, SCHEMA) == []
    print("test_validate_ok: PASS")


def test_validate_failures():
    issues = so.validate({"idee": "abc", "risiko": "extrem", "prio": 9}, SCHEMA)
    text = " | ".join(issues)
    assert "minLength" in text
    assert "enum" in text
    assert "maximum" in text
    issues2 = so.validate({}, SCHEMA)
    assert any("idee" in i for i in issues2) and any("risiko" in i for i in issues2)
    # bool ist kein integer
    issues3 = so.validate({"idee": "lange idee", "risiko": "hoch", "prio": True}, SCHEMA)
    assert any("boolean" in i for i in issues3)
    print("test_validate_failures: PASS")


def test_request_structured_repairs():
    calls = {"n": 0}

    def backend(prompt, role):
        calls["n"] += 1
        if calls["n"] == 1:
            return "Nur Fließtext, kein JSON."
        assert "ungültig" in prompt  # Repair-Prompt enthält die Fehlerliste
        return '{"idee": "Kontext-Anker pro Schritt", "risiko": "niedrig"}'

    out = so.request_structured(backend, "Idee gegen Kontextverlust?", SCHEMA)
    assert out["ok"] is True
    assert out["attempts"] == 2
    assert out["data"]["risiko"] == "niedrig"
    print("test_request_structured_repairs: PASS")


def test_request_structured_gives_up():
    out = so.request_structured(lambda p, r: "niemals json", "x", SCHEMA, retries=1)
    assert out["ok"] is False
    assert out["attempts"] == 2
    assert out["issues"]
    print("test_request_structured_gives_up: PASS")


def test_tool_loop_with_fake_transport():
    import claude_science as cs

    tools = [{
        "name": "add",
        "description": "Addiert zwei Zahlen",
        "input_schema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
    }]

    state = {"round": 0}

    def fake_post(payload):
        state["round"] += 1
        assert payload["tools"] == tools
        if state["round"] == 1:
            return {
                "stop_reason": "tool_use",
                "content": [
                    {"type": "text", "text": "Ich rechne."},
                    {"type": "tool_use", "id": "tu_1", "name": "add", "input": {"a": 2, "b": 40}},
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        # Runde 2: das tool_result muss in den Messages angekommen sein
        last = payload["messages"][-1]
        assert last["role"] == "user"
        assert last["content"][0]["type"] == "tool_result"
        assert last["content"][0]["content"] == "42"
        return {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "Ergebnis: 42"}],
            "usage": {"input_tokens": 20, "output_tokens": 7},
        }

    def executor(name, tool_input):
        assert name == "add"
        return str(int(tool_input["a"] + tool_input["b"]))

    out = cs.run_tool_loop("Was ist 2+40?", tools, executor, post=fake_post)
    assert out["ok"] is True
    assert out["response"] == "Ergebnis: 42"
    assert out["rounds"] == 2
    assert len(out["tool_calls"]) == 1 and out["tool_calls"][0]["ok"] is True
    assert out["usage"] == {"input_tokens": 30, "output_tokens": 12}
    print("test_tool_loop_with_fake_transport: PASS")


def test_tool_loop_reports_tool_error():
    import claude_science as cs

    def fake_post(payload):
        if len(payload["messages"]) == 1:
            return {
                "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "id": "tu_1", "name": "boom", "input": {}}],
                "usage": {},
            }
        last = payload["messages"][-1]
        assert last["content"][0].get("is_error") is True
        return {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "Tool schlug fehl."}],
            "usage": {},
        }

    def executor(name, tool_input):
        raise RuntimeError("kaputt")

    out = cs.run_tool_loop("test", [], executor, post=fake_post)
    assert out["ok"] is True
    assert out["tool_calls"][0]["ok"] is False
    print("test_tool_loop_reports_tool_error: PASS")


def test_tool_loop_offline_without_key():
    import claude_science as cs

    if cs.is_configured():
        print("test_tool_loop_offline_without_key: SKIP (API-Key gesetzt)")
        return
    out = cs.run_tool_loop("test", [], lambda n, i: "")
    assert out["ok"] is False
    assert "ANTHROPIC_API_KEY" in out["error"]
    print("test_tool_loop_offline_without_key: PASS")


if __name__ == "__main__":
    test_extract_json_from_fence()
    test_extract_json_inline_and_nested()
    test_validate_ok()
    test_validate_failures()
    test_request_structured_repairs()
    test_request_structured_gives_up()
    test_tool_loop_with_fake_transport()
    test_tool_loop_reports_tool_error()
    test_tool_loop_offline_without_key()
    print("ALLE TESTS PASS")
