#!/bin/bash
# Tailscale Installation + Setup für Fusion Hero OS Heimserver
# Layer 0 kompatibel – 09.07.2026

set -e

echo "🚀 [Fusion Hero OS] Tailscale Installation wird gestartet..."

# 1. Tailscale offizielles Install-Skript ausführen
curl -fsSL https://tailscale.com/install.sh | sh

echo "✅ Tailscale Binary installiert."

# 2. tailscaled Service aktivieren
sudo systemctl enable --now tailscaled

echo "✅ tailscaled Service aktiviert."

# 3. Authentifizierung starten (öffnet Browser oder gibt Login-Link aus)
echo ""
echo "🔐 Jetzt Tailscale authentifizieren..."
echo "   Bitte im Browser anmelden (GitHub / Google / Microsoft empfohlen)."
echo ""

sudo tailscale up --ssh

echo ""
echo "✅ Tailscale erfolgreich eingerichtet!"
echo ""
echo "Nächster Schritt: ./tailscale_start.sh ausführen (falls noch nicht geschehen)"
echo ""
echo "Status prüfen mit: tailscale status"