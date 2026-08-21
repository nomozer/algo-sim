# -*- coding: utf-8 -*-
"""Khoá con dấu SEALED benchmark (spec 2026-08-20 §7.4).

DEV được phép làm thay đổi IR. SEALED chỉ được phép làm thay đổi KẾT LUẬN.
Sửa SEALED sau khi niêm phong ⇒ mọi con số held-out thu được đều rỗng nghĩa.
"""
import hashlib
from pathlib import Path

import pytest

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


# ── Khớp nối seal_benchmark ↔ runner ─────────────────────────────
# Hai script được viết RỜI NHAU: `seal_benchmark.py` GHI vân tay, còn
# `run_sealed_evaluation._kiem_seal()` ĐỌC nó. Trước 2026-08-22 sự tương thích
# ấy chưa có gì khoá — đổi định dạng ghi (thêm nhãn, bỏ newline, viết hoa hex)
# là runner từ chối một tập hoàn toàn hợp lệ, và nó từ chối ĐÚNG LÚC lượt chạy
# duy nhất bắt đầu.
#
# Các test dưới chạy trên đường dẫn TẠM: cố ý không dựng `sealed/` giả trong
# kho mã, vì một `FINGERPRINT.txt` giả nằm đó là thứ có thể bị nhầm là con dấu
# thật.


def _hai_script():
    import importlib.util

    scripts = ROOT / "backend" / "scripts"
    ra = []
    for ten in ("seal_benchmark", "run_sealed_evaluation"):
        spec = importlib.util.spec_from_file_location(ten, scripts / f"{ten}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        ra.append(m)
    return ra


@pytest.fixture()
def con_dau(tmp_path, monkeypatch):
    seal, runner = _hai_script()
    cases = tmp_path / "cases.json"
    fp = tmp_path / "FINGERPRINT.txt"
    for mod in (seal, runner):
        monkeypatch.setattr(mod, "SEALED", cases)
        monkeypatch.setattr(mod, "FINGERPRINT", fp)
    return seal, runner, cases, fp


def test_chua_co_cases_thi_seal_thoat_2(con_dau):
    seal, _, _, _ = con_dau
    assert seal.main() == 2


def test_niem_phong_roi_runner_doc_duoc_dung_van_tay(con_dau):
    """Khớp nối: cái này ghi, cái kia đọc — phải cùng một định dạng."""
    seal, runner, cases, fp = con_dau
    cases.write_text('{"cases": [{"case_id": "x"}]}', encoding="utf-8")

    assert seal.main() == 0, "niêm phong lần đầu phải thành công"
    assert fp.exists()
    assert seal.main() == 0, "chạy lại khi không sửa gì phải báo còn nguyên"

    van_tay = runner._kiem_seal()
    assert van_tay == hashlib.sha256(cases.read_bytes()).hexdigest()


def test_sua_sau_khi_niem_phong_thi_CA_HAI_deu_tu_choi(con_dau):
    """Tiêm lỗi — guard chưa từng đỏ là guard chưa được chứng minh."""
    seal, runner, cases, _ = con_dau
    cases.write_text('{"cases": [{"case_id": "x"}]}', encoding="utf-8")
    seal.main()

    cases.write_text('{"cases": [{"case_id": "x", "them": 1}]}', encoding="utf-8")
    assert seal.main() == 1, "seal_benchmark không phát hiện file bị sửa"
    with pytest.raises(runner.DungSach, match="BỊ SỬA"):
        runner._kiem_seal()


@pytest.mark.skipif(
    not SEALED.exists(), reason="SEALED chưa được dựng (Task 1 — cần nguồn đề từ user)"
)
def test_sealed_khong_bi_sua_sau_khi_niem_phong():
    assert FINGERPRINT.exists(), (
        "SEALED tồn tại nhưng chưa niêm phong. Chạy backend/scripts/seal_benchmark.py "
        "TRƯỚC khi chỉnh IR/schema/prompt."
    )
    expected = FINGERPRINT.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(SEALED.read_bytes()).hexdigest()
    assert actual == expected, (
        "SEALED benchmark đã bị sửa sau khi niêm phong. Theo luật con dấu "
        "(spec §7.4), dataset này trở thành DEV/history và phải tạo SEALED mới."
    )
