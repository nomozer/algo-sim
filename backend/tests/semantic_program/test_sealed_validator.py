# -*- coding: utf-8 -*-
"""Bộ kiểm hình dạng SEALED phải bắt được đúng những lỗi làm hỏng lượt chạy.

Nó là lớp chắn duy nhất giữa "custodian gõ nhầm một trường" và "mất lượt live
duy nhất". Một validator chưa từng đỏ là một validator chưa được chứng minh, nên
mỗi lỗi nó phải bắt đều có một case giả ở đây.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

VALIDATOR = (Path(__file__).resolve().parents[2] / "scripts"
             / "validate_sealed_submission.py")


@pytest.fixture(scope="module")
def vd():
    spec = importlib.util.spec_from_file_location("validate_sealed_submission",
                                                  VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _case(**ghi_de):
    c = {
        "case_id": "sealed_001",
        "source": {"book": "tin-hoc-11.pdf", "location": "trang 62"},
        "problem_text": "Tìm giá trị lớn nhất trong dãy 12 45 67",
        "eligibility_audit": {"discrete": True, "finite_input": True,
                              "deterministic_bounded_procedure": True,
                              "in_scope": True},
        "metadata": {"no_specialized_module": True, "no_target_template": True,
                     "not_prompt_example": True, "expressible_in_ir": True},
        "prescribed_procedure": None,
        "ground_truth": {"kind": "human", "provenance": "giáo viên giải tay",
                         "expected": [{"obligation_kind": "extremum", "value": 67}]},
    }
    c.update(ghi_de)
    return c


def _bo(*cases):
    return {"cases": list(cases)}


def test_tap_hop_le_thi_khong_co_loi(vd):
    loi, _ = vd.kiem(_bo(_case()))
    assert loi == [], loi


def test_thieu_problem_text_la_loi(vd):
    loi, _ = vd.kiem(_bo(_case(problem_text="   ")))
    assert any("problem_text" in x for x in loi)


def test_case_id_trung_bi_bat(vd):
    """Trùng id ⇒ báo cáo lẫn hai case làm một mà không ai nhận ra."""
    loi, _ = vd.kiem(_bo(_case(), _case()))
    assert any("TRÙNG" in x for x in loi)


def test_thieu_metadata_guard_la_loi(vd):
    md = {"no_specialized_module": True, "not_prompt_example": True,
          "expressible_in_ir": True}
    loi, _ = vd.kiem(_bo(_case(metadata=md)))
    assert any("no_target_template" in x for x in loi)


def test_metadata_guard_false_la_loi(vd):
    """Guard false ⇒ case ấy phá tính held-out của cả tập."""
    md = {"no_specialized_module": False, "no_target_template": True,
          "not_prompt_example": True, "expressible_in_ir": True}
    loi, _ = vd.kiem(_bo(_case(metadata=md)))
    assert any("held-out" in x for x in loi)


# ── `expressible_in_ir` KHÔNG được là điều kiện loại case ────────
def test_expressible_in_ir_FALSE_khong_phai_loi(vd):
    """Sửa 2026-08-22, TRƯỚC khi giao custodian.

    Bắt `expressible_in_ir=true` là dùng NĂNG LỰC HIỆN TẠI CỦA IR làm bộ lọc
    population — tức loại trước đúng những bài đáng lẽ phải ở lại để thành
    `capability_gap` trung thực, và làm tỉ lệ A cao lên một cách giả tạo.
    Rubric §7.2 vốn đã nói ngược lại.
    """
    md = {"no_specialized_module": True, "no_target_template": True,
          "not_prompt_example": True, "expressible_in_ir": False}
    loi, cb = vd.kiem(_bo(_case(metadata=md)))
    assert loi == [], f"case dự kiến capability_gap bị loại khỏi tập: {loi}"
    assert any("VẪN Ở LẠI" in x for x in cb), cb


def test_thieu_han_expressible_in_ir_cung_khong_phai_loi(vd):
    """Nó là MÔ TẢ, không phải guard — vắng mặt không chặn được gì."""
    md = {"no_specialized_module": True, "no_target_template": True,
          "not_prompt_example": True}
    loi, _ = vd.kiem(_bo(_case(metadata=md)))
    assert loi == [], loi


def test_guard_cung_dung_BA_cai_va_khong_cai_nao_ve_nang_luc_IR(vd):
    assert vd.METADATA_GUARDS == (
        "no_specialized_module", "no_target_template", "not_prompt_example",
    ), (
        "Guard cứng chỉ được nói về NHIỄM DỮ LIỆU. Thêm điều kiện về năng lực "
        "hệ vào đây là tự chọn population có lợi cho mình."
    )
    assert "expressible_in_ir" in vd.METADATA_MO_TA


def test_in_scope_false_khong_duoc_nam_trong_tap(vd):
    el = {"discrete": True, "finite_input": True,
          "deterministic_bounded_procedure": True, "in_scope": False}
    loi, _ = vd.kiem(_bo(_case(eligibility_audit=el)))
    assert any("ngoài phạm vi" in x for x in loi)


def test_thieu_eligibility_audit_la_loi(vd):
    c = _case()
    del c["eligibility_audit"]
    loi, _ = vd.kiem(_bo(c))
    assert any("chưa ai audit" in x for x in loi)


def test_expected_dang_ANH_XA_TEN_BIEN_bi_tu_choi(vd):
    """Dạng cũ `{ten_bien: gia_tri}` phải bị chặn Ở ĐÂY, không phải lúc chạy."""
    gt = {"kind": "human", "provenance": "x", "expected": {"max_val": 67}}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert any("TÊN BIẾN" in x for x in loi)


def test_obligation_kind_ngoai_taxonomy_bi_bat(vd):
    gt = {"kind": "human", "provenance": "x",
          "expected": [{"obligation_kind": "tim_so_lon_nhat", "value": 67}]}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert any("ngoài taxonomy" in x for x in loi)


def test_thieu_value_bi_bat(vd):
    gt = {"kind": "human", "provenance": "x",
          "expected": [{"obligation_kind": "extremum"}]}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert any("thiếu `value`" in x for x in loi)


def test_nhieu_nghia_vu_cung_loai_ma_thieu_index_bi_bat(vd):
    gt = {"kind": "human", "provenance": "x", "expected": [
        {"obligation_kind": "extremum", "value": 1},
        {"obligation_kind": "extremum", "value": 2},
    ]}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert any("thiếu `index`" in x for x in loi)


def test_co_index_thi_khong_bao_loi(vd):
    gt = {"kind": "human", "provenance": "x", "expected": [
        {"obligation_kind": "extremum", "index": 0, "value": 1},
        {"obligation_kind": "extremum", "index": 1, "value": 2},
    ]}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert loi == [], loi


def test_prescribed_procedure_ngoai_tap_dong_bi_bat(vd):
    loi, _ = vd.kiem(_bo(_case(prescribed_procedure="sap_xep_kieu_gi_do")))
    assert any("ngoài tập đóng" in x for x in loi)


def test_khong_case_nao_cham_duoc_la_LOI_chu_khong_phai_canh_bao(vd):
    """Cả tập không có oracle độc lập ⇒ báo cáo chỉ còn phán quyết nội bộ."""
    gt = {"kind": "human", "provenance": "x", "expected": []}
    loi, _ = vd.kiem(_bo(_case(ground_truth=gt)))
    assert any("KHÔNG case nào chấm được" in x for x in loi)


def test_thieu_case_so_voi_N_planned_la_canh_bao(vd):
    _, cb = vd.kiem(_bo(_case()))
    assert any("N_planned" in x for x in cb)


def test_du_40_case_thi_khong_canh_bao_so_luong(vd):
    cases = [_case(case_id=f"sealed_{i:03d}") for i in range(40)]
    loi, cb = vd.kiem(_bo(*cases))
    assert loi == [], loi
    assert not any("N_planned" in x for x in cb)


def test_thong_bao_kem_VI_TRI_de_dinh_vi_duoc(vd):
    """Phát hiện khi chạy thử chính CLI: với file 40 case mà `case_id` trùng
    hoặc bỏ trống, chỉ in id thì người sửa không biết dòng nào."""
    loi, _ = vd.kiem(_bo(_case(), _case()))
    assert any(x.startswith("[#1 ") for x in loi), loi

    c = _case()
    del c["case_id"]
    loi2, _ = vd.kiem(_bo(c))
    assert any("#0" in x and "thiếu case_id" in x for x in loi2), loi2


def test_validator_KHONG_tu_nhan_la_bo_cham(vd):
    """Nó chỉ trả lời 'runner đọc được không'. Tự nhận nhiều hơn là nguy hiểm:
    ground truth mà máy kiểm được thì không còn độc lập."""
    src = VALIDATOR.read_text(encoding="utf-8")
    assert "KHÔNG PHẢI, và không được dùng như, một bộ chấm" in src
