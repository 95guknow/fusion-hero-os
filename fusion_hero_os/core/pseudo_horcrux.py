"""
Multimodale Pseudohorkruxe + Autosave — redundante Zustandsshards für das
Hyperclusterup Zitterpolymesh.

Prinzip (ehrlich implementiert, keine Magie):

* Ein "Pseudohorkrux" ist ein vollständiger, unabhängig wiederherstellbarer
  Zustandsshard. ``preserve()`` schreibt denselben Zustand in mehrere
  Modalitäten (JSON, CSV, Base64-Container) und optional mehrere Kopien —
  solange EIN Shard überlebt, ist der Zustand wiederherstellbar.
* Jeder Shard trägt SHA-256-Checksumme + Generationszähler. ``restore()``
  verifiziert alle Shards und nimmt die höchste gültige Generation.
* Race-Sicherheit über :mod:`fusion_hero_os.core.race_guard`: FileLock auf
  dem Store serialisiert Writer (Desktop + Cron + Cluster), Shard-Dateien
  werden atomar geschrieben (temp + fsync + os.replace).
* ``AutosaveDaemon``: Hintergrund-Thread mit Intervall + Debounce, der den
  Zustand eines Providers periodisch (und nach ``mark_dirty()``) in den
  Horkrux-Store sichert. Läuft auf der MEM-Lane-Seite des Zitterpolymesh.

Nur Stdlib; kompatibel mit Windows + Linux wie race_guard.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union
from collections.abc import Callable

from fusion_hero_os.core.race_guard import FileLock, atomic_write_text

PathLike = Union[str, Path]

__all__ = [
    "MODALITIES",
    "HorcruxShard",
    "PseudoHorcruxStore",
    "AutosaveDaemon",
]

MODALITIES: tuple[str, ...] = ("json", "csv", "b64")
_MAGIC_B64 = "FHOS-HORCRUX-B64 v1"


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class HorcruxShard:
    path: Path
    modality: str
    generation: int
    checksum: str
    valid: bool
    payload: dict[str, Any] | None
    error: str = ""


# ---------------------------------------------------------------------------
# Modalitäten: encode/decode — jeder Shard ist für sich vollständig
# ---------------------------------------------------------------------------


def _encode_json(meta: dict[str, Any], payload: dict[str, Any]) -> str:
    return json.dumps({"meta": meta, "payload": payload}, indent=2, ensure_ascii=False) + "\n"


def _decode_json(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    doc = json.loads(text)
    return dict(doc["meta"]), dict(doc["payload"])


def _encode_csv(meta: dict[str, Any], payload: dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["key", "value_json"])
    for k, v in sorted(meta.items()):
        writer.writerow([f"_meta:{k}", json.dumps(v, ensure_ascii=False)])
    for k, v in sorted(payload.items()):
        writer.writerow([k, json.dumps(v, ensure_ascii=False)])
    return buf.getvalue()


def _decode_csv(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    meta: dict[str, Any] = {}
    payload: dict[str, Any] = {}
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header != ["key", "value_json"]:
        raise ValueError("CSV-Horkrux ohne gültigen Header")
    for row in reader:
        if len(row) != 2:
            raise ValueError(f"CSV-Horkrux: kaputte Zeile {row!r}")
        key, raw = row
        value = json.loads(raw)
        if key.startswith("_meta:"):
            meta[key[len("_meta:"):]] = value
        else:
            payload[key] = value
    return meta, payload


def _encode_b64(meta: dict[str, Any], payload: dict[str, Any]) -> str:
    body = base64.b64encode(_canonical(payload).encode("utf-8")).decode("ascii")
    return "\n".join([_MAGIC_B64, json.dumps(meta, sort_keys=True, ensure_ascii=False), body, ""])


def _decode_b64(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0] != _MAGIC_B64:
        raise ValueError("B64-Horkrux: Magic-Header fehlt")
    meta = dict(json.loads(lines[1]))
    payload = dict(json.loads(base64.b64decode(lines[2]).decode("utf-8")))
    return meta, payload


_CODECS: dict[str, tuple[Callable[..., str], Callable[[str], tuple[dict[str, Any], dict[str, Any]]]]] = {
    "json": (_encode_json, _decode_json),
    "csv": (_encode_csv, _decode_csv),
    "b64": (_encode_b64, _decode_b64),
}


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class PseudoHorcruxStore:
    """Redundanter Zustandsspeicher: n Kopien × 3 Modalitäten pro Generation."""

    def __init__(
        self,
        base_dir: PathLike,
        *,
        copies: int = 1,
        keep_generations: int = 5,
        lock_timeout: float = 30.0,
    ):
        if copies < 1:
            raise ValueError("copies muss >= 1 sein")
        self.base_dir = Path(base_dir)
        self.copies = copies
        self.keep_generations = max(1, keep_generations)
        self.lock_timeout = lock_timeout
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock_anchor = self.base_dir / "horcrux-store"

    # -- intern ------------------------------------------------------------

    def _shard_path(self, modality: str, copy_idx: int) -> Path:
        return self.base_dir / f"horcrux-{modality}-c{copy_idx}.hx"

    def _iter_shard_paths(self) -> list[tuple[str, Path]]:
        return [
            (modality, self._shard_path(modality, c))
            for modality in MODALITIES
            for c in range(self.copies)
        ]

    def _read_shard(self, modality: str, path: Path) -> HorcruxShard:
        if not path.is_file():
            return HorcruxShard(path, modality, -1, "", False, None, "fehlt")
        try:
            _, decode = _CODECS[modality]
            meta, payload = decode(path.read_text(encoding="utf-8"))
            gen = int(meta.get("generation", -1))
            claimed = str(meta.get("sha256", ""))
            actual = _checksum(payload)
            if claimed != actual:
                return HorcruxShard(
                    path, modality, gen, claimed, False, None,
                    f"Checksumme falsch (erwartet {claimed[:12]}…, ist {actual[:12]}…)",
                )
            return HorcruxShard(path, modality, gen, claimed, True, payload)
        except Exception as exc:  # noqa: BLE001 — kaputter Shard darf restore nie stoppen
            return HorcruxShard(path, modality, -1, "", False, None, f"{type(exc).__name__}: {exc}")

    # -- API ---------------------------------------------------------------

    def preserve(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Schreibt den Zustand als neue Generation in alle Shards.

        Serialisiert über FileLock (multi-process-sicher), jede Datei atomar.
        Gibt Manifest der geschriebenen Shards zurück.
        """
        if not isinstance(payload, dict):
            raise TypeError("payload muss ein dict sein")
        with FileLock(self._lock_anchor, timeout=self.lock_timeout):
            current = self._best_shard_unlocked()
            generation = (current.generation if current else 0) + 1
            meta = {
                "generation": generation,
                "sha256": _checksum(payload),
                "written_at": time.time(),
                "modalities": list(MODALITIES),
                "copies": self.copies,
            }
            written: list[str] = []
            for modality, path in self._iter_shard_paths():
                encode, _ = _CODECS[modality]
                atomic_write_text(path, encode(dict(meta, modality=modality), payload))
                written.append(str(path.name))
            return {"generation": generation, "sha256": meta["sha256"], "shards": written}

    def _best_shard_unlocked(self) -> HorcruxShard | None:
        best: HorcruxShard | None = None
        for modality, path in self._iter_shard_paths():
            shard = self._read_shard(modality, path)
            if shard.valid and (best is None or shard.generation > best.generation):
                best = shard
        return best

    def restore(self) -> dict[str, Any] | None:
        """Beste gültige Generation über alle Shards; None wenn keiner überlebt hat."""
        with FileLock(self._lock_anchor, timeout=self.lock_timeout):
            best = self._best_shard_unlocked()
        return dict(best.payload) if best and best.payload is not None else None

    def integrity_report(self) -> dict[str, Any]:
        shards = [self._read_shard(m, p) for m, p in self._iter_shard_paths()]
        valid = [s for s in shards if s.valid]
        best_gen = max((s.generation for s in valid), default=-1)
        return {
            "total_shards": len(shards),
            "valid_shards": len(valid),
            "best_generation": best_gen,
            "restorable": bool(valid),
            "shards": [
                {
                    "file": s.path.name,
                    "modality": s.modality,
                    "generation": s.generation,
                    "valid": s.valid,
                    "error": s.error,
                }
                for s in shards
            ],
        }


