# -*- coding: utf-8 -*-
"""TASK 3 — ranh giới GIẢ THIẾT MÔ HÌNH HOÁ vs KHAI ĐÁP ÁN. **0 API call.**

Cơ chế có từ Wave 2; file này khoá **ranh giới** của nó bằng đúng cặp ca mà đặc
tả TASK 3 nêu, cộng những lối vòng mà Wave 3 vừa mở ra.

Vì sao cần một file riêng dù `test_geometry_wave2.py` đã có test: Wave 3 nới
grounding ở hai chỗ (chuẩn hoá id · hạ cấp trích dẫn hỏng). Mỗi lần nới một cổng
an toàn thì tập ca ÂM phải được kiểm lại — nới đúng là nới mà mọi ca âm cũ vẫn
âm. Không kiểm lại thì "nới một chút" là cách một cổng chết dần.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.grounding_gate import (
    ERR_GIA_THIET_LA_DAP_AN,
    ERR_GIA_THIET_SAI_KIEU,
    _KIEU_DUOC_GIA_THIET,
    check_grounding,
)
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS, Obligation
from app.simulation.semantic_program.request_contract import RequestContract


def _spec(*decls: dict) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Kiểm ranh giới giả thiết",
        memory_declarations=[MemoryDeclaration(**d) for d in decls],
        statements=[],
    )


# ══ CA DƯƠNG — đúng hai ca đặc tả nêu ════════════════════════════════════
def test_PASS_point3_co_gia_thiet():
    """"Chọn hệ toạ độ Oxyz" — hợp lệ. Đây là NỬA KHÓ của bài toán sinh ở miền
    hình học: đề không cho toạ độ, mô hình phải tự đặt."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "chọn A làm gốc vì SA vuông góc đáy"}))
    assert kq.ok and kq.assumptions == ["A: chọn A làm gốc vì SA vuông góc đáy"]


def test_FAIL_volume_khai_dap_an():
    """"Thể tích bằng 2/3" — reject. Đúng ca đặc tả nêu."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "V", "type": "float", "initial_value": "2/3",
         "model_assumption": "thể tích khối chóp"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_SAI_KIEU
    assert not kq.assumptions


# ══ MỌI KIỂU NGOÀI point3/vector3 ĐỀU BỊ CHẶN ════════════════════════════
@pytest.mark.parametrize("kieu,gt", [
    ("float", "2/3"), ("int", 5), ("bool", True), ("str", "HỢP LỆ"),
    ("line3", {"through": [[0, 0, 0], [1, 0, 0]]}),
    ("plane3", {"through": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}),
    ("polygon3", [[0, 0, 0], [1, 0, 0], [1, 1, 0]]),
    ("solid", {"vertices": [[0, 0, 0]], "faces": [[0]]}),
    ("array", [1, 2, 3]), ("map", {"a": 1}),
])
def test_chi_point3_va_vector3_duoc_mang_gia_thiet(kieu, gt):
    """Đường thẳng, mặt phẳng, khối phải được DỰNG từ điểm — cho chúng mang giả
    thiết là mở cửa khai thẳng toạ độ kết quả. Vô hướng thì là chỗ đáp án sống."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "x", "type": kieu, "initial_value": gt,
         "model_assumption": "lý do gì đó"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_SAI_KIEU


def test_hai_kieu_duoc_phep_dung_nhu_khai_bao():
    assert _KIEU_DUOC_GIA_THIET == {"point3", "vector3"}


# ══ WITNESS KHÔNG BAO GIỜ LÀ GIẢ THIẾT ═══════════════════════════════════
@pytest.mark.parametrize("kind", sorted(OBLIGATION_KINDS))
def test_witness_cua_MOI_nghia_vu_deu_bi_chan(kind):
    """Quét toàn taxonomy, không chọn vài cái tiêu biểu: thêm một nghĩa vụ mới
    mà quên khoá này thì test tự bắt."""
    hd = RequestContract(obligations=(
        Obligation(kind=kind, container="c", params={"witness": "W"}),
    ))
    kq = check_grounding(hd, _spec(
        {"name": "W", "type": "point3", "initial_value": [1, 2, 3],
         "model_assumption": "kết quả cần tìm"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_LA_DAP_AN


def test_witness_bi_chan_KE_CA_khi_kem_source_fact_id():
    """Lối vòng Wave 3 vừa mở: trích dẫn hỏng nay được hạ cấp. Witness phải bị
    chặn TRƯỚC khi tới nhánh hạ cấp ấy."""
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="k", params={"witness": "V"}),
    ))
    kq = check_grounding(hd, _spec(
        {"name": "V", "type": "point3", "initial_value": [1, 1, 1],
         "source_fact_id": "id_bia_ra", "model_assumption": "đáp số"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_LA_DAP_AN


# ══ LÝ DO BẮT BUỘC ═══════════════════════════════════════════════════════
@pytest.mark.parametrize("ly_do", ["", "   ", "\t\n"])
def test_gia_thiet_phai_co_LY_DO_thuc(ly_do):
    """Không kiểm được nội dung lý do, nhưng bắt viết ra thì biến một lựa chọn
    NGẦM thành một lựa chọn KHAI BÁO — và cái sau đếm được, tra lại được."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": ly_do}))
    assert not kq.ok and not kq.assumptions


# ══ KHÔNG KHAI GÌ ⇒ VẪN CHẶT NHƯ TRƯỚC ═══════════════════════════════════
def test_im_lang_bia_toa_do_van_truot():
    """Kênh giả thiết là OPT-IN. Wave 2 mở một cửa CÓ KHAI BÁO, không tháo cổng
    — và Wave 3 không được đổi điều đó."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "A", "type": "point3", "initial_value": [3, 1, 4]}))
    assert not kq.ok and kq.error_code == "INPUT_NOT_GROUNDED"


def test_point3_co_source_fact_id_ma_KHONG_co_gia_thiet_van_truot():
    """Ca thứ ba của TASK 1 — và là ca dễ tưởng Wave 3 đã nới ra.

    Wave 3 hạ cấp trích dẫn hỏng, nhưng **chỉ khi** khai báo tự đứng vững bằng
    kênh giả thiết. Không có `model_assumption` thì `point3` cũng chết y như một
    `float`: kiểu đúng KHÔNG phải là giấy phép, khai báo mới là.
    """
    kq = check_grounding(RequestContract(), _spec(
        {"name": "P", "type": "point3", "initial_value": [1, 2, 3],
         "source_fact_id": "abc"}))
    assert not kq.ok and kq.error_code == "INPUT_NOT_GROUNDED"
    assert not kq.assumptions and not kq.unresolved_citations


def test_gia_thiet_KHONG_cuu_duoc_gia_tri_ghim_SAI():
    """`source_fact_id` giải được thì đi đường CŨ, nghiêm ngặt. Giả thiết chỉ
    đỡ khi trích dẫn KHÔNG giải được — không phải khi nó giải được mà sai số."""
    from app.simulation.semantic_program.request_contract import InputFact

    hd = RequestContract(input_facts=(
        InputFact(fact_id="sa", label="SA", values=(2,)),
    ))
    kq = check_grounding(hd, _spec(
        {"name": "h", "type": "point3", "initial_value": [0, 0, 99],
         "source_fact_id": "sa", "model_assumption": "chiều cao"}))
    assert not kq.ok, "ghim đúng mục mà khai sai số vẫn phải chết"
