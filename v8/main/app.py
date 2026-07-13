#!/usr/bin/env python3
"""Fusion Hero OS — GUI + IDE, v2.2 (NiceGUI 3.x).

Neu in v2.2:
- Modulares Layout: Editor | Hauptagent-Panel (nested splitter, ein-/ausklappbar)
- Live-Hauptagent-Monitor (agents.py): Belegschaft + Ereignis-Stream "über die Schulter"
- Chat-I/O-Panel: Aufgaben an den Hauptagenten, Ergebnis als Verlauf
- Live-Pipeline-Statuszeile + Konvergenz; Substanz-Fix (Stufe 4 auditiert dieselbe Q)
- Formatierung: schlanke Scrollbars, kompakte Tabs/Felder, konsistente Abstände


Verbesserungen ggü. v1.0:
- Resizable Splitter (Sidebar | Editor) statt fixer Breite
- Mehrere offene Dateien als Tabs mit eigenem Puffer + Dirty-Tracking
- "Ausführen"-Button: startet .py via Subprocess, Ausgabe in Konsole unten
- Datei-Filter, neue Datei anlegen, Statuszeile

Neu in v2.1:
- Visualisierung via ui.echart (Konvergenz, Q-/Beitrags-Heatmap, CPU/RAM-Verlauf, Sweep)
- Pipelines-Panel: 4 Workflows (Erkenntnis-Lauf 5-Stufen, Parallel-Solve, Review&Archive, Sweep)
- Hyperthreading: paralleles Multi-Start-SA über alle Kerne (engine.mainframe.parallel_anneal)
"""
from pathlib import Path
from collections import deque
import zipfile, datetime, re, subprocess, sys, os, io, contextlib, time
import numpy as np
from nicegui import ui, run
from fusion_hero_os.registry import get_registry

_registry = get_registry()
hc = _registry.get("engine.mainframe")      # QUBO-Solver-Engine (Parallel-SA, Audit-Layer)
ag = _registry.get("orchestration.agents")  # Multi-Agenten-Orchestrierung (Supervisor/Worker)

ROOT = Path(__file__).parent
EXT_LANG = {".md": "Markdown", ".py": "Python", ".json": "JSON",
            ".txt": None, ".yaml": "YAML", ".yml": "YAML"}

# --- Zustand --------------------------------------------------------------
# buffers[path] = {"content": str, "saved": str, "dirty": bool}
state = {"current": None, "filter": ""}
opened: list[Path] = []
buffers: dict[Path, dict] = {}

# Pipeline-/Chart-Zustand (Modul-Ebene; UI-Refs werden im Layout zugewiesen)
pipeline = {"name": None, "steps": [], "current": -1, "running": False, "cancel": False}
last_Q = {"Q": None}        # zuletzt erzeugte Matrix (für 'wiederverwenden')
pipe_ctx = {}               # Zwischenergebnisse zwischen Pipeline-Schritten
conv_chart = heat_chart = metrics_chart = sweep_chart = surf3d_chart = None  # ui.echart-Refs
auto_state = {"on": False, "rounds": 0}  # autonome Hintergrundaufgaben

PALETTE = ['#00d4aa', '#8b5cf6', '#f59e0b', '#22d3ee', '#ef4444', '#10b981',
           '#eab308', '#3b82f6', '#ec4899', '#14b8a6', '#a78bfa', '#f97316']
HIST = 60
cpu_hist = deque([0.0] * HIST, maxlen=HIST)
ram_hist = deque([0.0] * HIST, maxlen=HIST)
time_axis = [f"-{(HIST - 1 - i) * 2}s" for i in range(HIST)]


def list_files():
    return sorted(p for p in ROOT.iterdir()
                  if p.is_file() and p.suffix in EXT_LANG and not p.name.startswith("Archiv_"))


# --- Datei-Operationen ----------------------------------------------------
def open_file(path: Path):
    if path not in buffers:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Konnte {path.name} nicht lesen: {exc}", type="negative")
            return
        buffers[path] = {"content": text, "saved": text, "dirty": False}
    if path not in opened:
        opened.append(path)
    activate(path)


def activate(path: Path):
    state["current"] = path
    buf = buffers[path]
    lang = EXT_LANG.get(path.suffix)
    editor.set_language(lang or "Markdown")
    editor.set_value(buf["content"])
    render_tabs()
    render_files()
    update_status()


def _do_close(path: Path):
    if path in opened:
        opened.remove(path)
    buffers.pop(path, None)
    if state["current"] == path:
        state["current"] = opened[-1] if opened else None
        if state["current"]:
            activate(state["current"])
        else:
            editor.set_value("")
            render_tabs()
            render_files()
            update_status()
    else:
        render_tabs()
        render_files()


def close_file(path: Path):
    if buffers.get(path, {}).get("dirty"):
        with ui.dialog() as d, ui.card().classes("bg-[#11111b] min-w-[300px]"):
            ui.label(f"Ungespeicherte Änderungen in {path.name} verwerfen?") \
                .classes("text-sm text-[#e2e8f0]")
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Abbrechen", on_click=d.close).props("flat")
                ui.button("Verwerfen", on_click=lambda: (d.close(), _do_close(path))) \
                    .props("color=red")
        d.open()
    else:
        _do_close(path)


def on_edit(e):
    path = state["current"]
    if path is None:
        return
    buf = buffers[path]
    buf["content"] = e.value
    new_dirty = buf["content"] != buf["saved"]
    if new_dirty != buf["dirty"]:
        buf["dirty"] = new_dirty
        render_tabs()
        render_files()
    update_status()


def save():
    path = state["current"]
    if not path:
        ui.notify("Keine Datei geöffnet", type="warning")
        return
    buf = buffers[path]
    try:
        path.write_text(buf["content"], encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        ui.notify(f"Speichern fehlgeschlagen: {exc}", type="negative")
        return
    buf["saved"] = buf["content"]
    buf["dirty"] = False
    saved.text = f"Gespeichert {datetime.datetime.now():%H:%M:%S}"
    render_tabs()
    render_files()
    update_status()
    ui.notify(f"✓ {path.name}", type="positive")


def new_file():
    with ui.dialog() as d, ui.card().classes("bg-[#11111b] min-w-[320px]"):
        ui.label("Neue Datei").classes("text-base font-bold text-[#00d4aa]")
        name_in = ui.input("Dateiname (z. B. notiz.md)").classes("w-full")
        msg = ui.label("").classes("text-xs text-amber-400")

        def create():
            name = (name_in.value or "").strip()
            if not name:
                msg.text = "Name darf nicht leer sein."
                return
            p = ROOT / name
            if p.suffix not in EXT_LANG:
                msg.text = f"Endung muss eine von {', '.join(EXT_LANG)} sein."
                return
            if p.exists():
                msg.text = "Datei existiert bereits."
                return
            p.write_text("", encoding="utf-8")
            d.close()
            ui.notify(f"Neu: {p.name}", type="positive")
            open_file(p)

        with ui.row().classes("w-full justify-end gap-2 mt-2"):
            ui.button("Abbrechen", on_click=d.close).props("flat")
            ui.button("Anlegen", on_click=create).props("color=teal")
    d.open()


# --- 5-Dimensionen-Review -------------------------------------------------
REVIEW_CHECKS = [
    ("1 Evidenz/Quellen", r"(quelle|source|ref|http|doi|zitat)"),
    ("2 Logische Kette", r"(→|=>|daher|because|weil|therefore|deshalb|folgt)"),
    ("3 Alternativen", r"(alternativ|gegenargument|jedoch|stattdessen|abwägung)"),
    ("4 Implikationen", r"(implikation|folge|handlungsempfehl|nächst|next step)"),
    ("5 Risiken/Lücken", r"(risik|unsicher|lücke|tbd|todo|offen)"),
]


def score_review(text: str):
    """5-Dimensionen-Score über einen Text -> (score:int, hits:list[(name, ok)])."""
    hits = [(n, bool(re.search(p, text or "", re.I))) for n, p in REVIEW_CHECKS]
    return sum(ok for _, ok in hits), hits


def review():
    if not state["current"]:
        ui.notify("Keine Datei geöffnet", type="warning")
        return
    score, hits = score_review(editor.value or "")
    with ui.dialog() as d, ui.card().classes("bg-[#11111b] min-w-[340px]"):
        ui.label("5-Dimensionen-Review").classes("text-lg font-bold text-[#00d4aa]")
        ui.label(f"{state['current'].name} · {score}/5 Dimensionen abgedeckt") \
            .classes("text-xs text-[#94a3b8] mb-2")
        ui.linear_progress(value=score / 5, show_value=False).classes("mb-2") \
            .props("color=teal track-color=grey-9")
        for name, ok in hits:
            ui.label(f"{'✓' if ok else '○'} {name}").classes(
                f"text-sm {'text-emerald-400' if ok else 'text-amber-400'}")
        ui.button("OK", on_click=d.close).classes("mt-3").props("color=teal")
    d.open()


# --- Ausführen ------------------------------------------------------------
def _run_py(path: Path):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, str(path)], cwd=str(ROOT),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180, env=env,
    )


