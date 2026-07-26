# -*- coding: utf-8 -*-
"""
Tailscale Quantize Self-Mod — Fusion Hero OS v12.0.0 · BIG ALPHA

Creates and maintains **quantize assist** roles that self-modulate calculation
quantization parameters using Tailscale mesh health as a capacity signal.

Axes of support:
  - annealer shards (parallel SA)
  - bit-depth reduction / energy binning
  - graph partition for mesh offload
  - integrity probe (MasterSeed contraction)
  - eudaemon heal of param drift

Honesty:
  - Does NOT create foreign Tailscale user accounts or mutate remote ACLs.
  - "Virtual" assists are local lab nodes when peers are missing (labeled).
  - Real Tailscale status is read-only via CLI when available.
  - Offense FORBIDDEN · sandbox_only · no vault in git.

Geltung: peer counts / run metrics = Satz · param map = Modell · ACL push = Fragment.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PLATFORM = "12.1.0"
CONFIG_PATH = ROOT / "mesh_quantize_selfmod.yaml"
DOCS_SUMMARY = ROOT / "docs" / "mesh" / "tailscale_quantize_selfmod.latest.json"

__all__ = [
    "load_config",
    "status",
    "ensure_assist_nodes",
    "self_modulate",
    "run_quantize",
    "run_full_cycle",
]


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _cfg() -> Dict[str, Any]:
    return load_config()


def state_dir() -> Path:
    raw = ((_cfg().get("paths") or {}).get("state_dir") or "~/.fusion/mesh/quantize_selfmod")
    p = Path(os.path.expanduser(raw))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ts_exe() -> Optional[str]:
    for c in (r"C:\Program Files\Tailscale\tailscale.exe", "tailscale"):
        if Path(c).is_file() or shutil.which(c):
            return c if Path(c).is_file() else shutil.which(c)
    return None


def tailscale_snapshot() -> Dict[str, Any]:
    """Read-only Tailscale status (Satz when CLI present)."""
    exe = _ts_exe()
    if not exe:
        return {
            "ok": False,
            "online": False,
            "peers_online": 0,
            "peer_count": 0,
            "virtual_floor": True,
            "error": "tailscale CLI not found",
        }
    try:
        raw = subprocess.check_output(
            [exe, "status", "--json"],
            timeout=12,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(raw.decode("utf-8", errors="replace"))
        self = data.get("Self") or {}
        peers = data.get("Peer") or {}
        online = sum(1 for p in peers.values() if p.get("Online"))
        return {
            "ok": True,
            "online": bool(self.get("Online")),
            "hostname": self.get("HostName"),
            "ips": self.get("TailscaleIPs"),
            "dns": self.get("DNSName"),
            "backend": data.get("BackendState"),
            "peer_count": len(peers),
            "peers_online": online,
            "magic_dns": (data.get("CurrentTailnet") or {}).get("MagicDNSSuffix"),
            "virtual_floor": online == 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "online": False,
            "peers_online": 0,
            "peer_count": 0,
            "virtual_floor": True,
            "error": str(exc)[:200],
        }


@dataclass
class AssistNode:
    id: str
    tag: str
    function: str
    layer: int
    virtual: bool
    capacity: float
    status: str = "ready"
    last_mod: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuantizeParams:
    bit_depth: int
    anneal_steps: int
    workers: int
    partitions: int
    T0: float
    n: int
    density: float
    scale: float
    heroic_boost: float = 0.0
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _mesh_scale(ts: Dict[str, Any], cfg: Dict[str, Any]) -> float:
    sm = cfg.get("self_mod") or {}
    target = float(sm.get("peer_target") or 4)
    peers = float(ts.get("peers_online") or 0)
    scale = peers / max(1.0, target)
    floor = float(sm.get("offline_virtual_floor") or 0.25)
    if not ts.get("online") or peers <= 0:
        scale = max(scale, floor)
    return _clamp(scale, 0.15, 1.0)


def ensure_assist_nodes(*, force_virtual: Optional[bool] = None) -> Dict[str, Any]:
    """Create/update self-modulating Tailscale quantize assist nodes (lab registry)."""
    cfg = _cfg()
    ts = tailscale_snapshot()
    scale = _mesh_scale(ts, cfg)
    virtual = force_virtual if force_virtual is not None else bool(ts.get("virtual_floor", True))
    roles = cfg.get("assist_roles") or []
    nodes: List[AssistNode] = []
    now = datetime.now(timezone.utc).isoformat()
    for r in roles:
        # capacity per role slightly skewed by layer (L0 integrity stable)
        raw_layer = r.get("layer") if r.get("layer") is not None else 1
        if isinstance(raw_layer, str):
            raw_layer = raw_layer.strip().upper().lstrip("L")
        try:
            layer = int(raw_layer)
        except (TypeError, ValueError):
            layer = 1
        cap = _clamp(scale * (1.0 - 0.05 * layer), 0.1, 1.0)
        nodes.append(
            AssistNode(
                id=str(r.get("id")),
                tag=str(r.get("tag")),
                function=str(r.get("function")),
                layer=layer,
                virtual=virtual,
                capacity=round(cap, 4),
                status="ready" if cap >= 0.15 else "degraded",
                last_mod=now,
            )
        )
    out = {
        "ok": True,
        "platform": PLATFORM,
        "created_at": now,
        "virtual": virtual,
        "mesh_scale": scale,
        "tailscale": {
            "ok": ts.get("ok"),
            "online": ts.get("online"),
            "peers_online": ts.get("peers_online"),
            "peer_count": ts.get("peer_count"),
            "hostname": ts.get("hostname"),
        },
        "nodes": [n.to_dict() for n in nodes],
        "note": (
            "virtual assists = local lab nodes (labeled). "
            "No foreign tailnet ACL mutation."
        ),
        "geltung": "node registry = Spezifikation (Lab) · peer counts = Satz",
    }
    path = state_dir() / ((_cfg().get("paths") or {}).get("nodes_file") or "nodes.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["path"] = str(path)
    return out


def self_modulate(
    *,
    heroic_boost: float = 0.0,
    n_override: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Self-modulate quantization params from mesh capacity + optional heroic boost.

    MasterSeed contraction: integrity_gate prevents aggressive expansion when
    mesh is offline and scale is at virtual floor.
    """
    cfg = _cfg()
    sm = cfg.get("self_mod") or {}
    if not sm.get("enabled", True):
        return {"ok": False, "error": "self_mod disabled in config"}

    ts = tailscale_snapshot()
    scale = _mesh_scale(ts, cfg)
    hb = _clamp(float(heroic_boost), 0.0, 1.0)
    w_h = float(sm.get("heroic_boost_weight") or 0.12)
    eff = _clamp(scale + w_h * hb, 0.15, 1.0)

    # Contraction: if integrity gate and fully virtual/offline → cap eff
    if sm.get("integrity_gate", True) and (not ts.get("online") or ts.get("virtual_floor")):
        eff = min(eff, max(float(sm.get("offline_virtual_floor") or 0.25) + 0.15, 0.4))

    bit_lo = int(sm.get("min_bit_depth") or 2)
    bit_hi = int(sm.get("max_bit_depth") or 8)
    steps_lo = int(sm.get("min_anneal_steps") or 200)
    steps_hi = int(sm.get("max_anneal_steps") or 8000)
    w_lo = int(sm.get("min_workers") or 1)
    w_hi = int(sm.get("max_workers") or 16)
    p_lo = int(sm.get("min_partitions") or 1)
    p_hi = int(sm.get("max_partitions") or 8)
    T0_base = float(sm.get("T0_base") or 2.5)
    T0_span = float(sm.get("T0_span") or 1.5)

    bit_depth = int(round(bit_lo + (bit_hi - bit_lo) * eff))
    anneal_steps = int(round(steps_lo + (steps_hi - steps_lo) * eff))
    workers = int(round(w_lo + (w_hi - w_lo) * eff))
    partitions = int(round(p_lo + (p_hi - p_lo) * eff))
    T0 = T0_base + T0_span * (1.0 - eff)  # cooler when more capacity (finer search)

    qcfg = cfg.get("quantize") or {}
    n = int(n_override if n_override is not None else qcfg.get("default_n") or 24)

    params = QuantizeParams(
        bit_depth=bit_depth,
        anneal_steps=anneal_steps,
        workers=max(1, workers),
        partitions=max(1, partitions),
        T0=round(T0, 4),
        n=n,
        density=float(qcfg.get("density") or 0.18),
        scale=round(eff, 4),
        heroic_boost=round(hb, 4),
        reason=(
            f"mesh_scale={scale:.3f} peers_online={ts.get('peers_online')} "
            f"virtual_floor={ts.get('virtual_floor')} heroic={hb:.3f}"
        ),
    )

    nodes = ensure_assist_nodes()
    payload = {
        "ok": True,
        "platform": PLATFORM,
        "modulated_at": datetime.now(timezone.utc).isoformat(),
        "params": params.to_dict(),
        "tailscale": {
            "ok": ts.get("ok"),
            "online": ts.get("online"),
            "peers_online": ts.get("peers_online"),
            "peer_count": ts.get("peer_count"),
            "virtual_floor": ts.get("virtual_floor"),
        },
        "nodes_count": len(nodes.get("nodes") or []),
        "virtual_nodes": nodes.get("virtual"),
        "contraction": {
            "integrity_gate": bool(sm.get("integrity_gate", True)),
            "masterseed_contraction": bool(sm.get("masterseed_contraction", True)),
        },
        "geltung": "params = Modell · peer metrics = Satz",
    }
    path = state_dir() / ((cfg.get("paths") or {}).get("last_mod_file") or "last_selfmod.json")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["path"] = str(path)
    return payload


