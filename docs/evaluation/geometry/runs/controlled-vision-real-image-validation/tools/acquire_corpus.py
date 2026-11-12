"""Acquire public VMMU Math images into the ignored local cache and shortlist solid-geometry candidates.

No AI provider is called. Requests are paged (100 rows per metadata call) and paced; the tool stops at the
first HTTP 429 instead of retrying. Images never enter Git.

Selection is two-stage and its bias is measured, not assumed away:
  1. `screen`: Tesseract-only text of every image is matched against a deliberately loose, accent-insensitive
     keyword list. This uses one of the product's OCR engines, so images whose header words that engine cannot
     read at all are under-represented.
  2. `sheets`: contact sheets of the keyword hits AND of a seeded random sample of the non-hits are written for
     visual review, so the miss rate of stage 1 can be reported.

Run from backend/ with the backend interpreter:
  python <tools>/acquire_corpus.py list | download | screen | sheets
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
CACHE = ROOT / ".superpowers/external_image_cache/controlled-vision-vmmu"
META = CACHE / "math_rows_metadata.json"
SCREEN = CACHE / "keyword_screen.json"
DATASET = "anvo25/vmmu"
SERVER = "https://datasets-server.huggingface.co"
AGENT = {"User-Agent": "python-httpx"}  # generic on purpose: no project or user identity leaves this machine
ID_CORE = re.compile(r"Math_\d+_test_\d+_question_\d+")
KEYWORDS = ("chop", "lang tru", "hinh hop", "tu dien", "lap phuong", "khoi da dien", "mat phang", "s.abc", "abc.a", "abcd.a",
            "thiet dien", "nhi dien", "the tich")


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return " ".join("".join(c for c in text if unicodedata.category(c) != "Mn").split())


def previously_used() -> set[str]:
    """Dataset question ids already present in earlier corpora (by cached filename), whatever the split."""
    used = set()
    for path in (ROOT / ".superpowers/external_image_cache").rglob("*"):
        if path.is_file() and CACHE not in path.parents:
            match = ID_CORE.search(path.name)
            if match:
                used.add(match.group(0))
    return used


def list_rows() -> None:
    import httpx
    CACHE.mkdir(parents=True, exist_ok=True)
    # /rows over the contiguous Math block (row 240 onward) and a local subject check; /filter is unreliable (HTTP 500).
    rows, offset, total = [], 240, None
    with httpx.Client(timeout=60, headers=AGENT, trust_env=False) as client:
        while total is None or offset < total:  # total = rows in the whole split
            for attempt in range(3):  # a slow page is retried; a refusal (429/4xx) is not
                try:
                    response = client.get(f"{SERVER}/rows", params={"dataset": DATASET, "config": "default", "split": "full_vqa",
                                                                   "offset": offset, "length": 100})
                    break
                except httpx.TimeoutException:
                    print("timeout at offset", offset, "attempt", attempt + 1, flush=True)
                    time.sleep(15)
            else:
                break
            if response.status_code != 200:
                print("stopped", offset, response.status_code, flush=True)
                break
            page = response.json()
            total = page["num_rows_total"]
            for record in page["rows"]:
                row = record["row"]
                if row["subject"] != "Math":
                    continue
                rows.append({"row_idx": record["row_idx"], "dataset_id": row["ID"], "dataset_answer_key": row["ground_truth"],
                             "multiple_question": row["multiple_question"], "width": row["image"]["width"],
                             "height": row["image"]["height"], "signed_image_url": row["image"]["src"]})
            offset += 100
            print("listed", len(rows), "Math rows; next offset", offset, flush=True)
            if not any(record["row"]["subject"] == "Math" for record in page["rows"]):
                break
            time.sleep(2.0)
    if not rows:
        raise SystemExit("nothing listed; existing metadata kept")
    META.write_text(json.dumps({"dataset": DATASET, "split": "full_vqa", "filter": "subject='Math' (local)", "split_rows": total,
                                "listed_at_utc": datetime.now(timezone.utc).isoformat(), "rows": rows}, indent=1), encoding="utf-8")


def filename(row: dict) -> str:
    return f"r{row['row_idx']}_{row['dataset_id']}"


def download() -> None:
    import httpx
    meta = json.loads(META.read_text(encoding="utf-8"))
    used = previously_used()
    todo = [r for r in meta["rows"] if ID_CORE.search(r["dataset_id"]).group(0) not in used and not (CACHE / filename(r)).exists()]
    print("to download", len(todo), "| excluded as previously used", sum(ID_CORE.search(r["dataset_id"]).group(0) in used for r in meta["rows"]), flush=True)
    with httpx.Client(timeout=60, headers=AGENT, trust_env=False, follow_redirects=True) as client:
        for count, row in enumerate(todo, 1):
            response = client.get(row["signed_image_url"])
            if response.status_code != 200:
                print("stopped at", row["row_idx"], "http", response.status_code, "- rerun `list` if the signed URLs expired", flush=True)
                break
            (CACHE / filename(row)).write_bytes(response.content)
            if count % 25 == 0:
                print("downloaded", count, "of", len(todo), flush=True)
            time.sleep(0.6)


def screen() -> None:
    os.environ["ALLOW_LIVE_AI"] = "0"
    os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
    os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
    sys.path.insert(0, str(ROOT / "backend"))
    from app.ingestion import local_ocr as ocr

    meta = json.loads(META.read_text(encoding="utf-8"))
    done = json.loads(SCREEN.read_text(encoding="utf-8")) if SCREEN.exists() else {}
    for row in meta["rows"]:
        path = CACHE / filename(row)
        if not path.exists() or path.name in done:
            continue
        data = path.read_bytes()
        raw = ocr.run_local_ocr(data, engines=("tesseract",))
        text = fold(" ".join(line.get("text", "") for line in ((raw.get("engines") or {}).get("tesseract") or {}).get("lines", [])))
        done[path.name] = {"row_idx": row["row_idx"], "sha256": hashlib.sha256(data).hexdigest(),
                           "keyword_hits": [k for k in KEYWORDS if k in text], "tesseract_ok": bool(raw.get("ok"))}
        ocr.clear_local_ocr_cache()
        if len(done) % 50 == 0:
            SCREEN.write_text(json.dumps(done, indent=1), encoding="utf-8")
            print("screened", len(done), flush=True)
    SCREEN.write_text(json.dumps(done, indent=1), encoding="utf-8")
    ocr.shutdown_local_ocr()
    print("screened", len(done), "| keyword hits", sum(bool(v["keyword_hits"]) for v in done.values()))


def sheets(audit_size: int) -> None:
    from PIL import Image, ImageDraw
    done = json.loads(SCREEN.read_text(encoding="utf-8"))
    hits = sorted((n for n, v in done.items() if v["keyword_hits"]), key=lambda n: done[n]["row_idx"])
    rest = sorted(n for n, v in done.items() if not v["keyword_hits"])
    audit = sorted(random.Random(20261112).sample(rest, min(audit_size, len(rest))), key=lambda n: done[n]["row_idx"])
    # Hits are reviewed for transcription (2 large columns); audit tiles only need to reveal a missed solid-geometry item.
    for label, names, columns, per_sheet, box in (("hits", hits, 2, 8, (1000, 430)), ("audit", audit, 4, 16, (500, 240))):
        width = 2040 // columns
        for old in CACHE.glob(f"sheet_{label}_*.jpg"):
            old.unlink()
        for start in range(0, len(names), per_sheet):
            tiles = []
            for name in names[start:start + per_sheet]:
                with Image.open(CACHE / name) as original:
                    tile = original.convert("RGB")
                tile.thumbnail(box)
                tiles.append((done[name]["row_idx"], tile))
            sheet = Image.new("RGB", (2040, sum(max(t.height for _, t in tiles[i:i + columns]) + 34 for i in range(0, len(tiles), columns))), "#cccccc")
            draw, y = ImageDraw.Draw(sheet), 0
            for i in range(0, len(tiles), columns):
                for column, (row_idx, tile) in enumerate(tiles[i:i + columns]):
                    draw.text((column * width + 6, y + 4), f"row {row_idx}", fill="black")
                    sheet.paste(tile, (column * width + 5, y + 26))
                y += max(t.height for _, t in tiles[i:i + columns]) + 34
            sheet.save(CACHE / f"sheet_{label}_{start // per_sheet:02d}.jpg", quality=80)
    (CACHE / "sheet_index.json").write_text(json.dumps({"hits": hits, "audit": audit, "audit_seed": 20261112,
                                                        "non_hits": len(rest)}, indent=1), encoding="utf-8")
    print("hits", len(hits), "sheets", -(-len(hits) // 8), "| audit", len(audit), "of", len(rest), "non-hits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["list", "download", "screen", "sheets"])
    parser.add_argument("--audit-size", type=int, default=48)
    args = parser.parse_args()
    {"list": list_rows, "download": download, "screen": screen}.get(args.step, lambda: sheets(args.audit_size))()
