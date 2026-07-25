# -*- coding: utf-8 -*-
"""Asset-path & persona-token gate (v10 Stage-A).

Guards the class of defect that a content-only PII scrub introduced: string
references were rewritten while the underlying files / directories kept their
old (unprofessional) names, producing dangling references. These tests assert:

  * every VR asset referenced by the manifests / runtime exists on disk,
  * the legacy path referenced by the cherry-pick script exists,
  * no unprofessional persona token survives in tracked paths or references.

The bare word "jailbreak" is a legitimate LLM-security term and is *not*
forbidden; only persona spellings ("Mr./Mister Jailbreak", "jailbait") are.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]

# Forbidden persona spellings (case-insensitive). Bare "jailbreak" is allowed.
_FORBIDDEN_CONTENT = re.compile(
    r"jailbait|mister[ _-]jailbreak|mr\.?\s*jailbreak", re.IGNORECASE
)
_FORBIDDEN_PATH = re.compile(r"jailbait|jailbreak", re.IGNORECASE)

# Dangling intermediate token from the scrub that must never persist.
_DANGLING = re.compile(r"vr_mister_(jailbait|Contributor)|mister-(jailbait|Contributor)-gui")

# These gate tests intentionally embed the forbidden tokens as detection
# patterns; exclude them from the content scans they implement.
_SELF_ALLOWLIST = {
    "tests/test_asset_persona_paths.py",
    "tests/test_archive_salt.py",
}


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


def _is_text(p: Path) -> bool:
    try:
        with open(p, "rb") as f:
            chunk = f.read(4096)
        return b"\x00" not in chunk
    except OSError:
        return False


VR_ASSET_FILES = [
    "03_VR_Assets/vr_builder_hero_equirectangular.jpg",
    "src/normal_os/vr/03_VR_Assets/vr_builder_hero_equirectangular.jpg",
    "src/normal_os/vr/assets/vr_builder_hero_equirectangular.jpg",
]

LEGACY_PATHS = [
    "legacy_sources/mister-builder-gui/lib/heroic-core.js",
    "legacy_sources/mister-builder-gui/package.json",
    "legacy_sources/mister-builder-gui/README.md",
]


@pytest.mark.parametrize("rel", VR_ASSET_FILES)
def test_vr_asset_file_exists(rel: str):
    assert (ROOT / rel).is_file(), f"missing VR asset: {rel}"


@pytest.mark.parametrize("rel", LEGACY_PATHS)
def test_legacy_gui_path_exists(rel: str):
    assert (ROOT / rel).is_file(), f"missing legacy path: {rel}"


def test_cherry_pick_referenced_path_exists():
    script = (ROOT / "scripts/apply_cherry_picks.py").read_text(encoding="utf-8")
    assert "mister-builder-gui" in script
    assert "mister-jailbait-gui" not in script
    assert "mister-Contributor-gui" not in script
    assert (ROOT / "legacy_sources/mister-builder-gui/lib/heroic-core.js").is_file()


@pytest.mark.skipif(yaml is None, reason="pyyaml not available")
def test_asset_manifest_paths_resolve():
    manifest = ROOT / "03_Code/tools/asset_manifest.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    vr_assets = data["categories"]["vr"]["assets"]
    vr_ids = {a["id"] for a in vr_assets}
    assert "vr_builder_hero_equirectangular" in vr_ids
    for asset in vr_assets:
        rel = asset["rel_path"]
        assert not _FORBIDDEN_PATH.search(rel), f"persona token in manifest path: {rel}"
        assert (ROOT / rel).is_file(), f"manifest rel_path missing on disk: {rel}"


def test_no_persona_token_in_tracked_paths():
    offenders = [p for p in _tracked_files() if _FORBIDDEN_PATH.search(p)]
    assert not offenders, f"unprofessional token in tracked paths: {offenders}"


def test_no_dangling_scrub_reference():
    offenders: list[str] = []
    for rel in _tracked_files():
        assert not _DANGLING.search(rel), f"dangling token in path: {rel}"
        if rel in _SELF_ALLOWLIST:
            continue
        p = ROOT / rel
        if not p.is_file() or not _is_text(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        if _DANGLING.search(text):
            offenders.append(rel)
    assert not offenders, f"dangling scrub token in content: {offenders}"


# Operator-Entscheidung 2026-07-25: die Persona bleibt bestehen, der Klarname
# steht im Vordergrund (docs/ops/PERSONA_KLARNAME_KONTRAKT.md). Das frühere
# Absolut-Verbot der Persona-Schreibweise im INHALT gilt damit nicht mehr —
# wohl aber weiterhin in PFADEN (test_no_persona_token_in_tracked_paths), denn
# Datei- und Verzeichnisnamen sind die öffentlich sichtbare Oberfläche.
#
# Die Nennungen bleiben auf diese bekannten Stellen begrenzt, damit sich die
# Persona nicht unbemerkt neu im Baum ausbreitet: eine NEUE Datei mit der
# Schreibweise fällt weiterhin durch.
_PERSONA_CONTENT_ALLOWLIST = {
    # Protokollname in der Modulliste des Mainframe-Skills (zwei Spiegel).
    ".grok/skills/mainframe-laden/SKILL.md",
    "01_Framework/skills/mainframe-laden/SKILL.md",
    # Business-Dokumente nennen die Persona ausschließlich als NEGATIV-Regel
    # ("nur implizit heroisch – keine explicit ..."), also gerade um sie aus
    # geschäftlicher Kommunikation herauszuhalten.
    "business/STEPHAN_HAGEN_URBAN_BUSINESS_PERSONA_PUBLICATION.md",
    "business/auto_recognition_stephan_hagen_urban.py",
}


def test_persona_spelling_stays_within_known_files():
    """Eindämmung statt Verbot: die Persona darf bestehen, aber nicht wuchern."""
    offenders: list[str] = []
    for rel in _tracked_files():
        if rel in _SELF_ALLOWLIST or rel in _PERSONA_CONTENT_ALLOWLIST:
            continue
        p = ROOT / rel
        if not p.is_file() or not _is_text(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        if _FORBIDDEN_CONTENT.search(text):
            offenders.append(rel)
    assert not offenders, (
        f"Persona-Schreibweise in neuen Dateien: {offenders} — entweder "
        "entfernen oder bewusst in _PERSONA_CONTENT_ALLOWLIST aufnehmen."
    )


def test_persona_content_allowlist_has_no_dead_entries():
    """Die Allowlist darf nicht auf geloeschte Pfade zeigen (stille Erosion)."""
    tracked = set(_tracked_files())
    dead = sorted(rel for rel in _PERSONA_CONTENT_ALLOWLIST if rel not in tracked)
    assert dead == [], f"_PERSONA_CONTENT_ALLOWLIST zeigt auf untracked/fehlende Pfade: {dead}"
