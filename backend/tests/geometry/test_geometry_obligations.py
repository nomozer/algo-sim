# -*- coding: utf-8 -*-
"""Tám checker nghĩa vụ hình học — mỗi cái một ca ĐÚNG và một ca SAI. 0 API call.

Chỉ có ca đúng thì test vô dụng: một checker luôn trả `None` sẽ xanh hết. Nên
mỗi nghĩa vụ ở đây có **cặp** — và ca sai được tạo bằng cách **đổi đúng một
toạ độ**, đúng như phép thử bạn mô tả (`SA ⊥ (ABCD)` → PASS; sửa một toạ độ →
FAIL).

Hình dùng xuyên suốt: chóp `S.ABCD`, đáy vuông cạnh 1 ở `z=0`, `S(0,0,2)`.
"""
from __future__ import annotations

from fractions import Fraction as F

from app.simulation.geometry import Line3, Plane3, Vec3
from app.simulation.geometry.section import pyramid_square
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS as G,
)
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    Obligation,
    accepts_container_type,
    has_server_owned_checker,
)

A, B, C, D = Vec3.of(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(1, 1, 0), Vec3.of(0, 1, 0)
S = Vec3.of(0, 0, 2)
DAY = Plane3.through(A, B, C)
CHOP = pyramid_square(1, 2)


def _ob(kind: str, container: str, witness: str | None = None, **params):
    """`witness` là PROPERTY đọc từ `params`, không phải một trường riêng —
    dựng `Obligation(witness=…)` sẽ bị Pydantic bỏ qua im lặng và mọi checker
    nhận `None`. Bản đầu của helper này viết sai đúng chỗ ấy."""
    if witness is not None:
        params["witness"] = witness
    return Obligation(kind=kind, container=container, params=params)


# ── 1. point_on_line ──────────────────────────────────────────────────────
def test_point_on_line_DUNG():
    snap = {"d": Line3.through(A, B), "M": Vec3.of(F(1, 2), 0, 0)}
    assert G["point_on_line"](snap, _ob("point_on_line", "d", "M")) is None


def test_point_on_line_SAI_khi_lech_mot_toa_do():
    snap = {"d": Line3.through(A, B), "M": Vec3.of(F(1, 2), F(1, 100), 0)}
    assert G["point_on_line"](snap, _ob("point_on_line", "d", "M")) is not None


# ── 2. point_on_plane ─────────────────────────────────────────────────────
def test_point_on_plane_DUNG():
    snap = {"day": DAY, "M": Vec3.of(F(1, 3), F(1, 7), 0)}
    assert G["point_on_plane"](snap, _ob("point_on_plane", "day", "M")) is None


def test_point_on_plane_SAI():
    snap = {"day": DAY, "M": Vec3.of(F(1, 3), F(1, 7), F(1, 1000))}
    assert G["point_on_plane"](snap, _ob("point_on_plane", "day", "M")) is not None


# ── 3. parallel ───────────────────────────────────────────────────────────
def test_parallel_hai_duong_DUNG():
    snap = {"ab": Line3.through(A, B), "dc": Line3.through(D, C)}
    assert G["parallel"](snap, _ob("parallel", "ab", "dc")) is None


def test_parallel_hai_duong_SAI():
    snap = {"ab": Line3.through(A, B), "ad": Line3.through(A, D)}
    assert G["parallel"](snap, _ob("parallel", "ab", "ad")) is not None


def test_parallel_duong_NAM_TRONG_mat_KHONG_tinh_la_song_song():
    """Ranh giới dạy học: nằm trong ≠ song song. Gộp là mất một kết luận."""
    snap = {"ab": Line3.through(A, B), "day": DAY}
    r = G["parallel"](snap, _ob("parallel", "ab", "day"))
    assert r is not None and "TRONG" in r


# ── 4. perpendicular ──────────────────────────────────────────────────────
def test_perpendicular_SA_vuong_goc_DAY_DUNG():
    """Phép thử kinh điển: `SA ⊥ (ABCD)` ⇒ PASS."""
    snap = {"sa": Line3.through(S, A), "day": DAY}
    assert G["perpendicular"](snap, _ob("perpendicular", "sa", "day")) is None


def test_perpendicular_SAI_khi_SUA_MOT_TOA_DO():
    """Kéo `S` lệch khỏi trục ⇒ FAIL. Đúng phép thử bạn mô tả."""
    S_lech = Vec3.of(F(1, 10), 0, 2)
    snap = {"sa": Line3.through(S_lech, A), "day": DAY}
    assert G["perpendicular"](snap, _ob("perpendicular", "sa", "day")) is not None


def test_perpendicular_hai_duong_ke_DUNG():
    snap = {"ab": Line3.through(A, B), "ad": Line3.through(A, D)}
    assert G["perpendicular"](snap, _ob("perpendicular", "ab", "ad")) is None


def test_perpendicular_duong_NAM_TRONG_mat_KHONG_phai_vuong_goc():
    """Bẫy lộn dấu: `AB` nằm trong đáy nên `AB·n = 0`, nhưng nó KHÔNG vuông góc
    với đáy. Viết `dot==0` cho cặp đường-mặt là test này đỏ."""
    snap = {"ab": Line3.through(A, B), "day": DAY}
    assert G["perpendicular"](snap, _ob("perpendicular", "ab", "day")) is not None


# ── 5. coplanar ───────────────────────────────────────────────────────────
def test_coplanar_bon_dinh_day_DUNG():
    assert G["coplanar"]({"tg": [A, B, C, D]}, _ob("coplanar", "tg")) is None


def test_coplanar_SAI_khi_mot_dinh_nhac_len():
    assert G["coplanar"]({"tg": [A, B, C, Vec3.of(0, 1, F(1, 50))]},
                         _ob("coplanar", "tg")) is not None


def test_coplanar_gan_vao_KHOI_thi_bao_gan_sai_chu_the():
    r = G["coplanar"]({"k": CHOP}, _ob("coplanar", "k"))
    assert r is not None and "gắn sai chủ thể" in r


# ── 6. distance ───────────────────────────────────────────────────────────
def test_distance_S_den_day_bang_2_DUNG():
    snap = {"day": DAY, "S": S}
    assert G["distance"](snap, _ob("distance", "day", "S", value="2")) is None


def test_distance_SAI_khi_de_mong_so_khac():
    snap = {"day": DAY, "S": S}
    r = G["distance"](snap, _ob("distance", "day", "S", value="3"))
    assert r is not None and "d²" in r


def test_distance_KHONG_khai_gia_tri_thi_KHONG_bao_sai():
    """Không khai ⇒ chỉ kiểm được cấu trúc. Báo sai ở đây là bắt oan."""
    snap = {"day": DAY, "S": S}
    assert G["distance"](snap, _ob("distance", "day", "S")) is None


def test_distance_so_tren_BINH_PHUONG_van_dung_voi_can_vo_ti():
    """`AC` = √2 — vô tỉ. Đề khai `value` là chuỗi phân số nên ca này KHÔNG
    khớp được, và checker phải nói lệch chứ không được làm tròn cho khớp."""
    snap = {"A": A, "C": C}
    assert G["distance"](snap, _ob("distance", "A", "C", value="1")) is not None


# ── 7. angle ──────────────────────────────────────────────────────────────
def test_angle_AB_AD_vuong_goc_cos_sq_bang_0():
    snap = {"ab": Line3.through(A, B), "ad": Line3.through(A, D)}
    assert G["angle"](snap, _ob("angle", "ab", "ad", cos_sq="0")) is None


def test_angle_AB_AC_bang_45_do():
    """`cos45° = √2/2` ⇒ `cos² = 1/2`. Kiểm tay."""
    snap = {"ab": Line3.through(A, B), "ac": Line3.through(A, C)}
    assert G["angle"](snap, _ob("angle", "ab", "ac", cos_sq="1/2")) is None


def test_angle_SAI_khi_de_mong_goc_khac():
    snap = {"ab": Line3.through(A, B), "ac": Line3.through(A, C)}
    assert G["angle"](snap, _ob("angle", "ab", "ac", cos_sq="0")) is not None


# ── 8. volume ─────────────────────────────────────────────────────────────
def test_volume_chop_bang_2_phan_3_DUNG():
    """`V = (1/3)·1·2 = 2/3`. Kiểm tay."""
    assert G["volume"]({"k": CHOP}, _ob("volume", "k", value="2/3")) is None


def test_volume_SAI_khi_de_mong_so_khac():
    r = G["volume"]({"k": CHOP}, _ob("volume", "k", value="1"))
    assert r is not None and "V =" in r


def test_volume_gan_vao_thu_KHONG_phai_khoi_thi_bao_loi():
    assert G["volume"]({"k": [A, B, C]}, _ob("volume", "k", value="1")) is not None


# ── Hợp đồng taxonomy ─────────────────────────────────────────────────────
def test_ca_TAM_nghia_vu_deu_co_checker_server_owned():
    """Khác miền Tin học — ở đó `predicate_verdict` phải để mức yếu vì kiểm nó
    đòi cài lại thuật toán đang kiểm. Hình học không có vấn đề ấy."""
    for k in G:
        assert has_server_owned_checker(k), f"{k} không có checker server-owned"


def test_bang_KIEU_chan_dung_chu_the_sai():
    """`point_on_plane` gắn vào một `line3` phải bị chặn NGAY ở C₁a."""
    assert accepts_container_type("point_on_plane", "plane3")
    assert not accepts_container_type("point_on_plane", "line3")
    assert accepts_container_type("volume", "solid")
    assert not accepts_container_type("volume", "array")


def test_tam_kind_deu_nam_trong_taxonomy():
    for k in G:
        assert k in OBLIGATION_KINDS
