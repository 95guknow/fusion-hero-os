#!/bin/bash
# Tailscale Start + Service Setup für Fusion Hero OS
# Kann auch remote über Bridge getriggert werden

set -e

echo "🚀 [Fusion Hero OS] Tailscale wird gestartet..."

# Tailscale starten (falls noch nicht aktiv)
sudo tailscale up --ssh

# tailscaled Service sicherstellen
sudo systemctl enable --now tailscaled

echo "✅ Tailscale läuft und ist als Service eingerichtet."

# Kurzer Status
echo ""
echo "📡 Aktueller Tailscale-Status:"
tailscale status --json | head -n 20 || echo "(Status konnte nicht vollständig geladen werden)"

echo ""
echo "✅ Fertig. Dein Server ist jetzt über Tailscale erreichbar."
echo "   IP im Tailnet: $(tailscale ip -4 2>/dev/null || echo 'noch nicht vergeben')"