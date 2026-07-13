#!/usr/bin/env python3
"""
Fusion Hero OS v8 — Integration Hub
Verknüpft: Tailscale Mesh + MCP-Konnektoren + LLM-Frameworks + Orchestration
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
CODE_DIR = ROOT / "03_Code"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


def _get_mesh_status() -> dict:
    try:
        from tailscale_mesh_registry import get_mesh_status
        return get_mesh_status()
    except Exception as e:
        return {"error": str(e), "layer": "mesh"}


def _get_llm_status() -> dict:
    try:
        from llm_frameworks import connector_status
        return connector_status()
    except Exception as e:
        return {"error": str(e), "layer": "llm"}


def _get_tailscale_raw() -> dict:
    try:
        import subprocess
        r = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=8,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            self_data = data.get("Self", {})
            peer_data = data.get("Peer") or {}
            peers = []
            for _pk, p in peer_data.items():
                peers.append({
                    "hostname": p.get("HostName"),
                    "os": p.get("OS"),
                    "online": p.get("Online", False),
                    "magicdns": (p.get("DNSName") or "").rstrip("."),
                    "ip": (p.get("TailscaleIPs") or [None])[0],
                })
            login = ""
            for uid, u in (data.get("User") or {}).items():
                login = u.get("LoginName", login)
            return {
                "online": self_data.get("Online", False),
                "hostname": self_data.get("HostName"),
                "tailscale_ip": (self_data.get("TailscaleIPs") or [None])[0],
                "magicdns": (self_data.get("DNSName") or "").rstrip("."),
                "peers": len(peers),
                "peer_list": peers,
                "tailnet": (data.get("CurrentTailnet") or {}).get("Name"),
                "login": login,
            }
    except Exception as e:
        return {"online": False, "error": str(e)}
    return {"online": False}


def _get_vr_status() -> dict:
    """VR assets + Highest Layer mit VR."""
    root = Path(os.environ.get("FUSION_HERO_ROOT", str(ROOT)))
    vr_root = Path(os.environ.get("FUSION_VR_ASSETS_ROOT", str(root / "03_VR_Assets")))
    expected = [
        "vr_mister_Contributor_hero_equirectangular.jpg",
        "heroic_evolution_fractal.jpg",
    ]
    assets = []
    for name in expected:
        p = vr_root / name
        assets.append({
            "file": name,
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
        })
    layer = {}
    hl_path = CODE_DIR / "heroic-highest-layer"
    try:
        if str(hl_path) not in sys.path:
            sys.path.insert(0, str(hl_path))
        from highest_layer import load_vr
        layer = load_vr().get_vr_status()
    except Exception as e:
        layer = {"error": str(e)}
    present = sum(1 for a in assets if a["exists"] and a["size_bytes"] > 10000)
    return {
        "assets_root": str(vr_root),
        "assets": assets,
        "assets_ready": present,
        "assets_total": len(expected),
        "viewer_path": "/vr/viewer",
        "dashboard_port": 8000,
        "layer": layer,
        "status": "ready" if present == len(expected) else "needs_assets",
    }


def _workstation_paths_file() -> Optional[Path]:
    candidates: List[Path] = []
    env_ws = os.environ.get("NORMALOS_WORKSTATION")
    if env_ws:
        candidates.append(Path(env_ws) / "paths.json")
    home = Path.home()
    candidates.extend([
        home / "normalOS" / "workstation" / "paths.json",
        home / "normalOS-workstation" / "paths.json",
    ])
    for p in candidates:
        if p.exists():
            return p
    return None


def _get_workstation() -> dict:
    ws = _workstation_paths_file()
    if not ws:
        return {"configured": False}
    try:
        with open(ws, encoding="utf-8") as f:
            return {"configured": True, "paths": json.load(f)}
    except Exception as e:
        return {"configured": False, "error": str(e)}


def _check_phone_visibility(unified: dict, tailscale: dict) -> dict:
    """Warnung wenn Phone in Config aber nicht in Tailscale-Peers."""
    phone_cfg = (unified.get("nodes") or {}).get("phone", {})
    expected = phone_cfg.get("hostname", "phone-node")
    peer_list = tailscale.get("peer_list") or []
    found = any(
        expected.lower() in (p.get("hostname") or "").lower()
        or expected.lower() in (p.get("magicdns") or "").lower()
        for p in peer_list
    )
    hint = phone_cfg.get("login_hint") or (
        "Handy und PC muessen im gleichen Tailnet sein (gleicher Login: Google, nicht GitHub)"
    )
    return {
        "expected_hostname": expected,
        "visible": found,
        "peer_count": tailscale.get("peers", 0),
        "account_login": tailscale.get("login"),
        "fix_hint": None if found else hint,
    }


def _build_graph(unified: dict, mesh: dict, llm: dict) -> dict:
    """Build linked graph: nodes → connectors → LLMs."""
    links = unified.get("connector_llm_links", {})
    nodes = []

    for node_id, cfg in unified.get("nodes", {}).items():
        nodes.append({
            "id": node_id,
            "type": "node",
            "role": cfg.get("role"),
            "magicdns": cfg.get("magicdns"),
            "hosts": cfg.get("hosts", []),
        })

    segments = []
    connectors = mesh.get("connectors", {})
    frameworks = llm.get("frameworks", {})

    for cid, seg in connectors.items():
        linked_llm = links.get(cid)
        llm_info = frameworks.get(linked_llm, {}) if linked_llm else {}
        segments.append({
            "id": seg.get("mesh_id", f"mesh-connector-{cid}"),
            "type": "mcp_connector",
            "connector_id": cid,
            "segment_status": seg.get("segment_status"),
            "linked_llm": linked_llm,
            "linked_llm_status": "configured" if llm_info.get("configured") else "pending",
            "health_path": seg.get("health_path"),
            "edge": f"{cid} → {linked_llm}" if linked_llm else None,
        })

    for pid, fw in frameworks.items():
        linked_connectors = [c for c, l in links.items() if l == pid]
        segments.append({
            "id": fw.get("mesh_id", f"mesh-llm-{pid}") if isinstance(fw, dict) else f"mesh-llm-{pid}",
            "type": "llm_framework",
            "provider_id": pid,
            "display_name": fw.get("display_name", pid),
            "api_key_set": fw.get("api_key_set", False),
            "configured": fw.get("configured", False),
            "linked_connectors": linked_connectors,
            "health_path": f"/llm/{pid}/status",
        })

    trinity = unified.get("trinity_roles", {})
    trinity_edges = [
        {"from": role, "to": llm_id, "relation": "trinity_role"}
        for role, llm_id in trinity.items()
    ]
    node_edges = unified.get("node_edges", [])
    ws = unified.get("workstation", {})

    return {
        "nodes": nodes,
        "segments": segments,
        "connector_llm_edges": [
            {"from": c, "to": l, "relation": "primary_llm"}
            for c, l in links.items()
        ],
        "trinity_edges": trinity_edges,
        "node_edges": node_edges,
        "workstation": ws,
        "edge_count": len(links) + len(trinity) + len(node_edges),
    }


def get_unified_status() -> dict:
    """Vollständiger verknüpfter Status aller Layer."""
    unified = _load_yaml(ROOT / "fusion_unified.yaml")
    mesh = _get_mesh_status()
    llm = _get_llm_status()
    tailscale = _get_tailscale_raw()
    workstation = _get_workstation()
    phone_check = _check_phone_visibility(unified, tailscale)
    vr_status = _get_vr_status()
    graph = _build_graph(unified, mesh, llm)

    mesh_ok = mesh.get("connectors_registered", 0) > 0 or not mesh.get("error")
    llm_ok = llm.get("any_live", False)
    net_ok = tailscale.get("online", False)

    return {
        "timestamp": datetime.now().isoformat(),
        "version": unified.get("version", "1.0"),
        "principle": unified.get("principle"),
        "layers": unified.get("layers", {}),
        "health": {
            "network": "online" if net_ok else "offline",
            "connectors": f"{mesh.get('connectors_registered', 0)}/{mesh.get('connector_count', 0)}",
            "llm": "live" if llm_ok else "no_keys",
            "vr": vr_status.get("status", "unknown"),
            "overall": "healthy" if (mesh_ok or llm_ok) else "degraded",
        },
        "vr": vr_status,
        "tailscale": tailscale,
        "mesh_summary": {
            "connector_count": mesh.get("connector_count"),
            "connectors_registered": mesh.get("connectors_registered"),
            "tailnet": mesh.get("tailnet"),
        },
        "llm_summary": {
            "count": llm.get("count"),
            "available": llm.get("available"),
            "trinity": llm.get("trinity"),
        },
        "trinity_roles": unified.get("trinity_roles", {}),
        "connector_llm_links": unified.get("connector_llm_links", {}),
        "endpoints": unified.get("endpoints", {}),
        "workstation": workstation,
        "phone_mesh": phone_check,
        "graph": graph,
    }


def get_llm_segment(provider_id: str) -> dict:
    try:
        from llm_frameworks import get_framework
        fw = get_framework(provider_id)
        if not fw:
            return {"error": f"Unknown LLM: {provider_id}"}
        status = fw.status()
        unified = _load_yaml(ROOT / "fusion_unified.yaml")
        links = unified.get("connector_llm_links", {})
        status["linked_connectors"] = [c for c, l in links.items() if l == provider_id]
        status["tailscale"] = _get_tailscale_raw()
        return status
    except Exception as e:
        return {"error": str(e)}


def orchestrate(
    query: str,
    connector: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    """Orchestriert über verknüpfte LLM-Frameworks (TRINITY oder Connector→LLM)."""
    unified = _load_yaml(ROOT / "fusion_unified.yaml")
    links = unified.get("connector_llm_links", {})
    trinity = unified.get("trinity_roles", {})

    if connector and connector in links:
        provider = links[connector]
        orch_role = role or "worker"
    elif role and role in trinity:
        provider = trinity[role]
        orch_role = role
    else:
        provider = trinity.get("worker", "gpt")
        orch_role = "worker"

    try:
        from model_connectors import invoke_model
        result = invoke_model(provider, query, role=orch_role, context={
            "routing": "fusion_integration_hub",
            "connector": connector,
        })
        return {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "connector": connector,
            "provider": provider,
            "role": orch_role,
            "ok": result.ok,
            "response": result.response,
            "latency_ms": result.latency_ms,
            "source": result.source,
            "error": result.error,
        }
    except Exception as e:
        return {"error": str(e), "provider": provider, "role": orch_role}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        out = get_unified_status()
    elif cmd == "graph":
        u = get_unified_status()
        out = u.get("graph", {})
    elif cmd == "llm" and len(sys.argv) > 2:
        out = get_llm_segment(sys.argv[2])
    elif cmd == "orchestrate" and len(sys.argv) > 2:
        connector = sys.argv[3] if len(sys.argv) > 3 else None
        out = orchestrate(sys.argv[2], connector=connector)
    else:
        out = {"error": f"Unknown command: {cmd}", "usage": "status|graph|llm <id>|orchestrate <query> [connector]"}

    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(1 if "error" in out and cmd != "status" else 0)