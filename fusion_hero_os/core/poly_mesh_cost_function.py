# -*- coding: utf-8 -*-
"""Poly-Mesh Cost Function v2.0 (2026-07-16).

Formal, measured-first cost model for Fusion Hero OS on L0–L4:

  C_h  = C_L1 + C_L2 + C_L3 + C_L4_est          [EUR/h real burn]
  E_h  = (C_h / p_grid) * PUE                   [kWh-equivalent / h]
  FEU_h = C_h * λ_FEU                           [Fusion Energy Units / h]

Subcontractor API price (per 1k tokens, tier t):

  c_1k(t) = C_h / κ(t) * 1000
  m*(t)   = competitive margin or floor under market ceiling
  P_1k(t) = max( P_min , min( c_1k(t)·(1+m*(t)) , ceiling_1k(t) ) )

Placement soft-cost (orchestration, does NOT override force_cluster):

  Π(tier) = π_base[tier] · (1 + load[tier])
  prefer argmin Π among online candidates subject to hard constraints.

Geltung: Spezifikation (Formel) · Raten = Bedingt/empirisch (europe-west3).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "COST_FUNCTION_VERSION",
    "RATES_EUR",
    "PLACEMENT_BASE",
    "compute_burn",
    "compute_feu",
    "tier_price",
    "placement_cost",
    "cost_function_status",
    "evaluate_full",
]

COST_FUNCTION_VERSION = "2.1.0"

# EUR rates — europe-west3 / Senfkorn 2026-07 (angemessene Defaults)
# v2.1: L4 LLM token burn from public provider list prices (provider_token_costs)
RATES_EUR: Dict[str, float] = {
    "gce_e2_micro_month": 7.50,
    "gce_e2_micro_hour": 7.50 / 730.0,
    "gcs_storage_gb_month": 0.023,  # STANDARD europe
    "gke_autopilot_mgmt_month": 0.0,  # free tier 1 cluster
    "cpu_pod_hour": 0.06,  # Autopilot-ish CPU pod
    "cpu_light_job_hour": 0.03,  # coordination / L3 light task
    "l4_gpu_hour": 0.70,
    "a100_gpu_hour": 3.90,
    "h100_gpu_hour": 12.00,  # order-of-magnitude; confirm Billing
    "l1_desk_power_hour": 0.08,  # local mainframe electricity EWMA floor
    "l4_saas_api_est_hour": 0.02,  # soft estimate when MCP active
    # LLM: fallback EUR/1M blend if provider module unavailable
    "llm_flagship_blend_eur_per_1m": 8.0,
    "llm_fast_blend_eur_per_1m": 0.7,
}

# Soft placement bases (relative, not EUR) — lower = preferred when free
PLACEMENT_BASE: Dict[str, float] = {
    "L0_edge": 0.05,
    "L1_mainframe": 0.15,
    "L2_mesh_anchor": 0.35,
    "L3_cluster": 1.00,
    "L4_external_saas": 0.25,
}

_HOURS_PER_MONTH = 730.0


@dataclass
class BurnBreakdown:
    l1_eur_h: float = 0.0
    l2_eur_h: float = 0.0
    l3_eur_h: float = 0.0
    l4_eur_h: float = 0.0
    fixed_month_eur: float = 0.0
    detail: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_eur_h(self) -> float:
        return self.l1_eur_h + self.l2_eur_h + self.l3_eur_h + self.l4_eur_h

    @property
    def total_eur_month(self) -> float:
        return self.fixed_month_eur + self.total_eur_h * _HOURS_PER_MONTH

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_eur_h"] = round(self.total_eur_h, 6)
        d["total_eur_month"] = round(self.total_eur_month, 2)
        return d


def compute_burn(
    *,
    gke_pods_running: int = 0,
    gke_pods_pending: int = 0,
    gpu_l4: int = 0,
    gpu_a100: int = 0,
    coordination_jobs_running: int = 0,
    mesh_exit_nodes: int = 1,
    gcs_gb: float = 10.0,
    l1_power_eur_h: Optional[float] = None,
    l4_saas_active: bool = False,
    llm_tokens_in_per_h: float = 0.0,
    llm_tokens_out_per_h: float = 0.0,
    llm_provider_id: str = "anthropic_claude_sonnet",
    rates: Optional[Dict[str, float]] = None,
) -> BurnBreakdown:
    """Aggregate real EUR/h burn across poly-mesh tiers.

    v2.1: C_L4 includes measured/estimated LLM token burn from public
    provider rates (provider_token_costs) when token throughput is known.
    """
    r = dict(RATES_EUR)
    if rates:
        r.update(rates)

    # refresh LLM blend defaults from live analysis when possible
    try:
        from fusion_hero_os.core.provider_token_costs import (
            blended_top_tier_eur_per_1m,
            estimate_llm_burn_eur_h,
        )

        r["llm_flagship_blend_eur_per_1m"] = blended_top_tier_eur_per_1m("flagship")
        r["llm_fast_blend_eur_per_1m"] = blended_top_tier_eur_per_1m("fast")
        llm_burn = estimate_llm_burn_eur_h(
            llm_tokens_in_per_h,
            llm_tokens_out_per_h,
            provider_id=llm_provider_id,
        )
        l4_llm = float(llm_burn.get("eur_h") or 0.0)
    except Exception:
        llm_burn = {}
        # fallback blend: treat tokens as 70/30 in/out at flagship median
        tok = float(llm_tokens_in_per_h) + float(llm_tokens_out_per_h)
        l4_llm = (tok / 1e6) * float(r.get("llm_flagship_blend_eur_per_1m", 8.0))

    l1 = float(l1_power_eur_h if l1_power_eur_h is not None else r["l1_desk_power_hour"])
    l2 = mesh_exit_nodes * r["gce_e2_micro_hour"]
    # second e2 if subnet router present — caller can pass mesh_exit_nodes=2
    l3 = (
        gke_pods_running * r["cpu_pod_hour"]
        + coordination_jobs_running * r["cpu_light_job_hour"]
        + gpu_l4 * r["l4_gpu_hour"]
        + gpu_a100 * r["a100_gpu_hour"]
    )
    l4_saas = r["l4_saas_api_est_hour"] if l4_saas_active else 0.0
    l4 = l4_saas + l4_llm
    fixed = (
        mesh_exit_nodes * r["gce_e2_micro_month"]
        + gcs_gb * r["gcs_storage_gb_month"]
        + r["gke_autopilot_mgmt_month"]
    )
    return BurnBreakdown(
        l1_eur_h=round(l1, 6),
        l2_eur_h=round(l2, 6),
        l3_eur_h=round(l3, 6),
        l4_eur_h=round(l4, 6),
        fixed_month_eur=round(fixed, 4),
        detail={
            "gke_pods_running": gke_pods_running,
            "gke_pods_pending": gke_pods_pending,
            "gpu_l4": gpu_l4,
            "gpu_a100": gpu_a100,
            "coordination_jobs_running": coordination_jobs_running,
            "mesh_exit_nodes": mesh_exit_nodes,
            "gcs_gb": gcs_gb,
            "l4_saas_eur_h": round(l4_saas, 6),
            "l4_llm_eur_h": round(l4_llm, 6),
            "llm_burn": llm_burn,
            "cost_function_version": COST_FUNCTION_VERSION,
            "rates": r,
            "formula": (
                "C_h = C_L1 + C_L2 + C_L3 + C_L4; "
                "C_L4 = saas_est + LLM(tokens, provider_rates); "
                "C_L3 = pods*cpu_h + coord*light_h + GPU; "
                "C_L2 = n_exit * e2_micro_h; C_month = fixed + C_h*730"
            ),
        },
    )


def compute_feu(
    eur_h: float,
    *,
    grid_eur_per_kwh: float = 0.35,
    pue: float = 1.25,
    feu_per_eur: float = 100.0,
) -> Dict[str, Any]:
    """Energy + FEU from EUR burn."""
    grid = max(grid_eur_per_kwh, 0.01)
    energy_kwh_h = (eur_h / grid) * pue if eur_h > 0 else 0.0
    feu_h = eur_h * feu_per_eur
    return {
        "eur_h": round(eur_h, 6),
        "energy_kwh_h": round(energy_kwh_h, 6),
        "feu_h": round(feu_h, 4),
        "grid_eur_per_kwh": grid,
        "pue": pue,
        "feu_per_eur": feu_per_eur,
        "formula": "E_h=(C_h/p_grid)*PUE; FEU_h=C_h*λ_FEU; 1 FEU≈0.01 EUR when λ=100",
    }


def resolve_margin(
    cost_per_1k: float,
    *,
    target_margin: float = 1.50,
    floor_margin: float = 0.35,
    ceiling_1k: Optional[float] = None,
    competitive: bool = True,
) -> Tuple[float, bool]:
    """Return (margin_pct, is_competitive)."""
    if not competitive or ceiling_1k is None:
        return target_margin, True
    if cost_per_1k * (1 + target_margin) <= ceiling_1k:
        return target_margin, True
    if cost_per_1k <= 0:
        return target_margin, True
    m_ceil = (ceiling_1k / cost_per_1k) - 1.0
    if m_ceil >= target_margin:
        return target_margin, True
    if m_ceil >= floor_margin:
        return round(m_ceil, 4), False
    return floor_margin, False


def tier_price(
    eur_h: float,
    tokens_per_hour_capacity: int,
    *,
    target_margin: float = 1.50,
    floor_margin: float = 0.35,
    ceiling_eur_per_1m: Optional[float] = None,
    min_price_1k: float = 0.002,
    competitive: bool = True,
) -> Dict[str, Any]:
    """P_1k from real hour burn and tier capacity."""
    cap = max(1, int(tokens_per_hour_capacity))
    cost_1k = (eur_h / cap) * 1000.0
    ceiling_1k = (ceiling_eur_per_1m / 1000.0) if ceiling_eur_per_1m is not None else None
    margin, is_comp = resolve_margin(
        cost_1k,
        target_margin=target_margin,
        floor_margin=floor_margin,
        ceiling_1k=ceiling_1k,
        competitive=competitive,
    )
    raw = cost_1k * (1 + margin)
    if ceiling_1k is not None:
        raw = min(raw, ceiling_1k)
    price_1k = max(min_price_1k, round(raw, 6))
    return {
        "real_cost_eur_per_1k_tokens": round(cost_1k, 6),
        "margin_pct": margin,
        "competitive": is_comp,
        "api_price_eur_per_1k_tokens": price_1k,
        "api_price_eur_per_1m_tokens": round(price_1k * 1000, 4),
        "market_ceiling_eur_per_1m_tokens": ceiling_eur_per_1m,
        "formula": "P_1k=max(P_min, min(c_1k*(1+m*), ceiling_1k)); c_1k=C_h/κ*1000",
    }


def placement_cost(
    tier: str,
    *,
    load: float = 0.0,
    online: bool = True,
    force_cluster: bool = False,
    gke_live: bool = False,
) -> Dict[str, Any]:
    """Soft placement cost Π for orchestration (hard constraints separate)."""
    base = PLACEMENT_BASE.get(tier, 1.0)
    if not online and tier != "L4_external_saas":
        return {
            "tier": tier,
            "pi": float("inf"),
            "online": False,
            "admissible": False,
            "reason": "tier_offline",
        }
    if force_cluster and tier != "L3_cluster":
        return {
            "tier": tier,
            "pi": float("inf"),
            "online": online,
            "admissible": False,
            "reason": "force_cluster_requires_L3",
        }
    if force_cluster and tier == "L3_cluster" and not gke_live:
        return {
            "tier": tier,
            "pi": float("inf"),
            "online": False,
            "admissible": False,
            "reason": "gke_offline",
        }
    pi = base * (1.0 + max(0.0, float(load)))
    return {
        "tier": tier,
        "pi": round(pi, 6),
        "base": base,
        "load": load,
        "online": online,
        "admissible": True,
        "formula": "Π=π_base*(1+load)  s.t. force_cluster→L3, control→L1",
    }


def evaluate_full(
    *,
    burn: Optional[BurnBreakdown] = None,
    gke: Optional[Dict[str, Any]] = None,
    energy_model: Optional[Dict[str, Any]] = None,
    pricing_cfg: Optional[Dict[str, Any]] = None,
    online_tiers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Full cost-function evaluation for API / orchestrator."""
    gke = gke or {}
    if burn is None:
        burn = compute_burn(
            gke_pods_running=int(gke.get("pods_running") or 0),
            gke_pods_pending=int(gke.get("pods_pending") or 0),
            gpu_l4=int(gke.get("gpu_l4") or 0),
            gpu_a100=int(gke.get("gpu_a100") or 0),
            coordination_jobs_running=int(gke.get("coordination_jobs_running") or 0),
            mesh_exit_nodes=int(gke.get("mesh_exit_nodes") or 1),
            gcs_gb=float(gke.get("gcs_gb") or 10),
        )
    em = energy_model or {}
    feu = compute_feu(
        burn.total_eur_h,
        grid_eur_per_kwh=float(em.get("grid_eur_per_kwh", 0.35)),
        pue=float(em.get("pue_cloud_factor", 1.25)),
        feu_per_eur=float(em.get("feu_per_eur_real", 100)),
    )
    sub = pricing_cfg or {}
    comp = dict(sub.get("competitive_pricing") or {})
    target = float(comp.get("margin_pct", sub.get("margin_pct", 1.50)))
    floor = float(sub.get("margin_pct_floor", 0.35))
    min_p = float(sub.get("minimum_price_eur_per_1k_tokens", 0.002))
    ceilings = dict(comp.get("market_ceiling_eur_per_1m_tokens") or {})
    # v2.1: overlay real top-provider market ceilings when not explicitly set
    try:
        from fusion_hero_os.core.provider_token_costs import market_ceilings_eur_per_1m

        for k, v in market_ceilings_eur_per_1m().items():
            ceilings.setdefault(k, v)
    except Exception:
        pass
    tiers_out = {}
    for tid, tier in (sub.get("tiers") or {
        "inference_standard": {"tokens_per_hour_capacity": 500000, "label": "Standard"},
        "poly_mesh_orchestration": {
            "tokens_per_hour_capacity": 200000,
            "label": "Poly-Mesh L3 Orchestration",
        },
    }).items():
        cap = int(tier.get("tokens_per_hour_capacity", 100000))
        ceil = ceilings.get(tid)
        price = tier_price(
            burn.total_eur_h,
            cap,
            target_margin=target,
            floor_margin=floor,
            ceiling_eur_per_1m=float(ceil) if ceil is not None else None,
            min_price_1k=min_p,
            competitive=bool(comp.get("enabled", True)),
        )
        tiers_out[tid] = {
            "label": tier.get("label", tid),
            "use_case": tier.get("use_case", ""),
            "tokens_per_hour_capacity": cap,
            **price,
            "feu_per_1k_tokens": round(
                price["api_price_eur_per_1k_tokens"] * float(em.get("feu_per_eur_real", 100)),
                4,
            ),
        }

    online = set(online_tiers or ["L1_mainframe"])
    gke_live = "L3_cluster" in online or bool(gke.get("live"))
    placement = {
        t: placement_cost(
            t,
            load=float((gke.get("load") or {}).get(t, 0)),
            online=(t in online) or t == "L4_external_saas",
            force_cluster=False,
            gke_live=gke_live,
        )
        for t in PLACEMENT_BASE
    }
    provider_analysis = None
    try:
        from fusion_hero_os.core.provider_token_costs import analyse_providers

        provider_analysis = analyse_providers()
    except Exception as exc:
        provider_analysis = {"ok": False, "error": str(exc)[:160]}

    return {
        "ok": True,
        "cost_function_version": COST_FUNCTION_VERSION,
        "ts": time.time(),
        "burn": burn.to_dict(),
        "feu": feu,
        "subcontractor_tiers": tiers_out,
        "placement_soft_costs": placement,
        "provider_token_costs": provider_analysis,
        "market_ceilings_eur_per_1m": ceilings,
        "formulas": {
            "C_h": "C_L1 + C_L2 + C_L3 + C_L4",
            "C_L4": "saas_est + LLM(tokens, provider_list_prices)",
            "E_h": "(C_h / p_grid) * PUE",
            "FEU_h": "C_h * λ_FEU",
            "P_1k": "max(P_min, min(c_1k*(1+m*), ceiling_1k))",
            "Pi_tier": "π_base*(1+load) s.t. force_cluster→L3, control→L1",
            "MCP_fill": "keep token_fill ∈ [0.40, 0.70]; compress by Sinnkongruenz",
        },
        "policy": {
            "real_cost_basis": "measured_or_rate_model",
            "mesh_aware": True,
            "force_cluster_hard": True,
            "competitive_margin_target": target,
            "provider_ceilings_overlay": True,
            "mcp_fill_band": [0.40, 0.70],
        },
    }


