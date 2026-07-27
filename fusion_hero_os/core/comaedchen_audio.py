"""
Comädchen Audio Channel — voice path Operator ↔ Nummer 2 (Comet).

Modes:
  local  — PC mic + PC speakers (default when phone offline)
  phone  — AudioRelay virtual speakers/mic via phone headset

Does not invent speech APIs; activates the physical audio membrane and
surfaces Comet so the operator can use Comet voice / mic permissions.

Geltung: Spezifikation (channel) · hardware state = empirical.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE = Path.home() / ".fusion" / "comaedchen_audio.json"
COMET_EXE = Path(r"C:\Program Files\Perplexity\Comet\Application\comet.exe")

__all__ = ["activate", "status", "deactivate_route_note"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ps(script: str, timeout: int = 60) -> dict[str, Any]:
    """Run a short PowerShell snippet; return stdout/stderr/rc."""
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
        return {
            "ok": r.returncode == 0,
            "rc": r.returncode,
            "stdout": (r.stdout or "").strip(),
            "stderr": (r.stderr or "").strip()[:800],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _process_running(names: list[str]) -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    for name in names:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-Process -Name '{name}' -ErrorAction SilentlyContinue | "
                 "Select-Object -ExpandProperty Id"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            ids = [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]
            if ids:
                found.append({"name": name, "pids": ids})
        except Exception:
            continue
    return {"running": bool(found), "processes": found}


def _ensure_comet() -> dict[str, Any]:
    st = _process_running(["comet", "Comet"])
    if st["running"]:
        return {"ok": True, "already": True, "processes": st["processes"]}
    if not COMET_EXE.is_file():
        return {"ok": False, "error": f"comet_missing:{COMET_EXE}"}
    try:
        subprocess.Popen([str(COMET_EXE)], close_fds=True)
        time.sleep(1.2)
        st2 = _process_running(["comet", "Comet"])
        return {"ok": st2["running"], "started": True, "processes": st2["processes"]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _ensure_audiorelay() -> dict[str, Any]:
    st = _process_running(["AudioRelay", "audiorelay-backend"])
    if st["running"]:
        return {"ok": True, "already": True, "processes": st["processes"]}
    candidates = [
        Path(r"C:\Program Files (x86)\AudioRelay\AudioRelay.exe"),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "AudioRelay"
        / "AudioRelay.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "AudioRelay" / "AudioRelay.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "AudioRelay" / "AudioRelay.exe",
        Path(r"C:\Program Files\AudioRelay\AudioRelay.exe"),
    ]
    # search shallow under LocalAppData
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    if local.is_dir():
        for p in local.rglob("AudioRelay.exe"):
            candidates.append(p)
            break
    exe = next((c for c in candidates if c.is_file()), None)
    if not exe:
        return {"ok": False, "error": "AudioRelay.exe not found", "hint": "Install AudioRelay or start manually"}
    try:
        subprocess.Popen([str(exe)], close_fds=True)
        time.sleep(1.5)
        st2 = _process_running(["AudioRelay", "audiorelay-backend"])
        return {"ok": st2["running"], "started": True, "exe": str(exe), "processes": st2["processes"]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _svv_path() -> Path | None:
    cands = [
        ROOT / "workstation" / "tools" / "SoundVolumeView.exe",
        ROOT / "workstation" / "tools" / "soundvolumeview" / "SoundVolumeView.exe",
    ]
    for c in cands:
        if c.is_file():
            return c
    return None


def _set_default_endpoint(device_name: str) -> dict[str, Any]:
    """Set Windows default playback device via SoundVolumeView if available."""
    svv = _svv_path()
    if not svv:
        return {
            "ok": False,
            "error": "SoundVolumeView.exe missing",
            "manual": f"Windows Sound → Output → {device_name}",
        }
    try:
        r = subprocess.run(
            [str(svv), "/SetDefault", device_name, "all"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return {
            "ok": r.returncode == 0,
            "rc": r.returncode,
            "device": device_name,
            "tool": str(svv),
            "stderr": (r.stderr or "")[:300],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _phone_online() -> dict[str, Any]:
    ts = Path(r"C:\Program Files\Tailscale\tailscale.exe")
    if not ts.is_file():
        return {"ok": False, "online": False, "error": "tailscale_missing"}
    try:
        r = subprocess.run(
            [str(ts), "status", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0 or not r.stdout:
            return {"ok": False, "online": False, "error": "tailscale_status_failed"}
        data = json.loads(r.stdout)
        peers = data.get("Peer") or {}
        for _k, p in peers.items():
            if not isinstance(p, dict):
                continue
            host = str(p.get("HostName") or "")
            dns = str(p.get("DNSName") or "")
            if "redmi" in host.lower() or "redmi" in dns.lower() or "phone" in host.lower():
                online = bool(p.get("Online"))
                return {
                    "ok": True,
                    "online": online,
                    "host": host,
                    "dns": dns,
                    "tailscale_ips": p.get("TailscaleIPs"),
                }
        return {"ok": True, "online": False, "note": "no redmi/phone peer found"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "online": False, "error": str(e)[:200]}


def _open_comet_surface() -> dict[str, Any]:
    """Bring operator to Comet (Nummer-2 surface) without forcing a Google route."""
    try:
        from fusion_hero_os.core.browser_egress import open_url

        # Comet home / chat surface — operator starts voice in-app
        return open_url("https://www.perplexity.ai/", profile="comet")
    except Exception as e:  # noqa: BLE001
        if COMET_EXE.is_file():
            try:
                subprocess.Popen([str(COMET_EXE)], close_fds=True)
                return {"ok": True, "fallback": "launch_exe_only"}
            except Exception as e2:  # noqa: BLE001
                return {"ok": False, "error": str(e2)[:200]}
        return {"ok": False, "error": str(e)[:200]}


def activate(
    *,
    mode: str = "auto",
    open_surface: bool = True,
    route_audio: bool = True,
) -> dict[str, Any]:
    """
    Activate Operator ↔ Comädchen audio channel.

    mode:
      auto  — phone if redmi online else local
      local — PC speakers/mic
      phone — AudioRelay virtual devices
    """
    mode = (mode or "auto").lower().strip()
    phone = _phone_online()
    if mode == "auto":
        mode = "phone" if phone.get("online") else "local"

    report: dict[str, Any] = {
        "ok": False,
        "channel": "comaedchen_audio",
        "version": "1.0.0",
        "activated_at": _now(),
        "mode": mode,
        "policy": {
            "rank": "nummer_2",
            "reports_only_to": "operator",  # abstract role — person extracted
            "input_only_from": "operator",
            "audio_is_operator_membrane": True,
            "identity_membrane": "operator_identity_v1",
        },
        "phone": phone,
        "steps": {},
    }

    report["steps"]["comet"] = _ensure_comet()
    # Multi-layer headset: map mode -> clear ACTIVE level (other layers stay armed)
    try:
        from fusion_hero_os.core.headset_layers import set_active, banner

        layer = "L3_comaedchen" if mode == "phone" else "L1_local"
        if route_audio:
            report["steps"]["headset_layer"] = set_active(layer, apply_route=True)
        else:
            report["steps"]["headset_layer"] = set_active(layer, apply_route=False)
        report["headset_active_level"] = layer
        report["headset_banner"] = banner()
    except Exception as exc:  # noqa: BLE001
        report["steps"]["headset_layer"] = {"ok": False, "error": str(exc)[:200]}
        report["headset_banner"] = ""

    if mode == "phone":
        # Full auto repair if layer apply did not already
        if route_audio and not (report["steps"].get("headset_layer") or {}).get("ok"):
            fix_ps1 = ROOT / "workstation" / "fix-headset-relay.ps1"
            if fix_ps1.is_file():
                report["steps"]["fix_headset_relay"] = _ps(
                    f'& "{fix_ps1}"',
                    timeout=90,
                )
        report["steps"]["audiorelay"] = _ensure_audiorelay()
        if route_audio and "route_speakers" not in (report["steps"].get("headset_layer") or {}).get("apply", {}):
            report["steps"]["route_speakers"] = _set_default_endpoint(
                "Virtual Speakers for AudioRelay"
            )
            report["steps"]["route_mic_note"] = {
                "ok": True,
                "note": "Optional: set input to 'Virtual Mic for AudioRelay' if phone mic is uplink",
            }
    else:
        report["steps"]["audiorelay"] = {
            "ok": True,
            "skipped": True,
            "reason": "local mode — PC speakers/mic (L1_local active)",
        }
        if route_audio:
            report["steps"]["route_speakers"] = {
                "ok": True,
                "mode": "local",
                "layer": "L1_local",
                "note": "Using Windows host speakers; phone relay not default",
            }

    if open_surface:
        report["steps"]["surface"] = _open_comet_surface()

    report["operator_checklist"] = [
        "In Comet: allow microphone when prompted",
        "Use Comet voice / mic button for spoken input",
        "You speak → Comädchen (Comet) hears via system mic",
        "Comädchen replies (TTS/voice) → your speakers (local) or phone (AudioRelay)",
        "No mesh agent may inject audio as her boss — Operator only",
    ]
    if mode == "phone":
        report["operator_checklist"].extend(
            [
                "AudioRelay app: phone connected + Playback active",
                "Phone Tailscale online (redmi)",
            ]
        )

    report["ok"] = bool(report["steps"]["comet"].get("ok"))
    report["cli"] = {
        "activate_auto": "python -m fusion_hero_os.core.comaedchen_audio --activate",
        "activate_local": "python -m fusion_hero_os.core.comaedchen_audio --activate --mode local",
        "activate_phone": "python -m fusion_hero_os.core.comaedchen_audio --activate --mode phone",
        "status": "python -m fusion_hero_os.core.comaedchen_audio --status",
        "ps1": "powershell -File scripts/activate_comaedchen_audio.ps1",
    }

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["state_path"] = str(STATE)
    return report


def status() -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": True,
        "channel": "comaedchen_audio",
        "comet": _process_running(["comet", "Comet"]),
        "audiorelay": _process_running(["AudioRelay", "audiorelay-backend"]),
        "phone": _phone_online(),
        "svv": str(_svv_path()) if _svv_path() else None,
        "state_path": str(STATE) if STATE.is_file() else None,
    }
    if STATE.is_file():
        try:
            out["last"] = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            out["last"] = None
    return out


def deactivate_route_note() -> dict[str, Any]:
    """Advisory only — restore local speakers if AudioRelay was forced."""
    return {
        "ok": True,
        "note": "Switch Windows Sound output back to Realtek/host speakers if phone path ends",
        "optional": _set_default_endpoint("Speakers") if _svv_path() else None,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Comädchen audio channel")
    ap.add_argument("--activate", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--mode", choices=["auto", "local", "phone"], default="auto")
    ap.add_argument("--no-surface", action="store_true", help="do not open Comet URL")
    ap.add_argument("--no-route", action="store_true", help="do not change default audio device")
    args = ap.parse_args()

    if args.activate:
        r = activate(
            mode=args.mode,
            open_surface=not args.no_surface,
            route_audio=not args.no_route,
        )
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    r = status()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
