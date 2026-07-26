"""
Grok Route Table — single source of truth for re-routing all Grok interconnect traffic.

Every intent/surface/API entry point resolves through this table so Mainframe,
Dauer-VR, IDE, Worktree, Mesh, Publish and Bridge stay coherent.

Usage:
  from fusion_hero_os.core.grok_route_table import resolve, route_message, ROUTE_TABLE
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "RouteTarget",
    "ROUTE_TABLE",
    "LEGACY_REDIRECTS",
    "resolve",
    "route_message",
    "all_routes",
]


@dataclass
class RouteTarget:
    intent: str
    surface: str          # primary UI path or URL
    api: str = ""         # primary API if any
    kind: str = "surface"  # surface | api | action | external
    node_id: str = ""     # interconnect node id
    aliases: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Canonical routing after "alles umrouten"
ROUTE_TABLE: Dict[str, RouteTarget] = {
    "interconnect": RouteTarget(
        "interconnect",
        "/mainframe/grok",
        "/api/grok/interconnect",
        "surface",
        "grok-bridge",
        ["grok-graph", "vernetzung", "grok"],
        "Grok interconnect capture/evolve graph",
    ),
    "mainframe": RouteTarget(
        "mainframe",
        "/mainframe",
        "/api/mainframe/site/status",
        "surface",
        "mainframe-hub",
        ["portal", "mainframe website", "hub"],
        "Mainframe website hub",
    ),
    "dauer_vr": RouteTarget(
        "dauer_vr",
        "/mainframe/vr",
        "/api/vr/status",
        "surface",
        "mainframe-vr",
        ["vr", "persistent-vr", "dauer-vr"],
        "Always-on Dauer-VR",
    ),
    "ide": RouteTarget(
        "ide",
        "/mainframe/ide",
        "/api/mainframe/ide/status",
        "surface",
        "mainframe-ide",
        ["ide-shell", "editor"],
        "Browser IDE shell",
    ),
    "worktree": RouteTarget(
        "worktree",
        "/mainframe/worktree",
        "/api/mainframe/worktree/list",
        "surface",
        "mainframe-worktree",
        ["tree", "repo", "files"],
        "Hyperlinked worktree",
    ),
    "ops": RouteTarget(
        "ops",
        "/mainframe/ops",
        "/api/mainframe/ops/summary",
        "surface",
        "dashboard",
        ["mainframe-ops", "cost"],
        "Ops console",
    ),
    "health": RouteTarget(
        "health",
        "/mainframe",
        "/api/health",
        "api",
        "dashboard",
        ["status", "zustand"],
        "System health",
    ),
    "mesh": RouteTarget(
        "mesh",
        "/mainframe/grok",
        "/api/mainframe/site/status",
        "api",
        "tailscale-mesh",
        ["tailscale", "coord", "coordinator"],
        "Mesh + coordinator via interconnect",
    ),
    "publish": RouteTarget(
        "publish",
        "http://100.103.188.54:8088/docs/publish/v10/",
        "",
        "external",
        "gce-publish",
        ["gce", "releases"],
        "GCE L2 publish mirror",
    ),
    "race_guard": RouteTarget(
        "race_guard",
        "/mainframe/grok",
        "/api/grok/interconnect",
        "api",
        "mesh-coordinator",
        ["race-condition", "race"],
        "Race-guard / multi-writer safety",
    ),
    "chat": RouteTarget(
        "chat",
        "/mainframe/grok",
        "/api/grok/chat",
        "api",
        "grok-bridge",
        ["message", "ask"],
        "Grok chat entry (re-routed via interconnect)",
    ),
    "load_all": RouteTarget(
        "load_all",
        "/mainframe",
        "/api/load-all",
        "action",
        "dashboard",
        ["load-all", "alle laden"],
        "Load all modules",
    ),
    "mainframe_load": RouteTarget(
        "mainframe_load",
        "/mainframe",
        "/api/mainframe/load",
        "action",
        "dashboard",
        ["lade mainframe"],
        "Boot mainframe core",
    ),
    "qubo": RouteTarget(
        "qubo",
        "/mainframe",
        "/api/v12/orchestrate",
        "action",
        "dashboard",
        ["solve", "optimier"],
        "QUBO / orchestration",
    ),
    "sync": RouteTarget(
        "sync",
        "/mainframe/grok",
        "/api/v12/sync",
        "action",
        "sync-grok-intern",
        ["horkrux", "medienserver"],
        "Sync / Horkrux",
    ),
    "pipeline": RouteTarget(
        "pipeline",
        "/mainframe",
        "/api/mainframe/pipeline",
        "api",
        "dashboard",
        ["kaskade"],
        "Mainframe pipeline",
    ),
    "layer4": RouteTarget(
        "layer4",
        "/highest-layer-vr",
        "/api/layer4/status",
        "surface",
        "mainframe-vr",
        ["highest-layer", "highest layer"],
        "Highest layer VR",
    ),
    "ht_on": RouteTarget(
        "ht_on",
        "/mainframe",
        "/api/hyperthreading",
        "action",
        "dashboard",
        ["hyperthread"],
        "Enable hyperthreading",
    ),
    "ht_off": RouteTarget(
        "ht_off",
        "/mainframe",
        "/api/hyperthreading",
        "action",
        "dashboard",
        [],
        "Disable hyperthreading",
    ),
    "agents": RouteTarget(
        "agents",
        "/mainframe",
        "/api/modules",
        "api",
        "dashboard",
        ["agenten"],
        "Agents / modules",
    ),
    "architecture": RouteTarget(
        "architecture",
        "/architecture",
        "/api/architecture/atlas",
        "surface",
        "dashboard",
        ["atlas", "dependency"],
        "Dependency atlas",
    ),
    "dashboard": RouteTarget(
        "dashboard",
        "/",
        "/api/health",
        "surface",
        "dashboard",
        ["home", "gui"],
        "Classic dashboard (still available)",
    ),
    "ai_inhouse": RouteTarget(
        "ai_inhouse",
        "/api/ai/inhouse/status",
        "/api/ai/inhouse/chat",
        "api",
        "pseudo-inhouse-ai",
        ["inhouse-ai", "openai-proxy", "v1-chat"],
        "Pseudo-inhouse AI facade (freemium=false)",
    ),
    "creative_inhouse": RouteTarget(
        "creative_inhouse",
        "/api/creative/inhouse/status",
        "/api/creative/inhouse/create",
        "api",
        "pseudo-inhouse-creative",
        ["creative", "image-gen", "video-gen", "pdf-gen", "graphics"],
        "Pseudo-inhouse creative facade (image/video/PDF/graphics)",
    ),
    "dual_timeline": RouteTarget(
        "dual_timeline",
        "/api/training/dual-timeline/status",
        "/api/training/dual-timeline/run",
        "api",
        "dual-timeline-training",
        [
            "auto-train",
            "imaginary-time",
            "zeitstrahl",
            "tau",
            "virtual-timeline",
            "virtuelle timeline",
            "heroic timeline",
        ],
        "Auto-training dual+virtual timeline t ∥ τ ∥ v (heroic SHU)",
    ),
    "quantize_selfmod": RouteTarget(
        "quantize_selfmod",
        "/api/mesh/ops/quantize-selfmod",
        "/api/mesh/ops/quantize-selfmod/cycle",
        "api",
        "tailscale-quantize-selfmod",
        [
            "tailscale quantize",
            "quantisierung",
            "selbstmodulierend",
            "quantize selfmod",
            "mesh quantize",
            "bit depth",
        ],
        "Tailscale assist nodes self-modulating calculation quantization",
    ),
    "daycycle": RouteTarget(
        "daycycle",
        None,
        None,
        "cli",
        "daycycle-mem-v12.1",
        [
            "daycycle",
            "mem.md",
            "minutentakt",
            "zentralkonsolidierung",
            "testtest",
        ],
        "Minute mem · hourly private dev · 4h PR · daily top + fanout (v12.1)",
    ),
}


# Legacy paths → new interconnect surfaces
LEGACY_REDIRECTS: Dict[str, str] = {
    "/grok": "/mainframe/grok",
    "/grok/status": "/api/grok/status",
    "/grok/chat": "/api/grok/chat",
    "/vr/persistent": "/mainframe/vr",
    "/ide": "/mainframe/ide",
    "/worktree": "/mainframe/worktree",
    "/portal": "/mainframe",
    "/mainframe/website": "/mainframe",
    "/interconnect": "/mainframe/grok",
    "/api/interconnect": "/api/grok/interconnect",
}


def resolve(intent_or_alias: str) -> Optional[RouteTarget]:
    key = (intent_or_alias or "").strip().lower().replace("-", "_").replace(" ", "_")
    if key in ROUTE_TABLE:
        return ROUTE_TABLE[key]
    for rt in ROUTE_TABLE.values():
        for a in rt.aliases:
            al = a.lower().replace("-", "_").replace(" ", "_")
            if al == key or key in al or al in key:
                return rt
    return None


def route_message(message: str, intents: Optional[List[str]] = None) -> Dict[str, Any]:
    """Map message intents to ordered route targets (re-route plan)."""
    intents = list(intents or [])
    routes: List[Dict[str, Any]] = []
    seen = set()
    for intent in intents:
        rt = resolve(intent)
        if rt and rt.intent not in seen:
            seen.add(rt.intent)
            routes.append(rt.to_dict())
    # default: if no intents, send to interconnect + chat
    if not routes:
        for fallback in ("interconnect", "chat"):
            rt = ROUTE_TABLE[fallback]
            routes.append(rt.to_dict())
    primary = routes[0] if routes else ROUTE_TABLE["interconnect"].to_dict()
    return {
        "ok": True,
        "primary": primary,
        "routes": routes,
        "redirect_hint": primary.get("surface"),
        "api_hint": primary.get("api"),
        "legacy_redirects": LEGACY_REDIRECTS,
    }


def all_routes() -> Dict[str, Any]:
    return {
        "table": {k: v.to_dict() for k, v in ROUTE_TABLE.items()},
        "legacy_redirects": LEGACY_REDIRECTS,
        "entrypoints": {
            "control_plane": "/mainframe/grok",
            "hub": "/mainframe",
            "chat_api": "/api/grok/chat",
            "interconnect_api": "/api/grok/interconnect",
            "route_api": "/api/grok/route",
        },
    }
