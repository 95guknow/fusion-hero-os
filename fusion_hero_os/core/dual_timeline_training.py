# -*- coding: utf-8 -*-
"""
Dual + Virtual Timeline Auto-Training — Fusion Hero OS v12.

Axes:
  - t  = real time (mtime UTC)
  - τ  = imaginary/structural time ∈ [0,1] (layer/path/modality/Geltung/heroic)
  - v  = virtual heroic scenario (labor sandbox) — re-enabled under BIG ALPHA

Virtual timelines are lab-only (INVERT Realraum → labor hypothesis).
Heroic optimization targets the operator (dich / SHU / St3phaN).

Policy: pseudo_inhouse_only · freemium=false · offense FORBIDDEN.
Geltung: Spezifikation (pipeline) · τ/v-mapping = Modell (not physical Wick proof).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "FileEvent",
    "TrainSample",
    "scan_files",
    "build_samples",
    "run_auto_train",
    "status",
    "load_config",
    "virtual_timelines_enabled",
    "heroic_score_for_text",
]

PLATFORM = "12.1.0"


@dataclass
class FileEvent:
    path: str
    rel: str
    t_real: float
    t_iso: str
    tau: float
    layer: int
    modality: str
    bytes: int
    sha16: str
    geltung_hits: Dict[str, int] = field(default_factory=dict)
    heroic_score: float = 0.0
    heroic_hits: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrainSample:
    prompt: str
    response: str
    source: str
    t_real: float
    t_iso: str
    tau: float
    layer: int
    timeline: str  # "real" | "imaginary" | "dual" | "virtual"
    sample_id: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_config() -> Dict[str, Any]:
    path = ROOT / "training_dual_timeline.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _cfg() -> Dict[str, Any]:
    return load_config()


def output_dir() -> Path:
    cfg = _cfg()
    raw = (cfg.get("training") or {}).get("output_dir") or "~/.fusion/training/dual_timeline"
    p = Path(os.path.expanduser(raw))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _layer_for(rel: str, layers: Dict[str, int]) -> int:
    rel_n = rel.replace("\\", "/")
    best_k, best_v = "", 2
    for prefix, rank in (layers or {}).items():
        pref = prefix.replace("\\", "/").rstrip("/")
        if rel_n.startswith(pref) and len(pref) >= len(best_k):
            best_k, best_v = pref, int(rank)
    return best_v


def _geltung_hits(text: str, boosts: Dict[str, float]) -> Dict[str, int]:
    hits: Dict[str, int] = {}
    for marker in boosts or {}:
        n = len(re.findall(re.escape(marker), text, flags=re.IGNORECASE))
        if n:
            hits[marker] = n
    return hits


def virtual_timelines_enabled(cfg: Optional[Dict[str, Any]] = None) -> bool:
    """BIG ALPHA gate: virtual timelines re-allowed (labor sandbox only)."""
    cfg = cfg or _cfg()
    vt = cfg.get("virtual_timelines") or {}
    if "enabled" in vt:
        return bool(vt.get("enabled"))
    timelines = cfg.get("timelines") or {}
    virtual = timelines.get("virtual") or {}
    return bool(virtual.get("enabled", False))


def heroic_score_for_text(text: str, cfg: Optional[Dict[str, Any]] = None) -> Tuple[float, Dict[str, int]]:
    """Heroic optimization score ∈ [0,1] for operator (SHU/dich) alignment."""
    cfg = cfg or _cfg()
    ho = cfg.get("heroic_optimization") or {}
    if not ho.get("enabled", True):
        return 0.0, {}
    markers = ho.get("boost_markers") or {}
    if not markers:
        return 0.0, {}
    snippet = (text or "")[:50000]
    hits: Dict[str, int] = {}
    score = 0.0
    for marker, w in markers.items():
        # allow dotted keys as phrase alternatives
        pattern = re.escape(str(marker).replace(".", r"[\s._-]+"))
        n = len(re.findall(pattern, snippet, flags=re.IGNORECASE))
        if n:
            hits[str(marker)] = n
            score += float(w) * min(3, n)
    return round(max(0.0, min(1.0, score)), 6), hits


def _tau(
    rel: str,
    layer: int,
    ext: str,
    text: str,
    layers: Dict[str, int],
    mod_w: Dict[str, float],
    geltung: Dict[str, float],
    heroic: float = 0.0,
    cfg: Optional[Dict[str, Any]] = None,
) -> float:
    """Imaginary structural time τ ∈ [0,1] — parallel to real chronology (Modell)."""
    cfg = cfg or _cfg()
    ho = cfg.get("heroic_optimization") or {}
    h_w = float(ho.get("tau_heroic_weight") or 0.15) if ho.get("enabled", True) else 0.0
    layer_norm = max(0.0, min(1.0, layer / 6.0))
    depth = rel.replace("\\", "/").count("/")
    path_depth_norm = max(0.0, min(1.0, depth / 12.0))
    modality_weight = float(mod_w.get(ext.lower(), 0.5))
    hits = _geltung_hits(text[:50000], geltung)
    g_score = 0.0
    for k, n in hits.items():
        g_score += float(geltung.get(k, 0)) * min(3, n)
    g_score = max(0.0, min(1.0, g_score))
    # hash phase — stable micro-structure (not random each run)
    h = int(hashlib.md5(rel.encode()).hexdigest()[:8], 16)
    hash_phase = (h % 1000) / 1000.0
    heroic_n = max(0.0, min(1.0, float(heroic)))
    tau = (
        0.30 * layer_norm
        + 0.20 * path_depth_norm
        + 0.18 * modality_weight
        + 0.12 * g_score
        + h_w * heroic_n
        + 0.05 * hash_phase
    )
    return round(max(0.0, min(1.0, tau)), 6)


def iter_candidate_files(cfg: Optional[Dict[str, Any]] = None) -> Iterator[Path]:
    cfg = cfg or _cfg()
    scan = cfg.get("scan") or {}
    roots = scan.get("roots") or ["docs", "fusion_hero_os"]
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in (scan.get("extensions") or [".md", ".py"])}
    exclude = set(scan.get("exclude_dir_names") or [])
    max_files = int(scan.get("max_files") or 8000)
    max_bytes = int(scan.get("max_file_bytes") or 800_000)
    n = 0
    for root_name in roots:
        base = ROOT / root_name
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if n >= max_files:
                return
            if not p.is_file():
                continue
            if any(part in exclude for part in p.parts):
                continue
            if p.suffix.lower() not in exts:
                continue
            try:
                if p.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            n += 1
            yield p


def scan_files(cfg: Optional[Dict[str, Any]] = None) -> List[FileEvent]:
    cfg = cfg or _cfg()
    layers = cfg.get("layers") or {}
    mod_w = cfg.get("modality_weights") or {}
    geltung = cfg.get("geltung_boost") or {}
    events: List[FileEvent] = []
    for p in iter_candidate_files(cfg):
        try:
            st = p.stat()
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        t_real = float(st.st_mtime)
        t_iso = datetime.fromtimestamp(t_real, tz=timezone.utc).isoformat()
        layer = _layer_for(rel, layers)
        h_score, h_hits = heroic_score_for_text(text, cfg)
        tau = _tau(rel, layer, p.suffix, text, layers, mod_w, geltung, heroic=h_score, cfg=cfg)
        events.append(
            FileEvent(
                path=str(p),
                rel=rel,
                t_real=t_real,
                t_iso=t_iso,
                tau=tau,
                layer=layer,
                modality=p.suffix.lower(),
                bytes=st.st_size,
                sha16=_sha16(text),
                geltung_hits=_geltung_hits(text[:50000], geltung),
                heroic_score=h_score,
                heroic_hits=h_hits,
            )
        )
    events.sort(key=lambda e: (e.t_real, e.tau, e.rel))
    return events


def _chunk_text(text: str, size: int) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start, end)
            if cut > start + size // 2:
                end = cut
        part = text[start:end].strip()
        if part:
            chunks.append(part)
        start = end if end > start else start + size
    return chunks


def _samples_from_file(ev: FileEvent, cfg: Dict[str, Any]) -> List[TrainSample]:
    train = cfg.get("training") or {}
    chunk = int(train.get("chunk_chars") or 1000)
    max_resp = int(train.get("max_response") or 800)
    cap = int(train.get("samples_per_file_cap") or 12)
    min_c = int(train.get("min_chunk_chars") or 80)
    vt = cfg.get("virtual_timelines") or {}
    virtual_on = virtual_timelines_enabled(cfg)
    max_virtual = int(vt.get("max_virtual_samples_per_file") or 4)
    min_h_for_v = float(vt.get("min_heroic_score_for_virtual") or 0.12)
    try:
        text = Path(ev.path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    title = Path(ev.rel).stem.replace("_", " ")
    samples: List[TrainSample] = []
    virtual_n = 0
    # Prefer markdown headers
    sections = re.split(r"\n(?=#{1,3}\s)", text) if ev.modality == ".md" else [text]
    bodies: List[Tuple[str, str]] = []
    if ev.modality == ".md" and len(sections) > 1:
        for sec in sections:
            sec = sec.strip()
            if len(sec) < min_c:
                continue
            header = sec.split("\n", 1)[0].lstrip("#").strip()
            body = sec.split("\n", 1)[1].strip() if "\n" in sec else ""
            if body:
                bodies.append((header, body))
    else:
        bodies.append((title, text))

    for header, body in bodies:
        for i, part in enumerate(_chunk_text(body, chunk)):
            if len(part) < min_c:
                continue
            if len(samples) >= cap:
                break
            # Dual prompts: real t ∥ imaginary τ, heroically framed for operator
            sid = _sha16(f"{ev.rel}:{header}:{i}:{ev.sha16}")
            meta = {
                "header": header[:200],
                "chunk": i,
                "geltung_hits": ev.geltung_hits,
                "heroic_score": ev.heroic_score,
                "heroic_hits": ev.heroic_hits,
                "platform": PLATFORM,
            }
            samples.append(
                TrainSample(
                    prompt=(
                        f"[t={ev.t_iso} · τ={ev.tau:.4f} · H={ev.heroic_score:.3f} · L{ev.layer}] "
                        f"Erkläre heroisch-optimiert für den Operator (SHU/dich) aus {title}: {header}. "
                        f"Nutze Geltung (Satz|Bedingt|Modell|Fragment), MasterSeed-Kontraktion, "
                        f"Labor-only. (realer Zeitstrahl t + imaginäre Strukturzeit τ, Fusion Hero OS v{PLATFORM})"
                    ),
                    response=part[:max_resp],
                    source=ev.rel,
                    t_real=ev.t_real,
                    t_iso=ev.t_iso,
                    tau=ev.tau,
                    layer=ev.layer,
                    timeline="dual",
                    sample_id=sid,
                    meta=meta,
                )
            )
            # Virtual heroic scenario axis (re-allowed) — labor sandbox only
            if (
                virtual_on
                and virtual_n < max_virtual
                and ev.heroic_score >= min_h_for_v
                and len(samples) < cap
            ):
                vsid = _sha16(f"virtual:{ev.rel}:{header}:{i}:{ev.sha16}")
                vmeta = {
                    **meta,
                    "axis": "virtual",
                    "mode": "labor_sandbox",
                    "invert": "INVERT(realraum)=labor_hypothesis+integrity_probe+no_vault_commit",
                    "geltung": "Modell|Bedingt",
                    "offense": "FORBIDDEN",
                }
                samples.append(
                    TrainSample(
                        prompt=(
                            f"[VIRTUAL v · t={ev.t_iso} · τ={ev.tau:.4f} · H={ev.heroic_score:.3f} · L{ev.layer}] "
                            f"Labor-Szenario (virtuelle Timeline, heroisch für SHU/Operator): "
                            f"aus {title} — {header}. "
                            f"Entfalte additive Optionen unter MasterSeed, Eudaimonia-Ceiling, Sisyphos-Nachhaltigkeit. "
                            f"Kein Realraum-Commit, kein Offense. Fusion Hero OS v{PLATFORM} BIG ALPHA."
                        ),
                        response=part[:max_resp],
                        source=ev.rel,
                        t_real=ev.t_real,
                        t_iso=ev.t_iso,
                        tau=ev.tau,
                        layer=ev.layer,
                        timeline="virtual",
                        sample_id=vsid,
                        meta=vmeta,
                    )
                )
                virtual_n += 1
        if len(samples) >= cap:
            break
    return samples


def build_samples(events: Optional[List[FileEvent]] = None, cfg: Optional[Dict[str, Any]] = None) -> List[TrainSample]:
    cfg = cfg or _cfg()
    events = events if events is not None else scan_files(cfg)
    samples: List[TrainSample] = []
    for ev in events:
        samples.extend(_samples_from_file(ev, cfg))
    # Sort dual: primary by t, secondary by τ (parallel traversal key)
    samples.sort(key=lambda s: (s.t_real, s.tau, s.source))
    return samples


def consistency_report(events: List[FileEvent], samples: List[TrainSample], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic dual-timeline consistency (Modell)."""
    cons = cfg.get("consistency") or {}
    max_jump = float(cons.get("max_tau_jump_same_day") or 0.45)
    min_roots = int(cons.get("min_coverage_roots") or 3)

    by_day: Dict[str, List[float]] = {}
    for e in events:
        day = e.t_iso[:10]
        by_day.setdefault(day, []).append(e.tau)

    jumps = 0
    day_checks = 0
    for day, taus in by_day.items():
        if len(taus) < 2:
            continue
        day_checks += 1
        if max(taus) - min(taus) > max_jump:
            jumps += 1

    roots = set()
    for e in events:
        roots.add(e.rel.split("/")[0] if "/" in e.rel else e.rel)

    # samples must carry both axes
    missing_axis = sum(1 for s in samples if s.t_real <= 0 or s.tau < 0)
    tau_vals = [e.tau for e in events] or [0.0]
    t_vals = [e.t_real for e in events] or [0.0]

    ok = (
        len(roots) >= min_roots
        and missing_axis == 0
        and len(events) > 0
        and len(samples) > 0
    )
    return {
        "ok": ok,
        "files": len(events),
        "samples": len(samples),
        "roots_covered": sorted(roots),
        "root_count": len(roots),
        "min_roots_required": min_roots,
        "days_with_tau_spread": day_checks,
        "days_tau_jump_over_threshold": jumps,
        "max_tau_jump_threshold": max_jump,
        "missing_axis_samples": missing_axis,
        "tau_min": min(tau_vals),
        "tau_max": max(tau_vals),
        "tau_mean": sum(tau_vals) / len(tau_vals),
        "t_min_iso": datetime.fromtimestamp(min(t_vals), tz=timezone.utc).isoformat() if t_vals else None,
        "t_max_iso": datetime.fromtimestamp(max(t_vals), tz=timezone.utc).isoformat() if t_vals else None,
        "note": "τ is structural/model time parallel to real chronology — not a physics proof",
    }


