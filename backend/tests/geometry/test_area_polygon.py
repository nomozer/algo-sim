# -*- coding: utf-8 -*-
"""DIỆN TÍCH PHẲNG — **một** thẩm quyền toán học, chính xác tuyệt đối.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`CURRENT_ARCHITECTURE_GAP_AUDIT` tìm ra đúng một lỗ nằm ở **cả hai** tầng (IR
lẫn kernel): `area`. Chương trình Toán 11–12 hỏi diện tích thiết diện thường
xuyên, và hệ dựng được thiết diện chính xác rồi **không nói được nó rộng bao
nhiêu**.

─── ĐIỀU KHÓ NHẤT Ở ĐÂY KHÔNG PHẢI CÔNG THỨC ──────────────────────────────

Mà là **thứ tự phép toán**. Cộng diện tích từng tam giác thì mỗi hạng tử đã là
một căn, và `radical.add` từ chối tổng nhiều căn khác căn thức — tức cách làm
ấy hỏng ở đúng những đa giác thú vị nhất (`test_A2`, `test_A5`).

Cộng **các tích có hướng** trong ℚ³ trước rồi lấy căn ĐÚNG MỘT LẦN thì mọi đa
giác đều đo được. Nên `test_A2` và `test_A5` không phải hai ca ngẫu nhiên: nếu
ai đó "đơn giản hoá" `area_polygon` thành tổng các tam giác, hai ca ấy ĐỎ.

─── MỘT THẨM QUYỀN, KHÔNG BA ──────────────────────────────────────────────

Tam giác · tứ giác · thiết diện n cạnh là **cùng một bài toán**.
`test_MOT_tham_quyen_toan_hoc` khoá `area_section` ở lại vai adapter.
"""
from __future__ import annotations

import ast
import inspect
import textwrap
from fractions import Fraction

import pytest

from app.simulation.geometry import measure as M
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.measure import area_polygon, area_section
from app.simulation.geometry.radical import Radical, display, radical
from app.simulation.geometry.section import box, cross_section, pyramid_square

v = Vec3.of


# ══ A1 · HỮU TỈ ══════════════════════════════════════════════════════════
def test_A1_tam_giac_dien_tich_huu_ti():
    assert area_polygon([v(0, 0, 0), v(1, 0, 0), v(0, 1, 0)]) == Fraction(1, 2)


def test_A1b_hinh_vuong_canh_a():
    assert area_polygon([v(0, 0, 0), v(2, 0, 0), v(2, 2, 0), v(0, 2, 0)]) == 4


def test_A1c_tam_giac_lech_trong_khong_gian():
    """Đa giác không nằm trên mặt toạ độ nào — công thức vectơ không cần biết
    mặt phẳng chứa nó, và đó là lý do chọn nó thay vì chiếu xuống 2D."""
    assert area_polygon([v(1, 1, 1), v(3, 1, 1), v(1, 4, 1)]) == 3


# ══ A2 · VÔ TỈ ═══════════════════════════════════════════════════════════
def test_A2_dien_tich_vo_ti_van_CHINH_XAC():
    s = area_polygon([v(0, 0, 0), v(1, 0, 0), v(1, 1, 1), v(0, 1, 1)])
    assert s == radical(1, 2)
    assert display(s) == "√2"
    assert isinstance(s, Radical), "diện tích vô tỉ KHÔNG được rơi về float"


def test_A2b_khong_co_float_o_dau_trong_ket_qua():
    for d in ([v(0, 0, 0), v(1, 0, 0), v(0, 1, 0)],
              [v(0, 0, 0), v(1, 0, 0), v(1, 1, 1), v(0, 1, 1)],
              [v(0, 0, 0), v(3, 0, 0), v(3, 5, 0)]):
        s = area_polygon(d)
        assert isinstance(s, (Fraction, Radical))
        assert not isinstance(s, float)


# ══ A3–A4 · BẤT BIẾN HÌNH HỌC ════════════════════════════════════════════
def test_A3_dao_chieu_bien_KHONG_doi_dien_tich():
    """Diện tích phụ thuộc thứ tự biên **về dấu**, không về độ lớn — ta lấy
    chuẩn của tổng vectơ, nên chiều duyệt không đổi kết quả."""
    d = [v(0, 0, 0), v(1, 0, 0), v(1, 1, 1), v(0, 1, 1)]
    assert area_polygon(d) == area_polygon(list(reversed(d)))


def test_A3b_xoay_diem_bat_dau_KHONG_doi_dien_tich():
    d = [v(0, 0, 0), v(2, 0, 0), v(2, 2, 0), v(0, 2, 0)]
    for k in range(len(d)):
        assert area_polygon(d[k:] + d[:k]) == 4


def test_A4_tinh_tien_KHONG_doi_dien_tich():
    d = [v(0, 0, 0), v(1, 0, 0), v(1, 1, 1), v(0, 1, 1)]
    doi = v(7, -3, Fraction(1, 2))
    assert area_polygon([p + doi for p in d]) == area_polygon(d)


