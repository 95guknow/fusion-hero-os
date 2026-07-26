# -*- coding: utf-8 -*-
"""Host-side Injection Table — max injectability for Fusion Hero OS (Windows).

Mirrors kernel/inject assembly ABI so the control plane can inject quantum
handlers without a freestanding boot. Capability-gated; no foreign-process
injection (cooperative quanta only).

Usage:
  from kernel.inject.inject_host import get_inject_host
  h = get_inject_host()
  h.register(0, "q1_health", quantum_id=1, caps=CAP_READ|CAP_HOOK, fn=my_fn, hot=True)
  h.call(0, 0, 0, 0, 0, holder_caps=CAP_READ|CAP_HOOK)
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

INJECT_SLOTS = 256
NAME_MAX = 32

CAP_NONE = 0
CAP_READ = 1 << 0
CAP_HOOK = 1 << 1
CAP_SWAP = 1 << 2
CAP_ISR = 1 << 3
CAP_QUANTUM = 1 << 4
CAP_PRIV = 1 << 7

SLOT_EMPTY = 0
SLOT_ACTIVE = 1 << 0
SLOT_HOT = 1 << 1
SLOT_ASM = 1 << 2
SLOT_HOST = 1 << 3

InjectFn = Callable[[int, int, int, int], int]


@dataclass
class InjectSlot:
    flags: int = SLOT_EMPTY
    required_caps: int = CAP_NONE
    quantum_id: int = 0xFFFFFFFF
    generation: int = 0
    name: str = ""
    entry: Optional[InjectFn] = field(default=None, repr=False)

    def to_public(self) -> Dict[str, Any]:
        return {
            "flags": self.flags,
            "required_caps": self.required_caps,
            "quantum_id": self.quantum_id,
            "generation": self.generation,
            "name": self.name,
            "active": bool(self.flags & SLOT_ACTIVE),
            "hot": bool(self.flags & SLOT_HOT),
            "has_entry": self.entry is not None,
        }


class InjectHost:
    """Maximum injectability host: 256 slots, hot-swap, capability gates."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.slots: List[InjectSlot] = [InjectSlot() for _ in range(INJECT_SLOTS)]
        self.epoch: int = 0
        self.magic = "FHOSINJ"
        self.language_primary = "assembly"
        self.mode = "host_simulated"
        self.init()

    def init(self) -> None:
        with self._lock:
            for s in self.slots:
                s.flags = SLOT_EMPTY
                s.entry = None
                s.name = ""
                s.generation = 0
            self.epoch += 1

    def register(
        self,
        slot: int,
        name: str,
        *,
        quantum_id: int = 0xFFFFFFFF,
        caps: int = CAP_HOOK,
        fn: Optional[InjectFn] = None,
        hot: bool = True,
        asm: bool = False,
    ) -> int:
        if not (0 <= slot < INJECT_SLOTS):
            return -1
        with self._lock:
            s = self.slots[slot]
            flags = SLOT_ACTIVE | SLOT_HOST
            if hot:
                flags |= SLOT_HOT
            if asm:
                flags |= SLOT_ASM
            s.flags = flags
            s.required_caps = caps
            s.quantum_id = quantum_id
            s.generation += 1
            s.name = (name or "")[: NAME_MAX - 1]
            s.entry = fn
            self.epoch += 1
            return 0

    def swap(self, slot: int, fn: InjectFn, holder_caps: int) -> int:
        if not (0 <= slot < INJECT_SLOTS):
            return -1
        with self._lock:
            s = self.slots[slot]
            if not (s.flags & SLOT_ACTIVE):
                return -1
            if not (s.flags & SLOT_HOT):
                return -1
            if (s.required_caps & ~holder_caps) != 0:
                return -2
            s.entry = fn
            s.generation += 1
            self.epoch += 1
            return 0

    def call(
        self,
        slot: int,
        a0: int = 0,
        a1: int = 0,
        a2: int = 0,
        a3: int = 0,
        holder_caps: int = CAP_READ | CAP_HOOK | CAP_QUANTUM,
    ) -> int:
        if not (0 <= slot < INJECT_SLOTS):
            return 0
        with self._lock:
            s = self.slots[slot]
            if not (s.flags & SLOT_ACTIVE) or s.entry is None:
                return 0
            if (s.required_caps & ~holder_caps) != 0:
                return 0
            fn = s.entry
        try:
            return int(fn(a0, a1, a2, a3))
        except Exception:
            return 0

    def clear(self, slot: int, holder_caps: int) -> int:
        if not (0 <= slot < INJECT_SLOTS):
            return -1
        with self._lock:
            s = self.slots[slot]
            if (s.required_caps & ~holder_caps) != 0:
                return -2
            self.slots[slot] = InjectSlot()
            self.epoch += 1
            return 0

    def status(self) -> Dict[str, Any]:
        with self._lock:
            active = [s.to_public() for s in self.slots if s.flags & SLOT_ACTIVE]
            return {
                "magic": self.magic,
                "mode": self.mode,
                "language_primary": self.language_primary,
                "n_slots": INJECT_SLOTS,
                "active_count": len(active),
                "epoch": self.epoch,
                "slots": active,
                "principle": "max_injectability_capability_gated",
                "geltung": "host_simulated=Satz on Windows; freestanding asm=Modell until QEMU boot green",
            }

    def inject_quantum_defaults(self) -> Dict[str, Any]:
        """Register default no-op hooks for Q0–Q12 (always injectable)."""
        registered = []

        def _make_nop(qid: int, label: str) -> InjectFn:
            def _fn(a0: int, a1: int, a2: int, a3: int) -> int:
                return (qid << 32) | (a0 & 0xFFFFFFFF)

            _fn.__name__ = f"inject_{label}"
            return _fn

        mapping = [
            (0, "Q0_integrity", CAP_PRIV | CAP_HOOK),
            (1, "Q1_control", CAP_READ | CAP_HOOK),
            (2, "Q2_compute", CAP_HOOK | CAP_QUANTUM),
            (3, "Q3_agents", CAP_HOOK | CAP_QUANTUM),
            (4, "Q4_intelligence", CAP_HOOK | CAP_QUANTUM),
            (5, "Q5_storage", CAP_HOOK),
            (6, "Q6_mesh", CAP_HOOK),
            (7, "Q7_surface", CAP_READ | CAP_HOOK),
            (8, "Q8_ops", CAP_HOOK),
            (9, "Q9_ascension", CAP_HOOK | CAP_QUANTUM),
            (10, "Q10_ipc", CAP_HOOK | CAP_ISR),
            (11, "Q11_proof", CAP_READ),
            (12, "Q12_security", CAP_PRIV | CAP_HOOK),
        ]
        for qid, name, caps in mapping:
            rc = self.register(
                qid, name, quantum_id=qid, caps=caps, fn=_make_nop(qid, name), hot=True, asm=True
            )
            registered.append({"slot": qid, "name": name, "rc": rc})
        return {"registered": registered, "status": self.status()}

    def persist(self, path: Optional[Path] = None) -> Path:
        path = path or Path.home() / ".fusion" / "kernel" / "inject_table.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")
        return path


_HOST: Optional[InjectHost] = None


def get_inject_host() -> InjectHost:
    global _HOST
    if _HOST is None:
        _HOST = InjectHost()
        if os.getenv("FUSION_KERNEL_INJECT_DEFAULTS", "1").strip() not in ("0", "false", "off"):
            _HOST.inject_quantum_defaults()
    return _HOST


def preload_kernel_inject() -> Dict[str, Any]:
    """Called from universal_startup_preload — max injectability online."""
    h = get_inject_host()
    p = h.persist()
    st = h.status()
    st["persisted"] = str(p)
    return st


if __name__ == "__main__":
    h = get_inject_host()
    print(json.dumps(h.status(), indent=2))
