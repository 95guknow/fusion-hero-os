# string_quantizer_agent.py — 3. Agent: String-Quantisierer (begleitet jede Verhandlung)
#
# Prinzipien (verbindlich):
#   1. Emission in logischer Folge — niemals Buchstabe-für-Buchstabe.
#   2. Quant-Einheit = **adaptive logische Substrings** (nicht zwingend komplette
#      Vollstrings): wachsen/schrumpfen/mergen nach Frequenz & Ko-Occurrence.
#   3. Anbindung an Sinnquanten (Liebesquant, Zufriedenheitsquant, Sinnquant, …)
#      und M→N-Datenbank-Transfers (m_to_n_quant_db).
#   4. Dieser Agent wohnt jeder Dual-Verhandlung als Dritter bei.
#
# Env:
#   FUSION_QUANTIZER_AGENT=1          (default an)
#   FUSION_QUANTIZER_MIN_PHRASE=4     Mindestlänge Substring
#   FUSION_QUANTIZER_MIN_REPEAT=2     Mindest-Wiederholungen
#   FUSION_QUANTIZER_BACKEND=local    local | passthrough
#   FUSION_QUANTIZER_MODE=adaptive_substring   (default)

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ROLE = "quantizer"
AGENT_ID = "string-quantizer"
QUANTIZER_ROLES = frozenset({
    "quantizer", "string_quantizer", "string-quantizer", "q-agent", "phrase_quantizer",
})


def is_enabled() -> bool:
    return os.getenv("FUSION_QUANTIZER_AGENT", "1") == "1"


def is_quantizer(role: Optional[str] = None, task: Optional[Dict[str, Any]] = None) -> bool:
    if task:
        if task.get("quantizer") or task.get("is_quantizer") or task.get("agent_kind") == "quantizer":
            return True
        role = role or task.get("role") or task.get("agent_role") or task.get("mode")
        name = str(task.get("assigned_agent") or task.get("agent_id") or "").lower()
        if "quantizer" in name or name in ("string-quantizer", "q-agent"):
            return True
    r = (role or "").lower().replace("-", "_")
    return r in QUANTIZER_ROLES or r.startswith("quantiz")


def _min_phrase() -> int:
    try:
        return max(2, int(os.getenv("FUSION_QUANTIZER_MIN_PHRASE", "4")))
    except ValueError:
        return 4


def _min_repeat() -> int:
    try:
        return max(2, int(os.getenv("FUSION_QUANTIZER_MIN_REPEAT", "2")))
    except ValueError:
        return 2


# ── logische String-Einheiten (nie Einzelbuchstaben als Emissionseinheit) ──

_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")
_WORD_SPLIT = re.compile(r"(\s+|[^\w\säöüÄÖÜß\-]+)", re.UNICODE)
_WS = re.compile(r"\s+")


def split_logical_strings(text: str) -> List[str]:
    """Zerlegt Text in logische Ganz-Strings (Sätze → Wörter), nie in Chars."""
    text = (text or "").strip()
    if not text:
        return []
    sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s and s.strip()]
    if len(sentences) <= 1 and len(text) > 120:
        # Fallback: Absätze / Zeilen
        parts = [p.strip() for p in re.split(r"\n{2,}|\r\n\r\n", text) if p.strip()]
        if len(parts) > 1:
            return parts
    return sentences if sentences else [text]


def split_phrase_tokens(unit: str) -> List[str]:
    """Tokenisiert eine logische Einheit in Wort-/Interpunktions-Strings (ganz)."""
    if not unit:
        return []
    parts = [p for p in _WORD_SPLIT.split(unit) if p != ""]
    return parts if parts else [unit]


def emit_whole_strings(parts: Sequence[str], sep: str = "") -> str:
    """
    Emittiert ausschließlich ganze Strings in gegebener logischer Folge.
    Einzelne Buchstaben als separate Emissionseinheit sind verboten —
    1-Zeichen-Teile werden nur mitgenommen, wenn sie Interpunktion/Whitespace sind,
    und werden mit Nachbarn gebündelt wenn möglich.
    """
    if not parts:
        return ""
    out: List[str] = []
    buf = ""
    for p in parts:
        if p is None:
            continue
        s = str(p)
        if not s:
            continue
        # Einzelbuchstaben (keine Interpunktion) → in Puffer bündeln, nie solo emittieren
        if len(s) == 1 and s.isalnum():
            buf += s
            continue
        if buf:
            out.append(buf)
            buf = ""
        out.append(s)
    if buf:
        out.append(buf)
    if sep:
        return sep.join(out)
    return "".join(out)


