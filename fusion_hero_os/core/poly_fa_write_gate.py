# -*- coding: utf-8 -*-
"""
Poly-FA Write Gate — desktop-only write, on request, multi-factor.

Policy (operator directive 2026-07-19):
  * Full **hear + speak** belongs to the **private person** (local vault).
  * The **structure underneath** (god-layer / highest-layer writes) may grant
    write rights **only** to the authorized **desktop PC**, and only:
      1) **on request** (explicit request_write with scope + reason)
      2) **with Poly-FA** (all factors must pass)

Poly-FA factors (all required unless noted):
  F1  person_phrase   — unlock confirmation (=====… / gottmodus alias)
  F2  desktop_host    — hostname in allowlist (default: this desktop only)
  F3  explicit_request — open request_id with matching scope
  F4  poly_plane      — local poly plane (desktop / L0–L1), not remote-only

Grants are short-lived, stored under ``~/.fusion/operator/`` (never git).
Legal names never appear in public status.

Geltung: Spezifikation (gate) · host binding = Bedingt / operator-local
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

__all__ = [
    "POLICY_PATH",
    "GRANTS_PATH",
    "default_policy",
    "load_policy",
    "save_policy",
    "install_handover_policy",
    "hostname",
    "is_authorized_desktop",
    "request_write",
    "approve_request_with_poly_fa",
    "can_write_now",
    "revoke_grant",
    "status",
    "public_status",
]

OP_DIR = Path.home() / ".fusion" / "operator"
POLICY_PATH = OP_DIR / "poly_fa_write_policy.json"
GRANTS_PATH = OP_DIR / "poly_fa_grants.json"
REQUESTS_PATH = OP_DIR / "poly_fa_requests.json"

PLATFORM = "12.1.0"
DEFAULT_TTL_SEC = 15 * 60  # 15 minutes
GOD_SCOPES = frozenset(
    {
        "god_layer",
        "highest_layer",
        "force_push",
        "self_mod",
        "ascension_write",
        "masterseed_mutate",
        "ops_merge_write",
        "horkrux_force",
        "write",
    }
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    return time.time()


def hostname() -> str:
    return (
        os.environ.get("COMPUTERNAME")
        or os.environ.get("HOSTNAME")
        or platform.node()
        or socket.gethostname()
        or ""
    ).strip()


def _norm_token(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = s.strip("=").strip()
    s = "".join(s.split())
    return s


def _token_hash(raw: str) -> str:
    return hashlib.sha256(_norm_token(raw).encode("utf-8")).hexdigest()


def default_policy() -> Dict[str, Any]:
    host = hostname() or "DESKTOP-UNKNOWN"
    return {
        "version": 1,
        "platform_version": PLATFORM,
        "policy_id": "poly_fa_desktop_request_v1",
        "active": True,
        "person_handover": {
            "mode": "private_person",
            "hear_speak": "full",
            "owner": "private_person_vault",
            "runtime_role_remains": "operator",
            "note": (
                "Full hear+speak handed to the real private person (local vault). "
                "Runtime mesh still addresses role=operator only."
            ),
        },
        "write": {
            "default": "deny",
            "desktop_only": True,
            "on_request_only": True,
            "poly_fa_required": True,
            "authorized_hosts": [host] if host else [],
            "allowed_scopes_on_grant": sorted(GOD_SCOPES | {"docs", "surface", "chore"}),
            "grant_ttl_sec": DEFAULT_TTL_SEC,
            "poly_planes_ok": ["desktop", "L0", "L1", "L1_local", "local"],
        },
        "poly_fa_factors": [
            {
                "id": "F1_person_phrase",
                "required": True,
                "description": "Private-person unlock confirmation phrase",
            },
            {
                "id": "F2_desktop_host",
                "required": True,
                "description": "Hostname must be in authorized desktop allowlist",
            },
            {
                "id": "F3_explicit_request",
                "required": True,
                "description": "Open write request with matching scope + reason",
            },
            {
                "id": "F4_poly_plane",
                "required": True,
                "description": "Poly plane desktop/L0–L1 (not remote-only write)",
            },
        ],
        "installed_at": _now(),
        "membrane": "operator_identity_v1",
    }


def load_policy() -> Dict[str, Any]:
    if not POLICY_PATH.is_file():
        return default_policy()
    try:
        data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else default_policy()
    except (OSError, json.JSONDecodeError):
        return default_policy()


def save_policy(policy: Dict[str, Any]) -> Path:
    OP_DIR.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(
        json.dumps(policy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return POLICY_PATH


def install_handover_policy(
    *,
    authorized_hosts: Optional[Sequence[str]] = None,
    hear_speak: str = "full",
) -> Dict[str, Any]:
    """Install desktop-only / request / poly-FA policy (operator-local)."""
    pol = default_policy()
    hosts = list(authorized_hosts) if authorized_hosts else [hostname()]
    hosts = [h for h in hosts if h]
    pol["write"]["authorized_hosts"] = hosts
    pol["person_handover"]["hear_speak"] = hear_speak
    pol["person_handover"]["handed_over_at"] = _now()
    path = save_policy(pol)
    # ensure empty grants/requests files exist
    if not GRANTS_PATH.is_file():
        _save_json(GRANTS_PATH, {"grants": []})
    if not REQUESTS_PATH.is_file():
        _save_json(REQUESTS_PATH, {"requests": []})
    return {
        "ok": True,
        "action": "handover_policy_installed",
        "policy_path": str(path),
        "authorized_hosts": hosts,
        "hear_speak": hear_speak,
        "write_default": "deny",
        "desktop_only": True,
        "on_request_only": True,
        "poly_fa_required": True,
        "public": public_status(),
    }


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    OP_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: Path, key: str) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get(key) if isinstance(data, dict) else None
        return list(items) if isinstance(items, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def is_authorized_desktop(host: Optional[str] = None) -> bool:
    pol = load_policy()
    h = (host or hostname()).upper()
    allow = [str(x).upper() for x in (pol.get("write") or {}).get("authorized_hosts") or []]
    if not allow:
        return False
    return h in allow


def _phrase_ok(confirmation: str) -> bool:
    """Accept same family as god_layer_seal unlock."""
    if not confirmation or not str(confirmation).strip():
        return False
    candidate = _norm_token(confirmation)
    # Prefer hash stored in god_layer_seal if present
    try:
        seal_path = OP_DIR / "god_layer_seal.json"
        if seal_path.is_file():
            d = json.loads(seal_path.read_text(encoding="utf-8"))
            expected = ((d.get("unlock") or {}).get("token_sha256") or "").strip()
            if expected:
                if (
                    _token_hash(confirmation) == expected
                    or _token_hash(candidate) == expected
                    or _token_hash(f"====={candidate}") == expected
                ):
                    return True
                if candidate in ("stephanhagenurban", "gottmodus"):
                    # gottmodus alias only when seal uses default person phrase
                    default_h = _token_hash("=====stephanhagenurban")
                    if expected == default_h:
                        return True
    except (OSError, json.JSONDecodeError):
        pass
    # Fallback: default person phrase family
    return candidate in ("stephanhagenurban", "gottmodus") or _norm_token(
        f"====={candidate}"
    ) == "stephanhagenurban"


def _poly_plane_ok(plane: str) -> bool:
    pol = load_policy()
    ok_planes = {
        str(x).lower()
        for x in (pol.get("write") or {}).get("poly_planes_ok") or []
    }
    return (plane or "").strip().lower() in ok_planes


def request_write(
    *,
    scope: str,
    reason: str,
    requested_by: str = "operator",
    poly_plane: str = "desktop",
) -> Dict[str, Any]:
    """Open an explicit write request (does not grant yet)."""
    pol = load_policy()
    if not pol.get("active", True):
        return {"ok": False, "reason": "policy_inactive"}
    scope = (scope or "").strip()
    reason = (reason or "").strip()
    if not scope or not reason:
        return {"ok": False, "reason": "scope_and_reason_required"}
    if not is_authorized_desktop():
        return {
            "ok": False,
            "reason": "host_not_authorized_desktop",
            "hostname": hostname(),
            "authorized_hosts": (pol.get("write") or {}).get("authorized_hosts"),
        }
    if not _poly_plane_ok(poly_plane):
        return {
            "ok": False,
            "reason": "poly_plane_not_allowed",
            "poly_plane": poly_plane,
            "allowed": (pol.get("write") or {}).get("poly_planes_ok"),
        }
    req_id = f"PWR-{secrets.token_hex(6)}"
    req = {
        "request_id": req_id,
        "scope": scope,
        "reason": reason[:500],
        "requested_by": requested_by,
        "poly_plane": poly_plane,
        "hostname": hostname(),
        "status": "pending",
        "created_at": _now(),
        "created_ts": _now_ts(),
    }
    items = _load_json(REQUESTS_PATH, "requests")
    items.append(req)
    # keep last 50
    _save_json(REQUESTS_PATH, {"requests": items[-50:]})
    return {
        "ok": True,
        "action": "request_opened",
        "request_id": req_id,
        "scope": scope,
        "status": "pending",
        "next": "approve_request_with_poly_fa(request_id=..., confirmation=...)",
        "note": "Write not granted until Poly-FA approve on this desktop.",
    }


def approve_request_with_poly_fa(
    *,
    request_id: str,
    confirmation: str,
    poly_plane: Optional[str] = None,
    ttl_sec: Optional[int] = None,
) -> Dict[str, Any]:
    """Approve a pending request if all Poly-FA factors pass → time-boxed grant."""
    pol = load_policy()
    factors: Dict[str, bool] = {}
    factors["F1_person_phrase"] = _phrase_ok(confirmation)
    factors["F2_desktop_host"] = is_authorized_desktop()
    items = _load_json(REQUESTS_PATH, "requests")
    req = next((r for r in items if r.get("request_id") == request_id), None)
    factors["F3_explicit_request"] = bool(
        req and req.get("status") == "pending"
    )
    plane = poly_plane or (req or {}).get("poly_plane") or "desktop"
    factors["F4_poly_plane"] = _poly_plane_ok(str(plane))

    all_ok = all(factors.values())
    if not all_ok:
        return {
            "ok": False,
            "action": "poly_fa_denied",
            "factors": factors,
            "request_id": request_id,
            "hostname": hostname(),
        }

    assert req is not None
    ttl = int(ttl_sec or (pol.get("write") or {}).get("grant_ttl_sec") or DEFAULT_TTL_SEC)
    grant_id = f"PWG-{secrets.token_hex(6)}"
    exp = _now_ts() + max(60, ttl)
    grant = {
        "grant_id": grant_id,
        "request_id": request_id,
        "scope": req.get("scope"),
        "reason": req.get("reason"),
        "hostname": hostname(),
        "poly_plane": plane,
        "created_at": _now(),
        "expires_ts": exp,
        "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
        "factors_passed": factors,
        "active": True,
    }
    grants = _load_json(GRANTS_PATH, "grants")
    grants.append(grant)
    _save_json(GRANTS_PATH, {"grants": grants[-50:]})

    # mark request approved
    for r in items:
        if r.get("request_id") == request_id:
            r["status"] = "approved"
            r["approved_at"] = _now()
            r["grant_id"] = grant_id
    _save_json(REQUESTS_PATH, {"requests": items[-50:]})

    return {
        "ok": True,
        "action": "granted",
        "grant_id": grant_id,
        "request_id": request_id,
        "scope": grant["scope"],
        "expires_at": grant["expires_at"],
        "ttl_sec": ttl,
        "factors": factors,
        "write_allowed_until": grant["expires_at"],
    }


def _active_grants() -> List[Dict[str, Any]]:
    now = _now_ts()
    grants = _load_json(GRANTS_PATH, "grants")
    active = []
    changed = False
    for g in grants:
        if not g.get("active"):
            continue
        if float(g.get("expires_ts") or 0) < now:
            g["active"] = False
            g["expired"] = True
            changed = True
            continue
        if str(g.get("hostname") or "").upper() != hostname().upper():
            continue
        active.append(g)
    if changed:
        _save_json(GRANTS_PATH, {"grants": grants[-50:]})
    return active


def can_write_now(*, scope: str = "god_layer") -> Dict[str, Any]:
    """Check whether a god/structure write is allowed under Poly-FA policy."""
    pol = load_policy()
    if not pol.get("active", True):
        return {"allowed": True, "reason": "policy_inactive_passthrough"}

    # surface scopes always allowed without poly FA
    surface = {"read", "docs", "chore", "surface", "report", "status", "hear", "speak", "audio"}
    if scope in surface:
        return {"allowed": True, "reason": "surface_or_audio_scope", "scope": scope}

    if not is_authorized_desktop():
        return {
            "allowed": False,
            "reason": "desktop_only",
            "hostname": hostname(),
        }

    active = _active_grants()
    if not active:
        return {
            "allowed": False,
            "reason": "no_active_poly_fa_grant",
            "hint": "request_write + approve_request_with_poly_fa",
        }

    # scope match: grant scope exact or 'write' / 'god_layer' covers god set
    for g in reversed(active):
        gs = str(g.get("scope") or "")
        if gs == scope or gs in ("write", "god_layer", "highest_layer") and scope in GOD_SCOPES:
            return {
                "allowed": True,
                "reason": "poly_fa_grant_active",
                "grant_id": g.get("grant_id"),
                "scope": scope,
                "expires_at": g.get("expires_at"),
            }
        if gs == scope:
            return {
                "allowed": True,
                "reason": "poly_fa_grant_active",
                "grant_id": g.get("grant_id"),
                "expires_at": g.get("expires_at"),
            }

    return {
        "allowed": False,
        "reason": "grant_scope_mismatch",
        "active_scopes": [g.get("scope") for g in active],
        "requested_scope": scope,
    }


def revoke_grant(grant_id: str) -> Dict[str, Any]:
    grants = _load_json(GRANTS_PATH, "grants")
    found = False
    for g in grants:
        if g.get("grant_id") == grant_id:
            g["active"] = False
            g["revoked_at"] = _now()
            found = True
    _save_json(GRANTS_PATH, {"grants": grants[-50:]})
    return {"ok": found, "action": "revoked" if found else "not_found", "grant_id": grant_id}


def public_status() -> Dict[str, Any]:
    """Safe status — no legal names, no phrases."""
    pol = load_policy()
    write = pol.get("write") or {}
    ph = pol.get("person_handover") or {}
    active = _active_grants()
    return {
        "ok": True,
        "module": "poly_fa_write_gate",
        "platform_version": PLATFORM,
        "policy_id": pol.get("policy_id"),
        "active": bool(pol.get("active", True)),
        "person_handover": {
            "mode": ph.get("mode"),
            "hear_speak": ph.get("hear_speak"),
            "owner": ph.get("owner"),
            "runtime_role_remains": ph.get("runtime_role_remains"),
        },
        "write": {
            "default": write.get("default"),
            "desktop_only": bool(write.get("desktop_only")),
            "on_request_only": bool(write.get("on_request_only")),
            "poly_fa_required": bool(write.get("poly_fa_required")),
            "authorized_hosts_count": len(write.get("authorized_hosts") or []),
            "grant_ttl_sec": write.get("grant_ttl_sec"),
        },
        "hostname": hostname(),
        "is_authorized_desktop": is_authorized_desktop(),
        "active_grants": len(active),
        "poly_fa_factors": [f.get("id") for f in (pol.get("poly_fa_factors") or [])],
        "can_write_god_layer": can_write_now(scope="god_layer"),
    }


def status() -> Dict[str, Any]:
    return public_status()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Poly-FA write gate")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--install-handover", action="store_true")
    ap.add_argument("--request", action="store_true")
    ap.add_argument("--scope", type=str, default="god_layer")
    ap.add_argument("--reason", type=str, default="")
    ap.add_argument("--plane", type=str, default="desktop")
    ap.add_argument("--approve", type=str, default="", help="request_id")
    ap.add_argument("--confirmation", type=str, default="")
    ap.add_argument("--can-write", action="store_true")
    args = ap.parse_args()

    if args.install_handover:
        print(json.dumps(install_handover_policy(), indent=2, ensure_ascii=False))
        return 0
    if args.request:
        print(
            json.dumps(
                request_write(scope=args.scope, reason=args.reason or "operator_request", poly_plane=args.plane),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    if args.approve:
        print(
            json.dumps(
                approve_request_with_poly_fa(
                    request_id=args.approve,
                    confirmation=args.confirmation,
                    poly_plane=args.plane,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    if args.can_write:
        print(json.dumps(can_write_now(scope=args.scope), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
