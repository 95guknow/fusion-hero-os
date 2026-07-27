"""Hebbian association memory as consent-scoped sparse edge weights.

This is a plain, well-defined learning rule on a sparse weight table — **not**
a claim of biological cognition. "Neurons that fire together wire together" is
used only as the name of the update rule.

Update rule
-----------
For a co-activation pair ``(i, j)`` with activations ``a_i, a_j``::

    w_ij <- clip((1 - lam) * w_ij + eta * a_i * a_j, -w_max, w_max)

where ``eta`` is the learning rate, ``lam`` the per-update decay (forgetting),
and ``w_max`` the clamp bound. Weights are stored sparsely (only non-negligible
pairs). Deletion removes a pair entirely. Determinism: given the same ordered
sequence of updates, the resulting table is identical (no randomness).

Consent scoping: the owning service must authorise ``Purpose.ASSOCIATION`` for
the subject before applying updates; this module stores only opaque slot names.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable


class HebbianError(ValueError):
    pass


def _key(a: str, b: str) -> tuple[str, str]:
    # Undirected association: canonical ordering for a stable, symmetric key.
    return (a, b) if a <= b else (b, a)


@dataclass
class HebbianConfig:
    learning_rate: float = 0.1
    decay: float = 0.01
    w_max: float = 1.0
    prune_below: float = 1e-9

    def __post_init__(self) -> None:
        if self.learning_rate < 0:
            raise HebbianError("learning_rate must be >= 0")
        if not (0.0 <= self.decay <= 1.0):
            raise HebbianError("decay must be in [0, 1]")
        if self.w_max <= 0:
            raise HebbianError("w_max must be > 0")


class HebbianAssociationMemory:
    """Sparse, clamped, decaying undirected association weights."""

    def __init__(self, config: HebbianConfig | None = None) -> None:
        self.config = config or HebbianConfig()
        self._w: dict[tuple[str, str], float] = {}

    def _clip(self, v: float) -> float:
        m = self.config.w_max
        return max(-m, min(m, v))

    def update(self, a: str, b: str, act_a: float, act_b: float) -> float:
        """Apply one Hebbian update to pair ``(a, b)`` and return the new weight."""
        if a == b:
            raise HebbianError("self-association is not allowed")
        k = _key(a, b)
        cfg = self.config
        current = self._w.get(k, 0.0)
        new = self._clip((1.0 - cfg.decay) * current + cfg.learning_rate * act_a * act_b)
        if abs(new) < cfg.prune_below:
            self._w.pop(k, None)
            return 0.0
        self._w[k] = new
        return new

    def update_many(self, pairs: Iterable[tuple[str, str, float, float]]) -> None:
        for a, b, act_a, act_b in pairs:
            self.update(a, b, act_a, act_b)

    def decay_all(self) -> None:
        """Apply forgetting to every stored weight (independent of co-activation)."""
        factor = 1.0 - self.config.decay
        pruned = []
        for k in list(self._w):
            v = self._clip(self._w[k] * factor)
            if abs(v) < self.config.prune_below:
                pruned.append(k)
            else:
                self._w[k] = v
        for k in pruned:
            self._w.pop(k, None)

    def weight(self, a: str, b: str) -> float:
        return self._w.get(_key(a, b), 0.0)

    def delete(self, a: str, b: str) -> bool:
        """Remove a pair. Returns True if it existed (right-to-erasure hook)."""
        return self._w.pop(_key(a, b), None) is not None

    def delete_slot(self, slot: str) -> int:
        """Remove all associations touching ``slot``. Returns count removed."""
        to_remove = [k for k in self._w if slot in k]
        for k in to_remove:
            self._w.pop(k, None)
        return len(to_remove)

    def items(self) -> list[tuple[tuple[str, str], float]]:
        """Deterministically ordered (key, weight) pairs."""
        return sorted(self._w.items(), key=lambda kv: kv[0])

    def to_matrix(self, slots: list[str]) -> tuple[list[str], list[list[float]]]:
        """Dense symmetric matrix over the given slot order."""
        idx = {s: i for i, s in enumerate(slots)}
        n = len(slots)
        m = [[0.0] * n for _ in range(n)]
        for (a, b), w in self._w.items():
            if a in idx and b in idx:
                i, j = idx[a], idx[b]
                m[i][j] = w
                m[j][i] = w
        return list(slots), m

    def __len__(self) -> int:
        return len(self._w)
