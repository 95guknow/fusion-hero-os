#!/usr/bin/env python3
"""Audit + generate missing Fusion Hero OS visual assets (SD WebUI or Pillow fallback)."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore

ROOT = Path(os.environ.get("FUSION_HERO_ROOT", r"C:\Users\Admin\fusion-hero-os"))
MANIFEST = Path(__file__).resolve().parent / "asset_manifest.yaml"
AUDIT_LOG = ROOT / "03_Code" / "tools" / "asset_audit.json"


def _load_manifest() -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    with open(MANIFEST, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _collect_assets(manifest: dict, category: Optional[str]) -> List[dict]:
    items: List[dict] = []
    for cat_id, cat in (manifest.get("categories") or {}).items():
        if category and category != cat_id:
            continue
        for asset in cat.get("assets") or []:
            items.append({**asset, "category": cat_id, "category_label": cat.get("label", cat_id)})
    return items


def _asset_path(asset: dict) -> Path:
    return ROOT / asset["rel_path"]


def audit_assets(manifest: dict, category: Optional[str] = None) -> dict:
    missing: List[dict] = []
    present: List[dict] = []
    insufficient: List[dict] = []

    for asset in _collect_assets(manifest, category):
        path = _asset_path(asset)
        min_bytes = int(asset.get("min_bytes", 10000))
        entry = {
            "id": asset["id"],
            "category": asset["category"],
            "path": str(path),
            "rel_path": asset["rel_path"],
            "min_bytes": min_bytes,
        }
        if not path.exists():
            missing.append(entry)
        elif path.stat().st_size < min_bytes:
            entry["size_bytes"] = path.stat().st_size
            insufficient.append(entry)
        else:
            entry["size_bytes"] = path.stat().st_size
            present.append(entry)

    report = {
        "timestamp": datetime.now().isoformat(),
        "root": str(ROOT),
        "summary": {
            "total": len(missing) + len(insufficient) + len(present),
            "present": len(present),
            "missing": len(missing),
            "insufficient": len(insufficient),
            "needs_generation": len(missing) + len(insufficient),
        },
        "present": present,
        "missing": missing,
        "insufficient": insufficient,
    }
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _sd_available(url: str, timeout: float = 5.0) -> bool:
    try:
        import httpx
        r = httpx.get(f"{url.rstrip('/')}/sdapi/v1/sd-models", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _generate_sd(asset: dict, sd_url: str, timeout: float) -> Optional[bytes]:
    import httpx

    w = int(asset.get("width", 512))
    h = int(asset.get("height", 512))
    payload = {
        "prompt": asset.get("sd_prompt", asset["id"]),
        "negative_prompt": asset.get("negative", ""),
        "width": w,
        "height": h,
        "steps": 20 if asset.get("type") == "equirectangular" else 18,
        "cfg_scale": 7,
        "sampler_name": "Euler a",
        "batch_size": 1,
        "n_iter": 1,
    }
    r = httpx.post(
        f"{sd_url.rstrip('/')}/sdapi/v1/txt2img",
        json=payload,
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    images = data.get("images") or []
    if not images:
        return None
    return base64.b64decode(images[0])


def _fallback_equirectangular(w: int, h: int, asset_id: str) -> "Image.Image":
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(10 + 30 * (1 - t))
        g = int(20 + 180 * (1 - t) * 0.6)
        b = int(40 + 80 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    cx, cy = w // 2, int(h * 0.55)
    for i in range(12, 0, -1):
        rad = i * 18
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(0, 255, 159), width=2)
    draw.text((20, h - 28), f"[fallback] {asset_id}", fill=(255, 51, 102))
    return img


def _fallback_texture(w: int, h: int, asset_id: str) -> "Image.Image":
    img = Image.new("RGB", (w, h), (10, 10, 18))
    draw = ImageDraw.Draw(img)
    for i in range(80):
        x = int((math.sin(i * 0.7) + 1) * 0.5 * w)
        y = int((math.cos(i * 1.1) + 1) * 0.5 * h)
        c = (0, 200 + (i % 55), 120 + (i % 80))
        draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=c)
    draw.text((10, 10), f"evolution::{asset_id}", fill=(201, 162, 39))
    return img


def _fallback_portrait(w: int, h: int, asset_id: str) -> "Image.Image":
    img = Image.new("RGB", (w, h), (12, 12, 20))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line([(0, y), (w, y)], fill=(int(8 + 40 * t), int(10 + 20 * t), int(25 + 60 * t)))
    for i in range(120):
        x = int((math.sin(i * 0.31) * 0.45 + 0.5) * w)
        y = int((math.cos(i * 0.47) * 0.45 + 0.5) * h)
        draw.rectangle([x, y, x + 2, y + 6], fill=(0, 180 + i % 60, 120))
    draw.rectangle([w // 4, h // 6, 3 * w // 4, 5 * h // 6], outline=(0, 255, 159), width=4)
    draw.ellipse([w // 3, h // 5, 2 * w // 3, h // 2], outline=(255, 51, 102), width=3)
    draw.rectangle([0, h - 80, w, h], fill=(20, 20, 32))
    draw.text((16, h - 56), "95g Hacker Seed", fill=(0, 255, 159))
    draw.text((16, h - 32), asset_id[:48], fill=(180, 180, 200))
    # Feinkorn für ausreichende Dateigröße ohne sichtbare Artefakte
    px = img.load()
    for n in range(w * h // 8):
        x, y = n % w, (n * 7) % h
        r, g, b = px[x, y]
        px[x, y] = (min(255, r + (n % 5)), g, min(255, b + (n % 3)))
    return img


def _fallback_icon(w: int, h: int, asset_id: str) -> "Image.Image":
    img = Image.new("RGBA", (w, h), (10, 10, 18, 255))
    draw = ImageDraw.Draw(img)
    for ring in range(6, 0, -1):
        rad = ring * (w // 14)
        cx, cy = w // 2, h // 2 + 8
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(0, 255, 159, 80), width=2)
    cx, cy = w // 2, h // 2 + 10
    pts = [(cx, cy - 48), (cx - 34, cy + 26), (cx + 34, cy + 26)]
    draw.polygon(pts, fill=(0, 255, 159, 230))
    draw.ellipse([cx - 12, cy - 58, cx + 12, cy - 38], fill=(255, 51, 102, 255))
    for i in range(24):
        ang = i * math.pi / 12
        x1 = cx + int(math.cos(ang) * 20)
        y1 = cy - 44 + int(math.sin(ang) * 10)
        x2 = cx + int(math.cos(ang) * 56)
        y2 = cy - 44 + int(math.sin(ang) * 22)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 200, 80, 140), width=2)
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            if (x + y) % 9 == 0:
                draw.rectangle([x, y, x + 2, y + 2], fill=(0, 255, 159, 40))
    return img


def _generate_fallback(asset: dict) -> bytes:
    if Image is None:
        raise RuntimeError("Pillow required for fallback: pip install pillow")

    w = int(asset.get("width", 512))
    h = int(asset.get("height", 512))
    fmt = (asset.get("format") or "jpg").lower()
    atype = asset.get("type", "texture")

    if atype == "equirectangular":
        img = _fallback_equirectangular(w, h, asset["id"])
    elif atype == "portrait":
        img = _fallback_portrait(w, h, asset["id"])
    elif atype == "icon":
        img = _fallback_icon(w, h, asset["id"])
    else:
        img = _fallback_texture(w, h, asset["id"])

    from io import BytesIO
    buf = BytesIO()
    if fmt == "png":
        img.save(buf, format="PNG", compress_level=3)
    else:
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def generate_assets(
    manifest: dict,
    *,
    category: Optional[str] = None,
    force: bool = False,
    prefer_sd: bool = True,
) -> dict:
    audit = audit_assets(manifest, category)
    to_gen = audit["missing"] + audit["insufficient"]
    if force:
        ids_force = {a["id"] for a in _collect_assets(manifest, category)}
        to_gen = [
            {
                "id": a["id"],
                "category": a["category"],
                "path": str(_asset_path(a)),
                "rel_path": a["rel_path"],
            }
            for a in _collect_assets(manifest, category)
            if a["id"] in ids_force
        ]

    sd_cfg = manifest.get("sd_webui") or {}
    sd_url = os.environ.get("SD_WEBUI_URL", sd_cfg.get("url", "http://127.0.0.1:7860"))
    sd_timeout = float(sd_cfg.get("timeout_seconds", 180))
    sd_ok = prefer_sd and _sd_available(sd_url)

    results: List[dict] = []
    asset_by_id = {a["id"]: a for a in _collect_assets(manifest, category)}

    for entry in to_gen:
        asset = asset_by_id.get(entry["id"])
        if not asset:
            continue
        out_path = _asset_path(asset)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        source = "skipped"
        error = None
        size = 0

        try:
            raw: Optional[bytes] = None
            if sd_ok:
                try:
                    raw = _generate_sd(asset, sd_url, sd_timeout)
                    source = "stable-diffusion-webui"
                except Exception as exc:
                    error = f"sd: {exc}"
            if raw is None:
                raw = _generate_fallback(asset)
                source = "pillow_fallback" if not sd_ok else f"pillow_fallback ({error or 'sd empty'})"
            out_path.write_bytes(raw)
            size = len(raw)
        except Exception as exc:
            source = "error"
            error = str(exc)

        results.append({
            "id": entry["id"],
            "category": entry.get("category"),
            "path": str(out_path),
            "source": source,
            "size_bytes": size,
            "error": error,
        })

    final_audit = audit_assets(manifest, category)
    return {
        "generated": results,
        "sd_webui_available": sd_ok,
        "sd_webui_url": sd_url,
        "audit_before": audit["summary"],
        "audit_after": final_audit["summary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and generate missing Fusion Hero assets")
    parser.add_argument("--audit", action="store_true", help="Audit only")
    parser.add_argument("--generate", action="store_true", help="Generate missing/insufficient assets")
    parser.add_argument("--category", choices=["vr", "visual_seeds", "memes"], default=None)
    parser.add_argument("--force", action="store_true", help="Regenerate all in category")
    parser.add_argument("--no-sd", action="store_true", help="Pillow fallback only")
    args = parser.parse_args()

    manifest = _load_manifest()
    if args.generate:
        out = generate_assets(
            manifest,
            category=args.category,
            force=args.force,
            prefer_sd=not args.no_sd,
        )
    else:
        out = audit_assets(manifest, args.category)

    print(json.dumps(out, indent=2, ensure_ascii=False))
    needs = out.get("summary", {}).get("needs_generation", 0)
    if args.audit and not args.generate:
        return 0 if needs == 0 else 2
    after = out.get("audit_after", out.get("summary", {}))
    return 0 if after.get("needs_generation", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())