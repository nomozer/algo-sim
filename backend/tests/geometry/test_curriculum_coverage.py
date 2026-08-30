# -*- coding: utf-8 -*-
"""Khoá BẢNG PHỦ CHƯƠNG TRÌNH khỏi trôi. **0 API call.**

`GEOMETRY_CURRICULUM_COVERAGE.md` trả lời câu hội đồng sẽ hỏi — *"hệ làm được
bao nhiêu phần chương trình phổ thông?"* — nên mọi ô **ĐƯỢC/KHÔNG** trong đó
phải là **sự thật máy kiểm được**, không phải một khẳng định viết ra rồi quên.

Một bảng phủ không có test là một bảng phủ sẽ sai sau bản vá thứ ba.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry import GeometryError, Line3, Plane3, Vec3
from app.simulation.geometry import measure as M
from app.simulation.geometry import predicates as P
from app.simulation.semantic_program.geometry_exec import ERR_SAI_LOAI, _do

_DOC = (Path(__file__).resolve().parents[3] / "docs" / "geometry"
        / "GEOMETRY_CURRICULUM_COVERAGE.md")

V = Vec3.of
_MEM = {
    "P": V(0, 0, 3), "Q": V(1, 1, 1),
    "d1": Line3.through(V(0, 0, 0), V(1, 0, 0)),
    "d2": Line3.through(V(0, 1, 5), V(0, 1, 6)),
    "mp": Plane3.through(V(0, 0, 0), V(1, 0, 0), V(0, 1, 0)),
}


class _N:
    def __init__(self, q, o, w):
        self.quantity, self.of, self.wrt = q, o, w


def _dom(q, a, b):
    return _do(_N(q, a, b), _MEM)


# ══ Ô "ĐƯỢC" phải THẬT SỰ đo được ═══════════════════════════════════════
def test_khoang_cach_diem_mat_va_diem_duong_DO_DUOC():
    assert _dom("distance", "P", "mp") == Fraction(3)
    assert _dom("distance", "P", "d1") == Fraction(3)


@pytest.mark.parametrize("a,b", [("d1", "d2"), ("mp", "mp"), ("d1", "mp")])
def test_goc_ba_cap_DO_DUOC(a, b):
    assert isinstance(_dom("angle_cos_sq", a, b), Fraction)


def test_bon_vi_tu_QUAN_HE_deu_co():
    """#2 #3 #4 #7 #8 #9 của bảng — song song và vuông góc, ba cặp mỗi loại."""
    for f in ("parallel_lines", "parallel_planes", "parallel_line_plane",
              "perpendicular_lines", "perpendicular_planes",
              "line_perpendicular_plane", "collinear", "coplanar",
              "point_on_line", "point_on_plane"):
        assert hasattr(P, f), f


def test_the_tich_va_thiet_dien_DO_DUOC():
    from app.simulation.geometry.section import Polyhedron, cross_section

    kh = Polyhedron(
        vertices=(V(0, 0, 0), V(1, 0, 0), V(1, 1, 0), V(0, 1, 0), V(0, 0, 2)),
        faces=((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)))
    from app.simulation.semantic_program.geometry_exec import volume_polyhedron

    assert volume_polyhedron(kh) == Fraction(2, 3)
    mp = Plane3.through(V(0, 0, 1), V(1, 0, 1), V(0, 1, 1))
    assert len(cross_section(kh, mp).polygon) >= 3


# ══ Ô #13 ĐÃ VÁ (2026-08-30) — ba cặp nay ĐO ĐƯỢC ══════════════════════
#
# Bản trước của khối này khẳng định ba cặp KHÔNG đo được, và tự ghi rằng nó sẽ
# "đỏ khi ai đó nối `distance`, và đỏ là tin tốt". Nó đã đỏ đúng như thế. Đây
# là bản thay: cùng ba cặp, nay đòi chúng CHẠY TỚI MỘT CON SỐ.
@pytest.mark.parametrize("a,b,ten", [
    ("d1", "d2", "hai đường chéo nhau"),
    ("d1", "mp", "đường – mặt"),
    ("mp", "mp", "mặt – mặt"),
])
def test_khoang_cach_BA_CAP_NAY_NAY_DO_DUOC(a, b, ten):
    """Không còn `GEOMETRY_OPERAND_TYPE` cho ba cặp này.

    Kết quả có thể vẫn là `GEOMETRY_IRRATIONAL_RESULT` — đó là giới hạn MIỀN
    SỐ, khác hẳn "không có cầu nối", và test dưới tách bạch hai thứ ấy.
    """
    try:
        d = _dom("distance", a, b)
    except GeometryError as e:
        assert e.code == "GEOMETRY_IRRATIONAL_RESULT", (ten, e.code)
        return
    assert d >= 0, ten


