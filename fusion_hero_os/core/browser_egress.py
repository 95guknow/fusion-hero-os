"""
Browser egress — controlled URL opening for Fusion Hero OS.

Bug+Feature: OS default (here: Perplexity Comet / CometHTM) tunnels all
Start-Process / webbrowser.open traffic through one browser. That is a single
membrane (feature) and wrong account/context for Google One (bug).

This module chooses an explicit profile from browser_egress.yaml.

Geltung: Spezifikation · default detection = workstation-specific
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]

__all__ = ["load_config", "open_url", "open_urls", "status", "resolve_profile"]


def load_config() -> dict[str, Any]:
    path = ROOT / "browser_egress.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _expand(s: str) -> str:
    return os.path.expandvars(os.path.expanduser(str(s)))


def resolve_profile(name: str | None = None, *, url: str = "") -> dict[str, Any]:
    cfg = load_config()
    profiles = cfg.get("profiles") or {}
    routes = cfg.get("routes") or {}
    active = name or cfg.get("active") or "default"

    if not name and url:
        host = (urlparse(url).netloc or "").lower()
        path = (urlparse(url).path or "").lower()
        if "one.google.com" in host or "google.com/drive" in host + path:
            active = routes.get("google_one") or routes.get("google_drive") or active
        elif "drive.google.com" in host:
            active = routes.get("google_drive") or active
        elif "play.google.com" in host:
            active = routes.get("play_store") or active
        elif "apps.apple.com" in host:
            active = routes.get("app_store") or active
        elif "github.com" in host:
            active = routes.get("github") or active
        elif "127.0.0.1" in host or "localhost" in host:
            active = routes.get("local_dashboard") or active

    prof = dict(profiles.get(active) or profiles.get("default") or {"kind": "shell", "label": "shell"})
    prof["id"] = active
    return prof


def open_url(url: str, *, profile: str | None = None) -> dict[str, Any]:
    """Open one URL via configured egress profile."""
    url = (url or "").strip()
    if not url:
        return {"ok": False, "error": "empty_url"}
    prof = resolve_profile(profile, url=url)
    kind = (prof.get("kind") or "shell").lower()
    label = prof.get("label") or prof.get("id")

    if kind in ("none", "noop"):
        return {"ok": True, "skipped": True, "profile": prof.get("id"), "url": url, "label": label}

    try:
        if kind == "chrome":
            exe = _expand(prof.get("exe") or r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            user_data = _expand(prof.get("user_data_dir") or r"%LOCALAPPDATA%\Google\Chrome\User Data")
            profile_dir = prof.get("profile_directory") or "Default"
            if not Path(exe).is_file():
                return {"ok": False, "error": f"chrome_missing:{exe}", "url": url}
            args = [
                exe,
                f"--user-data-dir={user_data}",
                f"--profile-directory={profile_dir}",
                "--new-tab",
                url,
            ]
            subprocess.Popen(args, close_fds=True)
            return {
                "ok": True,
                "profile": prof.get("id"),
                "label": label,
                "kind": kind,
                "url": url,
                "exe": exe,
                "profile_directory": profile_dir,
            }

        if kind == "exe":
            exe = _expand(prof.get("exe") or "")
            if not exe or not Path(exe).is_file():
                return {"ok": False, "error": f"exe_missing:{exe}", "url": url}
            subprocess.Popen([exe, url], close_fds=True)
            return {"ok": True, "profile": prof.get("id"), "label": label, "kind": kind, "url": url, "exe": exe}

        # shell = OS default (Comet tunnel on this workstation)
        if sys.platform.startswith("win"):
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            import webbrowser

            webbrowser.open(url)
        return {
            "ok": True,
            "profile": prof.get("id"),
            "label": label,
            "kind": "shell",
            "url": url,
            "note": "OS default handler (Comet tunnel if CometHTM is default)",
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200], "url": url, "profile": prof.get("id")}


def open_urls(urls: list[str], *, profile: str | None = None, stagger_ms: int = 350) -> dict[str, Any]:
    import time

    results = []
    for u in urls:
        results.append(open_url(u, profile=profile))
        if stagger_ms > 0:
            time.sleep(stagger_ms / 1000.0)
    return {
        "ok": all(r.get("ok") for r in results),
        "count": len(results),
        "results": results,
        "active_policy": (load_config() or {}).get("active"),
    }


def status() -> dict[str, Any]:
    cfg = load_config()
    return {
        "ok": True,
        "active": cfg.get("active"),
        "default_progid": cfg.get("default_progid"),
        "default_label": cfg.get("default_label"),
        "profiles": list((cfg.get("profiles") or {}).keys()),
        "routes": cfg.get("routes"),
        "comaedchen": cfg.get("comaedchen")
        or {
            "codename": "Comädchen",
            "rank": "nummer_2",
            "reports_only_to": "operator",
            "input_only_from": "operator",
        },
        "bug_and_feature": {
            "feature": "Comädchen/Comet = operator-exclusive Nummer-2 membrane (input+report only with you)",
            "confusion": "Agents treated Comet as general system browser / command bus",
            "account_organ": "Google One/Drive/Play use Chrome profile — parallel organ, not her boss",
            "fix": "browser_egress.yaml routes + docs/mesh/COMAEDCHEN_NUMMER2.md",
        },
        "principle": cfg.get("principle"),
    }


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Browser egress (bug+feature tunnel control)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--url", action="append", default=[], help="URL to open (repeatable)")
    ap.add_argument("--profile", default=None, help="default|chrome_personal|chrome_work|edge|comet|none")
    ap.add_argument(
        "--google-one-bundle",
        action="store_true",
        help="Open Google One + Drive + phone store links via routed profiles",
    )
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    urls = list(args.url)
    if args.google_one_bundle:
        urls.extend(
            [
                "https://one.google.com/?g1_landing_page=1",
                "https://one.google.com/storage",
                "https://one.google.com/about/device-backup",
                "https://drive.google.com/drive/my-drive",
                "https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO",
                "https://drive.google.com/drive/folders/1-4vzNZWS3IzBBHRXkaqVG8E-UHmU5ON_",
                "https://play.google.com/store/apps/details?id=com.google.android.apps.docs",
                "https://play.google.com/store/apps/details?id=com.google.android.apps.subscriptions.red",
            ]
        )
    if not urls:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(open_urls(urls, profile=args.profile), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
