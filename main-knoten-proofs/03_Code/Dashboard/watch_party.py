# -*- coding: utf-8 -*-
"""Watch Together — synchronisierte YouTube-Räume für PC + Handy."""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Set

_YT_PATTERNS = (
    re.compile(r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})"),
    re.compile(r"^([A-Za-z0-9_-]{11})$"),
)


@dataclass
class WatchRoom:
    room_id: str
    video_id: str
    position: float = 0.0
    playing: bool = False
    updated_at: float = field(default_factory=time.time)
    title: str = ""
    created_at: float = field(default_factory=time.time)
    revision: int = 0
    controller_id: str = ""

    def current_position(self, now: Optional[float] = None) -> float:
        now = now or time.time()
        if self.playing:
            return self.position + max(0.0, now - self.updated_at)
        return self.position

    def bump_revision(self, now: Optional[float] = None) -> float:
        """Monotone Zeit + Revisionszähler für konfliktfreien Multi-Device-Sync."""
        ts = now or time.time()
        if ts <= self.updated_at:
            ts = self.updated_at + 0.001
        self.updated_at = ts
        self.revision += 1
        return ts

    def to_state(self) -> Dict[str, Any]:
        now = time.time()
        return {
            "type": "watch_state",
            "room_id": self.room_id,
            "video_id": self.video_id,
            "position": round(self.current_position(now), 2),
            "playing": self.playing,
            "server_time": now,
            "updated_at": self.updated_at,
            "revision": self.revision,
            "controller_id": self.controller_id,
            "title": self.title,
            "sync_authority": "server",
        }


