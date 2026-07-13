# -*- coding: utf-8 -*-
"""Proof-Registry-Gate: erzwingt Claim-vs-Substanz-Deckung maschinell.

Prueft proof_registry.yaml gegen die reale Test-Suite:

  1. Schema: jeder Claim hat id, statement, status in {BEWIESEN, OFFEN, WIDERLEGT}.
  2. BEWIESEN/WIDERLEGT => proofs nicht leer.
  3. Jeder referenzierte proof-Knoten EXISTIERT in der pytest-Collection
     (Tippfehler/geloeschte Tests lassen das Gate sofort scheitern).
  4. Keine doppelten Claim-IDs.
  5. --run: fuehrt zusaetzlich alle referenzierten Beweis-Knoten aus.

Bewusst NICHT Teil von v1 (ehrlich dokumentiert statt behauptet):
  * Doc-Scan (Claims, die in Markdown als "bewiesen" zitiert werden, ohne in
    der Registry BEWIESEN zu sein) — geplanter Ausbau.

Aufruf:
    python scripts/check_proof_registry.py           # strukturelle Pruefung
    python scripts/check_proof_registry.py --run     # + Beweis-Knoten ausfuehren
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "proof_registry.yaml"
VALID_STATUS = {"BEWIESEN", "OFFEN", "WIDERLEGT"}


def load_claims() -> list[dict]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "claims" not in data:
        raise SystemExit("[FEHLER] proof_registry.yaml: Top-Level 'claims' fehlt.")
    return data["claims"]


def collect_test_nodes() -> set[str]:
    """Alle existierenden pytest-Knoten-IDs (relativ zum Repo-Root, '/'-Pfade)."""
    # -o addopts= neutralisiert das "-q" aus pyproject.toml — sonst wird die
    # Collection zu -qq (nur Datei-Zaehler) und enthaelt keine Knoten-IDs mehr.
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode not in (0, 5):  # 5 = keine Tests gefunden
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("[FEHLER] pytest-Collection fehlgeschlagen.")
    nodes = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if "::" in line:
            nodes.add(line.replace("\\", "/"))
    return nodes


def structural_check(claims: list[dict], nodes: set[str]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for c in claims:
        cid = str(c.get("id", "<ohne id>"))
        if cid in seen_ids:
            errors.append(f"{cid}: doppelte Claim-ID.")
        seen_ids.add(cid)

        status = c.get("status")
        if status not in VALID_STATUS:
            errors.append(f"{cid}: ungueltiger status {status!r} (erlaubt: {sorted(VALID_STATUS)}).")
            continue
        if not str(c.get("statement", "")).strip():
            errors.append(f"{cid}: leeres statement.")

        proofs = c.get("proofs") or []
        if status in ("BEWIESEN", "WIDERLEGT") and not proofs:
            errors.append(f"{cid}: status {status}, aber keine proofs — Claim-vs-Substanz-Luecke.")
        for p in proofs:
            if p.replace("\\", "/") not in nodes:
                errors.append(f"{cid}: proof-Knoten existiert nicht in der Collection: {p}")
    return errors


def run_proofs(claims: list[dict]) -> int:
    node_ids = sorted({
        p for c in claims if c.get("status") in ("BEWIESEN", "WIDERLEGT")
        for p in (c.get("proofs") or [])
    })
    if not node_ids:
        print("[OK] Keine auszufuehrenden Beweis-Knoten.")
        return 0
    print(f"[..] Fuehre {len(node_ids)} Beweis-Knoten aus ...")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *node_ids], cwd=ROOT)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Beweis-Knoten zusaetzlich ausfuehren")
    args = parser.parse_args()

    claims = load_claims()
    nodes = collect_test_nodes()
    errors = structural_check(claims, nodes)

    n_bew = sum(1 for c in claims if c.get("status") == "BEWIESEN")
    n_off = sum(1 for c in claims if c.get("status") == "OFFEN")
    n_wid = sum(1 for c in claims if c.get("status") == "WIDERLEGT")
    print(f"Registry: {len(claims)} Claims — {n_bew} BEWIESEN, {n_off} OFFEN, {n_wid} WIDERLEGT.")

    if errors:
        for e in errors:
            print(f"[FEHLER] {e}")
        return 1
    print("[OK] Struktur & Beweis-Existenz: alle BEWIESEN-Claims sind durch reale Tests gedeckt.")

    if args.run:
        rc = run_proofs(claims)
        if rc != 0:
            print("[FEHLER] Mindestens ein Beweis-Knoten schlaegt fehl.")
            return rc
        print("[OK] Alle Beweis-Knoten gruen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
