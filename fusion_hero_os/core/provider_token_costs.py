"""Top-provider LLM token real-cost table (public list prices).

Geltung: **Bedingt** — public API list prices as of 2026-H1/H2 synthesis;
not a live billing scrape. EUR conversion via FUSION_USD_EUR (default 0.92).

Used to:
  * analyse real $/MTok for top providers
  * set competitive market ceilings for internal subcontractor pricing
  * feed L4 LLM burn into poly_mesh_cost_function v2.1
"""
from __future__ import annotations

import os
from typing import Any

__all__ = [
    "PROVIDER_RATES_USD_PER_1M",
    "usd_to_eur",
    "analyse_providers",
    "blended_top_tier_eur_per_1m",
    "market_ceilings_eur_per_1m",
    "estimate_llm_burn_eur_h",
]

# USD per 1M tokens — top public list prices (2026 synthesis; Bedingt)
# Prefer mid-tier flagship + fast tiers used in practice.
PROVIDER_RATES_USD_PER_1M: dict[str, dict[str, Any]] = {
    "openai_gpt4o": {
        "provider": "OpenAI",
        "model": "GPT-4o",
        "input": 2.50,
        "output": 10.00,
        "tier": "flagship",
        "context_k": 128,
    },
    "openai_gpt4_1": {
        "provider": "OpenAI",
        "model": "GPT-4.1",
        "input": 2.00,
        "output": 8.00,
        "tier": "flagship",
        "context_k": 1000,
    },
    "openai_gpt4o_mini": {
        "provider": "OpenAI",
        "model": "GPT-4o mini",
        "input": 0.15,
        "output": 0.60,
        "tier": "fast",
        "context_k": 128,
    },
    "anthropic_claude_sonnet": {
        "provider": "Anthropic",
        "model": "Claude Sonnet 4.x",
        "input": 3.00,
        "output": 15.00,
        "tier": "flagship",
        "context_k": 200,
    },
    "anthropic_claude_opus": {
        "provider": "Anthropic",
        "model": "Claude Opus 4.x",
        "input": 5.00,
        "output": 25.00,
        "tier": "frontier",
        "context_k": 200,
    },
    "anthropic_claude_haiku": {
        "provider": "Anthropic",
        "model": "Claude Haiku 4.x",
        "input": 0.80,
        "output": 4.00,
        "tier": "fast",
        "context_k": 200,
    },
    "google_gemini_2_5_pro": {
        "provider": "Google",
        "model": "Gemini 2.5 Pro",
        "input": 1.25,
        "output": 10.00,
        "tier": "flagship",
        "context_k": 1000,
    },
    "google_gemini_2_5_flash": {
        "provider": "Google",
        "model": "Gemini 2.5 Flash",
        "input": 0.15,
        "output": 0.60,
        "tier": "fast",
        "context_k": 1000,
    },
    "xai_grok_4": {
        "provider": "xAI",
        "model": "Grok 4",
        "input": 3.00,
        "output": 15.00,
        "tier": "flagship",
        "context_k": 128,
    },
    "xai_grok_4_fast": {
        "provider": "xAI",
        "model": "Grok 4 Fast",
        "input": 0.20,
        "output": 0.50,
        "tier": "fast",
        "context_k": 128,
    },
}


def usd_to_eur(usd: float) -> float:
    rate = float(os.getenv("FUSION_USD_EUR", "0.92"))
    return float(usd) * max(rate, 0.01)


