"""Fusion Hero OS — v12.1.0 (operativer Kanon; v8.3-Funktionskern + Stage-A/B + daycycle).

Namespace-Paket für die aktiven Kernkomponenten des Projekts:

- ``fusion_hero_os.core``           — mathematischer Kern + Orchestrator
- ``fusion_hero_os.engine``         — QUBO-Solver / Simulated-Annealing
- ``fusion_hero_os.orchestration``  — Multi-Agenten-System
- ``fusion_hero_os.methodology``    — externe Service-Connectoren (Dry-Run default)
- ``fusion_hero_os.modules``        — Skill-Module (teils noch Platzhalter, siehe registry)

Alle Teilsysteme werden zentral über :mod:`fusion_hero_os.registry` initialisiert
und abgefragt, statt einzeln und lose per Direktimport verdrahtet zu werden.
"""

__version__ = "12.1.0"

__all__ = ["__version__"]
