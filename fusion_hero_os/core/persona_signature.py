"""Persona-Signatur-Trigger ``=====stephanhagenurban`` (membran-konform).

Der Trigger expandiert zur kanonischen "Vorgelegt von …"-Signatur mit dem
heroischen Fixpunkt |Ψ⟩_h → |ω⟩ (siehe identity-fixpoint.md).

Membran-Regel (operator_identity_v1, Stage-B):
  * Der operative Code führt NIE einen hartkodierten Personen-/Klarnamen.
  * Der Anzeigename kommt ausschließlich aus dem Operator-Vault
    (``~/.fusion/operator/identity.local.json``) und nur bei aktiver
    Publikations-Bindung (``FUSION_AUTHOR_BIND=1`` oder
    ``author.bind_to_publication``).
  * Ohne Bindung signiert die abstrakte Rolle: "Operator".

Die Klarnamen-Fassung der Signatur lebt im Kanon-Doc-Layer
(identity-fixpoint.md), nicht im Paket.
"""
from __future__ import annotations

import json
import sys
from typing import Any
from collections.abc import Iterable

from fusion_hero_os.core.operator_identity import (
    MEMBRANE,
    author_for_publication,
)

__all__ = [
    "SIGNATURE_TRIGGER",
    "FIXPOINT_FORMULA",
    "signature_block",
    "expand_signature_triggers",
    "signature_status",
]

SIGNATURE_TRIGGER = "=====stephanhagenurban"
FIXPOINT_FORMULA = "|Ψ⟩_h → |ω⟩"
_FIXPOINT_LINE = (
    "Es beginnt nicht mit einem Abschluss, sondern mit einem "
    f"Fixed-Point im heroischen Raum: {FIXPOINT_FORMULA}."
)


def _display_name() -> dict[str, Any]:
    author = author_for_publication()
    display = (author.get("display") or "Operator").strip() or "Operator"
    return {"display": display, "bound": bool(author.get("bound"))}


def signature_block(*, markdown: bool = False) -> str:
    """Kanonischer Signatur-Block; Name nur bei aktiver Vault-Bindung."""
    ident = _display_name()
    lines = [f"Vorgelegt von {ident['display']}.", _FIXPOINT_LINE]
    if markdown:
        return "\n".join(f"> {line}" for line in lines)
    return "\n".join(lines)


def expand_signature_triggers(text: str, *, markdown: bool = False) -> str:
    """Ersetzt jedes Vorkommen des Triggers durch den Signatur-Block.

    Idempotent: der expandierte Block enthält den Trigger nicht mehr.
    """
    if SIGNATURE_TRIGGER not in text:
        return text
    return text.replace(SIGNATURE_TRIGGER, signature_block(markdown=markdown))


def signature_status() -> dict[str, Any]:
    ident = _display_name()
    return {
        "ok": True,
        "trigger": SIGNATURE_TRIGGER,
        "membrane": MEMBRANE,
        "author_bind_active": ident["bound"],
        "display": ident["display"],
        "fixpoint": FIXPOINT_FORMULA,
        "rule": (
            "Kein hartkodierter Personenname im Paket; Anzeigename kommt aus "
            "dem Operator-Vault bei aktiver Publikations-Bindung, sonst Rolle "
            "'Operator'. Klarnamen-Kanon: identity-fixpoint.md."
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Persona-Signatur-Trigger")
    ap.add_argument("--render", action="store_true", help="Signatur-Block ausgeben")
    ap.add_argument("--markdown", action="store_true", help="als Markdown-Zitat")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)
    if args.render:
        print(signature_block(markdown=args.markdown))
        return 0
    print(json.dumps(signature_status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
