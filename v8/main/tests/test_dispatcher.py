# -*- coding: utf-8 -*-
"""Gates für Dispatcher, BaseModule-Vertrag und die Core-Module aus
fusion_hero_os/modules/.

Deckt ab: Registrierung/Routing, Fehlerfall bei unbekanntem Modul, parallele
Ausführung, sowie je Modul einen minimalen Funktionsnachweis. Für
SelfModify/PeerReview/Weltraudaimonia/MER wird zusätzlich geprüft, dass sie
sich an ihr dokumentiertes Sicherheitsversprechen halten (keine automatische
Anwendung, kein "automatisch bestanden" ohne echte Kriterien).
"""
import numpy as np
import pytest

from fusion_hero_os.core.base_module import BaseModule, EvolutionProposal, ReviewResult
from fusion_hero_os.core.dispatcher import (
    Dispatcher,
    ModuleNotRegisteredError,
    build_default_dispatcher,
)
from fusion_hero_os.modules import ALL_CORE_MODULES


class _EchoModule(BaseModule):
    name = "echo"

    def process(self, payload=None):
        return payload


def test_register_and_dispatch_routes_to_process():
    dispatcher = Dispatcher()
    dispatcher.register(_EchoModule())
    assert dispatcher.dispatch("echo", {"x": 1}) == {"x": 1}


def test_dispatch_unknown_module_raises_clear_error():
    dispatcher = Dispatcher()
    with pytest.raises(ModuleNotRegisteredError):
        dispatcher.dispatch("does-not-exist")


def test_dispatch_many_parallel_preserves_order():
    dispatcher = Dispatcher()
    dispatcher.register(_EchoModule())
    results = dispatcher.dispatch_many([("echo", i) for i in range(8)], parallel=True)
    assert results == list(range(8))


def test_base_module_defaults_are_neutral_not_silently_passing():
    class Bare(BaseModule):
        def process(self, payload=None):
            return None

    m = Bare()
    assert m.propose_evolution() is None
    review = m.peer_review()
    assert isinstance(review, ReviewResult)
    assert review.passed is False  # keine Kriterien definiert -> nicht "automatisch bestanden"


def test_build_default_dispatcher_registers_all_core_modules():
    dispatcher = build_default_dispatcher()
    registered = set(dispatcher.list_modules())
    expected = {cls.__name__ for cls in ALL_CORE_MODULES}
    assert expected <= registered


def test_self_modify_never_applies_only_records_proposal():
    dispatcher = build_default_dispatcher()
    module = dispatcher._get("SelfModifyCoreModule")
    proposal = dispatcher.propose_evolution(
        "SelfModifyCoreModule",
        {"target_module": "engine.mainframe", "summary": "x", "rationale": "y", "diff": "--- a\n+++ b"},
    )
    assert isinstance(proposal, EvolutionProposal)
    assert proposal.requires_review is True
    # Der Vorschlag landet in der Historie als "pending_review" -- nicht als angewendet.
    history = module.history()
    assert history[-1]["status"] == "pending_review"
    assert history[-1]["diff"] == "--- a\n+++ b"


def test_code_review_checklist_fails_when_any_criterion_missing():
    dispatcher = build_default_dispatcher()
    result = dispatcher.dispatch("PeerReviewCoreModule", {
        "correctness_verified": True,
        "tests_added": False,
        "style_checked": True,
        "security_reviewed": True,
        "docs_updated": True,
        "performance_considered": True,
    })
    assert isinstance(result, ReviewResult)
    assert result.passed is False
    assert result.score == pytest.approx(5 / 6)


def test_code_review_checklist_passes_when_all_criteria_met():
    dispatcher = build_default_dispatcher()
    payload = {
        "correctness_verified": True, "tests_added": True, "style_checked": True,
        "security_reviewed": True, "docs_updated": True, "performance_considered": True,
    }
    assert dispatcher.dispatch("PeerReviewCoreModule", payload).passed is True
    assert dispatcher.peer_review("PeerReviewCoreModule", payload).passed is True


def test_weltraudaimonia_score_is_bounded_and_carries_disclaimer():
    dispatcher = build_default_dispatcher()
    out = dispatcher.dispatch("WeltraudaimoniaModule", {"scores": {"stakeholder_breadth": 1.0}})
    assert 0.0 <= out["weltraudaimonia_score"] <= 1.0
    assert "disclaimer" in out


def test_mer_module_index_and_optimize_priority_order():
    dispatcher = build_default_dispatcher()
    values = {"stability": 0.9, "capacity": 0.2, "alignment": 0.5}
    out = dispatcher.dispatch("MERModule", {"values": values})
    assert 0.0 <= out["mer_index"] <= 1.0

    mer_module = dispatcher._get("MERModule")
    priorities = mer_module.optimize({"values": values})["priority_order"]
    # "capacity" hat den größten Rückstand -> muss oben stehen.
    assert priorities[0]["name"] == "capacity"


def test_conversation_context_evicts_oldest_beyond_max_turns():
    dispatcher = Dispatcher()
    from fusion_hero_os.modules.conversation_context import ConversationContextCoreModule

    dispatcher.register(ConversationContextCoreModule(max_turns=2))
    for i in range(5):
        dispatcher.dispatch("ConversationContextCoreModule", {"action": "add", "content": str(i)})
    window = dispatcher.dispatch("ConversationContextCoreModule", {"action": "window"})["window"]
    assert [t["content"] for t in window] == ["3", "4"]


def test_live_process_tracking_lifecycle_and_unknown_process_error():
    dispatcher = build_default_dispatcher()
    dispatcher.dispatch("LiveProcessTrackingCoreModule", {"name": "job", "action": "start"})
    result = dispatcher.dispatch("LiveProcessTrackingCoreModule", {"name": "job", "action": "fail"})
    assert result["status"] == "failed"

    with pytest.raises(KeyError):
        dispatcher.dispatch("LiveProcessTrackingCoreModule", {"name": "ghost", "action": "complete"})


def test_generational_evolution_fitness_is_monotonic_non_decreasing():
    dispatcher = Dispatcher()
    from fusion_hero_os.modules.generational_evolution import (
        GenerationalEvolutionProtocolCoreModule,
    )

    dispatcher.register(GenerationalEvolutionProtocolCoreModule())
    result = dispatcher.dispatch("GenerationalEvolutionProtocolCoreModule", {
        "init": {"n": 6, "mu": 2, "lam": 3, "seed": 1},
        "n_generations": 3,
    })
    history = result["fitness_history"]
    assert all(b >= a - 1e-9 for a, b in zip(history, history[1:]))


def test_qubo_integration_matches_known_ground_state():
    dispatcher = Dispatcher()
    from fusion_hero_os.modules.qubo_integration import QUBOIntegrationCoreModule

    dispatcher.register(QUBOIntegrationCoreModule())
    Q = -np.eye(5)
    result = dispatcher.dispatch("QUBOIntegrationCoreModule", {"problem_matrix": Q})
    assert abs(result.energy - (-5)) < 1e-9
