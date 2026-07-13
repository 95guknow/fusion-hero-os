# -*- coding: utf-8 -*-
"""
Fusion Era Design — Aussehen 2026, Effizienz ~1996.
Ein Token-Set, zwei Oberflächen (Workspace + Monitor), keine CDN-Fonts, kein Blur.
"""
from __future__ import annotations

ERA_VISUAL = "2026"
ERA_EFFICIENCY = "1996-core"
THEME_VERSION = "2026.1"

# Polling — wenig Traffic, Pulse/Delta-first (wie frühe Terminals, aber smart)
POLL_PULSE_SEC = 6.0
POLL_JOBS_SEC = 5.0
POLL_METRICS_SEC = 4.0
POLL_IDLE_MULT = 2.0  # verdoppelt wenn Tab/Seite hidden

_CSS_TOKENS = """
:root{
  --fusion-bg:#020208;--fusion-surface:#0a0a12;--fusion-elevated:#101018;
  --fusion-accent:#00ffd5;--fusion-accent2:#a855f7;--fusion-glow:rgba(0,255,213,.22);
  --fusion-text:#e4eaf4;--fusion-muted:#7a8aa3;
  --shadow-3d:0 10px 24px rgba(0,0,0,.45);
  --shadow-btn:0 3px 0 #064a3f;
  --fusion-radius-lg:16px;--fusion-radius-md:12px;--fusion-radius-sm:8px;
  --fusion-mono:ui-monospace,'Cascadia Mono','Consolas',monospace;
  --fusion-sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}
}
"""

_CSS_ERA = """
.fusion-era-tag{
  display:inline-flex;align-items:center;gap:6px;padding:2px 10px;border-radius:999px;
  font-size:.62rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:#00ffd5;background:rgba(0,255,213,.06);border:1px solid rgba(0,255,213,.22);
}
.fusion-era-tag small{font-weight:500;color:#7a8aa3;letter-spacing:.06em}
.fusion-live-dot{
  width:7px;height:7px;border-radius:50%;background:var(--fusion-accent);
  box-shadow:0 0 6px var(--fusion-glow);
}
.fusion-live-dot--pulse{animation:fusion-blink 3s steps(2,end) infinite}
@keyframes fusion-blink{50%{opacity:.35}}
.fusion-title-3d,.fusion-title-grad{
  font-weight:700;letter-spacing:.06em;
  background:linear-gradient(92deg,#00ffd5 0%,#5eead4 45%,#c084fc 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.fusion-hud-corner{position:relative}
.fusion-hud-corner::before,.fusion-hud-corner::after{
  content:'';position:absolute;width:10px;height:10px;border-color:rgba(0,255,213,.35);border-style:solid;pointer-events:none;
}
.fusion-hud-corner::before{top:6px;left:6px;border-width:1px 0 0 1px}
.fusion-hud-corner::after{bottom:6px;right:6px;border-width:0 1px 1px 0}
"""