def cost_function_status() -> Dict[str, Any]:
    """Live status using cost daemon snapshot when available."""
    gke_info: Dict[str, Any] = {"mesh_exit_nodes": 1, "gcs_gb": 10.0}
    online: List[str] = ["L1_mainframe"]
    try:
        from fusion_hero_os.core.poly_mesh_os_port import inventory_mesh

        inv = inventory_mesh()
        online = list(inv.get("tiers_online") or online)
        # count L2 exits among peers
        exits = 0
        for p in inv.get("peers") or []:
            if p.get("online") and p.get("tier_hint") == "L2_mesh_anchor":
                exits += 1
        if (inv.get("self") or {}).get("tier_hint") == "L2_mesh_anchor":
            exits += 1
        gke_info["mesh_exit_nodes"] = max(1, exits) if exits else 1
        gke_info["live"] = "L3_cluster" in online
    except Exception:
        pass
    try:
        # prefer existing cost daemon breakdown if present
        snap_path = (
            Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
            / "mainframe_cost_analysis"
            / "snapshot.json"
        )
        if snap_path.is_file():
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            bd = (snap.get("breakdown") or {}).get("gke") or {}
            gke_info.update(
                {
                    "pods_running": bd.get("pods_running", 0),
                    "pods_pending": bd.get("pods_pending", 0),
                    "gpu_l4": bd.get("gpu_l4", 0),
                    "gpu_a100": bd.get("gpu_a100", 0),
                }
            )
    except Exception:
        pass
    # coordination jobs
    try:
        import subprocess

        kubectl = os.getenv("KUBECTL_PATH") or str(
            Path.home() / ".local" / "bin" / "kubectl.exe"
        )
        if not Path(kubectl).is_file():
            kubectl = "kubectl"
        r = subprocess.run(
            [kubectl, "get", "pods", "-n", "fusion-coordination", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if r.returncode == 0:
            items = (json.loads(r.stdout or "{}")).get("items") or []
            running = sum(
                1
                for p in items
                if (p.get("status") or {}).get("phase") == "Running"
            )
            gke_info["coordination_jobs_running"] = running
            gke_info["pods_running"] = int(gke_info.get("pods_running") or 0) + running
    except Exception:
        pass

    bp: Dict[str, Any] = {}
    try:
        import yaml

        bp_path = Path(
            os.getenv(
                "FUSION_BUSINESSPLAN_PATH",
                str(
                    Path(__file__).resolve().parents[2]
                    / "docs"
                    / "business"
                    / "senfkorn_businessplan.yaml"
                ),
            )
        )
        if bp_path.is_file():
            bp = yaml.safe_load(bp_path.read_text(encoding="utf-8")) or {}
    except Exception:
        pass

    return evaluate_full(
        gke=gke_info,
        energy_model=bp.get("energy_model"),
        pricing_cfg=bp.get("subcontractor_api_pricing"),
        online_tiers=online,
    )


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Poly-Mesh Cost Function v2")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.parse_args()  # validiert Flags/--help; Ausgabe ist ohnehin JSON-Status
    r = cost_function_status()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
