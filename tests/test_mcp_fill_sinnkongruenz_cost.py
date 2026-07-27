# -*- coding: utf-8 -*-
"""MCP fill band + Sinnkongruenz compress + provider costs v2.1."""
from __future__ import annotations

from fusion_hero_os.core.mcp_fill_governor import FillBand, McpFillGovernor, govern_messages
from fusion_hero_os.core.poly_mesh_cost_function import COST_FUNCTION_VERSION, compute_burn
from fusion_hero_os.core.provider_token_costs import analyse_providers, market_ceilings_eur_per_1m
from fusion_hero_os.core.sinnkongruenz_compressor import MessageUnit, compress_to_budget, score_unit


def test_cost_function_version_2_1():
    assert COST_FUNCTION_VERSION.startswith("2.1")


def test_provider_analysis_has_rows():
    a = analyse_providers()
    assert a["ok"]
    assert len(a["rows"]) >= 5
    assert a["flagship_median_eur_per_1m"] is not None
    ceilings = market_ceilings_eur_per_1m()
    assert "inference_standard" in ceilings


def test_llm_burn_in_compute_burn():
    b = compute_burn(
        llm_tokens_in_per_h=1_000_000,
        llm_tokens_out_per_h=200_000,
        llm_provider_id="anthropic_claude_sonnet",
    )
    assert b.l4_eur_h > 0
    assert b.detail.get("l4_llm_eur_h", 0) > 0


def test_llm_blend_kommt_aus_der_live_analyse():
    """Der Live-Zweig in compute_burn muss tatsaechlich durchlaufen.

    ``compute_burn`` kapselt die Live-Aktualisierung in ``try/except
    Exception``. Faellt darin irgendetwas um, greift still ein statischer
    Fallback und ``llm_burn`` bleibt leer — der Burn-Wert sieht dann trotzdem
    plausibel aus. Genau so blieb ein ``TypeError`` (positionaler Aufruf einer
    keyword-only-Funktion) lange unbemerkt: ``l4_llm_eur_h > 0`` galt auch im
    Fallback.

    Dieser Test prueft deshalb nicht den Wert, sondern dass der Zweig
    *durchgelaufen* ist.
    """
    b = compute_burn(
        llm_tokens_in_per_h=1_000_000,
        llm_tokens_out_per_h=300_000,
        llm_provider_id="anthropic_claude_sonnet",
    )
    llm_burn = b.detail.get("llm_burn")
    assert llm_burn, "llm_burn ist leer — der except-Zweig hat gegriffen"
    assert llm_burn.get("provider_id") == "anthropic_claude_sonnet"
    assert llm_burn.get("eur_h", 0) > 0

    # Der Blend stammt aus der Live-Analyse, nicht aus den statischen RATES_EUR.
    from fusion_hero_os.core.poly_mesh_cost_function import RATES_EUR

    blend = b.detail["rates"]["llm_flagship_blend_eur_per_1m"]
    assert blend != RATES_EUR["llm_flagship_blend_eur_per_1m"]


def test_blended_top_tier_ist_keyword_only():
    """Regression: der Aufruf muss keyword-only bleiben.

    Ein positionaler Aufruf wirft TypeError und wird von compute_burn
    verschluckt — deshalb hier direkt und ungekapselt geprueft.
    """
    import pytest

    from fusion_hero_os.core.provider_token_costs import blended_top_tier_eur_per_1m

    assert blended_top_tier_eur_per_1m(prefer="flagship") > 0
    with pytest.raises(TypeError):
        blended_top_tier_eur_per_1m("flagship")  # type: ignore[misc]


def test_sinnkongruenz_prefers_intent_match():
    intent = "QUBO mesh inject MasterSeed"
    hi = MessageUnit(role="user", content="QUBO anneal mesh inject MasterSeed layer")
    lo = MessageUnit(role="assistant", content="lorem ipsum dolor sit amet " * 40)
    assert score_unit(hi, intent=intent, index=1, n=2) > score_unit(
        lo, intent=intent, index=0, n=2
    )


def test_compress_lossless_no_information_loss():
    intent = "Banach contraction Geltung"
    long_body = "unique_fact_alpha = 42\n" + ("noise filler xyz " * 200) + "\nunique_fact_beta = 99"
    units = [
        MessageUnit(role="system", content="MasterSeed fixed", meta={"pin": True}),
        MessageUnit(role="user", content="Banach contraction Geltung proof QUBO"),
        MessageUnit(role="assistant", content=long_body),
    ]
    total = sum(u.tokens for u in units)
    budget = max(30, total // 3)
    out = compress_to_budget(units, max_tokens=budget, intent=intent, lossless=True)
    assert out["information_loss"] is False
    assert out["dropped"] == 0
    assert out["lossless"] is True
    assert any(u.meta.get("pin") for u in out["units"])
    # either densified enough or reversible offload with archive
    if out["offloaded"]:
        from fusion_hero_os.core.sinnkongruenz_compressor import rehydrate_from_archive

        sha = out["offload_index"][0]["sha"]
        full = rehydrate_from_archive(sha)
        assert full is not None
        assert "unique_fact_alpha" in full.content
        assert "unique_fact_beta" in full.content


def test_lossless_dedupe_preserves_unique():
    units = [
        MessageUnit(role="user", content="same line\nsame line\nunique only once"),
        MessageUnit(role="user", content="same line\nsame line\nunique only once"),
    ]
    out = compress_to_budget(units, max_tokens=10_000, intent="same")
    assert out["action"] in ("noop", "lossless_only")
    texts = "\n".join(u.content for u in out["units"])
    assert texts.count("unique only once") == 1
    assert "same line" in texts


def test_fill_governor_compresses_above_70():
    band = FillBand(window_tokens=1000, fill_min=0.40, fill_max=0.70, fill_target=0.55)
    gov = McpFillGovernor(band)
    units = [
        MessageUnit(role="system", content="MasterSeed", meta={"pin": True, "masterseed": True}),
        MessageUnit(role="user", content="important QUBO intent " * 5),
        MessageUnit(role="assistant", content=("zzzz " * 400)),
    ]
    out = gov.govern(units, intent="QUBO intent")
    fill = out["fill"]["fill_pct"]
    assert fill <= 0.70 + 0.05
    assert out["fill"]["action"] in (
        "compress_sinnkongruenz_lossless",
        "hold_in_band",
    )
    if out["fill"]["action"].startswith("compress"):
        assert out["fill"]["detail"].get("information_loss") is False


def test_govern_messages_api():
    msgs = [
        {"role": "user", "content": "hello mesh"},
        {"role": "assistant", "content": "world " * 10},
    ]
    out = govern_messages(msgs, intent="mesh")
    assert "messages" in out
    assert "fill" in out
