# -*- coding: utf-8 -*-
"""Tests fuer den spec-korrekten MCP-Server (Registry: MCP-SPEC-KONFORM).

Verankert die Peer-Review-Korrektur: KEIN tools/register — Discovery via
tools/list, Aufruf via tools/call, Handshake via initialize.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fusion_hero_os.mcp.fhero_mcp_server import PROTOCOL_VERSION, handle_message


def _call(method, params=None, msg_id=1):
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return handle_message(msg)


def test_initialize_handshake_is_spec_conform():
    resp = _call("initialize", {"protocolVersion": PROTOCOL_VERSION,
                                "capabilities": {}, "clientInfo": {"name": "t"}})
    assert resp["jsonrpc"] == "2.0" and resp["id"] == 1
    result = resp["result"]
    assert result["protocolVersion"] == PROTOCOL_VERSION
    assert "tools" in result["capabilities"]
    assert result["serverInfo"]["name"]


def test_initialized_notification_gets_no_response():
    assert handle_message({"jsonrpc": "2.0",
                           "method": "notifications/initialized"}) is None


def test_tools_list_exposes_tools_with_input_schema():
    result = _call("tools/list")["result"]
    names = [t["name"] for t in result["tools"]]
    assert "fhero_layer0_verify" in names
    assert "fhero_schedule_qubo" in names
    for t in result["tools"]:
        assert t["inputSchema"]["type"] == "object"
        assert t["description"]


def test_tools_register_does_not_exist():
    """Der Kern der Review-Korrektur: tools/register ist KEINE MCP-Methode."""
    resp = _call("tools/register", {"name": "x"})
    assert resp["error"]["code"] == -32601


def test_tools_call_layer0_verify_reports_registry():
    resp = _call("tools/call", {"name": "fhero_layer0_verify", "arguments": {}})
    result = resp["result"]
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["structurally_valid"] is True
    assert payload["counts"].get("BEWIESEN", 0) > 0
    assert any(c["id"] == "QPT-QQ-EQUALITY" for c in payload["claims"])


def test_tools_call_layer0_verify_single_claim_and_unknown_claim():
    resp = _call("tools/call", {"name": "fhero_layer0_verify",
                                "arguments": {"claim_id": "K16"}})
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert [c["id"] for c in payload["claims"]] == ["K16"]
    resp = _call("tools/call", {"name": "fhero_layer0_verify",
                                "arguments": {"claim_id": "GIBTS-NICHT"}})
    assert resp["result"]["isError"] is True


def test_tools_call_schedule_qubo_returns_assignment():
    resp = _call("tools/call", {"name": "fhero_schedule_qubo", "arguments": {
        "cost_cpu": [5.0, 5.0, 5.0],
        "cost_npu": [1.0, 1.0, 1.0],
        "penalty_npu": [[0.0, 2.5, 0.0], [2.5, 0.0, 0.0], [0.0, 0.0, 0.0]],
    }})
    result = resp["result"]
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert len(payload["assignment"]) == 3
    assert payload["cost_sa"] <= payload["cost_greedy"] + 1e-9 or payload["winner"] == "greedy"
    # NPU ueberall guenstiger, Contention (2.5) frisst den Vorteil nicht auf:
    assert payload["assignment"] == [1, 1, 1]
    assert abs(payload["total_cost"] - 5.5) < 1e-9  # 3*1.0 + 2.5


def test_tools_call_unknown_tool_is_invalid_params():
    resp = _call("tools/call", {"name": "gibts_nicht", "arguments": {}})
    assert resp["error"]["code"] == -32602


def test_unknown_notification_ignored_and_unknown_request_errors():
    assert handle_message({"jsonrpc": "2.0", "method": "wat/auch/immer"}) is None
    resp = _call("wat/auch/immer")
    assert resp["error"]["code"] == -32601
