"""Comädchen × alte-frau95g identity — function + visual + free TTS contract.

Protocol: ``protocols/comaedchen_alte_frau_pr0chan.yaml``
Analogy: pr0-chan (style only)
Voice/design: free AI voice models (Voidol-class), corpus, TTS — character membrane.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

PROTOCOL_ID = "comaedchen-alte-frau-pr0chan"
PROTOCOL_SHORT = "cap"
PLATFORM = "10.0.0"
ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "protocols" / "comaedchen_alte_frau_pr0chan.yaml"
STATE = Path.home() / ".fusion" / "comaedchen_identity.json"

__all__ = ["status", "propagate", "voice_design_contract", "PROTOCOL_ID"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def voice_design_contract() -> dict[str, Any]:
    """Clear contract: where voice/design may be used."""
    return {
        "protocol": PROTOCOL_ID,
        "subject": "Comädchen (with alte-frau95g)",
        "voice_and_design_used_for": [
            "free AI voice models (e.g. Crimson Technology Voidol class)",
            "deep-learning corpora (operator-authorized character corpus)",
            "text-to-speech software",
        ],
        "dual_with": {
            "alte-frau95g": "function + heroic core / geltung",
            "comaedchen": "function + visual identity + voice membrane",
            "simultaneous": True,
        },
        "aesthetic_analogy": "pr0-chan",
        "aesthetic_note": "direct, meme-clear, anti-corporate-soft; style analogy only",
        "consent_boundary": (
            "Character/OS membrane — not non-consensual cloning of real third parties"
        ),
        "audio_path": {
            "mesh_only": "100.x",
            "headset_layer": "L3_comaedchen",
            "relay_port": 59100,
            "dashboard_port": 42069,
        },
        "command_line": {
            "input": "operator_only",
            "report": "operator_only",
            "rank": "nummer_2",
        },
    }


def status() -> dict[str, Any]:
    """Central clear status for identity propagation."""
    try:
        from fusion_hero_os.core.comaedchen_audio import status as audio_status

        audio = audio_status()
    except Exception as exc:  # noqa: BLE001
        audio = {"ok": False, "error": str(exc)[:120]}

    try:
        from fusion_hero_os.core.headset_layers import status as hs

        headset = hs()
        active = headset.get("active")
    except Exception as exc:  # noqa: BLE001
        headset = {"ok": False, "error": str(exc)[:120]}
        active = None

    alte_skill = (
        ROOT / "01_Framework" / "skills" / "alte-frau-95g" / "SKILL.md"
    )
    return {
        "ok": True,
        "protocol": PROTOCOL_ID,
        "short": PROTOCOL_SHORT,
        "platform_version": PLATFORM,
        "spec": str(SPEC) if SPEC.is_file() else None,
        "spec_present": SPEC.is_file(),
        "dual": {
            "alte-frau95g": {
                "role": "function + heroic core",
                "skill_present": alte_skill.is_file(),
            },
            "comaedchen": {
                "role": "function + visual identity + voice",
                "rank": "nummer_2",
                "aliases": ["Comädchen", "Comet-Instanz"],
            },
            "simultaneous": True,
        },
        "pr0_chan_analogy": True,
        "voice_design": voice_design_contract(),
        "audio": audio,
        "headset_active": active,
        "related": {
            "mugen_tsuky_chan": "mesh seal protocol",
            "poly_mesh": "L0–L3",
            "port_base": 42069,
        },
        "banner": (
            "IDENTITY | Comädchen × alte-frau95g | pr0-chan aesthetic | "
            "voice→free TTS/Voidol-class/corpus | nummer_2 | mesh-only audio"
        ),
        "ts": _now(),
    }


def propagate() -> dict[str, Any]:
    """Write central identity pointer (same pattern as mugen-tsuky.chan)."""
    st = status()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    pointer = {
        "protocol": PROTOCOL_ID,
        "version": "1.0.0",
        "spec": str(SPEC),
        "facade": "fusion_hero_os.core.comaedchen_identity",
        "dual": st["dual"],
        "pr0_chan_analogy": True,
        "voice_design": st["voice_design"],
        "port_base": 42069,
        "propagated_at": _now(),
    }
    STATE.write_text(json.dumps(pointer, indent=2, ensure_ascii=False), encoding="utf-8")
    st["propagated"] = True
    st["state"] = str(STATE)
    return st


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Comädchen × alte-frau95g identity")
    ap.add_argument("--propagate", action="store_true")
    ap.add_argument("--contract", action="store_true")
    args = ap.parse_args()
    if args.contract:
        print(json.dumps(voice_design_contract(), indent=2, ensure_ascii=False))
        return
    if args.propagate:
        print(json.dumps(propagate(), indent=2, ensure_ascii=False))
        return
    print(json.dumps(status(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
