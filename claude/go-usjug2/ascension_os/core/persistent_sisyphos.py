# -*- coding: utf-8 -*-
"""
AscensionOS v9.4 - Persistent Stateful Sisyphos-Zyklus

Coevolutionär aufgebaut:
- Erweitert den bestehenden SisyphosCycle um Persistence + Historie
- Integriert mit CoEvolutionaryClosure (CEC)
- Nutzbar durch GenerationalEvolutionEngine
- Langzeitfähig (History + Save/Load)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from fusion_hero_os.core.universal_llm_router import SisyphosCycle
except Exception:
    SisyphosCycle = None

try:
    from .coevolutionary_closure import get_coevolutionary_closure
except Exception:
    get_coevolutionary_closure = None


@dataclass
class SisyphosCycleState:
    """Repräsentiert einen einzelnen Zustand im Sisyphos-Zyklus."""
    cycle_number: int
    load: float
    satisfaction: float
    timestamp: str
    notes: str = ""


class PersistentSisyphosCycle:
    """
    Persistent und stateful Version des Sisyphos-Zyklus.

    Features:
    - Volle Historie aller Zyklen
    - Save/Load (JSON)
    - Automatische Benachrichtigung an CoEvolutionaryClosure
    - Kompatibel mit bestehendem SisyphosCycle
    """

    def __init__(self, persistence_path: str = "data/sisyphos_history.json", 
                 max_history: int = 1000):
        self.persistence_path = Path(persistence_path)
        self.max_history = max_history
        self.history: List[SisyphosCycleState] = []
        self.current_load: float = 0.0
        self.current_satisfaction: float = 0.5
        self.cycle_count: int = 0

        # Lade existierende Historie falls vorhanden
        self._load_from_disk()

        # Optional: Verbindung zum CoEvolutionaryClosure
        self.cec = get_coevolutionary_closure() if get_coevolutionary_closure else None

    def step(self, new_load: float, notes: str = "") -> Dict[str, Any]:
        """Führt einen neuen Schritt im Sisyphos-Zyklus aus und persistiert ihn."""
        self.current_load = max(0.0, min(1.0, new_load))
        self.current_satisfaction = max(0.0, 1.0 - self.current_load * 0.7)
        self.cycle_count += 1

        state = SisyphosCycleState(
            cycle_number=self.cycle_count,
            load=self.current_load,
            satisfaction=self.current_satisfaction,
            timestamp=datetime.now().isoformat(),
            notes=notes
        )

        self.history.append(state)

        # Begrenze Historie
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Persistieren
        self._save_to_disk()

        # Coevolutionäre Benachrichtigung
        if self.cec:
            self.cec.notify_change(
                source="PersistentSisyphosCycle",
                change_type="cycle_step",
                payload={
                    "cycle_number": self.cycle_count,
                    "load": self.current_load,
                    "satisfaction": self.current_satisfaction
                }
            )

        return self.get_current_state()

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "cycle_count": self.cycle_count,
            "load": self.current_load,
            "satisfaction": self.current_satisfaction,
            "is_sustainable": self.current_satisfaction > 0.4 and self.current_load < 0.85,
            "total_cycles_recorded": len(self.history),
        }

    def get_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        if last_n is None:
            return [asdict(s) for s in self.history]
        return [asdict(s) for s in self.history[-last_n:]]

    def _save_to_disk(self):
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "current_load": self.current_load,
                "current_satisfaction": self.current_satisfaction,
                "cycle_count": self.cycle_count,
                "history": [asdict(s) for s in self.history],
            }
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Sisyphos] Failed to save history: {e}")

    def _load_from_disk(self):
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.current_load = data.get("current_load", 0.0)
            self.current_satisfaction = data.get("current_satisfaction", 0.5)
            self.cycle_count = data.get("cycle_count", 0)

            for item in data.get("history", []):
                self.history.append(SisyphosCycleState(**item))

        except Exception as e:
            print(f"[Sisyphos] Failed to load history: {e}")

    def get_sustainability_trend(self, window: int = 20) -> Dict[str, Any]:
        if len(self.history) < 2:
            return {"trend": "insufficient_data"}

        recent = self.history[-window:]
        avg_satisfaction = sum(s.satisfaction for s in recent) / len(recent)
        avg_load = sum(s.load for s in recent) / len(recent)

        return {
            "avg_satisfaction": round(avg_satisfaction, 3),
            "avg_load": round(avg_load, 3),
            "is_currently_sustainable": self.get_current_state()["is_sustainable"],
        }
