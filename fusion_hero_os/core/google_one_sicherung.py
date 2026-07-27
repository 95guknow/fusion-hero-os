"""
Google One Sicherung — activate + local snapshot for Fusion Hero OS.

- Opens Google One landing / storage (operator confirms product backup)
- Marks local activation under ~/.fusion/sicherung
- Creates public-safe snapshot (no secrets) of dissertation/control docs
- Records Drive folder target (Google One storage)

Geltung: Spezifikation (local backup) · Google One product state = operator/Bedingt
Policy: pseudo_inhouse_only · freemium=false · secrets never copied
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

try:
    from fusion_hero_os.core.browser_egress import open_url as _egress_open
except Exception:  # noqa: BLE001
    _egress_open = None  # type: ignore


def _open_browser_url(url: str) -> bool:
    """Open via browser_egress (Chrome for Google) — not blind OS default/Comet."""
    if _egress_open is not None:
        r = _egress_open(url)
        return bool(r.get("ok"))
    try:
        import webbrowser

        return bool(webbrowser.open(url))
    except Exception:
        return False

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "activate",
    "status",
    "run_snapshot",
    "load_config",
    "setup_desktop",
    "setup_phone",
]


def load_config() -> dict[str, Any]:
    path = ROOT / "google_one_sicherung.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(str(p)))


def _local_root(cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    p = _expand((cfg.get("local") or {}).get("root") or "~/.fusion/sicherung")
    p.mkdir(parents=True, exist_ok=True)
    for sub in ("local", "snapshots", "manifests", "google_one"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def _is_excluded(rel: str, exclude: list[str]) -> bool:
    rel_f = rel.replace("\\", "/")
    low = rel_f.lower()
    if any(x in low for x in (".env", "secret", "credential", ".pem", "id_rsa", "push_secret")):
        return True
    for pat in exclude:
        if fnmatch.fnmatch(rel_f, pat) or fnmatch.fnmatch(Path(rel_f).name, pat):
            return True
    return False


def _match_include(rel: str, includes: list[str]) -> bool:
    rel_f = rel.replace("\\", "/")
    for pat in includes:
        if fnmatch.fnmatch(rel_f, pat):
            return True
        # simple ** prefix support via pathlib parts
        if pat.endswith("/**"):
            prefix = pat[:-3].rstrip("/")
            if rel_f == prefix or rel_f.startswith(prefix + "/"):
                return True
    return False


def _sha16_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def activate(*, open_browser: bool = True) -> dict[str, Any]:
    """Activate local sicherung + open Google One URLs."""
    cfg = load_config()
    root = _local_root(cfg)
    now = datetime.now(UTC).isoformat()
    drive = cfg.get("drive") or {}
    flag = {
        "activated": True,
        "activated_at": now,
        "provider": "google_one",
        "landing_url": cfg.get("landing_url") or "https://one.google.com/?g1_landing_page=1",
        "storage_url": cfg.get("storage_url") or "https://one.google.com/storage",
        "drive_folder_name": drive.get("folder_name") or "Fusion_Hero_OS_Sicherung",
        "drive_folder_id": drive.get("folder_id"),
        "drive_web_view_link": drive.get("web_view_link"),
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "secrets_excluded": True,
        "platform": cfg.get("platform_version") or "10.0.0",
        "notes": (
            "Local Fusion sicherung ACTIVE. "
            "Confirm Google One plan/device backup in browser if needed."
        ),
    }
    flag_path = root / "google_one" / "ACTIVATED.json"
    flag_path.write_text(json.dumps(flag, indent=2, ensure_ascii=False), encoding="utf-8")
    # also public-safe status in docs
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    pub = {
        "activated": True,
        "activated_at": now,
        "provider": "google_one",
        "landing_url": flag["landing_url"],
        "storage_url": flag["storage_url"],
        "drive_folder_name": flag["drive_folder_name"],
        "drive_web_view_link": flag.get("drive_web_view_link"),
        "secrets_excluded": True,
        "local_root": str(root),
    }
    (docs / "GOOGLE_ONE_SICHERUNG.md").write_text(
        "\n".join(
            [
                "# Google One Sicherung — aktiv",
                "",
                f"**Status:** ACTIVATED (`{now}`)",
                "**Provider:** Google One + Drive",
                f"**Landing:** {flag['landing_url']}",
                f"**Storage:** {flag['storage_url']}",
                f"**Drive-Ordner:** [{flag['drive_folder_name']}]({flag.get('drive_web_view_link') or '#'})",
                f"**Lokal:** `{root}`",
                "",
                "## Operator (Browser)",
                "",
                "1. https://one.google.com/?g1_landing_page=1 — Plan / Geräte-Backup prüfen",
                "2. https://one.google.com/storage — Speicherplatz prüfen",
                "3. Drive-Ordner `Fusion_Hero_OS_Sicherung` für public-safe Snapshots",
                "4. Google Drive for Desktop: optional Ordner spiegeln",
                "",
                "## CLI",
                "",
                "```powershell",
                "python -m fusion_hero_os.core.google_one_sicherung --activate",
                "python -m fusion_hero_os.core.google_one_sicherung --snapshot",
                "python -m fusion_hero_os.core.google_one_sicherung --status",
                "```",
                "",
                "**Policy:** secrets NEVER · freemium=false · pseudo_inhouse_only",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (docs / "last_activation.summary.json").write_text(
        json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    opened: list[str] = []
    if open_browser:
        for key in ("landing_url", "storage_url"):
            url = cfg.get(key) or flag.get(key)
            if url and _open_browser_url(url):
                opened.append(url)
        link = drive.get("web_view_link")
        if link and _open_browser_url(link):
            opened.append(link)

    return {
        "ok": True,
        "activated": True,
        "flag_path": str(flag_path),
        "drive_folder_id": flag.get("drive_folder_id"),
        "drive_web_view_link": flag.get("drive_web_view_link"),
        "browser_opened": opened,
        "local_root": str(root),
        "docs": str(docs / "GOOGLE_ONE_SICHERUNG.md"),
    }


def run_snapshot() -> dict[str, Any]:
    """Copy public-safe includes into a timestamped local snapshot."""
    cfg = load_config()
    root = _local_root(cfg)
    includes = list(cfg.get("include_globs") or [])
    excludes = list(cfg.get("exclude_globs") or [])
    max_mb = float((cfg.get("policy") or {}).get("max_file_mb") or 25)
    max_b = int(max_mb * 1024 * 1024)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = root / "snapshots" / f"snap_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, Any]] = []
    skipped: list[str] = []
    total = 0
    t0 = time.time()

    for dirpath, _dirnames, filenames in os.walk(ROOT):
        # skip heavy/unwanted trees early
        rel_dir = str(Path(dirpath).relative_to(ROOT)).replace("\\", "/")
        if rel_dir.startswith((".git", "node_modules", "__pycache__", "legacy_sources", ".venv")):
            continue
        for name in filenames:
            path = Path(dirpath) / name
            try:
                rel = str(path.relative_to(ROOT)).replace("\\", "/")
            except ValueError:
                continue
            if _is_excluded(rel, excludes):
                continue
            if includes and not _match_include(rel, includes):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > max_b:
                skipped.append(f"too_large:{rel}")
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(path, target)
            except OSError as e:
                skipped.append(f"copy_fail:{rel}:{e}")
                continue
            sha = _sha16_file(target)
            files.append({"rel": rel, "bytes": size, "sha16": sha})
            total += size

    manifest = {
        "ok": True,
        "snapshot_id": stamp,
        "created_at": datetime.now(UTC).isoformat(),
        "file_count": len(files),
        "bytes_total": total,
        "files": files,
        "skipped": skipped[:50],
        "dest": str(dest),
        "provider": "google_one",
        "drive_folder": (cfg.get("drive") or {}).get("folder_name"),
        "drive_web_view_link": (cfg.get("drive") or {}).get("web_view_link"),
        "secrets_excluded": True,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }
    man_path = root / "manifests" / f"manifest_{stamp}.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "manifests" / "last_snapshot.summary.json").write_text(
        json.dumps(
            {
                "snapshot_id": stamp,
                "file_count": len(files),
                "bytes_total": total,
                "created_at": manifest["created_at"],
                "dest": str(dest),
                "drive_web_view_link": manifest["drive_web_view_link"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    # public docs summary
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "last_snapshot.summary.json").write_text(
        json.dumps(
            {
                "snapshot_id": stamp,
                "file_count": len(files),
                "bytes_total": total,
                "created_at": manifest["created_at"],
                "secrets_excluded": True,
                "provider": "google_one",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest


def _find_drivefs_exe() -> str | None:
    bases = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google" / "Drive File Stream",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Google"
        / "Drive File Stream",
    ]
    for base in bases:
        if not base.is_dir():
            continue
        versions = sorted(
            [p for p in base.iterdir() if p.is_dir() and p.name[0].isdigit()],
            key=lambda p: p.name,
            reverse=True,
        )
        for v in versions:
            exe = v / "GoogleDriveFS.exe"
            if exe.is_file():
                return str(exe)
    return None


def _drivefs_running() -> bool:
    try:
        import subprocess

        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq GoogleDriveFS.exe"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return "GoogleDriveFS.exe" in (r.stdout or "")
    except Exception:
        return False


def _find_my_drive_paths() -> list[str]:
    candidates = [
        Path.home() / "Google Drive",
        Path.home() / "Meine Ablage",
        Path.home() / "My Drive",
        Path("G:/Meine Ablage"),
        Path("G:/My Drive"),
        Path("G:/"),
        Path("H:/Meine Ablage"),
        Path("H:/My Drive"),
    ]
    found: list[str] = []
    for p in candidates:
        try:
            if p.exists():
                found.append(str(p))
        except OSError:
            continue
    # letter scan
    for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
        for name in ("Meine Ablage", "My Drive", "Google Drive"):
            p = Path(f"{letter}:/{name}")
            try:
                if p.is_dir():
                    found.append(str(p))
            except OSError:
                continue
    # unique preserve order
    out: list[str] = []
    for x in found:
        if x not in out:
            out.append(x)
    return out


def setup_desktop(*, open_browser: bool = True, start_app: bool = True) -> dict[str, Any]:
    """Start Drive for Desktop if present; stage local mirror of latest snapshot."""
    cfg = load_config()
    root = _local_root(cfg)
    desk_cfg = cfg.get("desktop") or {}
    exe = _find_drivefs_exe()
    started = False
    if start_app and exe and not _drivefs_running():
        try:
            os.startfile(exe)  # type: ignore[attr-defined]
            started = True
            time.sleep(3)
        except Exception:
            try:
                import subprocess

                subprocess.Popen([exe], close_fds=True)
                started = True
                time.sleep(3)
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "error": f"start_failed:{e}", "exe": exe}

    my_drives = _find_my_drive_paths()
    mirror = root / "drive_mirror"
    mirror.mkdir(parents=True, exist_ok=True)
    snap_root = root / "snapshots"
    latest = None
    if snap_root.is_dir():
        dirs = sorted(
            [p for p in snap_root.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        latest = dirs[0] if dirs else None
    mirror_latest = mirror / "latest_snapshot"
    if latest:
        if mirror_latest.exists():
            shutil.rmtree(mirror_latest, ignore_errors=True)
        shutil.copytree(latest, mirror_latest)

    cloud_folder = None
    cloud_copied = False
    folder_name = (cfg.get("drive") or {}).get("folder_name") or "Fusion_Hero_OS_Sicherung"
    # Primary: Documents/Desktop (DriveFS folder-mirror mode on this workstation)
    docs_candidates = [
        Path.home() / "Documents" / folder_name,
        Path.home() / "Desktop" / folder_name,
    ]
    for cand in docs_candidates:
        try:
            cand.mkdir(parents=True, exist_ok=True)
            (cand / "snapshots").mkdir(exist_ok=True)
            (cand / "phone_uploads").mkdir(exist_ok=True)
            (cand / "manifests").mkdir(exist_ok=True)
            cloud_folder = str(cand)
            if latest:
                dest = cand / "snapshots" / latest.name
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(latest, dest)
                cloud_copied = True
                man_src = root / "manifests"
                if man_src.is_dir():
                    for f in man_src.glob("*.json"):
                        shutil.copy2(f, cand / "manifests" / f.name)
            break
        except OSError:
            continue
    # Secondary: virtual My Drive letter if present
    if not cloud_folder:
        for md in my_drives:
            cand = Path(md) / folder_name
            try:
                cand.mkdir(parents=True, exist_ok=True)
                cloud_folder = str(cand)
                if latest:
                    dest = cand / "snapshots" / latest.name
                    if not dest.exists():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(latest, dest)
                        cloud_copied = True
                break
            except OSError:
                continue

    now = datetime.now(UTC).isoformat()
    state = {
        "ok": True,
        "device": "desktop",
        "updated_at": now,
        "drivefs_exe": exe,
        "drivefs_running": _drivefs_running(),
        "started_now": started,
        "my_drive_paths": my_drives,
        "cloud_fusion_folder": cloud_folder,
        "cloud_copied_latest": cloud_copied,
        "local_mirror": str(mirror_latest if latest else mirror),
        "latest_snapshot": str(latest) if latest else None,
        "drive_web_view_link": (cfg.get("drive") or {}).get("web_view_link"),
        "plan_tb": (cfg.get("plan") or {}).get("capacity_tb", 5),
        "needs_signin": not bool(my_drives) and not cloud_copied,
        "mirror_mode": "documents_desktop_folder_mirror",
        "hint": (
            "Snapshot placed under Documents/Desktop (DriveFS folder mirror → Google One 5TB)"
            if cloud_copied
            else (
                "My Drive letter not visible — using Documents/Desktop mirror roots"
                if not my_drives
                else "Drive mount detected"
            )
        ),
    }
    (root / "google_one" / "DESKTOP_STATE.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "DRIVE_FOR_DESKTOP.md").write_text(
        "\n".join(
            [
                "# Google Drive for Desktop",
                "",
                f"**DriveFS running:** {state['drivefs_running']}",
                f"**Exe:** `{exe or 'not found'}`",
                f"**My Drive paths:** {', '.join(my_drives) or '(noch nicht gemountet — anmelden)'}",
                f"**Cloud folder:** `{cloud_folder or 'pending sign-in'}`",
                f"**Local mirror:** `{state['local_mirror']}`",
                f"**Drive web:** {(cfg.get('drive') or {}).get('web_view_link')}",
                "",
                "## Setup",
                "",
                "```powershell",
                "powershell -File scripts/setup_drive_desktop_phone.ps1",
                "python -m fusion_hero_os.core.google_one_sicherung --desktop --status",
                "```",
                "",
                "1. Taskleiste → Google Drive → **anmelden** (5-TB-Konto).",
                "2. Einstellungen → Streamen oder Spiegeln.",
                "3. Ordner `Fusion_Hero_OS_Sicherung` erscheint in My Drive.",
                "4. Skript erneut ausführen → Snapshot in Cloud kopieren.",
                "",
                "Install falls fehlend: `winget install Google.GoogleDrive`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    opened: list[str] = []
    if open_browser:
        for url in (
            (cfg.get("drive") or {}).get("web_view_link"),
            desk_cfg.get("download_url") or "https://www.google.com/drive/download/",
        ):
            if url and _open_browser_url(url):
                opened.append(url)
    state["browser_opened"] = opened
    return state


def setup_phone(*, open_browser: bool = True) -> dict[str, Any]:
    """Write phone checklist + open app/store links (analog to desktop Drive)."""
    cfg = load_config()
    root = _local_root(cfg)
    phone_cfg = cfg.get("phone") or {}
    phone_dir = root / "phone"
    phone_dir.mkdir(parents=True, exist_ok=True)
    drive = cfg.get("drive") or {}
    links = {
        "drive_android": phone_cfg.get("drive_android")
        or "https://play.google.com/store/apps/details?id=com.google.android.apps.docs",
        "drive_ios": phone_cfg.get("drive_ios")
        or "https://apps.apple.com/app/google-drive/id507874739",
        "one_android": phone_cfg.get("one_android")
        or "https://play.google.com/store/apps/details?id=com.google.android.apps.subscriptions.red",
        "one_ios": phone_cfg.get("one_ios")
        or "https://apps.apple.com/app/google-one/id1454120035",
        "device_backup": phone_cfg.get("device_backup")
        or "https://one.google.com/about/device-backup",
        "drive_folder": drive.get("web_view_link")
        or "https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO",
        "storage": cfg.get("storage_url") or "https://one.google.com/storage",
    }
    checklist = f"""# Handy-Sicherung (analog Drive for Desktop)

