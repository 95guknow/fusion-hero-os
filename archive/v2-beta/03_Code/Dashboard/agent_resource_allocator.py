# -*- coding: utf-8 -*-
"""Intelligente Agent/Subagent-Ressourcenverteilung — profil- und lastbasiert."""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from fusion_profile import get_profile_config
from hyperthreading_config import logical_cpu_count, parallel_workers


TIER_WEIGHTS = {
    "model": 1.0,
    "primary": 0.85,
    "agent": 0.85,
    "subagent": 0.35,
    "specialist": 0.55,
}


@dataclass
class AgentSlot:
    agent_id: str
    mode: str
    tier: str
    weight: float
    workers: int
    priority: int
    concurrent: int
    backend: str = "llama-local"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResourcePlan:
    profile: str
    total_workers: int
    cpu_pressure: float
    ram_pressure: float
    model_pool: List[str] = field(default_factory=list)
    trinity_pool: List[str] = field(default_factory=list)
    agent_slots: List[AgentSlot] = field(default_factory=list)
    orchestrator_workers: int = 1
    qubo_workers: int = 1
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "total_workers": self.total_workers,
            "cpu_pressure": round(self.cpu_pressure, 3),
            "ram_pressure": round(self.ram_pressure, 3),
            "model_pool": self.model_pool,
            "trinity_pool": self.trinity_pool,
            "agent_slots": [s.to_dict() for s in self.agent_slots],
            "orchestrator_workers": self.orchestrator_workers,
            "qubo_workers": self.qubo_workers,
            "notes": self.notes,
        }


def _tier_for_mode(mode: str) -> str:
    m = (mode or "subagent").lower()
    if m in ("primary", "agent"):
        return "primary"
    if m == "subagent":
        return "subagent"
    return "specialist"


def _system_pressure() -> tuple[float, float]:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None) / 100.0
        ram = psutil.virtual_memory().percent / 100.0
        return min(max(cpu, 0.0), 1.0), min(max(ram, 0.0), 1.0)
    except Exception:
        return 0.0, 0.0


def build_resource_plan(
    agents: List[dict],
    metrics: Optional[dict] = None,
    profile_name: Optional[str] = None,
) -> ResourcePlan:
    """Verteilt Worker-Slots intelligent zwischen Modellen, Agenten, Subagenten."""
    profile = get_profile_config(profile_name)
    pname = profile["id"]
    base_workers = parallel_workers()
    cap = max(1, int(base_workers * profile.get("worker_cap_ratio", 1.0)))
    reserve = int(profile.get("reserve_workers", 1))
    usable = max(1, cap - reserve)

    cpu_p, ram_p = _system_pressure()
    if metrics:
        cpu_p = max(cpu_p, (metrics.get("cpu", 0) or 0) / 100.0)
        ram_p = max(ram_p, (metrics.get("ram", 0) or 0) / 100.0)
    pressure = max(cpu_p, ram_p)
    if pressure > 0.85:
        usable = max(1, usable // 2)
    elif pressure > 0.65:
        usable = max(1, int(usable * 0.75))

    model_share = profile.get("model_share", 0.1)
    agent_share = profile.get("agent_share", 0.5)
    sub_share = profile.get("subagent_share", 0.25)

    model_workers = max(1, int(usable * model_share))
    agent_budget = max(1, int(usable * agent_share))
    sub_budget = max(0, int(usable * sub_share))

    primaries = [a for a in agents if _tier_for_mode(a.get("mode", "")) == "primary"]
    subagents = [a for a in agents if _tier_for_mode(a.get("mode", "")) == "subagent"]
    specialists = [a for a in agents if _tier_for_mode(a.get("mode", "")) == "specialist"]

    max_p = int(profile.get("max_parallel_agents", 4))
    max_s = int(profile.get("max_parallel_subagents", 2))

    model_pool = ["llama-local", "grok", "claude", "gpt"]
    if pname == "admin":
        model_pool += [a["id"] for a in primaries[:max_p]]
    elif pname == "balanced":
        model_pool += [a["id"] for a in primaries[: max_p // 2]]
    else:
        model_pool = ["llama-local", "grok"] + [a["id"] for a in primaries[:1]]

    slots: List[AgentSlot] = []

    def _distribute(group: List[dict], budget: int, tier: str, max_n: int) -> int:
        if not group or budget <= 0:
            return budget
        selected = group[:max_n]
        total_w = sum(TIER_WEIGHTS.get(tier, 0.5) for _ in selected) or 1.0
        used = 0
        for i, ag in enumerate(selected):
            w = TIER_WEIGHTS.get(tier, 0.5)
            share = max(1, int(budget * (w / total_w)))
            if i == len(selected) - 1:
                share = max(1, budget - used)
            used += share
            backend = "grok-intern" if str(ag.get("id", "")).startswith("anti-") else "llama-local"
            slots.append(AgentSlot(
                agent_id=ag["id"],
                mode=ag.get("mode", tier),
                tier=tier,
                weight=w,
                workers=share,
                priority=profile.get("priority", 50) - i,
                concurrent=min(share, 2 if tier == "primary" else 1),
                backend=backend,
            ))
        return max(0, budget - used)

    rem = _distribute(primaries, agent_budget, "primary", max_p)
    _distribute(subagents, sub_budget + rem, "subagent", max_s)
    if specialists and pname == "admin":
        _distribute(specialists, max(1, usable // 6), "specialist", 2)

    notes = [
        f"Profil {pname}: {usable} nutzbare Worker (Reserve {reserve})",
        f"Druck CPU={cpu_p:.0%} RAM={ram_p:.0%}",
        f"Primary={len(primaries)} Subagent={len(subagents)}",
    ]

    try:
        from model_connectors import filter_llm_pool
        trinity = filter_llm_pool(model_pool)
    except Exception:
        trinity = [m for m in model_pool if m in ("grok", "claude", "gpt")][:3] or ["grok"]

    return ResourcePlan(
        profile=pname,
        total_workers=cap,
        cpu_pressure=cpu_p,
        ram_pressure=ram_p,
        model_pool=model_pool,
        trinity_pool=trinity,
        agent_slots=slots,
        orchestrator_workers=min(model_workers, len(model_pool)),
        qubo_workers=max(1, usable - model_workers),
        notes=notes,
    )


_last_plan: Optional[ResourcePlan] = None
_last_plan_ts: float = 0.0
_PLAN_TTL = 5.0


def get_resource_plan(
    agents: List[dict],
    metrics: Optional[dict] = None,
    force: bool = False,
) -> ResourcePlan:
    global _last_plan, _last_plan_ts
    now = time.time()
    if not force and _last_plan and (now - _last_plan_ts) < _PLAN_TTL:
        return _last_plan
    _last_plan = build_resource_plan(agents, metrics=metrics)
    _last_plan_ts = now
    return _last_plan


def pick_agent_pool(agent_id: str, agents: List[dict], metrics: Optional[dict] = None) -> List[str]:
    plan = get_resource_plan(agents, metrics=metrics)
    slot = next((s for s in plan.agent_slots if s.agent_id == agent_id), None)
    pool = ["grok", agent_id]
    if slot and slot.tier == "primary" and plan.profile == "admin":
        pool.insert(1, "claude")
    return pool[: max(2, (slot.workers if slot else 2))]