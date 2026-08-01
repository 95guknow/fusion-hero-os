# -*- coding: utf-8 -*-
"""Struktur-Gates fuer den Human-Confirm-Gate-Workflow (.github/workflows/human-confirm-gate.yml).

Geprueft wird ausschliesslich, was IM REPO liegt: dass der Workflow den von
ihm eroeffneten Check nicht selbst schliessen kann und dafuer auch keine
Rechte beansprucht, die er nicht braucht.

NICHT geprueft — und mit pytest auch nicht pruefbar — ist die Frage, ob ein
Merge tatsaechlich blockiert wird. Das haengt allein an der Branch-Protection-
Konfiguration auf GitHub (Server-State, ausserhalb dieses Repos). Genau diese
Trennung ist der Punkt: am 2026-08-01 wurde PR #105 gemergt, waehrend
`human-confirm/google` pending stand, weil der Check nicht in den Required
Checks eingetragen war. Die Eigenschaften unten galten dabei unveraendert —
sie sind notwendig, aber nicht hinreichend.

Proof-Registry-Anker:
  GATE-WORKFLOW-KANN-SICH-NICHT-SELBST-FREIGEBEN (BEWIESEN, hier)
  GATE-BLOCKIERT-MERGE-TATSAECHLICH             (OFFEN, extern)
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "human-confirm-gate.yml"
GATE_DOC = REPO_ROOT / "docs" / "ops" / "HUMAN_CONFIRM_GATE.md"

# Ein Check-Run wird ueber 'conclusion' abgeschlossen. Taucht eine dieser
# Formen im Workflow auf, koennte er sich selbst gruen setzen — dann waere das
# Google-Bein wertlos, weil GitHub Actions die Schranke allein oeffnen koennte.
SELF_CLOSING_MARKERS = (
    "conclusion",
    "completed",
)

# Rechte, die der Workflow nicht braucht und mit denen er die Schranke
# umkonfigurieren koennte.
FORBIDDEN_PERMISSIONS = (
    "administration",
    "workflows",
)


def _raw() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _doc() -> dict:
    # 'on:' wird von YAML 1.1 als bool True geparst — das ist erwartet.
    return yaml.safe_load(_raw())


def test_gate_workflow_exists_and_is_valid_yaml():
    assert WORKFLOW.is_file(), f"{WORKFLOW.relative_to(REPO_ROOT)} fehlt"
    doc = _doc()
    assert isinstance(doc, dict) and doc.get("name")


def test_gate_workflow_never_closes_its_own_check():
    """Der Workflow darf den Check oeffnen, aber nicht abschliessen.

    Das ist die eigentliche Sicherheitseigenschaft des Google-Beins: nur der
    Apps-Script-Endpoint mit dem separaten, eng gescopten PAT patcht auf
    'success'. Kaeme das in den Workflow, waere die zweite Identitaet weg.
    """
    raw = _raw()
    for marker in SELF_CLOSING_MARKERS:
        assert marker not in raw, (
            f"'{marker}' steht im Gate-Workflow — damit koennte er den eigenen "
            "Check schliessen. Abschliessen darf nur scripts/google_confirm_webapp/."
        )


def test_gate_workflow_opens_the_check_as_pending():
    """Ohne einen eroeffneten pending-Check gibt es nichts, das blockieren koennte."""
    assert "in_progress" in _raw(), (
        "Der Workflow eroeffnet keinen laufenden Check-Run — dann existiert "
        "'human-confirm/google' nie und kann auch nie required werden."
    )


def test_gate_workflow_claims_no_excessive_permissions():
    perms = _doc().get("permissions") or {}
    assert isinstance(perms, dict), "permissions muss explizit gesetzt sein, nicht geerbt"
    for forbidden in FORBIDDEN_PERMISSIONS:
        assert forbidden not in perms, (
            f"permissions.{forbidden} beansprucht — damit liesse sich die "
            "Schranke selbst umkonfigurieren."
        )
    assert perms.get("checks") == "write", "checks: write wird zum Oeffnen gebraucht"
    assert perms.get("contents") in (None, "read"), "contents darf nicht schreibend sein"


def test_gate_doc_does_not_promise_enforcement_unconditionally():
    """Die Doku darf 'kein Merge ohne Bestaetigung' nicht als Tatsache behaupten.

    Sie hat es bis 2026-08-01 getan, waehrend die Durchsetzung an einer
    Branch-Protection-Einstellung hing, die nicht gesetzt war. Der Test haelt
    fest, dass der Vorbehalt im Dokument steht und nicht wieder wegredigiert
    wird — nicht, dass die Durchsetzung existiert.
    """
    assert GATE_DOC.is_file(), f"{GATE_DOC.relative_to(REPO_ROOT)} fehlt"
    text = GATE_DOC.read_text(encoding="utf-8").lower()
    assert "required checks" in text, (
        "Das Dokument muss benennen, dass die Durchsetzung an den Required "
        "Checks der Branch Protection haengt."
    )
    assert "nicht erzwungen" in text or "nicht durchgesetzt" in text, (
        "Das Dokument muss den Zustand benennen, in dem das Gate NICHT "
        "erzwungen wird — sonst liest es sich wieder als Garantie."
    )
