# -*- coding: utf-8 -*-
"""MIỀN SỐ `a·√b` — chính tắc, chính xác, và **fail closed** ở đúng ranh giới.

Ba nhóm câu hỏi, cố ý tách rời vì chúng hỏng theo ba kiểu khác nhau:

  ① CHUẨN HOÁ — `√8` và `2√2` có phải cùng một đối tượng không? Nếu không thì
    mọi phép so bằng phía dưới đều nói dối, kể cả khi số học đúng.
  ② RANH GIỚI — `√2 + √3` có bị từ chối không? Một miền lặng lẽ nới rộng là
    một CAS nửa vời, và nó sai ở chỗ không ai kiểm.
  ③ KHÔNG FLOAT — quyết định "có phải chính phương" đi bằng số học nguyên.
"""
from __future__ import annotations

import math
from fractions import Fraction

import pytest

from app.simulation.geometry.radical import (
    MAX_RADICAND,
    ExactNumber,
    Radical,
    RadicalDomainError,
    add,
    display,
    divided_by_rational,
    from_json,
    is_exact_number,
    negate,
    parse_exact,
    radical,
    sign,
    sqrt_rational,
    square,
    times_rational,
    to_json,
)

F = Fraction


# ══ ① CHUẨN HOÁ ═══════════════════════════════════════════════════════════
@pytest.mark.parametrize("vao, ra", [
    (F(1), F(1)),          # √1  = 1
    (F(4), F(2)),          # √4  = 2
    (F(9), F(3)),
    (F(0), F(0)),
    (F(1, 4), F(1, 2)),    # √(1/4) = 1/2
    (F(4, 9), F(2, 3)),
])
def test_can_cua_so_chinh_phuong_ve_HUU_TI(vao, ra):
    """Kết quả hữu tỉ phải là `Fraction`, KHÔNG phải `2·√1` (`§17`)."""
    kq = sqrt_rational(vao)
    assert isinstance(kq, Fraction), f"√{vao} trả về {type(kq).__name__}, không phải Fraction"
    assert kq == ra


@pytest.mark.parametrize("vao, he, can", [
    (F(2), F(1), 2),           # √2
    (F(3), F(1), 3),
    (F(8), F(2), 2),           # √8   = 2√2
    (F(18), F(3), 2),          # √18  = 3√2
    (F(12), F(2), 3),          # √12  = 2√3
    (F(3, 4), F(1, 2), 3),     # √(3/4)   = √3/2
    (F(8, 9), F(2, 3), 2),     # √(8/9)   = 2√2/3
    (F(18, 25), F(3, 5), 2),   # √(18/25) = 3√2/5
    (F(5, 4), F(1, 2), 5),     # √(5/4)   = √5/2
    (F(50), F(5), 2),          # √50  = 5√2
])
def test_can_vo_ti_ve_dang_CHINH_TAC(vao, he, can):
    kq = sqrt_rational(vao)
    assert isinstance(kq, Radical), f"√{vao} phải là Radical, nhận {kq!r}"
    assert (kq.he, kq.can) == (he, can)


def test_MOT_so_co_DUNG_MOT_cach_viet():
    """`√8 == 2√2` — nếu sai, bộ chấm chính xác trở thành bộ chấm gần đúng."""
    assert sqrt_rational(F(8)) == radical(2, 2)
    assert sqrt_rational(F(8)) == radical(1, 8)      # dựng từ căn chưa rút
    assert radical(1, 18) == radical(3, 2)
    assert radical(6, 8) == radical(12, 2)
    # …và hai số KHÁC nhau thì khác nhau.
    assert radical(1, 2) != radical(1, 3)
    assert radical(2, 2) != radical(3, 2)


def test_khong_ton_tai_bieu_dien_thoai_hoa():
    """Trong hệ KHÔNG có `0·√2`, `3·√1`, `2·√4` — chúng đã về hữu tỉ lúc dựng."""
    assert radical(0, 7) == F(0) and isinstance(radical(0, 7), Fraction)
    assert radical(3, 1) == F(3) and isinstance(radical(3, 1), Fraction)
    assert radical(2, 4) == F(4) and isinstance(radical(2, 4), Fraction)


def test_can_AM_bi_TU_CHOI_khong_tra_None():
    """Từ chối bằng exception, không bằng `None`: `None` trôi xuống dưới rồi nổ
    ở một chỗ không liên quan, còn exception dừng ngay tại chỗ sai."""
    with pytest.raises(RadicalDomainError):
        sqrt_rational(F(-1))
    with pytest.raises(RadicalDomainError):
        radical(1, 0)
    with pytest.raises(RadicalDomainError):
        radical(1, -2)


