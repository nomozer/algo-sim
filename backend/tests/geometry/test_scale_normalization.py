# -*- coding: utf-8 -*-
"""SCALE NORMALIZATION — tám ca A–H của chỉ thị, tất định, **0 API call**.

Bài kiểm ở đây trả lời đúng một câu: *một ký hiệu tỉ lệ tự do của đề có được
buộc về `1` không, và khi nào thì KHÔNG*.

Bốn ca đầu (A–D) là chỗ cơ chế phải chạy. Bốn ca sau (E–H) là chỗ nó phải
NGẬM MIỆNG, và chúng mới là phần đắt: một phép chuẩn hoá quá hăng sẽ viết lại
cả đề `AB = 5`, hoặc xoá mất chính ẩn số mà đề hỏi, hoặc tự kết luận `a = b`.
Mỗi ca âm ở đây là một cách hệ có thể nói dối mà vẫn xanh.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
)
from app.simulation.semantic_program.request_contract import InputFact, RequestContract
from app.simulation.semantic_program.scale_normalization import (
    bang_huu_ti,
    chuan_hoa_thang,
    tim_thang,
)


def _hd(*facts: tuple[str, str], obligations=()) -> RequestContract:
    return RequestContract(
        obligations=tuple(obligations),
        input_facts=tuple(
            InputFact(fact_id=fid, label=fid, values=(gt,)) for fid, gt in facts
        ),
    )


def _gia_tri(hd: RequestContract, fid: str):
    return next(f for f in hd.input_facts if f.fact_id == fid).values


# ── A · một ký hiệu trần ─────────────────────────────────────────────────────
def test_A_AB_bang_a_thanh_1():
    hd = chuan_hoa_thang(_hd(("ab", "a")), "Cho hình chóp S.ABC có AB = a.")
    assert hd.scale_binding is not None
    assert hd.scale_binding.symbol == "a"
    assert hd.scale_binding.canonical_value == "1"
    assert _gia_tri(hd, "ab") == (1,)


# ── B · ký hiệu trần + phân số ───────────────────────────────────────────────
def test_B_giu_dung_phan_so_3_tren_5():
    hd = chuan_hoa_thang(
        _hd(("ab", "a"), ("sa", "3a/5")), "… AB = a, SA = 3a/5 …")
    assert _gia_tri(hd, "ab") == (1,)
    assert _gia_tri(hd, "sa") == ("3/5",)


# ── C · hệ số ở cả hai mục ───────────────────────────────────────────────────
def test_C_he_so_2a_va_3a_tren_5():
    hd = chuan_hoa_thang(
        _hd(("ab", "2a"), ("sa", "3a/5")), "… AB = 2a, SA = 3a/5 …")
    assert _gia_tri(hd, "ab") == (2,)
    assert _gia_tri(hd, "sa") == ("3/5",)


# ── D · nhiều mục dùng chung `a` ⇒ ĐÚNG MỘT phép buộc ────────────────────────
def test_D_nhieu_muc_chung_mot_ky_hieu_chi_mot_binding():
    hd = chuan_hoa_thang(
        _hd(("ab", "a"), ("bc", "2a"), ("sa", "3a/5")),
        "… AB = a, BC = 2a, SA = 3a/5 …")
    b = hd.scale_binding
    assert b is not None and b.symbol == "a"
    assert set(b.fact_ids) == {"ab", "bc", "sa"}
    assert {f.scale_symbol for f in hd.input_facts} == {"a"}


# ── E · đề cho SỐ ⇒ không có thang tự do nào ────────────────────────────────
def test_E_so_cu_the_khong_sinh_binding():
    hd = chuan_hoa_thang(_hd(("ab", "5")), "Cho hình lập phương cạnh AB = 5.")
    assert hd.scale_binding is None
    assert _gia_tri(hd, "ab") == ("5",)   # nguyên vẹn, không ai chạm vào


# ── F · ký hiệu CHÍNH LÀ ẩn số ⇒ không được buộc về 1 ───────────────────────
def test_F_ky_hieu_la_an_so_thi_khong_chuan_hoa():
    hd = chuan_hoa_thang(_hd(("ab", "a")), "Cho AB = a. Tìm a biết thể tích 6.")
    assert hd.scale_binding is None
    assert _gia_tri(hd, "ab") == ("a",)


def test_F2_ky_hieu_la_witness_cua_nghia_vu_thi_khong_chuan_hoa():
    from app.simulation.semantic_program.obligations import Obligation

    hd = chuan_hoa_thang(
        _hd(("ab", "a"), obligations=(
            Obligation(kind="distance", container="ABC", params={"witness": "a"}),
        )),
        "Cho AB = a. Tính khoảng cách từ S đến (ABC).")
    assert hd.scale_binding is None


# ── G · hai đại lượng ký hiệu ĐỘC LẬP ⇒ không tự kết luận cùng thang ────────
def test_G_hai_ky_hieu_doc_lap_thi_khong_chuan_hoa():
    hd = chuan_hoa_thang(
        _hd(("ab", "a"), ("sa", "b")), "… AB = a, SA = b …")
    assert hd.scale_binding is None
    assert _gia_tri(hd, "ab") == ("a",)
    assert _gia_tri(hd, "sa") == ("b",)


# ── H · biểu thức hỏng / nhập nhằng ⇒ FAIL CLOSED ───────────────────────────
@pytest.mark.parametrize("xau", ["a√2", "a^2", "3/2a"])
def test_H_bieu_thuc_khong_phan_tich_duoc_thi_fail_closed(xau: str):
    hd = chuan_hoa_thang(_hd(("ab", "a"), ("sa", xau)), f"… AB = a, SA = {xau} …")
    assert hd.scale_binding is None, f"{xau!r} phải làm cả phép chuẩn hoá dừng"
    assert _gia_tri(hd, "ab") == ("a",)


def test_H2_de_gan_so_cho_ky_hieu_thi_no_khong_tu_do():
    hd = chuan_hoa_thang(_hd(("ab", "a")), "Cho AB = a với a = 5.")
    assert hd.scale_binding is None


# ── Ranh giới: không chạm miền Tin học, không chạm văn xuôi ─────────────────
def test_van_xuoi_khong_bao_gio_bi_viet_lai():
    hd = chuan_hoa_thang(
        _hd(("ab", "a"), ("tc", "tam giác SAB vuông tại S")),
        "… tam giác SAB vuông tại S, AB = a …")
    assert hd.scale_binding is not None
    assert _gia_tri(hd, "tc") == ("tam giác SAB vuông tại S",)


def test_mien_tin_hoc_KHONG_bi_chuan_hoa_thang():
    """`'a'` ở Tin học là DỮ LIỆU, không phải tham số tỉ lệ."""
    payload = {"input_facts": [{"id": "chuoi", "label": "Chuỗi", "value": "a"}]}
    hd = build_request_contract(
        payload, problem_text="Đếm số lần ký tự a xuất hiện.",
        domain=DOMAIN_TIN_HOC)
    assert hd.scale_binding is None
    assert _gia_tri(hd, "chuoi") == ("a",)


def test_build_request_contract_hinh_hoc_co_chuan_hoa():
    payload = {"input_facts": [
        {"id": "ab_length", "label": "Độ dài AB", "value": "a"},
        {"id": "sa_length", "label": "Độ dài SA", "value": "4a/5"},
    ]}
    hd = build_request_contract(
        payload,
        problem_text=("Cho hình chóp S.ABC có AB = a, SA = 4a/5. Tính khoảng "
                      "cách từ S đến mặt phẳng (ABC)."),
        domain=DOMAIN_HINH_HOC)
    assert hd.scale_binding is not None
    assert _gia_tri(hd, "ab_length") == (1,)
    assert _gia_tri(hd, "sa_length") == ("4/5",)


# ── XUẤT XỨ — ba chặng phải đọc ngược được ─────────────────────────────────
def test_giu_nguyen_fact_id_va_nguyen_van():
    hd = chuan_hoa_thang(_hd(("sa_length", "4a/5")), "… SA = 4a/5 …")
    f = next(f for f in hd.input_facts if f.fact_id == "sa_length")
    assert f.fact_id == "sa_length"          # ghim của IR không được đổi
    assert f.original_values == ("4a/5",)    # nguyên văn còn nguyên
    assert f.scale_symbol == "a"             # buộc bởi ký hiệu nào
    assert hd.scale_binding.rewrites == (("sa_length", "4a/5", "4/5"),)


def test_KHONG_dung_float_khi_phan_so_dien_dat_duoc():
    """`4/5` phải ở lại là `4/5`. `0.8` là mất chính xác ngay tại biên."""
    hd = chuan_hoa_thang(_hd(("sa", "4a/5")), "… SA = 4a/5 …")
    (v,) = _gia_tri(hd, "sa")
    assert v == "4/5" and not isinstance(v, float)


def test_tim_thang_khong_co_de_thi_tra_None():
    """Đường gọi cũ (không truyền `problem_text`) giữ nguyên hành vi."""
    assert tim_thang(_hd(("ab", "a")), None) is None
    assert tim_thang(_hd(("ab", "a")), "") is None


# ── Phép so hữu tỉ — cầu nối giữa hợp đồng chính xác và IR chỉ có float ─────
@pytest.mark.parametrize("a,b", [("4/5", 0.8), (0.8, "4/5"), (1, 1.0),
                                 ("3/5", 0.6), ("-1/2", -0.5)])
def test_bang_huu_ti_khop_hai_cach_viet(a, b):
    assert bang_huu_ti(a, b)


@pytest.mark.parametrize("a,b", [("4/5", 0.7), ("4/5", "abc"), (True, 1),
                                 (None, 1), ("x", "x")])
def test_bang_huu_ti_khong_khop_bua(a, b):
    assert not bang_huu_ti(a, b)
