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


def main():
    q1 = "[cond] Wie verbindet die MER-Matrix Neurotheologie mit heroischer Mathematik?"
    use, reason = should_use_claude_science(q1)
    assert use and reason == "heroic_science", f"heroic: {use}, {reason}"
    assert is_heroic_science_query(q1)
    prov = select_provider_for_query(q1)
    assert prov == "claude-science", prov
    print("heroic science routing OK")

    q2 = "What is the role of CRISPR in single-cell genomics?"
    use2, reason2 = should_use_claude_science(q2)
    assert use2 and reason2 == "science_domain"
    print("science domain routing OK")

    unclear = "[Heroic Orchestration] Dom=General, Agent=general-worker, Geltung=model"
    assert is_unclear_response(unclear)
    use3, reason3 = should_use_claude_science("Erkläre Photosynthese kurz.", unclear)
    assert use3 and reason3 == "unclear_result", f"got {use3}, {reason3}"
    esc = escalate_to_science("Erkläre Photosynthese kurz.", unclear)
    assert esc.get("ok") and esc.get("response")
    print("unclear escalation OK:", esc.get("backend"), esc.get("route_reason"))

    res = analyze(q1)
    assert res.get("ok")
    assert res.get("meta", {}).get("subdomain") == "heroic_science"
    print("heroic analyze OK:", res.get("route_reason"))

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()