def test_tran_can_thuc_tu_choi_ro_rang_thay_vi_treo():
    with pytest.raises(RadicalDomainError, match="vượt trần"):
        radical(1, MAX_RADICAND + 1)


# ══ ② PHÉP TOÁN + RANH GIỚI ═══════════════════════════════════════════════
def test_binh_phuong_LUON_huu_ti():
    """Tính chất giữ cho bộ chấm không phải viết lại: nó so `d² == khai²`."""
    for x in [sqrt_rational(F(2)), radical(F(3, 5), 2), F(7, 3), F(0)]:
        assert isinstance(square(x), Fraction)
    assert square(sqrt_rational(F(2))) == F(2)
    assert square(radical(F(3, 5), 2)) == F(18, 25)
    assert square(radical(F(-3, 5), 2)) == F(18, 25)


def test_binh_phuong_la_nghich_dao_cua_can():
    for v in [F(2), F(3), F(8), F(18, 25), F(3, 4), F(7), F(0), F(4, 9)]:
        assert square(sqrt_rational(v)) == v


def test_dau_va_doi_dau():
    assert sign(radical(F(3), 2)) == 1
    assert sign(radical(F(-3), 2)) == -1
    assert sign(F(0)) == 0
    assert negate(radical(F(3), 2)) == radical(F(-3), 2)
    assert negate(negate(radical(F(3), 2))) == radical(F(3), 2)


def test_nhan_chia_huu_ti_giu_chinh_tac():
    r = sqrt_rational(F(2))                    # √2
    assert times_rational(r, 3) == radical(3, 2)
    assert divided_by_rational(radical(6, 2), 3) == radical(2, 2)
    # Nhân về 0 phải rơi về hữu tỉ, không giữ `0·√2`.
    assert times_rational(r, 0) == F(0)
    assert isinstance(times_rational(r, 0), Fraction)
    with pytest.raises(RadicalDomainError):
        divided_by_rational(r, 0)


def test_cong_CHI_khi_con_trong_mien():
    assert add(F(1, 2), F(1, 3)) == F(5, 6)
    assert add(radical(2, 3), radical(5, 3)) == radical(7, 3)   # cùng căn thức
    assert add(radical(1, 2), F(0)) == radical(1, 2)            # cộng 0
    assert add(radical(2, 2), radical(-2, 2)) == F(0)           # triệt tiêu ⇒ hữu tỉ


def test_TONG_HAI_CAN_KHAC_NHAU_bi_tu_choi():
    """RANH GIỚI CỦA MIỀN. `√2 + √3` không viết được dưới dạng `a·√b`.

    Nếu ca này thôi đỏ, ai đó đã mở tổng tuỳ ý — tức đã bắt đầu viết một CAS,
    và một CAS nửa vời trả lời sai ở chỗ không ai kiểm.
    """
    with pytest.raises(RadicalDomainError, match="không viết được"):
        add(sqrt_rational(F(2)), sqrt_rational(F(3)))
    with pytest.raises(RadicalDomainError):
        add(sqrt_rational(F(2)), F(1))


# ══ ③ KHÔNG FLOAT ═════════════════════════════════════════════════════════
def test_quyet_dinh_chinh_phuong_KHONG_di_qua_float():
    """Số lớn là chỗ float phân rẽ khỏi số học nguyên.

    `int(x ** 0.5) ** 2 == x` sai với những `x` cỡ này; `math.isqrt` thì không.
    Ca này chạy đúng ⇒ đường quyết định là số học nguyên.
    """
    # Giữ DƯỚI `MAX_RADICAND`: trần là một quyết định thật của miền (`§19`),
    # nên ca kiểm không được lách nó — lách trần là kiểm một hệ khác.
    m = 999983**2                        # = 999966000289 < 10¹², chính phương
    assert m < MAX_RADICAND
    assert sqrt_rational(F(m)) == F(999983)

    n = m - 1                            # KHÔNG chính phương
    assert math.isqrt(n) ** 2 != n
    kq = sqrt_rational(F(n))
    assert isinstance(kq, Radical), "số không chính phương lại ra hữu tỉ"
    # …và bình phương lại phải khớp CHÍNH XÁC. Một sai số một đơn vị ở tầng
    # nguyên sẽ lộ ra đúng ở đây.
    assert square(kq) == F(n)


