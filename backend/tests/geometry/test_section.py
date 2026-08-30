# -*- coding: utf-8 -*-
"""Dựng thiết diện — đáp án KIỂM TAY. **0 API call.**

Mọi đáp án dưới đây tính được bằng đầu và **không chép từ đầu ra của kernel**.
Lấy kernel làm `EXPECTED` thì test thành tautology — bẫy đã gặp một lần ở
`cross_domain_matrix`.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry import GeometryError, Plane3, Vec3
from app.simulation.geometry import measure as M
from app.simulation.geometry import predicates as P
from app.simulation.geometry.section import box, cross_section, pyramid_square

HOP = box(1, 1, 1)
CHOP = pyramid_square(1, 2)


def _tap(pts) -> set[tuple]:
    return {(p.x, p.y, p.z) for p in pts}


# ── 1. Hộp cắt ngang ──────────────────────────────────────────────────────
def test_hop_cat_boi_z_bang_mot_nua_ra_HINH_VUONG():
    """Kiểm tay: mặt `z = 1/2` cắt hình lập phương đơn vị theo hình vuông
    `(0,0,½) (1,0,½) (1,1,½) (0,1,½)`."""
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = cross_section(HOP, mp)
    assert len(s.polygon) == 4
    assert _tap(s.polygon) == {
        (F(0), F(0), F(1, 2)), (F(1), F(0), F(1, 2)),
        (F(1), F(1), F(1, 2)), (F(0), F(1), F(1, 2)),
    }


def test_moi_dinh_thiet_dien_THUOC_mat_phang_cat():
    """Bất biến phải đúng với MỌI thiết diện — kiểm được mà không cần đáp án."""
    mp = Plane3.through(Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1))
    for p in cross_section(HOP, mp).polygon:
        assert P.point_on_plane(p, mp)


def test_thiet_dien_la_da_giac_KIN():
    mp = Plane3(Vec3.of(0, 0, F(1, 3)), Vec3.of(0, 0, 1))
    s = cross_section(HOP, mp)
    assert s.is_closed
    assert len(s.steps) == len(s.polygon), "mỗi bước dựng đúng một cạnh"


def test_cat_qua_ba_dinh_ra_TAM_GIAC_DEU():
    """Mặt `x+y+z=1` cắt lập phương qua ba đỉnh kề gốc.
    Kiểm tay: ba đỉnh `(1,0,0) (0,1,0) (0,0,1)`, ba cạnh đều dài `√2` ⇒ `d²=2`."""
    mp = Plane3.through(Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1))
    s = cross_section(HOP, mp)
    assert len(s.polygon) == 3
    canh = [M.distance_sq(s.polygon[i], s.polygon[(i + 1) % 3]) for i in range(3)]
    assert canh == [2, 2, 2]


# ── 2. Chóp — cấu hình Toán 11 ────────────────────────────────────────────
def test_chop_cat_ngang_ra_TU_GIAC():
    """`z = 1` cắt chóp cao 2. Kiểm tay: ở nửa chiều cao, thiết diện là hình
    vuông đồng dạng đáy với tỉ số 1/2 ⇒ cạnh `1/2`."""
    mp = Plane3(Vec3.of(0, 0, 1), Vec3.of(0, 0, 1))
    s = cross_section(CHOP, mp)
    assert len(s.polygon) == 4
    canh = [M.distance_sq(s.polygon[i], s.polygon[(i + 1) % 4]) for i in range(4)]
    assert all(c == F(1, 4) for c in canh), "cạnh 1/2 ⇒ d² = 1/4"


def test_thiet_dien_chop_song_song_day_thi_SONG_SONG_day():
    mp = Plane3(Vec3.of(0, 0, 1), Vec3.of(0, 0, 1))
    s = cross_section(CHOP, mp)
    day = Plane3.through(CHOP.vertices[0], CHOP.vertices[1], CHOP.vertices[2])
    mp_td = Plane3.through(*s.polygon[:3])
    assert P.parallel_planes(mp_td, day)


# ── 3. Bước dựng — nguyên liệu của timeline ───────────────────────────────
def test_moi_buoc_gan_voi_MOT_MAT_cua_khoi():
    """Lời kể *'trên mặt (SBC), nối M với N'* chỉ nói được khi biết mặt nào."""
    mp = Plane3(Vec3.of(0, 0, 1), Vec3.of(0, 0, 1))
    s = cross_section(CHOP, mp)
    assert len({st.face_index for st in s.steps}) == len(s.steps), \
        "hai bước không được đến từ cùng một mặt"
    for st in s.steps:
        assert 0 <= st.face_index < len(CHOP.faces)


def test_cac_buoc_noi_TIEP_NHAU_thanh_vong():
    mp = Plane3.through(Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1))
    s = cross_section(HOP, mp)
    for i in range(len(s.steps)):
        assert s.steps[i].b == s.steps[(i + 1) % len(s.steps)].a, \
            "cạnh sau phải bắt đầu ở chỗ cạnh trước kết thúc"


# ── 4. FAIL-CLOSED ────────────────────────────────────────────────────────
def test_mat_phang_NGOAI_khoi_thi_NEM_khong_tra_da_giac_rong():
    """Đa giác rỗng đi tiếp tới renderer thành một cảnh trống mà không ai nói
    là đang trống — đúng lỗi đã sinh ra bất biến #31."""
    mp = Plane3(Vec3.of(0, 0, 5), Vec3.of(0, 0, 1))
    with pytest.raises(GeometryError) as e:
        cross_section(HOP, mp)
    assert e.value.code == "PLANE_DOES_NOT_CUT"
    assert "một phía" in str(e.value)


