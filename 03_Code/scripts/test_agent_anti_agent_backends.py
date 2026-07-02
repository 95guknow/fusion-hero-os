"""Agent→Llama, Anti-Agent→Grok Policy-Test."""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE = os.path.join(_ROOT, "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from agent_backend_router import policy, backend_for_role, annotate_task, invoke
from heroic_orchestration import assign_task_to_agent


def main():
    pol = policy()
    assert pol["agent_backend"] == "llama-local"
    assert pol["anti_agent_backend"] == "grok-intern"
    print("policy OK")

    t = {"query": "[model] QUBO Test", "dom": "Math", "id": 1}
    agent = assign_task_to_agent(t)
    assert agent == "math-worker"
    assert t.get("backend") == "llama-local"
    print("agent assign OK:", agent, t.get("backend"))

    t2 = {"query": "[model] prüfe epistemisch", "dom": "Phil", "anti_agent": True, "id": 2}
    anti = assign_task_to_agent(t2)
    assert anti.startswith("anti-")
    assert t2.get("backend") == "grok-intern"
    print("anti-agent assign OK:", anti, t2.get("backend"))

    grok = invoke("anti_agent", "Kurzer Anti-Agent Ping", {"health": {}})
    print("anti invoke ok:", grok.get("ok"), grok.get("backend"))
    assert grok.get("backend") in ("grok-intern", "grok-api/grok")

    print("ALL BACKEND ROUTING TESTS PASSED")


if __name__ == "__main__":
    main()