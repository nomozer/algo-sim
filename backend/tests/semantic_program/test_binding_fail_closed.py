# -*- coding: utf-8 -*-
"""Bất biến #34 — binding bắt buộc không phân giải được thì KHÔNG phát envelope.

Luật KHÔNG phải "bỏ con trỏ rồi vẫn vẽ phần còn lại" — đó là hạ cấp âm thầm,
đúng loại lỗi ở spec §0(b) (con trỏ `i` neo vào container rỗng nên đè lên dòng
thuyết minh).

Vì sao kiểm ở tầng adapter chứ không ở validator tĩnh: `validator.py` có hai
nhánh `pass` tự khai cho `var_ref` của pointer/value_box, vì một `var_ref` hợp
lệ có thể là `loop_var` — thứ không nằm trong bảng ký hiệu tĩnh. Chỉ sau khi
CHẠY mới biết nó có bao giờ phân giải hay không.
"""
import pytest

from app.simulation.semantic_program.contract import (
    AssignStmt,
    LiteralExpr,
    MemoryDeclaration,
    SemanticProgramSpec,
    VisualBindings,
    VisualContainerBinding,
    VisualPointerBinding,
    VisualValueBoxBinding,
)
from app.simulation.semantic_program.pipeline_adapter import (
    VisualBindingUnresolved,
    compile_semantic_program_to_envelope,
)

_DECLS = [
    MemoryDeclaration(name="a", type="array", element_type="int", initial_value=[1, 2, 3]),
    MemoryDeclaration(name="i", type="int", initial_value=0),
]
_CONTAINERS = [VisualContainerBinding(semantic_id="a", primitive="array_strip", label="Dãy")]


def _spec(pointers=None, boxes=None) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        title="Kiểm tra neo hỏng",
        memory_declarations=list(_DECLS),
        statements=[AssignStmt(target_var="i", expr=LiteralExpr(value=0))],
        visual_bindings=VisualBindings(
            containers=list(_CONTAINERS),
            pointers=pointers or [],
            value_boxes=boxes or [],
        ),
    )


def test_con_tro_khong_bao_gio_phan_giai_thi_khong_phat_envelope():
    spec = _spec(
        pointers=[
            VisualPointerBinding(
                pointer_id="p_ghost",
                var_ref="bien_khong_ton_tai",
                target_container="a",
                label="k",
            )
        ]
    )
    with pytest.raises(VisualBindingUnresolved) as e:
        compile_semantic_program_to_envelope(spec)
    assert "p_ghost" in str(e.value)


def test_value_box_ma_cung_bi_chan():
    spec = _spec(
        boxes=[
            VisualValueBoxBinding(
                box_id="box_ghost", var_ref="cung_khong_ton_tai", label="Kết quả"
            )
        ]
    )
    with pytest.raises(VisualBindingUnresolved):
        compile_semantic_program_to_envelope(spec)


def test_binding_phan_giai_duoc_thi_qua_binh_thuong():
    spec = _spec(
        pointers=[
            VisualPointerBinding(
                pointer_id="p_i", var_ref="i", target_container="a", label="i"
            )
        ]
    )
    env = compile_semantic_program_to_envelope(spec)
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.semantic_program"
