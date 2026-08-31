# -*- coding: utf-8 -*-
"""BỀ MẶT MÔ HÌNH THẤY ⊆ THỨ SCHEMA NHẬN. 0 API call.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`fresh-probe fp_6` yêu cầu *"chứng minh BD vuông góc với (SAC)"*. Mô hình phát

    {"kind": "perpendicular", ...}

ở **cả hai** lượt rồi hết ngân sách. Nó không bịa: prompt có một bảng liệt kê
`parallel`, `perpendicular`, `coplanar`, `point_on_line` dưới cột *"Nghĩa vụ"*
kèm cột *"witness"*. Nhưng `SemanticProgramSpec` **không có trường
`obligations`**, và không `kind` nào trong `ValueExpr`/`SemanticStatement` mang
những tên ấy. Nghĩa vụ do `analyze` sinh ở phía HỢP ĐỒNG; mô hình tổng hợp
không có ô nào để viết chúng vào.

Bảng ấy dạy một từ vựng không tồn tại — cùng lớp lỗi với nhãn
`construct_plane.through` từng nói *"[x,y,z]"* cho một trường nhận TÊN. Cả hai
đều là: **nhãn sai của TA đẻ ra lỗi của NÓ.**

─── MỤC TIÊU ──────────────────────────────────────────────────────────────

    PROMPT_ADVERTISES_NONEXISTENT_IR = impossible

Test này quét bề mặt mô hình THẬT SỰ nhận — file skill + thẻ văn phạm — và đòi
mọi định danh trông-như-IR trong đó phải tồn tại ở schema. Quét văn bản, không
quét ý định: một bảng markdown mới thêm vào prompt cũng bị soi.
"""
from __future__ import annotations

import re
import typing
from pathlib import Path

import pytest

from app.ai.gemini import load_skill
from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.grammar_card import grammar_card
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    quantity_trong_contract,
)

_SKILL = "geometry_program_generator"


def _tap_kind(alias) -> set[str]:
    ra = set()
    for arg in typing.get_args(typing.get_args(alias)[0]):
        m = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        f = getattr(m, "model_fields", {}).get("kind")
        if f is not None:
            ra.add(f.default)
    return ra


def _moi_dinh_danh_IR() -> set[str]:
    """Mọi thứ mô hình ĐƯỢC PHÉP viết: kind, tên trường, giá trị enum."""
    ra: set[str] = set()
    ra |= _tap_kind(C.SemanticStatement)
    ra |= _tap_kind(C.ValueExpr)
    ra |= _tap_kind(C.ConditionExpr)
    ra |= set(typing.get_args(C.MemoryType))
    ra |= set(quantity_trong_contract())
    for m in (C.SemanticProgramSpec, C.MemoryDeclaration,
              C.VisualContainerBinding, C.VisualPointerBinding,
              C.VisualValueBoxBinding):
        ra |= set(m.model_fields)
    for k in _tap_kind(C.SemanticStatement) | _tap_kind(C.ValueExpr):
        pass
    # Trường của TỪNG câu lệnh/biểu thức, không chỉ của đối tượng gốc.
    for alias in (C.SemanticStatement, C.ValueExpr, C.ConditionExpr):
        for arg in typing.get_args(typing.get_args(alias)[0]):
            m = typing.get_args(arg)[0] if typing.get_args(arg) else arg
            ra |= set(getattr(m, "model_fields", {}))
    return ra


#: Định danh xuất hiện trong prompt/thẻ mà KHÔNG phải từ vựng IR — tên module,
#: tên hàm nội bộ, thuật ngữ. Danh sách này chỉ được NGẮN ĐI: mỗi mục là một
#: chỗ prompt nói bằng ngôn ngữ của ta thay vì ngôn ngữ mô hình phát ra được.
_KHONG_PHAI_IR = frozenset({
    "semantic_program", "variables", "program",  # tên bị CẤM, nêu để cấm
    "sqrt", "json",
})


