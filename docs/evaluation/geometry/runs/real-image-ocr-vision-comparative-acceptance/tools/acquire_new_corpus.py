"""Acquire public VMMU images into ignored cache; never invoke an AI provider.

Run using the existing .superpowers/ocr-venv interpreter (requests/Pillow).
Metadata-only inventory is a draft until original images are visually reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[6]
CACHE = ROOT / ".superpowers/external_image_cache/new-corpus-vmmu"
API = "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset={}&length={}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=425)
    parser.add_argument("--count", type=int, default=125)
    args = parser.parse_args()
    assert os.environ.get("ALLOW_LIVE_AI") == "0"
    assert 0 < args.count <= 200
    CACHE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "AlgoSim-local-research-image-acquisition/1"
    inventory = []
    failures = []
    for offset in range(args.offset, args.offset + args.count):
        response = session.get(API.format(offset, 1), timeout=30)
        if response.status_code != 200:
            failures.append({"url": response.url, "http_status": response.status_code})
            (CACHE / "fetch_failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
            print("unavailable", offset, response.status_code, flush=True)
            if response.status_code == 429:
                break
            continue
        for record in response.json()["rows"]:
            row = record["row"]
            if not row["ID"].startswith("Math_"):
                continue
            index = record["row_idx"]
            path = CACHE / f"new_vmmu_full_r{index}_{row['ID']}"
            if not path.exists():
                response = session.get(row["image"]["src"], timeout=30)
                response.raise_for_status()
                path.write_bytes(response.content)
            with Image.open(path) as image:
                width, height = image.size
                image.verify()
            inventory.append({
                "row_idx": index, "dataset_id": row["ID"], "filename": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "width": width, "height": height, "bytes": path.stat().st_size,
                "api_row_url": API.format(index, 1), "original_image_url": row["image"]["src"],
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "dataset_multiple_question": row.get("multiple_question"),
                "dataset_answer_key": row.get("ground_truth"),
            })
        (CACHE / "candidate_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        print("downloaded", offset, "total", len(inventory), flush=True)
    for start in range(0, len(inventory), 12):
        sheet = Image.new("RGB", (1600, 1800), "#dddddd")
        draw = ImageDraw.Draw(sheet)
        for position, item in enumerate(inventory[start:start + 12]):
            with Image.open(CACHE / item["filename"]) as original:
                preview = original.convert("RGB")
                preview.thumbnail((780, 260))
                x, y = position % 2 * 800, position // 2 * 300
                sheet.paste(preview, (x, y + 25))
                draw.text((x + 5, y + 5), str(item["row_idx"]), fill="black")
        sheet.save(CACHE / f"contact_{start // 12}.jpg")
    assert len({item["sha256"] for item in inventory}) == len(inventory)


if __name__ == "__main__":
    main()
