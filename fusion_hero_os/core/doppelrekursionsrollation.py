"""Internal algorithm source for **mugen-tsuky.chan** (clear protocol elsewhere).

Prefer public API: ``fusion_hero_os.core.mugen_tsuky_chan``.
Obfuscated body: ``fusion_hero_os.core._mtc_obf``.
Spec: ``protocols/mugen_tsuky_chan.yaml``.

This module remains as readable source for audits; runtime path uses mtc facade.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import time
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

from fusion_hero_os.ports import PORT_BASE


# ---------------------------------------------------------------------------
# Alternate PRNG: PCG64 XSH-RR (NOT the SHA256 stream used by once_url)
# ---------------------------------------------------------------------------
class PCG64:
    """Minimal PCG-XSH-RR 64-bit PRNG (O'Neill) — independent of SHA streams."""

    __slots__ = ("_state", "_inc")

    def __init__(self, seed: int, seq: int = 0xDA3E39CB94B95BDB) -> None:
        self._state = 0
        self._inc = ((seq << 1) | 1) & ((1 << 64) - 1)
        self._step(seed + self._inc)
        self._step(0)

    def _step(self, delta: int = 0) -> None:
        self._state = (self._state + (delta & ((1 << 64) - 1))) & ((1 << 64) - 1)
        old = self._state
        self._state = (old * 6364136223846793005 + self._inc) & ((1 << 64) - 1)

    def next_u64(self) -> int:
        old = self._state
        self._state = (old * 6364136223846793005 + self._inc) & ((1 << 64) - 1)
        xorshifted = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rot = (old >> 59) & 0x1F
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF

    def fill(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            out += struct.pack(">I", self.next_u64())
        return bytes(out[:n])


def _rotl_bytes(data: bytes, bits: int) -> bytes:
    if not data:
        return data
    bits %= len(data) * 8
    byte_shift, bit_shift = divmod(bits, 8)
    rotated = data[-byte_shift:] + data[:-byte_shift] if byte_shift else data
    if bit_shift == 0:
        return rotated
    out = bytearray(len(rotated))
    for i, b in enumerate(rotated):
        prev = rotated[i - 1]
        out[i] = ((b << bit_shift) | (prev >> (8 - bit_shift))) & 0xFF
    return bytes(out)


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def polymesh_day_seed(day_utc: str, mesh_ip: str = "100.64.104.58", port: int = PORT_BASE) -> bytes:
    """Deterministic seed material for a UTC calendar day."""
    material = f"polymesh|v10|day={day_utc}|ip={mesh_ip}|port={port}|tier=L1-L2|kanon=v10.0.0"
    # fold mesh secret if present
    secret_path = Path.home() / ".fusion" / "poly_mesh_once" / "mesh_dns_secret.bin"
    if secret_path.exists():
        material_b = material.encode("utf-8") + b"|" + secret_path.read_bytes()
    else:
        material_b = material.encode("utf-8")
    return _sha256(material_b)


def polymesh_hash_number_1(day_utc: str, mesh_ip: str = "100.64.104.58") -> str:
    """Hash #1 of the day (index 1): first roll of day seed (not the raw seed).

    Definition:
      H0 = day_seed
      H1 = SHA256( H0 || rotl(H0, 13) || day_utc || \"#1\" )   ← nummer 1
    """
    h0 = polymesh_day_seed(day_utc, mesh_ip)
    h1 = _sha256(h0 + _rotl_bytes(h0, 13) + f"{day_utc}#1".encode())
    return h1.hex()


def doppelrekursionsrollation(
    seed_hex: str,
    *,
    depth_a: int = 8,
    depth_b: int = 8,
    rot_a: int = 7,
    rot_b: int = 11,
    prng_seed: int | None = None,
) -> dict[str, Any]:
    """Double recursive rollation.

    Recursion A (SHA path):  a_{n+1} = SHA256( a_n || rotl(a_n, rot_a) || n )
    Recursion B (PRNG path): b_{n+1} = SHA512( b_n || PCG64.fill(32) || rotl(b_n, rot_b) )

    Cross fold:  final = SHA256( a_final || b_final || rotl(a_final XOR b_final[:32], 17) )
    """
    a = bytes.fromhex(seed_hex)
    if len(a) != 32:
        a = _sha256(a)

    chain_a: list[str] = [a.hex()]
    for n in range(depth_a):
        a = _sha256(a + _rotl_bytes(a, rot_a + n) + struct.pack(">I", n))
        chain_a.append(a.hex())

    # PRNG seed distinct system: mix seed with golden ratio constant (not SHA stream)
    if prng_seed is None:
        prng_seed = int.from_bytes(a[:8], "big") ^ 0x9E3779B97F4A7C15
    pcg = PCG64(prng_seed & ((1 << 64) - 1), seq=0xC0FFEE50C0FFEE51 ^ 0xDEADBEEF)

    b = _sha512(a + pcg.fill(32) + b"PRNG-LAYER-B")
    chain_b: list[str] = [b.hex()]
    for n in range(depth_b):
        pad = pcg.fill(32)
        b = _sha512(b + pad + _rotl_bytes(b[:32], rot_b + n) + struct.pack(">I", n))
        chain_b.append(b.hex())

    xor_ab = bytes(x ^ y for x, y in zip(a, b[:32]))
    final = _sha256(a + b + _rotl_bytes(xor_ab, 17) + b"DOPPELREKURSIONSROLLATION")

    return {
        "seed_hex": seed_hex,
        "depth_a": depth_a,
        "depth_b": depth_b,
        "rot_a": rot_a,
        "rot_b": rot_b,
        "prng": "PCG64-XSH-RR",
        "prng_seed": prng_seed,
        "chain_a_tail": chain_a[-1],
        "chain_b_tail": chain_b[-1],
        "chain_a_len": len(chain_a),
        "chain_b_len": len(chain_b),
        "final_sha256": final.hex(),
        "final_sha256_short": final.hex()[:16],
    }


def gpg_hash_payload(
    payload: bytes,
    *,
    algo: str = "SHA512",
) -> dict[str, Any]:
    """GPG-mediated digest using ``gpg --print-md`` (independent hash path).

    Falls back to pure hashlib if gpg unavailable.
    """
    algo = algo.upper().replace("-", "")
    try:
        # gpg --print-md SHA512 -
        proc = subprocess.run(
            ["gpg", "--print-md", algo],
            input=payload,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            # format: "SHA512(stdin)= AB CD EF ..."
            text = proc.stdout.decode("utf-8", errors="replace").strip()
            hexpart = text.split("=")[-1].replace(" ", "").replace("\n", "").lower()
            if all(c in "0123456789abcdef" for c in hexpart) and len(hexpart) >= 32:
                return {
                    "ok": True,
                    "backend": "gpg",
                    "algo": algo,
                    "digest_hex": hexpart,
                    "raw_line": text[:200],
                }
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[:200]
        raise RuntimeError(err or f"gpg exit {proc.returncode}")
    except Exception as exc:  # noqa: BLE001
        # fallback hashlib
        h = hashlib.new("sha512" if algo == "SHA512" else "sha384")
        h.update(payload)
        return {
            "ok": True,
            "backend": "hashlib_fallback",
            "algo": algo,
            "digest_hex": h.hexdigest(),
            "error": str(exc)[:160],
        }


def gpg_hash_with_prng(
    seed_hex: str,
    *,
    nbytes: int = 64,
    algo: str = "SHA512",
) -> dict[str, Any]:
    """Feed GPG a buffer expanded by PCG64 (different PRNG system than SHA-stream)."""
    seed_int = int(seed_hex[:16], 16) if seed_hex else 1
    # Second PRNG domain: different stream constant than doppel layer B
    pcg = PCG64(seed_int ^ 0xA5A5A5A5A5A5A5A5, seq=0x600DC0DE500D500D)
    buf = pcg.fill(nbytes) + bytes.fromhex(seed_hex) + b"|GPG-PRNG-DOMAIN"
    gh = gpg_hash_payload(buf, algo=algo)
    gh["prng"] = "PCG64-XSH-RR"
    gh["prng_domain"] = "GPG-PRNG-DOMAIN"
    gh["payload_len"] = len(buf)
    return gh


def run_day_rollation(
    day_utc: str | None = None,
    *,
    mesh_ip: str = "100.64.104.58",
    depth: int = 8,
) -> dict[str, Any]:
    """Full pipeline: day hash #1 → doppel rollation → GPG+PRNG hash."""
    if not day_utc:
        # "letzten tages" = yesterday UTC
        day_utc = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

    h1 = polymesh_hash_number_1(day_utc, mesh_ip)
    doppel = doppelrekursionsrollation(h1, depth_a=depth, depth_b=depth)
    gpg = gpg_hash_with_prng(doppel["final_sha256"], algo="SHA512")

    # Cross seal
    seal = _sha256(
        bytes.fromhex(h1)
        + bytes.fromhex(doppel["final_sha256"])
        + bytes.fromhex(gpg["digest_hex"][:64])
        + f"|seal|{day_utc}|42069".encode()
    )

    out = {
        "ok": True,
        "operation": "doppelrekursionsrollation",
        "day_utc": day_utc,
        "mesh_ip": mesh_ip,
        "port_base": PORT_BASE,
        "polymesh_hash_nummer_1": h1,
        "doppel": doppel,
        "gpg_prng": gpg,
        "seal_sha256": seal.hex(),
        "banner": (
            f"DOPPELREKURSIONSROLLATION | day={day_utc} | "
            f"H1={h1[:16]}… | final={doppel['final_sha256_short']}… | "
            f"gpg={gpg['digest_hex'][:16]}… | seal={seal.hex()[:16]}…"
        ),
        "ts": time.time(),
        "ts_iso": datetime.now(UTC).isoformat(),
    }

    # Persist day chain
    out_dir = Path.home() / ".fusion" / "poly_mesh_day_hashes"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{day_utc}_rollation.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> None:
    import sys

    day = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_day_rollation(day)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
