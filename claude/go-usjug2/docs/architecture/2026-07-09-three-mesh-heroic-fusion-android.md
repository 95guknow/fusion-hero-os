# Three-Mesh Tailscale + Unified Heroic Fusion Android

**Date:** 2026-07-09
**Author:** Grok (Fusion Hero OS Core)
**Status:** Initial Draft / For Review

## Executive Summary

This document captures the architecture decisions from the 2026-07-09 session regarding:

- A clean three-zone logical mesh architecture using one Tailscale tailnet
- The rollout of "Unified Heroic Fusion Android" on the Redmi Note 13 Pro 5G
- Deep integration of pc-handy-bridge and phonelink-control
- Foundation for running the ALTE_Frau_95g Heroic Core on the mobile device

## 1. Current Tailscale State

### Devices
- `desktop-kpki9e4` (Windows): Stable, Connected
- `phone-node` (Android): Unstable – frequent "Logged out" with `fetch control key: context canceled` error

### Problem Analysis
The Android client has recurring issues fetching the control key from Tailscale's control plane. This is a common Android + battery optimization + Doze mode problem.

## 2. Target Architecture: Three Logical Meshes

Instead of three separate tailnets, we use **one primary tailnet** with strict segmentation:

| Zone            | Tag             | Purpose                          | Trust Level | Internet Breakout |
|-----------------|-----------------|----------------------------------|-------------|-------------------|
| Frontend Mesh   | `tag:frontend`  | Daily driver devices (phones, laptops) | Low        | Via Internet Zone |
| Internet Mesh   | `tag:internet`  | Exit Nodes & controlled breakout | Medium     | Yes (dedicated)   |
| Backend Mesh    | `tag:backend`   | Homelab, servers, Mainframe, sensitive services | High     | Via Internet Zone (strict) |

**Interconnection:**
- Strong ACLs in the Tailscale policy file
- Subnet routers where needed
- The xAI Sandbox remains an external high-performance compute layer, accessed from the Backend Mesh via controlled bridges

## 3. Unified Heroic Fusion Android

### Chosen Path
**Root + Magisk** (chosen by user)

### Goals
- Transform the Redmi Note 13 Pro 5G into a **mobile Heroic Extension Node** of the Fusion Hero OS Mainframe
- Deep visual identity (Heroic / Cyberpunk Campfire / Mister Contributor aesthetic) at SystemUI level
- Functional integration of `pc-handy-bridge` v8.1 and `phonelink-control` v8.2
- System-level heroic core services (quick tiles, background processes, theory tools)

### Technical Layers (post-Root)
1. **Visual Layer**: Magisk + LSPosed SystemUI theming + custom icons + KLWP
2. **Functional Layer**: Zygisk modules + Tasker + Shizuku + root services for bridges
3. **Core Integration Layer**: Direct low-latency connection to Mainframe via Tailscale + pc-handy-bridge

## 4. Next Steps

- [ ] Complete Bootloader Unlock + Magisk installation (one-time USB)
- [ ] Deploy Heroic Fusion Android Magisk modules
- [ ] Implement pc-handy-bridge Android side
- [ ] Create Tailscale ACL policy for the three zones
- [ ] Visual identity assets (mister-Contributor-protocol)

## References
- Conversation 2026-07-09 (Tailscale issues, three-mesh vision, Android rollout)
- ALTE_Frau_95g Heroic Core v8
- pc-handy-bridge v8.1 / phonelink-control v8.2

---
*This document was autonomously prepared by Grok under Fusion Hero OS protocol.*