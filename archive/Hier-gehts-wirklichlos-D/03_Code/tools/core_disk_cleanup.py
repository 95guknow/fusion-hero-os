#!/usr/bin/env python3
"""
ALTE_Frau_95g Heroic Core - Disk Usage Optimization & Cleanup Script

This script helps keep your local ALTE_Frau_95g_Core folder clean and optimized.

Features:
- Moves old generated images to archive
- Cleans up old ZIP archives
- Removes old log files
- Creates a usage report
- Safe by default (dry-run mode)

Usage:
    python3 core_disk_cleanup.py --help
    python3 core_disk_cleanup.py --execute          # Actually perform cleanup
    python3 core_disk_cleanup.py --dry-run          # Show what would be done
"""

import os
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# ==================== CONFIGURATION ====================
CORE_BASE = Path.home() / "ALTE_Frau_95g_Core"

# Folders
ARCHIVE_DIR = CORE_BASE / "10_Archiv"
TEMP_DIR = CORE_BASE / "99_Temp"

# Age thresholds (in days)
IMAGE_ARCHIVE_AGE = 30          # Move images older than this to archive
ZIP_DELETE_AGE = 60             # Delete ZIPs older than this
LOG_DELETE_AGE = 14             # Delete logs older than this

DRY_RUN = True                  # Safety default
# =======================================================


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def ensure_dirs():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    (ARCHIVE_DIR / "Bilder_Archiv").mkdir(exist_ok=True)
    (ARCHIVE_DIR / "ZIP_Archiv").mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)


def get_file_age_days(path: Path) -> int:
    if not path.exists():
        return 0
    mtime = path.stat().st_mtime
    age = datetime.now() - datetime.fromtimestamp(mtime)
    return age.days


def cleanup_images(dry_run=True):
    log("=== Cleaning up old images ===")
    image_dirs = [
        CORE_BASE / "03_VR_Assets",
        # Add other image folders here if needed
    ]

    moved = 0
    for img_dir in image_dirs:
        if not img_dir.exists():
            continue
        for img_file in img_dir.glob("*.jpg"):
            if get_file_age_days(img_file) > IMAGE_ARCHIVE_AGE:
                target = ARCHIVE_DIR / "Bilder_Archiv" / img_file.name
                if dry_run:
                    log(f"  [DRY] Would move: {img_file.name} → Bilder_Archiv/")
                else:
                    shutil.move(str(img_file), str(target))
                    log(f"  Moved: {img_file.name}")
                moved += 1
    log(f"Images processed: {moved}")


def cleanup_zips(dry_run=True):
    log("=== Cleaning up old ZIP archives ===")
    zip_count = 0
    for zip_file in CORE_BASE.glob("*.zip"):
        if get_file_age_days(zip_file) > ZIP_DELETE_AGE:
            if dry_run:
                log(f"  [DRY] Would delete: {zip_file.name}")
            else:
                zip_file.unlink()
                log(f"  Deleted: {zip_file.name}")
            zip_count += 1
    log(f"ZIPs processed: {zip_count}")


def cleanup_logs(dry_run=True):
    log("=== Cleaning up old log files ===")
    log_count = 0
    for log_file in Path("/tmp").glob("alte_frau_*.log"):
        if get_file_age_days(log_file) > LOG_DELETE_AGE:
            if dry_run:
                log(f"  [DRY] Would delete: {log_file.name}")
            else:
                log_file.unlink()
                log(f"  Deleted: {log_file.name}")
            log_count += 1
    log(f"Log files processed: {log_count}")


def show_disk_usage():
    log("=== Current Disk Usage ===")
    total_size = 0
    for root, dirs, files in os.walk(CORE_BASE):
        for f in files:
            fp = os.path.join(root, f)
            total_size += os.path.getsize(fp)
    log(f"Total size of {CORE_BASE}: {total_size / (1024*1024):.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="ALTE_Frau_95g Disk Cleanup")
    parser.add_argument("--execute", action="store_true", help="Actually perform cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done (default)")
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = not args.execute

    if DRY_RUN:
        log("Running in DRY-RUN mode. Nothing will be changed.")
    else:
        log("Running in EXECUTE mode. Changes will be made!")

    ensure_dirs()
    show_disk_usage()
    cleanup_images(DRY_RUN)
    cleanup_zips(DRY_RUN)
    cleanup_logs(DRY_RUN)
    show_disk_usage()

    log("Cleanup finished.")


if __name__ == "__main__":
    main()
