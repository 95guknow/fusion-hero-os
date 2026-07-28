"""API Plane Membrane — Hyperraum (half-private) vs Business (classical API).

Prospective clean separation (BCG / additive):
  * **hyperraum** — operator hyperspace: mesh, consent, identity, dissertation organs
  * **business**  — product API: businessplan, energy quotes, light health/metrics

Classification is path-based from ``api_planes.yaml``. Does not break legacy
routes; tags them so cutover can proceed without a big bang.

Geltung: Spezifikation (plane membrane) · placement L1 default.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = [
    "PLANE_HYPERRAUM",
    "PLANE_BUSINESS",
    "load_catalog",
    "classify_path",
    "plane_meta",
    "planes_status",
    "assert_plane_safe_payload",
]

PLANE_HYPERRAUM = "hyperraum"
PLANE_BUSINESS = "business"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "api_planes.yaml"


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else Path(
        os.environ.get("FUSION_API_PLANES", str(DEFAULT_CATALOG))
    )
    if not p.is_file():
        return _fallback_catalog()
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            return _fallback_catalog()
        data["_catalog_path"] = str(p)
        return data
    except Exception:
        return _fallback_catalog()


def _fallback_catalog() -> dict[str, Any]:
    return {
        "version": "1.0-fallback",
        "platform_version": "10.0.0",
        "planes": {
            PLANE_HYPERRAUM: {
                "id": PLANE_HYPERRAUM,
                "privacy": "half_private",
                "audience": "operator",
            },
            PLANE_BUSINESS: {
                "id": PLANE_BUSINESS,
                "privacy": "product",
                "audience": "subcontractors_customers_ops",
            },
        },
        "classification_rules": [
            {"plane": PLANE_BUSINESS, "match_prefix": "/api/v1/business"},
            {"plane": PLANE_BUSINESS, "match_prefix": "/api/businessplan"},
            {"plane": PLANE_BUSINESS, "match_prefix": "/api/health"},
            {"plane": PLANE_BUSINESS, "match_prefix": "/api/metrics"},
            {"plane": PLANE_HYPERRAUM, "match_prefix": "/api/hyperraum"},
            {"plane": PLANE_HYPERRAUM, "match_prefix": "/api/"},
        ],
        "_catalog_path": "fallback",
    }


def classify_path(path: str) -> dict[str, Any]:
    """Return plane classification for an HTTP path."""
    raw = (path or "/").strip() or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    # strip query
    path_only = raw.split("?", 1)[0]
    cat = load_catalog()
    rules = cat.get("classification_rules") or []
    matched: str | None = None
    matched_prefix = ""
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        pref = str(rule.get("match_prefix") or "")
        plane = str(rule.get("plane") or "")
        if not pref or not plane:
            continue
        if path_only == pref or path_only.startswith(pref):
            # longest prefix wins among sequential first-match if we track
            if len(pref) > len(matched_prefix):
                matched = plane
                matched_prefix = pref
    if not matched:
        matched = PLANE_HYPERRAUM
        matched_prefix = "(default)"
    meta = plane_meta(matched)
    return {
        "path": path_only,
        "plane": matched,
        "match_prefix": matched_prefix,
        "privacy": meta.get("privacy"),
        "audience": meta.get("audience"),
        "auth_posture": meta.get("auth_posture"),
        "label": meta.get("label"),
    }


def plane_meta(plane_id: str) -> dict[str, Any]:
    cat = load_catalog()
    planes = cat.get("planes") or {}
    p = planes.get(plane_id) or {}
    if not isinstance(p, dict):
        return {"id": plane_id}
    out = dict(p)
    out.setdefault("id", plane_id)
    return out


def planes_status() -> dict[str, Any]:
    cat = load_catalog()
    planes = cat.get("planes") or {}
    summary = {}
    for pid, meta in planes.items():
        if not isinstance(meta, dict):
            continue
        summary[pid] = {
            "id": pid,
            "label": meta.get("label"),
            "privacy": meta.get("privacy"),
            "audience": meta.get("audience"),
            "path_prefixes": meta.get("path_prefixes") or [],
            "capabilities": meta.get("capabilities") or [],
            "anti_patterns": meta.get("anti_patterns") or [],
        }
    return {
        "ok": True,
        "version": cat.get("version"),
        "platform_version": cat.get("platform_version", "10.0.0"),
        "catalog_path": cat.get("_catalog_path"),
        "planes": summary,
        "bridge": cat.get("bridge") or {},
        "principle": (cat.get("principle") or "")[:500],
        "entrypoints": {
            "planes_status": "/api/planes",
            "classify": "/api/planes/classify?path=/api/health",
            "business_root": "/api/v1/business",
            "hyperraum_root": "/api/hyperraum",
        },
        "examples": {
            "/api/health": classify_path("/api/health"),
            "/api/businessplan": classify_path("/api/businessplan"),
            "/api/v1/business/pricing": classify_path("/api/v1/business/pricing"),
            "/api/grok/interconnect": classify_path("/api/grok/interconnect"),
            "/api/hyperraum/status": classify_path("/api/hyperraum/status"),
            "/mainframe/grok": classify_path("/mainframe/grok"),
        },
    }


# Keys that must never appear on business plane responses
_BUSINESS_FORBIDDEN_KEY_FRAGMENTS = (
    "legal_name",
    "operator_vault",
    "consent_body",
    "chat_body",
    "shard_gpg",
    "private_key",
    "tailscale_peer_map",
)


def assert_plane_safe_payload(
    plane: str,
    payload: Any,
    *,
    path: str = "",
) -> tuple[bool, list[str]]:
    """Lightweight structural guard (not a full redactor).

    Returns (ok, issues). Business plane rejects known hyperraum-only key names.
    """
    if plane != PLANE_BUSINESS:
        return True, []
    issues: list[str] = []

    def walk(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = str(k).lower()
                path_k = f"{prefix}.{k}" if prefix else str(k)
                for frag in _BUSINESS_FORBIDDEN_KEY_FRAGMENTS:
                    if frag in key:
                        issues.append(f"forbidden_key:{path_k}")
                walk(v, path_k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:50]):
                walk(item, f"{prefix}[{i}]")

    walk(payload)
    return len(issues) == 0, issues


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="API plane classifier")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--path", default="", help="classify a path")
    args = ap.parse_args()
    if args.path:
        print(json.dumps(classify_path(args.path), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(planes_status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
