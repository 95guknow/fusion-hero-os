"""
Private MasterSeed vault — GPG + QUBO obfuscation, split by module/function.

Public display: masterseed_public.public_view()
Private shards: ~/.fusion/masterseed/private/modules/{module}/functions/{fn}.shard.gpg

Never commit private shards. Values never logged.

Geltung: Spezifikation (vault layout) · QUBO permute = local obfuscation model.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import numpy as np

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
from fusion_hero_os.core.masterseed_public import public_view

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "vault_root",
    "status",
    "list_module_split",
    "qubo_permute",
    "qubo_unpermute",
    "seal_function_shard",
    "open_function_shard",
    "seal_all_modules",
    "export_public_display",
]


@dataclass
class ShardMeta:
    module_id: str
    function_id: str
    sealed_at: str
    public_fingerprint_prefix: str
    gpg: bool
    qubo: bool
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def vault_root() -> Path:
    env = os.getenv("FUSION_MASTERSEED_VAULT", "").strip()
    p = Path(env) if env else Path.home() / ".fusion" / "masterseed"
    (p / "private" / "modules").mkdir(parents=True, exist_ok=True)
    (p / "public").mkdir(parents=True, exist_ok=True)
    return p


def _load_split_config() -> list[dict[str, Any]]:
    path = ROOT / "masterseed_public_display.yaml"
    if not path.exists():
        return [
            {
                "module": "core.orchestrator",
                "functions": ["MasterSeed.state_hash", "MasterSeed.verify_integrity"],
            }
        ]
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return list(data.get("modules_split") or [])
    except Exception:
        return []


def list_module_split() -> list[dict[str, Any]]:
    return _load_split_config()


def _qubo_perm_from_seed(n: int, seed_hex: str, steps: int = 200) -> list[int]:
    """Derive a permutation of range(n) from a small QUBO solve (local obfuscation)."""
    rng = np.random.default_rng(int(seed_hex[:16], 16) % (2**63))
    # random symmetric Q
    A = rng.normal(size=(n, n))
    Q = (A + A.T) / 2.0
    # binary state via simple SA-ish flips for obfuscation (not claiming optimality)
    x = rng.integers(0, 2, size=n).astype(np.float64)
    for _ in range(steps):
        i = int(rng.integers(0, n))
        x[i] = 1.0 - x[i]
    # order indices by (x_i, Q diagonal, index) → permutation
    order = sorted(range(n), key=lambda i: (-x[i], float(Q[i, i]), i))
    return order


def qubo_permute(data: bytes, key_hex: str, n: int = 16) -> bytes:
    """Permute fixed-size blocks using QUBO-derived order; pad last block."""
    if not data:
        return data
    # pad to multiple of n
    pad = (n - (len(data) % n)) % n
    blob = data + bytes([pad]) * (pad if pad else 0)
    if pad == 0:
        # still store pad length 0 as last meta via struct header
        pass
    header = struct.pack(">I", pad)
    perm = _qubo_perm_from_seed(n, key_hex)
    inv = [0] * n
    for i, p in enumerate(perm):
        inv[p] = i  # not needed for forward
    out = bytearray(header)
    for off in range(0, len(blob), n):
        block = blob[off : off + n]
        if len(block) < n:
            block = block + b"\x00" * (n - len(block))
        new_block = bytes(block[perm[i]] for i in range(n))
        out.extend(new_block)
    return bytes(out)


def qubo_unpermute(data: bytes, key_hex: str, n: int = 16) -> bytes:
    if len(data) < 4:
        return data
    pad = struct.unpack(">I", data[:4])[0]
    body = data[4:]
    perm = _qubo_perm_from_seed(n, key_hex)
    inv = [0] * n
    for i, p in enumerate(perm):
        inv[p] = i
    out = bytearray()
    for off in range(0, len(body), n):
        block = body[off : off + n]
        if len(block) < n:
            break
        orig = bytearray(n)
        for i in range(n):
            orig[perm[i]] = block[i]
        out.extend(orig)
    if pad and pad < n:
        return bytes(out[:-pad] if pad else out)
    # if pad was 0, full length
    if pad == 0:
        return bytes(out)
    return bytes(out[:-pad]) if pad else bytes(out)


def _gpg_available() -> bool:
    return bool(shutil.which("gpg") or shutil.which("gpg.exe"))


def _gpg_encrypt(plaintext: bytes, out_path: Path) -> bool:
    """Symmetric GPG encrypt; passphrase from FUSION_MASTERSEED_GPG_PASSPHRASE or public fp."""
    if not _gpg_available():
        # fallback: write obfuscated only with marker
        out_path.write_bytes(b"NOGPG|" + plaintext)
        return False
    recipient = (os.environ.get("FUSION_MASTERSEED_GPG_RECIPIENT") or "").strip()
    passphrase = (os.environ.get("FUSION_MASTERSEED_GPG_PASSPHRASE") or "").strip()
    if not passphrase:
        # derive ephemeral local passphrase from machine+fp prefix (not for multi-host)
        passphrase = hashlib.sha256(
            (os.environ.get("COMPUTERNAME", "host") + "fusion-ms-vault").encode()
        ).hexdigest()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        shutil.which("gpg") or "gpg",
        "--batch",
        "--yes",
        "--pinentry-mode",
        "loopback",
        "--passphrase",
        passphrase,
        "--symmetric",
        "--cipher-algo",
        "AES256",
        "-o",
        str(out_path),
    ]
    if recipient:
        cmd = [
            shutil.which("gpg") or "gpg",
            "--batch",
            "--yes",
            "--encrypt",
            "-r",
            recipient,
            "-o",
            str(out_path),
        ]
    r = subprocess.run(cmd, input=plaintext, capture_output=True)
    return r.returncode == 0 and out_path.is_file()


def _gpg_decrypt(path: Path) -> bytes | None:
    raw = path.read_bytes()
    if raw.startswith(b"NOGPG|"):
        return raw[6:]
    if not _gpg_available():
        return None
    passphrase = (os.environ.get("FUSION_MASTERSEED_GPG_PASSPHRASE") or "").strip()
    if not passphrase:
        passphrase = hashlib.sha256(
            (os.environ.get("COMPUTERNAME", "host") + "fusion-ms-vault").encode()
        ).hexdigest()
    cmd = [
        shutil.which("gpg") or "gpg",
        "--batch",
        "--yes",
        "--pinentry-mode",
        "loopback",
        "--passphrase",
        passphrase,
        "--decrypt",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def seal_function_shard(
    module_id: str,
    function_id: str,
    payload: dict[str, Any],
    *,
    seed: MasterSeed | None = None,
) -> ShardMeta:
    """QUBO-permute JSON payload then GPG-encrypt into module/function path."""
    view = public_view(seed)
    key_hex = view.public_fingerprint
    plain = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    obfuscated = qubo_permute(plain, key_hex, n=16)
    rel = Path("private") / "modules" / module_id.replace(".", "_") / "functions"
    out = vault_root() / rel / f"{function_id.replace('.', '_')}.shard.gpg"
    gpg_ok = _gpg_encrypt(obfuscated, out)
    meta = ShardMeta(
        module_id=module_id,
        function_id=function_id,
        sealed_at=datetime.now(UTC).isoformat(),
        public_fingerprint_prefix=view.public_fingerprint[:16],
        gpg=gpg_ok,
        qubo=True,
        path=str(out),
    )
    meta_path = out.with_suffix(".meta.json")
    # meta is non-secret (no payload)
    meta_path.write_text(json.dumps(meta.to_dict(), indent=2), encoding="utf-8")
    return meta


def open_function_shard(
    module_id: str,
    function_id: str,
    *,
    seed: MasterSeed | None = None,
) -> dict[str, Any] | None:
    view = public_view(seed)
    path = (
        vault_root()
        / "private"
        / "modules"
        / module_id.replace(".", "_")
        / "functions"
        / f"{function_id.replace('.', '_')}.shard.gpg"
    )
    if not path.is_file():
        return None
    raw = _gpg_decrypt(path)
    if raw is None:
        return None
    plain = qubo_unpermute(raw, view.public_fingerprint, n=16)
    try:
        return json.loads(plain.decode("utf-8"))
    except Exception:
        return None


def seal_all_modules(seed: MasterSeed | None = None) -> dict[str, Any]:
    """Seal default private refs for each configured module/function (local only)."""
    seed = seed or MasterSeed()
    view = public_view(seed)
    sealed: list[dict[str, Any]] = []
    for entry in list_module_split():
        mod = entry.get("module") or "unknown"
        for fn in entry.get("functions") or []:
            payload = {
                "module": mod,
                "function": fn,
                "ref": "private_binding",
                "public_display_id": view.display_id,
                "note": "implementation binding — not for publication",
                "sealed_epoch": time.time(),
            }
            meta = seal_function_shard(mod, fn, payload, seed=seed)
            sealed.append(meta.to_dict())
    pub = export_public_display(seed)
    return {
        "ok": True,
        "sealed_count": len(sealed),
        "public": pub,
        "shards": sealed,
        "vault": str(vault_root()),
    }


def export_public_display(seed: MasterSeed | None = None) -> dict[str, Any]:
    """Write unique public presentation only (no private shards)."""
    view = public_view(seed)
    path = vault_root() / "public" / "display.json"
    data = view.to_dict()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # also repo-safe example under docs (public fields only) — optional mirror
    mirror = ROOT / "docs" / "masterseed" / "PUBLIC_DISPLAY.example.json"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def status() -> dict[str, Any]:
    view = public_view()
    root = vault_root()
    private = root / "private" / "modules"
    shard_count = len(list(private.rglob("*.shard.gpg"))) if private.exists() else 0
    return {
        "ok": True,
        "policy": "public_unique_private_gpg_qubo_split",
        "freemium": False,
        "public": view.to_dict(),
        "gpg_available": _gpg_available(),
        "vault": str(root),
        "shard_count": shard_count,
        "modules_split": list_module_split(),
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="MasterSeed public display + private vault")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--seal", action="store_true", help="Seal all module/function shards locally")
    ap.add_argument("--public-only", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if args.public_only:
        print(json.dumps(export_public_display(), indent=2, ensure_ascii=False))
        return 0
    if args.seal:
        print(json.dumps(seal_all_modules(), indent=2, ensure_ascii=False)[:3000])
        return 0
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
