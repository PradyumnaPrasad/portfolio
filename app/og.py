"""Generate the 1200x630 social-share image (og:image) with Pillow.

Rendered once and cached in memory. Deliberately matches the RPG palette.
"""

from __future__ import annotations

import io
import textwrap
from functools import lru_cache

from app.config import SITE

W, H = 1200, 630
BG = (22, 18, 12)
INK = (236, 224, 200)
GOLD = (255, 207, 77)
MUTED = (160, 141, 111)
TILE = [(90, 160, 74), (95, 156, 47), (58, 110, 34)]
ROOFS = [(201, 162, 74), (74, 134, 201), (193, 74, 58), (58, 163, 138), (208, 138, 44)]


@lru_cache(maxsize=1)
def render_card() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # grass strip along the bottom, like the map
    px = 30
    for gy in range(H - 120, H, px):
        for gx in range(0, W, px):
            d.rectangle([gx, gy, gx + px, gy + px], fill=TILE[(gx // px + gy // px) % 3])
    # a little row of coloured-roof houses
    for i, roof in enumerate(ROOFS):
        hx = 90 + i * 150
        hy = H - 150
        d.rectangle([hx, hy, hx + 90, hy + 70], fill=INK)
        d.polygon([(hx - 8, hy), (hx + 45, hy - 46), (hx + 98, hy)], fill=roof)
        d.rectangle([hx + 36, hy + 30, hx + 54, hy + 70], fill=(90, 60, 35))

    big = ImageFont.load_default(size=76)
    mid = ImageFont.load_default(size=34)
    small = ImageFont.load_default(size=26)

    d.text((80, 92), "PORTFOLIO", font=small, fill=GOLD)
    d.text((80, 138), SITE["name"], font=big, fill=INK)
    for j, line in enumerate(textwrap.wrap(SITE["tagline"], width=48)):
        d.text((80, 250 + j * 44), line, font=mid, fill=INK)
    d.text(
        (80, 372),
        "CSE (AI/ML) @ SIT  ·  Data & AI intern at Hexango  ·  400+ DSA  ·  hackathon winner",
        font=small,
        fill=MUTED,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
