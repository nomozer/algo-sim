# -*- coding: utf-8 -*-
"""Build a compact contact sheet and reject blank browser captures."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat


def _font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _meaningful(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(image.resize((96, 64)))
    dynamic = max(channel[1] - channel[0] for channel in stat.extrema)
    variance = max(stat.var)
    if image.width < 200 or image.height < 150 or dynamic < 12 or variance < 10:
        raise ValueError(f"BLANK_OR_INVALID_SCREENSHOT:{path}")
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence.resolve()
    names = {"default.png", "rotated.png", "causal_closure.png", "refusal.png"}
    panels = sorted(path for path in root.rglob("*.png") if path.name in names)
    if not panels:
        raise ValueError("NO_CONTACT_SHEET_PANELS")
    images = [(path, _meaningful(path)) for path in panels]
    family_count = len({path.relative_to(root).parts[0] for path in panels})

    columns = 4
    rows = math.ceil(len(images) / columns)
    cell_w, cell_h, label_h = 360, 230, 34
    title_h, gap = 72, 14
    width = gap + columns * (cell_w + gap)
    height = title_h + gap + rows * (cell_h + label_h + gap)
    sheet = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, width, title_h), fill="#15243b")
    draw.text((20, 14), "Cross-family Scene3D semantic repair", fill="white", font=_font(25))
    draw.text((20, 44), f"{family_count} families · desktop/mobile · orbit · causal · refusal",
              fill="#b9ccec", font=_font(14))
    for index, (path, image) in enumerate(images):
        row, column = divmod(index, columns)
        x = gap + column * (cell_w + gap)
        y = title_h + gap + row * (cell_h + label_h + gap)
        label = str(path.relative_to(root)).replace("\\", "/")
        draw.rectangle((x, y, x + cell_w, y + label_h), fill="#304664")
        draw.text((x + 8, y + 9), label[:52], fill="white", font=_font(12))
        image.thumbnail((cell_w - 6, cell_h - 6), Image.Resampling.LANCZOS)
        px = x + (cell_w - image.width) // 2
        py = y + label_h + (cell_h - image.height) // 2
        sheet.paste(image, (px, py))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out, format="PNG", optimize=True)
    print(f"Wrote {args.out} with {len(images)} validated panels")


if __name__ == "__main__":
    main()
