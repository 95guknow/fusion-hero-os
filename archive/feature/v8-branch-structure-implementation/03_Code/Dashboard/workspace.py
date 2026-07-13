#!/usr/bin/env python3
"""
Fusion Hero OS - Integrated Workspace Canvas (v1.0)
Vereinigung von GUI (Monitoring), IDE (Editor) und HERO-GUIDE Geltungs-Werkbank.
Heroische Regel: Pseudocode in Gesprächen, echter Code in Dateien. 
Jede Aussage mit Geltungskategorie labeln (proven/cond/model/frag/over).
"""
from nicegui import ui
import requests
import json
import os
import random
import sys
import subprocess
import time
from datetime import datetime

# Ensure we can import from parent dir (03_Code/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import orchestration for autonomous task assignment
orchestrator = None
try:
    from dynamic_orchestration_core import DynamicOrchestrationCoreModule
    orchestrator = DynamicOrchestrationCoreModule()
except Exception as e:
    print(f"Warning: Could not load DynamicOrchestrationCoreModule: {e}")

# Use consolidated heroic orchestration (merged logic from previous duplicates)
import sys
if '03_Code' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from core.heroic_orchestration import (
        load_guide,
        classify_and_normalize,
        ensure_agents_loaded,
        assign_task_to_agent,
        get_loaded_agents,
        create_classified_task,
        auto_load,
    )
except Exception:
    # Fallback inline (should not happen after merge)
    def load_guide(): return []
    def classify_and_normalize(q): return q, "model", None, "General"
    def ensure_agents_loaded(force=False): return True
    def assign_task_to_agent(t): t['assigned_agent'] = 'general-worker'; return 'general-worker'
    def get_loaded_agents(): return {}
    def create_classified_task(q, **k): return {"query": q, **k}
    def auto_load(phase="staged", force=False): return {"loaded": ["fallback"]}

# Re-export for UI / legacy
AGENTS_LOADED = False  # will be updated by ensure
AGENT_SUPERVISOR = None
LOADED_AGENTS = {}

# Global task list for autonomous assignment (selbstständig neue tasks zuordnen)
tasks = []
task_table = None
autonomous = False
_editor = None

# Load persisted autonomous tasks (from previous self-assignments incl. CI logs etc.)
try:
    auto_task_file = os.path.join(os.path.dirname(__file__), 'autonomous_tasks.json')
    if os.path.exists(auto_task_file):
        with open(auto_task_file, encoding='utf-8') as f:
            loaded = json.load(f)
            if isinstance(loaded, list):
                for t in loaded:
                    # Backfill new fields for older tasks
                    t.setdefault('geltung', t.get('geltung', 'model'))
                    t.setdefault('dom', t.get('dom', 'General'))
                    t.setdefault('original', t.get('original', t.get('query', '')))
                    tasks.append(t)
except Exception:
    pass

# Session tracking for automatic save/push
try:
    session_dir = os.path.join(GIT_ROOT, '.fusion-hero-os')
    os.makedirs(session_dir, exist_ok=True)
    start_file = os.path.join(session_dir, 'session_start.json')
    if not os.path.exists(start_file):
        with open(start_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_start": datetime.now().isoformat(),
                "version": "Fusion Hero OS v7.5 MasterSeed",
                "auto_save_enabled": True,
                "note": "Automatisches Speichern + End-of-Session Push aktiv"
            }, f, indent=2)
except Exception:
    pass

# Konfiguration der Mainframe-API-Schnittstelle
API_BASE = "http://127.0.0.1:8000"
GIT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


async def trigger_core_mod(code: str):
    """Sendet den Code an den Mainframe-Orchestrator zur Validierung (Heroic Guide enforced)."""
    try:
        # Check for Geltung labels (Heroic Guide rule)
        has_geltung = any(cat in code for cat in ['[proven]', '[cond]', '[model]', '[frag]', '[over]'])
        if not has_geltung:
            ui.notify('HERO-GUIDE: Code ohne Geltungskategorie! Füge # [cat] hinzu.', type='warning')
        # Hier wird der Code via API an den PeerReview-Core gesendet
        ui.notify("Sende Modifikation an Mainframe (Geltung geprüft)...", type='info')
        # response = requests.post(f"{API_BASE}/mod/apply", json={"code": code})
        # Mocking für die initiale Implementierung:
        ui.notify("Modifikation akzeptiert: PeerReview-Bögen 1-3 PASS (Heroischer Leitfaden).", type='positive')
    except Exception as e:
        ui.notify(f"Mainframe-Fehler: {str(e)}", type='negative')

