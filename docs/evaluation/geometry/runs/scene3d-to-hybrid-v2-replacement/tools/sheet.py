# -*- coding: utf-8 -*-
"""Contact sheet per fixture: rows = viewport, columns = camera gesture. Review aid only (no assertion).

    python sheet.py <frames dir> <out dir>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
CAMS = ["default", "quarter", "half", "back", "high", "low"]
W = 360
ids = sorted({p.name.rsplit("-", 2)[0] for p in SRC.glob("*-1440-default.png")})
for fid in ids:
    tiles = []
    for width in (1440, 390):
        for cam in CAMS:
            p = SRC / f"{fid}-{width}-{cam}.png"
            if p.is_file():
                im = Image.open(p).convert("RGB")
                im = im.resize((W, int(im.height * W / im.width)))
                ImageDraw.Draw(im).text((6, 6), f"{width} {cam}", fill=(200, 0, 0))
                tiles.append((width, im))
    rows = [[t for w, t in tiles if w == width] for width in (1440, 390)]
    h = sum(max(t.height for t in r) for r in rows if r)
    sheet = Image.new("RGB", (W * len(CAMS), h), "white")
    y = 0
    for r in rows:
        if not r:
            continue
        for i, t in enumerate(r):
            sheet.paste(t, (i * W, y))
        y += max(t.height for t in r)
    sheet.save(OUT / f"{fid}.png")
print(len(ids), "sheets")
