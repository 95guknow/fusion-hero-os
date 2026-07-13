# -*- coding: utf-8 -*-
"""Windows-Substrat-Skin — modifizierbar via JSON-Presets + User-Override."""
from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

SKINS_DIR = Path(__file__).resolve().parent / "skins"
STATE_DIR = Path(os.getenv("FUSION_META_STATE", Path.home() / ".fusion-hero-os"))
USER_SKIN_FILE = STATE_DIR / "windows_skin.json"
ACTIVE_SKIN_FILE = STATE_DIR / "windows_skin_active.json"
DEFAULT_PRESET = os.getenv("FUSION_WINDOWS_SKIN", "synthwave")

_TOKEN_DEFAULTS = {
    "accent": "#00ffd5",
    "accent2": "#a855f7",
    "accent_soft": "#5eead4",
    "bg": "#020208",
    "surface": "#0a0a12",
    "elevated": "#101018",
    "text": "#e4eaf4",
    "muted": "#7a8aa3",
    "glow": "rgba(0,255,213,0.22)",
    "frame_border": "rgba(0,255,213,0.18)",
    "frame_glow_in": "rgba(0,255,213,0.04)",
    "frame_glow_out": "rgba(168,85,247,0.08)",
    "corner": "rgba(0,255,213,0.55)",
    "scanline": "rgba(0,255,213,0.7)",
    "badge_bg": "rgba(2,18,16,0.88)",
    "badge_border": "rgba(0,255,213,0.45)",
    "signal_border": "rgba(0,255,213,0.2)",
    "signal_bg": "rgba(0,255,213,0.05)",
    "grid_line": "rgba(0,255,213,0.05)",
    "grid_size": "24px",
    "corner_size": "28px",
    "frame_inset": "8px",
    "radius_md": "12px",
    "radius_sm": "8px",
    "font_mono": "ui-monospace,'Cascadia Mono',Consolas,monospace",
    "font_sans": "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif",
    "badge_active": "OPTIMIZATION ACTIVE",
    "badge_standby": "CYBER STANDBY",
    "scan_sec": "5s",
}

_FEATURE_DEFAULTS = {
    "scanline": True,
    "frame": True,
    "corner_brackets": True,
    "grid_boost": True,
    "badge_pulse": True,
}


@dataclass
class WindowsSkin:
    id: str
    label: str
    tokens: Dict[str, str] = field(default_factory=dict)
    features: Dict[str, bool] = field(default_factory=dict)
    description: str = ""
    extends: Optional[str] = None
    source: str = "preset"

    def to_dict(self) -> dict:
        return asdict(self)


_active: Optional[WindowsSkin] = None


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_presets() -> List[dict]:
    out: List[dict] = []
    if not SKINS_DIR.exists():
        return out
    for p in sorted(SKINS_DIR.glob("*.json")):
        data = _read_json(p)
        if data.get("id"):
            out.append({
                "id": data["id"],
                "label": data.get("label", data["id"]),
                "description": data.get("description", ""),
                "path": str(p),
            })
    return out


def _load_preset(preset_id: str) -> dict:
    path = SKINS_DIR / f"{preset_id}.json"
    if not path.exists():
        for p in SKINS_DIR.glob("*.json"):
            data = _read_json(p)
            if data.get("id") == preset_id:
                return data
        return _read_json(SKINS_DIR / f"{DEFAULT_PRESET}.json") or {"id": DEFAULT_PRESET, "tokens": {}}
    return _read_json(path)


def _merge_skin(base: dict, override: dict) -> WindowsSkin:
    extends = override.get("extends")
    merged = deepcopy(base)
    if extends and extends != base.get("id"):
        parent = _load_preset(extends)
        merged = _merge_dict(parent, override)
    else:
        merged = _merge_dict(base, override)

    tokens = {**_TOKEN_DEFAULTS, **(merged.get("tokens") or {})}
    features = {**_FEATURE_DEFAULTS, **(merged.get("features") or {})}
    return WindowsSkin(
        id=merged.get("id", "custom"),
        label=merged.get("label", "Custom"),
        description=merged.get("description", ""),
        extends=merged.get("extends"),
        tokens=tokens,
        features=features,
        source=merged.get("source", "merged"),
    )


