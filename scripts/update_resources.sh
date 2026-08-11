#!/usr/bin/env bash
set -e

# Generiert resources.md. Die Kopfzeile traegt bewusst einen Versionsmarker:
# scripts/check_doc_versions.py verlangt fuer jedes Top-Level-*.md ein
# '**Stand:**' / 'version:' / 'vX.Y' in den ersten 12 Zeilen und ist CI-fatal.
# Ohne diese Zeile hat der naechtliche update-resources-Lauf (03:00 UTC) die
# Versionierung jedes Mal wieder herausgeneriert und damit die CI rot gemacht.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RESOURCE_FILE="resources.md"

VERSION_STR="$(tr -d '[:space:]' < VERSION 2>/dev/null || true)"
[ -n "$VERSION_STR" ] || VERSION_STR="0.0.0"

# Datum aus dem letzten VERSION-Commit statt aus `date`: sonst erzeugt die
# naechtliche Cron jede Nacht einen Diff, committet auf main und triggert
# damit die CI erneut. `date` bleibt nur Fallback ohne Git-Kontext.
STAND_DATE="$(git log -1 --format=%cs -- VERSION 2>/dev/null || true)"
[ -n "$STAND_DATE" ] || STAND_DATE="$(date -u +%F)"

{
  echo "# AscensionOS / Fusion Hero OS Ressourcen"
  echo
  echo "> **Stand:** v${VERSION_STR} · ${STAND_DATE}"
} > "$RESOURCE_FILE"

cat >> "$RESOURCE_FILE" << 'EOR'

Diese Seite wird automatisch aus festen Quellen und Repo-Metadaten generiert.

## Eigene Repositories und Organisationen

- Fusion Hero OS Repo: https://github.com/95guknow/fusion-hero-os
- Senfkorn-Organisation: https://github.com/Senfkorn-UG

## Mesh, Monitoring und Archiv-Tools (Externe)

- Mesh-Monitoring / Dashboards: Grafana, Prometheus, Meshtastic-Integrationen.
- Web-Archivierung: ArchiveBox.
- Architektur-Dokumentation: Beispiele und Awesome-Architecture-Listen.

## XR / WebXR / VR/AR Frameworks

- WebXR Mesh Detection / Scene Understanding.
- Frameworks: A-Frame, Three.js, Babylon.js, 8th Wall.

## Dokumentation / Templates

- Good Docs / Architektur-Templates.
- Richtlinien für technische und semantische Kanon-Dokumente.

EOR
