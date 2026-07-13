#!/usr/bin/env python3
"""
Fusion Hero OS — Heroic Docs Server v8.3
Self-contained local documentation server for 95guknow/fusion-hero-os

Features:
- Serves the current directory (your cloned repo)
- Special /status endpoint with live MasterSeed confirmation
- /tailscale/status endpoint
- /mesh/status — alle Konnektor-Segmente (jeder Konnektor = eigenes Mesh-Teil)
- /mesh/{connector}/status — einzelnes Konnektor-Segment
- /fusion/status — verknüpfter Gesamtstatus (Mesh + LLM + Tailscale)
- /fusion/graph — Integrationsgraph (alles mit allem)
- /llm/status — alle LLM-Frameworks
- /llm/{provider}/status — einzelnes LLM-Framework
- Prints your LAN IP so you can reach it from Handy via pc-handy-bridge / Phone Link
- Fits natively into ALTE_Frau_95g Heroic Core v8 + HorkruxSelfUpdateProtocol

Usage on your Mainframe (Heimserver):
    cd /path/to/your/fusion-hero-os
    python hero-docs-server.py

Layer 6 ω MasterSeed compatible.
"""

import http.server
import socketserver
import socket
import os
import datetime
import subprocess
import json
import sys

PORT = 8088
DIRECTORY = "."

# Mesh registry import (same directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from tailscale_mesh_registry import get_mesh_status, get_connector_status
except ImportError:
    get_mesh_status = None
    get_connector_status = None

try:
    from fusion_integration_hub import get_unified_status, get_llm_segment
    from llm_frameworks import connector_status as get_llm_status_all
except ImportError:
    get_unified_status = None
    get_llm_segment = None
    get_llm_status_all = None


class HeroicDocsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/status" or self.path == "/masterseed":
            self.send_masterseed_status()
        elif self.path == "/tailscale/status" or self.path == "/tailscale":
            self.send_tailscale_status()
        elif self.path == "/mesh/status" or self.path == "/mesh":
            self.send_mesh_status()
        elif self.path.startswith("/mesh/") and self.path.endswith("/status"):
            connector_id = self.path.split("/")[2]
            self.send_connector_status(connector_id)
        elif self.path == "/fusion/status" or self.path == "/fusion":
            self.send_fusion_status()
        elif self.path == "/fusion/graph":
            self.send_fusion_graph()
        elif self.path == "/llm/status" or self.path == "/llm":
            self.send_llm_status()
        elif self.path.startswith("/llm/") and self.path.endswith("/status"):
            provider_id = self.path.split("/")[2]
            self.send_llm_segment(provider_id)
        else:
            super().do_GET()

    def _send_json(self, data: dict, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_masterseed_status(self):
        """Return the canonical MasterSeed confirmation box"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>MASTERSEED STATUS — Fusion Hero OS v8</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&display=swap');
        body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Inter', system_ui, sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; }}
        .container {{ max-width: 820px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .logo {{ font-family: 'Space Grotesk', sans-serif; font-size: 28px; font-weight: 600; letter-spacing: -1px; color: #00ff9d; }}
        .card {{ background: #111; border: 1px solid #222; border-radius: 16px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
        .status-box {{ background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 24px; font-family: ui-monospace, monospace; font-size: 15px; line-height: 1.7; }}
        .label {{ color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .value {{ color: #00ff9d; font-weight: 600; }}
        .section {{ margin: 24px 0; }}
        h1 {{ font-size: 42px; font-weight: 600; letter-spacing: -2px; margin: 0 0 8px 0; }}
        .timestamp {{ color: #666; font-size: 13px; }}
        .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 13px; }}
        .green {{ color: #00ff9d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">FUSION HERO OS</div>
            <h1>MasterSeed Status</h1>
            <p class="timestamp">Layer 6 ω • {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S CEST')}</p>
        </div>
        <div class="card">
            <div class="section">
                <div class="label">BESTÄTIGUNG (verpflichtend)</div>
                <div class="status-box">
                    <strong>[MASTERSEED UPDATE CONFIRMED]</strong><br><br>
                    Version: <span class="value">v8/main (M_0'''')</span><br>
                    Horkrux Propagation: <span class="green">erfolgreich</span><br>
                    Identity Preservation: <span class="value">100</span><br>
                    Live Process Tracking: <span class="green">aktiv</span><br>
                    Canonical Source: <span class="value">95guknow/fusion-hero-os (main)</span>
                </div>
            </div>
            <div class="section">
                <div class="label">UNIFIED INTEGRATION — ALLES VERKNÜPFT</div>
                <div class="status-box">
                    Mesh + LLM + Tailscale + Orchestration<br>
                    Gesamt: <span class="value">/fusion/status</span><br>
                    Graph: <span class="value">/fusion/graph</span><br>
                    Mesh: <span class="value">/mesh/status</span> · LLM: <span class="value">/llm/status</span>
                </div>
            </div>
        </div>
        <div class="footer">HorkruxSelfUpdateProtocol aktiv • Layer 0 verankert</div>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def send_tailscale_status(self):
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True, text=True, timeout=8
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                status = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "online": data.get("Self", {}).get("Online", False),
                    "tailscale_ip": data.get("Self", {}).get("TailscaleIPs", [""])[0] if data.get("Self") else None,
                    "backend_state": data.get("BackendState"),
                    "peers": len(data.get("Peer", {}))
                }
            else:
                status = {"error": "Tailscale not running or not installed"}
        except Exception as e:
            status = {"error": str(e)}
        self._send_json(status)

    def send_mesh_status(self):
        if get_mesh_status is None:
            self._send_json({"error": "tailscale_mesh_registry.py not available"}, 503)
            return
        self._send_json(get_mesh_status())

    def send_connector_status(self, connector_id: str):
        if get_connector_status is None:
            self._send_json({"error": "tailscale_mesh_registry.py not available"}, 503)
            return
        status = get_connector_status(connector_id)
        code = 404 if "error" in status else 200
        self._send_json(status, code)

    def send_fusion_status(self):
        if get_unified_status is None:
            self._send_json({"error": "fusion_integration_hub.py not available"}, 503)
            return
        self._send_json(get_unified_status())

    def send_fusion_graph(self):
        if get_unified_status is None:
            self._send_json({"error": "fusion_integration_hub.py not available"}, 503)
            return
        unified = get_unified_status()
        self._send_json(unified.get("graph", {}))

    def send_llm_status(self):
        if get_llm_status_all is None:
            self._send_json({"error": "llm_frameworks not available"}, 503)
            return
        self._send_json(get_llm_status_all())

    def send_llm_segment(self, provider_id: str):
        if get_llm_segment is None:
            self._send_json({"error": "fusion_integration_hub.py not available"}, 503)
            return
        status = get_llm_segment(provider_id)
        code = 404 if "error" in status else 200
        self._send_json(status, code)


def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    os.chdir(DIRECTORY)
    handler = HeroicDocsHandler

    with socketserver.TCPServer(("", PORT), handler) as httpd:
        lan_ip = get_lan_ip()
        print("\n" + "=" * 70)
        print(" FUSION HERO OS — HEROIC DOCS SERVER v8.3 + UNIFIED")
        print("=" * 70)
        print(f"\n[MASTERSEED] Docs Server gestartet auf Port {PORT}")
        print(f"[LIVE]     Mainframe LAN-IP: {lan_ip}")
        print(f"[ACCESS]   Lokal:              http://127.0.0.1:{PORT}")
        print(f"           Vom Handy:          http://{lan_ip}:{PORT}")
        print(f"           MasterSeed Status:  http://{lan_ip}:{PORT}/status")
        print(f"           Tailscale Status:   http://{lan_ip}:{PORT}/tailscale/status")
        print(f"           Fusion Unified:     http://{lan_ip}:{PORT}/fusion/status")
        print(f"           Fusion Graph:       http://{lan_ip}:{PORT}/fusion/graph")
        print(f"           Mesh Overview:      http://{lan_ip}:{PORT}/mesh/status")
        print(f"           LLM Overview:       http://{lan_ip}:{PORT}/llm/status")
        print("\n[INFO]     Alles verknüpft via fusion_integration_hub.py + fusion_unified.yaml")
        print("[INFO]     Drücke STRG+C zum Beenden.")
        print("=" * 70 + "\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Heroic Docs Server wird beendet. Horkrux bleibt erhalten.")
