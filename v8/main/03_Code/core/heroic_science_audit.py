# heroic_science_audit.py — Formale Heroik-Mathematik + Wissenschaftsansätze via Claude Science

from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[2]
_CORE = Path(__file__).resolve().parent
_REF = _CORE.parent / "reference"
_GUIDE = _ROOT / "02_Mathematik" / "hero-guide_geltungsstand.json"
_KNOWLEDGE = _CORE / "knowledge"
_REPORT_JSON = _KNOWLEDGE / "heroic_science_audit_report.json"
_REPORT_MD = _KNOWLEDGE / "Heroik_Wissenschaft_Claude_Science_Audit.md"

if str(_REF) not in sys.path:
    sys.path.insert(0, str(_REF))

HEROIC_SCIENCE_APPROACHES: List[Dict[str, Any]] = [
    {
        "id": "formal_mathematics",
        "title": "Formale Mathematik der Heroik",
        "dom": "Math",
        "source": "hero-guide_geltungsstand.json",
        "knowledge_refs": [],
    },
    {
        "id": "heroic_philosophy",
        "title": "Heroische Philosophie",
        "dom": "Phil",
        "source": "hero-guide + Concept Space",
        "knowledge_refs": ["Geisteskrankheiten_4D_Dissertation_Philosophie_v6.md"],
    },
    {
        "id": "heroic_informatics",
        "title": "Heroische Informatik",
        "dom": "Info",
        "source": "hero-guide + v4 Brücken §17",
        "knowledge_refs": ["Geisteskrankheiten_4D_Bruecken_v4.md"],
    },
    {
        "id": "heroic_mathematics_extended",
        "title": "Heroische Mathematik (ψ↔Z, Banach, QUBO)",
        "dom": "Math",
        "source": "v4 Brücken §16",
        "knowledge_refs": ["Geisteskrankheiten_4D_Bruecken_v4.md"],
    },
    {
        "id": "neurotheology",
        "title": "Neurotheologie (DMN, S–N-Brücke)",
        "dom": "Science",
        "source": "v4 Brücken §18",
        "knowledge_refs": ["Geisteskrankheiten_4D_Bruecken_v4.md"],
    },
    {
        "id": "psychiatric_mer_4d",
        "title": "Psychiatrische MER-4D-Matrix",
        "dom": "Science",
        "source": "Kompendium v7",
        "knowledge_refs": [
            "Geisteskrankheiten_4D_Matrix_v7_Kompendium.md",
            "Geisteskrankheiten_4D_Kompendium_Rahmen.md",
        ],
    },
    {
        "id": "layer_architecture",
        "title": "Layer-Architektur L0–L6ω (MasterSeed, Banach)",
        "dom": "Meta",
        "source": "CORE_ANCHOR + FUSION_HERO_OS",
        "knowledge_refs": ["Geisteskrankheiten_4D_Heroismus_Edition_v7.md"],
    },
    {
        "id": "integration_stack",
        "title": "Integrationsmatrix v4 (Operator-Stack)",
        "dom": "Science",
        "source": "v4 Brücken §19",
        "knowledge_refs": ["Geisteskrankheiten_4D_Bruecken_v4.md"],
    },
]

_AUDIT_PROMPT_ITEM = """\
[heroic-science] Formale Überprüfung — Einzeleintrag

Du bist Claude Science im Modus „Formale Heroik-Überprüfung".

Prüfe diesen Eintrag aus dem Hero-GUIDE / heroischen Wissenschaftskorpus:

**Name:** {name}
**Domäne:** {dom}
**Formel/These:** {formula}
**Deklarierte Kategorie (cat):** {cat}
**Aktuell (current):** {current}
**Drift-Hinweis:** {drift}
**Drift problematisch:** {drift_bad}
**Aufgabe (task):** {task}

Pflicht-Prüfdimensionen:
1. Geltungskategorie korrekt? (Satz | Bedingt | Modell | Fragment | Overreach)
2. Epistemische Drift — wurde Modell fälschlich zum Satz?
3. Metapher-als-Beweis-Risiko?
4. Mathematische/wissenschaftliche Korrektheit der Formel
5. Konkrete Korrektur-Empfehlung

Antwort strukturiert (Markdown):
- **Verdict:** PASS | WARN | FAIL
- **Empfohlene Kategorie:**
- **Begründung:** (3–6 Sätze)
- **Risiken:** (Bullet-Liste)
- **Maßnahmen:** (Bullet-Liste)
"""

