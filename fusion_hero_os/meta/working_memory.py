"""Working memory as mathematically-defined activation vectors.

``WorkingMemorySpace`` is a bounded activation buffer. We document the internal
nickname "J-space" only as an *analogy* for a joint activation space; the public
type name is deliberately professional and no biological/consciousness claim is
made.

Mathematics
-----------
State is an activation vector ``a in R^d`` over ``d`` named slots. Two operations:

* **decay**: ``a <- gamma * a`` with decay factor ``gamma in [0, 1]``. Applied
  once per :meth:`step`. After ``k`` steps an un-refreshed activation is
  ``gamma**k`` of its original magnitude (geometric decay).
* **activate**: ``a[slot] <- clip(a[slot] + x, -c, c)`` where ``c`` is the
  per-slot capacity bound. Capacity is enforced by clipping (saturating), so
  ``||a||_inf <= c`` always holds.

Reportability: :meth:`report` returns the current activations above a threshold,
sorted deterministically — an explicit, inspectable read-out (no hidden state).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class WorkingMemoryError(ValueError):
    pass


@dataclass(frozen=True)
class ActivationReport:
    step_index: int
    capacity: float
    decay: float
    active: list[tuple[str, float]]  # (slot, activation), sorted by -activation then slot

    def to_dict(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "capacity": self.capacity,
            "decay": self.decay,
            "active": [{"slot": s, "activation": round(v, 12)} for s, v in self.active],
        }


class WorkingMemorySpace:
    """Bounded, decaying activation buffer over named slots."""

    def __init__(
        self,
        slots: list[str],
        *,
        capacity: float = 1.0,
        decay: float = 0.9,
        report_threshold: float = 1e-6,
    ) -> None:
        if not slots:
            raise WorkingMemoryError("at least one slot is required")
        if len(set(slots)) != len(slots):
            raise WorkingMemoryError("slot names must be unique")
        if capacity <= 0:
            raise WorkingMemoryError("capacity must be > 0")
        if not (0.0 <= decay <= 1.0):
            raise WorkingMemoryError("decay must be in [0, 1]")
        self._slots = list(slots)
        self._index = {s: i for i, s in enumerate(self._slots)}
        self.capacity = float(capacity)
        self.decay = float(decay)
        self.report_threshold = float(report_threshold)
        self._a = [0.0] * len(self._slots)
        self._step_index = 0

    @property
    def slots(self) -> list[str]:
        return list(self._slots)

    @property
    def step_index(self) -> int:
        return self._step_index

    def _clip(self, v: float) -> float:
        return max(-self.capacity, min(self.capacity, v))

    def activate(self, slot: str, amount: float) -> float:
        if slot not in self._index:
            raise WorkingMemoryError(f"unknown slot {slot!r}")
        i = self._index[slot]
        self._a[i] = self._clip(self._a[i] + float(amount))
        return self._a[i]

    def step(self) -> None:
        """Advance one time step: apply geometric decay to all slots."""
        self._a = [self._clip(self.decay * v) for v in self._a]
        self._step_index += 1

    def activation(self, slot: str) -> float:
        if slot not in self._index:
            raise WorkingMemoryError(f"unknown slot {slot!r}")
        return self._a[self._index[slot]]

    def vector(self) -> list[float]:
        return list(self._a)

    def norm(self) -> float:
        return math.sqrt(sum(v * v for v in self._a))

    def report(self) -> ActivationReport:
        active = [
            (s, self._a[i])
            for i, s in enumerate(self._slots)
            if abs(self._a[i]) > self.report_threshold
        ]
        active.sort(key=lambda kv: (-abs(kv[1]), kv[0]))
        return ActivationReport(
            step_index=self._step_index,
            capacity=self.capacity,
            decay=self.decay,
            active=active,
        )

    def reset(self) -> None:
        self._a = [0.0] * len(self._slots)
        self._step_index = 0
