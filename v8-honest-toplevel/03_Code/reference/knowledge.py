# -*- coding: utf-8 -*-
"""
PROJEKT-WISSENSBASIS (knowledge.py)
===================================
Strukturiertes, importierbares Projektwissen für "Fusion Hero OS" /
"ALTE_FRAU_95g Core". Dieses Modul kodiert die etablierten Architektur-,
Entscheidungs- und Umgebungs-Fakten als *Daten* (keine Prosa), damit andere
Werkzeuge sie programmatisch abfragen können.

Verwendung:
    from knowledge import KNOWLEDGE, get_decision, list_modules, as_markdown
    print(get_decision("visualization").rationale)
    print(as_markdown())

Eigenschaften (HARTE CONSTRAINTS):
  * Import-sicher: keine Top-Level-Seiteneffekte, keine Netzwerkaufrufe,
    kein ui.run(). Die Demo läuft ausschließlich unter __main__.
  * Reine Daten + reine Funktionen. Keine externen Pflicht-Abhängigkeiten.
  * Läuft unter Python 3.10 auf Windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

__version__ = "1.0"


# =====================================================================
# DATENTYPEN
# =====================================================================

@dataclass(frozen=True)
class Module:
    """Ein konzeptionelles oder ausführbares Modul innerhalb einer Datei."""
    name: str
    role: str
    file: str
    details: str = ""


@dataclass(frozen=True)
class Decision:
    """Eine etablierte technische Entscheidung samt Kurz-Begründung."""
    key: str
    choice: str
    rationale: str
    alternatives_rejected: str = ""


@dataclass(frozen=True)
class Repo:
    """Ein GitHub-Repository des Projekt-Accounts."""
    name: str
    description: str


@dataclass(frozen=True)
class FileVersion:
    """Versionsstand einer zentralen Projektdatei."""
    file: str
    version: str
    role: str


# =====================================================================
# ARCHITEKTUR — Module in mainframe.py (v5.25)
# =====================================================================

_MAINFRAME = "mainframe.py"
_APP = "app.py"
_SKILL = "HEROIC_SKILL.md"

MAINFRAME_MODULES: List[Module] = [
    Module(
        "SelfModifyCoreModule",
        "PLATZHALTER-STUB: Audit-Hook-Registry (registrieren/ausloesen) und "
        "Vorschlags-Liste. Kein echtes Selbst-Modifikationssystem zur Laufzeit.",
        _MAINFRAME,
        "Hook-Registry (Stub).",
    ),
    Module(
        "GenerationalEvolutionProtocolCoreModule",
        "Echte (mu+lambda)-Evolution ueber SA-Solver-Konfigurationen "
        "(Genom=(steps,T0,n_restarts), Fitness=-energy via parallel_anneal); "
        "elitaer, beste Fitness monoton nicht-fallend.",
        _MAINFRAME,
        "(mu+lambda)-Evolution; Methoden run_generation()/evolve().",
    ),
    Module(
        "CriticalMetaAnalysisCoreModule",
        "PLATZHALTER-STUB: grobe Substring-Pruefung auf Absolutheits-Marker "
        "(\"immer\"/\"nie\"). Heuristik, kein inhaltliches Meta-Analyse-Urteil.",
        _MAINFRAME,
    ),
    Module(
        "ClassicalBackend",
        "Klassisches Solver-Backend mit Audit-Layern (AuditAgent / EudaimoniaGuard).",
        _MAINFRAME,
        "Epistemischer Gateway mit Audit-Schichten.",
    ),
    Module(
        "_sa_kernel_trace",
        "Numba-JIT-Kernel (nopython=True, nogil=True) für den Simulated-Annealing-"
        "Core-Loop mit Trace-Aufzeichnung — ohne Speicherallokationen, GIL-frei.",
        _MAINFRAME,
        "Parallel-Engine-Kernel.",
    ),
    Module(
        "_anneal_one",
        "Führt einen einzelnen Annealing-Restart aus (ruft den JIT-Kernel auf).",
        _MAINFRAME,
        "Parallel-Engine-Worker.",
    ),
    Module(
        "parallel_anneal",
        "Parallelisiert mehrere Restarts über einen ThreadPoolExecutor. Liefert ein "
        "dict mit den Schlüsseln: solution, energy, energies, best_restart, traces, "
        "trace_steps, n_restarts, workers, runtime_seconds.",
        _MAINFRAME,
        "Parallel-Engine-Orchestrierung (numba nogil + ThreadPoolExecutor).",
    ),
    Module(
        "QUBOIntegrationCoreModule",
        "Integrationsschicht für QUBO-Läufe; exponiert execute_parallel_run(...), "
        "das parallel_anneal kapselt.",
        _MAINFRAME,
        "Methode: execute_parallel_run(...).",
    ),
]

# =====================================================================
# ARCHITEKTUR — Module in app.py (v2.2, NiceGUI 3.x)
# =====================================================================

APP_MODULES: List[Module] = [
    Module("Editor/IDE-Shell", "NiceGUI-Editor mit Splitter und Datei-Tabs.", _APP),
    Module("Run-Console", "Konsole zum Ausführen von Code und Anzeige der Ausgabe.", _APP),
    Module("5-Dimensionen-Review", "Eingebauter Peer-Review nach 5 Dimensionen.", _APP),
    Module("ZIP-Bundle", "Bündelt Projektdateien als ZIP-Export.", _APP),
    Module("Mainframe-Dialog", "Dialog zur Interaktion mit der Mainframe-Engine (mainframe.py).", _APP),
    Module(
        "Live-Monitoring",
        "Live-CPU-/RAM-Anzeige via psutil, aktualisiert über ui.timer.",
        _APP,
    ),
    Module(
        "Visualisierung",
        "Diagramme über NiceGUIs eingebautes ui.echart (ECharts).",
        _APP,
        "Siehe DECISIONS['visualization'].",
    ),
]

# =====================================================================
# ARCHITEKTUR — Konzeptionelle Module in HEROIC_SKILL.md (Methodik)
# =====================================================================

SKILL_MODULES: List[Module] = [
    Module("PeerReviewCoreModule", "5-Dimensionen-Review.", _SKILL),
    Module("ErkenntnisprozessCoreModule", "5-stufiger Erkenntnisprozess.", _SKILL),
    Module("CriticalMetaAnalysisCoreModule", "Kritische Meta-Analyse.", _SKILL),
    Module("FormalMathematicsCoreModule", "Formalisierung: Satz/Bedingt/Modell/Fragment.", _SKILL),
    Module("V3.3StructureCoreModule", "V3.3-Strukturvorgabe.", _SKILL),
    Module(
        "AutomaticArchivingCoreModule",
        "Automatische Archivierung; zusammen mit AllesZuEinemZusammenfuehrenCoreModule.",
        _SKILL,
    ),
    Module("AllesZuEinemZusammenfuehrenCoreModule", "Zusammenführung aller Artefakte zu einem.", _SKILL),
    Module("LiveProcessTrackingCoreModule", "Live-Prozess-Verfolgung.", _SKILL),
    Module("SelfModifyCoreModule", "Selbstmodifikation (konzeptionell).", _SKILL),
    Module("SelfModificationAuditAndSimulationCoreModule", "Audit & Simulation der Selbstmodifikation.", _SKILL),
    Module("AutonomousGraphicsEmbeddingCoreModule", "Autonomes Einbetten von Grafiken.", _SKILL),
    Module("RoadmapCoreModule", "Roadmap-Verwaltung.", _SKILL),
    Module("PseudocodeAndDictionaryCoreModule", "Pseudocode- und Wörterbuch-Modul.", _SKILL),
    Module("ConversationContextCoreModule", "Konversationskontext.", _SKILL),
    Module("GenerationalEvolutionProtocolCoreModule", "Generationelles Evolutionsprotokoll.", _SKILL),
]

# Konnektoren aus HEROIC_SKILL.md — jeweils nur aktiv, wenn die entsprechenden
# Tools verbunden sind. (Reine Beschreibung; keine echten Aktionen hier.)
CONNECTORS: Dict[str, str] = {
    "GitHub": "Nur aktiv, wenn die GitHub-Tools verbunden sind.",
    "Drive": "Nur aktiv, wenn die Drive-Tools verbunden sind.",
    "Vercel": "Nur aktiv, wenn die Vercel-Tools verbunden sind.",
    "Gmail": "Nur aktiv, wenn die Gmail-Tools verbunden sind.",
    "XAPI": "Nur aktiv, wenn die XAPI-Tools verbunden sind.",
}


# =====================================================================
# ENTSCHEIDUNGEN (DECISIONS)
# =====================================================================

_DECISIONS_LIST: List[Decision] = [
    Decision(
        "visualization",
        "NiceGUI ui.echart (ECharts)",
        "ui.echart ist in NiceGUI bereits eingebaut und benötigt keine "
        "zusätzlichen Pakete.",
        "plotly und matplotlib sind in dieser Umgebung NICHT installiert.",
    ),
    Decision(
        "hyperthreading",
        "numba nogil-Kernel + ThreadPoolExecutor (~3.6x Speedup)",
        "Mit nopython+nogil JIT-Kerneln läuft die heiße Schleife GIL-frei; ein "
        "ThreadPoolExecutor verteilt die Restarts über die logischen Kerne. "
        "Verifiziert: ~3.6x auf 6 physischen / 12 logischen Kernen.",
        "multiprocessing wurde verworfen (Pickling-/Startkosten, kein gemeinsamer Speicher).",
    ),
    Decision(
        "rng",
        "Modul-globaler rng = np.random.default_rng(7)",
        "Ein fester Seed liefert deterministische, reproduzierbare Heuristiken — "
        "House-Style über alle Module hinweg.",
    ),
    Decision(
        "import_safety",
        "Keine Top-Level-Seiteneffekte; Demo nur unter __main__",
        "Module müssen import-sicher sein (kein ui.run(), keine Netzwerkaufrufe "
        "beim Import), damit sie gefahrlos eingebunden werden können.",
    ),
    Decision(
        "connectors_dry_run",
        "Konnektoren als typisierte Wrapper mit available-Flag (Dry-Run by default)",
        "Konnektor-Klassen führen standardmäßig KEINE echten Außenaktionen aus "
        "(keine E-Mail/Push/Deploy/API-Writes); sie liefern Plan-/Dry-Run-Objekte "
        "oder werfen NotImplementedError mit klarer Meldung.",
    ),
    Decision(
        "docstring_language",
        "Deutsche Docstrings/Kommentare",
        "House-Style des Projekts; Konsistenz über alle Dateien.",
    ),
]

DECISIONS: Dict[str, Decision] = {d.key: d for d in _DECISIONS_LIST}


# =====================================================================
# GITHUB
# =====================================================================

GITHUB: Dict[str, object] = {
    "account": "95guknow",
    "repos": [
        Repo("fusion-hero-os", "Monorepo; enthält ein FastAPI-Dashboard unter 03_Code/Dashboard."),
        Repo("Fusion_Hero_OS_v1.1", "Versioniertes Fusion-Hero-OS-Repository (v1.1)."),
        Repo("dashboard", "Dashboard-Repository."),
        Repo("kilo", "kilo-Repository."),
    ],
}


# =====================================================================
# VERSIONEN
# =====================================================================

VERSIONS: Dict[str, FileVersion] = {
    _APP: FileVersion(_APP, "2.2", "NiceGUI 3.x Editor/IDE + Live-Agent-Monitor."),
    _MAINFRAME: FileVersion(_MAINFRAME, "5.25", "QUBO-Solver / Parallel-SA-Engine + Audit-Layer (Stub-Hooks)."),
}


# =====================================================================
# UMGEBUNG (ENVIRONMENT)
# =====================================================================

ENVIRONMENT: Dict[str, object] = {
    "os": "Windows (Windows 10 Pro)",
    "python": "3.10",
    "installed": ["numpy", "numba", "psutil", "nicegui (3.13)"],
    "not_installed": ["plotly", "matplotlib"],
    "cpu_topology": "6 physische / 12 logische Kerne",
    "notes": "German docstrings/comments are the house style.",
}


# =====================================================================
# AGGREGAT: KNOWLEDGE
# =====================================================================

KNOWLEDGE: Dict[str, object] = {
    "project": {
        "name": "Fusion Hero OS / ALTE_FRAU_95g Core",
        "knowledge_version": __version__,
    },
    "architecture": {
        "mainframe_modules": MAINFRAME_MODULES,
        "app_modules": APP_MODULES,
        "skill_modules": SKILL_MODULES,
        "connectors": CONNECTORS,
    },
    "decisions": DECISIONS,
    "github": GITHUB,
    "versions": VERSIONS,
    "environment": ENVIRONMENT,
}


# =====================================================================
# HELFER-FUNKTIONEN (reine Funktionen)
# =====================================================================

def get_decision(key: str) -> Optional[Decision]:
    """Liefert die Entscheidung zum gegebenen Schlüssel oder None.

    Verfügbare Schlüssel: siehe DECISIONS.keys().
    """
    return DECISIONS.get(key)


def list_modules(file: Optional[str] = None) -> List[Module]:
    """Liste aller bekannten Module.

    Wird ``file`` angegeben (z. B. "mainframe.py", "app.py" oder
    "HEROIC_SKILL.md"), werden nur die Module dieser Datei zurückgegeben.
    """
    all_modules: List[Module] = [*MAINFRAME_MODULES, *APP_MODULES, *SKILL_MODULES]
    if file is None:
        return all_modules
    return [m for m in all_modules if m.file == file]


def _md_modules(title: str, modules: List[Module]) -> List[str]:
    """Hilfsfunktion: rendert eine Modul-Liste als Markdown-Zeilen."""
    lines = [f"### {title}", ""]
    for m in modules:
        lines.append(f"- **{m.name}** — {m.role}")
    lines.append("")
    return lines


def as_markdown() -> str:
    """Rendert die gesamte Wissensbasis als lesbaren Markdown-Report (str)."""
    proj = KNOWLEDGE["project"]
    lines: List[str] = [
        f"# Projekt-Wissensbasis: {proj['name']}",
        "",
        f"_knowledge.py v{proj['knowledge_version']}_",
        "",
        "## Architektur",
        "",
    ]
    lines += _md_modules("mainframe.py (v5.25)", MAINFRAME_MODULES)
    lines += _md_modules("app.py (v2.2, NiceGUI 3.x)", APP_MODULES)
    lines += _md_modules("HEROIC_SKILL.md (Methodik)", SKILL_MODULES)

    lines += ["### Konnektoren", ""]
    for name, note in CONNECTORS.items():
        lines.append(f"- **{name}** — {note}")
    lines.append("")

    lines += ["## Entscheidungen", ""]
    for d in _DECISIONS_LIST:
        lines.append(f"- **{d.key}**: {d.choice}")
        lines.append(f"  - Begründung: {d.rationale}")
        if d.alternatives_rejected:
            lines.append(f"  - Verworfen: {d.alternatives_rejected}")
    lines.append("")

    lines += ["## GitHub", "", f"- Account: **{GITHUB['account']}**"]
    for repo in GITHUB["repos"]:  # type: ignore[index]
        lines.append(f"  - `{repo.name}` — {repo.description}")
    lines.append("")

    lines += ["## Versionen", ""]
    for v in VERSIONS.values():
        lines.append(f"- `{v.file}` — v{v.version} — {v.role}")
    lines.append("")

    env = ENVIRONMENT
    lines += [
        "## Umgebung",
        "",
        f"- OS: {env['os']}",
        f"- Python: {env['python']}",
        f"- CPU: {env['cpu_topology']}",
        f"- Installiert: {', '.join(env['installed'])}",  # type: ignore[arg-type]
        f"- Nicht installiert: {', '.join(env['not_installed'])}",  # type: ignore[arg-type]
        f"- Hinweis: {env['notes']}",
        "",
    ]
    return "\n".join(lines)


# =====================================================================
# DEMO (nur bei direktem Aufruf — import-sicher)
# =====================================================================

if __name__ == "__main__":
    print(as_markdown())