_AUDIT_PROMPT_DOMAIN = """\
[heroik] Claude Science — Domänen-Audit: {title}

Du prüfst den gesamten heroischen Wissenschaftsansatz „{title}".

**Domäne:** {dom}
**Quellen:** {source}
**Anzahl formaler Einträge:** {n_items}

## Kontext-Auszug aus Werk/Knowledge
{context_excerpt}

## Formale Einträge (Kurzliste)
{items_list}

Pflicht:
1. Gesamtverdict für den Ansatz (PASS/WARN/FAIL)
2. Evidenzlage und Methodik (A/B/C/konzeptionell)
3. Stärken und epistemische Risiken
4. Drift-Muster (Upgrade Modell→Satz?)
5. Priorisierte Korrektur-Roadmap (max. 5 Punkte)
6. Abgrenzung: was ist Modell vs. was beansprucht Beweis?

Antwort auf Deutsch, strukturiert mit Überschriften.
"""


@dataclass
class AuditItem:
    approach_id: str
    name: str
    dom: str
    formula: str
    cat: str
    current: str
    drift: str
    drift_bad: bool
    risk: bool
    task: str
    local: Dict[str, Any] = field(default_factory=dict)
    claude: Dict[str, Any] = field(default_factory=dict)


def load_hero_guide() -> List[Dict[str, Any]]:
    path = _GUIDE if _GUIDE.exists() else _ROOT / "hero-guide_geltungsstand.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _read_excerpt(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars]


def _extract_section(md: str, section_marker: str, max_chars: int = 4000) -> str:
    idx = md.find(section_marker)
    if idx < 0:
        return md[:max_chars]
    chunk = md[idx : idx + max_chars]
    nxt = chunk.find("\n## ", 10)
    if nxt > 0:
        chunk = chunk[:nxt]
    return chunk


def load_approach_context(approach: Dict[str, Any]) -> str:
    parts: List[str] = []
    for ref in approach.get("knowledge_refs", []):
        p = _KNOWLEDGE / ref
        if p.exists():
            parts.append(f"### {ref}\n{_read_excerpt(p, 5000)}")
    if approach["id"] == "heroic_mathematics_extended":
        for ref in approach.get("knowledge_refs", []):
            full = (_KNOWLEDGE / ref).read_text(encoding="utf-8", errors="replace") if (_KNOWLEDGE / ref).exists() else ""
            sec = _extract_section(full, "## 16 — Heroische Mathematik")
            if sec:
                parts.append(sec)
    if approach["id"] == "heroic_informatics":
        for ref in approach.get("knowledge_refs", []):
            full = (_KNOWLEDGE / ref).read_text(encoding="utf-8", errors="replace") if (_KNOWLEDGE / ref).exists() else ""
            sec = _extract_section(full, "## 17 — Heroische Informatik")
            if sec:
                parts.append(sec)
    if approach["id"] == "neurotheology":
        for ref in approach.get("knowledge_refs", []):
            full = (_KNOWLEDGE / ref).read_text(encoding="utf-8", errors="replace") if (_KNOWLEDGE / ref).exists() else ""
            sec = _extract_section(full, "## 18 — Neurotheologie")
            if sec:
                parts.append(sec)
    if approach["id"] == "integration_stack":
        for ref in approach.get("knowledge_refs", []):
            full = (_KNOWLEDGE / ref).read_text(encoding="utf-8", errors="replace") if (_KNOWLEDGE / ref).exists() else ""
            sec = _extract_section(full, "## 19 — Integrationsmatrix")
            if sec:
                parts.append(sec)
    return "\n\n".join(parts)[:12000]


