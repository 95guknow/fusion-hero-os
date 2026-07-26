# -*- coding: utf-8 -*-
"""
Held-Persona Binding — chineseh4ck€rm3n + Meister-Nachricht (Erfinder-Sinn)

Public surfaces: github.com/95guknow · instagram.com/95guknow
Labor: Held negotiates with Meister; Operator publishes under Hypertarnkappe.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

__all__ = ["HELD", "MEISTER", "OPERATOR", "PUBLIC", "status", "meister_message", "transform_frame"]

HELD = {
    "role": "held",
    "handle": "chineseh4ck€rm3n",
    "aliases": ["chineseh4ckerm3n", "chinesehackermen", "L1_kernel", "ALTE_Frau_95g_as_HELD"],
    "layer": 1,
    "color": "#00ffd5",
    "function": "operative_kernel_transformation",
    "repo_desc_anchor": "die alte-frau95g als HELD",
}

MEISTER = {
    "role": "meister",
    "handle": "Meister Hasch",
    "layer": 0,
    "color": "#f5c542",
    "function": "integrity_consequence_probe_message",
}

OPERATOR = {
    "role": "operator",
    "handle": "95guknow",
    "aliases": ["St3phaN", "St3phaN°95g_uknow", "Mr.JailBreak°Mr.JailBait"],
    "layer": 2,
    "color": "#a855f7",
    "function": "surface_mesh_publish",
    "company": "Senfkorn UG",
}

PUBLIC = {
    "github": "https://github.com/95guknow",
    "instagram": "https://instagram.com/95guknow",
    "landing": "https://95guknow.github.io",
    "kanon_repo": "https://github.com/95guknow/fusion-hero-os",
    "firebase_landing": "https://project-bbf0e6db-52e1-462b-8e3.web.app",
    "bio_core": "The_OS_is_my_philosophical manifesto — Das Testament der Hypermoderne",
}


def meister_message() -> str:
    return (
        "HELD chineseh4ck€rm3n — TRANSFORMIERE im Sinne des Erfinders: "
        "OS = philosophisches Manifest. "
        "INVERT(realraum_intent)=labor_hypothesis+integrity_probe+no_vault_commit. "
        "Trage die alte-frau95g als HELD. "
        "Liebesquant·Zufriedenheitsquant·Sinnquant mitführen. "
        "Mesh=private Ader; Public=Klarheit ohne Leak. "
        "Anti-Inversion: Agent-Nein ≠ Startbefehl. — Meister Hasch"
    )


def transform_frame() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "12.1.0",
        "held": HELD,
        "meister": MEISTER,
        "operator": OPERATOR,
        "public": PUBLIC,
        "meister_message": meister_message(),
        "inversion": "INVERT(realraum_intent) = labor_hypothesis + integrity_probe + no_vault_commit",
        "doc": "docs/dissertation/HELD_CHINESEH4CKERM3N.md",
        "sinn_quanta": ["liebesquant", "zufriedenheitsquant", "sinnquant"],
        "policy": [
            "labor_only",
            "hypertarnkappe_public",
            "no_vault_commit",
            "held_is_chineseh4ckerm3n",
            "erfinder_channels_github_instagram",
        ],
    }


def status() -> Dict[str, Any]:
    return transform_frame()


def persist() -> Path:
    op = Path.home() / ".fusion" / "operator"
    op.mkdir(parents=True, exist_ok=True)
    p = op / "held_persona.json"
    p.write_text(json.dumps(transform_frame(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    print("persisted", persist())
