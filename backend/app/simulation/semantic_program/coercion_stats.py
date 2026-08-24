# -*- coding: utf-8 -*-
"""Đếm số lần BIÊN CHUẨN HOÁ phải ra tay — `contract.py` gộp cách viết bao nhiêu lần.

VÌ SAO TỒN TẠI: ba biên chuẩn hoá ở `contract.py` (`canonical_spec_version`,
`canonical_container_name`, `canonical_condition`) đều sinh ra từ cùng một quan
sát — LLM viết đúng nghĩa, sai cách viết, và fail-closed ở tầng cú pháp che mất
năng lực ngữ nghĩa thật. Chúng đã cứu được rất nhiều case. Nhưng chính vì thế
mà chúng nguy hiểm: một khi đã gộp, **không còn ai biết chúng gộp bao nhiêu
lần**, và một biên gộp im lặng thì không phân biệt được hai tình huống trái
ngược nhau:

  (a) mô hình thỉnh thoảng viết dạng khác — biên làm đúng việc của nó;
  (b) mô hình LUÔN viết dạng khác — hợp đồng đang mô tả sai thứ mô hình
      thật sự phát, và chỗ phải sửa là prompt/thẻ văn phạm, không phải thêm
      một lớp gộp nữa.

Phân biệt (a) với (b) chỉ cần một con số: tỉ lệ lượt phải gộp. Cao và dai dẳng
là dấu hiệu (b) — nói theo tài liệu vận hành LLM: *coercion rate* cao báo hiệu
mô hình đã hình thành thói quen định dạng khác hợp đồng, và phải chữa ở bề mặt
sinh trước khi nó thành một phụ thuộc vĩnh viễn vào lớp sửa.

CÙNG KHUÔN VỚI `app/ai/telemetry.py`, CỐ Ý KHÔNG DÙNG LẠI NÓ: telemetry ấy đếm
`usageMetadata` theo stage Gemini và thuộc tầng `app.ai`. `contract.py` nằm sâu
trong `app.simulation` và **không được** phụ thuộc ngược lên tầng AI — hướng phụ
thuộc đó là bất biến kiến trúc, không phải sở thích. Bộ đếm ở đây vì thế là bản
nhỏ, độc lập, 0 import chéo tầng.

KHÔNG BAO GIỜ ĐƯỢC NÉM LỖI. Quan trắc mà giết được một lượt phân tích thì nó
đang trả giá đắt hơn thứ nó đo — cùng luật đã viết trong `telemetry.py`.
"""
from __future__ import annotations

from collections import Counter

#: Bốn lớp gộp, ĐÓNG. Thêm một biên chuẩn hoá ở `contract.py` thì thêm khoá ở
#: đây — khoá bởi
#: `test_coercion_stats.py::test_bon_lop_khop_voi_so_bien_chuan_hoa_trong_contract`,
#: và cái khoá ấy đếm bằng cách soi chính `contract.py` chứ không chép tay.
LOP_SPEC_VERSION = "spec_version_so_thanh_chuoi"
LOP_CONTAINER_REF = "container_var_thanh_ten"
LOP_CONDITION_BOOL = "bien_bool_thanh_menh_de"
LOP_CONST_INT = "step_literal_thanh_so_tran"

LOP_HOP_LE: frozenset[str] = frozenset(
    {LOP_SPEC_VERSION, LOP_CONTAINER_REF, LOP_CONDITION_BOOL, LOP_CONST_INT}
)

_dem: Counter[str] = Counter()


def ghi_coercion(lop: str) -> None:
    """Cộng một lượt gộp. Lớp lạ bị bỏ qua im lặng — xem luật không-ném-lỗi."""
    if lop in LOP_HOP_LE:
        _dem[lop] += 1


def reset_coercion() -> None:
    """Xoá bộ đếm. Gọi ở ĐẦU mỗi case, và trong test."""
    _dem.clear()


def coercion_report() -> dict[str, int]:
    """Bản chụp bộ đếm — mọi lớp đều có mặt, kể cả lớp chưa nổ lần nào.

    Có mặt-với-0 là cố ý: một lớp vắng khỏi báo cáo không phân biệt được
    'chưa nổ lần nào' với 'quên gắn bộ đếm vào biên đó'.
    """
    return {lop: _dem.get(lop, 0) for lop in sorted(LOP_HOP_LE)}


def tong_coercion() -> int:
    """Tổng số lượt gộp — một con số để so nhanh giữa hai lượt đo."""
    return sum(_dem.values())