async def run_current():
    path = state["current"]
    if not path:
        ui.notify("Keine Datei geöffnet", type="warning")
        return
    if path.suffix != ".py":
        ui.notify("Ausführen nur für .py-Dateien", type="warning")
        return
    if buffers[path]["dirty"]:
        save()  # auf Platte schreiben, damit der aktuelle Stand läuft
    console_exp.open()
    console.clear()
    console.push(f"$ python {path.name}")
    try:
        result = await run.io_bound(_run_py, path)
    except subprocess.TimeoutExpired:
        console.push("[FEHLER] Zeitlimit (180 s) überschritten — abgebrochen.")
        ui.notify("Zeitlimit überschritten", type="negative")
        return
    except Exception as exc:  # noqa: BLE001
        console.push(f"[FEHLER] {exc}")
        ui.notify("Ausführung fehlgeschlagen", type="negative")
        return
    for line in (result.stdout or "").splitlines():
        console.push(line)
    for line in (result.stderr or "").splitlines():
        console.push(f"⚠ {line}")
    console.push(f"— Exit-Code {result.returncode} —")
    ui.notify("Lauf abgeschlossen" if result.returncode == 0 else
              f"Beendet mit Code {result.returncode}",
              type="positive" if result.returncode == 0 else "warning")


def bundle():
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    out = ROOT / f"Archiv_{stamp}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in ROOT.iterdir():
            if p.is_file() and not p.name.startswith("Archiv_"):
                z.write(p, p.name)
    ui.notify(f"→ {out.name}", type="positive")
    render_files()


# --- HEROIC Mainframe (QUBO-Solver, in-process) ---------------------------
def _solve_qubo(n: int, steps: int, submodular: bool):
    """Führt den integrierten Mainframe aus und fängt das Audit-Log (stdout) ab."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mf = hc.QUBOIntegrationCoreModule()
        Q = hc.make_Q(int(n), submodular=bool(submodular), scale=2.5)
        cfg = hc.QUBOSolverConfig(backend="simulated_annealing", steps=int(steps), T0=2.5)
        res = mf.execute_secure_run(Q, config=cfg)
    return res.solution.tolist(), float(res.energy), res.runtime_seconds, buf.getvalue()


def _solve_qubo_on(Q, steps: int):
    """Wie _solve_qubo, aber auditiert eine VORGEGEBENE Matrix Q (nicht neu gewürfelt),
    damit Stufe 4 dieselbe Probleminstanz prüft, die Stufe 2 gelöst hat."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mf = hc.QUBOIntegrationCoreModule()
        cfg = hc.QUBOSolverConfig(backend="simulated_annealing", steps=int(steps), T0=2.5)
        res = mf.execute_secure_run(np.asarray(Q, dtype=np.float64), config=cfg)
    return res.solution.tolist(), float(res.energy), res.runtime_seconds, buf.getvalue()


def open_mainframe():
    with ui.dialog() as d, ui.card().classes("bg-[#11111b] min-w-[480px]"):
        ui.label("HEROIC Mainframe · QUBO-Solver").classes("text-lg font-bold text-[#00d4aa]")
        ui.label("Simulated Annealing über die integrierte Engine (engine/mainframe.py)") \
            .classes("text-xs text-[#94a3b8]")
        with ui.row().classes("w-full gap-3 mt-2 items-center"):
            n_in = ui.number("Dimension n", value=12, min=2, max=200, format="%d") \
                .props("dense dark").classes("w-28")
            steps_in = ui.number("Steps", value=8000, min=100, max=200000, format="%d") \
                .props("dense dark").classes("w-36")
            sub_in = ui.checkbox("submodular").classes("self-center")
        result_lbl = ui.label("").classes(
            "text-sm text-[#e2e8f0] whitespace-pre-wrap font-mono mt-1")
        log = ui.log(max_lines=200).classes(
            "w-full h-40 bg-[#05050a] text-[#cbd5e1] text-xs rounded p-2 mt-2")

        async def solve():
            btn.props("loading")
            result_lbl.text = "Rechne… (erster Lauf kompiliert den Numba-Kernel)"
            log.clear()
            try:
                sol, energy, rt, audit = await run.io_bound(
                    _solve_qubo, n_in.value, steps_in.value, sub_in.value)
            except Exception as exc:  # noqa: BLE001
                result_lbl.text = f"Fehler: {exc}"
                btn.props(remove="loading")
                ui.notify("Solver-Fehler", type="negative")
                return
            for line in audit.splitlines():
                log.push(line)
            result_lbl.text = (f"x      = {sol}\n"
                               f"E_min  = {energy:.6f}\n"
                               f"Laufzeit = {rt * 1000:.1f} ms")
            btn.props(remove="loading")
            ui.notify("QUBO gelöst", type="positive")

        with ui.row().classes("w-full justify-end gap-2 mt-3"):
            ui.button("Schließen", on_click=d.close).props("flat")
            btn = ui.button("Lösen", on_click=solve).props("color=teal")
    d.open()


def update_metrics():
    try:
        import psutil
        c = psutil.cpu_percent()
        r = psutil.virtual_memory().percent
        metrics.text = f"CPU {c:.0f}%  ·  RAM {r:.0f}%"
        if metrics_chart is not None:          # Chart evtl. noch nicht gebaut
            cpu_hist.append(c)
            ram_hist.append(r)
            metrics_chart.options["series"][0]["data"] = list(cpu_hist)
            metrics_chart.options["series"][1]["data"] = list(ram_hist)
            metrics_chart.update()
    except Exception:  # noqa: BLE001
        metrics.text = ""


