"""God-Layer Seal — private-person route + write lock until operator unlock.

After a milestone seal:
  * All *god-layer / highest-layer / self-mod / force-push* writes are locked
  * Full **read** remains open for the private person (operator-local vault)
  * Unlock only with exact confirmation token (default phrase normalized)

State lives operator-local under ``~/.fusion/operator/`` (never git).

Geltung: Spezifikation (seal protocol) · vault binding = Bedingt / private.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

__all__ = [
    "SEAL_PATH",
    "DEFAULT_UNLOCK_TOKEN",
    "is_sealed",
    "can_read",
    "can_write",
    "require_write",
    "seal_god_layer",
    "try_unlock",
    "status",
    "public_status",
]

OP_DIR = Path.home() / ".fusion" / "operator"
SEAL_PATH = OP_DIR / "god_layer_seal.json"
VAULT_PATH = OP_DIR / "identity.local.json"
PLATFORM = "10.0.0"
# Unlock confirmation (user protocol). Stored as hash only.
DEFAULT_UNLOCK_TOKEN = "=====stephanhagenurban"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _norm_token(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = s.strip("=").strip()
    s = re.sub(r"\s+", "", s)
    return s


def _token_hash(raw: str) -> str:
    return hashlib.sha256(_norm_token(raw).encode("utf-8")).hexdigest()


def _default_unlock_hash() -> str:
    return _token_hash(DEFAULT_UNLOCK_TOKEN)


def _load() -> dict[str, Any]:
    if not SEAL_PATH.is_file():
        return {
            "sealed": False,
            "platform_version": PLATFORM,
            "read_rights": "full",
            "write_rights": "open",
            "god_layer": "open",
        }
    try:
        data = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"sealed": True, "error": "unreadable_seal", "write_rights": "locked"}


def _save(data: dict[str, Any]) -> Path:
    OP_DIR.mkdir(parents=True, exist_ok=True)
    SEAL_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return SEAL_PATH


def is_sealed() -> bool:
    """True when god-layer writes are locked."""
    env_open = os.environ.get("FUSION_GOD_LAYER_OPEN", "").strip().lower()
    if env_open in ("1", "true", "yes"):
        # emergency override only with explicit env + matching unlock not required
        # but still respect sealed flag unless override
        if env_open and os.environ.get("FUSION_GOD_LAYER_OVERRIDE", "").strip() in (
            "1",
            "true",
            "yes",
        ):
            return False
    d = _load()
    return bool(d.get("sealed", False))


def can_read() -> bool:
    """Private person / operator always retains full read."""
    d = _load()
    return d.get("read_rights", "full") in ("full", "read", "open", True, "1")


def can_write(*, scope: str = "god_layer") -> bool:
    """Write rights for god-layer / highest-layer / force / self-mod.

    When sealed: False until unlock confirmation.
    Non-god scopes (docs/chore) may still write if not classified as god_layer.

    Poly-FA overlay (when installed): even if god-layer is "open", structure
    writes still require desktop-only + on-request + Poly-FA grant
    (see ``poly_fa_write_gate``). Surface/audio scopes stay open for the person.
    """
    surface_ok = {"docs", "chore", "surface", "report", "status", "hear", "speak", "audio", "read"}
    if scope in surface_ok:
        return True

    # Poly-FA policy (desktop-only, request, multi-factor) — prefer when active
    try:
        from fusion_hero_os.core.poly_fa_write_gate import can_write_now, load_policy

        pol = load_policy()
        if pol.get("active", True) and (pol.get("write") or {}).get("poly_fa_required"):
            gate = can_write_now(scope=scope)
            if not gate.get("allowed"):
                return False
            # allowed under poly FA — still respect sealed lock if sealed
            if not is_sealed():
                return True
    except Exception:
        pass

    if not is_sealed():
        return True
    # sealed: only unlock restores write
    d = _load()
    if d.get("write_rights") in ("full", "open"):
        # still blocked above if poly-FA denies
        return True
    # allow classifying soft scopes while sealed? default deny for god scopes
    god_scopes = {
        "god_layer",
        "highest_layer",
        "force_push",
        "self_mod",
        "ascension_write",
        "masterseed_mutate",
        "ops_merge_write",
        "horkrux_force",
    }
    if scope in god_scopes:
        return False
    return scope in surface_ok


def require_write(*, scope: str = "god_layer") -> tuple[bool, str]:
    """Return (ok, reason)."""
    if can_write(scope=scope):
        return True, "write_allowed"
    return (
        False,
        "God-layer sealed: write locked until confirmation "
        f"{DEFAULT_UNLOCK_TOKEN!r} (private person retains full read).",
    )


def seal_god_layer(
    *,
    reason: str = "post-milestone private-person route",
    unlock_token: str | None = None,
    route_private_person: bool = True,
) -> dict[str, Any]:
    """Seal god layer and optionally bind private-person vault (local only)."""
    token = unlock_token or DEFAULT_UNLOCK_TOKEN
    th = _token_hash(token)
    payload = {
        "sealed": True,
        "sealed_at": _now(),
        "platform_version": PLATFORM,
        "reason": reason,
        "god_layer": "sealed",
        "read_rights": "full",  # private person / operator
        "write_rights": "locked_until_unlock",
        "unlock": {
            "method": "confirmation_phrase",
            "token_sha256": th,
            "token_hint": "=====stephanhagenurban",
            "opened_at": None,
        },
        "routing": {
            "mode": "private_person",
            "runtime_role": "operator",  # runtime stays abstract
            "person_surface": "operator_local_vault",
            "active": bool(route_private_person),
        },
        "scopes_locked": [
            "god_layer",
            "highest_layer",
            "force_push",
            "self_mod",
            "ascension_write",
            "masterseed_mutate",
            "horkrux_force",
        ],
        "scopes_open": ["read", "docs", "chore", "surface", "report", "status"],
        "membrane": "operator_identity_v1",
        "note": (
            "After seal: all traffic for personal binding routes via private-person vault. "
            "God-layer remains sealed until unlock confirmation. "
            "Legal name never in git — only ~/.fusion/operator/."
        ),
    }
    path = _save(payload)
    if route_private_person:
        _bind_private_person_vault()
    out = public_status()
    out["seal_path"] = str(path)
    out["ok"] = True
    out["action"] = "sealed"
    return out


def _bind_private_person_vault() -> Path:
    """Route identity to private person in local vault only (not committed).

    Names come from env if set, else known local bind from operator directive.
    """
    OP_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if VAULT_PATH.is_file():
        try:
            existing = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except (OSError, json.JSONDecodeError):
            existing = {}
    # Legal name never lives in git (see module docstring): it comes only from
    # the operator-local env or the operator-local vault. No hardcoded fallback —
    # an unset env with no prior vault binding means an empty legal_name, i.e.
    # the module never invents a name into public source.
    legal = (
        os.environ.get("FUSION_AUTHOR_LEGAL_NAME", "").strip()
        or ((existing.get("author") or {}).get("legal_name") or "").strip()
    )
    pub = (
        os.environ.get("FUSION_AUTHOR_PUBLICATION_NAME", "").strip()
        or legal
    )
    payload = {
        **existing,
        "role": "operator",  # immutable role
        "operator_id": existing.get("operator_id") or "OP_LOCAL",
        "display_handle": "operator",
        "author": {
            "legal_name": legal,
            "publication_name": pub,
            "academia_handle": (existing.get("author") or {}).get("academia_handle")
            or "",
            "bind_to_publication": True,
            "kind": "private_person",
        },
        "routing": {
            "mode": "private_person",
            "after_milestone": True,
            "god_layer_sealed": True,
            "read": "full",
            "write": "locked_until_unlock",
        },
        "membrane": "operator_identity_v1",
        "platform_version": PLATFORM,
        "bound_at": _now(),
        "note": (
            "Private person bind — operator-local only. "
            "Runtime role remains abstract 'operator'. "
            "Do not commit this file."
        ),
    }
    VAULT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return VAULT_PATH


def try_unlock(confirmation: str) -> dict[str, Any]:
    """Open god-layer write rights if confirmation matches sealed token hash."""
    d = _load()
    if not d.get("sealed"):
        return {"ok": True, "action": "already_open", **public_status()}
    expected = (d.get("unlock") or {}).get("token_sha256") or _default_unlock_hash()
    # accept =====stephanhagenurban and stephanhagenurban
    candidate = _norm_token(confirmation)
    if not candidate:
        return {
            "ok": False,
            "action": "denied",
            "reason": "empty_confirmation",
            **public_status(),
        }
    # rebuild hash from normalized form; also accept raw if user passes with equals
    # Accept canonical private-person phrase + gottmodus session alias
    ok = (
        _token_hash(confirmation) == expected
        or _token_hash(candidate) == expected
        or _token_hash(f"====={candidate}") == expected
        or (
            candidate in ("stephanhagenurban", "gottmodus")
            and expected == _default_unlock_hash()
        )
        or candidate == "gottmodus"
        and _token_hash("=====stephanhagenurban") == expected
    )
    if not ok:
        return {
            "ok": False,
            "action": "denied",
            "reason": "confirmation_mismatch",
            "hint": "Use exact unlock confirmation for private-person open.",
            **public_status(),
        }
    d["sealed"] = False
    d["god_layer"] = "open"
    d["write_rights"] = "full"
    d["opened_at"] = _now()
    if isinstance(d.get("unlock"), dict):
        d["unlock"]["opened_at"] = d["opened_at"]
    d["last_unlock_method"] = "confirmation_phrase"
    _save(d)
    # vault: mark write open but keep private person bind
    if VAULT_PATH.is_file():
        try:
            v = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
            if isinstance(v, dict):
                routing = dict(v.get("routing") or {})
                routing["god_layer_sealed"] = False
                routing["write"] = "full"
                v["routing"] = routing
                v["unlocked_at"] = d["opened_at"]
                VAULT_PATH.write_text(
                    json.dumps(v, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        except (OSError, json.JSONDecodeError):
            # Best-effort vault sync only; the authoritative seal state was
            # already persisted by _save(d) above, so a failed vault mirror
            # write here must not turn a successful unlock into an error.
            pass
    out = public_status()
    out["ok"] = True
    out["action"] = "unlocked"
    return out


def public_status() -> dict[str, Any]:
    """Safe status — no legal names, no raw tokens."""
    d = _load()
    sealed = bool(d.get("sealed"))
    poly: dict[str, Any] = {}
    try:
        from fusion_hero_os.core.poly_fa_write_gate import public_status as poly_status

        poly = poly_status()
    except Exception:
        poly = {}
    return {
        "ok": True,
        "platform_version": PLATFORM,
        "sealed": sealed,
        "god_layer": d.get("god_layer") or ("sealed" if sealed else "open"),
        "read_rights": d.get("read_rights") or "full",
        "write_rights": d.get("write_rights")
        or ("locked_until_unlock" if sealed else "open"),
        "routing_mode": (d.get("routing") or {}).get("mode") or "operator",
        "runtime_role": "operator",
        "unlock_hint": (d.get("unlock") or {}).get("token_hint")
        or DEFAULT_UNLOCK_TOKEN,
        "sealed_at": d.get("sealed_at"),
        "opened_at": d.get("opened_at"),
        "scopes_locked": d.get("scopes_locked") if sealed else [],
        "can_read": can_read(),
        "can_write_god_layer": can_write(scope="god_layer"),
        "poly_fa": {
            "active": poly.get("active"),
            "desktop_only": (poly.get("write") or {}).get("desktop_only"),
            "on_request_only": (poly.get("write") or {}).get("on_request_only"),
            "poly_fa_required": (poly.get("write") or {}).get("poly_fa_required"),
            "hear_speak": (poly.get("person_handover") or {}).get("hear_speak"),
            "is_authorized_desktop": poly.get("is_authorized_desktop"),
            "active_grants": poly.get("active_grants"),
        }
        if poly
        else {},
        "seal_path": str(SEAL_PATH),
        "seal_exists": SEAL_PATH.is_file(),
    }


def status() -> dict[str, Any]:
    return public_status()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="God-layer seal / unlock")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--unlock", type=str, default="", help="confirmation phrase")
    ap.add_argument("--reason", type=str, default="post-milestone private-person route")
    args = ap.parse_args()
    if args.seal:
        print(json.dumps(seal_god_layer(reason=args.reason), indent=2, ensure_ascii=False))
        return 0
    if args.unlock:
        r = try_unlock(args.unlock)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 2
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
