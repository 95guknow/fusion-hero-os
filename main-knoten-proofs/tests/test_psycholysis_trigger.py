# -*- coding: utf-8 -*-
"""Tests fuer die verpflichtende somatische Integrationsphase (v8.1)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fusion_hero_os.core.psycholysis_trigger import SOMATIC_CHECKLIST, PsycholysisTrigger


def test_should_trigger_thresholds_unchanged():
    t = PsycholysisTrigger(threshold=0.75)
    assert t.should_trigger(coherence_score=0.5, load_level=0.1)
    assert t.should_trigger(coherence_score=0.9, load_level=0.9)
    assert not t.should_trigger(coherence_score=0.9, load_level=0.1)


def test_trigger_has_real_timestamp_and_open_somatic_phase():
    t = PsycholysisTrigger()
    s = t.trigger({"anlass": "test"})
    assert s["timestamp"] != "now"
    assert "T" in s["timestamp"]  # ISO-8601
    assert set(s["somatic_phase"]) == set(SOMATIC_CHECKLIST)
    assert not any(s["somatic_phase"].values())


def test_complete_session_blocked_until_somatic_phase_done():
    """PSYCHOLYSE-SOMATIC-PFLICHT: Abschluss ohne vollstaendige Somatikphase
    ist unmoeglich; nach vollstaendigem Logging klappt er."""
    t = PsycholysisTrigger()
    s = t.trigger({})
    with pytest.raises(ValueError, match="unvollstaendig"):
        t.complete_session(s)
    for item in SOMATIC_CHECKLIST[:-1]:
        t.log_somatic_practice(s, item)
    with pytest.raises(ValueError, match=SOMATIC_CHECKLIST[-1]):
        t.complete_session(s)
    t.log_somatic_practice(s, SOMATIC_CHECKLIST[-1], note="Spaziergang")
    done = t.complete_session(s)
    assert done["completed_at"] is not None
    assert len(done["somatic_log"]) == len(SOMATIC_CHECKLIST)


def test_unknown_checklist_item_rejected():
    t = PsycholysisTrigger()
    s = t.trigger({})
    with pytest.raises(ValueError, match="Unbekannter"):
        t.log_somatic_practice(s, "netflix")