# ---------------------------------------------------------------------------
# Autosave
# ---------------------------------------------------------------------------


@dataclass
class AutosaveStats:
    saves: int = 0
    errors: int = 0
    last_generation: int = 0
    last_save_at: float = 0.0
    last_error: str = ""


class AutosaveDaemon:
    """Periodischer + ereignisgetriebener Autosave in einen Horkrux-Store.

    * ``interval``: spätestens alle N Sekunden wird gesichert.
    * ``mark_dirty()``: Ereignis-Trigger; ``debounce`` bündelt Ereignis-Stürme
      zu einem Save (gedämpft, analog Zitterfunktion).
    * Save läuft über ``store.preserve()`` → FileLock + atomare Writes,
      dadurch race-sicher gegenüber parallelen Writern.
    """

    def __init__(
        self,
        store: PseudoHorcruxStore,
        state_provider: Callable[[], dict[str, Any]],
        *,
        interval: float = 30.0,
        debounce: float = 0.5,
    ):
        self.store = store
        self.state_provider = state_provider
        self.interval = max(0.05, interval)
        self.debounce = max(0.0, debounce)
        self.stats = AutosaveStats()
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._stats_lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> AutosaveDaemon:
        if self._thread and self._thread.is_alive():
            return self
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="horcrux-autosave", daemon=True)
        self._thread.start()
        return self

    def stop(self, *, final_save: bool = True, join_timeout: float = 10.0) -> None:
        self._stop.set()
        self._dirty.set()  # Loop aufwecken
        if self._thread:
            self._thread.join(timeout=join_timeout)
            self._thread = None
        if final_save:
            self._save_once()

    def __enter__(self) -> AutosaveDaemon:
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    # -- triggers ----------------------------------------------------------

    def mark_dirty(self) -> None:
        self._dirty.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            triggered = self._dirty.wait(timeout=self.interval)
            if self._stop.is_set():
                return
            if triggered:
                # Debounce: Ereignis-Sturm zu einem Save bündeln
                time.sleep(self.debounce)
                self._dirty.clear()
            self._save_once()

    def _save_once(self) -> None:
        try:
            state = self.state_provider()
            manifest = self.store.preserve(state)
            with self._stats_lock:
                self.stats.saves += 1
                self.stats.last_generation = int(manifest["generation"])
                self.stats.last_save_at = time.time()
        except Exception as exc:  # noqa: BLE001 — Autosave darf den Host nie reißen
            with self._stats_lock:
                self.stats.errors += 1
                self.stats.last_error = f"{type(exc).__name__}: {exc}"

    def snapshot_stats(self) -> dict[str, Any]:
        with self._stats_lock:
            return {
                "saves": self.stats.saves,
                "errors": self.stats.errors,
                "last_generation": self.stats.last_generation,
                "last_save_at": self.stats.last_save_at,
                "last_error": self.stats.last_error,
            }
