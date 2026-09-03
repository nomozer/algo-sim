# -*- coding: utf-8 -*-
"""MIỀN SỐ CHÍNH XÁC MỞ RỘNG SANG π — `he·π^mu·√can`, `mu ∈ {0, 1}`.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

Mọi đại lượng của hình học cong THPT có dạng `q·π·(một căn hoặc một hữu tỉ)`:
`(4/3)πR³`, `4πR²`, `πr²h`, `2πrh`, `(1/3)πr²h`, `πrl`. Miền `a·√b` không chở
nổi một cái nào. Không có π thì Phase 2 (`CURVED_SOLID_FOUNDATION`) không có
chỗ để trả kết quả về, và mọi phép đo cong sẽ phải trả `float` — tức mở lại
đúng cánh cửa mà cả kernel này được dựng để đóng.

─── ĐIỀU FILE NÀY CANH, NGOÀI VIỆC π CHẠY ĐÚNG ────────────────────────────

**Mở miền ĐO không được mở miền TOẠ ĐỘ.** Đó là bất biến đắt nhất ở đây: một
toạ độ vô tỉ làm hỏng mọi phép so bằng của kernel (`same_point`, `coplanar`,
`point_on_plane`), trong khi một đại lượng vô tỉ chỉ là một đáp số bình thường.
`test_N10_*` canh đúng ranh giới ấy.

**Và số cũ phải không đổi — cả về nghĩa lẫn về DÂY.** `to_json` cố ý bỏ trường
`pi` khi `mu == 0`, nên mọi payload đã tồn tại (fixture, envelope cache,
artifact đánh giá) giữ nguyên từng byte. `test_N8_*`/`test_N9_*` khoá cả hai
chiều.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry.exact import GeometryError, Vec3
from app.simulation.geometry.radical import (
    MAX_RADICAND,
    PI_EXPONENT_DOMAIN,
    Radical,
    RadicalDomainError,
    add,
    display,
    divided_by_rational,
    from_json,
    multiply,
    negate,
    radical,
    sign,
    sqrt_rational,
    square,
    times_rational,
    to_json,
)

PI = radical(1, 1, 1)


# ══ N1–N2 · MIỀN CŨ KHÔNG ĐỔI ════════════════════════════════════════════
def test_N1_huu_ti_van_la_Fraction():
    assert radical(4, 1) == Fraction(4)
    assert sqrt_rational(Fraction(9, 4)) == Fraction(3, 2)
    assert isinstance(radical(2, 4), Fraction)


def test_N2_can_thuc_cu_khong_doi_mot_ly():
    """Mọi tính chất của `a·√b` giữ nguyên — `mu` mặc định 0 nên số cũ dựng
    bằng constructor hai đối số vẫn so BẰNG với số dựng qua `radical()`."""
    assert radical(1, 8) == Radical(Fraction(2), 2)
    assert Radical(Fraction(2), 2) == Radical(Fraction(2), 2, 0)
    assert display(radical(3, 2)) == "3√2"
    assert display(sqrt_rational(Fraction(1, 2))) == "√2/2"
    assert square(radical(3, 2)) == 18
    assert add(radical(1, 5), radical(2, 5)) == radical(3, 5)


# ══ N3–N4 · π VÀO ĐƯỢC ═══════════════════════════════════════════════════
def test_N3_pi_la_mot_so_chinh_xac():
    assert isinstance(PI, Radical)
    assert (PI.he, PI.can, PI.mu) == (Fraction(1), 1, 1)
    assert display(PI) == "π"
    assert sign(PI) == 1 and sign(negate(PI)) == -1


def test_N4_pi_can_thuc():
    assert display(radical(1, 5, 1)) == "π√5"
    assert display(radical(Fraction(4, 3), 3, 1)) == "4π√3/3"
    assert display(radical(2, 1, 1)) == "2π"
    assert display(radical(-1, 1, 1)) == "-π"


@pytest.mark.parametrize("he,can,mu,mong", [
    (Fraction(4, 3), 3, 1, "4π√3/3"),   # V khối cầu, R² = 3
    (4 * 3, 1, 1, "12π"),               # S mặt cầu, R² = 3
    (1, 5, 1, "π√5"),                   # S_xq nón, r = 1, h = 2
    (2, 1, 1, "2π"),
])
def test_N4b_dang_thuc_te_cua_hinh_hoc_cong(he, can, mu, mong):
    """Bốn dạng lấy thẳng từ `CURVED_GEOMETRY_FOUNDATION_DESIGN §8b`. Nếu một
    dạng nào của Phase 2 không viết được ở đây thì nền này chưa đủ."""
    assert display(radical(he, can, mu)) == mong


# ══ N5 · NHÂN + CHUẨN HOÁ ════════════════════════════════════════════════
def test_N5_nhan_xu_ca_ba_thanh_phan():
    assert multiply(PI, radical(1, 5)) == radical(1, 5, 1)
    assert multiply(radical(2, 1, 1), radical(3, 5)) == radical(6, 5, 1)
    assert multiply(radical(1, 5), radical(1, 5)) == Fraction(5)
    assert multiply(radical(1, 5), Fraction(3, 2)) == radical(Fraction(3, 2), 5)
    assert multiply(PI, Fraction(0)) == Fraction(0)


def test_N5b_nhan_rut_binh_phuong_QUA_pi():
    """`π·√2·√2 = 2π`, không phải `π√4`. Chuẩn hoá chạy SAU phép nhân, nếu
    không thì một số có hai cách viết và phép so bằng nói dối."""
    assert multiply(radical(1, 2, 1), radical(1, 2)) == radical(2, 1, 1)
    assert display(multiply(radical(1, 2, 1), radical(1, 2))) == "2π"


def test_N5c_chuan_hoa_khong_de_lai_hai_cach_viet():
    assert radical(0, 5, 1) == Fraction(0)      # hệ số 0 thắng cả π
    assert radical(1, 4, 1) == radical(2, 1, 1)  # √4 rút qua π
    assert radical(1, 3, 0) == radical(1, 3)     # mu = 0 là số cũ


# ══ N6–N7 · CỘNG ═════════════════════════════════════════════════════════
def test_N6_cong_cung_can_cung_mu():
    assert add(radical(1, 5, 1), radical(2, 5, 1)) == radical(3, 5, 1)
    assert add(PI, PI) == radical(2, 1, 1)
    # Trừ = cộng với số đối. `V trụ − V nón` cùng dạng ⇒ cộng được, và đó là
    # tiền đề của "khối bù" ở `§18` của bản thiết kế.
    assert add(radical(1, 1, 1), negate(radical(Fraction(1, 3), 1, 1))) == \
        radical(Fraction(2, 3), 1, 1)
    assert add(PI, negate(PI)) == Fraction(0)


@pytest.mark.parametrize("a,b", [
    (radical(1, 5, 1), PI),              # π√5 + π   — khác căn
    (PI, Fraction(1)),                   # π + 1     — khác mũ
    (radical(1, 2), radical(1, 3)),      # √2 + √3   — giới hạn cũ, còn nguyên
    (radical(1, 5, 1), radical(1, 5)),   # π√5 + √5  — khác mũ
])
def test_N7_cong_khong_tuong_thich_TU_CHOI(a, b):
    """Fail closed, không xấp xỉ, không dựng cây biểu thức.

    Hệ quả thật phải khai: `S_tp` nón `= πrl + πr²` KHÔNG viết được trong miền
    này. Đó không phải giới hạn mới — nó là `√2 + √3`, chỉ lộ ra ở chỗ khác.
    """
    with pytest.raises(RadicalDomainError):
        add(a, b)


# ══ N8–N9 · TUẦN TỰ HOÁ ══════════════════════════════════════════════════
def test_N8_vong_lai_giu_nguyen_gia_tri():
    for x in (Fraction(3), Fraction(-1, 7), radical(3, 2), PI,
              radical(Fraction(4, 3), 3, 1), radical(-2, 5, 1)):
        assert from_json(to_json(x)) == x


def test_N8b_pi_KHONG_xuat_hien_khi_mu_bang_0():
    """DÂY của số cũ không đổi một byte — đó là điều kiện để mọi fixture,
    envelope đã cache và artifact đánh giá giữ nguyên."""
    assert to_json(radical(3, 2)) == {
        "kind": "radical", "coefficient": "3", "radicand": 2}
    assert "pi" not in to_json(radical(3, 2))
    assert to_json(Fraction(5)) == {"kind": "rational", "value": "5"}


def test_N8c_pi_xuat_hien_dung_khi_can():
    assert to_json(PI) == {
        "kind": "radical", "coefficient": "1", "radicand": 1, "pi": 1}


def test_N9_payload_CU_doc_duoc_nhu_mu_0():
    """Hợp đồng thuộc về `from_json`, không thuộc về phía đọc: `pi` vắng ⇒ 0.

    Đây là đọc ĐÚNG, không phải đọc rộng lượng — mọi payload sinh trước bản
    này đều là số không chứa π.
    """
    assert from_json({"kind": "radical", "coefficient": "3", "radicand": 2}) \
        == radical(3, 2)
    assert from_json({"kind": "rational", "value": "7/2"}) == Fraction(7, 2)


# ══ N10 · TOẠ ĐỘ KHÔNG ĐƯỢC MỞ ═══════════════════════════════════════════
@pytest.mark.parametrize("xau", [PI, radical(1, 2), radical(1, 5, 1)])
def test_N10_toa_do_TU_CHOI_so_khong_huu_ti(xau):
    """Bất biến đắt nhất của wave này.

    `Vec3` là ℚ³ và phải ở lại ℚ³: mọi vị từ của kernel (`same_point`,
    `coplanar`, `point_on_plane`) so BẰNG trên `Fraction`. Một toạ độ mang căn
    thức làm chúng hoặc sai hoặc phải học so gần đúng — mà so gần đúng chính là
    thứ `Fraction` được chọn để tránh.
    """
    with pytest.raises(GeometryError):
        Vec3.of(xau, 0, 0)


def test_N10b_Vec3_van_chi_giu_Fraction():
    v = Vec3.of(1, Fraction(1, 2), "3/4")
    assert all(isinstance(c, Fraction) for c in (v.x, v.y, v.z))


# ══ MIỀN SỐ MŨ ═══════════════════════════════════════════════════════════
def test_mien_so_mu_pi_dung_la_0_va_1():
    assert PI_EXPONENT_DOMAIN == (0, 1)


@pytest.mark.parametrize("mu", [2, -1, 3, -2])
def test_so_mu_ngoai_mien_TU_CHOI(mu):
    with pytest.raises(RadicalDomainError):
        radical(1, 5, mu)


def test_nhan_hai_dai_luong_pi_TU_CHOI_vi_ra_pi_binh():
    """`π · π` không có phép đo nào sinh ra, nên từ chối ở đây là chặn một
    đường không ai đi — không phải cắt một năng lực."""
    with pytest.raises(RadicalDomainError):
        multiply(PI, PI)


def test_binh_phuong_cua_dai_luong_pi_TU_CHOI():
    """`square` là đường của bộ chấm (`check_distance` so `d² == khai²`).
    Trả một `Fraction` đúng-hệ-số mà sai-giá-trị sẽ làm bộ chấm nói PASS."""
    with pytest.raises(RadicalDomainError):
        square(PI)
    with pytest.raises(RadicalDomainError):
        square(radical(1, 5, 1))


def test_chia_va_nhan_huu_ti_GIU_nguyen_so_mu():
    assert times_rational(PI, Fraction(3, 2)) == radical(Fraction(3, 2), 1, 1)
    assert divided_by_rational(radical(4, 3, 1), 2) == radical(2, 3, 1)
    with pytest.raises(RadicalDomainError):
        divided_by_rational(PI, 0)


def test_sqrt_van_chi_nhan_huu_ti():
    """Không có `sqrt(π)`. π đi vào đại lượng SAU các phép metric hữu tỉ/căn,
    không đi vào giữa chúng — thêm `sqrt(π)` "cho đủ" là thêm một dạng số mà
    không phép đo nào sinh ra."""
    assert sqrt_rational(Fraction(5)) == radical(1, 5)
    with pytest.raises((TypeError, ValueError)):
        sqrt_rational(PI)  # type: ignore[arg-type]


def test_tran_can_thuc_van_ap_cho_ca_so_co_pi():
    with pytest.raises(RadicalDomainError):
        radical(1, MAX_RADICAND + 1, 1)