def _dinh_danh_trong(van: str) -> set[str]:
    """Chuỗi trong dấu backtick trông như một định danh IR.

    Chỉ soi trong backtick: văn xuôi tiếng Việt có `mặt phẳng`, `hình chóp`…
    và soi cả chúng thì test biến thành một bộ kiểm chính tả.
    """
    ra = set()
    for m in re.finditer(r"`([a-z][a-z0-9_.]{2,})`", van):
        t = m.group(1)
        if "." in t:          # `measure.quantity` → lấy cả hai vế
            ra |= set(t.split("."))
        else:
            ra.add(t)
    return {t for t in ra if t and t not in _KHONG_PHAI_IR}


# ══ ① BỀ MẶT MÔ HÌNH ⊆ SCHEMA ═══════════════════════════════════════════
@pytest.mark.parametrize("nguon", ["skill", "the"])
def test_prompt_khong_quang_cao_thu_schema_KHONG_CO(nguon):
    van = (load_skill(_SKILL) if nguon == "skill"
           else grammar_card("hinh_hoc"))
    hop_le = _moi_dinh_danh_IR()
    la = _dinh_danh_trong(van) - hop_le
    assert not la, (
        f"prompt/thẻ ({nguon}) quảng cáo định danh KHÔNG có trong schema: "
        f"{sorted(la)}. Mô hình sẽ cố phát chúng rồi bị từ chối — đúng cách "
        "`fp_6` đốt cả hai lượt vì `perpendicular`.")


@pytest.mark.parametrize("tu", ["perpendicular", "parallel", "coplanar",
                                "point_on_line", "point_on_plane",
                                "obligations", "witness"])
def test_TU_VUNG_NGHIA_VU_da_bien_khoi_be_mat_tong_hop(tu):
    """Từ vựng nghĩa vụ thuộc phía HỢP ĐỒNG (`analyze`), không phải phía
    chương trình. Nêu nó ở prompt tổng hợp là mời mô hình phát một thứ không
    có ô để nhận."""
    van = load_skill(_SKILL) + grammar_card("hinh_hoc")
    assert tu not in van, (
        f"bề mặt tổng hợp còn nhắc `{tu}` — mô hình không có cách nào phát nó")


def test_schema_THAT_SU_khong_co_truong_obligations():
    """Neo cho hai test trên: nếu mai schema CÓ trường ấy thì chúng phải được
    xem lại, chứ không im lặng tiếp tục cấm."""
    assert "obligations" not in C.SemanticProgramSpec.model_fields
    assert "perpendicular" not in _tap_kind(C.ValueExpr)
    assert "perpendicular" not in _tap_kind(C.SemanticStatement)


# ══ ② CHIỀU NGƯỢC — mọi phép đo canonical phải có chữ ký thật ═══════════
def test_moi_phep_do_trong_bang_deu_co_trong_schema():
    assert set(BANG_PHEP_DO) <= set(quantity_trong_contract())


def test_moi_kieu_toan_hang_deu_la_MemoryType_hop_le():
    hop_le = set(typing.get_args(C.MemoryType))
    for q, p in BANG_PHEP_DO.items():
        for k in set(p.kieu_of) | set(p.kieu_wrt):
            assert k in hop_le, f"`{q}` khai kiểu '{k}' ngoài MemoryType"


def test_the_hinh_hoc_khong_bo_sot_phep_do_nao():
    """Ngược lại chiều ①: bảng có mà thẻ không nói thì mô hình không biết dùng."""
    the = grammar_card("hinh_hoc")
    for q in BANG_PHEP_DO:
        assert q in the, f"`{q}` có trong bảng nhưng KHÔNG tới tay mô hình"


# ══ ③ PROMPT KHÔNG ĐƯỢC NHẮC LẠI THỨ THẺ ĐÃ NÓI ════════════════════════
def test_prompt_khong_chep_lai_bang_kieu_cua_the():
    """Hai bản của cùng một bảng kiểu sẽ trôi. Thẻ là bản sinh ra từ thẩm
    quyền; prompt chỉ được TRỎ tới nó."""
    van = load_skill(_SKILL)
    assert "of:point3" not in van and "of:vector3" not in van, (
        "prompt chép lại chữ ký kiểu — để thẻ nói, prompt trỏ")
