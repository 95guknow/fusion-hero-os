# -*- coding: utf-8 -*-
"""Geräte-Discovery und Access-Point-Übersicht für Fusion Hero OS."""

from __future__ import annotations

import os
import socket
import time
from typing import Any, Dict, List, Optional, Tuple


def dashboard_port() -> int:
    raw = os.getenv("FUSION_DASHBOARD_PORT") or os.getenv("PORT") or "8000"
    try:
        return int(raw)
    except ValueError:
        return 8000


def _score_ip(ip: str) -> int:
    if ip.startswith("127."):
        return 100
    if ip.startswith("169.254."):
        return 90
    if ip.startswith("192.168."):
        return 10
    if ip.startswith("10."):
        return 20
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) == 4:
            try:
                second = int(parts[1])
                if 16 <= second <= 31:
                    return 80
            except ValueError:
                pass
        return 30
    return 50


def list_lan_ips() -> List[str]:
    ips: List[str] = []
    try:
        import psutil

        for _name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address:
                    ips.append(addr.address)
    except Exception:
        pass
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ips.append(sock.getsockname()[0])
        sock.close()
    except Exception:
        pass
    unique = list(dict.fromkeys(ips))
    unique.sort(key=_score_ip)
    return unique


def best_lan_ip() -> str:
    override = os.getenv("FUSION_LAN_IP", "").strip()
    if override:
        return override
    ips = list_lan_ips()
    return ips[0] if ips else "127.0.0.1"


def local_network_base(port: Optional[int] = None) -> str:
    override = os.getenv("FUSION_LAN_BASE_OVERRIDE", "").strip().rstrip("/")
    if override:
        return override
    p = dashboard_port() if port is None else port
    return f"http://{best_lan_ip()}:{p}"


def _device_id() -> str:
    try:
        import supabase_store as store

        return store.device_id()
    except Exception:
        return os.getenv("FUSION_DEVICE_ID") or socket.gethostname()


def build_discovery() -> Dict[str, Any]:
    port = dashboard_port()
    lan = best_lan_ip()
    base = local_network_base(port)
    host = socket.gethostname()
    return {
        "ok": True,
        "device_id": _device_id(),
        "hostname": host,
        "port": port,
        "lan_ip": lan,
        "lan_ips": list_lan_ips(),
        "local_url": f"http://127.0.0.1:{port}",
        "lan_base": base,
        "watch_url": f"{base}/watch",
        "dashboard_url": f"{base}/",
        "ws_url": f"ws://{lan}:{port}/ws",
        "watch_ws_pattern": f"ws://{lan}:{port}/ws/watch/{{room_id}}",
        "endpoints": {
            "health": f"{base}/api/health",
            "discovery": f"{base}/api/discovery",
            "connectivity": f"{base}/api/connectivity",
            "watch_network": f"{base}/api/watch/network",
            "supabase_sync": f"{base}/api/supabase/sync/status",
            "bridge_ipc": f"{base}/api/bridge/ipc/status",
            "phone_link": f"{base}/api/phone-link/status",
            "settings": f"{base}/api/settings",
        },
        "hint": "Handy im gleichen WLAN — QR auf /watch scannen",
    }


def build_connectivity_summary() -> Dict[str, Any]:
    """Aggregiert Status aller Access Points (sync, ohne blockierende Probes)."""
    port = dashboard_port()
    base = local_network_base(port)
    out: Dict[str, Any] = {
        "ok": True,
        "ts": time.time(),
        "discovery": {
            "lan_ip": best_lan_ip(),
            "lan_base": base,
            "device_id": _device_id(),
            "port": port,
        },
        "access_points": {},
    }

    try:
        import supabase_store as store

        out["access_points"]["supabase"] = {
            "ok": store.cloud_sync_enabled(),
            **store.sync_status(),
        }
    except Exception as exc:
        out["access_points"]["supabase"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from fusion_hero_os.integrations.phone_link import phone_link_status

        pl = phone_link_status()
        out["access_points"]["phone_link"] = {
            "ok": pl.get("connected") is True,
            "host_running": pl.get("host_running"),
            "message_count": pl.get("message_count", 0),
        }
    except Exception as exc:
        out["access_points"]["phone_link"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from core.v8_core_bridge import ipc_status

        ipc = ipc_status()
        out["access_points"]["ipc_bridge"] = {
            "ok": ipc.get("ok", False),
            "transport": ipc.get("transport"),
            "module_count": len(ipc.get("modules") or []),
        }
    except Exception as exc:
        out["access_points"]["ipc_bridge"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from watch_party import get_watch_manager

        mgr = get_watch_manager()
        out["access_points"]["watch_together"] = {
            "ok": True,
            "rooms": len(mgr._rooms),
            "join_url": f"{base}/watch",
        }
    except Exception as exc:
        out["access_points"]["watch_together"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from app import TASK_QUEUE, JOBS

        out["access_points"]["jobs"] = {
            "ok": True,
            "queue_len": len(TASK_QUEUE),
            "jobs_len": len(JOBS),
        }
    except Exception:
        out["access_points"]["jobs"] = {"ok": True, "queue_len": 0, "jobs_len": 0}

    ap_ok = [v.get("ok") for v in out["access_points"].values() if isinstance(v, dict)]
    out["all_ok"] = all(ap_ok) if ap_ok else False
    return out