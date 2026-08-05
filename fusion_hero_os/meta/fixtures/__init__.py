"""Synthetic, neutral test fixtures — no real personal data.

Subject ids are opaque and derived; node/edge content is abstract ("concept_*").
These fixtures are safe to ship in the public repository.
"""

from __future__ import annotations

from typing import Dict, List

from ..vault import SubjectRef


def load_neutral_fixture() -> dict[str, object]:
    subject_id = SubjectRef.derive("fixture-subject-001").subject_id
    nodes: list[dict] = [
        {"node_id": "concept_a", "type": "concept",
         "dimensions": {"salience": 0.9, "valence": 0.2, "recency": 0.5}},
        {"node_id": "concept_b", "type": "concept",
         "dimensions": {"salience": 0.6, "valence": -0.1, "recency": 0.8}},
        {"node_id": "concept_c", "type": "concept",
         "dimensions": {"salience": 0.3, "valence": 0.4, "recency": 0.2}},
        {"node_id": "concept_d", "type": "artifact",
         "dimensions": {"salience": 0.7, "valence": 0.0, "recency": 0.9}},
    ]
    edges: list[dict] = [
        {"edge_id": "e1", "type": "relates_to", "source": "concept_a",
         "target": "concept_b", "weight": 0.8},
        {"edge_id": "e2", "type": "relates_to", "source": "concept_b",
         "target": "concept_c", "weight": 0.4},
        {"edge_id": "e3", "type": "derived_from", "source": "concept_d",
         "target": "concept_a", "weight": 0.6},
    ]
    activations = {"concept_a": 0.9, "concept_b": 0.7, "concept_d": 0.5}
    return {
        "subject_id": subject_id,
        "nodes": nodes,
        "edges": edges,
        "activations": activations,
    }
