"""Adaptives Subagent-Kontextfenster + Banach-Rückkopplung zum Start-Kontext."""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE = os.path.join(_ROOT, "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from conversation_context_core import (
    allocate_subagent,
    feedback,
    get_context,
    init_root,
    is_enabled,
    status,
)
from heroic_orchestration import assign_task_to_agent, create_classified_task
from llama_subagent_tester import run as llama_run


def test_root_and_feedback_loop():
    assert is_enabled()
    root = init_root("[model] Adaptives Kontextfenster Test", {"task_weight": "medium"}, force_new=True)
    assert root["ok"]
    rid = root["root"]["window_id"]
    assert rid.startswith("root-")

    sub = allocate_subagent("math-worker", task_weight="medium", seed_fragment="QUBO Kurztest")
    wid = sub["subagent_window"]["window_id"]
    assert sub["subagent_window"]["parent_id"] == rid
    assert "Start-Kontext" in sub.get("prompt_block", "")

    fb = feedback(wid, "Ergebnis: Banach-Kontraktion λ=0.74 konvergiert zum Start-Anker.")
    assert fb["ok"]
    assert fb["root_window"] is not None
    assert fb["lambda"] == 0.74
    print("feedback loop OK:", fb["feedback"]["delta"][:80])


def test_orchestration_wiring():
    task = create_classified_task("[model] Kontextfenster Wiring", id=99)
    assert task.get("start_context_window")
    agent = assign_task_to_agent(task)
    assert agent
    assert task.get("subagent_context_window")
    print("orchestration wiring OK:", agent)


def test_llama_subagent_context():
    # llama_config_valid wurde bewusst NICHT verwendet: es erfordert einen echten
    # HeroicLlamaOptimizer-Trainingslauf (heroic_llama_config.json wird erst von
    # train.py geschrieben), der pro Generation >180s CLI-Subprocess-Zeit braucht
    # (kein llama-cpp-python installiert -> CLI-Fallback). Das würde diesen Test
    # von einer langsamen, hardwareabhängigen LLM-Generierung abhängig machen,
    # obwohl er eigentlich nur die Subagent-Kontextfenster-Verdrahtung prüft.
    # llama_cli_binary prüft stattdessen schnell + deterministisch (reine
    # Dateisystem-Prüfung) einen dritten, unabhängigen Subagenten-Kanal.
    result = llama_run(
        subagents=["llama_status", "llama_model_file", "llama_cli_binary"],
        include_generate=False,
        seed_context="Llama-Kontextfenster-Test",
    )
    assert result.get("start_context_window")
    assert result["subagents_ok"] >= 3
    tracks_with_ctx = [t for t in result["tracks"] if t.get("context_window")]
    assert len(tracks_with_ctx) >= 3
    st = status()
    assert st["feedback_log_len"] >= 3
    print("llama subagent context OK:", result["subagents_ok"], "/", result["subagents_total"])


def main():
    test_root_and_feedback_loop()
    test_orchestration_wiring()
    test_llama_subagent_context()
    print("ALL CONTEXT WINDOW TESTS PASSED")


if __name__ == "__main__":
    main()