# --- Renderer -------------------------------------------------------------
def render_tabs():
    tab_row.clear()
    with tab_row:
        if not opened:
            ui.label("Keine Datei geöffnet").classes("text-xs text-[#94a3b8] px-2 self-center")
        for p in opened:
            active = p == state["current"]
            dirty = buffers.get(p, {}).get("dirty")
            bg = "bg-[#1e1e2e]" if active else "bg-transparent"
            with ui.row().classes(
                    f"items-center gap-1 pl-3 pr-1 h-8 rounded-t {bg} cursor-pointer flex-nowrap") \
                    .on("click", lambda q=p: activate(q)):
                ui.label(f"{'● ' if dirty else ''}{p.name}").classes(
                    f"text-xs {'text-[#00d4aa]' if active else 'text-[#94a3b8]'} whitespace-nowrap")
                ui.icon("close", size="14px").classes("text-[#94a3b8] hover:text-red-400") \
                    .on("click.stop", lambda q=p: close_file(q))


def render_files():
    file_col.clear()
    flt = state["filter"].lower()
    with file_col:
        shown = [p for p in list_files() if flt in p.name.lower()]
        if not shown:
            ui.label("— keine Treffer —").classes("text-xs text-[#94a3b8] px-2")
        for p in shown:
            is_open = p in opened
            dirty = buffers.get(p, {}).get("dirty")
            active = p == state["current"]
            with ui.row().classes(
                    f"items-center w-full gap-1 px-2 py-1 rounded cursor-pointer "
                    f"{'bg-[#1e1e2e]' if active else 'hover:bg-[#161622]'}") \
                    .on("click", lambda q=p: open_file(q)):
                ui.label("●" if dirty else ("○" if is_open else " ")).classes(
                    f"text-[10px] w-3 {'text-[#00d4aa]' if dirty else 'text-[#475569]'}")
                ui.label(p.name).classes(
                    f"text-xs {'text-[#e2e8f0]' if active else 'text-[#94a3b8]'} truncate")


def update_status():
    path = state["current"]
    if not path:
        status.text = "Bereit"
        return
    buf = buffers[path]
    lang = EXT_LANG.get(path.suffix) or "Text"
    lines = buf["content"].count("\n") + 1
    flag = "● geändert" if buf["dirty"] else "gespeichert"
    status.text = f"{path.name}  ·  {lang}  ·  {lines} Zeilen  ·  {flag}"


# =========================================================================
# Charts (ui.echart / ECharts — keine zusätzliche Abhängigkeit)
# =========================================================================
_AXIS = "#475569"
_GRID = "#1e1e2e"
_MUTED = "#94a3b8"


def build_convergence_chart():
    return ui.echart({
        "backgroundColor": "transparent", "animation": False,
        "title": {"text": "QUBO Energie-Konvergenz", "textStyle": {"color": "#e2e8f0", "fontSize": 13}},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24, "type": "scroll", "data": [], "textStyle": {"color": _MUTED}},
        "grid": {"left": 56, "right": 24, "top": 64, "bottom": 40},
        "xAxis": {"type": "value", "name": "Schritt", "nameTextStyle": {"color": _MUTED},
                  "axisLine": {"lineStyle": {"color": _AXIS}}, "axisLabel": {"color": _MUTED},
                  "splitLine": {"lineStyle": {"color": _GRID}}},
        "yAxis": {"type": "value", "name": "beste Energie", "scale": True, "nameTextStyle": {"color": _MUTED},
                  "axisLine": {"lineStyle": {"color": _AXIS}}, "axisLabel": {"color": _MUTED},
                  "splitLine": {"lineStyle": {"color": _GRID}}},
        "series": [],
    }).classes("w-full h-48")


def build_heatmap_chart():
    return ui.echart({
        "backgroundColor": "transparent", "animation": False,
        "title": {"text": "Q-Matrix Heatmap", "textStyle": {"color": "#e2e8f0", "fontSize": 13}},
        "tooltip": {"position": "top"},
        "grid": {"left": 48, "right": 24, "top": 48, "bottom": 56},
        "xAxis": {"type": "category", "data": [], "axisLabel": {"color": _MUTED, "fontSize": 9},
                  "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": [], "inverse": True, "axisLabel": {"color": _MUTED, "fontSize": 9},
                  "splitArea": {"show": True}},
        "visualMap": {"min": -1, "max": 1, "calculable": True, "orient": "horizontal",
                      "left": "center", "bottom": 0, "dimension": 2,
                      "textStyle": {"color": _MUTED},
                      "inRange": {"color": ["#1e3a8a", "#0d0d14", "#00d4aa"]}},
        "series": [{"type": "heatmap", "data": [],
                    "label": {"show": False, "color": "#e2e8f0", "fontSize": 9},
                    "emphasis": {"itemStyle": {"shadowBlur": 6, "shadowColor": "rgba(0,212,170,0.5)"}}}],
    }).classes("w-full h-64")


def build_metrics_chart():
    return ui.echart({
        "backgroundColor": "transparent", "animation": False,
        "title": {"text": "CPU / RAM Verlauf", "textStyle": {"color": "#e2e8f0", "fontSize": 13}},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24, "data": ["CPU", "RAM"], "textStyle": {"color": _MUTED}},
        "grid": {"left": 48, "right": 16, "top": 56, "bottom": 32},
        "xAxis": {"type": "category", "boundaryGap": False, "data": time_axis,
                  "axisLabel": {"color": _MUTED, "interval": 9}, "axisLine": {"lineStyle": {"color": _AXIS}}},
        "yAxis": {"type": "value", "min": 0, "max": 100, "axisLabel": {"color": _MUTED, "formatter": "{value}%"},
                  "splitLine": {"lineStyle": {"color": _GRID}}},
        "series": [
            {"name": "CPU", "type": "line", "smooth": True, "showSymbol": False,
             "areaStyle": {"opacity": 0.15}, "lineStyle": {"color": "#00d4aa"},
             "itemStyle": {"color": "#00d4aa"}, "data": list(cpu_hist)},
            {"name": "RAM", "type": "line", "smooth": True, "showSymbol": False,
             "areaStyle": {"opacity": 0.15}, "lineStyle": {"color": "#8b5cf6"},
             "itemStyle": {"color": "#8b5cf6"}, "data": list(ram_hist)},
        ],
    }).classes("w-full h-48")


def build_sweep_chart():
    return ui.echart({
        "backgroundColor": "transparent", "animation": False,
        "title": {"text": "Sweep · E_min & Laufzeit vs. Steps", "textStyle": {"color": "#e2e8f0", "fontSize": 13}},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24, "data": ["E_min", "Laufzeit (ms)"], "textStyle": {"color": _MUTED}},
        "grid": {"left": 56, "right": 56, "top": 56, "bottom": 32},
        "xAxis": {"type": "category", "data": [], "name": "Steps", "nameTextStyle": {"color": _MUTED},
                  "axisLabel": {"color": _MUTED}, "axisLine": {"lineStyle": {"color": _AXIS}}},
        "yAxis": [
            {"type": "value", "name": "E_min", "scale": True, "axisLabel": {"color": _MUTED},
             "splitLine": {"lineStyle": {"color": _GRID}}},
            {"type": "value", "name": "ms", "axisLabel": {"color": _MUTED}, "splitLine": {"show": False}},
        ],
        "series": [
            {"name": "E_min", "type": "line", "smooth": True, "itemStyle": {"color": "#00d4aa"}, "data": []},
            {"name": "Laufzeit (ms)", "type": "bar", "yAxisIndex": 1,
             "itemStyle": {"color": "#8b5cf6", "opacity": 0.6}, "data": []},
        ],
    }).classes("w-full h-48")


