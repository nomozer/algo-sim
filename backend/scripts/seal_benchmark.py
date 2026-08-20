# -*- coding: utf-8 -*-
"""Khoá fingerprint cho SEALED benchmark.

Chạy MỘT LẦN ở pha EARLY, TRƯỚC khi chỉnh IR/schema/prompt. Sau đó mỗi lần
chạy lại chỉ để KIỂM con dấu còn nguyên.

Luật con dấu (spec 2026-08-20 §7.4):
    DEV được phép làm thay đổi IR.
    SEALED chỉ được phép làm thay đổi KẾT LUẬN của luận văn.

Thoát != 0 khi seal vỡ — dùng được trong CI.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEALED = ROOT / "docs" / "evaluation" / "semantic-benchmark" / "sealed" / "cases.json"
FINGERPRINT = SEALED.parent / "FINGERPRINT.txt"


def fingerprint_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not SEALED.exists():
        print(f"Thiếu {SEALED} — SEALED chưa được dựng (Task 1).")
        return 2

    digest = fingerprint_of(SEALED)

    if FINGERPRINT.exists():
        old = FINGERPRINT.read_text(encoding="utf-8").strip()
        if old != digest:
            print(
                "SEAL VỠ.\n"
                f"  fingerprint đã niêm phong : {old}\n"
                f"  fingerprint hiện tại      : {digest}\n"
                "SEALED đã bị sửa sau khi niêm phong. Theo §7.4, dataset này trở "
                "thành DEV/history và phải tạo một SEALED MỚI."
            )
            return 1
        print("Fingerprint khớp — seal còn nguyên.")
        return 0

    FINGERPRINT.write_text(digest + "\n", encoding="utf-8")
    print(f"Đã niêm phong: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
