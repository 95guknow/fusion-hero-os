# parallel_internal_optimizer.py — Parallele Intern-Optimierung (Hyperthreading-Tracks)

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[2]
_CORE = _ROOT / "03_Code" / "core"
_LLM = _ROOT / "03_Code" / "internal_llm"
_KNOWLEDGE = _CORE / "knowledge"
_V2_MD = Path(
    r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch\Geisteskrankheiten_4D_Matrix_v2_claude_science.md"
)
_V4_MD = Path(
    r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch\Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
)
_V5_MD = Path(
    r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch\Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
)
_V6_MD = Path(
    r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch\Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md"
)
_V6_INDEX = _KNOWLEDGE / "geisteskrankheiten_4d_v6.json"
_V4_INDEX = _KNOWLEDGE / "geisteskrankheiten_4d_v4.json"
_V5_INDEX = _KNOWLEDGE / "geisteskrankheiten_4d_v5.json"
_DATA_JSONL = _LLM / "data.jsonl"
_CONFIG = _LLM / "output" / "heroic_llama_config.json"


def _workers() -> int:
    try:
        from resource_workflow import recommend_workers

        rec = recommend_workers("medium")
        return max(1, rec.get("recommended_workers", 2))
    except Exception:
        pass
    try:
        import hyperthreading_config as ht

        return max(2, min(ht.parallel_workers(), 8))
    except Exception:
        return min(6, (os.cpu_count() or 4))