_CSS_SHARED = """
.fusion-panel,.fusion-panel-3d,.fusion-task-panel,.fusion-stat-card,.fusion-status-card,.fusion-tab-panel-3d{
  background:var(--fusion-surface);border:1px solid rgba(0,255,213,.1);
  border-radius:var(--fusion-radius-md);box-shadow:var(--shadow-3d);
}
.fusion-section-title,.fusion-task-title{
  font-size:.68rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--fusion-accent);
}
.fusion-label-muted,.fusion-stat-label,.fusion-stat-sub{color:var(--fusion-muted)!important;font-size:.75rem}
.fusion-stat-value{font-size:1.4rem;font-weight:700;font-variant-numeric:tabular-nums}
.fusion-stat-value--accent,.text-accent{color:#00ffd5}
.fusion-stat-value--purple,.text-purple{color:#c084fc}
.fusion-stat-value--amber,.text-amber{color:#fbbf24}
.fusion-metric-track{height:4px;border-radius:2px;background:#000;overflow:hidden;margin-top:6px}
.fusion-metric-fill{height:100%;transition:width .25s linear}
.fusion-metric-fill--cpu,.fusion-metric-fill[style*="00a884"]{background:#00ffd5}
.fusion-metric-fill--ram{background:#a855f7}
.fusion-btn-primary .q-btn,.fusion-btn.fusion-btn--primary{
  background:#00ffd5!important;color:#021a14!important;font-weight:700!important;
  border-radius:var(--fusion-radius-sm)!important;box-shadow:var(--shadow-btn)!important;
}
.fusion-btn-secondary .q-btn,.fusion-btn.fusion-btn--ghost{background:rgba(255,255,255,.04)!important;color:var(--fusion-muted)!important}
.fusion-btn-accent .q-btn,.fusion-btn.fusion-btn--accent{background:#7c3aed!important;color:#fff!important}
.fusion-job-row,.fusion-module-chip,.fusion-event-row{
  font-size:.72rem;border-left:2px solid rgba(0,255,213,.25);background:rgba(255,255,255,.02);
  border-radius:var(--fusion-radius-sm);padding:5px 8px;margin-bottom:3px;
}
.fusion-job--done,.fusion-module-chip--loaded{border-left-color:#00ffd5}
.fusion-job--run,.fusion-module-chip--standby{border-left-color:#fbbf24}
.fusion-job--queue,.fusion-module-chip--pending{border-left-color:#64748b}
.fusion-job--err,.fusion-module-chip--error{border-left-color:#f87171}
.fusion-job-id{font-family:var(--fusion-mono);color:#5eead4}
.fusion-output-area,.fusion-editor,.fusion-output,.fusion-grok-log{font-family:var(--fusion-mono)!important}
.fusion-stat-card--clickable{cursor:pointer}
.fusion-stat-card--clickable:hover{border-color:rgba(0,255,213,.28)}
.fusion-sparkline-wrap{border:1px solid rgba(0,255,213,.08);border-radius:var(--fusion-radius-md);background:#05050c;padding:8px}
canvas.fusion-sparkline{display:block;width:100%;height:140px}
.fusion-efficiency-hint{font-size:.62rem;color:#5c6b82;letter-spacing:.04em}
"""

