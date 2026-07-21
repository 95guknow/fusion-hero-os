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
        "vr_builder_hero_equirectangular.jpg",
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
        import sys

        ws_dir = ws.parent
        if str(ws_dir) not in sys.path:
            sys.path.insert(0, str(ws_dir))
        from resolve_paths import resolve_paths  # type: ignore[import-not-found]

        return {"configured": True, "paths": resolve_paths(ws_dir), "source": str(ws)}
    except Exception as e:
        return {"configured": False, "error": str(e)}


def _check_phone_visibility(unified: dict, tailscale: dict) -> dict:
    """Warnung wenn Phone in Config aber nicht in Tailscale-Peers."""
    phone_cfg = (unified.get("nodes") or {}).get("phone", {})
    expected = phone_cfg.get("hostname", "phone-node")
    aliases = [expected.lower()]
    aliases.extend(a.lower() for a in phone_cfg.get("hostname_aliases", []))
    aliases.extend(["redmi", "android"])
    peer_list = tailscale.get("peer_list") or []
    found_peer = None
    for p in peer_list:
        hn = (p.get("hostname") or "").lower()
        dns = (p.get("magicdns") or "").lower()
        os_name = (p.get("os") or "").lower()
        if os_name == "android" or any(a in hn or a in dns for a in aliases):
            found_peer = p
            break
    found = found_peer is not None
    hint = phone_cfg.get("login_hint") or (
        "Handy und PC muessen im gleichen Tailnet sein (gleicher Login: Google, nicht GitHub)"
    )
    file_mirror = {}
    try:
        from mesh_file_share import get_mirror_status
        file_mirror = get_mirror_status()
    except Exception as e:
        file_mirror = {"error": str(e)}
    return {
        "expected_hostname": expected,
        "resolved_hostname": (found_peer or {}).get("hostname"),
        "visible": found,
        "online": (found_peer or {}).get("online", False),
        "peer_count": tailscale.get("peers", 0),
        "account_login": tailscale.get("login"),
        "fix_hint": None if found else hint,
        "file_mirror": file_mirror,
    }


def _get_layer_registry_status() -> dict:
    """Status aller Layer (inkl. kernel/ascension/tarnkappe/android/knowledge, v8.3)."""
    try:
        from fusion_hero_os.core.layer_registry import get_all_layer_status
        return get_all_layer_status()
    except Exception as e:
        return {"error": str(e), "layer": "layer_registry"}


def _get_erkenntnisse_status() -> dict:
    """Zusammenfassung des Erkenntnis-Index (docs/v8/erkenntnisse_index.yaml)."""
    try:
        from fusion_hero_os.core.layer_registry import erkenntnisse_summary
        return erkenntnisse_summary()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _get_fractal_mesh_status() -> dict:
    """Fractal mainframe persistence + virtual exit node catalog."""
    try:
        from fractal_mainframe_mesh import get_fractal_status
        status = get_fractal_status()
        try:
            from mesh_cloud_backends import cloud_backends_status
            status["cloud_backends"] = cloud_backends_status()
        except Exception as exc:
            status["cloud_backends"] = {"error": str(exc)}
        return status
    except Exception as e:
        return {"ok": False, "error": str(e), "layer": "fractal_mesh"}