def set_convergence(chart, trace_steps, traces, best_restart):
    chart.options["legend"]["data"] = [f"Restart {i + 1}" for i in range(len(traces))]
    chart.options["series"] = [
        {"name": f"Restart {i + 1}", "type": "line", "showSymbol": False, "smooth": True,
         "lineStyle": {"width": 3 if i == best_restart else 1,
                       "color": PALETTE[i % len(PALETTE)],
                       "opacity": 1.0 if i == best_restart else 0.45},
         "data": [[int(s), float(e)] for s, e in zip(trace_steps, tr)]}
        for i, tr in enumerate(traces)]
    chart.update()


def set_heatmap(chart, M, title="Q-Matrix"):
    M = np.asarray(M, dtype=np.float64)
    n = M.shape[0]
    labels = [f"x{i}" for i in range(n)]
    data = [[j, i, round(float(M[i, j]), 4)] for i in range(n) for j in range(n)]
    vmax = float(max(abs(M.min()), abs(M.max()))) or 1.0
    chart.options["title"]["text"] = title
    chart.options["xAxis"]["data"] = labels
    chart.options["yAxis"]["data"] = labels
    chart.options["visualMap"]["min"] = -vmax
    chart.options["visualMap"]["max"] = vmax
    chart.options["series"][0]["data"] = data
    chart.options["series"][0]["label"]["show"] = n <= 16
    chart.update()


def set_sweep(chart, xs, emins, rts):
    chart.options["xAxis"]["data"] = [str(x) for x in xs]
    chart.options["series"][0]["data"] = [round(float(e), 3) for e in emins]
    chart.options["series"][1]["data"] = [round(float(t), 1) for t in rts]
    chart.update()


def build_surface3d_chart():
    """Live-3D-Surface der QUBO-Heuristik: x=Schritt, y=Restart, z=beste Energie.
    Die rechteckigen Konvergenz-Traces (n_restarts × n_samples) bilden direkt das Gitter."""
    return ui.echart({
        "backgroundColor": "transparent",
        "tooltip": {},
        "visualMap": {"show": False, "dimension": 2, "min": -1, "max": 1,
                      "inRange": {"color": ["#00d4aa", "#22d3ee", "#3b82f6",
                                            "#8b5cf6", "#ec4899", "#ef4444"]}},
        "xAxis3D": {"type": "value", "name": "Schritt", "nameTextStyle": {"color": _MUTED},
                    "axisLabel": {"color": _MUTED}},
        "yAxis3D": {"type": "value", "name": "Restart", "nameTextStyle": {"color": _MUTED},
                    "axisLabel": {"color": _MUTED}},
        "zAxis3D": {"type": "value", "name": "Energie", "nameTextStyle": {"color": _MUTED},
                    "axisLabel": {"color": _MUTED}},
        "grid3D": {"boxWidth": 100, "boxDepth": 80,
                   "axisLine": {"lineStyle": {"color": _AXIS}},
                   "splitLine": {"lineStyle": {"color": _GRID}},
                   "viewControl": {"autoRotate": True, "autoRotateSpeed": 8, "distance": 200},
                   "light": {"main": {"intensity": 1.2}, "ambient": {"intensity": 0.4}}},
        "series": [{"type": "surface", "shading": "color",
                    "wireframe": {"show": True, "lineStyle": {"opacity": 0.25}},
                    "data": []}],
    }, enable_3d=True).classes("w-full h-64")


def set_surface3d(chart, trace_steps, traces):
    if chart is None or not traces:
        return
    zmin = min(min(t) for t in traces)
    zmax = max(max(t) for t in traces)
    data = [[int(s), int(i), float(e)]
            for i, tr in enumerate(traces) for s, e in zip(trace_steps, tr)]
    chart.options["visualMap"]["min"] = zmin
    chart.options["visualMap"]["max"] = zmax
    chart.options["series"][0]["data"] = data
    chart.update()


# =========================================================================
# Pipelines (Workflow-Runner) — ein await pro Schritt, run.io_bound für CPU
# =========================================================================
def _set_detail(text):
    i = pipeline["current"]
    if 0 <= i < len(pipeline["steps"]):
        pipeline["steps"][i]["detail"] = text


def _uebersicht_text(res, n, steps, sub, audit):
    x = res["solution"].tolist() if hasattr(res["solution"], "tolist") else list(res["solution"])
    lines = [
        "# 00 Übersicht — Erkenntnis-Lauf",
        f"_Erzeugt: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}_", "",
        "## Konfiguration",
        f"- Dimension n: {n}", f"- Steps: {steps}", f"- submodular: {sub}",
        f"- Restarts: {res['n_restarts']} (Workers: {res['workers']})", "",
        "## Ergebnis",
        f"- E_min: {res['energy']:.6f} (bester Restart #{res['best_restart'] + 1})",
        f"- Energie-Spread: {min(res['energies']):.3f} … {max(res['energies']):.3f}",
        f"- Laufzeit (parallel): {res['runtime_seconds'] * 1000:.1f} ms",
        f"- Zustand x: {x}", "",
        "## Audit (Layer 1 + 3)",
        "```", (audit.strip() or "(kein Audit-Log)"), "```", "",
        "## Risiken / offene Punkte",
        "- Heuristik (Simulated Annealing) — kein Optimalitätsbeweis; alternativ exakte Solver für kleine n.",
        "- fastmath kann E in der letzten Stelle variieren; Vergleiche mit np.isclose.",
    ]
    return "\n".join(lines)


# --- Pipeline A: Erkenntnis-Lauf (HEROIC 5-Stufen 1:1) --------------------
async def _a_scoping():
    n, sub = int(pn_n.value), bool(pn_sub.value)
    Q = await run.io_bound(hc.make_Q, n, sub, 2.5)
    last_Q["Q"] = Q
    pipe_ctx.update(n=n, sub=sub)
    set_heatmap(heat_chart, Q, "Stufe 1 · Q-Struktur")
    _set_detail(f"n={n} · max|Q|={float(abs(Q).max()):.2f}")


async def _a_quellen():
    Q, steps, T0, r = last_Q["Q"], int(pn_steps.value), float(pn_T0.value), int(pn_restarts.value)
    res = await run.io_bound(hc.parallel_anneal, Q, steps, T0, r, 40, backend="auto")
    pipe_ctx["res"] = res
    _set_detail(f"{r} Restarts · E_min {res['energy']:.3f} · {res['runtime_seconds'] * 1000:.0f} ms "
                f"· {res.get('backend', 'numba')} / {res.get('workers', '?')} Kerne")


async def _a_evidenz():
    res = pipe_ctx["res"]
    set_convergence(conv_chart, res["trace_steps"], res["traces"], res["best_restart"])
    set_surface3d(surf3d_chart, res["trace_steps"], res["traces"])
    _set_detail(f"Spread {min(res['energies']):.2f} … {max(res['energies']):.2f}")


async def _a_kritik():
    Q, steps = last_Q["Q"], int(pn_steps.value)
    sol, energy, rt, audit = await run.io_bound(_solve_qubo_on, Q, steps)
    pipe_ctx["audit"] = audit
    for line in audit.splitlines():
        if line.strip():
            pipe_log.push(line)
    _set_detail("Audit Layer 1+3 passed (gleiche Q wie Stufe 2)")