_CSS_WORKSPACE = """
body.fusion-body{
  overflow:hidden;font-family:var(--fusion-sans);color:var(--fusion-text);
  background:var(--fusion-bg);
  background-image:
    linear-gradient(rgba(0,255,213,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,213,.03) 1px,transparent 1px);
  background-size:32px 32px;
}
body.fusion-body::after{
  content:'';position:fixed;inset:0;pointer-events:none;opacity:.04;z-index:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,#fff 2px,#fff 3px);
}
#fusion-root{height:calc(100vh - 52px);overflow:hidden;padding:10px;gap:10px;position:relative;z-index:1}
#fusion-sidebar.is-collapsed{pointer-events:none!important;width:0!important;min-width:0!important;
  max-width:0!important;padding:0!important;border:0!important;box-shadow:none!important;margin:0!important}
.fusion-header-3d{
  background:rgba(10,10,18,.96)!important;border-bottom:1px solid rgba(0,255,213,.12)!important;
  box-shadow:0 4px 16px rgba(0,0,0,.35);min-height:52px;
}
.fusion-header-link{
  padding:3px 10px;border-radius:999px;font-size:.7rem;font-weight:600;color:#c084fc!important;
  text-decoration:none!important;background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.25);
}
.fusion-sidebar-panel{margin-right:2px}
.fusion-main-panel{padding:14px!important}
.fusion-status-row{display:flex;align-items:center;gap:8px;padding:2px 0;font-size:.8rem}
.fusion-status-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.fusion-status-dot--ok{background:#00ffd5}.fusion-status-dot--warn{background:#fbbf24}
.fusion-status-dot--idle{background:#64748b}.fusion-status-dot--err{background:#f87171}
.fusion-tabs-3d .q-tabs{background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.06);border-radius:var(--fusion-radius-md);padding:3px}
.fusion-tabs-3d .q-tab--active{background:rgba(0,255,213,.12)!important;border-radius:var(--fusion-radius-sm)!important}
.fusion-tab-panel-3d{margin-top:10px;padding:12px;content-visibility:auto}
.fusion-dash-hero{padding:12px 14px;margin-bottom:10px;border:1px solid rgba(0,255,213,.1);border-radius:var(--fusion-radius-md)}
.fusion-stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:12px}
.fusion-stat-card{padding:12px 14px}
.fusion-task-layer,.fusion-stack-layers{position:absolute;inset:0;pointer-events:none;z-index:20}
.fusion-task-panel,.fusion-layer-panel{position:absolute;width:min(270px,40vw);pointer-events:auto;padding:8px 10px}
.fusion-layer-panel{width:min(260px,38vw);z-index:22}
.fusion-task-handle,.fusion-layer-handle{cursor:grab;user-select:none;padding-bottom:5px;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,.06)}
.fusion-layer-handle:active,.fusion-task-handle:active{cursor:grabbing}
.fusion-drag-active{box-shadow:0 0 0 1px rgba(0,255,213,.35),0 8px 28px rgba(0,0,0,.45)!important;z-index:120!important}
.fusion-layer-title{font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#e2e8f0}
.fusion-layer-hint{font-size:.58rem;color:#64748b;margin-bottom:4px}
.fusion-layer-body{font-size:.68rem;line-height:1.45;white-space:pre-line;color:#94a3b8}
.fusion-layer-body--ok{color:#5eead4}.fusion-layer-body--warn{color:#fbbf24}
.fusion-layer-body--cyber{color:#00ffd5;font-weight:600}.fusion-layer-body--idle{color:#64748b}
.fusion-layer-plug{font-size:.5rem;padding:1px 5px;border-radius:3px;border:1px solid rgba(0,255,213,.2);color:#00ffd5;letter-spacing:.08em}
.fusion-layer--substrat{border-left:2px solid rgba(148,163,184,.5)}
.fusion-layer--meta{border-left:2px solid rgba(110,231,215,.5)}
.fusion-layer--cyber{border-left:2px solid rgba(0,255,213,.55)}
.fusion-layer--fusion{border-left:2px solid rgba(124,58,237,.5)}
.fusion-cyber-hud.fusion-drag-layer{pointer-events:auto!important}
.fusion-cyber-hud-handle{display:flex;align-items:center;gap:8px;cursor:grab;padding:2px 0 4px}
.fusion-cyber-hud-handle:active{cursor:grabbing}
.fusion-cyber-hud-grip{font-size:.65rem;color:#64748b;letter-spacing:-2px;user-select:none}
.fusion-quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.fusion-job-list{max-height:150px;overflow-y:auto}
.fusion-body ::-webkit-scrollbar{width:6px}.fusion-body ::-webkit-scrollbar-thumb{background:rgba(0,255,213,.25);border-radius:3px}
.fusion-btn-icon .q-btn{background:rgba(255,255,255,.05)!important;border:1px solid rgba(255,255,255,.1)!important}
.fusion-btn-secondary .q-btn{background:rgba(30,58,95,.6)!important;color:#7dd3fc!important}
.fusion-btn-ghost .q-btn{background:rgba(255,255,255,.04)!important;color:var(--fusion-muted)!important}
.fusion-editor{height:340px;max-height:38vh}.fusion-output{height:280px;max-height:32vh}
.fusion-grok-log{height:360px;max-height:42vh}
.fusion-grok-badge{font-size:.68rem;padding:2px 10px;border-radius:999px;border:1px solid rgba(0,255,213,.25);color:#5eead4}
.fusion-iframe-monitor{width:100%;height:min(460px,48vh);border-radius:var(--fusion-radius-md);border:1px solid rgba(0,255,213,.1);background:#030308}
.fusion-expansion .q-item{background:rgba(255,255,255,.02)!important}
.fusion-module-chip{display:flex;align-items:center;gap:6px}
.fusion-toolbar-btn .q-btn{font-size:.72rem!important;min-height:28px!important}
.q-field--outlined .q-field__control{border-radius:var(--fusion-radius-sm)!important;background:rgba(0,0,0,.3)!important}
"""

