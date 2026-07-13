"""Fitness-Berechnung + PeerReview-Integration."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.methodology.core_modules import PeerReviewCoreModule


def fitness_function(
    text: str,
    *,
    peer_review_score: float,
    performance_score: float,
    consistency_score: float,
) -> float:
    w_cons, w_perf, w_peer = 0.35, 0.35, 0.30
    length_penalty = min(1.0, len(text) / 500.0)
    return (
        w_cons * consistency_score
        + w_perf * performance_score
        + w_peer * peer_review_score
    ) * max(0.1, length_penalty)


def score_with_peer_review(
    text: str,
    context: Dict[str, Any],
    reviewer: Optional[PeerReviewCoreModule] = None,
) -> Dict[str, float]:
    """Nutzt echten 5-Dim-PeerReview wenn nicht in context vorgegeben."""
    if "peer_review_score" in context:
        peer = float(context["peer_review_score"])
    else:
        rev = (reviewer or PeerReviewCoreModule()).review(text)
        peer = float(rev["coverage"])
    perf = float(context.get("performance_score", 0.5))
    cons = float(context.get("consistency_score", 0.7))
    return {
        "peer_review_score": peer,
        "performance_score": perf,
        "consistency_score": cons,
        "fitness": fitness_function(
            text,
            peer_review_score=peer,
            performance_score=perf,
            consistency_score=cons,
        ),
    }