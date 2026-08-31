# -*- coding: utf-8 -*-
"""KHOẢNG CÁCH KHÔNG GIAN — ba cặp toán hạng mở thêm. 0 API call.

`hp_b01_032` chết hai lượt ở Phase 7B với câu *"cặp đối tượng không hợp lệ cho
khoảng cách"*, trong khi `measure.distance_sq_skew_lines` nằm sẵn trong kho từ
đầu. Một năng lực không có CẦU NỐI là một năng lực **không tồn tại với hệ** —
và bản soát năng lực đã đo đúng điều đó chứ không suy từ tên hàm.

File này khoá cả ba tầng của cùng một năng lực:

    kernel (đo đúng) → cầu nối IR (chạy tới số) → C₂ (tự kiểm lại)

Cộng hai thứ dễ mất khi mở rộng: **cặp không hỗ trợ vẫn phải chết TRƯỚC
kernel**, và **kết quả vô tỉ vẫn fail-closed** chứ không thành `1.414…`.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry import measure as M
from app.simulation.geometry.exact import GeometryError, Line3, Plane3, Vec3
from app.simulation.geometry.radical import Radical, radical, square
from app.simulation.semantic_program.geometry_obligations import GEOMETRY_CHECKERS
from app.simulation.semantic_program.ir_static_check import (
    ERR_SAI_KIEU,
    kiem_tinh,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.validator import validate_semantic_program


def V(*x) -> Vec3:
    return Vec3(*(Fraction(v) for v in x))


#: Ox — đường mốc của cả file.
AB = Line3.through(V(0, 0, 0), V(1, 0, 0))
#: Song song Ox, cách 3.
SS = Line3.through(V(0, 3, 0), V(1, 3, 0))
#: Cắt Ox tại gốc.
CAT = Line3.through(V(0, 0, 0), V(0, 1, 0))
#: Chéo Ox, khoảng cách 2 — HỮU TỈ.
CHEO = Line3.through(V(0, 0, 2), V(0, 1, 2))
#: Chéo Ox, khoảng cách √2 — VÔ TỈ.
CHEO_VT = Line3.through(V(0, 0, 1), V(0, 1, 2))

#: z = 0.
P0 = Plane3.through(V(0, 0, 0), V(1, 0, 0), V(0, 1, 0))
#: z = 5, song song P0.
P5 = Plane3.through(V(0, 0, 5), V(1, 0, 5), V(0, 1, 5))
#: x = 0, cắt P0.
PX = Plane3.through(V(0, 0, 0), V(0, 1, 0), V(0, 0, 1))
#: Đường nằm ở z = 4, song song P0.
TREN = Line3.through(V(0, 0, 4), V(1, 0, 4))
#: Đường cắt P0.
XUYEN = Line3.through(V(0, 0, 0), V(0, 0, 1))


# ══ A–C · ĐƯỜNG × ĐƯỜNG, ba trường hợp ══════════════════════════════════
def test_A_hai_duong_CHEO_nhau():
    assert M.distance_sq_lines(AB, CHEO) == 4          # d = 2

def test_B_hai_duong_SONG_SONG():
    assert M.distance_sq_lines(AB, SS) == 9            # d = 3

def test_C_hai_duong_CAT_nhau_thi_bang_0():
    assert M.distance_sq_lines(AB, CAT) == 0

def test_C2_hai_duong_TRUNG_nhau_cung_bang_0():
    """`parallel_lines` bao gồm cả trùng nhau — không cần nhánh riêng."""
    assert M.distance_sq_lines(AB, AB) == 0

def test_doi_thu_tu_KHONG_doi_ket_qua():
    for a, b in ((AB, CHEO), (AB, SS), (AB, CAT)):
        assert M.distance_sq_lines(a, b) == M.distance_sq_lines(b, a)


# ══ D–F · ĐƯỜNG × MẶT ═══════════════════════════════════════════════════
def test_D_duong_SONG_SONG_mat():
    assert M.distance_sq_line_plane(TREN, P0) == 16    # d = 4

def test_E_duong_CAT_mat_thi_bang_0():
    assert M.distance_sq_line_plane(XUYEN, P0) == 0

def test_F_duong_NAM_TRONG_mat_thi_bang_0():
    """Nằm trong ≠ song song, và cả hai vẫn cho 0 — vì có điểm chung.

    `parallel_line_plane` cố ý LOẠI trường hợp nằm trong (giao là vô số điểm,
    không phải rỗng). Phép đo không cần phân biệt hai cái ấy, nhưng phép
    KIỂM QUAN HỆ thì cần — nên chúng vẫn là hai vị từ khác nhau.
    """
    from app.simulation.geometry.predicates import (
        line_in_plane, parallel_line_plane,
    )
    assert line_in_plane(AB, P0) and not parallel_line_plane(AB, P0)
    assert M.distance_sq_line_plane(AB, P0) == 0


# ══ G–I · MẶT × MẶT ═════════════════════════════════════════════════════
def test_G_hai_mat_SONG_SONG_phan_biet():
    assert M.distance_sq_planes(P0, P5) == 25          # d = 5

def test_H_hai_mat_CAT_nhau_thi_bang_0():
    assert M.distance_sq_planes(P0, PX) == 0

def test_I_hai_mat_TRUNG_nhau_thi_bang_0():
    khac = Plane3.through(V(1, 0, 0), V(0, 1, 0), V(1, 1, 0))   # cũng là z = 0
    assert M.distance_sq_planes(P0, khac) == 0


# ══ CẦU NỐI IR — chạy tới một CON SỐ, không dừng ở kernel ═══════════════
class _Node:
    def __init__(self, quantity, of, wrt=None):
        self.quantity, self.of, self.wrt = quantity, of, wrt


def _do(of: str, wrt: str):
    from app.simulation.semantic_program import geometry_exec as GX

    mem = {"AB": AB, "CHEO": CHEO, "SS": SS, "CAT": CAT, "TREN": TREN,
           "XUYEN": XUYEN, "P0": P0, "P5": P5, "PX": PX, "CHEO_VT": CHEO_VT,
           "A": V(0, 0, 0)}
    return GX._do(_Node("distance", of, wrt), mem)


@pytest.mark.parametrize("of,wrt,mong", [
    ("AB", "CHEO", 2), ("AB", "SS", 3), ("AB", "CAT", 0),
    ("TREN", "P0", 4), ("XUYEN", "P0", 0),
    ("P0", "TREN", 4),                       # đổi thứ tự vẫn phải chạy
    ("P0", "P5", 5), ("P0", "PX", 0),
])
def test_cau_noi_IR_chay_toi_mot_con_so(of, wrt, mong):
    assert _do(of, wrt) == Fraction(mong)


def test_cau_noi_tra_PHAN_SO_CHINH_XAC_khong_float():
    d = _do("AB", "CHEO")
    assert isinstance(d, Fraction) and not isinstance(d, float)


# ══ M–O · VÔ TỈ ⇒ CĂN THỨC CHÍNH XÁC (2026-08-31) ══════════════════════
#
# HỢP ĐỒNG CŨ: ba ca dưới đây từng khẳng định `GEOMETRY_IRRATIONAL_RESULT` —
# hệ TỪ CHỐI trả lời khi khoảng cách vô tỉ. Hợp đồng ấy đúng khi miền số chỉ
# có ℚ, và nó từ chối phần lớn bài khoảng cách của hình học THPT: `√2`, `√3`,
# `3√2/4` là đáp số bình thường, không phải ca biên.
#
# Vấn đề chưa bao giờ là tính được hay không — kernel đã có `d²` chính xác từ
# đầu. Nó là BIỂU DIỄN. Nay `sqrt_rational` viết được mọi `√(p/q)` dưới dạng
# `a·√b`, nên ba ca này khẳng định GIÁ TRỊ ĐÚNG thay vì khẳng định lời từ chối.
#
# Ranh giới fail-closed KHÔNG mất, nó chỉ dời tới chỗ thật sự ngoài miền —
# xem `test_P2` (căn thức vượt trần) và `test_radical_domain.py` (tổng hai căn).


def test_M_khoang_cach_CHEO_vo_ti_ra_CAN_THUC_chinh_xac():
    d = _do("AB", "CHEO_VT")
    assert isinstance(d, Radical), f"khoảng cách vô tỉ lại ra {type(d).__name__}"
    # Bình phương lại phải khớp CHÍNH XÁC bình phương khoảng cách của kernel —
    # đây là phép kiểm mạnh hơn so chuỗi, và nó không phụ thuộc cách viết.
    assert square(d) == M.distance_sq_skew_lines(AB, CHEO_VT)


def test_N_duong_mat_vo_ti_ra_CAN_THUC_chinh_xac():
    from app.simulation.semantic_program import geometry_exec as GX

    xien = Plane3(V(0, 0, 0), V(1, 1, 0))              # |n|² = 2
    ln = Line3.through(V(1, 0, 5), V(1, 0, 6))         # ∥ mặt, d = 1/√2
    d = GX._do(_Node("distance", "L", "Q"), {"L": ln, "Q": xien})
    # 1/√2 = √2/2 — dạng chính tắc KHÔNG để căn dưới mẫu.
    assert d == radical(Fraction(1, 2), 2)
    assert square(d) == Fraction(1, 2)


def test_O_mat_mat_vo_ti_ra_CAN_THUC_chinh_xac():
    from app.simulation.semantic_program import geometry_exec as GX

    a = Plane3(V(0, 0, 0), V(1, 1, 0))
    b = Plane3(V(1, 0, 0), V(1, 1, 0))                 # ∥, d = 1/√2
    d = GX._do(_Node("distance", "A", "B"), {"A": a, "B": b})
    assert d == radical(Fraction(1, 2), 2)


def test_P2_ngoai_mien_VAN_fail_closed():
    """Ranh giới không biến mất — nó dời. Căn thức vượt trần vẫn bị TỪ CHỐI.

    Nếu ca này thôi đỏ khi trần bị gỡ, hệ sẽ TREO trên một số bệnh lý thay vì
    nói không — và một lượt treo trông giống hệt một lượt hỏng.
    """
    from app.simulation.geometry.radical import MAX_RADICAND, RadicalDomainError, sqrt_rational

    with pytest.raises(RadicalDomainError):
        sqrt_rational(Fraction(MAX_RADICAND + 1))


def test_P_KHONG_co_mot_xap_xi_float_nao_tren_duong_nay():
    """Đọc mã: không `float(`, không `math.sqrt`, không `** 0.5` ở nhánh đo.

    Đây là chốt cuối. Một `1.414…` lọt vào đây thì mọi phép so BẰNG phía sau
    mất nghĩa, và hệ tụt xuống hạng một bộ vẽ hình.
    """
    from app.simulation.geometry import radical as R
    from app.simulation.semantic_program import geometry_exec as GX
    from app.simulation.semantic_program import geometry_obligations as GO
    from tests.source_scan import con_du, than_ma

    # Quét CẢ ĐƯỜNG, không chỉ một hàm. Mở rộng miền số 2026-08-31 thêm hai
    # mắt xích — `sqrt_rational` và cổng chấm — và một guard chỉ soi `_do` sẽ
    # xanh trong khi float lẻn vào ngay mắt xích bên cạnh.
    #
    # `than_ma` bóc docstring/chú thích trước khi soi. Không bóc thì guard ĐỎ vì
    # chính câu giải thích *"`int(n**0.5)**2 == n` thì sai"* — lần thứ NĂM của
    # cùng một lớp lỗi trong repo này (xem `tests/source_scan.py`).
    duong = [
        ("geometry_exec._do", GX._do, "distance_sq"),
        ("radical.sqrt_rational", R.sqrt_rational, "numerator"),
        ("radical._tach_binh_phuong", R._tach_binh_phuong, "isqrt"),
        ("radical.square", R.square, "Radical"),
        ("radical.radical", R.radical, "Fraction"),
        ("obligations.check_distance", GO.check_distance, "distance_sq"),
    ]
    for ten, ham, moc in duong:
        src = than_ma(ham)
        assert con_du(src, moc), f"{ten}: bóc hỏng — guard tự mù"
        for cam in ["float(", "math.sqrt", "** 0.5", "**0.5", "round(", "abs("]:
            assert cam not in src, f"{ten} dùng {cam} trên đường đúng đắn"


# ══ J–L · THẨM ĐỊNH TĨNH — cặp sai chết TRƯỚC kernel ════════════════════
def _spec(decls, stmts):
    val = validate_semantic_program({
        "simulation_id": "geometry.demo", "title": "Demo khoảng cách",
        "description": "Chương trình đo khoảng cách",
        "pedagogical_intent": "Cho thấy cơ chế ẩn",
        "memory_declarations": decls, "statements": stmts, "obligations": []})
    assert val.ok, val.error
    return val.spec


_DIEM = [{"name": n, "type": "point3", "initial_value": v,
          "model_assumption": "chọn"} for n, v in
         [("A", [0, 0, 0]), ("B", [1, 0, 0]), ("C", [0, 1, 0]), ("S", [0, 0, 1])]]


def test_J_do_khoang_cach_toi_mot_KHOI_bi_tu_choi_truoc_kernel():
    """Khoảng cách tới một khối chưa có định nghĩa — tới mặt gần nhất? tâm?"""
    kq = kiem_tinh(_spec(
        _DIEM + [{"name": "K", "type": "solid"}],
        [{"kind": "construct_solid", "target_var": "K",
          "vertices": ["A", "B", "C", "S"],
          "faces": [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]]},
         {"kind": "assign", "target_var": "d",
          "expr": {"kind": "measure", "quantity": "distance",
                   "of": "K", "wrt": "A"}}]))
    assert not kq.ok
    assert ERR_SAI_KIEU in [i.error_code for i in kq.issues]


def test_K_ten_khong_giai_duoc_bi_tu_choi():
    from app.simulation.semantic_program.validator import (
        validate_semantic_program as v,
    )
    r = v({"simulation_id": "geometry.demo", "title": "Demo khoảng cách",
           "description": "Mô tả", "pedagogical_intent": "Ý đồ",
           "memory_declarations": _DIEM,
           "statements": [{"kind": "assign", "target_var": "d",
                           "expr": {"kind": "measure", "quantity": "distance",
                                    "of": "KHONG_CO", "wrt": "A"}}],
           "obligations": []})
    assert not r.ok


def test_L_cap_ĐUONG_x_MAT_di_qua_tham_dinh_tinh():
    kq = kiem_tinh(_spec(
        _DIEM + [{"name": "d1", "type": "line3"}, {"name": "mp", "type": "plane3"}],
        [{"kind": "construct_line", "target_var": "d1",
          "through_a": "A", "through_b": "B"},
         {"kind": "construct_plane", "target_var": "mp",
          "through": ["A", "B", "C"]},
         {"kind": "assign", "target_var": "kc",
          "expr": {"kind": "measure", "quantity": "distance",
                   "of": "d1", "wrt": "mp"}}]))
    assert kq.ok, [i.dong() for i in kq.issues]


# ══ C₂ · BỘ KIỂM TỰ DẪN XUẤT, không tin lời khai ════════════════════════
def _kiem(snap, container, witness, value=None, wrt=None):
    params = {"witness": witness}
    if value is not None:
        params["value"] = value
    if wrt is not None:
        params["wrt"] = wrt
    return GEOMETRY_CHECKERS["distance"](
        snap, Obligation(kind="distance", container=container, params=params))


SNAP = {"AB": AB, "CHEO": CHEO, "SS": SS, "P0": P0, "P5": P5, "TREN": TREN,
        "d": Fraction(2)}


@pytest.mark.parametrize("a,b,dung", [
    ("AB", "CHEO", "2"), ("AB", "SS", "3"),
    ("TREN", "P0", "4"), ("P0", "P5", "5"),
])
def test_C2_kiem_dung_gia_tri_dung(a, b, dung):
    assert _kiem(SNAP, a, b, value=dung) is None


@pytest.mark.parametrize("a,b,sai", [
    ("AB", "CHEO", "3"), ("TREN", "P0", "5"), ("P0", "P5", "4"),
])
def test_C2_bat_gia_tri_SAI(a, b, sai):
    r = _kiem(SNAP, a, b, value=sai)
    assert r is not None and "d²" in r


def test_C2_chuong_trinh_khai_SAI_thi_bi_bat():
    """LLM khai `d = 7` cho một cặp mà hình cho `2` ⇒ runtime phải cãi."""
    snap = {**SNAP, "kq": Fraction(7)}
    r = _kiem(snap, "AB", "kq", wrt="CHEO")
    assert r is not None and "khai d = 7" in r


def test_C2_chuong_trinh_khai_DUNG_thi_qua():
    snap = {**SNAP, "kq": Fraction(2)}
    assert _kiem(snap, "AB", "kq", wrt="CHEO") is None