**Gleicher Account wie PC · Google One 5 TB**  
**Cloud-Ordner:** [{drive.get('folder_name') or 'Fusion_Hero_OS_Sicherung'}]({links['drive_folder']})

## Apps

| App | Android | iOS |
|-----|---------|-----|
| Google Drive | [Play]({links['drive_android']}) | [App Store]({links['drive_ios']}) |
| Google One | [Play]({links['one_android']}) | [App Store]({links['one_ios']}) |

## Schritte (analog Desktop)

| Desktop | Handy (analog) |
|---------|----------------|
| Drive for Desktop starten | Google Drive App öffnen |
| Mit 5-TB-Konto anmelden | **Derselbe** Google-Account |
| Ordner Fusion_Hero_OS_Sicherung | In Drive-App denselben Ordner öffnen |
| Snapshot spiegeln | Optional: Dateien nach `phone_uploads` hochladen |
| (PC-Dateien) | Google One → **Geräte-Backup** (Fotos, Kontakte, SMS/Android) |

## Checkliste

1. [ ] Google Drive App installiert + Login
2. [ ] Google One App installiert + Login (5 TB sichtbar)
3. [ ] Geräte-Backup aktiv: {links['device_backup']}
4. [ ] Ordner `Fusion_Hero_OS_Sicherung` in Drive sichtbar
5. [ ] Optional: wichtige Handy-Dateien nach `Fusion_Hero_OS_Sicherung/phone_uploads`
6. [ ] Optional Mesh lokal: `powershell -File workstation/mesh_phone_mirror.ps1`

