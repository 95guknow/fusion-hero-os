# -*- coding: utf-8 -*-
"""Hintergrund-Sync: Auto-Metriken + Phone-Link-Snapshots → Supabase."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable, Dict, Optional

_running = False


def _sync_enabled() -> bool:
    return os.getenv("FUSION_SUPABASE_SYNC", "1") == "1"


async def metrics_loop(get_metrics: Callable[[], Awaitable[Any]], interval_sec: float) -> None:
    import supabase_store as store

    while True:
        await asyncio.sleep(max(5.0, interval_sec))
        if not _sync_enabled():
            continue
        try:
            metrics = await get_metrics()
            if hasattr(metrics, "model_dump"):
                payload = metrics.model_dump()
            elif isinstance(metrics, dict):
                payload = metrics
            else:
                payload = dict(metrics)
            await asyncio.to_thread(store.save_metrics, payload)
        except Exception:
            pass


async def phone_link_snapshot_loop(interval_sec: float) -> None:
    import supabase_store as store

    while True:
        await asyncio.sleep(max(30.0, interval_sec))
        if not _sync_enabled() or not store.cloud_sync_enabled():
            continue
        try:
            from fusion_hero_os.integrations.phone_link import phone_link_status

            snap = await asyncio.to_thread(phone_link_status)
            if isinstance(snap, dict):
                await asyncio.to_thread(store.save_phone_link_snapshot, snap)
        except Exception:
            pass


async def watch_server_sync_loop(interval_sec: float) -> None:
    """Pollt Supabase und synchronisiert aktive Watch-Räume an alle WS-Clients."""
    while True:
        await asyncio.sleep(max(1.0, interval_sec))
        try:
            from watch_sync_server import active_room_ids, refresh_room_from_server, server_sync_enabled
            from watch_party import broadcast_room_state, get_watch_manager

            if not server_sync_enabled():
                continue
            mgr = get_watch_manager()
            changed: list[str] = []
            for rid in active_room_ids(mgr):
                before = mgr.get_room(rid)
                before_ts = before.updated_at if before else 0.0
                refresh_room_from_server(mgr, rid)
                after = mgr.get_room(rid)
                if after and after.updated_at > before_ts + 0.001:
                    changed.append(rid)
            for rid in changed:
                await broadcast_room_state(mgr, rid)
        except Exception:
            pass


def start_background_tasks(
    get_metrics: Callable[[], Awaitable[Any]],
    *,
    metrics_interval: Optional[float] = None,
    phone_link_interval: Optional[float] = None,
    watch_sync_interval: Optional[float] = None,
) -> Dict[str, Any]:
    global _running
    if _running:
        return {"started": False, "reason": "already_running"}
    if not _sync_enabled():
        return {"started": False, "reason": "FUSION_SUPABASE_SYNC=0"}

    m_int = metrics_interval or float(os.getenv("FUSION_SUPABASE_METRICS_INTERVAL_SEC", "30"))
    p_int = phone_link_interval or float(os.getenv("FUSION_PHONE_LINK_SNAPSHOT_INTERVAL_SEC", "300"))
    w_int = watch_sync_interval
    if w_int is None:
        try:
            from watch_sync_server import active_poll_interval_sec

            w_int = active_poll_interval_sec()
        except Exception:
            w_int = float(os.getenv("FUSION_WATCH_ACTIVE_POLL_SEC", "2"))

    asyncio.create_task(metrics_loop(get_metrics, m_int))
    asyncio.create_task(phone_link_snapshot_loop(p_int))
    watch_mode = "poll"
    try:
        from watch_sync_server import poll_fallback_only, server_sync_enabled

        if server_sync_enabled():
            try:
                from watch_realtime_server import start_watch_realtime_task

                rt = start_watch_realtime_task()
                if rt.get("started"):
                    watch_mode = "realtime"
            except Exception:
                pass
            if poll_fallback_only() and watch_mode == "realtime":
                asyncio.create_task(watch_server_sync_loop(w_int))
            elif watch_mode == "poll":
                asyncio.create_task(watch_server_sync_loop(w_int))
    except Exception:
        pass
    _running = True
    return {
        "started": True,
        "metrics_interval_sec": m_int,
        "phone_link_interval_sec": p_int,
        "watch_sync_interval_sec": w_int,
        "watch_sync_mode": watch_mode,
    }