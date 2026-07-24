# -*- coding: utf-8 -*-
"""
AscensionOS - MpressionProjection (v2.0, axiomatisch verankert)

Operationalisiert die im Gemini-Brainstorm vom 2026-07-24 verwendete
"M-pression" (Projektions-/Reibungsverlust beim Uebergang latent -> manifest)
als messbaren Orthogonalprojektions-Verlust:

    loss = ||v - P v||_2,   P = U U^T  (Orthogonalprojektor auf span(U))

Axiom-Anker: proof_registry.yaml K17 (Orthogonalprojektor, BEWIESEN) und
MPRESSION-PROJECTION-LOSS (BEWIESEN). Nutzt denselben bewiesenen
OrthogonalProjector wie die Knoten-17-Tests (heroic_math_engine.py) statt
neuer, unbewiesener Projektionslogik — gleiche Wiederverwendungs-Konvention
wie geisterjagd_module.py (BanachContractionSeed).

Ehrlicher Status: Die Verlustmessung ist reine lineare Algebra (Satz-Ebene:
Pythagoras-Zerlegung ||v||^2 = ||Pv||^2 + ||v-Pv||^2 folgt aus K17). Die
DEUTUNG "v = Intention im latenten Raum, span(U) = manifestierbarer
Unterraum, loss = M-pression" ist ein MODELL aus dem Brainstorm — keine
gemessene psychologische oder physikalische Groesse. Dieses Modul macht den
Begriff berechenbar, nicht wahr.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

try:
    _ROOT = str(Path(__file__).resolve().parents[2])
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from fusion_hero_os.core.heroic_math_engine import OrthogonalProjector
except Exception:
    OrthogonalProjector = None


@dataclass
class MpressionResult:
    loss: float
    relative_loss: float
    norm_original: float
    norm_projected: float
    pythagoras_residual: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loss": self.loss,
            "relative_loss": self.relative_loss,
            "norm_original": self.norm_original,
            "norm_projected": self.norm_projected,
            "pythagoras_residual": self.pythagoras_residual,
        }


def measure_mpression(v: Any, basis_candidates: Any) -> Optional[MpressionResult]:
    """Projektionsverlust von v auf span(basis_candidates).

    Liefert None statt eines Fake-Ergebnisses, wenn der bewiesene
    OrthogonalProjector (K17) nicht importierbar ist — dieselbe
    Fail-Honest-Konvention wie Geisterjagdmodul.hunt().
    """
    if OrthogonalProjector is None:
        return None

    v_arr = np.asarray(v, dtype=np.float64)
    projector = OrthogonalProjector(np.asarray(basis_candidates, dtype=np.float64))
    projected = projector.project(v_arr)
    residual = v_arr - projected

    norm_original = float(np.linalg.norm(v_arr))
    norm_projected = float(np.linalg.norm(projected))
    loss = float(np.linalg.norm(residual))
    relative_loss = loss / norm_original if norm_original > 0.0 else 0.0
    pythagoras_residual = abs(norm_original ** 2 - (norm_projected ** 2 + loss ** 2))

    return MpressionResult(
        loss=loss,
        relative_loss=relative_loss,
        norm_original=norm_original,
        norm_projected=norm_projected,
        pythagoras_residual=pythagoras_residual,
    )


if __name__ == "__main__":
    import json

    # Demo: 3D-"Intention", manifestierbarer Unterraum = x/y-Ebene.
    result = measure_mpression([1.0, 2.0, 3.0], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    print(json.dumps(result.to_dict() if result else {"error": "K17-Projektor fehlt"},
                     indent=2))
