# -*- coding: utf-8 -*-
from fusion_hero_os.core.dual_timeline_training import (
    build_samples,
    consistency_report,
    heroic_score_for_text,
    load_config,
    run_auto_train,
    scan_files,
    status,
    virtual_timelines_enabled,
)


def test_config_loads():
    c = load_config()
    assert c.get("policy") == "pseudo_inhouse_only"
    assert c.get("freemium") is False
    assert virtual_timelines_enabled(c) is True
    assert (c.get("heroic_optimization") or {}).get("enabled") is True


def test_scan_and_tau_bounds():
    events = scan_files()
    assert len(events) > 10
    for e in events[:50]:
        assert 0.0 <= e.tau <= 1.0
        assert 0.0 <= e.heroic_score <= 1.0
        assert e.t_real > 0
        assert e.rel


def test_heroic_score_markers():
    score, hits = heroic_score_for_text(
        "MasterSeed contraction and Eudaimonia with PeerReview and Geltung Satz"
    )
    assert score > 0.0
    assert hits


def test_samples_dual_and_virtual_axes():
    samples = build_samples()
    assert len(samples) > 20
    dual = [s for s in samples if s.timeline == "dual"]
    virtual = [s for s in samples if s.timeline == "virtual"]
    assert dual
    # virtual allowed again under BIG ALPHA (heroic threshold may filter some runs)
    assert virtual_timelines_enabled() is True
    s = dual[0]
    assert "τ=" in s.prompt or "tau" in s.prompt.lower() or "τ" in s.prompt
    assert "heroisch" in s.prompt.lower() or "H=" in s.prompt
    assert s.t_real > 0
    assert 0.0 <= s.tau <= 1.0
    if virtual:
        assert "VIRTUAL" in virtual[0].prompt or virtual[0].meta.get("axis") == "virtual"
        assert virtual[0].meta.get("offense") == "FORBIDDEN"


def test_run_auto_train():
    r = run_auto_train(write=True)
    assert r.get("files", 0) > 0
    assert r.get("samples", 0) > 0
    assert r.get("virtual_timelines_enabled") is True
    assert "paths" in r
    st = status()
    assert st.get("freemium") is False
    assert st.get("virtual_timelines_enabled") is True
    assert st.get("axes", {}).get("v") == "virtual_heroic_scenario"
    assert st.get("heroic_optimization") is True


def test_consistency_shape():
    events = scan_files()
    samples = build_samples(events)
    c = consistency_report(events, samples, load_config())
    assert "tau_mean" in c
    assert "t_min_iso" in c
    assert c.get("files") == len(events)
