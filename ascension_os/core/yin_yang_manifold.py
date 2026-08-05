# -*- coding: utf-8 -*-
"""
AscensionOS - YinYangManifold: Triple-Yin-Yang-Modus in n Dimensionen

Verallgemeinert die bereits vorhandene, zweipolige Devil-vs-Christus-QUBO
(:mod:`ascension_os.core.qubo_ascension_optimizer`) auf **k Polpaare ueber
n Checkpoints**. Der "Triple-Yin-Yang-Modus" ist der Spezialfall k=3 mit den
drei Paaren, die im Kanon bereits existieren:

    1. q / b                      fliessend / schneidend   (Gesetz 2, Raster IV)
    2. Impression / Expression    Aufnahme / Hervorbringung (Fundament v13)
    3. Devil / Christus           Rohmaterial / Integration (Stage-9-Trajektorie)

Ehrlicher Status
----------------
* **Satz-Ebene** (getestet, siehe tests/test_yin_yang_manifold.py):
  - Q ist symmetrisch.
  - Dimension des Zustandsraums ist exakt 2*k*n.
  - Reproduktion: k=1 mit den Devil/Christus-Parametern liefert **bitgenau**
    dieselbe Matrix wie build_devil_christus_qubo (kein Fork der Semantik).
  - Inkohaerenz-Schranke: ist die Inkohaerenz-Strafe groesser als der maximale
    Bias-Gewinn, so ist jeder Zustand, in dem beide Pole eines Paares am selben
    Checkpoint aktiv sind, strikt energiereicher als derselbe Zustand mit
    abgeschaltetem Yin-Pol. "Beides zugleich" ist damit nicht verboten, sondern
    *teuer* — und das ist beweisbar, nicht behauptet.
* **Modell-Ebene** (KEIN Beweisanspruch): Dass diese drei Paare *die* Paare
  sind, dass ihre Kopplung reale psychische oder soziale Dynamik abbildet, und
  dass "Yin/Yang" mehr ist als ein Name fuer zwei komplementaere Pole. Die
  Zuordnung ist EINE Formalisierung, keine autoritative.
* **Fragment**: Jede Deutung der Kreuzkopplung zwischen verschiedenen Paaren
  als "Nicht-Kommutativitaet hoeherer Ordnung". Der Parameter existiert und
  wirkt; seine Deutung ist unbelegt.

Nutzt denselben bestehenden Solver-Pfad wie der zweipolige Fall (qb_qubo ueber
QUBOAscensionOptimizer) statt einer neuen Optimierungs-Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class PolePair:
    """Ein komplementaeres Polpaar. `yin` ist der Pol, der mit der Zeit an
    Attraktivitaet verliert, `yang` der, der gewinnt."""
    name: str
    yin: str
    yang: str


#: Die drei Paare, die im Kanon bereits vorkommen (Triple-Yin-Yang-Modus).
#: Reihenfolge ist bedeutsam: Sie folgt der Reihenfolge der Boegen.
TRIPLE_CANON: Tuple[PolePair, PolePair, PolePair] = (
    PolePair("qb", "b", "q"),
    PolePair("impression_expression", "impression", "expression"),
    PolePair("devil_christus", "devil", "christus"),
)


@dataclass
class ManifoldSpec:
    """Deklarierte Form des Zustandsraums — reine Buchhaltung, keine Deutung."""
    n_pairs: int
    n_checkpoints: int

    @property
    def dimension(self) -> int:
        """Dimension des binaeren Zustandsraums: 2 Pole * k Paare * n Checkpoints."""
        return 2 * self.n_pairs * self.n_checkpoints

    def index(self, pair: int, pole: str, checkpoint: int) -> int:
        """Index einer Variablen in x. `pole` ist "yin" oder "yang"."""
        if pole not in ("yin", "yang"):
            raise ValueError(f"pole must be 'yin' or 'yang', got {pole!r}")
        if not 0 <= pair < self.n_pairs:
            raise IndexError(f"pair {pair} out of range (n_pairs={self.n_pairs})")
        if not 0 <= checkpoint < self.n_checkpoints:
            raise IndexError(
                f"checkpoint {checkpoint} out of range (n={self.n_checkpoints})"
            )
        offset = pair * 2 * self.n_checkpoints
        if pole == "yang":
            offset += self.n_checkpoints
        return offset + checkpoint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_pairs": self.n_pairs,
            "n_checkpoints": self.n_checkpoints,
            "dimension": self.dimension,
        }


def build_yin_yang_qubo(
    n_checkpoints: int,
    pairs: Sequence[PolePair] = TRIPLE_CANON,
    base_bias: float = 1.0,
    incoherence_penalty: float = 2.0,
    lock_in_penalty: float = 0.5,
    oscillation_tail_fraction: float = 0.3,
    cross_pair_coupling: float = 0.0,
) -> np.ndarray:
    """Baut die QUBO-Matrix fuer k Polpaare ueber n Checkpoints.

    Die ersten vier Modellannahmen sind identisch mit dem zweipoligen Fall
    (build_devil_christus_qubo) und werden hier pro Paar angewandt:

      1. Linearer Bias ueber die Zeit: der Yin-Pol wird zunehmend unattraktiv,
         der Yang-Pol zunehmend attraktiv.
      2. Inkohaerenz-Strafe: beide Pole desselben Paares am selben Checkpoint
         gleichzeitig aktiv wird bestraft.
      3. Lock-in-Strafe im Oszillations-Schwanz: zwei aufeinanderfolgende
         Checkpoints mit demselben aktiven Pol werden leicht bestraft
         (Oszillation statt erstarrter Ein-Pol-Dominanz).
      4. NEU, und ausdruecklich Fragment-Status: `cross_pair_coupling` koppelt
         die Yang-Pole benachbarter Paare am selben Checkpoint. Bei 0.0
         (Default) sind die Paare vollstaendig entkoppelt und das Ergebnis ist
         die blockdiagonale Summe der Einzelpaare — dieser Default ist bewusst
         gewaehlt, damit die unbelegte Deutung nicht stillschweigend mitlaeuft.

    Mit ``pairs=(PolePair("devil_christus","devil","christus"),)`` und den
    Default-Parametern ist das Ergebnis bitgenau ``build_devil_christus_qubo``.
    """
    if n_checkpoints < 1:
        raise ValueError("n_checkpoints must be >= 1")
    if not pairs:
        raise ValueError("at least one PolePair required")

    spec = ManifoldSpec(n_pairs=len(pairs), n_checkpoints=n_checkpoints)
    n = n_checkpoints
    Q = np.zeros((spec.dimension, spec.dimension), dtype=np.float64)

    for p in range(spec.n_pairs):
        for i in range(n):
            t = i / max(1, n - 1)
            yin = spec.index(p, "yin", i)
            yang = spec.index(p, "yang", i)
            # 1. Bias: Yin verliert, Yang gewinnt ueber die Zeit
            Q[yin, yin] += base_bias * t
            Q[yang, yang] += -base_bias * t
            # 2. Inkohaerenz: nicht beides zugleich
            Q[yin, yang] += incoherence_penalty / 2.0
            Q[yang, yin] += incoherence_penalty / 2.0

        # 3. Lock-in im Oszillations-Schwanz
        tail_start = int(n * (1.0 - oscillation_tail_fraction))
        for i in range(max(tail_start, 0), n - 1):
            for pole in ("yin", "yang"):
                a = spec.index(p, pole, i)
                b = spec.index(p, pole, i + 1)
                Q[a, b] += lock_in_penalty / 2.0
                Q[b, a] += lock_in_penalty / 2.0

    # 4. Kreuzkopplung benachbarter Paare (Default 0.0 = aus)
    if cross_pair_coupling:
        for p in range(spec.n_pairs - 1):
            for i in range(n):
                a = spec.index(p, "yang", i)
                b = spec.index(p + 1, "yang", i)
                Q[a, b] += cross_pair_coupling / 2.0
                Q[b, a] += cross_pair_coupling / 2.0

    return Q


def incoherence_is_dominated(
    n_checkpoints: int,
    base_bias: float = 1.0,
    incoherence_penalty: float = 2.0,
) -> bool:
    """Prueft die Schranke, unter der 'beide Pole zugleich' strikt teuer ist.

    Schaltet man in einem Zustand mit yin_i = yang_i = 1 den Yin-Pol ab, so
    aendert sich die Energie um  -(base_bias * t_i) - incoherence_penalty.
    Wegen t_i <= 1 ist diese Differenz strikt negativ, sobald

        incoherence_penalty > base_bias.

    Dann ist der inkohaerente Zustand *immer* strikt energiereicher als seine
    kohaerente Reduktion — unabhaengig von n und vom Checkpoint.
    """
    if n_checkpoints < 1:
        raise ValueError("n_checkpoints must be >= 1")
    return incoherence_penalty > base_bias


def energy(Q: np.ndarray, x: Sequence[int]) -> float:
    """QUBO-Energie x^T Q x — dieselbe Konvention wie qb_qubo."""
    v = np.asarray(x, dtype=np.float64)
    return float(v @ Q @ v)


def describe(
    pairs: Sequence[PolePair] = TRIPLE_CANON,
    n_checkpoints: int = 12,
) -> Dict[str, Any]:
    """Maschinenlesbare Selbstauskunft — ohne Deutung, nur Struktur."""
    spec = ManifoldSpec(n_pairs=len(pairs), n_checkpoints=n_checkpoints)
    return {
        "mode": "triple" if len(pairs) == 3 else f"{len(pairs)}-fold",
        "pairs": [{"name": p.name, "yin": p.yin, "yang": p.yang} for p in pairs],
        **spec.to_dict(),
        "geltung": {
            "structure": "Satz (symmetrisch, Dimension 2*k*n, Reproduktion k=1)",
            "pair_choice": "Modell (eine Formalisierung, keine autoritative)",
            "cross_pair_coupling": "Fragment (Parameter wirkt, Deutung unbelegt)",
        },
    }