def run_auto_train(*, write: bool = True) -> Dict[str, Any]:
    t0 = time.time()
    cfg = _cfg()
    events = scan_files(cfg)
    samples = build_samples(events, cfg)
    cons = consistency_report(events, samples, cfg)

    # Dual + virtual indices
    by_t = sorted(events, key=lambda e: e.t_real)
    by_tau = sorted(events, key=lambda e: e.tau)
    by_heroic = sorted(events, key=lambda e: (-e.heroic_score, e.tau))
    virtual_samples = [s for s in samples if s.timeline == "virtual"]
    dual_samples = [s for s in samples if s.timeline == "dual"]
    timeline = {
        "platform": PLATFORM,
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "cycle": "BIG_ALPHA",
        "axes": {
            "t": "real chronology (mtime UTC)",
            "tau": "imaginary/structural time ∈ [0,1] (Modell, heroic-weighted)",
            "v": "virtual heroic scenario (labor sandbox, re-enabled)",
        },
        "virtual_timelines_enabled": virtual_timelines_enabled(cfg),
        "heroic_optimization": True,
        "heroic_target": (cfg.get("heroic_optimization") or {}).get("target", "operator_shu"),
        "real_timeline": [e.to_dict() for e in by_t[:5000]],
        "imaginary_timeline": [e.to_dict() for e in by_tau[:5000]],
        "heroic_ranked": [e.to_dict() for e in by_heroic[:2000]],
        "virtual_sample_count": len(virtual_samples),
        "dual_sample_count": len(dual_samples),
        "parallel": True,
        "bounds": {
            "offense": "FORBIDDEN",
            "sandbox_only": True,
            "realraum_vault_commit": False,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out: Dict[str, Any] = {
        "ok": cons.get("ok", False),
        "files": len(events),
        "samples": len(samples),
        "dual_samples": len(dual_samples),
        "virtual_samples": len(virtual_samples),
        "virtual_timelines_enabled": virtual_timelines_enabled(cfg),
        "heroic_mean": (
            round(sum(e.heroic_score for e in events) / len(events), 6) if events else 0.0
        ),
        "consistency": cons,
        "duration_sec": round(time.time() - t0, 2),
        "output_dir": str(output_dir()),
        "platform": PLATFORM,
    }

    if write:
        od = output_dir()
        train = cfg.get("training") or {}
        jsonl = od / (train.get("jsonl_name") or "samples_dual_timeline.jsonl")
        tl_path = od / (train.get("timeline_name") or "timeline_dual.json")
        man_path = od / (train.get("manifest_name") or "auto_train_manifest.json")
        cons_path = od / (train.get("consistency_name") or "consistency_report.json")

        with jsonl.open("w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")

        tl_path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
        cons_path.write_text(json.dumps(cons, indent=2, ensure_ascii=False), encoding="utf-8")

        # also mirror under docs/training for repo visibility (manifest summary only)
        docs_mirror = ROOT / "docs" / "training"
        docs_mirror.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": PLATFORM,
            "cycle": "BIG_ALPHA",
            "files": len(events),
            "samples": len(samples),
            "dual_samples": len(dual_samples),
            "virtual_samples": len(virtual_samples),
            "virtual_timelines_enabled": virtual_timelines_enabled(cfg),
            "heroic_mean": out.get("heroic_mean"),
            "consistency_ok": cons.get("ok"),
            "tau_mean": cons.get("tau_mean"),
            "t_min_iso": cons.get("t_min_iso"),
            "t_max_iso": cons.get("t_max_iso"),
            "roots": cons.get("roots_covered"),
            "jsonl": str(jsonl),
            "timeline": str(tl_path),
            "policy": "pseudo_inhouse_only",
            "freemium": False,
            "axes": {
                "t": "real",
                "tau": "imaginary_structural_heroic",
                "v": "virtual_heroic_scenario",
            },
            "bounds": timeline["bounds"],
        }
        (docs_mirror / "dual_timeline_training.latest.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        man = {
            **summary,
            "duration_sec": out["duration_sec"],
            "consistency": cons,
            "config": "training_dual_timeline.yaml",
        }
        man_path.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
        # coordination hook
        coord = Path.home() / ".fusion" / "mesh" / "coordination"
        coord.mkdir(parents=True, exist_ok=True)
        (coord / "dual_timeline_training_latest.json").write_text(
            json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        out["paths"] = {
            "jsonl": str(jsonl),
            "timeline": str(tl_path),
            "manifest": str(man_path),
            "consistency": str(cons_path),
            "docs_summary": str(docs_mirror / "dual_timeline_training.latest.json"),
        }
    return out


def status() -> Dict[str, Any]:
    od = output_dir()
    man = od / "auto_train_manifest.json"
    latest = {}
    if man.exists():
        try:
            latest = json.loads(man.read_text(encoding="utf-8"))
        except Exception:
            latest = {}
    cfg = _cfg()
    return {
        "ok": True,
        "platform": PLATFORM,
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "cycle": "BIG_ALPHA",
        "virtual_timelines_enabled": virtual_timelines_enabled(cfg),
        "heroic_optimization": bool((cfg.get("heroic_optimization") or {}).get("enabled", True)),
        "heroic_target": (cfg.get("heroic_optimization") or {}).get("target", "operator_shu"),
        "axes": {
            "t": "real_chronology",
            "tau": "imaginary_structural_heroic",
            "v": "virtual_heroic_scenario",
        },
        "bounds": {
            "offense": "FORBIDDEN",
            "sandbox_only": True,
            "realraum_vault_commit": False,
            "invert": "INVERT(realraum)=labor_hypothesis+integrity_probe+no_vault_commit",
        },
        "output_dir": str(od),
        "latest": latest,
        "config": "training_dual_timeline.yaml",
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Dual-timeline auto-training")
    ap.add_argument("--dry", action="store_true", help="Scan/build without writing")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    report = run_auto_train(write=not args.dry)
    print(json.dumps(report, indent=2, ensure_ascii=False)[:4000])
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
