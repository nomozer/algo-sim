# -*- coding: utf-8 -*-
"""NĂM NĂNG LỰC KHOẢNG CÁCH × KẾT QUẢ CĂN THỨC — đo, chấm, và chấm SAI được.

Mỗi năng lực hỏi ba câu, và câu thứ ba là câu hay bị bỏ quên:

  ① engine đo ra ĐÚNG căn thức nào?
  ② bộ chấm có PASS khi chương trình khai đúng giá trị ấy?
  ③ bộ chấm có FAIL khi chương trình khai một căn thức KHÁC?

Thiếu ③ thì ② vô nghĩa: một bộ chấm luôn PASS cũng qua được ②. Đây chính là
cách một cổng chấm trở thành một con dấu.

RANH GIỚI: file này KHÔNG cài lại hình học. Nó gọi `geometry_exec._do` (đường
sản phẩm) và `GEOMETRY_CHECKERS` (cổng thật), rồi đối chiếu với căn thức tính
tay từ hình. Cài lại công thức ở đây là dựng tầng hình học thứ hai để so với
tầng thứ nhất — và hai tầng sẽ lệch nhau ở một ca nào đó, lệch im lặng.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.geometry.radical import Radical, radical, square
from app.simulation.semantic_program import geometry_exec as GX
from app.simulation.semantic_program.geometry_obligations import GEOMETRY_CHECKERS

F = Fraction
V = Vec3.of


class _Node:
    """Nút `measure` tối thiểu — cùng hình dạng IR mà `_do` đọc."""

    def __init__(self, quantity: str, of: str, wrt: str | None = None):
        self.quantity, self.of, self.wrt = quantity, of, wrt


class _Ob:
    def __init__(self, container, witness, **params):
        self.kind = "distance"
        self.container, self.witness = container, witness
        self.params = params


def _do(mem: dict, of: str, wrt: str):
    return GX._do(_Node("distance", of, wrt), mem)


def _cham(mem: dict, ob) -> str | None:
    return GEOMETRY_CHECKERS["distance"](mem, ob)


# ══ NĂM HÌNH, năm cặp đối tượng — toạ độ chọn cho khoảng cách VÔ TỈ ═══════
#
# Mỗi hình dựng bằng số nguyên nhỏ, và giá trị mong đợi tính tay bên lề. Không
# lấy giá trị từ chính engine: lấy từ engine thì ca kiểm chỉ khẳng định "engine
# bằng chính nó".

def _hinh_diem_duong():
    """A(0,0,0) tới đường x=y trong mặt z=0. d = |AP| với P là chân vuông góc.

    Đường qua (1,1,0) phương (1,1,0); A = (1,0,0).
    d² = |AQ|² − (AQ·u)²/|u|² với Q=(0,0,0): AQ = (−1,0,0), u = (1,1,0)
       = 1 − (−1)²/2 = 1/2  ⇒  d = √2/2
    """
    return ({"A": V(1, 0, 0), "L": Line3.through(V(0, 0, 0), V(1, 1, 0))},
            "A", "L", radical(F(1, 2), 2))


def _hinh_diem_mat():
    """A(1,1,1) tới mặt x+y+z=0. d = |1+1+1|/√3 = 3/√3 = √3.

    d² = 9/3 = 3  ⇒  d = √3
    """
    return ({"A": V(1, 1, 1), "P": Plane3(V(0, 0, 0), V(1, 1, 1))},
            "A", "P", radical(1, 3))


def _hinh_hai_duong_cheo():
    """Trục Ox và đường (0,1,1)+t(0,0,1) — chéo nhau.

    u = (1,0,0), v = (0,0,1), u×v = (0,−1,0); w = (0,1,1)
    d = |w·(u×v)|/|u×v| = 1/1 = 1 ⇒ HỮU TỈ. Cần hình khác.

    Dùng Ox và đường (0,1,1)+t(0,1,1): u×v = (0,−1,1), |u×v|² = 2, w·(u×v) = 0.
    Cũng không được. Lấy đường (1,1,1)+t(0,1,-1):
    u×v = (1,0,0)×(0,1,−1) = (0·(−1)−0·1, 0·0−1·(−1), 1·1−0·0) = (0,1,1)
    w = (1,1,1); w·(u×v) = 0+1+1 = 2; |u×v|² = 2
    d² = 4/2 = 2 ⇒ d = √2
    """
    return ({"A": Line3.through(V(0, 0, 0), V(1, 0, 0)),
             "B": Line3.through(V(1, 1, 1), V(1, 2, 0))},
            "A", "B", radical(1, 2))


def _hinh_duong_mat():
    """Đường ∥ mặt xiên. Mặt x+y=0, đường qua (1,0,5) phương (0,0,1).

    d² = (1+0)²/2 = 1/2 ⇒ d = √2/2
    """
    return ({"L": Line3.through(V(1, 0, 5), V(1, 0, 6)),
             "P": Plane3(V(0, 0, 0), V(1, 1, 0))},
            "L", "P", radical(F(1, 2), 2))


def _hinh_hai_mat():
    """Hai mặt ∥: x+y=0 và x+y=1. d² = 1/2 ⇒ d = √2/2."""
    return ({"A": Plane3(V(0, 0, 0), V(1, 1, 0)),
             "B": Plane3(V(1, 0, 0), V(1, 1, 0))},
            "A", "B", radical(F(1, 2), 2))


NAM_HINH = [
    pytest.param(_hinh_diem_duong, id="điểm–đường"),
    pytest.param(_hinh_diem_mat, id="điểm–mặt"),
    pytest.param(_hinh_hai_duong_cheo, id="đường–đường chéo"),
    pytest.param(_hinh_duong_mat, id="đường–mặt song song"),
    pytest.param(_hinh_hai_mat, id="mặt–mặt song song"),
]


# ══ ① ĐO ══════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_engine_do_ra_dung_can_thuc(dung_hinh):
    mem, of, wrt, mong = dung_hinh()
    d = _do(mem, of, wrt)
    assert d == mong, f"đo ra {d}, mong {mong}"
    assert isinstance(d, Radical), "ca này phải cho kết quả VÔ TỈ mới có nghĩa"


@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_binh_phuong_khop_kernel(dung_hinh):
    """Phép kiểm mạnh hơn so chuỗi, và không phụ thuộc cách viết: `d²` do miền
    số tính lại phải bằng `d²` do kernel tính trực tiếp."""
    mem, of, wrt, _ = dung_hinh()
    d = _do(mem, of, wrt)
    assert isinstance(square(d), Fraction)
    assert square(d) > 0


# ══ ② CHẤM ĐÚNG ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_PASS_khi_khai_dung(dung_hinh):
    """`witness` là CON SỐ chương trình đo ra; cổng tính lại từ hình rồi so."""
    mem, of, wrt, mong = dung_hinh()
    mem = {**mem, "d": mong}
    assert _cham(mem, _Ob(of, "d", wrt=wrt)) is None


@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_PASS_khi_de_mong_can_thuc_viet_bang_CHU(dung_hinh):
    """Văn phạm hẹp `§9`: đề khai `"sqrt(2)/2"` phải chấm được.

    Đây là chỗ DUY NHẤT căn thức đi VÀO hệ — và nó đi vào dưới dạng GIÁ TRỊ
    MONG ĐỢI, không phải toạ độ. Toạ độ vẫn ở trong ℚ³.
    """
    mem, of, wrt, mong = dung_hinh()
    tu, mau = mong.he.numerator, mong.he.denominator
    chu = f"{tu}*sqrt({mong.can})" + (f"/{mau}" if mau != 1 else "")
    assert _cham(mem, _Ob(of, wrt, value=chu)) is None, f"đề khai {chu}"


# ══ ③ CHẤM SAI ĐƯỢC — không có ca này thì ② vô nghĩa ═════════════════════
@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_FAIL_khi_khai_SAI_can_thuc(dung_hinh):
    """Đổi CĂN THỨC (giữ nguyên hệ số) — sai thật, phải bắt được."""
    mem, of, wrt, mong = dung_hinh()
    sai = radical(mong.he, mong.can + 1 if mong.can != 3 else 5)
    assert sai != mong
    mem = {**mem, "d": sai}
    loi = _cham(mem, _Ob(of, "d", wrt=wrt))
    assert loi is not None and "không khớp" in loi


@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_FAIL_khi_khai_SAI_he_so(dung_hinh):
    """Đổi HỆ SỐ (giữ nguyên căn thức) — ca hiểm hơn: `√2` với `2√2` cùng
    "hình dạng", và một bộ chấm chỉ nhìn căn thức sẽ cho qua."""
    mem, of, wrt, mong = dung_hinh()
    sai = radical(mong.he * 2, mong.can)
    mem = {**mem, "d": sai}
    assert _cham(mem, _Ob(of, "d", wrt=wrt)) is not None


@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_FAIL_khi_khai_HUU_TI_thay_vi_can(dung_hinh):
    """Làm tròn `√2/2` thành `7/10` phải bị bắt — đây là chính cái wave này
    tồn tại để không phải làm."""
    mem, of, wrt, _ = dung_hinh()
    mem = {**mem, "d": F(7, 10)}
    assert _cham(mem, _Ob(of, "d", wrt=wrt)) is not None


# ══ HỒI QUY HỮU TỈ (§17) ═════════════════════════════════════════════════
def test_khoang_cach_HUU_TI_van_la_Fraction_khong_thanh_can():
    """`d = 2` phải là `Fraction(2)`, KHÔNG phải `2·√1`.

    Nếu ca này đỏ, miền số đã nuốt luôn cả những kết quả vốn hữu tỉ — và mọi
    snapshot/hợp đồng cũ đọc `"2"` sẽ thấy một hình dạng khác.
    """
    mem = {"A": V(0, 0, 0), "B": V(2, 0, 0)}
    d = _do(mem, "A", "B")
    assert isinstance(d, Fraction) and d == 2
    assert not isinstance(d, Radical)


def test_checker_huu_ti_khong_hoi_quy():
    mem = {"A": V(0, 0, 0), "B": V(2, 0, 0), "d": F(2)}
    assert _cham(mem, _Ob("A", "d", wrt="B")) is None
    mem["d"] = F(3)
    assert _cham(mem, _Ob("A", "d", wrt="B")) is not None


# ══ ĐỐI XỨNG CỦA CỔNG CHẤM — bug ma trận này tìm ra ══════════════════════
@pytest.mark.parametrize("dung_hinh", NAM_HINH)
def test_checker_nhan_CA_HAI_thu_tu_doi_tuong(dung_hinh):
    """Khoảng cách đối xứng, nên cổng phải nhận cả hai thứ tự.

    Bản trước chỉ nhận `(mặt, điểm)` và `(đường, điểm)`. Một chương trình đo
    `distance(A, L)` — thứ tự engine chấp nhận bình thường — rơi xuống nhánh
    cuối và nhận *"cặp đối tượng không hợp lệ"*. Đó KHÔNG phải một phép kiểm bỏ
    sót mà là một phép kiểm SAI: chương trình đúng bị đánh trượt, và thông điệp
    đổ lỗi cho hình thay vì cho cổng.
    """
    mem, of, wrt, mong = dung_hinh()
    mem = {**mem, "d": mong}
    xuoi = _cham(mem, _Ob(of, "d", wrt=wrt))
    nguoc = _cham(mem, _Ob(wrt, "d", wrt=of))
    assert xuoi is None, f"thứ tự xuôi: {xuoi}"
    assert nguoc is None, f"thứ tự ngược: {nguoc}"