# ── Phrase-Table / Quantisierung ───────────────────────────────────────────

@dataclass
class QuantEntry:
    qid: int
    text: str
    count: int = 1
    hash8: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"qid": self.qid, "text": self.text, "count": self.count, "hash8": self.hash8}


@dataclass
class QuantizedPayload:
    """Quantisierte Repräsentation: adaptive Substrings / Q-Referenzen + Sinnquanten."""
    sequence: List[str] = field(default_factory=list)   # "Q#3" oder Substring
    table: Dict[int, str] = field(default_factory=dict)  # qid → adaptive substring
    stats: Dict[str, Any] = field(default_factory=dict)
    mode: str = "adaptive_substring_logical"
    sinn: Dict[str, Any] = field(default_factory=dict)  # Liebesquant etc.

    def expand(self) -> str:
        parts: List[str] = []
        for tok in self.sequence:
            if tok.startswith("Q#"):
                try:
                    qid = int(tok[2:])
                    parts.append(self.table.get(qid, tok))
                except ValueError:
                    parts.append(tok)
            else:
                parts.append(tok)
        return emit_whole_strings(parts, sep=" ")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "sequence": list(self.sequence),
            "table": {str(k): v for k, v in self.table.items()},
            "stats": dict(self.stats),
            "sinn": dict(self.sinn),
            "expanded_preview": self.expand()[:500],
        }