def _merge_dict(base: dict, patch: dict) -> dict:
    out = deepcopy(base)
    for key, val in patch.items():
        if key == "tokens" and isinstance(val, dict):
            out.setdefault("tokens", {})
            out["tokens"].update(val)
        elif key == "features" and isinstance(val, dict):
            out.setdefault("features", {})
            out["features"].update(val)
        else:
            out[key] = val
    return out


def load_skin(force: bool = False) -> WindowsSkin:
    global _active
    if _active and not force:
        return _active

    active_meta = _read_json(ACTIVE_SKIN_FILE)
    preset_id = active_meta.get("preset") or os.getenv("FUSION_WINDOWS_SKIN", DEFAULT_PRESET)
    base = _load_preset(preset_id)
    user = _read_json(USER_SKIN_FILE)

    if user:
        skin = _merge_skin(base, user)
        skin.source = "user_override"
    else:
        skin = _merge_skin(base, base)
        skin.source = "preset"

    _active = skin
    return skin


def set_preset(preset_id: str, persist: bool = True) -> WindowsSkin:
    global _active
    base = _load_preset(preset_id)
    skin = _merge_skin(base, base)
    skin.source = "preset"
    _active = skin
    if persist:
        _write_json(ACTIVE_SKIN_FILE, {
            "preset": preset_id,
            "set_at": time.time(),
            "label": skin.label,
        })
        os.environ["FUSION_WINDOWS_SKIN"] = preset_id
    return skin


def patch_user_skin(patch: dict) -> WindowsSkin:
    """User-Override mergen — Datei ~/.fusion-hero-os/windows_skin.json."""
    global _active
    existing = _read_json(USER_SKIN_FILE)
    merged = _merge_dict(existing, patch)
    merged["source"] = "user_override"
    _write_json(USER_SKIN_FILE, merged)

    preset_id = _read_json(ACTIVE_SKIN_FILE).get("preset") or DEFAULT_PRESET
    base = _load_preset(preset_id)
    _active = _merge_skin(base, merged)
    _active.source = "user_override"
    return _active


def reset_user_skin() -> WindowsSkin:
    global _active
    if USER_SKIN_FILE.exists():
        USER_SKIN_FILE.unlink()
    return load_skin(force=True)


def skin_css_variables(skin: Optional[WindowsSkin] = None) -> str:
    s = skin or load_skin()
    lines = [":root{"]
    for key, val in s.tokens.items():
        css_key = key.replace("_", "-")
        lines.append(f"  --win-skin-{css_key}:{val};")
        if key in ("accent", "accent2", "bg", "surface", "elevated", "text", "muted", "glow"):
            fusion_key = key if key != "glow" else "glow"
            if fusion_key == "glow":
                lines.append(f"  --fusion-glow:{val};")
            elif fusion_key in ("bg", "surface", "elevated", "text", "muted"):
                lines.append(f"  --fusion-{fusion_key}:{val};")
            elif fusion_key in ("accent", "accent2"):
                pass
    if "accent" in s.tokens:
        lines.append(f"  --fusion-accent:{s.tokens['accent']};")
    lines.append("}")
    return "\n".join(lines)