def test_khong_float_tren_duong_so_chinh_xac():
    """Guard NGUỒN: miền số không được gọi `math.sqrt` / `float(` / `**0.5`.

    Bóc docstring bằng AST (`tests/source_scan`), không bằng biểu thức chính
    quy — module này NÓI VỀ `math.sqrt` để giải thích vì sao không dùng nó, và
    một guard so khớp thô sẽ đỏ vì chính câu ấy. Đó là lớp lỗi đã lặp năm lần
    trong repo.
    """
    import app.simulation.geometry.radical as R
    from tests.source_scan import con_du, than_ma

    src = than_ma(R.__file__)
    assert con_du(src, "isqrt", 2000), "bóc hỏng — không còn mã để soi"
    for cam in ["math.sqrt", "float(", "** 0.5", "**0.5", "round("]:
        assert cam not in src, f"miền số chính xác dùng {cam}"


# ══ SERIALIZATION + HIỂN THỊ ══════════════════════════════════════════════
@pytest.mark.parametrize("x", [
    F(0), F(2), F(-3, 5), F(7, 2),
    radical(1, 2), radical(3, 2), radical(F(3, 5), 2), radical(F(-1, 2), 3),
])
def test_serialization_roundtrip(x: ExactNumber):
    assert from_json(to_json(x)) == x


def test_json_la_CAU_TRUC_khong_phai_chuoi_hien_thi():
    d = to_json(radical(F(3, 5), 2))
    assert d == {"kind": "radical", "coefficient": "3/5", "radicand": 2}
    assert to_json(F(3, 5)) == {"kind": "rational", "value": "3/5"}


def test_from_json_tu_choi_du_lieu_la():
    for xau in [None, "3/5", {"kind": "float", "value": "1.4"}, {"kind": "radical"}]:
        with pytest.raises((RadicalDomainError, KeyError, TypeError)):
            from_json(xau)


@pytest.mark.parametrize("x, chu", [
    (F(2), "2"),
    (F(3, 5), "3/5"),
    (radical(1, 2), "√2"),
    (radical(3, 2), "3√2"),
    (radical(F(3, 5), 2), "3√2/5"),
    (radical(F(1, 2), 3), "√3/2"),
    (radical(F(-1, 2), 3), "-√3/2"),
    (radical(F(-3, 4), 5), "-3√5/4"),
])
def test_hien_thi_theo_cach_viet_SGK(x, chu):
    assert display(x) == chu


# ══ ĐỌC GIÁ TRỊ MONG ĐỢI (§9 — văn phạm HẸP) ══════════════════════════════
@pytest.mark.parametrize("raw, ky_vong", [
    ("sqrt(2)", radical(1, 2)),
    ("√2", radical(1, 2)),
    ("3*sqrt(2)", radical(3, 2)),
    ("sqrt(2)/5", radical(F(1, 5), 2)),
    ("3*sqrt(2)/5", radical(F(3, 5), 2)),
    ("sqrt(8)", radical(2, 2)),          # rút gọn lúc đọc
    ("-sqrt(3)", radical(-1, 3)),
    ("1/2*sqrt(3)", radical(F(1, 2), 3)),
    ("3/5", F(3, 5)),                    # hữu tỉ vẫn đọc được
    ("2", F(2)),
    (Fraction(3, 5), F(3, 5)),
    (7, F(7)),
])
def test_parse_van_pham_hep(raw, ky_vong):
    assert parse_exact(raw) == ky_vong


@pytest.mark.parametrize("raw", [
    "sqrt(2) + sqrt(3)",     # tổng — ngoài miền
    "sqrt(-2)",              # căn âm
    "2**64",                 # biểu thức
    "__import__('os')",      # không eval, và ca này khoá điều đó
    "abc", "", "sqrt()",
])
def test_parse_TU_CHOI_ngoai_van_pham(raw):
    """`None`, không phải 0 — nhầm 'không biết' thành 'bằng 0' làm nghĩa vụ
    không kiểm được trở thành nghĩa vụ kiểm SAI, và nó PASS bài đáng lẽ FAIL."""
    assert parse_exact(raw) is None


def test_is_exact_number_loai_bool():
    assert is_exact_number(F(1)) and is_exact_number(2) and is_exact_number(radical(1, 2))
    assert not is_exact_number(True) and not is_exact_number(False)
    assert not is_exact_number(1.5) and not is_exact_number("2")
