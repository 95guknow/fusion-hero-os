# VR Visualization Protocol — Highest Layer (mit VR)

**Part of Heroic Highest Layer when loaded "mit VR".**

## Purpose

Enable immersive and visual representation of the generational evolution, roadmap, and heroic concepts using VR assets and rendering.

## Components

- **03_VR_Assets/** : Equirectangular images, 360° hero visuals, mister-Contributor VR scenes, fractal/heroic symbols for VR.
- **VR Visualization Protocol**: Defines how to map Layer 4 state (generations, fitness tracks, roadmap milestones) into visual/VR space.
- **Hero Visuals**: Integration with cool-mode prompts and asset loading for consistent heroic identity.

## Rules for mit VR

- All visual outputs must still respect Layer 0 Foundation (Geltungskategorien, no metaphor-as-proof in visuals too).
- VR mode augments, does not replace, the pure logic.
- Use lightweight rendering where possible; heavy generation offloaded to workstation (per resource distribution).
- Track "Visual Fidelity" as additional fitness dimension when in VR mode (but secondary to 5-Dim core).

## Loading

```python
from highest_layer import load_vr

hl = load_vr()   # "highest layer mit vr laden"
```

This activates:
- VRAssetManager
- VRTrack in evolution protocol
- Visual snapshotting (references to assets)
- Layer stack including VR layer

## Asset Reference

Typical structure:
```
03_VR_Assets/
├── vr_mister_Contributor_hero_equirectangular.jpg
├── heroic_evolution_360/
└── roadmap_visual_vr/
```

## Integration with Highest Layer

The GenerationalEvolutionProtocol gains a "VR Visual" parallel track that scores visual coherence, asset usage, and immersive representation quality (using 5-Dim + visual criteria).

## Ohne VR vs Mit VR

- ohne VR: Pure logic, CLI, data only.
- mit VR: + visual protocol, asset references, visual layer in status, hooks for image/VR generation tools, overlay/GUI integration.

Status when loaded mit VR will show `"mode": "mit_vr"`.
