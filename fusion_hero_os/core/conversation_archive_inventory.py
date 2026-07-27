"""
Conversation archives across instances — inventory for Dissertation-as-OS.

Scans ~/.grok/sessions and related roots. Records *what exists* (structure,
counts, mtimes) without dumping private chat bodies into public docs.

Inside-out: identity of sessions → instance roots → session folders → artifact types.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from urllib.parse import unquote

__all__ = ["scan_conversation_archives", "write_dissertation_appendix", "status"]

SESSIONS_ROOT = Path.home() / ".grok" / "sessions"


def _author_display() -> str:
    """Publication author or abstract Operator — person extracted from role."""
    try:
        from fusion_hero_os.core.operator_identity import author_for_publication

        a = author_for_publication()
        if a.get("bound") and a.get("display"):
            return str(a["display"])
    except Exception:  # noqa: BLE001
        pass
    return "Operator"

# Known artifact filenames inside a session dir
ARTIFACT_NAMES = {
    "chat_history.jsonl": "dialog_stream",
    "events.jsonl": "event_stream",
    "updates.jsonl": "update_stream",
    "summary.json": "session_summary",
    "prompt_context.json": "prompt_context",
    "system_prompt.txt": "system_prompt",
    "rewind_points.jsonl": "rewind",
    "hunk_records.jsonl": "code_hunks",
    "plan.json": "plan",
    "plan_mode.json": "plan_mode",
    "signals.json": "signals",
    "resources_state.json": "resources",
    "announcement_state.json": "announcements",
}


def _decode_instance_key(name: str) -> str:
    """C%3A%5CProgram%20Files%5CGit → C:\\Program Files\\Git"""
    try:
        return unquote(name.replace("%5C", "\\").replace("%3A", ":").replace("+", " "))
    except Exception:
        return name


def _safe_public_path(p: str) -> str:
    home = str(Path.home())
    s = p.replace(home, "~")
    # collapse long worktree noise slightly
    return s


def scan_conversation_archives(
    sessions_root: Path | None = None,
) -> dict[str, Any]:
    root = sessions_root or SESSIONS_ROOT
    instances: list[dict[str, Any]] = []
    totals = defaultdict(int)
    session_count = 0
    bytes_total = 0

    if not root.is_dir():
        return {
            "ok": False,
            "error": f"sessions root missing: {root}",
            "instances": [],
            "totals": {},
        }

    for inst_dir in sorted(root.iterdir()):
        if not inst_dir.is_dir():
            if inst_dir.name == "session_search.sqlite":
                totals["session_search_db"] = 1
            continue
        if inst_dir.name.startswith("."):
            continue

        decoded = _decode_instance_key(inst_dir.name)
        sessions: list[dict[str, Any]] = []
        inst_bytes = 0
        inst_files = 0
        artifact_counts: dict[str, int] = defaultdict(int)

        # instance-level prompt history
        ph = inst_dir / "prompt_history.jsonl"
        inst_meta: dict[str, Any] = {
            "instance_key": inst_dir.name,
            "instance_path_decoded": decoded,
            "instance_path_public": _safe_public_path(decoded),
            "has_prompt_history": ph.is_file(),
        }

        for child in sorted(inst_dir.iterdir()):
            if child.is_file():
                inst_files += 1
                try:
                    inst_bytes += child.stat().st_size
                except OSError:
                    pass
                continue
            if not child.is_dir():
                continue
            # session UUID-like or subagent id
            sid = child.name
            sess: dict[str, Any] = {
                "session_id": sid,
                "artifacts": {},
                "subdirs": [],
                "file_count": 0,
                "bytes": 0,
                "mtime_max": 0.0,
            }
            for dirpath, dirnames, filenames in os.walk(child):
                rel_base = Path(dirpath).relative_to(child)
                if rel_base.parts:
                    top = rel_base.parts[0]
                    if top not in sess["subdirs"] and top not in (
                        "__pycache__",
                    ):
                        sess["subdirs"].append(top)
                for fn in filenames:
                    fp = Path(dirpath) / fn
                    sess["file_count"] += 1
                    inst_files += 1
                    try:
                        st = fp.stat()
                        sess["bytes"] += st.st_size
                        inst_bytes += st.st_size
                        sess["mtime_max"] = max(sess["mtime_max"], st.st_mtime)
                    except OSError:
                        pass
                    kind = ARTIFACT_NAMES.get(fn)
                    if kind:
                        sess["artifacts"][kind] = sess["artifacts"].get(kind, 0) + 1
                        artifact_counts[kind] += 1
                    elif fn.endswith(".jsonl"):
                        artifact_counts["other_jsonl"] += 1
                    elif fn.endswith(".log"):
                        artifact_counts["terminal_log"] += 1
                    elif fn.endswith(".md") and "compaction" in str(fp):
                        artifact_counts["compaction_md"] += 1

            if sess["mtime_max"]:
                sess["mtime_iso"] = datetime.fromtimestamp(
                    sess["mtime_max"], tz=UTC
                ).isoformat()
            sessions.append(sess)
            session_count += 1

        # role hint from path
        role = "unknown"
        dlow = decoded.lower()
        if "program files" in dlow and "git" in dlow:
            role = "git_workspace_session"
        elif "desktop" in dlow and "dashboard" in dlow:
            role = "desktop_dashboard_instance"
        elif "worktrees" in dlow or "best-fuhos" in dlow:
            role = "worktree_agent_instance"
        elif "windows\\system32" in dlow or "system32" in dlow:
            role = "system32_cwd_session"
        elif decoded.rstrip("\\").endswith("Admin") or dlow.endswith("\\admin"):
            role = "user_home_session"
        elif dlow.endswith(":\\") or re.match(r"^[a-z]:\\?$", dlow, re.I):
            role = "drive_root_session"

        instances.append(
            {
                **inst_meta,
                "role_hint": role,
                "session_count": len(sessions),
                "file_count": inst_files,
                "bytes": inst_bytes,
                "artifact_totals": dict(artifact_counts),
                "sessions": sessions,
            }
        )
        bytes_total += inst_bytes
        totals["instances"] += 1

    totals["sessions"] = session_count
    totals["bytes"] = bytes_total
    totals["chat_history_files"] = sum(
        inst.get("artifact_totals", {}).get("dialog_stream", 0) for inst in instances
    )

    # dissertation framing
    report = {
        "ok": True,
        "method": "inside_out_multi_instance",
        "principle": (
            "Conversation archives on diverse instances are organs of the living dissertation "
            "(Dissertation-as-OS). Inventory records existence and structure; full chat bodies "
            "stay operator-local (privacy + volume)."
        ),
        "scanned_at": datetime.now(UTC).isoformat(),
        "sessions_root": _safe_public_path(str(root)),
        "vocabulary": {
            "deploy": "private (archives stay local)",
            "push": "public (structure + counts only)",
            "merge": "both via dual timeline",
        },
        "totals": dict(totals),
        "instances": instances,
        "canonical_names": {
            # Author legal name is extracted from Operator role (membrane).
            # Runtime uses role=operator; publication name only if vault binds.
            "author": _author_display(),
            "operator_role": "operator",
            "platform": "Fusion Hero OS v10.0.0",
            "field": "Autopoietische Autopolitik / Autopoietic Autopolitics",
        },
    }
    return report


def write_dissertation_appendix(report: dict[str, Any] | None = None) -> dict[str, str]:
    """Write public-safe appendix for dissertation + private full JSONL."""
    report = report or scan_conversation_archives()
    out_priv = Path.home() / ".fusion" / "inventory" / "conversation_archives"
    out_priv.mkdir(parents=True, exist_ok=True)
    full_path = out_priv / "conversation_archives_full.json"
    full_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # public appendix (no chat bodies)
    diss = Path(__file__).resolve().parents[2] / "docs" / "dissertation" / "anhaenge"
    diss.mkdir(parents=True, exist_ok=True)
    md_path = diss / "A11_Konversationsarchive_Multi_Instanz.md"

    lines = [
        "# A11 — Konversationsarchive auf mehreren Instanzen",
        "",
        f"**Operator-Rolle:** operator · **Autor-Kontext:** {_author_display()}  ",
        "**Plattform:** Fusion Hero OS v10.0.0  ",
        "**Feld:** Autopoietische Autopolitik / Autopoietic Autopolitics  ",
        "**Geltung:** Spezifikation (Inventar) · Dialoginhalte bleiben **privat** (deploy)  ",
        f"**Erfasst:** {report.get('scanned_at')}",
        "",
        "> Person (legal name) is **extracted** from the Operator role via ",
        "> `fusion_hero_os.core.operator_identity` — runtime never requires it.",
        "",
        "## Synthese",
        "",
        "Die Dissertation *ist* Fusion Hero OS. Konversationsarchive auf verschiedenen ",
        "Instanzen (Arbeitsverzeichnisse, Worktrees, Dashboard-Pfade, System-CWDs) sind ",
        "**Ausdrucksorgane** der gleichen Arbeit — analog zu Mesh-Knoten und Horkruxen: ",
        "verteilt gespeichert, inhaltlich auf die Autopoiesis der Theorie bezogen.",
        "",
        "Diese Anlage inventarisiert **was existiert** (Inside-Out, speicherort-agnostisch) ",
        "und **verbindet** die Instanzen über den dualen Zeitstrahl (merge). ",
        "Volltexte der Chats werden **nicht** in die öffentliche Monographie übernommen ",
        "(Privacy, Volumen, Code Honesty).",
        "",
        "## Ops-Vokabeln",
        "",
        "| Op | Bedeutung für Archive |",
        "|----|------------------------|",
        "| **deploy** | privat — Seal/Index lokal unter `~/.fusion/inventory/conversation_archives/` |",
        "| **push** | public — nur Struktur, Zählungen, Rollen-Hints, diese Anlage A11 |",
        "| **merge** | beide — public display/MasterSeed ↔ private Session-Refs ↔ Timeline t∥τ |",
        "",
        "## Gesamtsummen",
        "",
    ]
    tot = report.get("totals") or {}
    lines += [
        f"- **Instanzen (CWD-Wurzeln):** {tot.get('instances', 0)}",
        f"- **Sessions:** {tot.get('sessions', 0)}",
        f"- **Bytes (roh):** {tot.get('bytes', 0)}",
        f"- **chat_history.jsonl (Dialog-Streams):** {tot.get('chat_history_files', 0)}",
        "",
        "## Instanzen (Rollen-Hints)",
        "",
        "| Rolle (Hint) | Decodierter Pfad (public-safe) | Sessions | Dateien | Bytes |",
        "|--------------|--------------------------------|----------|---------|-------|",
    ]
    for inst in report.get("instances") or []:
        lines.append(
            f"| {inst.get('role_hint')} | `{inst.get('instance_path_public')}` | "
            f"{inst.get('session_count')} | {inst.get('file_count')} | {inst.get('bytes')} |"
        )

    lines += [
        "",
        "## Typische Artefakte je Session",
        "",
        "| Datei | Bedeutung |",
        "|-------|-----------|",
    ]
    for fn, kind in ARTIFACT_NAMES.items():
        lines.append(f"| `{fn}` | {kind} |")
    lines += [
        "| `terminal/*.log` | Werkzeug-/Shell-Spuren |",
        "| `compaction/segment_*.md` | komprimierte Segment-Archive |",
        "| `subagents/*` | Subagenten-Transcripts |",
        "",
        "## Artifact-Zählungen (aggregiert)",
        "",
    ]
    agg: dict[str, int] = defaultdict(int)
    for inst in report.get("instances") or []:
        for k, v in (inst.get("artifact_totals") or {}).items():
            agg[k] += int(v)
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
        lines.append(f"- **{k}:** {v}")

    lines += [
        "",
        "## Verbindung zur Dissertation",
        "",
        "1. **Autopoiesis:** Sessions erzeugen fortlaufend State (history, compaction, tools).  ",
        "2. **Autopolitik:** Placement — Dialoge bleiben L1/operator-local; public nur Index.  ",
        "3. **Dissertation-as-OS:** Multi-Instanz-Archive = verteilte Organe desselben Werks.  ",
        "4. **Dual Timeline:** Session-`mtime` speist real t; strukturelle Rolle speist τ.  ",
        "5. **MasterSeed public:** MS-PUB-… bleibt eindeutig; private Session-Bodies nie im Push.  ",
        "",
        "## Ausführliche Session-Tabelle (ohne Dialogtext)",
        "",
    ]
    for inst in report.get("instances") or []:
        lines.append(f"### Instanz: `{inst.get('instance_path_public')}` ({inst.get('role_hint')})")
        lines.append("")
        lines.append("| session_id | files | bytes | artifacts | mtime |")
        lines.append("|------------|------:|------:|-----------|-------|")
        for s in inst.get("sessions") or []:
            arts = ",".join(sorted((s.get("artifacts") or {}).keys())) or "—"
            lines.append(
                f"| `{s.get('session_id')}` | {s.get('file_count')} | {s.get('bytes')} | "
                f"{arts} | {s.get('mtime_iso', '—')} |"
            )
        lines.append("")

    lines += [
        "## Private Vollform",
        "",
        f"Operator-lokal: `{full_path}` (nicht für Academia/GitHub-Push der Rohdialoge).",
        "",
        "**Vermerk:** [MAINFRAME · Dissertation-as-OS · Konversationsarchive multi-instanz · deploy=private]",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # short JSON for docs (public)
    pub = {
        "ok": report.get("ok"),
        "scanned_at": report.get("scanned_at"),
        "totals": report.get("totals"),
        "instances": [
            {
                "role_hint": i.get("role_hint"),
                "path_public": i.get("instance_path_public"),
                "session_count": i.get("session_count"),
                "file_count": i.get("file_count"),
                "bytes": i.get("bytes"),
                "artifact_totals": i.get("artifact_totals"),
            }
            for i in (report.get("instances") or [])
        ],
        "appendix": "docs/dissertation/anhaenge/A11_Konversationsarchive_Multi_Instanz.md",
        "principle": report.get("principle"),
    }
    pub_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "dissertation"
        / "conversation_archives_index.json"
    )
    pub_path.write_text(json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "appendix_md": str(md_path),
        "public_index": str(pub_path),
        "private_full": str(full_path),
    }


def status() -> dict[str, Any]:
    p = Path.home() / ".fusion" / "inventory" / "conversation_archives" / "conversation_archives_full.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return {
                "ok": True,
                "totals": data.get("totals"),
                "instances": len(data.get("instances") or []),
                "scanned_at": data.get("scanned_at"),
            }
        except Exception:
            pass
    return {"ok": False, "error": "no scan yet"}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2))
        return 0
    report = scan_conversation_archives()
    paths = write_dissertation_appendix(report)
    print(
        json.dumps(
            {
                "ok": report.get("ok"),
                "totals": report.get("totals"),
                "instances": len(report.get("instances") or []),
                "paths": paths,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
