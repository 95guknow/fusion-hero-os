---
name: pending-code-honesty-audit
description: Offene Aufgabe — gesamten Code auf Bugs + Claim-vs-Substanz-Überclaims prüfen/fixen; teils blockiert durch Session-Limit
metadata: 
  node_type: memory
  type: project
  originSessionId: e5bb8844-5bfd-4246-aa4e-e24f875c5844
---

Auftrag des Nutzers (2026-06-29): den **gesamten Code** des ALTE_Frau_95g/Heroic-Core-Repos auf zwei Dinge prüfen und fixen — (1) echte Bugs, (2) die wiederkehrende **Claim-vs-Substanz-Lücke**: Docstrings/Header/Prints, die Fähigkeiten/Garantien behaupten, die der Code nicht einlöst.

**ERLEDIGT (2026-06-29, inline verifiziert):**
- `C:\Users\Admin\Downloads\qb_qubo.py` (AUSSERHALB des Repos): `qubo_to_ising`-Faktor-2-Fehler gefixt — `h` und `const` jetzt `/2` statt `/4`; `if okmap:`-Guard ergänzt. Lauf zeigt jetzt `[4] ... True`. (Standalone-Datei, nicht versioniert.)
- `engine/mainframe.py`: Modul-Header entzerrt ("Core Sicherheits-Layer"/"Immutable Foundations" → ehrliche Stub-Beschreibung) + die drei Stub-Klassen mit "PLATZHALTER-STUB"-Docstrings versehen. Commit **0e8c326** auf main.

**NOCH OFFEN — als Hintergrund-Chips gespawnt (2026-06-29):**
- task_1392b6cb "Code-Honesty-Audit: große Dateien fixen" — app.py, core_modules.py, knowledge.py, agents.py auf Bugs + Überclaims (der ursprünglich am Session-Limit gescheiterte Sweep; resumebares Workflow-Script: workflows/scripts/audit-heroic-core-wf_06db8156-56d.js).
- task_6296454e "Echte Generationen-Evolution auf parallel_anneal" — Platzhalter-GenerationalEvolution durch echte (μ+λ)-Schleife mit parallel_anneal als Fitness ersetzen.
- task_1e03ffb3 "v5.22-Kompendium-Stubs ehrlich labeln" — gleiche Docstring-Korrektur für die Standalone-Kopien unter Downloads/v5.22_QUBO_Architektur_Kompendium/.../core/.

Verwandt: [[project-architecture]]. Commit 617e1ac (Rust-Backend + mining_qubo.py) war nur ein Checkpoint davor.

**2026-06-29 Fortsetzung:** task_6296454e (echte μ+λ-Evolution) und Knowledge-Honesty-Sync sind erledigt (Commits 004173f, 00194e2, 0725947) — liefen auf einer von der Hauptlinie abgezweigten Branch (`rescue/qubo-session-2026-06-29`), während parallel ein Supervisor-Bugfix (7c7fdf6 "zählt nur eigene Worker bei Bus-Reuse") auf einer ANDEREN Branch (`claude/loving-williams-ae2943`, separates Worktree unter `Desktop/projekt_archiv/CLAUDE/...`) entstand. Beide wurden konfliktfrei gemerged (126a68a). Zusätzlich: Rust-Kernel hatte einen echten Performance-Bug — `Q.ravel().tolist()` entpackte jedes Matrix-Element als PyObject (O(n²) mit hohem Konstantfaktor), wodurch Rust bei n=800 LANGSAMER war als numba (0.67x). Fix: `PyReadonlyArray2` (numpy-Crate) liest über das Buffer-Protokoll → danach durchgehend 1.4x–8x schneller als numba (Commit d07b790). 16/16 Tests grün nach Merge.

Restliche offene Punkte aus der ursprünglichen Liste (app.py/core_modules.py/agents.py voller Audit-Sweep, v5.22-Kompendium-Stub-Labels) sind weiterhin offen.
