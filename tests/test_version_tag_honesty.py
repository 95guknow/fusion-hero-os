# -*- coding: utf-8 -*-
"""Gate gegen eine still auseinanderlaufende Versionsaussage.

BRANCH_STRATEGY.md erklaert den annotierten Git-Tag auf ``main`` zur Quelle
der Wahrheit und ``VERSION`` zu dessen Spiegel. Am 2026-08-01 stimmte das
nicht mehr: ``VERSION`` stand auf 15.0.0, letzter Tag war v13.0.0 — zwei
Majors ohne Release.

Was hier NICHT geprueft wird: ob ein Tag existiert. Der Tag-Zustand liegt bei
GitHub, nicht im Repo, und ein CI-Checkout hat Tags oft gar nicht dabei. Ein
Test, der so tut, als pruefe er das, waere schlimmer als keiner.

Geprueft wird das, was im Repo liegt: solange ``VERSION`` dem letzten
veroeffentlichten Release vorausgelaufen ist, muessen beide Dokumente diese
Luecke ausdruecklich benennen — und duerfen die Tag-Regel nicht als
unbedingt geltend hinstellen.

Proof-Registry-Anker: V15-ZWEI-AEREN-OHNE-RELEASE (WIDERLEGT).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"
BEST_VERSION = REPO_ROOT / "BEST_VERSION.md"
BRANCH_STRATEGY = REPO_ROOT / "BRANCH_STRATEGY.md"

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")
# Die Zeile, in der BEST_VERSION.md das letzte tatsaechlich veroeffentlichte
# Release nennt, z. B. "letzte **veroeffentlichte** Release ist `v13.0.0`".
LAST_RELEASE = re.compile(r"[Rr]elease(?:-Tag)?\s*(?:ist|:)?\s*`v(\d+\.\d+\.\d+)`")


def _version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def _last_published() -> str | None:
    m = LAST_RELEASE.search(BEST_VERSION.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _as_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("-")[0].split("."))


def test_version_is_valid_semver():
    v = _version()
    assert SEMVER.match(v), f"VERSION enthaelt kein gueltiges SemVer: {v!r}"


def test_docs_flag_the_gap_when_version_ran_ahead():
    """Laeuft VERSION dem letzten Release voraus, muss BEST_VERSION.md das sagen."""
    version = _version()
    published = _last_published()
    if published is None:
        # Kein Release genannt — dann gibt es auch nichts zu verschweigen.
        return
    if _as_tuple(version) <= _as_tuple(published):
        # Kein Vorlauf, nichts zu benennen.
        return

    text = BEST_VERSION.read_text(encoding="utf-8").lower()
    assert "ungetaggt" in text or "nicht getaggt" in text, (
        f"VERSION ({version}) laeuft dem letzten Release (v{published}) voraus, "
        "aber BEST_VERSION.md benennt den Zustand nicht. Genau so wird aus einer "
        "Luecke eine stille Falschaussage."
    )


def test_branch_strategy_does_not_claim_the_tag_rule_holds_unconditionally():
    """Bei Vorlauf darf BRANCH_STRATEGY.md die Tag-Regel nicht unbedingt behaupten."""
    version = _version()
    published = _last_published()
    if published is None or _as_tuple(version) <= _as_tuple(published):
        return

    text = BRANCH_STRATEGY.read_text(encoding="utf-8").lower()
    assert "nicht getaggt" in text or "gilt derzeit nicht" in text, (
        "BRANCH_STRATEGY.md erklaert den Tag zur Quelle der Wahrheit, waehrend "
        f"VERSION ({version}) ueber dem letzten Release (v{published}) liegt. "
        "Der Vorbehalt muss im Dokument stehen, solange das so ist."
    )
