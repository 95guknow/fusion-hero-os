"""
Pseudo-Inhouse Creative Hub — image, video, PDF, graphics.

Policy: NO freemium product surface. Everything is local-first
pseudo-inhouse; optional external APIs are membranes only.

Geltung: Spezifikation (local generators) · membrane paths Bedingt.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import textwrap
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

__all__ = [
    "CreativeResult",
    "status",
    "catalog",
    "create",
    "create_image",
    "create_pdf",
    "create_video",
    "create_graphics",
    "list_artifacts",
    "output_dir",
]

PLATFORM = "10.0.0"
ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CreativeResult:
    ok: bool
    modality: str
    engine: str
    path: str | None = None
    paths: list[str] = field(default_factory=list)
    mime: str = "application/octet-stream"
    latency_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    pseudo_inhouse: bool = True
    freemium: bool = False
    platform: str = PLATFORM

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def output_dir() -> Path:
    env = os.getenv("FUSION_CREATIVE_OUT", "").strip()
    if env:
        p = Path(env)
    else:
        p = Path.home() / ".fusion" / "creative" / "inhouse"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_yaml() -> dict[str, Any]:
    path = ROOT / "creative_inhouse_services.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def catalog() -> dict[str, Any]:
    data = _load_yaml()
    return {
        "ok": True,
        "platform": PLATFORM,
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "principle": data.get("principle"),
        "facade": data.get("facade"),
        "engines": data.get("engines") or {},
        "modalities": data.get("modalities") or {},
        "anti_patterns": data.get("anti_patterns") or [],
        "placement": data.get("placement", "L1"),
    }


def _pil():
    from PIL import Image, ImageDraw, ImageFont

    return Image, ImageDraw, ImageFont


def _font(size: int = 28):
    Image, ImageDraw, ImageFont = _pil()
    for name in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _parse_size(size: str, default: tuple[int, int] = (1024, 768)) -> tuple[int, int]:
    try:
        w, h = size.lower().split("x")
        return max(64, int(w)), max(64, int(h))
    except Exception:
        return default


def _slug(text: str, n: int = 40) -> str:
    s = "".join(c if c.alnum() or c in "-_" else "-" for c in (text or "work")[:n])
    return s.strip("-") or "work"


def _stamp(prefix: str, ext: str) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    h = hashlib.sha1(f"{prefix}{ts}{os.getpid()}".encode()).hexdigest()[:8]
    return output_dir() / f"{prefix}_{ts}_{h}.{ext}"


def _palette(seed: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    h = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16)
    bg = (10 + (h % 30), 16 + (h >> 4) % 40, 28 + (h >> 8) % 50)
    accent = (0, 180 + (h % 50), 150 + (h >> 2) % 60)
    fg = (230, 236, 245)
    return bg, accent, fg


def create_image(
    prompt: str,
    *,
    size: str = "1024x768",
    style: str = "poster",
    title: str | None = None,
) -> CreativeResult:
    t0 = time.time()
    try:
        Image, ImageDraw, ImageFont = _pil()
        w, h = _parse_size(size)
        bg, accent, fg = _palette(prompt or style)
        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)

        # geometric field (local generative graphic — not freemium API)
        for i in range(0, w, max(32, w // 24)):
            col = (
                min(255, bg[0] + (i * 3) % 40),
                min(255, bg[1] + (i * 5) % 50),
                min(255, bg[2] + (i * 7) % 60),
            )
            draw.rectangle([i, 0, i + w // 40, h], fill=col)
        draw.ellipse(
            [w * 0.55, h * 0.1, w * 0.95, h * 0.55],
            outline=accent,
            width=max(2, w // 200),
        )
        draw.rectangle(
            [w * 0.06, h * 0.08, w * 0.08, h * 0.92],
            fill=accent,
        )

        title_txt = (title or "Fusion Hero OS · Pseudo-Inhouse").strip()
        body = textwrap.fill((prompt or "Creative work").strip(), width=42)
        draw.text((w * 0.12, h * 0.12), title_txt, fill=accent, font=_font(max(18, w // 28)))
        draw.text((w * 0.12, h * 0.28), body, fill=fg, font=_font(max(14, w // 40)))
        draw.text(
            (w * 0.12, h * 0.88),
            "v10 · no freemium · local canvas",
            fill=(140, 160, 180),
            font=_font(max(11, w // 55)),
        )

        path = _stamp("img", "png")
        img.save(path, format="PNG")
        return CreativeResult(
            ok=True,
            modality="image",
            engine="pillow_canvas",
            path=str(path),
            paths=[str(path)],
            mime="image/png",
            latency_ms=(time.time() - t0) * 1000,
            meta={"size": f"{w}x{h}", "style": style, "prompt": prompt[:200]},
        )
    except Exception as e:  # noqa: BLE001
        return CreativeResult(
            ok=False,
            modality="image",
            engine="pillow_canvas",
            error=str(e)[:300],
            latency_ms=(time.time() - t0) * 1000,
        )


def create_graphics(
    prompt: str,
    *,
    kind: str = "diagram",
    size: str = "1024x768",
) -> CreativeResult:
    """Graphics = poster/diagram/card via canvas + optional SVG twin."""
    t0 = time.time()
    img_r = create_image(prompt, size=size, style=kind, title=f"Graphics · {kind}")
    paths = list(img_r.paths)
    svg_path = None
    try:
        w, h = _parse_size(size)
        bg, accent, fg = _palette(prompt)
        lines = textwrap.wrap(prompt or kind, 48)[:12]
        text_svg = "".join(
            f'<text x="80" y="{160 + i * 36}" fill="rgb{fg}" font-size="22" '
            f'font-family="Segoe UI, Arial, sans-serif">{_xml_escape(line)}</text>'
            for i, line in enumerate(lines)
        )
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="rgb{bg}"/>
  <rect x="40" y="40" width="12" height="{h-80}" fill="rgb{accent}"/>
  <circle cx="{w*0.75}" cy="{h*0.3}" r="{min(w,h)*0.12}" fill="none" stroke="rgb{accent}" stroke-width="4"/>
  <text x="80" y="100" fill="rgb{accent}" font-size="32" font-family="Segoe UI, Arial, sans-serif">
    Fusion Hero OS · SVG Graphics
  </text>
  {text_svg}
  <text x="80" y="{h-40}" fill="#94a3b8" font-size="14">pseudo-inhouse · freemium=false</text>
</svg>
"""
        svg_path = _stamp("gfx", "svg")
        svg_path.write_text(svg, encoding="utf-8")
        paths.append(str(svg_path))
    except Exception as e:  # noqa: BLE001
        return CreativeResult(
            ok=img_r.ok,
            modality="graphics",
            engine="pillow_canvas+svg",
            path=img_r.path,
            paths=paths,
            mime="image/png",
            latency_ms=(time.time() - t0) * 1000,
            meta={"svg_error": str(e)[:120], "kind": kind},
            error=img_r.error,
        )
    return CreativeResult(
        ok=img_r.ok,
        modality="graphics",
        engine="pillow_canvas+svg",
        path=str(svg_path) if svg_path else img_r.path,
        paths=paths,
        mime="image/svg+xml" if svg_path else "image/png",
        latency_ms=(time.time() - t0) * 1000,
        meta={"kind": kind, "png": img_r.path},
    )


