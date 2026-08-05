# -*- coding: utf-8 -*-
"""
Energiefunktion — Realkosten → FEU (Fusion Energy Units) → Subunternehmer API-Token-Preis.
Analog zu mainframe_cost_analysis_daemon; liest Kosten-Snapshots als Ground Truth.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_INTERVAL = float(os.getenv("FUSION_ENERGY_PRICING_INTERVAL_SEC", "60"))
_STATE = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os"))) / "mainframe_energy_pricing"
_BP_PATH = Path(os.getenv(
    "FUSION_BUSINESSPLAN_PATH",
    Path(__file__).resolve().parents[2] / "docs" / "business" / "senfkorn_businessplan.yaml",
))


def _state_dir() -> Path:
    p = _STATE
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_businessplan() -> Dict[str, Any]:
    if not _BP_PATH.exists():
        return {"ok": False, "error": f"missing: {_BP_PATH}"}
    try:
        data = yaml.safe_load(_BP_PATH.read_text(encoding="utf-8")) or {}
        data["ok"] = True
        data["path"] = str(_BP_PATH)
        return data
    except Exception as exc:
        return {"ok": False, "error": str(exc), "path": str(_BP_PATH)}


@dataclass
class EnergySnapshot:
    ts: float
    eur_hour_real: float
    eur_month_real: float
    energy_kwh_equivalent: float
    feu_total: float
    feu_per_hour: float
    subcontractor_pricing: Dict[str, Any] = field(default_factory=dict)
    businessplan_version: str = "1.0"
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MainframeEnergyPricingDaemon:
    def __init__(self) -> None:
        self._last: Optional[EnergySnapshot] = None
        self._history_path = _state_dir() / "history.jsonl"
        self._snapshot_path = _state_dir() / "snapshot.json"
        self._pricing_path = _state_dir() / "subcontractor_pricing.json"
        self._running = False
        self._ticks = 0

    def _load_cost_snapshot(self) -> Dict[str, Any]:
        cost_path = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os"))) / "mainframe_cost_analysis" / "snapshot.json"
        if cost_path.exists():
            try:
                return json.loads(cost_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        try:
            from core.mainframe_cost_analysis_daemon import get_cost_daemon
            snap = get_cost_daemon().tick()
            return snap.to_dict()
        except Exception:
            return {}

    def _resolve_tier_margin(
        self,
        cost_per_1k: float,
        tier_id: str,
        sub: Dict[str, Any],
    ) -> tuple[float, bool, Optional[float]]:
        """Return (margin_pct, competitive, market_ceiling_1k)."""
        comp = sub.get("competitive_pricing") or {}
        target = float(comp.get("margin_pct", sub.get("margin_pct", 1.50)))
        floor = float(sub.get("margin_pct_floor", 0.35))
        ceilings_1m = comp.get("market_ceiling_eur_per_1m_tokens") or {}
        ceiling_1m = ceilings_1m.get(tier_id)
        ceiling_1k = float(ceiling_1m) / 1000.0 if ceiling_1m is not None else None

        if not comp.get("enabled", True):
            return float(sub.get("margin_pct", target)), True, ceiling_1k

        price_target = cost_per_1k * (1 + target)
        if ceiling_1k is None or price_target <= ceiling_1k:
            return target, True, ceiling_1k

        if cost_per_1k <= 0:
            return target, True, ceiling_1k

        margin_at_ceiling = (ceiling_1k / cost_per_1k) - 1.0
        if margin_at_ceiling >= target:
            return target, True, ceiling_1k
        if margin_at_ceiling >= floor:
            return round(margin_at_ceiling, 4), False, ceiling_1k
        return floor, False, ceiling_1k

    def _compute_subcontractor_pricing(
        self,
        eur_hour: float,
        bp: Dict[str, Any],
    ) -> Dict[str, Any]:
        model = bp.get("energy_model", {})
        sub = bp.get("subcontractor_api_pricing", {})
        comp = dict(sub.get("competitive_pricing") or {})
        # Overlay real top-provider market ceilings (Bedingt list prices)
        try:
            from fusion_hero_os.core.provider_token_costs import (
                analyse_providers,
                market_ceilings_eur_per_1m,
            )

            market = market_ceilings_eur_per_1m()
            ceilings = dict(comp.get("market_ceiling_eur_per_1m_tokens") or {})
            for k, v in market.items():
                ceilings.setdefault(k, v)
            comp["market_ceiling_eur_per_1m_tokens"] = ceilings
            comp["provider_analysis_summary"] = {
                "flagship_median_eur_per_1m": analyse_providers().get(
                    "flagship_median_eur_per_1m"
                ),
                "fast_median_eur_per_1m": analyse_providers().get("fast_median_eur_per_1m"),
                "geltung": "Bedingt — public list prices",
            }
            # re-bind so _resolve_tier_margin sees ceilings via sub
            sub = dict(sub)
            sub["competitive_pricing"] = comp
        except Exception:
            pass
        target_margin = float(comp.get("margin_pct", sub.get("margin_pct", 1.50)))
        min_p1k = float(sub.get("minimum_price_eur_per_1k_tokens", 0.002))
        feu_per_eur = float(model.get("feu_per_eur_real", 100))

        tiers_out: Dict[str, Any] = {}
        competitive_count = 0
        for tier_id, tier in (sub.get("tiers") or {}).items():
            cap = max(1, int(tier.get("tokens_per_hour_capacity", 100000)))
            cost_per_token = eur_hour / cap
            cost_per_1k = cost_per_token * 1000
            margin, is_competitive, ceiling_1k = self._resolve_tier_margin(cost_per_1k, tier_id, sub)
            if is_competitive:
                competitive_count += 1
            raw_price = cost_per_1k * (1 + margin)
            if ceiling_1k is not None:
                raw_price = min(raw_price, ceiling_1k)
            price_per_1k = max(min_p1k, round(raw_price, 6))
            price_per_1m = round(price_per_1k * 1000, 4)
            feu_per_1k = round((price_per_1k / max(eur_hour, 1e-9)) * feu_per_eur * eur_hour / 1000, 4)
            tiers_out[tier_id] = {
                "label": tier.get("label", tier_id),
                "use_case": tier.get("use_case", ""),
                "tokens_per_hour_capacity": cap,
                "real_cost_eur_per_1k_tokens": round(cost_per_1k, 6),
                "api_price_eur_per_1k_tokens": price_per_1k,
                "api_price_eur_per_1m_tokens": price_per_1m,
                "feu_per_1k_tokens": feu_per_1k,
                "margin_pct": margin,
                "margin_pct_target": target_margin,
                "competitive": is_competitive,
                "market_ceiling_eur_per_1m_tokens": round(ceiling_1k * 1000, 4) if ceiling_1k else None,
                "currency": "EUR",
                "billing_unit": sub.get("billing_unit", "per_1000_tokens"),
            }

        default_tier = tiers_out.get("inference_standard") or next(iter(tiers_out.values()), {})
        all_competitive = competitive_count == len(tiers_out) and len(tiers_out) > 0
        return {
            "company": bp.get("company", {}).get("name", "Senfkorn UG"),
            "margin_pct": target_margin,
            "margin_pct_applied_mode": "competitive_150" if all_competitive else "mixed",
            "competitive_pricing_enabled": bool(comp.get("enabled", True)),
            "competitive_tiers": competitive_count,
            "eur_hour_basis": round(eur_hour, 6),
            "default_tier": "inference_standard",
            "headline_price_eur_per_1k_tokens": default_tier.get("api_price_eur_per_1k_tokens"),
            "headline_price_eur_per_1m_tokens": default_tier.get("api_price_eur_per_1m_tokens"),
            "tiers": tiers_out,
            "formula": (
                "P_1k=max(P_min,min(c_1k*(1+m*),ceiling_1k)); "
                "c_1k=C_h/κ*1000; C_h=C_L1+C_L2+C_L3+C_L4; "
                "m*=150% competitive else floor 35% under market ceiling"
            ),
            "cost_function_version": str(bp.get("cost_function_version", "2.0.0")),
            "anchored_in": str(_BP_PATH),
        }

    def tick(self) -> EnergySnapshot:
        bp = load_businessplan()
        cost = self._load_cost_snapshot()
        eur_hour = float(cost.get("total_eur_hour_burn", 0))
        eur_month = float(cost.get("total_eur_month_est", 0))

        em = bp.get("energy_model", {}) if bp.get("ok") else {}
        grid = float(em.get("grid_eur_per_kwh", 0.35))
        pue = float(em.get("pue_cloud_factor", 1.25))
        feu_per_eur = float(em.get("feu_per_eur_real", 100))

        energy_kwh = (eur_hour / max(grid, 0.01)) * pue if eur_hour > 0 else 0
        feu_hour = eur_hour * feu_per_eur
        feu_month = eur_month * feu_per_eur

        subcontractor = self._compute_subcontractor_pricing(eur_hour, bp if bp.get("ok") else {
            "energy_model": em,
            "subcontractor_api_pricing": {
                "margin_pct": 1.50,
                "margin_pct_floor": 0.35,
                "competitive_pricing": {"enabled": True, "margin_pct": 1.50},
                "minimum_price_eur_per_1k_tokens": 0.002,
                "tiers": {"inference_standard": {"label": "Standard", "tokens_per_hour_capacity": 500000}},
            },
            "company": {"name": "Senfkorn UG"},
        })

        alerts: List[str] = []
        if eur_hour > 10:
            alerts.append(f"Hohe Energielast: {energy_kwh:.2f} kWh-Äq/h")
        ceiling = float((bp.get("financial_targets") or {}).get("monthly_infra_ceiling_eur", 150))
        if eur_month > ceiling:
            alerts.append(f"Monatskosten über Businessplan-Ceiling ({ceiling} EUR)")

        snap = EnergySnapshot(
            ts=time.time(),
            eur_hour_real=round(eur_hour, 6),
            eur_month_real=round(eur_month, 2),
            energy_kwh_equivalent=round(energy_kwh, 4),
            feu_total=round(feu_month, 2),
            feu_per_hour=round(feu_hour, 2),
            subcontractor_pricing=subcontractor,
            businessplan_version=str(bp.get("businessplan_version", "1.0")),
            alerts=alerts,
        )
        self._last = snap
        self._ticks += 1
        payload = snap.to_dict()
        self._snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._pricing_path.write_text(
            json.dumps(subcontractor, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        with self._history_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return snap

    def status(self) -> Dict[str, Any]:
        hist: List[Dict[str, Any]] = []
        if self._history_path.exists():
            try:
                for line in self._history_path.read_text(encoding="utf-8").strip().splitlines()[-120:]:
                    hist.append(json.loads(line))
            except Exception:
                pass
        return {
            "daemon": "mainframe_energy_pricing",
            "running": self._running,
            "ticks": self._ticks,
            "interval_sec": _INTERVAL,
            "snapshot": self._last.to_dict() if self._last else None,
            "subcontractor_pricing": self._last.subcontractor_pricing if self._last else None,
            "businessplan": load_businessplan(),
            "history_points": len(hist),
            "history": hist[-60:],
        }

    def subcontractor_quote(self, tier: str = "inference_standard", tokens: int = 1000) -> Dict[str, Any]:
        if not self._last:
            self.tick()
        pricing = (self._last.subcontractor_pricing if self._last else {}).get("tiers", {})
        t = pricing.get(tier)
        if not t:
            return {"ok": False, "error": f"unknown tier: {tier}", "available": list(pricing.keys())}
        units_1k = max(1, tokens // 1000)
        price = round(t["api_price_eur_per_1k_tokens"] * units_1k, 4)
        eur_h = self._last.eur_hour_real if self._last else 0.0
        feu_equiv = round(price * float((self._last.subcontractor_pricing or {}).get("tiers", {}).get(tier, {}).get("feu_per_1k_tokens", 0) or 0) / max(t["api_price_eur_per_1k_tokens"], 1e-9), 2) if self._last else 0.0
        if eur_h <= 0:
            feu_equiv = round(price * 100, 2)  # 1 FEU ≈ 0.01 EUR bei Idle-Basis
        return {
            "ok": True,
            "tier": tier,
            "tokens": tokens,
            "price_eur": price,
            "price_per_1k": t["api_price_eur_per_1k_tokens"],
            "real_cost_basis_eur_hour": eur_h,
            "feu_equivalent": feu_equiv,
            "company": "Senfkorn UG",
            "valid_at": self._last.ts if self._last else time.time(),
        }

    def start_background(self) -> bool:
        if self._running:
            return False
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False


_daemon: Optional[MainframeEnergyPricingDaemon] = None


def get_energy_daemon() -> MainframeEnergyPricingDaemon:
    global _daemon
    if _daemon is None:
        _daemon = MainframeEnergyPricingDaemon()
    return _daemon