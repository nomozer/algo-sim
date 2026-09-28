# -*- coding: utf-8 -*-
"""Build contact sheet and per-witness crops from authoritative PNG sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    parser.add_argument("--measurement", required=True, type=Path)
    args = parser.parse_args()
    browser = json.loads(args.browser.read_text(encoding="utf-8"))
    measurement = json.loads(args.measurement.read_text(encoding="utf-8"))
    screenshots = sorted(args.run_dir.glob("screenshots/**/*.png"))
    thumbs = []
    for path in screenshots:
        image = Image.open(path).convert("RGB")
        image.thumbnail((360, 220))
        thumbs.append((path.relative_to(args.run_dir).as_posix(), image.copy()))
    columns = 3
    cell_w, cell_h = 380, 260
    rows = max(1, (len(thumbs) + columns - 1) // columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(thumbs):
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        sheet.paste(image, (x + 10, y + 28))
        draw.text((x + 10, y + 8), label[:58], fill="black")
    sheet.save(args.run_dir / "contact-sheet.png")

    crop_root = args.run_dir / "crops"
    crop_root.mkdir(parents=True, exist_ok=True)
    for scenario_id, scenario in measurement.get("scenarios", {}).items():
        state = scenario.get("desktop", {}).get("neutral_final", {})
        positive = browser.get("scenarios", {}).get(scenario_id, {}).get("positive", {}).get("desktop", {})
        source_value = positive.get("screenshots", {}).get("neutral_final")
        if not source_value:
            continue
        source = Path(source_value.get("path", "") if isinstance(source_value, dict) else source_value)
        if not source.is_absolute():
            source = args.run_dir / source
        if not source.exists():
            candidates = list(args.run_dir.glob(
                f"screenshots/{scenario_id}/desktop/neutral_final.png"
            ))
            if not candidates:
                continue
            source = candidates[0]
        image = Image.open(source).convert("RGB")
        box = positive.get("canvas_box") or {"x": 0, "y": 0}
        for index, witness in enumerate(state.get("witnesses", [])):
            sx, sy = witness["screen_coordinate"]
            cx, cy = int(box.get("x", 0) + sx), int(box.get("y", 0) + sy)
            half = 64
            crop = image.crop((max(0, cx - half), max(0, cy - half),
                               min(image.width, cx + half), min(image.height, cy + half)))
            safe_edge = witness["edge_id"].replace(":", "_").replace("/", "_")
            target = crop_root / scenario_id
            target.mkdir(parents=True, exist_ok=True)
            crop.save(target / f"{safe_edge}-{index}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
