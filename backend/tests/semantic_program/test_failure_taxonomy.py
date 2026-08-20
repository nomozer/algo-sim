# -*- coding: utf-8 -*-
"""`verification_gap` TÁCH HẲN `capability_gap` (spec §3.6, §5.4).

Hai câu hỏi khác nhau về nhận thức luận:

    capability_gap    — "Máy có thực thi được không?"                 → KHÔNG
    verification_gap  — "Máy chạy được, nhưng có đủ bằng chứng để
                         phát canonical cho học sinh không?"          → CHƯA

Gộp làm một là báo cáo sai năng lực của chính hệ, và xoá mất đúng cái phân biệt
mà đề tài lấy làm đóng góp. Nó cũng tách được hai chỉ số phải báo riêng:

    Generative executability rate   ≠   Safe serve rate
"""
import pytest

from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY, ErrorCode


def test_muc_yeu_la_verification_gap_khong_phai_capability_gap():
    cat = SEMANTIC_FAILURE_CATEGORY[ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE.value]
    assert cat == "verification_gap"
    assert cat != "capability_gap"


def test_khong_chay_duoc_moi_la_capability_gap():
    """Chương trình không hợp lệ / hết ngân sách = KHÔNG thực thi được."""
    for code in (ErrorCode.SEMANTIC_PROGRAM_INVALID,
                 ErrorCode.INTERPRETER_BUDGET_EXHAUSTED):
        assert SEMANTIC_FAILURE_CATEGORY[code.value] == "capability_gap"


def test_thieu_du_lieu_de_la_insufficient_specification():
    """Đề không cho dãy ⇒ hỏi lại, KHÔNG phải 'hệ không làm được'."""
    assert (
        SEMANTIC_FAILURE_CATEGORY[ErrorCode.INPUT_NOT_GROUNDED.value]
        == "insufficient_specification"
    )


def test_nghia_vu_thieu_hoac_khong_hien_thuc_hoa_la_semantic_incomplete():
    for code in (ErrorCode.REQUESTED_OPERATION_UNCOVERED,
                 ErrorCode.OBLIGATION_WITNESS_UNREALIZED):
        assert SEMANTIC_FAILURE_CATEGORY[code.value] == "semantic_incomplete"


def test_hau_dieu_kien_vi_pham_cung_la_verification_gap():
    """Chạy được nhưng tự mâu thuẫn ⇒ chưa đủ bằng chứng, không phải bất lực."""
    assert (
        SEMANTIC_FAILURE_CATEGORY[ErrorCode.POSTCONDITION_VIOLATED.value]
        == "verification_gap"
    )


def test_oracle_mismatch_KHONG_co_failure_category():
    """Telemetry-only — không bao giờ thành phán quyết trả cho người dùng."""
    assert ErrorCode.ORACLE_SEMANTIC_MISMATCH.value not in SEMANTIC_FAILURE_CATEGORY


@pytest.mark.parametrize("cat", sorted(set(SEMANTIC_FAILURE_CATEGORY.values())))
def test_chi_dung_cac_category_da_khai(cat):
    assert cat in {
        "capability_gap",
        "insufficient_specification",
        "semantic_incomplete",
        "synthesis_exhausted",
        "verification_gap",
    }
