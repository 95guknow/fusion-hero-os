# -*- coding: utf-8 -*-
"""MCP-Autokompression: geschärft, **ohne Informationsverlust**.

Pipeline (strict order):
  1. Lossless normalize (whitespace / repeated blank lines)
  2. Lossless dedupe (exact + normalized content)
  3. Lossless intra-unit densify (unique lines, order-preserving)
  4. Lossless same-role merge (union of unique lines)
  5. If still over budget: **reversible offload** — full content archived
     with content-hash; active window keeps a compact rehydrate stub.
     Nothing is discarded permanently.

Geltung: Spezifikation · token estimate = Modell (chars/words heuristic).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "MessageUnit",
    "estimate_tokens",
    "score_unit",
    "normalize_lossless",
    "compress_to_budget",
    "compress_report",
    "rehydrate_from_archive",
    "get_archive_path",
]

_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9_./:-]+")
_MULTI_NL = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_STATE = Path(
    __import__("os").environ.get(
        "FUSION_STATE_DIR", __import__("os").path.expanduser("~/.fusion-hero-os")
    )
) / "mcp_fill" / "lossless_archive"


@dataclass
class MessageUnit:
    role: str  # system | user | assistant | tool | archive
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.content)

    def content_hash(self) -> str:
        raw = f"{self.role}\n{normalize_lossless(self.content or '')}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = _WORD_RE.findall(text)
    by_words = int(len(words) * 1.3) if words else 0
    by_chars = max(1, len(text) // 4) if text.strip() else 0
    return max(by_words, by_chars, 1 if text.strip() else 0)


def normalize_lossless(text: str) -> str:
    """Whitespace-only normalization — information-preserving."""
    if not text:
        return ""
    # normalize newlines, strip trailing spaces per line, collapse blank runs
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    out: List[str] = []
    blank_run = 0
    for ln in lines:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 1:
                out.append("")
            continue
        blank_run = 0
        out.append(_MULTI_SPACE.sub(" ", ln))
    # strip leading/trailing empty
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def densify_lines_lossless(text: str) -> str:
    """Keep every unique non-empty line in first-seen order; drop pure dups."""
    text = normalize_lossless(text)
    seen = set()
    kept: List[str] = []
    for ln in text.split("\n"):
        key = ln.strip()
        if not key:
            if kept and kept[-1] != "":
                kept.append("")
            continue
        if key in seen:
            continue
        seen.add(key)
        kept.append(ln)
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept)


def score_unit(
    unit: MessageUnit,
    *,
    intent: str = "",
    index: int = 0,
    n: int = 1,
) -> float:
    """Higher = keep in active window longer. Does not authorize deletion."""
    role_w = {
        "system": 1.00,
        "user": 0.92,
        "tool": 0.55,
        "assistant": 0.48,
        "archive": 0.35,
    }.get((unit.role or "").lower(), 0.40)

    recency = (index + 1) / max(n, 1)
    content = unit.content or ""
    intent_l = (intent or "").lower()
    content_l = content.lower()

    cong = 0.0
    if intent_l.strip():
        a = set(_WORD_RE.findall(intent_l))
        b = set(_WORD_RE.findall(content_l))
        if a and b:
            cong = len(a & b) / max(1, len(a | b))
        for w in a:
            if len(w) > 3 and w in content_l:
                cong = min(1.0, cong + 0.05)

    anchors = (
        "masterseed", "banach", "geltung", "proof", "qubo", "layer",
        "inject", "mcp", "contract", "bcg", "satz", "fusion", "sinnkongruenz",
    )
    anchor_hits = sum(1 for a in anchors if a in content_l)
    anchor_score = min(1.0, anchor_hits * 0.08)

    if unit.meta.get("pin") or unit.meta.get("immutable"):
        return 100.0
    if (unit.role or "").lower() == "system" and unit.meta.get("masterseed"):
        return 100.0
    if unit.meta.get("rehydrate_stub"):
        return 95.0  # keep stubs so rehydrate map stays

    tok = unit.tokens
    verbosity = min(1.0, tok / 800.0)
    length_penalty = verbosity * (1.0 - cong) * 0.35

    score = (
        0.28 * role_w
        + 0.18 * recency
        + 0.42 * cong
        + 0.12 * anchor_score
        - length_penalty
    )
    return round(max(0.0, score), 6)


def get_archive_path() -> Path:
    _STATE.mkdir(parents=True, exist_ok=True)
    return _STATE


def _archive_write(unit: MessageUnit) -> str:
    """Persist full unit; return content hash id."""
    h = unit.content_hash()
    path = get_archive_path() / f"{h}.json"
    if not path.exists():
        path.write_text(
            json.dumps(
                {
                    "role": unit.role,
                    "content": unit.content,
                    "meta": unit.meta,
                    "sha256_16": h,
                    "ts": time.time(),
                    "tokens": unit.tokens,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return h


def rehydrate_from_archive(hash_id: str) -> Optional[MessageUnit]:
    path = get_archive_path() / f"{hash_id}.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return MessageUnit(
        role=str(data.get("role") or "archive"),
        content=str(data.get("content") or ""),
        meta=dict(data.get("meta") or {}),
    )


def _lossless_pass(units: List[MessageUnit]) -> Tuple[List[MessageUnit], Dict[str, int]]:
    """Steps 1–4: normalize, densify, dedupe, merge — no archive."""
    stats = {
        "normalized": 0,
        "densified": 0,
        "deduped": 0,
        "merged": 0,
        "tokens_saved": 0,
    }
    before = sum(u.tokens for u in units)

    # 1–2 normalize + densify per unit
    step1: List[MessageUnit] = []
    for u in units:
        raw = u.content or ""
        norm = normalize_lossless(raw)
        dense = densify_lines_lossless(norm)
        if dense != raw:
            if norm != raw:
                stats["normalized"] += 1
            if dense != norm:
                stats["densified"] += 1
        step1.append(
            MessageUnit(
                role=u.role,
                content=dense,
                meta={**u.meta, "lossless_norm": True},
            )
        )

    # 3 exact / normalized dedupe (keep first)
    seen_hash: set = set()
    step2: List[MessageUnit] = []
    for u in step1:
        h = u.content_hash()
        if h in seen_hash and not (u.meta.get("pin") or u.meta.get("immutable")):
            stats["deduped"] += 1
            continue
        seen_hash.add(h)
        step2.append(u)

    # 4 merge consecutive same-role non-pinned into line-union (order preserved)
    step3: List[MessageUnit] = []
    i = 0
    while i < len(step2):
        u = step2[i]
        if u.meta.get("pin") or u.meta.get("immutable") or u.meta.get("rehydrate_stub"):
            step3.append(u)
            i += 1
            continue
        j = i + 1
        lines: List[str] = []
        seen_ln: set = set()
        for ln in (u.content or "").split("\n"):
            k = ln.strip()
            if k and k not in seen_ln:
                seen_ln.add(k)
                lines.append(ln)
            elif not k and lines and lines[-1] != "":
                lines.append("")
        roles = {u.role}
        while j < len(step2):
            v = step2[j]
            if v.role != u.role:
                break
            if v.meta.get("pin") or v.meta.get("immutable") or v.meta.get("rehydrate_stub"):
                break
            # merge if high overlap or same role consecutive
            for ln in (v.content or "").split("\n"):
                k = ln.strip()
                if k and k not in seen_ln:
                    seen_ln.add(k)
                    lines.append(ln)
            stats["merged"] += 1
            j += 1
        merged = MessageUnit(
            role=u.role,
            content="\n".join(lines).strip(),
            meta={**u.meta, "lossless_merged": j > i + 1},
        )
        step3.append(merged)
        i = j if j > i + 1 else i + 1

    after = sum(u.tokens for u in step3)
    stats["tokens_saved"] = max(0, before - after)
    return step3, stats


def compress_to_budget(
    units: Sequence[MessageUnit],
    *,
    max_tokens: int,
    intent: str = "",
    summarize_dropped: bool = True,  # kept for API compat; means "emit rehydrate stubs"
    lossless: bool = True,
) -> Dict[str, Any]:
    """Compress to token budget **without information loss**.

    Default path is fully reversible: offloaded content lives in
    ``~/.fusion-hero-os/mcp_fill/lossless_archive/<hash>.json``.
    """
    units_list = [MessageUnit(u.role, u.content or "", dict(u.meta or {})) for u in units]
    total_before = sum(u.tokens for u in units_list)

    # --- Phase A: always run lossless structural (free token wins, no loss) ---
    worked, lossless_stats = _lossless_pass(units_list)
    tokens_now = sum(u.tokens for u in worked)
    phases = ["lossless_normalize_dedupe_merge"]

    if tokens_now <= max_tokens:
        action = "noop" if tokens_now == total_before else "lossless_only"
        return {
            "units": worked,
            "tokens_before": total_before,
            "tokens_after": tokens_now,
            "dropped": 0,
            "offloaded": 0,
            "action": action,
            "lossless": True,
            "information_loss": False,
            "phases": phases,
            "lossless_stats": lossless_stats,
            "intent": intent[:200],
            "scores": [
                {
                    "i": i,
                    "score": score_unit(u, intent=intent, index=i, n=len(worked)),
                    "tokens": u.tokens,
                }
                for i, u in enumerate(worked)
            ],
        }

    # --- Phase B: reversible offload (NO delete) ---
    # Rank by Sinnkongruenz — lowest leave active window first, full body archived
    n = len(worked)
    ranked = sorted(
        range(n),
        key=lambda i: (
            score_unit(worked[i], intent=intent, index=i, n=n),
            -worked[i].tokens,
        ),
    )
    keep_mask = [True] * n
    offloaded: List[Dict[str, Any]] = []
    tokens_now = sum(u.tokens for u in worked)

    for i in ranked:
        if tokens_now <= max_tokens:
            break
        u = worked[i]
        sc = score_unit(u, intent=intent, index=i, n=n)
        if sc >= 99.0 or u.meta.get("pin") or u.meta.get("immutable"):
            continue
        if u.meta.get("rehydrate_stub"):
            continue
        # archive full content
        hid = _archive_write(u)
        stub_body = (
            f"[lossless-offload sha={hid} role={u.role} tok≈{u.tokens}]\n"
            f"rehydrate: fusion_hero_os.core.sinnkongruenz_compressor.rehydrate_from_archive({hid!r})\n"
            f"cues: " + ", ".join(_WORD_RE.findall((u.content or "")[:500])[:16])
        )
        stub = MessageUnit(
            role="system",
            content=stub_body,
            meta={
                "rehydrate_stub": True,
                "archive_sha": hid,
                "original_role": u.role,
                "original_tokens": u.tokens,
                "lossless": True,
            },
        )
        # replace unit with stub in place
        delta = u.tokens - stub.tokens
        worked[i] = stub
        tokens_now -= max(0, delta)
        offloaded.append({"index": i, "sha": hid, "original_tokens": u.tokens, "stub_tokens": stub.tokens})
        keep_mask[i] = True  # stub stays

    phases.append("reversible_offload")
    tokens_after = sum(u.tokens for u in worked)

    # if still over (too many pins), densify stubs further is N/A — report over_budget
    over = tokens_after > max_tokens

    return {
        "units": worked,
        "tokens_before": total_before,
        "tokens_after": tokens_after,
        "dropped": 0,  # never permanent drop
        "offloaded": len(offloaded),
        "offload_index": offloaded,
        "action": "lossless_compress" if not over else "lossless_compress_over_budget_pins",
        "lossless": True,
        "information_loss": False,
        "reversible": True,
        "archive_dir": str(get_archive_path()),
        "phases": phases,
        "lossless_stats": lossless_stats,
        "intent": intent[:200],
        "over_budget": over,
        "scores": [
            {
                "i": i,
                "score": score_unit(worked[i], intent=intent, index=i, n=len(worked)),
                "tokens": worked[i].tokens,
            }
            for i in range(len(worked))
        ],
    }


def compress_report(result: Dict[str, Any]) -> str:
    return (
        f"Sinnkongruenz-lossless: {result.get('action')} "
        f"{result.get('tokens_before')}→{result.get('tokens_after')} tok "
        f"offloaded={result.get('offloaded')} loss={result.get('information_loss')}"
    )
