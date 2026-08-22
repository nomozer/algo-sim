# -*- coding: utf-8 -*-
"""Đọc SGK bản QUÉT thành text bằng Google Cloud Vision, có CACHE trên đĩa.

VÌ SAO CẦN: năm cuốn SGK trong `data/knowledge/sources/` là ảnh quét, không có
lớp chữ — `pdftotext` trả 60 ký tự cho 60 trang, đúng bằng số dấu ngắt trang.
Repo không có RAG/index/cache nào để tái dùng: `data/knowledge/` chỉ có PDF
nguồn, còn `app/ingestion/input.py` là lớp chuẩn hoá input của SẢN PHẨM
(text/docx/ảnh), không đọc PDF.

Đường đọc: PyMuPDF dựng ảnh trang → Cloud Vision `document_text_detection`.
Credential lấy từ `.secrets/` qua `GOOGLE_APPLICATION_CREDENTIALS`; script
KHÔNG in và KHÔNG ghi giá trị secret vào bất kỳ artifact nào.

CACHE là điểm chính: mỗi trang OCR đúng MỘT lần rồi ghi vào
`data/knowledge/ocr-cache/<sách>.json` (thư mục `data/` bị gitignore nên text
SGK không vào kho mã). Chạy lại chỉ đọc cache, không tốn call.

    python scripts/ocr_sgk_ingest.py --book tin-hoc-11-ict
    python scripts/ocr_sgk_ingest.py --all
    python scripts/ocr_sgk_ingest.py --all --stats   # chỉ báo cache, 0 call
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NGUON = ROOT / "data" / "knowledge" / "sources"
CACHE = ROOT / "data" / "knowledge" / "ocr-cache"
SECRET = ROOT / ".secrets" / "lecture-ai-501210-74c8077e09f6.json"

SACH = ("tin-hoc-10", "tin-hoc-11-cs", "tin-hoc-11-ict",
        "tin-hoc-12-cs", "tin-hoc-12-ict")

DPI = 200


def _cache_path(ten: str) -> Path:
    return CACHE / f"{ten}.json"


def doc_cache(ten: str) -> dict[str, str]:
    p = _cache_path(ten)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _client():
    """Client Cloud Vision. Secret nạp qua biến môi trường, không log ra."""
    if not SECRET.exists():
        raise SystemExit(f"Thiếu credential: {SECRET.relative_to(ROOT)}")
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(SECRET))
    from google.cloud import vision

    return vision.ImageAnnotatorClient(), vision


def ingest(ten: str, chi_thong_ke: bool = False) -> dict:
    import pymupdf

    pdf = NGUON / f"{ten}.pdf"
    doc = pymupdf.open(pdf)
    cache = doc_cache(ten)
    tong = len(doc)
    thieu = [i for i in range(tong) if str(i + 1) not in cache]

    if chi_thong_ke or not thieu:
        return {"sach": ten, "tong_trang": tong, "tu_cache": tong - len(thieu),
                "ocr_moi": 0, "con_thieu": len(thieu)}

    client, vision = _client()
    moi = 0
    for i in thieu:
        img = doc[i].get_pixmap(dpi=DPI).tobytes("png")
        resp = client.document_text_detection(image=vision.Image(content=img))
        if resp.error.message:
            print(f"  trang {i+1}: LỖI OCR — {resp.error.message[:120]}",
                  file=sys.stderr)
            continue
        cache[str(i + 1)] = resp.full_text_annotation.text
        moi += 1
        if moi % 20 == 0:
            CACHE.mkdir(parents=True, exist_ok=True)
            _cache_path(ten).write_text(
                json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"  {ten}: {moi}/{len(thieu)}", flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    _cache_path(ten).write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {"sach": ten, "tong_trang": tong, "tu_cache": tong - len(thieu),
            "ocr_moi": moi, "con_thieu": tong - len(cache)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", choices=SACH)
    p.add_argument("--all", action="store_true")
    p.add_argument("--stats", action="store_true",
                   help="chỉ báo trạng thái cache, không gọi API")
    a = p.parse_args()

    ds = list(SACH) if a.all else ([a.book] if a.book else [])
    if not ds:
        p.print_help()
        return 2

    tong_cache = tong_moi = 0
    for ten in ds:
        kq = ingest(ten, chi_thong_ke=a.stats)
        tong_cache += kq["tu_cache"]
        tong_moi += kq["ocr_moi"]
        print(f"{kq['sach']:18} {kq['tong_trang']:4} trang · "
              f"cache {kq['tu_cache']:4} · OCR mới {kq['ocr_moi']:4} · "
              f"còn thiếu {kq['con_thieu']}")
    print(f"\ncached_pages_reused: {tong_cache}")
    print(f"document_pipeline_pages: {tong_moi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
