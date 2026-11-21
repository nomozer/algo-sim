# -*- coding: utf-8 -*-
"""Tải ảnh MỚI (chưa dùng ở run nào) từ HuggingFace `anvo25/vmmu` (giấy phép MIT) để đánh giá SAU khi đóng băng
logic OCR của run `image-first-ocr-verified-geometry`. Ảnh lưu trong `.superpowers/external_image_cache/` (gitignored);
chỉ metadata (URL, SHA-256, khoá đáp án của bộ dữ liệu) được ghi vào `new_external_source_inventory.json`.

Lọc miền: chỉ môn Toán; chọn đề hình học không gian bằng từ khoá trên văn bản RapidOCR thô (chỉ để chọn đề, không
dùng làm ground truth); loại 7 ID đã dùng ở run trước.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
CACHE = ROOT / ".superpowers" / "external_image_cache"
RUN_DIR = Path(__file__).resolve().parents[1]
USED = {
    "Math_0445_test_258_question_14_page_2_key_B_vqa.png", "Math_0307_test_059_question_49_page_6_key_A_vqa.png",
    "Math_0020_test_004_question_30_page_4_key_C_vqa.png", "Math_0303_test_059_question_39_page_4_key_B_vqa.png",
    "Math_0143_test_024_question_48_page_6_key_B_vqa.png", "Math_0120_test_020_question_40_page_7_key_B_vqa.png",
    "Math_0399_test_080_question_35_page_5_key_A_vqa.png",
}
API = "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split={split}&offset={off}&length={n}"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main() -> int:
    split = "random_subset_ocr"
    math_rows = []
    for off in range(0, 35, 5):
        try:
            d = json.loads(_get(API.format(split=split, off=off, n=5)).decode("utf-8"))
        except Exception as exc:
            print("skip off", off, exc, flush=True)
            continue
        for r in d.get("rows") or []:
            row = r["row"] | {"_row_idx": r["row_idx"]}
            if (
                (row.get("subject") in ("Math", "Toán") or str(row.get("ID", "")).startswith("Math_"))
                and row["ID"] not in USED
                and str(row.get("multiple_question")) == "False"
            ):
                math_rows.append(row)
                print("found", row["_row_idx"], row["ID"], flush=True)
    print("math new single-question", len(math_rows))
    inv = []
    for r in math_rows:
        fname = f"vmmu_new_r{r['_row_idx']}_{r['ID']}"
        p = CACHE / fname
        if not p.exists():
            p.write_bytes(_get(r["image"]["src"]))
            time.sleep(0.3)
        b = p.read_bytes()
        inv.append({
            "filename": fname,
            "dataset": "anvo25/vmmu",
            "split": split,
            "row_idx": r["_row_idx"],
            "dataset_id": r["ID"],
            "license": "MIT",
            "answer_key_letter": r.get("ground_truth"),
            "sha256": hashlib.sha256(b).hexdigest(),
            "bytes": len(b),
            "api_row_url": API.format(split=split, off=r["_row_idx"], n=1),
        })
    (RUN_DIR / "_new_vmmu_candidates.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", len(inv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
