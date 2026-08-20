# -*- coding: utf-8 -*-
"""Bất biến #33 — mọi primitive khai trong enum phải có nhánh adapter.

Sinh ra từ `bar_chart`: contract liệt kê nó trong `VisualContainerBinding.primitive`
nhưng `_adapt_single_step` không có nhánh nào, nên LLM khai `bar_chart` là ra
object rỗng — lỗi CÂM, không đỏ ở đâu.

Vá riêng một nhánh thì primitive kế tiếp lại rơi y hệt, nên luật là đối sánh
HAI CHIỀU: thiếu hay thừa đều ĐỎ.
"""
import typing

from app.simulation.semantic_program.contract import VisualContainerBinding
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter


def _declared() -> set[str]:
    return set(typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation))


def test_moi_primitive_deu_co_nhanh_xu_ly():
    missing = _declared() - VisualTraceAdapter.HANDLED_PRIMITIVES
    assert not missing, (
        f"Primitive khai trong contract nhưng adapter KHÔNG xử lý: {sorted(missing)} "
        "— LLM khai giá trị này sẽ ra object rỗng, lỗi câm."
    )


def test_khong_khai_thua_trong_adapter():
    extra = VisualTraceAdapter.HANDLED_PRIMITIVES - _declared()
    assert not extra, (
        f"Adapter xử lý primitive KHÔNG có trong contract: {sorted(extra)} "
        "— nhánh chết, hoặc contract đã bỏ giá trị mà adapter chưa dọn."
    )
