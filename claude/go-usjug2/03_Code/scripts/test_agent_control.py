"""Quick test for global agent_control module."""
import os
import sys

os.environ["FUSION_AGENT_CONTROL"] = "1"
os.environ["FUSION_AGENT_CONTROL_STRATEGIES"] = "geltung,peer_review,meta,audit"

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.agent_control import status, pre_dispatch, verify_text
from core.heroic_orchestration import create_classified_task


def test_status_enabled():
    s = status()
    assert s["enabled"], "control should be enabled"


def test_pre_dispatch_good_query_passes():
    t1 = {"query": "[model] Test query mit Geltung", "dom": "Info", "geltung": "model", "id": 1}
    r1 = pre_dispatch(t1)
    assert r1.passed, "good query should pass"


def test_pre_dispatch_bad_query_blocked():
    t2 = {"query": "ohne kategorie", "dom": "General", "id": 2}
    r2 = pre_dispatch(t2)
    assert r2.blocked, "bad query should be blocked (fail-closed)"


def test_classified_task_has_control_pre():
    task = create_classified_task("[cond] QUBO Optimierung test")
    assert task.get("control_pre"), "task should have control_pre"


def test_verify_text_passes_well_formed_review():
    """Ein Text, der wirklich >=4/5 PeerReview-Dimensionen trifft, muss passieren."""
    text = (
        "Laut Quelle X folgt daher die Kernaussage. Jedoch waere alternativ auch Y denkbar. "
        "Als Handlungsempfehlung ergibt sich der naechste Schritt. Es bestehen noch offene Risiken."
    )
    v = verify_text(text, {"dom": "Phil", "geltung": "model"})
    assert v["passed"], f"gut formulierter Text sollte PeerReview bestehen: {v}"


def test_verify_text_fails_underspecified_text():
    """Fail-closed-Beleg: ein Text mit nur 2/5 Dimensionen wird korrekt abgelehnt.

    (Frueher wurde dieses Ergebnis nur geprintet, nie assertiert - die
    urspruengliche Beispielformulierung erfuellt die PeerReview-Schwelle
    (>=4/5) nie, unabhaengig vom Code; das ist korrektes Fail-Closed-Verhalten,
    kein Bug.)
    """
    text = "[model] Antwort mit Empfehlung und Risiko-Hinweis."
    v = verify_text(text, {"dom": "Phil", "geltung": "model"})
    assert not v["passed"], "unterspezifizierter Text sollte NICHT bestehen (fail-closed)"
    peer_review = next(s for s in v["post"]["strategies"] if s["strategy"] == "peer_review")
    assert peer_review["details"]["score"] < 4


def main():
    test_status_enabled()
    print("status OK")
    test_pre_dispatch_good_query_passes()
    print("pre good OK")
    test_pre_dispatch_bad_query_blocked()
    print("pre bad blocked OK")
    test_classified_task_has_control_pre()
    print("classified task OK")
    test_verify_text_passes_well_formed_review()
    print("verify (gut formuliert) passed OK")
    test_verify_text_fails_underspecified_text()
    print("verify (unterspezifiziert) korrekt abgelehnt OK")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