async def _a_synthese():
    res, n = pipe_ctx["res"], pipe_ctx["n"]
    txt = _uebersicht_text(res, n, int(pn_steps.value), pipe_ctx["sub"], pipe_ctx.get("audit", ""))
    p = ROOT / "00_Uebersicht.md"
    p.write_text(txt, encoding="utf-8")
    # frischen Inhalt erzwingen, falls bereits offen
    buffers.pop(p, None)
    if p in opened:
        opened.remove(p)
    open_file(p)
    score, _ = score_review(txt)
    bundle()
    _set_detail(f"Review {score}/5 · Archiv erstellt")


# --- Pipeline B: Parallel-Solve & Visualize -------------------------------
async def _b_matrix():
    if pn_reuse.value and last_Q["Q"] is not None:
        pipe_ctx["Q"] = last_Q["Q"]
        _set_detail("Q wiederverwendet")
    else:
        n, sub = int(pn_n.value), bool(pn_sub.value)
        Q = await run.io_bound(hc.make_Q, n, sub, 2.5)
        last_Q["Q"] = Q
        pipe_ctx["Q"] = Q
        _set_detail(f"n={n} generiert")


async def _b_solve():
    Q, steps, T0, r = pipe_ctx["Q"], int(pn_steps.value), float(pn_T0.value), int(pn_restarts.value)
    res = await run.io_bound(hc.parallel_anneal, Q, steps, T0, r, 40, backend="auto")
    pipe_ctx["res"] = res
    _set_detail(f"E_min {res['energy']:.3f} · {res['runtime_seconds'] * 1000:.0f} ms "
                f"· {res.get('backend', 'numba')} / {res.get('workers', '?')} Kerne")


async def _b_viz():
    res, Q = pipe_ctx["res"], pipe_ctx["Q"]
    set_convergence(conv_chart, res["trace_steps"], res["traces"], res["best_restart"])
    set_surface3d(surf3d_chart, res["trace_steps"], res["traces"])
    x = np.asarray(res["solution"], dtype=np.float64)
    set_heatmap(heat_chart, np.outer(x, x) * Q, "Beitrags-Matrix xᵢ·xⱼ·Qᵢⱼ")
    _set_detail("Konvergenz + 3D-Surface + Beitrags-Heatmap aktualisiert")


async def _b_report():
    res = pipe_ctx["res"]
    note = " ⚠ Meta-Analyse: divergent" if res["energy"] > 1e6 else ""
    x = res["solution"].tolist() if hasattr(res["solution"], "tolist") else res["solution"]
    pipe_log.push(f"best x = {x}")
    pipe_log.push(f"E_min = {res['energy']:.4f} · Restarts {res['n_restarts']} · "
                  f"{res['runtime_seconds'] * 1000:.0f} ms{note}")
    _set_detail(f"E_min {res['energy']:.3f}{note}")


# --- Pipeline C: Active-File Review & Archive -----------------------------
async def _c_review():
    score, hits = score_review(editor.value or "")
    pipe_ctx["score"] = score
    for name, ok in hits:
        pipe_log.push(f"{'✓' if ok else '○'} {name}")
    _set_detail(f"Review {score}/5")


async def _c_gate():
    score = pipe_ctx.get("score", 0)
    if score < 3:
        _set_detail(f"Gate nicht bestanden ({score}/5)")
        raise RuntimeError(f"Review-Gate: nur {score}/5 — Datei zuerst ergänzen")
    _set_detail(f"Gate bestanden ({score}/5)")


async def _c_archive():
    if state["current"]:
        save()
    bundle()
    _set_detail("gespeichert + archiviert")


# --- Pipeline D: Sweep & Compare ------------------------------------------
async def _d_setup():
    n, sub = int(pn_n.value), bool(pn_sub.value)
    Q = await run.io_bound(hc.make_Q, n, sub, 2.5)
    last_Q["Q"] = Q
    pipe_ctx["Q"] = Q
    _set_detail(f"feste Q (n={n})")


async def _d_sweep():
    Q, T0, r = pipe_ctx["Q"], float(pn_T0.value), int(pn_restarts.value)
    sweep = [2000, 8000, 32000]
    emins, rts = [], []
    for k, s in enumerate(sweep):
        res = await run.io_bound(hc.parallel_anneal, Q, s, T0, r, 30, backend="auto")
        emins.append(res["energy"])
        rts.append(res["runtime_seconds"] * 1000)
        progress.value = (k + 1) / len(sweep)
        pipe_log.push(f"steps={s}: E_min {res['energy']:.3f} · {rts[-1]:.0f} ms")
    pipe_ctx["sweep"] = (sweep, emins, rts)
    _set_detail("Sweep abgeschlossen")


async def _d_viz():
    sweep, emins, rts = pipe_ctx["sweep"]
    set_sweep(sweep_chart, sweep, emins, rts)
    best = min(range(len(emins)), key=lambda i: emins[i])
    _set_detail(f"bestes E bei steps={sweep[best]}")


PIPELINES = {
    "Erkenntnis-Lauf (5 Stufen)": [
        ("Stufe 1 · Scoping & Q-Matrix", _a_scoping),
        ("Stufe 2 · Quellen (Parallel-Solve)", _a_quellen),
        ("Stufe 3 · Evidenz & Muster (Konvergenz)", _a_evidenz),
        ("Stufe 4 · Kritik & Stress-Test (Audit)", _a_kritik),
        ("Stufe 5 · Synthese & Archiv", _a_synthese),
    ],
    "Parallel-Solve & Visualize": [
        ("Matrix erzeugen/wiederverwenden", _b_matrix),
        ("Parallel-Solve (alle Kerne)", _b_solve),
        ("Visualisieren (Konvergenz + Heatmap)", _b_viz),
        ("Ergebnis-Report", _b_report),
    ],
    "Active-File Review & Archive": [
        ("5-Dim-Review der aktiven Datei", _c_review),
        ("Qualitäts-Gate (≥3/5)", _c_gate),
        ("Speichern & Archivieren", _c_archive),
    ],
    "Sweep & Compare": [
        ("Feste Q erzeugen", _d_setup),
        ("Steps-Sweep [2k/8k/32k]", _d_sweep),
        ("Vergleich visualisieren", _d_viz),
    ],
}


async def run_pipeline(name):
    if not name or name not in PIPELINES:
        ui.notify("Keine Pipeline gewählt", type="warning")
        return
    if pipeline["running"]:
        ui.notify("Pipeline läuft bereits", type="warning")
        return
    steps = PIPELINES[name]
    pipeline.update(name=name, running=True, cancel=False, current=-1,
                    steps=[{"label": lbl, "status": "pending", "detail": ""} for lbl, _ in steps])
    pipe_ctx.clear()
    progress.value = 0.0
    pipeline_panel.open()
    render_steps()
    for i, (lbl, fn) in enumerate(steps):
        if pipeline["cancel"]:
            for s in pipeline["steps"][i:]:
                s["status"] = "skipped"
            render_steps()
            break
        pipeline["current"] = i
        pipeline["steps"][i]["status"] = "running"
        render_steps()
        try:
            await fn()
            pipeline["steps"][i]["status"] = "ok"
        except Exception as exc:  # noqa: BLE001
            pipeline["steps"][i]["status"] = "fail"
            if not pipeline["steps"][i]["detail"]:
                pipeline["steps"][i]["detail"] = str(exc)
            for s in pipeline["steps"][i + 1:]:
                s["status"] = "skipped"
            render_steps()
            ui.notify(f"Pipeline gestoppt: {exc}", type="negative")
            break
        progress.value = sum(s["status"] in ("ok", "skipped") for s in pipeline["steps"]) / max(len(steps), 1)
        render_steps()
    pipeline["running"] = False
    progress.value = sum(s["status"] in ("ok", "skipped") for s in pipeline["steps"]) / max(len(steps), 1)
    if not pipeline["cancel"] and all(s["status"] == "ok" for s in pipeline["steps"]):
        ui.notify(f"Pipeline '{name}' abgeschlossen", type="positive")