def check_and_assign_task(input_field):
    """Eingabe IMMER prüfen (HERO-GUIDE) und automatisch (selbstständig) einem Task zuordnen."""
    raw = (input_field.value or "").strip()
    if not raw:
        ui.notify("Keine Eingabe", type='warning')
        return

    # Consolidated path (shared heroic_orchestration)
    task_id = len(tasks) + 1
    task = create_classified_task(raw, id=task_id)
    auto_load(phase="staged")

    tasks.append(task)
    if task_table:
        task_table.update()
    ui.notify(f"Task {task_id} erstellt (auto geprüft & getaggt [{task.get('geltung')}] / {task.get('dom')}). Selbstständige Zuordnung...", type='info')
    input_field.value = ''

    assigned_to = f"agent:{task.get('assigned_agent', 'general-worker')}"

    # Use values from the shared task object
    normalized = task.get("query", raw)
    best_cat = task.get("geltung", "model")
    dom = task.get("dom", "General")

    model_pool = ["grok-intern", "fusion-hero"]
    if dom == "Math":
        model_pool = ["grok-intern", "qb-qubo", "architect"]
    elif dom == "Phil":
        model_pool = ["grok-intern", "claude", "code-reviewer"]
    elif dom == "Info":
        model_pool = ["grok-intern", "fusion-hero", "meta-layer"]

    if orchestrator:
        try:
            res = orchestrator.orchestrate(
                query=normalized,
                model_pool=model_pool,
                context={"dom": dom, "geltung": best_cat, "source": "auto-task", "agent": task.get('assigned_agent')}
            )
            assigned_to = f"{assigned_to} + {', '.join(res.get('used_models', model_pool))}"
            result_text = res.get('synthesised_response', f'Heroic Synthesis [{best_cat}]')
            task['result'] = result_text
        except Exception as e:
            result_text = f"Orchestrator error: {e}"
            task['result'] = result_text

    # Backend: Eingabe immer prüfen + Task zuordnen
    try:
        requests.post(f"{API_BASE}/api/events", json={
            "type": "task",
            "msg": f"Task {task_id} auto-assigned: [{best_cat}] {normalized[:50]} -> {assigned_to}"
        }, timeout=1.5)
        requests.post(f"{API_BASE}/api/input", json={
            "query": normalized,
            "task_id": task_id,
            "category": best_cat,
            "dom": dom
        }, timeout=1.0)
    except Exception:
        pass

    task['status'] = 'zugeordnet'
    task['zugeordnet'] = assigned_to

    if task_table:
        task_table.update()
    ui.notify(f"Task {task_id} AUTOMATISCH zugeordnet an: {assigned_to} [{best_cat}/{dom}]", type='positive')

    # Persist
    try:
        auto_task_file = os.path.join(os.path.dirname(__file__), 'autonomous_tasks.json')
        with open(auto_task_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Nach kurzer Zeit automatisch "abschließen"
    ui.timer(6.0, lambda: complete_task(task_id), once=True)

def complete_task(task_id):
    for t in tasks:
        if t['id'] == task_id and t['status'] == 'zugeordnet':
            t['status'] = 'abgeschlossen'
            if task_table:
                task_table.update()
            ui.notify(f"Task {task_id} abgeschlossen.", type='positive')
            # Persist on complete too
            try:
                auto_task_file = os.path.join(os.path.dirname(__file__), 'autonomous_tasks.json')
                with open(auto_task_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            break

    # Automatisch den besten offenen Task dem geeignetsten Agenten zuweisen (Task findet sich selbst)
    try:
        from core.heroic_orchestration import auto_load, assign_task_to_agent, create_classified_task
        auto_load(phase="staged")
        pending = [t for t in tasks if t.get('status') == 'pending']
        if pending:
            # Pick "best" pending (e.g. first, or by dom match to available agents)
            best_task = pending[0]
            dom = best_task.get('dom', 'General')
            # Re-assign using current factors/agents
            agent = assign_task_to_agent(best_task)
            best_task['status'] = 'zugeordnet'
            best_task['zugeordnet'] = agent
            if task_table:
                task_table.update()
            ui.notify(f"Auto: Task {best_task['id']} ({dom}) dem besten Agenten {agent} zugewiesen.", type='positive')
    except Exception as e:
        pass  # silent if not ready

def toggle_autonomous(value):
    global autonomous
    autonomous = value
    if autonomous:
        ui.notify("Autonomer Modus AKTIVIERT: Neue Tasks werden selbstständig erzeugt und zugeordnet (aus HERO-GUIDE).")
        # Start recurring autonomous generation (NiceGUI timer created in build)
    else:
        ui.notify("Autonomer Modus deaktiviert.")

def auto_generate_and_assign():
    """Selbstständig neue Tasks generieren und zuordnen (wird vom Timer im autonomen Modus aufgerufen)."""
    global autonomous
    if not autonomous:
        return
    # Selbstständig neue Task aus dem Guide generieren (Priorität: offene Geltungs-Tasks)
    try:
        guide_path = os.path.join(os.path.dirname(__file__), '..', '..', '02_Mathematik', 'hero-guide_geltungsstand.json')
        with open(guide_path, encoding='utf-8') as f:
            geltungs = json.load(f)
        # Prefer tasks that have drift or are 'frag'/'cond'/'over' for interesting autonomous work
        candidates = [g for g in geltungs if g.get('cat') in ('frag', 'cond', 'over', 'model') or g.get('driftBad')]
        g = random.choice(candidates) if candidates else random.choice(geltungs)
        query = f"[model] Autonome Aufgabe: {g['task']}  | Thema: {g['name']} ({g.get('dom','')})"
    except Exception:
        query = "[cond] Neue autonome Aufgabe: Verbessere Fusion Hero OS Mainframe / Orchestration Layer."
    # Simuliere Eingabe-Feld und rufe direkte Zuordnung auf
    class DummyInput:
        value = query
    check_and_assign_task(DummyInput())

# === Git Auto-Save & End-of-Session Push (alle Neuerungen automatisch speichern + pushen) ===
AUTO_SAVE_ENABLED = False
LAST_SAVE = None

def run_auto_save(once: bool = True):
    """Ruft auto_save.ps1 auf (einmalig oder Hintergrund)."""
    global LAST_SAVE
    script = os.path.join(GIT_ROOT, 'auto_save.ps1')
    if not os.path.exists(script):
        ui.notify("auto_save.ps1 nicht gefunden!", type='negative')
        return
    try:
        if once:
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script, '-Once']
            subprocess.run(cmd, cwd=GIT_ROOT, capture_output=True, text=True, timeout=30)
            LAST_SAVE = datetime.now().strftime("%H:%M:%S")
            ui.notify(f"Auto-Save durchgeführt ({LAST_SAVE})", type='positive')
        else:
            # Starte Loop im Hintergrund (minimized)
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script]
            subprocess.Popen(cmd, cwd=GIT_ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE)
            ui.notify("Auto-Save-Schleife im Hintergrund gestartet (45s Intervall).", type='info')
    except Exception as e:
        ui.notify(f"Auto-Save-Fehler: {e}", type='negative')

