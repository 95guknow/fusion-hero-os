#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests für die Frontier-Erweiterungen in claude_science (offline, ohne Netz)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

import claude_science as cs  # noqa: E402


def test_system_field_caching():
    # cache=False -> String
    assert isinstance(cs._system_field("SYS", cache=False), str)
    # cache=True -> Liste mit cache_control-Block
    blocks = cs._system_field("SYS", cache=True)
    assert isinstance(blocks, list)
    assert blocks[0]["type"] == "text"
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[0]["text"] == "SYS"
    print("test_system_field_caching: PASS")


def test_build_payload_defaults_cache_on():
    p = cs._build_payload("frage", system="sys", cache=True)
    assert isinstance(p["system"], list)  # gecached
    assert p["messages"][0]["content"] == "frage"
    assert "thinking" not in p
    assert "stream" not in p
    print("test_build_payload_defaults_cache_on: PASS")


def test_build_payload_thinking_budget():
    p = cs._build_payload("frage", thinking_budget=2000, cache=False)
    assert p["thinking"] == {"type": "enabled", "budget_tokens": 2000}
    assert p["max_tokens"] >= 2000 + 512  # max_tokens muss > budget sein
    print("test_build_payload_thinking_budget: PASS")


def test_build_payload_stream_flag():
    p = cs._build_payload("frage", stream=True)
    assert p["stream"] is True
    print("test_build_payload_stream_flag: PASS")


def test_call_stream_with_injected_sse():
    """Streaming über injizierte SSE-Zeilen (kein Netz)."""
    sse = [
        'data: {"type":"message_start","message":{"usage":{"input_tokens":12,"cache_read_input_tokens":10}}}',
        'data: {"type":"content_block_delta","delta":{"text":"Kontext"}}',
        'data: {"type":"content_block_delta","delta":{"text":"-Anker"}}',
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":7}}',
        'data: [DONE]',
    ]
    deltas = []
    text, meta = cs.call_stream("frage", on_delta=deltas.append, iter_lines=iter(sse))
    assert text == "Kontext-Anker"
    assert deltas == ["Kontext", "-Anker"]
    assert meta["streamed"] is True
    assert meta["input_tokens"] == 12
    assert meta["cache_read_input_tokens"] == 10
    assert meta["output_tokens"] == 7
    assert meta["stop_reason"] == "end_turn"
    print("test_call_stream_with_injected_sse: PASS")


def test_call_stream_handles_bytes_lines():
    sse = [b'data: {"type":"content_block_delta","delta":{"text":"x"}}', b'data: [DONE]']
    text, meta = cs.call_stream("f", iter_lines=iter(sse))
    assert text == "x"
    print("test_call_stream_handles_bytes_lines: PASS")


def test_status_advertises_capabilities():
    st = cs.status()
    caps = st["frontier_capabilities"]
    assert caps["tool_use_loop"] is True
    assert caps["streaming"] is True
    assert "prompt_caching" in caps
    assert "extended_thinking" in caps
    print("test_status_advertises_capabilities: PASS")


if __name__ == "__main__":
    test_system_field_caching()
    test_build_payload_defaults_cache_on()
    test_build_payload_thinking_budget()
    test_build_payload_stream_flag()
    test_call_stream_with_injected_sse()
    test_call_stream_handles_bytes_lines()
    test_status_advertises_capabilities()
    print("ALLE TESTS PASS")
