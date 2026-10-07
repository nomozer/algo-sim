# -*- coding: utf-8 -*-
"""regular-square-pyramid-w05 — bộ đọc độ dài nguồn đọc CHUỖI BẰNG NHAU (`SA = SB = SC = SD = 3`).

`ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`, tiền đăng ký §4 (hàng `AB = AC = 5`). Một bộ đọc dùng chung cho bằng chứng
GIVEN (`grounding_gate`), bất biến nguồn/chứng chỉ (`bat_bien_do_dai`), nguyên nhân từ chối (`do_dai_trong_de`) và phần
dữ kiện chưa đọc (`shape_constraint.phan_chua_doc`). Route thật: `test_regular_square_pyramid.py` (lớp nhãn W05).
"""
from __future__ import annotations

from fractions import Fraction as F

from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.grounding_gate import _bang_chung_do_dai
from app.simulation.semantic_program.shape_constraint import phan_chua_doc

DE = "Cho hình chóp tứ giác đều S.ABCD có AB = 4, SA = SB = SC = SD = 3. Tính thể tích khối chóp S.ABCD."


def _doan(*ten: str) -> set[frozenset]:
    return {frozenset({t[0], t[1]}) for t in ten}


def test_chuoi_gan_cung_gia_tri_cho_moi_doan():
    dd = SR.do_dai_trong_de(DE)
    assert dd == {frozenset({"A", "B"}): F(4), **{k: F(3) for k in _doan("SA", "SB", "SC", "SD")}}


def test_chuoi_viet_bang_chu_bang():
    dd = SR.do_dai_trong_de("Tam giác ABC có AB bằng AC bằng 5.")
    assert dd == {k: F(5) for k in _doan("AB", "AC")}


def test_chuoi_tron_gia_tri_khac_nhau_giu_mau_thuan():
    """`SA = SB = 3` và `SA = 5` ⇒ SA hai giá trị ⇒ bỏ SA; SB vẫn 3."""
    dd = SR.do_dai_trong_de("Cho chóp S.ABC có SA = SB = 3, SA = 5.")
    assert frozenset({"S", "A"}) not in dd
    assert dd[frozenset({"S", "B"})] == F(3)


def test_chuoi_khong_co_so_khong_gan_gi():
    assert SR.do_dai_trong_de("Cho chóp S.ABCD có AB = 4 và SA = SB = SC = SD.") == {frozenset({"A", "B"}): F(4)}


def test_boi_so_khong_phai_chuoi():
    """`AB = 2AC = 6`: `2AC` là bội, không phải tên đoạn — không đoạn nào được gắn 6 hay 2."""
    assert SR.do_dai_trong_de("Có AB = 2AC = 6.") == {}


def test_cac_doan_truoc_tra_moi_doan_cua_chuoi():
    tien_to = DE[:DE.index("= 3") + 2]
    assert SR.cac_doan_truoc(tien_to) == (("S", "A"), ("S", "B"), ("S", "C"), ("S", "D"))
    assert SR.cac_doan_truoc("Cho hình chóp có cạnh bằng ") == ()
    assert SR.cac_doan_truoc("có AB = ") == (("A", "B"),)


def test_bang_chung_given_cho_moi_thanh_vien_chuoi():
    for ten in ("SA", "SB", "SC", "SD"):
        ma, bc, ly_do = _bang_chung_do_dai(DE, f"{ten}_length", F(3), None)
        assert ma is None, (ten, ma, ly_do)
        assert bc["span_text"] == "3"


def test_bang_chung_doan_ngoai_chuoi_van_mau_thuan():
    ma, _bc, _ = _bang_chung_do_dai(DE, "SO_length", F(3), None)
    assert ma == "SOURCE_EVIDENCE_CONFLICT"
    ma, _bc, _ = _bang_chung_do_dai(DE, "SA_length", F(5), None)
    assert ma is not None


def test_bat_bien_nguon_phat_cho_ca_chuoi():
    bb = {(b.points, b.expected) for b in SR.bat_bien_do_dai(None, DE)}
    assert {(("A", "B"), "4"), (("A", "S"), "3"), (("B", "S"), "3"), (("C", "S"), "3"), (("D", "S"), "3")} <= bb


def test_phan_chua_doc_xoa_ca_chuoi():
    assert phan_chua_doc(DE) == ()