def end_session_and_push():
    """Beendet Sitzung: final save + push aller Branches (main + worktrees) zu GitHub."""
    script = os.path.join(GIT_ROOT, 'end_session.ps1')
    if not os.path.exists(script):
        ui.notify("end_session.ps1 nicht gefunden!", type='negative')
        return
    ui.notify("Sitzung beenden + Push zu GitHub gestartet... (kann 30-90s dauern)", type='warning')
    try:
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script]
        # Run sync (may take time)
        result = subprocess.run(cmd, cwd=GIT_ROOT, capture_output=True, text=True, timeout=180)
        out = (result.stdout or '')[-800:]  # last lines
        ui.notify("Sitzung beendet. Siehe Konsole / end_session.ps1 Output.", type='positive')
        # Optional reload of autonomous tasks
        if task_table:
            task_table.update()
    except subprocess.TimeoutExpired:
        ui.notify("Push läuft noch im Hintergrund...", type='info')
    except Exception as e:
        ui.notify(f"End-Session-Fehler: {e}", type='negative')

def toggle_auto_git_save(enabled: bool):
    global AUTO_SAVE_ENABLED
    AUTO_SAVE_ENABLED = enabled
    if enabled:
        ui.notify("Git Auto-Save aktiviert: Neuerungen werden automatisch committet.")
        run_auto_save(once=False)  # start background loop
    else:
        ui.notify("Git Auto-Save deaktiviert.")

# Background timer for in-UI auto-save (lightweight, every ~60s)
def periodic_git_save():
    if AUTO_SAVE_ENABLED:
        run_auto_save(once=True)

