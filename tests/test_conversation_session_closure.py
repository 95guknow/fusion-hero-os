# -*- coding: utf-8 -*-
"""Abschluss + Archivierung inaktiver Chat-Sessions.

Die Tests bauen einen eigenen Sessions-Baum unter tmp_path nach (Instanz-
Ordner url-encoded wie im echten ~/.grok/sessions) und haengen load_config
um, damit weder ~/.fusion/sicherung noch das Repo beschrieben werden.
"""
from __future__ import annotations

import json
import os
import tarfile
import time
from pathlib import Path

import pytest

from fusion_hero_os.core import conversation_session_closure as csc

INSTANCE = "C%3A%5CProgram%20Files%5CGit"
DAY = 86400.0


def _write(path: Path, text: str, *, age_days: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    stamp = time.time() - age_days * DAY
    os.utime(path, (stamp, stamp))


@pytest.fixture()
def sessions_root(tmp_path: Path) -> Path:
    root = tmp_path / "sessions"
    old = root / INSTANCE / "sess-old"
    _write(old / "chat_history.jsonl", '{"role":"user"}\n', age_days=40)
    _write(old / "summary.json", "{}", age_days=40)
    _write(old / "terminal" / "run.log", "ok\n", age_days=40)
    _write(old / ".env", "TOKEN=must-not-be-archived\n", age_days=40)

    fresh = root / INSTANCE / "sess-fresh"
    _write(fresh / "chat_history.jsonl", '{"role":"user"}\n', age_days=1)

    empty = root / INSTANCE / "sess-empty"
    empty.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture()
def cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Sicherungs-Root, Drive-Spiegel und Repo-Root nach tmp_path umbiegen."""
    drive = tmp_path / "drive_mirror"
    drive.mkdir()
    config = {
        "provider": "google_one",
        "local": {"root": str(tmp_path / "sicherung")},
        "desktop": {"fusion_folder_documents": str(drive)},
        "drive": {"folder_name": "Fusion_Hero_OS_Sicherung"},
        "exclude_globs": ["**/.env*", "**/*secret*"],
        "chat_archive": {"inactive_days": 14, "drive_subfolder": "chat_archives", "gcs_prefix": ""},
    }
    monkeypatch.setattr(csc, "load_config", lambda: config)
    monkeypatch.setattr(csc, "ROOT", tmp_path / "repo")
    monkeypatch.delenv("FUSION_CHAT_ARCHIVE_GCS", raising=False)
    return config


def test_find_sessions_splits_by_idle_age(sessions_root: Path, cfg: dict):
    by_id = {s["session_id"]: s for s in csc.find_sessions(sessions_root, inactive_days=14)}

    assert by_id["sess-old"]["inactive"] is True
    assert by_id["sess-old"]["idle_days"] > 14
    assert by_id["sess-old"]["artifacts"]["dialog_stream"] == 1
    assert by_id["sess-fresh"]["inactive"] is False
    # Ein Ordner ohne datierbares Artefakt ist ein Rest, keine laufende Arbeit.
    assert by_id["sess-empty"]["inactive"] is True
    assert by_id["sess-empty"]["last_activity"] is None


def test_close_is_idempotent_and_seal_does_not_reactivate(sessions_root: Path, cfg: dict):
    first = csc.close_inactive(sessions_root, inactive_days=14)
    assert first["ok"] is True
    assert {s["session_id"] for s in first["closed"]} == {"sess-old", "sess-empty"}
    assert first["still_active"] == ["sess-fresh"]

    seal = json.loads((sessions_root / INSTANCE / "sess-old" / csc.SEAL_NAME).read_text())
    assert seal["schema"] == csc.SEAL_SCHEMA
    assert seal["reason"] == "inactive"
    assert seal["inactive_threshold_days"] == 14
    assert len(seal["fingerprint_sha256"]) == 64

    # Das frisch geschriebene Siegel darf die Session nicht wieder aktiv machen.
    second = csc.close_inactive(sessions_root, inactive_days=14)
    assert second["closed"] == []
    assert sorted(second["already_closed"]) == ["sess-empty", "sess-old"]


def test_dry_run_writes_nothing(sessions_root: Path, cfg: dict):
    result = csc.close_inactive(sessions_root, inactive_days=14, dry_run=True)
    assert result["closed_count"] == 2
    assert not (sessions_root / INSTANCE / "sess-old" / csc.SEAL_NAME).exists()


def test_archive_bundles_closed_sessions_without_secrets(sessions_root: Path, cfg: dict):
    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)

    assert manifest["ok"] is True
    assert manifest["session_count"] == 2
    assert len(manifest["tar_sha256"]) == 64
    assert manifest["sessions_root"] == str(sessions_root)

    with tarfile.open(manifest["tar"]) as tar:
        names = tar.getnames()
    assert f"{INSTANCE}/sess-old/chat_history.jsonl" in names
    assert f"{INSTANCE}/sess-fresh/chat_history.jsonl" not in names
    assert not any(name.endswith(".env") for name in names)
    assert any(entry.startswith("secret_filtered:") for entry in manifest["skipped"])


def test_archive_ledger_skips_unchanged_sessions(sessions_root: Path, cfg: dict):
    csc.close_inactive(sessions_root, inactive_days=14)
    csc.archive_closed(sessions_root, inactive_days=14)

    again = csc.archive_closed(sessions_root, inactive_days=14)
    assert again["session_count"] == 0
    assert again["bundle_id"] is None

    # Bewegt sich die Konversation nach dem Abschluss doch noch, wird neu gebuendelt.
    _write(sessions_root / INSTANCE / "sess-old" / "events.jsonl", "{}\n", age_days=40)
    third = csc.archive_closed(sessions_root, inactive_days=14)
    assert third["session_count"] == 1


def test_transfer_to_drive_mirror_is_verified(sessions_root: Path, cfg: dict, tmp_path: Path):
    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)

    transfer = csc.transfer_to_google(manifest, route="drive")
    assert transfer["ok"] is True
    assert transfer["verified"] is True
    assert transfer["sha256"] == manifest["tar_sha256"]

    dest = Path(transfer["dest"])
    assert dest.is_file()
    assert dest.parent == tmp_path / "drive_mirror" / "chat_archives" / manifest["bundle_id"]
    assert (dest.parent / "manifest.json").is_file()


def test_transfer_dry_run_does_not_copy(sessions_root: Path, cfg: dict, tmp_path: Path):
    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)

    transfer = csc.transfer_to_google(manifest, route="drive", dry_run=True)
    assert transfer["ok"] is True and transfer["dry_run"] is True
    assert not (tmp_path / "drive_mirror" / "chat_archives").exists()


def test_gcs_route_used_when_prefix_configured(
    sessions_root: Path, cfg: dict, monkeypatch: pytest.MonkeyPatch
):
    cfg["chat_archive"]["gcs_prefix"] = "gs://fusion-ai-data/chat_archives"
    uploads: list[tuple[str, str]] = []

    def fake_upload(local_path: Path, prefix: str) -> dict:
        uploads.append((local_path.name, prefix))
        return {"ok": True, "dest": f"{prefix}/{local_path.name}", "backend": "stub"}

    monkeypatch.setattr(csc, "_gcs_upload", fake_upload)

    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)
    transfer = csc.transfer_to_google(manifest, route="auto")

    assert transfer["route"] == "gcs"
    assert transfer["ok"] is True
    bundle_prefix = f"gs://fusion-ai-data/chat_archives/{manifest['bundle_id']}"
    assert uploads == [
        (f"chats_{manifest['bundle_id']}.tar.gz", bundle_prefix),
        ("manifest.json", bundle_prefix),
    ]


def test_purge_refuses_unverified_transfer(sessions_root: Path, cfg: dict):
    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)

    refused = csc.purge_archived(manifest, {"ok": False, "verified": False})
    assert refused["ok"] is False
    assert refused["purged"] == []
    assert (sessions_root / INSTANCE / "sess-old").is_dir()


def test_purge_removes_only_after_verified_transfer(sessions_root: Path, cfg: dict):
    csc.close_inactive(sessions_root, inactive_days=14)
    manifest = csc.archive_closed(sessions_root, inactive_days=14)
    transfer = csc.transfer_to_google(manifest, route="drive")

    purge = csc.purge_archived(manifest, transfer)
    assert purge["ok"] is True
    assert sorted(purge["purged"]) == [f"{INSTANCE}/sess-empty", f"{INSTANCE}/sess-old"]
    assert not (sessions_root / INSTANCE / "sess-old").exists()
    # Die aktive Session bleibt unangetastet.
    assert (sessions_root / INSTANCE / "sess-fresh" / "chat_history.jsonl").is_file()


def test_run_sweep_writes_public_summary(sessions_root: Path, cfg: dict, tmp_path: Path):
    report = csc.run(sessions_root, inactive_days=14, route="drive")

    assert report["ok"] is True
    assert report["close"]["closed_count"] == 2
    assert report["archive"]["session_count"] == 2
    assert report["transfer"]["verified"] is True

    summary = json.loads(
        (tmp_path / "repo" / "docs" / "sicherung" / "last_chat_closure.summary.json").read_text()
    )
    assert summary["sessions_archived"] == 2
    assert summary["transfer_route"] == "drive"
    assert summary["secrets_excluded"] is True
    # Public-safe: Zaehlungen ja, Session-Inhalte nein.
    assert "sessions" not in summary


def test_dry_run_sweep_plans_the_bundle_without_touching_disk(
    sessions_root: Path, cfg: dict, tmp_path: Path
):
    report = csc.run(sessions_root, inactive_days=14, route="drive", dry_run=True)

    # Der Plan muss zeigen, was ein echter Lauf buendeln wuerde — nicht "nichts",
    # nur weil im Dry-Run kein Siegel geschrieben wurde.
    assert report["close"]["closed_count"] == 2
    assert report["archive"]["session_count"] == 2
    assert report["transfer"]["dry_run"] is True

    assert not (sessions_root / INSTANCE / "sess-old" / csc.SEAL_NAME).exists()
    assert not (tmp_path / "sicherung" / "snapshots").exists()
    assert not (tmp_path / "drive_mirror" / "chat_archives").exists()


def test_run_without_transfer_stays_local(sessions_root: Path, cfg: dict, tmp_path: Path):
    report = csc.run(sessions_root, inactive_days=14, transfer=False)

    assert report["ok"] is True
    assert report["transfer"]["skipped"] is True
    assert not (tmp_path / "drive_mirror" / "chat_archives").exists()
    assert Path(report["archive"]["tar"]).is_file()