_STEP_ICONS = {
    "pending": ("radio_button_unchecked", "text-[#475569]", ""),
    "running": ("autorenew", "text-amber-400", "animate-spin"),
    "ok": ("check_circle", "text-emerald-400", ""),
    "fail": ("error", "text-red-400", ""),
    "skipped": ("remove_circle", "text-slate-500", ""),
}


def render_steps():
    steps_col.clear()
    with steps_col:
        if not pipeline["steps"]:
            ui.label("Keine Pipeline gestartet").classes("text-xs text-[#94a3b8]")
            return
        for s in pipeline["steps"]:
            ic, col, extra = _STEP_ICONS.get(s["status"], _STEP_ICONS["pending"])
            with ui.row().classes("items-center gap-2 w-full flex-nowrap"):
                ui.icon(ic, size="18px").classes(f"{col} {extra}")
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(s["label"]).classes("text-xs text-[#e2e8f0] truncate")
                    if s["detail"]:
                        ui.label(s["detail"]).classes("text-[10px] text-[#94a3b8] truncate")


# =========================================================================
# Live-Hauptagent (agents.py) — "über die Schulter sehen" + Chat-I/O
# =========================================================================
AGENT_BUS = ag.MessageBus()
agent_state = {"supervisor": None, "running": False, "seen": 0, "started": 0.0}
chat_messages = []          # [{"role": "user"|"agent"|"system", "text": str}]
agent_view = {"open": True}


def _cpu_task_executor(agent, task):
    """Echter CPU-Task statt sleep: ein kleiner QUBO-Solve über den nogil-Kernel.

    Der Kernel gibt den GIL frei, daher lasten die Worker-Threads die Kerne wirklich
    aus — so wird Hyperthreading im Schwarm tatsächlich aktiv (und im Monitor sichtbar)."""
    seed = int(task.payload.get("i", 0)) + 1
    n = 256
    r = np.random.default_rng(seed)
    M = r.normal(0, 2.0, (n, n))
    Qf = np.ascontiguousarray(((M + M.T) / 2.0).astype(np.float64))
    _x, e, _t = hc._anneal_one(Qf, 150_000, 2.0, n, seed, 4)
    return {"worker": agent.name, "task": task.name, "energy": float(e)}


def _run_agent_batch(prompt: str, n_tasks: int):
    """Läuft auf einem Worker-Thread: startet den Hauptagenten (Supervisor) auf dem
    persistenten Bus, reiht n Teilaufgaben ein, wartet bis abgearbeitet und liefert den
    Abschlussreport. Der Live-Monitor liest derweil Bus + summarize().

    Die Worker führen echte CPU-Arbeit aus (_cpu_task_executor) → Mehrkern-Last."""
    tq = ag.TaskQueue()
    sup = ag.Supervisor(name="hauptagent", bus=AGENT_BUS, task_queue=tq,
                        executor=_cpu_task_executor,
                        min_workers=1, max_workers=os.cpu_count() or 4,
                        scale_up_threshold=3, idle_rounds_before_fire=3,
                        tick_interval=0.03, worker_work_seconds=0.0, heartbeat_interval=0.12)
    label = (prompt[:24] + "…") if len(prompt) > 24 else prompt
    for i in range(n_tasks):
        tq.put(ag.Task(name=f"{label}#{i + 1}", payload={"i": i, "prompt": prompt}))
    agent_state["supervisor"] = sup
    agent_state["started"] = time.time()
    sup.start()
    sup.join(timeout=30.0)
    sup.shutdown(timeout=2.0)
    return sup.report()


async def chat_send():
    text = (chat_in.value or "").strip()
    if not text:
        return
    chat_in.value = ""
    chat_messages.append({"role": "user", "text": text})
    render_chat()
    if agent_state["running"]:
        chat_messages.append({"role": "system", "text": "Hauptagent ist beschäftigt — bitte warten."})
        render_chat()
        return
    m = re.search(r"\d+", text)
    n_tasks = max(1, min(60, int(m.group()) if m else 12))
    agent_state["running"] = True
    chat_messages.append({"role": "agent",
                          "text": f"Verteile {n_tasks} Teilaufgaben an den Schwarm — live im Monitor zu sehen."})
    render_chat()
    try:
        report = await run.io_bound(_run_agent_batch, text, n_tasks)
    except Exception as exc:  # noqa: BLE001
        chat_messages.append({"role": "system", "text": f"Fehler: {exc}"})
    else:
        chat_messages.append({"role": "agent",
                              "text": (f"Fertig: {report['tasks_done']} Tasks erledigt · Peak "
                                       f"{report['peak_workforce']} Worker · {report['hires']} eingestellt / "
                                       f"{report['fires']} entlassen.")})
    finally:
        agent_state["running"] = False
    render_chat()


async def auto_tick():
    """Selbstständige Zuordnung: ist 'Auto-Hintergrund' aktiv und der Schwarm frei,
    ordnet der Hauptagent sich eigenständig eine kleine Charge echter Aufgaben zu."""
    if not auto_state["on"] or agent_state["running"]:
        return
    auto_state["rounds"] += 1
    n = 6
    chat_messages.append({"role": "system",
                          "text": f"Auto-Runde {auto_state['rounds']}: {n} Hintergrundaufgaben selbst zugeordnet."})
    render_chat()
    agent_state["running"] = True
    try:
        await run.io_bound(_run_agent_batch, f"auto r{auto_state['rounds']}", n)
    except Exception:  # noqa: BLE001
        pass
    finally:
        agent_state["running"] = False


def render_chat():
    chat_col.clear()
    with chat_col:
        if not chat_messages:
            ui.label('Gib dem Hauptagenten eine Aufgabe (z. B. "verarbeite 20 module").') \
                .classes("text-xs text-[#475569] italic")
        for m in chat_messages[-120:]:
            role = m["role"]
            if role == "user":
                with ui.row().classes("w-full justify-end"):
                    ui.label(m["text"]).classes(
                        "text-xs bg-[#0e2e2a] text-[#d1fae5] rounded-lg px-3 py-1 "
                        "max-w-[85%] whitespace-pre-wrap")
            elif role == "agent":
                with ui.row().classes("w-full justify-start"):
                    ui.label(m["text"]).classes(
                        "text-xs bg-[#1e1e2e] text-[#e2e8f0] rounded-lg px-3 py-1 "
                        "max-w-[85%] whitespace-pre-wrap")
            else:
                with ui.row().classes("w-full justify-center"):
                    ui.label(m["text"]).classes("text-[10px] text-amber-400 italic")
    try:
        chat_scroll.scroll_to(percent=1.0)
    except Exception:  # noqa: BLE001
        pass


_WSTATE_COL = {"running": "text-emerald-400", "busy": "text-amber-400",
               "stopping": "text-slate-500", "created": "text-[#475569]"}