def _xml_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def create_pdf(
    prompt: str,
    *,
    title: str | None = None,
    pages: int = 2,
) -> CreativeResult:
    """Multi-page PDF via Pillow (no freemium SaaS)."""
    t0 = time.time()
    try:
        Image, ImageDraw, ImageFont = _pil()
        pages = max(1, min(20, int(pages)))
        w, h = 1240, 1754  # ~A4 @ 150dpi
        frames = []
        title_txt = title or "Fusion Hero OS · Pseudo-Inhouse Document"
        body = textwrap.wrap(prompt or "Document body", 52)
        for i in range(pages):
            bg, accent, fg = _palette(f"{prompt}-{i}")
            img = Image.new("RGB", (w, h), (252, 252, 250) if i % 2 == 0 else bg)
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, w, 16], fill=accent)
            draw.text((64, 80), title_txt, fill=accent if i == 0 else fg, font=_font(36))
            draw.text((64, 140), f"Page {i+1}/{pages} · v{PLATFORM}", fill=(100, 110, 120), font=_font(18))
            y = 220
            chunk = body[i * 18 : (i + 1) * 18] or [f"(page {i+1})"]
            for line in chunk:
                draw.text((64, y), line, fill=(20, 24, 32) if i % 2 == 0 else fg, font=_font(22))
                y += 36
            draw.text(
                (64, h - 80),
                "Pseudo-Inhouse · freemium=false · local PDF engine",
                fill=(120, 130, 140),
                font=_font(14),
            )
            frames.append(img.convert("RGB"))

        path = _stamp("doc", "pdf")
        first, rest = frames[0], frames[1:]
        first.save(path, "PDF", save_all=bool(rest), append_images=rest, resolution=150.0)
        return CreativeResult(
            ok=True,
            modality="pdf",
            engine="pillow_pdf",
            path=str(path),
            paths=[str(path)],
            mime="application/pdf",
            latency_ms=(time.time() - t0) * 1000,
            meta={"pages": pages, "title": title_txt},
        )
    except Exception as e:  # noqa: BLE001
        return CreativeResult(
            ok=False,
            modality="pdf",
            engine="pillow_pdf",
            error=str(e)[:300],
            latency_ms=(time.time() - t0) * 1000,
        )


