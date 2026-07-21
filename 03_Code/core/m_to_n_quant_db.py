# -*- coding: utf-8 -*-
"""
M→N Quantisierungsbau — M Quell-Datenbanken → N Ziel-Datenbanken + Sinnquanten

Architektur:
  M sources (roh / connector / corpus / conversation / …)
       │  adaptive Substrings (nicht komplette Strings)
       ▼
  Quant-Layer (string_quantizer + sinn_quanten_registry)
       │  Q# + Liebesquant / Zufriedenheitsquant / Sinnquant / …
       ▼
  N targets (sinn_store, quantized_phrases, entwicklungsquant_bus, quantum_dict, …)

Jeder Transfer ist ein diskretes Quant (Magnitude gerundet).
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "M_DATABASES",
    "N_DATABASES",
    "QuantTransfer",
    "MToNQuantBuilder",
    "build_default",
    "run_pipeline",
    "status",
]

# ── M Quell-DBs ────────────────────────────────────────────────────────────
M_DATABASES: Dict[str, Dict[str, Any]] = {
    "public_corpus": {
        "path_env": "FUSION_SUITE_ROOT",
        "rel": "data/public_raw",
        "kind": "files",
        "description": "Öffentliche gescrapte Datensätze",
    },
    "public_quantized": {
        "path_env": "FUSION_SUITE_ROOT",
        "rel": "data/public_quantized",
        "kind": "files",
        "description": "Bereits quantisierte Corpora",
    },
    "conversation": {
        "module": "conversation_context_core",
        "kind": "memory",
        "description": "Gesprächskontext / Subagent-Fenster",
    },
    "heroic_book": {
        "rel_root": "04_Buch_und_Archiv",
        "kind": "docs",
        "description": "Der heroische Mensch + Quant-Seiten",
    },
    "knowledge": {
        "rel_root": "03_Code/core/knowledge",
        "kind": "docs",
        "description": "4D-Matrix / Kompendien",
    },
    "github_connector": {
        "kind": "connector",
        "description": "GitHub MCP / raw catalogs",
    },
    "notion": {
        "kind": "connector",
        "description": "Notion Seiten / Attachments",
    },
    "google_drive": {
        "kind": "connector",
        "description": "Drive Offload / Mirror",
    },
    "llm_frameworks": {
        "module": "llm_frameworks",
        "kind": "registry",
        "description": "LLM Framework Status / Antworten",
    },
    "mesh": {
        "module": "framework_cross_mesh",
        "kind": "mesh",
        "description": "Kreuznetz Framework-Graph",
    },
    "journal": {
        "path_env": "FUSION_JOURNAL_ROOT",
        "kind": "files",
        "description": "Operator-Journal (optional)",
    },
    "ops": {
        "rel_root": "docs/ops",
        "kind": "docs",
        "description": "Ops / Seal / Autoload State",
    },
}

# ── N Ziel-DBs ─────────────────────────────────────────────────────────────
N_DATABASES: Dict[str, Dict[str, Any]] = {
    "sinn_store": {
        "path": "~/.fusion/operator/sinn_store",
        "kind": "jsonl",
        "description": "Persistierte Sinnquant-Events",
    },
    "quantized_phrases": {
        "path": "~/.fusion/operator/quantized_phrases",
        "kind": "json",
        "description": "Adaptive Substring Q-Tables",
    },
    "entwicklungsquant_bus": {
        "module": "entwicklungsquant_bus",
        "kind": "bus",
        "description": "Propagation als Entwicklungsquanten",
    },
    "quantum_dict": {
        "module": "fusion_hero_os.core.quantum_dictionaries",
        "kind": "dict",
        "description": "QuantumDictionary memo store",
    },
    "ascension": {
        "module": "ascension_os",
        "kind": "layer",
        "description": "Ascension / Sinn-Layer Ziel",
    },
    "suite_quantized": {
        "path_env": "FUSION_SUITE_ROOT",
        "rel": "data/public_quantized",
        "kind": "files",
        "description": "Suite quantisierte Outputs",
    },
    "cross_mesh_cache": {
        "path": "~/.fusion/operator/cross_mesh_quant.json",
        "kind": "json",
        "description": "Kreuznetz Quant-Snapshot",
    },
}


@dataclass
class QuantTransfer:
    """Ein M→N Transfer-Quant."""
    source_db: str
    target_db: str
    quant_type: str  # substring | sinn | liebesquant | zufriedenheitsquant | ...
    magnitude: float
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def _suite_root() -> Path:
    return Path(os.environ.get("FUSION_SUITE_ROOT", Path.home() / "private-hacking-suite"))


def _fusion_root() -> Path:
    return Path(os.environ.get("FUSION_HERO_ROOT", Path.home() / "fusion-hero-os"))


def _read_source_text(source_id: str, max_chars: int = 500_000) -> str:
    """Lädt Text aus einer M-DB (best-effort)."""
    meta = M_DATABASES.get(source_id) or {}
    kind = meta.get("kind")
    chunks: List[str] = []

    if kind == "files":
        base = _suite_root()
        rel = meta.get("rel") or ""
        d = base / rel
        if d.is_dir():
            for p in sorted(d.glob("*"), key=lambda x: -x.stat().st_size)[:40]:
                if p.suffix.lower() in (".txt", ".md", ".json", ".csv", ".rst"):
                    try:
                        chunks.append(p.read_text(encoding="utf-8", errors="replace")[:80_000])
                    except Exception:
                        pass
                if sum(len(c) for c in chunks) >= max_chars:
                    break
    elif kind == "docs":
        root = _fusion_root() / (meta.get("rel_root") or "")
        if root.is_dir():
            for p in list(root.rglob("*.md"))[:30] + list(root.rglob("*.txt"))[:20]:
                try:
                    chunks.append(p.read_text(encoding="utf-8", errors="replace")[:40_000])
                except Exception:
                    pass
                if sum(len(c) for c in chunks) >= max_chars:
                    break
    elif kind == "memory":
        try:
            from conversation_context_core import status as ctx_status
            st = ctx_status()
            chunks.append(json.dumps(st, ensure_ascii=False)[:20_000])
        except Exception as exc:
            chunks.append(f"[conversation unavailable: {exc}]")
    elif kind == "registry":
        try:
            from llm_frameworks import connector_status
            chunks.append(json.dumps(connector_status(), ensure_ascii=False)[:30_000])
        except Exception as exc:
            chunks.append(f"[llm_frameworks unavailable: {exc}]")
    elif kind == "mesh":
        try:
            from framework_cross_mesh import cross_mesh_status
            chunks.append(json.dumps(cross_mesh_status(), ensure_ascii=False, default=str)[:30_000])
        except Exception as exc:
            chunks.append(f"[cross_mesh unavailable: {exc}]")
    elif kind == "connector":
        chunks.append(f"[connector:{source_id} — content via MCP at session time]")

    text = "\n".join(chunks)
    return text[:max_chars]


def _adaptive_substrings(text: str, min_len: int = 4, max_n: int = 4) -> List[str]:
    """
    Logisch adaptive Substrings: Wörter + n-gramme, die sich an Frequenz anpassen.
    Keine Einzelbuchstaben, keine kompletten Dokumente als Einheit.
    """
    words = re.findall(r"[\wÄÖÜäöüß]{3,}", (text or "").lower())
    if not words:
        return []
    from collections import Counter
    c = Counter()
    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            gram = " ".join(words[i : i + n])
            if len(gram) >= min_len:
                c[gram] += 1
    # adaptive: behalte wiederholte + mittellange (nicht nur max-lang)
    items = [(g, n) for g, n in c.items() if n >= 2 or (len(g.split()) >= 2 and n >= 1)]
    items.sort(key=lambda x: (-x[1], -min(len(x[0]), 40), x[0]))
    # diversify lengths
    out: List[str] = []
    seen_len_buckets = {1: 0, 2: 0, 3: 0, 4: 0}
    for g, n in items:
        bucket = min(4, len(g.split()))
        if seen_len_buckets[bucket] > 800:
            continue
        out.append(g)
        seen_len_buckets[bucket] += 1
        if len(out) >= 5000:
            break
    return out


class MToNQuantBuilder:
    """Baut Quantisierungs-Transfers von M Quellen nach N Zielen inkl. Sinnquanten."""

    def __init__(self) -> None:
        self.transfers: List[QuantTransfer] = []
        self._last_report: Dict[str, Any] = {}

    def edges(self) -> List[Tuple[str, str]]:
        """Vollständiges bipartites M×N (jeder Source → jedes Target)."""
        return [(m, n) for m in M_DATABASES for n in N_DATABASES]

    def run(
        self,
        sources: Optional[Sequence[str]] = None,
        targets: Optional[Sequence[str]] = None,
        max_chars_per_source: int = 400_000,
    ) -> Dict[str, Any]:
        from sinn_quanten_registry import get_registry
        from string_quantizer_agent import StringQuantizer

        sources = list(sources or M_DATABASES.keys())
        targets = list(targets or N_DATABASES.keys())
        reg = get_registry()
        quantizer = StringQuantizer()
        all_subs: List[str] = []
        source_payloads: Dict[str, Any] = {}

        for sid in sources:
            if sid not in M_DATABASES:
                continue
            text = _read_source_text(sid, max_chars=max_chars_per_source)
            subs = _adaptive_substrings(text)
            all_subs.extend(subs)
            # string quantizer on joined sample (adaptive substrings as units)
            sample = "\n".join(subs[:2000])
            qpay = quantizer.quantize(sample) if sample.strip() else None
            sinn = reg.map_substrings(subs[:1500], adapt=True)
            source_payloads[sid] = {
                "chars": len(text),
                "substrings": len(subs),
                "quantizer": qpay.to_dict() if qpay else None,
                "sinn": {
                    "aggregate": sinn.get("aggregate"),
                    "mapped_count": sinn.get("mapped_count"),
                    "adaptive_learned": sinn.get("adaptive_learned"),
                },
            }
            # emit transfers M→N
            for tid in targets:
                if tid not in N_DATABASES:
                    continue
                # magnitude from sinn aggregate strength
                agg = sinn.get("aggregate") or {}
                mag = max(agg.values()) if agg else (0.25 if subs else 0.0)
                if mag < 0.25 and subs:
                    mag = 0.25
                if mag <= 0:
                    continue
                # type: dominant sinn or substring
                qtype = max(agg, key=agg.get) if agg else "substring"
                tr = QuantTransfer(
                    source_db=sid,
                    target_db=tid,
                    quant_type=qtype,
                    magnitude=float(mag),
                    payload={
                        "substrings_sample": subs[:30],
                        "sinn_aggregate": agg,
                        "q_table_size": (qpay.stats or {}).get("table_size") if qpay else 0,
                    },
                )
                self.transfers.append(tr)
                self._write_target(tid, tr, sinn, qpay)

        # entwicklungsquant bus broadcast for top sinn
        try:
            self._propagate_bus(source_payloads)
        except Exception as exc:
            bus_err = str(exc)
        else:
            bus_err = None

        reg.persist()
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "m_to_n_adaptive_substring_sinn",
            "m_sources": sources,
            "n_targets": targets,
            "edges_total": len(sources) * len(targets),
            "transfers": len(self.transfers),
            "source_payloads": source_payloads,
            "sinn_registry": reg.to_dict(),
            "liebesquant_hits": reg._hit_counts.get("liebesquant", 0),
            "zufriedenheitsquant_hits": reg._hit_counts.get("zufriedenheitsquant", 0),
            "sinnquant_hits": reg._hit_counts.get("sinnquant", 0),
            "bus_error": bus_err,
            "principle": "adaptive_substrings + sinnquanten + M×N db mesh",
        }
        self._last_report = report
        # persist report
        out = _expand("~/.fusion/operator/m_to_n_quant_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        # suite copy
        try:
            suite_meta = _suite_root() / "data" / "public_meta"
            suite_meta.mkdir(parents=True, exist_ok=True)
            (suite_meta / "m_to_n_quant_report.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        return report

    def _write_target(
        self,
        tid: str,
        tr: QuantTransfer,
        sinn: Dict[str, Any],
        qpay: Any,
    ) -> None:
        meta = N_DATABASES[tid]
        kind = meta.get("kind")
        if kind == "jsonl":
            p = _expand(meta["path"])
            p.mkdir(parents=True, exist_ok=True)
            f = p / "events.jsonl"
            with f.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(tr.to_dict(), ensure_ascii=False) + "\n")
        elif kind == "json":
            p = _expand(meta.get("path") or "~/.fusion/operator/quantized_phrases")
            if p.suffix == ".json":
                p.parent.mkdir(parents=True, exist_ok=True)
                data = {"transfers": [tr.to_dict()], "sinn": sinn.get("aggregate"), "ts": tr.ts}
                p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                p.mkdir(parents=True, exist_ok=True)
                fp = p / f"{tr.source_db}__{tr.quant_type}.json"
                fp.write_text(
                    json.dumps(
                        {
                            "transfer": tr.to_dict(),
                            "sinn": sinn.get("aggregate"),
                            "q_preview": (qpay.to_dict() if qpay else None),
                        },
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    ),
                    encoding="utf-8",
                )
        elif kind == "files":
            base = _suite_root() / (meta.get("rel") or "data/public_quantized")
            base.mkdir(parents=True, exist_ok=True)
            fp = base / f"m2n_{tr.source_db}_{tr.quant_type}.json"
            fp.write_text(
                json.dumps(tr.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        elif kind == "dict":
            try:
                from fusion_hero_os.core.quantum_dictionaries import get_quantum_dictionary

                qd = get_quantum_dictionary("sinn_quanten_m2n")
                qd.get_or_compute(
                    {"src": tr.source_db, "type": tr.quant_type},
                    lambda: tr.to_dict(),
                    signature=str(tr.ts),
                )
            except Exception:
                pass
        # bus / layer: handled in _propagate_bus

    def _propagate_bus(self, source_payloads: Dict[str, Any]) -> None:
        from entwicklungsquant_bus import EntwicklungsquantBus

        bus = EntwicklungsquantBus(quant_size=0.25, min_quant=0.25)
        # register nodes for each N target + sinn quanta
        for tid in N_DATABASES:
            bus.register(tid, reactions=[
                ("sinn_update", "sinn_echo", "*", 0.4),
                ("liebesquant", "bindung_ripple", "sinn_store", 0.5),
                ("zufriedenheitsquant", "wohl_ripple", "sinn_store", 0.5),
            ])
        for qid in ("liebesquant", "zufriedenheitsquant", "sinnquant", "stammquant"):
            bus.register(qid, reactions=[
                ("strength_update", "sinn_update", "sinn_store", 0.6),
                ("strength_update", "sinn_update", "entwicklungsquant_bus", 0.3),
            ])
        bus.register("sinn_store", reactions=[])
        bus.register("string_quantizer", reactions=[
            ("substring", "strength_update", "*", 0.35),
        ])

        for sid, pay in source_payloads.items():
            agg = (pay.get("sinn") or {}).get("aggregate") or {}
            for qid, mag in agg.items():
                bus.emit("string_quantizer", qid, "strength_update", float(mag), layer=3, payload={"source_db": sid})
            if pay.get("substrings"):
                bus.emit("string_quantizer", "sinn_store", "substring", 0.5, layer=2, payload={"source_db": sid})

        res = bus.run_until_fixpoint()
        self._last_report["bus"] = res


def build_default() -> MToNQuantBuilder:
    return MToNQuantBuilder()


def run_pipeline(
    sources: Optional[Sequence[str]] = None,
    targets: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    return build_default().run(sources=sources, targets=targets)


def status() -> Dict[str, Any]:
    from sinn_quanten_registry import status as sinn_status

    return {
        "module": "m_to_n_quant_db",
        "m_count": len(M_DATABASES),
        "n_count": len(N_DATABASES),
        "m_ids": list(M_DATABASES.keys()),
        "n_ids": list(N_DATABASES.keys()),
        "edges_full": len(M_DATABASES) * len(N_DATABASES),
        "sinn": sinn_status(),
        "mode": "adaptive_substrings + sinnquanten (liebes/zufriedenheit/sinn)",
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    # light pipeline: subset of sources for speed
    src = ["public_corpus", "public_quantized", "heroic_book", "llm_frameworks", "mesh"]
    rep = run_pipeline(sources=src)
    print(json.dumps({
        "transfers": rep.get("transfers"),
        "liebesquant_hits": rep.get("liebesquant_hits"),
        "zufriedenheitsquant_hits": rep.get("zufriedenheitsquant_hits"),
        "sinnquant_hits": rep.get("sinnquant_hits"),
        "edges_total": rep.get("edges_total"),
        "sources": list((rep.get("source_payloads") or {}).keys()),
    }, indent=2, ensure_ascii=False))
    sys.exit(0)
