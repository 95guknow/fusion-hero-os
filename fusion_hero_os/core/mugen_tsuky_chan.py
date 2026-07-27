"""mugen-tsuky.chan — clear facade (propagation is central & readable).

Protocol id: **mugen-tsuky.chan** (short: ``mtc``)

Human truth:
  ``protocols/mugen_tsuky_chan.yaml``

Crypto body:
  obfuscated under ``fusion_hero_os.core._mtc_obf`` (label mugen-tsuky.chan)

Public language uses mtc_* field names only — not heroic lexicon / GPG-snapshot branding.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

PROTOCOL_ID = "mugen-tsuky.chan"
PROTOCOL_SHORT = "mtc"
PROTOCOL_VERSION = "1.0.0"
SPEC_PATH = Path(__file__).resolve().parents[2] / "protocols" / "mugen_tsuky_chan.yaml"


def _obf():
    from fusion_hero_os.core import _mtc_obf as obf

    return obf


def status() -> dict[str, Any]:
    """Central, clear protocol status (no obfuscation in the message)."""
    spec_ok = SPEC_PATH.is_file()
    try:
        _obf()  # nur Importbarkeit des obfuskierten Body prüfen
        body_ok = True
        body_err = None
    except Exception as exc:  # noqa: BLE001
        body_ok = False
        body_err = str(exc)[:160]
    state = Path.home() / ".fusion" / "mugen_tsuky_chan"
    return {
        "ok": body_ok and spec_ok,
        "protocol": PROTOCOL_ID,
        "short": PROTOCOL_SHORT,
        "version": PROTOCOL_VERSION,
        "spec": str(SPEC_PATH) if spec_ok else None,
        "spec_present": spec_ok,
        "body": "obfuscated",
        "body_module": "fusion_hero_os.core._mtc_obf",
        "body_ok": body_ok,
        "body_error": body_err,
        "port_base": 42069,
        "state_dir": str(state),
        "propagation": {
            "registry": "core.mugen_tsuky_chan",
            "api": [
                "/api/mesh/ops/mtc",
                "/api/mesh/ops/mtc/status",
                "/api/mesh/ops/mtc/roll",
            ],
            "yaml": "protocols/mugen_tsuky_chan.yaml",
        },
        "replaces_user_facing": [
            "heroic once-name branding",
            "gpg snapshot versiegelung branding",
        ],
        "note": "Read this status + YAML for operators. Crypto steps are not documented in cleartext.",
    }


def day_hash_1(day_utc: str | None = None, mesh_ip: str = "100.64.104.58") -> dict[str, Any]:
    """Poly-Mesh day hash #1 under mugen-tsuky.chan naming."""
    if not day_utc:
        day_utc = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    h1 = _obf().polymesh_hash_number_1(day_utc, mesh_ip)
    return {
        "ok": True,
        "protocol": PROTOCOL_ID,
        "day_utc": day_utc,
        "mtc_day_hash_1": h1,
        "mesh_ip": mesh_ip,
    }


def roll(day_utc: str | None = None, depth: int = 8, mesh_ip: str = "100.64.104.58") -> dict[str, Any]:
    """Run day rollation; map outputs to mtc_* clear fields."""
    if not day_utc:
        day_utc = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    raw = _obf().run_day_rollation(day_utc, mesh_ip=mesh_ip, depth=depth)

    # Map to mugen-tsuky.chan public vocabulary
    out = {
        "ok": True,
        "protocol": PROTOCOL_ID,
        "version": PROTOCOL_VERSION,
        "day_utc": raw.get("day_utc"),
        "mesh_ip": raw.get("mesh_ip"),
        "port_base": raw.get("port_base", 42069),
        "mtc_day_hash_1": raw.get("polymesh_hash_nummer_1"),
        "mtc_roll_final": (raw.get("doppel") or {}).get("final_sha256"),
        "mtc_roll_final_short": (raw.get("doppel") or {}).get("final_sha256_short"),
        "mtc_seal": raw.get("seal_sha256"),
        "mtc_secondary_digest": (raw.get("gpg_prng") or {}).get("digest_hex"),
        "mtc_secondary_backend": (raw.get("gpg_prng") or {}).get("backend"),
        "mtc_prng": (raw.get("doppel") or {}).get("prng"),
        "banner": (
            f"mugen-tsuky.chan | day={raw.get('day_utc')} | "
            f"H1={(raw.get('polymesh_hash_nummer_1') or '')[:16]}… | "
            f"roll={((raw.get('doppel') or {}).get('final_sha256_short') or '')}… | "
            f"seal={(raw.get('seal_sha256') or '')[:16]}…"
        ),
        "artifact": raw.get("artifact"),
        "ts_iso": raw.get("ts_iso"),
    }

    # Persist under mtc state dir (clear name)
    state = Path.home() / ".fusion" / "mugen_tsuky_chan" / "day"
    state.mkdir(parents=True, exist_ok=True)
    path = state / f"{out['day_utc']}_mtc.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    out["mtc_artifact"] = str(path)
    return out


def mint_once(port: int = 42069, ttl_sec: int = 900, name: str | None = None) -> dict[str, Any]:
    """Single-use mesh URL under mugen-tsuky.chan labels (not heroic lexicon)."""
    from fusion_hero_os.core.poly_mesh_once_url import mint_from_tailscale

    # Force protocol-scoped names
    mtc_names = (
        "mtc-alpha",
        "mtc-nova",
        "mtc-prime",
        "mtc-vigil",
        "mtc-apex",
        "mtc-node",
        "mtc-seal",
        "mtc-wave",
        "mtc-core",
        "mtc-mesh",
    )
    if not name:
        import secrets

        name = secrets.choice(mtc_names)

    d = mint_from_tailscale(port=port, ttl_sec=ttl_sec, name=name)
    return {
        "ok": True,
        "protocol": PROTOCOL_ID,
        "mtc_name": d.get("heroic_name"),
        "mtc_once_url": d.get("once_url"),
        "mtc_dns_label": d.get("polymesh_dns") or d.get("dns_label"),
        "mtc_encrypted_mesh_ip": d.get("encrypted_mesh_ip"),
        "mesh_ip": d.get("mesh_ip"),
        "port": d.get("port"),
        "expires_in_sec": d.get("expires_in_sec"),
        "single_use": True,
        "path": d.get("path"),
        "magic_dns": d.get("magic_dns"),
        "note": "mugen-tsuky.chan once-link; polymesh DNS label is mesh-local encrypted IP handle.",
    }


def propagate() -> dict[str, Any]:
    """Register protocol presence for central mesh ops (idempotent)."""
    st = status()
    # ensure state dirs
    for sub in ("", "day", "once"):
        (Path.home() / ".fusion" / "mugen_tsuky_chan" / sub).mkdir(parents=True, exist_ok=True)
    # write live pointer
    pointer = Path.home() / ".fusion" / "mugen_tsuky_chan" / "PROTOCOL.json"
    pointer.write_text(
        json.dumps(
            {
                "protocol": PROTOCOL_ID,
                "version": PROTOCOL_VERSION,
                "spec": str(SPEC_PATH),
                "facade": "fusion_hero_os.core.mugen_tsuky_chan",
                "body": "fusion_hero_os.core._mtc_obf",
                "port_base": 42069,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    st["propagated"] = True
    st["pointer"] = str(pointer)
    return st