# ══ A5 · THIẾT DIỆN ══════════════════════════════════════════════════════
def test_A5_dien_tich_thiet_dien_luc_giac():
    """Mặt phẳng qua tâm hộp 2×2×2, pháp tuyến (1,1,1) ⇒ lục giác đều cạnh √2
    ⇒ `S = (3√3/2)·(√2)² = 3√3`. Ca này là lý do thứ tự phép toán phải đúng:
    sáu tam giác cộng lại sẽ vấp `radical.add`."""
    s = cross_section(box(2, 2, 2), Plane3(v(1, 1, 1), v(1, 1, 1)))
    assert len(s.polygon) == 6
    assert area_section(s) == radical(3, 3)
    assert display(area_section(s)) == "3√3"


def test_A5b_thiet_dien_tam_giac_cua_chop():
    s = cross_section(pyramid_square(2, 2), Plane3(v(0, 0, 1), v(0, 0, 1)))
    assert area_section(s) == area_polygon(s.polygon)


def test_A5c_area_section_TU_CHOI_vat_khong_phai_thiet_dien():
    with pytest.raises(GeometryError):
        area_section(object())


# ══ A6 · KHÔNG PHẲNG ═════════════════════════════════════════════════════
def test_A6_da_giac_KHONG_PHANG_bi_tu_choi():
    """Không chiếu xấp xỉ xuống một mặt phẳng nào cả. Với dãy điểm không phẳng
    công thức vẫn cho ra *một con số*, và con số ấy không phải diện tích của
    gì — đúng loại sai lặng lẽ mà kernel này được dựng để chặn."""
    with pytest.raises(GeometryError) as e:
        area_polygon([v(0, 0, 0), v(1, 0, 0), v(0, 1, 0), v(1, 1, 1)])
    assert "đồng phẳng" in str(e.value)


def test_A6b_dung_lai_tham_quyen_dong_phang_cua_kernel():
    """So BẰNG trên `Fraction`, không epsilon: lệch một phần triệu vẫn là
    không phẳng, và phải bị từ chối."""
    eps = Fraction(1, 10**6)
    with pytest.raises(GeometryError):
        area_polygon([v(0, 0, 0), v(1, 0, 0), v(1, 1, 0), v(0, 1, eps)])


# ══ A7 · SUY BIẾN ════════════════════════════════════════════════════════
def test_A7_ba_diem_thang_hang_cho_dien_tich_0():
    """0 là câu trả lời ĐÚNG, không phải một lỗi.

    Từ chối ở đây là đặt một luật thẩm định vào một phép ĐO — sai thẩm quyền.
    `exec_construct_polygon` là nơi quyết một dãy đỉnh có phải đa giác hợp lệ
    hay không, và nó cố ý không cấm thẳng hàng.
    """
    assert area_polygon([v(0, 0, 0), v(1, 0, 0), v(2, 0, 0)]) == 0
    assert area_polygon([v(0, 0, 0), v(1, 1, 1), v(3, 3, 3)]) == 0


@pytest.mark.parametrize("d", [[], [v(0, 0, 0)], [v(0, 0, 0), v(1, 0, 0)]])
def test_A7b_duoi_ba_dinh_bi_tu_choi(d):
    with pytest.raises(GeometryError):
        area_polygon(d)


# ══ A8 · MỘT THẨM QUYỀN ══════════════════════════════════════════════════
def test_A8_chu_trinh_giu_NGUYEN_thu_tu_cross_section_dung():
    """`area_section` không được sắp lại đỉnh theo một heuristic toạ độ — thứ
    tự `cross_section` dựng ra **là** biên của hình."""
    s = cross_section(box(2, 2, 2), Plane3(v(1, 1, 1), v(1, 1, 1)))
    assert area_section(s) == area_polygon(list(s.polygon))
    src = inspect.getsource(M.area_section)
    for cam in ("sort", "sorted", "canonical_cycle"):
        assert cam not in src, f"`area_section` tự sắp lại biên bằng {cam!r}"


def test_MOT_tham_quyen_toan_hoc():
    """`AREA_MATHEMATICAL_AUTHORITIES = 1`.

    `area_section` chỉ được uỷ quyền, không được tự tính. Viết
    `area_triangle`/`area_quad` riêng "vì đơn giản hơn" là dựng hai thẩm quyền
    cho một công thức, rồi chúng lệch nhau ở ca thứ ba.
    """
    assert "area_polygon" in inspect.getsource(M.area_section)
    ten_ham = [t for t in dir(M) if t.startswith("area")]
    assert sorted(ten_ham) == ["area_polygon", "area_section"], (
        f"có thẩm quyền diện tích thứ hai: {ten_ham}")
    # Thân của adapter phải NGẮN — dài ra nghĩa là nó đang tự làm toán. Đếm
    # CÂU LỆNH bằng `ast`, không đếm dòng: đếm dòng thì một docstring dài làm
    # cổng đỏ, và một cổng đỏ vì lý do sai sẽ bị nới cho xong.
    ham = ast.parse(textwrap.dedent(inspect.getsource(M.area_section))).body[0]
    cau_lenh = [n for n in ham.body
                if not (isinstance(n, ast.Expr)
                        and isinstance(n.value, ast.Constant))]
    assert len(cau_lenh) <= 3, (
        f"adapter `area_section` có {len(cau_lenh)} câu lệnh — nó đang tự làm "
        "toán thay vì uỷ quyền")
