#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plattform-Version-Gate: VERSION ist die einzige Quelle der Wahrheit.

Die Datei VERSION im Repo-Root traegt die Plattform-Version (SemVer,
ohne 'v'-Prefix). Release-Tags auf main heissen v<VERSION>. Alle
Paket-Manifeste werden von hier aus synchron gehalten.

Verwendung:
  python scripts/bump_version.py            Manifeste auf VERSION angleichen
  python scripts/bump_version.py 8.4.0      VERSION setzen und angleichen
  python scripts/bump_version.py --check    CI-Gate: Abweichung => Exit 1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"

# Manifeste, die der Plattform-Version folgen. JSON und TOML werden per
# Zeilen-Ersetzung aktualisiert, damit Formatierung (Tabs, Reihenfolge)
# unangetastet bleibt; ersetzt wird jeweils nur der erste Treffer.
JSON_MANIFESTS = [
    REPO_ROOT / "package.json",
    REPO_ROOT / "workstation" / "package.json",
]
TOML_MANIFESTS = [
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "pms_rust_kernel_crate" / "Cargo.toml",
    REPO_ROOT / "rust_engine_crate" / "Cargo.toml",
]

JSON_RE = re.compile(r'("version"\s*:\s*")([^"]+)(")')
TOML_RE = re.compile(r'^(version\s*=\s*")([^"]+)(")', re.MULTILINE)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")


def _read_raw(path: Path) -> str:
    # newline="" laesst CRLF/LF unangetastet, damit sync() keine
    # Ganzdatei-Diffs durch Zeilenenden-Normalisierung erzeugt.
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_raw(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def read_platform_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.match(version):
        sys.exit(f"FEHLER: VERSION enthaelt kein gueltiges SemVer: {version!r}")
    return version


def manifest_version(path: Path, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(_read_raw(path))
    return match.group(2) if match else None


def sync(version: str) -> None:
    for path, pattern in _all_manifests():
        text = _read_raw(path)
        new_text, count = pattern.subn(rf"\g<1>{version}\g<3>", text, count=1)
        if count == 0:
            sys.exit(f"FEHLER: keine version-Zeile gefunden in {path}")
        if new_text != text:
            _write_raw(path, new_text)
            print(f"  angeglichen: {path.relative_to(REPO_ROOT)} -> {version}")


def check(version: str) -> None:
    drift = []
    for path, pattern in _all_manifests():
        found = manifest_version(path, pattern)
        if found != version:
            drift.append(f"  {path.relative_to(REPO_ROOT)}: {found!r} != {version!r}")
    if drift:
        print(f"Plattform-Version-Gate VERLETZT (VERSION = {version}):")
        print("\n".join(drift))
        print("Beheben mit: python scripts/bump_version.py")
        sys.exit(1)
    print(f"Plattform-Version-Gate OK: alle Manifeste auf {version}")


def _all_manifests() -> list[tuple[Path, re.Pattern[str]]]:
    return [(p, JSON_RE) for p in JSON_MANIFESTS] + [(p, TOML_RE) for p in TOML_MANIFESTS]


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check(read_platform_version())
        return
    if args:
        new_version = args[0].lstrip("v")
        if not SEMVER_RE.match(new_version):
            sys.exit(f"FEHLER: kein gueltiges SemVer: {args[0]!r}")
        VERSION_FILE.write_text(new_version + "\n", encoding="utf-8", newline="\n")
        print(f"VERSION -> {new_version}")
    sync(read_platform_version())


if __name__ == "__main__":
    main()
