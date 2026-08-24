# -*- coding: utf-8 -*-
"""Geometry kernel — chính xác, tất định, fail-closed. **0 API call.**

ĐÁP ÁN KIỂM TAY, KHÔNG chép từ đầu ra của kernel. Lấy kết quả kernel làm
`EXPECTED` thì test thành tautology — bẫy đã gặp một lần ở
`cross_domain_matrix` và được ghi lại trong `CODE_INDEX`.

Hình dùng xuyên suốt: chóp `S.ABCD`, đáy vuông cạnh 1 trong mặt `z = 0`,
`S(0,0,2)` — cấu hình kinh điển của Toán 11, và mọi đáp án dưới đây tính được
bằng đầu.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry import GeometryError, Line3, Plane3, Vec3
from app.simulation.geometry import kernel as K
from app.simulation.geometry import measure as M
from app.simulation.geometry import predicates as P

A = Vec3.of(0, 0, 0)
B = Vec3.of(1, 0, 0)
C = Vec3.of(1, 1, 0)
D = Vec3.of(0, 1, 0)
S = Vec3.of(0, 0, 2)
DAY = Plane3.through(A, B, C)          # mặt phẳng z = 0


# ── 1. Số học CHÍNH XÁC, không sai số tích luỹ ────────────────────────────
def test_toa_do_la_HUU_TI_khong_phai_float():
    p = K.divide_segment(A, B, F(1, 3))
    assert p.x == F(1, 3), "toạ độ phải chính xác, không phải 0.333…"
    assert isinstance(p.x, F)


def test_chia_ba_roi_nhan_ba_ve_DUNG_diem_dau():
    """Trên float, `(1/3)*3 != 1` ở nhiều trường hợp. Trên ℚ thì luôn đúng."""
    p = K.divide_segment(A, B, F(1, 3))
    assert (p - A).scale(3) == (B - A)


def test_float_dau_vao_duoc_chuyen_CHINH_XAC():
    assert Vec3.of(0.5, 0.25, 0).x == F(1, 2)


def test_bool_bi_chan_tuong_minh():
    """`True` là subclass của `int` — không chặn thì nó thành toạ độ 1."""
    with pytest.raises(GeometryError):
        Vec3.of(True, 0, 0)


# ── 1b. Ca mà FLOAT TRẢ LỜI SAI, ℚ trả lời đúng ───────────────────────────
#
# Ba test dưới đây tồn tại vì một phép tiêm lỗi đã phơi ra rằng phần còn lại
# của file này KHÔNG nhạy với việc mất tính chính xác: thay `Fraction` bằng
# `float` chỉ làm 2/37 test đỏ, và cả hai chỉ kiểm KIỂU chứ không kiểm HỆ QUẢ.
# Lý do: mọi toạ độ dùng ở trên (0, 1, 2, 1/2) đều biểu diễn ĐÚNG được bằng
# float, nên chúng không phân biệt được gì.
#
# Muốn chứng minh số học chính xác đáng giá thì phải chọn giá trị mà float
# THẬT SỰ sai — mẫu số không phải luỹ thừa của 2.

_MP_XIEN = Plane3.through(Vec3.of(0, 0, 0), Vec3.of(1, 0, 3), Vec3.of(0, 1, 7))


def test_diem_thuoc_mat_phang_XIEN_voi_toa_do_mau_3_va_7():
    """Kiểm tay: pháp tuyến `(1,0,3)×(0,1,7) = (−3,−7,1)`.
    Với `P(1/3, 1/7, 2)`: `−3·(1/3) − 7·(1/7) + 1·2 = −1 − 1 + 2 = 0` ⇒ P thuộc.

    Trên float, `1/3` và `1/7` đều KHÔNG biểu diễn đúng được, nên tổng ra
    khoảng `1e−16` chứ không phải `0` — và phép kiểm `== 0` trả SAI.
    """
    assert P.point_on_plane(Vec3.of(F(1, 3), F(1, 7), 2), _MP_XIEN)


def test_dong_phang_o_ca_ma_FLOAT_TRA_LOI_SAI():
    """Bốn điểm `O`, `u`, `v`, `u+v` — đồng phẳng **theo định nghĩa**, mọi lúc.

    Giá trị mẫu số `(3,7,11,13)` chọn bằng cách **dò số**, không chọn cho đẹp:
    trên float, `det` ra `1.084e−19` chứ không phải `0`, nên `== 0` trả SAI.
    Trên ℚ nó đúng bằng `0`.

    Đây là bằng chứng số học chính xác **đáng giá**, không phải một lựa chọn
    phong cách. Ba test cạnh đây (mẫu 3, 7) hoá ra float vẫn trả đúng vì
    `3·(1/3)` tình cờ tròn lại thành `1.0` — phép tiêm lỗi đã phơi ra điều đó,
    và đó là lý do ca này tồn tại.
    """
    u = Vec3.of(F(1, 3), F(1, 7), F(1, 11))
    v = Vec3.of(F(1, 7), F(1, 11), F(1, 13))
    assert P.coplanar(Vec3.of(0, 0, 0), u, v, u + v)


def test_the_tich_voi_toa_do_mau_3_van_CHINH_XAC():
    """Kiểm tay: `det((1/3,0,0), (0,1/3,0), (0,0,1/3)) = 1/27` ⇒ `V = 1/162`.

    Float cho `1/27 ≈ 0.037037…` rồi chia 6 — sai số nhỏ nhưng KHÔNG bằng
    `Fraction(1, 162)`, nên so sánh chính xác sẽ đỏ.
    """
    v = M.volume_tetrahedron(
        Vec3.of(0, 0, 0),
        Vec3.of(F(1, 3), 0, 0),
        Vec3.of(0, F(1, 3), 0),
        Vec3.of(0, 0, F(1, 3)),
    )
    assert v == F(1, 162)


# ── 2. Vị từ — KHÔNG epsilon ──────────────────────────────────────────────
def test_SA_vuong_goc_day():
    """`SA ⊥ (ABCD)`: phương `SA` cùng phương pháp tuyến đáy. Kiểm tay: đáy nằm
    trong `z=0`, `SA` dọc trục `z` ⇒ đúng."""
    assert P.line_perpendicular_plane(Line3.through(S, A), DAY)


def test_AB_KHONG_vuong_goc_day():
    """Bẫy trực giác: `AB` nằm TRONG đáy nên `AB·n = 0`, nhưng nó KHÔNG vuông
    góc với đáy. Viết ngược điều kiện là test này đỏ."""
    assert not P.line_perpendicular_plane(Line3.through(A, B), DAY)
    assert P.line_in_plane(Line3.through(A, B), DAY)


def test_AB_vuong_goc_AD():
    assert P.perpendicular_lines(Line3.through(A, B), Line3.through(A, D))


def test_AB_song_song_DC():
    assert P.parallel_lines(Line3.through(A, B), Line3.through(D, C))


def test_SA_va_BC_CHEO_NHAU():
    """Quan hệ mà hình biểu diễn phẳng nói dối rõ nhất."""
    assert P.skew_lines(Line3.through(S, A), Line3.through(B, C))


def test_hai_duong_cat_nhau_thi_KHONG_cheo():
    assert not P.skew_lines(Line3.through(A, B), Line3.through(A, D))


def test_bon_dinh_day_dong_phang():
    assert P.coplanar(A, B, C, D)
    assert not P.coplanar(A, B, C, S)


# ── 3. Phép dựng — đáp án kiểm tay ────────────────────────────────────────
def test_giao_diem_duong_mat():
    """`SB` cắt `z=0` tại `B`. Kiểm tay: `S(0,0,2)`, `B(1,0,0)`, đáy `z=0`."""
    assert K.intersect_line_plane(Line3.through(S, B), DAY) == B


def test_giao_tuyen_hai_mat_phang():
    """`(SAB)` ∩ `(ABCD)` = đường `AB`. Kiểm tay: cả hai chứa `A` và `B`."""
    g = K.intersect_plane_plane(Plane3.through(S, A, B), DAY)
    assert P.point_on_line(A, g) and P.point_on_line(B, g)
    assert P.parallel_vectors(g.direction, B - A)


def test_trung_diem():
    assert K.midpoint(A, C) == Vec3.of(F(1, 2), F(1, 2), 0)


def test_hinh_chieu_S_xuong_day_la_A():
    """Chân đường cao — chỗ hình vẽ tay hay đặt sai nhất."""
    assert K.project_point_onto_plane(S, DAY) == A


def test_hinh_chieu_diem_len_duong():
    """Chiếu `C(1,1,0)` lên `AB` (trục x) ⇒ `(1,0,0)`. Kiểm tay."""
    assert K.project_point_onto_line(C, Line3.through(A, B)) == B


def test_giao_hai_duong_thang():
    """`AC` ∩ `BD` = tâm đáy `(1/2, 1/2, 0)`. Kiểm tay: hai đường chéo hình
    vuông cắt nhau tại tâm."""
    assert K.intersect_line_line(Line3.through(A, C),
                                 Line3.through(B, D)) == Vec3.of(F(1, 2), F(1, 2), 0)


# ── 4. FAIL-CLOSED — mỗi tình huống một MÃ RIÊNG ──────────────────────────
def test_hai_mat_song_song_thi_NEM_khong_tra_None():
    tren = Plane3.through(Vec3.of(0, 0, 1), Vec3.of(1, 0, 1), Vec3.of(0, 1, 1))
    with pytest.raises(GeometryError) as e:
        K.intersect_plane_plane(DAY, tren)
    assert e.value.code == "PARALLEL_NO_INTERSECTION"


def test_hai_mat_TRUNG_nhau_co_ma_KHAC_song_song():
    """Trùng và song song dạy hai điều khác nhau — gộp mã là mất một kết luận."""
    with pytest.raises(GeometryError) as e:
        K.intersect_plane_plane(DAY, Plane3.through(A, B, D))
    assert e.value.code == "CONTAINED_INFINITE_INTERSECTION"


def test_duong_NAM_TRONG_mat_thi_ma_rieng():
    with pytest.raises(GeometryError) as e:
        K.intersect_line_plane(Line3.through(A, B), DAY)
    assert e.value.code == "CONTAINED_INFINITE_INTERSECTION"


def test_duong_song_song_mat_thi_ma_song_song():
    ln = Line3(Vec3.of(0, 0, 1), Vec3.of(1, 0, 0))
    with pytest.raises(GeometryError) as e:
        K.intersect_line_plane(ln, DAY)
    assert e.value.code == "PARALLEL_NO_INTERSECTION"


def test_hai_duong_CHEO_NHAU_thi_NEM():
    """Trên hình phẳng chúng trông như cắt nhau. Trả một điểm 'gần đúng' ở đây
    chính là dạy sai."""
    with pytest.raises(GeometryError):
        K.intersect_line_line(Line3.through(S, A), Line3.through(B, C))


def test_ba_diem_thang_hang_KHONG_dung_duoc_mat_phang():
    with pytest.raises(GeometryError) as e:
        Plane3.through(A, B, Vec3.of(2, 0, 0))
    assert e.value.code == "COLLINEAR_POINTS"


def test_hai_diem_trung_nhau_KHONG_dung_duoc_duong_thang():
    with pytest.raises(GeometryError) as e:
        Line3.through(A, A)
    assert e.value.code == "DEGENERATE_POINTS"


def test_diem_da_thuoc_mat_thi_khong_co_duong_vuong_goc():
    with pytest.raises(GeometryError):
        K.perpendicular_foot_line(A, DAY)


# ── 5. Đo — so trên BÌNH PHƯƠNG ───────────────────────────────────────────
def test_khoang_cach_S_den_day_bang_2():
    """Kiểm tay: `S(0,0,2)`, đáy `z=0` ⇒ `d = 2` ⇒ `d² = 4`."""
    assert M.distance_sq_point_plane(S, DAY) == 4


def test_khoang_cach_luon_tra_BINH_PHUONG_huu_ti():
    """`AC` là đường chéo hình vuông cạnh 1 ⇒ `d = √2` vô tỉ, `d² = 2` hữu tỉ."""
    d2 = M.distance_sq(A, C)
    assert d2 == 2 and isinstance(d2, F)


def test_so_sanh_do_dai_lam_tren_binh_phuong_van_dung():
    assert M.distance_sq(A, C) > M.distance_sq(A, B)


def test_goc_giua_AB_va_AD_bang_90_do():
    """`cos²θ = 0` ⇔ vuông góc. Kiểm tay: hai cạnh kề hình vuông."""
    assert M.cos_sq_between_lines(Line3.through(A, B), Line3.through(A, D)) == 0


def test_goc_giua_AB_va_AC_bang_45_do():
    """Kiểm tay: `cos45° = √2/2` ⇒ `cos²= 1/2`."""
    assert M.cos_sq_between_lines(Line3.through(A, B), Line3.through(A, C)) == F(1, 2)
    assert abs(M.degrees(F(1, 2)) - 45.0) < 1e-9


def test_the_tich_chop_bang_2_phan_3():
    """Kiểm tay: `V = (1/3)·S_đáy·h = (1/3)·1·2 = 2/3`. Hữu tỉ CHÍNH XÁC."""
    v = M.volume_pyramid_fan(S, [A, B, C, D])
    assert v == F(2, 3) and isinstance(v, F)


def test_the_tich_tu_dien():
    """`V = (1/3)·(1/2)·2 = 1/3`. Kiểm tay."""
    assert M.volume_tetrahedron(A, B, D, S) == F(1, 3)


def test_day_KHONG_phang_thi_NEM_khong_tra_so_vo_nghia():
    with pytest.raises(GeometryError):
        M.volume_pyramid_fan(S, [A, B, C, Vec3.of(0, 1, 5)])


def test_khoang_cach_hai_duong_cheo_nhau():
    """`SA` (trục z qua gốc) và `BC` (đường `x=1`, dọc `y`). Kiểm tay: khoảng
    cách = 1 ⇒ `d² = 1`."""
    d2 = M.distance_sq_skew_lines(Line3.through(S, A), Line3.through(B, C))
    assert d2 == 1


# ── 6. TẤT ĐỊNH — cùng input, cùng output ─────────────────────────────────
def test_cung_input_cho_cung_output():
    """Cổng qua bắt buộc của Phase 2."""
    for _ in range(5):
        assert K.intersect_plane_plane(
            Plane3.through(S, A, B), DAY
        ).direction == K.intersect_plane_plane(
            Plane3.through(S, A, B), DAY
        ).direction


def test_ket_qua_KHONG_phu_thuoc_thu_tu_dinh_cua_mat_phang():
    """`(SAB)` và `(BAS)` là cùng một mặt phẳng — pháp tuyến đảo dấu nhưng
    quan hệ hình học phải y hệt."""
    p1, p2 = Plane3.through(S, A, B), Plane3.through(B, A, S)
    assert P.parallel_planes(p1, p2)
    assert M.distance_sq_point_plane(C, p1) == M.distance_sq_point_plane(C, p2)


# ── 7. Nhân KHÔNG được biết gì về LLM ─────────────────────────────────────
def test_kernel_khong_import_tang_AI():
    """Điều kiện để R0 kiểm được BẰNG MẮT, không phải bằng lời hứa."""
    import inspect

    from app.simulation.geometry import exact, kernel, measure, predicates

    for m in (exact, predicates, kernel, measure):
        src = inspect.getsource(m)
        assert "app.ai" not in src, f"{m.__name__} import tầng AI"
        assert "gemini" not in src.lower(), f"{m.__name__} chạm LLM"
