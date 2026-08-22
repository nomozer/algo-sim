# -*- coding: utf-8 -*-
"""Soát cache OCR để dựng bản đồ chương/bài và định vị khối bài tập.

Đây là bước KHẢO SÁT của coverage audit: nó chỉ nói *chương nào nằm ở trang
nào* và *trang nào có khối bài tập*, để việc đọc kỹ sau đó nhắm đúng chỗ thay
vì quét mù 483 trang.

Nó KHÔNG quyết định bài nào eligible — đó là việc đọc và phán đoán, làm ở bước
sau theo rubric đã khai trong SOURCE_UNIVERSE.md.

    python scan_cache.py tin-hoc-11-ict
    python scan_cache.py tin-hoc-11-ict --exercises
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / "data" / "knowledge" / "ocr-cache"

#: Nhãn mở đầu một khối bài tập trong SGK bộ Kết nối tri thức.
NHAN_BAI_TAP = ("LUYỆN TẬP", "VẬN DỤNG", "THỰC HÀNH", "CÂU HỎI",
                "Nhiệm vụ", "Hoạt động", "Câu hỏi")

_BAI = re.compile(r"^\s*BÀI\s+(\d{1,2})\b", re.M | re.I)
_CHUDE = re.compile(r"^\s*CHỦ\s*ĐỀ\s+([0-9A-Z]+)\b", re.M | re.I)


def _cache(ten: str) -> dict[str, str]:
    p = CACHE / f"{ten}.json"
    if not p.exists():
        raise SystemExit(f"Chưa có cache: {p}. Chạy scripts/ocr_sgk_ingest.py trước.")
    return json.loads(p.read_text(encoding="utf-8"))


def ban_do(ten: str) -> list[dict]:
    """Bài/chủ đề bắt đầu ở trang PDF nào."""
    c = _cache(ten)
    ra = []
    for k in sorted(c, key=int):
        t = c[k]
        for m in _CHUDE.finditer(t):
            ra.append({"pdf_page": int(k), "loai": "chủ đề", "so": m.group(1),
                       "dong": t[m.start():m.start() + 90].replace("\n", " ")})
        for m in _BAI.finditer(t):
            ra.append({"pdf_page": int(k), "loai": "bài", "so": m.group(1),
                       "dong": t[m.start():m.start() + 90].replace("\n", " ")})
    return ra


def trang_co_bai_tap(ten: str) -> list[dict]:
    c = _cache(ten)
    ra = []
    for k in sorted(c, key=int):
        t = c[k]
        co = sorted({n for n in NHAN_BAI_TAP if n in t})
        if co:
            ra.append({"pdf_page": int(k), "nhan": co})
    return ra


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("book")
    p.add_argument("--exercises", action="store_true")
    a = p.parse_args()

    if a.exercises:
        rows = trang_co_bai_tap(a.book)
        print(f"{len(rows)} trang có khối bài tập")
        for r in rows:
            print(f"  PDF {r['pdf_page']:3} · {', '.join(r['nhan'])}")
    else:
        for r in ban_do(a.book):
            print(f"PDF {r['pdf_page']:3} · {r['loai']:7} {r['so']:>3} · {r['dong'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
