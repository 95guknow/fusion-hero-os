# -*- coding: utf-8 -*-
"""
Inactive chat sessions: close them, archive them, hand the archive to Google.

The inventory in :mod:`fusion_hero_os.core.conversation_archive_inventory`
records *what exists* under ``~/.grok/sessions``. This module is the next
step: a session that nobody has touched for a while is not work in progress
any more, it is a finished conversation that still behaves like an open one.
Closing it makes that explicit.

Three steps, each usable on its own:

``close``
    A session whose newest artifact is older than ``inactive_days`` gets a
    ``CLOSED.json`` seal written into its directory -- last activity, idle
    days, artifact counts, and a fingerprint over the file index. The seal
    itself is excluded from the activity clock, so closing a session does
    not make it look active again on the next run.

``archive``
    Every sealed session that the ledger has not archived yet goes into one
    timestamped ``.tar.gz`` under the private sicherung root, next to a
    manifest carrying SHA-256 for the bundle and per-session metadata. The
    ledger makes repeated runs idempotent -- this is meant to run unattended.

``transfer``
    The bundle goes to Google: a GCS prefix when one is configured, else the
    Drive-for-Desktop mirror folder from ``google_one_sicherung.yaml``. The
    Drive route is verified by re-hashing the copy.

Privacy follows the vocabulary the rest of the sicherung uses: dialogue
bodies are **deploy** (private -- the tarball never leaves the operator's
own storage), only counts and structure are **push** (public summary under
``docs/sicherung/``). Files whose *names* match the secret patterns in
``google_one_sicherung.yaml`` are left out of the bundle and reported as
skipped; that is a filename filter, not a content scan.

Nothing here deletes a session. ``purge`` exists as an explicit opt-in and
runs only after a transfer has been verified.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import unquote

from fusion_hero_os.core.conversation_archive_inventory import (
    ARTIFACT_NAMES,
    SESSIONS_ROOT,
)
from fusion_hero_os.core.google_one_sicherung import load_config

__all__ = [
    "find_sessions",
    "find_inactive_sessions",
    "close_inactive",
    "archive_closed",
    "transfer_to_google",
    "run",
    "status",
]

ROOT = Path(__file__).resolve().parents[2]

#: Seal written into a closed session directory.
SEAL_NAME = "CLOSED.json"
SEAL_SCHEMA = "fusion.chat.session.closure/1"

#: A session with no artifact newer than this is treated as finished.
DEFAULT_INACTIVE_DAYS = 14

#: Which bundle a session went into -- keeps unattended reruns idempotent.
LEDGER_NAME = "chat_archive_ledger.json"

GCS_TIMEOUT_S = 600.0

#: Filename fragments that never enter a bundle, regardless of config.
SECRET_FRAGMENTS = (
    ".env",
    "secret",
    "credential",
    ".pem",
    "id_rsa",
    "push_secret",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _decode_instance_key(name: str) -> str:
    """C%3A%5CProgram%20Files%5CGit -> C:\\Program Files\\Git"""
    try:
        return unquote(name.replace("%5C", "\\").replace("%3A", ":").replace("+", " "))
    except Exception:  # noqa: BLE001
        return name


def _public_path(p: str) -> str:
    return str(p).replace(str(Path.home()), "~")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sicherung_root(cfg: Optional[Dict[str, Any]] = None, *, create: bool = False) -> Path:
    """
    Private sicherung root. Only creates directories when asked to.

    Resolving a path must stay free of side effects -- a dry run walks
    through here to name the bundle it *would* write, and a plan that
    already left folders behind is not a plan.
    """
    cfg = cfg if cfg is not None else load_config()
    raw = (cfg.get("local") or {}).get("root") or "~/.fusion/sicherung"
    root = Path(os.path.expanduser(str(raw)))
    if create:
        for sub in ("snapshots", "manifests"):
            (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _chat_cfg(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = cfg if cfg is not None else load_config()
    return dict(cfg.get("chat_archive") or {})


def _is_secretish(rel: str, excludes: List[str]) -> bool:
    """Filename-level secret filter -- same patterns the sicherung uses."""
    rel_f = str(rel).replace("\\", "/")
    low = rel_f.lower()
    if any(fragment in low for fragment in SECRET_FRAGMENTS):
        return True
    name = Path(rel_f).name
    return any(fnmatch.fnmatch(rel_f, pat) or fnmatch.fnmatch(name, pat) for pat in excludes)


def _iter_session_dirs(root: Path) -> Iterator[Tuple[Path, Path]]:
    """Yield ``(instance_dir, session_dir)`` for every session under ``root``."""
    for instance_dir in sorted(root.iterdir()):
        if not instance_dir.is_dir() or instance_dir.name.startswith("."):
            continue
        for session_dir in sorted(instance_dir.iterdir()):
            if session_dir.is_dir():
                yield instance_dir, session_dir


def _scan_session(session_dir: Path) -> Dict[str, Any]:
    """
    Index one session: files, sizes, mtimes, artifact kinds.

    ``CLOSED.json`` is deliberately left out of the activity clock. It is
    written *by* this module, so counting it would make every session look
    freshly active the moment it was closed -- and a closed session would
    never stay closed.
    """
    files: List[Dict[str, Any]] = []
    artifacts: Dict[str, int] = {}
    mtime_max = 0.0
    bytes_total = 0

    for dirpath, _dirnames, filenames in os.walk(session_dir):
        for name in filenames:
            path = Path(dirpath) / name
            try:
                stat = path.stat()
            except OSError:
                continue
            rel = str(path.relative_to(session_dir)).replace("\\", "/")
            files.append({"rel": rel, "bytes": stat.st_size, "mtime": int(stat.st_mtime)})
            bytes_total += stat.st_size
            if name != SEAL_NAME:
                mtime_max = max(mtime_max, stat.st_mtime)
            kind = ARTIFACT_NAMES.get(name)
            if kind:
                artifacts[kind] = artifacts.get(kind, 0) + 1
            elif name.endswith(".log"):
                artifacts["terminal_log"] = artifacts.get("terminal_log", 0) + 1

    files.sort(key=lambda entry: entry["rel"])
    return {
        "files": files,
        "file_count": len(files),
        "bytes": bytes_total,
        "artifacts": artifacts,
        "mtime_max": mtime_max,
    }


def _fingerprint(files: List[Dict[str, Any]]) -> str:
    """
    SHA-256 over the file *index*, not the bodies.

    Cheap enough to run over a 300 MB session store on every pass, and still
    changes if anything is added, removed, resized, or rewritten.
    """
    digest = hashlib.sha256()
    for entry in files:
        if entry["rel"] == SEAL_NAME:
            continue
        digest.update(f"{entry['rel']}|{entry['bytes']}|{entry['mtime']}\n".encode("utf-8"))
    return digest.hexdigest()


def find_sessions(
    sessions_root: Optional[Path] = None,
    *,
    inactive_days: Optional[float] = None,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Every session under the root, each marked active/inactive and open/closed."""
    root = Path(sessions_root) if sessions_root else SESSIONS_ROOT
    if inactive_days is None:
        inactive_days = float(_chat_cfg().get("inactive_days") or DEFAULT_INACTIVE_DAYS)
    now = now or _utcnow()
    cutoff = now.timestamp() - float(inactive_days) * 86400.0

    if not root.is_dir():
        return []

    sessions: List[Dict[str, Any]] = []
    for instance_dir, session_dir in _iter_session_dirs(root):
        scan = _scan_session(session_dir)
        mtime = scan["mtime_max"]
        seal_path = session_dir / SEAL_NAME
        # A session with no datable artifact at all is a leftover directory,
        # not something in progress -- treat it as inactive so it gets swept.
        inactive = mtime <= cutoff if mtime else True
        sessions.append(
            {
                "session_id": session_dir.name,
                "instance_key": instance_dir.name,
                "instance_path": _decode_instance_key(instance_dir.name),
                "instance_path_public": _public_path(_decode_instance_key(instance_dir.name)),
                "path": str(session_dir),
                "file_count": scan["file_count"],
                "bytes": scan["bytes"],
                "artifacts": scan["artifacts"],
                "last_activity": (
                    datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat() if mtime else None
                ),
                "idle_days": round((now.timestamp() - mtime) / 86400.0, 2) if mtime else None,
                "inactive": inactive,
                "closed": seal_path.is_file(),
                "fingerprint": _fingerprint(scan["files"]),
                "_files": scan["files"],
            }
        )
    return sessions


