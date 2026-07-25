# -*- coding: utf-8 -*-
"""Struktur-Gates fuer den Coworking-KI-Workflow (.github/workflows/claude-coworking.yml).

Geprueft wird die WORKFLOW-STRUKTUR, nicht das Laufzeitverhalten der Action
(das haengt von GitHub + Secret ab und ist hier nicht testbar). Der Wert
dieser Tests: die Nie-Selbst-Merge-Doktrin und die ehrliche Degradation
koennen nicht unbemerkt wegeditiert werden.

Proof-Registry-Anker: COWORKING-KI-NO-SELF-MERGE.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "claude-coworking.yml"

# Aufrufe, die einen Merge/Approve ausloesen wuerden — im Coworking-Workflow verboten.
FORBIDDEN_MERGE_CALLS = (
    "pulls.merge",
    "merge_pull_request",
    "gh pr merge",
    "pull_request_review_write",
    "gh pr review --approve",
)


def _raw() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _doc() -> dict:
    # 'on:' wird von YAML 1.1 als bool True geparst — das ist erwartet.
    return yaml.safe_load(_raw())


def test_coworking_workflow_exists_and_is_valid_yaml():
    assert WORKFLOW.is_file(), f"{WORKFLOW.relative_to(REPO_ROOT)} fehlt"
    doc = _doc()
    assert isinstance(doc, dict) and doc.get("name")


def test_workflow_reacts_to_comment_and_issue_events():
    doc = _doc()
    triggers = doc.get("on", doc.get(True)) or {}
    for event in ("issue_comment", "pull_request_review_comment", "issues"):
        assert event in triggers, f"Trigger '{event}' fehlt — keine Coworking-Interaktion moeglich"


def test_workflow_has_honest_secret_guard():
    """Ohne ANTHROPIC_API_KEY muss der Workflow das SAGEN, nicht still scheitern."""
    doc = _doc()
    steps = doc["jobs"]["coworking"]["steps"]
    guard = next((s for s in steps if s.get("id") == "guard"), None)
    assert guard is not None, "Secret-Guard-Step fehlt"
    assert "ANTHROPIC_API_KEY" in _raw()
    # Die eigentlichen Arbeits-Steps haengen am Guard-Ergebnis.
    gated = [s for s in steps if "steps.guard.outputs.ready" in str(s.get("if", ""))]
    assert gated, "Kein Step ist an den Secret-Guard gekoppelt"


def test_workflow_contains_no_merge_or_approve_call():
    """Nie-Selbst-Merge-Doktrin (human-confirm-gate.yml) gegen Regression gesichert."""
    raw = _raw()
    hits = [c for c in FORBIDDEN_MERGE_CALLS if c in raw]
    assert hits == [], f"Verbotener Merge-/Approve-Aufruf im Coworking-Workflow: {hits}"


def test_workflow_permissions_are_bounded():
    doc = _doc()
    perms = doc.get("permissions") or {}
    assert perms, "permissions-Block fehlt (kein implizites Voll-Token)"
    assert "administration" not in perms
    assert perms.get("workflows") != "write", "workflows: write erlaubt Self-Rewrite des Gates"


def test_third_party_actions_are_pinned_to_commit_sha():
    """Supply-Chain-Guard (CodeQL Alert 2127): Drittanbieter-Actions muessen auf
    einen 40-stelligen Commit-SHA gepinnt sein. Ein beweglicher Tag wie 'v1'
    kann umgehaengt werden, ein SHA nicht. actions/* ist first-party GitHub und
    von der Regel ausgenommen (so wertet CodeQL es ebenfalls)."""
    doc = _doc()
    unpinned = []
    for step in doc["jobs"]["coworking"]["steps"]:
        uses = str(step.get("uses", ""))
        if not uses or uses.startswith("actions/"):
            continue
        ref = uses.partition("@")[2]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            unpinned.append(uses)
    assert unpinned == [], f"Drittanbieter-Action nicht auf SHA gepinnt: {unpinned}"


@pytest.mark.parametrize("event", ["issue_comment", "pull_request_review_comment"])
def test_trigger_phrase_gate_present_for_comment_events(event):
    """Nicht jeder Kommentar darf einen Lauf starten — '@claude' filtert."""
    doc = _doc()
    condition = str(doc["jobs"]["coworking"]["if"])
    assert event in condition
    assert "@claude" in condition
