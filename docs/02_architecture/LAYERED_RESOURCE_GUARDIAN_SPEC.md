# Layered Resource Guardian — Ueberholt, siehe local_infrastructure_kernel

> **Stand:** 2026-07-13 · **Status:** Ersetzt durch die tatsaechlich lokal
> implementierte Kernlogik.

Dieses Dokument beschrieb urspruenglich eine 3-Layer-Spezifikation
(sofort/kurzfristig/mittelfristig, CPU/GPU/Fans/SSD/Temperatur, Kreuz-Check
bei Eskalation) fuer ein noch zu bauendes Kernmodul
`layered_resource_guardian.py`. Bei der lokalen Umsetzung (Windows-Mainframe,
ueber Windows-Coding-Tools) wurde bewusst ein anderes, einfacheres Design
gewaehlt:

- **Modul:** `src/normal_os/core/local_infrastructure_kernel.py`
- **Vertrag (kanonisch):** `workstation/contracts/local_infrastructure_kernel.v1.json`
- **Schwellenwerte:** `workstation/local_infrastructure_thresholds.json`
- **Eskalationsstufen:** `ok` / `warn` / `alert` / `critical` (kein 3-Layer-Timing)
- **Probe-Targets:** `ram_util_pct`, `disk_c_util_pct`, `tailscale_online`,
  sowie HTTP-Health der Services `service_dashboard`, `service_hero_docs`,
  `service_bridge` — kein CPU/GPU/Temperatur/Fan-Probing.
- **Transport:** `python_import` (bevorzugt) oder `status_file`
  (`~/.fusion/local-infrastructure-kernel/status.json`) als Fallback.

Die API/GUI-Schicht (`resource_guardian_routes.py`, `/resources`) wurde
entsprechend an dieses reale Modul angepasst (nicht an dieses Dokument).
**`workstation/contracts/local_infrastructure_kernel.v1.json` ist die
kanonische Schnittstellen-Referenz, nicht diese Datei.**

Diese Datei bleibt nur als historischer Kontext stehen, warum die
API-Routen unter `/api/resources/*` so heissen, wie sie heissen.