class WatchPartyManager:
    def __init__(self) -> None:
        self._rooms: Dict[str, WatchRoom] = {}
        self._subscribers: Dict[str, Set[Any]] = {}
        self._hydrated = False

    def _room_row(self, room: WatchRoom) -> Dict[str, Any]:
        return {
            "room_id": room.room_id,
            "video_id": room.video_id,
            "position": room.position,
            "playing": room.playing,
            "title": room.title,
            "updated_at": room.updated_at,
            "created_at": room.created_at,
        }

    def _persist_room(self, room: WatchRoom) -> None:
        try:
            from watch_sync_server import push_room_to_server, server_sync_enabled

            if server_sync_enabled():
                push_room_to_server(room)
                return
            import supabase_store as store

            if store.cloud_sync_enabled():
                store.save_watch_room(self._room_row(room))
        except Exception:
            pass

    def _finalize_command(self, room: WatchRoom) -> WatchRoom:
        try:
            from watch_sync_server import finalize_command

            return finalize_command(self, room)
        except Exception:
            self._persist_room(room)
            return room

    def hydrate_from_cloud(self) -> int:
        if self._hydrated:
            return 0
        self._hydrated = True
        try:
            import supabase_store as store

            rows = store.load_watch_rooms()
        except Exception:
            return 0
        loaded = 0
        for row in rows:
            rid = row.get("room_id")
            if not rid or rid in self._rooms:
                continue
            payload = row.get("payload") or {}
            self._rooms[rid] = WatchRoom(
                room_id=rid,
                video_id=row.get("video_id") or "",
                position=float(row.get("position") or 0),
                playing=bool(row.get("playing")),
                updated_at=float(row.get("updated_at") or time.time()),
                title=row.get("title") or "",
                created_at=float(row.get("created_at") or time.time()),
                revision=int(payload.get("revision") or 0),
                controller_id=str(payload.get("controller_id") or ""),
            )
            self._subscribers.setdefault(rid, set())
            loaded += 1
        return loaded

    @staticmethod
    def extract_video_id(url_or_id: str) -> Optional[str]:
        text = (url_or_id or "").strip()
        if not text:
            return None
        for pat in _YT_PATTERNS:
            m = pat.search(text)
            if m:
                return m.group(1)
        return None

    def create_room(self, url_or_id: str = "") -> WatchRoom:
        room_id = uuid.uuid4().hex[:8]
        video_id = self.extract_video_id(url_or_id) or ""
        room = WatchRoom(room_id=room_id, video_id=video_id)
        self._rooms[room_id] = room
        self._subscribers.setdefault(room_id, set())
        self._persist_room(room)
        return room

    def get_room(self, room_id: str) -> Optional[WatchRoom]:
        return self._rooms.get(room_id)

    def ensure_room(self, room_id: str) -> WatchRoom:
        room = self._rooms.get(room_id)
        if room is None:
            room = WatchRoom(room_id=room_id, video_id="")
            self._rooms[room_id] = room
            self._subscribers.setdefault(room_id, set())
            self._persist_room(room)
        return room

    def register_ws(self, room_id: str, ws: Any) -> None:
        self._subscribers.setdefault(room_id, set()).add(ws)

    def unregister_ws(self, room_id: str, ws: Any) -> None:
        subs = self._subscribers.get(room_id)
        if subs:
            subs.discard(ws)

    def subscribers(self, room_id: str) -> Set[Any]:
        return set(self._subscribers.get(room_id, set()))

    def _ensure_controller(self, room: WatchRoom, device_id: Optional[str]) -> bool:
        """Nur ein Gerät darf Befehle senden — erstes Controller-Gerät bleibt Master."""
        if not device_id:
            return True
        if room.controller_id and room.controller_id != device_id:
            return False
        if not room.controller_id:
            room.controller_id = device_id
        return True

    def apply_command(
        self,
        room_id: str,
        cmd: str,
        *,
        video_id: Optional[str] = None,
        position: Optional[float] = None,
        playing: Optional[bool] = None,
        device_id: Optional[str] = None,
    ) -> Optional[WatchRoom]:
        room = self.ensure_room(room_id)
        now = time.time()

        if cmd == "claim_controller":
            if not device_id:
                return None
            room.controller_id = device_id
            room.bump_revision(now)
            return self._finalize_command(room)

        if cmd in ("load", "seek", "play", "pause"):
            if not self._ensure_controller(room, device_id):
                return None

        if cmd == "load":
            vid = self.extract_video_id(video_id or "") if video_id else None
            if not vid:
                return None
            room.video_id = vid
            room.position = 0.0
            room.playing = False
            room.bump_revision(now)
            return self._finalize_command(room)

        if cmd == "seek":
            if position is None:
                return None
            room.position = max(0.0, float(position))
            if playing is not None:
                room.playing = bool(playing)
            room.bump_revision(now)
            return self._finalize_command(room)

        if cmd == "play":
            room.position = room.current_position(now) if position is None else max(0.0, float(position))
            room.playing = True
            room.bump_revision(now)
            return self._finalize_command(room)

        if cmd == "pause":
            room.position = room.current_position(now) if position is None else max(0.0, float(position))
            room.playing = False
            room.bump_revision(now)
            return self._finalize_command(room)

        return None

    def room_info(self, room_id: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        room = self.get_room(room_id)
        if not room:
            return {"ok": False, "error": "room_not_found"}
        lan = base_url or local_network_base()
        join = join_url_for_room(room.room_id, lan)
        return {
            "ok": True,
            "room_id": room.room_id,
            "video_id": room.video_id,
            "watch_url": join,
            "join_url": join,
            "lan_base": lan,
            "local_url": f"http://127.0.0.1:8000/watch/{room.room_id}",
            "ws_url": f"/ws/watch/{room.room_id}",
            "qr_url": f"/api/watch/room/{room.room_id}/qr",
            "state": room.to_state(),
            "viewers": len(self.subscribers(room_id)),
            "server_sync": _server_sync_flag(),
        }


def _server_sync_flag() -> bool:
    try:
        from watch_sync_server import server_sync_enabled

        return server_sync_enabled()
    except Exception:
        return False


_manager: Optional[WatchPartyManager] = None


def get_watch_manager() -> WatchPartyManager:
    global _manager
    if _manager is None:
        _manager = WatchPartyManager()
        _manager.hydrate_from_cloud()
    return _manager


def local_network_base(port: Optional[int] = None) -> str:
    """Basis-URL für Handy im WLAN (bevorzugt 192.168.x, nicht Docker/WSL)."""
    from connectivity import local_network_base as _lan_base

    return _lan_base(port)


def join_url_for_room(
    room_id: str,
    base_url: Optional[str] = None,
    port: int = 8000,
    *,
    follower: bool = False,
) -> str:
    base = (base_url or local_network_base(port)).rstrip("/")
    url = f"{base}/watch/{room_id}"
    return f"{url}?follower=1" if follower else url


def render_watch_page(
    room_id: str,
    video_id: str = "",
    template_path: Optional[Any] = None,
    lan_base: Optional[str] = None,
    *,
    role: str = "controller",
) -> str:
    import json
    from pathlib import Path

    path = template_path or Path(__file__).parent / "templates" / "watch.html"
    html = path.read_text(encoding="utf-8")
    base = lan_base or local_network_base()
    html = html.replace("{{ room_id|tojson }}", json.dumps(room_id))
    html = html.replace("{{ video_id|tojson }}", json.dumps(video_id))
    html = html.replace("{{ lan_base|tojson }}", json.dumps(base))
    html = html.replace("{{ watch_server_sync|tojson }}", json.dumps(_server_sync_flag()))
    try:
        from watch_sync_server import get_realtime_client_config, server_poll_interval_sec

        poll_ms = int(server_poll_interval_sec() * 1000)
        rt_cfg = get_realtime_client_config()
    except Exception:
        poll_ms = 2000
        rt_cfg = {"enabled": False}
    html = html.replace("{{ watch_poll_ms|tojson }}", json.dumps(poll_ms))
    html = html.replace("{{ watch_realtime_config|tojson }}", json.dumps(rt_cfg))
    html = html.replace("{{ watch_role|tojson }}", json.dumps(role))
    return html


async def broadcast_room_state(manager: WatchPartyManager, room_id: str) -> None:
    room = manager.get_room(room_id)
    if not room:
        return
    state = room.to_state()
    meta = {"type": "watch_meta", "viewers": len(manager.subscribers(room_id))}
    dead = []
    for ws in manager.subscribers(room_id):
        try:
            await ws.send_json(state)
            await ws.send_json(meta)
        except Exception:
            dead.append(ws)
    for ws in dead:
        manager.unregister_ws(room_id, ws)