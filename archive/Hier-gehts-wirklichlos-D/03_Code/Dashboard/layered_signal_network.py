# -*- coding: utf-8 -*-
"""Gelayerte Signale — Netzwerknutzung optimieren (Pulse/Delta/Batch/Full)."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fusion_profile import get_profile_config

LAYERS = ("pulse", "delta", "batch", "full")
_LAYER_ORDER = {name: i for i, name in enumerate(LAYERS)}

_sessions: Dict[str, "_SignalSession"] = {}


@dataclass
class SignalEnvelope:
    layer: str
    seq: int
    ts: float
    payload: dict
    bytes_estimate: int = 0
    skipped_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "seq": self.seq,
            "ts": self.ts,
            "payload": self.payload,
            "bytes_estimate": self.bytes_estimate,
            "skipped_fields": self.skipped_fields,
            "coalesce_ms": get_profile_config().get("signal_coalesce_ms", 500),
        }


class _SignalSession:
    def __init__(self) -> None:
        self.seq = 0
        self.last_full: dict = {}
        self.last_hash: str = ""
        self.last_emit: float = 0.0


def _session_id(client: str = "default") -> str:
    return client or "default"


def _get_session(client: str) -> _SignalSession:
    sid = _session_id(client)
    if sid not in _sessions:
        _sessions[sid] = _SignalSession()
    return _sessions[sid]


def _hash_payload(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _estimate_bytes(data: dict) -> int:
    return len(json.dumps(data, default=str).encode("utf-8"))


def _flatten_delta(prev: dict, curr: dict, prefix: str = "") -> dict:
    delta: dict = {}
    for key, val in curr.items():
        path = f"{prefix}.{key}" if prefix else key
        old = prev.get(key)
        if isinstance(val, dict) and isinstance(old, dict):
            nested = _flatten_delta(old, val, path)
            delta.update(nested)
        elif val != old:
            delta[path] = val
    return delta


def _pulse_payload(full: dict) -> dict:
    mf = full.get("mainframe", {})
    m = full.get("metrics", {})
    v12 = full.get("v12", {})
    ml = full.get("meta_layer", {})
    reg = full.get("registry", {}).get("summary", {})
    prof = full.get("profile", {})
    return {
        "ok": full.get("backend") == "online",
        "mf": bool(mf.get("loaded")),
        "cpu": m.get("cpu", 0),
        "ram": m.get("ram", 0),
        "agents": reg.get("total_agents", 0),
        "modules_loaded": reg.get("loaded", 0),
        "modules_total": reg.get("total_modules", reg.get("loaded", 0)),
        "profile": prof.get("active", "admin"),
        "aligned": v12.get("grok_intern_aligned", False),
        "meta": bool(ml.get("attached")),
    }


def _batch_payload(full: dict) -> dict:
    pulse = _pulse_payload(full)
    reg = full.get("registry", {})
    ht = full.get("hyperthreading", {})
    profile = full.get("profile", {})
    resources = full.get("resources", {})
    return {
        **pulse,
        "modules_loaded": reg.get("summary", {}).get("loaded", 0),
        "ht": ht.get("enabled", False),
        "workers": ht.get("workers", 0),
        "profile": profile.get("active", "admin"),
        "orch_workers": resources.get("orchestrator_workers", 0),
    }


def emit_signal(
    full_payload: dict,
    layer: Optional[str] = None,
    client: str = "default",
    force_full: bool = False,
) -> SignalEnvelope:
    """Erzeugt gelayertes Signal — weniger Bytes bei Pulse/Delta."""
    profile = get_profile_config()
    layer = (layer or profile.get("network_layer_default", "delta")).lower()
    if layer not in _LAYER_ORDER:
        layer = "delta"

    sess = _get_session(client)
    now = time.time()
    coalesce = profile.get("signal_coalesce_ms", 500) / 1000.0

    if not force_full and layer != "full" and (now - sess.last_emit) < coalesce:
        layer = "pulse" if _LAYER_ORDER[layer] > _LAYER_ORDER["pulse"] else layer

    sess.seq += 1

    if force_full or layer == "full":
        payload = full_payload
        skipped: List[str] = []
    elif layer == "pulse":
        payload = _pulse_payload(full_payload)
        skipped = [k for k in full_payload if k not in payload]
    elif layer == "batch":
        payload = _batch_payload(full_payload)
        skipped = [k for k in full_payload if k not in ("mainframe", "metrics", "v12", "registry", "hyperthreading", "profile", "resources", "meta_layer")]
    else:
        delta = _flatten_delta(sess.last_full, full_payload)
        if not delta and sess.last_full:
            payload = {"unchanged": True, "seq_ref": sess.seq - 1}
            skipped = list(full_payload.keys())
        else:
            payload = {"delta": delta, "seq_ref": sess.seq}
            skipped = [k for k in full_payload if k not in delta and f".{k}" not in "".join(delta)]

    new_hash = _hash_payload(full_payload)
    if new_hash != sess.last_hash:
        sess.last_full = full_payload
        sess.last_hash = new_hash
    sess.last_emit = now

    return SignalEnvelope(
        layer=layer,
        seq=sess.seq,
        ts=now,
        payload=payload,
        bytes_estimate=_estimate_bytes(payload),
        skipped_fields=skipped,
    )


def network_stats() -> dict:
    return {
        "layers": list(LAYERS),
        "sessions": len(_sessions),
        "default_layer": get_profile_config().get("network_layer_default", "delta"),
        "coalesce_ms": get_profile_config().get("signal_coalesce_ms", 500),
    }