_CSS_MONITOR = """
body.fusion-monitor{
  margin:0;min-height:100vh;font-family:var(--fusion-sans);color:var(--fusion-text);
  background:var(--fusion-bg);
  background-image:
    linear-gradient(rgba(0,255,213,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,213,.03) 1px,transparent 1px);
  background-size:32px 32px;
}
.fusion-app{position:relative;z-index:1;padding:1rem}
.fusion-header{
  display:flex;flex-wrap:wrap;align-items:center;gap:.6rem;margin-bottom:.85rem;padding:.55rem .85rem;
  background:rgba(10,10,18,.96);border:1px solid rgba(0,255,213,.1);border-radius:var(--fusion-radius-md);
}
.fusion-header-actions{margin-left:auto;display:flex;gap:.45rem;align-items:center;flex-wrap:wrap}
.fusion-btn{
  padding:.3rem .75rem;border-radius:var(--fusion-radius-sm);border:1px solid rgba(255,255,255,.08);
  background:rgba(255,255,255,.04);color:var(--fusion-muted);font-size:.72rem;font-weight:600;cursor:pointer;
}
.fusion-btn--primary{background:#00ffd5;color:#021a14;border-color:transparent}
.fusion-btn--accent{background:#7c3aed;color:#fff;border-color:transparent}
.fusion-link-pill{padding:3px 12px;border-radius:999px;font-size:.72rem;font-weight:600;color:#c084fc;
  text-decoration:none;background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.25)}
.fusion-status-text{font-size:.68rem;color:var(--fusion-muted)}
.fusion-dash-wrap{position:relative;min-height:480px}
.fusion-stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:12px}
.fusion-stat-card{padding:12px}
.fusion-grid-main{display:grid;gap:12px}@media(min-width:1024px){.fusion-grid-main{grid-template-columns:2fr 1fr}}
.fusion-panel{padding:12px}
.fusion-task-layer,.fusion-stack-layers{position:absolute;inset:0;pointer-events:none;z-index:30}
.fusion-task-panel,.fusion-layer-panel{position:absolute;width:min(280px,42vw);pointer-events:auto;padding:8px 10px}
.fusion-layer-panel{width:min(260px,38vw)}
.fusion-task-panel--wide{width:min(320px,48vw)}
.fusion-quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.fusion-job-list{max-height:160px;overflow-y:auto}
.fusion-job-row{display:grid;grid-template-columns:52px 1fr auto;gap:5px;align-items:center;cursor:pointer}
.fusion-hint-list{font-size:.66rem;color:var(--fusion-muted);line-height:1.55}
.fusion-hint-list kbd{padding:1px 4px;border-radius:3px;font-size:.6rem;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1)}
.fusion-output-area{width:100%;min-height:110px;max-height:180px;resize:vertical;border-radius:var(--fusion-radius-sm);
  border:1px solid rgba(255,255,255,.08);background:#030308;color:#b8c5d6;font-family:var(--fusion-mono);font-size:.7rem;padding:6px}
.fusion-toast{position:fixed;bottom:16px;right:16px;z-index:100;padding:8px 14px;border-radius:var(--fusion-radius-sm);
  font-size:.75rem;opacity:0;transition:opacity .15s linear;pointer-events:none}
.fusion-toast--show{opacity:1}.fusion-toast--ok{border:1px solid rgba(0,255,213,.35);color:#5eead4;background:rgba(0,40,35,.9)}
.fusion-toast--warn{border:1px solid rgba(251,191,36,.35);color:#fcd34d;background:rgba(40,30,0,.85)}
.fusion-toast--err{border:1px solid rgba(248,113,113,.35);color:#fca5a5;background:rgba(40,10,10,.9)}
.fusion-busy-bar{height:2px;background:rgba(255,255,255,.05);overflow:hidden;margin-top:3px}
.fusion-busy-bar span{display:block;height:100%;width:25%;background:#00ffd5;animation:fusion-slide 1s linear infinite}
@keyframes fusion-slide{from{transform:translateX(-100%)}to{transform:translateX(400%)}}
"""

