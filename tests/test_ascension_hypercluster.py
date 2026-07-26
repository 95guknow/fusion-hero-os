# -*- coding: utf-8 -*-
"""Tests für den AscensionHypercluster (Zitterpolymesh × AscensionOS)."""
from __future__ import annotations

from pathlib import Path

from ascension_os.hypercluster import (
    DEFAULT_GOVERNANCE,
    DEFAULT_UNITS,
    AscensionHypercluster,
    AscensionUnit,
)
from fusion_hero_os.core.zitterpolymesh import LaneKind, LaneProfile

REPO_ROOT = Path(__file__).resolve().parents[1]


def small_lanes() -> dict:
    return {
        kind: LaneProfile(kind=kind, workers=2, backend="threadpool", virtual=kind != LaneKind.CPU)
        for kind in LaneKind
    }


def test_governance_owner_is_senfkorn_holding():
    hc = AscensionHypercluster.from_config()
    assert hc.governance["owner"] == "Senfkorn Holding UG"
    assert hc.governance["track"] == "ascension"
    assert hc.governance["consent_required_for_personal_data"] is True


def test_default_constructor_uses_module_default_governance():
    """Ohne from_config() greift der Dataclass-Default DEFAULT_GOVERNANCE."""
    hc = AscensionHypercluster()
    assert hc.governance == DEFAULT_GOVERNANCE
    assert hc.governance is not DEFAULT_GOVERNANCE  # eigene Kopie, kein Alias


def test_all_four_lanes_used_by_default_units():
    lanes = {u.lane for u in DEFAULT_UNITS}
    assert lanes == set(LaneKind), "Hypercluster soll alle vier PVHT-Lanes bespielen"


def test_dag_validates_without_cycles():
    hc = AscensionHypercluster(units=list(DEFAULT_UNITS), lanes=small_lanes())
    order = hc.validate()
    # consent-gate hat keine Deps -> muss vor seinen Abhängigen kommen
    assert order.index("consent-gate") < order.index("ascension-core")
    assert order.index("consent-gate") < order.index("persistent-sisyphos")


def test_operationalize_reports_every_ascension():
    hc = AscensionHypercluster(units=list(DEFAULT_UNITS), lanes=small_lanes())
    report = hc.operationalize(consent_ok=False, timeout=60.0)
    assert report["ok"] is True
    assert set(report["ascensions"]) == {u.name for u in DEFAULT_UNITS}
    assert report["governance"]["owner"] == "Senfkorn Holding UG"
    # Summe der Status-Buckets == Anzahl Einheiten
    s = report["summary"]
    assert s["operational"] + s["degraded"] + s["blocked_consent"] == s["total"] == len(DEFAULT_UNITS)


def test_consent_gate_fail_closed_by_default():
    """Personenbezogene Einheiten laufen ohne Grant NICHT als operational."""
    hc = AscensionHypercluster(units=list(DEFAULT_UNITS), lanes=small_lanes())
    report = hc.operationalize(consent_ok=False, timeout=60.0)
    for name in ("persistent-sisyphos", "stage9-tracker"):
        assert report["ascensions"][name]["status"] == "blocked_consent"
        assert report["ascensions"][name]["operational"] is False


def test_consent_ok_unblocks_personal_units():
    hc = AscensionHypercluster(units=list(DEFAULT_UNITS), lanes=small_lanes())
    blocked = hc.operationalize(consent_ok=False)["summary"]["blocked_consent"]
    granted = hc.operationalize(consent_ok=True)["summary"]["blocked_consent"]
    assert blocked == 2
    assert granted == 0  # mit Grant keine consent-Sperre mehr


def test_probe_is_honest_about_missing_module():
    """Ein nicht existierendes Modul -> degraded mit Fehlertext, kein Crash."""
    unit = AscensionUnit("ghost", LaneKind.CPU, "ascension_os.does_not_exist", "Nope")
    hc = AscensionHypercluster(units=[unit], lanes=small_lanes())
    report = hc.operationalize(consent_ok=True, timeout=30.0)
    rec = report["ascensions"]["ghost"]
    assert rec["status"] == "degraded"
    assert rec["importable"] is False
    assert rec["error"] and "does_not_exist" in rec["error"] or rec["error"]


def test_status_lists_units_and_lanes_without_running():
    hc = AscensionHypercluster.from_config()
    st = hc.status()
    assert st["ok"] is True
    assert st["count"] == len(hc.units)
    assert set(st["lanes"]) == {"cpu", "mem", "gpu", "qpu"}
    # QPU-Lane bleibt ehrlich virtuell
    assert st["lanes"]["qpu"]["virtual"] is True


def test_config_file_declares_senfkorn_and_all_units():
    import yaml

    cfg = yaml.safe_load((REPO_ROOT / "ascension_os" / "config" / "hypercluster.yaml").read_text(encoding="utf-8"))
    assert cfg["governance"]["owner"] == "Senfkorn Holding UG"
    names = {u["name"] for u in cfg["units"]}
    assert names == {u.name for u in DEFAULT_UNITS}
