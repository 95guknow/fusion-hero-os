# -*- coding: utf-8 -*-
"""Persona-scanner gate (v10 Stage-B).

The active integration package ``fusion_hero_os/`` was de-personalised in
Stage-B: the retired persona identifier no longer appears anywhere in it, and
the PII/secret scanner promotes any *reappearance* under that prefix from a
tree-wide warning to a BLOCKING finding (regression guard).

These tests pin that contract:

  * the persona token is classified BLOCKING under ``fusion_hero_os/`` but only
    a warning elsewhere (Stage-C full-tree remediation is still pending),
  * the active package is currently persona-clean on disk.

The persona token is assembled at runtime from fragments so this test file
itself contains no persona literal in tracked content.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "scripts" / "check_pii_scanner.py"

# Assemble the retired persona token without embedding the literal in this file.
_PERSONA_TOKEN = "alte" + "_frau_" + "95g"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("check_pii_scanner", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


scanner = _load_scanner()


def _persona_finding(path: str):
    return scanner.Finding(path=path, line=1, rule="persona_identifier", match=_PERSONA_TOKEN)


def test_persona_regex_matches_assembled_token():
    assert scanner.RULES["persona_identifier"].search(_PERSONA_TOKEN)


def test_persona_blocks_under_active_package_prefix():
    f = _persona_finding("fusion_hero_os/modules/example.py")
    assert scanner.is_blocking(f) is True


def test_persona_is_warning_outside_active_prefix():
    for path in ("docs/v8/history.md", "legacy_sources/old/readme.md",
                 "src/normal_os/tools/thing.py"):
        f = _persona_finding(path)
        assert scanner.is_blocking(f) is False, path


# Operator-Entscheidung 2026-07-25: die Persona-Token bleiben bestehen, der
# Klarname steht im Vordergrund (docs/ops/PERSONA_KLARNAME_KONTRAKT.md).
# Stage-B forderte fusion_hero_os/ AUSNAHMSLOS persona-frei. Das gilt nicht
# mehr fuer die Dateien, deren GEGENSTAND die Identitaet selbst ist — dort das
# Token zu streichen wuerde das Modul inhaltlich aushoehlen. Ueberall sonst im
# aktiven Paket bleibt der Regressions-Guard scharf: eine NEUE Datei mit dem
# Token faellt weiterhin durch.
PERSONA_SUBJECT_FILES = {
    # Modul, das die Identitaet Comaedchen x Persona beschreibt und exportiert.
    "fusion_hero_os/core/comaedchen_identity.py",
    # Eine Zeile: Registry-Beschreibung ebendieses Identity-Moduls.
    "fusion_hero_os/registry.py",
}


def test_active_package_is_persona_free_outside_identity_files():
    """Regressions-Guard mit dokumentierter Ausnahme statt Absolut-Verbot."""
    pattern = scanner.RULES["persona_identifier"]
    offenders = []
    pkg = ROOT / "fusion_hero_os"
    for path in pkg.rglob("*"):
        if not path.is_file() or scanner._should_skip(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in PERSONA_SUBJECT_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(text):
            offenders.append(rel)
    assert offenders == [], (
        "persona token outside the documented identity files: "
        f"{offenders} — entweder entfernen oder bewusst in "
        "PERSONA_SUBJECT_FILES aufnehmen (mit Begruendung)."
    )


def test_persona_subject_files_still_exist():
    """Die Ausnahmeliste darf nicht auf geloeschte Pfade zeigen (stille Erosion)."""
    missing = [rel for rel in PERSONA_SUBJECT_FILES if not (ROOT / rel).is_file()]
    assert missing == [], f"PERSONA_SUBJECT_FILES zeigt auf fehlende Dateien: {missing}"
