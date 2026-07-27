"""
Grok Interconnect — capture and evolve Grok↔Mainframe connectivity.

Maps every known Grok edge (CLI, skill, dashboard bridge, LLM provider,
PC bridge, mesh, mainframe site, MCP host affinity, sync) into a live graph,
probes reachability, and persists a snapshot for Dauer-VR / mainframe website.

Usage:
  from fusion_hero_os.core.grok_interconnect import capture, evolve, get_graph
  g = capture()
  e = evolve(g)
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "GrokNode",
    "GrokEdge",
    "InterconnectGraph",
    "capture",
    "evolve",
    "get_graph",
    "probe_http",
]

_HOME = Path.home()
_STATE = _HOME / ".fusion" / "grok_interconnect.json"
_CLI_STATUS = _HOME / ".fusion" / "grok-cli.status.json"
_SKILL = _HOME / ".grok" / "skills" / "fusion-hero-os" / "SKILL.md"
_GROK_BIN = _HOME / ".grok" / "bin" / "grok.exe"
_REPO = Path(os.getenv("FUSION_REPO_ROOT", Path(__file__).resolve().parents[2]))


@dataclass
class GrokNode:
    id: str
    kind: str  # cli | skill | bridge | llm | mesh | surface | sync | host
    label: str
    path_or_url: str = ""
    online: bool = False
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class GrokEdge:
    source: str
    target: str
    relation: str
    live: bool = False
    note: str = ""


@dataclass
class InterconnectGraph:
    version: str = "1.0"
    captured_at: float = 0.0
    platform: str = "10.0.0"
    nodes: list[GrokNode] = field(default_factory=list)
    edges: list[GrokEdge] = field(default_factory=list)
    health_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    evolved: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "captured_at": self.captured_at,
            "platform": self.platform,
            "health_score": self.health_score,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "recommendations": self.recommendations,
            "evolved": self.evolved,
            "summary": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "online_nodes": sum(1 for n in self.nodes if n.online),
                "live_edges": sum(1 for e in self.edges if e.live),
            },
        }


def probe_http(url: str, timeout: float = 2.5) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(2000)
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "bytes": len(body),
            }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def capture(*, dash_base: str = "http://127.0.0.1:8000") -> InterconnectGraph:
    """Abgreifen: build live interconnect graph of all Grok-related nodes."""
    g = InterconnectGraph(captured_at=time.time())
    nodes: list[GrokNode] = []
    edges: list[GrokEdge] = []

    # --- CLI ---
    cli_st = _read_json(_CLI_STATUS)
    cli_bin = str(_GROK_BIN) if _GROK_BIN.is_file() else "grok"
    cli_ok = bool(cli_st.get("cli_found") or _GROK_BIN.is_file())
    if not cli_ok:
        try:
            r = subprocess.run(
                [cli_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            cli_ok = r.returncode == 0
            if cli_ok:
                cli_st["cli_raw"] = (r.stdout or r.stderr or "")[:200]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    nodes.append(
        GrokNode(
            id="grok-cli",
            kind="cli",
            label="Grok CLI",
            path_or_url=cli_st.get("cli_command") or cli_bin,
            online=cli_ok,
            detail={
                "version": cli_st.get("version"),
                "checked_at": cli_st.get("checked_at"),
                "raw": cli_st.get("cli_raw"),
            },
        )
    )

    # --- Skill ---
    skill_ok = _SKILL.is_file()
    skill_chars = _SKILL.stat().st_size if skill_ok else 0
    nodes.append(
        GrokNode(
            id="grok-skill",
            kind="skill",
            label="fusion-hero-os Skill",
            path_or_url=str(_SKILL),
            online=skill_ok,
            detail={"bytes": skill_chars},
        )
    )
    edges.append(GrokEdge("grok-cli", "grok-skill", "loads_skill", live=cli_ok and skill_ok))

    # --- Dashboard Grok Bridge ---
    dash_health = probe_http(f"{dash_base}/api/health?light=true")
    grok_status = probe_http(f"{dash_base}/api/grok/status")
    nodes.append(
        GrokNode(
            id="dashboard",
            kind="surface",
            label="Dashboard :8000",
            path_or_url=dash_base,
            online=bool(dash_health.get("ok")),
            detail=dash_health,
        )
    )
    nodes.append(
        GrokNode(
            id="grok-bridge",
            kind="bridge",
            label="Grok-intern Bridge",
            path_or_url=f"{dash_base}/api/grok/status",
            online=bool(grok_status.get("ok")),
            detail=grok_status,
        )
    )
    edges.append(
        GrokEdge("dashboard", "grok-bridge", "hosts", live=bool(dash_health.get("ok") and grok_status.get("ok")))
    )
    edges.append(GrokEdge("grok-bridge", "grok-skill", "reads_skill", live=skill_ok and bool(grok_status.get("ok"))))

    # --- Mainframe site surfaces ---
    for nid, path, label in [
        ("mainframe-hub", "/mainframe", "Mainframe Website"),
        ("mainframe-vr", "/mainframe/vr", "Dauer-VR"),
        ("mainframe-ide", "/mainframe/ide", "Mainframe IDE"),
        ("mainframe-worktree", "/mainframe/worktree", "Worktree"),
    ]:
        pr = probe_http(f"{dash_base}{path}")
        nodes.append(
            GrokNode(
                id=nid,
                kind="surface",
                label=label,
                path_or_url=f"{dash_base}{path}",
                online=bool(pr.get("ok")),
                detail=pr,
            )
        )
        edges.append(GrokEdge("dashboard", nid, "serves", live=bool(pr.get("ok"))))
        edges.append(GrokEdge("grok-bridge", nid, "can_drive_via_intent", live=bool(pr.get("ok"))))

    # --- PC Bridge :8765 ---
    pc_online = _tcp_open("127.0.0.1", 8765)
    nodes.append(
        GrokNode(
            id="grok-pc-bridge",
            kind="bridge",
            label="GrokPCBridge :8765",
            path_or_url="http://127.0.0.1:8765",
            online=pc_online,
            detail={"port": 8765, "module": "src.normal_os.bridge.grok_pc_bridge"},
        )
    )
    edges.append(GrokEdge("grok-cli", "grok-pc-bridge", "optional_pc_access", live=pc_online))

    # --- LLM provider config ---
    has_key = bool(os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY"))
    llm_file = _REPO / "03_Code" / "llm_frameworks" / "grok.py"
    nodes.append(
        GrokNode(
            id="grok-llm",
            kind="llm",
            label="Grok LLM Framework (xAI API)",
            path_or_url=str(llm_file),
            online=llm_file.is_file(),
            detail={
                "api_key_configured": has_key,
                "base": os.getenv("FUSION_GROK_BASE", "https://api.x.ai/v1"),
                "model": os.getenv("FUSION_GROK_MODEL", "grok-2-latest"),
                "provider": "fusion_hero_os.providers.grok_provider",
            },
        )
    )
    edges.append(GrokEdge("grok-bridge", "grok-llm", "may_escalate_to_api", live=llm_file.is_file()))
    edges.append(GrokEdge("dashboard", "grok-llm", "provider_route", live=llm_file.is_file() and has_key))

    # --- Mesh / Tailscale ---
    mesh_online = False
    mesh_detail: dict[str, Any] = {}
    try:
        r = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            ts = json.loads(r.stdout)
            self_n = ts.get("Self") or {}
            mesh_online = True
            mesh_detail = {
                "hostname": self_n.get("HostName"),
                "ips": self_n.get("TailscaleIPs"),
                "peers": len(ts.get("Peer") or {}),
            }
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    nodes.append(
        GrokNode(
            id="tailscale-mesh",
            kind="mesh",
            label="Tailscale Mesh",
            path_or_url="tag:fusion-node-desktop",
            online=mesh_online,
            detail=mesh_detail,
        )
    )
    edges.append(GrokEdge("dashboard", "tailscale-mesh", "runs_on_mesh_host", live=mesh_online))
    edges.append(GrokEdge("grok-cli", "tailscale-mesh", "operator_on_mesh", live=mesh_online and cli_ok))

    # GCE publish mirror
    gce = probe_http("http://100.103.188.54:8088/docs/publish/v10/")
    nodes.append(
        GrokNode(
            id="gce-publish",
            kind="mesh",
            label="GCE fusion-mesh-exit publish",
            path_or_url="http://100.103.188.54:8088/docs/publish/v10/",
            online=bool(gce.get("ok")),
            detail=gce,
        )
    )
    edges.append(GrokEdge("tailscale-mesh", "gce-publish", "l2_publish_mirror", live=bool(gce.get("ok"))))

    # --- Sync state ---
    sync_script = _REPO / "sync_grok_intern.ps1"
    nodes.append(
        GrokNode(
            id="sync-grok-intern",
            kind="sync",
            label="sync_grok_intern.ps1",
            path_or_url=str(sync_script),
            online=sync_script.is_file(),
            detail={"workstation": str(_REPO / "workstation" / "sync_grok_intern.ps1")},
        )
    )
    edges.append(GrokEdge("sync-grok-intern", "grok-skill", "mirrors_skill", live=sync_script.is_file() and skill_ok))
    edges.append(GrokEdge("sync-grok-intern", "grok-cli", "checks_cli", live=sync_script.is_file()))

    # --- Coordination / race guard ---
    coord = _HOME / ".fusion" / "mesh" / "coordination" / "latest.json"
    coord_data = _read_json(coord)
    nodes.append(
        GrokNode(
            id="mesh-coordinator",
            kind="host",
            label="Mesh Coordinator State",
            path_or_url=str(coord),
            online=bool(coord_data),
            detail={
                "race_guard": coord_data.get("race_guard"),
                "generated_at": coord_data.get("generated_at"),
                "tiers": (coord_data.get("plan") or {}).get("online_tiers"),
            },
        )
    )
    edges.append(
        GrokEdge(
            "grok-cli",
            "mesh-coordinator",
            "operator_triggers_coord",
            live=bool(coord_data),
            note="race_guard protects multi-writer",
        )
    )

    # --- MCP host affinity (desktop / grok workstation) ---
    nodes.append(
        GrokNode(
            id="mcp-host",
            kind="host",
            label="MCP Bridges (Grok session host)",
            path_or_url="L1_mainframe",
            online=True,  # this session is evidence of MCP host
            detail={
                "connectors": [
                    "github", "gmail", "google_drive", "google_calendar",
                    "canva", "gamma", "notion", "vercel", "tasks",
                ],
                "principle": "MCP stays on mainframe; Grok drives via tools",
            },
        )
    )
    edges.append(GrokEdge("grok-cli", "mcp-host", "uses_mcp_tools", live=True))
    edges.append(GrokEdge("mcp-host", "dashboard", "same_operator_machine", live=bool(dash_health.get("ok"))))

    g.nodes = nodes
    g.edges = edges

    # health score
    n_on = sum(1 for n in nodes if n.online)
    e_live = sum(1 for e in edges if e.live)
    g.health_score = round(
        0.6 * (n_on / max(1, len(nodes))) + 0.4 * (e_live / max(1, len(edges))),
        3,
    )

    # recommendations
    rec: list[str] = []
    if not skill_ok:
        rec.append("Run sync_grok_intern.ps1 to restore fusion-hero-os skill")
    if not cli_ok:
        rec.append("Install/repair Grok CLI (~/.grok/bin/grok.exe)")
    if not dash_health.get("ok"):
        rec.append("Start Dashboard: uvicorn app:app --port 8000 (FUSION_AUTO_LOAD=0)")
    if not has_key:
        rec.append("Optional: set XAI_API_KEY for full Grok LLM API path")
    if not pc_online:
        rec.append("Optional: start GrokPCBridge on :8765 for desktop file bridge")
    if not gce.get("ok"):
        rec.append("GCE publish offline or not reachable via Tailscale")
    if g.health_score < 0.7:
        rec.append("Interconnect health < 0.7 — prioritize skill+dashboard+cli")
    g.recommendations = rec

    _persist(g)
    return g


def evolve(graph: InterconnectGraph | None = None) -> InterconnectGraph:
    """Weiterentwickeln: enrich graph with action routes and intent map."""
    g = graph or capture()
    # Intent → target surface map (extends grok_bridge)
    intent_map = {
        "mainframe": "/mainframe",
        "dauer_vr": "/mainframe/vr",
        "ide": "/mainframe/ide",
        "worktree": "/mainframe/worktree",
        "ops": "/mainframe/ops",
        "health": "/api/health",
        "mesh_status": "/api/mainframe/site/status",
        "interconnect": "/api/grok/interconnect",
        "coord": "~/.fusion/mesh/coordination/latest.json",
        "publish": "http://100.103.188.54:8088/docs/publish/v10/",
    }
    # Missing edges we want to grow
    online_ids = {n.id for n in g.nodes if n.online}
    growth = []
    if "dashboard" in online_ids and "mainframe-hub" in online_ids:
        growth.append("mainframe_site_operational")
    if "tailscale-mesh" in online_ids and "gce-publish" in online_ids:
        growth.append("l2_publish_path_live")
    if "grok-cli" in online_ids and "mcp-host" in online_ids:
        growth.append("session_mcp_host_active")
    if "mesh-coordinator" in online_ids:
        growth.append("coord_state_present")

    # merge canonical route table (alles umgeroutet)
    route_table: dict[str, Any] = {}
    try:
        from fusion_hero_os.core.grok_route_table import ROUTE_TABLE, all_routes

        route_table = all_routes()
        for k, rt in ROUTE_TABLE.items():
            intent_map[k] = rt.surface or rt.api
    except Exception as exc:  # noqa: BLE001
        route_table = {"error": str(exc)}

    g.evolved = {
        "intent_map": intent_map,
        "route_table": route_table.get("table") if isinstance(route_table, dict) else {},
        "entrypoints": route_table.get("entrypoints") if isinstance(route_table, dict) else {},
        "legacy_redirects": route_table.get("legacy_redirects") if isinstance(route_table, dict) else {},
        "growth_flags": growth,
        "next_intents_for_bridge": [
            "mainframe", "dauer_vr", "ide", "worktree", "interconnect",
            "mesh", "publish", "race_guard", "coord",
        ],
        "architecture": {
            "control_plane": "grok-cli + mcp-host (L1) → /mainframe/grok",
            "local_brain": "dashboard + grok-bridge + grok_route_table",
            "optional_api": "grok-llm (xAI)",
            "mesh_anchor": "gce-publish (L2)",
            "sync": "sync_grok_intern.ps1 → skill + workspace",
            "routing": "all intents resolve via fusion_hero_os.core.grok_route_table",
        },
    }
    # bump recommendations from evolve
    if "mainframe_site_operational" not in growth:
        g.recommendations.append("Bring /mainframe surfaces online for full interconnect")
    _persist(g)
    return g


def get_graph(*, refresh: bool = False) -> dict[str, Any]:
    if not refresh and _STATE.is_file():
        age = time.time() - _STATE.stat().st_mtime
        if age < 30:
            data = _read_json(_STATE)
            if data:
                return data
    return evolve(capture()).to_dict()


def _persist(g: InterconnectGraph) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    payload = g.to_dict()
    try:
        from fusion_hero_os.core.race_guard import locked_atomic_write_json

        locked_atomic_write_json(_STATE, payload)
    except Exception:  # noqa: BLE001
        _STATE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(evolve(capture()).to_dict(), indent=2, ensure_ascii=False))
