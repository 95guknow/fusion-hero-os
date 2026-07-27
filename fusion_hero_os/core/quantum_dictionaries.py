"""Fusion Hero OS — Quanten-Wörterbücher (zentrale Lookup-/Memoisierungs-Register).

Ehrliche Begriffsklaerung (Code-Honesty, Praezedenz: VirtualGPUHTCache bleibt
deklarierte Simulation): "Quanten-Wörterbuch" ist die Projekt-Namenskonvention
fuer ein zentrales, deterministisch adressiertes Nachschlagewerk mit
Zustands-Invalidierung. KEIN Quantencomputing. Die Performance-Wirkung ist
klassisch und messbar: teure, wiederholte Berechnungen (Repo-Scan des
Dependency Atlas, YAML-Parsing der Layer-Prefixe) werden nur bei tatsaechlich
geaendertem Eingabezustand neu ausgefuehrt.

Eigenschaften:
  * Deterministische Adressen: kanonisches JSON -> SHA-256 (gleicher Input =
    gleicher Schluessel, prozess- und sitzungsuebergreifend stabil).
  * Zustands-Signaturen: ein Eintrag traegt die Signatur seines Eingabe-
    zustands (z.B. mtime-Aggregat der gescannten Dateien). Weicht die aktuelle
    Signatur ab, gilt der Eintrag als ungueltig -> Neuberechnung.
  * Statistik: hits/misses/invalidations je Woerterbuch, abfragbar ueber
    stats() — Performance-Behauptungen sind damit nachpruefbar statt behauptet.
  * Optionaler TTL als zweite Verfallslinie fuer zeitgebundene Werte.

Bestehende Spezial-Caches bleiben unberuehrt und zustaendig fuer ihre Domaene
(03_Code/suite/qubo/cache_integration.py: GPU/VRAM-Cache der QUBO-Probleme;
core/virtual_gpu_hyperthreading: deklarierte Simulation). Dieses Modul ist
das ZENTRALE Register fuer alles, was keinen Spezial-Cache braucht.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable

__all__ = ["QuantumDictionary", "get_quantum_dictionary", "canonical_key", "registry_stats"]


def canonical_key(obj: Any) -> str:
    """Deterministische Adresse: kanonisches JSON -> SHA-256-Hexdigest."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class _Entry:
    value: Any
    signature: str | None
    stored_at: float = field(default_factory=time.time)


class QuantumDictionary:
    """Zentrales Nachschlagewerk mit deterministischen Adressen + Invalidierung."""

    def __init__(self, name: str, ttl_sec: float | None = None, max_entries: int = 256):
        self.name = name
        self.ttl_sec = ttl_sec
        self.max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._invalidations = 0

    def get_or_compute(
        self,
        key_obj: Any,
        compute: Callable[[], Any],
        signature: str | None = None,
    ) -> Any:
        """Liefert den Eintrag zu key_obj oder berechnet ihn neu.

        signature: aktueller Eingabezustand (z.B. mtime-Aggregat). Weicht er
        vom gespeicherten ab, wird invalidiert und neu berechnet.
        """
        key = canonical_key(key_obj)
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                expired = self.ttl_sec is not None and (time.time() - entry.stored_at) > self.ttl_sec
                stale = signature is not None and entry.signature != signature
                if not expired and not stale:
                    self._hits += 1
                    return entry.value
                self._invalidations += 1
                del self._entries[key]
            self._misses += 1

        value = compute()  # bewusst ausserhalb des Locks: compute kann teuer sein

        with self._lock:
            if len(self._entries) >= self.max_entries:
                oldest = min(self._entries, key=lambda k: self._entries[k].stored_at)
                del self._entries[oldest]
            self._entries[key] = _Entry(value=value, signature=signature)
        return value

    def invalidate(self, key_obj: Any = None) -> int:
        """Einen Eintrag (key_obj) oder alles (None) verwerfen. Liefert Anzahl."""
        with self._lock:
            if key_obj is None:
                n = len(self._entries)
                self._entries.clear()
            else:
                n = 1 if self._entries.pop(canonical_key(key_obj), None) is not None else 0
            self._invalidations += n
            return n

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "entries": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "invalidations": self._invalidations,
                "hit_rate": round(self._hits / max(1, self._hits + self._misses), 4),
                "ttl_sec": self.ttl_sec,
            }


_registry: dict[str, QuantumDictionary] = {}
_registry_lock = threading.Lock()


def get_quantum_dictionary(name: str, ttl_sec: float | None = None,
                           max_entries: int = 256) -> QuantumDictionary:
    """Zentrales Register: gleicher Name -> gleiches Woerterbuch (prozessweit)."""
    with _registry_lock:
        if name not in _registry:
            _registry[name] = QuantumDictionary(name, ttl_sec=ttl_sec, max_entries=max_entries)
        return _registry[name]


def registry_stats() -> dict[str, dict[str, Any]]:
    """Statistik aller Woerterbuecher — fuer /api/architecture/atlas u.a."""
    with _registry_lock:
        return {name: qd.stats() for name, qd in _registry.items()}
