# -*- coding: utf-8 -*-
"""BỘ TẠO CÂU LỆNH IR — hàm thuần dựng dict câu lệnh/khai báo của `SemanticProgramSpec` HIỆN CÓ.

Dời nguyên văn từ `primitives.py` của gói compiler họ-bài (run `ai-function-route`): hai bộ phát IR dùng chung chúng —
compiler họ-bài (re-export ở `primitives.py`, `REGISTRY` của nó không đổi) và engine lời gọi hàm (`geometry_functions`).
Đặt ở gói IR để engine mới không phải nhập gói compiler (mà `__init__` của gói ấy kéo theo compiler, FactGraph,
adapter) — bất biến "ngoài gói compiler không tệp sản phẩm nào nhắc tới nó" giữ nguyên, không ngoại lệ. Luật cũ giữ nguyên: không biết `case_id`, không đọc văn bản đề, không gọi provider,
nhãn điểm là THAM SỐ, không hằng số của một bài.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any


def _so(x: Fraction) -> str:
    """Phân số → chuỗi IR. Số nguyên ra dạng nguyên; còn lại giữ `a/b`."""
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


# ══ PRIMITIVE ═══════════════════════════════════════════════════════════════
def declare_point(ten: str, xyz: tuple[Fraction, Fraction, Fraction],
                  nhan: str | None = None) -> dict[str, Any]:
    """Đặt một điểm tại toạ độ đã chọn.

    ⚠️ Toạ độ ở đây là `LAYOUT_DERIVED` — một lựa chọn TRÌNH BÀY của compiler,
    không phải dữ kiện đề. Việc gắn nhãn ấy thuộc `fact_graph`/`compiler`;
    primitive chỉ dựng câu lệnh.
    """
    st: dict[str, Any] = {"kind": "declare_point", "target_var": ten,
                          "at": [_so(xyz[0]), _so(xyz[1]), _so(xyz[2])]}
    if nhan:
        st["label"] = nhan
    return st


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


def construct_polygon(ten: str, dinh: tuple[str, ...],
                      nhan: str | None = None) -> dict[str, Any]:
    """Đa giác từ các điểm ĐÃ CÓ TÊN. Dùng `construct_polygon` của IR."""
    st: dict[str, Any] = {"kind": "construct_polygon", "target_var": ten,
                          "vertices": list(dinh)}
    if nhan:
        st["label"] = nhan
    return st


def construct_line(ten: str, diem_dau: str, diem_cuoi: str,
                   nhan: str | None = None) -> dict[str, Any]:
    """Đường thẳng qua hai điểm ĐÃ CÓ TÊN (VÔ HẠN). Dùng `construct_line` của IR."""
    st: dict[str, Any] = {"kind": "construct_line", "target_var": ten,
                          "through_a": diem_dau, "through_b": diem_cuoi}
    if nhan:
        st["label"] = nhan
    return st


def vector_from_points(ten: str, tu_diem: str, toi_diem: str) -> dict[str, Any]:
    """Vectơ CÓ HƯỚNG giữa hai điểm ĐÃ CÓ TÊN. Kernel tính, compiler không chép toạ độ."""
    return {"kind": "assign", "target_var": ten,
            "expr": {"kind": "vector_from_points", "from_point": tu_diem, "to_point": toi_diem}}


def translate_point(ten: str, diem: str, vecto: str,
                    nhan: str | None = None) -> dict[str, Any]:
    """Điểm `diem + vecto` — dựng bằng phép `translate` của IR (lăng trụ: đáy trên là ảnh tịnh tiến của đáy dưới)."""
    st: dict[str, Any] = {"kind": "construct_point", "target_var": ten,
                          "expr": {"kind": "translate", "point": diem, "vector": vecto}}
    if nhan:
        st["label"] = nhan
    return st


def memory_declaration(ten: str, kieu: str,
                       model_assumption: str | None = None,
                       provenance: str | None = None,
                       source_fact_id: str | None = None,
                       initial_value: Any = None) -> dict[str, Any]:
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
    if source_fact_id:
        d["source_fact_id"] = source_fact_id
    if initial_value is not None:
        d["initial_value"] = initial_value
    return d