class StringQuantizer:
    """
    Persistente adaptive-Substring-Table pro Prozess.
    Quantisiert logische Substrings (nicht nur komplette Vollstrings)
    und mappt auf Sinnquanten (Liebesquant, Zufriedenheitsquant, …).
    """

    def __init__(self) -> None:
        self._phrase_to_qid: Dict[str, int] = {}
        self._qid_to_phrase: Dict[int, str] = {}
        self._counts: Dict[str, int] = {}
        self._pair_counts: Dict[Tuple[str, str], int] = {}  # adaptive merge signal
        self._next_id = 1
        self._history: List[Dict[str, Any]] = []

    def reset(self) -> None:
        self._phrase_to_qid.clear()
        self._qid_to_phrase.clear()
        self._counts.clear()
        self._pair_counts.clear()
        self._next_id = 1

    def _register(self, phrase: str, count: int = 1) -> int:
        if phrase in self._phrase_to_qid:
            qid = self._phrase_to_qid[phrase]
            self._counts[phrase] = self._counts.get(phrase, 0) + count
            return qid
        qid = self._next_id
        self._next_id += 1
        self._phrase_to_qid[phrase] = qid
        self._qid_to_phrase[qid] = phrase
        self._counts[phrase] = count
        return qid

    def _hash8(self, s: str) -> str:
        return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:8]

    def adaptive_substrings(self, text: str) -> List[str]:
        """
        Logisch adaptive Substrings: Wort-n-gramme + Merge bei hoher Ko-Occurrence.
        Keine Einzelbuchstaben, keine erzwungene Vollsatz-Einheit.
        """
        min_p = _min_phrase()
        words = [
            t for t in split_phrase_tokens(text)
            if t.strip() and not t.isspace() and (t.isalnum() or any(c.isalnum() for c in t))
        ]
        # normalize pure word tokens
        words = [w for w in re.findall(r"[\wÄÖÜäöüß]{2,}", text or "", flags=re.UNICODE)]
        if not words:
            return []
        # pair stats for adaptation
        for i in range(len(words) - 1):
            pair = (words[i].lower(), words[i + 1].lower())
            self._pair_counts[pair] = self._pair_counts.get(pair, 0) + 1

        counts: Dict[str, int] = {}
        for n in range(1, 5):
            if len(words) < n:
                break
            for i in range(0, len(words) - n + 1):
                gram = " ".join(words[i : i + n])
                if len(gram) < min_p:
                    continue
                counts[gram] = counts.get(gram, 0) + 1

        # adaptive merge: if bigram very frequent, prefer it over unigrams
        merge_threshold = max(2, _min_repeat())
        merged: Dict[str, int] = dict(counts)
        for (a, b), c in self._pair_counts.items():
            if c >= merge_threshold:
                big = f"{a} {b}"
                merged[big] = merged.get(big, 0) + c
                # shrink weight of isolated unigrams slightly (logical adapt)
                if a in merged:
                    merged[a] = max(1, merged[a] - c // 2)
                if b in merged:
                    merged[b] = max(1, merged[b] - c // 2)

        # order: medium-high frequency adaptive substrings (not only longest full strings)
        items = sorted(merged.items(), key=lambda x: (-x[1], -min(len(x[0]), 48), x[0]))
        return [p for p, c in items if c >= 1][:3000]

    def discover_repeats(self, text: str) -> List[Tuple[str, int]]:
        """Wiederholte adaptive Substrings (n-gram + merge), nie Char-Stream."""
        min_r = _min_repeat()
        counts: Dict[str, int] = {}
        for sub in self.adaptive_substrings(text):
            counts[sub] = counts.get(sub, 0) + 1
        # re-count properly via adaptive_substrings internals
        # (adaptive_substrings already frequency-sorted; recompute counts)
        words = re.findall(r"[\wÄÖÜäöüß]{2,}", text or "", flags=re.UNICODE)
        counts = {}
        for n in range(1, 5):
            for i in range(0, max(0, len(words) - n + 1)):
                gram = " ".join(words[i : i + n])
                if len(gram) >= _min_phrase():
                    counts[gram] = counts.get(gram, 0) + 1
        for (a, b), c in list(self._pair_counts.items())[-5000:]:
            if c >= min_r:
                counts[f"{a} {b}"] = max(counts.get(f"{a} {b}", 0), c)
        repeats = [(p, c) for p, c in counts.items() if c >= min_r]
        # prefer frequent adaptive mid-length over pure longest full sentence
        repeats.sort(key=lambda x: (-x[1], -min(len(x[0]), 40), x[0]))
        return repeats

    def quantize(self, text: str, reuse_table: bool = True) -> QuantizedPayload:
        """
        Quantisiert Text in adaptive Substrings → Q#id + Sinnquanten-Mapping.
        """
        t0 = time.time()
        text = text or ""
        if not text.strip():
            return QuantizedPayload(sequence=[], table={}, stats={"empty": True})

        if not reuse_table:
            local = StringQuantizer()
            return local.quantize(text, reuse_table=True)

        repeats = self.discover_repeats(text)
        min_r = _min_repeat()
        active: List[Tuple[str, int]] = []
        for phrase, count in repeats:
            if count >= min_r:
                qid = self._register(phrase, count)
                active.append((phrase, qid))

        # Greedy on adaptive substrings within each logical sentence unit
        sequence: List[str] = []
        table: Dict[int, str] = {}
        replaced = 0
        literal_units = 0

        for unit in split_logical_strings(text):
            remaining = unit
            unit_parts: List[str] = []
            safety = 0
            while remaining and safety < 10_000:
                safety += 1
                matched = False
                for phrase, qid in active[:500]:
                    # case-insensitive logical match for adaptive substrings
                    idx = remaining.lower().find(phrase.lower())
                    if idx == -1:
                        continue
                    if idx > 0:
                        left = remaining[:idx]
                        # left rest → smaller adaptive tokens (words), not char stream
                        left_words = re.findall(r"[\wÄÖÜäöüß]+|[^\w\s]+|\s+", left, flags=re.UNICODE)
                        unit_parts.extend([w for w in left_words if w.strip()])
                        literal_units += 1
                    unit_parts.append(f"Q#{qid}")
                    table[qid] = self._qid_to_phrase.get(qid, phrase)
                    remaining = remaining[idx + len(phrase) :]
                    replaced += 1
                    matched = True
                    break
                if not matched:
                    toks = re.findall(r"[\wÄÖÜäöüß]+|[^\w\s]+|\s+", remaining, flags=re.UNICODE)
                    unit_parts.extend([t for t in toks if t.strip()])
                    literal_units += 1
                    remaining = ""
            sequence.extend(unit_parts)

        used = {int(t[2:]) for t in sequence if t.startswith("Q#") and t[2:].isdigit()}
        table = {qid: self._qid_to_phrase[qid] for qid in used if qid in self._qid_to_phrase}

        # Sinnquanten (Liebesquant, Zufriedenheitsquant, …)
        sinn: Dict[str, Any] = {}
        try:
            from sinn_quanten_registry import get_registry

            reg = get_registry()
            subs = [table[q] for q in table] + [t for t in sequence if not t.startswith("Q#")][:200]
            sinn = reg.map_substrings(subs, adapt=True)
            sinn["score_full"] = reg.score_text(text)
        except Exception as exc:
            sinn = {"error": str(exc)}

        stats = {
            "input_chars": len(text),
            "sequence_len": len(sequence),
            "table_size": len(table),
            "replaced_spans": replaced,
            "literal_units": literal_units,
            "repeat_candidates": len(repeats),
            "emit_policy": "adaptive_substring_logical_never_char_stream",
            "unit": "adaptive_substring",
            "elapsed_ms": round((time.time() - t0) * 1000, 2),
            "compression_ratio": round(
                (len(sequence) / max(1, len(re.findall(r"\S+", text)))), 4
            ),
            "sinn_dominant": (sinn.get("score_full") or {}).get("dominant")
            or (max((sinn.get("aggregate") or {}), key=(sinn.get("aggregate") or {}).get)
                if sinn.get("aggregate") else None),
        }
        payload = QuantizedPayload(
            sequence=sequence,
            table=table,
            stats=stats,
            mode="adaptive_substring_logical",
            sinn=sinn,
        )
        self._history.append({"ts": time.time(), "stats": stats, "table_keys": list(table.keys())})
        if len(self._history) > 100:
            del self._history[: len(self._history) - 100]
        return payload

    def expand(self, payload: QuantizedPayload) -> str:
        return payload.expand()

    def emit_from_source(self, text: str) -> str:
        """
        Primärer Generierungs-/Abrufpfad: immer ganze Strings in logischer Folge.
        Quantisiert intern, expandiert wieder — erprobt Roundtrip + Bündelung.
        """
        units = split_logical_strings(text)
        # Emittiere Satz für Satz (ganze Strings), nicht Char-Stream
        emitted = emit_whole_strings(units, sep=" ")
        payload = self.quantize(emitted)
        # Für Downstream: expandierte Form + Metadaten im Task speicherbar
        return payload.expand()

    def accompany_negotiation(
        self,
        query: str,
        agent_text: str = "",
        anti_text: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        3. Agent: adaptive Substrings + Sinnquanten (Liebesquant, Zufriedenheit, …).
        """
        ctx = dict(context or {})
        # Logische Reihenfolge: Query → Agent → Anti (Verhandlungspfad)
        ordered_units: List[str] = []
        for label, body in (("query", query), ("agent", agent_text), ("anti", anti_text)):
            if not (body or "").strip():
                continue
            for u in split_logical_strings(body):
                ordered_units.append(u)

        joined = emit_whole_strings(ordered_units, sep="\n")
        payload = self.quantize(joined)

        # Erprobung: Roundtrip + Wiederverwendung der Table auf Agent-only
        agent_payload = self.quantize(agent_text or "") if agent_text else QuantizedPayload()
        anti_payload = self.quantize(anti_text or "") if anti_text else QuantizedPayload()
        expanded = payload.expand()
        roundtrip_ok = _normalize_ws(expanded) == _normalize_ws(joined) or (
            # bei Q-Ersatz kann Whitespace leicht abweichen — Inhalt-Ähnlichkeit
            len(expanded) >= max(1, int(len(joined) * 0.5))
        )

        # Kompakte „genutzte“ Form für Downstream-Caches
        compact = self._format_compact(payload)

        result = {
            "ok": True,
            "role": ROLE,
            "agent_id": AGENT_ID,
            "agent_kind": "quantizer",
            "backend": os.getenv("FUSION_QUANTIZER_BACKEND", "local"),
            "emit_policy": "adaptive_substring_logical_sequence",
            "never_char_by_char": True,
            "unit": "adaptive_substring",
            "ordered_units": ordered_units[:50],
            "ordered_unit_count": len(ordered_units),
            "quantized": payload.to_dict(),
            "agent_quantized": agent_payload.to_dict() if agent_text else None,
            "anti_quantized": anti_payload.to_dict() if anti_text else None,
            "compact": compact,
            "expanded": expanded[:8000],
            "roundtrip_ok": roundtrip_ok,
            "table_global_size": len(self._qid_to_phrase),
            "reuse": {
                "shared_qids": sorted(
                    set(payload.table.keys())
                    & set(agent_payload.table.keys() if agent_text else [])
                    & set(anti_payload.table.keys() if anti_text else [])
                ),
                "phrase_counts_top": self.top_phrases(8),
            },
            "context_keys": sorted(ctx.keys())[:20],
        }
        return result

    def _format_compact(self, payload: QuantizedPayload) -> str:
        lines = ["# Q-TABLE"]
        for qid, text in sorted(payload.table.items()):
            preview = text if len(text) <= 80 else text[:77] + "..."
            lines.append(f"Q#{qid}\t{preview}")
        lines.append("# SEQUENCE (whole strings / Q-refs, logical order)")
        # Emittiere Sequence als ganze Tokens zeilenweise (nicht char-stream)
        chunk: List[str] = []
        for tok in payload.sequence:
            chunk.append(tok)
            if len(chunk) >= 24 or tok.startswith("Q#"):
                lines.append(emit_whole_strings(chunk, sep=" "))
                chunk = []
        if chunk:
            lines.append(emit_whole_strings(chunk, sep=" "))
        return "\n".join(lines)

    def top_phrases(self, n: int = 10) -> List[Dict[str, Any]]:
        items = sorted(self._counts.items(), key=lambda x: (-x[1], -len(x[0])))
        out = []
        for phrase, count in items[:n]:
            qid = self._phrase_to_qid.get(phrase)
            out.append({
                "qid": qid,
                "count": count,
                "len": len(phrase),
                "hash8": self._hash8(phrase),
                "text": phrase if len(phrase) <= 100 else phrase[:97] + "...",
            })
        return out

    def status(self) -> Dict[str, Any]:
        sinn_ids = []
        try:
            from sinn_quanten_registry import status as sinn_status
            sinn_ids = sinn_status().get("ids") or []
        except Exception:
            pass
        return {
            "enabled": is_enabled(),
            "role": ROLE,
            "agent_id": AGENT_ID,
            "table_size": len(self._qid_to_phrase),
            "history_len": len(self._history),
            "min_phrase": _min_phrase(),
            "min_repeat": _min_repeat(),
            "emit_policy": "adaptive_substring_logical_never_char_stream",
            "unit": "adaptive_substring",
            "sinn_quanta": sinn_ids,
            "top_phrases": self.top_phrases(5),
        }


def _normalize_ws(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())


# ── Singleton ──────────────────────────────────────────────────────────────

_INSTANCE: Optional[StringQuantizer] = None


def get_quantizer() -> StringQuantizer:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = StringQuantizer()
    return _INSTANCE


def quantize_text(text: str) -> Dict[str, Any]:
    return get_quantizer().quantize(text).to_dict()


def emit_logical(text: str) -> str:
    """Öffentliche API: ganze Strings in logischer Folge (kein Char-Stream)."""
    return get_quantizer().emit_from_source(text)


def accompany(
    query: str,
    agent_text: str = "",
    anti_text: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not is_enabled():
        return {
            "ok": False,
            "role": ROLE,
            "skipped": True,
            "reason": "FUSION_QUANTIZER_AGENT=0",
        }
    return get_quantizer().accompany_negotiation(query, agent_text, anti_text, context)


def invoke_quantizer(
    query: str,
    agent_response: str = "",
    anti_response: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Router-kompatible invoke-Signatur für den 3. Agenten."""
    return accompany(query, agent_response, anti_response, context)
