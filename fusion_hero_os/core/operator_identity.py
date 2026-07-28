"""Operator Identity Membrane — extract person from role (v10 Stage-B+).

**Principle (Autopolitik):**
  * Runtime role is always abstract: ``operator`` (never a legal name).
  * Legal / academic person (e.g. dissertation author) lives in an
    **operator-local vault** or explicit publication profile — not hard-coded
    into the operative package.
  * Peers, agents, Comädchen, mesh: may address *role* only.
  * Publication surfaces may bind author display names from the vault when the
    operator opts in (``FUSION_AUTHOR_BIND=1``).

Paths (operator-local, git-ignored via ``~/.fusion/``):
  ``~/.fusion/operator/identity.local.json``

Example (never commit real values)::

    {
      "role": "operator",
      "operator_id": "OP_LOCAL",
      "display_handle": "operator",
      "author": {
        "legal_name": "<only in local vault>",
        "publication_name": "<only in local vault>",
        "academia_handle": "",
        "bind_to_publication": true
      },
      "extracted_at": "…",
      "membrane": "operator_identity_v1"
    }

Geltung: Spezifikation (membrane) · personal binding = operator-local / Bedingt.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

__all__ = [
    "ROLE_OPERATOR",
    "VAULT_PATH",
    "load_identity",
    "save_identity_template",
    "operator_role",
    "operator_id",
    "author_for_publication",
    "public_operator_view",
    "is_person_bound",
    "extract_status",
]

ROLE_OPERATOR = "operator"
VAULT_DIR = Path.home() / ".fusion" / "operator"
VAULT_PATH = VAULT_DIR / "identity.local.json"
MEMBRANE = "operator_identity_v1"
PLATFORM = "10.0.0"

# Public placeholders only — never legal names in package defaults
_DEFAULT_PUBLIC: dict[str, Any] = {
    "role": ROLE_OPERATOR,
    "operator_id": "OP_LOCAL",
    "display_handle": "operator",
    "author": {
        "legal_name": "",
        "publication_name": "",
        "academia_handle": "",
        "bind_to_publication": False,
    },
    "membrane": MEMBRANE,
    "platform_version": PLATFORM,
    "person_bound": False,
    "note": (
        "Person (legal name) is extracted from the Operator role. "
        "Fill ~/.fusion/operator/identity.local.json locally if publication "
        "binding is required. Runtime never requires a legal name."
    ),
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def load_identity() -> dict[str, Any]:
    """Load operator-local identity; fall back to public abstract role."""
    env_path = os.environ.get("FUSION_OPERATOR_IDENTITY", "").strip()
    path = Path(env_path) if env_path else VAULT_PATH
    data = dict(_DEFAULT_PUBLIC)
    data["vault_path"] = str(path)
    data["vault_exists"] = path.is_file()
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if k not in ("note",)})
                author = raw.get("author") if isinstance(raw.get("author"), dict) else {}
                data["author"] = {
                    **_DEFAULT_PUBLIC["author"],
                    **(author or {}),
                }
        except (OSError, json.JSONDecodeError):
            data["vault_error"] = "unreadable"
    # person_bound only if vault has a non-empty legal or publication name
    author = data.get("author") or {}
    data["person_bound"] = bool(
        (author.get("legal_name") or "").strip()
        or (author.get("publication_name") or "").strip()
    )
    data["role"] = ROLE_OPERATOR  # immutable: role is never a person name
    data["membrane"] = MEMBRANE
    return data


def save_identity_template(*, force: bool = False) -> Path:
    """Write empty local vault template (no legal names)."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    if VAULT_PATH.is_file() and not force:
        return VAULT_PATH
    payload = {
        "role": ROLE_OPERATOR,
        "operator_id": "OP_LOCAL",
        "display_handle": "operator",
        "author": {
            "legal_name": "",
            "publication_name": "",
            "academia_handle": "",
            "bind_to_publication": False,
        },
        "membrane": MEMBRANE,
        "platform_version": PLATFORM,
        "extracted_at": _now(),
        "note": (
            "Operator role is abstract. Put dissertation author fields here "
            "only if you want local publication tooling to bind them. "
            "Do not commit this file."
        ),
    }
    VAULT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return VAULT_PATH


def operator_role() -> str:
    return ROLE_OPERATOR


def operator_id() -> str:
    return str(load_identity().get("operator_id") or "OP_LOCAL")


def author_for_publication() -> dict[str, Any]:
    """Author fields for *publication* tooling only.

    Returns empty names unless vault binds them **and**
    ``FUSION_AUTHOR_BIND=1`` (or vault ``author.bind_to_publication``).
    Never invents a legal name.
    """
    ident = load_identity()
    author = dict(ident.get("author") or {})
    bind_env = os.environ.get("FUSION_AUTHOR_BIND", "").strip() in ("1", "true", "yes")
    bind = bind_env or bool(author.get("bind_to_publication"))
    if not bind or not ident.get("person_bound"):
        return {
            "legal_name": "",
            "publication_name": "",
            "academia_handle": "",
            "bound": False,
            "display": "Operator",
        }
    legal = (author.get("legal_name") or "").strip()
    pub = (author.get("publication_name") or legal).strip()
    return {
        "legal_name": legal,
        "publication_name": pub,
        "academia_handle": (author.get("academia_handle") or "").strip(),
        "bound": True,
        "display": pub or "Operator",
    }


def public_operator_view() -> dict[str, Any]:
    """Safe view for logs, mesh, GCS, dissertation *structure* appendices."""
    ident = load_identity()
    seal: dict[str, Any] = {}
    try:
        from fusion_hero_os.core.god_layer_seal import public_status as seal_status

        seal = seal_status()
    except Exception:
        seal = {}
    return {
        "role": ROLE_OPERATOR,
        "operator_id": ident.get("operator_id") or "OP_LOCAL",
        "display_handle": ident.get("display_handle") or "operator",
        "person_bound": bool(ident.get("person_bound")),
        "membrane": MEMBRANE,
        "platform_version": PLATFORM,
        "routing_mode": (ident.get("routing") or {}).get("mode")
        or seal.get("routing_mode")
        or "operator",
        "god_layer_sealed": bool(seal.get("sealed")),
        "write_rights": seal.get("write_rights") or "open",
        "read_rights": seal.get("read_rights") or "full",
        # never include legal_name here
    }


def is_person_bound() -> bool:
    return bool(load_identity().get("person_bound"))


def extract_status() -> dict[str, Any]:
    """Status of the Urban/person extraction (role vs person split)."""
    ident = load_identity()
    pub = author_for_publication()
    return {
        "ok": True,
        "membrane": MEMBRANE,
        "platform_version": PLATFORM,
        "role": ROLE_OPERATOR,
        "operator_id": ident.get("operator_id"),
        "person_bound_in_vault": bool(ident.get("person_bound")),
        "author_bind_active": bool(pub.get("bound")),
        "vault_path": str(VAULT_PATH),
        "vault_exists": VAULT_PATH.is_file(),
        "public_view": public_operator_view(),
        "rule": (
            "Operative code addresses role=operator only. "
            "Legal/publication person lives only in operator-local vault "
            "or dissertation publication surfaces — extracted from runtime role."
        ),
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Operator identity membrane")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--init-vault", action="store_true", help="write empty local vault")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--public", action="store_true")
    args = ap.parse_args()
    if args.init_vault:
        p = save_identity_template(force=args.force)
        print(json.dumps({"ok": True, "vault": str(p)}, indent=2))
        return 0
    if args.public:
        print(json.dumps(public_operator_view(), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(extract_status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
