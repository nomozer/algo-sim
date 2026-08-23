# -*- coding: utf-8 -*-
"""Biên chuẩn hoá ĐIỀU KIỆN — `hop_le` và `hop_le == true` là MỘT mệnh đề.

─── SỰ CỐ ĐO ĐƯỢC (probe E2E sản phẩm, 2026-08-23) ────────────────────────

Đề *"Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng ngăn xếp Stack với chuỗi
{[()]}"*, chạy qua `run_pipeline` thật với `semantic_route="serve"`:

    statements.2.if.condition.logic.left
      Input tag 'var' found using 'kind' does not match any of the expected
      tags: 'compare', 'logic', 'not', 'is_empty', 'contains', 'is_null'
      input_value={'kind': 'var', 'name': 'hop_le'}

LLM viết `if hop_le and ...` — cách mọi ngôn ngữ học sinh từng thấy đều cho
viết. Union điều kiện chỉ nhận sáu dạng mệnh đề, nên cả chương trình bị vứt vì
một khác biệt KÝ PHÁP, trước khi một chữ nào về ngữ nghĩa được xét.

Đây là lớp lỗi thứ tư cùng họ trên cùng một đề — sau `container: {"kind":"var"}`,
`container: {"kind":"literal"}` và `pop` dùng như biểu thức. Tất cả đều là *model
viết dạng tự nhiên, IR đòi dạng khác*.

─── LUẬT, VÀ VẾ THỨ HAI KHÔNG ĐƯỢC BỎ ────────────────────────────────────

Gấp `x` thành `x == true` chỉ là gộp hai cách viết của MỘT mệnh đề — cùng họ với
`canonical_container_name`, KHÔNG nới ngữ nghĩa.

Vế thứ hai: chỉ gấp những dạng **có thể mang giá trị đúng/sai** (`var`, `field`,
`index`, `map_get`, `literal`). `arith`/`length`/`neighbors` vẫn phải bị từ chối
— `2+3` làm điều kiện là lỗi kiểu THẬT, và im lặng bọc nó thành `2+3 == true`
chỉ đẩy lỗi xuống sâu hơn với thông báo khó hiểu hơn. Nới lỏng KÝ PHÁP không
được biến thành nới lỏng KIỂU.
"""
import pytest
from pydantic import ValidationError

from app.simulation.semantic_program.contract import (
    IfStmt,
    LogicCond,
    NotCond,
    canonical_condition,
)

TRUE_LIT = {"kind": "literal", "value": True}


def _var(ten: str) -> dict:
    return {"kind": "var", "name": ten}


# ── 1. Gấp đúng: biến bool dùng thẳng làm điều kiện ────────────────────────
@pytest.mark.parametrize(
    "tho",
    [
        {"kind": "var", "name": "hop_le"},
        {"kind": "field", "obj": {"kind": "var", "name": "nut"}, "field": "val"},
        {"kind": "map_get", "container": "bang", "key": {"kind": "literal", "value": "a"}},
        {"kind": "literal", "value": True},
    ],
)
def test_dang_mang_bool_duoc_gap_thanh_so_sanh_voi_true(tho):
    ra = canonical_condition(tho)
    assert ra["kind"] == "compare"
    assert ra["op"] == "=="
    assert ra["left"] == tho
    assert ra["right"] == TRUE_LIT


def test_gap_trong_logic_that_su_qua_duoc_pydantic():
    """Đúng hình dạng đã giết chương trình trong probe E2E."""
    c = LogicCond.model_validate(
        {
            "kind": "logic",
            "op": "and",
            "left": _var("hop_le"),
            "right": {"kind": "is_empty", "container": "ngan_xep"},
        }
    )
    assert c.left.kind == "compare"
    assert c.left.left.name == "hop_le"
    assert c.left.right.value is True


def test_gap_trong_not_va_trong_if():
    n = NotCond.model_validate({"kind": "not", "expr": _var("da_gap")})
    assert n.expr.kind == "compare"

    s = IfStmt.model_validate(
        {
            "kind": "if",
            "condition": _var("hop_le"),
            "then_body": [],
            "else_body": [],
        }
    )
    assert s.condition.kind == "compare"


# ── 2. Vế thứ hai: KHÔNG nới kiểu ─────────────────────────────────────────
@pytest.mark.parametrize(
    "tho",
    [
        {
            "kind": "arith",
            "op": "+",
            "left": {"kind": "literal", "value": 1},
            "right": {"kind": "literal", "value": 2},
        },
        {"kind": "length", "container": "day"},
        {"kind": "neighbors", "container": "do_thi", "node": {"kind": "literal", "value": "a"}},
    ],
)
def test_dang_khong_mang_bool_van_bi_tu_choi(tho):
    assert canonical_condition(tho) is tho
    with pytest.raises(ValidationError):
        LogicCond.model_validate(
            {
                "kind": "logic",
                "op": "and",
                "left": tho,
                "right": {"kind": "is_empty", "container": "s"},
            }
        )


# ── 3. Mệnh đề thật đi qua NGUYÊN VẸN ─────────────────────────────────────
@pytest.mark.parametrize(
    "menh_de",
    [
        {"kind": "is_empty", "container": "ngan_xep"},
        {"kind": "is_null", "expr": {"kind": "var", "name": "x"}},
        {"kind": "contains", "container": "tap", "item": {"kind": "literal", "value": 1}},
        {
            "kind": "compare",
            "op": "==",
            "left": {"kind": "var", "name": "a"},
            "right": {"kind": "literal", "value": 1},
        },
    ],
)
def test_sau_dang_menh_de_khong_bi_dung_toi(menh_de):
    assert canonical_condition(menh_de) is menh_de


def test_khong_dung_toi_thu_khong_phai_dict():
    for v in (None, "hop_le", 3, [1, 2]):
        assert canonical_condition(v) is v
