# -*- coding: utf-8 -*-
"""
AscensionOS v9.3 - CoEvolutionaryClosure (CEC)

Zentrales coevolutionäres Fundament.

Enthält:
- CoEvolutionaryClosure als Container für coevolutionäre Beziehungen
- Active MasterSeed Strict Contraction Enforcement (runtime)
- Hyperthreading Runtime Management (parallele Tracks)

Dieses Modul ist der coevolutionäre Kern, auf dem später
Persistent Sisyphos, HorkruxSelfUpdate, Self-Modification Governance etc.
 aufbauen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime


@dataclass
class Track:
    """Repräsentiert einen Hyperthreading-Track."""
    name: str
    mode: str = "heroic"          # heroic | ascension | experimental
    active: bool = True
    last_update: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class MasterSeedContractionEnforcer:
    """
    Aktive Strict Contraction Enforcement für den MasterSeed.

    Im Gegensatz zur reinen Verifikation kann dieser Enforcer
    bei Verletzung Maßnahmen ergreifen (Warnung, Degradation, Phoenix etc.).
    """

    def __init__(self, strictness: float = 0.95):
        self.strictness = strictness
        self.violation_count = 0
        self.last_violation: Optional[Dict[str, Any]] = None

    def enforce(self, current_hash: str, expected_hash: str, context: str = "") -> bool:
        """
        Prüft aktiv die Contraction und reagiert bei Verletzung.
        """
        if current_hash.strip().lower() != expected_hash.strip().lower():
            self.violation_count += 1
            self.last_violation = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "expected": expected_hash,
                "actual": current_hash,
            }
            # Hier können später echte Maßnahmen kommen (z.B. Phoenix triggern)
            print(f"[CONTRACTION ENFORCER] Violation detected in {context}")
            return False
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "violation_count": self.violation_count,
            "last_violation": self.last_violation,
            "strictness": self.strictness,
        }


class CoEvolutionaryClosure:
    """
    Zentrale CoEvolutionaryClosure (CEC).

    Diese Klasse verwaltet coevolutionäre Beziehungen zwischen Komponenten
    und stellt sicher, dass Änderungen in einem Teil des Systems
    kontrolliert auf andere Teile wirken können.
    """

    def __init__(self):
        self.tracks: Dict[str, Track] = {}
        self.contraction_enforcer = MasterSeedContractionEnforcer()
        self.registered_components: Dict[str, Any] = {}
        self.coevolution_rules: List[Callable] = []
        self.history: List[Dict[str, Any]] = []

    def create_track(self, name: str, mode: str = "heroic") -> Track:
        if name in self.tracks:
            return self.tracks[name]
        track = Track(name=name, mode=mode)
        self.tracks[name] = track
        return track

    def get_track(self, name: str) -> Optional[Track]:
        return self.tracks.get(name)

    def register_component(self, name: str, component: Any, track: str = "main"):
        self.registered_components[name] = {
            "component": component,
            "track": track,
            "registered_at": datetime.now().isoformat(),
        }
        if track not in self.tracks:
            self.create_track(track)

    def enforce_masterseed_contraction(self, current_hash: str, expected_hash: str, context: str = "") -> bool:
        return self.contraction_enforcer.enforce(current_hash, expected_hash, context)

    def add_coevolution_rule(self, rule: Callable[[Dict[str, Any]], None]):
        """Fügt eine Regel hinzu, die bei relevanten Änderungen ausgeführt wird."""
        self.coevolution_rules.append(rule)

    def notify_change(self, source: str, change_type: str, payload: Dict[str, Any]):
        """Informiert das System über eine Änderung (Coevolution)."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": change_type,
            "payload": payload,
        }
        self.history.append(event)

        # Führe coevolutionäre Regeln aus
        for rule in self.coevolution_rules:
            try:
                rule(event)
            except Exception as e:
                print(f"[CEC] Rule execution failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_tracks": list(self.tracks.keys()),
            "registered_components": list(self.registered_components.keys()),
            "contraction_status": self.contraction_enforcer.get_status(),
            "total_events": len(self.history),
        }


# Singleton
_cec_instance: Optional[CoEvolutionaryClosure] = None

def get_coevolutionary_closure() -> CoEvolutionaryClosure:
    global _cec_instance
    if _cec_instance is None:
        _cec_instance = CoEvolutionaryClosure()
    return _cec_instance
