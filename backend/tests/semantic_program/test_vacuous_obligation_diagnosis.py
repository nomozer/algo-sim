# -*- coding: utf-8 -*-
"""NGHĨA VỤ VÔ HIỆU PHẢI ĐƯỢC GỌI ĐÚNG TÊN — không được báo như "đáp án sai".

─── SỰ CỐ ĐO ĐƯỢC (SEALED 7e5df014…, OFFICIAL Task 12) ────────────────────

`T11CS-C6-041` — đề: "n = 5; S = 0; for i in range(n+1): S = S + i. S bằng mấy?"

    nghĩa vụ LLM khai : aggregate_matching(container='day_so_cong', witness='s')
    bộ nhớ cuối       : {n: 5, s: 15, i: 5, day_so_cong: []}
    C₂ báo            : "witness 's' = 15, đúng phải là 0"
    oracle độc lập    : PASS — 15 LÀ đáp án đúng

Câu "đúng phải là 0" sinh ra vì `sum([]) == 0`. Nó đọc như *"đáp án 15 của bạn
sai, phải là 0"* — trong khi 15 đúng. Thứ sai là **nghĩa vụ**: chương trình khai
`s` là tổng của `day_so_cong`, rồi không bao giờ ghi gì vào `day_so_cong` và
tính `s` bằng cộng dồn vô hướng.

Vì sao LLM làm thế: taxonomy 9 nghĩa vụ đều **xoay quanh container**, không có
kind nào diễn đạt "vô hướng cộng dồn trên một khoảng số ngầm". Không có chỗ đúng
để khai, LLM nhét vào một container rồi bỏ trống. Cùng gốc với 6 case
`requested_operation_uncovered` ("kiểu 'int' không hợp với nghĩa vụ này").

─── PHẠM VI BẢN VÁ NÀY — HẸP CÓ CHỦ ĐÍCH ──────────────────────────────────

KHÔNG nới C₂ để case này qua. Nới ra thì một chương trình cộng SAI trên container
thật cũng lọt, tức phá đúng thứ C₂ sinh ra để giữ. `servable=False` ở đây vẫn là
phán quyết ĐÚNG.

Chỉ sửa **chẩn đoán**: container rỗng và chưa từng được ghi ⇒ nói "nghĩa vụ vô
hiệu", đừng suy ra một giá trị "đúng" từ tập rỗng rồi tố cáo witness.

`max/min` đã có nhánh rỗng riêng từ trước; `count/sum/product` thì chưa — đó
chính là khe hở. Sửa cho `membership` cùng lý do (`T11CS-C6-057` báo
"None phải có mặt" trên `day_so_a: []`).
"""
import pytest

from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.postconditions import CHECKERS


def _kiem(kind: str, snap: dict, **params) -> str | None:
    return CHECKERS[kind](snap, Obligation(kind=kind, container="c", params=params))


def _noi_vo_hieu(msg: str) -> bool:
    """Không khoá cách viết hoa/thường — luật là "phải gọi đúng tên vấn đề",
    không phải "phải viết đúng kiểu chữ này"."""
    return "vô hiệu" in msg.lower()


class TestContainerRongPhaiNoiLaNghiaVuVoHieu:
    @pytest.mark.parametrize("op", ["sum", "count", "product"])
    def test_khong_duoc_to_cao_witness_bang_gia_tri_suy_tu_tap_rong(self, op):
        """Đúng hình dạng T11CS-C6-041."""
        msg = _kiem("aggregate_matching", {"c": [], "w": 15}, op=op, witness="w")
        assert msg is not None, "Vẫn phải là vi phạm — không nới C₂"
        assert "đúng phải là" not in msg, (
            "Thông điệp đang suy một giá trị 'đúng' từ tập RỖNG rồi tố cáo "
            f"witness. Nhận được: {msg!r}"
        )
        assert _noi_vo_hieu(msg), f"Phải gọi đúng tên vấn đề. Nhận được: {msg!r}"
        assert "c" in msg, "Phải nêu container nào rỗng"

    def test_membership_tren_container_rong_cung_the(self):
        """Đúng hình dạng T11CS-C6-057."""
        msg = _kiem("membership", {"c": [], "w": None}, witness="w")
        assert msg is not None
        assert _noi_vo_hieu(msg), f"Nhận được: {msg!r}"


class TestKhongDuocNUOTMATViPhamTHAT:
    """Vế âm. Bỏ vế này thì bản vá biến thành 'container rỗng luôn được tha'."""

    def test_container_CO_du_lieu_ma_tong_sai_van_bi_bat(self):
        msg = _kiem("aggregate_matching", {"c": [1, 2, 3], "w": 99}, op="sum", witness="w")
        assert msg is not None
        assert "đúng phải là 6" in msg, f"Nhận được: {msg!r}"

    def test_container_CO_du_lieu_va_tong_dung_thi_qua(self):
        assert _kiem("aggregate_matching", {"c": [1, 2, 3], "w": 6}, op="sum", witness="w") is None

    def test_dem_dung_tren_container_co_du_lieu_thi_qua(self):
        assert _kiem("aggregate_matching", {"c": [1, 2, 3], "w": 3}, op="count", witness="w") is None

    def test_membership_tren_container_co_du_lieu_van_kiem_binh_thuong(self):
        """Có dữ liệu thì `membership` phải chạy luật cũ, không rẽ vào nhánh mới."""
        msg = _kiem("membership", {"c": [1, 2, 3], "w": 99}, witness="w")
        assert msg is not None
        assert not _noi_vo_hieu(msg), f"Nhánh rỗng ăn nhầm case có dữ liệu: {msg!r}"
