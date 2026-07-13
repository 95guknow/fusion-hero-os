# -*- coding: utf-8 -*-
"""Persistenz-Layer: Fusion Hero OS → Supabase (swmmoxhdzarmoupyssqe)."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from supabase_client import get_client, is_configured


def _insert(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return {"ok": False, "error": "supabase client unavailable"}
    try:
        resp = client.table(table).insert(row).execute()
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


def store_status() -> Dict[str, Any]:
    return {
        "configured": is_configured(),
        "tables": [
            "fusion_events",
            "fusion_metrics",
            "fusion_jobs",
            "heroic_llama_configs",
        ],
    }