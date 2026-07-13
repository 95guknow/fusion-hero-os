# -*- coding: utf-8 -*-
"""Faden-Speicher — Persistenz für Verknüpfungsthreads nach Stärke (Fein → Fixpunkt)."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

STRENGTH_TIERS: Dict[str, Dict[str, Any]] = {
    "fein": {
        "level": 1,
        "label": "Feinfaden",
        "ttl_sec": 3600,
        "max_local": 200,
        "cloud_default": False,
        "lambda_range": (0.85, 0.99),
        "description": "Ephemer — Session-Spikes, latente Geister, kurze Echo-Tracks",
    },
    "mittel": {
        "level": 2,
        "label": "Mittelfaden",
        "ttl_sec": 7 * 86400,
        "max_local": 500,
        "cloud_default": False,
        "lambda_range": (0.55, 0.84),
        "description": "Session — Erkenntnis-Stufen, Kontext-Merge, TMS-Tracks",
    },
    "stark": {
        "level": 3,
        "label": "Starkfaden",
        "ttl_sec": 30 * 86400,
        "max_local": 300,
        "cloud_default": True,
        "lambda_range": (0.25, 0.54),
        "description": "Fixpunkt-nah — Layer-Verknüpfungen, QUBO-Bottleneck-Gewinner",
    },
    "fixpunkt": {
        "level": 4,
        "label": "Fixpunktfaden",
        "ttl_sec": None,
        "max_local": 100,
        "cloud_default": True,
        "lambda_range": (0.0, 0.24),
        "description": "Permanent — M₀-Anker, Z*, archivierte Synthese",
    },
}

VALID_STRENGTHS = frozenset(STRENGTH_TIERS.keys())


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "faden_threads"


def _index_path() -> Path:
    return _state_root() / "index.json"


@dataclass
class FadenThread:
    thread_id: str
    strength: str
    label: str = ""
    source: str = ""
    layer: int = 0
    lambda_contract: float = 0.74
    fixpoint_id: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    device_id: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    cloud_synced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "FadenThread":
        strength = (raw.get("strength") or "mittel").lower()
        if strength not in VALID_STRENGTHS:
            strength = "mittel"
        return cls(
            thread_id=str(raw.get("thread_id") or uuid.uuid4().hex[:12]),
            strength=strength,
            label=str(raw.get("label") or ""),
            source=str(raw.get("source") or ""),
            layer=int(raw.get("layer") or 0),
            lambda_contract=float(raw.get("lambda_contract") or 0.74),
            fixpoint_id=str(raw.get("fixpoint_id") or ""),
            state=dict(raw.get("state") or {}),
            device_id=str(raw.get("device_id") or ""),
            created_at=float(raw.get("created_at") or time.time()),
            updated_at=float(raw.get("updated_at") or time.time()),
            expires_at=raw.get("expires_at"),
            cloud_synced=bool(raw.get("cloud_synced")),
        )


def strength_from_lambda(lam: float) -> str:
    """Banach-λ → Fadenstärke (niedriges λ = näher am Fixpunkt = stärkerer Faden)."""
    lam = max(0.0, min(0.99, float(lam)))
    for name, tier in sorted(STRENGTH_TIERS.items(), key=lambda x: -x[1]["level"]):
        lo, hi = tier["lambda_range"]
        if lo <= lam <= hi:
            return name
    return "mittel"


def _expires_for_strength(strength: str, now: Optional[float] = None) -> Optional[float]:
    now = now or time.time()
    ttl = STRENGTH_TIERS.get(strength, {}).get("ttl_sec")
    if ttl is None:
        return None
    return now + float(ttl)


class FadenStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or _index_path()
        self._threads: Dict[str, FadenThread] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for raw in data.get("threads", []):
                t = FadenThread.from_dict(raw)
                self._threads[t.thread_id] = t
        except Exception:
            self._threads = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "updated_at": time.time(),
            "threads": [t.to_dict() for t in self._threads.values()],
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def prune(self, now: Optional[float] = None) -> Dict[str, int]:
        """Entfernt abgelaufene Fäden und erzwingt Tier-Limits."""
        now = now or time.time()
        removed_expired = 0
        for tid in list(self._threads.keys()):
            t = self._threads[tid]
            if t.expires_at is not None and t.expires_at <= now:
                del self._threads[tid]
                removed_expired += 1

        removed_cap = 0
        for strength in VALID_STRENGTHS:
            cap = int(STRENGTH_TIERS[strength]["max_local"])
            items = sorted(
                [t for t in self._threads.values() if t.strength == strength],
                key=lambda x: x.updated_at,
            )
            overflow = len(items) - cap
            if overflow > 0:
                for t in items[:overflow]:
                    del self._threads[t.thread_id]
                    removed_cap += 1

        if removed_expired or removed_cap:
            self._save()
        return {"expired": removed_expired, "capped": removed_cap, "remaining": len(self._threads)}

    def upsert(
        self,
        payload: Dict[str, Any],
        *,
        sync_cloud: Optional[bool] = None,
    ) -> Dict[str, Any]:
        from supabase_store import device_id

        now = time.time()
        tid = str(payload.get("thread_id") or "").strip()
        existing = self._threads.get(tid) if tid else None

        strength = (payload.get("strength") or (existing.strength if existing else "")).lower()
        if not strength and payload.get("lambda_contract") is not None:
            strength = strength_from_lambda(float(payload["lambda_contract"]))
        if strength not in VALID_STRENGTHS:
            strength = existing.strength if existing else "mittel"

        thread = FadenThread(
            thread_id=tid or uuid.uuid4().hex[:12],
            strength=strength,
            label=str(payload.get("label") or (existing.label if existing else "")),
            source=str(payload.get("source") or (existing.source if existing else "")),
            layer=int(payload.get("layer") if payload.get("layer") is not None else (existing.layer if existing else 0)),
            lambda_contract=float(
                payload.get("lambda_contract")
                if payload.get("lambda_contract") is not None
                else (existing.lambda_contract if existing else 0.74)
            ),
            fixpoint_id=str(payload.get("fixpoint_id") or (existing.fixpoint_id if existing else "")),
            state=dict(payload.get("state") or (existing.state if existing else {})),
            device_id=str(payload.get("device_id") or device_id()),
            created_at=float(existing.created_at if existing else now),
            updated_at=now,
            expires_at=_expires_for_strength(strength, now),
            cloud_synced=bool(existing.cloud_synced if existing else False),
        )

        self._threads[thread.thread_id] = thread
        self.prune(now)
        self._save()

        cloud_result: Dict[str, Any] = {"ok": False, "skipped": True}
        want_cloud = sync_cloud if sync_cloud is not None else bool(STRENGTH_TIERS[strength]["cloud_default"])
        if want_cloud:
            try:
                import supabase_store as store

                if store.cloud_sync_enabled():
                    cloud_result = store.save_faden_thread(thread.to_dict())
                    if cloud_result.get("ok"):
                        thread.cloud_synced = True
                        self._threads[thread.thread_id] = thread
                        self._save()
            except Exception as exc:
                cloud_result = {"ok": False, "error": str(exc)[:120]}

        return {
            "ok": True,
            "thread": thread.to_dict(),
            "cloud": cloud_result,
            "strength_meta": STRENGTH_TIERS[strength],
        }

    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        t = self._threads.get(thread_id)
        return t.to_dict() if t else None

    def list_threads(
        self,
        *,
        strength: Optional[str] = None,
        fixpoint_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        self.prune()
        items = list(self._threads.values())
        if strength:
            items = [t for t in items if t.strength == strength.lower()]
        if fixpoint_id:
            items = [t for t in items if t.fixpoint_id == fixpoint_id]
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return [t.to_dict() for t in items[: max(1, limit)]]

    def delete(self, thread_id: str) -> Dict[str, Any]:
        if thread_id not in self._threads:
            return {"ok": False, "error": "not_found"}
        del self._threads[thread_id]
        self._save()
        return {"ok": True, "thread_id": thread_id}

    def status(self) -> Dict[str, Any]:
        self.prune()
        counts: Dict[str, int] = {s: 0 for s in VALID_STRENGTHS}
        for t in self._threads.values():
            counts[t.strength] = counts.get(t.strength, 0) + 1
        return {
            "ok": True,
            "path": str(self.path),
            "total": len(self._threads),
            "by_strength": counts,
            "tiers": STRENGTH_TIERS,
        }


_store: Optional[FadenStore] = None


def get_faden_store() -> FadenStore:
    global _store
    if _store is None:
        _store = FadenStore()
    return _store