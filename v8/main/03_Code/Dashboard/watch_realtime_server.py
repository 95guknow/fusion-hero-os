# -*- coding: utf-8 -*-
"""Supabase Realtime Listener — Server-seitig WS-Broadcast bei watch_rooms Änderungen."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

_running = False
_channel: Any = None


async def watch_realtime_listener() -> None:
    """Abonniert Postgres-Änderungen an watch_rooms und broadcastet an WS-Clients."""
    global _running, _channel
    if _running:
        return

    from watch_sync_server import apply_realtime_payload, realtime_enabled

    if not realtime_enabled():
        return

    from supabase_client import SUPABASE_KEY, SUPABASE_URL, is_configured

    if not is_configured():
        return

    try:
        from supabase import create_async_client
    except Exception as exc:
        print(f"[Watch Realtime] async client unavailable: {exc}")
        return

    loop = asyncio.get_running_loop()

    async def handle_change(payload: Any) -> None:
        try:
            from watch_party import broadcast_room_state, get_watch_manager

            mgr = get_watch_manager()
            room_id = apply_realtime_payload(mgr, payload)
            if room_id:
                await broadcast_room_state(mgr, room_id)
        except Exception:
            pass

    def on_change(payload: Any) -> None:
        asyncio.run_coroutine_threadsafe(handle_change(payload), loop)

    try:
        client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
        _channel = client.channel("fusion-watch-rooms-server")
        _channel.on_postgres_changes(
            event="*",
            schema="public",
            table="watch_rooms",
            callback=on_change,
        )
        await _channel.subscribe()
        _running = True
        print("[Watch Realtime] Server-Listener aktiv (watch_rooms)")
        while True:
            await asyncio.sleep(3600)
    except Exception as exc:
        _running = False
        print(f"[Watch Realtime] Server-Listener Fehler: {exc}")


def start_watch_realtime_task() -> dict:
    global _running
    if _running:
        return {"started": False, "reason": "already_running"}
    if os.getenv("FUSION_WATCH_REALTIME", "1") != "1":
        return {"started": False, "reason": "FUSION_WATCH_REALTIME=0"}
    try:
        from watch_sync_server import realtime_enabled

        if not realtime_enabled():
            return {"started": False, "reason": "server_sync_disabled"}
    except Exception:
        return {"started": False, "reason": "watch_sync_unavailable"}
    asyncio.create_task(watch_realtime_listener())
    return {"started": True, "mode": "realtime"}