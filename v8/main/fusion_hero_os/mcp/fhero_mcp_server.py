# -*- coding: utf-8 -*-
"""
Fusion-Hero-OS MCP-Server - v1 (Layer 6, spec-korrekte Fassung)

Korrigiert das Peer-Review-Artefakt vom 2026-07-05: Das dortige
'"method": "tools/register"' existiert in der MCP-Spezifikation NICHT.
Tools werden serverseitig deklariert und vom Client via

    tools/list   (Discovery)
    tools/call   (Aufruf)

genutzt; der Handshake laeuft ueber initialize / notifications/initialized.
Dieser Server implementiert genau das — minimal, stdlib-only (JSON-RPC 2.0
ueber stdio, eine Nachricht pro Zeile), ohne SDK-Abhaengigkeit.

Exponierte Tools:
  * fhero_layer0_verify   — Beweis-Registry-Status (Claims + Statusverteilung,
                            Strukturpruefung BEWIESEN => proofs vorhanden).
                            EHRLICH: Die eigentliche Beweisfuehrung laeuft in
                            pytest/CI; dieses Tool exponiert den registrierten
                            Stand, es ERSETZT die Testausfuehrung nicht.
  * fhero_schedule_qubo   — Inference-Scheduling via inference_scheduler_qubo
                            (SA + Greedy-Garantie, Layer/Batch-Granularitaet).

Start:  python -m fusion_hero_os.mcp.fhero_mcp_server
Tests:  tests/test_fhero_mcp_server.py (Registry: MCP-SPEC-KONFORM)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fusion_hero_os.core.inference_scheduler_qubo import (
    ScheduleProblem,
    solve_schedule,
)

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "fusion-hero-os-layer0", "version": "1.0.0"}
REGISTRY_PATH = _ROOT / "proof_registry.yaml"

TOOLS = [
    {
        "name": "fhero_layer0_verify",
        "description": (
            "Liefert den Stand der Beweis-Registry (proof_registry.yaml): "
            "Claims mit Status BEWIESEN/OFFEN/WIDERLEGT inkl. Strukturpruefung "
            "(jeder BEWIESEN-Claim muss Test-Knoten listen). Ersetzt nicht die "
            "pytest/CI-Ausfuehrung."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "Optional: nur diesen Claim ausgeben."},
            },
        },
    },
    {
        "name": "fhero_schedule_qubo",
        "description": (
            "Loest ein Zwei-Einheiten-Inference-Scheduling (CPU vs. NPU) in "
            "Layer/Batch-Granularitaet als QUBO (repo-eigenes parallel_anneal) "
            "mit Greedy-Garantie (nie schlechter als die Supervisor-Heuristik)."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cost_cpu": {"type": "array", "items": {"type": "number"},
                             "description": "Kosten je Einheit auf der CPU."},
                "cost_npu": {"type": "array", "items": {"type": "number"},
                             "description": "Kosten je Einheit auf der NPU."},
                "penalty_npu": {"type": "array",
                                "description": "Optionale symmetrische n x n Contention-Matrix (beide auf NPU)."},
                "penalty_cpu": {"type": "array",
                                "description": "Optionale symmetrische n x n Contention-Matrix (beide auf CPU)."},
            },
            "required": ["cost_cpu", "cost_npu"],
        },
    },
]


# ---------------- Tool-Implementierungen ----------------

def _tool_layer0_verify(args: Dict[str, Any]) -> Dict[str, Any]:
    reg = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    claims = reg.get("claims", [])
    claim_id = args.get("claim_id")
    if claim_id:
        claims = [c for c in claims if c.get("id") == claim_id]
        if not claims:
            raise ValueError(f"Claim {claim_id!r} nicht in der Registry.")
    structural_errors = [
        c["id"] for c in claims
        if c.get("status") == "BEWIESEN" and not c.get("proofs")]
    counts: Dict[str, int] = {}
    for c in claims:
        counts[c.get("status", "?")] = counts.get(c.get("status", "?"), 0) + 1
    return {
        "registry_version": reg.get("version"),
        "counts": counts,
        "structural_errors": structural_errors,
        "structurally_valid": not structural_errors,
        "claims": [{"id": c["id"], "status": c["status"],
                    "statement": c["statement"],
                    "n_proofs": len(c.get("proofs") or [])} for c in claims],
        "hinweis": "Beweisdeckung wird durch pytest/CI erbracht (scripts/check_proof_registry.py); dieses Tool exponiert den registrierten Stand.",
    }


def _tool_schedule_qubo(args: Dict[str, Any]) -> Dict[str, Any]:
    cost_cpu = np.asarray(args["cost_cpu"], dtype=np.float64)
    cost_npu = np.asarray(args["cost_npu"], dtype=np.float64)
    n = cost_cpu.shape[0]
    if cost_npu.shape[0] != n:
        raise ValueError("cost_cpu und cost_npu muessen gleich lang sein.")
    zero = np.zeros((n, n))
    problem = ScheduleProblem(
        cost_cpu, cost_npu,
        np.asarray(args.get("penalty_npu", zero), dtype=np.float64),
        np.asarray(args.get("penalty_cpu", zero), dtype=np.float64),
    )
    out = solve_schedule(problem)
    return {
        "assignment": out["assignment"].tolist(),
        "legende": "0 = CPU, 1 = NPU",
        "total_cost": out["total_cost"],
        "winner": out["winner"],
        "cost_sa": out["cost_sa"],
        "cost_greedy": out["cost_greedy"],
        "sa_strictly_better": out["sa_strictly_better"],
    }


_TOOL_IMPL = {
    "fhero_layer0_verify": _tool_layer0_verify,
    "fhero_schedule_qubo": _tool_schedule_qubo,
}


# ---------------- JSON-RPC / MCP-Handler ----------------

def _result(msg_id, result) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Verarbeitet EINE JSON-RPC-Nachricht; None fuer Notifications
    (Notifications bekommen laut Spec keine Antwort)."""
    method = msg.get("method")
    msg_id = msg.get("id")
    is_notification = "id" not in msg

    if method == "initialize":
        return _result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _result(msg_id, {})
    if method == "tools/list":
        return _result(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        impl = _TOOL_IMPL.get(name)
        if impl is None:
            return _error(msg_id, -32602, f"Unbekanntes Tool: {name!r}")
        try:
            payload = impl(params.get("arguments") or {})
            return _result(msg_id, {
                "content": [{"type": "text",
                             "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
                "isError": False,
            })
        except Exception as e:  # Tool-Fehler gehen als isError-Result raus (Spec)
            return _result(msg_id, {
                "content": [{"type": "text", "text": f"Tool-Fehler: {e}"}],
                "isError": True,
            })
    if is_notification:
        return None  # unbekannte Notifications still ignorieren
    return _error(msg_id, -32601, f"Methode nicht unterstuetzt: {method!r}")


def main() -> None:
    """stdio-Transport: eine JSON-RPC-Nachricht pro Zeile (UTF-8)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        response = handle_message(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