def test_ba_cap_KHONG_con_bao_SAI_KIEU():
    """Phân biệt hai lời từ chối rất khác nhau, và đó là điểm của test này.

      `GEOMETRY_OPERAND_TYPE`      — hệ KHÔNG BIẾT đo cặp này. Đã hết.
      `GEOMETRY_IRRATIONAL_RESULT` — hệ đo được, nhưng kết quả không viết được
                                     bằng số hữu tỉ. Vẫn còn, và là giới hạn
                                     ĐÃ KHAI của nền số.
    """
    for a, b in (("d1", "d2"), ("d1", "mp"), ("mp", "mp")):
        try:
            _dom("distance", a, b)
        except GeometryError as e:
            assert e.code != ERR_SAI_LOAI, (a, b, e.code)


def test_kernel_VA_cau_noi_nay_khop_nhau():
    """Trước đây kernel có phép tính mà hợp đồng không nối tới. Nay nối rồi."""
    assert hasattr(M, "distance_sq_skew_lines")
    assert hasattr(M, "distance_sq_parallel_lines")
    assert hasattr(M, "distance_sq_lines")
    assert hasattr(M, "distance_sq_line_plane")
    assert hasattr(M, "distance_sq_planes")
    assert M.distance_sq_skew_lines(_MEM["d1"], _MEM["d2"]) > 0


def test_khoang_cach_VO_TI_bao_loi_thay_vi_lam_tron():
    """Quyết định thiết kế ĐÚNG, và nó có giá: loại mọi đề mà khoảng cách vô
    tỉ. Khai ra ở bảng phủ §3 thay vì giấu."""
    from app.simulation.semantic_program.geometry_exec import ERR_VO_TI

    with pytest.raises(GeometryError) as e:
        _dom("distance", "P", "Q")  # √6
    assert e.value.code == ERR_VO_TI


def test_KHONG_co_mat_cong_va_KHONG_co_phep_chieu_song_song():
    """#5 #19 #20 của bảng. Ranh giới của PHƯƠNG PHÁP, không phải thiếu sót
    cài đặt: kernel dựng trên `Fraction` + đa diện."""
    from app.simulation.geometry import kernel as K

    for chua_co in ("sphere", "cone", "cylinder", "locus",
                    "project_parallel", "oblique_projection"):
        assert not any(chua_co in f for f in dir(K)), chua_co
        assert not any(chua_co in f for f in dir(M)), chua_co


def test_IR_khong_co_phep_toan_VECTO():
    """#6 — `vector3` là một KIỂU, nhưng không có cộng/nhân vô hướng/tích vô
    hướng ở tầng biểu thức."""
    import typing

    from app.simulation.semantic_program.contract import ValueExpr

    tags = {typing.get_args(a)[1].tag
            for a in typing.get_args(typing.get_args(ValueExpr)[0])}
    for chua_co in ("vec_add", "vec_scale", "dot_product", "cross_product"):
        assert chua_co not in tags


# ══ BẢNG không được lệch khỏi mã ════════════════════════════════════════
def test_bang_phu_ton_tai_va_khai_dung_so():
    """Rỗng-là-hỏng: mất file thì mọi assert trên vẫn xanh mà bảng đã biến mất."""
    assert _DOC.exists()
    txt = _DOC.read_text(encoding="utf-8")
    assert "**18**" in txt and "**9**" in txt and "**6**" in txt


def test_bang_phu_KHONG_duoc_doc_thanh_ti_le_de_thi():
    """Khoá lời cảnh báo, không chỉ khoá con số.

    "Phủ 9/18 chủ đề" KHÔNG được đọc thành "làm được 50% đề thi": chưa ai đếm
    mỗi chủ đề chiếm bao nhiêu phần trăm đề thật.
    """
    txt = _DOC.read_text(encoding="utf-8")
    assert "không** được đọc thành" in txt
    assert "phủ **HỢP ĐỒNG**" in txt


def test_tam_nghia_vu_trong_bang_deu_co_that():
    from app.simulation.semantic_program import domain_profile as DP

    txt = _DOC.read_text(encoding="utf-8")
    for k in DP.geometry_obligation_kinds():
        assert f"`{k}`" in txt, f"bảng phủ không nhắc nghĩa vụ {k}"
