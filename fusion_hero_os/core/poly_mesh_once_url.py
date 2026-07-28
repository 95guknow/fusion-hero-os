"""Poly-Mesh once-URLs + encrypted mesh-IP DNS labels (heroic naming).

- **Encrypted mesh IP**: URL-safe token wrapping Tailscale 100.x (+ optional port)
  under a local secret (not public PKI — mesh-scoped obfuscation + integrity).
- **Once-URL**: single-use, TTL-bound redirect/proxy handle with a heroic name.

State: ``~/.fusion/poly_mesh_once/``
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Heroic name pool (Fusion / Senfkorn / Hypermoderne lexicon)
HEROIC_NAMES = (
    "sisyphos",
    "banach",
    "hyperraum",
    "senfkorn",
    "coal-canary",
    "prometheus",
    "daimon",
    "eudaimonia",
    "masterseed",
    "horkrux",
    "alte-frau",
    "omega-layer",
    "fixpunkt",
    "kontraktion",
    "poly-mesh",
    "heroic-core",
    "ascension",
    "phantom-node",
    "mesh-anchor",
    "exit-phoenix",
)

DEFAULT_TTL_SEC = 900  # 15 min
DEFAULT_PORT = 42069

# The real MagicDNS host is operator-local infrastructure, never hardcoded in
# public source. At runtime the live Tailscale DNSName is read from `tailscale
# status` (see below); this env-driven constant is only the fallback/default and
# defaults to a neutral placeholder so the public skeleton carries no real node.
MESH_HOST = os.environ.get("FUSION_MESH_HOST", "your-node.example.ts.net")


def _state_dir() -> Path:
    d = Path.home() / ".fusion" / "poly_mesh_once"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _secret_path() -> Path:
    return _state_dir() / "mesh_dns_secret.bin"


def _ledger_path() -> Path:
    return _state_dir() / "once_ledger.json"


def get_or_create_secret() -> bytes:
    p = _secret_path()
    if p.exists():
        return p.read_bytes()
    key = secrets.token_bytes(32)
    p.write_bytes(key)
    try:
        p.chmod(0o600)
    except OSError:
        pass
    return key


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def encrypt_mesh_ip(ip: str, port: int = DEFAULT_PORT, secret: bytes | None = None) -> str:
    """Pack mesh IP+port into authenticated encrypted blob (XOR stream + HMAC)."""
    secret = secret or get_or_create_secret()
    payload = f"{ip}:{int(port)}".encode()
    nonce = secrets.token_bytes(12)
    # stream key
    stream = hashlib.sha256(secret + nonce).digest()
    while len(stream) < len(payload):
        stream += hashlib.sha256(stream).digest()
    cipher = bytes(a ^ b for a, b in zip(payload, stream[: len(payload)]))
    mac = hmac.new(secret, nonce + cipher, hashlib.sha256).digest()[:16]
    return _b64url(nonce + mac + cipher)


def decrypt_mesh_ip(token: str, secret: bytes | None = None) -> tuple[str, int]:
    secret = secret or get_or_create_secret()
    raw = _b64url_decode(token)
    if len(raw) < 12 + 16 + 1:
        raise ValueError("token too short")
    nonce, mac, cipher = raw[:12], raw[12:28], raw[28:]
    expect = hmac.new(secret, nonce + cipher, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(mac, expect):
        raise ValueError("invalid token mac")
    stream = hashlib.sha256(secret + nonce).digest()
    while len(stream) < len(cipher):
        stream += hashlib.sha256(stream).digest()
    plain = bytes(a ^ b for a, b in zip(cipher, stream[: len(cipher)])).decode("utf-8")
    ip, _, port_s = plain.partition(":")
    return ip, int(port_s or DEFAULT_PORT)


def heroic_dns_label(name: str, enc_token: str) -> str:
    """Display / local DNS-style label: heroic-name.polymesh.<enc> (not public ICANN DNS)."""
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "hero"
    # shorten enc for label readability (full token still in once path)
    short = enc_token[:20]
    return f"{slug}.polymesh.{short}.mesh.local"


def pick_heroic_name(rng: secrets.SystemRandom | None = None) -> str:
    r = rng or secrets.SystemRandom()
    base = r.choice(HEROIC_NAMES)
    # rare compound
    if r.random() < 0.35:
        base = f"{base}-{r.choice(('omega', 'prime', 'nova', 'apex', 'vigil'))}"
    return base


def _load_ledger() -> dict[str, Any]:
    p = _ledger_path()
    if not p.exists():
        return {"tokens": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"tokens": {}}


def _save_ledger(data: dict[str, Any]) -> None:
    _ledger_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


@dataclass
class OnceUrl:
    name: str
    token: str
    enc_ip: str
    dns_label: str
    path: str
    expires_at: float
    mesh_ip: str
    port: int
    public_base: str
    mesh_base: str

    @property
    def once_url(self) -> str:
        base = self.public_base.rstrip("/")
        return f"{base}{self.path}"

    @property
    def mesh_once_url(self) -> str:
        base = self.mesh_base.rstrip("/")
        return f"{base}{self.path}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "heroic_name": self.name,
            "once_url": self.once_url,
            "mesh_once_url": self.mesh_once_url,
            "path": self.path,
            "dns_label": self.dns_label,
            "encrypted_mesh_ip": self.enc_ip,
            "mesh_ip": self.mesh_ip,
            "port": self.port,
            "expires_at": self.expires_at,
            "expires_in_sec": max(0, int(self.expires_at - time.time())),
            "single_use": True,
            "ok": True,
        }


def mint_once_url(
    mesh_ip: str,
    port: int = DEFAULT_PORT,
    *,
    ttl_sec: int = DEFAULT_TTL_SEC,
    public_base: str = f"https://{MESH_HOST}",
    mesh_base: str = f"https://{MESH_HOST}",
    name: str | None = None,
    target_path: str = "/",
) -> OnceUrl:
    """Create a single-use heroic once-URL pointing at mesh service."""
    name = name or pick_heroic_name()
    enc = encrypt_mesh_ip(mesh_ip, port)
    once_id = secrets.token_urlsafe(18)
    path = f"/once/{name}/{once_id}"
    exp = time.time() + max(60, int(ttl_sec))
    ledger = _load_ledger()
    ledger.setdefault("tokens", {})[once_id] = {
        "name": name,
        "enc_ip": enc,
        "mesh_ip": mesh_ip,
        "port": port,
        "target_path": target_path,
        "expires_at": exp,
        "used": False,
        "created_at": time.time(),
    }
    _save_ledger(ledger)
    dns = heroic_dns_label(name, enc)
    return OnceUrl(
        name=name,
        token=once_id,
        enc_ip=enc,
        dns_label=dns,
        path=path,
        expires_at=exp,
        mesh_ip=mesh_ip,
        port=port,
        public_base=public_base,
        mesh_base=mesh_base,
    )


def redeem_once(once_id: str) -> dict[str, Any]:
    """Consume once-token; returns target or error. Single use."""
    ledger = _load_ledger()
    rec = (ledger.get("tokens") or {}).get(once_id)
    if not rec:
        return {"ok": False, "error": "unknown_or_expired_token"}
    if rec.get("used"):
        return {"ok": False, "error": "already_used"}
    if time.time() > float(rec.get("expires_at") or 0):
        return {"ok": False, "error": "expired"}
    rec["used"] = True
    rec["used_at"] = time.time()
    ledger["tokens"][once_id] = rec
    _save_ledger(ledger)
    return {
        "ok": True,
        "heroic_name": rec.get("name"),
        "mesh_ip": rec.get("mesh_ip"),
        "port": rec.get("port"),
        "target_path": rec.get("target_path") or "/",
        "enc_ip": rec.get("enc_ip"),
        "redirect": f"http://{rec.get('mesh_ip')}:{rec.get('port')}{rec.get('target_path') or '/'}",
    }


def mint_from_tailscale(
    port: int = DEFAULT_PORT,
    **kwargs: Any,
) -> dict[str, Any]:
    """Read local Tailscale IPv4 and mint once-URL."""
    import json
    import shutil
    import subprocess

    exe = r"C:\Program Files\Tailscale\tailscale.exe"
    if not Path(exe).is_file():
        exe = shutil.which("tailscale") or "tailscale"
    raw = subprocess.check_output([exe, "status", "--json"], timeout=12)
    data = json.loads(raw.decode("utf-8", errors="replace"))
    self = data.get("Self") or {}
    ips = self.get("TailscaleIPs") or []
    ip4 = next((i for i in ips if str(i).startswith("100.")), None) or (ips[0] if ips else None)
    if not ip4:
        raise RuntimeError("no Tailscale mesh IP")
    dns = (self.get("DNSName") or f"{MESH_HOST}.").rstrip(".")
    public_base = kwargs.pop("public_base", f"https://{dns}")
    mesh_base = kwargs.pop("mesh_base", f"https://{dns}")
    once = mint_once_url(
        str(ip4),
        port,
        public_base=public_base,
        mesh_base=mesh_base,
        **kwargs,
    )
    d = once.to_dict()
    d["magic_dns"] = dns
    d["polymesh_dns"] = once.dns_label
    d["note"] = (
        "polymesh_dns is a mesh-local label (encrypted IP handle), not public ICANN DNS. "
        "once_url is single-use; open before TTL."
    )
    return d
