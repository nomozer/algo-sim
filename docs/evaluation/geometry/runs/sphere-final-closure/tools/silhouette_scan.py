"""Pixel check of the sphere outline on canvas screenshots (presentation evidence, not a geometry oracle).

    python silhouette_scan.py <capture dir> <name> <width>   → JSON per orbit frame

The sphere disc is located from its bluish-grey fill (b − r ≥ 6): centre and radius R from the fill's bounding box
(the centroid is pulled by curves drawn over the fill). For 360 rays, scanning INWARD from the canvas border, the
first dark pixel (luminance < 120) must lie within R ± 6 px: otherwise the outline is missing or too faint on that ray
(`gaps`). Fill-colour tests near the limb are not used — layered back faces change the fill tone there (found while
certifying this scanner on frames that visibly have a continuous outline). Also reported: `radius_cv` (a perspective
sphere outline is a circle) and the lightest outline luminance (`outline_tone_max`, uneven tone).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image


def scan(path: Path) -> dict:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    fill = [(x, y) for y in range(0, h, 2) for x in range(0, w, 2)
            if px[x, y][2] - px[x, y][0] >= 6 and sum(px[x, y]) > 500]
    if not fill:
        return {"error": "no sphere fill"}
    x0, x1 = min(p[0] for p in fill), max(p[0] for p in fill)
    y0, y1 = min(p[1] for p in fill), max(p[1] for p in fill)
    cx, cy, rad = (x0 + x1) / 2, (y0 + y1) / 2, ((x1 - x0) + (y1 - y0)) / 4
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]  # noqa: E731
    radii, tones, gaps = [], [], []
    for k in range(360):
        a = math.radians(k)
        dx, dy = math.cos(a), math.sin(a)
        hit = None
        for t in range(int(rad + 40), int(rad - 40), -1):
            x, y = int(round(cx + dx * t)), int(round(cy + dy * t))
            if 0 <= x < w and 0 <= y < h and lum(px[x, y]) < 120:
                hit = (t, lum(px[x, y]))
                break
        if hit is None or abs(hit[0] - rad) > 6:
            gaps.append(k)
        else:
            radii.append(hit[0])
            tones.append(hit[1])
    mean = sum(radii) / len(radii) if radii else 0
    sd = math.sqrt(sum((r - mean) ** 2 for r in radii) / len(radii)) if radii else 0
    return {"gaps": len(gaps), "gap_angles": gaps[:12], "radius": round(rad, 1),
            "radius_cv": round(sd / mean, 4) if mean else None,
            "outline_tone_max": round(max(tones), 1) if tones else None}


def main() -> int:
    d, name, width = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    rows = {p.stem.split("-")[-1]: scan(p) for p in sorted(d.glob(f"{name}-{width}-orbit*.png"))}
    print(json.dumps(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