def test_chi_CHAM_mot_dinh_thi_NEM():
    """Mặt `z = 2` chạm đúng đỉnh `S` của chóp — chạm không phải cắt.

    Mã RIÊNG, không gộp vào `PLANE_DOES_NOT_CUT` (đổi 2026-08-30). Bản cũ gộp
    hai ca vào một mã VÀ một câu — *"toàn bộ khối nằm về một phía"* — mà câu ấy
    SAI ở đây: khối có đúng một điểm nằm TRÊN mặt phẳng. Kernel phân biệt được,
    nên gộp là vứt đi thông tin đã có.
    """
    mp = Plane3(Vec3.of(0, 0, 2), Vec3.of(0, 0, 1))
    with pytest.raises(GeometryError) as e:
        cross_section(CHOP, mp)
    assert e.value.code == "PLANE_TOUCHES_VERTEX"
    assert "một đỉnh" in str(e.value)


def test_mat_phang_CHUA_mot_mat_cua_khoi_thi_ma_rieng():
    """`z = 0` chứa trọn đáy — thiết diện suy biến, phải nói khác 'không cắt'."""
    mp = Plane3(Vec3.of(0, 0, 0), Vec3.of(0, 0, 1))
    with pytest.raises(GeometryError) as e:
        cross_section(CHOP, mp)
    assert e.value.code == "CONTAINED_INFINITE_INTERSECTION"


def test_khoi_khai_hong_thi_NEM_ngay_luc_dung():
    from app.simulation.geometry.section import Polyhedron

    with pytest.raises(GeometryError) as e:
        Polyhedron(vertices=tuple(Vec3.of(i, 0, 0) for i in range(4)),
                   faces=((0, 1, 99),))
    assert e.value.code == "MALFORMED_SOLID"


def test_mat_it_hon_ba_dinh_thi_NEM():
    from app.simulation.geometry.section import Polyhedron

    with pytest.raises(GeometryError):
        Polyhedron(vertices=tuple(Vec3.of(i, 0, 0) for i in range(4)),
                   faces=((0, 1),))


# ── 5. TẤT ĐỊNH ───────────────────────────────────────────────────────────
def test_cung_input_cho_cung_thiet_dien():
    mp = Plane3.through(Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1))
    a = cross_section(HOP, mp)
    b = cross_section(HOP, mp)
    assert a.polygon == b.polygon
    assert [s.face_index for s in a.steps] == [s.face_index for s in b.steps]


def test_toa_do_thiet_dien_la_HUU_TI_chinh_xac():
    """Mặt cắt ở `z = 1/3` — mẫu số 3, float không biểu diễn đúng được."""
    mp = Plane3(Vec3.of(0, 0, F(1, 3)), Vec3.of(0, 0, 1))
    for p in cross_section(HOP, mp).polygon:
        assert p.z == F(1, 3)
