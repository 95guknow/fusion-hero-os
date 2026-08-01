"""Schwerkraftserver — dual multi-model control + lossless gate + poly-mesh git ingest.

Protocol coupling: **mugen-tsuky.chan** (clear status; obfuscated crypto body).

Flow:
  1) Dual control (A/B) verifies encryption round-trip is *vollständig verlustfrei*
  2) If both agree → execute
  3) Full git commit history is folded into poly-mesh under mugen-tsuky.chan seal

Gravity (Schwerkraft): each control instance contributes weight = confidence×accuracy;
consensus requires agreement on lossless boolean with total gravity ≥ threshold.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "mugen-tsuky.chan"
PORT_BASE = 42069


def _state_dir() -> Path:
    d = Path.home() / ".fusion" / "schwerkraftserver"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Lossless encryption probe (two independent checkers = dual control)
# ---------------------------------------------------------------------------
def control_a_lossless() -> dict[str, Any]:
    """Control A: poly_mesh_once_url encrypt/decrypt + mtc roll determinism."""
    t0 = time.time()
    try:
        from fusion_hero_os.core.poly_mesh_once_url import encrypt_mesh_ip, decrypt_mesh_ip
        from fusion_hero_os.core.mugen_tsuky_chan import roll

        cases = [
            ("100.64.104.58", 42069),
            ("100.103.188.54", 42069),
            ("100.108.67.116", 59100),
        ]
        fails = []
        for ip, port in cases:
            enc = encrypt_mesh_ip(ip, port)
            ip2, port2 = decrypt_mesh_ip(enc)
            if ip2 != ip or port2 != port:
                fails.append(f"{ip}:{port}->{ip2}:{port2}")
        r1 = roll("2026-07-15", depth=4)
        r2 = roll("2026-07-15", depth=4)
        det = (
            r1.get("mtc_day_hash_1") == r2.get("mtc_day_hash_1")
            and r1.get("mtc_roll_final") == r2.get("mtc_roll_final")
            and r1.get("mtc_seal") == r2.get("mtc_seal")
        )
        lossless = (not fails) and det
        return {
            "instance_id": "schwerkraft_control_a",
            "label": "encrypt-roundtrip + mtc-determinism",
            "ok": True,
            "lossless": lossless,
            "fails": fails,
            "deterministic_roll": det,
            "confidence": 100.0 if lossless else 20.0,
            "accuracy_self": 100.0 if lossless else 40.0,
            "gravity": 100.0 if lossless else 8.0,
            "latency_ms": (time.time() - t0) * 1000,
            "provider": "internal_crypto_a",
            "protocol": PROTOCOL,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "instance_id": "schwerkraft_control_a",
            "ok": False,
            "lossless": False,
            "error": str(exc)[:200],
            "confidence": 0.0,
            "accuracy_self": 0.0,
            "gravity": 0.0,
            "latency_ms": (time.time() - t0) * 1000,
            "provider": "internal_crypto_a",
        }


def control_b_lossless() -> dict[str, Any]:
    """Control B: independent re-encode path via mtc obfuscated body + bit-identity."""
    t0 = time.time()
    try:
        from fusion_hero_os.core import _mtc_obf as obf
        from fusion_hero_os.core.poly_mesh_once_url import encrypt_mesh_ip, decrypt_mesh_ip

        # Independent: double encrypt/decrypt cycle (must preserve)
        ip, port = "100.64.104.58", PORT_BASE
        enc1 = encrypt_mesh_ip(ip, port)
        ip_m, port_m = decrypt_mesh_ip(enc1)
        enc2 = encrypt_mesh_ip(ip_m, port_m)
        ip_f, port_f = decrypt_mesh_ip(enc2)
        cycle_ok = ip_f == ip and port_f == port

        # Day hash #1 stable through obfuscated module
        h1 = obf.polymesh_hash_number_1("2026-07-15", ip)
        h1b = obf.polymesh_hash_number_1("2026-07-15", ip)
        hash_ok = h1 == h1b and len(h1) == 64

        lossless = cycle_ok and hash_ok
        return {
            "instance_id": "schwerkraft_control_b",
            "label": "double-cycle + obf-dayhash-stable",
            "ok": True,
            "lossless": lossless,
            "cycle_ok": cycle_ok,
            "hash_ok": hash_ok,
            "mtc_day_hash_1_sample": h1[:16] + "…",
            "confidence": 100.0 if lossless else 25.0,
            "accuracy_self": 100.0 if lossless else 35.0,
            "gravity": 95.0 if lossless else 7.0,
            "latency_ms": (time.time() - t0) * 1000,
            "provider": "internal_crypto_b_obf",
            "protocol": PROTOCOL,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "instance_id": "schwerkraft_control_b",
            "ok": False,
            "lossless": False,
            "error": str(exc)[:200],
            "confidence": 0.0,
            "accuracy_self": 0.0,
            "gravity": 0.0,
            "latency_ms": (time.time() - t0) * 1000,
            "provider": "internal_crypto_b_obf",
        }


def dual_multi_model_control(gravity_threshold: float = 150.0) -> dict[str, Any]:
    """Doppelte Multi-Model-Kontrolle via Schwerkraftserver."""
    a = control_a_lossless()
    b = control_b_lossless()
    results = [a, b]
    agree = a.get("lossless") is True and b.get("lossless") is True
    gravity_sum = float(a.get("gravity") or 0) + float(b.get("gravity") or 0)
    execute = agree and gravity_sum >= gravity_threshold
    return {
        "ok": True,
        "server": "schwerkraftserver",
        "protocol": PROTOCOL,
        "dual_control": True,
        "instances": results,
        "consensus": {
            "lossless": agree,
            "agree": agree,
            "gravity_sum": gravity_sum,
            "gravity_threshold": gravity_threshold,
            "execute": execute,
        },
        "banner": (
            f"SCHWERKRAFTSERVER | dual-control | lossless={agree} | "
            f"gravity={gravity_sum:.0f}/{gravity_threshold:.0f} | execute={execute}"
        ),
    }


# ---------------------------------------------------------------------------
# Full git history → poly-mesh (mugen-tsuky.chan seal)
# ---------------------------------------------------------------------------
def _git_log_rows(repo: Path) -> list[dict[str, str]]:
    fmt = "%H%x09%cI%x09%s"
    raw = subprocess.check_output(
        ["git", "-C", str(repo), "log", f"--format={fmt}", "--reverse"],
        timeout=120,
    )
    rows = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        rows.append({"hash": parts[0], "date": parts[1], "subject": parts[2][:200]})
    return rows


def ingest_commit_history(
    repo: Path | None = None,
    *,
    batch_note: str = "full-history",
) -> dict[str, Any]:
    """Fold entire commit history into poly-mesh chain under mugen-tsuky.chan."""
    repo = repo or ROOT
    rows = _git_log_rows(repo)
    if not rows:
        return {"ok": False, "error": "no commits"}

    # Rolling Merkle-style chain: C0 = sha256(first), C_{n}=sha256(C_{n-1}||hash_n)
    chain = b""
    for i, row in enumerate(rows):
        piece = f"{i}|{row['hash']}|{row['date']}|{row['subject']}".encode()
        chain = hashlib.sha256(chain + piece).digest()

    tip = rows[-1]["hash"]
    genesis = rows[0]["hash"]
    chain_hex = chain.hex()

    # Seal with mugen-tsuky.chan day roll (today UTC) + history chain
    from fusion_hero_os.core.mugen_tsuky_chan import roll, PROTOCOL_ID

    day = datetime.now(UTC).strftime("%Y-%m-%d")
    mtc = roll(day, depth=6)
    seal = hashlib.sha256(
        bytes.fromhex(chain_hex)
        + bytes.fromhex(mtc.get("mtc_seal") or ("00" * 32))
        + f"|schwerkraft|git-ingest|{tip}|{PROTOCOL_ID}|{PORT_BASE}".encode()
    ).hexdigest()

    out = {
        "ok": True,
        "server": "schwerkraftserver",
        "protocol": PROTOCOL_ID,
        "operation": "git_history_poly_mesh_ingest",
        "repo": str(repo),
        "commit_count": len(rows),
        "genesis_hash": genesis,
        "tip_hash": tip,
        "history_chain_sha256": chain_hex,
        "mtc_day": day,
        "mtc_day_hash_1": mtc.get("mtc_day_hash_1"),
        "mtc_seal": mtc.get("mtc_seal"),
        "schwerkraft_seal": seal,
        "batch_note": batch_note,
        "port_base": PORT_BASE,
        "ts_iso": datetime.now(UTC).isoformat(),
        "banner": (
            f"SCHWERKRAFTSERVER INGEST | commits={len(rows)} | "
            f"tip={tip[:12]}… | chain={chain_hex[:16]}… | seal={seal[:16]}… | {PROTOCOL_ID}"
        ),
    }

    # Persist full index (hashes only + meta — subjects truncated already)
    out_dir = _state_dir() / "git_ingest"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    index_path = out_dir / f"history_{stamp}.json"
    # Store compact commit list + seals
    payload = {
        **out,
        "commits": rows,  # full ordered history for poly-mesh replay
    }
    index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest = out_dir / "latest.json"
    latest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    # Pointer for poly-mesh coordination
    mesh_ptr = Path.home() / ".fusion" / "mesh" / "git_history_ingest.json"
    mesh_ptr.parent.mkdir(parents=True, exist_ok=True)
    mesh_ptr.write_text(json.dumps({**out, "index": str(index_path)}, indent=2), encoding="utf-8")

    out["index"] = str(index_path)
    out["latest"] = str(latest)
    out["mesh_pointer"] = str(mesh_ptr)
    return out


def execute(
    repo: Path | None = None,
    *,
    gravity_threshold: float = 150.0,
    force: bool = False,
) -> dict[str, Any]:
    """Dual control → if lossless → ingest full git history into poly-mesh."""
    control = dual_multi_model_control(gravity_threshold=gravity_threshold)
    result: dict[str, Any] = {
        "ok": True,
        "server": "schwerkraftserver",
        "protocol": PROTOCOL,
        "control": control,
        "executed": False,
        "ingest": None,
    }
    can_run = control["consensus"]["execute"] or force
    if not can_run:
        result["ok"] = False
        result["error"] = "lossless_not_confirmed_or_gravity_below_threshold"
        result["banner"] = control["banner"] + " | INGEST SKIPPED"
        return result

    ingest = ingest_commit_history(repo or ROOT)
    result["executed"] = True
    result["ingest"] = ingest
    result["banner"] = control["banner"] + " | " + ingest.get("banner", "INGEST OK")
    # master report
    report_path = _state_dir() / "last_execute.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["report"] = str(report_path)
    return result


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Schwerkraftserver dual control + git→polymesh")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--threshold", type=float, default=150.0)
    ap.add_argument("--control-only", action="store_true")
    args = ap.parse_args()
    if args.control_only:
        print(json.dumps(dual_multi_model_control(args.threshold), indent=2))
        return
    print(json.dumps(execute(force=args.force, gravity_threshold=args.threshold), indent=2))


if __name__ == "__main__":
    main()