def find_inactive_sessions(
    sessions_root: Optional[Path] = None,
    *,
    inactive_days: Optional[float] = None,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """The subset of :func:`find_sessions` that is past the idle threshold."""
    return [
        s
        for s in find_sessions(sessions_root, inactive_days=inactive_days, now=now)
        if s["inactive"]
    ]


def _seal_for(session: Dict[str, Any], *, inactive_days: float, now: datetime) -> Dict[str, Any]:
    return {
        "schema": SEAL_SCHEMA,
        "session_id": session["session_id"],
        "instance_key": session["instance_key"],
        "instance_path_public": session["instance_path_public"],
        "closed_at": now.isoformat(),
        "closed_by": "fusion_hero_os.core.conversation_session_closure",
        "reason": "inactive",
        "inactive_threshold_days": inactive_days,
        "last_activity": session["last_activity"],
        "idle_days": session["idle_days"],
        "file_count": session["file_count"],
        "bytes": session["bytes"],
        "artifacts": session["artifacts"],
        "fingerprint_sha256": session["fingerprint"],
        "fingerprint_scope": "file index (name, size, mtime) -- not dialogue bodies",
    }


def close_inactive(
    sessions_root: Optional[Path] = None,
    *,
    inactive_days: Optional[float] = None,
    now: Optional[datetime] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Seal every inactive session that is not sealed yet.

    Purely additive: one ``CLOSED.json`` per session directory, nothing
    moved, nothing removed. Re-running only touches sessions that crossed
    the threshold since the last pass.
    """
    if inactive_days is None:
        inactive_days = float(_chat_cfg().get("inactive_days") or DEFAULT_INACTIVE_DAYS)
    now = now or _utcnow()
    sessions = find_sessions(sessions_root, inactive_days=inactive_days, now=now)

    closed: List[Dict[str, Any]] = []
    already: List[str] = []
    active: List[str] = []
    failed: List[Dict[str, str]] = []

    for session in sessions:
        if not session["inactive"]:
            active.append(session["session_id"])
            continue
        if session["closed"]:
            already.append(session["session_id"])
            continue
        seal = _seal_for(session, inactive_days=float(inactive_days), now=now)
        if not dry_run:
            try:
                (Path(session["path"]) / SEAL_NAME).write_text(
                    json.dumps(seal, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            except OSError as exc:
                failed.append({"session_id": session["session_id"], "error": str(exc)[:200]})
                continue
        closed.append(seal)

    return {
        "ok": not failed,
        "dry_run": dry_run,
        "inactive_days": float(inactive_days),
        "scanned": len(sessions),
        "closed": closed,
        "closed_count": len(closed),
        "already_closed": already,
        "still_active": active,
        "failed": failed,
    }


def _ledger_path(cfg: Optional[Dict[str, Any]] = None) -> Path:
    return _sicherung_root(cfg) / "manifests" / LEDGER_NAME


def _load_ledger(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    path = _ledger_path(cfg)
    if not path.is_file():
        return {"schema": "fusion.chat.archive.ledger/1", "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("entries", {})
        return data
    except (OSError, json.JSONDecodeError):
        return {"schema": "fusion.chat.archive.ledger/1", "entries": {}}


def _save_ledger(ledger: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> None:
    ledger["updated_at"] = _utcnow().isoformat()
    _sicherung_root(cfg, create=True)
    _ledger_path(cfg).write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _ledger_key(session: Dict[str, Any]) -> str:
    return f"{session['instance_key']}/{session['session_id']}"


def archive_closed(
    sessions_root: Optional[Path] = None,
    *,
    inactive_days: Optional[float] = None,
    now: Optional[datetime] = None,
    dry_run: bool = False,
    assume_closed: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Bundle every sealed-but-not-yet-archived session into one tarball.

    The bundle lands under the private sicherung root, because it carries
    dialogue bodies. A session already in the ledger with an unchanged
    fingerprint is skipped; a changed fingerprint means the conversation
    moved again after closing, so it is bundled afresh.

    ``assume_closed`` holds ledger keys to treat as sealed even though no
    seal is on disk. Only a dry run needs it: closing wrote nothing, so
    without it the plan would claim there is nothing to archive.
    """
    cfg = load_config()
    now = now or _utcnow()
    root = Path(sessions_root) if sessions_root else SESSIONS_ROOT
    sessions = find_sessions(root, inactive_days=inactive_days, now=now)
    ledger = _load_ledger(cfg)
    excludes = list(cfg.get("exclude_globs") or [])

    assumed = assume_closed or set()
    pending = [
        s
        for s in sessions
        if (s["closed"] or _ledger_key(s) in assumed)
        and ledger["entries"].get(_ledger_key(s), {}).get("fingerprint") != s["fingerprint"]
    ]

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = _sicherung_root(cfg) / "snapshots" / f"chats_{stamp}"
    tar_path = bundle_dir / f"chats_{stamp}.tar.gz"

    if not pending:
        return {
            "ok": True,
            "dry_run": dry_run,
            "bundle_id": None,
            "session_count": 0,
            "note": "no closed session awaiting archival",
        }

    entries: List[Dict[str, Any]] = []
    skipped: List[str] = []
    bytes_total = 0
    started = time.time()

    if not dry_run:
        bundle_dir.mkdir(parents=True, exist_ok=True)

    tar = tarfile.open(tar_path, "w:gz") if not dry_run else None
    try:
        for session in pending:
            session_dir = Path(session["path"])
            arc_base = f"{session['instance_key']}/{session['session_id']}"
            included = 0
            included_bytes = 0
            for entry in session["_files"]:
                rel = entry["rel"]
                if _is_secretish(rel, excludes):
                    skipped.append(f"secret_filtered:{arc_base}/{rel}")
                    continue
                if tar is not None:
                    try:
                        tar.add(session_dir / rel, arcname=f"{arc_base}/{rel}")
                    except OSError as exc:
                        skipped.append(f"read_fail:{arc_base}/{rel}:{exc}")
                        continue
                included += 1
                included_bytes += entry["bytes"]
            bytes_total += included_bytes
            entries.append(
                {
                    "session_id": session["session_id"],
                    "instance_key": session["instance_key"],
                    "instance_path_public": session["instance_path_public"],
                    "arc_base": arc_base,
                    "file_count": included,
                    "bytes": included_bytes,
                    "artifacts": session["artifacts"],
                    "last_activity": session["last_activity"],
                    "idle_days": session["idle_days"],
                    "fingerprint": session["fingerprint"],
                }
            )
    finally:
        if tar is not None:
            tar.close()

    manifest: Dict[str, Any] = {
        "schema": "fusion.chat.archive.bundle/1",
        "ok": True,
        "bundle_id": stamp,
        "created_at": now.isoformat(),
        # Recorded so purge resolves the same directories that were bundled,
        # even when the sweep ran against a non-default sessions root.
        "sessions_root": str(root),
        "session_count": len(entries),
        "file_count": sum(e["file_count"] for e in entries),
        "bytes_total": bytes_total,
        "sessions": entries,
        "skipped": skipped[:50],
        "skipped_count": len(skipped),
        "secrets_excluded": True,
        "visibility": "deploy=private (dialogue bodies stay in operator storage)",
        "dry_run": dry_run,
        "latency_ms": round((time.time() - started) * 1000, 2),
    }

    # Set on a dry run too -- it is the path the bundle *would* take, which is
    # what makes the planned transfer legible instead of "nothing archived".
    manifest["tar"] = str(tar_path)
    if not dry_run:
        manifest["tar_bytes"] = tar_path.stat().st_size
        manifest["tar_sha256"] = _sha256_file(tar_path)
        (bundle_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        for session in pending:
            ledger["entries"][_ledger_key(session)] = {
                "bundle_id": stamp,
                "fingerprint": session["fingerprint"],
                "archived_at": now.isoformat(),
            }
        _save_ledger(ledger, cfg)

    manifest["bundle_dir"] = str(bundle_dir)
    return manifest


def _gcs_prefix(cfg: Optional[Dict[str, Any]] = None) -> str:
    env = os.environ.get("FUSION_CHAT_ARCHIVE_GCS", "").strip()
    if env:
        return env
    return str(_chat_cfg(cfg).get("gcs_prefix") or "").strip()


def _gcs_upload(local_path: Path, prefix: str) -> Dict[str, Any]:
    """
    Push one file to GCS: official client first, then the gcloud CLIs.

    Mirrors ``scripts/mesh_cluster_coordinator.upload_gcs`` -- on a machine
    with Workload Identity the client just works, on the operator's
    workstation only the CLI is usually present.
    """
    if not prefix.startswith("gs://"):
        return {"ok": False, "error": f"invalid gcs prefix: {prefix}"}
    raw = prefix[len("gs://") :].rstrip("/")
    bucket_name, _, blob_prefix = raw.partition("/")
    object_name = f"{blob_prefix.rstrip('/')}/{local_path.name}".lstrip("/")
    dest = f"gs://{bucket_name}/{object_name}"
    client_error: Optional[str] = None

    try:
        from google.cloud import storage  # type: ignore

        client = storage.Client()
        client.bucket(bucket_name).blob(object_name).upload_from_filename(str(local_path))
        return {"ok": True, "dest": dest, "backend": "google-cloud-storage"}
    except ImportError:
        client_error = "google-cloud-storage not installed"
    except Exception as exc:  # noqa: BLE001
        client_error = str(exc)[:400]

    for command in (["gcloud", "storage", "cp"], ["gsutil", "cp"]):
        try:
            proc = subprocess.run(
                [*command, str(local_path), dest],
                capture_output=True,
                text=True,
                timeout=GCS_TIMEOUT_S,
                check=False,
            )
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "error": f"{command[0]} timeout",
                "dest": dest,
                "client_error": client_error,
            }
        if proc.returncode == 0:
            return {"ok": True, "dest": dest, "backend": command[0]}
        client_error = (proc.stderr or "").strip()[:400] or client_error

    return {
        "ok": False,
        "error": "no usable GCS backend (client, gcloud, gsutil all unavailable)",
        "dest": dest,
        "client_error": client_error,
    }


def _drive_mirror_dir(cfg: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """First Drive-for-Desktop mirror folder that actually exists locally."""
    desktop = (cfg if cfg is not None else load_config()).get("desktop") or {}
    for key in ("fusion_folder_documents", "fusion_folder_desktop", "mirror_local"):
        raw = desktop.get(key)
        if not raw:
            continue
        path = Path(os.path.expanduser(str(raw)))
        if path.is_dir():
            return path
    return None


def transfer_to_google(
    manifest: Dict[str, Any],
    *,
    route: str = "auto",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Hand a finished bundle to Google.

    ``auto`` prefers a configured GCS prefix and falls back to the
    Drive-for-Desktop mirror. The Drive copy is verified by re-hashing the
    destination -- a mirror folder that silently truncates a 300 MB tarball
    would otherwise look like a success.
    """
    cfg = load_config()
    tar_raw = manifest.get("tar")
    if not tar_raw:
        return {"ok": False, "error": "manifest carries no bundle (nothing archived)"}
    tar_path = Path(tar_raw)
    if not dry_run and not tar_path.is_file():
        return {"ok": False, "error": f"bundle missing: {tar_path}"}

    prefix = _gcs_prefix(cfg)
    chosen = route
    if route == "auto":
        chosen = "gcs" if prefix else "drive"

    if chosen == "gcs":
        if not prefix:
            return {"ok": False, "error": "route=gcs but no gcs_prefix configured"}
        bundle_prefix = f"{prefix.rstrip('/')}/{manifest['bundle_id']}"
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "route": "gcs",
                "dest": f"{bundle_prefix}/{tar_path.name}",
            }
        result = _gcs_upload(tar_path, bundle_prefix)
        manifest_result = _gcs_upload(tar_path.parent / "manifest.json", bundle_prefix)
        return {
            "route": "gcs",
            "ok": bool(result.get("ok")),
            "verified": bool(result.get("ok")),
            "manifest_upload": manifest_result,
            **result,
        }

    mirror = _drive_mirror_dir(cfg)
    subfolder = str(_chat_cfg(cfg).get("drive_subfolder") or "chat_archives")
    if mirror is None:
        return {
            "ok": False,
            "route": "drive",
            "error": (
                "no Drive-for-Desktop mirror folder found -- run "
                "`python -m fusion_hero_os.core.google_one_sicherung --desktop` first"
            ),
        }
    dest_dir = mirror / subfolder / str(manifest["bundle_id"])
    if dry_run:
        return {"ok": True, "dry_run": True, "route": "drive", "dest": str(dest_dir)}

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_tar = dest_dir / tar_path.name
    try:
        shutil.copy2(tar_path, dest_tar)
        shutil.copy2(tar_path.parent / "manifest.json", dest_dir / "manifest.json")
    except OSError as exc:
        return {"ok": False, "route": "drive", "dest": str(dest_dir), "error": str(exc)[:300]}

    dest_sha = _sha256_file(dest_tar)
    verified = dest_sha == manifest.get("tar_sha256")
    return {
        "ok": verified,
        "route": "drive",
        "backend": "drive_for_desktop_mirror",
        "dest": str(dest_tar),
        "dest_public": _public_path(str(dest_tar)),
        "verified": verified,
        "sha256": dest_sha,
        "drive_folder": (cfg.get("drive") or {}).get("folder_name"),
        "note": "Drive client uploads the mirror folder in the background",
        **({} if verified else {"error": "sha256 mismatch after copy"}),
    }


def purge_archived(manifest: Dict[str, Any], transfer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove the session directories of a bundle that reached Google intact.

    Opt-in only, and gated twice: the transfer must report ``verified`` and
    the bundle must still hash to what the manifest recorded. Losing a
    conversation because a copy half-failed is not recoverable.
    """
    if not transfer.get("verified"):
        return {"ok": False, "purged": [], "error": "transfer not verified -- refusing to purge"}
    tar_path = Path(manifest.get("tar", ""))
    if not tar_path.is_file() or _sha256_file(tar_path) != manifest.get("tar_sha256"):
        return {"ok": False, "purged": [], "error": "local bundle missing or altered"}

    root = Path(manifest.get("sessions_root") or SESSIONS_ROOT)
    purged: List[str] = []
    failed: List[Dict[str, str]] = []
    for entry in manifest.get("sessions") or []:
        session_dir = root / entry["instance_key"] / entry["session_id"]
        if not session_dir.is_dir():
            continue
        try:
            shutil.rmtree(session_dir)
            purged.append(entry["arc_base"])
        except OSError as exc:
            failed.append({"session": entry["arc_base"], "error": str(exc)[:200]})
    return {"ok": not failed, "purged": purged, "purged_count": len(purged), "failed": failed}


def run(
    sessions_root: Optional[Path] = None,
    *,
    inactive_days: Optional[float] = None,
    route: str = "auto",
    transfer: bool = True,
    purge: bool = False,
    dry_run: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Close, archive, transfer -- the whole sweep, safe to run unattended."""
    cfg = load_config()
    now = now or _utcnow()
    report: Dict[str, Any] = {
        "schema": "fusion.chat.closure.run/1",
        "started_at": now.isoformat(),
        "dry_run": dry_run,
        "sessions_root": _public_path(str(sessions_root or SESSIONS_ROOT)),
    }

    closing = close_inactive(
        sessions_root, inactive_days=inactive_days, now=now, dry_run=dry_run
    )
    report["close"] = closing

    archiving = archive_closed(
        sessions_root,
        inactive_days=inactive_days,
        now=now,
        dry_run=dry_run,
        # A dry run left no seals on disk; carry the planned ones forward so
        # the plan shows the bundle a real sweep would build.
        assume_closed=(
            {f"{s['instance_key']}/{s['session_id']}" for s in closing.get("closed") or []}
            if dry_run
            else None
        ),
    )
    report["archive"] = archiving

    if transfer and archiving.get("session_count"):
        report["transfer"] = transfer_to_google(archiving, route=route, dry_run=dry_run)
    else:
        report["transfer"] = {
            "ok": True,
            "skipped": True,
            "reason": "nothing to transfer" if transfer else "transfer disabled",
        }

    if purge and not dry_run:
        report["purge"] = purge_archived(archiving, report["transfer"])
    elif purge:
        report["purge"] = {"ok": True, "dry_run": True, "purged": []}

    report["ok"] = bool(
        closing.get("ok")
        and archiving.get("ok")
        and report["transfer"].get("ok")
        and report.get("purge", {"ok": True}).get("ok")
    )
    report["finished_at"] = _utcnow().isoformat()

    if not dry_run:
        _write_run_records(report, archiving, cfg)
    return report


def _write_run_records(
    report: Dict[str, Any], archiving: Dict[str, Any], cfg: Dict[str, Any]
) -> None:
    """Private run manifest, plus the public-safe counts-only summary."""
    manifests = _sicherung_root(cfg, create=True) / "manifests"
    stamp = archiving.get("bundle_id") or _utcnow().strftime("%Y%m%dT%H%M%SZ")
    (manifests / f"chat_closure_{stamp}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "schema": "fusion.chat.closure.summary/1",
        "run_at": report.get("finished_at"),
        "ok": report.get("ok"),
        "inactive_days": report.get("close", {}).get("inactive_days"),
        "sessions_scanned": report.get("close", {}).get("scanned"),
        "sessions_closed": report.get("close", {}).get("closed_count"),
        "sessions_archived": archiving.get("session_count"),
        "bundle_id": archiving.get("bundle_id"),
        "bytes_total": archiving.get("bytes_total"),
        "transfer_route": report.get("transfer", {}).get("route"),
        "transfer_ok": report.get("transfer", {}).get("ok"),
        "secrets_excluded": True,
        "visibility": "push=public (counts only) · deploy=private (bodies)",
    }
    (manifests / "last_chat_closure.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "last_chat_closure.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def status() -> Dict[str, Any]:
    """What the last sweep did, and what is waiting for the next one."""
    cfg = load_config()
    summary_path = _sicherung_root(cfg) / "manifests" / "last_chat_closure.summary.json"
    last: Optional[Dict[str, Any]] = None
    if summary_path.is_file():
        try:
            last = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            last = None

    sessions = find_sessions()
    ledger = _load_ledger(cfg)
    return {
        "ok": True,
        "sessions_root": _public_path(str(SESSIONS_ROOT)),
        "sessions_root_present": SESSIONS_ROOT.is_dir(),
        "inactive_days": float(_chat_cfg(cfg).get("inactive_days") or DEFAULT_INACTIVE_DAYS),
        "total": len(sessions),
        "inactive": sum(1 for s in sessions if s["inactive"]),
        "closed": sum(1 for s in sessions if s["closed"]),
        "open_inactive": sum(1 for s in sessions if s["inactive"] and not s["closed"]),
        "archived_in_ledger": len(ledger.get("entries") or {}),
        "gcs_prefix": _gcs_prefix(cfg) or None,
        "drive_mirror": _public_path(str(_drive_mirror_dir(cfg) or "")) or None,
        "last_run": last,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Close inactive chat sessions, archive them, transfer to Google."
    )
    parser.add_argument("--status", action="store_true", help="report state, change nothing")
    parser.add_argument("--list", action="store_true", help="list inactive sessions and exit")
    parser.add_argument("--close-only", action="store_true", help="seal sessions, do not archive")
    parser.add_argument("--no-transfer", action="store_true", help="archive locally, do not upload")
    parser.add_argument(
        "--route",
        choices=["auto", "gcs", "drive"],
        default="auto",
        help="transfer target (default: gcs when configured, else Drive mirror)",
    )
    parser.add_argument(
        "--inactive-days",
        type=float,
        default=None,
        help=f"idle threshold in days (default: config, else {DEFAULT_INACTIVE_DAYS})",
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="delete archived sessions after a verified transfer (destructive, opt-in)",
    )
    parser.add_argument("--dry-run", action="store_true", help="plan only, write nothing")
    parser.add_argument("--sessions-root", default=None, help="override ~/.grok/sessions")
    args = parser.parse_args(argv)

    root = Path(args.sessions_root) if args.sessions_root else None

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0

    if args.list:
        found = find_inactive_sessions(root, inactive_days=args.inactive_days)
        print(
            json.dumps(
                [{k: v for k, v in s.items() if not k.startswith("_")} for s in found],
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.close_only:
        result = close_inactive(root, inactive_days=args.inactive_days, dry_run=args.dry_run)
    else:
        result = run(
            root,
            inactive_days=args.inactive_days,
            route=args.route,
            transfer=not args.no_transfer,
            purge=args.purge,
            dry_run=args.dry_run,
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
