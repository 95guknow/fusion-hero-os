"""Read-only Zugriff auf Microsoft Phone Link lokale SQLite-Speicher.

Microsoft bietet keine öffentliche API. Dieses Modul liest nur die lokal
gespiegelten Daten (SMS, Konversationen, Benachrichtigungen) und prüft
Prozess-Status — keine UI-Automation, kein Schreibzugriff.

Hinweis: Schema/Pfade können sich mit Phone-Link-Updates ändern.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_PHONE_LINK_PKG = "Microsoft.YourPhone_8wekyb3d8bbwe"
_WIN_EPOCH_OFFSET = 116444736000000000  # 100-ns ticks between 1601-01-01 and 1970-01-01


@dataclass
class PhoneLinkSnapshot:
    connected: bool
    host_running: bool
    database_found: bool
    database_path: Optional[str]
    conversation_count: int
    message_count: int
    unread_total: int
    notification_count: int
    recent_messages: List[Dict[str, Any]]
    recent_conversations: List[Dict[str, Any]]
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _package_root() -> Path:
    local = os.environ.get("LOCALAPPDATA", "")
    return Path(local) / "Packages" / _PHONE_LINK_PKG


def _discover_database(name: str = "phone.db") -> Optional[Path]:
    indexed = _package_root() / "LocalCache" / "Indexed"
    if not indexed.is_dir():
        return None
    candidates = sorted(
        indexed.glob(f"*/System/Database/{name}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _filetime_to_iso(ticks: Optional[int]) -> Optional[str]:
    if not ticks:
        return None
    try:
        unix = (int(ticks) - _WIN_EPOCH_OFFSET) / 10_000_000
        return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _mask_address(addr: str) -> str:
    if not addr or len(addr) <= 4:
        return addr or ""
    if addr.startswith("+"):
        return f"+{'*' * max(0, len(addr) - 5)}{addr[-4:]}"
    if addr.isdigit() and len(addr) > 4:
        return f"{'*' * (len(addr) - 4)}{addr[-4:]}"
    return addr


def _is_host_running() -> bool:
    try:
        import psutil

        for proc in psutil.process_iter(["name"]):
            name = (proc.info.get("name") or "").lower()
            if name in ("phoneexperiencehost.exe", "yourphoneappproxy.exe"):
                return True
    except Exception:
        pass
    try:
        import subprocess

        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq PhoneExperienceHost.exe"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        return "PhoneExperienceHost.exe" in out
    except Exception:
        return False


class PhoneLinkReader:
    """Liest gespiegelte Phone-Link-Daten (read-only)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _discover_database("phone.db")
        self._notifications_path = _discover_database("notifications.db")

    @property
    def database_path(self) -> Optional[Path]:
        return self._db_path

    def _query(self, path: Path, sql: str, params: tuple = ()) -> List[tuple]:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return list(cur.fetchall())
        finally:
            conn.close()

    def recent_conversations(self, limit: int = 8) -> List[Dict[str, Any]]:
        if not self._db_path:
            return []
        rows = self._query(
            self._db_path,
            "SELECT thread_id, recipient_list, msg_count, unread_count, timestamp "
            "FROM conversation ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "thread_id": r[0],
                "recipient": r[1],
                "recipient_masked": _mask_address(str(r[1] or "")),
                "msg_count": r[2],
                "unread_count": r[3],
                "timestamp": _filetime_to_iso(r[4]),
            }
            for r in rows
        ]

    def recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self._db_path:
            return []
        rows = self._query(
            self._db_path,
            "SELECT from_address, body, timestamp, thread_id "
            "FROM message ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "from": r[0],
                "from_masked": _mask_address(str(r[0] or "")),
                "body_preview": (r[1] or "")[:120],
                "timestamp": _filetime_to_iso(r[2]),
                "thread_id": r[3],
            }
            for r in rows
        ]

    def counts(self) -> Dict[str, int]:
        if not self._db_path:
            return {
                "conversations": 0,
                "messages": 0,
                "unread_total": 0,
                "notifications": 0,
            }
        conv = self._query(self._db_path, "SELECT COUNT(*), COALESCE(SUM(unread_count),0) FROM conversation")[0]
        msg = self._query(self._db_path, "SELECT COUNT(*) FROM message")[0]
        notif = 0
        if self._notifications_path:
            try:
                notif = self._query(self._notifications_path, "SELECT COUNT(*) FROM notifications")[0][0]
            except sqlite3.Error:
                notif = 0
        return {
            "conversations": int(conv[0]),
            "messages": int(msg[0]),
            "unread_total": int(conv[1]),
            "notifications": int(notif),
        }

    def snapshot(self) -> PhoneLinkSnapshot:
        host = _is_host_running()
        counts = self.counts()
        db_found = self._db_path is not None and self._db_path.exists()
        connected = host and db_found and counts["messages"] > 0
        limitations = [
            "Keine offizielle Microsoft-API — nur lokale SQLite-Spiegel.",
            "Benachrichtigungen oft leer (Phone Link cached sie nicht lokal).",
            "SMS-Versand erfordert UI-Automation (nicht in diesem Modul).",
            "Schema kann sich mit Phone-Link-Updates ändern.",
        ]
        return PhoneLinkSnapshot(
            connected=connected,
            host_running=host,
            database_found=db_found,
            database_path=str(self._db_path) if self._db_path else None,
            conversation_count=counts["conversations"],
            message_count=counts["messages"],
            unread_total=counts["unread_total"],
            notification_count=counts["notifications"],
            recent_messages=self.recent_messages(),
            recent_conversations=self.recent_conversations(),
            limitations=limitations,
        )


def phone_link_status() -> Dict[str, Any]:
    """Kurzstatus für Dashboard / Bridge."""
    return PhoneLinkReader().snapshot().to_dict()