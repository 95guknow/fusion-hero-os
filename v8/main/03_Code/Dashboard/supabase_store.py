# -*- coding: utf-8 -*-
"""Persistenz-Layer: Fusion Hero OS → Supabase (swmmoxhdzarmoupyssqe)."""
from __future__ import annotations

import os
import socket
import time
from typing import Any, Dict, List, Optional

from supabase_client import get_client, is_configured

# --- Tables-Ready-Gate -------------------------------------------------------
# Ohne angewendetes Schema (supabase/schema.sql) existieren die Ziel-Tabellen
# nicht -> jeder Insert wäre ein fehlschlagender Netzwerk-Aufruf. Da emit() bei
# jedem Event einen save_event() feuert, würde das Supabase dauerhaft mit
# aussichtslosen Requests fluten. Deshalb wird die Existenz EINMAL geprüft und
# gecacht; solange die Tabellen fehlen, werden Inserts lokal übersprungen.
# check_tables() aktualisiert den Cache — nach dem Anwenden des Schemas genügt
# ein Aufruf (z.B. GET /api/supabase/tables), um die Persistenz scharf zu schalten.
_TABLES_READY: Optional[bool] = None  # None = noch nicht geprüft


def _ensure_ready() -> bool:
    """Einmalige, gecachte Prüfung, ob die Ziel-Tabellen existieren."""
    global _TABLES_READY
    if _TABLES_READY is None:
        if not is_configured() or get_client() is None:
            _TABLES_READY = False
        else:
            _TABLES_READY = bool(check_tables().get("ok"))  # setzt Cache selbst
    return bool(_TABLES_READY)


def refresh_ready() -> bool:
    """Cache invalidieren und neu prüfen (z.B. nachdem das Schema angewendet wurde)."""
    global _TABLES_READY
    _TABLES_READY = None
    return _ensure_ready()


def cloud_sync_enabled() -> bool:
    return os.getenv("FUSION_SUPABASE_SYNC", "1") == "1" and os.getenv("FUSION_SUPABASE_CLOUD_SYNC", "1") == "1"


def device_id() -> str:
    return os.getenv("FUSION_DEVICE_ID", socket.gethostname() or "fusion-pc")


def _insert(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return {"ok": False, "error": "supabase client unavailable"}
    if not _ensure_ready():
        # Schema nicht angewendet -> nicht sinnlos gegen fehlende Tabellen schreiben
        return {"ok": False, "skipped": True, "table": table,
                "reason": "tables not ready (schema not applied)"}
    try:
        resp = client.table(table).insert(row).execute()
        return {"ok": True, "table": table, "count": len(resp.data or [])}
    except Exception as exc:
        return {"ok": False, "table": table, "error": str(exc)}


def _upsert(table: str, row: Dict[str, Any], on_conflict: str) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return {"ok": False, "error": "supabase client unavailable"}
    try:
        resp = client.table(table).upsert(row, on_conflict=on_conflict).execute()
        return {"ok": True, "table": table, "count": len(resp.data or [])}
    except Exception as exc:
        return {"ok": False, "table": table, "error": str(exc)}


def save_event(event: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "event_id": event.get("id"),
        "event_type": event.get("type", "info"),
        "message": event.get("msg", ""),
        "severity": event.get("severity"),
        "layer": event.get("layer"),
        "ts": event.get("ts", time.time()),
        "payload": {k: v for k, v in event.items() if k not in ("id", "type", "msg", "severity", "layer", "ts")},
    }
    return _insert("fusion_events", row)


def save_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "cpu_pct": metrics.get("cpu"),
        "ram_pct": metrics.get("ram"),
        "events_count": metrics.get("events"),
        "subs_count": metrics.get("subs"),
        "ops_per_sec": metrics.get("ops_per_sec"),
        "ts": metrics.get("ts", time.time()),
        "payload": metrics,
    }
    return _insert("fusion_metrics", row)


def save_job(job: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "job_id": job.get("id"),
        "query": job.get("query", ""),
        "category": job.get("category"),
        "dom": job.get("dom"),
        "status": job.get("status", "received"),
        "ts": time.time(),
        "payload": job,
    }
    return _insert("fusion_jobs", row)


def save_llama_config(config: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "algorithm": config.get("algorithm", "heroic_qubo_annealing_v1"),
        "model_path": config.get("model_path"),
        "generation": config.get("generation", {}),
        "metrics": config.get("metrics", {}),
        "ts": time.time(),
    }
    return _insert("heroic_llama_configs", row)


