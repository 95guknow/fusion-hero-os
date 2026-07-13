# -*- coding: utf-8 -*-
"""Watch Together — Supabase als autoritativer Sync-Server.

Alle Geräte (PC, Redmi, zweiter PC) lesen/schreiben den Raumzustand über
Supabase. Lokaler Speicher ist nur Cache; Konflikte gewinnt der Server-Stand.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from watch_party import WatchPartyManager, WatchRoom


def server_sync_enabled() -> bool:
    if os.getenv("FUSION_WATCH_SERVER_SYNC", "1") != "1":
        return False
    try:
        import supabase_store as store

        return store.cloud_sync_enabled()
    except Exception:
        return False


def realtime_enabled() -> bool:
    return server_sync_enabled() and os.getenv("FUSION_WATCH_REALTIME", "1") == "1"


def server_poll_interval_sec() -> float:
    """Poll-Intervall: Fallback wenn Realtime aus oder als Backup."""
    if realtime_enabled():
        try:
            return float(os.getenv("FUSION_WATCH_POLL_FALLBACK_SEC", "3"))
        except ValueError:
            return 3.0
    try:
        return float(os.getenv("FUSION_WATCH_SERVER_POLL_SEC", "2"))
    except ValueError:
        return 2.0


def active_poll_interval_sec() -> float:
    """Server-Broadcast-Schleife für aktive Räume (immer schnell genug für Sync)."""
    try:
        return float(os.getenv("FUSION_WATCH_ACTIVE_POLL_SEC", "2"))
    except ValueError:
        return 2.0


def poll_fallback_only() -> bool:
    return realtime_enabled()


def get_realtime_client_config() -> Dict[str, Any]:
    from supabase_client import SUPABASE_KEY, SUPABASE_URL, is_configured

    return {
        "enabled": realtime_enabled() and is_configured(),
        "url": SUPABASE_URL or "",
        "anon_key": SUPABASE_KEY or "",
        "table": "watch_rooms",
        "schema": "public",
    }


def extract_realtime_row(payload: Any) -> Optional[Dict[str, Any]]:
    if payload is None:
        return None
    if isinstance(payload, dict):
        row = payload.get("new") or payload.get("record")
        if row:
            return row
        data = payload.get("data")
        if isinstance(data, dict):
            return data.get("record") or data.get("new")
        return None
    for attr in ("new", "record"):
        if hasattr(payload, attr):
            val = getattr(payload, attr)
            if val:
                return dict(val) if not isinstance(val, dict) else val
    return None


def row_to_watch_state(row: Dict[str, Any]) -> Dict[str, Any]:
    now = time.time()
    position = float(row.get("position") or 0)
    updated_at = float(row.get("updated_at") or now)
    playing = bool(row.get("playing"))
    if playing:
        position += max(0.0, now - updated_at)
    payload = row.get("payload") or {}
    return {
        "type": "watch_state",
        "room_id": row.get("room_id", ""),
        "video_id": row.get("video_id") or "",
        "position": round(position, 2),
        "playing": playing,
        "server_time": now,
        "updated_at": updated_at,
        "revision": int(payload.get("revision") or row.get("revision") or 0),
        "controller_id": str(payload.get("controller_id") or ""),
        "title": row.get("title") or "",
        "sync_authority": "server",
        "sync_source": "realtime",
    }


def apply_realtime_payload(mgr: "WatchPartyManager", payload: Any) -> Optional[str]:
    row = extract_realtime_row(payload)
    if not row or not row.get("room_id"):
        return None
    room_id = str(row["room_id"])
    room = mgr.ensure_room(room_id)
    if merge_row_into_room(room, row):
        return room_id
    return None


def merge_row_into_room(room: "WatchRoom", row: Dict[str, Any]) -> bool:
    """Überschreibt lokalen Cache wenn Supabase neuer ist."""
    server_ts = float(row.get("updated_at") or 0)
    server_rev = int((row.get("payload") or {}).get("revision") or 0)
    local_rev = int(getattr(room, "revision", 0) or 0)
    if server_rev > 0 and local_rev > 0 and server_rev < local_rev:
        return False
    if server_rev <= local_rev and server_ts <= room.updated_at + 0.001:
        return False
    room.video_id = row.get("video_id") or ""
    room.position = float(row.get("position") or 0)
    room.playing = bool(row.get("playing"))
    room.updated_at = server_ts
    room.title = row.get("title") or ""
    if row.get("created_at"):
        room.created_at = float(row.get("created_at"))
    if server_rev > 0:
        room.revision = server_rev
    ctrl = (row.get("payload") or {}).get("controller_id")
    if ctrl:
        room.controller_id = str(ctrl)
    return True


def refresh_room_from_server(mgr: "WatchPartyManager", room_id: str) -> Optional["WatchRoom"]:
    if not server_sync_enabled():
        return mgr.get_room(room_id)
    try:
        import supabase_store as store

        row = store.load_watch_room(room_id)
    except Exception:
        return mgr.get_room(room_id)
    if not row:
        return mgr.get_room(room_id)
    room = mgr.ensure_room(room_id)
    merge_row_into_room(room, row)
    return room


def push_room_to_server(room: "WatchRoom") -> Dict[str, Any]:
    try:
        import supabase_store as store

        return store.save_watch_room(
            {
                "room_id": room.room_id,
                "video_id": room.video_id,
                "position": room.position,
                "playing": room.playing,
                "title": room.title,
                "updated_at": room.updated_at,
                "created_at": room.created_at,
                "payload": {
                    "sync_authority": "server",
                    "pushed_at": time.time(),
                    "revision": int(getattr(room, "revision", 0) or 0),
                    "controller_id": str(getattr(room, "controller_id", "") or ""),
                },
            }
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def low_latency_enabled() -> bool:
    return os.getenv("FUSION_WATCH_LOW_LATENCY", "1") == "1"


def finalize_command(mgr: "WatchPartyManager", room: "WatchRoom") -> "WatchRoom":
    """Nach lokaler Berechnung: Supabase synchron schreiben (Sync muss zuverlässig sein)."""
    if server_sync_enabled():
        push_room_to_server(room)
        if not low_latency_enabled():
            refreshed = refresh_room_from_server(mgr, room.room_id)
            return refreshed or room
        return room
    mgr._persist_room(room)
    return room


def state_response(room: "WatchRoom", *, sync_source: str = "memory") -> Dict[str, Any]:
    state = room.to_state()
    state["updated_at"] = room.updated_at
    state["sync_authority"] = "server" if server_sync_enabled() else "local"
    return {
        "ok": True,
        "state": state,
        "sync_source": sync_source,
        "server_sync": server_sync_enabled(),
        "low_latency": low_latency_enabled(),
    }


def get_authoritative_state(
    room_id: str,
    mgr: "WatchPartyManager",
    *,
    refresh: bool = True,
) -> Dict[str, Any]:
    if refresh and server_sync_enabled():
        refresh_room_from_server(mgr, room_id)
    room = mgr.get_room(room_id)
    if not room:
        return {"ok": False, "error": "room_not_found"}
    src = "supabase" if server_sync_enabled() and refresh else "memory"
    return state_response(room, sync_source=src)


def active_room_ids(mgr: "WatchPartyManager") -> list[str]:
    ids = set(mgr._rooms.keys())
    for rid, subs in mgr._subscribers.items():
        if subs:
            ids.add(rid)
    return list(ids)