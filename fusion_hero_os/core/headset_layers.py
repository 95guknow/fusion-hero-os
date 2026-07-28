"""Headset multi-layer membrane — several layers armed, ONE active (loud & clear).

Layers (placement-aligned, additive):
  L1_local       PC speakers/mic (no AudioRelay default)
  L2_phone       Phone headset via AudioRelay (system audio)
  L3_comaedchen  Operator <-> Comädchen voice on phone path
  L4_hyperraum   Hyperraum control-plane membrane (phone path + plane tag)

Multi-layer usage: any subset may be **enabled** (armed).
Exactly one layer is **active** (default playback route + channel semantics).

State: ``~/.fusion/headset_layers.json``
Banner: always printed / returned so the operator never guesses the level.

Geltung: Spezifikation · hardware state = empirical.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

__all__ = [
    "LAYERS",
    "LAYER_ORDER",
    "STATE_PATH",
    "banner",
    "status",
    "enable",
    "disable",
    "set_active",
    "apply_active_route",
    "activate_stack",
    "set_mesh_only",
    "is_mesh_only",
]

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path.home() / ".fusion" / "headset_layers.json"
SVV = ROOT / "workstation" / "tools" / "SoundVolumeView.exe"

LAYER_ORDER = ("L1_local", "L2_phone", "L3_comaedchen", "L4_hyperraum")

LAYERS: dict[str, dict[str, Any]] = {
    "L1_local": {
        "id": "L1_local",
        "rank": 1,
        "label": "LOCAL PC",
        "short": "L1",
        "route": "local",
        "device_hint": "Lautsprecher / host Realtek",
        "plane": "hyperraum",
        "description": "PC speakers + mic. No phone relay as default output.",
        "color": "cyan",
    },
    "L2_phone": {
        "id": "L2_phone",
        "rank": 2,
        "label": "PHONE RELAY",
        "short": "L2",
        "route": "phone",
        "device_hint": "Virtual Speakers for AudioRelay",
        "plane": "hyperraum",
        "description": "System audio -> phone headset (AudioRelay).",
        "color": "green",
    },
    "L3_comaedchen": {
        "id": "L3_comaedchen",
        "rank": 3,
        "label": "COMAEDCHEN",
        "short": "L3",
        "route": "phone",
        "device_hint": "Virtual Speakers for AudioRelay + Comet",
        "plane": "hyperraum",
        "description": "Operator <-> Nummer-2 voice channel on phone path.",
        "opens_comet": True,
        "color": "magenta",
    },
    "L4_hyperraum": {
        "id": "L4_hyperraum",
        "rank": 4,
        "label": "HYPERRAUM",
        "short": "L4",
        "route": "phone",
        "device_hint": "Virtual Speakers + hyperraum control membrane",
        "plane": "hyperraum",
        "description": "Half-private hyperraum audio membrane (control plane).",
        "color": "yellow",
        "opens_comet": False,
    },
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0",
        "platform_version": "10.0.0",
        "membrane": "headset_layers_v1",
        "enabled": ["L1_local", "L2_phone", "L3_comaedchen", "L4_hyperraum"],
        "active": "L1_local",
        # Phone layers (L2+) must use Tailscale 100.x only — never LAN
        "mesh_only": os.environ.get("FUSION_HEADSET_MESH_ONLY", "1").strip()
        in ("1", "true", "yes", ""),
        "updated_at": None,
        "last_apply": None,
        "history": [],
    }


def load_state() -> dict[str, Any]:
    st = _default_state()
    if STATE_PATH.is_file():
        try:
            raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                st.update({k: v for k, v in raw.items() if k in st or k in (
                    "enabled", "active", "updated_at", "last_apply", "history",
                    "note", "mesh_only",
                )})
        except (OSError, json.JSONDecodeError):
            st["load_error"] = "corrupt_state_reset"
    # env overrides file when explicitly set
    env_mo = os.environ.get("FUSION_HEADSET_MESH_ONLY", "").strip().lower()
    if env_mo in ("1", "true", "yes"):
        st["mesh_only"] = True
    elif env_mo in ("0", "false", "no"):
        st["mesh_only"] = False
    else:
        st["mesh_only"] = bool(st.get("mesh_only", True))
    # sanitize
    enabled = [x for x in (st.get("enabled") or []) if x in LAYERS]
    if not enabled:
        enabled = list(LAYER_ORDER)
    st["enabled"] = enabled
    active = st.get("active") or "L1_local"
    if active not in LAYERS:
        active = "L1_local"
    # active must be enabled — if not, promote first enabled
    if active not in enabled:
        active = enabled[0]
    st["active"] = active
    return st


def save_state(st: dict[str, Any]) -> Path:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    st = dict(st)
    st["updated_at"] = _now()
    # keep short history
    hist = list(st.get("history") or [])
    hist.append({
        "ts": st["updated_at"],
        "active": st.get("active"),
        "enabled": list(st.get("enabled") or []),
    })
    st["history"] = hist[-20:]
    STATE_PATH.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return STATE_PATH


def _phone_link_snapshot() -> dict[str, Any]:
    """Live phone + AudioRelay link (for banner clarity)."""
    out: dict[str, Any] = {
        "phone_online": False,
        "phone_host": None,
        "phone_ips": [],
        "audiorelay_running": False,
        "port_59100_listen": False,
        "port_59100_established": False,
        "remote_peers": [],
        "link": "none",
        "link_detail": "",
    }
    try:
        from fusion_hero_os.core.comaedchen_audio import _process_running, _phone_online

        ar = _process_running(["AudioRelay", "audiorelay-backend"])
        out["audiorelay_running"] = bool(ar.get("running"))
        phone = _phone_online()
        out["phone_online"] = bool(phone.get("online"))
        out["phone_host"] = phone.get("host")
        out["phone_ips"] = list(phone.get("tailscale_ips") or [])
    except Exception as exc:  # noqa: BLE001
        out["phone_error"] = str(exc)[:120]

    # TCP 59100 — AudioRelay peer (often LAN even when Tailscale online)
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-NetTCPConnection -LocalPort 59100 -ErrorAction SilentlyContinue | "
                    "Select-Object State,RemoteAddress,RemotePort | ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        raw = (r.stdout or "").strip()
        if raw:
            data = json.loads(raw)
            rows = data if isinstance(data, list) else [data]
            remotes = []
            # Win32 / ConvertTo-Json may emit numeric State:
            # 2=Listen, 5=Established (also accept name strings)
            for row in rows:
                stt = row.get("State")
                stt_s = str(stt or "").lower()
                is_listen = stt in (2, "2") or stt_s == "listen"
                is_est = stt in (5, "5") or stt_s == "established"
                if is_listen:
                    out["port_59100_listen"] = True
                if is_est:
                    out["port_59100_established"] = True
                    ra = str(row.get("RemoteAddress") or "")
                    rp = row.get("RemotePort")
                    if ra and ra not in (":", "::", "0.0.0.0"):
                        remotes.append(f"{ra}:{rp}")
            out["remote_peers"] = remotes
    except Exception as exc:  # noqa: BLE001
        out["port_error"] = str(exc)[:120]

    if out["port_59100_established"] and out["remote_peers"]:
        # classify path: CGNAT 100.x = tailscale, else typically LAN
        peer = out["remote_peers"][0]
        ip = peer.split(":")[0]
        if ip.startswith("100."):
            out["link"] = "tailscale"
        else:
            out["link"] = "lan"
        out["link_detail"] = f"AudioRelay ESTABLISHED -> {peer} ({out['link']})"
    elif out["audiorelay_running"] and out["port_59100_listen"]:
        out["link"] = "listening"
        out["link_detail"] = "AudioRelay listening :59100 (phone not established yet)"
    elif out["phone_online"]:
        out["link"] = "phone_online_no_relay"
        out["link_detail"] = f"phone online ({out.get('phone_host')}) but no AudioRelay session"
    else:
        out["link"] = "down"
        out["link_detail"] = "no phone relay session"

    out["connected_to_phone"] = bool(out["port_59100_established"])
    # mesh-only policy evaluation
    out["mesh_link_ok"] = bool(
        out["port_59100_established"] and out.get("link") == "tailscale"
    )
    out["lan_link"] = bool(out.get("link") == "lan")
    return out


def set_mesh_only(enabled: bool = True) -> dict[str, Any]:
    """Persist mesh-only policy (phone path must use Tailscale 100.x)."""
    st = load_state()
    st["mesh_only"] = bool(enabled)
    save_state(st)
    return status(apply_probe=False)


def is_mesh_only() -> bool:
    return bool(load_state().get("mesh_only", True))


def banner(
    active: str | None = None,
    enabled: list[str] | None = None,
    *,
    link: dict[str, Any] | None = None,
) -> str:
    """Very loud, unambiguous active-level banner (ASCII)."""
    st = load_state()
    act = active or st["active"]
    en = enabled if enabled is not None else list(st["enabled"])
    meta = LAYERS.get(act, {})
    label = meta.get("label", act)
    short = meta.get("short", "?")
    route = meta.get("route", "?")
    plane = meta.get("plane", "?")
    desc = meta.get("description", "")
    device = meta.get("device_hint", "")

    # enabled markers
    marks = []
    for lid in LAYER_ORDER:
        m = LAYERS[lid]
        if lid == act:
            marks.append(f"[{m['short']}:ACTIVE]")
        elif lid in en:
            marks.append(f"[{m['short']}:armed]")
        else:
            marks.append(f"[{m['short']}:off]")

    if link is None and route == "phone":
        try:
            link = _phone_link_snapshot()
        except Exception:
            link = None

    phone_line = "#  phone_link: (n/a for local route)"
    mesh_line = "#  transport: n/a"
    st_mo = load_state()
    mesh_only = bool(st_mo.get("mesh_only", True))
    if link:
        conn = "YES" if link.get("connected_to_phone") else "NO"
        host = link.get("phone_host") or "?"
        phone_line = (
            f"#  phone_link: CONNECTED={conn}  host={host}  "
            f"{link.get('link_detail') or link.get('link')}"
        )
        transport = (link.get("link") or "none").upper()
        if route == "phone" and mesh_only:
            if link.get("mesh_link_ok"):
                mesh_line = "#  transport: MESH-ONLY OK (Tailscale 100.x)"
            elif link.get("lan_link"):
                mesh_line = (
                    "#  transport: !! VIOLATION LAN — policy=mesh_only "
                    "(run force-headset-mesh-only.ps1)"
                )
            elif link.get("connected_to_phone"):
                mesh_line = f"#  transport: {transport} (mesh_only policy on)"
            else:
                mesh_line = (
                    "#  transport: WAITING mesh reconnect "
                    "(connect phone to PC Tailscale IP 100.x)"
                )
        else:
            mesh_line = f"#  transport: {transport}  mesh_only={mesh_only}"

    lines = [
        "",
        "################################################################",
        f"#  HEADSET ACTIVE LEVEL >>>  {short} = {label}  <<<",
        f"#  route={route}   plane={plane}",
        f"#  device: {device}",
        f"#  {desc}",
        phone_line,
        mesh_line,
        f"#  stack: {'  '.join(marks)}",
        "################################################################",
        "",
    ]
    return "\n".join(lines)


def status(*, apply_probe: bool = False) -> dict[str, Any]:
    st = load_state()
    act = st["active"]
    meta = dict(LAYERS[act])
    layers_view = []
    for lid in LAYER_ORDER:
        m = dict(LAYERS[lid])
        m["enabled"] = lid in st["enabled"]
        m["active"] = lid == act
        m["marker"] = "ACTIVE" if lid == act else ("armed" if lid in st["enabled"] else "off")
        layers_view.append(m)

    link = _phone_link_snapshot()
    out: dict[str, Any] = {
        "ok": True,
        "membrane": "headset_layers_v1",
        "platform_version": "10.0.0",
        "active": act,
        "active_label": meta.get("label"),
        "active_short": meta.get("short"),
        "active_route": meta.get("route"),
        "active_plane": meta.get("plane"),
        "active_device_hint": meta.get("device_hint"),
        "enabled": list(st["enabled"]),
        "layers": layers_view,
        "phone_link": link,
        "connected_to_phone": bool(link.get("connected_to_phone")),
        "mesh_only": bool(st.get("mesh_only", True)),
        "mesh_link_ok": bool(link.get("mesh_link_ok")),
        "lan_violation": bool(
            st.get("mesh_only", True)
            and meta.get("route") == "phone"
            and link.get("lan_link")
        ),
        "banner": banner(act, st["enabled"], link=link),
        "banner_one_line": (
            f"HEADSET ACTIVE LEVEL >>> {meta.get('short')}={meta.get('label')} "
            f"(route={meta.get('route')}) "
            f"phone_connected={'YES' if link.get('connected_to_phone') else 'NO'} "
            f"mesh={'OK' if link.get('mesh_link_ok') else ('LAN_VIOLATION' if link.get('lan_link') else 'WAIT')} <<<"
        ),
        "state_path": str(STATE_PATH),
        "updated_at": st.get("updated_at"),
        "clarity_rule": (
            "Multi-layer allowed: many layers may be armed; "
            "exactly ONE is ACTIVE. mesh_only=True requires Tailscale 100.x "
            "(never LAN 192.168). Always read banner."
        ),
    }

    # live hardware hints (also nested for API consumers)
    out["live"] = {
        "audiorelay_running": link.get("audiorelay_running"),
        "phone_online": link.get("phone_online"),
        "phone_host": link.get("phone_host"),
        "link": link.get("link"),
        "link_detail": link.get("link_detail"),
        "remote_peers": link.get("remote_peers"),
    }

    if apply_probe:
        out["default_device_probe"] = _probe_default_device()
    return out


def _probe_default_device() -> dict[str, Any]:
    if not SVV.is_file():
        return {"ok": False, "error": "SoundVolumeView missing"}
    csv = Path.home() / ".fusion" / "headset_default_probe.csv"
    try:
        subprocess.run(
            [str(SVV), "/scomma", str(csv)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if not csv.is_file():
            return {"ok": False, "error": "no csv"}
        import csv as csvmod

        with csv.open("r", encoding="utf-8", errors="replace") as f:
            rows = list(csvmod.DictReader(f))
        for row in rows:
            if row.get("Type") == "Device" and row.get("Direction") == "Render":
                d = row.get("Default") or ""
                dm = row.get("Default Multimedia") or ""
                if d == "Render" or dm == "Render":
                    name = row.get("Name") or ""
                    dev = row.get("Device Name") or ""
                    is_ar = "AudioRelay" in dev or "Virtual Speakers" in name
                    return {
                        "ok": True,
                        "name": name,
                        "device_name": dev,
                        "is_audiorelay": is_ar,
                        "inferred_route": "phone" if is_ar else "local",
                    }
        return {"ok": False, "error": "no default render row"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def enable(layer_id: str) -> dict[str, Any]:
    lid = _norm(layer_id)
    st = load_state()
    en = list(st["enabled"])
    if lid not in en:
        en.append(lid)
        # keep order
        en = [x for x in LAYER_ORDER if x in en]
    st["enabled"] = en
    save_state(st)
    return status()


def disable(layer_id: str) -> dict[str, Any]:
    lid = _norm(layer_id)
    st = load_state()
    en = [x for x in st["enabled"] if x != lid]
    if not en:
        return {
            "ok": False,
            "error": "cannot disable last layer — at least one must stay armed",
            "banner": banner(),
        }
    st["enabled"] = en
    if st["active"] == lid:
        st["active"] = en[0]
    save_state(st)
    # re-apply if active changed
    return set_active(st["active"], apply_route=True)


def _norm(layer_id: str) -> str:
    raw = (layer_id or "").strip()
    aliases = {
        "1": "L1_local",
        "l1": "L1_local",
        "local": "L1_local",
        "pc": "L1_local",
        "2": "L2_phone",
        "l2": "L2_phone",
        "phone": "L2_phone",
        "relay": "L2_phone",
        "3": "L3_comaedchen",
        "l3": "L3_comaedchen",
        "comaedchen": "L3_comaedchen",
        "comet": "L3_comaedchen",
        "4": "L4_hyperraum",
        "l4": "L4_hyperraum",
        "hyperraum": "L4_hyperraum",
        "hyper": "L4_hyperraum",
    }
    key = raw.lower().replace("-", "_")
    if raw in LAYERS:
        return raw
    if key in aliases:
        return aliases[key]
    # L2_phone style
    for lid in LAYER_ORDER:
        if key == lid.lower() or key == LAYERS[lid]["short"].lower():
            return lid
    raise ValueError(f"unknown headset layer: {layer_id!r} — use {list(LAYER_ORDER)}")


def set_active(layer_id: str, *, apply_route: bool = True) -> dict[str, Any]:
    """Set the single ACTIVE layer (must be enabled or will be auto-enabled)."""
    lid = _norm(layer_id)
    st = load_state()
    en = list(st["enabled"])
    if lid not in en:
        en.append(lid)
        en = [x for x in LAYER_ORDER if x in en]
    st["enabled"] = en
    st["active"] = lid
    save_state(st)

    apply_result = None
    if apply_route:
        apply_result = apply_active_route()
        st = load_state()
        st["last_apply"] = apply_result
        save_state(st)

    out = status(apply_probe=True)
    out["apply"] = apply_result
    out["ok"] = True if apply_result is None else bool(
        (apply_result or {}).get("ok", True)
    )
    return out


def apply_active_route() -> dict[str, Any]:
    """Apply Windows default device + optional Comet for current active layer."""
    st = load_state()
    lid = st["active"]
    meta = LAYERS[lid]
    route = meta["route"]
    report: dict[str, Any] = {
        "ok": False,
        "active": lid,
        "label": meta["label"],
        "route": route,
        "ts": _now(),
        "steps": {},
        "banner_one_line": (
            f"HEADSET ACTIVE LEVEL >>> {meta['short']}={meta['label']} "
            f"(route={route}) <<<"
        ),
    }

    if route == "phone":
        st_pol = load_state()
        if st_pol.get("mesh_only", True):
            # Enforce mesh-only firewall + drop LAN sessions when applying phone route
            mesh_ps1 = ROOT / "workstation" / "force-headset-mesh-only.ps1"
            if mesh_ps1.is_file():
                try:
                    r = subprocess.run(
                        [
                            "powershell",
                            "-NoProfile",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-File",
                            str(mesh_ps1),
                            "-SkipRoute",  # avoid recursion
                        ],
                        capture_output=True,
                        text=True,
                        timeout=180,
                        cwd=str(ROOT),
                        env={**os.environ, "FUSION_HEADSET_MESH_ONLY": "1"},
                    )
                    report["steps"]["mesh_only_enforce"] = {
                        "ok": r.returncode in (0, 2),
                        "rc": r.returncode,
                        "stdout_tail": (r.stdout or "")[-500:],
                    }
                except Exception as exc:  # noqa: BLE001
                    report["steps"]["mesh_only_enforce"] = {
                        "ok": False,
                        "error": str(exc)[:200],
                    }
        fix = ROOT / "workstation" / "fix-headset-relay.ps1"
        if fix.is_file():
            try:
                r = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(fix),
                        "-NoRestartAudioRelay",
                        "-SkipFirewall",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    cwd=str(ROOT),
                )
                report["steps"]["fix_headset_relay"] = {
                    "ok": r.returncode == 0,
                    "rc": r.returncode,
                    "stdout_tail": (r.stdout or "")[-400:],
                }
            except Exception as exc:  # noqa: BLE001
                report["steps"]["fix_headset_relay"] = {"ok": False, "error": str(exc)[:200]}
        # ensure default Virtual Speakers
        report["steps"]["set_default"] = _svv_set_default("Virtual Speakers for AudioRelay")
        link = _phone_link_snapshot()
        report["phone_link"] = link
        report["mesh_only"] = bool(st_pol.get("mesh_only", True))
        if st_pol.get("mesh_only", True):
            report["mesh_link_ok"] = bool(link.get("mesh_link_ok"))
            report["lan_violation"] = bool(link.get("lan_link"))
    else:
        # local — try common host speaker names
        for name in (
            "Lautsprecher",
            "Speakers",
            "2- Realtek(R) Audio",
        ):
            res = _svv_set_default(name)
            report["steps"][f"set_default_{name}"] = res
            if res.get("ok"):
                break
        report["steps"]["local_note"] = {
            "ok": True,
            "note": "L1 local: prefer host speakers; phone relay not forced as default",
        }

    if meta.get("opens_comet"):
        try:
            from fusion_hero_os.core.comaedchen_audio import activate as comaedchen_activate

            report["steps"]["comaedchen"] = comaedchen_activate(
                mode="phone" if route == "phone" else "local",
                open_surface=True,
                route_audio=False,  # already routed above
            )
        except Exception as exc:  # noqa: BLE001
            report["steps"]["comaedchen"] = {"ok": False, "error": str(exc)[:200]}

    # probe
    probe = _probe_default_device()
    report["probe"] = probe
    if route == "phone":
        report["ok"] = bool(probe.get("is_audiorelay") or report["steps"].get("fix_headset_relay", {}).get("ok"))
    else:
        report["ok"] = bool(not probe.get("is_audiorelay", False) or probe.get("ok") is False)
        # if probe failed, still ok if we attempted local
        if not probe.get("ok"):
            report["ok"] = True
            report["note"] = "local apply attempted; probe inconclusive"

    report["banner"] = banner()
    return report


def _svv_set_default(device_name: str) -> dict[str, Any]:
    if not SVV.is_file():
        return {"ok": False, "error": "SoundVolumeView missing", "device": device_name}
    try:
        r = subprocess.run(
            [str(SVV), "/SetDefault", device_name, "all"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        time.sleep(0.4)
        return {"ok": r.returncode == 0, "rc": r.returncode, "device": device_name}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200], "device": device_name}


def activate_stack(
    *,
    active: str = "L2_phone",
    enable_all: bool = True,
) -> dict[str, Any]:
    """Arm multi-layer stack and set active level (default phone relay)."""
    st = load_state()
    if enable_all:
        st["enabled"] = list(LAYER_ORDER)
    save_state(st)
    return set_active(active, apply_route=True)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Headset multi-layer — clear ACTIVE level"
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--banner", action="store_true")
    ap.add_argument("--active", default="", help="set active layer (L1..L4 or alias)")
    ap.add_argument("--enable", default="", help="arm a layer without switching active")
    ap.add_argument("--disable", default="", help="disarm a layer")
    ap.add_argument("--apply", action="store_true", help="re-apply route for current active")
    ap.add_argument("--stack", action="store_true", help="enable all layers")
    ap.add_argument("--mesh-only", action="store_true", help="force mesh-only policy + enforce")
    ap.add_argument("--allow-lan", action="store_true", help="disable mesh-only policy")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.allow_lan:
        set_mesh_only(False)
        out = status(apply_probe=True)
    elif args.mesh_only:
        set_mesh_only(True)
        mesh_ps1 = ROOT / "workstation" / "force-headset-mesh-only.ps1"
        if mesh_ps1.is_file():
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(mesh_ps1),
                ],
                cwd=str(ROOT),
                timeout=180,
            )
        out = status(apply_probe=True)
    elif args.enable:
        out = enable(args.enable)
    elif args.disable:
        out = disable(args.disable)
    elif args.active:
        out = set_active(args.active, apply_route=True)
    elif args.apply:
        apply_active_route()
        out = status(apply_probe=True)
    elif args.stack:
        set_mesh_only(True)
        out = activate_stack(active="L2_phone", enable_all=True)
    else:
        out = status(apply_probe=True)

    # Always print banner to stdout (clarity requirement)
    print(out.get("banner") or banner(), file=sys.stderr if args.json else sys.stdout)
    if args.json or args.status or args.active or args.stack or args.apply or args.enable or args.disable:
        # strip huge banner from json body duplicate
        body = dict(out)
        if args.json:
            print(json.dumps(body, indent=2, ensure_ascii=False))
        else:
            print(body.get("banner_one_line", ""))
            print(f"active={body.get('active')}  enabled={body.get('enabled')}")
            if body.get("apply"):
                print(f"apply_ok={body['apply'].get('ok')}  route={body['apply'].get('route')}")
            probe = body.get("default_device_probe") or (body.get("apply") or {}).get("probe")
            if probe:
                print(
                    f"device_probe: {probe.get('name')} / {probe.get('device_name')} "
                    f"is_audiorelay={probe.get('is_audiorelay')}"
                )
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