def refresh_live():
    """Pollt den Bus: Hauptagent-Monitor (Belegschaft + Ereignisse) und Pipeline-Uhr."""
    # Live-Kern-Auslastung (zeigt, dass Hyperthreading wirklich greift)
    try:
        import psutil
        per = psutil.cpu_percent(percpu=True)
        active = sum(1 for c in per if c > 40.0)
        ht_lbl.text = f"⚡ Kerne aktiv: {active}/{len(per)}"
        ht_lbl.classes(replace="text-[11px] font-mono " +
                       ("text-emerald-400" if active >= 3 else "text-[#94a3b8]"))
    except Exception:  # noqa: BLE001
        pass
    sup = agent_state["supervisor"]
    summ = None
    if sup is not None:
        try:
            summ = sup.summarize()
        except Exception:  # noqa: BLE001
            summ = None
    # Kopfzeile des Monitors
    if agent_state["running"] and summ:
        el = time.time() - agent_state["started"]
        mon_metrics.text = (f"● aktiv · Worker {summ['workers']} · Queue {summ['queue_depth']} · "
                            f"offen {summ['outstanding']} · erledigt {summ['worker_tasks_done']} · {el:.1f}s")
        mon_metrics.classes(replace="text-[11px] font-mono text-emerald-400")
    elif sup is not None:
        rep = sup.report()
        mon_metrics.text = (f"○ idle · letzte Runde: {rep['tasks_done']} Tasks · Peak "
                            f"{rep['peak_workforce']} · {rep['hires']} hire / {rep['fires']} fire")
        mon_metrics.classes(replace="text-[11px] font-mono text-[#94a3b8]")
    else:
        mon_metrics.text = "○ Hauptagent bereit — noch keine Aufgabe."
        mon_metrics.classes(replace="text-[11px] font-mono text-[#94a3b8]")
    # Belegschaft (Roster)
    roster_col.clear()
    with roster_col:
        per = (summ.get("per_worker") if (summ and agent_state["running"]) else []) or []
        if not per:
            ui.label("— keine aktiven Worker —").classes("text-[10px] text-[#475569]")
        for w in per:
            with ui.row().classes("items-center gap-2 w-full flex-nowrap"):
                ui.icon("circle", size="9px").classes(_WSTATE_COL.get(w.get("state"), "text-[#475569]"))
                ui.label(w["name"]).classes("text-[11px] text-[#e2e8f0] truncate flex-1")
                ui.label(f"⊕{w['backlog']}  ✓{w['done']}").classes("text-[10px] text-[#94a3b8] font-mono")
    # Ereignis-Stream (nur Roster + Task-Done; Heartbeats werden übersprungen)
    hist = AGENT_BUS.history()
    if agent_state["seen"] > len(hist):
        agent_state["seen"] = 0
    for msg in hist[agent_state["seen"]:]:
        if msg.topic == "roster":
            ev = msg.payload.get("event")
            mon_log.push(f"{'＋ hire ' if ev == 'hire' else '－ fire '} {msg.payload.get('child')}")
        elif msg.topic == "task_done":
            mon_log.push(f"✓ {msg.payload.get('worker')} → {msg.payload.get('task_id')}")
    agent_state["seen"] = len(hist)
    # Pipeline-Live-Uhr
    if pipeline.get("running"):
        cur = pipeline.get("current", -1)
        lbl = pipeline["steps"][cur]["label"] if 0 <= cur < len(pipeline["steps"]) else "…"
        pipe_status.text = f"● läuft · Schritt {cur + 1}/{len(pipeline['steps'])} · {lbl}"
        pipe_status.classes(replace="text-[11px] text-emerald-400")
    elif pipeline.get("steps"):
        ok = sum(s["status"] == "ok" for s in pipeline["steps"])
        pipe_status.text = f"○ fertig · {ok}/{len(pipeline['steps'])} Schritte ok"
        pipe_status.classes(replace="text-[11px] text-[#94a3b8]")
    else:
        pipe_status.text = "○ bereit"
        pipe_status.classes(replace="text-[11px] text-[#94a3b8]")


def toggle_agent_panel():
    agent_view["open"] = not agent_view["open"]
    edsplit.value = 64 if agent_view["open"] else 100


# =========================================================================
# Layout
# =========================================================================
ui.colors(primary="#00d4aa")
ui.dark_mode(True)
ui.query("body").classes("bg-[#0a0a0f] text-[#e2e8f0]")
ui.add_head_html("""
<style>
  .q-btn { text-transform: none; }
  .nicegui-log { font-family: ui-monospace, 'Cascadia Code', Consolas, monospace; line-height: 1.35; }
  /* schlanke, dunkle Scrollbars für ein ruhigeres Layout */
  *::-webkit-scrollbar { width: 8px; height: 8px; }
  *::-webkit-scrollbar-thumb { background: #1e1e2e; border-radius: 8px; }
  *::-webkit-scrollbar-thumb:hover { background: #2a2a3e; }
  *::-webkit-scrollbar-track { background: transparent; }
  /* Tabs & Eingaben kompakter und konsistent */
  .q-tab { text-transform: none; min-height: 32px; }
  .q-field--dense .q-field__control { height: 34px; }
  .q-expansion-item__container .q-item { min-height: 40px; }
  body { -webkit-font-smoothing: antialiased; }
</style>
""")

