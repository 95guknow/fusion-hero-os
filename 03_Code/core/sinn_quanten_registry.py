# -*- coding: utf-8 -*-
"""
Sinnquanten-Registry — erarbeitete heroische Quanten (Liebesquant, Zufriedenheitsquant, …)

Diskrete Sinn-Einheiten (Metapher der quantisierten Kognition, kein QM-Überclaim).
Jedes Sinnquant hat:
  * id, name, domain
  * magnitude scale (0..1 default)
  * adaptive substring cues (logische Teilstrings, die sich anpassen)
  * M→N Datenbank-Links (welche Quell-DBs speisen, welche Ziel-DBs speichern)

Zusammen mit string_quantizer_agent (adaptive Substrings) und entwicklungsquant_bus.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "SinnQuant",
    "SINN_QUANTA",
    "get_registry",
    "score_text",
    "map_substrings_to_sinn",
    "status",
]

# ── erarbeitete Sinnquanten (Heroic Core / Der heroische Mensch) ────────────

@dataclass
class SinnQuant:
    id: str
    name: str
    domain: str
    description: str
    # logische adaptive Substring-Cues (nicht komplette Sätze)
    cues: List[str] = field(default_factory=list)
    # synonym / adaptive Varianten (wachsen mit Nutzung)
    adaptations: List[str] = field(default_factory=list)
    layer: int = 3
    quant_size: float = 0.25
    default_magnitude: float = 0.5
    # M-Quellen / N-Ziele (DB-IDs)
    source_dbs: List[str] = field(default_factory=list)
    target_dbs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def all_cues(self) -> List[str]:
        return list(dict.fromkeys([*self.cues, *self.adaptations]))


# Kanonische Menge — erarbeitet im Heroic-Programm + User-Direktive
SINN_QUANTA: List[SinnQuant] = [
    SinnQuant(
        id="liebesquant",
        name="Liebesquant",
        domain="bindung",
        description=(
            "Diskrete Einheit echter Bindung / Verstehensmoment. "
            "Aufbau langsam und verlässlich; Surrogate (Substanz, Strategie) ersetzen sie nicht."
        ),
        cues=[
            "liebe", "bindung", "versteh", "vertrauen", "nähe", "naehe", "stamm",
            "paar", "freundschaft", "gesehen", "getragen", "zuwendung", "zärtlich",
            "zaertlich", "intim", "wir", "gemeinsam", "loyal", "gehalten",
        ],
        adaptations=["liebes quant", "love quant", "mimetische bindung", "verstehensmoment"],
        layer=4,
        source_dbs=["conversation", "public_corpus", "heroic_book", "notion"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases", "quantum_dict"],
    ),
    SinnQuant(
        id="zufriedenheitsquant",
        name="Zufriedenheitsquant",
        domain="wohlbefinden",
        description=(
            "Diskrete Einheit erlebter Zufriedenheit / Genugsein ohne Surrogat-Jagd. "
            "Ko-existiert mit Liebesquant und Sinnquant, ersetzt sie nicht."
        ),
        cues=[
            "zufrieden", "genug", "ruhe", "frieden", "dankbar", "ausgeglichen",
            "content", "satisfaction", "erfüllt", "erfuellt", "gelassen", "stabil",
            "wohl", "erleichter", "angenommen", "ok mit",
        ],
        adaptations=["zufriedenheits quant", "satisfaction quant", "genugsein"],
        layer=3,
        source_dbs=["conversation", "public_corpus", "heroic_book", "journal"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases", "quantum_dict"],
    ),
    SinnQuant(
        id="sinnquant",
        name="Sinnquant",
        domain="sinn",
        description=(
            "Diskrete Einheit von Sinn / spiritueller oder heroischer Verbindung. "
            "Surrogate (Substanz) sind oft effiziente Platzhalter — echten Sinn nicht ersetzen."
        ),
        cues=[
            "sinn", "bedeutung", "warum", "berufung", "heroisch", "purpose",
            "spirituell", "verbindung", "mission", "richtung", "fixpunkt", "masterseed",
            "geltung", "wahrheit", "eudaimonia",
        ],
        adaptations=["sinn quant", "sense quant", "purpose quant"],
        layer=5,
        source_dbs=["conversation", "heroic_book", "knowledge", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases", "ascension"],
    ),
    SinnQuant(
        id="sicherheitsquant",
        name="Sicherheitsquant",
        domain="sicherheit",
        description="Diskrete Einheit von Sicherheit & Stabilität (Boden unter den Füßen).",
        cues=["sicher", "stabil", "schutz", "boden", "halt", "ruhepunkt", "geborgen", "safe"],
        layer=2,
        source_dbs=["conversation", "ops", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases"],
    ),
    SinnQuant(
        id="koerperquant",
        name="Körperquant",
        domain="embodiment",
        description="Diskrete Einheit von Embodiment / körperlicher Präsenz.",
        cues=["körper", "koerper", "leib", "atmung", "bewegung", "embodiment", "spür", "spuer"],
        layer=1,
        source_dbs=["conversation", "health", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases"],
    ),
    SinnQuant(
        id="bewaehrungsquant",
        name="Bewährungsquant",
        domain="leistung",
        description="Diskrete Einheit von Bewährung & Leistung ohne Identitäts-Kollaps.",
        cues=["bewährung", "bewaehrung", "leistung", "können", "koennen", "probe", "mut", "tat"],
        layer=3,
        source_dbs=["conversation", "work", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases"],
    ),
    SinnQuant(
        id="ausdrucksquant",
        name="Ausdrucksquant",
        domain="kreativitaet",
        description="Diskrete Einheit von Ausdruck & Kreativität.",
        cues=["ausdruck", "kreativ", "kunst", "stimme", "schreiben", "schaffen", "form"],
        layer=3,
        source_dbs=["conversation", "creative", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases"],
    ),
    SinnQuant(
        id="stammquant",
        name="Stammquant",
        domain="bindung",
        description="Diskrete Einheit verlässlicher Stamm-/Freundschaftsbindung (Liebesquant-Familie).",
        cues=["stamm", "freund", "tribe", "peer", "mitstreiter", "verlässlich", "verlaesslich"],
        adaptations=["freundschaft quant", "tribe quant"],
        layer=4,
        source_dbs=["conversation", "mesh", "public_corpus"],
        target_dbs=["sinn_store", "entwicklungsquant_bus", "quantized_phrases"],
    ),
]


class SinnQuantenRegistry:
    """Registry + Scoring + adaptive Cue-Erweiterung."""

    def __init__(self, quanta: Optional[Sequence[SinnQuant]] = None) -> None:
        self._by_id: Dict[str, SinnQuant] = {}
        for q in (quanta or SINN_QUANTA):
            self._by_id[q.id] = q
        self._hit_counts: Dict[str, int] = {qid: 0 for qid in self._by_id}
        self._adaptive_learned: Dict[str, List[str]] = {qid: [] for qid in self._by_id}

    def get(self, qid: str) -> Optional[SinnQuant]:
        return self._by_id.get(qid)

    def list(self) -> List[SinnQuant]:
        return list(self._by_id.values())

    def score_text(self, text: str) -> Dict[str, Any]:
        """Ordnet Text adaptive Substring-Treffer → Sinnquanten-Magnituden."""
        low = (text or "").lower()
        scores: Dict[str, float] = {}
        hits: Dict[str, List[str]] = {}
        for q in self._by_id.values():
            matched = []
            for cue in q.all_cues():
                c = cue.lower()
                if len(c) >= 3 and c in low:
                    matched.append(cue)
            if matched:
                # magnitude: quantisiert auf quant_size
                raw = min(1.0, 0.15 * len(matched) + 0.1 * sum(len(m) for m in matched) / max(20, len(low)))
                mag = round(raw / q.quant_size) * q.quant_size
                if mag < q.quant_size:
                    mag = q.quant_size
                scores[q.id] = min(1.0, mag)
                hits[q.id] = matched
                self._hit_counts[q.id] = self._hit_counts.get(q.id, 0) + 1
        return {
            "scores": scores,
            "hits": hits,
            "dominant": max(scores, key=scores.get) if scores else None,
            "mode": "adaptive_substring_cues",
        }

    def learn_adaptation(self, qid: str, substring: str) -> bool:
        """Adaptive Erweiterung: neues logisches Substring-Cue an Sinnquant binden."""
        q = self._by_id.get(qid)
        if not q:
            return False
        s = (substring or "").strip().lower()
        if len(s) < 3 or len(s) > 80:
            return False
        if s in q.all_cues():
            return False
        q.adaptations.append(s)
        self._adaptive_learned.setdefault(qid, []).append(s)
        return True

    def map_substrings(
        self,
        substrings: Sequence[str],
        adapt: bool = True,
    ) -> Dict[str, Any]:
        """
        Mappt adaptive Substrings → Sinnquanten (nicht komplette Strings).
        Optional: häufige unbekannte Substrings an dominantem Quant anlernen.
        """
        mapping: List[Dict[str, Any]] = []
        aggregate: Dict[str, float] = {}
        for sub in substrings:
            if not sub or len(sub.strip()) < 3:
                continue
            # nie Einzelbuchstaben
            if len(sub.strip()) == 1:
                continue
            sc = self.score_text(sub)
            entry = {
                "substring": sub[:200],
                "scores": sc["scores"],
                "dominant": sc["dominant"],
                "hits": sc["hits"],
            }
            mapping.append(entry)
            for qid, mag in sc["scores"].items():
                aggregate[qid] = aggregate.get(qid, 0.0) + mag
            # adaptive: unbekannte längere Substrings an dominant binden
            if adapt and sc["dominant"] and not sc["hits"].get(sc["dominant"]):
                pass  # only adapt when partial cue match exists
            if adapt and sc["dominant"] and sc["hits"]:
                # take a mid-length token from substring as adaptation candidate
                words = re.findall(r"[\wÄÖÜäöüß]{4,}", sub.lower())
                for w in words[:2]:
                    if w not in (self._by_id[sc["dominant"]].all_cues()):
                        # only learn if co-occurs with known cue in same substring
                        if any(c.lower() in sub.lower() for c in self._by_id[sc["dominant"]].cues):
                            self.learn_adaptation(sc["dominant"], w)

        # normalize aggregate
        if aggregate:
            mx = max(aggregate.values()) or 1.0
            aggregate = {k: round(v / mx, 4) for k, v in aggregate.items()}

        return {
            "mapping": mapping[:500],
            "aggregate": aggregate,
            "mapped_count": len(mapping),
            "adaptive_learned": {k: v for k, v in self._adaptive_learned.items() if v},
            "mode": "adaptive_substring_to_sinnquant",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quanta": [q.to_dict() for q in self._by_id.values()],
            "hit_counts": dict(self._hit_counts),
            "adaptive_learned": {k: v for k, v in self._adaptive_learned.items() if v},
            "count": len(self._by_id),
        }

    def persist(self, path: Optional[Path] = None) -> Path:
        p = path or (Path.home() / ".fusion" / "operator" / "sinn_quanten_state.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return p


_REG: Optional[SinnQuantenRegistry] = None


def get_registry() -> SinnQuantenRegistry:
    global _REG
    if _REG is None:
        _REG = SinnQuantenRegistry()
        # load adaptations if present
        p = Path.home() / ".fusion" / "operator" / "sinn_quanten_state.json"
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for qid, cues in (data.get("adaptive_learned") or {}).items():
                    for c in cues:
                        _REG.learn_adaptation(qid, c)
            except Exception:
                pass
    return _REG


def score_text(text: str) -> Dict[str, Any]:
    return get_registry().score_text(text)


def map_substrings_to_sinn(substrings: Sequence[str], adapt: bool = True) -> Dict[str, Any]:
    return get_registry().map_substrings(substrings, adapt=adapt)


def status() -> Dict[str, Any]:
    r = get_registry()
    return {
        "module": "sinn_quanten_registry",
        "count": len(r.list()),
        "ids": [q.id for q in r.list()],
        "names": [q.name for q in r.list()],
        "hit_counts": dict(r._hit_counts),
        "liebesquant": r.get("liebesquant").to_dict() if r.get("liebesquant") else None,
        "zufriedenheitsquant": r.get("zufriedenheitsquant").to_dict() if r.get("zufriedenheitsquant") else None,
        "sinnquant": r.get("sinnquant").to_dict() if r.get("sinnquant") else None,
    }


if __name__ == "__main__":
    demo = (
        "Ich fühle echte Nähe und Vertrauen — der Liebesquant wächst. "
        "Gleichzeitig bin ich zufrieden und ruhig, Sinn und MasterSeed halten."
    )
    print(json.dumps(score_text(demo), indent=2, ensure_ascii=False))
    print(json.dumps(status(), indent=2, ensure_ascii=False))
