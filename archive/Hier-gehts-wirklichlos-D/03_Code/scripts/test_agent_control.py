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


def main():
    s = status()
    assert s["enabled"], "control should be enabled"
    print("status OK:", s["strategies"], s["modules"])

    t1 = {"query": "[model] Test query mit Geltung", "dom": "Info", "geltung": "model", "id": 1}
    r1 = pre_dispatch(t1)
    assert r1.passed, "good query should pass"
    print("pre good OK")

    t2 = {"query": "ohne kategorie", "dom": "General", "id": 2}
    r2 = pre_dispatch(t2)
    assert r2.blocked, "bad query should be blocked (fail-closed)"
    print("pre bad blocked OK:", r2.reason)

    task = create_classified_task("[cond] QUBO Optimierung test")
    assert task.get("control_pre"), "task should have control_pre"
    print("classified task OK:", task.get("assigned_agent"))

    v = verify_text(
        "[model] Antwort mit Empfehlung und Risiko-Hinweis.",
        {"dom": "Phil", "geltung": "model"},
    )
    print("verify passed:", v["passed"])
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()