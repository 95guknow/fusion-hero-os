# OS → Poly-Mesh Port Report

**UTC:** 2026-08-10T07:50:35.686250+00:00
**Platform:** Fusion Hero OS v10.0.0
**Banner:** OS PORTED TO POLY-MESH | self=100.64.104.58 | tiers=L1_mainframe,L2_mesh_anchor | organs=10

## Self

- hostname: `desktop-kpki9e4`
- mesh_ip: `100.64.104.58`
- tiers_online: `L1_mainframe, L2_mesh_anchor`
- peers: `6`

## Organs

Count: **10**

- `http://100.64.104.58:8000/`
- `http://100.64.104.58:8000/api/hyperraum`
- `http://100.64.104.58:8000/api/v1/business`
- `http://100.64.104.58:8000/mainframe/grok`

## Steps

- mesh_serve: `{"ok": true, "cmd": "C:\\Program Files\\Tailscale\\tailscale.exe serve --bg 8000", "stdout": "Available within your tailnet:\n\nhttps://desktop-kpki9e4.tail391adb.ts.net/\n|-- proxy http://127.0.0.1:8`
- coordinator: ok=`True`
- headset_mesh_only: `{'ok': True, 'mesh_only': True}`

## CLI

```powershell
python scripts/port_os_poly_mesh.py
python -m fusion_hero_os.core.poly_mesh_os_port --status
python scripts/mesh_cluster_coordinator.py --mode all
```

## Notes

- Secrets/MCP stay **L1**.
- Dashboard mesh URLs need `:8000` process up.
- AudioRelay phone path: **mesh only** (100.x).
- Tailscale **Apps** UI is SaaS routing — not required for this port.
