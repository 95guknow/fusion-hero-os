#!/usr/bin/env python3
"""
Fusion Hero OS — Framework Kreuzvernetzung (vollständiges Mesh)

Prinzip: Jedes Framework / Segment ist eigenständig UND mit JEDEM anderen
über bidirektionale Kanten verbunden (Kreuznetz), nicht nur 1:1-Primärlinks.

Verknüpft:
  • alle LLM-Frameworks untereinander (vollständiger Graph)
  • alle MCP-Connectoren ↔ alle LLM-Frameworks (primary + secondary mesh)
  • Agent-Triade: agent ↔ anti_agent ↔ quantizer
  • OS-Layer untereinander + zu intelligence/orchestration
  • QUBO / local-llama / Firebase Landing / Integration Hub
"""
from __future__ import annotations

import itertools
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parent
CODE = ROOT / "03_Code"
for p in (ROOT, CODE, CODE / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ── kanonische ID-Listen ───────────────────────────────────────────────────

DEFAULT_CONNECTORS = (
    "github", "gmail", "google_drive", "google_calendar",
    "canva", "gamma", "notion", "vercel", "hyperframes", "tasks",
    "google_tasks",  # alias
)

AGENT_TRIAD = (
    {"id": "agent", "role": "proposer", "backend": "llama-local", "kind": "agent"},
    {"id": "anti_agent", "role": "verifier", "backend": "grok-intern", "kind": "anti_agent"},
    {"id": "quantizer", "role": "string_quantizer", "backend": "local", "kind": "quantizer"},
)

SYSTEM_SEGMENTS = (
    {"id": "qubo_engine", "type": "compute", "module": "qb_qubo / qubo_llama_bridge"},
    {"id": "local_llama", "type": "llm_local", "module": "03_Code/core/local_llama.py"},
    {"id": "agent_backend_router", "type": "orchestration", "module": "agent_backend_router"},
    {"id": "string_quantizer", "type": "agent", "module": "string_quantizer_agent"},
    {"id": "fusion_integration_hub", "type": "hub", "module": "fusion_integration_hub"},
    {"id": "fractal_mainframe_mesh", "type": "mesh", "module": "fractal_mainframe_mesh"},
    {"id": "firebase_landing", "type": "surface", "url": "https://project-bbf0e6db-52e1-462b-8e3.web.app"},
    {"id": "hero_docs", "type": "surface", "port": 8088},
    {"id": "dashboard", "type": "surface", "port": 8000},
)


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    return {}


def _unique_edge(a: str, b: str, relation: str) -> Tuple[str, str, str]:
    """Normalisierte Kante (undirected key, directed payload)."""
    lo, hi = sorted((a, b))
    return lo, hi, relation


def full_mesh_edges(
    ids: Sequence[str],
    relation: str = "cross_mesh",
) -> List[Dict[str, str]]:
    """Vollständiger ungerichteter Graph als gerichtete Paare (bidirektional)."""
    edges: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    for a, b in itertools.combinations(ids, 2):
        for src, dst in ((a, b), (b, a)):
            key = (src, dst, relation)
            if key in seen:
                continue
            seen.add(key)
            edges.append({"from": src, "to": dst, "relation": relation, "bidirectional": True})
    return edges


def bipartite_mesh(
    left: Sequence[str],
    right: Sequence[str],
    relation: str = "cross_link",
    primary: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Kreuznetz zwischen zwei Mengen (jeder mit jedem)."""
    primary = primary or {}
    edges: List[Dict[str, Any]] = []
    for a in left:
        for b in right:
            is_primary = primary.get(a) == b
            edges.append({
                "from": a,
                "to": b,
                "relation": "primary_llm" if is_primary else relation,
                "primary": is_primary,
                "bidirectional": True,
            })
            edges.append({
                "from": b,
                "to": a,
                "relation": "serves_connector" if is_primary else f"rev_{relation}",
                "primary": is_primary,
                "bidirectional": True,
            })
    return edges


def list_llm_framework_ids() -> List[str]:
    try:
        from llm_frameworks import list_frameworks
        ids = list(list_frameworks())
        if ids:
            return ids
    except Exception:
        pass
    cfg = _load_yaml(ROOT / "llm_frameworks.yaml")
    return list((cfg.get("frameworks") or {}).keys())


def list_connector_ids(unified: Optional[dict] = None) -> List[str]:
    u = unified if unified is not None else _load_yaml(ROOT / "fusion_unified.yaml")
    links = u.get("connector_llm_links") or {}
    ids = list(links.keys())
    if not ids:
        ids = list(DEFAULT_CONNECTORS)
    # dedupe keep order
    seen: Set[str] = set()
    out: List[str] = []
    for c in ids:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def list_layer_ids(unified: Optional[dict] = None) -> List[str]:
    u = unified if unified is not None else _load_yaml(ROOT / "fusion_unified.yaml")
    layers = u.get("layers") or {}
    return list(layers.keys()) if layers else [
        "network", "connectors", "intelligence", "orchestration",
        "surface", "kernel", "ascension", "knowledge",
    ]


def build_cross_mesh(unified: Optional[dict] = None) -> Dict[str, Any]:
    """
    Baut das vollständige Kreuznetz:
      frameworks × frameworks
      connectors × frameworks
      agents × agents
      layers × layers
      system segments × hub
    """
    u = unified if unified is not None else _load_yaml(ROOT / "fusion_unified.yaml")
    primary = dict(u.get("connector_llm_links") or {})
    # fallback from llm_frameworks.yaml
    if not primary:
        y = _load_yaml(ROOT / "llm_frameworks.yaml")
        primary = dict(y.get("connector_links") or {})

    frameworks = list_llm_framework_ids()
    connectors = list_connector_ids(u)
    layers = list_layer_ids(u)
    agents = [a["id"] for a in AGENT_TRIAD]
    systems = [s["id"] for s in SYSTEM_SEGMENTS]

    fw_edges = full_mesh_edges(frameworks, "framework_cross")
    conn_fw_edges = bipartite_mesh(connectors, frameworks, "connector_framework_mesh", primary)
    agent_edges = full_mesh_edges(agents, "agent_triad_cross")
    layer_edges = full_mesh_edges(layers, "layer_cross")
    # existing declared edges kept + marked
    declared_layer = list(u.get("layer_edges") or [])
    declared_node = list(u.get("node_edges") or [])

    # system hub star + mesh among key systems
    sys_edges = full_mesh_edges(systems, "system_cross")
    # each framework ↔ hub + quantizer + qubo
    for fw in frameworks:
        for hub in ("fusion_integration_hub", "agent_backend_router", "string_quantizer", "qubo_engine"):
            sys_edges.append({"from": fw, "to": hub, "relation": "framework_to_system", "bidirectional": True})
            sys_edges.append({"from": hub, "to": fw, "relation": "system_to_framework", "bidirectional": True})

    # agent triad ↔ frameworks (role defaults)
    trinity = u.get("trinity_roles") or {"thinker": "claude", "worker": "gpt", "verifier": "grok"}
    agent_fw: List[Dict[str, Any]] = []
    role_map = {
        "agent": trinity.get("worker", "gpt"),
        "anti_agent": trinity.get("verifier", "grok"),
        "quantizer": "ollama" if "ollama" in frameworks else frameworks[0] if frameworks else "grok",
    }
    for ag in agents:
        for fw in frameworks:
            primary_link = role_map.get(ag) == fw
            agent_fw.append({
                "from": ag, "to": fw,
                "relation": "agent_primary_llm" if primary_link else "agent_framework_mesh",
                "primary": primary_link,
                "bidirectional": True,
            })

    all_edges = (
        fw_edges + conn_fw_edges + agent_edges + layer_edges
        + declared_layer + declared_node + sys_edges + agent_fw
    )

    # nodes catalog
    nodes: List[Dict[str, Any]] = []
    for pid in frameworks:
        nodes.append({"id": pid, "type": "llm_framework", "mesh": "framework"})
    for cid in connectors:
        nodes.append({
            "id": cid,
            "type": "mcp_connector",
            "mesh": "connector",
            "primary_llm": primary.get(cid),
        })
    for a in AGENT_TRIAD:
        nodes.append({**a, "type": "agent", "mesh": "triad"})
    for lid in layers:
        cfg = (u.get("layers") or {}).get(lid) or {}
        nodes.append({
            "id": lid,
            "type": "layer",
            "mesh": "layer",
            "module": cfg.get("module"),
            "health": cfg.get("health"),
        })
    for s in SYSTEM_SEGMENTS:
        nodes.append({**s, "mesh": "system"})

    # adjacency degree
    degree: Dict[str, int] = {}
    for e in all_edges:
        if not isinstance(e, dict):
            continue
        fr, to = e.get("from"), e.get("to")
        if fr:
            degree[fr] = degree.get(fr, 0) + 1
        if to:
            degree[to] = degree.get(to, 0) + 1

    n_fw = len(frameworks)
    expected_fw_undirected = n_fw * (n_fw - 1) // 2 if n_fw > 1 else 0

    return {
        "timestamp": datetime.now().isoformat(),
        "principle": "full_cross_mesh — jedes Framework mit jedem",
        "platform_version": u.get("platform_version") or "12.0.0",
        "counts": {
            "frameworks": n_fw,
            "connectors": len(connectors),
            "agents": len(agents),
            "layers": len(layers),
            "systems": len(systems),
            "nodes": len(nodes),
            "edges": len(all_edges),
            "framework_mesh_pairs_undirected": expected_fw_undirected,
            "framework_mesh_edges_directed": len(fw_edges),
            "connector_framework_edges": len(conn_fw_edges),
            "agent_triad_edges": len(agent_edges),
            "layer_cross_edges": len(layer_edges),
        },
        "frameworks": frameworks,
        "connectors": connectors,
        "agents": list(AGENT_TRIAD),
        "layers": layers,
        "systems": list(SYSTEM_SEGMENTS),
        "primary_connector_llm": primary,
        "trinity_roles": trinity,
        "nodes": nodes,
        "edges": all_edges,
        "degree": degree,
        "fully_connected_frameworks": expected_fw_undirected > 0 and len(fw_edges) == expected_fw_undirected * 2,
        "emit_policy": "whole_string_logical_never_char_stream",  # quantizer present
        "endpoints": {
            "cross_mesh": "/fusion/cross",
            "cross_mesh_alias": "/fusion/crossmesh",
            "graph": "/fusion/graph",
            "status": "/fusion/status",
            "llm": "/llm/status",
        },
    }


def neighbor_map(mesh: Optional[dict] = None) -> Dict[str, List[str]]:
    m = mesh or build_cross_mesh()
    adj: Dict[str, Set[str]] = {}
    for e in m.get("edges") or []:
        if not isinstance(e, dict):
            continue
        a, b = e.get("from"), e.get("to")
        if not a or not b:
            continue
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {k: sorted(v) for k, v in sorted(adj.items())}


def route_via_mesh(
    source: str,
    target: str,
    mesh: Optional[dict] = None,
) -> Dict[str, Any]:
    """BFS-Pfad im Kreuznetz (shortest path)."""
    m = mesh or build_cross_mesh()
    adj = neighbor_map(m)
    if source not in adj:
        return {"ok": False, "error": f"unknown source: {source}", "path": []}
    if source == target:
        return {"ok": True, "path": [source], "hops": 0}
    from collections import deque
    q = deque([(source, [source])])
    seen = {source}
    while q:
        node, path = q.popleft()
        for nxt in adj.get(node, []):
            if nxt in seen:
                continue
            np = path + [nxt]
            if nxt == target:
                return {"ok": True, "path": np, "hops": len(np) - 1}
            seen.add(nxt)
            q.append((nxt, np))
    return {"ok": False, "error": "no path", "path": []}


def orchestrate_cross(
    query: str,
    prefer: Optional[Sequence[str]] = None,
    max_providers: int = 3,
) -> Dict[str, Any]:
    """
    Kreuz-Orchestrierung: nutzt Mesh-Nachbarn / Trinity + Free-Chain,
    emittiert whole-string Logik über Quantisierer.
    """
    mesh = build_cross_mesh()
    prefer = list(prefer or [])
    try:
        from llm_frameworks import connector_status, invoke, filter_llm_pool, list_frameworks
        st = connector_status()
        available = list(st.get("available") or [])
        free = list(st.get("free_ready") or [])
        pool = prefer or list(st.get("trinity") or []) + free + available
        pool = filter_llm_pool(pool, max_models=max_providers)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "mesh_counts": mesh["counts"]}

    results = []
    for pid in pool:
        try:
            from llm_frameworks import invoke as inv
            r = inv(pid, query, role="worker", context={"routing": "framework_cross_mesh"})
            results.append(r.to_dict() if hasattr(r, "to_dict") else dict(r))
        except Exception as exc:
            results.append({"provider_id": pid, "ok": False, "error": str(exc)})

    # Quantisierer (3. Agent) auf Synthese
    synthesis_parts = []
    for r in results:
        if r.get("ok") and r.get("response"):
            synthesis_parts.append(str(r["response"]))
    synthesis = "\n\n---\n\n".join(synthesis_parts)
    quant = None
    try:
        from string_quantizer_agent import accompany, emit_logical
        if synthesis.strip():
            synthesis = emit_logical(synthesis)
            quant = accompany(query, synthesis, "")
    except Exception as exc:
        quant = {"ok": False, "error": str(exc)}

    return {
        "ok": any(r.get("ok") for r in results),
        "query": query,
        "pool": pool,
        "results": results,
        "synthesis": synthesis[:12000],
        "quantizer": quant,
        "mesh": {
            "frameworks": mesh["frameworks"],
            "counts": mesh["counts"],
            "fully_connected_frameworks": mesh["fully_connected_frameworks"],
        },
        "routing": "framework_cross_mesh",
        "timestamp": datetime.now().isoformat(),
    }


def cross_mesh_status() -> Dict[str, Any]:
    mesh = build_cross_mesh()
    llm = {}
    try:
        from llm_frameworks import connector_status
        llm = connector_status()
    except Exception as exc:
        llm = {"error": str(exc)}
    agents = {}
    try:
        from agent_backend_router import policy, status as abr_status
        agents = {"policy": policy(), "status": abr_status()}
    except Exception as exc:
        agents = {"error": str(exc)}
    quant = {}
    try:
        from string_quantizer_agent import get_quantizer
        quant = get_quantizer().status()
    except Exception as exc:
        quant = {"error": str(exc)}

    return {
        "ok": True,
        "cross_mesh": True,
        "timestamp": datetime.now().isoformat(),
        "counts": mesh["counts"],
        "fully_connected_frameworks": mesh["fully_connected_frameworks"],
        "frameworks": mesh["frameworks"],
        "connectors": mesh["connectors"],
        "agents": mesh["agents"],
        "layers": mesh["layers"],
        "llm_live": llm,
        "agent_router": agents,
        "quantizer": quant,
        "sample_routes": {
            "github→claude": route_via_mesh("github", "claude", mesh),
            "agent→quantizer": route_via_mesh("agent", "quantizer", mesh),
            "grok→ollama": route_via_mesh("grok", "ollama", mesh) if "ollama" in mesh["frameworks"] else {},
            "kernel→intelligence": route_via_mesh("kernel", "intelligence", mesh),
        },
        "endpoints": mesh["endpoints"],
        "degree_top": sorted(
            mesh["degree"].items(), key=lambda x: -x[1]
        )[:15],
    }


if __name__ == "__main__":
    import json
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        out = cross_mesh_status()
    elif cmd == "mesh":
        out = build_cross_mesh()
        # compact: drop full edge list for CLI readability unless --full
        if "--full" not in sys.argv:
            out = {**out, "edges": f"<{len(out.get('edges', []))} edges — pass --full>"}
    elif cmd == "route" and len(sys.argv) >= 4:
        out = route_via_mesh(sys.argv[2], sys.argv[3])
    elif cmd == "orchestrate" and len(sys.argv) >= 3:
        out = orchestrate_cross(sys.argv[2])
    else:
        out = {
            "error": "usage: status|mesh [--full]|route <from> <to>|orchestrate <query>",
        }
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
