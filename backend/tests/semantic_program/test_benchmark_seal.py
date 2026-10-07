# -*- coding: utf-8 -*-
"""Khoá con dấu SEALED benchmark (spec 2026-08-20 §7.4).

DEV được phép làm thay đổi IR. SEALED chỉ được phép làm thay đổi KẾT LUẬN.
Sửa SEALED sau khi niêm phong ⇒ mọi con số held-out thu được đều rỗng nghĩa.

repo-cleanup: lượt SEALED của miền Tin học đã chạy; `seal_benchmark.py` và `run_sealed_evaluation.py` đã gỡ cùng các
test khớp nối giữa chúng. Còn lại đúng phần khoá BẰNG CHỨNG: tập SEALED đã niêm phong vẫn nằm trong kho (bất biến,
AGENTS §4) và không được sửa sau con dấu.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "docs" / "evaluation" / "semantic-benchmark"
SEALED = BENCH / "sealed" / "cases.json"
FINGERPRINT = SEALED.parent / "FINGERPRINT.txt"


def test_rubric_va_freeze_protocol_ton_tai_truoc_khi_seal():
    """Population phải được định nghĩa TRƯỚC, độc lập cài đặt."""
    assert (BENCH / "eligibility_rubric.md").exists(), (
        "Thiếu eligibility rubric — không có nó thì phạm vi tự tham chiếu vào IR"
    )
    assert (BENCH / "freeze_protocol.md").exists(), "Thiếu freeze protocol"


def test_sealed_khong_bi_sua_sau_khi_niem_phong():
    assert SEALED.exists() and FINGERPRINT.exists(), "bằng chứng SEALED đã niêm phong phải còn nguyên trong kho"
    expected = FINGERPRINT.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(SEALED.read_bytes()).hexdigest()
    assert actual == expected, (
        "SEALED benchmark đã bị sửa sau khi niêm phong. Theo luật con dấu "
        "(spec §7.4), dataset này trở thành DEV/history và phải tạo SEALED mới."
    )
