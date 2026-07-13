"""Test Claude Science routing for heroic science and unclear escalation."""
import os
import sys

os.environ["FUSION_CLAUDE_SCIENCE"] = "1"
os.environ["FUSION_CLAUDE_SCIENCE_ESCALATE"] = "1"

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.claude_science import (
    should_use_claude_science,
    is_heroic_science_query,
    is_unclear_response,
    analyze,
    escalate_to_science,
)
from core.provider_switcher import select_provider_for_query

_Q1 = "[cond] Wie verbindet die MER-Matrix Neurotheologie mit heroischer Mathematik?"
_UNCLEAR = "[Heroic Orchestration] Dom=General, Agent=general-worker, Geltung=model"


def test_heroic_science_routing():
    use, reason = should_use_claude_science(_Q1)
    assert use and reason == "heroic_science", f"heroic: {use}, {reason}"
    assert is_heroic_science_query(_Q1)
    prov = select_provider_for_query(_Q1)
    assert prov == "claude-science", prov


def test_science_domain_routing():
    q2 = "What is the role of CRISPR in single-cell genomics?"
    use2, reason2 = should_use_claude_science(q2)
    assert use2 and reason2 == "science_domain"


def test_unclear_response_escalation():
    assert is_unclear_response(_UNCLEAR)
    use3, reason3 = should_use_claude_science("Erkläre Photosynthese kurz.", _UNCLEAR)
    assert use3 and reason3 == "unclear_result", f"got {use3}, {reason3}"
    esc = escalate_to_science("Erkläre Photosynthese kurz.", _UNCLEAR)
    assert esc.get("ok") and esc.get("response")


def test_heroic_analyze():
    res = analyze(_Q1)
    assert res.get("ok")
    assert res.get("meta", {}).get("subdomain") == "heroic_science"


def main():
    test_heroic_science_routing()
    print("heroic science routing OK")
    test_science_domain_routing()
    print("science domain routing OK")
    test_unclear_response_escalation()
    print("unclear escalation OK")
    test_heroic_analyze()
    print("heroic analyze OK")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
