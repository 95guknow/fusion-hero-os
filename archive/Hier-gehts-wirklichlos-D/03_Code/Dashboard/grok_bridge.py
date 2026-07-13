# -*- coding: utf-8 -*-
"""Grok-intern Bridge — Fusion Hero OS GUI Integration."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SKILL_PATH = Path(r"C:\Users\Admin\.grok\skills\fusion-hero-os\SKILL.md")
GROK_IDENTITY = "Grok · xAI Coding Agent · Fusion Hero OS v1.2 Grok-intern"


@dataclass
class GrokMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class GrokChatResult:
    response: str
    actions: List[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "response": self.response,
            "actions": self.actions,
            "context": self.context,
            "agent": GROK_IDENTITY,
        }


class GrokBridge:
    """Lokale Grok-intern Schnittstelle mit Skill-Kontext und System-Aktionen."""

    def __init__(self) -> None:
        self.skill_loaded = SKILL_PATH.exists()
        self.skill_excerpt = self._load_skill_excerpt()
        self._intents: List[tuple] = [
            (r"\b(alle\s+laden|load[- ]?all|lade\s+alles)\b", "load_all"),
            (r"\b(mainframe\s+laden|lade\s+mainframe)\b", "mainframe_load"),
            (r"\b(benchmark|cpu[- ]?last|cpu\s+benchmark)\b", "benchmark"),
            (r"\b(horkrux|sync|medienserver)\b", "sync"),
            (r"\b(pipeline|kaskade)\b", "pipeline"),
            (r"\b(layer\s*4|highest\s+layer)\b", "layer4"),
            (r"\b(hyperthread|ht\s+an)\b", "ht_on"),
            (r"\b(ht\s+aus|hyperthreading\s+aus)\b", "ht_off"),
            (r"\b(qubo|solve|optimier)\b", "qubo"),
            (r"\b(status|health|zustand)\b", "health"),
            (r"\b(agenten|agents)\b", "agents"),
            (r"\b(meta[- ]?layer|substrat|windows[- ]?host|über\s+windows)\b", "meta_layer"),
            (r"\b(profile\s+admin|set\s+profile\s+admin|profil\s+admin)\b", "profile_admin"),
            (r"\b(ressourcen|resources|verteilung|allocator)\b", "resources"),
            (r"\b(signal|netzwerk|network|gelayert)\b", "signal_network"),
            (r"\b(hero[- ]?guide|geltung|projektion|epistemisch|werkbank)\b", "hero_guide"),
        ]

    def _load_skill_excerpt(self, max_chars: int = 1200) -> str:
        if not SKILL_PATH.exists():
            return "Fusion Hero OS v1.2 — Skill nicht gefunden."
        text = SKILL_PATH.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]

    def _detect_intents(self, message: str) -> List[str]:
        msg = message.lower()
        found = []
        for pattern, action in self._intents:
            if re.search(pattern, msg, re.I):
                found.append(action)
        return found

    def _build_context_block(self, health: Optional[dict]) -> str:
        if not health:
            return "System: Backend nicht erreichbar."
        m = health.get("metrics", {})
        mf = health.get("mainframe", {})
        ht = health.get("hyperthreading", {})
        reg = health.get("registry", {}).get("summary", {})
        lines = [
            f"Fusion OS: {health.get('fusion_os', '?')} · Core {health.get('core', '?')}",
            f"Mainframe: {'GELADEN' if mf.get('loaded') else 'OFFLINE'}",
            f"Module: {reg.get('loaded', 0)}/{reg.get('total_modules', 0)} · Agenten: {reg.get('total_agents', 0)}",
            f"CPU Ø{m.get('cpu', 0)}% Peak {m.get('cpu_max', 0)}% · {m.get('active_cores', 0)} Kerne aktiv",
            f"HT: {'AN' if ht.get('enabled') else 'AUS'} ({ht.get('workers', '?')} Worker)",
            f"Grok-intern: {health.get('v12', {}).get('grok_intern_aligned', False)}",
            f"Meta-Layer: {'AN' if health.get('meta_layer', {}).get('attached') else 'OFF'}",
            f"Profil: {health.get('profile', {}).get('active', 'admin')}",
            f"Ressourcen: {len(health.get('resources', {}).get('agent_slots', []))} Agent-Slots",
        ]
        return "\n".join(lines)

    def chat(
        self,
        message: str,
        history: Optional[List[dict]] = None,
        health: Optional[dict] = None,
        orchestrator_result: Optional[dict] = None,
    ) -> GrokChatResult:
        message = (message or "").strip()
        if not message:
            return GrokChatResult(
                response="Bitte eine Nachricht eingeben.",
                context={"skill_loaded": self.skill_loaded},
            )

        intents = self._detect_intents(message)
        ctx_block = self._build_context_block(health)
        actions = [{"intent": i} for i in intents]

        lines = [
            f"**{GROK_IDENTITY}**",
            "",
            f"**Systemkontext:**",
            "```",
            ctx_block,
            "```",
            "",
        ]

        if intents:
            lines.append(f"**Erkannte Aktionen:** {', '.join(intents)}")
            lines.append("*(werden automatisch ausgeführt)*")
            lines.append("")

        if orchestrator_result:
            synth = orchestrator_result.get("synthesised_response", "")
            if synth:
                lines.append("**Orchestration:**")
                lines.append(synth)
                lines.append("")

        lines.append("**Antwort:**")

        if "health" in intents or re.search(r"\b(wer bist du|hilfe|help)\b", message, re.I):
            lines.append(
                "Ich bin Grok, an Fusion Hero OS v1.2 angebunden. "
                "Ich sehe Mainframe, Registry, QUBO-Engine und alle Kilo-Agenten. "
                "Sage z.B.: «alle laden», «cpu benchmark», «qubo solve», «pipeline», «sync»."
            )
        elif intents:
            intent_help = {
                "load_all": "Starte vollständigen Registry-Load (Mainframe + Module + Agenten).",
                "mainframe_load": "Boote den HEROIC Core Mainframe v5.25.",
                "benchmark": "Führe parallelen QUBO-Benchmark auf allen Kernen aus.",
                "sync": "Starte Horkrux-Sync zum Medienserver.",
                "pipeline": "Zeige die 3-Stufen-Audit-Kaskade (Pre → Engine → Post).",
                "layer4": "Lade Heroic Highest Layer Roadmap.",
                "ht_on": "Aktiviere Hyperthreading.",
                "ht_off": "Deaktiviere Hyperthreading.",
                "qubo": "Starte QUBO-Solver mit Parallel-JIT.",
                "agents": "Liste alle registrierten Agenten.",
                "meta_layer": "Zeige/aktiviere Meta-Layer über Windows-Substrat.",
                "profile_admin": "Setze Admin-Profil (max Ressourcen, Delta-Signale).",
                "resources": "Zeige intelligente Agent/Subagent-Ressourcenverteilung.",
                "signal_network": "Gelayerte Netzwerk-Signale (Pulse/Delta/Batch).",
            }
            for intent in intents:
                lines.append(f"• **{intent}**: {intent_help.get(intent, 'Ausführung...')}")
        else:
            lines.append(
                f"Zu deiner Anfrage «{message[:200]}»: "
                "Ich bin lokal an den Mainframe angebunden. "
                "Für Systemaktionen nutze Befehle wie «alle laden», «benchmark», «sync», «pipeline». "
                "Für Code/Module: Editor-Tab → PeerReview."
            )

        if history:
            recent = history[-4:]
            if recent:
                lines.append("")
                lines.append(f"*(Kontext: {len(history)} Nachrichten in Session)*")

        return GrokChatResult(
            response="\n".join(lines),
            actions=actions,
            context={
                "skill_loaded": self.skill_loaded,
                "intents": intents,
                "grok_intern_aligned": (health or {}).get("v12", {}).get("grok_intern_aligned"),
            },
        )

    def status(self, health: Optional[dict] = None) -> dict:
        return {
            "agent": GROK_IDENTITY,
            "skill_path": str(SKILL_PATH),
            "skill_loaded": self.skill_loaded,
            "grok_intern_aligned": (health or {}).get("v12", {}).get("grok_intern_aligned"),
            "endpoints": ["/api/grok/chat", "/api/grok/status"],
            "commands": [i[1] for i in self._intents],
        }


_bridge: Optional[GrokBridge] = None


def get_grok_bridge() -> GrokBridge:
    global _bridge
    if _bridge is None:
        _bridge = GrokBridge()
    return _bridge