def skin_layer_css(skin: Optional[WindowsSkin] = None) -> str:
    s = skin or load_skin()
    f = s.features
    scan = ""
    if f.get("scanline", True):
        scan = f"""
.fusion-cyber-layer--active .fusion-cyber-scan{{
  opacity:.65;animation:cyber-scan {s.tokens.get('scan_sec','5s')} linear infinite;
}}"""
    else:
        scan = ".fusion-cyber-layer--active .fusion-cyber-scan{display:none;}"

    frame = ""
    if f.get("frame", True):
        inset = s.tokens.get("frame_inset", "8px")
        frame = f"""
.fusion-cyber-layer--active .fusion-cyber-frame{{
  position:absolute;inset:{inset};border:1px solid var(--win-skin-frame-border);
  box-shadow:inset 0 0 40px var(--win-skin-frame-glow-in),0 0 24px var(--win-skin-frame-glow-out);
}}"""
    else:
        frame = ".fusion-cyber-layer--active .fusion-cyber-frame{display:none;}"

    corners = ""
    if f.get("corner_brackets", True):
        cs = s.tokens.get("corner_size", "28px")
        corners = f"""
.fusion-cyber-layer--active .fusion-cyber-frame::before,.fusion-cyber-layer--active .fusion-cyber-frame::after{{
  content:'';position:absolute;width:{cs};height:{cs};border-color:var(--win-skin-corner);border-style:solid;
}}
.fusion-cyber-layer--active .fusion-cyber-frame::before{{top:-1px;left:-1px;border-width:2px 0 0 2px}}
.fusion-cyber-layer--active .fusion-cyber-frame::after{{bottom:-1px;right:-1px;border-width:0 2px 2px 0}}"""
    else:
        corners = ".fusion-cyber-layer--active .fusion-cyber-frame::before,.fusion-cyber-layer--active .fusion-cyber-frame::after{display:none;}"

    grid = ""
    if f.get("grid_boost", True):
        gs = s.tokens.get("grid_size", "24px")
        grid = f"""
body.fusion-cyber-active{{
  background-image:
    linear-gradient(var(--win-skin-grid-line) 1px,transparent 1px),
    linear-gradient(90deg,var(--win-skin-grid-line) 1px,transparent 1px)!important;
  background-size:{gs} {gs}!important;
}}"""
    else:
        grid = "body.fusion-cyber-active{background-image:none!important;}"

    pulse = ""
    if f.get("badge_pulse", True):
        pulse = ".fusion-cyber-badge::before{animation:fusion-blink 2s steps(2,end) infinite;}"
    else:
        pulse = ".fusion-cyber-badge::before{animation:none;}"

    return f"""
/* Windows Skin: {s.id} ({s.label}) */
.fusion-cyber-layer{{position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden;}}
.fusion-cyber-scan{{
  position:absolute;left:0;right:0;height:2px;opacity:0;
  background:linear-gradient(90deg,transparent,var(--win-skin-scanline),transparent);
}}
{scan}
{frame}
{corners}
.fusion-cyber-hud{{
  position:fixed;top:10px;right:12px;z-index:9999;pointer-events:none;
  display:flex;flex-direction:column;align-items:flex-end;gap:6px;
}}
.fusion-cyber-hud.fusion-drag-layer{{pointer-events:auto!important}}
.fusion-cyber-hud-handle{{display:flex;align-items:center;gap:8px;cursor:grab}}
.fusion-cyber-badge{{
  display:inline-flex;align-items:center;gap:8px;padding:4px 12px;border-radius:4px;
  font-family:var(--win-skin-font-mono);font-size:.62rem;font-weight:700;letter-spacing:.18em;
  color:var(--win-skin-accent);background:var(--win-skin-badge-bg);border:1px solid var(--win-skin-badge-border);
  box-shadow:0 0 12px var(--win-skin-glow);
}}
.fusion-cyber-badge::before{{
  content:'';width:6px;height:6px;border-radius:50%;background:var(--win-skin-accent);
  box-shadow:0 0 8px var(--win-skin-accent);
}}
{pulse}
.fusion-cyber-layer--standby .fusion-cyber-badge{{
  color:var(--win-skin-muted);border-color:rgba(122,138,163,.35);box-shadow:none;
}}
.fusion-cyber-layer--standby .fusion-cyber-badge::before{{background:#64748b;box-shadow:none;animation:none}}
.fusion-cyber-signals{{display:flex;flex-wrap:wrap;gap:4px;justify-content:flex-end;max-width:min(420px,92vw);}}
.fusion-cyber-signal{{
  font-family:var(--win-skin-font-mono);font-size:.58rem;padding:2px 8px;border-radius:3px;
  border:1px solid var(--win-skin-signal-border);color:var(--win-skin-accent-soft);
  background:var(--win-skin-signal-bg);
}}
.fusion-cyber-signal--off{{opacity:.45;border-color:rgba(100,116,139,.25);color:#64748b;background:rgba(255,255,255,.02);}}
.fusion-cyber-score{{font-family:var(--win-skin-font-mono);font-size:.58rem;color:var(--win-skin-accent2);letter-spacing:.1em;}}
@keyframes cyber-scan{{0%{{top:8px}}100%{{top:calc(100% - 10px)}}}}
{grid}
"""