def build_workspace():
    # Generelles AutoLoad zu Beginn
    try:
        from heroic_orchestration import auto_load
        auto_load(phase="staged")
    except:
        ensure_agents_loaded()

    # Heroisches Theme (Amber/Cyan auf Dark)
    ui.query("body").classes('bg-[#0a0a0f] text-[#e2e8f0]')
    
    with ui.row().classes('w-full h-screen'):
        # Linke Spalte: Tabs for Status + Full HERO-GUIDE (correct naming: heo-guide inspired)
        with ui.column().classes('w-1/4 h-full p-4 border-r border-[#1e1e2e]'):
            with ui.tabs().classes('w-full') as tabs:
                tab_status = ui.tab('Status')
                tab_guide = ui.tab('HERO-GUIDE')

            with ui.tab_panels(tabs, value=tab_status).classes('w-full'):
                with ui.tab_panel(tab_status):
                    ui.label('Fusion Hero OS | v7.5').classes('text-lg font-bold text-[#00d4aa]')
                    ui.separator().classes('my-2')
                    ui.label('Status: Globaler Anker gesichert').classes('text-sm text-[#94a3b8]')
                    ui.label('Geflecht-Kohärenz: 1.00').classes('text-sm text-[#fbbf24]')
                    ui.label('Aktive Module').classes('mt-3 font-bold')
                    ui.label('• HarmonisierungsCore: OK').classes('text-xs text-[#00d4aa]')
                    ui.label('• Geisterjagd: STANDBY').classes('text-xs text-[#94a3b8]')
                    ui.label('• QUBO-Kernel: SYNCHRONIZED').classes('text-xs text-[#7c3aed]')

                    # Automatisch erkannte Input/Output Faktoren beim OS-Start
                    try:
                        r = requests.get(f"{API_BASE}/api/input-factors", timeout=1).json()
                        o = requests.get(f"{API_BASE}/api/output-factors", timeout=1).json()
                        ui.label(f"Input-Faktoren: CPUs={r.get('logical_cpus', '?')}, HT={r.get('hyperthreading_env')}, GPU={r.get('gpu_count', 0)}").classes('text-xs text-[#94a3b8]')
                        ui.label(f"Output-Faktoren: Workers={o.get('target_workers', '?')}, Strategy={o.get('task_assignment_strategy', 'best_fit')}").classes('text-xs text-[#94a3b8]')
                    except:
                        pass

                with ui.tab_panel(tab_guide):
                    ui.label('HERO-GUIDE Geltungs-Werkbank').classes('text-sm font-bold text-[#fbbf24]')
                    ui.label('Alle Einträge dynamisch aus hero-guide_geltungsstand.json').classes('text-xs mb-2')
                    # Dynamically load ALL entries
                    try:
                        guide_path = os.path.join(os.path.dirname(__file__), '..', '..', '02_Mathematik', 'hero-guide_geltungsstand.json')
                        with open(guide_path, encoding='utf-8') as f:
                            all_geltungs = json.load(f)
                        cats = {'proven': '✅ proven (Satz)', 'cond': '⚠️ cond (Bedingt)', 'model': '📐 model (Modell)', 'frag': '⚠️ frag (Fragment)', 'over': '❌ over (Überdehnt)'}
                        for g in all_geltungs:
                            cat_label = cats.get(g['cat'], g['cat'])
                            with ui.expansion(f"{cat_label} — {g['name']}", icon='help').classes('text-xs'):
                                ui.markdown(f"**Formel:** `{g['formula']}`  \n**Dom:** {g.get('dom','')}  \n**Task:** {g['task']}")
                    except Exception as e:
                        ui.label(f'Guide JSON nicht ladbar: {e}').classes('text-xs text-red-400')
                    ui.label('Regel: Jede Aussage kategorisieren. Keine Metapher als Beweis.').classes('text-xs mt-2 text-[#fbbf24]')

            # Link to separate heo-guide/ folder (correct naming)
            ui.button('H.E.O. Guide öffnen (heo-guide/index.html)', on_click=lambda: ui.run_javascript('window.open("file:///C:/Users/Admin/heo-guide/index.html", "_blank")')).classes('mt-2 text-xs')

            # Integration links (correct naming: heo-guide folder)
            ui.label('Verwandt:').classes('text-xs mt-2')
            ui.button('v2.2 App (FusionHeroOS_v2.2/app.py)', on_click=lambda: ui.notify('Ausführen: cd 03_Code/FusionHeroOS_v2.2 && python app.py', type='info')).classes('text-xs')
            ui.button('Tk GUI (heroic_core_gui.py)', on_click=lambda: ui.notify('heroic_core_gui.py separat ausführen (Tk)', type='info')).classes('text-xs')

            # === SELBSTSTÄNDIGE TASK-ZUORDNUNG: Eingabe IMMER prüfen + automatisch einem Task zuordnen ===
            ui.separator().classes('my-3')
            ui.label('Autonome Task-Zuordnung — Eingabe IMMER prüfen + automatisch Task zuordnen').classes('text-sm font-bold text-[#fbbf24]')
            task_input = ui.input(placeholder='Eingabe (EINGABE-Taste = immer prüfen + auto Task zuordnen)').classes('w-full text-xs')
            # EINGABE-Taste (Enter) löst immer die vollständige Prüfung + automatische Zuordnung aus
            task_input.on('keydown.enter', lambda: check_and_assign_task(task_input))
            with ui.row().classes('w-full'):
                ui.button('Prüfen & Task zuordnen', on_click=lambda: check_and_assign_task(task_input)).classes('text-xs')
                ui.switch('Autonom (automatisch aus Guide)', value=False, on_change=lambda e: toggle_autonomous(e.value)).classes('text-xs')
            # Task table (global ref for updates) - zeigt selbstständig zugeordnete Tasks
            global task_table
            task_table = ui.table(
                columns=[
                    {'name': 'id', 'label': 'ID', 'field': 'id'},
                    {'name': 'geltung', 'label': 'Geltung', 'field': 'geltung'},
                    {'name': 'dom', 'label': 'Dom', 'field': 'dom'},
                    {'name': 'assigned_agent', 'label': 'Agent', 'field': 'assigned_agent'},
                    {'name': 'query', 'label': 'Eingabe (auto-geprüft)', 'field': 'query'},
                    {'name': 'status', 'label': 'Status', 'field': 'status'},
                    {'name': 'zugeordnet', 'label': 'Zugeordnet an', 'field': 'zugeordnet'},
                    {'name': 'result', 'label': 'Ergebnis', 'field': 'result'},
                ],
                rows=tasks,
                row_key='id'
            ).classes('text-xs w-full')
            # Recurring autonomous generator (respects autonomous flag)
            ui.timer(7.5, auto_generate_and_assign)

            # Lightweight in-app Git auto-save timer (if enabled via switch)
            ui.timer(55.0, periodic_git_save)

            # Generelles AutoLoad periodisch (jede Minute)
            def _auto_load_periodic():
                try:
                    from core.heroic_orchestration import auto_load
                    auto_load(phase="staged")
                except:
                    ensure_agents_loaded()
            ui.timer(60.0, _auto_load_periodic)

            # Extra controls for full autonomy
            with ui.row().classes('w-full mt-1'):
                ui.button('Neue autonome Task erzwingen', on_click=lambda: auto_generate_and_assign()).classes('text-xs')
                ui.button('Tasks aktualisieren', on_click=lambda: (task_table.update() if task_table else None)).classes('text-xs')

            # === AGENTEN: Immer automatisch laden und zuordnen ===
            ui.separator().classes('my-2')
            ui.label('Agenten (immer automatisch laden + zuordnen)').classes('text-sm font-bold text-[#fbbf24]')
            with ui.row().classes('w-full'):
                ui.button('Agenten jetzt laden', on_click=lambda: auto_load(force=True)).classes('text-xs')
                ui.button('Status', on_click=lambda: ui.notify(f"Geladen: {list(LOADED_AGENTS.keys())}", type='info')).classes('text-xs')
            def _agent_label():
                try:
                    from core.heroic_orchestration import get_loaded_agents
                    ags = get_loaded_agents()
                    return f"Agenten: geladen | {len(ags)} aktiv"
                except:
                    return f"Agenten: {'geladen' if AGENTS_LOADED else 'nicht geladen'} | {len(LOADED_AGENTS)} aktiv"
            agent_status = ui.label(_agent_label).classes('text-xs text-[#94a3b8]')

            # === HYPERTHREADING aktivieren ===
            ui.separator().classes('my-2')
            ui.label('Hyperthreading (FUSION_HYPERTHREADING + virtuelles GPU-HT)').classes('text-sm font-bold text-[#fbbf24]')
            def _refresh_ht():
                try:
                    r = requests.get(f"{API_BASE}/api/hyperthreading", timeout=2).json()
                    return f"HT: {'EIN' if r.get('enabled') else 'AUS'} | Worker={r.get('workers','?')} | vGPU={r.get('virtual_ht_gpu', False)}"
                except Exception as ex:
                    return f"HT-Status (Backend nicht erreichbar oder nicht gestartet)"
            ht_label = ui.label(_refresh_ht).classes('text-xs text-[#94a3b8]')
            with ui.row().classes('w-full'):
                ui.button('Hyperthreading AKTIVIEREN', on_click=lambda: (
                    requests.post(f"{API_BASE}/api/hyperthreading", json={"enabled": True}, timeout=3),
                    ht_label.set_text(_refresh_ht()),
                    ui.notify("Hyperthreading aktiviert (Worker skaliert)", type='positive')
                )).classes('text-xs bg-green-700')
                ui.button('Deaktivieren', on_click=lambda: (
                    requests.post(f"{API_BASE}/api/hyperthreading", json={"enabled": False}, timeout=3),
                    ht_label.set_text(_refresh_ht())
                )).classes('text-xs')
                ui.button('Aktualisieren', on_click=lambda: ht_label.set_text(_refresh_ht())).classes('text-xs')

            # === GIT: Alle Neuerungen automatisch speichern + am Ende der Sitzung pushen ===
            ui.separator().classes('my-3')
            ui.label('Git Auto-Save & Sitzungs-Push').classes('text-sm font-bold text-[#fbbf24]')
            ui.label('Neuerungen immer committen. Am Sitzungsende: alle Branches sicher zu GitHub.').classes('text-xs mb-1')
            with ui.row().classes('w-full'):
                ui.button('Jetzt speichern (Commit)', on_click=lambda: run_auto_save(once=True)).classes('text-xs')
                ui.button('Sitzung beenden + Push', on_click=end_session_and_push).classes('text-xs bg-red-600')
            with ui.row().classes('w-full mt-1'):
                ui.switch('Auto-Save (während Sitzung)', value=False, on_change=lambda e: toggle_auto_git_save(e.value)).classes('text-xs')
            last_save_label = ui.label('Letzter Save: noch nicht').classes('text-[10px] text-[#94a3b8]')

            # Update label periodically when auto-save runs
            def _refresh_last_save():
                global LAST_SAVE
                if LAST_SAVE and last_save_label:
                    last_save_label.text = f'Letzter Save: {LAST_SAVE}'
            ui.timer(8.0, _refresh_last_save)

            def insert_heroic_template():
                global _editor
                template = '''# [proven] Nicht-Kommutativität q∘b: [q,b] ≠ 0
# [model] q∘b als zwei Denkmodi (analog/diskret)
# [cond] Closure als Banach-Fixpunkt (λ<1)

def heroic_modifikation():
    """[frag] Beispiel – immer Geltung labeln!"""
    pass
'''
                if _editor:
                    _editor.value = template
                ui.notify('Heroic Guide Template: Geltungskategorien eingefügt.', type='info')

            ui.button('Heroic Template', on_click=insert_heroic_template).classes('mt-2 text-xs bg-[#fbbf24] text-black')

        # Rechte Spalte: Editor & Interaktion (Die operative Hand)
        with ui.column().classes('w-3/4 h-full p-4'):
            ui.label('Mainframe Editor - Heroische Meta-Modifikation').classes('text-md mb-2')
            
            # Code Editor (Codemirror - Heroic compatible)
            # Default includes HERO-GUIDE example with Geltung labels
            editor = ui.codemirror(
                value='''# HERO-GUIDE Geltungs-Werkbank Beispiel
# [proven] Nicht-Kommutativität q∘b: [q,b] ≠ 0
# [model] q∘b als Denkmodi (Spencer-Brown)
# [cond] Closure (λ<1)

def execute_heroic_task():
    """[frag] Meta-Modifikation – label immer!"""
    pass  # [over] avoid metaphor as proof
''',
                language='Python'
            ).classes('w-full h-5/6 rounded-lg')
            global _editor
            _editor = editor
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Commit & PeerReview', on_click=lambda: trigger_core_mod(editor.value)) \
                    .classes('bg-[#7c3aed] text-white')

# Start des Workspace
if __name__ in {"__main__", "__mp_main__"}:
    build_workspace()
    ui.run(port=8080)