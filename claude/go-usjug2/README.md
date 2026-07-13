# Tailscale Mesh Integration – Fusion Hero OS v8

**Status:** Vollständig integriert (09.07.2026)  
**Zweck:** Zero-Config Mesh-VPN + Phone-Bridge + Funnel für den gesamten Heimserver

## Mesh-Prinzip: Jeder Konnektor = eigenes Teil

Kein Monolith. Jedes Mesh-Segment hat:

- **Eigene ID** (`mesh-connector-github`, `mesh-connector-gmail`, …)
- **Eigener Host-Knoten** (`mainframe` oder `desktop`)
- **Eigene Health-Probe** (`/mesh/{connector}/status`)
- **Eigener Tailscale-Tag** (`tag:fusion-connector-github`, …)

Registry: `mesh_connectors.yaml`

### Physische Knoten

| Knoten | Rolle | MagicDNS |
|--------|-------|----------|
| `mainframe` | Orchestrator (Linux Heimserver) | `host.example.ts.net` |
| `desktop` | Grok-Workstation (Windows) | `host.example.ts.net` |

### MCP-Konnektor-Segmente (je eigenständig)

| Konnektor | Mesh-ID | Host |
|-----------|---------|------|
| GitHub | `mesh-connector-github` | desktop |
| Gmail | `mesh-connector-gmail` | desktop |
| Google Drive | `mesh-connector-google-drive` | desktop |
| Google Calendar | `mesh-connector-google-calendar` | desktop |
| Canva | `mesh-connector-canva` | desktop |
| Gamma | `mesh-connector-gamma` | desktop |
| Notion | `mesh-connector-notion` | desktop |
| Vercel | `mesh-connector-vercel` | desktop |
| HyperFrames | `mesh-connector-hyperframes` | desktop |
| Tasks | `mesh-connector-tasks` | desktop |

## Ein-Klick Mesh Setup

### Von Windows (Git Bash) aus (empfohlen)

```bash
chmod +x run_on_heimgserver.sh
./run_on_heimgserver.sh all
```

Einzelne Kommandos:
```bash
./run_on_heimgserver.sh install
./run_on_heimgserver.sh start
./run_on_heimgserver.sh funnel
./run_on_heimgserver.sh status
./run_on_heimgserver.sh mesh
```

### Direkt auf dem Linux-Heimserver

```bash
chmod +x tailscale_control.sh
sudo ./tailscale_control.sh all
sudo ./tailscale_control.sh mesh
sudo ./tailscale_control.sh mesh-connector github
```

## Verfügbare Kommandos

| Command | Beschreibung |
|---------|-------------|
| `install` | Installation + Authentifizierung |
| `start` | Start + Service einrichten |
| `status` | Tailscale-Status |
| `mesh` | Alle Konnektor-Segmente anzeigen |
| `mesh-connector <id>` | Einzelnes Segment prüfen |
| `funnel` | Funnel für Hero Docs Server |
| `notify` | Phone Notification Monitor |
| `all` | Komplettes Mesh-Setup |

## Erreichbare URLs (nach Funnel + MagicDNS)

- **Hero Docs Server**: `https://host.example.ts.net`
- **MasterSeed Status**: `https://host.example.ts.net/status`
- **Tailscale Status**: `https://host.example.ts.net/tailscale/status`
- **Mesh Overview**: `https://host.example.ts.net/mesh/status`
- **Einzelner Konnektor**: `https://host.example.ts.net/mesh/github/status`

## Dateien

| Datei | Zweck |
|-------|-------|
| `mesh_connectors.yaml` | Registry aller Mesh-Segmente |
| `tailscale_mesh_registry.py` | Health-Probes pro Konnektor |
| `tailscale_control.sh` | Zentrales Control Center |
| `tailscale_install.sh` | Installation + Login |
| `tailscale_start.sh` | Start + Service |
| `tailscale_status.py` | Tailscale-Status als JSON |
| `tailscale_funnel.sh` | Funnel-Aktivierung |
| `tailscale_phone_notify.py` | Phone Notifications |
| `run_on_heimgserver.sh` | Remote-Ausführung per SSH |
| `hero-docs-server.py` | Docs + Mesh-Endpoints |

---

**Layer 0 verankert** – Vollständig integriert in ALTE_Frau_95g Heroic Core v8 + HorkruxSelfUpdateProtocol.