def _local_review_item(entry: Dict[str, Any]) -> Dict[str, Any]:
    """FormalMathematics + PeerReview + Drift-Heuristik (offline)."""
    name = entry.get("name", "")
    formula = entry.get("formula", "")
    text = f"{name}. {formula}. {entry.get('drift', '')} {entry.get('task', '')}"

    out: Dict[str, Any] = {"verdict": "WARN", "modules": {}}

    try:
        from core_modules import FormalMathematicsCoreModule, PeerReviewCoreModule

        fm = FormalMathematicsCoreModule()
        cls = fm.classify(
            f"[{entry.get('current', entry.get('cat', 'model'))}] {formula} — {name}",
            annahmen=["λ<1"] if "banach" in name.lower() or "fixpunkt" in name.lower() else None,
        )
        out["modules"]["formal_math"] = {
            "kategorie": cls.kategorie,
            "begruendung": cls.begruendung,
        }
        pr = PeerReviewCoreModule().review(text)
        out["modules"]["peer_review"] = {
            "score": pr["score"],
            "passed": pr["passed"],
            "coverage": pr["coverage"],
        }
    except Exception as exc:
        out["modules"]["error"] = str(exc)

    cat = entry.get("current") or entry.get("cat", "model")
    drift_bad = bool(entry.get("driftBad"))
    risk = bool(entry.get("risk"))

    if drift_bad and cat in ("proven", "cond"):
        out["verdict"] = "FAIL"
        out["reason"] = "driftBad + starke Kategorie"
    elif entry.get("cat") == "over" or cat == "over":
        out["verdict"] = "WARN"
        out["reason"] = "overreach markiert"
    elif risk:
        out["verdict"] = "WARN"
        out["reason"] = "risk flag"
    elif out.get("modules", {}).get("peer_review", {}).get("passed"):
        out["verdict"] = "PASS"
        out["reason"] = "peer_review coverage ok"
    else:
        out["reason"] = "unvollständige Abdeckung"

    return out


def _parse_claude_verdict(response: str) -> str:
    m = re.search(r"\*\*Verdict:\*\*\s*(PASS|WARN|FAIL)", response, re.I)
    if m:
        return m.group(1).upper()
    if "FAIL" in response.upper()[:200]:
        return "FAIL"
    if "WARN" in response.upper()[:200]:
        return "WARN"
    return "PASS"


def _import_science():
    try:
        from core.claude_science import analyze, is_configured, status as science_status
    except ImportError:
        from claude_science import analyze, is_configured, status as science_status  # type: ignore
    return analyze, is_configured, science_status


def _claude_review_item(entry: Dict[str, Any], approach_id: str) -> Dict[str, Any]:
    analyze, _, _ = _import_science()

    prompt = _AUDIT_PROMPT_ITEM.format(
        name=entry.get("name", ""),
        dom=entry.get("dom", ""),
        formula=entry.get("formula", ""),
        cat=entry.get("cat", ""),
        current=entry.get("current", entry.get("cat", "")),
        drift=entry.get("drift", ""),
        drift_bad=entry.get("driftBad", False),
        task=entry.get("task", ""),
    )
    result = analyze(prompt, context={"approach_id": approach_id, "audit_type": "formal_item"})
    response = result.get("response", "")
    configured = bool(result.get("configured"))
    verdict = _parse_claude_verdict(response) if configured else "OFFLINE"
    return {
        "ok": result.get("ok", False),
        "backend": result.get("backend", "claude-science"),
        "configured": configured,
        "verdict": verdict,
        "response": response,
        "error": result.get("error"),
    }


def _claude_review_domain(
    approach: Dict[str, Any],
    items: List[Dict[str, Any]],
    context: str,
) -> Dict[str, Any]:
    analyze, _, _ = _import_science()

    items_list = "\n".join(
        f"- **{e.get('name')}** [{e.get('current', e.get('cat'))}] `{e.get('formula', '')}`"
        for e in items[:20]
    )
    prompt = _AUDIT_PROMPT_DOMAIN.format(
        title=approach["title"],
        dom=approach.get("dom", ""),
        source=approach.get("source", ""),
        n_items=len(items),
        context_excerpt=context[:8000] or "(kein Knowledge-Auszug)",
        items_list=items_list or "(keine Einträge)",
    )
    result = analyze(prompt, context={"approach_id": approach["id"], "audit_type": "domain"})
    response = result.get("response", "")
    configured = bool(result.get("configured"))
    return {
        "ok": result.get("ok", False),
        "backend": result.get("backend"),
        "configured": configured,
        "verdict": _parse_claude_verdict(response) if configured else "OFFLINE",
        "response": response,
        "error": result.get("error"),
    }


