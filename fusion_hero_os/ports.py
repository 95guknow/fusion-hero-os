"""Canonical port base for Fusion Hero OS / Poly-Mesh (worktree port/42069).

Everything public-facing and dashboard-related defaults to **42069** unless
overridden by environment variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Sacred / ops base — do not change lightly
PORT_BASE = 42069


@dataclass(frozen=True)
class PortMap:
    """Resolved runtime ports."""

    base: int = PORT_BASE
    dashboard: int = PORT_BASE
    funnel_target: int = PORT_BASE
    static_site: int = PORT_BASE
    ipc_bridge: int = 19753  # keep IPC off the HTTP base

    @property
    def dashboard_url_local(self) -> str:
        return f"http://127.0.0.1:{self.dashboard}"

    @property
    def mesh_ops_url(self) -> str:
        return f"{self.dashboard_url_local}/api/mesh/ops"


def get_ports() -> PortMap:
    base = _env_int("FUSION_PORT_BASE", PORT_BASE)
    dash = _env_int("FUSION_BACKEND_PORT", base)
    funnel = _env_int("FUSION_FUNNEL_PORT", dash)
    static = _env_int("FUSION_STATIC_PORT", dash)
    ipc = _env_int("FUSION_IPC_PORT", 19753)
    return PortMap(
        base=base,
        dashboard=dash,
        funnel_target=funnel,
        static_site=static,
        ipc_bridge=ipc,
    )
