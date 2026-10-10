# -*- coding: utf-8 -*-
"""REGISTRY PRIMITIVE — khối dựng TỔNG QUÁT, biên dịch về IR hiện có.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

Mỗi primitive nhận đối số CÓ KIỂU và trả về các câu lệnh của
`SemanticProgramSpec` **đang tồn tại** — không DSL thứ hai, không scene builder
thứ hai. Đó là lý do đầu ra của compiler đi lọt nguyên bộ cổng hiện có mà không
phải nới một cổng nào.

LUẬT CỦA REGISTRY, và chúng là thứ `test_L`/`test_M` khoá lại:

  · primitive KHÔNG biết `case_id`;
  · primitive KHÔNG đọc `problem_text` hay bất kỳ văn bản thô nào;
  · primitive KHÔNG gọi provider;
  · primitive KHÔNG nhận nhãn điểm cố định — nhãn là THAM SỐ;
  · primitive KHÔNG chứa hằng số của một bài cụ thể;
  · một primitive dùng lại được ở nhiều họ bài.

Nên KHÔNG có `solve_C01()`, `build_SABC_3_4_5()`, `return_answer_10()`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PRIMITIVE_REGISTRY_VERSION = "geometry-primitives/1"


@dataclass(frozen=True)
class LoiGoiPrimitive:
    """Một lượt gọi primitive — dạng RÚT GỌN để ghi vào trace.

    Chỉ chở tên primitive, số đối số và ID fact liên quan. KHÔNG chở toạ độ,
    KHÔNG chở giá trị đo, KHÔNG chở nguyên văn.
    """

    primitive_id: str
    arg_count: int
    source_fact_ids: tuple[str, ...] = ()
    derived_fact_ids: tuple[str, ...] = ()


# Bộ tạo câu lệnh IR sống ở gói IR (run ai-function-route); re-export để mọi chỗ gọi `P.<hàm>` giữ nguyên.
from app.simulation.semantic_program.ir_builders import (  # noqa: F401
    _so,
    declare_point,
    construct_triangle,
    construct_pyramid,
    construct_prism,
    measure_quantity,
    assign_final_memory,
    KIEU_DAI_LUONG,
    construct_polygon,
    construct_line,
    vector_from_points,
    translate_point,
    memory_declaration,
)


#: Bảng primitive ĐÓNG của lát cắt. Khoá là `primitive_id` ổn định.
REGISTRY: dict[str, Any] = {
    "declare_point": declare_point,
    "construct_triangle": construct_triangle,
    "construct_pyramid": construct_pyramid,
    "construct_prism": construct_prism,
    "measure_quantity": measure_quantity,
    "assign_final_memory": assign_final_memory,
    "memory_declaration": memory_declaration,
}


def danh_tinh_registry() -> dict[str, Any]:
    return {"version": PRIMITIVE_REGISTRY_VERSION,
            "primitives": sorted(REGISTRY)}