def collect_items_for_approach(approach: Dict[str, Any], guide: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dom = approach.get("dom")
    if approach["id"] == "formal_mathematics":
        return [g for g in guide if g.get("dom") == "Math"]
    if approach["id"] == "heroic_philosophy":
        return [g for g in guide if g.get("dom") == "Phil"]
    if approach["id"] == "heroic_informatics":
        return [g for g in guide if g.get("dom") == "Info"]
    if approach["id"] == "layer_architecture":
        return [g for g in guide if g.get("dom") == "Meta"]
    # Wissenschaftsansätze ohne hero-guide-Einträge: synthetischer Prüfgegenstand
    if approach["id"] in ("neurotheology", "heroic_mathematics_extended", "integration_stack", "psychiatric_mer_4d"):
        return [
            {
                "name": approach["title"],
                "dom": approach.get("dom", "Science"),
                "formula": approach.get("source", ""),
                "cat": "model",
                "current": "model",
                "drift": "Domänen-Audit über Knowledge-Korpus",
                "driftBad": False,
                "risk": False,
                "task": f"Claude Science Gesamtprüfung: {approach['title']}",
            }
        ]
    return [g for g in guide if g.get("dom") == dom] if dom else list(guide)


def run_audit(
    approach_ids: Optional[List[str]] = None,
    include_items: bool = True,
    include_domains: bool = True,
    max_workers: int = 2,
    save: bool = True,
    desktop_copy: bool = True,
) -> Dict[str, Any]:
    """Vollständige Überprüfung formaler Mathematik + heroischer Wissenschaftsansätze."""
    started = time.time()
    guide = load_hero_guide()
    approaches = HEROIC_SCIENCE_APPROACHES
    if approach_ids:
        approaches = [a for a in approaches if a["id"] in approach_ids]

    _, is_configured, science_status = _import_science()

    report: Dict[str, Any] = {
        "module": "heroic_science_audit",
        "ts": time.time(),
        "claude_science": science_status(),
        "configured": is_configured(),
        "approaches": [],
        "summary": {},
    }

    total_pass = total_warn = total_fail = 0

    for approach in approaches:
        items_raw = collect_items_for_approach(approach, guide)
        context = load_approach_context(approach)
        approach_result: Dict[str, Any] = {
            "id": approach["id"],
            "title": approach["title"],
            "dom": approach.get("dom"),
            "n_items": len(items_raw),
            "items": [],
            "domain_review": None,
        }

        # Item-level audits
        if include_items:
            def _audit_one(entry: Dict[str, Any]) -> Dict[str, Any]:
                local = _local_review_item(entry)
                claude = _claude_review_item(entry, approach["id"])
                return {
                    "name": entry.get("name"),
                    "formula": entry.get("formula"),
                    "cat": entry.get("cat"),
                    "current": entry.get("current"),
                    "local": local,
                    "claude": claude,
                    "combined_verdict": _combine_verdict(local.get("verdict"), claude.get("verdict")),
                }

            if max_workers > 1 and len(items_raw) > 2:
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    futures = {pool.submit(_audit_one, e): e for e in items_raw}
                    for fut in as_completed(futures):
                        approach_result["items"].append(fut.result())
            else:
                for entry in items_raw:
                    approach_result["items"].append(_audit_one(entry))

        # Domain-level audit
        if include_domains:
            approach_result["domain_review"] = _claude_review_domain(approach, items_raw, context)

        # Tally
        for it in approach_result["items"]:
            v = it.get("combined_verdict", "WARN")
            if v == "PASS":
                total_pass += 1
            elif v == "FAIL":
                total_fail += 1
            else:
                total_warn += 1
        dv = approach_result.get("domain_review", {}).get("verdict", "WARN")
        if dv == "PASS":
            total_pass += 1
        elif dv == "FAIL":
            total_fail += 1
        else:
            total_warn += 1

        report["approaches"].append(approach_result)

    report["summary"] = {
        "approaches": len(approaches),
        "items_reviewed": sum(len(a["items"]) for a in report["approaches"]),
        "pass": total_pass,
        "warn": total_warn,
        "fail": total_fail,
        "duration_s": round(time.time() - started, 1),
    }

    if save:
        _KNOWLEDGE.mkdir(parents=True, exist_ok=True)
        _REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md = render_markdown_report(report)
        _REPORT_MD.write_text(md, encoding="utf-8")
        if desktop_copy:
            desktop = Path(r"C:\Users\Admin\Desktop\Heroik_Wissenschaft_Claude_Science_Audit.md")
            try:
                desktop.write_text(md, encoding="utf-8")
                report["desktop_path"] = str(desktop)
            except Exception as exc:
                report["desktop_error"] = str(exc)

    report["report_json"] = str(_REPORT_JSON)
    report["report_md"] = str(_REPORT_MD)
    return report


def _combine_verdict(local: Optional[str], claude: Optional[str]) -> str:
    order = {"FAIL": 3, "WARN": 2, "PASS": 1, "OFFLINE": 0}
    a = order.get((local or "WARN").upper(), 2)
    if (claude or "").upper() == "OFFLINE":
        return {3: "FAIL", 2: "WARN", 1: "PASS"}[a]
    b = order.get((claude or "WARN").upper(), 2)
    worst = max(a, b)
    return {3: "FAIL", 2: "WARN", 1: "PASS"}[worst]


def render_markdown_report(report: Dict[str, Any]) -> str:
    lines = [
        "# Heroik — Claude Science Audit",
        "### Formale Mathematik + heroische Wissenschaftsansätze",
        "",
        f"> **Stand:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(report.get('ts', time.time())))}",
        f"> **Claude Science konfiguriert:** {report.get('configured')}",
        f"> **Backend:** {report.get('claude_science', {}).get('model', '?')}",
        "",
        "## Zusammenfassung",
        "",
        f"| Metrik | Wert |",
        f"|--------|------|",
        f"| Ansätze geprüft | {report['summary'].get('approaches', 0)} |",
        f"| Einträge geprüft | {report['summary'].get('items_reviewed', 0)} |",
        f"| PASS | {report['summary'].get('pass', 0)} |",
        f"| WARN | {report['summary'].get('warn', 0)} |",
        f"| FAIL | {report['summary'].get('fail', 0)} |",
        f"| Dauer | {report['summary'].get('duration_s', 0)} s |",
        "",
    ]

    for ap in report.get("approaches", []):
        lines += [f"## {ap['title']}", "", f"**ID:** `{ap['id']}` · **Domäne:** {ap.get('dom')} · **Einträge:** {ap.get('n_items')}", ""]
        dr = ap.get("domain_review") or {}
        if dr:
            lines += [
                f"### Domänen-Verdict: **{dr.get('verdict', '?')}** ({dr.get('backend', '?')})",
                "",
                dr.get("response", "(keine Antwort)")[:4000],
                "",
            ]
        for it in ap.get("items", []):
            lines += [
                f"### {it.get('name')}",
                f"- **Formel:** `{it.get('formula', '')}`",
                f"- **Kategorie:** {it.get('current', it.get('cat'))}",
                f"- **Combined Verdict:** **{it.get('combined_verdict')}**",
                f"- **Lokal (FormalMath/PeerReview):** {it.get('local', {}).get('verdict')} — {it.get('local', {}).get('reason', '')}",
                f"- **Claude Science:** {it.get('claude', {}).get('verdict')} ({it.get('claude', {}).get('backend')})",
                "",
            ]
            claude_text = (it.get("claude") or {}).get("response", "")
            if claude_text and len(claude_text) < 2500:
                lines += [claude_text, ""]
        lines.append("---\n")

    lines += [
        "## Methodik",
        "",
        "1. **Lokal:** FormalMathematicsCoreModule + PeerReviewCoreModule + Drift-Heuristik (hero-guide)",
        "2. **Claude Science:** Anthropic API — formale Überprüfung, Evidenz, Metapher-als-Beweis-Schutz",
        "3. **Combined Verdict:** konservatives Maximum (FAIL > WARN > PASS)",
        "",
        "*Modell — kein Satz. Audit ersetzt keine Peer-Review-Gates des Cores.*",
    ]
    return "\n".join(lines)


def status() -> Dict[str, Any]:
    guide = load_hero_guide()
    return {
        "module": "heroic_science_audit",
        "approaches": len(HEROIC_SCIENCE_APPROACHES),
        "hero_guide_entries": len(guide),
        "math_entries": sum(1 for g in guide if g.get("dom") == "Math"),
        "report_json": str(_REPORT_JSON) if _REPORT_JSON.exists() else None,
        "report_md": str(_REPORT_MD) if _REPORT_MD.exists() else None,
        "approach_ids": [a["id"] for a in HEROIC_SCIENCE_APPROACHES],
    }


def load_last_report() -> Optional[Dict[str, Any]]:
    if not _REPORT_JSON.exists():
        return None
    return json.loads(_REPORT_JSON.read_text(encoding="utf-8"))