def create_video(
    prompt: str,
    *,
    frames: int = 8,
    size: str = "640x360",
    fps: int = 4,
) -> CreativeResult:
    """Animated GIF always; MP4 if ffmpeg available."""
    t0 = time.time()
    try:
        Image, ImageDraw, ImageFont = _pil()
        w, h = _parse_size(size, (640, 360))
        frames = max(3, min(48, int(frames)))
        imgs = []
        for i in range(frames):
            bg, accent, fg = _palette(f"{prompt}-{i}")
            # animate accent position
            img = Image.new("RGB", (w, h), bg)
            draw = ImageDraw.Draw(img)
            cx = int(w * (0.2 + 0.6 * (i / max(1, frames - 1))))
            draw.ellipse([cx - 40, h // 2 - 40, cx + 40, h // 2 + 40], fill=accent)
            draw.text((24, 24), "Pseudo-Inhouse Video", fill=accent, font=_font(20))
            draw.text(
                (24, 60),
                textwrap.fill(prompt or "motion", 40)[:120],
                fill=fg,
                font=_font(14),
            )
            draw.text((24, h - 36), f"frame {i+1}/{frames}", fill=(150, 160, 170), font=_font(12))
            imgs.append(img)

        gif_path = _stamp("vid", "gif")
        imgs[0].save(
            gif_path,
            save_all=True,
            append_images=imgs[1:],
            duration=max(50, int(1000 / max(1, fps))),
            loop=0,
        )
        paths = [str(gif_path)]
        engine = "gif_animator"
        mime = "image/gif"
        out_path = str(gif_path)

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            # write temp pngs and encode mp4
            tmp = output_dir() / f"_frames_{int(time.time())}"
            tmp.mkdir(exist_ok=True)
            try:
                for i, im in enumerate(imgs):
                    im.save(tmp / f"f{i:04d}.png")
                mp4 = _stamp("vid", "mp4")
                cmd = [
                    ffmpeg,
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(tmp / "f%04d.png"),
                    "-pix_fmt",
                    "yuv420p",
                    "-c:v",
                    "libx264",
                    str(mp4),
                ]
                r = subprocess.run(cmd, capture_output=True, timeout=120)
                if r.returncode == 0 and mp4.exists():
                    paths.append(str(mp4))
                    out_path = str(mp4)
                    engine = "gif_animator+ffmpeg"
                    mime = "video/mp4"
            finally:
                for f in tmp.glob("*.png"):
                    f.unlink(missing_ok=True)
                tmp.rmdir()

        return CreativeResult(
            ok=True,
            modality="video",
            engine=engine,
            path=out_path,
            paths=paths,
            mime=mime,
            latency_ms=(time.time() - t0) * 1000,
            meta={"frames": frames, "fps": fps, "ffmpeg": bool(ffmpeg)},
        )
    except Exception as e:  # noqa: BLE001
        return CreativeResult(
            ok=False,
            modality="video",
            engine="gif_animator",
            error=str(e)[:300],
            latency_ms=(time.time() - t0) * 1000,
        )


def create(
    modality: str,
    prompt: str,
    **kwargs: Any,
) -> CreativeResult:
    mod = (modality or "image").lower().strip()
    if mod in ("image", "img", "png", "picture"):
        return create_image(prompt, **{k: v for k, v in kwargs.items() if k in ("size", "style", "title")})
    if mod in ("graphics", "graphic", "diagram", "poster", "svg", "banner"):
        kind = kwargs.get("kind") or ("svg" if mod == "svg" else mod if mod != "graphics" else "diagram")
        return create_graphics(prompt, kind=str(kind), size=kwargs.get("size", "1024x768"))
    if mod in ("pdf", "document", "doc"):
        return create_pdf(
            prompt,
            title=kwargs.get("title"),
            pages=int(kwargs.get("pages", 2)),
        )
    if mod in ("video", "gif", "anim", "mp4", "movie"):
        return create_video(
            prompt,
            frames=int(kwargs.get("frames", 8)),
            size=kwargs.get("size", "640x360"),
            fps=int(kwargs.get("fps", 4)),
        )
    return CreativeResult(
        ok=False,
        modality=mod,
        engine="none",
        error=f"Unknown modality: {mod}. Use image|graphics|pdf|video",
    )


def status() -> dict[str, Any]:
    engines = {
        "pillow_canvas": True,
        "pillow_pdf": True,
        "svg_writer": True,
        "gif_animator": True,
        "ffmpeg_slideshow": bool(shutil.which("ffmpeg")),
    }
    try:
        _pil()
    except Exception:
        engines["pillow_canvas"] = False
        engines["pillow_pdf"] = False
        engines["gif_animator"] = False

    return {
        "ok": True,
        "platform": PLATFORM,
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "pseudo_inhouse": True,
        "output_dir": str(output_dir()),
        "engines": engines,
        "modalities": ["image", "graphics", "svg", "pdf", "video"],
        "facade": {
            "status": "/api/creative/inhouse/status",
            "create": "/api/creative/inhouse/create",
            "openai_images": "/v1/images/generations",
        },
        "honesty": (
            "Local canvas/PDF/GIF engines are primary. "
            "No freemium SKUs. Optional membranes only behind this facade."
        ),
    }


def list_artifacts(limit: int = 30) -> dict[str, Any]:
    d = output_dir()
    files = sorted(d.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for p in files[: max(1, min(100, limit))]:
        if p.is_file() and not p.name.startswith("_"):
            items.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "bytes": p.stat().st_size,
                    "mtime": p.stat().st_mtime,
                }
            )
    return {"ok": True, "count": len(items), "items": items, "dir": str(d)}


def openai_image_response(result: CreativeResult) -> dict[str, Any]:
    """OpenAI-like images.generations shape (local path as b64-less url file)."""
    return {
        "created": int(time.time()),
        "data": [
            {
                "url": f"file://{result.path}" if result.path else None,
                "path": result.path,
                "revised_prompt": (result.meta or {}).get("prompt"),
            }
        ],
        "fusion": result.to_dict(),
    }


def main() -> int:
    print(json.dumps(status(), indent=2))
    r = create("image", "Heroic cyberpunk campfire — pseudo inhouse")
    print(json.dumps(r.to_dict(), indent=2)[:800])
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
