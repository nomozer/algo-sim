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


# ── Mức yếu phải ĐẾN ĐƯỢC, không chỉ có tên trong bảng ───────────
# Mọi test ở trên kiểm BẢNG ÁNH XẠ, và bảng ánh xạ vẫn xanh kể cả khi đường sinh
# ra nó đã chết. Đó đúng là chuyện đã xảy ra: `is_supported()` mang docstring
# "có checker server-owned không?" nhưng thân hàm trả `kind in OBLIGATION_KINDS`,
# nên mức yếu KHÔNG BAO GIỜ kích hoạt — `verification_gap` thành mã chết, còn tỉ
# lệ "phát canonical an toàn" thì bị thổi lên vì hệ phát kết quả duyệt cây mà
# không có một cách kiểm độc lập nào.


def test_ham_kiem_checker_dung_bang_CHECKERS_lam_nguon():
    from app.simulation.semantic_program.obligations import (
        OBLIGATION_KINDS,
        has_server_owned_checker,
    )
    from app.simulation.semantic_program.postconditions import CHECKERS

    for kind in OBLIGATION_KINDS:
        assert has_server_owned_checker(kind) == (kind in CHECKERS), (
            f"{kind}: hỏi 'có checker không' mà trả lời theo 'có trong taxonomy "
            "không' — hai tập KHÁC NHAU"
        )


def test_co_that_it_nhat_mot_nghia_vu_muc_yeu():
    """Không còn kind nào thiếu checker ⇒ `verification_gap` thành rỗng nghĩa.

    Không phải lỗi — nhưng phải BIẾT, vì lúc ấy mọi con số "safe serve rate"
    trong luận văn bằng đúng "executability rate", và câu chuyện hai tỉ lệ tách
    nhau không còn gì để kể.
    """
    from app.simulation.semantic_program.obligations import (
        OBLIGATION_KINDS,
        has_server_owned_checker,
    )

    yeu = [k for k in OBLIGATION_KINDS if not has_server_owned_checker(k)]
    assert yeu == ["structural_traversal"], (
        f"tập nghĩa vụ mức yếu đã đổi: {yeu}. Thêm checker là tiến bộ THẬT — "
        "nhưng phải cập nhật luận văn, đừng để số cũ đứng nguyên."
    )


@pytest.mark.parametrize("cat", sorted(set(SEMANTIC_FAILURE_CATEGORY.values())))
def test_chi_dung_cac_category_da_khai(cat):
    assert cat in {
        "capability_gap",
        "insufficient_specification",
        "semantic_incomplete",
        "synthesis_exhausted",
        "verification_gap",
    }