def _track(name: str, fn: Callable[[], Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = fn()
        return {
            "track": name,
            "ok": True,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "result": _safe(result),
        }
    except Exception as exc:
        return {
            "track": name,
            "ok": False,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": str(exc),
        }


def _safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe(v) for k, v in list(obj.items())[:50]}
    if isinstance(obj, (list, tuple)):
        return [_safe(x) for x in obj[:30]]
    return str(obj)[:400]


def _read_v2() -> str:
    if not _V2_MD.exists():
        alt = _ROOT / "03_Code" / "core" / "knowledge" / "Geisteskrankheiten_4D_Matrix_v2_claude_science.md"
        if alt.exists():
            return alt.read_text(encoding="utf-8")
        raise FileNotFoundError(f"v2 matrix not found: {_V2_MD}")
    return _V2_MD.read_text(encoding="utf-8")


def _build_training_pairs(text: str) -> List[Dict[str, str]]:
    pairs = [
        {
            "prompt": "Erkläre die 4D-Matrix Geisteskrankheiten (v2): Was bedeuten K, G, S, N und I(Z)?",
            "response": (
                "K=Körper, G=Geist, S=Seele, N=Natur. Z=(K,G,S,N). "
                "I(Z)=Σ|Δi_imaginär| misst Selbstwahrnehmungsverzerrung. "
                "v2: Triangulation aus Selbstbericht, Fremdbeurteilung, Verhalten. "
                "Kein DSM-Ersatz — MER-Ursachen-Schwerpunkte."
            ),
        },
        {
            "prompt": "Was ist neu in der 4D-Matrix v2 zu Schizophrenie und Autismus?",
            "response": (
                "Schizophrenie: Salienz-/Netzwerkmodelle (dopaminerg, glutamaterg, immunologisch), "
                "nicht monokausal Dopamin. Autismus: i variabel (Masking, soziale Fehlattribution), "
                "nicht 'kein imaginärer Raum'."
            ),
        },
        {
            "prompt": "Nenne Komorbiditäts-Bündel aus der 4D-Matrix v2.",
            "response": (
                "ADHS+Borderline (q↑ S−−), Depression+Angst (G+ K+ S−), PTBS+Substanz (S−→K+), "
                "OCD+Depression (b↑ q↑), Autismus+Angst (N+G+), Essstörung+Borderline (G+ S−±). "
                "Komorbidität erhöht I(Z) überadditiv bei stabilisierenden Fehlattributionen."
            ),
        },
        {
            "prompt": "Welche Therapiepfade ordnet die 4D-Matrix v2 den Clustern zu?",
            "response": (
                "N-primär: Medikation+Psychoedukation+Struktur. S-primär: Trauma/DBT/Bindung. "
                "G-primär: KVT/Metakognition/Exposition. K-primär: Interozeption/Entzug/Somatik. "
                "Memetisch senkt d(Z,Z*); mimetisch senkt nur I(Z) ohne reale Veränderung."
            ),
        },
        {
            "prompt": "Wie unterscheidet v2 memetische von mimetischer Heilung?",
            "response": (
                "Memetisch: d(Z(t+1),Z*) < d(Z(t),Z*) — echte Veränderung. "
                "Mimetisch: I(Z) sinkt, d unverändert — Surrogat (z.B. SSRI ohne Stamm/S/G-Arbeit)."
            ),
        },
    ]
    if "## 7 — Komorbiditäts" in text:
        chunk = text.split("## 7 — Komorbiditäts", 1)[1][:900]
        pairs.append({
            "prompt": "Fasse den Komorbiditäts-Abschnitt der Geisteskrankheiten-4D-Matrix zusammen.",
            "response": chunk.strip(),
        })
    return pairs


def track_ingest_training() -> Dict[str, Any]:
    text = _read_v2()
    pairs = _build_training_pairs(text)
    _LLM.mkdir(parents=True, exist_ok=True)
    existing = set()
    if _DATA_JSONL.exists():
        for line in _DATA_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    existing.add(json.loads(line).get("prompt", ""))
                except Exception:
                    pass
    added = 0
    with _DATA_JSONL.open("a", encoding="utf-8") as f:
        for row in pairs:
            if row["prompt"] in existing:
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            added += 1
    return {"added": added, "total_pairs_built": len(pairs), "data_jsonl": str(_DATA_JSONL)}


def track_knowledge_index() -> Dict[str, Any]:
    text = _read_v2()
    _KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    dest_md = _KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v2_claude_science.md"
    dest_md.write_text(text, encoding="utf-8")
    index = {
        "id": "geisteskrankheiten_4d_v2",
        "version": "2.0",
        "source": "claude_science_review",
        "updated_ts": time.time(),
        "domains": ["psychiatry", "mer", "science", "4d_matrix"],
        "key_insights": [
            "I(Z) triangulation operationalized",
            "komorbidity matrix section 7",
            "autism i_variabel masking",
            "schizophrenia salience network",
            "therapy paths memetic_vs_mimetic",
            "evidence grades A/B/C",
        ],
        "clusters": ["N-primär", "S-primär", "G-primär", "K-primär"],
        "path": str(dest_md),
    }
    index_path = _KNOWLEDGE / "geisteskrankheiten_4d_v2.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"index": str(index_path), "md": str(dest_md), "chars": len(text)}


def _read_v4() -> str:
    if _V4_MD.exists():
        return _V4_MD.read_text(encoding="utf-8")
    alt = _KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
    if alt.exists():
        return alt.read_text(encoding="utf-8")
    raise FileNotFoundError(f"v4 matrix not found: {_V4_MD}")


def _read_v5() -> str:
    if _V5_MD.exists():
        return _V5_MD.read_text(encoding="utf-8")
    alt = _KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
    if alt.exists():
        return alt.read_text(encoding="utf-8")
    raise FileNotFoundError(f"v5 matrix not found: {_V5_MD}")


def track_v5_knowledge_index() -> Dict[str, Any]:
    text = _read_v5()
    _KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    dest_md = _KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
    dest_md.write_text(text, encoding="utf-8")
    if _V5_INDEX.exists():
        index = json.loads(_V5_INDEX.read_text(encoding="utf-8"))
        index["path"] = str(dest_md)
        index["updated_ts"] = time.time()
    else:
        index = {
            "id": "geisteskrankheiten_4d_v5",
            "version": "5.0",
            "path": str(dest_md),
            "updated_ts": time.time(),
        }
    _V5_INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"index": str(_V5_INDEX), "md": str(dest_md), "chars": len(text)}


def track_v4_knowledge_index() -> Dict[str, Any]:
    text = _read_v4()
    _KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    dest_md = _KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
    dest_md.write_text(text, encoding="utf-8")
    if _V4_INDEX.exists():
        index = json.loads(_V4_INDEX.read_text(encoding="utf-8"))
        index["path"] = str(dest_md)
        index["updated_ts"] = time.time()
    else:
        index = {
            "id": "geisteskrankheiten_4d_v4",
            "version": "4.0",
            "path": str(dest_md),
            "updated_ts": time.time(),
        }
    _V4_INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"index": str(_V4_INDEX), "md": str(dest_md), "chars": len(text)}


