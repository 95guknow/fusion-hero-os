"""Ehrliche Regressionstests für fusion_hero_os/core/heroic_core_orchestrator.py.

Verankert den tatsächlichen Stand (Fail-Closed real, Integritätsprüfung seit
2026-07-04 echt, PMS-Kernel Platzhalter) - siehe
docs/02_architecture/HEROIC_CORE_ORCHESTRATOR.md.
"""
import pytest

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed, PMSEvidenceSpine, QuadCoreBridge


def test_master_seed_verify_integrity_is_real():
    """verify_integrity() prüft echt: nur der kanonische state_hash() gilt (seit 2026-07-04)."""
    seed = MasterSeed()
    assert seed.verify_integrity(seed.state_hash()) is True
    assert seed.verify_integrity("beliebiger_hash") is False
    assert seed.verify_integrity("") is False
    assert seed.verify_integrity(None) is False  # type: ignore[arg-type]
    assert "PLATZHALTER" not in (seed.verify_integrity.__doc__ or "")


def test_pms_spine_fails_closed_when_kernel_missing():
    """Ohne ./pms_rust_kernel-Binary muss JEDE Ausführung FAIL_CLOSED liefern."""
    spine = PMSEvidenceSpine(executable_path="./definitiv_nicht_vorhandenes_kernel_binary")
    result = spine.execute_operator_chain("OP_TEST", {"action": "test"})
    assert result["status"] == "FAIL_CLOSED"


def test_quad_core_bridge_rejects_invalid_domain():
    bridge = QuadCoreBridge(PMSEvidenceSpine())
    with pytest.raises(ValueError):
        bridge.process_query("UNGUELTIG", "OP_TEST", {})


def test_quad_core_bridge_gestalt_routes_to_failing_spine():
    """GESTALT/BEWEIS leiten an den Spine weiter, der mangels Kernel FAIL_CLOSED liefert."""
    bridge = QuadCoreBridge(PMSEvidenceSpine())
    result = bridge.process_query("GESTALT", "OP_Q_B_CIRC", {"action": "test"})
    assert result["status"] == "FAIL_CLOSED"


def test_phoenix_mode_does_not_reset_real_state():
    """Phoenix-Mode ist aktuell reines Logging - kein Attribut wird zurückgesetzt."""
    bridge = QuadCoreBridge(PMSEvidenceSpine())
    attrs_before = set(vars(bridge).keys())
    bridge.invoke_phoenix_mode()
    assert bridge.mode == "PHOENIX"
    assert set(vars(bridge).keys()) == attrs_before, (
        "Falls hier neue Attribute entstehen, wurde eventuell ein echter "
        "State-Reset eingebaut - dann sollte diese Doku/dieser Test aktualisiert werden."
    )
