#!/usr/bin/env python3
"""
Tailscale Phone Notification Module
Sendet Status-Updates via phonelink-control an dein Handy

Integration mit:
- pc-handy-bridge v8.1
- phonelink-control v8.2
- hero-docs-server /tailscale/status

Layer 0 kompatibel — Fusion Hero OS v8
"""

import subprocess
import json
import time
import os
from datetime import datetime

def get_tailscale_status():
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8
        )
        if result.returncode != 0:
            return {"online": False, "error": "Tailscale nicht erreichbar"}

        data = json.loads(result.stdout)
        return {
            "online": data.get("Self", {}).get("Online", False),
            "tailscale_ip": data.get("Self", {}).get("TailscaleIPs", [""])[0],
            "backend_state": data.get("BackendState"),
            "peers": len(data.get("Peer", {}))
        }
    except Exception as e:
        return {"online": False, "error": str(e)}

def send_phone_notification(message: str, title: str = "Tailscale"):
    """
    Sendet eine Benachrichtigung ans Handy.
    Hier wird später phonelink-control aufgerufen.
    Aktuell: Gibt nur aus (kann später erweitert werden).
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📱 PHONE NOTIFICATION → {title}: {message}")

    # TODO: Hier später echten phonelink-control Call einbauen:
    # from phonelink_control import send_notification
    # send_notification(title=title, message=message)

def monitor_tailscale(interval_seconds: int = 30):
    """Überwacht Tailscale und sendet Notification bei Status-Änderung"""
    last_online = None

    print("🔄 Tailscale Phone Monitor gestartet...")
    print(f"   Prüfintervall: {interval_seconds}s")
    print("   Drücke STRG+C zum Beenden.\n")

    while True:
        status = get_tailscale_status()
        current_online = status.get("online", False)

        if last_online is None:
            # Erster Durchlauf
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online"
                )
            else:
                send_phone_notification("Nicht verbunden", "Tailscale Offline")
        elif current_online != last_online:
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online"
                )
            else:
                send_phone_notification("Verbindung getrennt", "Tailscale Offline")

        last_online = current_online
        time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_tailscale(interval_seconds=30)