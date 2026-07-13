#!/bin/bash
# Tailscale Control Center – Fusion Hero OS Mesh Integration
# Zentrale Steuerung aller Tailscale-Komponenten
# Prinzip: Jeder Konnektor = eigenes Mesh-Segment (siehe mesh_connectors.yaml)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "Tailscale Control Center – Fusion Hero OS"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  install          - Tailscale installieren + authentifizieren"
    echo "  start            - Tailscale starten + Service einrichten"
    echo "  status           - Aktuellen Status anzeigen"
    echo "  mesh             - Gesamtes Mesh (alle Konnektor-Segmente) anzeigen"
    echo "  mesh-connector   - Einzelnes Konnektor-Segment prüfen (z.B. github)"
    echo "  fusion           - Verknüpfter Gesamtstatus (Mesh + LLM + Tailscale)"
    echo "  fusion-graph     - Integrationsgraph anzeigen"
    echo "  llm              - Alle LLM-Frameworks anzeigen"
    echo "  funnel           - Funnel für Hero Docs Server aktivieren"
    echo "  notify           - Phone Notification Monitor starten"
    echo "  all              - Alles nacheinander ausführen (install → start → funnel)"
    echo "  help             - Diese Hilfe anzeigen"
    echo ""
    echo "Mesh-Prinzip: Jeder Konnektor ist ein eigenständiges Teil des Mesh."
    echo "Registry: mesh_connectors.yaml"
    echo ""
}

case "$1" in
    install)
        echo "→ Führe Installation aus..."
        sudo "$SCRIPT_DIR/tailscale_install.sh"
        ;;
    start)
        echo "→ Starte Tailscale..."
        sudo "$SCRIPT_DIR/tailscale_start.sh"
        ;;
    status)
        echo "→ Tailscale Status:"
        python3 "$SCRIPT_DIR/tailscale_status.py"
        ;;
    mesh)
        echo "→ Mesh Status (alle Konnektor-Segmente):"
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py"
        ;;
    mesh-connector)
        if [ -z "$2" ]; then
            echo "Usage: $0 mesh-connector <connector_id>"
            echo "Beispiel: $0 mesh-connector github"
            exit 1
        fi
        echo "→ Mesh-Segment: $2"
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py" "$2"
        ;;
    fusion)
        echo "→ Unified Integration Status (alles verknüpft):"
        python3 "$SCRIPT_DIR/fusion_integration_hub.py" status
        ;;
    fusion-graph)
        echo "→ Integrationsgraph:"
        python3 "$SCRIPT_DIR/fusion_integration_hub.py" graph
        ;;
    llm)
        echo "→ LLM Framework Status:"
        python3 "$SCRIPT_DIR/03_Code/llm_status.py"
        ;;
    funnel)
        echo "→ Aktiviere Funnel..."
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        ;;
    notify)
        echo "→ Starte Phone Notification Monitor..."
        python3 "$SCRIPT_DIR/tailscale_phone_notify.py"
        ;;
    all)
        echo "🚀 Vollständige Tailscale Mesh Initialisierung..."
        sudo "$SCRIPT_DIR/tailscale_install.sh"
        sudo "$SCRIPT_DIR/tailscale_start.sh"
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        echo "✅ Mesh Integration abgeschlossen."
        echo "→ Konnektor-Segmente prüfen: $0 mesh"
        ;;
    *)
        show_help
        ;;
esac