def render_full_skin_css(skin: Optional[WindowsSkin] = None) -> str:
    s = skin or load_skin()
    fusion_map = f"""
:root{{
  --fusion-bg:var(--win-skin-bg);--fusion-surface:var(--win-skin-surface);--fusion-elevated:var(--win-skin-elevated);
  --fusion-accent:var(--win-skin-accent);--fusion-accent2:var(--win-skin-accent2);--fusion-glow:var(--win-skin-glow);
  --fusion-text:var(--win-skin-text);--fusion-muted:var(--win-skin-muted);
  --fusion-mono:var(--win-skin-font-mono);--fusion-sans:var(--win-skin-font-sans);
  --fusion-radius-md:var(--win-skin-radius-md);--fusion-radius-sm:var(--win-skin-radius-sm);
}}
.fusion-title-grad,.fusion-title-3d{{
  background:linear-gradient(92deg,var(--win-skin-accent) 0%,var(--win-skin-accent-soft) 45%,var(--win-skin-accent2) 100%);
}}
.fusion-era-tag{{color:var(--win-skin-accent);border-color:color-mix(in srgb,var(--win-skin-accent) 22%,transparent);}}
.fusion-live-dot{{background:var(--win-skin-accent);box-shadow:0 0 6px var(--win-skin-glow);}}
"""
    return skin_css_variables(s) + fusion_map + skin_layer_css(s)


def skin_status() -> dict:
    s = load_skin()
    return {
        "active": s.to_dict(),
        "presets": list_presets(),
        "paths": {
            "presets_dir": str(SKINS_DIR),
            "user_override": str(USER_SKIN_FILE),
            "active_meta": str(ACTIVE_SKIN_FILE),
        },
        "modifiable": {
            "presets": "Dashboard/skins/*.json",
            "user_patch": str(USER_SKIN_FILE),
            "env": "FUSION_WINDOWS_SKIN=<preset_id>",
            "example_patch": {
                "extends": "cyber_neon",
                "tokens": {"accent": "#00ffd5", "badge_active": "MEIN SKIN"},
                "features": {"scanline": True, "grid_boost": False},
            },
        },
    }


def ensure_user_skin_template() -> Path:
    """Legt editierbare Vorlage an, falls keine User-Datei existiert."""
    if USER_SKIN_FILE.exists():
        return USER_SKIN_FILE
    template = {
        "_comment": "User-Override — extends = Preset, tokens/features überschreiben",
        "extends": load_skin().id,
        "label": "Mein Windows-Skin",
        "tokens": {
            "accent": load_skin().tokens.get("accent"),
            "accent2": load_skin().tokens.get("accent2"),
            "badge_active": "OPTIMIZATION ACTIVE",
        },
        "features": {
            "scanline": True,
            "frame": True,
            "corner_brackets": True,
            "grid_boost": True,
            "badge_pulse": True,
        },
    }
    _write_json(USER_SKIN_FILE, template)
    return USER_SKIN_FILE