_CSS_CYBER_LAYER = """
.fusion-cyber-layer{
  position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden;
}
.fusion-cyber-layer--active .fusion-cyber-frame{
  position:absolute;inset:8px;border:1px solid rgba(0,255,213,.18);
  box-shadow:inset 0 0 40px rgba(0,255,213,.04),0 0 24px rgba(168,85,247,.08);
}
.fusion-cyber-layer--active .fusion-cyber-frame::before,.fusion-cyber-layer--active .fusion-cyber-frame::after,
.fusion-cyber-layer--active .fusion-cyber-corner-tl,.fusion-cyber-layer--active .fusion-cyber-corner-br{
  content:'';position:absolute;width:28px;height:28px;border-color:rgba(0,255,213,.55);border-style:solid;
}
.fusion-cyber-layer--active .fusion-cyber-frame::before{top:-1px;left:-1px;border-width:2px 0 0 2px}
.fusion-cyber-layer--active .fusion-cyber-frame::after{bottom:-1px;right:-1px;border-width:0 2px 2px 0}
.fusion-cyber-scan{
  position:absolute;left:0;right:0;height:2px;opacity:0;
  background:linear-gradient(90deg,transparent,rgba(0,255,213,.7),transparent);
}
.fusion-cyber-layer--active .fusion-cyber-scan{
  opacity:.65;animation:cyber-scan 5s linear infinite;
}
@keyframes cyber-scan{0%{top:8px}100%{top:calc(100% - 10px)}}
.fusion-cyber-hud{
  position:fixed;top:10px;right:12px;z-index:9999;pointer-events:none;
  display:flex;flex-direction:column;align-items:flex-end;gap:6px;
}
.fusion-cyber-badge{
  display:inline-flex;align-items:center;gap:8px;padding:4px 12px;border-radius:4px;
  font-family:var(--fusion-mono);font-size:.62rem;font-weight:700;letter-spacing:.18em;
  color:#00ffd5;background:rgba(2,18,16,.88);border:1px solid rgba(0,255,213,.45);
  box-shadow:0 0 12px rgba(0,255,213,.2);
}
.fusion-cyber-badge::before{
  content:'';width:6px;height:6px;border-radius:50%;background:#00ffd5;
  box-shadow:0 0 8px #00ffd5;animation:fusion-blink 2s steps(2,end) infinite;
}
.fusion-cyber-layer--standby .fusion-cyber-badge{
  color:#7a8aa3;border-color:rgba(122,138,163,.35);box-shadow:none;
}
.fusion-cyber-layer--standby .fusion-cyber-badge::before{background:#64748b;box-shadow:none;animation:none}
.fusion-cyber-signals{
  display:flex;flex-wrap:wrap;gap:4px;justify-content:flex-end;max-width:min(420px,92vw);
}
.fusion-cyber-signal{
  font-family:var(--fusion-mono);font-size:.58rem;padding:2px 8px;border-radius:3px;
  border:1px solid rgba(0,255,213,.2);color:#5eead4;background:rgba(0,255,213,.05);
}
.fusion-cyber-signal--off{
  opacity:.45;border-color:rgba(100,116,139,.25);color:#64748b;background:rgba(255,255,255,.02);
}
.fusion-cyber-score{
  font-family:var(--fusion-mono);font-size:.58rem;color:#a855f7;letter-spacing:.1em;
}
body.fusion-cyber-active{
  background-image:
    linear-gradient(rgba(0,255,213,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,213,.05) 1px,transparent 1px)!important;
  background-size:24px 24px!important;
}
"""


def _skin_css_block() -> str:
    try:
        from windows_skin import render_full_skin_css
        return render_full_skin_css()
    except Exception:
        return _CSS_TOKENS + _CSS_CYBER_LAYER


def workspace_css() -> str:
    return _skin_css_block() + _CSS_ERA + _CSS_SHARED + _CSS_WORKSPACE


def cyber_layer_css() -> str:
    try:
        from windows_skin import skin_css_variables, skin_layer_css, load_skin
        s = load_skin()
        return skin_css_variables(s) + skin_layer_css(s)
    except Exception:
        return _CSS_CYBER_LAYER


def monitor_css() -> str:
    return _skin_css_block() + _CSS_ERA + _CSS_SHARED + _CSS_MONITOR


def era_meta() -> dict:
    return {
        "visual": ERA_VISUAL,
        "efficiency": ERA_EFFICIENCY,
        "theme_version": THEME_VERSION,
        "poll": {
            "pulse_sec": POLL_PULSE_SEC,
            "jobs_sec": POLL_JOBS_SEC,
            "metrics_sec": POLL_METRICS_SEC,
        },
        "rules": [
            "system-fonts-only",
            "no-backdrop-filter",
            "pulse-delta-first",
            "canvas-sparkline",
            "visibility-pause",
        ],
    }