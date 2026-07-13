#!/bin/bash
# run_on_heimgserver.sh
# Führt Tailscale-Kommandos remote auf dem Linux-Heimserver aus
# Funktioniert von Windows (Git Bash) oder Linux aus

set -e

SERVER="host.example.ts.net"
USER="admin"          # <-- Hier deinen SSH-User auf dem Heimserver eintragen
REMOTE_DIR="/home/workdir/artifacts/tools/tailscale"

if [ -z "$1" ]; then
    echo "Usage: $0 <command>"
    echo ""
    echo "Beispiele:"
    echo "  $0 all          → Vollständiges Mesh-Setup"
    echo "  $0 install"
    echo "  $0 start"
    echo "  $0 funnel"
    echo "  $0 status"
    echo "  $0 notify"
    exit 1
fi

COMMAND="$1"

echo "🔗 Verbinde mit $SERVER ..."

echo "→ Führe aus: ./tailscale_control.sh $COMMAND"

echo ""

ssh "$USER@$SERVER" "cd $REMOTE_DIR && chmod +x tailscale_control.sh && sudo ./tailscale_control.sh $COMMAND"

echo ""
echo "✅ Befehl '$COMMAND' auf dem Heimserver ausgeführt."