with ui.column().classes("w-full h-screen flex-nowrap gap-0 p-0"):
    # Kopfzeile
    with ui.row().classes("w-full items-center gap-3 px-4 h-12 bg-[#0d0d14] "
                          "border-b border-[#1e1e2e] flex-nowrap"):
        ui.label("Fusion Hero OS").classes("text-base font-bold text-[#00d4aa]")
        ui.label("GUI + IDE · v2.2").classes("text-xs text-[#94a3b8]")
        ui.space()
        metrics = ui.label("").classes("text-xs text-[#94a3b8] font-mono mr-1")
        ui.button(icon="smart_toy", on_click=lambda: toggle_agent_panel()) \
            .props("flat color=teal").tooltip("Hauptagent-Panel ein/aus")
        ui.button(icon="account_tree", on_click=lambda: pipeline_panel.open()) \
            .props("flat color=teal").tooltip("Pipelines-Panel öffnen")
        ui.button(icon="memory", on_click=open_mainframe).props("flat color=purple") \
            .tooltip("HEROIC Mainframe · QUBO-Solver")
        ui.button(icon="save", on_click=save).props("flat color=teal") \
            .tooltip("Speichern")
        ui.button(icon="play_arrow", on_click=run_current).props("flat color=green") \
            .tooltip("Aktuelle .py ausführen")
        ui.button(icon="fact_check", on_click=review).props("flat color=cyan") \
            .tooltip("5-Dimensionen-Review")
        ui.button(icon="note_add", on_click=new_file).props("flat color=teal") \
            .tooltip("Neue Datei")
        ui.button(icon="archive", on_click=bundle).props("flat color=orange") \
            .tooltip("Alles bündeln (ZIP)")

    # Hauptbereich: Sidebar | Editor
    with ui.splitter(value=22, limits=(14, 45)).classes("w-full") \
            .style("flex:1 1 0; min-height:0") as split:
        with split.before:
            with ui.column().classes("h-full w-full p-3 gap-2 bg-[#0a0a0f]"):
                filter_in = ui.input(placeholder="Dateien filtern…") \
                    .props("dense dark clearable").classes("w-full text-xs")
                filter_in.on_value_change(
                    lambda e: (state.update(filter=e.value or ""), render_files()))
                ui.label("Dateien").classes("text-xs font-bold text-[#94a3b8] mt-1")
                file_col = ui.column().classes("w-full gap-0 overflow-auto").style("flex:1 1 0")
                saved = ui.label("Noch nicht gespeichert").classes(
                    "text-xs text-[#94a3b8] mt-auto")

        with split.after:
            # Modulare Aufteilung: Editor | Hauptagent-Panel (über die Schulter)
            with ui.splitter(value=64, limits=(35, 100)).classes("w-full h-full") \
                    .style("min-height:0") as edsplit:
                with edsplit.before:
                    with ui.column().classes("h-full w-full gap-0 min-w-0"):
                        tab_row = ui.row().classes(
                            "w-full items-end gap-1 px-2 pt-2 bg-[#0d0d14] "
                            "border-b border-[#1e1e2e] flex-nowrap overflow-auto")
                        editor = ui.codemirror(value="", language="Markdown", theme="dracula",
                                               on_change=on_edit) \
                            .classes("w-full").style("flex:1 1 0; min-height:0")
                        status = ui.label("Bereit").classes(
                            "text-xs text-[#94a3b8] px-3 py-1 bg-[#0d0d14] border-t border-[#1e1e2e]")
                with edsplit.after:
                    with ui.column().classes("h-full w-full gap-0 min-w-0 bg-[#0a0a0f] "
                                             "border-l border-[#1e1e2e]"):
                        with ui.tabs().props("dense").classes("w-full bg-[#0d0d14]") as agent_tabs:
                            ui.tab("Monitor", icon="visibility")
                            ui.tab("Chat", icon="forum")
                        with ui.tab_panels(agent_tabs, value="Monitor") \
                                .classes("w-full").style("flex:1 1 0; min-height:0"):
                            with ui.tab_panel("Monitor"):
                                with ui.column().classes("h-full w-full gap-1"):
                                    ui.label("Hauptagent — live").classes(
                                        "text-xs font-bold text-[#00d4aa]")
                                    mon_metrics = ui.label("○ Hauptagent bereit") \
                                        .classes("text-[11px] font-mono text-[#94a3b8]")
                                    ht_lbl = ui.label("⚡ Kerne: —").classes(
                                        "text-[11px] font-mono text-[#94a3b8]")
                                    ui.checkbox("Auto-Hintergrundaufgaben",
                                                on_change=lambda e: auto_state.update(on=bool(e.value))) \
                                        .props("dense").classes("text-[11px]")
                                    ui.label("BELEGSCHAFT").classes(
                                        "text-[10px] font-bold text-[#475569] tracking-wider mt-1")
                                    roster_col = ui.column().classes("w-full gap-0")
                                    ui.label("EREIGNISSE").classes(
                                        "text-[10px] font-bold text-[#475569] tracking-wider mt-1")
                                    mon_log = ui.log(max_lines=500).classes(
                                        "w-full bg-[#05050a] text-[#cbd5e1] text-[11px] rounded p-2") \
                                        .style("flex:1 1 0; min-height:80px")
                            with ui.tab_panel("Chat"):
                                with ui.column().classes("h-full w-full gap-1"):
                                    chat_scroll = ui.scroll_area().classes("w-full") \
                                        .style("flex:1 1 0; min-height:120px")
                                    with chat_scroll:
                                        chat_col = ui.column().classes("w-full gap-1")
                                    with ui.row().classes("w-full gap-1 flex-nowrap items-center"):
                                        chat_in = ui.input(placeholder="Aufgabe an den Hauptagenten…") \
                                            .props("dense dark").classes("flex-1")
                                        chat_in.on("keydown.enter", lambda: chat_send())
                                        ui.button(icon="send", on_click=lambda: chat_send()) \
                                            .props("round dense color=teal")

    # Konsole (einklappbar)
    with ui.expansion("Konsole / Ausgabe", icon="terminal", value=False) \
            .classes("w-full bg-[#0d0d14] border-t border-[#1e1e2e]") as console_exp:
        console = ui.log(max_lines=2000).classes(
            "w-full h-48 bg-[#05050a] text-[#cbd5e1] text-xs rounded p-2")

    # Pipelines (Workflow-Runner)
    with ui.expansion("Pipelines", icon="account_tree", value=False) \
            .classes("w-full bg-[#0d0d14] border-t border-[#1e1e2e]") as pipeline_panel:
        with ui.column().classes("w-full p-2 gap-2"):
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                pipe_sel = ui.select(list(PIPELINES), value=next(iter(PIPELINES)), label="Pipeline") \
                    .props("dense dark options-dense").classes("w-72")
                ui.button("Start", icon="play_arrow",
                          on_click=lambda: run_pipeline(pipe_sel.value)).props("color=teal")
                ui.button("Stop", icon="stop",
                          on_click=lambda: pipeline.update(cancel=True)).props("flat color=red")
                ui.label("Abbruch greift zwischen Schritten (laufender Solve läuft aus).") \
                    .classes("text-[10px] text-[#475569] self-center")
            with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                pn_n = ui.number("n", value=12, min=2, max=400, format="%d").props("dense dark").classes("w-20")
                pn_steps = ui.number("Steps", value=8000, min=100, max=500000, format="%d") \
                    .props("dense dark").classes("w-28")
                pn_T0 = ui.number("T0", value=2.5, min=0.1, max=10, step=0.1, format="%.1f") \
                    .props("dense dark").classes("w-20")
                pn_restarts = ui.number("Restarts", value=os.cpu_count() or 12, min=1, max=64, format="%d") \
                    .props("dense dark").classes("w-24")
                pn_sub = ui.checkbox("submodular").classes("self-center")
                pn_reuse = ui.checkbox("Q wiederverwenden").classes("self-center")
            progress = ui.linear_progress(value=0.0, show_value=False) \
                .props("color=teal track-color=grey-9").classes("w-full")
            pipe_status = ui.label("○ bereit").classes("text-[11px] text-[#94a3b8]")
            with ui.row().classes("w-full gap-3 flex-nowrap items-stretch").style("min-height:0"):
                with ui.column().classes("gap-1").style("flex:0 0 36%; min-width:0"):
                    ui.label("Schritte").classes("text-xs font-bold text-[#94a3b8]")
                    steps_col = ui.column().classes("w-full gap-1")
                    pipe_log = ui.log(max_lines=2000).classes(
                        "w-full h-28 bg-[#05050a] text-[#cbd5e1] text-xs rounded p-2 mt-1")
                with ui.column().classes("gap-2 overflow-auto").style("flex:1 1 0; min-width:0; max-height:62vh"):
                    conv_chart = build_convergence_chart()
                    surf3d_chart = build_surface3d_chart()
                    heat_chart = build_heatmap_chart()
                    sweep_chart = build_sweep_chart()
                    metrics_chart = build_metrics_chart()


async def _warmup():
    try:
        await run.io_bound(hc.warmup_kernels)
    except Exception:  # noqa: BLE001
        pass

# Initialer Render + Live-Metriken + JIT-Warmup
render_tabs()
render_files()
render_steps()
render_chat()
refresh_live()
update_metrics()
ui.timer(2.0, update_metrics)
ui.timer(0.3, refresh_live)       # Hauptagent-Monitor + Pipeline-Uhr live
ui.timer(8.0, auto_tick)          # autonome Hintergrundaufgaben (wenn aktiviert)
ui.timer(0.1, _warmup, once=True)

if __name__ in {"__main__", "__mp_main__"}:
    # Port per Env übersteuerbar: 8080 ist auf diesem System oft schon belegt
    # (Monorepo-Workspace-GUI); 8181 als kollisionsfreier Default.
    ui.run(port=int(os.environ.get("FUSION_GUI_PORT", "8181")),
           title="Fusion Hero OS", dark=True, reload=False)
