#!/usr/bin/env bash
set -e

RESOURCE_FILE="resources.md"

cat > "$RESOURCE_FILE" << 'EOR'
# AscensionOS / Fusion Hero OS Ressourcen

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