def track_llama_config_patch() -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    if _CONFIG.exists():
        cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))
    domains = cfg.setdefault("domains", {})
    domains["science_psychiatry_4d"] = {
        "version": "v7_heroismus_edition",
        "updated_ts": time.time(),
        "knowledge_index": "geisteskrankheiten_4d_v7.json",
        "routing": "science-worker / claude-science",
        "bridges": ["heroische_mathematik", "heroische_informatik", "neurotheologie", "dissertation", "concept_space", "heroismus_edition_0.7"],
        "visual": ["Pi_KG", "Pi_SN", "trajektorien"],
    }
    import sys as _sys

    _llm = _ROOT / "03_Code" / "internal_llm"
    if str(_llm) not in _sys.path:
        _sys.path.insert(0, str(_llm))
    from system_prompt_normalize import normalize_system_prompt

    cfg["system_prompt"] = normalize_system_prompt(cfg.get("system_prompt", ""))
    cfg["internal_optimization"] = {
        "parallel_tracks": True,
        "last_insights": "geisteskrankheiten_4d_v7",
        "ts": time.time(),
    }
    _CONFIG.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"config": str(_CONFIG), "domain": domains["science_psychiatry_4d"]}


def track_claude_science_distill() -> Dict[str, Any]:
    from claude_science import analyze

    q = (
        "[science] Destilliere die 5 wichtigsten klinisch-epistemischen Neuerungen "
        "aus Geisteskrankheiten 4D-Matrix v5 (Pi_KG/Pi_SN, Trajektorien) für internes Fusion Hero OS Routing."
    )
    return analyze(q)


def track_llama_subagent_tests() -> Dict[str, Any]:
    from llama_subagent_tester import run

    return run(include_generate=None)


def track_context_window_feedback() -> Dict[str, Any]:
    from conversation_context_core import allocate_subagent, feedback, init_root, status

    root = init_root(
        "Parallel-Optimizer: adaptives Subagent-Kontextfenster mit Start-Anker",
        {"task_weight": "medium", "source": "parallel_internal_optimizer"},
    )
    sub = allocate_subagent("context-feedback-probe", task_weight="light")
    wid = sub["subagent_window"]["window_id"]
    fb = feedback(
        wid,
        "Probe-Rückkopplung: Subagent meldet erfolgreiche Delta-Kompression zum Root-Fenster.",
        {"probe": True},
    )
    return {"root": root, "subagent": sub, "feedback": fb, "status": status()}


def track_module_reload() -> Dict[str, Any]:
    from module_registry import load_module

    names = ["claude_science", "heroic_orchestration", "local_llama", "provider_switcher", "llama_subagent_tester"]
    loaded = []
    errors = []
    for name in names:
        r = load_module(name)
        if r.get("status") == "ok":
            loaded.append(name)
        else:
            errors.append({name: r.get("error")})
    return {"loaded": loaded, "errors": errors}


def track_supabase_event() -> Dict[str, Any]:
    import sys

    dash = _ROOT / "03_Code" / "Dashboard"
    if str(dash) not in sys.path:
        sys.path.insert(0, str(dash))
    import supabase_store as store

    event = {
        "id": f"parallel-opt-{int(time.time())}",
        "type": "internal_optimization",
        "msg": "Parallel intern: Geisteskrankheiten 4D v5 insights ingested",
        "severity": "info",
        "layer": 2,
        "source": "parallel_internal_optimizer",
    }
    return store.save_event(event)


def run(
    tracks: Optional[List[str]] = None,
    max_workers: Optional[int] = None,
) -> Dict[str, Any]:
    """Führt parallele Intern-Optimierung mit neuen Erkenntnissen aus."""
    all_tracks: Dict[str, Callable[[], Any]] = {
        "ingest_training": track_ingest_training,
        "knowledge_index": track_knowledge_index,
        "v4_knowledge_index": track_v4_knowledge_index,
        "v5_knowledge_index": track_v5_knowledge_index,
        "llama_config_patch": track_llama_config_patch,
        "claude_science_distill": track_claude_science_distill,
        "llama_subagent_tests": track_llama_subagent_tests,
        "context_window_feedback": track_context_window_feedback,
        "module_reload": track_module_reload,
        "supabase_event": track_supabase_event,
    }
    selected = tracks or list(all_tracks.keys())
    if os.getenv("FUSION_SUPABASE_SYNC", "1") != "1":
        selected = [t for t in selected if t != "supabase_event"]

    workers = max_workers or _workers()
    started = time.time()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_track, name, all_tracks[name]): name for name in selected if name in all_tracks}
        for fut in as_completed(futures):
            results.append(fut.result())

    ok = sum(1 for r in results if r.get("ok"))
    return {
        "status": "completed" if ok == len(results) else "partial",
        "tracks_ok": ok,
        "tracks_total": len(results),
        "workers": workers,
        "duration_ms": round((time.time() - started) * 1000, 1),
        "insights_source": str(_V2_MD),
        "tracks": sorted(results, key=lambda x: x.get("track", "")),
    }