def analyse_providers(
    *,
    in_share: float = 0.70,
    out_share: float = 0.30,
) -> dict[str, Any]:
    """Rank providers by blended cost for typical chat mix (70% in / 30% out)."""
    rows: list[dict[str, Any]] = []
    for key, r in PROVIDER_RATES_USD_PER_1M.items():
        blend_usd = r["input"] * in_share + r["output"] * out_share
        blend_eur = usd_to_eur(blend_usd)
        rows.append(
            {
                "id": key,
                "provider": r["provider"],
                "model": r["model"],
                "tier": r["tier"],
                "usd_in_per_1m": r["input"],
                "usd_out_per_1m": r["output"],
                "usd_blend_per_1m": round(blend_usd, 4),
                "eur_blend_per_1m": round(blend_eur, 4),
                "eur_in_per_1m": round(usd_to_eur(r["input"]), 4),
                "eur_out_per_1m": round(usd_to_eur(r["output"]), 4),
                "context_k": r["context_k"],
            }
        )
    rows.sort(key=lambda x: x["eur_blend_per_1m"])
    flagship = [x for x in rows if x["tier"] == "flagship"]
    fast = [x for x in rows if x["tier"] == "fast"]
    frontier = [x for x in rows if x["tier"] == "frontier"]
    return {
        "ok": True,
        "geltung": "Bedingt — public list prices 2026 synthesis; not live billing",
        "usd_eur": float(os.getenv("FUSION_USD_EUR", "0.92")),
        "mix": {"input_share": in_share, "output_share": out_share},
        "cheapest_blend": rows[0] if rows else None,
        "most_expensive_blend": rows[-1] if rows else None,
        "flagship_median_eur_per_1m": _median([x["eur_blend_per_1m"] for x in flagship]),
        "fast_median_eur_per_1m": _median([x["eur_blend_per_1m"] for x in fast]),
        "frontier_median_eur_per_1m": _median([x["eur_blend_per_1m"] for x in frontier]),
        "rows": rows,
        "top_by_provider": _top_per_provider(rows),
    }


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return round((s[n // 2 - 1] + s[n // 2]) / 2, 4)


def _top_per_provider(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best: dict[str, Any] = {}
    for r in rows:
        p = r["provider"]
        if p not in best or r["eur_blend_per_1m"] < best[p]["eur_blend_per_1m"]:
            best[p] = r
    return best


def blended_top_tier_eur_per_1m(*, prefer: str = "flagship") -> float:
    a = analyse_providers()
    if prefer == "fast":
        return float(a.get("fast_median_eur_per_1m") or 0.7)
    if prefer == "frontier":
        return float(a.get("frontier_median_eur_per_1m") or 15.0)
    return float(a.get("flagship_median_eur_per_1m") or 8.0)


def market_ceilings_eur_per_1m() -> dict[str, float]:
    """Ceilings for internal subcontractor tiers from real market out-prices."""
    a = analyse_providers()
    # map internal tiers → market ceilings (EUR / 1M tokens, output-heavy)
    flagship_out = []
    fast_out = []
    for r in a["rows"]:
        if r["tier"] == "flagship":
            flagship_out.append(r["eur_out_per_1m"])
        if r["tier"] == "fast":
            fast_out.append(r["eur_out_per_1m"])
    return {
        "inference_standard": _median(flagship_out) or 12.0,
        "inference_gpu": (_median(flagship_out) or 12.0) * 1.4,
        "qubo_enterprise": (_median(flagship_out) or 12.0) * 2.0,
        "mesh_ops": _median(fast_out) or 1.5,
        "poly_mesh_orchestration": _median(fast_out) or 1.5,
    }


def estimate_llm_burn_eur_h(
    tokens_in_per_h: float = 0.0,
    tokens_out_per_h: float = 0.0,
    *,
    provider_id: str = "anthropic_claude_sonnet",
) -> dict[str, Any]:
    """EUR/h LLM burn from token throughput and a provider rate row."""
    r = PROVIDER_RATES_USD_PER_1M.get(provider_id) or PROVIDER_RATES_USD_PER_1M["anthropic_claude_sonnet"]
    cost_usd = (tokens_in_per_h / 1e6) * r["input"] + (tokens_out_per_h / 1e6) * r["output"]
    cost_eur = usd_to_eur(cost_usd)
    return {
        "provider_id": provider_id,
        "model": r["model"],
        "tokens_in_per_h": tokens_in_per_h,
        "tokens_out_per_h": tokens_out_per_h,
        "eur_h": round(cost_eur, 6),
        "usd_h": round(cost_usd, 6),
        "rates_usd_per_1m": {"input": r["input"], "output": r["output"]},
    }
