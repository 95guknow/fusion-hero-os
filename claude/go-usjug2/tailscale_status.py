#!/usr/bin/env python3
"""
Tailscale Status Modul für Fusion Hero OS
Kompatibel mit pc-handy-bridge + phonelink-control
"""

import subprocess
import json
import sys
from datetime import datetime

def get_tailscale_status():
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return {"error": "Tailscale nicht erreichbar", "raw": result.stderr}

        data = json.loads(result.stdout)
        return {
            "timestamp": datetime.now().isoformat(),
            "version": data.get("Version", "unknown"),
            "backend_state": data.get("BackendState", "unknown"),
            "self": data.get("Self", {}),
            "peers_count": len(data.get("Peer", {})),
            "tailscale_ip": data.get("Self", {}).get("TailscaleIPs", [""])[0] if data.get("Self") else None,
            "online": data.get("Self", {}).get("Online", False)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    status = get_tailscale_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # Exit Code für Bridge-Integration
    if "error" in status:
        sys.exit(1)
    else:
        sys.exit(0)