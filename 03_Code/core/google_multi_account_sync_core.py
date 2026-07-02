# google_multi_account_sync_core.py
# Fusion Hero OS v1.2

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class GoogleMultiAccountSyncCoreModule:
    """Multi-Account-Sync mit lokalem Horkrux-Fallback (.fusion/sync/)."""

    def __init__(self, sync_root: Optional[Path] = None):
        self.sync_targets: List[str] = []
        self.last_sync: datetime.datetime = datetime.datetime.now()
        self.dimension_6_score: int = 100
        repo = Path(__file__).resolve().parents[2]
        self.sync_root = sync_root or (repo / ".fusion" / "sync")
        self.sync_root.mkdir(parents=True, exist_ok=True)

    def _hash_payload(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()[:16]

    def _local_snapshot(self, horkrux_id: str) -> Dict[str, str]:
        """Erstellt lokales Delta-Snapshot-Manifest für Horkrux-State."""
        repo = Path(__file__).resolve().parents[2]
        manifest: Dict[str, str] = {}
        watch_dirs = [
            repo / "03_Code" / "core",
            repo / "01_Framework" / "heroic-core-foundation",
        ]
        for base in watch_dirs:
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                rel = str(path.relative_to(repo))
                try:
                    manifest[rel] = self._hash_payload(path.read_bytes())
                except OSError:
                    continue
        out_dir = self.sync_root / horkrux_id
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    def sync_horkrux(
        self,
        horkrux_id: str,
        target_accounts: List[str],
        sync_mode: str = "delta",
    ) -> Dict:
        self.last_sync = datetime.datetime.now()
        manifest = {}
        if sync_mode in ("full", "delta"):
            manifest = self._local_snapshot(horkrux_id)

        remote_note = "google_drive_api_not_configured"
        if os.getenv("GOOGLE_DRIVE_SYNC", "0") == "1":
            remote_note = "google_drive_sync_pending_implementation"

        integrity = len(manifest)
        self.dimension_6_score = min(100, 60 + min(integrity, 40))

        log_entry = {
            "horkrux_id": horkrux_id,
            "targets": target_accounts,
            "mode": sync_mode,
            "files": integrity,
            "ts": self.last_sync.isoformat(),
        }
        log_path = self.sync_root / "sync_log.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return {
            "status": "success",
            "horkrux_id": horkrux_id,
            "synced_accounts": target_accounts,
            "local_manifest_files": integrity,
            "sync_root": str(self.sync_root),
            "remote": remote_note,
            "dimension_6_score": self.dimension_6_score,
            "timestamp": self.last_sync.isoformat(),
        }

    def sync_all(self, horkrux_id: str = "fusion-hero-os-main") -> Dict:
        targets = self.sync_targets or ["local-mainframe"]
        return self.sync_horkrux(horkrux_id, targets, sync_mode="delta")

    def register_target(self, account_or_folder: str) -> None:
        if account_or_folder not in self.sync_targets:
            self.sync_targets.append(account_or_folder)

    def status(self) -> Dict:
        return {
            "targets": self.sync_targets,
            "sync_root": str(self.sync_root),
            "last_sync": self.last_sync.isoformat(),
            "dimension_6_score": self.dimension_6_score,
        }