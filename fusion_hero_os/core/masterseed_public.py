"""
Public MasterSeed presentation — unique, unambiguous display IDs.

Private material never appears here. See masterseed_vault for GPG+QUBO
local shards split by module/function.

Geltung: Spezifikation (display) · public ID uniqueness = Satz under fixed fields.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from typing import Any

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed

__all__ = [
    "PublicMasterSeedView",
    "public_view",
    "display_id_from_fingerprint",
    "parse_display_id",
    "assert_unique_display",
]

# Crockford base32 (no I,L,O,U)
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _b32_crockford(data: bytes) -> str:
    # simple big-endian base32 crockford
    n = int.from_bytes(data, "big")
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 32)
        out.append(_CROCKFORD[r])
    return "".join(reversed(out))


def _check4(fp_hex: str) -> str:
    h = hashlib.sha256(fp_hex.encode("ascii")).hexdigest()[:4].upper()
    # map hex to crockford-ish alnum
    return h


@dataclass(frozen=True)
class PublicMasterSeedView:
    """What may be shown publicly — unique and unambiguous."""

    display_id: str
    public_fingerprint: str
    platform_version: str
    criticality_target_display: str
    integrity_ok: bool
    state_hash_prefix: str  # first 12 hex of state_hash only
    presented_at: str
    policy: str = "public_unique_private_obfuscated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"{self.display_id}  fp={self.public_fingerprint[:16]}…  "
            f"integrity={'OK' if self.integrity_ok else 'FAIL'}"
        )


def _platform_version_default() -> str:
    """Read root VERSION when present; fallback 12.0.0 (current kanon)."""
    try:
        from pathlib import Path

        vf = Path(__file__).resolve().parents[2] / "VERSION"
        if vf.is_file():
            v = vf.read_text(encoding="utf-8").strip()
            if v:
                return v
    except Exception:
        pass
    return "12.0.0"


def public_fingerprint(
    seed: MasterSeed | None = None, platform_version: str | None = None
) -> str:
    """Fingerprint over public-safe fields only (not private vault material)."""
    seed = seed or MasterSeed()
    platform_version = platform_version or _platform_version_default()
    payload = {
        "genesis_hash": seed.genesis_hash,
        "criticality_target": seed.criticality_target,
        "strict_contraction_enforced": seed.strict_contraction_enforced,
        "platform_version": platform_version,
        "kind": "public_masterseed_v1",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def display_id_from_fingerprint(fp_hex: str, major: str = "12") -> str:
    """MS-PUB-v{major}-{short8}-{check4} — unique under fingerprint collision resistance."""
    raw = bytes.fromhex(fp_hex[:10])  # 5 bytes
    short = _b32_crockford(raw).upper()
    # pad/truncate to 8
    short = (short + "00000000")[:8]
    check = _check4(fp_hex)
    return f"MS-PUB-v{major}-{short}-{check}"


def parse_display_id(display_id: str) -> dict[str, str] | None:
    m = re.fullmatch(
        r"MS-PUB-v(\d+)-([0-9A-Z]{8})-([0-9A-F]{4})",
        (display_id or "").strip(),
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return {
        "major": m.group(1),
        "short8": m.group(2).upper(),
        "check4": m.group(3).upper(),
    }


def public_view(
    seed: MasterSeed | None = None,
    *,
    platform_version: str | None = None,
) -> PublicMasterSeedView:
    seed = seed or MasterSeed()
    platform_version = platform_version or _platform_version_default()
    fp = public_fingerprint(seed, platform_version)
    major = platform_version.split(".")[0]
    did = display_id_from_fingerprint(fp, major=major)
    sh = seed.state_hash()
    return PublicMasterSeedView(
        display_id=did,
        public_fingerprint=fp,
        platform_version=platform_version,
        criticality_target_display=f"{seed.criticality_target:.2f} (model)",
        integrity_ok=seed.verify_integrity(sh),
        state_hash_prefix=sh[:12],
        presented_at=datetime.now(UTC).isoformat(),
    )


def assert_unique_display(views: list) -> bool:
    """True if all display_ids and fingerprints are pairwise unique."""
    ids = [v.display_id if hasattr(v, "display_id") else v["display_id"] for v in views]
    fps = [
        v.public_fingerprint if hasattr(v, "public_fingerprint") else v["public_fingerprint"]
        for v in views
    ]
    return len(ids) == len(set(ids)) and len(fps) == len(set(fps))
