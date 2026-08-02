#!/usr/bin/env python3
"""Relabel shuSHU Instagram square BIG ALPHA (1080) to platform VERSION."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "memes" / "shuSHU_insta_notarnkappe_bigalpha_v13_square.png"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() or "15.2.0"


def font(size: int):
    for p in (
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ):
        if Path(p).is_file():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def paint_right_align(draw, text, *, right_x, y, fill, fsize):
    f = font(fsize)
    bb = draw.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    x = right_x - tw
    glow = (0, 80, 120)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
        draw.text((x + dx, y + dy), text, font=f, fill=glow)
    draw.text((x, y), text, font=f, fill=fill)


def paint_left(draw, text, *, x, y, fill, fsize):
    f = font(fsize)
    glow = (0, 80, 120)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
        draw.text((x + dx, y + dy), text, font=f, fill=glow)
    draw.text((x, y), text, font=f, fill=fill)


def main():
    im = Image.open(SRC).convert("RGB")
    assert im.size == (1080, 1080)
    draw = ImageDraw.Draw(im)

    # 1) Cover mid-right "FUSION HERO OS v13.0.0" (measured cyan band y~801-813, x~853-1064)
    draw.rectangle((835, 792, 1075, 828), fill=(4, 6, 18))
    paint_right_align(
        draw,
        f"FUSION HERO OS v{VERSION}",
        right_x=1064,
        y=800,
        fill=(0, 229, 255),
        fsize=22,
    )

    # 2) Cover footer subtitle (y~1011-1027, x~58-550)
    draw.rectangle((50, 1004, 580, 1036), fill=(5, 8, 16))
    paint_left(
        draw,
        f"Fusion Hero OS v{VERSION}  ·  AscensionOS v9.10",
        x=58,
        y=1010,
        fill=(0, 210, 235),
        fsize=20,
    )

    outs = [
        ROOT / "memes" / f"shuSHU_insta_notarnkappe_bigalpha_v{VERSION.replace('.', '_')}_square.png",
        ROOT / "memes" / "shuSHU_insta_notarnkappe_bigalpha_v15_square.png",
        ROOT / "memes" / "shuSHU_insta_notarnkappe_bigalpha_square.png",
        ROOT / "docs" / "dissertation" / "assets" / f"shuSHU_insta_notarnkappe_bigalpha_v{VERSION.replace('.', '_')}_square.png",
        ROOT / "docs" / "dissertation" / "assets" / "shuSHU_insta_notarnkappe_bigalpha_v15_square.png",
        ROOT / "docs" / "dissertation" / "assets" / "shuSHU_insta_notarnkappe_bigalpha_square.png",
    ]
    for o in outs:
        o.parent.mkdir(parents=True, exist_ok=True)
        im.save(o, format="PNG", optimize=True)

    digest = hashlib.sha256(outs[-1].read_bytes()).hexdigest()
    (ROOT / "docs" / "ops" / "BIG_ALPHA_INSTA_NOTARNKAPPE_SQUARE.md").write_text(
        f"""# shuSHU Instagram square — NO TARNKAPPE · PUBLIC (BIG ALPHA)

**Policy:** public branding tile — *not* hypertarnkappe / identity scrub.  
**Source desktop:** `OneDrive/Desktop/shuSHU_insta_notarnkappe_bigalpha_v13_square.png`  
**Platform pin:** root `VERSION` = **{VERSION}** (relabeled from visual v13.0.0)

## Visual

| Field | Value |
|-------|--------|
| Format | 1080×1080 Instagram square |
| Brand | shuSHU · 95guknow |
| Badge | NO TARNKAPPE · PUBLIC |
| Title | ASCENSIONOS / BIG ALPHA |
| Left mid | v9.10 ASPIRATIONAL (unchanged — aspirational track) |
| Right mid | FUSION HERO OS v{VERSION} |
| Footer | Fusion Hero OS v{VERSION} · AscensionOS v9.10 |
| SHA256 (consumer primary) | `{digest}` |

## Repo paths

### Historical v13 snapshot (unmodified desktop import)
- `memes/shuSHU_insta_notarnkappe_bigalpha_v13_square.png`
- `docs/dissertation/assets/shuSHU_insta_notarnkappe_bigalpha_v13_square.png`

### Relabeled to kanon v{VERSION}
- `memes/shuSHU_insta_notarnkappe_bigalpha_square.png` (consumer primary)
- `memes/shuSHU_insta_notarnkappe_bigalpha_v15_square.png`
- `memes/shuSHU_insta_notarnkappe_bigalpha_v{VERSION.replace('.', '_')}_square.png`
- same under `docs/dissertation/assets/`

## Method (honesty)

PIL paint of discrete version strings only — composition / DNA / title art preserved.  
Does **not** overwrite landscape runtime `big_ALPHA.png` set (see `BIG_ALPHA_ASSET_V15.md`).

Script: `scripts/relabel_shuSHU_insta_square.py`
""",
        encoding="utf-8",
        newline="\n",
    )
    print("VERSION", VERSION)
    print("sha256", digest)
    # probes for QA
    im.crop((680, 780, 1080, 900)).save(ROOT / "_qa_right.png")
    im.crop((0, 990, 700, 1075)).save(ROOT / "_qa_footer.png")
    print("qa crops written")


if __name__ == "__main__":
    main()