def _make_qubo(n: int, density: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    Q = rng.normal(0.0, 1.0, size=(n, n))
    Q = 0.5 * (Q + Q.T)
    mask = rng.random((n, n)) < density
    mask = np.triu(mask, 1)
    mask = mask | mask.T
    np.fill_diagonal(mask, True)
    Q = Q * mask
    return Q


def _quantize_matrix(Q: np.ndarray, bit_depth: int) -> np.ndarray:
    """Uniform symmetric quantization of Q entries to 2^bit_depth levels (Modell)."""
    levels = max(2, 2 ** int(bit_depth))
    qmax = float(np.max(np.abs(Q))) or 1.0
    scale = (levels / 2 - 1) / qmax
    qi = np.clip(np.round(Q * scale), -(levels // 2 - 1), levels // 2 - 1)
    return qi / scale


def _anneal_once(Q: np.ndarray, steps: int, T0: float, seed: int) -> Tuple[np.ndarray, float]:
    """Simple SA for binary spin {-1,+1} / map to {0,1} energy  x^T Q x."""
    rng = np.random.default_rng(seed)
    n = Q.shape[0]
    x = rng.integers(0, 2, size=n).astype(np.float64)

    def energy(v: np.ndarray) -> float:
        return float(v @ Q @ v)

    e = energy(x)
    best_x, best_e = x.copy(), e
    for t in range(1, steps + 1):
        T = T0 * (1.0 - t / steps) + 1e-6
        i = int(rng.integers(0, n))
        x[i] = 1.0 - x[i]
        e2 = energy(x)
        de = e2 - e
        if de <= 0 or rng.random() < math.exp(-de / T):
            e = e2
            if e < best_e:
                best_e, best_x = e, x.copy()
        else:
            x[i] = 1.0 - x[i]
    return best_x, best_e


def run_quantize(
    *,
    params: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run mesh-assisted quantized QUBO solve with self-mod params.

    Workers/partitions are simulated as parallel SA restarts (honest local fan-out),
    not remote code execution on peers unless future secure offload is wired.
    """
    t0 = time.time()
    if params is None:
        mod = self_modulate()
        params = mod.get("params") or {}
    cfg = _cfg()
    qcfg = cfg.get("quantize") or {}
    n = int(params.get("n") or qcfg.get("default_n") or 24)
    density = float(params.get("density") or qcfg.get("density") or 0.18)
    bit_depth = int(params.get("bit_depth") or 4)
    steps = int(params.get("anneal_steps") or 500)
    workers = int(params.get("workers") or 1)
    partitions = int(params.get("partitions") or 1)
    T0 = float(params.get("T0") or 2.5)
    seed = int(seed if seed is not None else qcfg.get("seed") or 42)

    Q = _make_qubo(n, density, seed)
    Qq = _quantize_matrix(Q, bit_depth)
    quant_err = float(np.mean((Q - Qq) ** 2))

    # partition = chunk variables (block-diagonal style assist); here: multi-start SA
    starts = max(1, workers * max(1, partitions // 2))
    results: List[Dict[str, Any]] = []
    best_e = float("inf")
    best_x: Optional[np.ndarray] = None
    for w in range(starts):
        x, e = _anneal_once(Qq, steps=max(50, steps // max(1, starts // 2 + 1)), T0=T0, seed=seed + w * 17)
        results.append({"worker": w, "energy": e, "ones": int(x.sum())})
        if e < best_e:
            best_e, best_x = e, x

    # integrity: energy on original Q (not only quantized) as probe
    assert best_x is not None
    e_true = float(best_x @ Q @ best_x)
    integrity_gap = abs(e_true - best_e)

    out = {
        "ok": True,
        "platform": PLATFORM,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "params": {
            "n": n,
            "density": density,
            "bit_depth": bit_depth,
            "anneal_steps": steps,
            "workers": workers,
            "partitions": partitions,
            "T0": T0,
            "starts": starts,
            "scale": params.get("scale"),
        },
        "metrics": {
            "quantization_mse": round(quant_err, 8),
            "energy_quantized": round(best_e, 6),
            "energy_true_Q": round(e_true, 6),
            "integrity_gap": round(integrity_gap, 6),
            "solution_ones": int(best_x.sum()),
            "solution_sha16": hashlib.sha256(best_x.astype(np.uint8).tobytes()).hexdigest()[:16],
        },
        "workers_detail": results[:32],
        "honest": {
            "remote_peer_execution": False,
            "local_fanout_sim": True,
            "note": "Workers are local parallel SA restarts modulated by mesh scale; not remote code on peers.",
        },
        "duration_sec": round(time.time() - t0, 3),
        "geltung": "energies/mse = Satz (local) · mesh capacity map = Modell",
    }
    path = state_dir() / ((cfg.get("paths") or {}).get("last_run_file") or "last_quantize_run.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["path"] = str(path)
    return out


def run_full_cycle(*, heroic_boost: float = 0.0) -> Dict[str, Any]:
    """Ensure nodes → self-mod → quantize → docs summary."""
    t0 = time.time()
    nodes = ensure_assist_nodes()
    mod = self_modulate(heroic_boost=heroic_boost)
    run = run_quantize(params=mod.get("params"))
    summary = {
        "kind": "tailscale_quantize_selfmod",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": PLATFORM,
        "cycle": "BIG_ALPHA",
        "ok": bool(run.get("ok") and mod.get("ok") and nodes.get("ok")),
        "virtual_nodes": nodes.get("virtual"),
        "nodes_count": len(nodes.get("nodes") or []),
        "mesh_scale": (mod.get("params") or {}).get("scale"),
        "peers_online": (mod.get("tailscale") or {}).get("peers_online"),
        "params": mod.get("params"),
        "metrics": run.get("metrics"),
        "duration_sec": round(time.time() - t0, 3),
        "bounds": {
            "offense": "FORBIDDEN",
            "sandbox_only": True,
            "external_tailnet_mutate": False,
            "remote_peer_execution": False,
        },
        "entry_line": "BIG OMEGA sealed. BIG ALPHA open. MasterSeed fixed. Labor only. Build.",
        "geltung": "cycle metrics = Satz · capacity map = Modell",
    }
    DOCS_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    DOCS_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary["docs_summary"] = str(DOCS_SUMMARY)
    summary["nodes_path"] = nodes.get("path")
    summary["mod_path"] = mod.get("path")
    summary["run_path"] = run.get("path")
    # coordination pin
    coord = Path.home() / ".fusion" / "mesh" / "coordination"
    coord.mkdir(parents=True, exist_ok=True)
    (coord / "tailscale_quantize_selfmod_latest.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def status() -> Dict[str, Any]:
    cfg = _cfg()
    ts = tailscale_snapshot()
    nodes_path = state_dir() / ((cfg.get("paths") or {}).get("nodes_file") or "nodes.json")
    mod_path = state_dir() / ((cfg.get("paths") or {}).get("last_mod_file") or "last_selfmod.json")
    run_path = state_dir() / ((cfg.get("paths") or {}).get("last_run_file") or "last_quantize_run.json")

    def _load(p: Path) -> Dict[str, Any]:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    return {
        "ok": True,
        "platform": PLATFORM,
        "cycle": "BIG_ALPHA",
        "config": str(CONFIG_PATH),
        "self_mod_enabled": bool((cfg.get("self_mod") or {}).get("enabled", True)),
        "tailscale": ts,
        "mesh_scale": _mesh_scale(ts, cfg),
        "assist_roles": [r.get("id") for r in (cfg.get("assist_roles") or [])],
        "latest_nodes": _load(nodes_path),
        "latest_mod": _load(mod_path),
        "latest_run": _load(run_path),
        "docs_summary": str(DOCS_SUMMARY) if DOCS_SUMMARY.exists() else None,
        "bounds": {
            "offense": "FORBIDDEN",
            "sandbox_only": True,
            "external_tailnet_mutate": False,
        },
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Tailscale quantize self-mod assists")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--ensure-nodes", action="store_true")
    ap.add_argument("--modulate", action="store_true")
    ap.add_argument("--quantize", action="store_true")
    ap.add_argument("--cycle", action="store_true", help="full ensure+mod+quantize")
    ap.add_argument("--heroic", type=float, default=0.0)
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False)[:6000])
        return 0
    if args.ensure_nodes:
        print(json.dumps(ensure_assist_nodes(), indent=2, ensure_ascii=False))
        return 0
    if args.modulate:
        print(json.dumps(self_modulate(heroic_boost=args.heroic), indent=2, ensure_ascii=False))
        return 0
    if args.quantize:
        print(json.dumps(run_quantize(), indent=2, ensure_ascii=False)[:5000])
        return 0
    # default: full cycle
    r = run_full_cycle(heroic_boost=args.heroic)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
