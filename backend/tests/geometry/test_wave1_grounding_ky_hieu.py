# -*- coding: utf-8 -*-
"""WAVE 1 sau Phase 7B — đồng nhất KÝ HIỆU PHẨY và grounding.

Phase 7B chính thức xếp 6 lượt vào `B_grounding`. Wave này không dùng đề hay
chương trình của lượt ấy làm đầu vào; nó dò **tầng tất định** bằng ký hiệu
DEV tự soạn, và tầng ấy hỏng thấy được ngay.

─── NGUYÊN NHÂN GỐC ──────────────────────────────────────────────────────

`geometry_symbol_key("A'")` trả `None`. Dấu **phẩy** — cách viết phổ biến
nhất của hình học không gian THPT (`ABCD.A'B'C'D'`, có ở SGK cả ba bộ) —
không được nhận là ký hiệu hình học. Hàm bỏ `_` và `-` rồi đòi phần còn lại
`isalnum()`; `'` rớt cả hai vế.

Hệ quả dây chuyền: `khop_ky_hieu` không bao giờ nối được `A'` của hợp đồng
với biến nào của chương trình, nên nghĩa vụ mang witness `A'` **không có
đường nào** thoả — kể cả khi chương trình dựng đúng điểm ấy dưới tên `A1`.

Bốn cách viết cùng một điểm, đo được ở lượt sinh thật: `A'` (SGK) · `A1`
(mô hình hay hạ dấu phẩy thành chỉ số) · `A_prime` · `Aprime`.

─── VÌ SAO GỘP CHÚNG LÀ AN TOÀN ──────────────────────────────────────────

`khop_ky_hieu` đã fail-closed sẵn: **trùng khoá ⇒ trả `None`**. Nên nếu một
chương trình khai CẢ `A'` LẪN `A1` như hai điểm khác nhau, phép gộp làm hai
tên đụng khoá và cổng từ chối — đúng hành vi cần, không phải đoán bừa.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.domain_profile import (
    geometry_symbol_key,
    khop_ky_hieu,
)


@pytest.mark.parametrize("ten,khoa", [
    ("A'", "A1"), ("B'", "B1"), ("C′", "C1"),        # cả phẩy ASCII lẫn U+2032
    ("A_prime", "A1"), ("Aprime", "A1"),
    ("A1", "A1"), ("A_1", "A1"),
    ("point_A'", "A1"), ("diem_B'", "B1"),
])
def test_ky_hieu_PHAY_dong_nhat_voi_chi_so_1(ten, khoa):
    assert geometry_symbol_key(ten) == khoa, ten


@pytest.mark.parametrize("ten", ["A", "M", "S", "O", "AB", "M12"])
def test_ky_hieu_THUONG_khong_doi(ten):
    """Phép sửa không được đụng tới ký hiệu không có phẩy."""
    assert geometry_symbol_key(ten) == ten.upper()


@pytest.mark.parametrize("ten", ["volume", "abcd", "distance", "", "  "])
def test_thu_KHONG_phai_ky_hieu_van_bi_tu_choi(ten):
    """Ranh giới ≤3 ký tự phải giữ: `volume` không bao giờ được thành ký hiệu,
    nếu không quy tắc này biến thành so-không-phân-biệt-hoa-thường toàn cục."""
    assert geometry_symbol_key(ten) is None


def test_hop_dong_PHAY_khop_duoc_chuong_trinh_CHI_SO():
    """Đúng ca hỏng: SGK viết `A'`, mô hình sinh `A1`."""
    assert khop_ky_hieu("A'", {"A1", "B1", "C1"}) == "A1"
    assert khop_ky_hieu("A1", {"A'", "B'"}) == "A'"
    assert khop_ky_hieu("A'", {"A_prime", "B"}) == "A_prime"


def test_MO_HO_thi_TU_CHOI_chu_khong_doan():
    """Chương trình khai cả `A'` lẫn `A1` ⇒ trùng khoá ⇒ không khớp.

    Đây là thứ làm phép gộp an toàn: nó không bao giờ *chọn* giữa hai ứng
    viên, nó chỉ nối khi có đúng một.
    """
    assert khop_ky_hieu("A'", {"A'", "A1"}) is None
    assert khop_ky_hieu("A1", {"A_prime", "A1"}) is None


def test_khong_gop_nham_hai_DIEM_KHAC_NHAU():
    """`A'` ≢ `B1`, và `A'` ≢ `A2`. Gộp phải theo CHỮ CÁI + bậc, không phải
    'có phẩy thì giống nhau hết'."""
    assert geometry_symbol_key("A'") != geometry_symbol_key("B'")
    assert geometry_symbol_key("A'") != geometry_symbol_key("A2")
    assert khop_ky_hieu("A'", {"B1", "C1"}) is None


# ══ GROUNDING: nghĩa vụ mang witness PHẨY phải nối được ═══════════════════
def test_grounding_noi_duoc_witness_PHAY_voi_bien_CHI_SO():
    """Chuỗi thật, tất định, 0 API call: hợp đồng đòi `A'`, chương trình khai
    `A1`. Trước phép sửa, không đường nào nối được."""
    from app.simulation.semantic_program.contract import (
        MemoryDeclaration, SemanticProgramSpec,
    )
    spec = SemanticProgramSpec(
        title="hình lập phương DEV",
        memory_declarations=[
            MemoryDeclaration(name="A1", type="point3",
                              initial_value=[0, 0, 1],
                              model_assumption="đặt hệ trục tại A"),
        ],
        statements=[],
    )
    ten = {d.name for d in spec.memory_declarations}
    assert khop_ky_hieu("A'", ten) == "A1", (
        "witness `A'` của hợp đồng không nối được biến `A1` của chương trình")