def _build_graph(unified: dict, mesh: dict, llm: dict) -> dict:
    """Build linked graph: nodes → connectors → LLMs + full Kreuzvernetzung."""
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
        # Kreuz: alle Frameworks als secondary
        all_fw = list(frameworks.keys()) if isinstance(frameworks, dict) else []
        segments.append({
            "id": seg.get("mesh_id", f"mesh-connector-{cid}"),
            "type": "mcp_connector",
            "connector_id": cid,
            "segment_status": seg.get("segment_status"),
            "linked_llm": linked_llm,
            "linked_llm_status": "configured" if llm_info.get("configured") else "pending",
            "cross_linked_frameworks": all_fw,
            "health_path": seg.get("health_path"),
            "edge": f"{cid} → {linked_llm}" if linked_llm else None,
        })

    for pid, fw in frameworks.items():
        linked_connectors = [c for c, l in links.items() if l == pid]
        peer_frameworks = [p for p in frameworks.keys() if p != pid]
        segments.append({
            "id": fw.get("mesh_id", f"mesh-llm-{pid}") if isinstance(fw, dict) else f"mesh-llm-{pid}",
            "type": "llm_framework",
            "provider_id": pid,
            "display_name": fw.get("display_name", pid),
            "api_key_set": fw.get("api_key_set", False),
            "configured": fw.get("configured", False),
            "linked_connectors": linked_connectors,
            "cross_linked_frameworks": peer_frameworks,
            "cross_linked_connectors": list(links.keys()),
            "health_path": f"/llm/{pid}/status",
        })

    trinity = unified.get("trinity_roles", {})
    trinity_edges = [
        {"from": role, "to": llm_id, "relation": "trinity_role"}
        for role, llm_id in trinity.items()
    ]
    node_edges = unified.get("node_edges", [])
    layer_edges = unified.get("layer_edges", [])
    ws = unified.get("workstation", {})

    layer_nodes = [
        {"id": lid, "type": "layer", "module": (cfg or {}).get("module"),
         "health": (cfg or {}).get("health")}
        for lid, cfg in (unified.get("layers") or {}).items()
    ]

    # Full Kreuzvernetzung (alle Frameworks × alle Frameworks, Connectoren, Agenten, Layer)
    cross = {}
    try:
        from framework_cross_mesh import build_cross_mesh
        cross = build_cross_mesh(unified)
    except Exception as exc:
        cross = {"error": str(exc), "counts": {}}

    primary_edges = [
        {"from": c, "to": l, "relation": "primary_llm"}
        for c, l in links.items()
    ]
    edge_count = (
        len(primary_edges)
        + len(trinity)
        + len(node_edges)
        + len(layer_edges)
        + int((cross.get("counts") or {}).get("edges") or 0)
    )

    return {
        "nodes": nodes,
        "layer_nodes": layer_nodes,
        "segments": segments,
        "connector_llm_edges": primary_edges,
        "trinity_edges": trinity_edges,
        "node_edges": node_edges,
        "layer_edges": layer_edges,
        "cross_mesh": {
            "enabled": True,
            "counts": cross.get("counts"),
            "fully_connected_frameworks": cross.get("fully_connected_frameworks"),
            "frameworks": cross.get("frameworks"),
            "connectors": cross.get("connectors"),
            "agents": cross.get("agents"),
            "systems": cross.get("systems"),
            # edges can be large — summary + pointer
            "edge_count": (cross.get("counts") or {}).get("edges"),
            "detail_endpoint": "/fusion/cross",
        },
        "workstation": ws,
        "edge_count": edge_count,
        "principle": "full_cross_mesh",
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
    layer_registry = _get_layer_registry_status()
    erkenntnisse = _get_erkenntnisse_status()
    fractal_mesh = _get_fractal_mesh_status()

    mesh_ok = mesh.get("connectors_registered", 0) > 0 or not mesh.get("error")
    llm_ok = llm.get("any_live", False)
    net_ok = tailscale.get("online", False)

    return {
        "timestamp": datetime.now().isoformat(),
        "version": unified.get("version", "1.0"),
        "principle": unified.get("principle"),
        "layers": unified.get("layers", {}),
        "layer_registry": layer_registry,
        "erkenntnisse": erkenntnisse,
        "health": {
            "network": "online" if net_ok else "offline",
            "connectors": f"{mesh.get('connectors_registered', 0)}/{mesh.get('connector_count', 0)}",
            "llm": "live" if llm_ok else "no_keys",
            "vr": vr_status.get("status", "unknown"),
            "layers": f"{layer_registry.get('layers_ok', 0)}/{layer_registry.get('layer_count', 0)}",
            "erkenntnisse": "indexed" if erkenntnisse.get("ok") else "pending",
            "fractal_mesh": "saved" if fractal_mesh.get("fractal_manifest", {}).get("ok") else "pending",
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
        "fractal_mesh": fractal_mesh,
        "graph": graph,
        "cross_mesh": _get_cross_mesh_summary(unified),
    }


def _get_cross_mesh_summary(unified: Optional[dict] = None) -> dict:
    try:
        from framework_cross_mesh import cross_mesh_status
        return cross_mesh_status()
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
    cross: bool = False,
) -> dict:
    """Orchestriert über verknüpfte LLM-Frameworks (TRINITY, Connector→LLM oder Kreuznetz)."""
    if cross or os.getenv("FUSION_ORCHESTRATE_CROSS", "0") == "1":
        try:
            from framework_cross_mesh import orchestrate_cross
            return orchestrate_cross(query)
        except Exception as e:
            return {"error": str(e), "routing": "framework_cross_mesh"}

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
        # Post: Quantisierer (whole-string) + Kreuz-Nachbarn annotieren
        payload = {
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
        try:
            from framework_cross_mesh import neighbor_map, build_cross_mesh
            nm = neighbor_map(build_cross_mesh(unified))
            payload["cross_neighbors"] = nm.get(provider, [])[:12]
        except Exception:
            pass
        try:
            from string_quantizer_agent import emit_logical, accompany
            if result.ok and result.response:
                payload["response"] = emit_logical(result.response)
                payload["quantizer"] = accompany(query, payload["response"], "")
        except Exception:
            pass
        return payload
    except Exception as e:
        return {"error": str(e), "provider": provider, "role": orch_role}


def get_cross_mesh() -> dict:
    """Vollständiges Kreuznetz aller Frameworks."""
    try:
        from framework_cross_mesh import build_cross_mesh, cross_mesh_status
        mesh = build_cross_mesh()
        status = cross_mesh_status()
        return {"ok": True, "mesh": mesh, "status": status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        out = get_unified_status()
    elif cmd == "graph":
        u = get_unified_status()
        out = u.get("graph", {})
    elif cmd in ("cross", "crossmesh", "kreuz"):
        out = get_cross_mesh()
        if "--full" not in sys.argv and out.get("ok") and "mesh" in out:
            m = out["mesh"]
            out = {
                "ok": True,
                "status": out.get("status"),
                "mesh_summary": {
                    "counts": m.get("counts"),
                    "frameworks": m.get("frameworks"),
                    "connectors": m.get("connectors"),
                    "fully_connected_frameworks": m.get("fully_connected_frameworks"),
                    "edges": f"<{m.get('counts', {}).get('edges', 0)} — pass --full>",
                },
            }
    elif cmd == "llm" and len(sys.argv) > 2:
        out = get_llm_segment(sys.argv[2])
    elif cmd == "orchestrate" and len(sys.argv) > 2:
        connector = sys.argv[3] if len(sys.argv) > 3 else None
        use_cross = "--cross" in sys.argv
        out = orchestrate(sys.argv[2], connector=connector, cross=use_cross)
    else:
        out = {
            "error": f"Unknown command: {cmd}",
            "usage": "status|graph|cross|llm <id>|orchestrate <query> [connector] [--cross]",
        }

    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    sys.exit(1 if "error" in out and cmd not in ("status", "cross", "crossmesh", "kreuz", "graph") else 0)