## Policy

Keine Secrets (.env, API-Keys, private GPG) aufs Handy-Backup laden.
"""
    (phone_dir / "HANDY_CHECKLISTE.md").write_text(checklist, encoding="utf-8")
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "HANDY_CHECKLISTE.md").write_text(checklist, encoding="utf-8")
    now = datetime.now(UTC).isoformat()
    state = {
        "ok": True,
        "device": "phone",
        "updated_at": now,
        "links": links,
        "checklist_path": str(phone_dir / "HANDY_CHECKLISTE.md"),
        "docs_path": str(docs / "HANDY_CHECKLISTE.md"),
        "drive_folder": drive.get("folder_name"),
        "plan_tb": (cfg.get("plan") or {}).get("capacity_tb", 5),
        "operator_action": "install apps + enable device backup on phone",
    }
    (root / "google_one" / "PHONE_STATE.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # create phone_uploads marker folder id note (cloud side via Drive app)
    (phone_dir / "phone_uploads.README.txt").write_text(
        "Upload phone files into Drive folder Fusion_Hero_OS_Sicherung/phone_uploads\n"
        f"{links['drive_folder']}\n",
        encoding="utf-8",
    )
    opened: list[str] = []
    if open_browser:
        for key in ("drive_android", "one_android", "device_backup", "drive_folder"):
            url = links.get(key)
            if url and _open_browser_url(url):
                opened.append(url)
    state["browser_opened"] = opened
    return state


def status() -> dict[str, Any]:
    cfg = load_config()
    root = _local_root(cfg)
    flag_path = root / "google_one" / "ACTIVATED.json"
    flag = None
    if flag_path.is_file():
        try:
            flag = json.loads(flag_path.read_text(encoding="utf-8"))
        except Exception:
            flag = {"raw": True}
    last = root / "manifests" / "last_snapshot.summary.json"
    last_snap = None
    if last.is_file():
        try:
            last_snap = json.loads(last.read_text(encoding="utf-8"))
        except Exception:
            pass
    drive = cfg.get("drive") or {}
    desktop_state = None
    phone_state = None
    for name, attr in (
        ("DESKTOP_STATE.json", "desktop"),
        ("PHONE_STATE.json", "phone"),
        ("DESKTOP_PHONE_STATE.json", "desktop_phone"),
    ):
        p = root / "google_one" / name
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if "desktop" in name.lower() and "phone" not in name.lower().replace(
                    "desktop_phone", "x"
                ):
                    desktop_state = data
                elif name.startswith("PHONE"):
                    phone_state = data
            except Exception:
                pass
    # simpler reload
    dp = root / "google_one" / "DESKTOP_STATE.json"
    if dp.is_file():
        try:
            desktop_state = json.loads(dp.read_text(encoding="utf-8"))
        except Exception:
            pass
    pp = root / "google_one" / "PHONE_STATE.json"
    if pp.is_file():
        try:
            phone_state = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "ok": True,
        "activated": bool(flag and flag.get("activated")),
        "flag": flag,
        "provider": "google_one",
        "plan": cfg.get("plan"),
        "landing_url": cfg.get("landing_url"),
        "storage_url": cfg.get("storage_url"),
        "drive_folder_id": drive.get("folder_id"),
        "drive_web_view_link": drive.get("web_view_link"),
        "local_root": str(root),
        "last_snapshot": last_snap,
        "desktop": desktop_state
        or {
            "drivefs_running": _drivefs_running(),
            "drivefs_exe": _find_drivefs_exe(),
            "my_drive_paths": _find_my_drive_paths(),
        },
        "phone": phone_state,
        "config_version": cfg.get("version"),
        "freemium": False,
        "secrets_excluded": True,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Google One Sicherung (Fusion Hero OS)")
    ap.add_argument("--activate", action="store_true", help="activate + open Google One URLs")
    ap.add_argument("--desktop", action="store_true", help="Drive for Desktop setup")
    ap.add_argument("--phone", action="store_true", help="Handy analog checklist + links")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status and not (args.activate or args.snapshot or args.desktop or args.phone):
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    out: dict[str, Any] = {}
    do_all = not (args.activate or args.snapshot or args.status or args.desktop or args.phone)

    if args.activate or do_all:
        out["activate"] = activate(open_browser=not args.no_browser)
    if args.desktop or do_all:
        out["desktop"] = setup_desktop(open_browser=not args.no_browser)
    if args.phone or do_all:
        out["phone"] = setup_phone(open_browser=not args.no_browser)
    if args.snapshot or do_all:
        m = run_snapshot()
        out["snapshot"] = {
            "ok": m["ok"],
            "snapshot_id": m["snapshot_id"],
            "file_count": m["file_count"],
            "bytes_total": m["bytes_total"],
            "dest": m["dest"],
            "drive_web_view_link": m.get("drive_web_view_link"),
            "latency_ms": m["latency_ms"],
        }
    if args.status or do_all:
        out["status"] = status()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
