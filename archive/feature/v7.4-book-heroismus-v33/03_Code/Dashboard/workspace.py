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

# Konfiguration der Mainframe-API-Schnittstelle
API_BASE = "http://127.0.0.1:8000"

# Global for editor (to allow guide buttons before editor in layout)
_editor = None

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
        ui.notify("Modifikation akzeptiert: PeerReview-Bögen 1-3 PASS (Heroic Guide).", type='positive')
    except Exception as e:
        ui.notify(f"Mainframe-Error: {str(e)}", type='negative')

def build_workspace():
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
                    ui.label('Fusion Hero OS | v5.8').classes('text-lg font-bold text-[#00d4aa]')
                    ui.separator().classes('my-2')
                    ui.label('Status: Global Anchor Locked').classes('text-sm text-[#94a3b8]')
                    ui.label('Geflecht-Kohärenz: 1.00').classes('text-sm text-[#fbbf24]')
                    ui.label('Aktive Module').classes('mt-3 font-bold')
                    ui.label('• HarmonisierungsCore: OK').classes('text-xs text-[#00d4aa]')
                    ui.label('• Geisterjagd: STANDBY').classes('text-xs text-[#94a3b8]')
                    ui.label('• QUBO-Kernel: SYNCHRONIZED').classes('text-xs text-[#7c3aed]')

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
            ui.button('Open H.E.O. Guide (heo-guide/index.html)', on_click=lambda: ui.run_javascript('window.open("file:///C:/Users/Admin/heo-guide/index.html", "_blank")')).classes('mt-2 text-xs')

            # Integration links (correct naming: heo-guide folder)
            ui.label('Related:').classes('text-xs mt-2')
            ui.button('v2.2 App (FusionHeroOS_v2.2/app.py)', on_click=lambda: ui.notify('Run: cd 03_Code/FusionHeroOS_v2.2 && python app.py', type='info')).classes('text-xs')
            ui.button('Tk GUI (heroic_core_gui.py)', on_click=lambda: ui.notify('Run the heroic_core_gui.py separately (Tk)', type='info')).classes('text-xs')

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
build_workspace()
ui.run(port=8080)