def list_recent_events(limit: int = 20) -> List[Dict[str, Any]]:
    client = get_client()
    if not client:
        return []
    try:
        resp = (
            client.table("fusion_events")
            .select("*")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


TARGET_TABLES = [
    "fusion_events",
    "fusion_metrics",
    "fusion_jobs",
    "heroic_llama_configs",
    "watch_rooms",
    "fusion_settings_cloud",
    "fusion_agent_audit",
    "phone_link_snapshots",
]


def save_watch_room(room: Dict[str, Any]) -> Dict[str, Any]:
    if not cloud_sync_enabled():
        return {"ok": False, "skipped": True}
    row = {
        "room_id": room["room_id"],
        "video_id": room.get("video_id", ""),
        "position": float(room.get("position", 0)),
        "playing": bool(room.get("playing", False)),
        "title": room.get("title", ""),
        "updated_at": float(room.get("updated_at", time.time())),
        "created_at": float(room.get("created_at", time.time())),
        "payload": room.get("payload", {}),
    }
    return _upsert("watch_rooms", row, on_conflict="room_id")


def load_watch_room(room_id: str) -> Optional[Dict[str, Any]]:
    """Einzelnen Watch-Raum von Supabase laden (Server-Quelle der Wahrheit)."""
    if not cloud_sync_enabled():
        return None
    client = get_client()
    if not client:
        return None
    try:
        resp = (
            client.table("watch_rooms")
            .select("*")
            .eq("room_id", room_id)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def load_watch_rooms(max_age_hours: float = 48.0, limit: int = 50) -> List[Dict[str, Any]]:
    if not cloud_sync_enabled():
        return []
    client = get_client()
    if not client:
        return []
    cutoff = time.time() - max_age_hours * 3600
    try:
        resp = (
            client.table("watch_rooms")
            .select("*")
            .gte("updated_at", cutoff)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def save_settings_cloud(values: Dict[str, Any], set_by: str = "api") -> Dict[str, Any]:
    if not cloud_sync_enabled():
        return {"ok": False, "skipped": True}
    row = {
        "device_id": device_id(),
        "env": values.get("env") or {},
        "ui": values.get("ui") or {},
        "updated_at": float(values.get("updated_at") or time.time()),
        "set_by": set_by,
    }
    return _upsert("fusion_settings_cloud", row, on_conflict="device_id")


def load_settings_cloud(target_device: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not cloud_sync_enabled():
        return None
    client = get_client()
    if not client:
        return None
    did = target_device or device_id()
    try:
        resp = client.table("fusion_settings_cloud").select("*").eq("device_id", did).limit(1).execute()
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def pull_settings_from_cloud(merge_if_newer: bool = True) -> Dict[str, Any]:
    """Lädt Cloud-Einstellungen für dieses Gerät (optional Merge in lokale Datei)."""
    cloud = load_settings_cloud()
    if not cloud:
        return {"ok": False, "reason": "no_cloud_row"}
    if not merge_if_newer:
        return {"ok": True, "cloud": cloud, "merged": False}
    try:
        from fusion_settings import SETTINGS_SCHEMA, _read_file, apply_settings

        local = _read_file()
        local_ts = float(local.get("updated_at") or 0)
        cloud_ts = float(cloud.get("updated_at") or 0)
        if cloud_ts <= local_ts:
            return {"ok": True, "merged": False, "reason": "local_newer"}
        schema_keys = {s["key"]: s for s in SETTINGS_SCHEMA}
        clean: Dict[str, Any] = {}
        for k, v in (cloud.get("env") or {}).items():
            if k in schema_keys:
                clean[k] = v
        for k, v in (cloud.get("ui") or {}).items():
            for candidate in (k, f"ui.{k}"):
                if candidate in schema_keys:
                    clean[candidate] = v
                    break
        if clean:
            apply_settings(clean, set_by="cloud_pull")
        return {"ok": True, "merged": bool(clean), "keys": list(clean.keys())}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def save_agent_audit(
    action: str,
    *,
    job_id: Optional[str] = None,
    agent: Optional[str] = None,
    dom: Optional[str] = None,
    category: Optional[str] = None,
    status: str = "ok",
    query: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not cloud_sync_enabled():
        return {"ok": False, "skipped": True}
    row = {
        "job_id": job_id,
        "action": action,
        "agent": agent,
        "dom": dom,
        "category": category,
        "status": status,
        "query": (query or "")[:2000] if query else None,
        "ts": time.time(),
        "payload": payload or {},
    }
    return _insert("fusion_agent_audit", row)


def save_phone_link_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if not cloud_sync_enabled():
        return {"ok": False, "skipped": True}
    row = {
        "connected": bool(snapshot.get("connected")),
        "host_running": bool(snapshot.get("host_running")),
        "conversation_count": int(snapshot.get("conversation_count") or 0),
        "message_count": int(snapshot.get("message_count") or 0),
        "unread_total": int(snapshot.get("unread_total") or 0),
        "notification_count": int(snapshot.get("notification_count") or 0),
        "ts": time.time(),
        "payload": {
            "database_found": snapshot.get("database_found"),
            "limitations": snapshot.get("limitations"),
            "recent_messages_count": len(snapshot.get("recent_messages") or []),
        },
    }
    return _insert("phone_link_snapshots", row)


def list_recent_agent_audit(limit: int = 20) -> List[Dict[str, Any]]:
    client = get_client()
    if not client:
        return []
    try:
        resp = (
            client.table("fusion_agent_audit")
            .select("*")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def store_status() -> Dict[str, Any]:
    """Konfigurations-Status (KEIN Netzwerk). tables = Ziel-Tabellen, NICHT als
    'existiert' zu verstehen — dafür check_tables() aufrufen."""
    return {
        "configured": is_configured(),
        "target_tables": TARGET_TABLES,
        "schema_sql": "supabase/schema.sql",
        "note": "Ziel-Tabellen; Existenz per check_tables() prüfen",
    }


def check_tables() -> Dict[str, Any]:
    """Read-only-Prüfung, welche Ziel-Tabellen im Projekt existieren.

    select().limit(1) pro Tabelle. PostgREST-Fehler PGRST205 => Tabelle fehlt
    (Schema noch nicht via supabase/schema.sql angewendet). Ein leeres Ergebnis
    (RLS ohne SELECT-Policy) zählt trotzdem als 'exists', da die Anfrage 200 liefert.
    """
    client = get_client()
    if not client:
        return {
            "ok": False,
            "error": "supabase client unavailable",
            "tables": {t: None for t in TARGET_TABLES},
        }
    tables: Dict[str, str] = {}
    for t in TARGET_TABLES:
        try:
            client.table(t).select("*").limit(1).execute()
            tables[t] = "exists"
        except Exception as exc:
            tables[t] = "missing" if "PGRST205" in str(exc) else f"error: {str(exc)[:120]}"
    all_exist = all(v == "exists" for v in tables.values())
    # Gate-Cache aktualisieren: nach Anwenden des Schemas schaltet dieser Aufruf
    # (z.B. via GET /api/supabase/tables) die Persistenz ohne Neustart scharf.
    global _TABLES_READY
    _TABLES_READY = all_exist
    return {
        "ok": all_exist,
        "tables": tables,
        "schema_sql": None if all_exist else "supabase/schema.sql + supabase/schema_migration_v2.sql",
        "hint": None if all_exist else "Schema: schema.sql dann schema_migration_v2.sql im SQL Editor",
    }


def sync_status() -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "cloud_sync": cloud_sync_enabled(),
        "device_id": device_id(),
        "metrics_interval_sec": int(os.getenv("FUSION_SUPABASE_METRICS_INTERVAL_SEC", "30")),
        "phone_link_interval_sec": int(os.getenv("FUSION_PHONE_LINK_SNAPSHOT_INTERVAL_SEC", "300")),
        "settings_cloud_pull": os.getenv("FUSION_SETTINGS_CLOUD_PULL", "0") == "1",
    }
    try:
        from watch_sync_server import (
            get_realtime_client_config,
            realtime_enabled,
            server_sync_enabled,
        )

        status["watch_server_sync"] = server_sync_enabled()
        status["watch_realtime"] = realtime_enabled()
        status["watch_realtime_config"] = get_realtime_client_config()
        status["schema_migration_v3"] = (
            "supabase/schema_migration_v3_realtime.sql"
            if realtime_enabled()
            else None
        )
    except Exception as exc:
        status["watch_realtime_error"] = str(exc)[:120]
    try:
        tables = check_tables()
        status["tables_ok"] = tables.get("ok")
        status["tables"] = tables.get("tables")
    except Exception:
        pass
    return status


def roundtrip_test() -> Dict[str, Any]:
    """Schreib-Lese-Test: fügt ein markiertes Test-Event ein und liest es zurück.

    ACHTUNG: schreibt eine Zeile nach fusion_events — nur bewusst aufrufen.
    """
    marker = f"roundtrip-{int(time.time())}"
    ins = save_event({"id": marker, "type": "selftest", "msg": marker, "severity": "low"})
    if not ins.get("ok"):
        return {"ok": False, "stage": "insert", "marker": marker, **ins}
    rows = list_recent_events(10)
    found = any(r.get("event_id") == marker for r in rows)
    return {"ok": found, "stage": "read", "marker": marker, "recent_count": len(rows)}


if __name__ == "__main__":
    import json
    import sys

    print("[supabase_store] configured:", is_configured())
    tbl = check_tables()
    print("[supabase_store] check_tables:")
    print(json.dumps(tbl, indent=2, ensure_ascii=False))

    if "--write" in sys.argv:
        if tbl.get("ok"):
            print("[supabase_store] roundtrip_test (schreibt ein Test-Event):")
            print(json.dumps(roundtrip_test(), indent=2, ensure_ascii=False))
        else:
            print("[supabase_store] roundtrip übersprungen — Tabellen fehlen (Schema anwenden).")