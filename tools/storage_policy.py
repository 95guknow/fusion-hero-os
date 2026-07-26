# -*- coding: utf-8 -*-
"""Fusion Hero OS — Google-Drive-Speicherpolitik (Single Source of Truth)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

POLICY_REL = Path("workstation") / "storage_policy.json"


def _fusion_root() -> Path:
    env = os.environ.get("FUSION_HERO_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent.parent
    return here


def _expand(path: str) -> str:
    return path.replace("{USERPROFILE}", os.environ.get("USERPROFILE", r"C:\Users\Admin"))


def load_policy(fusion_root: Optional[Path] = None) -> Dict[str, Any]:
    root = fusion_root or _fusion_root()
    policy_path = root / POLICY_REL
    if not policy_path.is_file():
        return {}
    with open(policy_path, encoding="utf-8") as f:
        return json.load(f)


def _as_drive_root(path: Path) -> Path:
    """Normalize Windows drive roots so Path('G:') / 'x' becomes G:\\x not G:x."""
    s = str(path)
    if len(s) == 2 and s[1] == ":":
        return Path(s + "\\")
    if len(s) == 3 and s[1] == ":" and s[2] in ("/", "\\"):
        return Path(s[0] + ":\\")
    return path


def resolve_gdrive_paths(policy: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Path], Optional[Path]]:
    """Returns (library_root, cold_offload_root)."""
    policy = policy or load_policy()
    gd = policy.get("google_drive", {})
    library = gd.get("library", "Meine Ablage")
    cold = gd.get("cold_root", "FusionHero_Offload")
    for mount in gd.get("mount_candidates", []):
        base = _as_drive_root(Path(_expand(mount)))
        if not base.is_dir():
            continue
        # On G: the library may be "Meine Ablage" as subfolder or root is already library
        lib_path = base / library
        if not lib_path.is_dir() and (base / "FusionHero_Offload").is_dir():
            # base already is Meine Ablage (or equivalent)
            lib_path = base
        if not lib_path.is_dir() and base.is_dir():
            # G:\Meine Ablage style: library lives under base
            if (base / library).is_dir():
                lib_path = base / library
            elif base.name.lower() in ("meine ablage", "my drive"):
                lib_path = base
            else:
                # Prefer Meine Ablage when present on G:
                candidate = base / "Meine Ablage"
                lib_path = candidate if candidate.is_dir() else base
        if lib_path.is_dir() or base.is_dir():
            if not lib_path.is_dir():
                lib_path = base
            cold_path = lib_path / cold
            return lib_path, cold_path
    return None, None


def resolve_gdrive_offload_root(policy: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    env = os.environ.get("FUSION_GDRIVE_OFFLOAD")
    if env:
        return Path(env)
    _, cold = resolve_gdrive_paths(policy)
    return cold


def resolve_longterm_cache_root(policy: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Runtime memory/state spill (Virtual HT SSDLongTermCache) on GDrive cold storage."""
    env = os.environ.get("FUSION_SSD_LONGTERM_CACHE") or os.environ.get(
        "FUSION_GDRIVE_LONGTERM_CACHE"
    )
    if env:
        return Path(env)
    policy = policy or load_policy()
    gd = policy.get("google_drive", {})
    rel = gd.get("longterm_cache") or f"{gd.get('cold_root', 'FusionHero_Offload')}/LongTermCache"
    lib, cold = resolve_gdrive_paths(policy)
    if cold is not None:
        # Prefer explicit longterm under cold root
        p = cold / "LongTermCache" if "LongTermCache" not in str(cold) else cold
        if rel and lib is not None:
            candidate = lib / Path(rel.replace("\\", "/"))
            return candidate
        return p
    if lib is not None:
        return lib / Path(str(rel).replace("\\", "/"))
    return None


def offload_folder_map(policy: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
    policy = policy or load_policy()
    rows = policy.get("offload_folders", [])
    out: List[Tuple[str, str]] = []
    for row in rows:
        out.append((row["src"], row["dst"]))
    return out


def thresholds(policy: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    policy = policy or load_policy()
    return policy.get("thresholds", {})
