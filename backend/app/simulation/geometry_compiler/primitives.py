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
from fractions import Fraction
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


def _so(x: Fraction) -> str:
    """Phân số → chuỗi IR. Số nguyên ra dạng nguyên; còn lại giữ `a/b`."""
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


# ══ PRIMITIVE ═══════════════════════════════════════════════════════════════
def declare_point(ten: str, xyz: tuple[Fraction, Fraction, Fraction]) -> dict[str, Any]:
    """Đặt một điểm tại toạ độ đã chọn.

    ⚠️ Toạ độ ở đây là `LAYOUT_DERIVED` — một lựa chọn TRÌNH BÀY của compiler,
    không phải dữ kiện đề. Việc gắn nhãn ấy thuộc `fact_graph`/`compiler`;
    primitive chỉ dựng câu lệnh.
    """
    return {"kind": "declare_point", "target_var": ten,
            "at": [_so(xyz[0]), _so(xyz[1]), _so(xyz[2])]}


def construct_triangle(ten: str, dinh: tuple[str, str, str],
                       nhan: str | None = None) -> dict[str, Any]:
    """Tam giác từ ba điểm ĐÃ CÓ TÊN. Dùng `construct_polygon` của IR."""
    st: dict[str, Any] = {"kind": "construct_polygon", "target_var": ten,
                          "vertices": list(dinh)}
    if nhan:
        st["label"] = nhan
    return st


def construct_pyramid(ten: str, dinh_chop: str, day: tuple[str, ...],
                      nhan: str | None = None) -> dict[str, Any]:
    """Khối chóp: đáy là đa giác, cộng một đỉnh.

    `faces` dựng TỔNG QUÁT theo số đỉnh đáy — không cố định bốn mặt, nên cùng
    primitive dùng được cho chóp tam giác, chóp tứ giác…
    """
    n = len(day)
    mat: list[list[str]] = [list(day)]
    for i in range(n):
        mat.append([dinh_chop, day[i], day[(i + 1) % n]])
    st: dict[str, Any] = {"kind": "construct_solid", "target_var": ten,
                          "vertices": [dinh_chop, *day], "faces": mat}
    if nhan:
        st["label"] = nhan
    return st


def construct_prism(
    name: str,
    base_cycle: tuple[str, ...],
    top_cycle: tuple[str, ...],
    correspondence: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    """Khối lăng trụ: hai đáy đa giác và các mặt bên nối các cặp đỉnh tương ứng.

    Dẫn xuất 5 mặt (cho lăng trụ tam giác) và trả về câu lệnh IR chuẩn `construct_solid`.
    """
    n = len(base_cycle)
    if n < 3:
        raise ValueError(f"Chu trình đáy phải có ít nhất 3 đỉnh (nhận {n})")
    if len(top_cycle) != n:
        raise ValueError(f"Số đỉnh đáy trên ({len(top_cycle)}) phải khớp số đỉnh đáy dưới ({n})")
    if len(set(base_cycle)) != n or len(set(top_cycle)) != n:
        raise ValueError("Chu trình đáy không được chứa đỉnh lặp")
    if set(base_cycle) & set(top_cycle):
        raise ValueError("Trùng đỉnh giữa chu trình đáy dưới và đáy trên")

    corr_dict = dict(correspondence)
    if len(corr_dict) != n or set(corr_dict.keys()) != set(base_cycle):
        raise ValueError("Correspondence không phải song ánh từ đáy dưới sang đáy trên")
    if set(corr_dict.values()) != set(top_cycle):
        raise ValueError("Ảnh của correspondence không khớp với các đỉnh đáy trên")

    mat: list[list[str]] = [list(base_cycle), list(top_cycle)]
    for i in range(n):
        u1 = base_cycle[i]
        u2 = base_cycle[(i + 1) % n]
        v1 = corr_dict[u1]
        v2 = corr_dict[u2]
        mat.append([u1, u2, v2, v1])

    dinh_tong = list(base_cycle) + list(top_cycle)
    return {
        "kind": "construct_solid",
        "target_var": name,
        "vertices": dinh_tong,
        "faces": mat,
    }


def measure_quantity(ten: str, quantity: str, of: str,
                     wrt: str | None = None) -> dict[str, Any]:
    """Một phép ĐO của IR.

    ⚠️ `measure` là một BIỂU THỨC (`MeasureExpr`), không phải câu lệnh — nên nó
    đi qua `assign`. Đây đúng là hình dạng các chương trình đã được nhận dùng;
    dựng một câu lệnh `kind="measure"` sẽ bị Pydantic bác ở tag union.

    `quantity` thuộc `BANG_PHEP_DO` — không mở rộng ở đây.
    """
    e: dict[str, Any] = {"kind": "measure", "quantity": quantity, "of": of}
    if wrt is not None:
        e["wrt"] = wrt
    return {"kind": "assign", "target_var": ten, "expr": e}


def assign_final_memory(ten: str, tu_bien: str) -> dict[str, Any]:
    """Ghi kết quả sang tên mà nghĩa vụ đang chờ (`witness`)."""
    return {"kind": "assign", "target_var": ten,
            "expr": {"kind": "var", "name": tu_bien}}


#: Kiểu bộ nhớ của một ĐẠI LƯỢNG đo được. `MemoryType` KHÔNG có `measure` —
#: các chương trình đã được nhận khai `float` cho witness của `volume`/`area`.
KIEU_DAI_LUONG = "float"


def memory_declaration(ten: str, kieu: str,
                       model_assumption: str | None = None,
                       provenance: str | None = None) -> dict[str, Any]:
    """Khai kiểu bộ nhớ.

    ⚠️ KHÔNG bao giờ có khoá `at` — `at` là khoá của `declare_point`; đặt nó
    vào đây là lỗi lược đồ đã đo được (`SYNTHESIS_MEMORY_DECLARATION_SCHEMA_
    PROMPT_ALIGNMENT`).

    `model_assumption` là kênh HỢP LỆ để khai *cách đặt* một vật đề đã nêu, khi
    toạ độ do bố cục chọn chứ không do đề cho. Cổng grounding nhận nó thay cho
    `source_fact_id` với `point3`/`vector3`, và CHỈ khi cái tên có thật trong đề.
    """
    d: dict[str, Any] = {"name": ten, "type": kieu}
    if model_assumption:
        d["model_assumption"] = model_assumption
    if provenance:
        d["provenance"] = provenance
    return d


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

